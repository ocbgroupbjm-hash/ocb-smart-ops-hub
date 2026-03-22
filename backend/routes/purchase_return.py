"""
OCB TITAN ERP - PURCHASE RETURN (RETUR PEMBELIAN) ENGINE
=========================================================
P0: Implementasi flow retur yang audit-safe

FLOW RETUR PEMBELIAN:
1. Pilih PO yang akan diretur
2. Input item dan qty yang diretur
3. System auto:
   - Kurangi stock (stock_out movement)
   - Kurangi hutang AP (credit note / reduction)
   - Buat jurnal reversal (Debit: Hutang, Credit: Persediaan)
4. Jika sudah ada pembayaran:
   - Create supplier receivable / refund flow

RULES:
- Tidak boleh delete transaksi completed
- Tidak boleh edit langsung jurnal
- Semua koreksi via retur/reversal
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from database import get_db
from utils.auth import get_current_user
import uuid

router = APIRouter(prefix="/api/purchase-return", tags=["Purchase Return"])

# ==================== PYDANTIC MODELS ====================

class ReturnItem(BaseModel):
    product_id: str
    product_name: str = ""
    quantity: float  # Qty yang diretur
    unit_cost: float
    reason: str = ""

class CreatePurchaseReturn(BaseModel):
    po_id: str
    supplier_id: str
    branch_id: str = ""
    items: List[ReturnItem]
    return_type: str = "full"  # full, partial
    reason: str = ""
    notes: str = ""

# ==================== HELPER FUNCTIONS ====================

async def generate_return_number(db, prefix: str = "RTN") -> str:
    """Generate return number"""
    from database import get_next_sequence
    seq = await get_next_sequence("return_number")
    return f"{prefix}{str(seq).zfill(6)}"

async def derive_return_account(db, account_key: str, branch_id: str = None) -> Dict:
    """Derive account from setting akun ERP"""
    settings = await db["account_settings"].find_one({"code": account_key}, {"_id": 0})
    if settings:
        return {
            "code": settings.get("account_code", "1-1400"),
            "name": settings.get("account_name", "Persediaan Barang")
        }
    
    # Fallback defaults
    defaults = {
        "persediaan_barang": {"code": "1-1400", "name": "Persediaan Barang"},
        "hutang_dagang": {"code": "2-1100", "name": "Hutang Dagang"},
        "piutang_supplier": {"code": "1-1300", "name": "Piutang Supplier (Refund)"}
    }
    return defaults.get(account_key, {"code": "9-9999", "name": "Unknown"})

# ==================== API ENDPOINTS ====================

@router.post("/create")
async def create_purchase_return(
    data: CreatePurchaseReturn,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """
    Create Purchase Return (Retur Pembelian)
    
    FLOW:
    1. Validate PO exists and is received/posted
    2. Validate return qty doesn't exceed received qty
    3. Create stock_out movement (reduce stock)
    4. Update AP (reduce hutang) OR create supplier receivable
    5. Create reversal journal
    """
    db = get_db()
    now = datetime.now(timezone.utc).isoformat()
    
    # ============ VALIDASI PO ============
    po = await db["purchase_orders"].find_one({"id": data.po_id}, {"_id": 0})
    if not po:
        raise HTTPException(status_code=404, detail="Purchase Order tidak ditemukan")
    
    # Only allow return for received/posted POs
    allowed_status = ["received", "posted", "completed"]
    if po.get("status") not in allowed_status:
        raise HTTPException(
            status_code=400, 
            detail=f"Retur hanya bisa untuk PO dengan status: {', '.join(allowed_status)}"
        )
    
    # Get branch
    branch_id = data.branch_id or po.get("branch_id") or user.get("branch_id")
    await db["branches"].find_one({"id": branch_id}, {"_id": 0})  # Validate branch exists
    
    # ============ VALIDASI ITEMS ============
    total_return_value = 0
    return_items = []
    
    for item in data.items:
        if item.quantity <= 0:
            raise HTTPException(status_code=400, detail="Qty retur harus > 0")
        
        # Find matching PO item
        po_item = next((i for i in po.get("items", []) if i.get("product_id") == item.product_id), None)
        if not po_item:
            raise HTTPException(
                status_code=400, 
                detail=f"Product {item.product_id} tidak ada di PO"
            )
        
        received_qty = po_item.get("received_qty", po_item.get("quantity", 0))
        
        # Check existing returns for this PO
        existing_returns = await db["purchase_returns"].find({
            "po_id": data.po_id,
            "items.product_id": item.product_id,
            "status": {"$ne": "cancelled"}
        }).to_list(100)
        
        already_returned = sum(
            sum(ri.get("quantity", 0) for ri in r.get("items", []) if ri.get("product_id") == item.product_id)
            for r in existing_returns
        )
        
        max_returnable = received_qty - already_returned
        if item.quantity > max_returnable:
            raise HTTPException(
                status_code=400,
                detail=f"Qty retur ({item.quantity}) melebihi sisa yang bisa diretur ({max_returnable}) untuk {po_item.get('product_name', item.product_id)}"
            )
        
        unit_cost = item.unit_cost or po_item.get("unit_cost", 0)
        return_value = item.quantity * unit_cost
        total_return_value += return_value
        
        return_items.append({
            "product_id": item.product_id,
            "product_name": item.product_name or po_item.get("product_name", ""),
            "product_code": po_item.get("product_code", ""),
            "quantity": item.quantity,
            "unit_cost": unit_cost,
            "subtotal": return_value,
            "reason": item.reason
        })
    
    if total_return_value <= 0:
        raise HTTPException(status_code=400, detail="Total nilai retur harus > 0")
    
    # ============ CREATE RETURN DOCUMENT ============
    return_number = await generate_return_number(db, "RTN-PUR-")
    return_id = str(uuid.uuid4())
    
    return_doc = {
        "id": return_id,
        "return_number": return_number,
        "return_date": now,
        "po_id": data.po_id,
        "po_number": po.get("po_number"),
        "supplier_id": data.supplier_id or po.get("supplier_id"),
        "supplier_name": po.get("supplier_name", ""),
        "branch_id": branch_id,
        "return_type": data.return_type,
        "items": return_items,
        "total_items": len(return_items),
        "total_qty": sum(i["quantity"] for i in return_items),
        "total_value": total_return_value,
        "reason": data.reason,
        "notes": data.notes,
        "status": "posted",
        "created_by": user.get("user_id", ""),
        "created_by_name": user.get("name", ""),
        "created_at": now,
        "updated_at": now
    }
    
    await db["purchase_returns"].insert_one(return_doc)
    
    # ============ STOCK OUT (REDUCE STOCK) ============
    for item in return_items:
        # Create stock_out movement
        movement = {
            "id": str(uuid.uuid4()),
            "product_id": item["product_id"],
            "product_name": item["product_name"],
            "branch_id": branch_id,
            "movement_type": "stock_out",
            "quantity": -abs(item["quantity"]),  # Negative for out
            "reference_type": "purchase_return",
            "reference_id": return_id,
            "reference_number": return_number,
            "reference_no": return_number,
            "cost_per_unit": item["unit_cost"],
            "total_cost": -abs(item["subtotal"]),
            "notes": f"Retur Pembelian: {return_number} - {item.get('reason', '')}",
            "created_by": user.get("user_id", ""),
            "created_at": now
        }
        await db["stock_movements"].insert_one(movement)
        
        # Update product_stocks
        stock = await db["product_stocks"].find_one({
            "product_id": item["product_id"],
            "branch_id": branch_id
        })
        
        if stock:
            new_qty = max(0, stock.get("quantity", 0) - item["quantity"])
            await db["product_stocks"].update_one(
                {"product_id": item["product_id"], "branch_id": branch_id},
                {"$set": {"quantity": new_qty, "updated_at": now}}
            )
        
        # Update products.stock
        product = await db["products"].find_one({"id": item["product_id"]}, {"_id": 0})
        if product:
            current_stock = product.get("stock", 0)
            await db["products"].update_one(
                {"id": item["product_id"]},
                {"$set": {"stock": max(0, current_stock - item["quantity"]), "updated_at": now}}
            )
    
    # ============ UPDATE AP (REDUCE HUTANG) ============
    # Find AP for this PO
    ap = await db["accounts_payable"].find_one({
        "$or": [
            {"source_id": data.po_id},
            {"source_no": po.get("po_number")}
        ],
        "status": {"$ne": "paid"}
    })
    
    ap_updated = False
    supplier_receivable_created = False
    
    if ap:
        current_outstanding = ap.get("outstanding_amount", ap.get("original_amount", 0))
        new_outstanding = current_outstanding - total_return_value
        
        if new_outstanding >= 0:
            # Normal case: reduce AP outstanding
            await db["accounts_payable"].update_one(
                {"id": ap["id"]},
                {"$set": {
                    "outstanding_amount": new_outstanding,
                    "status": "open" if new_outstanding > 0 else "paid",
                    "return_reduction": ap.get("return_reduction", 0) + total_return_value,
                    "updated_at": now
                }}
            )
            ap_updated = True
        else:
            # Negative: Create supplier receivable (refund due)
            receivable = {
                "id": str(uuid.uuid4()),
                "receivable_no": f"SR-{return_number}",
                "supplier_id": data.supplier_id or po.get("supplier_id"),
                "supplier_name": po.get("supplier_name", ""),
                "source_type": "purchase_return",
                "source_id": return_id,
                "source_no": return_number,
                "amount": abs(new_outstanding),
                "status": "pending",
                "notes": f"Kelebihan bayar dari retur {return_number}",
                "created_at": now
            }
            await db["supplier_receivables"].insert_one(receivable)
            
            # Close AP
            await db["accounts_payable"].update_one(
                {"id": ap["id"]},
                {"$set": {
                    "outstanding_amount": 0,
                    "status": "paid",
                    "return_reduction": ap.get("return_reduction", 0) + current_outstanding,
                    "updated_at": now
                }}
            )
            supplier_receivable_created = True
            ap_updated = True
    
    # ============ CREATE REVERSAL JOURNAL ============
    # Debit: Hutang Dagang (reduce liability)
    # Credit: Persediaan (reduce asset)
    
    from utils.number_generator import generate_transaction_number
    
    journal_id = str(uuid.uuid4())
    journal_number = await generate_transaction_number(db, "JV-RTN")
    
    inventory_account = await derive_return_account(db, "persediaan_barang", branch_id)
    hutang_account = await derive_return_account(db, "hutang_dagang", branch_id)
    
    journal_entries_list = [
        {
            "account_code": hutang_account["code"],
            "account_name": hutang_account["name"],
            "debit": total_return_value,
            "credit": 0,
            "description": f"Pengurangan hutang dari retur {return_number}"
        },
        {
            "account_code": inventory_account["code"],
            "account_name": inventory_account["name"],
            "debit": 0,
            "credit": total_return_value,
            "description": f"Pengurangan persediaan dari retur {return_number}"
        }
    ]
    
    journal_entry = {
        "id": journal_id,
        "journal_number": journal_number,
        "journal_date": now,
        "reference_type": "purchase_return",
        "reference_id": return_id,
        "reference_number": return_number,
        "description": f"Retur Pembelian {return_number} - {po.get('supplier_name', '')}",
        "entries": journal_entries_list,
        "total_debit": total_return_value,
        "total_credit": total_return_value,
        "is_auto": True,
        "is_reversal": True,
        "original_journal_id": None,  # This is a new reversal, not reversing existing
        "status": "posted",
        "branch_id": branch_id,
        "created_by": user.get("user_id", ""),
        "created_by_name": user.get("name", "System"),
        "created_at": now
    }
    
    await db["journal_entries"].insert_one(journal_entry)
    
    # ============ AUDIT LOG ============
    from utils.security import log_security_event
    await log_security_event(
        db, user.get("user_id", ""), user.get("name", ""),
        "create", "purchase_return",
        f"Retur Pembelian {return_number} untuk PO {po.get('po_number')} | Nilai: Rp {total_return_value:,.0f}",
        request.client.host if request.client else "",
        document_no=return_number,
        severity="normal"
    )
    
    return {
        "success": True,
        "message": "Retur pembelian berhasil diproses",
        "return_id": return_id,
        "return_number": return_number,
        "po_number": po.get("po_number"),
        "total_value": total_return_value,
        "items_count": len(return_items),
        "stock_reduced": True,
        "ap_updated": ap_updated,
        "supplier_receivable_created": supplier_receivable_created,
        "journal_number": journal_number
    }


@router.get("/list")
async def list_purchase_returns(
    supplier_id: str = None,
    po_id: str = None,
    status: str = None,
    limit: int = 50,
    skip: int = 0,
    user: dict = Depends(get_current_user)
):
    """List purchase returns"""
    db = get_db()
    
    query = {}
    if supplier_id:
        query["supplier_id"] = supplier_id
    if po_id:
        query["po_id"] = po_id
    if status:
        query["status"] = status
    
    returns = await db["purchase_returns"].find(
        query, {"_id": 0}
    ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    total = await db["purchase_returns"].count_documents(query)
    
    return {"items": returns, "total": total}


@router.get("/{return_id}")
async def get_purchase_return(
    return_id: str,
    user: dict = Depends(get_current_user)
):
    """Get purchase return detail"""
    db = get_db()
    
    ret = await db["purchase_returns"].find_one({"id": return_id}, {"_id": 0})
    if not ret:
        raise HTTPException(status_code=404, detail="Return tidak ditemukan")
    
    return ret


@router.get("/po/{po_id}/returnable")
async def get_returnable_items(
    po_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Get items that can still be returned from a PO
    """
    db = get_db()
    
    po = await db["purchase_orders"].find_one({"id": po_id}, {"_id": 0})
    if not po:
        raise HTTPException(status_code=404, detail="PO tidak ditemukan")
    
    # Get existing returns for this PO
    existing_returns = await db["purchase_returns"].find({
        "po_id": po_id,
        "status": {"$ne": "cancelled"}
    }).to_list(100)
    
    returnable_items = []
    
    for item in po.get("items", []):
        product_id = item.get("product_id")
        received_qty = item.get("received_qty", item.get("quantity", 0))
        
        # Calculate already returned
        already_returned = sum(
            sum(ri.get("quantity", 0) for ri in r.get("items", []) if ri.get("product_id") == product_id)
            for r in existing_returns
        )
        
        max_returnable = received_qty - already_returned
        
        if max_returnable > 0:
            returnable_items.append({
                "product_id": product_id,
                "product_code": item.get("product_code", ""),
                "product_name": item.get("product_name", ""),
                "unit_cost": item.get("unit_cost", 0),
                "received_qty": received_qty,
                "already_returned": already_returned,
                "max_returnable": max_returnable
            })
    
    return {
        "po_id": po_id,
        "po_number": po.get("po_number"),
        "supplier_name": po.get("supplier_name", ""),
        "items": returnable_items,
        "can_return": len(returnable_items) > 0
    }
