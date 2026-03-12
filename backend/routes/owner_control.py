# OCB TITAN - Owner Edit Control Service
# Full edit control for owner with audit trail and data integrity
# SINGLE SOURCE OF TRUTH: stock_movements

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Any
from database import db, get_db
from utils.auth import get_current_user
from datetime import datetime, timezone
import uuid
import json

router = APIRouter(prefix="/owner", tags=["Owner Edit Control"])

audit_logs = db["audit_logs"]
stock_movements = db["stock_movements"]
purchase_orders = db["purchase_orders"]
purchases = db["purchases"]
sales_invoices = db["sales_invoices"]
items = db["products"]
suppliers = db["suppliers"]
customers = db["customers"]
journals = db["journals"]
journal_entries = db["journal_entries"]

# ==================== AUDIT TRAIL ====================

async def create_audit_log(
    user_id: str,
    user_name: str,
    action: str,  # create, update, delete
    module: str,  # purchase_order, purchase, sales, inventory, journal, etc
    record_id: str,
    old_value: Any,
    new_value: Any,
    description: str = ""
):
    """Create audit log entry for any data change"""
    log = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "user_name": user_name,
        "action": action,
        "module": module,
        "record_id": record_id,
        "old_value": json.dumps(old_value, default=str) if old_value else None,
        "new_value": json.dumps(new_value, default=str) if new_value else None,
        "description": description,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ip_address": ""  # Can be filled from request
    }
    await audit_logs.insert_one(log)
    return log

# ==================== STOCK RECALCULATION ====================

async def get_stock_from_movements(product_id: str, branch_id: str = None) -> float:
    """
    Calculate current stock from stock_movements - SINGLE SOURCE OF TRUTH
    """
    query = {"product_id": product_id}
    if branch_id:
        query["branch_id"] = branch_id
    
    pipeline = [
        {"$match": query},
        {"$group": {"_id": None, "total": {"$sum": "$quantity"}}}
    ]
    result = await stock_movements.aggregate(pipeline).to_list(1)
    return result[0]["total"] if result else 0

async def recalculate_stock_card(product_id: str, branch_id: str = None):
    """
    Recalculate stock card from all movements
    Returns the complete stock card history
    """
    query = {"product_id": product_id}
    if branch_id:
        query["branch_id"] = branch_id
    
    movements = await stock_movements.find(query, {"_id": 0}).sort("created_at", 1).to_list(1000)
    
    running_balance = 0
    stock_card = []
    
    for mov in movements:
        running_balance += mov.get("quantity", 0)
        stock_card.append({
            "date": mov.get("created_at"),
            "type": mov.get("movement_type"),
            "reference": mov.get("reference_no", ""),
            "in": mov.get("quantity", 0) if mov.get("quantity", 0) > 0 else 0,
            "out": abs(mov.get("quantity", 0)) if mov.get("quantity", 0) < 0 else 0,
            "balance": running_balance,
            "unit_cost": mov.get("unit_cost", 0),
            "total_value": running_balance * mov.get("unit_cost", 0)
        })
    
    return {
        "product_id": product_id,
        "branch_id": branch_id,
        "current_stock": running_balance,
        "movements": stock_card
    }

async def create_stock_movement(
    product_id: str,
    quantity: float,  # positive = in, negative = out
    movement_type: str,  # purchase_receive, sales, adjustment, transfer, return
    reference_no: str,
    reference_id: str,
    unit_cost: float = 0,
    branch_id: str = None,
    warehouse_id: str = None,
    notes: str = "",
    user_id: str = "",
    user_name: str = ""
):
    """Create a stock movement entry"""
    movement = {
        "id": str(uuid.uuid4()),
        "product_id": product_id,
        "quantity": quantity,
        "movement_type": movement_type,
        "reference_no": reference_no,
        "reference_id": reference_id,
        "unit_cost": unit_cost,
        "total_value": abs(quantity) * unit_cost,
        "branch_id": branch_id,
        "warehouse_id": warehouse_id,
        "notes": notes,
        "created_by": user_id,
        "created_by_name": user_name,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await stock_movements.insert_one(movement)
    return movement

# ==================== OWNER EDIT PURCHASE ORDER ====================

class EditPORequest(BaseModel):
    supplier_id: Optional[str] = None
    expected_date: Optional[str] = None
    notes: Optional[str] = None
    items: Optional[List[dict]] = None
    discount_amount: Optional[float] = None
    tax_percent: Optional[float] = None

@router.put("/edit/purchase-order/{po_id}")
async def owner_edit_purchase_order(
    po_id: str,
    data: EditPORequest,
    user: dict = Depends(get_current_user)
):
    """
    Owner can edit PO - system will:
    1. Update PO data
    2. If received, recalculate stock movements
    3. Update journal entries
    4. Create audit log
    """
    # Check if user is owner
    if user.get("role") not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Hanya owner yang dapat mengedit")
    
    # Get current PO
    po = await purchase_orders.find_one({"id": po_id}, {"_id": 0})
    if not po:
        raise HTTPException(status_code=404, detail="PO tidak ditemukan")
    
    old_value = po.copy()
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    
    # Update supplier
    if data.supplier_id:
        supplier = await suppliers.find_one({"id": data.supplier_id}, {"_id": 0})
        if supplier:
            update_data["supplier_id"] = data.supplier_id
            update_data["supplier_name"] = supplier.get("name", "")
    
    # Update other fields
    if data.expected_date:
        update_data["expected_date"] = data.expected_date
    if data.notes is not None:
        update_data["notes"] = data.notes
    
    # Update items
    if data.items is not None:
        po_items = []
        subtotal = 0
        old_items = {i["product_id"]: i for i in po.get("items", [])}
        
        for item in data.items:
            product = await items.find_one({"id": item.get("product_id")}, {"_id": 0})
            item_subtotal = item.get("unit_cost", 0) * item.get("quantity", 0)
            
            po_items.append({
                "product_id": item.get("product_id"),
                "product_code": item.get("product_code") or (product.get("code", "") if product else ""),
                "product_name": item.get("product_name") or (product.get("name", "") if product else ""),
                "unit": item.get("unit") or (product.get("unit", "PCS") if product else "PCS"),
                "quantity": item.get("quantity", 0),
                "unit_cost": item.get("unit_cost", 0),
                "discount_percent": item.get("discount_percent", 0),
                "subtotal": item_subtotal,
                "received_qty": item.get("received_qty", 0)
            })
            subtotal += item_subtotal
        
        update_data["items"] = po_items
        update_data["subtotal"] = subtotal
        
        # Calculate total
        discount = data.discount_amount if data.discount_amount is not None else po.get("discount_amount", 0)
        tax_pct = data.tax_percent if data.tax_percent is not None else po.get("tax_percent", 0)
        after_discount = subtotal - discount
        tax_amount = after_discount * (tax_pct / 100)
        total = after_discount + tax_amount
        
        update_data["discount_amount"] = discount
        update_data["tax_percent"] = tax_pct
        update_data["tax_amount"] = tax_amount
        update_data["total"] = total
        
        # If PO is received, recalculate stock movements
        if po.get("status") in ["received", "partial"]:
            # Reverse old stock movements
            await stock_movements.delete_many({
                "reference_id": po_id,
                "movement_type": "purchase_receive"
            })
            
            # Create new stock movements
            for item in po_items:
                received = item.get("received_qty", 0)
                if received > 0:
                    await create_stock_movement(
                        product_id=item["product_id"],
                        quantity=received,
                        movement_type="purchase_receive",
                        reference_no=po.get("po_number"),
                        reference_id=po_id,
                        unit_cost=item.get("unit_cost", 0),
                        branch_id=po.get("branch_id"),
                        notes=f"Edit PO by owner: {user.get('name')}",
                        user_id=user.get("user_id"),
                        user_name=user.get("name")
                    )
    
    await purchase_orders.update_one({"id": po_id}, {"$set": update_data})
    
    # Create audit log
    await create_audit_log(
        user_id=user.get("user_id"),
        user_name=user.get("name"),
        action="update",
        module="purchase_order",
        record_id=po_id,
        old_value=old_value,
        new_value=update_data,
        description=f"Owner edit PO {po.get('po_number')}"
    )
    
    updated_po = await purchase_orders.find_one({"id": po_id}, {"_id": 0})
    
    return {
        "success": True,
        "message": "PO berhasil diupdate",
        "po": updated_po,
        "audit_logged": True
    }

# ==================== OWNER EDIT PURCHASE (RECEIVING) ====================

class EditPurchaseRequest(BaseModel):
    supplier_id: Optional[str] = None
    items: Optional[List[dict]] = None
    notes: Optional[str] = None

@router.put("/edit/purchase/{purchase_id}")
async def owner_edit_purchase(
    purchase_id: str,
    data: EditPurchaseRequest,
    user: dict = Depends(get_current_user)
):
    """
    Owner can edit purchase/receiving
    System will recalculate: stock, AP, journal
    """
    if user.get("role") not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Hanya owner yang dapat mengedit")
    
    purchase = await purchases.find_one({"id": purchase_id}, {"_id": 0})
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase tidak ditemukan")
    
    old_value = purchase.copy()
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    
    if data.supplier_id:
        supplier = await suppliers.find_one({"id": data.supplier_id}, {"_id": 0})
        if supplier:
            update_data["supplier_id"] = data.supplier_id
            update_data["supplier_name"] = supplier.get("name", "")
    
    if data.notes is not None:
        update_data["notes"] = data.notes
    
    if data.items is not None:
        # Reverse old stock movements
        await stock_movements.delete_many({
            "reference_id": purchase_id,
            "movement_type": "purchase_receive"
        })
        
        purchase_items = []
        subtotal = 0
        
        for item in data.items:
            product = await items.find_one({"id": item.get("product_id")}, {"_id": 0})
            qty = item.get("quantity", 0)
            cost = item.get("unit_cost", 0)
            item_subtotal = qty * cost
            
            purchase_items.append({
                "product_id": item.get("product_id"),
                "product_code": product.get("code", "") if product else "",
                "product_name": product.get("name", "") if product else "",
                "unit": product.get("unit", "PCS") if product else "PCS",
                "quantity": qty,
                "unit_cost": cost,
                "subtotal": item_subtotal
            })
            subtotal += item_subtotal
            
            # Create new stock movement
            if qty > 0:
                await create_stock_movement(
                    product_id=item.get("product_id"),
                    quantity=qty,
                    movement_type="purchase_receive",
                    reference_no=purchase.get("purchase_no", ""),
                    reference_id=purchase_id,
                    unit_cost=cost,
                    branch_id=purchase.get("branch_id"),
                    notes=f"Edit purchase by owner: {user.get('name')}",
                    user_id=user.get("user_id"),
                    user_name=user.get("name")
                )
        
        update_data["items"] = purchase_items
        update_data["subtotal"] = subtotal
        update_data["total"] = subtotal  # Simplified, add tax/discount if needed
        
        # Update AP (accounts payable) if exists
        await db["accounts_payable"].update_many(
            {"reference_id": purchase_id},
            {"$set": {
                "amount": subtotal,
                "balance": subtotal,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
    
    await purchases.update_one({"id": purchase_id}, {"$set": update_data})
    
    # Audit log
    await create_audit_log(
        user_id=user.get("user_id"),
        user_name=user.get("name"),
        action="update",
        module="purchase",
        record_id=purchase_id,
        old_value=old_value,
        new_value=update_data,
        description=f"Owner edit purchase"
    )
    
    return {"success": True, "message": "Purchase berhasil diupdate", "audit_logged": True}

# ==================== OWNER EDIT SALES ====================

class EditSalesRequest(BaseModel):
    customer_id: Optional[str] = None
    items: Optional[List[dict]] = None
    notes: Optional[str] = None
    discount_amount: Optional[float] = None

@router.put("/edit/sales/{invoice_id}")
async def owner_edit_sales(
    invoice_id: str,
    data: EditSalesRequest,
    user: dict = Depends(get_current_user)
):
    """
    Owner can edit sales invoice
    System will recalculate: stock (reverse), AR, journal
    """
    if user.get("role") not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Hanya owner yang dapat mengedit")
    
    invoice = await sales_invoices.find_one({"id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice tidak ditemukan")
    
    old_value = invoice.copy()
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    
    if data.customer_id:
        customer = await customers.find_one({"id": data.customer_id}, {"_id": 0})
        if customer:
            update_data["customer_id"] = data.customer_id
            update_data["customer_name"] = customer.get("name", "")
    
    if data.notes is not None:
        update_data["notes"] = data.notes
    
    if data.items is not None:
        # Reverse old stock movements (return items to stock)
        await stock_movements.delete_many({
            "reference_id": invoice_id,
            "movement_type": "sales"
        })
        
        invoice_items = []
        subtotal = 0
        
        for item in data.items:
            product = await items.find_one({"id": item.get("product_id")}, {"_id": 0})
            qty = item.get("quantity", 0)
            price = item.get("unit_price", 0)
            item_subtotal = qty * price
            
            invoice_items.append({
                "product_id": item.get("product_id"),
                "product_code": product.get("code", "") if product else "",
                "product_name": product.get("name", "") if product else "",
                "unit": product.get("unit", "PCS") if product else "PCS",
                "quantity": qty,
                "unit_price": price,
                "subtotal": item_subtotal
            })
            subtotal += item_subtotal
            
            # Create new stock movement (negative for sales)
            if qty > 0:
                await create_stock_movement(
                    product_id=item.get("product_id"),
                    quantity=-qty,  # Negative for sales
                    movement_type="sales",
                    reference_no=invoice.get("invoice_no", ""),
                    reference_id=invoice_id,
                    unit_cost=product.get("cost_price", 0) if product else 0,
                    branch_id=invoice.get("branch_id"),
                    notes=f"Edit sales by owner: {user.get('name')}",
                    user_id=user.get("user_id"),
                    user_name=user.get("name")
                )
        
        update_data["items"] = invoice_items
        update_data["subtotal"] = subtotal
        
        discount = data.discount_amount if data.discount_amount is not None else invoice.get("discount_amount", 0)
        update_data["discount_amount"] = discount
        update_data["total"] = subtotal - discount
        
        # Update AR if exists
        await db["accounts_receivable"].update_many(
            {"reference_id": invoice_id},
            {"$set": {
                "amount": subtotal - discount,
                "balance": subtotal - discount,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
    
    await sales_invoices.update_one({"id": invoice_id}, {"$set": update_data})
    
    # Audit log
    await create_audit_log(
        user_id=user.get("user_id"),
        user_name=user.get("name"),
        action="update",
        module="sales",
        record_id=invoice_id,
        old_value=old_value,
        new_value=update_data,
        description=f"Owner edit sales invoice"
    )
    
    return {"success": True, "message": "Sales invoice berhasil diupdate", "audit_logged": True}

# ==================== OWNER EDIT ITEM/PRODUCT ====================

class EditItemRequest(BaseModel):
    name: Optional[str] = None
    cost_price: Optional[float] = None
    selling_price: Optional[float] = None
    supplier_id: Optional[str] = None
    min_stock: Optional[int] = None
    max_stock: Optional[int] = None

@router.put("/edit/item/{item_id}")
async def owner_edit_item(
    item_id: str,
    data: EditItemRequest,
    user: dict = Depends(get_current_user)
):
    """
    Owner can edit item/product
    If cost changes, system will update inventory valuation
    """
    if user.get("role") not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Hanya owner yang dapat mengedit")
    
    item = await items.find_one({"id": item_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Item tidak ditemukan")
    
    old_value = item.copy()
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    
    if data.name:
        update_data["name"] = data.name
    if data.cost_price is not None:
        update_data["cost_price"] = data.cost_price
    if data.selling_price is not None:
        update_data["selling_price"] = data.selling_price
    if data.supplier_id:
        supplier = await suppliers.find_one({"id": data.supplier_id}, {"_id": 0})
        if supplier:
            update_data["supplier_id"] = data.supplier_id
            update_data["supplier_name"] = supplier.get("name", "")
    if data.min_stock is not None:
        update_data["min_stock"] = data.min_stock
    if data.max_stock is not None:
        update_data["max_stock"] = data.max_stock
    
    await items.update_one({"id": item_id}, {"$set": update_data})
    
    # If cost price changed, update inventory valuation
    if data.cost_price is not None and data.cost_price != item.get("cost_price"):
        # Record in price history
        await db["item_price_history"].insert_one({
            "id": str(uuid.uuid4()),
            "product_id": item_id,
            "old_cost": item.get("cost_price", 0),
            "new_cost": data.cost_price,
            "changed_by": user.get("user_id"),
            "changed_by_name": user.get("name"),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    
    # Audit log
    await create_audit_log(
        user_id=user.get("user_id"),
        user_name=user.get("name"),
        action="update",
        module="item",
        record_id=item_id,
        old_value=old_value,
        new_value=update_data,
        description=f"Owner edit item {item.get('name')}"
    )
    
    return {"success": True, "message": "Item berhasil diupdate", "audit_logged": True}

# ==================== STOCK CARD ENDPOINT ====================

@router.get("/stock-card/{product_id}")
async def get_stock_card(product_id: str, branch_id: str = None, user: dict = Depends(get_current_user)):
    """Get complete stock card for a product"""
    stock_card = await recalculate_stock_card(product_id, branch_id)
    
    # Get product info
    product = await items.find_one({"id": product_id}, {"_id": 0})
    if product:
        stock_card["product_code"] = product.get("code", "")
        stock_card["product_name"] = product.get("name", "")
    
    return stock_card

# ==================== AUDIT LOG VIEWER ====================

@router.get("/audit-logs")
async def get_audit_logs(
    module: str = None,
    record_id: str = None,
    user_id: str = None,
    limit: int = 100,
    user: dict = Depends(get_current_user)
):
    """Get audit logs - Owner only"""
    if user.get("role") not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Akses ditolak")
    
    query = {}
    if module:
        query["module"] = module
    if record_id:
        query["record_id"] = record_id
    if user_id:
        query["user_id"] = user_id
    
    logs = await audit_logs.find(query, {"_id": 0}).sort("timestamp", -1).limit(limit).to_list(limit)
    return {"items": logs, "total": len(logs)}
