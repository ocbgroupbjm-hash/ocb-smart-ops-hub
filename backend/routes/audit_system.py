# OCB TITAN ERP - Centralized Audit System
# APPEND-ONLY audit logs - tidak boleh diubah atau dihapus
# MASTER BLUEPRINT: Every module must log to this system
# RBAC: Only OWNER, SUPER_ADMIN, AUDITOR can access

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from datetime import datetime, timezone
from database import get_db
from utils.auth import get_current_user
from routes.rbac_middleware import require_permission
import uuid
import hashlib
import json

router = APIRouter(prefix="/audit", tags=["Audit System"])

# ==================== RBAC FOR AUDIT ====================

AUDIT_ALLOWED_ROLES = ["owner", "super_admin", "auditor"]

def require_audit_role():
    """
    Middleware to check if user has audit access permission.
    Only OWNER, SUPER_ADMIN, AUDITOR can access audit logs.
    """
    async def check_audit_role(request: Request, user: dict = Depends(get_current_user)):
        user_role = (user.get("role", "") or "").lower()
        user_role_code = (user.get("role_code", "") or "").lower()
        
        # Check if user has allowed role
        has_role = user_role in AUDIT_ALLOWED_ROLES or user_role_code in AUDIT_ALLOWED_ROLES
        
        # Also check permissions array for wildcard
        permissions = user.get("permissions", [])
        has_wildcard = "*" in permissions
        has_audit_perm = "audit_log.view" in permissions or "audit" in permissions
        
        if not (has_role or has_wildcard or has_audit_perm):
            raise HTTPException(
                status_code=403,
                detail="AKSES DITOLAK: Hanya OWNER, SUPER_ADMIN, atau AUDITOR yang dapat mengakses audit logs"
            )
        return user
    return check_audit_role

# ==================== CONSTANTS ====================

AUDITABLE_MODULES = [
    "users", "products", "categories", "suppliers", "customers",
    "sales", "purchases", "inventory", "stock_movements",
    "journal_entries", "accounts", "cash_control", "shifts",
    "payroll", "employees", "branches", "settings", "rbac"
]

AUDIT_ACTIONS = [
    "create", "update", "delete", "soft_delete", "restore",
    "approve", "reject", "post", "void", "login", "logout",
    "export", "import", "print", "shift_open", "shift_close"
]


# ==================== PYDANTIC MODELS ====================

class AuditLogEntry(BaseModel):
    module: str = Field(..., description="Module name (users, products, sales, etc.)")
    action: str = Field(..., description="Action performed (create, update, delete, etc.)")
    entity_type: str = Field(..., description="Entity type (user, product, invoice, etc.)")
    entity_id: str = Field(..., description="ID of the affected entity")
    before_data: Optional[Dict[str, Any]] = Field(None, description="Data before change")
    after_data: Optional[Dict[str, Any]] = Field(None, description="Data after change")
    description: Optional[str] = Field("", description="Human-readable description")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class AuditQueryParams(BaseModel):
    module: Optional[str] = None
    action: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    user_id: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    ip_address: Optional[str] = None


# ==================== HELPER FUNCTIONS ====================

def generate_audit_hash(data: dict) -> str:
    """Generate SHA256 hash of audit entry for integrity verification"""
    canonical = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()


def get_client_ip(request: Request) -> str:
    """Extract client IP from request headers"""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


async def create_audit_log(
    db,
    module: str,
    action: str,
    entity_type: str,
    entity_id: str,
    user_id: str,
    user_name: str,
    before_data: dict = None,
    after_data: dict = None,
    description: str = "",
    ip_address: str = "",
    metadata: dict = None
) -> dict:
    """
    Create an append-only audit log entry
    
    This function is used internally by all modules to log changes.
    The audit log is immutable - no updates or deletes allowed.
    """
    
    # Build audit entry
    audit_entry = {
        "id": str(uuid.uuid4()),
        "tenant_id": db.name,  # Database name = tenant_id
        "module": module,
        "action": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "user_id": user_id,
        "user_name": user_name,
        "before_data": before_data,
        "after_data": after_data,
        "description": description,
        "ip_address": ip_address,
        "metadata": metadata or {},
        "created_at": datetime.now(timezone.utc).isoformat(),
        "timestamp_unix": int(datetime.now(timezone.utc).timestamp() * 1000)
    }
    
    # Generate integrity hash (for tamper detection)
    audit_entry["integrity_hash"] = generate_audit_hash({
        "module": module,
        "action": action,
        "entity_id": entity_id,
        "user_id": user_id,
        "created_at": audit_entry["created_at"],
        "before_data": before_data,
        "after_data": after_data
    })
    
    # Insert into audit_logs collection (APPEND ONLY)
    await db["audit_logs"].insert_one(audit_entry)
    
    # Remove MongoDB _id for return
    audit_entry.pop("_id", None)
    
    return audit_entry


# ==================== API ENDPOINTS ====================

@router.post("/log")
async def log_audit_entry(
    data: AuditLogEntry,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """
    Create a new audit log entry
    
    This endpoint is called by modules to log their actions.
    The log is APPEND-ONLY - cannot be modified or deleted.
    """
    db = get_db()
    
    ip_address = get_client_ip(request)
    
    audit_entry = await create_audit_log(
        db=db,
        module=data.module,
        action=data.action,
        entity_type=data.entity_type,
        entity_id=data.entity_id,
        user_id=user.get("user_id", ""),
        user_name=user.get("name", ""),
        before_data=data.before_data,
        after_data=data.after_data,
        description=data.description,
        ip_address=ip_address,
        metadata=data.metadata
    )
    
    return {"success": True, "audit_id": audit_entry["id"]}


@router.get("/logs")
async def get_audit_logs(
    module: Optional[str] = None,
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    user_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    ip_address: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    user: dict = Depends(require_audit_role())
):
    """
    Query audit logs with filters
    
    RBAC: Only OWNER, SUPER_ADMIN, AUDITOR can view audit logs.
    """
    db = get_db()
    
    # Build query
    query = {}
    
    # Filter by specific criteria
    if user_id:
        query["user_id"] = user_id
    
    if module:
        query["module"] = module
    
    if action:
        query["action"] = action
    
    if entity_type:
        query["entity_type"] = entity_type
    
    if entity_id:
        query["entity_id"] = entity_id
    
    if ip_address:
        query["ip_address"] = ip_address
    
    if date_from or date_to:
        query["created_at"] = {}
        if date_from:
            query["created_at"]["$gte"] = date_from
        if date_to:
            query["created_at"]["$lte"] = date_to + "T23:59:59"
    
    # Execute query
    total = await db["audit_logs"].count_documents(query)
    
    logs = await db["audit_logs"].find(query, {"_id": 0}).sort(
        "created_at", -1
    ).skip(skip).limit(limit).to_list(limit)
    
    return {
        "items": logs,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/logs/{entity_id}/history")
async def get_entity_history(
    entity_id: str,
    user: dict = Depends(require_audit_role())
):
    """
    Get complete audit history for a specific entity
    
    Shows all changes made to an entity over time.
    
    RBAC: Only OWNER, SUPER_ADMIN, AUDITOR can access.
    """
    db = get_db()
    
    logs = await db["audit_logs"].find(
        {"entity_id": entity_id},
        {"_id": 0}
    ).sort("created_at", 1).to_list(1000)
    
    if not logs:
        raise HTTPException(status_code=404, detail="No audit history found for this entity")
    
    return {
        "entity_id": entity_id,
        "total_changes": len(logs),
        "first_action": logs[0] if logs else None,
        "last_action": logs[-1] if logs else None,
        "history": logs
    }


@router.get("/summary")
async def get_audit_summary(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    user: dict = Depends(require_audit_role())
):
    """
    Get audit log summary statistics
    
    RBAC: Only OWNER, SUPER_ADMIN, AUDITOR can access.
    """
    db = get_db()
    
    # Build date filter
    date_filter = {}
    if date_from or date_to:
        date_filter["created_at"] = {}
        if date_from:
            date_filter["created_at"]["$gte"] = date_from
        if date_to:
            date_filter["created_at"]["$lte"] = date_to + "T23:59:59"
    
    # Aggregate by module
    module_pipeline = [
        {"$match": date_filter} if date_filter else {"$match": {}},
        {"$group": {"_id": "$module", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    by_module = await db["audit_logs"].aggregate(module_pipeline).to_list(100)
    
    # Aggregate by action
    action_pipeline = [
        {"$match": date_filter} if date_filter else {"$match": {}},
        {"$group": {"_id": "$action", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    by_action = await db["audit_logs"].aggregate(action_pipeline).to_list(100)
    
    # Aggregate by user
    user_pipeline = [
        {"$match": date_filter} if date_filter else {"$match": {}},
        {"$group": {"_id": {"user_id": "$user_id", "user_name": "$user_name"}, "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 20}
    ]
    by_user = await db["audit_logs"].aggregate(user_pipeline).to_list(20)
    
    # Total count
    total = await db["audit_logs"].count_documents(date_filter if date_filter else {})
    
    return {
        "total_logs": total,
        "by_module": {item["_id"]: item["count"] for item in by_module if item["_id"]},
        "by_action": {item["_id"]: item["count"] for item in by_action if item["_id"]},
        "top_users": [
            {"user_id": item["_id"]["user_id"], "user_name": item["_id"]["user_name"], "count": item["count"]}
            for item in by_user if item["_id"]
        ]
    }


@router.get("/verify/{audit_id}")
async def verify_audit_integrity(
    audit_id: str,
    user: dict = Depends(require_audit_role())
):
    """
    Verify integrity of an audit log entry
    
    Recalculates the hash and compares with stored hash
    to detect any tampering.
    
    RBAC: Only OWNER, SUPER_ADMIN, AUDITOR can access.
    """
    db = get_db()
    
    log = await db["audit_logs"].find_one({"id": audit_id}, {"_id": 0})
    
    if not log:
        raise HTTPException(status_code=404, detail="Audit log not found")
    
    # Recalculate hash
    recalculated_hash = generate_audit_hash({
        "module": log.get("module"),
        "action": log.get("action"),
        "entity_id": log.get("entity_id"),
        "user_id": log.get("user_id"),
        "created_at": log.get("created_at"),
        "before_data": log.get("before_data"),
        "after_data": log.get("after_data")
    })
    
    stored_hash = log.get("integrity_hash", "")
    is_valid = recalculated_hash == stored_hash
    
    return {
        "audit_id": audit_id,
        "is_valid": is_valid,
        "stored_hash": stored_hash,
        "calculated_hash": recalculated_hash,
        "status": "VALID - No tampering detected" if is_valid else "INVALID - Possible tampering!"
    }


# ==================== FORBIDDEN OPERATIONS ====================
# These endpoints exist to explicitly block modification/deletion

@router.put("/logs/{audit_id}")
async def block_update():
    """Audit logs are APPEND-ONLY. Updates are not allowed."""
    raise HTTPException(
        status_code=403, 
        detail="FORBIDDEN: Audit logs are APPEND-ONLY and cannot be modified."
    )


@router.delete("/logs/{audit_id}")
async def block_delete():
    """Audit logs are APPEND-ONLY. Deletion is not allowed."""
    raise HTTPException(
        status_code=403, 
        detail="FORBIDDEN: Audit logs are APPEND-ONLY and cannot be deleted."
    )


@router.delete("/logs")
async def block_bulk_delete():
    """Audit logs are APPEND-ONLY. Bulk deletion is not allowed."""
    raise HTTPException(
        status_code=403, 
        detail="FORBIDDEN: Audit logs are APPEND-ONLY and cannot be deleted."
    )
