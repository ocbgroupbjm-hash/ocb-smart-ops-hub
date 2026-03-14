# OCB TITAN - User Management API
# SECURITY: All operations require RBAC validation
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional, List
from database import users, branches, audit_logs, get_db
from utils.auth import get_current_user, hash_password, require_roles
from models.titan_models import User, UserRole, AuditLog
from routes.rbac_middleware import require_permission, log_security_event
from datetime import datetime, timezone

router = APIRouter(prefix="/users", tags=["Users"])

class UserCreate(BaseModel):
    email: str
    password: str
    name: str
    phone: str = ""
    role: str = "cashier"
    branch_id: Optional[str] = None
    branch_ids: List[str] = []

class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    role_id: Optional[str] = None  # Direct role_id override
    branch_id: Optional[str] = None
    branch_ids: Optional[List[str]] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None  # For password reset

class ChangePassword(BaseModel):
    current_password: str
    new_password: str

@router.get("")
async def list_users(
    branch_id: str = "",
    role: str = "",
    search: str = "",
    include_deleted: bool = False,
    limit: int = 200,
    user: dict = Depends(require_permission("master_user", "view"))
):
    """
    List users - Requires master_user.view permission
    
    By default, EXCLUDES deleted users (status = 'deleted').
    Use include_deleted=true to see all users including deleted ones.
    """
    if user.get("role") not in ["owner", "admin"]:
        # Regular users can only see their branch
        branch_id = user.get("branch_id", "")
    
    query = {}
    
    # IMPORTANT: Filter out deleted users by default
    if not include_deleted:
        query["status"] = {"$ne": "deleted"}
    
    if branch_id:
        query["branch_id"] = branch_id
    
    if role:
        query["role"] = role
    
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}}
        ]
    
    items = await users.find(query, {"_id": 0, "password_hash": 0}).sort("name", 1).to_list(limit)
    
    # Enrich with branch names
    for item in items:
        if item.get("branch_id"):
            branch = await branches.find_one({"id": item["branch_id"]}, {"_id": 0, "name": 1})
            item["branch_name"] = branch.get("name", "") if branch else ""
    
    return {"items": items, "total": len(items)}

@router.get("/{user_id}")
async def get_user(user_id: str, user: dict = Depends(require_permission("master_user", "view"))):
    """Get user details - Requires master_user.view permission"""
    user_data = await users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user_data.get("branch_id"):
        branch = await branches.find_one({"id": user_data["branch_id"]}, {"_id": 0, "name": 1, "code": 1})
        user_data["branch"] = branch
    
    return user_data

@router.post("")
async def create_user(data: UserCreate, request: Request, user: dict = Depends(require_permission("master_user", "create"))):
    """
    Create new user - Requires master_user.create permission
    
    VALIDATION RULES:
    - Only owner/admin can create users
    - Email must be valid and unique per tenant
    - Role must exist in tenant's roles collection
    - Branch must exist if provided
    
    STORED FIELDS:
    - tenant_id (from current database)
    - role_id (from roles collection)
    - role_code
    - created_at
    - status
    - audit trail
    """
    if user.get("role") not in ["owner", "admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions: Hanya owner/admin/super_admin yang dapat membuat user baru")
    
    # Validate email format
    if not data.email or "@" not in data.email:
        raise HTTPException(status_code=400, detail="Format email tidak valid")
    
    # Check email uniqueness per tenant
    existing = await users.find_one({"email": data.email})
    if existing:
        raise HTTPException(status_code=400, detail=f"Email '{data.email}' sudah terdaftar di tenant ini")
    
    # Get current database and tenant info
    db = get_db()
    from database import get_active_db_name
    tenant_id = get_active_db_name()
    
    # Validate role code exists
    valid_roles = ["owner", "admin", "finance", "warehouse", "cashier", "super_admin", "manager", "supervisor"]
    role_code = data.role.lower() if data.role else "cashier"
    
    if role_code not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Role '{data.role}' tidak valid. Role yang tersedia: {', '.join(valid_roles)}")
    
    role_doc = await db["roles"].find_one({"code": role_code})
    if not role_doc:
        # Try to find alternative role naming
        alt_role_doc = await db["roles"].find_one({"code": {"$regex": f"^{role_code}", "$options": "i"}})
        if alt_role_doc:
            role_doc = alt_role_doc
        else:
            # Get available roles for error message
            available_roles = await db["roles"].find({}, {"_id": 0, "code": 1}).to_list(20)
            role_codes = [r.get("code") for r in available_roles if r.get("code")]
            raise HTTPException(
                status_code=400, 
                detail=f"Role '{role_code}' tidak ditemukan di tenant '{tenant_id}'. Role tersedia: {', '.join(role_codes)}"
            )
    role_id = role_doc.get("id")
    
    # Validate branch_id if provided
    if data.branch_id:
        branch_exists = await db["branches"].find_one({"id": data.branch_id})
        if not branch_exists:
            # Get available branches for error message
            available_branches = await db["branches"].find({}, {"_id": 0, "id": 1, "name": 1}).to_list(20)
            branch_info = [f"{b.get('name')} ({b.get('id')})" for b in available_branches]
            raise HTTPException(
                status_code=400, 
                detail=f"Branch ID '{data.branch_id}' tidak ditemukan di tenant '{tenant_id}'. Branch tersedia: {', '.join(branch_info)}"
            )
    
    new_user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        name=data.name,
        phone=data.phone,
        role=UserRole(role_code),
        branch_id=data.branch_id,
        branch_ids=data.branch_ids or ([data.branch_id] if data.branch_id else [])
    )
    
    # Add role_id, role_code, and tenant_id to user document
    user_dict = new_user.model_dump()
    user_dict["role_id"] = role_id
    user_dict["role_code"] = role_code
    user_dict["tenant_id"] = tenant_id  # Store tenant for audit
    user_dict["status"] = "active"
    
    await users.insert_one(user_dict)
    
    # Audit log
    log = AuditLog(
        user_id=user.get("user_id", ""),
        user_name=user.get("name", ""),
        action="create",
        module="users",
        entity_type="user",
        entity_id=new_user.id,
        new_value={
            "email": new_user.email, 
            "name": new_user.name, 
            "role": role_code, 
            "role_id": role_id,
            "tenant_id": tenant_id
        }
    )
    await audit_logs.insert_one(log.model_dump())
    
    return {
        "id": new_user.id, 
        "message": "User berhasil dibuat", 
        "role_id": role_id,
        "tenant_id": tenant_id
    }

@router.put("/{user_id}")
async def update_user(user_id: str, data: UserUpdate, request: Request, user: dict = Depends(require_permission("master_user", "edit"))):
    """Update user - Requires master_user.edit permission"""
    if user.get("role") not in ["owner", "admin"] and user.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    target = await users.find_one({"id": user_id}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    
    # Role change requires owner/admin
    if "role" in update_data and user.get("role") not in ["owner", "admin"]:
        del update_data["role"]
    
    # Handle role -> role_id mapping
    if "role" in update_data:
        db = get_db()
        role_code = update_data["role"]
        role_doc = await db["roles"].find_one({"code": role_code})
        if role_doc:
            update_data["role_id"] = role_doc.get("id")
            update_data["role_code"] = role_code
        else:
            raise HTTPException(status_code=400, detail=f"Role '{role_code}' tidak ditemukan di database")
    
    # Handle password update
    if "password" in update_data:
        update_data["password_hash"] = hash_password(update_data.pop("password"))
    
    # Handle branch_id "all" or empty
    if "branch_id" in update_data:
        if update_data["branch_id"] in ["", "all", None]:
            update_data["branch_id"] = None
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await users.update_one({"id": user_id}, {"$set": update_data})
    
    # Audit log
    log = AuditLog(
        user_id=user.get("user_id", ""),
        user_name=user.get("name", ""),
        action="update",
        module="users",
        entity_type="user",
        entity_id=user_id,
        old_value={k: target.get(k) for k in update_data.keys() if k != "password_hash"},
        new_value={k: v for k, v in update_data.items() if k != "password_hash"}
    )
    await audit_logs.insert_one(log.model_dump())
    
    return {"message": "User updated", "user_id": user_id}

@router.post("/{user_id}/change-password")
async def change_password(user_id: str, data: ChangePassword, user: dict = Depends(get_current_user)):
    """Change password (self or admin)"""
    if user.get("user_id") != user_id and user.get("role") not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    target = await users.find_one({"id": user_id})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify current password (only if changing own password)
    if user.get("user_id") == user_id:
        from utils.auth import verify_password
        if not verify_password(data.current_password, target.get("password_hash", "")):
            raise HTTPException(status_code=400, detail="Current password incorrect")
    
    await users.update_one(
        {"id": user_id},
        {"$set": {
            "password_hash": hash_password(data.new_password),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"message": "Password changed"}

@router.delete("/{user_id}")
async def delete_user(user_id: str, hard: bool = False, request: Request = None, user: dict = Depends(require_permission("master_user", "delete"))):
    """
    Delete user (soft or hard delete) - Requires master_user.delete permission
    
    SOFT DELETE RULES:
    - User yang memiliki transaksi → WAJIB soft delete, status = "deleted"
    - User yang tidak memiliki transaksi → boleh hard delete (hanya owner)
    - Transaksi yang dicek: sales_invoices, purchases, journal_entries, stock_movements
    
    SOFT DELETE FIELDS:
    - status = "deleted"
    - is_active = False
    - deleted_at = timestamp
    - deleted_by = user_id yang menghapus
    
    User dengan status = "deleted" TIDAK akan muncul di list users default.
    """
    if user.get("role") not in ["owner", "admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions: Hanya owner/admin/super_admin")
    
    if user.get("user_id") == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    target = await users.find_one({"id": user_id}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if user is already deleted
    if target.get("status") == "deleted":
        raise HTTPException(status_code=400, detail="User sudah dihapus sebelumnya")
    
    db = get_db()
    from database import get_active_db_name
    tenant_id = get_active_db_name()
    now = datetime.now(timezone.utc).isoformat()
    
    # Check if user has transactions (SSOT check)
    transaction_count = 0
    transaction_types = []
    
    # Check sales
    sales_count = await db["sales_invoices"].count_documents({"user_id": user_id})
    if sales_count > 0:
        transaction_count += sales_count
        transaction_types.append(f"sales: {sales_count}")
    
    # Check purchases
    purchase_count = await db["purchase_orders"].count_documents({"user_id": user_id})
    if purchase_count > 0:
        transaction_count += purchase_count
        transaction_types.append(f"purchases: {purchase_count}")
    
    # Check journals
    journal_count = await db["journal_entries"].count_documents({"created_by": user_id})
    if journal_count > 0:
        transaction_count += journal_count
        transaction_types.append(f"journals: {journal_count}")
    
    # Check stock movements
    stock_count = await db["stock_movements"].count_documents({"user_id": user_id})
    if stock_count > 0:
        transaction_count += stock_count
        transaction_types.append(f"stock_movements: {stock_count}")
    
    has_transactions = transaction_count > 0
    
    if hard and user.get("role") == "owner" and not has_transactions:
        # Hard delete - only owner can do this and only if no transactions
        result = await users.delete_one({"id": user_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=500, detail="Delete operation failed")
        message = "User permanently deleted (hard delete)"
        action = "hard_delete"
        deleted_permanently = True
    elif hard and has_transactions:
        # Cannot hard delete if user has transactions
        raise HTTPException(
            status_code=400, 
            detail=f"DILARANG hard delete user yang memiliki transaksi ({', '.join(transaction_types)}). Gunakan soft delete."
        )
    else:
        # SOFT DELETE - Set status = "deleted"
        result = await users.update_one(
            {"id": user_id},
            {"$set": {
                "is_active": False, 
                "status": "deleted",  # CRITICAL: Must be "deleted" not "inactive"
                "deleted_at": now,    # WAJIB: timestamp penghapusan
                "deleted_by": user.get("user_id", ""),  # WAJIB: siapa yang menghapus
                "updated_at": now
            }}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=500, detail="Delete operation failed - user not found")
        if result.modified_count == 0:
            raise HTTPException(status_code=500, detail="Delete operation failed - no changes made")
        
        message = f"User berhasil dihapus (soft delete)" 
        if has_transactions:
            message += f" - memiliki {transaction_count} transaksi yang dipertahankan"
        action = "soft_delete"
        deleted_permanently = False
    
    # Audit log - WAJIB untuk semua delete
    log = AuditLog(
        user_id=user.get("user_id", ""),
        user_name=user.get("name", ""),
        action=action,
        module="users",
        entity_type="user",
        entity_id=user_id,
        old_value={
            "email": target.get("email"), 
            "name": target.get("name"),
            "role": target.get("role"),
            "status": target.get("status", "active"),
            "tenant_id": tenant_id,
            "has_transactions": has_transactions,
            "transaction_count": transaction_count,
            "transaction_types": transaction_types
        },
        new_value={
            "status": "deleted" if not deleted_permanently else "permanently_deleted",
            "deleted_at": now,
            "deleted_by": user.get("user_id", "")
        }
    )
    await audit_logs.insert_one(log.model_dump())
    
    return {
        "success": True,
        "message": message, 
        "user_id": user_id,
        "action": action,
        "deleted_permanently": deleted_permanently if 'deleted_permanently' in dir() else False,
        "has_transactions": has_transactions,
        "transaction_count": transaction_count,
        "deleted_at": now,
        "deleted_by": user.get("user_id", "")
    }

# ==================== AUDIT LOGS ====================

@router.get("/audit/logs")
async def get_audit_logs(
    module: str = "",
    user_id: str = "",
    date_from: str = "",
    skip: int = 0,
    limit: int = 100,
    user: dict = Depends(require_permission("audit_log", "view"))
):
    """Get audit logs - Requires audit_log.view permission"""
    if user.get("role") not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    query = {}
    
    if module:
        query["module"] = module
    
    if user_id:
        query["user_id"] = user_id
    
    if date_from:
        query["timestamp"] = {"$gte": date_from}
    
    items = await audit_logs.find(query, {"_id": 0}).sort("timestamp", -1).skip(skip).limit(limit).to_list(limit)
    total = await audit_logs.count_documents(query)
    
    return {"items": items, "total": total}
