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
    limit: int = 200,
    user: dict = Depends(require_permission("master_user", "view"))
):
    """List users - Requires master_user.view permission"""
    if user.get("role") not in ["owner", "admin"]:
        # Regular users can only see their branch
        branch_id = user.get("branch_id", "")
    
    query = {}
    
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
    """Create new user - Requires master_user.create permission"""
    if user.get("role") not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    existing = await users.find_one({"email": data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Get current database and find role
    db = get_db()
    role_code = data.role if data.role in [r.value for r in UserRole] else "cashier"
    role_doc = await db["roles"].find_one({"code": role_code})
    role_id = role_doc.get("id") if role_doc else None
    
    new_user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        name=data.name,
        phone=data.phone,
        role=UserRole(role_code),
        branch_id=data.branch_id,
        branch_ids=data.branch_ids or ([data.branch_id] if data.branch_id else [])
    )
    
    # Add role_id and role_code to user document
    user_dict = new_user.model_dump()
    user_dict["role_id"] = role_id
    user_dict["role_code"] = role_code
    
    await users.insert_one(user_dict)
    
    # Audit log
    log = AuditLog(
        user_id=user.get("user_id", ""),
        user_name=user.get("name", ""),
        action="create",
        module="users",
        entity_type="user",
        entity_id=new_user.id,
        new_value={"email": new_user.email, "name": new_user.name, "role": role_code, "role_id": role_id}
    )
    await audit_logs.insert_one(log.model_dump())
    
    return {"id": new_user.id, "message": "User created"}

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
    
    # Handle password update
    if "password" in update_data:
        update_data["password_hash"] = hash_password(update_data.pop("password"))
    
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
    
    return {"message": "User updated"}

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
    """Delete user (soft or hard delete) - Requires master_user.delete permission"""
    if user.get("role") not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    if user.get("user_id") == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    target = await users.find_one({"id": user_id}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    
    if hard and user.get("role") == "owner":
        # Hard delete - only owner can do this
        result = await users.delete_one({"id": user_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        message = "User permanently deleted"
    else:
        # Soft delete - deactivate
        result = await users.update_one(
            {"id": user_id},
            {"$set": {"is_active": False, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        message = "User deactivated"
    
    # Audit log
    log = AuditLog(
        user_id=user.get("user_id", ""),
        user_name=user.get("name", ""),
        action="delete",
        module="users",
        entity_type="user",
        entity_id=user_id,
        old_value={"email": target.get("email"), "name": target.get("name")}
    )
    await audit_logs.insert_one(log.model_dump())
    
    return {"message": message}

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
