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

class DeletePORequest(BaseModel):
    """Request body for PO deletion"""
    reason: str = ""  # Alasan penghapusan (optional/required based on policy)

# Delete mode constants
class DeleteMode:
    SOFT_DELETE = "SOFT_DELETE"  # For PO without any transaction impact
    CANCEL_HIDE = "CANCEL_HIDE"  # For PO with receiving/AP/journal impact

# ==================== PURCHASE ORDERS ====================

@router.get("/orders")
async def list_purchase_orders(
    status: str = "",
    supplier_id: str = "",
    search: str = "",  # Search by PO number, supplier name, notes
    include_deleted: bool = False,  # Filter untuk tampilkan deleted PO
    only_deleted: bool = False,  # Filter untuk hanya tampilkan deleted PO
    skip: int = 0,
    limit: int = 50,
    user: dict = Depends(require_permission("purchase", "view"))
):
    """
    List purchase orders - Requires purchase.view permission
    
    Filters:
    - status: Filter by PO status
    - search: Search by PO number, supplier name, or notes (case-insensitive)
    - include_deleted: false (default) = hide deleted, true = show all
    - only_deleted: true = show only deleted POs
    """
    query = {}
    
    # Default: exclude deleted POs (is_deleted != true)
    if only_deleted:
        query["is_deleted"] = True
    elif not include_deleted:
        query["$or"] = [
            {"is_deleted": {"$exists": False}},
            {"is_deleted": False}
        ]
    
    if status:
        # Support multiple statuses (comma-separated)
        if "," in status:
            status_list = [s.strip() for s in status.split(",")]
            if "$or" in query:
                # Combine with existing $or
                existing_or = query.pop("$or")
                query["$and"] = [
                    {"$or": existing_or},
                    {"status": {"$in": status_list}}
                ]
            else:
                query["status"] = {"$in": status_list}
        else:
            query["status"] = status
    
    if supplier_id:
        query["supplier_id"] = supplier_id
    
    # Search functionality - case insensitive
    if search:
        search_regex = {"$regex": search, "$options": "i"}
        search_conditions = [
            {"po_number": search_regex},
            {"supplier_name": search_regex},
            {"notes": search_regex}
        ]
        if "$and" in query:
            query["$and"].append({"$or": search_conditions})
        elif "$or" in query:
            existing_or = query.pop("$or")
            query["$and"] = [
                {"$or": existing_or},
                {"$or": search_conditions}
            ]
        else:
            query["$or"] = search_conditions
    
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
    """
    Update PO - allows editing for draft and ordered status
    
    EDIT POLICY (Blueprint v2.4.6):
    - BOLEH EDIT: draft, ordered (belum ada receiving/stock/AP/jurnal)
    - TIDAK BOLEH EDIT: partial, received, cancelled, deleted
    """
    po = await purchase_orders.find_one({"id": po_id}, {"_id": 0})
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    
    current_status = po.get("status", "").lower()
    
    # Editable statuses
    editable_statuses = ["draft", "ordered"]
    blocked_statuses = ["partial", "received", "cancelled", "deleted", "posted", "completed"]
    
    if current_status in blocked_statuses:
        reason_map = {
            "partial": "PO sudah ada penerimaan sebagian. Gunakan fitur Koreksi jika perlu perubahan.",
            "received": "PO sudah selesai diterima. Data tidak bisa diubah untuk menjaga integritas audit trail.",
            "cancelled": "PO sudah dibatalkan. Tidak bisa diedit.",
            "deleted": "PO sudah dihapus. Tidak bisa diedit.",
            "posted": "PO sudah di-post. Gunakan fitur Koreksi/Reversal.",
            "completed": "PO sudah selesai. Tidak bisa diedit."
        }
        raise HTTPException(status_code=400, detail=reason_map.get(current_status, f"Status {current_status} tidak dapat diedit"))
    
    if current_status not in editable_statuses:
        raise HTTPException(status_code=400, detail=f"Status '{current_status}' tidak dapat diedit")
    
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
    # TENANT GUARD: Get tenant from user context
    # ============================================================
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant tidak teridentifikasi")
    
    # ============================================================
    # VALIDATION: Mandatory fields per System Architect requirement
    # ============================================================
    if not data.supplier_id:
        raise HTTPException(status_code=400, detail="Supplier wajib dipilih")
    
    # TENANT GUARD: Query supplier (database context already tenant-scoped via JWT)
    # Note: Per-database multi-tenant - no tenant_id field needed in query
    supplier = await suppliers.find_one({"id": data.supplier_id}, {"_id": 0})
    if not supplier:
        raise HTTPException(status_code=400, detail="Supplier tidak ditemukan di tenant ini")
    
    if not data.items or len(data.items) == 0:
        raise HTTPException(status_code=400, detail="Minimal harus ada 1 item pembelian")
    
    # Validate warehouse if provided - TENANT GUARD
    # KONSOLIDASI: warehouse_id sekarang merujuk ke branches collection
    warehouse_name = ""
    if data.warehouse_id:
        # Query dari branches (source of truth setelah konsolidasi)
        branches_col = get_db()["branches"]
        warehouse = await branches_col.find_one({"id": data.warehouse_id}, {"_id": 0})
        if warehouse:
            warehouse_name = warehouse.get("name", "")
        else:
            raise HTTPException(status_code=400, detail="Cabang/Gudang tidak ditemukan")
    
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
        # TENANT GUARD: Query product (database context already tenant-scoped via JWT)
        # Note: Per-database multi-tenant - no tenant_id field needed in query
        product = await products.find_one({"id": item.product_id}, {"_id": 0})
        if not product:
            raise HTTPException(status_code=400, detail=f"Product tidak ditemukan di tenant ini: {item.product_id}")
        
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
        user_id=user.get("user_id", ""),
        tenant_id=tenant_id  # TENANT BINDING
    )
    
    # TENANT GUARD: Insert with explicit tenant_id
    po_data = po.model_dump()
    po_data["tenant_id"] = tenant_id  # Ensure tenant_id is set
    await purchase_orders.insert_one(po_data)
    
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
    
    # Allow receiving from submitted, ordered, or partial status
    if po.get("status") not in ["submitted", "ordered", "partial", "posted"]:
        raise HTTPException(status_code=400, detail="Cannot receive this PO - status must be submitted, ordered, partial, or posted")
    
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
                
                # Add to stock with WEIGHTED AVERAGE HPP calculation
                # Formula: new_hpp = (old_qty * old_hpp + new_qty * new_price) / (old_qty + new_qty)
                stock = await product_stocks.find_one(
                    {"product_id": receive_item.product_id, "branch_id": branch_id}
                )
                
                new_unit_cost = po_item.get("unit_cost", 0)
                
                if stock:
                    old_qty = stock.get("quantity", 0)
                    old_hpp = stock.get("unit_cost", 0)
                    new_qty = receive_item.quantity
                    
                    # WEIGHTED AVERAGE CALCULATION (iPOS-style)
                    if old_qty + new_qty > 0:
                        weighted_avg_hpp = ((old_qty * old_hpp) + (new_qty * new_unit_cost)) / (old_qty + new_qty)
                    else:
                        weighted_avg_hpp = new_unit_cost
                    
                    new_total_qty = old_qty + new_qty
                    new_total_value = new_total_qty * weighted_avg_hpp
                    
                    await product_stocks.update_one(
                        {"product_id": receive_item.product_id, "branch_id": branch_id},
                        {
                            "$inc": {"quantity": receive_item.quantity, "available": receive_item.quantity},
                            "$set": {
                                "unit_cost": round(weighted_avg_hpp, 2),
                                "total_value": round(new_total_value, 2),
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
                        unit_cost=new_unit_cost,
                        total_value=receive_item.quantity * new_unit_cost,
                        last_restock=datetime.now(timezone.utc).isoformat()
                    )
                    await product_stocks.insert_one(new_stock.model_dump())
                
                # Record stock movement - PROTECTION against duplicates
                # Check if this PO already has a quick_purchase movement (should skip for QPO)
                if po.get('is_quick_purchase', False):
                    # Skip creating another movement for Quick Purchase POs
                    continue
                
                # Check for existing movement to prevent duplicates
                existing_mov = await stock_movements.find_one({
                    "reference_id": po_id,
                    "product_id": receive_item.product_id,
                    "branch_id": branch_id,
                    "reference_type": "purchase_order"
                })
                
                if existing_mov:
                    # Movement already exists - skip
                    continue
                
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
    ap_no = None
    if all_received and po.get("is_credit", True):  # Default to credit
        from datetime import timedelta
        from routes.ap_system import generate_ap_number
        
        po_total = po.get("total", 0)
        credit_due_days = po.get("credit_due_days", 30)
        due_date = datetime.now(timezone.utc) + timedelta(days=credit_due_days)
        
        # Get branch code for AP number
        branch = await get_db()["branches"].find_one({"id": branch_id}, {"_id": 0})
        branch_code = branch.get("code", "HQ") if branch else "HQ"
        
        # Generate standardized AP number
        ap_no = await generate_ap_number(branch_code)
        
        # STANDARDIZED AP FORMAT (compatible with ap_system.py)
        ap_entry = {
            "id": str(uuid.uuid4()),
            "ap_no": ap_no,
            "ap_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "due_date": due_date.strftime("%Y-%m-%d"),
            "supplier_id": po.get("supplier_id"),
            "supplier_name": po.get("supplier_name", "Unknown"),
            "supplier_invoice_no": po.get("supplier_invoice_no", ""),
            "branch_id": branch_id,
            "source_type": "purchase",
            "source_id": po_id,
            "source_no": po.get("po_number"),
            "currency": "IDR",
            "original_amount": po_total,
            "paid_amount": 0,
            "outstanding_amount": po_total,
            "status": "open",
            "payment_term_days": credit_due_days,
            "notes": f"Hutang dari pembelian {po.get('po_number')}",
            "created_by": user.get("user_id", ""),
            "created_by_name": user.get("name", "System"),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
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


# ==================== REVERSAL ENGINE (WAJIB) ====================
# ATURAN: Tidak boleh hard delete jika sudah ada efek stok
# Semua koreksi HARUS lewat reversal
# Semua reversal HARUS masuk stock_movements
# P0: NO NEGATIVE STOCK + STOCK CHAIN DELETE PROTECTION

from utils.stock_validation import (
    StockValidationError,
    validate_stock_available,
    validate_stock_for_items,
    check_stock_chain_dependency,
    check_reversal_chain_for_transaction,
    validate_reversal_wont_cause_negative,
    validate_can_reverse_transaction,
    log_stock_validation_event
)

async def execute_stock_reversal(
    db,
    reference_id: str,
    reference_types: list,
    reversal_type: str,
    reversal_note: str,
    user_id: str,
    user_name: str,
    skip_validation: bool = False  # For emergency use only
) -> dict:
    """
    REVERSAL ENGINE - Core function untuk membalikkan stock movements
    
    P0 VALIDATIONS:
    1. Check stock chain dependency (no subsequent transactions)
    2. Check reversal won't cause negative stock
    
    Args:
        db: Database instance
        reference_id: ID transaksi yang akan di-reverse
        reference_types: List of reference_type yang akan di-reverse
        reversal_type: Type untuk reversal entry
        reversal_note: Catatan untuk reversal
        user_id: User yang melakukan reversal
        user_name: Nama user
        skip_validation: Skip validation (DANGEROUS - for emergency only)
    
    Returns:
        dict dengan info reversal yang dilakukan
    
    Raises:
        HTTPException jika validasi gagal
    """
    now = datetime.now(timezone.utc).isoformat()
    
    # ============ P0 VALIDATION: STOCK CHAIN + NO NEGATIVE ============
    if not skip_validation:
        try:
            await validate_can_reverse_transaction(db, reference_id, reference_types)
        except StockValidationError as e:
            # Log blocked action
            await log_stock_validation_event(
                db, user_id, user_name,
                "REVERSAL_BLOCKED",
                success=False,
                details={
                    "reference_id": reference_id,
                    "error_code": e.error_code,
                    "error_message": e.message,
                    "error_details": e.details
                }
            )
            raise HTTPException(
                status_code=400,
                detail={
                    "error": e.message,
                    "error_code": e.error_code,
                    "details": e.details
                }
            )
    
    # Find all movements to reverse
    movements = await db["stock_movements"].find({
        "reference_id": reference_id,
        "reference_type": {"$in": reference_types},
        # Exclude already reversed movements
        "is_reversed": {"$ne": True}
    }).to_list(1000)
    
    if not movements:
        return {
            "success": True,
            "message": "No movements to reverse",
            "movements_reversed": 0,
            "total_qty_reversed": 0
        }
    
    reversals_created = []
    total_qty_reversed = 0
    
    for mov in movements:
        original_qty = mov.get("quantity", mov.get("qty", 0))
        product_id = mov.get("product_id") or mov.get("item_id")
        branch_id = mov.get("branch_id")
        
        # Create reversal entry (qty dibalikkan)
        reversal = {
            "id": str(uuid.uuid4()),
            "product_id": product_id,
            "item_id": mov.get("item_id"),  # Backward compatibility
            "product_name": mov.get("product_name", ""),
            "branch_id": branch_id,
            "movement_type": "reversal",
            "quantity": -original_qty,  # BALIKKAN QTY
            "reference_type": reversal_type,
            "reference_id": reference_id,
            "reference_number": f"REV-{mov.get('reference_number', mov.get('reference_no', str(mov.get('_id'))[:8]))}",
            "reversed_movement_id": str(mov.get("_id")),
            "notes": reversal_note,
            "is_reversal": True,
            "created_by": user_id,
            "created_by_name": user_name,
            "created_at": now
        }
        
        await db["stock_movements"].insert_one(reversal)
        
        # Mark original movement as reversed
        await db["stock_movements"].update_one(
            {"_id": mov.get("_id")},
            {"$set": {
                "is_reversed": True,
                "reversed_at": now,
                "reversed_by": user_id,
                "reversal_id": reversal["id"]
            }}
        )
        
        # Update product_stocks (kurangi stok)
        if product_id and branch_id:
            await db["product_stocks"].update_one(
                {"product_id": product_id, "branch_id": branch_id},
                {"$inc": {"quantity": -original_qty, "available": -original_qty}},
                upsert=True
            )
        
        reversals_created.append({
            "original_movement_id": str(mov.get("_id")),
            "reversal_id": reversal["id"],
            "product_id": product_id,
            "branch_id": branch_id,
            "original_qty": original_qty,
            "reversed_qty": -original_qty
        })
        
        total_qty_reversed += abs(original_qty)
    
    return {
        "success": True,
        "message": f"Reversed {len(reversals_created)} movements",
        "movements_reversed": len(reversals_created),
        "total_qty_reversed": total_qty_reversed,
        "reversals": reversals_created
    }


# ==================== SAFE DELETE WITH REVERSAL ====================

@router.delete("/orders/{po_id}")
async def delete_purchase_order(
    po_id: str, 
    request: Request, 
    reason: str = "",
    user: dict = Depends(require_permission("purchase", "delete"))
):
    """
    REVERSAL-BASED Delete Purchase Order
    
    ⚠️ ATURAN BARU:
    - Jika PO sudah memiliki efek stok → WAJIB REVERSAL
    - Tidak boleh hard delete jika sudah ada stock_movements
    - Semua perubahan stok harus melalui reversal entries
    
    DELETE FLOW:
    1. Cek apakah ada stock movements terkait
    2. Jika ada → Execute REVERSAL ENGINE
    3. Update status PO menjadi "reversed" atau "deleted"
    4. Log audit trail
    """
    db = get_db()
    user_id = user.get("user_id", user.get("id", ""))
    user_name = user.get("name", "")
    now = datetime.now(timezone.utc).isoformat()
    
    # Get PO
    po = await purchase_orders.find_one({"id": po_id}, {"_id": 0})
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order tidak ditemukan")
    
    # Check if already deleted/reversed
    if po.get("is_deleted"):
        raise HTTPException(status_code=400, detail="Purchase order sudah dihapus sebelumnya")
    
    if po.get("status") == "reversed":
        raise HTTPException(status_code=400, detail="Purchase order sudah di-reverse sebelumnya")
    
    old_status = po.get("status")
    po_number = po.get("po_number", po_id)
    is_quick_purchase = po.get("is_quick_purchase", False)
    
    # ============ CHECK STOCK IMPACT ============
    # Cek movements dari PO biasa DAN Quick Purchase
    reference_types = ["purchase_order", "purchase_receive"]
    if is_quick_purchase:
        reference_types.append("quick_purchase")
    
    movement_count = await stock_movements.count_documents({
        "reference_id": po_id,
        "reference_type": {"$in": reference_types},
        "is_reversed": {"$ne": True}  # Exclude already reversed
    })
    
    has_stock_movement = movement_count > 0
    
    # Check other impacts
    has_receiving = any(item.get("received_qty", 0) > 0 for item in po.get("items", []))
    
    ap_collection = db["accounts_payable"]
    ap_count = await ap_collection.count_documents({"po_id": po_id})
    has_ap_record = ap_count > 0
    
    journal_collection = db["journal_entries"]
    journal_count = await journal_collection.count_documents({
        "$or": [{"reference_id": po_id}, {"reference_no": po_number}]
    })
    has_journal = journal_count > 0
    
    # ============ EXECUTE REVERSAL IF NEEDED ============
    reversal_result = None
    
    if has_stock_movement:
        # WAJIB REVERSAL - tidak boleh delete tanpa reversal
        reversal_result = await execute_stock_reversal(
            db=db,
            reference_id=po_id,
            reference_types=reference_types,
            reversal_type="purchase_reversal",
            reversal_note=f"AUTO REVERSAL DELETE {'Quick Purchase' if is_quick_purchase else 'PO'}: {po_number}. Reason: {reason or 'Deleted by user'}",
            user_id=user_id,
            user_name=user_name
        )
        
        new_status = "reversed"
        delete_mode = "REVERSAL_DELETE"
        audit_action = "PO_REVERSAL_DELETE"
        message = f"{'Quick Purchase' if is_quick_purchase else 'PO'} {po_number} berhasil di-reverse dan dihapus. {reversal_result.get('movements_reversed', 0)} movements reversed, total qty: {reversal_result.get('total_qty_reversed', 0)}"
    
    elif has_receiving or has_ap_record or has_journal:
        # Ada impact lain selain stock → CANCEL_HIDE
        new_status = "cancelled"
        delete_mode = "CANCEL_HIDE"
        audit_action = "PO_CANCEL_HIDE"
        message = f"PO {po_number} dibatalkan (cancel_hide - transaksi tetap tersimpan untuk audit)"
    
    else:
        # Tidak ada impact → SOFT_DELETE
        new_status = "deleted"
        delete_mode = "SOFT_DELETE"
        audit_action = "PO_SOFT_DELETED"
        message = f"PO {po_number} berhasil dihapus"
    
    # ============ UPDATE PO ============
    update_data = {
        "is_deleted": True,
        "status": new_status,
        "delete_mode": delete_mode,
        "delete_reason": reason,
        "deleted_at": now,
        "deleted_by": user_id,
        "deleted_by_name": user_name,
        "updated_at": now
    }
    
    if reversal_result:
        update_data["reversal_info"] = {
            "executed_at": now,
            "executed_by": user_id,
            "movements_reversed": reversal_result.get("movements_reversed", 0),
            "total_qty_reversed": reversal_result.get("total_qty_reversed", 0)
        }
    
    await purchase_orders.update_one({"id": po_id}, {"$set": update_data})
    
    # ============ AUDIT LOG ============
    await log_security_event(
        db, user_id, user_name,
        "delete", "purchase",
        f"{audit_action}: {po_number} | Mode: {delete_mode} | Old Status: {old_status} | Reason: {reason or 'No reason provided'} | Movements Reversed: {reversal_result.get('movements_reversed', 0) if reversal_result else 0}",
        request.client.host if request.client else "",
        document_no=po_number,
        severity="warning"
    )
    
    # Save detailed audit record
    audit_detail = {
        "id": str(uuid.uuid4()),
        "event_type": audit_action,
        "tenant_id": db.name,
        "po_id": po_id,
        "po_number": po_number,
        "is_quick_purchase": is_quick_purchase,
        "user_id": user_id,
        "user_name": user_name,
        "timestamp": now,
        "old_status": old_status,
        "new_status": new_status,
        "delete_mode": delete_mode,
        "reason": reason,
        "impact_check": {
            "has_receiving": has_receiving,
            "has_stock_movement": has_stock_movement,
            "has_ap_record": has_ap_record,
            "has_journal": has_journal
        },
        "reversal_info": reversal_result,
        "ip_address": request.client.host if request.client else ""
    }
    
    audit_logs = db["audit_logs"]
    await audit_logs.insert_one(audit_detail)
    
    return {
        "success": True,
        "message": message,
        "po_number": po_number,
        "is_quick_purchase": is_quick_purchase,
        "delete_mode": delete_mode,
        "old_status": old_status,
        "new_status": new_status,
        "reversal_info": reversal_result,
        "impact_preserved": has_receiving or has_ap_record or has_journal
    }


@router.get("/orders/{po_id}/delete-preview")
async def preview_delete_po(
    po_id: str,
    user: dict = Depends(require_permission("purchase", "view"))
):
    """
    Preview what will happen if PO is deleted/reversed
    Shows impact analysis before actual deletion
    
    ⚠️ PENTING: Jika ada stock movements, sistem akan otomatis
    melakukan REVERSAL saat delete
    """
    db = get_db()
    
    po = await purchase_orders.find_one({"id": po_id}, {"_id": 0})
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order tidak ditemukan")
    
    po_number = po.get("po_number", po_id)
    is_quick_purchase = po.get("is_quick_purchase", False)
    
    # Check impacts
    has_receiving = any(item.get("received_qty", 0) > 0 for item in po.get("items", []))
    
    # Check movements - termasuk quick_purchase
    reference_types = ["purchase_order", "purchase_receive"]
    if is_quick_purchase:
        reference_types.append("quick_purchase")
    
    movements = await stock_movements.find({
        "reference_id": po_id,
        "reference_type": {"$in": reference_types},
        "is_reversed": {"$ne": True}
    }).to_list(100)
    
    movement_count = len(movements)
    total_movement_qty = sum(m.get("quantity", m.get("qty", 0)) for m in movements)
    
    ap_collection = db["accounts_payable"]
    ap_count = await ap_collection.count_documents({"po_id": po_id})
    
    journal_collection = db["journal_entries"]
    journal_count = await journal_collection.count_documents({
        "$or": [{"reference_id": po_id}, {"reference_no": po_number}]
    })
    
    has_any_impact = has_receiving or movement_count > 0 or ap_count > 0 or journal_count > 0
    
    # Determine what will happen
    if movement_count > 0:
        delete_mode = "REVERSAL_DELETE"
        action_description = f"Sistem akan membuat {movement_count} REVERSAL entries untuk mengembalikan stok. Total qty yang akan di-reverse: {total_movement_qty}"
        warning = "⚠️ STOK AKAN DIKEMBALIKAN KE KONDISI SEBELUM TRANSAKSI INI"
    elif has_receiving or ap_count > 0 or journal_count > 0:
        delete_mode = "CANCEL_HIDE"
        action_description = "PO akan di-cancel dan disembunyikan dari daftar aktif. Data tetap tersimpan untuk audit."
        warning = None
    else:
        delete_mode = "SOFT_DELETE"
        action_description = "PO akan dihapus karena tidak memiliki efek transaksi apapun."
        warning = None
    
    # Detail movements yang akan di-reverse
    movements_detail = []
    for m in movements:
        movements_detail.append({
            "product_id": m.get("product_id") or m.get("item_id"),
            "product_name": m.get("product_name", ""),
            "branch_id": m.get("branch_id"),
            "quantity": m.get("quantity", m.get("qty", 0)),
            "reference_type": m.get("reference_type"),
            "created_at": str(m.get("created_at", ""))
        })
    
    return {
        "po_id": po_id,
        "po_number": po_number,
        "current_status": po.get("status"),
        "is_quick_purchase": is_quick_purchase,
        "can_delete": True,
        "delete_mode": delete_mode,
        "action_description": action_description,
        "warning": warning,
        "impacts": {
            "has_receiving": has_receiving,
            "has_stock_movement": movement_count > 0,
            "movement_count": movement_count,
            "total_movement_qty": total_movement_qty,
            "has_ap_record": ap_count > 0,
            "ap_count": ap_count,
            "has_journal": journal_count > 0,
            "journal_count": journal_count
        },
        "movements_to_reverse": movements_detail if delete_mode == "REVERSAL_DELETE" else []
    }


@router.post("/orders/{po_id}/reverse")
async def reverse_purchase_order(
    po_id: str,
    request: Request,
    reason: str = "",
    user: dict = Depends(require_permission("purchase", "delete"))
):
    """
    EXPLICIT REVERSAL - Membalikkan semua efek stok dari PO/Quick Purchase
    
    Gunakan endpoint ini untuk:
    1. Membatalkan transaksi yang sudah posted
    2. Mengembalikan stok ke kondisi sebelumnya
    3. Menjaga audit trail yang lengkap
    
    ⚠️ ATURAN:
    - PO dengan status "posted" TIDAK boleh dihapus, HARUS di-reverse
    - Semua reversal masuk ke stock_movements
    - Stok akan dikembalikan otomatis
    """
    db = get_db()
    user_id = user.get("user_id", user.get("id", ""))
    user_name = user.get("name", "")
    now = datetime.now(timezone.utc).isoformat()
    
    # Get PO
    po = await purchase_orders.find_one({"id": po_id}, {"_id": 0})
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order tidak ditemukan")
    
    # Check if already reversed
    if po.get("status") == "reversed":
        raise HTTPException(status_code=400, detail="Purchase order sudah di-reverse sebelumnya")
    
    old_status = po.get("status")
    po_number = po.get("po_number", po_id)
    is_quick_purchase = po.get("is_quick_purchase", False)
    
    # Determine reference types to reverse
    reference_types = ["purchase_order", "purchase_receive"]
    if is_quick_purchase:
        reference_types.append("quick_purchase")
    
    # Check if there are movements to reverse
    movement_count = await stock_movements.count_documents({
        "reference_id": po_id,
        "reference_type": {"$in": reference_types},
        "is_reversed": {"$ne": True}
    })
    
    if movement_count == 0:
        raise HTTPException(
            status_code=400, 
            detail="Tidak ada stock movements untuk di-reverse. Gunakan endpoint delete untuk menghapus PO ini."
        )
    
    # Execute reversal
    reversal_result = await execute_stock_reversal(
        db=db,
        reference_id=po_id,
        reference_types=reference_types,
        reversal_type="purchase_reversal",
        reversal_note=f"MANUAL REVERSAL {'Quick Purchase' if is_quick_purchase else 'PO'}: {po_number}. Reason: {reason or 'User requested reversal'}",
        user_id=user_id,
        user_name=user_name
    )
    
    # Update PO status
    update_data = {
        "status": "reversed",
        "reversed_at": now,
        "reversed_by": user_id,
        "reversed_by_name": user_name,
        "reversal_reason": reason,
        "reversal_info": {
            "executed_at": now,
            "executed_by": user_id,
            "movements_reversed": reversal_result.get("movements_reversed", 0),
            "total_qty_reversed": reversal_result.get("total_qty_reversed", 0)
        },
        "updated_at": now
    }
    
    await purchase_orders.update_one({"id": po_id}, {"$set": update_data})
    
    # Audit log
    await log_security_event(
        db, user_id, user_name,
        "reverse", "purchase",
        f"PO_REVERSED: {po_number} | Old Status: {old_status} | Movements Reversed: {reversal_result.get('movements_reversed', 0)} | Total Qty: {reversal_result.get('total_qty_reversed', 0)} | Reason: {reason or 'User requested'}",
        request.client.host if request.client else "",
        document_no=po_number,
        severity="warning"
    )
    
    return {
        "success": True,
        "message": f"{'Quick Purchase' if is_quick_purchase else 'PO'} {po_number} berhasil di-reverse",
        "po_number": po_number,
        "is_quick_purchase": is_quick_purchase,
        "old_status": old_status,
        "new_status": "reversed",
        "reversal_info": reversal_result
    }


@router.get("/orders/{po_id}/reversal-preview")
async def preview_reversal_po(
    po_id: str,
    user: dict = Depends(require_permission("purchase", "view"))
):
    """
    Preview what will happen if PO is reversed
    Shows impact analysis and movements that will be reversed
    
    PENTING: Endpoint ini menampilkan preview sebelum melakukan reversal
    """
    db = get_db()
    
    po = await purchase_orders.find_one({"id": po_id}, {"_id": 0})
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order tidak ditemukan")
    
    po_number = po.get("po_number", po_id)
    is_quick_purchase = po.get("is_quick_purchase", False)
    
    # Check if already reversed
    if po.get("status") == "reversed":
        return {
            "po_id": po_id,
            "po_number": po_number,
            "can_reverse": False,
            "message": "PO sudah di-reverse sebelumnya",
            "current_status": "reversed"
        }
    
    # Check movements - termasuk quick_purchase
    reference_types = ["purchase_order", "purchase_receive"]
    if is_quick_purchase:
        reference_types.append("quick_purchase")
    
    movements = await stock_movements.find({
        "reference_id": po_id,
        "reference_type": {"$in": reference_types},
        "is_reversed": {"$ne": True}
    }).to_list(100)
    
    movement_count = len(movements)
    total_movement_qty = sum(m.get("quantity", m.get("qty", 0)) for m in movements)
    
    # Detail movements
    movements_detail = []
    for m in movements:
        movements_detail.append({
            "movement_id": str(m.get("_id")),
            "product_id": m.get("product_id") or m.get("item_id"),
            "product_name": m.get("product_name", ""),
            "branch_id": m.get("branch_id"),
            "quantity": m.get("quantity", m.get("qty", 0)),
            "reference_type": m.get("reference_type"),
            "will_reverse_to": -(m.get("quantity", m.get("qty", 0))),
            "created_at": str(m.get("created_at", ""))
        })
    
    return {
        "po_id": po_id,
        "po_number": po_number,
        "current_status": po.get("status"),
        "is_quick_purchase": is_quick_purchase,
        "can_reverse": movement_count > 0,
        "message": f"Ada {movement_count} movements yang akan di-reverse dengan total qty {total_movement_qty}" if movement_count > 0 else "Tidak ada movements untuk di-reverse",
        "preview": {
            "movements_to_reverse": movement_count,
            "total_qty_to_reverse": total_movement_qty,
            "new_status_after_reverse": "reversed"
        },
        "movements_detail": movements_detail
    }


# ==================== FULL PURCHASE REVERSAL SYSTEM - EXTENDED ====================
# ENTERPRISE RULE: Transaksi Posted TIDAK boleh di-delete, harus di-REVERSE
# Reversal mengembalikan semua efek bisnis ke kondisi sebelum transaksi terjadi

class PurchaseReversalRequest(BaseModel):
    """Request untuk reversal purchase order"""
    reason: str
    notes: Optional[str] = None


@router.get("/orders/{po_id}/reversal-impact")
async def preview_purchase_reversal(
    po_id: str,
    user: dict = Depends(require_permission("purchase", "delete"))
):
    """
    Preview apa saja yang akan di-reverse jika PO ini di-cancel
    
    Returns:
    - stock_movements: daftar pergerakan stok yang akan di-reverse
    - ap_records: daftar hutang yang akan di-cancel
    - payments: daftar pembayaran yang harus di-reverse dulu
    - journals: daftar jurnal yang akan di-reverse
    """
    db = get_db()
    
    po = await purchase_orders.find_one({"id": po_id}, {"_id": 0})
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order tidak ditemukan")
    
    po_number = po.get("po_number", po_id)
    
    # Check if already reversed
    if po.get("status") == "reversed":
        raise HTTPException(status_code=400, detail="PO ini sudah di-reverse sebelumnya")
    
    # Check if draft - can be deleted instead of reversed
    if po.get("status") == "draft":
        return {
            "po_id": po_id,
            "po_number": po_number,
            "current_status": po.get("status"),
            "can_delete": True,
            "can_reverse": False,
            "message": "PO dengan status DRAFT dapat langsung dihapus",
            "action_recommended": "DELETE"
        }
    
    # ============ GATHER ALL IMPACTS ============
    
    # 1. Stock movements
    movements = await stock_movements.find({
        "reference_id": po_id,
        "reference_type": "purchase_order"
    }, {"_id": 0}).to_list(1000)
    
    stock_impact = []
    for m in movements:
        stock_impact.append({
            "product_id": m.get("product_id"),
            "product_name": m.get("product_name", "Unknown"),
            "warehouse_id": m.get("warehouse_id"),
            "quantity": m.get("quantity", 0),
            "movement_type": m.get("movement_type"),
            "will_reverse": f"Stok akan dikurangi {abs(m.get('quantity', 0))} untuk {m.get('product_name', 'Unknown')}"
        })
    
    # 2. AP records
    ap_collection = db["accounts_payable"]
    ap_records = await ap_collection.find({"po_id": po_id}, {"_id": 0}).to_list(100)
    
    ap_impact = []
    for ap in ap_records:
        ap_impact.append({
            "ap_id": ap.get("id"),
            "ap_number": ap.get("ap_number"),
            "amount": ap.get("amount", 0),
            "outstanding": ap.get("outstanding", 0),
            "status": ap.get("status"),
            "will_reverse": "Hutang akan di-cancel"
        })
    
    # 3. Payments (MUST be reversed first!)
    ap_payments_col = db["ap_payments"]
    payments = []
    for ap in ap_records:
        pmnts = await ap_payments_col.find({"ap_id": ap.get("id")}, {"_id": 0}).to_list(100)
        for p in pmnts:
            if p.get("status") not in ["reversed", "cancelled"]:
                payments.append({
                    "payment_id": p.get("id"),
                    "payment_no": p.get("payment_no"),
                    "amount": p.get("amount", 0),
                    "status": p.get("status"),
                    "must_reverse_first": True,
                    "message": "Pembayaran ini HARUS di-reverse terlebih dahulu"
                })
    
    # 4. Journals
    journal_collection = db["journal_entries"]
    journals = await journal_collection.find({
        "$or": [
            {"reference_id": po_id},
            {"reference_no": po_number}
        ]
    }, {"_id": 0}).to_list(100)
    
    journal_impact = []
    for j in journals:
        if j.get("status") != "reversed":
            journal_impact.append({
                "journal_no": j.get("journal_no"),
                "description": j.get("description", ""),
                "total_debit": j.get("total_debit", 0),
                "status": j.get("status"),
                "will_reverse": "Jurnal akan di-reverse"
            })
    
    # ============ DETERMINE ACTION ============
    has_active_payments = len([p for p in payments if p.get("must_reverse_first")]) > 0
    
    return {
        "po_id": po_id,
        "po_number": po_number,
        "current_status": po.get("status"),
        "can_delete": False,
        "can_reverse": not has_active_payments,
        "has_active_payments": has_active_payments,
        "action_recommended": "REVERSE_PAYMENTS_FIRST" if has_active_payments else "REVERSE",
        "impacts": {
            "stock_movements": stock_impact,
            "ap_records": ap_impact,
            "payments": payments,
            "journals": journal_impact
        },
        "summary": {
            "total_stock_movements": len(stock_impact),
            "total_ap_records": len(ap_impact),
            "total_payments": len(payments),
            "total_journals": len(journal_impact),
            "blocking_payments": len([p for p in payments if p.get("must_reverse_first")])
        },
        "message": "Pembayaran harus di-reverse terlebih dahulu" if has_active_payments else "PO siap untuk di-reverse"
    }


@router.post("/orders/{po_id}/full-reverse")
async def full_reverse_purchase_order(
    po_id: str,
    data: PurchaseReversalRequest,
    request: Request,
    user: dict = Depends(require_permission("purchase", "delete"))
):
    """
    FULL REVERSAL Purchase Order
    
    FLOW:
    1. Validasi tidak ada payment aktif
    2. Reverse semua stock movements (kembalikan stok)
    3. Cancel semua AP records (kembalikan hutang)
    4. Reverse semua journals (buat reversal journal)
    5. Update status PO ke REVERSED
    6. Create comprehensive audit trail
    
    HASIL:
    - Kondisi bisnis kembali seperti sebelum PO terjadi
    - Stok kembali ke kondisi awal
    - Hutang dihapus
    - Jurnal di-netralkan
    - Audit trail lengkap tersimpan
    """
    db = get_db()
    user_id = user.get("user_id", user.get("id", ""))
    user_name = user.get("name", "System")
    
    # Get PO
    po = await purchase_orders.find_one({"id": po_id}, {"_id": 0})
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order tidak ditemukan")
    
    po_number = po.get("po_number", po_id)
    old_status = po.get("status")
    
    # ============ VALIDATIONS ============
    if old_status == "reversed":
        raise HTTPException(status_code=400, detail="PO ini sudah di-reverse sebelumnya")
    
    if old_status == "draft":
        raise HTTPException(
            status_code=400, 
            detail="PO dengan status DRAFT tidak perlu di-reverse, gunakan DELETE saja"
        )
    
    # Check for active payments
    ap_collection = db["accounts_payable"]
    ap_payments_col = db["ap_payments"]
    
    ap_records = await ap_collection.find({"po_id": po_id}, {"_id": 0}).to_list(100)
    
    active_payments = []
    for ap in ap_records:
        pmnts = await ap_payments_col.find({
            "ap_id": ap.get("id"),
            "status": {"$nin": ["reversed", "cancelled", "draft"]}
        }, {"_id": 0}).to_list(100)
        active_payments.extend(pmnts)
    
    if active_payments:
        payment_nos = [p.get("payment_no", p.get("id")) for p in active_payments]
        raise HTTPException(
            status_code=400,
            detail=f"Tidak dapat reverse PO karena ada {len(active_payments)} pembayaran aktif yang harus di-reverse terlebih dahulu: {', '.join(payment_nos[:5])}"
        )
    
    # ============ START REVERSAL PROCESS ============
    reversal_results = {
        "stock_reversed": [],
        "ap_cancelled": [],
        "journals_reversed": [],
        "errors": []
    }
    
    reversal_timestamp = datetime.now(timezone.utc).isoformat()
    
    # ============ 1. REVERSE STOCK MOVEMENTS ============
    movements = await stock_movements.find({
        "reference_id": po_id,
        "reference_type": "purchase_order"
    }, {"_id": 0}).to_list(1000)
    
    for movement in movements:
        try:
            product_id = movement.get("product_id")
            warehouse_id = movement.get("warehouse_id")
            quantity = movement.get("quantity", 0)
            
            # Create reversal movement
            reversal_movement_id = str(uuid.uuid4())
            reversal_movement = {
                "id": reversal_movement_id,
                "product_id": product_id,
                "product_name": movement.get("product_name"),
                "warehouse_id": warehouse_id,
                "branch_id": movement.get("branch_id"),
                "movement_type": "stock_reversal",
                "quantity": -quantity,  # Negative to reverse
                "reference_type": "purchase_reversal",
                "reference_id": po_id,
                "reference_no": f"REV-{po_number}",
                "cost_per_unit": movement.get("cost_per_unit", 0),
                "total_cost": -(movement.get("total_cost", 0)),
                "notes": f"REVERSAL: {data.reason}",
                "created_by": user_id,
                "created_at": reversal_timestamp,
                "original_movement_id": movement.get("id")
            }
            
            await stock_movements.insert_one(reversal_movement)
            
            # Update product stock
            await product_stocks.update_one(
                {"product_id": product_id, "warehouse_id": warehouse_id},
                {"$inc": {"quantity": -quantity}}
            )
            
            # Also update main products collection if exists
            await products.update_one(
                {"id": product_id},
                {"$inc": {"stock": -quantity}}
            )
            
            reversal_results["stock_reversed"].append({
                "product_id": product_id,
                "product_name": movement.get("product_name"),
                "quantity_reversed": quantity,
                "reversal_movement_id": reversal_movement_id
            })
            
        except Exception as e:
            reversal_results["errors"].append(f"Stock reversal error for {product_id}: {str(e)}")
    
    # ============ 2. CANCEL AP RECORDS ============
    for ap in ap_records:
        try:
            ap_id = ap.get("id")
            
            await ap_collection.update_one(
                {"id": ap_id},
                {"$set": {
                    "status": "cancelled",
                    "cancelled_at": reversal_timestamp,
                    "cancelled_by": user_id,
                    "cancelled_reason": f"PO Reversal: {data.reason}",
                    "outstanding": 0
                }}
            )
            
            reversal_results["ap_cancelled"].append({
                "ap_id": ap_id,
                "ap_number": ap.get("ap_number"),
                "amount": ap.get("amount", 0)
            })
            
        except Exception as e:
            reversal_results["errors"].append(f"AP cancellation error for {ap_id}: {str(e)}")
    
    # ============ 3. REVERSE JOURNALS ============
    journal_collection = db["journal_entries"]
    journals = await journal_collection.find({
        "$or": [
            {"reference_id": po_id},
            {"reference_no": po_number}
        ],
        "status": {"$ne": "reversed"}
    }, {"_id": 0}).to_list(100)
    
    for journal in journals:
        try:
            # Create reversal journal
            reversal_journal_no = f"REV-{journal.get('journal_no', '')}"
            
            # Reverse entries (swap debit/credit)
            reversal_entries = []
            for entry in journal.get("entries", []):
                reversal_entries.append({
                    "account_code": entry.get("account_code"),
                    "account_name": entry.get("account_name"),
                    "debit": entry.get("credit", 0),
                    "credit": entry.get("debit", 0),
                    "description": f"REVERSAL: {entry.get('description', '')}"
                })
            
            reversal_journal = {
                "id": str(uuid.uuid4()),
                "journal_no": reversal_journal_no,
                "date": reversal_timestamp,
                "description": f"REVERSAL - {journal.get('description', '')} | Reason: {data.reason}",
                "entries": reversal_entries,
                "total_debit": journal.get("total_credit", 0),
                "total_credit": journal.get("total_debit", 0),
                "reference_type": "purchase_reversal",
                "reference_id": po_id,
                "reference_no": f"REV-{po_number}",
                "original_journal_id": journal.get("id"),
                "original_journal_no": journal.get("journal_no"),
                "status": "posted",
                "is_reversal": True,
                "created_by": user_id,
                "created_at": reversal_timestamp
            }
            
            await journal_collection.insert_one(reversal_journal)
            
            # Mark original journal as reversed
            await journal_collection.update_one(
                {"id": journal.get("id")},
                {"$set": {
                    "status": "reversed",
                    "reversed_at": reversal_timestamp,
                    "reversed_by": user_id,
                    "reversal_journal_no": reversal_journal_no
                }}
            )
            
            reversal_results["journals_reversed"].append({
                "original_journal_no": journal.get("journal_no"),
                "reversal_journal_no": reversal_journal_no,
                "total_amount": journal.get("total_debit", 0)
            })
            
        except Exception as e:
            reversal_results["errors"].append(f"Journal reversal error for {journal.get('journal_no')}: {str(e)}")
    
    # ============ 4. UPDATE PO STATUS ============
    await purchase_orders.update_one(
        {"id": po_id},
        {"$set": {
            "status": "reversed",
            "reversed_at": reversal_timestamp,
            "reversed_by": user_id,
            "reversed_by_name": user_name,
            "reversal_reason": data.reason,
            "reversal_notes": data.notes,
            "updated_at": reversal_timestamp
        }}
    )
    
    # ============ 5. COMPREHENSIVE AUDIT TRAIL ============
    audit_detail = {
        "id": str(uuid.uuid4()),
        "event_type": "PURCHASE_ORDER_REVERSAL",
        "tenant_id": db.name,
        "po_id": po_id,
        "po_number": po_number,
        "user_id": user_id,
        "user_name": user_name,
        "timestamp": reversal_timestamp,
        "old_status": old_status,
        "new_status": "reversed",
        "reason": data.reason,
        "notes": data.notes,
        "reversal_results": reversal_results,
        "ip_address": request.client.host if request.client else ""
    }
    
    audit_logs = db["audit_logs"]
    await audit_logs.insert_one(audit_detail)
    
    await log_security_event(
        db, user_id, user_name,
        "reverse", "purchase",
        f"REVERSAL PO {po_number} | Stock: {len(reversal_results['stock_reversed'])} items | AP: {len(reversal_results['ap_cancelled'])} records | Journals: {len(reversal_results['journals_reversed'])}",
        request.client.host if request.client else "",
        document_no=po_number,
        severity="critical"
    )
    
    return {
        "success": True,
        "message": f"Purchase Order {po_number} berhasil di-reverse",
        "po_id": po_id,
        "po_number": po_number,
        "old_status": old_status,
        "new_status": "reversed",
        "reversal_timestamp": reversal_timestamp,
        "reversal_summary": {
            "stock_movements_reversed": len(reversal_results["stock_reversed"]),
            "ap_records_cancelled": len(reversal_results["ap_cancelled"]),
            "journals_reversed": len(reversal_results["journals_reversed"]),
            "errors": len(reversal_results["errors"])
        },
        "reversal_details": reversal_results,
        "reason": data.reason
    }


# ==================== QUICK PURCHASE - DIRECT STOCK IN ====================
# ARSITEKTUR FINAL: Quick Purchase = purchase + stock in LANGSUNG
# Berbeda dengan Buat PO yang status draft dan menunggu Terima Barang

class QuickPurchaseInput(BaseModel):
    """Input for Quick Purchase - direct stock in"""
    supplier_id: str
    branch_id: Optional[str] = None  # CABANG = GUDANG (unified)
    items: List[POItemInput]
    notes: str = ""
    is_cash: bool = True  # Default tunai untuk quick purchase
    payment_account_id: Optional[str] = None


@router.post("/quick")
async def quick_purchase(
    data: QuickPurchaseInput, 
    request: Request, 
    user: dict = Depends(require_permission("purchase", "create"))
):
    """
    QUICK PURCHASE - Direct Stock In
    
    FLOW FINAL (per Arsitektur OCB TITAN):
    1. Validasi supplier dan items
    2. Buat PO dengan status 'posted' (bukan draft)
    3. LANGSUNG tambah stok ke product_stocks (SOURCE OF TRUTH)
    4. Catat stock_movements (HISTORI)
    5. (Opsional) Buat AP jika kredit
    
    RESULT:
    - Stok langsung muncul di daftar item
    - Tidak perlu proses "Terima Barang" terpisah
    """
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant tidak teridentifikasi")
    
    # ============ VALIDASI ============
    if not data.supplier_id:
        raise HTTPException(status_code=400, detail="Supplier wajib dipilih")
    
    supplier = await suppliers.find_one({"id": data.supplier_id}, {"_id": 0})
    if not supplier:
        raise HTTPException(status_code=400, detail="Supplier tidak ditemukan di tenant ini")
    
    if not data.items or len(data.items) == 0:
        raise HTTPException(status_code=400, detail="Minimal harus ada 1 item pembelian")
    
    # Branch = Gudang (unified concept)
    branch_id = data.branch_id or user.get("branch_id")
    if not branch_id:
        # Get default branch
        default_branch = await branches.find_one({"is_default": True}, {"_id": 0})
        if default_branch:
            branch_id = default_branch.get("id")
        else:
            # Fallback: get first branch
            first_branch = await branches.find_one({}, {"_id": 0})
            if first_branch:
                branch_id = first_branch.get("id")
            else:
                raise HTTPException(status_code=400, detail="Tidak ada cabang terdaftar")
    
    # Get branch name
    branch_doc = await branches.find_one({"id": branch_id}, {"_id": 0})
    branch_name = branch_doc.get("name", "") if branch_doc else ""
    
    # ============ BUILD PO ITEMS ============
    po_items = []
    subtotal = 0
    
    for item in data.items:
        product = await products.find_one({"id": item.product_id}, {"_id": 0})
        if not product:
            raise HTTPException(status_code=400, detail=f"Product tidak ditemukan: {item.product_id}")
        
        if item.quantity <= 0:
            raise HTTPException(status_code=400, detail=f"Qty {product.get('name')} harus > 0")
        
        item_subtotal = item.unit_cost * item.quantity
        if item.discount_percent > 0:
            item_subtotal -= item_subtotal * (item.discount_percent / 100)
        
        po_item = {
            "product_id": item.product_id,
            "product_code": product.get("code", ""),
            "product_name": item.product_name or product.get("name", ""),
            "quantity": item.quantity,
            "received_qty": item.quantity,  # LANGSUNG DITERIMA SEMUA
            "unit_cost": item.unit_cost,
            "discount_percent": item.discount_percent,
            "subtotal": item_subtotal,
            "unit": item.purchase_unit or product.get("unit", "pcs")
        }
        
        po_items.append(po_item)
        subtotal += item_subtotal
    
    if subtotal <= 0:
        raise HTTPException(status_code=400, detail="Total pembelian harus > 0")
    
    # ============ CREATE PO WITH POSTED STATUS ============
    po_number = await get_next_sequence("po_number", "QPO")  # QPO = Quick Purchase Order
    po_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    po_data = {
        "id": po_id,
        "po_number": po_number,
        "supplier_id": data.supplier_id,
        "supplier_name": supplier.get("name", ""),
        "supplier_code": supplier.get("code", ""),
        "branch_id": branch_id,
        "warehouse_id": branch_id,  # CABANG = GUDANG
        "warehouse_name": branch_name,
        "items": po_items,
        "total_items": len(po_items),
        "total_qty": sum(i["quantity"] for i in po_items),
        "subtotal": subtotal,
        "total": subtotal,
        "status": "posted",  # LANGSUNG POSTED (bukan draft)
        "is_quick_purchase": True,  # Flag pembeda
        "is_cash": data.is_cash,
        "order_date": now,
        "received_date": now,  # LANGSUNG DITERIMA
        "notes": data.notes,
        "created_by": user.get("user_id", ""),
        "created_by_name": user.get("name", ""),
        "created_at": now,
        "updated_at": now,
        "tenant_id": tenant_id
    }
    
    await purchase_orders.insert_one(po_data)
    
    # ============ DIRECT STOCK IN - SOURCE OF TRUTH: product_stocks ============
    stock_results = []
    
    for item in po_items:
        product_id = item["product_id"]
        qty = item["quantity"]
        unit_cost = item["unit_cost"]
        
        # Get or create product_stocks record
        stock_rec = await product_stocks.find_one(
            {"product_id": product_id, "branch_id": branch_id}
        )
        
        if stock_rec:
            # WEIGHTED AVERAGE HPP calculation
            old_qty = stock_rec.get("quantity", 0)
            old_hpp = stock_rec.get("unit_cost", 0)
            
            if old_qty + qty > 0:
                new_hpp = ((old_qty * old_hpp) + (qty * unit_cost)) / (old_qty + qty)
            else:
                new_hpp = unit_cost
            
            new_qty = old_qty + qty
            new_total_value = new_qty * new_hpp
            
            await product_stocks.update_one(
                {"product_id": product_id, "branch_id": branch_id},
                {"$set": {
                    "quantity": new_qty,
                    "available": new_qty,
                    "unit_cost": round(new_hpp, 2),
                    "total_value": round(new_total_value, 2),
                    "last_restock": now,
                    "updated_at": now
                }}
            )
            
            stock_results.append({
                "product_id": product_id,
                "product_name": item["product_name"],
                "old_stock": old_qty,
                "added": qty,
                "new_stock": new_qty,
                "hpp": round(new_hpp, 2)
            })
        else:
            # Create new stock record
            new_stock = {
                "id": str(uuid.uuid4()),
                "product_id": product_id,
                "branch_id": branch_id,
                "quantity": qty,
                "available": qty,
                "reserved": 0,
                "unit_cost": unit_cost,
                "total_value": qty * unit_cost,
                "last_restock": now,
                "created_at": now,
                "updated_at": now
            }
            await product_stocks.insert_one(new_stock)
            
            stock_results.append({
                "product_id": product_id,
                "product_name": item["product_name"],
                "old_stock": 0,
                "added": qty,
                "new_stock": qty,
                "hpp": unit_cost
            })
        
        # ============ RECORD STOCK MOVEMENT - HISTORI ============
        # PROTECTION: Check for existing movement to prevent duplicates
        existing_movement = await stock_movements.find_one({
            "reference_id": po_id,
            "product_id": product_id,
            "branch_id": branch_id,
            "reference_type": "quick_purchase"
        })
        
        if existing_movement:
            # Movement already exists - skip to prevent double entry
            continue
        
        movement = {
            "id": str(uuid.uuid4()),
            "product_id": product_id,
            "product_name": item["product_name"],
            "branch_id": branch_id,
            "movement_type": "stock_in",
            "quantity": qty,
            "reference_type": "quick_purchase",
            "reference_id": po_id,
            "reference_number": po_number,  # Added for clarity
            "reference_no": po_number,
            "cost_per_unit": unit_cost,
            "total_cost": qty * unit_cost,
            "notes": f"Quick Purchase: {po_number}",
            "created_by": user.get("user_id", ""),
            "created_at": now
        }
        await stock_movements.insert_one(movement)
        
        # Update product cost_price (HPP terakhir)
        await products.update_one(
            {"id": product_id},
            {"$set": {"cost_price": unit_cost, "updated_at": now}}
        )
    
    # ============ CREATE AP INVOICE (HUTANG) FOR CREDIT PURCHASE ============
    ap_id = None
    ap_no = None
    
    if not data.is_cash:  # Only create AP for credit purchases
        from datetime import timedelta
        from routes.ap_system import generate_ap_number
        
        credit_due_days = 30  # Default payment term
        due_date = datetime.now(timezone.utc) + timedelta(days=credit_due_days)
        
        # Get branch code for AP number
        branch_doc = await branches.find_one({"id": branch_id}, {"_id": 0})
        branch_code = branch_doc.get("code", "HQ") if branch_doc else "HQ"
        
        # Generate standardized AP number
        ap_no = await generate_ap_number(branch_code)
        
        # STANDARDIZED AP FORMAT (compatible with ap_system.py)
        ap_entry = {
            "id": str(uuid.uuid4()),
            "ap_no": ap_no,
            "ap_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "due_date": due_date.strftime("%Y-%m-%d"),
            "supplier_id": data.supplier_id,
            "supplier_name": supplier.get("name", ""),
            "supplier_invoice_no": "",
            "branch_id": branch_id,
            "source_type": "purchase",
            "source_id": po_id,
            "source_no": po_number,
            "currency": "IDR",
            "original_amount": subtotal,
            "paid_amount": 0,
            "outstanding_amount": subtotal,
            "status": "open",
            "payment_term_days": credit_due_days,
            "notes": f"Hutang dari Quick Purchase {po_number}",
            "created_by": user.get("user_id", ""),
            "created_by_name": user.get("name", "System"),
            "created_at": now,
            "updated_at": now
        }
        
        db_conn = get_db()
        await db_conn["accounts_payable"].insert_one(ap_entry)
        ap_id = ap_entry["id"]
        
        # ============ CREATE JOURNAL ENTRY ============
        # Debit: Persediaan, Credit: Hutang Dagang
        from utils.number_generator import generate_transaction_number
        
        journal_id = str(uuid.uuid4())
        journal_number = await generate_transaction_number(db_conn, "JV-PUR")
        
        # Derive accounts
        inventory_account = await derive_purchase_account(
            db_conn, "persediaan_barang",
            branch_id=branch_id
        )
        ap_account = await derive_purchase_account(
            db_conn, "pembayaran_kredit_pembelian",
            branch_id=branch_id
        )
        
        journal_entries_list = [
            {
                "account_code": inventory_account["code"],
                "account_name": inventory_account["name"],
                "debit": subtotal,
                "credit": 0,
                "description": f"Persediaan dari {po_number}"
            },
            {
                "account_code": ap_account["code"],
                "account_name": ap_account["name"],
                "debit": 0,
                "credit": subtotal,
                "description": f"Hutang ke {supplier.get('name', '')}"
            }
        ]
        
        journal_entry = {
            "id": journal_id,
            "journal_number": journal_number,
            "journal_date": now,
            "reference_type": "quick_purchase",
            "reference_id": po_id,
            "reference_number": po_number,
            "description": f"Pembelian {po_number} - {supplier.get('name', '')}",
            "entries": journal_entries_list,
            "total_debit": subtotal,
            "total_credit": subtotal,
            "is_auto": True,
            "status": "posted",
            "branch_id": branch_id,
            "created_by": user.get("user_id", ""),
            "created_by_name": user.get("name", "System"),
            "created_at": now
        }
        
        await db_conn["journal_entries"].insert_one(journal_entry)
    
    # ============ AUDIT LOG ============
    db_conn = get_db()
    await log_security_event(
        db_conn, user.get("user_id", ""), user.get("name", ""),
        "create", "purchase",
        f"QUICK PURCHASE {po_number} | Supplier: {supplier.get('name')} | Total: Rp {subtotal:,.0f} | Items: {len(po_items)} | STOK LANGSUNG MASUK",
        request.client.host if request.client else "",
        document_no=po_number,
        severity="normal"
    )
    
    return {
        "success": True,
        "message": "Quick Purchase berhasil! Stok langsung bertambah.",
        "id": po_id,
        "po_number": po_number,
        "supplier_name": supplier.get("name", ""),
        "branch_name": branch_name,
        "total": subtotal,
        "items_count": len(po_items),
        "stock_updated": stock_results,
        "is_quick_purchase": True,
        "ap_created": ap_no is not None,
        "ap_no": ap_no,
        "is_credit": not data.is_cash
    }


# ==================== INVENTORY INTEGRITY - DUPLICATE CLEANUP ====================

class DuplicateCleanupInput(BaseModel):
    """Input for duplicate movement cleanup"""
    product_id: str
    dry_run: bool = True  # Default to dry run (preview only)

@router.post("/inventory/audit-duplicates")
async def audit_duplicate_movements(
    data: DuplicateCleanupInput,
    request: Request,
    user: dict = Depends(require_permission("inventory", "admin"))
):
    """
    AUDIT & CLEANUP DUPLICATE STOCK MOVEMENTS
    
    Rule:
    - Tidak DELETE data apapun
    - Duplikat di-fix dengan REVERSAL ENTRY (qty negatif)
    - Unique key: (reference_id, product_id, branch_id, reference_type)
    """
    tenant_id = user.get("tenant_id")
    now = datetime.now(timezone.utc).isoformat()
    
    # Find all movements for this product
    all_movements = await stock_movements.find({
        "$or": [
            {"product_id": data.product_id},
            {"item_id": data.product_id}
        ]
    }).sort("created_at", 1).to_list(1000)
    
    # Group by reference_id + reference_type + branch_id
    seen = {}  # key -> first movement
    duplicates = []
    
    for mov in all_movements:
        key = (
            mov.get("reference_id", "none"),
            mov.get("reference_type", "none"),
            mov.get("branch_id", "none"),
            mov.get("product_id") or mov.get("item_id")
        )
        
        if key in seen:
            # This is a duplicate
            duplicates.append({
                "original": seen[key],
                "duplicate": mov
            })
        else:
            seen[key] = mov
    
    if not duplicates:
        return {
            "success": True,
            "message": "No duplicates found",
            "total_movements": len(all_movements),
            "duplicates_found": 0,
            "reversals_created": 0
        }
    
    reversals_created = []
    
    if not data.dry_run:
        # CREATE REVERSAL ENTRIES for each duplicate
        for dup in duplicates:
            original = dup["original"]
            duplicate = dup["duplicate"]
            
            dup_qty = duplicate.get("quantity", 0)
            
            # Create reversal entry (negative qty to cancel out duplicate)
            reversal = {
                "id": str(uuid.uuid4()),
                "product_id": duplicate.get("product_id") or duplicate.get("item_id"),
                "product_name": duplicate.get("product_name", ""),
                "branch_id": duplicate.get("branch_id"),
                "movement_type": "reversal",
                "quantity": -dup_qty,  # Negative to cancel
                "reference_type": "duplicate_reversal",
                "reference_id": str(duplicate.get("_id")),
                "reference_number": f"REV-{duplicate.get('reference_number', duplicate.get('reference_no', 'DUP'))}",
                "notes": f"REVERSAL: Duplicate cleanup for movement {duplicate.get('_id')}. Original ref: {duplicate.get('reference_type')}",
                "created_by": user.get("user_id", ""),
                "created_at": now,
                "is_reversal": True,
                "reversed_movement_id": str(duplicate.get("_id"))
            }
            
            await stock_movements.insert_one(reversal)
            
            # Also update product_stocks to fix the quantity
            await product_stocks.update_one(
                {"product_id": reversal["product_id"], "branch_id": reversal["branch_id"]},
                {"$inc": {"quantity": -dup_qty, "available": -dup_qty}}
            )
            
            reversals_created.append({
                "duplicate_id": str(duplicate.get("_id")),
                "reversed_qty": dup_qty,
                "reversal_id": reversal["id"]
            })
    
    return {
        "success": True,
        "message": "Dry run" if data.dry_run else f"Created {len(reversals_created)} reversals",
        "total_movements": len(all_movements),
        "duplicates_found": len(duplicates),
        "duplicates": [
            {
                "original_id": str(d["original"].get("_id")),
                "original_qty": d["original"].get("quantity"),
                "original_ref": d["original"].get("reference_type"),
                "original_created": str(d["original"].get("created_at")),
                "duplicate_id": str(d["duplicate"].get("_id")),
                "duplicate_qty": d["duplicate"].get("quantity"),
                "duplicate_ref": d["duplicate"].get("reference_type"),
                "duplicate_created": str(d["duplicate"].get("created_at"))
            }
            for d in duplicates
        ],
        "reversals_created": reversals_created if not data.dry_run else [],
        "dry_run": data.dry_run
    }

@router.post("/inventory/fix-all-duplicates")
async def fix_all_duplicate_movements(
    request: Request,
    user: dict = Depends(require_permission("inventory", "admin"))
):
    """
    FIX ALL DUPLICATE MOVEMENTS IN THE SYSTEM
    
    Finds all duplicates and creates reversal entries to fix them.
    """
    tenant_id = user.get("tenant_id")
    now = datetime.now(timezone.utc).isoformat()
    
    # Find duplicates using aggregation
    pipeline = [
        {"$group": {
            "_id": {
                "reference_id": "$reference_id",
                "product_id": "$product_id",
                "branch_id": "$branch_id",
                "reference_type": "$reference_type"
            },
            "count": {"$sum": 1},
            "total_qty": {"$sum": "$quantity"},
            "docs": {"$push": {
                "_id": "$_id",
                "quantity": "$quantity",
                "created_at": "$created_at",
                "product_name": "$product_name",
                "notes": "$notes"
            }}
        }},
        {"$match": {"count": {"$gt": 1}}}
    ]
    
    duplicates = await stock_movements.aggregate(pipeline).to_list(1000)
    
    if not duplicates:
        return {
            "success": True,
            "message": "No duplicates found in the system",
            "duplicates_fixed": 0
        }
    
    fixed_count = 0
    fixed_details = []
    
    for dup_group in duplicates:
        key = dup_group["_id"]
        docs = dup_group["docs"]
        
        # Sort by created_at to keep the oldest one
        docs_sorted = sorted(docs, key=lambda x: str(x.get("created_at", "")))
        
        # First one is the original, rest are duplicates
        original = docs_sorted[0]
        duplicates_to_reverse = docs_sorted[1:]
        
        for dup in duplicates_to_reverse:
            dup_qty = dup.get("quantity", 0)
            
            # Create reversal entry
            reversal = {
                "id": str(uuid.uuid4()),
                "product_id": key.get("product_id"),
                "branch_id": key.get("branch_id"),
                "movement_type": "reversal",
                "quantity": -dup_qty,
                "reference_type": "duplicate_reversal",
                "reference_id": str(dup.get("_id")),
                "reference_number": f"REV-DUP-{str(dup.get('_id'))[:8]}",
                "notes": f"REVERSAL: Auto-cleanup duplicate. Original ref_type: {key.get('reference_type')}",
                "created_by": user.get("user_id", ""),
                "created_at": now,
                "is_reversal": True
            }
            
            await stock_movements.insert_one(reversal)
            
            # Fix product_stocks quantity
            if key.get("product_id") and key.get("branch_id"):
                await product_stocks.update_one(
                    {"product_id": key.get("product_id"), "branch_id": key.get("branch_id")},
                    {"$inc": {"quantity": -dup_qty, "available": -dup_qty}}
                )
            
            fixed_count += 1
            fixed_details.append({
                "product_id": key.get("product_id"),
                "branch_id": key.get("branch_id"),
                "duplicate_id": str(dup.get("_id")),
                "reversed_qty": dup_qty
            })
    
    return {
        "success": True,
        "message": f"Fixed {fixed_count} duplicate movements via reversal entries",
        "duplicates_groups_found": len(duplicates),
        "duplicates_fixed": fixed_count,
        "details": fixed_details[:50]  # Limit to first 50 for response size
    }



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
