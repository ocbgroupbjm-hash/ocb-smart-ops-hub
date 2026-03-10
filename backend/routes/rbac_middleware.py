# OCB TITAN ERP - CENTRALIZED RBAC MIDDLEWARE
# Reusable permission check for all API routes
# SECURITY CRITICAL: All destructive actions MUST use these decorators

from fastapi import HTTPException, Depends, Request
from functools import wraps
from datetime import datetime, timezone
import uuid
import hashlib

def get_db():
    from database import get_db as db_get
    return db_get()

from routes.auth import get_current_user


# ==================== CORE PERMISSION CHECK ====================

async def check_permission(user_id: str, module: str, action: str) -> bool:
    """
    FAIL-SAFE: Default is DENY
    Check permission with role hierarchy support
    """
    db = get_db()
    
    # Get user with role
    user = await db["users"].find_one({"id": user_id}, {"_id": 0, "role_id": 1, "branch_access": 1, "role_code": 1})
    if not user or not user.get("role_id"):
        return False
    
    # Get role
    role = await db["roles"].find_one({"id": user["role_id"]}, {"_id": 0})
    if not role:
        return False
    
    # SUPER ADMIN / PEMILIK = FULL ACCESS
    role_code = role.get("code") or user.get("role_code")
    if role.get("inherit_all") or role_code in ["super_admin", "pemilik", "owner", "admin"]:
        return True
    
    # VIEW ONLY role
    if role.get("view_only") and action != "view":
        return False
    
    # Check specific permission
    permission = await db["role_permissions"].find_one({
        "role_id": user["role_id"],
        "module": module,
        "action": action,
        "allowed": True
    }, {"_id": 0})
    
    if permission:
        return True
    
    # Check inherited permissions
    inherit_from = role.get("inherit_from", [])
    for inherited_role_code in inherit_from:
        inherited_role = await db["roles"].find_one({"code": inherited_role_code}, {"_id": 0, "id": 1})
        if inherited_role:
            inherited_perm = await db["role_permissions"].find_one({
                "role_id": inherited_role["id"],
                "module": module,
                "action": action,
                "allowed": True
            }, {"_id": 0})
            if inherited_perm:
                return True
    
    return False


async def check_branch_access(user_id: str, branch_id: str) -> bool:
    """Check if user has access to specific branch"""
    db = get_db()
    
    user = await db["users"].find_one({"id": user_id}, {"_id": 0, "role_id": 1, "branch_access": 1, "all_branches": 1, "branch_id": 1})
    if not user:
        return False
    
    if user.get("all_branches"):
        return True
    
    role = await db["roles"].find_one({"id": user.get("role_id")}, {"_id": 0, "all_branches": 1, "inherit_all": 1})
    if role:
        if role.get("all_branches") or role.get("inherit_all"):
            return True
    
    # User's own branch
    if user.get("branch_id") == branch_id:
        return True
    
    # Check branch_access list
    branch_access = user.get("branch_access", [])
    return branch_id in branch_access


# ==================== AUDIT LOGGING ====================

async def log_security_event(
    db,
    user_id: str,
    user_name: str,
    action: str,
    module: str,
    description: str,
    ip_address: str = "",
    branch_id: str = "",
    data_before: dict = None,
    data_after: dict = None,
    severity: str = "normal",
    document_no: str = ""
):
    """Enterprise audit logging for security events"""
    log_entry = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "user_name": user_name,
        "action": action,
        "module": module,
        "description": description,
        "document_no": document_no,
        "ip_address": ip_address,
        "branch_id": branch_id,
        "data_before": data_before,
        "data_after": data_after,
        "severity": severity,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "checksum": hashlib.sha256(f"{user_id}{action}{module}{datetime.now().isoformat()}".encode()).hexdigest()[:16]
    }
    await db["audit_logs"].insert_one(log_entry)
    
    # Auto-create security alert for critical actions
    if severity == "critical" or action in ["delete", "void", "override_price", "override_stock", "approve"]:
        await db["security_alerts"].insert_one({
            "id": str(uuid.uuid4()),
            "alert_type": "sensitive_action",
            "severity": "high" if action == "delete" else "medium",
            "module": module,
            "description": f"{user_name} performed {action} on {module}: {description}",
            "user_id": user_id,
            "log_id": log_entry["id"],
            "acknowledged": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    
    return log_entry


# ==================== PERMISSION DEPENDENCY ====================

def require_permission(module: str, action: str):
    """
    FAIL-SAFE Dependency for FastAPI routes
    Usage: Depends(require_permission("sales", "delete"))
    
    Returns 403 Forbidden if permission is denied
    """
    async def permission_dependency(request: Request, user: dict = Depends(get_current_user)):
        user_id = user.get("user_id") or user.get("id")
        has_perm = await check_permission(user_id, module, action)
        
        if not has_perm:
            db = get_db()
            await log_security_event(
                db, user_id, user.get("name", "Unknown"),
                "access_denied", module,
                f"BLOCKED: {action} pada {module}",
                request.client.host if request.client else "",
                severity="warning"
            )
            raise HTTPException(
                status_code=403,
                detail=f"AKSES DITOLAK: Anda tidak memiliki izin untuk {action} pada modul {module}"
            )
        return user
    return permission_dependency


def require_branch_access(branch_param: str = "branch_id"):
    """
    Branch access check dependency
    Usage: Depends(require_branch_access())
    """
    async def branch_dependency(request: Request, user: dict = Depends(get_current_user)):
        # Get branch_id from query, path, or body
        branch_id = request.query_params.get(branch_param)
        if not branch_id:
            branch_id = request.path_params.get(branch_param)
        
        if branch_id:
            user_id = user.get("user_id") or user.get("id")
            has_access = await check_branch_access(user_id, branch_id)
            if not has_access:
                db = get_db()
                await log_security_event(
                    db, user_id, user.get("name", "Unknown"),
                    "branch_access_denied", "branch",
                    f"BLOCKED: Akses cabang {branch_id}",
                    request.client.host if request.client else "",
                    severity="warning"
                )
                raise HTTPException(
                    status_code=403,
                    detail="AKSES DITOLAK: Anda tidak memiliki akses ke cabang ini"
                )
        return user
    return branch_dependency


# ==================== SCOPE CHECK ====================

async def check_data_scope(user_id: str, data_owner_id: str = None, data_branch_id: str = None) -> bool:
    """
    Check if user can access specific data based on scope
    Scope levels:
    - own_only: Can only access own data
    - branch_only: Can access data from own branch
    - all: Can access all data
    """
    db = get_db()
    
    user = await db["users"].find_one({"id": user_id}, {"_id": 0})
    if not user:
        return False
    
    role = await db["roles"].find_one({"id": user.get("role_id")}, {"_id": 0})
    if not role:
        return False
    
    # Super admin / pemilik = all access
    if role.get("inherit_all") or role.get("code") in ["super_admin", "pemilik", "owner"]:
        return True
    
    # Check data ownership
    if data_owner_id and data_owner_id == user_id:
        return True
    
    # Check branch access
    if data_branch_id:
        return await check_branch_access(user_id, data_branch_id)
    
    # Default deny for kasir accessing other's data
    role_code = role.get("code", "").lower()
    if role_code in ["kasir", "cashier"]:
        if data_owner_id and data_owner_id != user_id:
            return False
    
    return True


# ==================== HELPER FUNCTIONS ====================

async def get_user_allowed_branches(user_id: str) -> list:
    """Get list of branch IDs user can access"""
    db = get_db()
    
    user = await db["users"].find_one({"id": user_id}, {"_id": 0})
    if not user:
        return []
    
    role = await db["roles"].find_one({"id": user.get("role_id")}, {"_id": 0})
    
    # Full access
    if role and (role.get("all_branches") or role.get("inherit_all")):
        branches = await db["branches"].find({}, {"_id": 0, "id": 1}).to_list(1000)
        return [b["id"] for b in branches]
    
    if user.get("all_branches"):
        branches = await db["branches"].find({}, {"_id": 0, "id": 1}).to_list(1000)
        return [b["id"] for b in branches]
    
    # Specific branches
    branch_access = user.get("branch_access", [])
    if user.get("branch_id"):
        if user["branch_id"] not in branch_access:
            branch_access.append(user["branch_id"])
    
    return branch_access


async def get_user_role_level(user_id: str) -> int:
    """Get user's role level (0=highest, 8=lowest)"""
    db = get_db()
    
    user = await db["users"].find_one({"id": user_id}, {"_id": 0, "role_id": 1})
    if not user:
        return 99
    
    role = await db["roles"].find_one({"id": user.get("role_id")}, {"_id": 0, "level": 1})
    if not role:
        return 99
    
    return role.get("level", 99)


async def can_user_manage_user(manager_id: str, target_user_id: str) -> bool:
    """Check if manager can manage target user (based on role hierarchy)"""
    manager_level = await get_user_role_level(manager_id)
    target_level = await get_user_role_level(target_user_id)
    
    # Can only manage users with higher level number (lower authority)
    return manager_level < target_level
