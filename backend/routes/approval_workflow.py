"""
OCB TITAN ERP - PHASE 3 OPERATIONAL CONTROL SYSTEM
Module 1: APPROVAL WORKFLOW ENGINE
Following OCB TITAN AI MASTER LAW - NON-DESTRUCTIVE Development

Features:
1. Purchase Approval - Approval untuk PO di atas limit
2. Discount Approval - Approval untuk diskon di atas batas
3. Void Approval - Approval untuk pembatalan transaksi
4. Price Override Approval - Approval untuk perubahan harga
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from database import get_db as get_database
from routes.auth import get_current_user
from routes.rbac_middleware import require_permission
import uuid

router = APIRouter(prefix="/api/approval", tags=["Approval Workflow Engine"])

# ==================== APPROVAL TYPES & RULES ====================

APPROVAL_TYPES = {
    "purchase_order": {
        "name": "Purchase Order",
        "description": "Approval untuk pembelian di atas limit",
        "default_limit": 10000000,  # 10 juta
        "approvers": ["owner", "admin", "purchasing_manager"],
        "levels": [
            {"min": 0, "max": 10000000, "level": 0, "auto_approve": True},
            {"min": 10000000, "max": 50000000, "level": 1, "approvers": ["purchasing_manager"]},
            {"min": 50000000, "max": 100000000, "level": 2, "approvers": ["finance_manager", "admin"]},
            {"min": 100000000, "max": None, "level": 3, "approvers": ["owner"]}
        ]
    },
    "discount": {
        "name": "Discount Approval",
        "description": "Approval untuk diskon di atas batas",
        "default_limit": 10,  # 10%
        "approvers": ["owner", "admin", "sales_manager"],
        "levels": [
            {"min": 0, "max": 10, "level": 0, "auto_approve": True},
            {"min": 10, "max": 20, "level": 1, "approvers": ["supervisor"]},
            {"min": 20, "max": 30, "level": 2, "approvers": ["sales_manager"]},
            {"min": 30, "max": None, "level": 3, "approvers": ["owner"]}
        ]
    },
    "void_transaction": {
        "name": "Void Transaction",
        "description": "Approval untuk pembatalan transaksi",
        "approvers": ["owner", "admin", "supervisor"],
        "always_require_approval": True,
        "levels": [
            {"min": 0, "max": 500000, "level": 1, "approvers": ["supervisor"]},
            {"min": 500000, "max": 5000000, "level": 2, "approvers": ["admin", "finance_manager"]},
            {"min": 5000000, "max": None, "level": 3, "approvers": ["owner"]}
        ]
    },
    "price_override": {
        "name": "Price Override",
        "description": "Approval untuk perubahan harga dari standar",
        "approvers": ["owner", "admin", "sales_manager"],
        "levels": [
            {"min": 0, "max": 5, "level": 0, "auto_approve": True},  # 0-5% variance auto approve
            {"min": 5, "max": 15, "level": 1, "approvers": ["supervisor"]},
            {"min": 15, "max": 30, "level": 2, "approvers": ["sales_manager"]},
            {"min": 30, "max": None, "level": 3, "approvers": ["owner"]}
        ]
    },
    "credit_override": {
        "name": "Credit Limit Override",
        "description": "Approval untuk transaksi melebihi credit limit",
        "approvers": ["owner", "admin", "finance_manager"],
        "always_require_approval": True,
        "levels": [
            {"min": 0, "max": 1000000, "level": 1, "approvers": ["finance_manager"]},
            {"min": 1000000, "max": None, "level": 2, "approvers": ["owner"]}
        ]
    }
}

APPROVAL_STATUS = {
    "pending": {"name": "Menunggu", "color": "yellow"},
    "approved": {"name": "Disetujui", "color": "green"},
    "rejected": {"name": "Ditolak", "color": "red"},
    "cancelled": {"name": "Dibatalkan", "color": "gray"},
    "expired": {"name": "Kedaluwarsa", "color": "gray"}
}

# ==================== PYDANTIC MODELS ====================

class ApprovalRequest(BaseModel):
    approval_type: str
    reference_type: str  # "purchase_order", "sales_invoice", "transaction"
    reference_id: str
    reference_no: str
    amount: float = 0
    variance_percent: float = 0  # For discount/price override
    branch_id: Optional[str] = None
    requester_notes: str = ""
    data: Optional[Dict[str, Any]] = None

class ApprovalAction(BaseModel):
    action: str  # "approve" or "reject"
    notes: str = ""

class ApprovalRuleCreate(BaseModel):
    approval_type: str
    min_amount: float
    max_amount: Optional[float] = None
    level: int
    approvers: List[str]
    branch_id: Optional[str] = None

# ==================== APPROVAL HELPER FUNCTIONS ====================

async def get_approval_level(approval_type: str, amount: float = 0, variance_percent: float = 0) -> Dict[str, Any]:
    """Determine required approval level based on amount/variance"""
    config = APPROVAL_TYPES.get(approval_type)
    if not config:
        return {"level": 0, "auto_approve": True, "approvers": []}
    
    # For percentage-based (discount, price_override)
    check_value = variance_percent if approval_type in ["discount", "price_override"] else amount
    
    for level_config in config.get("levels", []):
        min_val = level_config.get("min", 0)
        max_val = level_config.get("max")
        
        if max_val is None:
            if check_value >= min_val:
                return level_config
        else:
            if min_val <= check_value < max_val:
                return level_config
    
    # Default to highest level
    return config.get("levels", [{}])[-1] if config.get("levels") else {"level": 0, "auto_approve": True}

async def check_user_can_approve(user: dict, approval_type: str, level: int) -> bool:
    """Check if user has permission to approve at specified level"""
    user_role = user.get("role", "")
    
    config = APPROVAL_TYPES.get(approval_type, {})
    levels = config.get("levels", [])
    
    for level_config in levels:
        if level_config.get("level") == level:
            return user_role in level_config.get("approvers", [])
    
    return user_role in config.get("approvers", [])

async def create_approval_request(
    db,
    approval_type: str,
    reference_type: str,
    reference_id: str,
    reference_no: str,
    amount: float,
    variance_percent: float,
    branch_id: str,
    requester: dict,
    notes: str = "",
    data: dict = None
) -> Dict[str, Any]:
    """Create an approval request"""
    
    # Determine approval level
    level_config = await get_approval_level(approval_type, amount, variance_percent)
    
    # Check if auto-approve
    if level_config.get("auto_approve", False):
        return {
            "status": "auto_approved",
            "approval_id": None,
            "message": "Transaksi di-approve otomatis (di bawah limit)",
            "level": 0
        }
    
    approval_id = str(uuid.uuid4())
    approval_no = f"APR-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"
    
    approval = {
        "id": approval_id,
        "approval_no": approval_no,
        "approval_type": approval_type,
        "approval_type_name": APPROVAL_TYPES.get(approval_type, {}).get("name", approval_type),
        "reference_type": reference_type,
        "reference_id": reference_id,
        "reference_no": reference_no,
        "amount": amount,
        "variance_percent": variance_percent,
        "required_level": level_config.get("level", 1),
        "required_approvers": level_config.get("approvers", []),
        "status": "pending",
        "branch_id": branch_id,
        "requester_id": requester.get("user_id") or requester.get("id"),
        "requester_name": requester.get("name", ""),
        "requester_notes": notes,
        "data": data or {},
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "approvals": [],
        "rejections": []
    }
    
    await db.approval_requests.insert_one(approval)
    
    return {
        "status": "pending",
        "approval_id": approval_id,
        "approval_no": approval_no,
        "required_level": level_config.get("level"),
        "required_approvers": level_config.get("approvers"),
        "message": f"Memerlukan approval level {level_config.get('level')}"
    }

# ==================== API ENDPOINTS ====================

@router.get("/types")
async def list_approval_types(user: dict = Depends(get_current_user)):
    """Get all approval types and their configurations"""
    types_list = []
    for type_code, config in APPROVAL_TYPES.items():
        types_list.append({
            "code": type_code,
            "name": config["name"],
            "description": config["description"],
            "levels": config.get("levels", []),
            "approvers": config.get("approvers", [])
        })
    
    return {"items": types_list, "total": len(types_list)}

@router.post("/request")
async def create_approval_request_endpoint(
    data: ApprovalRequest,
    user: dict = Depends(get_current_user)
):
    """Create a new approval request"""
    db = get_database()
    
    if data.approval_type not in APPROVAL_TYPES:
        raise HTTPException(status_code=400, detail=f"Approval type {data.approval_type} tidak valid")
    
    result = await create_approval_request(
        db,
        data.approval_type,
        data.reference_type,
        data.reference_id,
        data.reference_no,
        data.amount,
        data.variance_percent,
        data.branch_id,
        user,
        data.requester_notes,
        data.data
    )
    
    return result

@router.get("/pending")
async def list_pending_approvals(
    approval_type: Optional[str] = None,
    branch_id: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Get pending approvals that user can approve"""
    db = get_database()
    
    user_role = user.get("role", "")
    
    query = {"status": "pending"}
    if approval_type:
        query["approval_type"] = approval_type
    if branch_id:
        query["branch_id"] = branch_id
    
    # Filter by approver role
    approvals = await db.approval_requests.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    # Filter to only show approvals user can approve
    user_approvals = []
    for approval in approvals:
        can_approve = await check_user_can_approve(
            user, 
            approval["approval_type"],
            approval.get("required_level", 1)
        )
        if can_approve or user_role in ["owner", "admin"]:
            user_approvals.append(approval)
    
    return {"items": user_approvals, "total": len(user_approvals)}

@router.get("/my-requests")
async def list_my_approval_requests(
    status: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Get approval requests created by current user"""
    db = get_database()
    
    user_id = user.get("user_id") or user.get("id")
    
    query = {"requester_id": user_id}
    if status:
        query["status"] = status
    
    approvals = await db.approval_requests.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    return {"items": approvals, "total": len(approvals)}

@router.get("/{approval_id}")
async def get_approval_detail(
    approval_id: str,
    user: dict = Depends(get_current_user)
):
    """Get approval request detail"""
    db = get_database()
    
    approval = await db.approval_requests.find_one({"id": approval_id}, {"_id": 0})
    if not approval:
        raise HTTPException(status_code=404, detail="Approval request tidak ditemukan")
    
    # Check if user can view
    user_role = user.get("role", "")
    user_id = user.get("user_id") or user.get("id")
    
    can_approve = await check_user_can_approve(
        user,
        approval["approval_type"],
        approval.get("required_level", 1)
    )
    
    is_requester = approval.get("requester_id") == user_id
    is_admin = user_role in ["owner", "admin"]
    
    if not (can_approve or is_requester or is_admin):
        raise HTTPException(status_code=403, detail="Tidak memiliki akses ke approval ini")
    
    return approval

@router.post("/{approval_id}/action")
async def process_approval(
    approval_id: str,
    action_data: ApprovalAction,
    user: dict = Depends(get_current_user)
):
    """Approve or reject an approval request"""
    db = get_database()
    
    approval = await db.approval_requests.find_one({"id": approval_id}, {"_id": 0})
    if not approval:
        raise HTTPException(status_code=404, detail="Approval request tidak ditemukan")
    
    if approval["status"] != "pending":
        raise HTTPException(status_code=400, detail=f"Approval sudah {APPROVAL_STATUS.get(approval['status'], {}).get('name', approval['status'])}")
    
    # Check permission
    user_role = user.get("role", "")
    can_approve = await check_user_can_approve(
        user,
        approval["approval_type"],
        approval.get("required_level", 1)
    )
    
    if not can_approve and user_role not in ["owner", "admin"]:
        raise HTTPException(
            status_code=403, 
            detail=f"Tidak memiliki izin untuk approval level {approval.get('required_level')}. Diperlukan: {', '.join(approval.get('required_approvers', []))}"
        )
    
    user_id = user.get("user_id") or user.get("id")
    user_name = user.get("name", "")
    action_time = datetime.now(timezone.utc).isoformat()
    
    action_record = {
        "user_id": user_id,
        "user_name": user_name,
        "user_role": user_role,
        "action": action_data.action,
        "notes": action_data.notes,
        "timestamp": action_time
    }
    
    if action_data.action == "approve":
        new_status = "approved"
        update_field = "approvals"
        message = f"Approval disetujui oleh {user_name}"
    elif action_data.action == "reject":
        new_status = "rejected"
        update_field = "rejections"
        message = f"Approval ditolak oleh {user_name}"
    else:
        raise HTTPException(status_code=400, detail="Action harus 'approve' atau 'reject'")
    
    await db.approval_requests.update_one(
        {"id": approval_id},
        {
            "$set": {
                "status": new_status,
                "approved_by": user_id if action_data.action == "approve" else None,
                "approved_by_name": user_name if action_data.action == "approve" else None,
                "rejected_by": user_id if action_data.action == "reject" else None,
                "rejected_by_name": user_name if action_data.action == "reject" else None,
                "action_notes": action_data.notes,
                "action_at": action_time,
                "updated_at": action_time
            },
            "$push": {update_field: action_record}
        }
    )
    
    # Log to audit trail
    await db.audit_logs.insert_one({
        "id": str(uuid.uuid4()),
        "action": f"approval_{action_data.action}",
        "module": "approval",
        "target_id": approval_id,
        "target_no": approval.get("approval_no"),
        "reference_id": approval.get("reference_id"),
        "reference_no": approval.get("reference_no"),
        "description": message,
        "user_id": user_id,
        "user_name": user_name,
        "timestamp": action_time
    })
    
    return {
        "success": True,
        "status": new_status,
        "message": message,
        "approval_id": approval_id,
        "approval_no": approval.get("approval_no")
    }

@router.post("/check")
async def check_approval_required(
    data: ApprovalRequest,
    user: dict = Depends(get_current_user)
):
    """Check if approval is required for a transaction (without creating request)"""
    level_config = await get_approval_level(
        data.approval_type,
        data.amount,
        data.variance_percent
    )
    
    return {
        "approval_type": data.approval_type,
        "amount": data.amount,
        "variance_percent": data.variance_percent,
        "requires_approval": not level_config.get("auto_approve", False),
        "required_level": level_config.get("level", 0),
        "required_approvers": level_config.get("approvers", []),
        "config": APPROVAL_TYPES.get(data.approval_type, {}).get("name", data.approval_type)
    }

@router.get("/status/{reference_id}")
async def check_approval_status(
    reference_id: str,
    user: dict = Depends(get_current_user)
):
    """Check approval status for a reference document"""
    db = get_database()
    
    approval = await db.approval_requests.find_one(
        {"reference_id": reference_id},
        {"_id": 0}
    )
    
    if not approval:
        return {
            "status": "no_approval",
            "message": "Tidak ada approval request untuk dokumen ini"
        }
    
    return {
        "approval_id": approval.get("id"),
        "approval_no": approval.get("approval_no"),
        "status": approval.get("status"),
        "status_name": APPROVAL_STATUS.get(approval.get("status"), {}).get("name"),
        "required_level": approval.get("required_level"),
        "approved_by": approval.get("approved_by_name"),
        "rejected_by": approval.get("rejected_by_name"),
        "action_at": approval.get("action_at")
    }

# ==================== APPROVAL CENTER DASHBOARD ====================

@router.get("/dashboard/summary")
async def get_approval_dashboard(
    user: dict = Depends(get_current_user)
):
    """Get approval dashboard summary"""
    db = get_database()
    
    # Pending by type
    pending_by_type = await db.approval_requests.aggregate([
        {"$match": {"status": "pending"}},
        {"$group": {"_id": "$approval_type", "count": {"$sum": 1}}}
    ]).to_list(20)
    
    # Today's approvals
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    today_stats = await db.approval_requests.aggregate([
        {"$match": {"created_at": {"$regex": f"^{today}"}}},
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]).to_list(10)
    
    # User's pending
    user_role = user.get("role", "")
    user_id = user.get("user_id") or user.get("id")
    
    my_pending = await db.approval_requests.count_documents({
        "status": "pending",
        "requester_id": user_id
    })
    
    # Can approve count (for approvers)
    can_approve_count = 0
    if user_role in ["owner", "admin", "purchasing_manager", "finance_manager", "sales_manager", "supervisor"]:
        all_pending = await db.approval_requests.find({"status": "pending"}, {"_id": 0}).to_list(100)
        for approval in all_pending:
            if await check_user_can_approve(user, approval["approval_type"], approval.get("required_level", 1)):
                can_approve_count += 1
    
    return {
        "pending_by_type": {item["_id"]: item["count"] for item in pending_by_type},
        "today_stats": {item["_id"]: item["count"] for item in today_stats},
        "my_pending_requests": my_pending,
        "pending_for_my_approval": can_approve_count,
        "total_pending": sum(item["count"] for item in pending_by_type)
    }
