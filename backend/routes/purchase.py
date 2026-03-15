# OCB TITAN - Purchase Management API
# SECURITY: All operations require RBAC validation
# INTEGRATED: Account Derivation Engine from Setting Akun ERP
# INTEGRATED: Fiscal Period Validation & Multi-Currency Support
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional, List, Dict
from database import (
    purchase_orders, suppliers, products, product_stocks, 
    stock_movements, branches, get_next_sequence, get_db, db
)
from utils.auth import get_current_user
from models.titan_models import PurchaseOrder, PurchaseOrderItem, PurchaseStatus, StockMovement, StockMovementType, ProductStock
from routes.rbac_middleware import require_permission, log_security_event
from datetime import datetime, timezone
import uuid

router = APIRouter(prefix="/purchase", tags=["Purchase"])

# PRIORITAS 5: Serial Number Collection
serial_numbers = db.inventory_serial_numbers

# ==================== FISCAL PERIOD & MULTI-CURRENCY IMPORTS ====================
async def enforce_fiscal_period(transaction_date: str, action: str = "create"):
    """Enforce fiscal period validation"""
    from routes.erp_hardening import enforce_fiscal_period as _enforce
    return await _enforce(transaction_date, action)

async def get_exchange_rate(currency_code: str, transaction_date: str = None) -> float:
    """Get exchange rate for multi-currency"""
    from routes.erp_hardening import get_exchange_rate as _get_rate
    return await _get_rate(currency_code, transaction_date)

async def convert_to_base_currency(amount: float, currency_code: str, transaction_date: str = None) -> Dict:
    """Convert to base currency (IDR)"""
    from routes.erp_hardening import convert_to_base_currency as _convert
    return await _convert(amount, currency_code, transaction_date)

# ==================== ACCOUNT DERIVATION ENGINE ====================
# Default account settings for fallback (from Setting Akun ERP - Tab Pembelian)
DEFAULT_PURCHASE_ACCOUNTS = {
    "persediaan_barang": {"code": "1-1400", "name": "Persediaan Barang"},
    "pembayaran_kredit_pembelian": {"code": "2-1100", "name": "Hutang Dagang"},
    "pembayaran_tunai_pembelian": {"code": "1-1100", "name": "Kas"},
    "potongan_pembelian": {"code": "5-1100", "name": "Potongan Pembelian"},
    "ppn_masukan": {"code": "1-1500", "name": "PPN Masukan"},
    "biaya_lain_pembelian": {"code": "5-1200", "name": "Biaya Lain Pembelian"},
    "uang_muka_po": {"code": "1-1600", "name": "Uang Muka Pembelian"},
    "deposit_supplier": {"code": "2-1200", "name": "Deposit Supplier"},
    "retur_potongan_pembelian": {"code": "5-1100", "name": "Potongan Pembelian"},
    "retur_ppn_pembelian": {"code": "1-1500", "name": "PPN Masukan"},
}

async def derive_purchase_account(db, account_key: str, branch_id: str = None, 
                                  warehouse_id: str = None, category_id: str = None,
                                  payment_method: str = None) -> Dict[str, str]:
    """
    ACCOUNT DERIVATION ENGINE for Purchase Module
    Priority: Branch > Warehouse > Category > Payment > Global > Default
    """
    # Priority 1: Branch mapping
    if branch_id:
        mapping = await db.account_mapping_branch.find_one({
            "branch_id": branch_id, "account_key": account_key
        }, {"_id": 0})
        if mapping:
            return {"code": mapping["account_code"], "name": mapping["account_name"]}
    
    # Priority 2: Warehouse mapping
    if warehouse_id:
        mapping = await db.account_mapping_warehouse.find_one({
            "warehouse_id": warehouse_id, "account_key": account_key
        }, {"_id": 0})
        if mapping:
            return {"code": mapping["account_code"], "name": mapping["account_name"]}
    
    # Priority 3: Category mapping
    if category_id:
        mapping = await db.account_mapping_category.find_one({
            "category_id": category_id, "account_key": account_key
        }, {"_id": 0})
        if mapping:
            return {"code": mapping["account_code"], "name": mapping["account_name"]}
    
    # Priority 4: Payment method mapping
    if payment_method:
        mapping = await db.account_mapping_payment.find_one({
            "payment_method_id": payment_method, "account_key": account_key
        }, {"_id": 0})
        if mapping:
            return {"code": mapping["account_code"], "name": mapping["account_name"]}
    
    # Priority 5: Global setting from account_settings
    global_setting = await db.account_settings.find_one({
        "account_key": account_key
    }, {"_id": 0})
    if global_setting:
        return {"code": global_setting["account_code"], "name": global_setting["account_name"]}
    
    # Priority 6: Default fallback
    default = DEFAULT_PURCHASE_ACCOUNTS.get(account_key)
    if default:
        return default
    
    # Final fallback
    return {"code": "9-9999", "name": f"Unknown Account ({account_key})"}

class POItemInput(BaseModel):
    product_id: str
    product_name: Optional[str] = ""
    quantity: int
    unit_cost: float
    discount_percent: float = 0
    purchase_unit: Optional[str] = "pcs"  # Unit for purchase
    conversion_ratio: Optional[float] = 1  # Conversion to base unit
    sn_start: Optional[str] = ""  # Serial number start
    sn_end: Optional[str] = ""  # Serial number end

class POItemUpdate(BaseModel):
    product_id: str
    product_code: str = ""
    product_name: str = ""
    unit: str = "PCS"
    quantity: float
    unit_cost: float
    discount_percent: float = 0

class UpdateDraftPO(BaseModel):
    supplier_id: Optional[str] = None
    branch_id: Optional[str] = None
    expected_date: Optional[str] = None
    notes: Optional[str] = None
    items: Optional[List[POItemUpdate]] = None
    discount_amount: Optional[float] = None
    tax_percent: Optional[float] = None

class CreatePO(BaseModel):
    supplier_id: str
    branch_id: Optional[str] = None
    warehouse_id: Optional[str] = None  # Single warehouse for all items
    pic_id: Optional[str] = None  # Person in Charge
    payment_account_id: Optional[str] = None  # Cash/Bank account for payment
    items: List[POItemInput]
    expected_date: Optional[str] = None
    notes: str = ""
    total_amount: Optional[float] = None  # Calculated total
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

@router.put("/orders/{po_id}")
async def update_draft_purchase_order(
    po_id: str, 
    data: UpdateDraftPO, 
    request: Request, 
    user: dict = Depends(require_permission("purchase", "edit"))
):
    """Update draft PO - allows editing supplier, items, prices"""
    po = await purchase_orders.find_one({"id": po_id}, {"_id": 0})
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    
    if po.get("status") != "draft":
        raise HTTPException(status_code=400, detail="Hanya PO draft yang dapat diedit")
    
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    
    # Update supplier if provided
    if data.supplier_id:
        supplier = await suppliers.find_one({"id": data.supplier_id}, {"_id": 0})
        if supplier:
            update_data["supplier_id"] = data.supplier_id
            update_data["supplier_name"] = supplier.get("name", "")
            update_data["supplier_code"] = supplier.get("code", "")
    
    # Update other fields
    if data.branch_id:
        update_data["branch_id"] = data.branch_id
    if data.expected_date:
        update_data["expected_date"] = data.expected_date
    if data.notes is not None:
        update_data["notes"] = data.notes
    
    # Update items if provided
    if data.items is not None:
        po_items = []
        subtotal = 0
        
        for item in data.items:
            # Get product info if not provided
            product = await products.find_one({"id": item.product_id}, {"_id": 0})
            
            item_subtotal = item.unit_cost * item.quantity
            if item.discount_percent > 0:
                item_subtotal -= item_subtotal * (item.discount_percent / 100)
            
            po_items.append({
                "product_id": item.product_id,
                "product_code": item.product_code or (product.get("code", "") if product else ""),
                "product_name": item.product_name or (product.get("name", "") if product else ""),
                "unit": item.unit or (product.get("unit", "PCS") if product else "PCS"),
                "quantity": item.quantity,
                "unit_cost": item.unit_cost,
                "discount_percent": item.discount_percent,
                "subtotal": item_subtotal,
                "needs_price": item.unit_cost <= 0
            })
            subtotal += item_subtotal
        
        update_data["items"] = po_items
        update_data["total_items"] = len(po_items)
        update_data["total_qty"] = sum(i["quantity"] for i in po_items)
        update_data["subtotal"] = subtotal
        
        # Calculate total with discount and tax
        discount_amount = data.discount_amount if data.discount_amount is not None else po.get("discount_amount", 0)
        tax_percent = data.tax_percent if data.tax_percent is not None else po.get("tax_percent", 0)
        
        after_discount = subtotal - discount_amount
        tax_amount = after_discount * (tax_percent / 100) if tax_percent > 0 else 0
        total = after_discount + tax_amount
        
        update_data["discount_amount"] = discount_amount
        update_data["tax_percent"] = tax_percent
        update_data["tax_amount"] = tax_amount
        update_data["total"] = total
        
        # Check if still needs completion
        needs_completion = any(i.get("needs_price", False) for i in po_items)
        update_data["needs_completion"] = needs_completion
    
    await purchase_orders.update_one({"id": po_id}, {"$set": update_data})
    
    # Audit log
    db = get_db()
    await log_security_event(
        db, user.get("user_id", ""), user.get("name", ""),
        "edit", "purchase",
        f"Update draft PO {po.get('po_number')}",
        request.client.host if request.client else "",
        document_no=po.get('po_number')
    )
    
    # Get updated PO
    updated_po = await purchase_orders.find_one({"id": po_id}, {"_id": 0})
    
    return {
        "success": True,
        "message": "PO draft berhasil diupdate",
        "po": updated_po
    }

@router.get("/orders/{po_id}/print")
async def get_po_print_data(po_id: str, user: dict = Depends(require_permission("purchase", "view"))):
    """Get PO data formatted for printing"""
    po = await purchase_orders.find_one({"id": po_id}, {"_id": 0})
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    
    # Get supplier details
    supplier = None
    if po.get("supplier_id"):
        supplier = await suppliers.find_one({"id": po["supplier_id"]}, {"_id": 0})
    
    # Get branch details
    branch = None
    if po.get("branch_id"):
        branch = await branches.find_one({"id": po["branch_id"]}, {"_id": 0})
    
    # Format items for print
    print_items = []
    for idx, item in enumerate(po.get("items", [])):
        print_items.append({
            "no": idx + 1,
            "product_code": item.get("product_code", ""),
            "product_name": item.get("product_name", ""),
            "unit": item.get("unit", "PCS"),
            "quantity": item.get("quantity", 0),
            "unit_cost": item.get("unit_cost", 0),
            "discount_percent": item.get("discount_percent", 0),
            "subtotal": item.get("subtotal", 0)
        })
    
    return {
        "po_number": po.get("po_number") or po.get("po_no"),
        "status": po.get("status"),
        "created_at": po.get("created_at"),
        "order_date": po.get("order_date"),
        "expected_date": po.get("expected_date"),
        "supplier": {
            "id": po.get("supplier_id"),
            "name": po.get("supplier_name") or (supplier.get("name") if supplier else ""),
            "code": po.get("supplier_code") or (supplier.get("code") if supplier else ""),
            "address": supplier.get("address", "") if supplier else "",
            "phone": supplier.get("phone", "") if supplier else "",
            "email": supplier.get("email", "") if supplier else ""
        },
        "branch": {
            "id": po.get("branch_id"),
            "name": branch.get("name", "") if branch else "",
            "address": branch.get("address", "") if branch else ""
        },
        "items": print_items,
        "subtotal": po.get("subtotal", 0),
        "discount_amount": po.get("discount_amount", 0),
        "tax_percent": po.get("tax_percent", 0),
        "tax_amount": po.get("tax_amount", 0),
        "total": po.get("total", 0),
        "notes": po.get("notes", ""),
        "created_by_name": po.get("created_by_name", "")
    }

@router.post("/orders")
async def create_purchase_order(data: CreatePO, request: Request, user: dict = Depends(require_permission("purchase", "create"))):
    """Create purchase order - Requires purchase.create permission"""
    # ============================================================
    # VALIDATION: Mandatory fields per System Architect requirement
    # ============================================================
    if not data.supplier_id:
        raise HTTPException(status_code=400, detail="Supplier wajib dipilih")
    
    supplier = await suppliers.find_one({"id": data.supplier_id}, {"_id": 0})
    if not supplier:
        raise HTTPException(status_code=400, detail="Supplier tidak ditemukan")
    
    if not data.items or len(data.items) == 0:
        raise HTTPException(status_code=400, detail="Minimal harus ada 1 item pembelian")
    
    # Validate warehouse if provided
    warehouse_name = ""
    if data.warehouse_id:
        warehouse = await get_db().warehouses.find_one({"id": data.warehouse_id}, {"_id": 0})
        if warehouse:
            warehouse_name = warehouse.get("name", "")
    
    # Validate PIC if provided
    pic_name = ""
    if data.pic_id:
        employee = await get_db().employees.find_one({"id": data.pic_id}, {"_id": 0})
        if employee:
            pic_name = employee.get("name", "")
    
    # Validate payment account if provided
    payment_account_name = ""
    if data.payment_account_id:
        account = await get_db().chart_of_accounts.find_one({"id": data.payment_account_id}, {"_id": 0})
        if account:
            payment_account_name = f"{account.get('code', '')} - {account.get('name', '')}"
    
    branch_id = data.branch_id or user.get("branch_id")
    
    # Build items
    po_items = []
    subtotal = 0
    
    for item in data.items:
        product = await products.find_one({"id": item.product_id}, {"_id": 0})
        if not product:
            raise HTTPException(status_code=400, detail=f"Product tidak ditemukan: {item.product_id}")
        
        if item.quantity <= 0:
            raise HTTPException(status_code=400, detail=f"Jumlah item {product.get('name')} harus lebih dari 0")
        
        item_subtotal = item.unit_cost * item.quantity
        if item.discount_percent > 0:
            item_subtotal -= item_subtotal * (item.discount_percent / 100)
        
        po_item = PurchaseOrderItem(
            product_id=item.product_id,
            product_code=product.get("code", ""),
            product_name=item.product_name or product.get("name", ""),
            quantity=item.quantity,
            unit_cost=item.unit_cost,
            discount_percent=item.discount_percent,
            subtotal=item_subtotal,
            unit=item.purchase_unit or product.get("unit", "pcs"),
            conversion_ratio=item.conversion_ratio or 1,
            sn_start=item.sn_start or "",
            sn_end=item.sn_end or ""
        )
        
        po_items.append(po_item)
        subtotal += item_subtotal
    
    # Final total validation
    if subtotal <= 0:
        raise HTTPException(status_code=400, detail="Total pembelian harus lebih dari 0")
    
    po_number = await get_next_sequence("po_number", "PO")
    
    po = PurchaseOrder(
        po_number=po_number,
        supplier_id=data.supplier_id,
        supplier_name=supplier.get("name", ""),
        branch_id=branch_id,
        warehouse_id=data.warehouse_id or "",
        warehouse_name=warehouse_name,
        pic_id=data.pic_id or "",
        pic_name=pic_name,
        payment_account_id=data.payment_account_id or "",
        payment_account_name=payment_account_name,
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
    
    # VALIDATION GATE - tidak boleh submit jika data tidak valid
    validation_errors = []
    
    # Check supplier
    if not po.get("supplier_id") or po.get("supplier_name") in ["Unknown", "", None, "(Perlu dipilih)"]:
        validation_errors.append("Supplier tidak valid atau belum dipilih")
    
    # Check items
    if not po.get("items") or len(po.get("items", [])) == 0:
        validation_errors.append("Tidak ada item dalam PO")
    
    # Check items detail
    for idx, item in enumerate(po.get("items", [])):
        if item.get("quantity", 0) <= 0:
            validation_errors.append(f"Item #{idx+1} ({item.get('product_name', 'Unknown')}): qty harus > 0")
        if item.get("unit_cost", 0) <= 0:
            validation_errors.append(f"Item #{idx+1} ({item.get('product_name', 'Unknown')}): harga harus > 0")
    
    # Check total
    if po.get("total", 0) <= 0:
        validation_errors.append("Total PO harus > 0")
    
    if validation_errors:
        raise HTTPException(
            status_code=400, 
            detail={
                "message": "PO tidak dapat di-submit karena data belum lengkap",
                "errors": validation_errors
            }
        )
    
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
    
    # =============== FISCAL PERIOD VALIDATION ===============
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    await enforce_fiscal_period(today, "create")
    
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
                
                # Save price history
                price_record = {
                    "id": str(uuid.uuid4()),
                    "product_id": receive_item.product_id,
                    "product_code": po_item.get("product_code", ""),
                    "product_name": po_item.get("product_name", ""),
                    "supplier_id": po.get("supplier_id"),
                    "supplier_name": po.get("supplier_name", ""),
                    "po_number": po.get("po_number"),
                    "unit": po_item.get("unit", "PCS"),
                    "unit_cost": po_item.get("unit_cost", 0),
                    "quantity": receive_item.quantity,
                    "discount_percent": po_item.get("discount_percent", 0),
                    "date": datetime.now(timezone.utc).isoformat(),
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                await price_history.insert_one(price_record)
                
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
        # Using Account Derivation Engine from Setting Akun ERP
        # STANDARD FORMAT: journal_number + embedded entries
        journal_id = str(uuid.uuid4())
        
        # Generate standard journal number
        from utils.number_generator import generate_transaction_number
        journal_number = await generate_transaction_number(db, "JV-PUR")
        
        # Get warehouse info for category lookup
        warehouse_id = po.get("warehouse_id")
        
        # Derive accounts from Setting Akun ERP
        inventory_account = await derive_purchase_account(
            db, "persediaan_barang",
            branch_id=branch_id,
            warehouse_id=warehouse_id
        )
        ap_account = await derive_purchase_account(
            db, "pembayaran_kredit_pembelian",
            branch_id=branch_id,
            warehouse_id=warehouse_id
        )
        
        # Build embedded entries (STANDARD FORMAT)
        journal_entries_list = [
            {
                "account_code": inventory_account["code"],
                "account_name": inventory_account["name"],
                "debit": po_total,
                "credit": 0,
                "description": f"Persediaan dari {po.get('po_number')}"
            },
            {
                "account_code": ap_account["code"],
                "account_name": ap_account["name"],
                "debit": 0,
                "credit": po_total,
                "description": f"Hutang ke {po.get('supplier_name')}"
            }
        ]
        
        journal_entry = {
            "id": journal_id,
            "journal_number": journal_number,
            "journal_date": datetime.now(timezone.utc).isoformat(),
            "reference_type": "purchase_credit",
            "reference_id": po_id,
            "reference_number": po.get('po_number'),
            "description": f"Pembelian kredit {po.get('po_number')} dari {po.get('supplier_name')}",
            "entries": journal_entries_list,
            "total_debit": po_total,
            "total_credit": po_total,
            "is_balanced": True,
            "status": "posted",
            "branch_id": branch_id,
            "created_by": user.get("user_id", ""),
            "created_by_name": user.get("name", ""),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db["journal_entries"].insert_one(journal_entry)
    
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



# ==================== PRIORITAS 5: SERIAL NUMBER RANGE ====================

class SerialNumberRangeInput(BaseModel):
    item_id: str
    product_id: str
    sn_start: str
    sn_end: str
    purchase_id: Optional[str] = None

async def generate_serial_numbers(item_id: str, product_id: str, sn_start: str, sn_end: str, purchase_id: str = None):
    """
    PRIORITAS 5: Generate serial numbers from range
    Input: SN Awal = 10001, SN Akhir = 10010
    Output: [10001, 10002, 10003, ..., 10010]
    """
    try:
        start_num = int(sn_start)
        end_num = int(sn_end)
    except ValueError:
        # If not numeric, generate as string sequence
        generated = [sn_start]  # Just use as single SN
        return generated
    
    if end_num < start_num:
        raise ValueError("SN Akhir harus lebih besar dari SN Awal")
    
    if end_num - start_num > 1000:
        raise ValueError("Maksimal 1000 serial number per batch")
    
    generated_sns = []
    now = datetime.now(timezone.utc).isoformat()
    
    for num in range(start_num, end_num + 1):
        sn = str(num).zfill(len(sn_start))  # Maintain leading zeros
        sn_doc = {
            "id": str(uuid.uuid4()),
            "item_id": item_id,
            "product_id": product_id,
            "serial_number": sn,
            "purchase_id": purchase_id,
            "status": "available",  # available, sold, damaged, returned
            "created_at": now
        }
        generated_sns.append(sn_doc)
    
    # Insert all serial numbers
    if generated_sns:
        await serial_numbers.insert_many(generated_sns)
    
    return [sn["serial_number"] for sn in generated_sns]


@router.post("/serial-numbers/generate")
async def api_generate_serial_numbers(
    data: SerialNumberRangeInput,
    user: dict = Depends(require_permission("purchase", "create"))
):
    """
    PRIORITAS 5: Generate serial numbers from range
    
    Input:
    - sn_start: "10001"
    - sn_end: "10010"
    
    Output:
    - Generates serial numbers 10001, 10002, ..., 10010
    - Saves to inventory_serial_numbers collection
    """
    try:
        generated = await generate_serial_numbers(
            item_id=data.item_id,
            product_id=data.product_id,
            sn_start=data.sn_start,
            sn_end=data.sn_end,
            purchase_id=data.purchase_id
        )
        
        return {
            "success": True,
            "message": f"Berhasil generate {len(generated)} serial number",
            "count": len(generated),
            "serial_numbers": generated[:20],  # Return first 20 for display
            "sn_start": data.sn_start,
            "sn_end": data.sn_end
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/serial-numbers")
async def list_serial_numbers(
    product_id: str = "",
    purchase_id: str = "",
    status: str = "",
    limit: int = 100,
    user: dict = Depends(require_permission("purchase", "view"))
):
    """List serial numbers with filters"""
    query = {}
    if product_id:
        query["product_id"] = product_id
    if purchase_id:
        query["purchase_id"] = purchase_id
    if status:
        query["status"] = status
    
    sns = await serial_numbers.find(query, {"_id": 0}).sort("serial_number", 1).to_list(limit)
    total = await serial_numbers.count_documents(query)
    
    return {
        "items": sns,
        "total": total,
        "limit": limit
    }


@router.put("/serial-numbers/{sn_id}/status")
async def update_serial_number_status(
    sn_id: str,
    status: str,
    user: dict = Depends(require_permission("purchase", "edit"))
):
    """Update serial number status (sold, damaged, returned)"""
    valid_statuses = ["available", "sold", "damaged", "returned"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Status harus salah satu dari: {valid_statuses}")
    
    result = await serial_numbers.update_one(
        {"id": sn_id},
        {"$set": {"status": status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Serial number tidak ditemukan")
    
    return {"success": True, "message": f"Status diupdate ke {status}"}
