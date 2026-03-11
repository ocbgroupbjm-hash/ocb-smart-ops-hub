# OCB TITAN - Branches, Customers, Suppliers API
# SECURITY: All operations require RBAC validation
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional, List
from database import branches, customers, suppliers, users, get_next_sequence, get_db
from utils.auth import get_current_user
from models.titan_models import Branch, Customer, Supplier, CustomerSegment
from routes.rbac_middleware import require_permission, log_security_event
from datetime import datetime, timezone

router = APIRouter(tags=["Master Data"])

# ==================== BRANCHES ====================

class BranchCreate(BaseModel):
    code: str
    name: str
    address: str = ""
    city: str = ""
    phone: str = ""
    email: str = ""
    is_warehouse: bool = False

class BranchUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    is_active: Optional[bool] = None
    manager_id: Optional[str] = None

@router.get("/branches")
async def list_branches(
    is_active: bool = True,
    user: dict = Depends(require_permission("master_branch", "view"))
):
    """List branches - Requires master_branch.view permission"""
    query = {"is_active": is_active}
    items = await branches.find(query, {"_id": 0}).sort("name", 1).to_list(500)
    
    # Add employee count
    for branch in items:
        count = await users.count_documents({"branch_id": branch["id"], "is_active": True})
        branch["employee_count"] = count
    
    return items

@router.get("/branches/{branch_id}")
async def get_branch(branch_id: str, user: dict = Depends(require_permission("master_branch", "view"))):
    """Get branch details - Requires master_branch.view permission"""
    branch = await branches.find_one({"id": branch_id}, {"_id": 0})
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")
    
    # Get employees
    employees = await users.find(
        {"branch_id": branch_id, "is_active": True},
        {"_id": 0, "password_hash": 0}
    ).to_list(200)
    branch["employees"] = employees
    
    return branch

@router.post("/branches")
async def create_branch(data: BranchCreate, request: Request, user: dict = Depends(require_permission("master_branch", "create"))):
    """Create branch - Requires master_branch.create permission"""
    existing = await branches.find_one({"code": data.code})
    if existing:
        raise HTTPException(status_code=400, detail="Branch code already exists")
    
    branch = Branch(**data.model_dump())
    await branches.insert_one(branch.model_dump())
    
    # Audit log
    db = get_db()
    await log_security_event(
        db, user.get("user_id", ""), user.get("name", ""),
        "create", "master_branch",
        f"Membuat cabang baru: {data.name} ({data.code})",
        request.client.host if request.client else ""
    )
    
    return {"id": branch.id, "message": "Branch created"}

@router.put("/branches/{branch_id}")
async def update_branch(branch_id: str, data: BranchUpdate, request: Request, user: dict = Depends(require_permission("master_branch", "edit"))):
    """Update branch - Requires master_branch.edit permission"""
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await branches.update_one({"id": branch_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Branch not found")
    
    # Audit log
    db = get_db()
    await log_security_event(
        db, user.get("user_id", ""), user.get("name", ""),
        "edit", "master_branch",
        f"Update cabang: {branch_id}",
        request.client.host if request.client else ""
    )
    
    return {"message": "Branch updated"}

# ==================== CUSTOMERS ====================

class CustomerCreate(BaseModel):
    name: str
    phone: str
    email: str = ""
    address: str = ""
    city: str = ""
    segment: str = "regular"
    notes: str = ""

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    segment: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None

@router.get("/customers")
async def list_customers(
    search: str = "",
    segment: str = "",
    skip: int = 0,
    limit: int = 100,
    user: dict = Depends(require_permission("master_customer", "view"))
):
    """List customers - Requires master_customer.view permission"""
    query = {"is_active": True}
    
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"phone": {"$regex": search, "$options": "i"}},
            {"code": {"$regex": search, "$options": "i"}}
        ]
    
    if segment:
        query["segment"] = segment
    
    items = await customers.find(query, {"_id": 0}).sort("name", 1).skip(skip).limit(limit).to_list(limit)
    total = await customers.count_documents(query)
    
    return {"items": items, "total": total}

@router.get("/customers/search")
async def search_customers(q: str, user: dict = Depends(require_permission("master_customer", "view"))):
    """Quick search for POS - Requires master_customer.view permission"""
    query = {
        "is_active": True,
        "$or": [
            {"name": {"$regex": q, "$options": "i"}},
            {"phone": {"$regex": q, "$options": "i"}}
        ]
    }
    
    items = await customers.find(query, {"_id": 0}).limit(10).to_list(10)
    return items

@router.get("/customers/{customer_id}")
async def get_customer(customer_id: str, user: dict = Depends(require_permission("master_customer", "view"))):
    """Get customer details - Requires master_customer.view permission"""
    customer = await customers.find_one({"id": customer_id}, {"_id": 0})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Get transaction history
    from database import transactions
    tx_history = await transactions.find(
        {"customer_id": customer_id},
        {"_id": 0, "id": 1, "invoice_number": 1, "total": 1, "created_at": 1}
    ).sort("created_at", -1).limit(20).to_list(20)
    customer["transactions"] = tx_history
    
    return customer

@router.post("/customers")
async def create_customer(data: CustomerCreate, request: Request, user: dict = Depends(require_permission("master_customer", "create"))):
    """Create customer - Requires master_customer.create permission"""
    # Check duplicate phone
    existing = await customers.find_one({"phone": data.phone})
    if existing:
        raise HTTPException(status_code=400, detail="Phone number already registered")
    
    code = await get_next_sequence("customer_code", "CUS")
    
    customer = Customer(
        code=code,
        segment=CustomerSegment(data.segment) if data.segment in [s.value for s in CustomerSegment] else CustomerSegment.REGULAR,
        **{k: v for k, v in data.model_dump().items() if k != "segment"}
    )
    
    await customers.insert_one(customer.model_dump())
    
    # Audit log
    db = get_db()
    await log_security_event(
        db, user.get("user_id", ""), user.get("name", ""),
        "create", "master_customer",
        f"Membuat customer baru: {data.name} ({code})",
        request.client.host if request.client else ""
    )
    
    return {"id": customer.id, "code": code, "message": "Customer created"}

@router.put("/customers/{customer_id}")
async def update_customer(customer_id: str, data: CustomerUpdate, request: Request, user: dict = Depends(require_permission("master_customer", "edit"))):
    """Update customer - Requires master_customer.edit permission"""
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await customers.update_one({"id": customer_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Audit log
    db = get_db()
    await log_security_event(
        db, user.get("user_id", ""), user.get("name", ""),
        "edit", "master_customer",
        f"Update customer: {customer_id}",
        request.client.host if request.client else ""
    )
    
    return {"message": "Customer updated"}

# ==================== SUPPLIERS ====================

class SupplierCreate(BaseModel):
    code: str
    name: str
    contact_person: str = ""
    phone: str = ""
    email: str = ""
    address: str = ""
    city: str = ""
    payment_terms: int = 30
    bank_name: str = ""
    bank_account: str = ""
    bank_holder: str = ""
    notes: str = ""

class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    payment_terms: Optional[int] = None
    is_active: Optional[bool] = None

@router.get("/suppliers")
async def list_suppliers(
    search: str = "",
    skip: int = 0,
    limit: int = 100,
    user: dict = Depends(require_permission("master_supplier", "view"))
):
    """List suppliers - Requires master_supplier.view permission"""
    query = {"is_active": True}
    
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"code": {"$regex": search, "$options": "i"}}
        ]
    
    items = await suppliers.find(query, {"_id": 0}).sort("name", 1).skip(skip).limit(limit).to_list(limit)
    total = await suppliers.count_documents(query)
    
    return {"items": items, "total": total}

@router.get("/suppliers/{supplier_id}")
async def get_supplier(supplier_id: str, user: dict = Depends(require_permission("master_supplier", "view"))):
    """Get supplier details - Requires master_supplier.view permission"""
    supplier = await suppliers.find_one({"id": supplier_id}, {"_id": 0})
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return supplier

@router.post("/suppliers")
async def create_supplier(data: SupplierCreate, request: Request, user: dict = Depends(require_permission("master_supplier", "create"))):
    """Create supplier - Requires master_supplier.create permission"""
    existing = await suppliers.find_one({"code": data.code})
    if existing:
        raise HTTPException(status_code=400, detail="Supplier code already exists")
    
    supplier = Supplier(**data.model_dump())
    await suppliers.insert_one(supplier.model_dump())
    
    # Audit log
    db = get_db()
    await log_security_event(
        db, user.get("user_id", ""), user.get("name", ""),
        "create", "master_supplier",
        f"Membuat supplier baru: {data.name} ({data.code})",
        request.client.host if request.client else ""
    )
    
    return {"id": supplier.id, "message": "Supplier created"}

@router.put("/suppliers/{supplier_id}")
async def update_supplier(supplier_id: str, data: SupplierUpdate, request: Request, user: dict = Depends(require_permission("master_supplier", "edit"))):
    """Update supplier - Requires master_supplier.edit permission"""
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await suppliers.update_one({"id": supplier_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    # Audit log
    db = get_db()
    await log_security_event(
        db, user.get("user_id", ""), user.get("name", ""),
        "edit", "master_supplier",
        f"Update supplier: {supplier_id}",
        request.client.host if request.client else ""
    )
    
    return {"message": "Supplier updated"}
