"""
OCB TITAN ERP - PHASE 3 OPERATIONAL CONTROL SYSTEM
Module 6: COMMISSION ENGINE (ENHANCED)
Following OCB TITAN AI MASTER LAW - NON-DESTRUCTIVE Development

COMMISSION TYPES:
1. Sales value based commission
2. Quantity based commission
3. Target achievement bonus
4. Branch target bonus pool
5. Super bonus if achievement > threshold

COMMISSION LEVELS:
- Per salesman
- Per branch
- Per period
- Optional per category

TARGET RULES:
- <80% target = no bonus (configurable)
- 80%-100% = base commission
- 100%-110% = bonus commission
- >110% = super bonus

BRANCH BONUS:
- Jika branch mencapai target, sistem membuat bonus pool
- Bonus pool dibagikan ke tim branch berdasarkan contribution

ACCOUNTING INTEGRATION:
- Journal entries untuk commission expense
- Commission payable tracking

SAFETY RULES:
- Commission by sales value
- Commission by quantity
- Commission by margin safe mode (optional)

AUDIT TRAIL:
- Semua perubahan policy tercatat
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

COMMISSION_TYPES = {
    "sales_value": {"name": "Sales Value Based", "description": "Commission based on total sales value"},
    "quantity": {"name": "Quantity Based", "description": "Commission based on units sold"},
    "achievement": {"name": "Achievement Based", "description": "Commission based on target achievement"},
    "branch_pool": {"name": "Branch Pool", "description": "Shared bonus pool for branch team"}
}

DEFAULT_COMMISSION_RATES = {
    # Base settings
    "base_rate": 0.02,  # 2% base commission
    "quantity_rate": 500,  # Rp 500 per unit sold
    
    # Achievement thresholds
    "min_achievement_for_commission": 80,  # Minimum 80% to earn commission
    "achievement_multiplier": 0.5,  # 0.5x bonus for each % above 100%
    "super_bonus_threshold": 110,  # Threshold for super bonus
    "super_bonus_rate": 0.01,  # Extra 1% for >110%
    
    # Branch bonus pool
    "branch_pool_enabled": True,
    "branch_pool_rate": 0.005,  # 0.5% of branch sales goes to pool
    "branch_pool_distribution": "contribution",  # contribution, equal
    
    # Safety settings
    "commission_type": "sales_value",  # sales_value, quantity, hybrid
    "margin_safe_mode": False,  # If true, only calculate on profitable sales
    "min_margin_percent": 10,  # Minimum margin required if margin_safe_mode
    
    # Caps
    "max_commission_percent": 10,  # Maximum commission as % of sales
    "max_commission_amount": 50000000  # Maximum commission amount per period
}

# ==================== PYDANTIC MODELS ====================

class CommissionPolicyUpdate(BaseModel):
    # Base rates
    base_rate: Optional[float] = Field(None, ge=0, le=1)
    quantity_rate: Optional[float] = Field(None, ge=0)
    
    # Achievement settings
    min_achievement_for_commission: Optional[float] = Field(None, ge=0, le=100)
    achievement_multiplier: Optional[float] = Field(None, ge=0)
    super_bonus_threshold: Optional[float] = Field(None, ge=100)
    super_bonus_rate: Optional[float] = Field(None, ge=0, le=1)
    
    # Branch pool
    branch_pool_enabled: Optional[bool] = None
    branch_pool_rate: Optional[float] = Field(None, ge=0, le=1)
    branch_pool_distribution: Optional[str] = None  # contribution, equal
    
    # Safety settings
    commission_type: Optional[str] = None  # sales_value, quantity, hybrid
    margin_safe_mode: Optional[bool] = None
    min_margin_percent: Optional[float] = Field(None, ge=0, le=100)
    
    # Caps
    max_commission_percent: Optional[float] = Field(None, ge=0, le=100)
    max_commission_amount: Optional[float] = Field(None, ge=0)

class CommissionCalculateRequest(BaseModel):
    period_type: str = "monthly"  # monthly, quarterly, yearly
    period_start: str  # YYYY-MM-DD
    period_end: str  # YYYY-MM-DD
    calculate_for: str = "all"  # all, salesman, branch, branch_pool
    ref_id: Optional[str] = None  # salesman_id or branch_id if not all
    commission_type: Optional[str] = None  # Override policy commission_type

class CommissionApproveRequest(BaseModel):
    commission_ids: List[str]
    notes: Optional[str] = ""

class CommissionPayRequest(BaseModel):
    commission_ids: List[str]
    payment_method: str = "bank_transfer"  # bank_transfer, cash
    payment_reference: Optional[str] = ""
    notes: Optional[str] = ""

class BranchPoolDistributeRequest(BaseModel):
    pool_id: str
    distribution: List[Dict[str, Any]]  # [{"salesman_id": "x", "amount": 1000000}, ...]
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

async def calculate_commission(policy: Dict, sales_value: float, total_qty: int, achievement: float) -> Dict[str, Any]:
    """Calculate commission based on policy - ENHANCED VERSION"""
    
    commission_type = policy.get("commission_type", "sales_value")
    min_achievement = policy.get("min_achievement_for_commission", 80)
    
    # Check minimum achievement (80% rule)
    if achievement < min_achievement:
        return {
            "eligible": False,
            "reason": f"Achievement {achievement}% below minimum {min_achievement}% - No commission earned",
            "base_commission": 0,
            "quantity_commission": 0,
            "achievement_bonus": 0,
            "super_bonus": 0,
            "total_commission": 0
        }
    
    base_commission = 0
    quantity_commission = 0
    achievement_bonus = 0
    super_bonus = 0
    
    # Calculate base commission based on type
    if commission_type == "sales_value":
        base_rate = policy.get("base_rate", 0.02)
        base_commission = sales_value * base_rate
    elif commission_type == "quantity":
        quantity_rate = policy.get("quantity_rate", 500)
        quantity_commission = total_qty * quantity_rate
        base_commission = quantity_commission
    elif commission_type == "hybrid":
        base_rate = policy.get("base_rate", 0.02)
        quantity_rate = policy.get("quantity_rate", 500)
        base_commission = sales_value * base_rate
        quantity_commission = total_qty * quantity_rate
    
    # Achievement bonus (if 100%-110%)
    if 100 <= achievement < policy.get("super_bonus_threshold", 110):
        over_achievement = achievement - 100
        multiplier = policy.get("achievement_multiplier", 0.5)
        achievement_bonus = base_commission * (over_achievement / 100) * multiplier
    
    # Super bonus (if >110%)
    super_threshold = policy.get("super_bonus_threshold", 110)
    if achievement >= super_threshold:
        # Full achievement bonus for reaching super threshold
        multiplier = policy.get("achievement_multiplier", 0.5)
        achievement_bonus = base_commission * ((super_threshold - 100) / 100) * multiplier
        
        # Plus super bonus
        super_rate = policy.get("super_bonus_rate", 0.01)
        super_bonus = sales_value * super_rate
    
    total = base_commission + quantity_commission + achievement_bonus + super_bonus
    
    # Apply caps
    max_percent = policy.get("max_commission_percent", 10)
    max_amount = policy.get("max_commission_amount", 50000000)
    
    max_by_percent = sales_value * (max_percent / 100)
    
    if total > max_by_percent:
        total = max_by_percent
    if total > max_amount:
        total = max_amount
    
    return {
        "eligible": True,
        "reason": None,
        "commission_type": commission_type,
        "base_commission": round(base_commission, 0),
        "quantity_commission": round(quantity_commission, 0),
        "achievement_bonus": round(achievement_bonus, 0),
        "super_bonus": round(super_bonus, 0),
        "total_commission": round(total, 0),
        "capped": total < (base_commission + quantity_commission + achievement_bonus + super_bonus),
        "breakdown": {
            "base_rate": policy.get("base_rate", 0.02),
            "quantity_rate": policy.get("quantity_rate", 500),
            "sales_value": sales_value,
            "total_qty": total_qty,
            "achievement": achievement,
            "achievement_tier": "super" if achievement >= super_threshold else "bonus" if achievement >= 100 else "base",
            "super_eligible": achievement >= super_threshold
        }
    }

async def calculate_branch_pool(db, policy: Dict, branch_id: str, period_start: str, period_end: str) -> Dict[str, Any]:
    """Calculate branch bonus pool"""
    
    if not policy.get("branch_pool_enabled", True):
        return {"enabled": False, "pool_amount": 0}
    
    # Get branch sales
    sales_data = await get_sales_data(db, branch_id=branch_id, period_start=period_start, period_end=period_end)
    
    # Get branch target achievement
    achievement_data = await get_target_achievement(db, "branch", branch_id, period_start, period_end)
    
    # Only create pool if branch meets target (100%+)
    if achievement_data.get("achievement_percent", 0) < 100:
        return {
            "enabled": True,
            "eligible": False,
            "reason": f"Branch achievement {achievement_data.get('achievement_percent', 0)}% below 100%",
            "pool_amount": 0
        }
    
    # Calculate pool
    pool_rate = policy.get("branch_pool_rate", 0.005)
    pool_amount = sales_data["total_sales"] * pool_rate
    
    return {
        "enabled": True,
        "eligible": True,
        "pool_amount": round(pool_amount, 0),
        "branch_sales": sales_data["total_sales"],
        "achievement": achievement_data.get("achievement_percent", 0),
        "distribution_method": policy.get("branch_pool_distribution", "contribution")
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
    """Calculate commission for a single salesman - ENHANCED"""
    
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
    
    # Calculate commission with qty support
    calc_result = await calculate_commission(
        policy, 
        sales_data["total_sales"], 
        sales_data["total_qty"],
        achievement
    )
    
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
        "commission_type": calc_result.get("commission_type", "sales_value"),
        "sales_value": sales_data["total_sales"],
        "total_qty": sales_data["total_qty"],
        "transaction_count": sales_data["transaction_count"],
        "target_value": achievement_data.get("target_value", 0),
        "achievement_percent": achievement,
        "achievement_tier": calc_result["breakdown"].get("achievement_tier", "base"),
        "has_target": achievement_data.get("has_target", False),
        "base_commission": calc_result["base_commission"],
        "quantity_commission": calc_result.get("quantity_commission", 0),
        "achievement_bonus": calc_result["achievement_bonus"],
        "super_bonus": calc_result["super_bonus"],
        "total_commission": calc_result["total_commission"],
        "capped": calc_result.get("capped", False),
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
    
    # Calculate commission with qty support
    calc_result = await calculate_commission(
        policy, 
        sales_data["total_sales"], 
        sales_data["total_qty"],
        achievement
    )
    
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
        "commission_type": calc_result.get("commission_type", "sales_value"),
        "sales_value": sales_data["total_sales"],
        "total_qty": sales_data["total_qty"],
        "transaction_count": sales_data["transaction_count"],
        "target_value": achievement_data.get("target_value", 0),
        "achievement_percent": achievement,
        "achievement_tier": calc_result["breakdown"].get("achievement_tier", "base"),
        "has_target": achievement_data.get("has_target", False),
        "base_commission": calc_result["base_commission"],
        "quantity_commission": calc_result.get("quantity_commission", 0),
        "achievement_bonus": calc_result["achievement_bonus"],
        "super_bonus": calc_result["super_bonus"],
        "total_commission": calc_result["total_commission"],
        "capped": calc_result.get("capped", False),
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

# ==================== COMMISSION TYPES INFO ====================

@router.get("/types")
async def get_commission_types(user: dict = Depends(get_current_user)):
    """Get available commission types"""
    return {
        "types": COMMISSION_TYPES,
        "rules": {
            "achievement_tiers": [
                {"name": "No Commission", "range": "< 80%", "description": "Below minimum achievement"},
                {"name": "Base Commission", "range": "80% - 99%", "description": "Base rate only"},
                {"name": "Bonus Commission", "range": "100% - 109%", "description": "Base + achievement bonus"},
                {"name": "Super Bonus", "range": ">= 110%", "description": "Base + achievement bonus + super bonus"}
            ],
            "branch_pool": {
                "description": "Branch bonus pool created when branch achieves 100%+ target",
                "distribution_methods": ["contribution", "equal"]
            }
        }
    }

# ==================== POLICY AUDIT LOG ====================

@router.get("/policy/history")
async def get_policy_history(
    limit: int = 20,
    user: dict = Depends(get_current_user)
):
    """Get commission policy change history"""
    db = get_database()
    
    policies = await db.commission_policy.find({}, {"_id": 0}).sort("updated_at", -1).limit(limit).to_list(limit)
    
    return {"items": policies}

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
    total_qty: int = 0,
    achievement: float = 100,
    user: dict = Depends(get_current_user)
):
    """Simulate commission calculation (for preview)"""
    db = get_database()
    policy = await get_commission_policy(db)
    
    result = await calculate_commission(policy, sales_value, total_qty, achievement)
    result["policy_used"] = policy
    
    return result

# ==================== BRANCH BONUS POOL ====================

@router.post("/branch-pool/calculate")
async def calculate_branch_bonus_pool(
    branch_id: str,
    period_start: str,
    period_end: str,
    user: dict = Depends(require_permission("commission", "create"))
):
    """Calculate branch bonus pool for a period"""
    db = get_database()
    policy = await get_commission_policy(db)
    
    # Check if pool already exists
    existing = await db.branch_pools.find_one({
        "branch_id": branch_id,
        "period_start": period_start,
        "period_end": period_end,
        "status": {"$ne": "cancelled"}
    })
    
    if existing:
        raise HTTPException(status_code=400, detail="Branch pool already calculated for this period")
    
    # Get branch info
    branch = await db.branches.find_one({"id": branch_id}, {"_id": 0})
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")
    
    # Calculate pool
    pool_result = await calculate_branch_pool(db, policy, branch_id, period_start, period_end)
    
    if not pool_result.get("eligible", False):
        return {
            "success": False,
            "reason": pool_result.get("reason", "Branch not eligible for bonus pool"),
            "achievement": pool_result.get("achievement", 0)
        }
    
    # Create pool record
    pool = {
        "id": str(uuid.uuid4()),
        "branch_id": branch_id,
        "branch_name": branch.get("name"),
        "period_start": period_start,
        "period_end": period_end,
        "pool_amount": pool_result["pool_amount"],
        "branch_sales": pool_result["branch_sales"],
        "achievement": pool_result["achievement"],
        "distribution_method": pool_result["distribution_method"],
        "distributed_amount": 0,
        "remaining_amount": pool_result["pool_amount"],
        "status": "pending",
        "distributions": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user.get("user_id"),
        "created_by_name": user.get("name")
    }
    
    await db.branch_pools.insert_one(pool)
    pool.pop("_id", None)
    
    # Audit log
    await db.audit_logs.insert_one({
        "id": str(uuid.uuid4()),
        "action": "branch_pool_create",
        "module": "commission",
        "target_id": pool["id"],
        "description": f"Branch pool created: {branch.get('name')} - Rp {pool_result['pool_amount']:,.0f}",
        "user_id": user.get("user_id"),
        "user_name": user.get("name"),
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    return {
        "success": True,
        "pool": pool
    }

@router.get("/branch-pool/list")
async def list_branch_pools(
    status: Optional[str] = None,
    branch_id: Optional[str] = None,
    limit: int = 50,
    user: dict = Depends(get_current_user)
):
    """List branch bonus pools"""
    db = get_database()
    
    query = {}
    if status:
        query["status"] = status
    if branch_id:
        query["branch_id"] = branch_id
    
    pools = await db.branch_pools.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    
    summary = {
        "total": len(pools),
        "total_pool_amount": sum(p.get("pool_amount", 0) for p in pools),
        "total_distributed": sum(p.get("distributed_amount", 0) for p in pools),
        "pending": sum(1 for p in pools if p.get("status") == "pending"),
        "distributed": sum(1 for p in pools if p.get("status") == "distributed")
    }
    
    return {"items": pools, "summary": summary}

@router.post("/branch-pool/distribute")
async def distribute_branch_pool(
    data: BranchPoolDistributeRequest,
    user: dict = Depends(require_permission("commission", "approve"))
):
    """Distribute branch pool to team members"""
    db = get_database()
    
    pool = await db.branch_pools.find_one({"id": data.pool_id})
    if not pool:
        raise HTTPException(status_code=404, detail="Branch pool not found")
    
    if pool["status"] == "distributed":
        raise HTTPException(status_code=400, detail="Pool already fully distributed")
    
    # Validate distribution
    total_distribution = sum(d.get("amount", 0) for d in data.distribution)
    
    if total_distribution > pool["remaining_amount"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Distribution amount ({total_distribution:,.0f}) exceeds remaining pool ({pool['remaining_amount']:,.0f})"
        )
    
    # Process distributions
    distributions = []
    for dist in data.distribution:
        distribution_record = {
            "id": str(uuid.uuid4()),
            "salesman_id": dist.get("salesman_id"),
            "salesman_name": dist.get("salesman_name"),
            "amount": dist.get("amount", 0),
            "distributed_at": datetime.now(timezone.utc).isoformat(),
            "distributed_by": user.get("user_id")
        }
        distributions.append(distribution_record)
    
    # Update pool
    new_distributed = pool["distributed_amount"] + total_distribution
    new_remaining = pool["pool_amount"] - new_distributed
    new_status = "distributed" if new_remaining <= 0 else "partial"
    
    await db.branch_pools.update_one(
        {"id": data.pool_id},
        {
            "$set": {
                "distributed_amount": new_distributed,
                "remaining_amount": new_remaining,
                "status": new_status,
                "updated_at": datetime.now(timezone.utc).isoformat()
            },
            "$push": {"distributions": {"$each": distributions}}
        }
    )
    
    # Create individual commission records for each distribution
    for dist in data.distribution:
        commission = {
            "id": str(uuid.uuid4()),
            "ref_type": "branch_pool",
            "ref_id": dist.get("salesman_id"),
            "ref_name": dist.get("salesman_name"),
            "pool_id": data.pool_id,
            "branch_id": pool["branch_id"],
            "branch_name": pool["branch_name"],
            "period_start": pool["period_start"],
            "period_end": pool["period_end"],
            "commission_type": "branch_pool",
            "total_commission": dist.get("amount", 0),
            "status": "approved",
            "approved_at": datetime.now(timezone.utc).isoformat(),
            "approved_by": user.get("user_id"),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": user.get("user_id")
        }
        await db.commissions.insert_one(commission)
    
    # Audit log
    await db.audit_logs.insert_one({
        "id": str(uuid.uuid4()),
        "action": "branch_pool_distribute",
        "module": "commission",
        "target_id": data.pool_id,
        "description": f"Distributed Rp {total_distribution:,.0f} to {len(data.distribution)} members",
        "user_id": user.get("user_id"),
        "user_name": user.get("name"),
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    return {
        "success": True,
        "distributed_amount": total_distribution,
        "distributed_count": len(distributions),
        "remaining_pool": new_remaining,
        "new_status": new_status
    }
