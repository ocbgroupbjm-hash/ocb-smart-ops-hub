"""
OCB TITAN ERP - SALES RETURN (RETUR PENJUALAN) ENGINE
=====================================================
P0: Implementasi flow retur penjualan yang audit-safe

FLOW RETUR PENJUALAN:
1. Pilih Invoice/Transaksi yang akan diretur
2. Input item dan qty yang diretur
3. System auto:
   - Tambah stock (stock_in movement)
   - Kurangi revenue (credit note)
   - Balik HPP (credit HPP, debit Persediaan)
   - Buat jurnal reversal

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

router = APIRouter(prefix="/api/sales-return", tags=["Sales Return"])

# ==================== PYDANTIC MODELS ====================

class SalesReturnItem(BaseModel):
    product_id: str
    product_name: str = ""
    quantity: float
    unit_price: float  # Harga jual
    unit_cost: float = 0  # HPP
    reason: str = ""

class CreateSalesReturn(BaseModel):
    invoice_id: str
    customer_id: str = ""
    branch_id: str = ""
    items: List[SalesReturnItem]
    return_type: str = "full"  # full, partial
    refund_method: str = "credit"  # credit, cash, transfer
    reason: str = ""
    notes: str = ""

# ==================== HELPER FUNCTIONS ====================

async def generate_return_number(db, prefix: str = "RTN") -> str:
    """Generate return number"""
    from database import get_next_sequence
    seq = await get_next_sequence("sales_return_number")
    return f"{prefix}{str(seq).zfill(6)}"

async def derive_account(db, account_key: str, branch_id: str = None) -> Dict:
    """Derive account from setting akun ERP"""
    settings = await db["account_settings"].find_one({"code": account_key}, {"_id": 0})
    if settings:
        return {
            "code": settings.get("account_code", ""),
            "name": settings.get("account_name", "")
        }
    
    # Fallback defaults
    defaults = {
        "persediaan_barang": {"code": "1-1400", "name": "Persediaan Barang"},
        "hpp": {"code": "5-1000", "name": "Harga Pokok Penjualan"},
        "penjualan": {"code": "4-1000", "name": "Penjualan"},
        "retur_penjualan": {"code": "4-1100", "name": "Retur Penjualan"},
        "kas": {"code": "1-1100", "name": "Kas"},
        "piutang_dagang": {"code": "1-1200", "name": "Piutang Dagang"}
    }
    return defaults.get(account_key, {"code": "9-9999", "name": "Unknown"})

# ==================== API ENDPOINTS ====================

@router.post("/create")
async def create_sales_return(
    data: CreateSalesReturn,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """
    Create Sales Return (Retur Penjualan)
    
    FLOW:
    1. Validate invoice exists and is completed
    2. Validate return qty doesn't exceed sold qty
    3. Create stock_in movement (increase stock)
    4. Create credit note / reduce revenue
    5. Reverse HPP
    6. Create reversal journal
    """
    db = get_db()
    now = datetime.now(timezone.utc).isoformat()
    
    # ============ FIND INVOICE ============
    # Try multiple collections (transactions, sales_invoices)
    invoice = await db["transactions"].find_one({"id": data.invoice_id}, {"_id": 0})
    if not invoice:
        invoice = await db["sales_invoices"].find_one({"id": data.invoice_id}, {"_id": 0})
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice/Transaksi tidak ditemukan")
    
    # Only allow return for completed invoices
    allowed_status = ["completed", "paid", "delivered"]
    if invoice.get("status") not in allowed_status:
        raise HTTPException(
            status_code=400,
            detail=f"Retur hanya bisa untuk transaksi dengan status: {', '.join(allowed_status)}"
        )
    
    # Get branch
    branch_id = data.branch_id or invoice.get("branch_id") or user.get("branch_id")
    
    # ============ VALIDASI ITEMS ============
    total_return_value = 0
    total_hpp_value = 0
    return_items = []
    
    invoice_items = invoice.get("items", invoice.get("line_items", []))
    
    for item in data.items:
        if item.quantity <= 0:
            raise HTTPException(status_code=400, detail="Qty retur harus > 0")
        
        # Find matching invoice item
        inv_item = next((i for i in invoice_items if i.get("product_id") == item.product_id), None)
        if not inv_item:
            raise HTTPException(
                status_code=400,
                detail=f"Product {item.product_id} tidak ada di invoice"
            )
        
        sold_qty = inv_item.get("quantity", inv_item.get("qty", 0))
        
        # Check existing returns
        existing_returns = await db["sales_returns"].find({
            "invoice_id": data.invoice_id,
            "items.product_id": item.product_id,
            "status": {"$ne": "cancelled"}
        }).to_list(100)
        
        already_returned = sum(
            sum(ri.get("quantity", 0) for ri in r.get("items", []) if ri.get("product_id") == item.product_id)
            for r in existing_returns
        )
        
        max_returnable = sold_qty - already_returned
        if item.quantity > max_returnable:
            raise HTTPException(
                status_code=400,
                detail=f"Qty retur ({item.quantity}) melebihi sisa yang bisa diretur ({max_returnable})"
            )
        
        unit_price = item.unit_price or inv_item.get("unit_price", inv_item.get("price", 0))
        unit_cost = item.unit_cost or inv_item.get("unit_cost", inv_item.get("hpp", inv_item.get("cost_price", 0)))
        
        return_value = item.quantity * unit_price
        hpp_value = item.quantity * unit_cost
        
        total_return_value += return_value
        total_hpp_value += hpp_value
        
        return_items.append({
            "product_id": item.product_id,
            "product_name": item.product_name or inv_item.get("product_name", inv_item.get("name", "")),
            "product_code": inv_item.get("product_code", inv_item.get("code", "")),
            "quantity": item.quantity,
            "unit_price": unit_price,
            "unit_cost": unit_cost,
            "subtotal": return_value,
            "hpp_subtotal": hpp_value,
            "reason": item.reason
        })
    
    if total_return_value <= 0:
        raise HTTPException(status_code=400, detail="Total nilai retur harus > 0")
    
    # ============ CREATE RETURN DOCUMENT ============
    return_number = await generate_return_number(db, "RTN-SLS-")
    return_id = str(uuid.uuid4())
    
    invoice_number = invoice.get("invoice_number", invoice.get("receipt_number", invoice.get("transaction_number", "")))
    customer_name = invoice.get("customer_name", invoice.get("customer", {}).get("name", ""))
    
    return_doc = {
        "id": return_id,
        "return_number": return_number,
        "return_date": now,
        "invoice_id": data.invoice_id,
        "invoice_number": invoice_number,
        "customer_id": data.customer_id or invoice.get("customer_id"),
        "customer_name": customer_name,
        "branch_id": branch_id,
        "return_type": data.return_type,
        "refund_method": data.refund_method,
        "items": return_items,
        "total_items": len(return_items),
        "total_qty": sum(i["quantity"] for i in return_items),
        "total_value": total_return_value,
        "total_hpp": total_hpp_value,
        "reason": data.reason,
        "notes": data.notes,
        "status": "posted",
        "created_by": user.get("user_id", ""),
        "created_by_name": user.get("name", ""),
        "created_at": now,
        "updated_at": now
    }
    
    await db["sales_returns"].insert_one(return_doc)
    
    # ============ STOCK IN (INCREASE STOCK) ============
    for item in return_items:
        # Create stock_in movement
        movement = {
            "id": str(uuid.uuid4()),
            "product_id": item["product_id"],
            "product_name": item["product_name"],
            "branch_id": branch_id,
            "movement_type": "stock_in",
            "quantity": item["quantity"],  # Positive for in
            "reference_type": "sales_return",
            "reference_id": return_id,
            "reference_number": return_number,
            "reference_no": return_number,
            "cost_per_unit": item["unit_cost"],
            "total_cost": item["hpp_subtotal"],
            "notes": f"Retur Penjualan: {return_number} - {item.get('reason', '')}",
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
            new_qty = stock.get("quantity", 0) + item["quantity"]
            await db["product_stocks"].update_one(
                {"product_id": item["product_id"], "branch_id": branch_id},
                {"$set": {"quantity": new_qty, "updated_at": now}}
            )
        else:
            # Create new stock record
            await db["product_stocks"].insert_one({
                "id": str(uuid.uuid4()),
                "product_id": item["product_id"],
                "branch_id": branch_id,
                "quantity": item["quantity"],
                "unit_cost": item["unit_cost"],
                "created_at": now,
                "updated_at": now
            })
        
        # Update products.stock
        product = await db["products"].find_one({"id": item["product_id"]}, {"_id": 0})
        if product:
            current_stock = product.get("stock", 0)
            await db["products"].update_one(
                {"id": item["product_id"]},
                {"$set": {"stock": current_stock + item["quantity"], "updated_at": now}}
            )
    
    # ============ CREATE REVERSAL JOURNAL ============
    # Journal entries:
    # 1. Debit: Retur Penjualan (4-1100) → reduce revenue
    # 2. Credit: Kas/Piutang → refund
    # 3. Debit: Persediaan (1-1400) → increase inventory
    # 4. Credit: HPP (5-1000) → reverse cost of goods
    
    from utils.number_generator import generate_transaction_number
    
    journal_id = str(uuid.uuid4())
    journal_number = await generate_transaction_number(db, "JV-SRT")
    
    retur_account = await derive_account(db, "retur_penjualan", branch_id)
    kas_account = await derive_account(db, "kas", branch_id)
    inventory_account = await derive_account(db, "persediaan_barang", branch_id)
    hpp_account = await derive_account(db, "hpp", branch_id)
    
    journal_entries_list = [
        # Revenue reversal
        {
            "account_code": retur_account["code"],
            "account_name": retur_account["name"],
            "debit": total_return_value,
            "credit": 0,
            "description": f"Retur penjualan {return_number}"
        },
        {
            "account_code": kas_account["code"],
            "account_name": kas_account["name"],
            "debit": 0,
            "credit": total_return_value,
            "description": f"Refund untuk retur {return_number}"
        },
        # HPP reversal
        {
            "account_code": inventory_account["code"],
            "account_name": inventory_account["name"],
            "debit": total_hpp_value,
            "credit": 0,
            "description": f"Persediaan kembali dari retur {return_number}"
        },
        {
            "account_code": hpp_account["code"],
            "account_name": hpp_account["name"],
            "debit": 0,
            "credit": total_hpp_value,
            "description": f"HPP dibalik dari retur {return_number}"
        }
    ]
    
    journal_entry = {
        "id": journal_id,
        "journal_number": journal_number,
        "journal_date": now,
        "reference_type": "sales_return",
        "reference_id": return_id,
        "reference_number": return_number,
        "description": f"Retur Penjualan {return_number} - {customer_name}",
        "entries": journal_entries_list,
        "total_debit": total_return_value + total_hpp_value,
        "total_credit": total_return_value + total_hpp_value,
        "is_auto": True,
        "is_reversal": True,
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
        "create", "sales_return",
        f"Retur Penjualan {return_number} untuk Invoice {invoice_number} | Nilai: Rp {total_return_value:,.0f}",
        request.client.host if request.client else "",
        document_no=return_number,
        severity="normal"
    )
    
    return {
        "success": True,
        "message": "Retur penjualan berhasil diproses",
        "return_id": return_id,
        "return_number": return_number,
        "invoice_number": invoice_number,
        "total_value": total_return_value,
        "total_hpp": total_hpp_value,
        "items_count": len(return_items),
        "stock_added": True,
        "revenue_reduced": True,
        "hpp_reversed": True,
        "journal_number": journal_number
    }


@router.get("/list")
async def list_sales_returns(
    customer_id: str = None,
    invoice_id: str = None,
    status: str = None,
    limit: int = 50,
    skip: int = 0,
    user: dict = Depends(get_current_user)
):
    """List sales returns"""
    db = get_db()
    
    query = {}
    if customer_id:
        query["customer_id"] = customer_id
    if invoice_id:
        query["invoice_id"] = invoice_id
    if status:
        query["status"] = status
    
    returns = await db["sales_returns"].find(
        query, {"_id": 0}
    ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    total = await db["sales_returns"].count_documents(query)
    
    return {"items": returns, "total": total}


@router.get("/{return_id}")
async def get_sales_return(
    return_id: str,
    user: dict = Depends(get_current_user)
):
    """Get sales return detail"""
    db = get_db()
    
    ret = await db["sales_returns"].find_one({"id": return_id}, {"_id": 0})
    if not ret:
        raise HTTPException(status_code=404, detail="Return tidak ditemukan")
    
    return ret
