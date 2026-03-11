"""
OCB TITAN ERP - PHASE 3 OPERATIONAL CONTROL SYSTEM
Module 2: CUSTOMER CREDIT LIMIT CONTROL
Following OCB TITAN AI MASTER LAW - NON-DESTRUCTIVE Development

Features:
1. Credit Limit per Customer - Batas maksimal piutang
2. Credit Hold Status - Status pemblokiran sementara
3. Overdue Blocking - Blokir jika ada invoice lewat jatuh tempo
4. Hard Stop - Menolak transaksi kredit jika melanggar aturan
5. Approval Override Integration - Override melalui Approval Workflow
6. Audit Trail - Pencatatan semua perubahan credit
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
from database import get_db as get_database, customers
from routes.auth import get_current_user
from routes.rbac_middleware import require_permission
from routes.approval_workflow import create_approval_request, check_user_can_approve
import uuid

router = APIRouter(prefix="/api/credit-control", tags=["Credit Control Engine"])

# ==================== CREDIT POLICY DEFAULTS ====================

DEFAULT_CREDIT_POLICY = {
    "default_credit_limit": 0,  # 0 = No credit (cash only)
    "max_overdue_days": 30,  # Max days overdue before blocking
    "overdue_tolerance_amount": 100000,  # Toleransi nominal overdue (Rp 100rb)
    "auto_hold_on_overdue": True,  # Otomatis hold jika overdue
    "require_approval_for_override": True,  # Wajib approval untuk override
    "segments": {
        "regular": {"default_limit": 0, "max_overdue_days": 0},
        "member": {"default_limit": 5000000, "max_overdue_days": 14},
        "vip": {"default_limit": 20000000, "max_overdue_days": 30},
        "corporate": {"default_limit": 100000000, "max_overdue_days": 45},
        "distributor": {"default_limit": 500000000, "max_overdue_days": 60}
    }
}

CREDIT_STATUS = {
    "active": {"name": "Aktif", "color": "green", "can_transact": True},
    "warning": {"name": "Peringatan", "color": "yellow", "can_transact": True},
    "hold": {"name": "Ditahan", "color": "red", "can_transact": False},
    "blocked": {"name": "Diblokir", "color": "red", "can_transact": False},
    "blacklist": {"name": "Blacklist", "color": "black", "can_transact": False}
}

# ==================== PYDANTIC MODELS ====================

class CreditLimitUpdate(BaseModel):
    customer_id: str
    credit_limit: float = Field(ge=0)
    notes: str = ""

class CreditHoldAction(BaseModel):
    customer_id: str
    action: str  # "hold", "release", "block", "unblock", "blacklist"
    reason: str = ""

class CreditOverrideRequest(BaseModel):
    customer_id: str
    transaction_type: str  # "sales", "ar"
    transaction_id: str
    transaction_no: str
    requested_amount: float
    current_balance: float
    credit_limit: float
    override_reason: str

class CreditCheckRequest(BaseModel):
    customer_id: str
    transaction_amount: float
    transaction_type: str = "sales"  # "sales", "ar"
    branch_id: Optional[str] = None

class CreditPolicyUpdate(BaseModel):
    segment: str
    default_limit: float
    max_overdue_days: int

# ==================== HELPER FUNCTIONS ====================

async def get_customer_credit_info(db, customer_id: str) -> Dict[str, Any]:
    """Get complete credit information for a customer"""
    customer = await customers.find_one({"id": customer_id}, {"_id": 0})
    if not customer:
        return None
    
    # Get AR balance (outstanding receivables)
    ar_collection = db["ar_system"]
    ar_pipeline = [
        {"$match": {"customer_id": customer_id, "status": {"$in": ["unpaid", "partial"]}}},
        {"$group": {
            "_id": None,
            "total_outstanding": {"$sum": "$outstanding_amount"},
            "count": {"$sum": 1}
        }}
    ]
    ar_result = await ar_collection.aggregate(ar_pipeline).to_list(1)
    outstanding = ar_result[0]["total_outstanding"] if ar_result else 0
    ar_count = ar_result[0]["count"] if ar_result else 0
    
    # Get overdue AR
    today = datetime.now(timezone.utc)
    overdue_pipeline = [
        {"$match": {
            "customer_id": customer_id,
            "status": {"$in": ["unpaid", "partial"]},
            "due_date": {"$lt": today.isoformat()}
        }},
        {"$group": {
            "_id": None,
            "total_overdue": {"$sum": "$outstanding_amount"},
            "count": {"$sum": 1},
            "oldest_overdue": {"$min": "$due_date"}
        }}
    ]
    overdue_result = await ar_collection.aggregate(overdue_pipeline).to_list(1)
    overdue_amount = overdue_result[0]["total_overdue"] if overdue_result else 0
    overdue_count = overdue_result[0]["count"] if overdue_result else 0
    oldest_overdue = overdue_result[0].get("oldest_overdue") if overdue_result else None
    
    # Calculate overdue days
    overdue_days = 0
    if oldest_overdue:
        try:
            oldest_date = datetime.fromisoformat(oldest_overdue.replace('Z', '+00:00'))
            overdue_days = (today - oldest_date).days
        except:
            overdue_days = 0
    
    # Get credit settings from customer or use segment defaults
    credit_limit = customer.get("credit_limit", 0)
    credit_status = customer.get("credit_status", "active")
    credit_hold_reason = customer.get("credit_hold_reason", "")
    segment = customer.get("segment", "regular")
    
    # If credit_limit is 0, check segment default
    if credit_limit == 0:
        segment_config = DEFAULT_CREDIT_POLICY["segments"].get(segment, {})
        credit_limit = segment_config.get("default_limit", 0)
    
    # Calculate available credit
    available_credit = max(0, credit_limit - outstanding)
    
    # Determine effective status
    effective_status = credit_status
    status_reason = ""
    
    if credit_status in ["hold", "blocked", "blacklist"]:
        effective_status = credit_status
        status_reason = credit_hold_reason
    elif overdue_amount > DEFAULT_CREDIT_POLICY["overdue_tolerance_amount"]:
        max_overdue = DEFAULT_CREDIT_POLICY["segments"].get(segment, {}).get("max_overdue_days", 30)
        if overdue_days > max_overdue:
            effective_status = "blocked"
            status_reason = f"Invoice overdue {overdue_days} hari (maks {max_overdue} hari)"
    elif outstanding >= credit_limit and credit_limit > 0:
        effective_status = "warning"
        status_reason = f"Mendekati/melebihi limit (Rp {outstanding:,.0f} / Rp {credit_limit:,.0f})"
    
    return {
        "customer_id": customer_id,
        "customer_name": customer.get("name", ""),
        "customer_code": customer.get("code", ""),
        "segment": segment,
        "credit_limit": credit_limit,
        "outstanding_balance": outstanding,
        "available_credit": available_credit,
        "ar_count": ar_count,
        "overdue_amount": overdue_amount,
        "overdue_count": overdue_count,
        "overdue_days": overdue_days,
        "oldest_overdue": oldest_overdue,
        "credit_status": credit_status,
        "effective_status": effective_status,
        "status_reason": status_reason,
        "can_transact": CREDIT_STATUS.get(effective_status, {}).get("can_transact", False),
        "credit_hold_reason": credit_hold_reason,
        "last_updated": customer.get("credit_updated_at", customer.get("updated_at"))
    }

async def check_credit_transaction(db, customer_id: str, amount: float, user: dict) -> Dict[str, Any]:
    """
    Check if a credit transaction can proceed
    Returns: allowed, reason, requires_override, override_type
    """
    credit_info = await get_customer_credit_info(db, customer_id)
    
    if not credit_info:
        return {
            "allowed": False,
            "reason": "Customer tidak ditemukan",
            "requires_override": False,
            "credit_info": None
        }
    
    effective_status = credit_info["effective_status"]
    available_credit = credit_info["available_credit"]
    credit_limit = credit_info["credit_limit"]
    outstanding = credit_info["outstanding_balance"]
    
    # Check 1: Credit status
    if effective_status in ["hold", "blocked", "blacklist"]:
        return {
            "allowed": False,
            "reason": f"Customer dalam status {CREDIT_STATUS.get(effective_status, {}).get('name', effective_status)}: {credit_info['status_reason']}",
            "requires_override": effective_status != "blacklist",  # Blacklist cannot be overridden
            "override_type": "credit_override",
            "credit_info": credit_info
        }
    
    # Check 2: Credit limit (if limit > 0)
    if credit_limit > 0:
        new_balance = outstanding + amount
        if new_balance > credit_limit:
            return {
                "allowed": False,
                "reason": f"Transaksi melebihi credit limit. Outstanding: Rp {outstanding:,.0f}, Transaksi: Rp {amount:,.0f}, Limit: Rp {credit_limit:,.0f}",
                "requires_override": True,
                "override_type": "credit_override",
                "over_limit_amount": new_balance - credit_limit,
                "credit_info": credit_info
            }
    
    # Check 3: Overdue blocking
    if credit_info["overdue_days"] > 0:
        max_overdue = DEFAULT_CREDIT_POLICY["segments"].get(credit_info["segment"], {}).get("max_overdue_days", 30)
        if credit_info["overdue_days"] > max_overdue and credit_info["overdue_amount"] > DEFAULT_CREDIT_POLICY["overdue_tolerance_amount"]:
            return {
                "allowed": False,
                "reason": f"Customer memiliki invoice overdue {credit_info['overdue_days']} hari (maks {max_overdue} hari). Total overdue: Rp {credit_info['overdue_amount']:,.0f}",
                "requires_override": True,
                "override_type": "credit_override",
                "credit_info": credit_info
            }
    
    # All checks passed
    return {
        "allowed": True,
        "reason": "Transaksi kredit diizinkan",
        "requires_override": False,
        "credit_info": credit_info
    }

# ==================== API ENDPOINTS ====================

@router.get("/policy")
async def get_credit_policy(user: dict = Depends(get_current_user)):
    """Get credit policy configuration"""
    db = get_database()
    
    # Try to get custom policy from DB
    policy = await db.settings.find_one({"type": "credit_policy"}, {"_id": 0})
    
    if not policy:
        return DEFAULT_CREDIT_POLICY
    
    return policy.get("config", DEFAULT_CREDIT_POLICY)

@router.put("/policy")
async def update_credit_policy(
    updates: Dict[str, Any],
    user: dict = Depends(require_permission("credit_control", "edit"))
):
    """Update credit policy configuration"""
    db = get_database()
    
    await db.settings.update_one(
        {"type": "credit_policy"},
        {"$set": {
            "config": updates,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "updated_by": user.get("user_id")
        }},
        upsert=True
    )
    
    # Audit log
    await db.audit_logs.insert_one({
        "id": str(uuid.uuid4()),
        "action": "credit_policy_update",
        "module": "credit_control",
        "description": "Update kebijakan credit control",
        "user_id": user.get("user_id"),
        "user_name": user.get("name"),
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    return {"success": True, "message": "Credit policy updated"}

@router.get("/customer/{customer_id}")
async def get_customer_credit_status(
    customer_id: str,
    user: dict = Depends(get_current_user)
):
    """Get credit information for a customer"""
    db = get_database()
    credit_info = await get_customer_credit_info(db, customer_id)
    
    if not credit_info:
        raise HTTPException(status_code=404, detail="Customer tidak ditemukan")
    
    return credit_info

@router.post("/check")
async def check_credit_for_transaction(
    data: CreditCheckRequest,
    user: dict = Depends(get_current_user)
):
    """
    Check if a credit transaction is allowed
    This is the HARD STOP endpoint - called before creating sales/AR
    """
    db = get_database()
    result = await check_credit_transaction(db, data.customer_id, data.transaction_amount, user)
    
    return {
        "customer_id": data.customer_id,
        "transaction_amount": data.transaction_amount,
        "allowed": result["allowed"],
        "reason": result["reason"],
        "requires_override": result.get("requires_override", False),
        "override_type": result.get("override_type"),
        "over_limit_amount": result.get("over_limit_amount", 0),
        "credit_info": result.get("credit_info")
    }

@router.put("/customer/{customer_id}/limit")
async def update_customer_credit_limit(
    customer_id: str,
    data: CreditLimitUpdate,
    user: dict = Depends(require_permission("credit_control", "edit"))
):
    """Update credit limit for a customer"""
    db = get_database()
    
    # Get current customer
    customer = await customers.find_one({"id": customer_id}, {"_id": 0})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer tidak ditemukan")
    
    old_limit = customer.get("credit_limit", 0)
    
    # Update credit limit
    await customers.update_one(
        {"id": customer_id},
        {"$set": {
            "credit_limit": data.credit_limit,
            "credit_updated_at": datetime.now(timezone.utc).isoformat(),
            "credit_updated_by": user.get("user_id")
        }}
    )
    
    # Audit log
    await db.audit_logs.insert_one({
        "id": str(uuid.uuid4()),
        "action": "credit_limit_update",
        "module": "credit_control",
        "target_id": customer_id,
        "target_name": customer.get("name"),
        "description": f"Update credit limit: Rp {old_limit:,.0f} -> Rp {data.credit_limit:,.0f}. Notes: {data.notes}",
        "old_value": old_limit,
        "new_value": data.credit_limit,
        "user_id": user.get("user_id"),
        "user_name": user.get("name"),
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    return {
        "success": True,
        "message": f"Credit limit updated to Rp {data.credit_limit:,.0f}",
        "customer_id": customer_id,
        "old_limit": old_limit,
        "new_limit": data.credit_limit
    }

@router.post("/customer/{customer_id}/hold")
async def manage_credit_hold(
    customer_id: str,
    data: CreditHoldAction,
    user: dict = Depends(require_permission("credit_control", "edit"))
):
    """Hold, release, block, or blacklist a customer's credit"""
    db = get_database()
    
    # Get current customer
    customer = await customers.find_one({"id": customer_id}, {"_id": 0})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer tidak ditemukan")
    
    old_status = customer.get("credit_status", "active")
    
    # Map action to status
    status_map = {
        "hold": "hold",
        "release": "active",
        "block": "blocked",
        "unblock": "active",
        "blacklist": "blacklist"
    }
    
    if data.action not in status_map:
        raise HTTPException(status_code=400, detail=f"Action tidak valid. Gunakan: {list(status_map.keys())}")
    
    new_status = status_map[data.action]
    
    # Special check: Only owner can blacklist or unblock blacklist
    if data.action == "blacklist" or (old_status == "blacklist" and data.action in ["release", "unblock"]):
        user_role = user.get("role", "")
        if user_role not in ["owner"]:
            raise HTTPException(status_code=403, detail="Hanya Owner yang dapat melakukan blacklist/unblacklist")
    
    # Update status
    await customers.update_one(
        {"id": customer_id},
        {"$set": {
            "credit_status": new_status,
            "credit_hold_reason": data.reason if new_status != "active" else "",
            "credit_updated_at": datetime.now(timezone.utc).isoformat(),
            "credit_updated_by": user.get("user_id")
        }}
    )
    
    # Audit log
    await db.audit_logs.insert_one({
        "id": str(uuid.uuid4()),
        "action": f"credit_{data.action}",
        "module": "credit_control",
        "target_id": customer_id,
        "target_name": customer.get("name"),
        "description": f"Credit status: {old_status} -> {new_status}. Reason: {data.reason}",
        "old_value": old_status,
        "new_value": new_status,
        "user_id": user.get("user_id"),
        "user_name": user.get("name"),
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    return {
        "success": True,
        "message": f"Customer credit status changed to {CREDIT_STATUS.get(new_status, {}).get('name', new_status)}",
        "customer_id": customer_id,
        "old_status": old_status,
        "new_status": new_status
    }

@router.post("/override-request")
async def request_credit_override(
    data: CreditOverrideRequest,
    user: dict = Depends(get_current_user)
):
    """
    Request approval for credit override
    Integrates with Approval Workflow Engine
    """
    db = get_database()
    
    # Get customer info
    customer = await customers.find_one({"id": data.customer_id}, {"_id": 0})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer tidak ditemukan")
    
    # Calculate override amount
    override_amount = data.requested_amount - (data.credit_limit - data.current_balance)
    if override_amount < 0:
        override_amount = data.requested_amount  # Full amount if blocked for other reasons
    
    # Create approval request through Approval Workflow Engine
    result = await create_approval_request(
        db,
        approval_type="credit_override",
        reference_type=data.transaction_type,
        reference_id=data.transaction_id,
        reference_no=data.transaction_no,
        amount=override_amount,
        variance_percent=0,
        branch_id=user.get("branch_id"),
        requester=user,
        notes=f"Override untuk {customer.get('name')} ({customer.get('code')}). Alasan: {data.override_reason}",
        data={
            "customer_id": data.customer_id,
            "customer_name": customer.get("name"),
            "customer_code": customer.get("code"),
            "credit_limit": data.credit_limit,
            "current_balance": data.current_balance,
            "requested_amount": data.requested_amount,
            "override_reason": data.override_reason
        }
    )
    
    return result

@router.get("/override-status/{transaction_id}")
async def check_override_status(
    transaction_id: str,
    user: dict = Depends(get_current_user)
):
    """Check if a credit override has been approved"""
    db = get_database()
    
    approval = await db.approval_requests.find_one(
        {
            "reference_id": transaction_id,
            "approval_type": "credit_override"
        },
        {"_id": 0}
    )
    
    if not approval:
        return {
            "has_override": False,
            "status": None,
            "message": "Tidak ada override request untuk transaksi ini"
        }
    
    return {
        "has_override": True,
        "approval_id": approval.get("id"),
        "approval_no": approval.get("approval_no"),
        "status": approval.get("status"),
        "approved_by": approval.get("approved_by_name"),
        "approved_at": approval.get("action_at"),
        "can_proceed": approval.get("status") == "approved"
    }

# ==================== DASHBOARD & REPORTS ====================

@router.get("/dashboard")
async def get_credit_dashboard(
    user: dict = Depends(get_current_user)
):
    """Get credit control dashboard summary"""
    db = get_database()
    
    # Customers by credit status
    status_pipeline = [
        {"$match": {"is_active": True}},
        {"$group": {
            "_id": {"$ifNull": ["$credit_status", "active"]},
            "count": {"$sum": 1}
        }}
    ]
    status_result = await customers.aggregate(status_pipeline).to_list(10)
    by_status = {item["_id"]: item["count"] for item in status_result}
    
    # Total outstanding AR
    ar_collection = db["ar_system"]
    ar_totals = await ar_collection.aggregate([
        {"$match": {"status": {"$in": ["unpaid", "partial"]}}},
        {"$group": {
            "_id": None,
            "total_outstanding": {"$sum": "$outstanding_amount"},
            "count": {"$sum": 1}
        }}
    ]).to_list(1)
    total_ar = ar_totals[0] if ar_totals else {"total_outstanding": 0, "count": 0}
    
    # Overdue AR
    today = datetime.now(timezone.utc).isoformat()
    overdue_totals = await ar_collection.aggregate([
        {"$match": {"status": {"$in": ["unpaid", "partial"]}, "due_date": {"$lt": today}}},
        {"$group": {
            "_id": None,
            "total_overdue": {"$sum": "$outstanding_amount"},
            "count": {"$sum": 1}
        }}
    ]).to_list(1)
    total_overdue = overdue_totals[0] if overdue_totals else {"total_overdue": 0, "count": 0}
    
    # Top 10 customers by outstanding
    top_customers = await ar_collection.aggregate([
        {"$match": {"status": {"$in": ["unpaid", "partial"]}}},
        {"$group": {
            "_id": "$customer_id",
            "customer_name": {"$first": "$customer_name"},
            "total_outstanding": {"$sum": "$outstanding_amount"},
            "invoice_count": {"$sum": 1}
        }},
        {"$sort": {"total_outstanding": -1}},
        {"$limit": 10}
    ]).to_list(10)
    
    # Pending credit override approvals
    pending_overrides = await db.approval_requests.count_documents({
        "approval_type": "credit_override",
        "status": "pending"
    })
    
    return {
        "customers_by_status": by_status,
        "total_customers": sum(by_status.values()),
        "total_outstanding": total_ar.get("total_outstanding", 0),
        "outstanding_invoice_count": total_ar.get("count", 0),
        "total_overdue": total_overdue.get("total_overdue", 0),
        "overdue_invoice_count": total_overdue.get("count", 0),
        "overdue_percentage": round(total_overdue.get("total_overdue", 0) / total_ar.get("total_outstanding", 1) * 100, 2) if total_ar.get("total_outstanding", 0) > 0 else 0,
        "top_outstanding_customers": top_customers,
        "pending_override_approvals": pending_overrides
    }

@router.get("/at-risk")
async def get_at_risk_customers(
    min_overdue_days: int = 7,
    user: dict = Depends(get_current_user)
):
    """Get customers at risk (near limit or overdue)"""
    db = get_database()
    
    # Get all active customers with credit enabled
    all_customers = await customers.find(
        {"is_active": True, "credit_limit": {"$gt": 0}},
        {"_id": 0}
    ).to_list(500)
    
    at_risk = []
    for customer in all_customers:
        credit_info = await get_customer_credit_info(db, customer["id"])
        if credit_info:
            # Check if at risk
            utilization = (credit_info["outstanding_balance"] / credit_info["credit_limit"] * 100) if credit_info["credit_limit"] > 0 else 0
            
            is_at_risk = (
                credit_info["effective_status"] in ["warning", "hold", "blocked"] or
                utilization >= 80 or
                credit_info["overdue_days"] >= min_overdue_days
            )
            
            if is_at_risk:
                at_risk.append({
                    **credit_info,
                    "utilization_percent": round(utilization, 2),
                    "risk_factors": []
                })
                
                # Add risk factors
                if credit_info["effective_status"] in ["hold", "blocked"]:
                    at_risk[-1]["risk_factors"].append(f"Status: {credit_info['effective_status']}")
                if utilization >= 100:
                    at_risk[-1]["risk_factors"].append(f"Melebihi limit ({utilization:.0f}%)")
                elif utilization >= 80:
                    at_risk[-1]["risk_factors"].append(f"Mendekati limit ({utilization:.0f}%)")
                if credit_info["overdue_days"] >= min_overdue_days:
                    at_risk[-1]["risk_factors"].append(f"Overdue {credit_info['overdue_days']} hari")
    
    # Sort by risk (blocked first, then by utilization)
    at_risk.sort(key=lambda x: (
        0 if x["effective_status"] == "blocked" else 1 if x["effective_status"] == "hold" else 2,
        -x.get("utilization_percent", 0)
    ))
    
    return {
        "items": at_risk,
        "total": len(at_risk),
        "total_at_risk_balance": sum(c["outstanding_balance"] for c in at_risk)
    }

@router.get("/audit-log")
async def get_credit_audit_log(
    customer_id: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = 50,
    user: dict = Depends(get_current_user)
):
    """Get credit control audit logs"""
    db = get_database()
    
    query = {"module": "credit_control"}
    if customer_id:
        query["target_id"] = customer_id
    if action:
        query["action"] = {"$regex": action, "$options": "i"}
    
    logs = await db.audit_logs.find(query, {"_id": 0}).sort("timestamp", -1).limit(limit).to_list(limit)
    
    return {"items": logs, "total": len(logs)}
