# OCB TITAN - Purchase Management API
# SECURITY: All operations require RBAC validation
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional, List
from database import (
    purchase_orders, suppliers, products, product_stocks, 
    stock_movements, branches, get_next_sequence, get_db
)
from utils.auth import get_current_user
from models.titan_models import PurchaseOrder, PurchaseOrderItem, PurchaseStatus, StockMovement, StockMovementType, ProductStock
from routes.rbac_middleware import require_permission, log_security_event
from datetime import datetime, timezone

router = APIRouter(prefix="/purchase", tags=["Purchase"])

class POItemInput(BaseModel):
    product_id: str
    quantity: int
    unit_cost: float
    discount_percent: float = 0

class CreatePO(BaseModel):
    supplier_id: str
    branch_id: Optional[str] = None
    items: List[POItemInput]
    expected_date: Optional[str] = None
    notes: str = ""
    # AP integration fields
    is_credit: bool = True  # Most purchases are on credit
    credit_due_days: int = 30  # Days until payment due

class ReceiveItem(BaseModel):
    product_id: str
    quantity: int

class ReceivePO(BaseModel):
    items: List[ReceiveItem]
    notes: str = ""

# ==================== PURCHASE ORDERS ====================

@router.get("/orders")
async def list_purchase_orders(
    status: str = "",
    supplier_id: str = "",
    skip: int = 0,
    limit: int = 50,
    user: dict = Depends(require_permission("purchase", "view"))
):
    """List purchase orders - Requires purchase.view permission"""
    query = {}
    
    if status:
        query["status"] = status
    
    if supplier_id:
        query["supplier_id"] = supplier_id
    
    items = await purchase_orders.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    total = await purchase_orders.count_documents(query)
    
    return {"items": items, "total": total}

@router.get("/orders/{po_id}")
async def get_purchase_order(po_id: str, user: dict = Depends(require_permission("purchase", "view"))):
    """Get purchase order details - Requires purchase.view permission"""
    po = await purchase_orders.find_one({"id": po_id}, {"_id": 0})
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return po

@router.post("/orders")
async def create_purchase_order(data: CreatePO, request: Request, user: dict = Depends(require_permission("purchase", "create"))):
    """Create purchase order - Requires purchase.create permission"""
    supplier = await suppliers.find_one({"id": data.supplier_id}, {"_id": 0})
    if not supplier:
        raise HTTPException(status_code=400, detail="Supplier not found")
    
    branch_id = data.branch_id or user.get("branch_id")
    
    # Build items
    po_items = []
    subtotal = 0
    
    for item in data.items:
        product = await products.find_one({"id": item.product_id}, {"_id": 0})
        if not product:
            raise HTTPException(status_code=400, detail=f"Product not found: {item.product_id}")
        
        item_subtotal = item.unit_cost * item.quantity
        if item.discount_percent > 0:
            item_subtotal -= item_subtotal * (item.discount_percent / 100)
        
        po_item = PurchaseOrderItem(
            product_id=item.product_id,
            product_code=product.get("code", ""),
            product_name=product.get("name", ""),
            quantity=item.quantity,
            unit_cost=item.unit_cost,
            discount_percent=item.discount_percent,
            subtotal=item_subtotal
        )
        
        po_items.append(po_item)
        subtotal += item_subtotal
    
    po_number = await get_next_sequence("po_number", "PO")
    
    po = PurchaseOrder(
        po_number=po_number,
        supplier_id=data.supplier_id,
        supplier_name=supplier.get("name", ""),
        branch_id=branch_id,
        items=[item.model_dump() for item in po_items],
        subtotal=subtotal,
        total=subtotal,
        expected_date=data.expected_date,
        notes=data.notes,
        user_id=user.get("user_id", "")
    )
    
    await purchase_orders.insert_one(po.model_dump())
    
    # Audit log
    db = get_db()
    await log_security_event(
        db, user.get("user_id", ""), user.get("name", ""),
        "create", "purchase",
        f"Membuat PO {po_number} ke {supplier.get('name')} sebesar Rp {subtotal:,.0f}",
        request.client.host if request.client else "",
        document_no=po_number
    )
    
    return {"id": po.id, "po_number": po_number, "message": "Purchase order created"}

@router.post("/orders/{po_id}/submit")
async def submit_purchase_order(po_id: str, request: Request, user: dict = Depends(require_permission("purchase", "edit"))):
    """Submit PO to supplier - Requires purchase.edit permission"""
    po = await purchase_orders.find_one({"id": po_id}, {"_id": 0})
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    
    if po.get("status") != "draft":
        raise HTTPException(status_code=400, detail="PO already submitted")
    
    await purchase_orders.update_one(
        {"id": po_id},
        {"$set": {
            "status": "ordered",
            "order_date": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Audit log
    db = get_db()
    await log_security_event(
        db, user.get("user_id", ""), user.get("name", ""),
        "edit", "purchase",
        f"Submit PO {po.get('po_number')} ke supplier",
        request.client.host if request.client else "",
        document_no=po.get('po_number')
    )
    
    return {"message": "Purchase order submitted"}

@router.post("/orders/{po_id}/receive")
async def receive_purchase_order(po_id: str, data: ReceivePO, request: Request, user: dict = Depends(require_permission("purchase", "edit"))):
    """Receive goods from purchase order - Requires purchase.edit permission"""
    po = await purchase_orders.find_one({"id": po_id}, {"_id": 0})
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    
    if po.get("status") not in ["ordered", "partial"]:
        raise HTTPException(status_code=400, detail="Cannot receive this PO")
    
    branch_id = po.get("branch_id")
    
    # Update received quantities and add to stock
    all_received = True
    
    for receive_item in data.items:
        # Find the PO item
        for po_item in po.get("items", []):
            if po_item["product_id"] == receive_item.product_id:
                new_received = po_item.get("received_qty", 0) + receive_item.quantity
                
                # Update PO item
                await purchase_orders.update_one(
                    {"id": po_id, "items.product_id": receive_item.product_id},
                    {"$set": {"items.$.received_qty": new_received}}
                )
                
                if new_received < po_item["quantity"]:
                    all_received = False
                
                # Add to stock
                stock = await product_stocks.find_one(
                    {"product_id": receive_item.product_id, "branch_id": branch_id}
                )
                
                if stock:
                    await product_stocks.update_one(
                        {"product_id": receive_item.product_id, "branch_id": branch_id},
                        {
                            "$inc": {"quantity": receive_item.quantity, "available": receive_item.quantity},
                            "$set": {
                                "last_restock": datetime.now(timezone.utc).isoformat(),
                                "updated_at": datetime.now(timezone.utc).isoformat()
                            }
                        }
                    )
                else:
                    new_stock = ProductStock(
                        product_id=receive_item.product_id,
                        branch_id=branch_id,
                        quantity=receive_item.quantity,
                        available=receive_item.quantity,
                        last_restock=datetime.now(timezone.utc).isoformat()
                    )
                    await product_stocks.insert_one(new_stock.model_dump())
                
                # Record stock movement
                movement = StockMovement(
                    product_id=receive_item.product_id,
                    branch_id=branch_id,
                    movement_type=StockMovementType.STOCK_IN,
                    quantity=receive_item.quantity,
                    reference_id=po_id,
                    reference_type="purchase_order",
                    cost_price=po_item.get("unit_cost", 0) * receive_item.quantity,
                    notes=f"PO: {po.get('po_number')}",
                    user_id=user.get("user_id", "")
                )
                await stock_movements.insert_one(movement.model_dump())
                
                # Update product cost price
                await products.update_one(
                    {"id": receive_item.product_id},
                    {"$set": {"cost_price": po_item.get("unit_cost", 0)}}
                )
                
                break
    
    # Update PO status
    new_status = "received" if all_received else "partial"
    
    await purchase_orders.update_one(
        {"id": po_id},
        {"$set": {
            "status": new_status,
            "received_date": datetime.now(timezone.utc).isoformat() if all_received else None,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # =============== AUTO-CREATE AP FOR CREDIT PURCHASES ===============
    ap_id = None
    if all_received and po.get("is_credit", True):  # Default to credit
        from datetime import timedelta
        import uuid
        
        po_total = po.get("total", 0)
        credit_due_days = po.get("credit_due_days", 30)
        due_date = datetime.now(timezone.utc) + timedelta(days=credit_due_days)
        
        ap_entry = {
            "id": str(uuid.uuid4()),
            "ap_number": f"AP-{po.get('po_number')}",
            "supplier_id": po.get("supplier_id"),
            "supplier_name": po.get("supplier_name", "Unknown"),
            "source_type": "purchase",
            "source_id": po_id,
            "source_number": po.get("po_number"),
            "branch_id": branch_id,
            "amount": po_total,
            "paid_amount": 0,
            "due_date": due_date.isoformat(),
            "status": "unpaid",
            "notes": f"Hutang dari pembelian {po.get('po_number')}",
            "created_by": user.get("user_id", ""),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        db = get_db()
        await db["accounts_payable"].insert_one(ap_entry)
        ap_id = ap_entry["id"]
        
        # Create journal entry for purchase (Debit: Inventory, Credit: AP)
        journal_id = str(uuid.uuid4())
        journal_no = f"JV-AP-{po.get('po_number')}"
        
        journal_entry = {
            "id": journal_id,
            "journal_no": journal_no,
            "journal_date": datetime.now(timezone.utc).isoformat(),
            "source_type": "purchase_credit",
            "source_id": po_id,
            "description": f"Pembelian kredit {po.get('po_number')} dari {po.get('supplier_name')}",
            "total_debit": po_total,
            "total_credit": po_total,
            "status": "posted",
            "branch_id": branch_id,
            "created_by": user.get("user_id", ""),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db["journal_entries"].insert_one(journal_entry)
        
        # Journal lines
        journal_lines = [
            {
                "id": str(uuid.uuid4()),
                "journal_id": journal_id,
                "account_code": "1301",  # Persediaan
                "account_name": "Persediaan Barang Dagang",
                "debit": po_total,
                "credit": 0,
                "description": f"Persediaan dari {po.get('po_number')}"
            },
            {
                "id": str(uuid.uuid4()),
                "journal_id": journal_id,
                "account_code": "2101",  # Hutang Dagang
                "account_name": "Hutang Dagang",
                "debit": 0,
                "credit": po_total,
                "description": f"Hutang ke {po.get('supplier_name')}"
            }
        ]
        await db["journal_entry_lines"].insert_many(journal_lines)
    
    # Audit log
    db = get_db()
    await log_security_event(
        db, user.get("user_id", ""), user.get("name", ""),
        "edit", "purchase",
        f"Receive PO {po.get('po_number')} - status: {new_status}" + (f" - AP {ap_id} created" if ap_id else ""),
        request.client.host if request.client else "",
        document_no=po.get('po_number')
    )
    
    return {
        "message": f"Goods received. Status: {new_status}",
        "ap_created": ap_id is not None,
        "ap_id": ap_id
    }

@router.post("/orders/{po_id}/cancel")
async def cancel_purchase_order(po_id: str, request: Request, user: dict = Depends(require_permission("purchase", "delete"))):
    """Cancel a purchase order - Requires purchase.delete permission"""
    po = await purchase_orders.find_one({"id": po_id}, {"_id": 0})
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    
    if po.get("status") not in ["draft", "ordered"]:
        raise HTTPException(status_code=400, detail="Cannot cancel this PO")
    
    await purchase_orders.update_one(
        {"id": po_id},
        {"$set": {
            "status": "cancelled",
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Audit log
    db = get_db()
    await log_security_event(
        db, user.get("user_id", ""), user.get("name", ""),
        "cancel", "purchase",
        f"CANCEL PO {po.get('po_number')}",
        request.client.host if request.client else "",
        document_no=po.get('po_number'),
        severity="warning"
    )
    
    return {"message": "Purchase order cancelled"}

# ==================== PURCHASE PAYMENTS ====================

from database import db
purchase_payments = db["purchase_payments"]
purchase_returns = db["purchase_returns"]
price_history = db["purchase_price_history"]

class PaymentCreate(BaseModel):
    po_id: str
    amount: float
    payment_method: str = "transfer"
    bank_id: str = ""
    reference: str = ""
    notes: str = ""

@router.get("/payments")
async def list_payments(search: str = "", user: dict = Depends(require_permission("pay_payable", "view"))):
    """List purchase payments - Requires pay_payable.view permission"""
    query = {}
    if search:
        query["$or"] = [
            {"payment_number": {"$regex": search, "$options": "i"}},
            {"po_number": {"$regex": search, "$options": "i"}}
        ]
    payments = await purchase_payments.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    return {"items": payments}

@router.post("/payments")
async def create_payment(data: PaymentCreate, request: Request, user: dict = Depends(require_permission("pay_payable", "create"))):
    """Create purchase payment - Requires pay_payable.create permission"""
    po = await purchase_orders.find_one({"id": data.po_id}, {"_id": 0})
    if not po:
        raise HTTPException(status_code=404, detail="PO tidak ditemukan")
    
    import uuid
    payment_number = f"PAY{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    payment = {
        "id": str(uuid.uuid4()),
        "payment_number": payment_number,
        "po_id": data.po_id,
        "po_number": po.get("po_number"),
        "supplier_id": po.get("supplier_id"),
        "supplier_name": po.get("supplier_name"),
        "amount": data.amount,
        "payment_method": data.payment_method,
        "bank_id": data.bank_id,
        "reference": data.reference,
        "notes": data.notes,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user.get("id")
    }
    await purchase_payments.insert_one(payment)
    
    # Audit log
    db_conn = get_db()
    await log_security_event(
        db_conn, user.get("user_id", ""), user.get("name", ""),
        "create", "pay_payable",
        f"Pembayaran {payment_number} sebesar Rp {data.amount:,.0f} untuk PO {po.get('po_number')}",
        request.client.host if request.client else "",
        document_no=payment_number
    )
    
    return {"id": payment["id"], "message": "Pembayaran berhasil dicatat"}

# ==================== PURCHASE RETURNS ====================

class ReturnItem(BaseModel):
    product_id: str
    quantity: int

class ReturnCreate(BaseModel):
    po_id: str
    reason: str
    items: List[ReturnItem]

@router.get("/returns")
async def list_returns(search: str = "", user: dict = Depends(require_permission("purchase_return", "view"))):
    """List purchase returns - Requires purchase_return.view permission"""
    query = {}
    if search:
        query["$or"] = [
            {"return_number": {"$regex": search, "$options": "i"}},
            {"po_number": {"$regex": search, "$options": "i"}}
        ]
    returns = await purchase_returns.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    return {"items": returns}

@router.post("/returns")
async def create_return(data: ReturnCreate, request: Request, user: dict = Depends(require_permission("purchase_return", "create"))):
    """Create purchase return - Requires purchase_return.create permission"""
    po = await purchase_orders.find_one({"id": data.po_id}, {"_id": 0})
    if not po:
        raise HTTPException(status_code=404, detail="PO tidak ditemukan")
    
    import uuid
    return_number = f"RTN{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    return_items = []
    total = 0
    
    for item in data.items:
        po_item = next((i for i in po.get("items", []) if i["product_id"] == item.product_id), None)
        if po_item:
            subtotal = item.quantity * po_item.get("unit_cost", 0)
            return_items.append({
                "product_id": item.product_id,
                "product_name": po_item.get("product_name"),
                "quantity": item.quantity,
                "unit_cost": po_item.get("unit_cost", 0),
                "subtotal": subtotal
            })
            total += subtotal
    
    retur = {
        "id": str(uuid.uuid4()),
        "return_number": return_number,
        "po_id": data.po_id,
        "po_number": po.get("po_number"),
        "supplier_id": po.get("supplier_id"),
        "supplier_name": po.get("supplier_name"),
        "reason": data.reason,
        "items": return_items,
        "total": total,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user.get("id")
    }
    await purchase_returns.insert_one(retur)
    
    # Audit log
    db_conn = get_db()
    await log_security_event(
        db_conn, user.get("user_id", ""), user.get("name", ""),
        "create", "purchase_return",
        f"Retur {return_number} dari PO {po.get('po_number')} sebesar Rp {total:,.0f}",
        request.client.host if request.client else "",
        document_no=return_number
    )
    
    return {"id": retur["id"], "message": "Retur berhasil dibuat"}

# ==================== PRICE HISTORY ====================

@router.get("/price-history")
async def list_price_history(
    search: str = "",
    product_id: str = "",
    user: dict = Depends(require_permission("purchase_price_history", "view"))
):
    """List price history - Requires purchase_price_history.view permission"""
    query = {}
    if product_id:
        query["product_id"] = product_id
    if search:
        query["product_name"] = {"$regex": search, "$options": "i"}
    
    history = await price_history.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    return {"items": history}
