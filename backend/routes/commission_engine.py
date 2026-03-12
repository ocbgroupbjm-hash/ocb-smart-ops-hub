"""
OCB TITAN ERP - PHASE 3 OPERATIONAL CONTROL SYSTEM
Module 6: COMMISSION ENGINE
Following OCB TITAN AI MASTER LAW - NON-DESTRUCTIVE Development

Fitur:
1. Komisi berdasarkan achievement target
2. Komisi berdasarkan sales value
3. Bonus jika achievement >110%
4. Perhitungan per salesman, branch, period
5. Integrasi dengan sales target system
6. Integrasi dengan accounting journal (expense commission)

Formula:
- Base Commission = Sales Value × Commission Rate
- Target Achievement Bonus = Base × (Achievement% - 100%) × Multiplier (if >100%)
- Super Bonus = Base × Extra Rate (if >110%)
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
from database import get_db as get_database
from routes.auth import get_current_user
from routes.rbac_middleware import require_permission
import uuid

router = APIRouter(prefix="/api/commission", tags=["Commission Engine"])

# ==================== CONSTANTS ====================

COMMISSION_STATUS = {
    "calculated": {"name": "Calculated", "color": "blue"},
    "approved": {"name": "Approved", "color": "green"},
    "paid": {"name": "Paid", "color": "purple"},
    "cancelled": {"name": "Cancelled", "color": "red"}
}

DEFAULT_COMMISSION_RATES = {
    "base_rate": 0.02,  # 2% base commission
    "achievement_multiplier": 0.5,  # 0.5x for each % above 100%
    "super_bonus_threshold": 110,  # Threshold for super bonus
    "super_bonus_rate": 0.01,  # Extra 1% for >110%
    "min_achievement_for_commission": 50  # Minimum achievement to earn commission
}

# ==================== PYDANTIC MODELS ====================

class CommissionPolicyUpdate(BaseModel):
    base_rate: Optional[float] = Field(None, ge=0, le=1)
    achievement_multiplier: Optional[float] = Field(None, ge=0)
    super_bonus_threshold: Optional[float] = Field(None, ge=100)
    super_bonus_rate: Optional[float] = Field(None, ge=0, le=1)
    min_achievement_for_commission: Optional[float] = Field(None, ge=0, le=100)

class CommissionCalculateRequest(BaseModel):
    period_type: str = "monthly"  # monthly, quarterly, yearly
    period_start: str  # YYYY-MM-DD
    period_end: str  # YYYY-MM-DD
    calculate_for: str = "all"  # all, salesman, branch
    ref_id: Optional[str] = None  # salesman_id or branch_id if not all

class CommissionApproveRequest(BaseModel):
    commission_ids: List[str]
    notes: Optional[str] = ""

class CommissionPayRequest(BaseModel):
    commission_ids: List[str]
    payment_method: str = "bank_transfer"  # bank_transfer, cash
    payment_reference: Optional[str] = ""
    notes: Optional[str] = ""

# ==================== HELPER FUNCTIONS ====================

async def get_commission_policy(db) -> Dict[str, Any]:
    """Get commission policy settings"""
    policy = await db.commission_policy.find_one({"active": True}, {"_id": 0})
    if not policy:
        return DEFAULT_COMMISSION_RATES.copy()
    return policy

async def get_sales_data(db, salesman_id: str = None, branch_id: str = None, 
                         period_start: str = None, period_end: str = None) -> Dict[str, Any]:
    """Get sales data from transactions"""
    
    query = {
        "status": {"$nin": ["cancelled", "void"]}
    }
    
    if period_start and period_end:
        query["transaction_date"] = {"$gte": period_start, "$lte": period_end}
    
    if salesman_id:
        query["salesman_id"] = salesman_id
    if branch_id:
        query["branch_id"] = branch_id
    
    # Aggregate from sales_invoices
    pipeline = [
        {"$match": query},
        {"$group": {
            "_id": None,
            "total_sales": {"$sum": "$grand_total"},
            "total_qty": {"$sum": "$total_qty"},
            "transaction_count": {"$sum": 1}
        }}
    ]
    
    result = await db.sales_invoices.aggregate(pipeline).to_list(1)
    
    # Also check POS transactions
    pos_result = await db.pos_transactions.aggregate(pipeline).to_list(1)
    
    sales_total = 0
    qty_total = 0
    tx_count = 0
    
    if result:
        sales_total += result[0].get("total_sales", 0)
        qty_total += result[0].get("total_qty", 0)
        tx_count += result[0].get("transaction_count", 0)
    
    if pos_result:
        sales_total += pos_result[0].get("total_sales", 0)
        qty_total += pos_result[0].get("total_qty", 0)
        tx_count += pos_result[0].get("transaction_count", 0)
    
    return {
        "total_sales": sales_total,
        "total_qty": qty_total,
        "transaction_count": tx_count
    }

async def get_target_achievement(db, target_type: str, ref_id: str, 
                                  period_start: str, period_end: str) -> Dict[str, Any]:
    """Get target and achievement from sales_targets"""
    
    target = await db.sales_targets.find_one({
        "target_type": target_type,
        "target_ref_id": ref_id,
        "period_start": {"$lte": period_end},
        "period_end": {"$gte": period_start}
    }, {"_id": 0})
    
    if not target:
        return {
            "has_target": False,
            "target_value": 0,
            "achievement_percent": 0
        }
    
    # Get actual sales
    if target_type == "salesman":
        sales_data = await get_sales_data(db, salesman_id=ref_id, 
                                          period_start=period_start, period_end=period_end)
    else:
        sales_data = await get_sales_data(db, branch_id=ref_id,
                                          period_start=period_start, period_end=period_end)
    
    target_value = target.get("target_value", 0)
    actual_value = sales_data.get("total_sales", 0)
    achievement = (actual_value / target_value * 100) if target_value > 0 else 0
    
    return {
        "has_target": True,
        "target_id": target.get("id"),
        "target_value": target_value,
        "actual_value": actual_value,
        "achievement_percent": round(achievement, 2)
    }

async def calculate_commission(policy: Dict, sales_value: float, achievement: float) -> Dict[str, Any]:
    """Calculate commission based on policy"""
    
    # Check minimum achievement
    if achievement < policy.get("min_achievement_for_commission", 50):
        return {
            "eligible": False,
            "reason": f"Achievement {achievement}% below minimum {policy.get('min_achievement_for_commission')}%",
            "base_commission": 0,
            "achievement_bonus": 0,
            "super_bonus": 0,
            "total_commission": 0
        }
    
    base_rate = policy.get("base_rate", 0.02)
    base_commission = sales_value * base_rate
    
    achievement_bonus = 0
    super_bonus = 0
    
    # Achievement bonus (if >100%)
    if achievement > 100:
        over_achievement = achievement - 100
        multiplier = policy.get("achievement_multiplier", 0.5)
        achievement_bonus = base_commission * (over_achievement / 100) * multiplier
    
    # Super bonus (if >110%)
    super_threshold = policy.get("super_bonus_threshold", 110)
    if achievement >= super_threshold:
        super_rate = policy.get("super_bonus_rate", 0.01)
        super_bonus = sales_value * super_rate
    
    total = base_commission + achievement_bonus + super_bonus
    
    return {
        "eligible": True,
        "reason": None,
        "base_commission": round(base_commission, 0),
        "achievement_bonus": round(achievement_bonus, 0),
        "super_bonus": round(super_bonus, 0),
        "total_commission": round(total, 0),
        "breakdown": {
            "base_rate": base_rate,
            "sales_value": sales_value,
            "achievement": achievement,
            "over_achievement": max(0, achievement - 100),
            "super_eligible": achievement >= super_threshold
        }
    }

# ==================== API ENDPOINTS ====================

@router.get("/policy")
async def get_policy(user: dict = Depends(get_current_user)):
    """Get current commission policy"""
    db = get_database()
    policy = await get_commission_policy(db)
    return policy

@router.put("/policy")
async def update_policy(
    data: CommissionPolicyUpdate,
    user: dict = Depends(require_permission("commission", "edit"))
):
    """Update commission policy"""
    db = get_database()
    
    current = await get_commission_policy(db)
    
    update_data = {k: v for k, v in data.dict().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    update_data["updated_by"] = user.get("user_id")
    update_data["active"] = True
    
    merged = {**current, **update_data}
    
    # Deactivate old policy
    await db.commission_policy.update_many({}, {"$set": {"active": False}})
    
    # Insert new policy
    merged["id"] = str(uuid.uuid4())
    await db.commission_policy.insert_one(merged)
    merged.pop("_id", None)  # Remove MongoDB _id before returning
    
    # Audit log
    await db.audit_logs.insert_one({
        "id": str(uuid.uuid4()),
        "action": "commission_policy_update",
        "module": "commission",
        "description": f"Updated commission policy: {update_data}",
        "user_id": user.get("user_id"),
        "user_name": user.get("name"),
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    return {"success": True, "policy": merged}

@router.post("/calculate")
async def calculate_commissions(
    data: CommissionCalculateRequest,
    user: dict = Depends(require_permission("commission", "create"))
):
    """Calculate commissions for a period"""
    db = get_database()
    policy = await get_commission_policy(db)
    
    commissions = []
    skipped = []
    
    if data.calculate_for == "salesman" and data.ref_id:
        # Calculate for specific salesman
        salesman = await db.users.find_one({"id": data.ref_id}, {"_id": 0})
        if salesman:
            result = await _calculate_for_salesman(
                db, policy, salesman, data.period_start, data.period_end, 
                data.period_type, user
            )
            if result.get("commission"):
                commissions.append(result["commission"])
            else:
                skipped.append(result)
    
    elif data.calculate_for == "branch" and data.ref_id:
        # Calculate for specific branch
        branch = await db.branches.find_one({"id": data.ref_id}, {"_id": 0})
        if branch:
            result = await _calculate_for_branch(
                db, policy, branch, data.period_start, data.period_end,
                data.period_type, user
            )
            if result.get("commission"):
                commissions.append(result["commission"])
            else:
                skipped.append(result)
    
    else:
        # Calculate for all salesmen
        salesmen = await db.users.find(
            {"role": {"$in": ["sales", "kasir"]}, "is_active": {"$ne": False}},
            {"_id": 0}
        ).to_list(200)
        
        for salesman in salesmen:
            # Check if commission already calculated
            existing = await db.commissions.find_one({
                "ref_type": "salesman",
                "ref_id": salesman["id"],
                "period_start": data.period_start,
                "period_end": data.period_end,
                "status": {"$ne": "cancelled"}
            })
            
            if existing:
                skipped.append({
                    "ref_name": salesman.get("name"),
                    "reason": "Already calculated"
                })
                continue
            
            result = await _calculate_for_salesman(
                db, policy, salesman, data.period_start, data.period_end,
                data.period_type, user
            )
            if result.get("commission"):
                commissions.append(result["commission"])
            else:
                skipped.append(result)
    
    return {
        "success": True,
        "calculated": len(commissions),
        "skipped": len(skipped),
        "commissions": commissions[:20],
        "skipped_details": skipped[:10]
    }

async def _calculate_for_salesman(db, policy, salesman, period_start, period_end, period_type, user):
    """Calculate commission for a single salesman"""
    
    # Get sales data
    sales_data = await get_sales_data(
        db, salesman_id=salesman["id"],
        period_start=period_start, period_end=period_end
    )
    
    if sales_data["total_sales"] <= 0:
        return {
            "ref_name": salesman.get("name"),
            "reason": "No sales in period"
        }
    
    # Get target achievement
    achievement_data = await get_target_achievement(
        db, "salesman", salesman["id"], period_start, period_end
    )
    
    achievement = achievement_data.get("achievement_percent", 100)  # Default 100% if no target
    
    # Calculate commission
    calc_result = await calculate_commission(policy, sales_data["total_sales"], achievement)
    
    if not calc_result["eligible"]:
        return {
            "ref_name": salesman.get("name"),
            "reason": calc_result["reason"]
        }
    
    # Create commission record
    commission = {
        "id": str(uuid.uuid4()),
        "ref_type": "salesman",
        "ref_id": salesman["id"],
        "ref_name": salesman.get("name"),
        "period_type": period_type,
        "period_start": period_start,
        "period_end": period_end,
        "sales_value": sales_data["total_sales"],
        "transaction_count": sales_data["transaction_count"],
        "target_value": achievement_data.get("target_value", 0),
        "achievement_percent": achievement,
        "has_target": achievement_data.get("has_target", False),
        "base_commission": calc_result["base_commission"],
        "achievement_bonus": calc_result["achievement_bonus"],
        "super_bonus": calc_result["super_bonus"],
        "total_commission": calc_result["total_commission"],
        "breakdown": calc_result["breakdown"],
        "status": "calculated",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user.get("user_id"),
        "created_by_name": user.get("name")
    }
    
    await db.commissions.insert_one(commission)
    commission.pop("_id", None)
    
    return {"commission": commission}

async def _calculate_for_branch(db, policy, branch, period_start, period_end, period_type, user):
    """Calculate commission for a branch (aggregate)"""
    
    # Get sales data
    sales_data = await get_sales_data(
        db, branch_id=branch["id"],
        period_start=period_start, period_end=period_end
    )
    
    if sales_data["total_sales"] <= 0:
        return {
            "ref_name": branch.get("name"),
            "reason": "No sales in period"
        }
    
    # Get target achievement
    achievement_data = await get_target_achievement(
        db, "branch", branch["id"], period_start, period_end
    )
    
    achievement = achievement_data.get("achievement_percent", 100)
    
    # Calculate commission
    calc_result = await calculate_commission(policy, sales_data["total_sales"], achievement)
    
    if not calc_result["eligible"]:
        return {
            "ref_name": branch.get("name"),
            "reason": calc_result["reason"]
        }
    
    # Create commission record
    commission = {
        "id": str(uuid.uuid4()),
        "ref_type": "branch",
        "ref_id": branch["id"],
        "ref_name": branch.get("name"),
        "period_type": period_type,
        "period_start": period_start,
        "period_end": period_end,
        "sales_value": sales_data["total_sales"],
        "transaction_count": sales_data["transaction_count"],
        "target_value": achievement_data.get("target_value", 0),
        "achievement_percent": achievement,
        "has_target": achievement_data.get("has_target", False),
        "base_commission": calc_result["base_commission"],
        "achievement_bonus": calc_result["achievement_bonus"],
        "super_bonus": calc_result["super_bonus"],
        "total_commission": calc_result["total_commission"],
        "breakdown": calc_result["breakdown"],
        "status": "calculated",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user.get("user_id"),
        "created_by_name": user.get("name")
    }
    
    await db.commissions.insert_one(commission)
    commission.pop("_id", None)
    
    return {"commission": commission}

@router.get("/list")
async def list_commissions(
    status: Optional[str] = None,
    ref_type: Optional[str] = None,
    period_type: Optional[str] = None,
    period_start: Optional[str] = None,
    limit: int = 100,
    user: dict = Depends(get_current_user)
):
    """List commissions with filters"""
    db = get_database()
    
    query = {}
    if status:
        query["status"] = status
    if ref_type:
        query["ref_type"] = ref_type
    if period_type:
        query["period_type"] = period_type
    if period_start:
        query["period_start"] = period_start
    
    commissions = await db.commissions.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    
    # Summary
    summary = {
        "total": len(commissions),
        "calculated": sum(1 for c in commissions if c["status"] == "calculated"),
        "approved": sum(1 for c in commissions if c["status"] == "approved"),
        "paid": sum(1 for c in commissions if c["status"] == "paid"),
        "total_amount": sum(c["total_commission"] for c in commissions),
        "total_sales": sum(c["sales_value"] for c in commissions)
    }
    
    return {"items": commissions, "summary": summary}

@router.get("/dashboard/summary")
async def get_commission_dashboard(
    period_type: str = "monthly",
    user: dict = Depends(get_current_user)
):
    """Get commission dashboard summary"""
    db = get_database()
    
    # Get current period bounds
    now = datetime.now(timezone.utc)
    if period_type == "monthly":
        period_start = now.replace(day=1).strftime("%Y-%m-%d")
        if now.month == 12:
            period_end = now.replace(year=now.year+1, month=1, day=1) - timedelta(days=1)
        else:
            period_end = now.replace(month=now.month+1, day=1) - timedelta(days=1)
        period_end = period_end.strftime("%Y-%m-%d")
    else:
        period_start = now.replace(month=1, day=1).strftime("%Y-%m-%d")
        period_end = now.replace(month=12, day=31).strftime("%Y-%m-%d")
    
    # Get commissions for current period
    commissions = await db.commissions.find({
        "period_start": period_start,
        "status": {"$ne": "cancelled"}
    }, {"_id": 0}).to_list(500)
    
    # Aggregate by status
    by_status = {}
    for c in commissions:
        status = c["status"]
        if status not in by_status:
            by_status[status] = {"count": 0, "amount": 0}
        by_status[status]["count"] += 1
        by_status[status]["amount"] += c["total_commission"]
    
    # Top earners
    top_earners = sorted(commissions, key=lambda x: x["total_commission"], reverse=True)[:5]
    
    # Get policy
    policy = await get_commission_policy(db)
    
    return {
        "period_type": period_type,
        "period_start": period_start,
        "period_end": period_end,
        "by_status": by_status,
        "total_commissions": len(commissions),
        "total_amount": sum(c["total_commission"] for c in commissions),
        "total_sales": sum(c["sales_value"] for c in commissions),
        "top_earners": [{
            "name": c["ref_name"],
            "amount": c["total_commission"],
            "achievement": c["achievement_percent"]
        } for c in top_earners],
        "policy": policy
    }

@router.get("/{commission_id}")
async def get_commission_detail(
    commission_id: str,
    user: dict = Depends(get_current_user)
):
    """Get commission detail"""
    db = get_database()
    
    commission = await db.commissions.find_one({"id": commission_id}, {"_id": 0})
    if not commission:
        raise HTTPException(status_code=404, detail="Commission tidak ditemukan")
    
    return commission

@router.post("/approve")
async def approve_commissions(
    data: CommissionApproveRequest,
    user: dict = Depends(require_permission("commission", "approve"))
):
    """Approve calculated commissions"""
    db = get_database()
    
    approved_count = 0
    errors = []
    
    for commission_id in data.commission_ids:
        commission = await db.commissions.find_one({"id": commission_id})
        if not commission:
            errors.append(f"{commission_id}: Not found")
            continue
        
        if commission["status"] != "calculated":
            errors.append(f"{commission_id}: Status is {commission['status']}, not calculated")
            continue
        
        await db.commissions.update_one(
            {"id": commission_id},
            {"$set": {
                "status": "approved",
                "approved_at": datetime.now(timezone.utc).isoformat(),
                "approved_by": user.get("user_id"),
                "approved_by_name": user.get("name"),
                "approval_notes": data.notes
            }}
        )
        approved_count += 1
    
    # Audit log
    await db.audit_logs.insert_one({
        "id": str(uuid.uuid4()),
        "action": "commission_approve",
        "module": "commission",
        "description": f"Approved {approved_count} commissions",
        "user_id": user.get("user_id"),
        "user_name": user.get("name"),
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    return {
        "success": True,
        "approved": approved_count,
        "errors": errors
    }

@router.post("/pay")
async def pay_commissions(
    data: CommissionPayRequest,
    user: dict = Depends(require_permission("commission", "approve"))
):
    """Mark commissions as paid and create accounting journal"""
    db = get_database()
    
    paid_count = 0
    total_paid = 0
    errors = []
    paid_items = []
    
    for commission_id in data.commission_ids:
        commission = await db.commissions.find_one({"id": commission_id})
        if not commission:
            errors.append(f"{commission_id}: Not found")
            continue
        
        if commission["status"] != "approved":
            errors.append(f"{commission_id}: Status is {commission['status']}, not approved")
            continue
        
        await db.commissions.update_one(
            {"id": commission_id},
            {"$set": {
                "status": "paid",
                "paid_at": datetime.now(timezone.utc).isoformat(),
                "paid_by": user.get("user_id"),
                "paid_by_name": user.get("name"),
                "payment_method": data.payment_method,
                "payment_reference": data.payment_reference,
                "payment_notes": data.notes
            }}
        )
        
        paid_count += 1
        total_paid += commission["total_commission"]
        paid_items.append({
            "ref_name": commission["ref_name"],
            "amount": commission["total_commission"]
        })
    
    # Create accounting journal entry
    if paid_count > 0:
        journal_entry = {
            "id": str(uuid.uuid4()),
            "journal_no": f"JV-COMM-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            "journal_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "description": f"Commission payment - {paid_count} items",
            "reference_type": "commission_payment",
            "reference_id": data.commission_ids[0] if len(data.commission_ids) == 1 else "batch",
            "entries": [
                {
                    "account_code": "5-2001",  # Commission Expense
                    "account_name": "Beban Komisi",
                    "debit": total_paid,
                    "credit": 0,
                    "description": f"Commission for {paid_count} person(s)"
                },
                {
                    "account_code": "1-1001" if data.payment_method == "cash" else "1-1101",
                    "account_name": "Kas" if data.payment_method == "cash" else "Bank",
                    "debit": 0,
                    "credit": total_paid,
                    "description": f"Payment: {data.payment_reference or data.payment_method}"
                }
            ],
            "total_debit": total_paid,
            "total_credit": total_paid,
            "status": "posted",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": user.get("user_id"),
            "created_by_name": user.get("name")
        }
        
        await db.journals.insert_one(journal_entry)
    
    # Audit log
    await db.audit_logs.insert_one({
        "id": str(uuid.uuid4()),
        "action": "commission_pay",
        "module": "commission",
        "description": f"Paid {paid_count} commissions, total Rp {total_paid:,.0f}",
        "user_id": user.get("user_id"),
        "user_name": user.get("name"),
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    return {
        "success": True,
        "paid": paid_count,
        "total_amount": total_paid,
        "paid_items": paid_items,
        "errors": errors
    }

@router.delete("/{commission_id}")
async def cancel_commission(
    commission_id: str,
    user: dict = Depends(require_permission("commission", "delete"))
):
    """Cancel a commission (only calculated status)"""
    db = get_database()
    
    commission = await db.commissions.find_one({"id": commission_id})
    if not commission:
        raise HTTPException(status_code=404, detail="Commission tidak ditemukan")
    
    if commission["status"] != "calculated":
        raise HTTPException(
            status_code=400, 
            detail=f"Hanya commission dengan status calculated yang dapat dibatalkan. Status saat ini: {commission['status']}"
        )
    
    await db.commissions.update_one(
        {"id": commission_id},
        {"$set": {
            "status": "cancelled",
            "cancelled_at": datetime.now(timezone.utc).isoformat(),
            "cancelled_by": user.get("user_id")
        }}
    )
    
    return {"success": True, "message": "Commission cancelled"}

# ==================== SIMULATION / PREVIEW ====================

@router.post("/simulate")
async def simulate_commission(
    sales_value: float,
    achievement: float = 100,
    user: dict = Depends(get_current_user)
):
    """Simulate commission calculation (for preview)"""
    db = get_database()
    policy = await get_commission_policy(db)
    
    result = await calculate_commission(policy, sales_value, achievement)
    result["policy_used"] = policy
    
    return result
