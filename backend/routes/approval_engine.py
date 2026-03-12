# OCB TITAN ERP - APPROVAL ENGINE
# Workflow approval untuk transaksi yang memerlukan otorisasi

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from database import db
from utils.auth import get_current_user
from routes.rbac_system import check_permission, log_activity
import uuid

router = APIRouter(prefix="/api/approval", tags=["Approval Engine"])

# Collections
approval_rules = db["approval_rules"]
approval_requests = db["approval_requests"]

# ==================== APPROVAL MODULES ====================
APPROVAL_MODULES = {
    "purchase": {"name": "Pembelian", "condition_types": ["amount"]},
    "purchase_return": {"name": "Retur Pembelian", "condition_types": ["amount", "percentage"]},
    "sales_void": {"name": "Void Penjualan", "condition_types": ["amount"]},
    "sales_return": {"name": "Retur Penjualan", "condition_types": ["amount", "percentage"]},
    "sales_discount": {"name": "Diskon Penjualan", "condition_types": ["percentage"]},
    "price_override": {"name": "Override Harga", "condition_types": ["percentage", "amount"]},
    "stock_adjustment": {"name": "Adjustment Stok", "condition_types": ["quantity", "amount"]},
    "deposit_difference": {"name": "Selisih Setoran", "condition_types": ["amount", "percentage"]},
    "ar_write_off": {"name": "Write-off Piutang", "condition_types": ["amount"]},
    "journal_manual": {"name": "Jurnal Manual", "condition_types": ["amount"]},
    "expense": {"name": "Pengeluaran", "condition_types": ["amount"]}
}

# ==================== PYDANTIC MODELS ====================

class ApprovalRuleCreate(BaseModel):
    rule_name: str
    module: str
    condition_type: str  # amount, percentage, quantity
    condition_operator: str  # >, >=, <, <=, =
    condition_value: float
    approval_levels: List[Dict[str, Any]]  # [{level: 1, role_code: "supervisor", can_skip: False}]
    branch_id: str = ""  # empty = all branches
    active: bool = True

class ApprovalRequestCreate(BaseModel):
    module: str
    document_type: str
    document_id: str
    document_no: str
    amount: float
    reason: str = ""
    metadata: Dict[str, Any] = {}

class ApprovalAction(BaseModel):
    action: str  # approve, reject
    notes: str = ""

# ==================== HELPER FUNCTIONS ====================

async def get_user_approval_scope(user: dict) -> Dict[str, Any]:
    """Get user's approval access scope"""
    user_id = user.get("user_id") or user.get("id")
    role_code = user.get("role_code") or user.get("role")
    branch_id = user.get("branch_id")
    
    db_user = await db["users"].find_one({"id": user_id}, {"_id": 0})
    if db_user:
        role_code = db_user.get("role_code") or role_code
        branch_id = db_user.get("branch_id") or branch_id
    
    role = await db["roles"].find_one({"code": role_code}, {"_id": 0})
    role_level = role.get("level", 99) if role else 99
    inherit_all = role.get("inherit_all", False) if role else False
    
    # RBAC ENFORCEMENT: Only owner and admin can manage approval rules
    # This is a critical security control
    is_owner_or_admin = role_code in ["owner", "admin"] or inherit_all or role_level <= 1
    
    return {
        "user_id": user_id,
        "user_name": user.get("name", ""),
        "role_code": role_code,
        "role_level": role_level,
        "branch_id": branch_id,
        "is_admin": is_owner_or_admin,
        "can_manage_rules": is_owner_or_admin,  # RESTRICTED: Only owner/admin
        "can_approve": role_level <= 5
    }


async def generate_request_number() -> str:
    """Generate unique approval request number"""
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    prefix = f"APR-{today}"
    
    last = await approval_requests.find_one(
        {"request_no": {"$regex": f"^{prefix}"}},
        {"_id": 0, "request_no": 1},
        sort=[("request_no", -1)]
    )
    
    if last:
        try:
            seq = int(last["request_no"].split("-")[-1]) + 1
        except:
            seq = 1
    else:
        seq = 1
    
    return f"{prefix}-{seq:04d}"


async def check_approval_required(
    module: str,
    amount: float,
    branch_id: str = ""
) -> Optional[Dict[str, Any]]:
    """
    Check if approval is required for a transaction
    Returns the matching rule if approval is needed, None otherwise
    """
    # Find active rules for this module
    query = {
        "module": module,
        "active": True,
        "$or": [
            {"branch_id": ""},
            {"branch_id": branch_id}
        ]
    }
    
    rules = await approval_rules.find(query, {"_id": 0}).to_list(100)
    
    for rule in rules:
        condition_type = rule.get("condition_type", "amount")
        operator = rule.get("condition_operator", ">")
        value = rule.get("condition_value", 0)
        
        # Evaluate condition
        meets_condition = False
        if operator == ">":
            meets_condition = amount > value
        elif operator == ">=":
            meets_condition = amount >= value
        elif operator == "<":
            meets_condition = amount < value
        elif operator == "<=":
            meets_condition = amount <= value
        elif operator == "=":
            meets_condition = amount == value
        
        if meets_condition:
            return rule
    
    return None


async def create_approval_request_internal(
    module: str,
    document_type: str,
    document_id: str,
    document_no: str,
    branch_id: str,
    amount: float,
    reason: str,
    rule: Dict[str, Any],
    user: dict,
    metadata: Dict[str, Any] = {}
) -> str:
    """Internal function to create approval request"""
    user_id = user.get("user_id") or user.get("id")
    user_name = user.get("name", "")
    
    request_no = await generate_request_number()
    approval_levels = rule.get("approval_levels", [])
    
    # Initialize steps
    steps = []
    for level_info in sorted(approval_levels, key=lambda x: x.get("level", 0)):
        steps.append({
            "level": level_info.get("level", 1),
            "role_code": level_info.get("role_code", ""),
            "can_skip": level_info.get("can_skip", False),
            "status": "pending",
            "actioned_by": None,
            "actioned_by_name": None,
            "actioned_at": None,
            "notes": ""
        })
    
    request = {
        "id": str(uuid.uuid4()),
        "request_no": request_no,
        "module": module,
        "document_type": document_type,
        "document_id": document_id,
        "document_no": document_no,
        "branch_id": branch_id,
        "rule_id": rule.get("id"),
        "rule_name": rule.get("rule_name"),
        "requested_by": user_id,
        "requested_by_name": user_name,
        "request_date": datetime.now(timezone.utc).isoformat(),
        "amount": amount,
        "reason": reason,
        "metadata": metadata,
        "current_level": 1,
        "max_level": len(steps),
        "status": "pending",
        "steps": steps,
        "completed_at": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await approval_requests.insert_one(request)
    
    return request_no


# ==================== API ENDPOINTS - RULES ====================

@router.get("/modules")
async def get_approval_modules(user: dict = Depends(get_current_user)):
    """Get list of modules that support approval"""
    return {"modules": APPROVAL_MODULES}


@router.get("/rules")
async def list_approval_rules(
    module: str = "",
    active_only: str = "yes",
    user: dict = Depends(get_current_user)
):
    """List approval rules"""
    scope = await get_user_approval_scope(user)
    
    query = {}
    if module:
        query["module"] = module
    if active_only == "yes":
        query["active"] = True
    
    rules = await approval_rules.find(query, {"_id": 0}).sort("module", 1).to_list(100)
    
    return {"rules": rules}


@router.get("/rules/{rule_id}")
async def get_approval_rule(
    rule_id: str,
    user: dict = Depends(get_current_user)
):
    """Get approval rule detail"""
    rule = await approval_rules.find_one({"id": rule_id}, {"_id": 0})
    if not rule:
        raise HTTPException(status_code=404, detail="Rule tidak ditemukan")
    return rule


@router.post("/rules")
async def create_approval_rule(
    data: ApprovalRuleCreate,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """Create new approval rule - RESTRICTED TO OWNER/ADMIN ONLY"""
    scope = await get_user_approval_scope(user)
    
    if not scope["can_manage_rules"]:
        raise HTTPException(
            status_code=403, 
            detail="AKSES DITOLAK - Hanya Owner dan Admin yang dapat membuat approval rules"
        )
    
    if data.module not in APPROVAL_MODULES:
        raise HTTPException(status_code=400, detail=f"Module tidak valid: {data.module}")
    
    # Validate approval levels
    if not data.approval_levels:
        raise HTTPException(status_code=400, detail="Minimal satu level approval harus ditentukan")
    
    rule = {
        "id": str(uuid.uuid4()),
        "rule_name": data.rule_name,
        "module": data.module,
        "condition_type": data.condition_type,
        "condition_operator": data.condition_operator,
        "condition_value": data.condition_value,
        "approval_levels": data.approval_levels,
        "branch_id": data.branch_id,
        "active": data.active,
        "created_by": scope["user_id"],
        "created_by_name": scope["user_name"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await approval_rules.insert_one(rule)
    
    await log_activity(
        db, scope["user_id"], scope["user_name"],
        "create", "approval_rules",
        f"Membuat rule approval: {data.rule_name}",
        request.client.host if request.client else "",
        scope["branch_id"]
    )
    
    return {"id": rule["id"], "message": "Rule berhasil dibuat"}


@router.put("/rules/{rule_id}")
async def update_approval_rule(
    rule_id: str,
    data: ApprovalRuleCreate,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """Update approval rule - RESTRICTED TO OWNER/ADMIN ONLY"""
    scope = await get_user_approval_scope(user)
    
    if not scope["can_manage_rules"]:
        raise HTTPException(
            status_code=403, 
            detail="AKSES DITOLAK - Hanya Owner dan Admin yang dapat mengubah approval rules"
        )
    
    existing = await approval_rules.find_one({"id": rule_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Rule tidak ditemukan")
    
    await approval_rules.update_one(
        {"id": rule_id},
        {"$set": {
            "rule_name": data.rule_name,
            "module": data.module,
            "condition_type": data.condition_type,
            "condition_operator": data.condition_operator,
            "condition_value": data.condition_value,
            "approval_levels": data.approval_levels,
            "branch_id": data.branch_id,
            "active": data.active,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "updated_by": scope["user_id"],
            "updated_by_name": scope["user_name"]
        }}
    )
    
    await log_activity(
        db, scope["user_id"], scope["user_name"],
        "update", "approval_rules",
        f"Update rule approval: {data.rule_name}",
        request.client.host if request.client else "",
        scope["branch_id"]
    )
    
    return {"message": "Rule berhasil diupdate"}


@router.delete("/rules/{rule_id}")
async def delete_approval_rule(
    rule_id: str,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """Delete approval rule - RESTRICTED TO OWNER/ADMIN ONLY"""
    scope = await get_user_approval_scope(user)
    
    if not scope["can_manage_rules"]:
        raise HTTPException(
            status_code=403, 
            detail="AKSES DITOLAK - Hanya Owner dan Admin yang dapat menghapus approval rules"
        )
    
    existing = await approval_rules.find_one({"id": rule_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Rule tidak ditemukan")
    
    # Soft delete by deactivating
    await approval_rules.update_one(
        {"id": rule_id},
        {"$set": {
            "active": False, 
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "deleted_by": scope["user_id"],
            "deleted_by_name": scope["user_name"]
        }}
    )
    
    await log_activity(
        db, scope["user_id"], scope["user_name"],
        "delete", "approval_rules",
        f"Menghapus rule approval: {existing.get('rule_name', rule_id)}",
        request.client.host if request.client else "",
        scope["branch_id"]
    )
    
    return {"message": "Rule berhasil dihapus"}


# ==================== API ENDPOINTS - REQUESTS ====================

@router.get("/pending")
async def get_my_pending_approvals(
    user: dict = Depends(get_current_user)
):
    """Get approval requests pending for current user's role"""
    scope = await get_user_approval_scope(user)
    
    if not scope["can_approve"]:
        return {"requests": [], "total": 0}
    
    # Find requests where current step matches user's role
    query = {
        "status": "pending",
        "steps": {
            "$elemMatch": {
                "status": "pending",
                "role_code": scope["role_code"]
            }
        }
    }
    
    # Add branch filter if not admin
    if not scope["is_admin"]:
        query["branch_id"] = scope["branch_id"]
    
    requests = await approval_requests.find(query, {"_id": 0}).sort("request_date", -1).to_list(100)
    
    # Filter to only show requests at current user's level
    filtered = []
    for req in requests:
        current_level = req.get("current_level", 1)
        for step in req.get("steps", []):
            if step.get("level") == current_level and step.get("role_code") == scope["role_code"]:
                filtered.append(req)
                break
    
    return {"requests": filtered, "total": len(filtered)}


@router.get("/requests")
async def list_approval_requests(
    module: str = "",
    status: str = "",
    start_date: str = "",
    end_date: str = "",
    skip: int = 0,
    limit: int = 50,
    user: dict = Depends(get_current_user)
):
    """List all approval requests (scoped by role)"""
    scope = await get_user_approval_scope(user)
    
    query = {}
    
    if not scope["is_admin"]:
        query["$or"] = [
            {"branch_id": scope["branch_id"]},
            {"requested_by": scope["user_id"]}
        ]
    
    if module:
        query["module"] = module
    if status:
        query["status"] = status
    if start_date:
        query["request_date"] = {"$gte": start_date}
    if end_date:
        if "request_date" in query:
            query["request_date"]["$lte"] = end_date + "T23:59:59"
        else:
            query["request_date"] = {"$lte": end_date + "T23:59:59"}
    
    total = await approval_requests.count_documents(query)
    requests = await approval_requests.find(query, {"_id": 0}).sort("request_date", -1).skip(skip).limit(limit).to_list(limit)
    
    return {"requests": requests, "total": total}


@router.get("/requests/{request_id}")
async def get_approval_request(
    request_id: str,
    user: dict = Depends(get_current_user)
):
    """Get approval request detail"""
    request_doc = await approval_requests.find_one({"id": request_id}, {"_id": 0})
    if not request_doc:
        raise HTTPException(status_code=404, detail="Request tidak ditemukan")
    
    return request_doc


@router.post("/request")
async def create_approval_request(
    data: ApprovalRequestCreate,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """Create new approval request manually"""
    scope = await get_user_approval_scope(user)
    
    # Check if approval is required
    rule = await check_approval_required(data.module, data.amount, scope["branch_id"])
    
    if not rule:
        return {"approval_required": False, "message": "Approval tidak diperlukan untuk transaksi ini"}
    
    request_no = await create_approval_request_internal(
        module=data.module,
        document_type=data.document_type,
        document_id=data.document_id,
        document_no=data.document_no,
        branch_id=scope["branch_id"],
        amount=data.amount,
        reason=data.reason,
        rule=rule,
        user=user,
        metadata=data.metadata
    )
    
    await log_activity(
        db, scope["user_id"], scope["user_name"],
        "create", "approval_requests",
        f"Membuat approval request {request_no} untuk {data.document_no}",
        request.client.host if request.client else "",
        scope["branch_id"]
    )
    
    return {
        "approval_required": True,
        "request_no": request_no,
        "message": "Approval request berhasil dibuat"
    }


@router.post("/requests/{request_id}/action")
async def process_approval(
    request_id: str,
    data: ApprovalAction,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """Process approval (approve/reject)"""
    scope = await get_user_approval_scope(user)
    
    if not scope["can_approve"]:
        raise HTTPException(status_code=403, detail="AKSES DITOLAK")
    
    approval_req = await approval_requests.find_one({"id": request_id}, {"_id": 0})
    if not approval_req:
        raise HTTPException(status_code=404, detail="Request tidak ditemukan")
    
    if approval_req.get("status") != "pending":
        raise HTTPException(status_code=400, detail="Request sudah diproses")
    
    # Check if user can approve at current level
    current_level = approval_req.get("current_level", 1)
    can_action = False
    step_index = -1
    
    for i, step in enumerate(approval_req.get("steps", [])):
        if step.get("level") == current_level and step.get("role_code") == scope["role_code"]:
            can_action = True
            step_index = i
            break
    
    # Admin can approve any level
    if scope["is_admin"]:
        can_action = True
        for i, step in enumerate(approval_req.get("steps", [])):
            if step.get("level") == current_level:
                step_index = i
                break
    
    if not can_action or step_index < 0:
        raise HTTPException(status_code=403, detail="Anda tidak memiliki akses untuk approve level ini")
    
    # Update step
    steps = approval_req.get("steps", [])
    steps[step_index]["status"] = "approved" if data.action == "approve" else "rejected"
    steps[step_index]["actioned_by"] = scope["user_id"]
    steps[step_index]["actioned_by_name"] = scope["user_name"]
    steps[step_index]["actioned_at"] = datetime.now(timezone.utc).isoformat()
    steps[step_index]["notes"] = data.notes
    
    # Determine overall status
    if data.action == "reject":
        new_status = "rejected"
        completed_at = datetime.now(timezone.utc).isoformat()
        new_level = current_level
    else:
        # Check if all levels approved
        max_level = approval_req.get("max_level", 1)
        if current_level >= max_level:
            new_status = "approved"
            completed_at = datetime.now(timezone.utc).isoformat()
            new_level = current_level
        else:
            new_status = "pending"
            completed_at = None
            new_level = current_level + 1
    
    await approval_requests.update_one(
        {"id": request_id},
        {"$set": {
            "steps": steps,
            "current_level": new_level,
            "status": new_status,
            "completed_at": completed_at
        }}
    )
    
    action_text = "menyetujui" if data.action == "approve" else "menolak"
    await log_activity(
        db, scope["user_id"], scope["user_name"],
        data.action, "approval_requests",
        f"{action_text} request {approval_req.get('request_no')} ({approval_req.get('document_no')})",
        request.client.host if request.client else "",
        approval_req.get("branch_id"),
        severity="warning" if data.action == "reject" else "normal"
    )
    
    return {
        "status": new_status,
        "current_level": new_level,
        "message": f"Request berhasil di-{data.action}"
    }


@router.get("/summary/dashboard")
async def get_approval_summary(
    user: dict = Depends(get_current_user)
):
    """Get approval summary for dashboard"""
    scope = await get_user_approval_scope(user)
    
    # Count by status
    pipeline = [
        {"$match": {"branch_id": scope["branch_id"]} if not scope["is_admin"] else {}},
        {"$group": {
            "_id": "$status",
            "count": {"$sum": 1}
        }}
    ]
    
    status_counts = {}
    async for doc in approval_requests.aggregate(pipeline):
        status_counts[doc["_id"]] = doc["count"]
    
    # Get my pending count
    my_pending_query = {
        "status": "pending",
        "steps": {
            "$elemMatch": {
                "status": "pending",
                "role_code": scope["role_code"]
            }
        }
    }
    if not scope["is_admin"]:
        my_pending_query["branch_id"] = scope["branch_id"]
    
    my_pending = await approval_requests.count_documents(my_pending_query)
    
    return {
        "my_pending": my_pending,
        "total_pending": status_counts.get("pending", 0),
        "total_approved": status_counts.get("approved", 0),
        "total_rejected": status_counts.get("rejected", 0)
    }


# ==================== UTILITY FUNCTIONS FOR OTHER MODULES ====================

async def submit_for_approval(
    module: str,
    document_type: str,
    document_id: str,
    document_no: str,
    branch_id: str,
    amount: float,
    reason: str,
    user: dict,
    metadata: Dict[str, Any] = {}
) -> Dict[str, Any]:
    """
    Submit a document for approval - called by other modules
    Returns: {required: bool, request_no: str or None, status: str}
    """
    rule = await check_approval_required(module, amount, branch_id)
    
    if not rule:
        return {
            "required": False,
            "request_no": None,
            "status": "auto_approved"
        }
    
    request_no = await create_approval_request_internal(
        module=module,
        document_type=document_type,
        document_id=document_id,
        document_no=document_no,
        branch_id=branch_id,
        amount=amount,
        reason=reason,
        rule=rule,
        user=user,
        metadata=metadata
    )
    
    return {
        "required": True,
        "request_no": request_no,
        "status": "pending_approval"
    }


async def get_approval_status(document_id: str) -> Optional[str]:
    """Get approval status for a document"""
    req = await approval_requests.find_one(
        {"document_id": document_id},
        {"_id": 0, "status": 1}
    )
    return req.get("status") if req else None


# ==================== INIT ====================

@router.post("/init")
async def initialize_approval_system(user: dict = Depends(get_current_user)):
    """Initialize approval system with default rules"""
    
    # Create indexes
    await approval_rules.create_index("module")
    await approval_rules.create_index("active")
    await approval_requests.create_index("request_no", unique=True)
    await approval_requests.create_index("status")
    await approval_requests.create_index("document_id")
    await approval_requests.create_index("branch_id")
    
    # Create default rules if none exist
    existing = await approval_rules.count_documents({})
    if existing == 0:
        default_rules = [
            {
                "id": str(uuid.uuid4()),
                "rule_name": "Pembelian > 10 Juta",
                "module": "purchase",
                "condition_type": "amount",
                "condition_operator": ">",
                "condition_value": 10000000,
                "approval_levels": [
                    {"level": 1, "role_code": "supervisor", "can_skip": False},
                    {"level": 2, "role_code": "manager", "can_skip": False}
                ],
                "branch_id": "",
                "active": True,
                "created_by": "system",
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "rule_name": "Void Penjualan > 1 Juta",
                "module": "sales_void",
                "condition_type": "amount",
                "condition_operator": ">",
                "condition_value": 1000000,
                "approval_levels": [
                    {"level": 1, "role_code": "supervisor", "can_skip": False}
                ],
                "branch_id": "",
                "active": True,
                "created_by": "system",
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "rule_name": "Diskon > 20%",
                "module": "sales_discount",
                "condition_type": "percentage",
                "condition_operator": ">",
                "condition_value": 20,
                "approval_levels": [
                    {"level": 1, "role_code": "supervisor", "can_skip": False}
                ],
                "branch_id": "",
                "active": True,
                "created_by": "system",
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "rule_name": "Selisih Setoran > 100rb",
                "module": "deposit_difference",
                "condition_type": "amount",
                "condition_operator": ">",
                "condition_value": 100000,
                "approval_levels": [
                    {"level": 1, "role_code": "supervisor", "can_skip": False},
                    {"level": 2, "role_code": "finance", "can_skip": False}
                ],
                "branch_id": "",
                "active": True,
                "created_by": "system",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        ]
        
        for rule in default_rules:
            await approval_rules.insert_one(rule)
    
    return {
        "message": "Approval system initialized",
        "default_rules_created": existing == 0
    }
