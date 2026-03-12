# OCB TITAN - Owner Edit Control API
# Full edit control for owner with audit trail and data integrity
# USES: stock_ssot.py and recalculation_engine.py

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional, List, Any
from database import get_db
from utils.auth import get_current_user
from datetime import datetime, timezone
import uuid
import json

router = APIRouter(prefix="/owner", tags=["Owner Edit Control"])

# ==================== PERMISSION CHECK ====================

async def require_owner(user: dict = Depends(get_current_user)):
    """Check if user is owner or has full_edit permission"""
    allowed_roles = ["owner", "admin", "super_admin"]
    if user.get("role") not in allowed_roles:
        raise HTTPException(
            status_code=403, 
            detail="Hanya owner yang dapat melakukan operasi ini"
        )
    return user

# ==================== REQUEST MODELS ====================

class EditPORequest(BaseModel):
    supplier_id: Optional[str] = None
    expected_date: Optional[str] = None
    notes: Optional[str] = None
    items: Optional[List[dict]] = None
    discount_amount: Optional[float] = None
    tax_percent: Optional[float] = None

class EditPurchaseRequest(BaseModel):
    supplier_id: Optional[str] = None
    items: Optional[List[dict]] = None
    notes: Optional[str] = None

class EditSalesRequest(BaseModel):
    customer_id: Optional[str] = None
    items: Optional[List[dict]] = None
    notes: Optional[str] = None
    discount_amount: Optional[float] = None

class EditItemRequest(BaseModel):
    name: Optional[str] = None
    cost_price: Optional[float] = None
    selling_price: Optional[float] = None
    supplier_id: Optional[str] = None
    min_stock: Optional[int] = None
    max_stock: Optional[int] = None

class EditSupplierRequest(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    credit_limit: Optional[float] = None

class EditCustomerRequest(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    credit_limit: Optional[float] = None

class EditJournalRequest(BaseModel):
    description: Optional[str] = None
    entries: Optional[List[dict]] = None

# ==================== EDIT PURCHASE ORDER ====================

@router.put("/edit/purchase-order/{po_id}")
async def owner_edit_purchase_order(
    po_id: str,
    data: EditPORequest,
    request: Request,
    user: dict = Depends(require_owner)
):
    """
    Owner can edit PO - system will:
    1. Update PO data
    2. If received, recalculate stock movements
    3. Recalculate journal entries
    4. Recalculate AP
    5. Create audit log
    """
    db = get_db()
    from services.recalculation_engine import get_recalculation_engine
    engine = get_recalculation_engine(db)
    
    # Get current PO
    po = await db["purchase_orders"].find_one({"id": po_id}, {"_id": 0})
    if not po:
        raise HTTPException(status_code=404, detail="PO tidak ditemukan")
    
    old_value = po.copy()
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    
    # Update supplier
    if data.supplier_id:
        supplier = await db["suppliers"].find_one({"id": data.supplier_id}, {"_id": 0})
        if supplier:
            update_data["supplier_id"] = data.supplier_id
            update_data["supplier_name"] = supplier.get("name", "")
            update_data["supplier_code"] = supplier.get("code", "")
    
    # Update other fields
    if data.expected_date:
        update_data["expected_date"] = data.expected_date
    if data.notes is not None:
        update_data["notes"] = data.notes
    
    # Update items
    recalc_result = None
    if data.items is not None:
        po_items = []
        subtotal = 0
        
        for item in data.items:
            product = await db["products"].find_one({"id": item.get("product_id")}, {"_id": 0})
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
        
        # If PO is received, trigger full recalculation
        if po.get("status") in ["received", "partial"]:
            recalc_result = await engine.recalculate_purchase_order(
                po_id=po_id,
                new_items=po_items,
                new_total=total,
                branch_id=po.get("branch_id", ""),
                supplier_id=update_data.get("supplier_id", po.get("supplier_id", "")),
                supplier_name=update_data.get("supplier_name", po.get("supplier_name", "")),
                user_id=user.get("user_id", user.get("id", "")),
                user_name=user.get("name", ""),
                po_number=po.get("po_number", "")
            )
    
    # Update PO
    await db["purchase_orders"].update_one({"id": po_id}, {"$set": update_data})
    
    # Create audit log if no recalculation was done
    if not recalc_result:
        await engine.create_audit_log(
            user_id=user.get("user_id", user.get("id", "")),
            user_name=user.get("name", ""),
            action="update",
            module="purchase_order",
            record_id=po_id,
            old_value=old_value,
            new_value=update_data,
            description=f"Owner edit PO {po.get('po_number')}",
            ip_address=request.client.host if request.client else ""
        )
    
    updated_po = await db["purchase_orders"].find_one({"id": po_id}, {"_id": 0})
    
    return {
        "success": True,
        "message": "PO berhasil diupdate",
        "po": updated_po,
        "recalculation": recalc_result,
        "audit_logged": True
    }

# ==================== EDIT PURCHASE (RECEIVING) ====================

@router.put("/edit/purchase/{purchase_id}")
async def owner_edit_purchase(
    purchase_id: str,
    data: EditPurchaseRequest,
    request: Request,
    user: dict = Depends(require_owner)
):
    """
    Owner can edit purchase/receiving.
    System will recalculate: stock, AP, journal.
    """
    db = get_db()
    from services.recalculation_engine import get_recalculation_engine
    engine = get_recalculation_engine(db)
    
    purchase = await db["purchases"].find_one({"id": purchase_id}, {"_id": 0})
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase tidak ditemukan")
    
    old_value = purchase.copy()
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    
    if data.supplier_id:
        supplier = await db["suppliers"].find_one({"id": data.supplier_id}, {"_id": 0})
        if supplier:
            update_data["supplier_id"] = data.supplier_id
            update_data["supplier_name"] = supplier.get("name", "")
    
    if data.notes is not None:
        update_data["notes"] = data.notes
    
    recalc_result = None
    if data.items is not None:
        purchase_items = []
        subtotal = 0
        
        for item in data.items:
            product = await db["products"].find_one({"id": item.get("product_id")}, {"_id": 0})
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
        
        update_data["items"] = purchase_items
        update_data["subtotal"] = subtotal
        update_data["total"] = subtotal
        
        # Recalculate stock movements
        recalc_result = await engine.recalculate_stock_movements(
            reference_id=purchase_id,
            reference_no=purchase.get("purchase_no", ""),
            new_items=[
                {"item_id": i["product_id"], "quantity": i["quantity"], "unit_cost": i["unit_cost"]}
                for i in purchase_items
            ],
            movement_type="purchase_receive",
            branch_id=purchase.get("branch_id", ""),
            user_id=user.get("user_id", user.get("id", "")),
            user_name=user.get("name", ""),
            supplier_name=update_data.get("supplier_name", purchase.get("supplier_name", ""))
        )
        
        # Recalculate AP
        await engine.recalculate_payable(
            reference_id=purchase_id,
            supplier_id=update_data.get("supplier_id", purchase.get("supplier_id", "")),
            supplier_name=update_data.get("supplier_name", purchase.get("supplier_name", "")),
            new_amount=subtotal,
            user_id=user.get("user_id", user.get("id", ""))
        )
    
    await db["purchases"].update_one({"id": purchase_id}, {"$set": update_data})
    
    # Audit log
    await engine.create_audit_log(
        user_id=user.get("user_id", user.get("id", "")),
        user_name=user.get("name", ""),
        action="update",
        module="purchase",
        record_id=purchase_id,
        old_value=old_value,
        new_value=update_data,
        description=f"Owner edit purchase",
        ip_address=request.client.host if request.client else ""
    )
    
    return {
        "success": True,
        "message": "Purchase berhasil diupdate",
        "recalculation": recalc_result,
        "audit_logged": True
    }

# ==================== EDIT SALES ====================

@router.put("/edit/sales/{invoice_id}")
async def owner_edit_sales(
    invoice_id: str,
    data: EditSalesRequest,
    request: Request,
    user: dict = Depends(require_owner)
):
    """
    Owner can edit sales invoice.
    System will recalculate: stock (reverse), AR, journal.
    """
    db = get_db()
    from services.recalculation_engine import get_recalculation_engine
    engine = get_recalculation_engine(db)
    
    invoice = await db["sales_invoices"].find_one({"id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice tidak ditemukan")
    
    old_value = invoice.copy()
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    
    if data.customer_id:
        customer = await db["customers"].find_one({"id": data.customer_id}, {"_id": 0})
        if customer:
            update_data["customer_id"] = data.customer_id
            update_data["customer_name"] = customer.get("name", "")
    
    if data.notes is not None:
        update_data["notes"] = data.notes
    
    recalc_result = None
    if data.items is not None:
        invoice_items = []
        subtotal = 0
        total_hpp = 0
        
        for item in data.items:
            product = await db["products"].find_one({"id": item.get("product_id")}, {"_id": 0})
            qty = item.get("quantity", 0)
            price = item.get("unit_price", 0)
            cost = product.get("cost_price", 0) if product else 0
            item_subtotal = qty * price
            item_hpp = qty * cost
            
            invoice_items.append({
                "product_id": item.get("product_id"),
                "product_code": product.get("code", "") if product else "",
                "product_name": product.get("name", "") if product else "",
                "unit": product.get("unit", "PCS") if product else "PCS",
                "quantity": qty,
                "unit_price": price,
                "cost_price": cost,
                "subtotal": item_subtotal,
                "hpp": item_hpp
            })
            subtotal += item_subtotal
            total_hpp += item_hpp
        
        update_data["items"] = invoice_items
        update_data["subtotal"] = subtotal
        update_data["total_hpp"] = total_hpp
        
        discount = data.discount_amount if data.discount_amount is not None else invoice.get("discount_amount", 0)
        update_data["discount_amount"] = discount
        update_data["total"] = subtotal - discount
        
        # Full recalculation
        recalc_result = await engine.recalculate_sales_invoice(
            invoice_id=invoice_id,
            new_items=invoice_items,
            new_total=subtotal - discount,
            new_hpp=total_hpp,
            branch_id=invoice.get("branch_id", invoice.get("warehouse_id", "")),
            customer_id=update_data.get("customer_id", invoice.get("customer_id", "")),
            customer_name=update_data.get("customer_name", invoice.get("customer_name", "")),
            user_id=user.get("user_id", user.get("id", "")),
            user_name=user.get("name", ""),
            invoice_number=invoice.get("invoice_number", ""),
            is_credit=invoice.get("is_credit", False)
        )
    
    await db["sales_invoices"].update_one({"id": invoice_id}, {"$set": update_data})
    
    return {
        "success": True,
        "message": "Sales invoice berhasil diupdate",
        "recalculation": recalc_result,
        "audit_logged": True
    }

# ==================== EDIT ITEM/PRODUCT ====================

@router.put("/edit/item/{item_id}")
async def owner_edit_item(
    item_id: str,
    data: EditItemRequest,
    request: Request,
    user: dict = Depends(require_owner)
):
    """
    Owner can edit item/product.
    If cost changes, system will update inventory valuation.
    """
    db = get_db()
    from services.recalculation_engine import get_recalculation_engine
    engine = get_recalculation_engine(db)
    
    item = await db["products"].find_one({"id": item_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Item tidak ditemukan")
    
    old_value = item.copy()
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    
    if data.name:
        update_data["name"] = data.name
    if data.selling_price is not None:
        update_data["selling_price"] = data.selling_price
    if data.min_stock is not None:
        update_data["min_stock"] = data.min_stock
    if data.max_stock is not None:
        update_data["max_stock"] = data.max_stock
    
    if data.supplier_id:
        supplier = await db["suppliers"].find_one({"id": data.supplier_id}, {"_id": 0})
        if supplier:
            update_data["supplier_id"] = data.supplier_id
            update_data["supplier_name"] = supplier.get("name", "")
    
    # Handle cost price change with valuation recalculation
    valuation_result = None
    if data.cost_price is not None:
        update_data["cost_price"] = data.cost_price
        
        valuation_result = await engine.recalculate_item_valuation(
            item_id=item_id,
            new_cost=data.cost_price,
            user_id=user.get("user_id", user.get("id", "")),
            user_name=user.get("name", "")
        )
    
    await db["products"].update_one({"id": item_id}, {"$set": update_data})
    
    # Audit log
    await engine.create_audit_log(
        user_id=user.get("user_id", user.get("id", "")),
        user_name=user.get("name", ""),
        action="update",
        module="item",
        record_id=item_id,
        old_value=old_value,
        new_value=update_data,
        description=f"Owner edit item {item.get('name')}",
        ip_address=request.client.host if request.client else ""
    )
    
    return {
        "success": True,
        "message": "Item berhasil diupdate",
        "valuation": valuation_result,
        "audit_logged": True
    }

# ==================== EDIT SUPPLIER ====================

@router.put("/edit/supplier/{supplier_id}")
async def owner_edit_supplier(
    supplier_id: str,
    data: EditSupplierRequest,
    request: Request,
    user: dict = Depends(require_owner)
):
    """Owner can edit supplier"""
    db = get_db()
    from services.recalculation_engine import get_recalculation_engine
    engine = get_recalculation_engine(db)
    
    supplier = await db["suppliers"].find_one({"id": supplier_id}, {"_id": 0})
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier tidak ditemukan")
    
    old_value = supplier.copy()
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    
    if data.name:
        update_data["name"] = data.name
    if data.code:
        update_data["code"] = data.code
    if data.address:
        update_data["address"] = data.address
    if data.phone:
        update_data["phone"] = data.phone
    if data.email:
        update_data["email"] = data.email
    if data.credit_limit is not None:
        update_data["credit_limit"] = data.credit_limit
    
    await db["suppliers"].update_one({"id": supplier_id}, {"$set": update_data})
    
    # Audit log
    await engine.create_audit_log(
        user_id=user.get("user_id", user.get("id", "")),
        user_name=user.get("name", ""),
        action="update",
        module="supplier",
        record_id=supplier_id,
        old_value=old_value,
        new_value=update_data,
        description=f"Owner edit supplier {supplier.get('name')}",
        ip_address=request.client.host if request.client else ""
    )
    
    return {"success": True, "message": "Supplier berhasil diupdate", "audit_logged": True}

# ==================== EDIT CUSTOMER ====================

@router.put("/edit/customer/{customer_id}")
async def owner_edit_customer(
    customer_id: str,
    data: EditCustomerRequest,
    request: Request,
    user: dict = Depends(require_owner)
):
    """Owner can edit customer"""
    db = get_db()
    from services.recalculation_engine import get_recalculation_engine
    engine = get_recalculation_engine(db)
    
    customer = await db["customers"].find_one({"id": customer_id}, {"_id": 0})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer tidak ditemukan")
    
    old_value = customer.copy()
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    
    if data.name:
        update_data["name"] = data.name
    if data.code:
        update_data["code"] = data.code
    if data.address:
        update_data["address"] = data.address
    if data.phone:
        update_data["phone"] = data.phone
    if data.email:
        update_data["email"] = data.email
    if data.credit_limit is not None:
        update_data["credit_limit"] = data.credit_limit
    
    await db["customers"].update_one({"id": customer_id}, {"$set": update_data})
    
    # Audit log
    await engine.create_audit_log(
        user_id=user.get("user_id", user.get("id", "")),
        user_name=user.get("name", ""),
        action="update",
        module="customer",
        record_id=customer_id,
        old_value=old_value,
        new_value=update_data,
        description=f"Owner edit customer {customer.get('name')}",
        ip_address=request.client.host if request.client else ""
    )
    
    return {"success": True, "message": "Customer berhasil diupdate", "audit_logged": True}

# ==================== EDIT JOURNAL ====================

@router.put("/edit/journal/{journal_id}")
async def owner_edit_journal(
    journal_id: str,
    data: EditJournalRequest,
    request: Request,
    user: dict = Depends(require_owner)
):
    """
    Owner can edit journal entry.
    System will recalculate ledger entries.
    """
    db = get_db()
    from services.recalculation_engine import get_recalculation_engine
    engine = get_recalculation_engine(db)
    
    journal = await db["journal_entries"].find_one({"id": journal_id}, {"_id": 0})
    if not journal:
        raise HTTPException(status_code=404, detail="Journal tidak ditemukan")
    
    old_value = journal.copy()
    
    if data.entries is not None:
        # Validate balance
        total_debit = sum(e.get("debit", 0) for e in data.entries)
        total_credit = sum(e.get("credit", 0) for e in data.entries)
        
        if abs(total_debit - total_credit) > 0.01:
            raise HTTPException(
                status_code=400,
                detail=f"Journal tidak balance: Debit={total_debit}, Credit={total_credit}"
            )
        
        # Recalculate
        recalc_result = await engine.recalculate_journal(
            reference_id=journal.get("reference_id", journal_id),
            reference_no=journal.get("journal_number", journal.get("journal_no", "")),
            reference_type=journal.get("reference_type", "manual"),
            new_entries=data.entries,
            description=data.description or journal.get("description", ""),
            branch_id=journal.get("branch_id", ""),
            user_id=user.get("user_id", user.get("id", "")),
            user_name=user.get("name", "")
        )
        
        return {
            "success": True,
            "message": "Journal berhasil diupdate",
            "recalculation": recalc_result,
            "audit_logged": True
        }
    
    # Simple update without entries change
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if data.description:
        update_data["description"] = data.description
    
    await db["journal_entries"].update_one({"id": journal_id}, {"$set": update_data})
    
    # Audit log
    await engine.create_audit_log(
        user_id=user.get("user_id", user.get("id", "")),
        user_name=user.get("name", ""),
        action="update",
        module="journal",
        record_id=journal_id,
        old_value=old_value,
        new_value=update_data,
        description=f"Owner edit journal {journal.get('journal_number', journal.get('journal_no', ''))}",
        ip_address=request.client.host if request.client else ""
    )
    
    return {"success": True, "message": "Journal berhasil diupdate", "audit_logged": True}

# ==================== STOCK CARD (SINGLE SOURCE OF TRUTH) ====================

@router.get("/stock-card/{item_id}")
async def get_stock_card(
    item_id: str,
    branch_id: str = None,
    start_date: str = None,
    end_date: str = None,
    user: dict = Depends(get_current_user)
):
    """Get complete stock card from stock_movements (SINGLE SOURCE OF TRUTH)"""
    db = get_db()
    from services.stock_ssot import get_stock_ssot
    stock_ssot = get_stock_ssot(db)
    
    return await stock_ssot.get_stock_card(item_id, branch_id, start_date, end_date)

@router.get("/stock/{item_id}")
async def get_item_stock(
    item_id: str,
    branch_id: str = None,
    user: dict = Depends(get_current_user)
):
    """Get current stock from stock_movements (SINGLE SOURCE OF TRUTH)"""
    db = get_db()
    from services.stock_ssot import get_stock_ssot
    stock_ssot = get_stock_ssot(db)
    
    stock = await stock_ssot.get_stock(item_id, branch_id)
    
    # Get product info
    product = await db["products"].find_one({"id": item_id}, {"_id": 0, "code": 1, "name": 1})
    
    return {
        "item_id": item_id,
        "branch_id": branch_id,
        "stock": stock,
        "product_code": product.get("code", "") if product else "",
        "product_name": product.get("name", "") if product else "",
        "source": "stock_movements (SSOT)"
    }

@router.get("/stock-by-branch/{item_id}")
async def get_stock_by_branch(
    item_id: str,
    user: dict = Depends(get_current_user)
):
    """Get stock breakdown by branch from stock_movements"""
    db = get_db()
    from services.stock_ssot import get_stock_ssot
    stock_ssot = get_stock_ssot(db)
    
    branch_stocks = await stock_ssot.get_stock_by_branch(item_id)
    total_stock = await stock_ssot.get_stock(item_id)
    
    return {
        "item_id": item_id,
        "total_stock": total_stock,
        "branch_stocks": branch_stocks,
        "source": "stock_movements (SSOT)"
    }

# ==================== AUDIT LOG VIEWER ====================

@router.get("/audit-logs")
async def get_audit_logs(
    module: str = None,
    record_id: str = None,
    user_id: str = None,
    action: str = None,
    start_date: str = None,
    end_date: str = None,
    limit: int = 100,
    user: dict = Depends(require_owner)
):
    """Get audit logs - Owner only"""
    db = get_db()
    
    query = {}
    if module:
        query["module"] = module
    if record_id:
        query["record_id"] = record_id
    if user_id:
        query["user_id"] = user_id
    if action:
        query["action"] = action
    
    if start_date or end_date:
        query["timestamp"] = {}
        if start_date:
            query["timestamp"]["$gte"] = start_date
        if end_date:
            query["timestamp"]["$lt"] = end_date
    
    logs = await db["audit_logs"].find(query, {"_id": 0}).sort("timestamp", -1).limit(limit).to_list(limit)
    total = await db["audit_logs"].count_documents(query)
    
    return {"items": logs, "total": total}

@router.get("/audit-logs/{record_id}")
async def get_audit_log_detail(
    record_id: str,
    user: dict = Depends(require_owner)
):
    """Get audit log history for a specific record"""
    db = get_db()
    
    logs = await db["audit_logs"].find(
        {"record_id": record_id},
        {"_id": 0}
    ).sort("timestamp", -1).to_list(100)
    
    return {"record_id": record_id, "history": logs, "count": len(logs)}
