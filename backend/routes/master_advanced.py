"""
OCB TITAN ERP - ADVANCED MASTER DATA MODULE
Module for Advanced Customers, Discounts, Promotions, Barcode Templates

INTEGRATIONS:
- Sales module: credit control, discount/promo auto-apply
- AR system: customer credit limits
- Journal engine: discount/promo journals
- Inventory: barcode printing
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from database import get_db as get_database
from routes.auth import get_current_user
from routes.rbac_middleware import require_permission, log_security_event
from utils.number_generator import generate_transaction_number
import uuid

router = APIRouter(prefix="/api/master-advanced", tags=["Master Advanced"])

# ==================== CUSTOMER ADVANCED ====================

class CustomerTaxInfo(BaseModel):
    tax_type: str = "default"  # default, custom, exempt
    tax_document_type: str = "npwp"  # npwp, nik, passport, other
    npwp: str = ""
    nik: str = ""
    passport: str = ""
    other_document: str = ""
    nitku: str = ""
    npwp_name: str = ""
    npwp_address: str = ""
    tax_country: str = "ID"

class CustomerCreditInfo(BaseModel):
    can_credit: bool = False
    credit_limit: float = 0
    credit_days_limit: int = 30
    default_due_days: int = 30
    max_invoice_amount: float = 0
    include_outstanding_check: bool = True
    default_discount_type: str = ""
    grace_period_days: int = 0

class CustomerAccountingInfo(BaseModel):
    ar_account_code: str = "1-1300"
    ar_account_name: str = "Piutang Usaha"
    default_payment_term: str = ""
    default_payment_method: str = ""

class CustomerAdvancedCreate(BaseModel):
    # General Data
    code: str = ""  # Auto if empty
    name: str
    customer_group: str = "umum"
    address: str = ""
    city: str = ""
    province: str = ""
    country: str = "Indonesia"
    postal_code: str = ""
    phone: str = ""
    fax: str = ""
    email: str = ""
    contact_person: str = ""
    birth_date: Optional[str] = None
    region: str = ""
    sub_region: str = ""
    default_sales_id: str = ""
    default_sales_name: str = ""
    notes: str = ""
    is_active: bool = True
    
    # Tax Info
    tax_info: CustomerTaxInfo = CustomerTaxInfo()
    
    # Credit Info
    credit_info: CustomerCreditInfo = CustomerCreditInfo()
    
    # Accounting Info
    accounting_info: CustomerAccountingInfo = CustomerAccountingInfo()

class CustomerAdvancedUpdate(BaseModel):
    name: Optional[str] = None
    customer_group: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    email: Optional[str] = None
    contact_person: Optional[str] = None
    birth_date: Optional[str] = None
    region: Optional[str] = None
    sub_region: Optional[str] = None
    default_sales_id: Optional[str] = None
    default_sales_name: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None
    tax_info: Optional[CustomerTaxInfo] = None
    credit_info: Optional[CustomerCreditInfo] = None
    accounting_info: Optional[CustomerAccountingInfo] = None

@router.get("/customers")
async def list_customers_advanced(
    search: str = "",
    customer_group: str = "",
    can_credit: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    user: dict = Depends(require_permission("master_customer", "view"))
):
    """List customers with advanced info"""
    db = get_database()
    
    query = {}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"code": {"$regex": search, "$options": "i"}},
            {"phone": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}}
        ]
    if customer_group:
        query["customer_group"] = customer_group
    if can_credit is not None:
        query["credit_info.can_credit"] = can_credit
    
    items = await db.customers_advanced.find(query, {"_id": 0}).sort("name", 1).skip(skip).limit(limit).to_list(limit)
    total = await db.customers_advanced.count_documents(query)
    
    return {"items": items, "total": total}

@router.get("/customers/{customer_id}")
async def get_customer_advanced(
    customer_id: str,
    user: dict = Depends(require_permission("master_customer", "view"))
):
    """Get customer advanced details"""
    db = get_database()
    
    customer = await db.customers_advanced.find_one({"id": customer_id}, {"_id": 0})
    if not customer:
        # Try legacy customers table
        customer = await db.customers.find_one({"id": customer_id}, {"_id": 0})
    
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Get AR summary
    ar_summary = await db.accounts_receivable.aggregate([
        {"$match": {"customer_id": customer_id, "status": {"$ne": "paid"}}},
        {"$group": {
            "_id": None,
            "total_outstanding": {"$sum": "$remaining_amount"},
            "count": {"$sum": 1}
        }}
    ]).to_list(1)
    
    if ar_summary:
        customer["ar_summary"] = ar_summary[0]
    else:
        customer["ar_summary"] = {"total_outstanding": 0, "count": 0}
    
    # Get recent transactions
    recent_tx = await db.transactions.find(
        {"customer_id": customer_id},
        {"_id": 0, "id": 1, "invoice_number": 1, "total": 1, "payment_type": 1, "created_at": 1}
    ).sort("created_at", -1).limit(10).to_list(10)
    customer["recent_transactions"] = recent_tx
    
    return customer

@router.post("/customers")
async def create_customer_advanced(
    data: CustomerAdvancedCreate,
    request: Request,
    user: dict = Depends(require_permission("master_customer", "create"))
):
    """Create customer with advanced fields"""
    db = get_database()
    
    # Generate code if empty
    code = data.code
    if not code:
        code = await generate_transaction_number(db, "CUS")
    
    # Check duplicate code or phone
    existing = await db.customers_advanced.find_one({
        "$or": [{"code": code}, {"phone": data.phone}] if data.phone else [{"code": code}]
    })
    if existing:
        raise HTTPException(status_code=400, detail="Kode atau nomor telepon sudah terdaftar")
    
    customer = {
        "id": str(uuid.uuid4()),
        "code": code,
        "name": data.name,
        "customer_group": data.customer_group,
        "address": data.address,
        "city": data.city,
        "province": data.province,
        "country": data.country,
        "postal_code": data.postal_code,
        "phone": data.phone,
        "fax": data.fax,
        "email": data.email,
        "contact_person": data.contact_person,
        "birth_date": data.birth_date,
        "region": data.region,
        "sub_region": data.sub_region,
        "default_sales_id": data.default_sales_id,
        "default_sales_name": data.default_sales_name,
        "notes": data.notes,
        "is_active": data.is_active,
        "tax_info": data.tax_info.model_dump(),
        "credit_info": data.credit_info.model_dump(),
        "accounting_info": data.accounting_info.model_dump(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user.get("user_id"),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.customers_advanced.insert_one(customer)
    
    # Also sync to legacy customers table
    legacy_customer = {
        "id": customer["id"],
        "code": code,
        "name": data.name,
        "phone": data.phone,
        "email": data.email,
        "address": data.address,
        "city": data.city,
        "segment": data.customer_group,
        "is_active": data.is_active,
        "created_at": customer["created_at"]
    }
    await db.customers.update_one(
        {"id": customer["id"]},
        {"$set": legacy_customer},
        upsert=True
    )
    
    await log_security_event(
        db, user.get("user_id"), user.get("name"),
        "create", "master_customer",
        f"Membuat customer advanced: {data.name} ({code})",
        request.client.host if request.client else ""
    )
    
    return {"success": True, "id": customer["id"], "code": code, "message": f"Customer {data.name} berhasil dibuat"}

@router.put("/customers/{customer_id}")
async def update_customer_advanced(
    customer_id: str,
    data: CustomerAdvancedUpdate,
    request: Request,
    user: dict = Depends(require_permission("master_customer", "edit"))
):
    """Update customer advanced"""
    db = get_database()
    
    update_data = {}
    for key, value in data.model_dump().items():
        if value is not None:
            if key in ["tax_info", "credit_info", "accounting_info"] and isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    update_data[f"{key}.{sub_key}"] = sub_value
            else:
                update_data[key] = value
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.customers_advanced.update_one(
        {"id": customer_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Sync critical fields to legacy table
    if any(k in data.model_dump() for k in ["name", "phone", "email", "address", "is_active"]):
        legacy_update = {k: v for k, v in data.model_dump().items() 
                        if v is not None and k in ["name", "phone", "email", "address", "is_active"]}
        if legacy_update:
            await db.customers.update_one({"id": customer_id}, {"$set": legacy_update})
    
    return {"success": True, "message": "Customer berhasil diupdate"}

# ==================== CREDIT CONTROL HELPER ====================

async def check_customer_credit_limit(db, customer_id: str, new_invoice_amount: float) -> Dict[str, Any]:
    """
    Check if customer can create credit invoice based on credit limits
    Called by sales module before creating credit invoice
    """
    customer = await db.customers_advanced.find_one({"id": customer_id}, {"_id": 0})
    
    if not customer:
        # Check legacy table
        customer = await db.customers.find_one({"id": customer_id}, {"_id": 0})
        if not customer:
            return {"allowed": False, "reason": "Customer not found"}
        # Default: allow with no limits
        return {"allowed": True, "reason": "No credit limit set (legacy customer)"}
    
    credit_info = customer.get("credit_info", {})
    
    if not credit_info.get("can_credit", False):
        return {"allowed": False, "reason": "Customer tidak diizinkan kredit"}
    
    # Check credit limit
    credit_limit = credit_info.get("credit_limit", 0)
    if credit_limit > 0:
        # Get current outstanding
        outstanding = await db.accounts_receivable.aggregate([
            {"$match": {"customer_id": customer_id, "status": {"$ne": "paid"}}},
            {"$group": {"_id": None, "total": {"$sum": "$remaining_amount"}}}
        ]).to_list(1)
        
        current_outstanding = outstanding[0]["total"] if outstanding else 0
        
        if current_outstanding + new_invoice_amount > credit_limit:
            return {
                "allowed": False,
                "reason": f"Melebihi batas kredit. Limit: Rp {credit_limit:,.0f}, Outstanding: Rp {current_outstanding:,.0f}, Invoice baru: Rp {new_invoice_amount:,.0f}"
            }
    
    # Check max invoice amount
    max_invoice = credit_info.get("max_invoice_amount", 0)
    if max_invoice > 0 and new_invoice_amount > max_invoice:
        return {
            "allowed": False,
            "reason": f"Nominal invoice melebihi batas per nota. Max: Rp {max_invoice:,.0f}"
        }
    
    return {"allowed": True, "default_due_days": credit_info.get("default_due_days", 30)}

# ==================== CUSTOMER GROUPS ====================

@router.get("/customer-groups")
async def list_customer_groups(user: dict = Depends(get_current_user)):
    """List customer groups for dropdown"""
    db = get_database()
    
    groups = await db.customer_groups.find({}, {"_id": 0}).sort("name", 1).to_list(100)
    
    if not groups:
        # Default groups
        groups = [
            {"id": "umum", "code": "UMUM", "name": "Umum", "description": "Pelanggan umum"},
            {"id": "member", "code": "MEMBER", "name": "Member", "description": "Pelanggan member"},
            {"id": "vip", "code": "VIP", "name": "VIP", "description": "Pelanggan VIP"},
            {"id": "wholesale", "code": "WHOLESALE", "name": "Grosir", "description": "Pelanggan grosir"},
            {"id": "reseller", "code": "RESELLER", "name": "Reseller", "description": "Pelanggan reseller"},
            {"id": "corporate", "code": "CORPORATE", "name": "Corporate", "description": "Pelanggan perusahaan"},
        ]
    
    return {"items": groups}

@router.post("/customer-groups")
async def create_customer_group(
    data: dict,
    user: dict = Depends(require_permission("master_customer", "create"))
):
    """Create customer group"""
    db = get_database()
    
    group = {
        "id": str(uuid.uuid4()),
        "code": data.get("code", ""),
        "name": data.get("name", ""),
        "description": data.get("description", ""),
        "discount_percentage": data.get("discount_percentage", 0),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.customer_groups.insert_one(group)
    
    return {"success": True, "id": group["id"]}

# ==================== DISCOUNT ADVANCED ====================

class DiscountAdvancedCreate(BaseModel):
    code: str = ""
    name: str
    discount_type: str  # percentage, nominal, per_pcs, per_item, per_transaction, tiered
    basis: str = "transaction"  # transaction, item, pcs
    value: float
    min_purchase: float = 0
    min_qty: int = 0
    max_discount: float = 0
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    start_time: str = "00:00"
    end_time: str = "23:59"
    is_active: bool = True
    priority: int = 0
    stackable: bool = False
    branches: List[str] = []  # Empty = all branches
    customer_groups: List[str] = []  # Empty = all groups
    categories: List[str] = []  # Empty = all categories
    brands: List[str] = []  # Empty = all brands
    items: List[str] = []  # Specific items (ID list)
    notes: str = ""

@router.get("/discounts")
async def list_discounts_advanced(
    search: str = "",
    is_active: Optional[bool] = None,
    discount_type: str = "",
    skip: int = 0,
    limit: int = 100,
    user: dict = Depends(require_permission("master_discount", "view"))
):
    """List discounts"""
    db = get_database()
    
    query = {}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"code": {"$regex": search, "$options": "i"}}
        ]
    if is_active is not None:
        query["is_active"] = is_active
    if discount_type:
        query["discount_type"] = discount_type
    
    items = await db.discounts_advanced.find(query, {"_id": 0}).sort("priority", -1).skip(skip).limit(limit).to_list(limit)
    total = await db.discounts_advanced.count_documents(query)
    
    return {"items": items, "total": total}

@router.get("/discounts/{discount_id}")
async def get_discount_advanced(
    discount_id: str,
    user: dict = Depends(require_permission("master_discount", "view"))
):
    """Get discount detail"""
    db = get_database()
    
    discount = await db.discounts_advanced.find_one({"id": discount_id}, {"_id": 0})
    if not discount:
        raise HTTPException(status_code=404, detail="Discount not found")
    
    return discount

@router.post("/discounts")
async def create_discount_advanced(
    data: DiscountAdvancedCreate,
    request: Request,
    user: dict = Depends(require_permission("master_discount", "create"))
):
    """Create discount"""
    db = get_database()
    
    code = data.code
    if not code:
        code = await generate_transaction_number(db, "DSC")
    
    existing = await db.discounts_advanced.find_one({"code": code})
    if existing:
        raise HTTPException(status_code=400, detail="Discount code already exists")
    
    discount = {
        "id": str(uuid.uuid4()),
        "code": code,
        **data.model_dump(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user.get("user_id"),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.discounts_advanced.insert_one(discount)
    
    return {"success": True, "id": discount["id"], "code": code}

@router.put("/discounts/{discount_id}")
async def update_discount_advanced(
    discount_id: str,
    data: dict,
    user: dict = Depends(require_permission("master_discount", "edit"))
):
    """Update discount"""
    db = get_database()
    
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.discounts_advanced.update_one(
        {"id": discount_id},
        {"$set": data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Discount not found")
    
    return {"success": True, "message": "Discount updated"}

@router.delete("/discounts/{discount_id}")
async def delete_discount_advanced(
    discount_id: str,
    user: dict = Depends(require_permission("master_discount", "delete"))
):
    """Soft delete discount"""
    db = get_database()
    
    result = await db.discounts_advanced.update_one(
        {"id": discount_id},
        {"$set": {"is_active": False, "deleted_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Discount not found")
    
    return {"success": True, "message": "Discount deleted"}

# ==================== DISCOUNT ENGINE ====================

async def calculate_applicable_discounts(
    db, 
    items: List[Dict], 
    customer_id: str, 
    branch_id: str,
    subtotal: float
) -> Dict[str, Any]:
    """
    Calculate all applicable discounts for a transaction
    Called by sales module during invoice creation
    """
    now = datetime.now(timezone.utc)
    current_date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M")
    
    # Get customer info
    customer = await db.customers_advanced.find_one({"id": customer_id}, {"_id": 0})
    customer_group = customer.get("customer_group", "umum") if customer else "umum"
    
    # Get all active discounts
    discounts = await db.discounts_advanced.find({
        "is_active": True,
        "$or": [
            {"start_date": None},
            {"start_date": {"$lte": current_date}}
        ]
    }, {"_id": 0}).sort("priority", -1).to_list(100)
    
    applicable_discounts = []
    total_discount = 0
    
    for discount in discounts:
        # Check date validity
        if discount.get("end_date") and discount["end_date"] < current_date:
            continue
        
        # Check time validity
        if discount.get("start_time", "00:00") > current_time or discount.get("end_time", "23:59") < current_time:
            continue
        
        # Check branch
        if discount.get("branches") and branch_id not in discount["branches"]:
            continue
        
        # Check customer group
        if discount.get("customer_groups") and customer_group not in discount["customer_groups"]:
            continue
        
        # Check minimum purchase
        if discount.get("min_purchase", 0) > 0 and subtotal < discount["min_purchase"]:
            continue
        
        discount_amount = 0
        discount_type = discount.get("discount_type", "percentage")
        discount_value = discount.get("value", 0)
        basis = discount.get("basis", "transaction")
        
        # Calculate based on type
        if discount_type == "percentage":
            discount_amount = subtotal * (discount_value / 100)
        elif discount_type == "nominal":
            discount_amount = discount_value
        elif discount_type == "per_pcs":
            # Calculate based on items qty
            total_qty = sum(item.get("qty", 0) for item in items)
            if discount.get("min_qty", 0) <= total_qty:
                discount_amount = discount_value * total_qty
        elif discount_type == "per_item":
            # Per unique item
            matching_items = 0
            for item in items:
                if not discount.get("items") or item.get("item_id") in discount.get("items", []):
                    if not discount.get("categories") or item.get("category_id") in discount.get("categories", []):
                        if not discount.get("brands") or item.get("brand_id") in discount.get("brands", []):
                            matching_items += 1
            discount_amount = discount_value * matching_items
        
        # Apply max discount cap
        if discount.get("max_discount", 0) > 0:
            discount_amount = min(discount_amount, discount["max_discount"])
        
        if discount_amount > 0:
            applicable_discounts.append({
                "discount_id": discount["id"],
                "discount_code": discount["code"],
                "discount_name": discount["name"],
                "discount_type": discount_type,
                "discount_value": discount_value,
                "calculated_amount": discount_amount
            })
            total_discount += discount_amount
            
            # Check stackable
            if not discount.get("stackable", False):
                break
    
    return {
        "discounts": applicable_discounts,
        "total_discount": total_discount
    }

# ==================== PROMOTION ADVANCED ====================

class PromotionRuleCreate(BaseModel):
    target_type: str = "all"  # all, category, brand, item, bundle
    condition_qty: int = 0
    condition_subtotal: float = 0
    trigger_items: List[str] = []  # Item IDs that trigger
    benefit_type: str = "discount"  # discount, free_item, bundle_price, special_price
    benefit_discount_type: str = "percentage"  # percentage, nominal
    benefit_discount_value: float = 0
    benefit_free_item_id: str = ""
    benefit_free_item_qty: int = 0
    benefit_special_price: float = 0

class PromotionTargetCreate(BaseModel):
    item_id: str = ""
    item_code: str = ""
    item_name: str = ""
    category_id: str = ""
    brand_id: str = ""
    trigger_qty: int = 0
    reward_qty: int = 0
    discount_value: float = 0
    special_price: float = 0
    is_free: bool = False

class PromotionAdvancedCreate(BaseModel):
    code: str = ""
    name: str
    promo_type: str  # product, category, brand, bundle, buy_x_get_y, special_price, period, branch, customer_group, quota
    description: str = ""
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    start_time: str = "00:00"
    end_time: str = "23:59"
    is_active: bool = True
    priority: int = 0
    stackable: bool = False
    branches: List[str] = []
    customer_groups: List[str] = []
    quota: int = 0  # 0 = unlimited
    used_count: int = 0
    rules: List[PromotionRuleCreate] = []
    targets: List[PromotionTargetCreate] = []
    notes: str = ""

@router.get("/promotions")
async def list_promotions_advanced(
    search: str = "",
    is_active: Optional[bool] = None,
    promo_type: str = "",
    skip: int = 0,
    limit: int = 100,
    user: dict = Depends(require_permission("master_promotion", "view"))
):
    """List promotions"""
    db = get_database()
    
    query = {}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"code": {"$regex": search, "$options": "i"}}
        ]
    if is_active is not None:
        query["is_active"] = is_active
    if promo_type:
        query["promo_type"] = promo_type
    
    items = await db.promotions_advanced.find(query, {"_id": 0}).sort("priority", -1).skip(skip).limit(limit).to_list(limit)
    total = await db.promotions_advanced.count_documents(query)
    
    return {"items": items, "total": total}

@router.get("/promotions/{promo_id}")
async def get_promotion_advanced(
    promo_id: str,
    user: dict = Depends(require_permission("master_promotion", "view"))
):
    """Get promotion detail"""
    db = get_database()
    
    promo = await db.promotions_advanced.find_one({"id": promo_id}, {"_id": 0})
    if not promo:
        raise HTTPException(status_code=404, detail="Promotion not found")
    
    return promo

@router.post("/promotions")
async def create_promotion_advanced(
    data: PromotionAdvancedCreate,
    request: Request,
    user: dict = Depends(require_permission("master_promotion", "create"))
):
    """Create promotion"""
    db = get_database()
    
    code = data.code
    if not code:
        code = await generate_transaction_number(db, "PROMO")
    
    existing = await db.promotions_advanced.find_one({"code": code})
    if existing:
        raise HTTPException(status_code=400, detail="Promotion code already exists")
    
    promo = {
        "id": str(uuid.uuid4()),
        "code": code,
        "name": data.name,
        "promo_type": data.promo_type,
        "description": data.description,
        "start_date": data.start_date,
        "end_date": data.end_date,
        "start_time": data.start_time,
        "end_time": data.end_time,
        "is_active": data.is_active,
        "priority": data.priority,
        "stackable": data.stackable,
        "branches": data.branches,
        "customer_groups": data.customer_groups,
        "quota": data.quota,
        "used_count": 0,
        "rules": [r.model_dump() for r in data.rules],
        "targets": [t.model_dump() for t in data.targets],
        "notes": data.notes,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user.get("user_id"),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.promotions_advanced.insert_one(promo)
    
    return {"success": True, "id": promo["id"], "code": code}

@router.put("/promotions/{promo_id}")
async def update_promotion_advanced(
    promo_id: str,
    data: dict,
    user: dict = Depends(require_permission("master_promotion", "edit"))
):
    """Update promotion"""
    db = get_database()
    
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.promotions_advanced.update_one(
        {"id": promo_id},
        {"$set": data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Promotion not found")
    
    return {"success": True, "message": "Promotion updated"}

@router.delete("/promotions/{promo_id}")
async def delete_promotion_advanced(
    promo_id: str,
    user: dict = Depends(require_permission("master_promotion", "delete"))
):
    """Soft delete promotion"""
    db = get_database()
    
    result = await db.promotions_advanced.update_one(
        {"id": promo_id},
        {"$set": {"is_active": False, "deleted_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Promotion not found")
    
    return {"success": True, "message": "Promotion deleted"}

# ==================== PROMOTION ENGINE ====================

async def apply_promotions(
    db,
    items: List[Dict],
    customer_id: str,
    branch_id: str,
    subtotal: float
) -> Dict[str, Any]:
    """
    Apply promotions to transaction items
    Called by sales module during invoice creation
    Returns modified items with promo info and free items
    """
    now = datetime.now(timezone.utc)
    current_date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M")
    
    # Get customer info
    customer = await db.customers_advanced.find_one({"id": customer_id}, {"_id": 0})
    customer_group = customer.get("customer_group", "umum") if customer else "umum"
    
    # Get active promotions
    promos = await db.promotions_advanced.find({
        "is_active": True,
        "$or": [
            {"start_date": None},
            {"start_date": {"$lte": current_date}}
        ]
    }, {"_id": 0}).sort("priority", -1).to_list(100)
    
    applied_promos = []
    free_items = []
    total_promo_discount = 0
    
    for promo in promos:
        # Check validity
        if promo.get("end_date") and promo["end_date"] < current_date:
            continue
        if promo.get("start_time", "00:00") > current_time or promo.get("end_time", "23:59") < current_time:
            continue
        if promo.get("branches") and branch_id not in promo["branches"]:
            continue
        if promo.get("customer_groups") and customer_group not in promo["customer_groups"]:
            continue
        if promo.get("quota", 0) > 0 and promo.get("used_count", 0) >= promo["quota"]:
            continue
        
        promo_type = promo.get("promo_type", "")
        promo_benefit = 0
        
        if promo_type == "special_price":
            # Apply special price to target items
            for target in promo.get("targets", []):
                for item in items:
                    if item.get("item_id") == target.get("item_id"):
                        original_price = item.get("price", 0)
                        special_price = target.get("special_price", original_price)
                        if special_price < original_price:
                            discount_per_item = original_price - special_price
                            qty = item.get("qty", 1)
                            promo_benefit += discount_per_item * qty
                            item["promo_code"] = promo["code"]
                            item["promo_name"] = promo["name"]
                            item["promo_price"] = special_price
        
        elif promo_type == "buy_x_get_y":
            # Buy X get Y free
            for rule in promo.get("rules", []):
                trigger_qty = rule.get("condition_qty", 0)
                for item in items:
                    if item.get("item_id") in rule.get("trigger_items", []):
                        item_qty = item.get("qty", 0)
                        if item_qty >= trigger_qty:
                            # Add free item
                            free_qty = rule.get("benefit_free_item_qty", 1)
                            free_item_id = rule.get("benefit_free_item_id", "")
                            if free_item_id:
                                free_item_data = await db.items.find_one({"id": free_item_id}, {"_id": 0})
                                if free_item_data:
                                    free_items.append({
                                        "item_id": free_item_id,
                                        "item_code": free_item_data.get("code", ""),
                                        "item_name": free_item_data.get("name", ""),
                                        "qty": free_qty,
                                        "price": 0,
                                        "promo_code": promo["code"],
                                        "promo_name": promo["name"],
                                        "is_promo_item": True
                                    })
        
        elif promo_type == "bundle":
            # Bundle pricing
            for target in promo.get("targets", []):
                item_ids = [t.get("item_id") for t in promo.get("targets", [])]
                cart_item_ids = [i.get("item_id") for i in items]
                if all(iid in cart_item_ids for iid in item_ids):
                    # All bundle items present
                    bundle_price = sum(t.get("special_price", 0) for t in promo.get("targets", []))
                    original_price = sum(
                        i.get("price", 0) * i.get("qty", 1) 
                        for i in items if i.get("item_id") in item_ids
                    )
                    if bundle_price < original_price:
                        promo_benefit = original_price - bundle_price
        
        if promo_benefit > 0 or free_items:
            applied_promos.append({
                "promo_id": promo["id"],
                "promo_code": promo["code"],
                "promo_name": promo["name"],
                "promo_type": promo_type,
                "benefit_amount": promo_benefit
            })
            total_promo_discount += promo_benefit
            
            # Update usage count
            await db.promotions_advanced.update_one(
                {"id": promo["id"]},
                {"$inc": {"used_count": 1}}
            )
            
            if not promo.get("stackable", False):
                break
    
    return {
        "items": items,
        "free_items": free_items,
        "applied_promos": applied_promos,
        "total_promo_discount": total_promo_discount
    }

# ==================== BARCODE TEMPLATES ====================

class BarcodeTemplateCreate(BaseModel):
    code: str = ""
    name: str
    paper_size: str = "label_58x40"  # label_58x40, label_38x25, a4_30, a4_65, custom
    width_mm: float = 58
    height_mm: float = 40
    columns: int = 1
    rows: int = 1
    margin_top: float = 2
    margin_bottom: float = 2
    margin_left: float = 2
    margin_right: float = 2
    gap_h: float = 2
    gap_v: float = 2
    barcode_type: str = "code128"  # code128, ean13, qrcode
    barcode_source: str = "barcode"  # barcode, item_code, sku
    show_item_name: bool = True
    show_item_code: bool = True
    show_price: bool = True
    price_type: str = "sell"  # sell, hpp, both
    font_size: int = 10
    barcode_height: float = 15
    is_active: bool = True
    notes: str = ""

@router.get("/barcode-templates")
async def list_barcode_templates(
    search: str = "",
    is_active: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    user: dict = Depends(get_current_user)
):
    """List barcode templates"""
    db = get_database()
    
    query = {}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"code": {"$regex": search, "$options": "i"}}
        ]
    if is_active is not None:
        query["is_active"] = is_active
    
    items = await db.barcode_templates.find(query, {"_id": 0}).sort("name", 1).skip(skip).limit(limit).to_list(limit)
    total = await db.barcode_templates.count_documents(query)
    
    if not items:
        # Default templates
        items = [
            {
                "id": "default_58x40",
                "code": "TPL-001",
                "name": "Label 58x40mm",
                "paper_size": "label_58x40",
                "width_mm": 58,
                "height_mm": 40,
                "columns": 1,
                "rows": 1,
                "barcode_type": "code128",
                "barcode_source": "barcode",
                "show_item_name": True,
                "show_item_code": True,
                "show_price": True,
                "price_type": "sell",
                "is_active": True
            },
            {
                "id": "default_38x25",
                "code": "TPL-002",
                "name": "Label 38x25mm",
                "paper_size": "label_38x25",
                "width_mm": 38,
                "height_mm": 25,
                "columns": 1,
                "rows": 1,
                "barcode_type": "code128",
                "barcode_source": "barcode",
                "show_item_name": True,
                "show_item_code": False,
                "show_price": True,
                "price_type": "sell",
                "is_active": True
            },
            {
                "id": "default_a4_30",
                "code": "TPL-003",
                "name": "A4 - 30 Label",
                "paper_size": "a4_30",
                "width_mm": 70,
                "height_mm": 29.7,
                "columns": 3,
                "rows": 10,
                "barcode_type": "code128",
                "barcode_source": "barcode",
                "show_item_name": True,
                "show_item_code": True,
                "show_price": True,
                "price_type": "sell",
                "is_active": True
            }
        ]
    
    return {"items": items, "total": total if total else len(items)}

@router.get("/barcode-templates/{template_id}")
async def get_barcode_template(
    template_id: str,
    user: dict = Depends(get_current_user)
):
    """Get barcode template detail"""
    db = get_database()
    
    template = await db.barcode_templates.find_one({"id": template_id}, {"_id": 0})
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return template

@router.post("/barcode-templates")
async def create_barcode_template(
    data: BarcodeTemplateCreate,
    user: dict = Depends(require_permission("master_item", "create"))
):
    """Create barcode template"""
    db = get_database()
    
    code = data.code
    if not code:
        code = await generate_transaction_number(db, "TPL")
    
    template = {
        "id": str(uuid.uuid4()),
        "code": code,
        **data.model_dump(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user.get("user_id")
    }
    
    await db.barcode_templates.insert_one(template)
    
    return {"success": True, "id": template["id"], "code": code}

@router.put("/barcode-templates/{template_id}")
async def update_barcode_template(
    template_id: str,
    data: dict,
    user: dict = Depends(require_permission("master_item", "edit"))
):
    """Update barcode template"""
    db = get_database()
    
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.barcode_templates.update_one(
        {"id": template_id},
        {"$set": data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return {"success": True, "message": "Template updated"}

@router.delete("/barcode-templates/{template_id}")
async def delete_barcode_template(
    template_id: str,
    user: dict = Depends(require_permission("master_item", "delete"))
):
    """Delete barcode template"""
    db = get_database()
    
    result = await db.barcode_templates.delete_one({"id": template_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return {"success": True, "message": "Template deleted"}

# ==================== BARCODE GENERATION ====================

@router.post("/barcode/generate")
async def generate_barcode_data(
    data: dict,
    user: dict = Depends(get_current_user)
):
    """
    Generate barcode data for printing
    Input: template_id, items: [{item_id, qty}]
    Output: List of barcode data ready for printing
    """
    db = get_database()
    
    template_id = data.get("template_id", "default_58x40")
    items_to_print = data.get("items", [])
    
    # Get template
    template = await db.barcode_templates.find_one({"id": template_id}, {"_id": 0})
    if not template:
        # Use default
        template = {
            "barcode_source": "barcode",
            "show_item_name": True,
            "show_item_code": True,
            "show_price": True,
            "price_type": "sell"
        }
    
    barcode_data = []
    
    for item_req in items_to_print:
        item_id = item_req.get("item_id")
        qty = item_req.get("qty", 1)
        
        item = await db.items.find_one({"id": item_id}, {"_id": 0})
        if not item:
            continue
        
        # Determine barcode value
        barcode_source = template.get("barcode_source", "barcode")
        if barcode_source == "barcode":
            barcode_value = item.get("barcode", item.get("code", ""))
        elif barcode_source == "item_code":
            barcode_value = item.get("code", "")
        else:
            barcode_value = item.get("sku", item.get("code", ""))
        
        # Determine price
        price_type = template.get("price_type", "sell")
        if price_type == "sell":
            price = item.get("sell_price", 0)
        elif price_type == "hpp":
            price = item.get("purchase_price", item.get("hpp", 0))
        else:
            price = item.get("sell_price", 0)
        
        for _ in range(qty):
            barcode_data.append({
                "item_id": item_id,
                "item_code": item.get("code", ""),
                "item_name": item.get("name", ""),
                "barcode_value": barcode_value,
                "price": price,
                "unit": item.get("unit", "")
            })
    
    return {
        "success": True,
        "template": template,
        "labels": barcode_data,
        "total_labels": len(barcode_data)
    }
