"""
OCB TITAN ERP - PHASE 3 OPERATIONAL CONTROL SYSTEM
Module 6: SALES TARGET SYSTEM
Following OCB TITAN AI MASTER LAW - NON-DESTRUCTIVE Development

Fitur:
1. Target per Branch
2. Target per Salesman
3. Target per Period
4. Target per Category (optional)
5. Achievement Tracking
6. Progress Percentage
7. Status: on-track / behind / achieved
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
from database import get_db as get_database
from routes.auth import get_current_user
from routes.rbac_middleware import require_permission
import uuid

router = APIRouter(prefix="/api/sales-target", tags=["Sales Target System"])

# ==================== CONSTANTS ====================

TARGET_STATUS = {
    "on_track": {"name": "On Track", "color": "green"},
    "behind": {"name": "Behind", "color": "yellow"},
    "at_risk": {"name": "At Risk", "color": "orange"},
    "achieved": {"name": "Achieved", "color": "blue"},
    "exceeded": {"name": "Exceeded", "color": "purple"},
    "failed": {"name": "Failed", "color": "red"}
}

PERIOD_TYPES = ["daily", "weekly", "monthly", "quarterly", "yearly"]

# ==================== PYDANTIC MODELS ====================

class SalesTargetCreate(BaseModel):
    target_type: str = "branch"  # branch, salesman, category
    target_ref_id: str  # branch_id, user_id, or category
    target_ref_name: Optional[str] = ""
    period_type: str = "monthly"  # daily, weekly, monthly, quarterly, yearly
    period_start: str  # YYYY-MM-DD
    period_end: str  # YYYY-MM-DD
    target_value: float = Field(gt=0)  # Target amount (Rp)
    target_qty: Optional[float] = None  # Optional qty target
    # Bonus settings
    bonus_type: Optional[str] = "percentage"  # percentage, nominal
    bonus_value: Optional[float] = 0  # Bonus jika target tercapai
    bonus_min_achievement: Optional[float] = 100  # Min achievement % untuk bonus
    notes: Optional[str] = ""

class SalesTargetUpdate(BaseModel):
    target_value: Optional[float] = None
    target_qty: Optional[float] = None
    bonus_type: Optional[str] = None
    bonus_value: Optional[float] = None
    bonus_min_achievement: Optional[float] = None
    notes: Optional[str] = None

class SalesTargetFilter(BaseModel):
    target_type: Optional[str] = None
    period_type: Optional[str] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    status: Optional[str] = None

# ==================== HELPER FUNCTIONS ====================

async def get_sales_actual(db, target_type: str, ref_id: str, period_start: str, period_end: str) -> Dict[str, Any]:
    """Get actual sales from transactions"""
    
    query = {
        "transaction_date": {"$gte": period_start, "$lte": period_end},
        "status": {"$nin": ["cancelled", "void"]}
    }
    
    if target_type == "branch":
        query["branch_id"] = ref_id
    elif target_type == "salesman":
        query["salesman_id"] = ref_id
    elif target_type == "category":
        # Need to join with items - more complex query
        pass
    
    # Try sales_invoices first
    pipeline = [
        {"$match": query},
        {"$group": {
            "_id": None,
            "total_value": {"$sum": "$grand_total"},
            "total_qty": {"$sum": "$total_qty"},
            "transaction_count": {"$sum": 1}
        }}
    ]
    
    result = await db.sales_invoices.aggregate(pipeline).to_list(1)
    
    if not result:
        # Try pos_transactions
        pos_result = await db.pos_transactions.aggregate(pipeline).to_list(1)
        if pos_result:
            result = pos_result
    
    if result:
        return {
            "actual_value": result[0].get("total_value", 0),
            "actual_qty": result[0].get("total_qty", 0),
            "transaction_count": result[0].get("transaction_count", 0)
        }
    
    return {"actual_value": 0, "actual_qty": 0, "transaction_count": 0}

async def calculate_target_status(target_value: float, actual_value: float, period_end: str) -> str:
    """Calculate target status based on progress"""
    
    if target_value <= 0:
        return "on_track"
    
    achievement = (actual_value / target_value) * 100
    
    # Check if period ended
    try:
        end_date = datetime.fromisoformat(period_end)
        now = datetime.now(timezone.utc)
        period_ended = now > end_date
    except:
        period_ended = False
    
    if period_ended:
        if achievement >= 100:
            return "exceeded" if achievement >= 110 else "achieved"
        else:
            return "failed"
    else:
        # Calculate expected progress based on time
        try:
            # Simplified: assume linear progress
            if achievement >= 100:
                return "exceeded"
            elif achievement >= 80:
                return "on_track"
            elif achievement >= 60:
                return "behind"
            else:
                return "at_risk"
        except:
            return "on_track"

async def enrich_target_with_actual(db, target: dict) -> dict:
    """Enrich target with actual sales data"""
    
    actual = await get_sales_actual(
        db, 
        target["target_type"], 
        target["target_ref_id"],
        target["period_start"],
        target["period_end"]
    )
    
    target["actual_value"] = actual["actual_value"]
    target["actual_qty"] = actual["actual_qty"]
    target["transaction_count"] = actual["transaction_count"]
    
    # Calculate achievement
    if target["target_value"] > 0:
        target["achievement_percent"] = round((actual["actual_value"] / target["target_value"]) * 100, 2)
    else:
        target["achievement_percent"] = 0
    
    if target.get("target_qty") and target["target_qty"] > 0:
        target["qty_achievement_percent"] = round((actual["actual_qty"] / target["target_qty"]) * 100, 2)
    else:
        target["qty_achievement_percent"] = None
    
    # Calculate status
    target["status"] = await calculate_target_status(
        target["target_value"],
        actual["actual_value"],
        target["period_end"]
    )
    
    # Calculate gap
    target["gap"] = target["target_value"] - actual["actual_value"]
    
    return target

# ==================== API ENDPOINTS ====================

@router.post("")
async def create_sales_target(
    data: SalesTargetCreate,
    user: dict = Depends(require_permission("sales_target", "create"))
):
    """Create a new sales target"""
    db = get_database()
    
    # Validate period type
    if data.period_type not in PERIOD_TYPES:
        raise HTTPException(status_code=400, detail=f"Period type tidak valid: {data.period_type}")
    
    # Validate target type
    if data.target_type not in ["branch", "salesman", "category"]:
        raise HTTPException(status_code=400, detail=f"Target type tidak valid: {data.target_type}")
    
    # Check for duplicate
    existing = await db.sales_targets.find_one({
        "target_type": data.target_type,
        "target_ref_id": data.target_ref_id,
        "period_start": data.period_start,
        "period_end": data.period_end
    })
    
    if existing:
        raise HTTPException(status_code=400, detail="Target untuk periode ini sudah ada")
    
    # Get reference name if not provided
    ref_name = data.target_ref_name
    if not ref_name:
        if data.target_type == "branch":
            branch = await db.branches.find_one({"id": data.target_ref_id}, {"_id": 0, "name": 1})
            ref_name = branch.get("name", "") if branch else ""
        elif data.target_type == "salesman":
            user_doc = await db.users.find_one({"id": data.target_ref_id}, {"_id": 0, "name": 1})
            ref_name = user_doc.get("name", "") if user_doc else ""
    
    target = {
        "id": str(uuid.uuid4()),
        "target_type": data.target_type,
        "target_ref_id": data.target_ref_id,
        "target_ref_name": ref_name,
        "period_type": data.period_type,
        "period_start": data.period_start,
        "period_end": data.period_end,
        "target_value": data.target_value,
        "target_qty": data.target_qty,
        "notes": data.notes,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user.get("user_id"),
        "created_by_name": user.get("name")
    }
    
    target_id = target["id"]
    await db.sales_targets.insert_one(target)
    
    # Audit log
    await db.audit_logs.insert_one({
        "id": str(uuid.uuid4()),
        "action": "sales_target_create",
        "module": "sales_target",
        "target_id": target_id,
        "description": f"Target {data.target_type}: {ref_name} - Rp {data.target_value:,.0f} ({data.period_start} to {data.period_end})",
        "user_id": user.get("user_id"),
        "user_name": user.get("name"),
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    return {
        "success": True,
        "target_id": target_id,
        "message": f"Target created for {ref_name}"
    }

@router.get("/list")
async def list_sales_targets(
    target_type: Optional[str] = None,
    period_type: Optional[str] = None,
    period_start: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    user: dict = Depends(get_current_user)
):
    """List sales targets with actual values"""
    db = get_database()
    
    query = {}
    if target_type:
        query["target_type"] = target_type
    if period_type:
        query["period_type"] = period_type
    if period_start:
        query["period_start"] = {"$gte": period_start}
    
    targets = await db.sales_targets.find(query, {"_id": 0}).sort("period_start", -1).limit(limit).to_list(limit)
    
    # Enrich with actual data
    enriched = []
    for target in targets:
        enriched_target = await enrich_target_with_actual(db, target)
        if status and enriched_target["status"] != status:
            continue
        enriched.append(enriched_target)
    
    # Summary
    summary = {
        "total": len(enriched),
        "achieved": sum(1 for t in enriched if t["status"] in ["achieved", "exceeded"]),
        "on_track": sum(1 for t in enriched if t["status"] == "on_track"),
        "behind": sum(1 for t in enriched if t["status"] in ["behind", "at_risk"]),
        "failed": sum(1 for t in enriched if t["status"] == "failed"),
        "total_target": sum(t["target_value"] for t in enriched),
        "total_actual": sum(t["actual_value"] for t in enriched)
    }
    
    return {"items": enriched, "summary": summary}

# ==================== DASHBOARD & LEADERBOARD ====================
# IMPORTANT: These routes MUST be defined BEFORE the /{target_id} parameterized route
# to avoid "dashboard" and "leaderboard" being treated as target_id values

@router.get("/dashboard/summary")
async def get_target_dashboard(
    period_type: str = "monthly",
    user: dict = Depends(get_current_user)
):
    """Get sales target dashboard summary"""
    db = get_database()
    
    # Get current period targets
    now = datetime.now(timezone.utc)
    
    if period_type == "monthly":
        period_start = now.replace(day=1).strftime("%Y-%m-%d")
    elif period_type == "yearly":
        period_start = now.replace(month=1, day=1).strftime("%Y-%m-%d")
    else:
        period_start = now.strftime("%Y-%m-%d")
    
    targets = await db.sales_targets.find({
        "period_type": period_type,
        "period_start": {"$lte": now.strftime("%Y-%m-%d")},
        "period_end": {"$gte": now.strftime("%Y-%m-%d")}
    }, {"_id": 0}).to_list(100)
    
    # Enrich and summarize
    by_type = {"branch": [], "salesman": []}
    total_target = 0
    total_actual = 0
    
    for target in targets:
        enriched = await enrich_target_with_actual(db, target)
        total_target += enriched["target_value"]
        total_actual += enriched["actual_value"]
        
        if enriched["target_type"] in by_type:
            by_type[enriched["target_type"]].append(enriched)
    
    # Sort by achievement
    for key in by_type:
        by_type[key].sort(key=lambda x: x["achievement_percent"], reverse=True)
    
    overall_achievement = round((total_actual / total_target * 100), 2) if total_target > 0 else 0
    
    return {
        "period_type": period_type,
        "total_target": total_target,
        "total_actual": total_actual,
        "overall_achievement": overall_achievement,
        "overall_status": await calculate_target_status(total_target, total_actual, now.strftime("%Y-%m-%d")),
        "by_type": by_type,
        "top_performers": by_type.get("salesman", [])[:5],
        "branch_performance": by_type.get("branch", [])[:10]
    }

@router.get("/leaderboard")
async def get_sales_leaderboard(
    period_type: str = "monthly",
    limit: int = 10,
    user: dict = Depends(get_current_user)
):
    """Get salesman leaderboard"""
    db = get_database()
    
    now = datetime.now(timezone.utc)
    
    targets = await db.sales_targets.find({
        "target_type": "salesman",
        "period_type": period_type,
        "period_start": {"$lte": now.strftime("%Y-%m-%d")},
        "period_end": {"$gte": now.strftime("%Y-%m-%d")}
    }, {"_id": 0}).to_list(100)
    
    leaderboard = []
    for target in targets:
        enriched = await enrich_target_with_actual(db, target)
        leaderboard.append({
            "rank": 0,
            "salesman_id": enriched["target_ref_id"],
            "salesman_name": enriched["target_ref_name"],
            "target_value": enriched["target_value"],
            "actual_value": enriched["actual_value"],
            "achievement_percent": enriched["achievement_percent"],
            "gap": enriched["gap"],
            "status": enriched["status"],
            "transaction_count": enriched["transaction_count"]
        })
    
    # Sort by achievement
    leaderboard.sort(key=lambda x: x["achievement_percent"], reverse=True)
    
    # Add rank
    for i, item in enumerate(leaderboard[:limit]):
        item["rank"] = i + 1
    
    return {"items": leaderboard[:limit], "total": len(leaderboard)}

# ==================== PARAMETERIZED ROUTES ====================
# These MUST come AFTER specific routes like /list, /dashboard/summary, /leaderboard

@router.get("/{target_id}")
async def get_sales_target(
    target_id: str,
    user: dict = Depends(get_current_user)
):
    """Get sales target detail with actual"""
    db = get_database()
    
    target = await db.sales_targets.find_one({"id": target_id}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="Target tidak ditemukan")
    
    enriched = await enrich_target_with_actual(db, target)
    
    return enriched

@router.put("/{target_id}")
async def update_sales_target(
    target_id: str,
    data: SalesTargetUpdate,
    user: dict = Depends(require_permission("sales_target", "edit"))
):
    """Update sales target"""
    db = get_database()
    
    target = await db.sales_targets.find_one({"id": target_id})
    if not target:
        raise HTTPException(status_code=404, detail="Target tidak ditemukan")
    
    update_data = {k: v for k, v in data.dict().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    update_data["updated_by"] = user.get("user_id")
    
    await db.sales_targets.update_one({"id": target_id}, {"$set": update_data})
    
    # Audit log
    await db.audit_logs.insert_one({
        "id": str(uuid.uuid4()),
        "action": "sales_target_update",
        "module": "sales_target",
        "target_id": target_id,
        "description": f"Updated target: {update_data}",
        "user_id": user.get("user_id"),
        "user_name": user.get("name"),
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    return {"success": True, "message": "Target updated"}

@router.delete("/{target_id}")
async def delete_sales_target(
    target_id: str,
    user: dict = Depends(require_permission("sales_target", "delete"))
):
    """Delete sales target"""
    db = get_database()
    
    target = await db.sales_targets.find_one({"id": target_id})
    if not target:
        raise HTTPException(status_code=404, detail="Target tidak ditemukan")
    
    await db.sales_targets.delete_one({"id": target_id})
    
    # Audit log
    await db.audit_logs.insert_one({
        "id": str(uuid.uuid4()),
        "action": "sales_target_delete",
        "module": "sales_target",
        "target_id": target_id,
        "description": f"Deleted target for {target.get('target_ref_name')}",
        "user_id": user.get("user_id"),
        "user_name": user.get("name"),
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    return {"success": True, "message": "Target deleted"}
