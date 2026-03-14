# OCB TITAN ERP - HR KPI ENGINE
# Performance Management System
# Formula: achievement = actual / target, score = achievement * weight

from fastapi import APIRouter, HTTPException, Depends, Request, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from database import db
from utils.auth import get_current_user
from routes.rbac_system import log_activity
import uuid

router = APIRouter(prefix="/api/hr/kpi", tags=["HR KPI Engine"])

# Collections
kpi_targets = db["kpi_targets"]
kpi_results = db["kpi_results"]
kpi_reviews = db["kpi_reviews"]
employees = db["employees"]

# ==================== PYDANTIC MODELS ====================

class KPITargetCreate(BaseModel):
    """KPI Target definition"""
    name: str
    code: str
    description: Optional[str] = None
    category: str = "performance"  # performance, sales, quality, attendance
    metric_type: str = "number"  # number, percentage, currency
    target_value: float
    weight: float = 1.0  # Weight for score calculation (0-1 or percentage)
    period_type: str = "monthly"  # monthly, quarterly, yearly
    department_id: Optional[str] = None  # Null = company-wide
    is_active: bool = True

class KPIAssignment(BaseModel):
    """Assign KPI to employee"""
    employee_id: str
    kpi_target_id: str
    period: str  # Format: "2026-03" for monthly, "2026-Q1" for quarterly
    target_value: Optional[float] = None  # Override default target
    notes: Optional[str] = None

class KPIResultUpdate(BaseModel):
    """Update KPI actual value"""
    actual_value: float
    notes: Optional[str] = None
    evidence_url: Optional[str] = None

class KPIReviewCreate(BaseModel):
    """Manager review for KPI"""
    kpi_result_id: str
    score_adjustment: float = 0  # Manual adjustment (-1 to +1)
    review_notes: str
    rating: str = "meets"  # exceeds, meets, below, unsatisfactory


# ==================== KPI TARGETS ====================

@router.post("/targets")
async def create_kpi_target(
    data: KPITargetCreate,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """Create KPI target definition"""
    user_id = user.get("user_id", user.get("id", ""))
    user_name = user.get("name", "")
    
    # Check duplicate code
    existing = await kpi_targets.find_one({"code": data.code.upper()})
    if existing:
        raise HTTPException(status_code=400, detail=f"KPI code {data.code} sudah ada")
    
    target = {
        "id": str(uuid.uuid4()),
        "code": data.code.upper(),
        "name": data.name,
        "description": data.description,
        "category": data.category,
        "metric_type": data.metric_type,
        "target_value": data.target_value,
        "weight": data.weight,
        "period_type": data.period_type,
        "department_id": data.department_id,
        "is_active": data.is_active,
        "created_by": user_id,
        "created_by_name": user_name,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await kpi_targets.insert_one(target)
    
    await log_activity(
        db, user_id, user_name,
        "create", "kpi_target",
        f"KPI Target dibuat: {data.name} ({data.code})",
        request.client.host if request.client else "",
        user.get("branch_id", "")
    )
    
    return {
        "status": "success",
        "message": "KPI target berhasil dibuat",
        "kpi_id": target["id"],
        "code": target["code"]
    }


@router.get("/targets")
async def get_kpi_targets(
    category: Optional[str] = None,
    department_id: Optional[str] = None,
    is_active: Optional[bool] = True,
    user: dict = Depends(get_current_user)
):
    """Get all KPI targets"""
    query = {}
    if category:
        query["category"] = category
    if department_id:
        query["$or"] = [{"department_id": department_id}, {"department_id": None}]
    if is_active is not None:
        query["is_active"] = is_active
    
    targets = await kpi_targets.find(query, {"_id": 0}).to_list(100)
    return {"targets": targets, "count": len(targets)}


@router.get("/targets/{target_id}")
async def get_kpi_target(
    target_id: str,
    user: dict = Depends(get_current_user)
):
    """Get single KPI target"""
    target = await kpi_targets.find_one(
        {"$or": [{"id": target_id}, {"code": target_id.upper()}]},
        {"_id": 0}
    )
    if not target:
        raise HTTPException(status_code=404, detail="KPI target tidak ditemukan")
    return target


# ==================== KPI ASSIGNMENTS & RESULTS ====================

@router.post("/assign")
async def assign_kpi_to_employee(
    data: KPIAssignment,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """
    Assign KPI target to an employee for a period
    
    This creates a kpi_result record to track progress
    """
    user_id = user.get("user_id", user.get("id", ""))
    user_name = user.get("name", "")
    
    # Verify employee
    employee = await employees.find_one(
        {"$or": [{"id": data.employee_id}, {"employee_id": data.employee_id.upper()}]},
        {"_id": 0}
    )
    if not employee:
        raise HTTPException(status_code=404, detail="Karyawan tidak ditemukan")
    
    # Verify KPI target
    target = await kpi_targets.find_one({"id": data.kpi_target_id}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="KPI target tidak ditemukan")
    
    # Check if already assigned
    existing = await kpi_results.find_one({
        "employee_id": employee["id"],
        "kpi_target_id": data.kpi_target_id,
        "period": data.period
    })
    if existing:
        raise HTTPException(status_code=400, detail="KPI sudah di-assign untuk periode ini")
    
    # Create KPI result record
    target_value = data.target_value if data.target_value is not None else target["target_value"]
    
    result = {
        "id": str(uuid.uuid4()),
        "employee_id": employee["id"],
        "employee_nik": employee.get("employee_id"),
        "employee_name": employee.get("full_name", employee.get("name")),
        "department_id": employee.get("department_id"),
        "department_name": employee.get("department_name"),
        
        "kpi_target_id": data.kpi_target_id,
        "kpi_code": target["code"],
        "kpi_name": target["name"],
        "kpi_category": target["category"],
        "metric_type": target["metric_type"],
        
        "period": data.period,
        "target_value": target_value,
        "actual_value": 0,
        "weight": target["weight"],
        
        # Calculated fields (will be updated)
        "achievement": 0,  # actual / target
        "weighted_score": 0,  # achievement * weight
        "rating": None,
        
        "status": "in_progress",  # in_progress, completed, reviewed
        "notes": data.notes,
        
        "created_by": user_id,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await kpi_results.insert_one(result)
    
    await log_activity(
        db, user_id, user_name,
        "assign", "kpi",
        f"KPI {target['name']} di-assign ke {employee.get('full_name', employee.get('name'))} periode {data.period}",
        request.client.host if request.client else "",
        user.get("branch_id", "")
    )
    
    return {
        "status": "success",
        "message": "KPI berhasil di-assign",
        "result_id": result["id"],
        "employee_name": result["employee_name"],
        "kpi_name": result["kpi_name"],
        "period": data.period,
        "target_value": target_value
    }


@router.put("/results/{result_id}")
async def update_kpi_result(
    result_id: str,
    data: KPIResultUpdate,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """
    Update KPI actual value and calculate achievement
    
    Formula:
    - achievement = actual_value / target_value
    - weighted_score = achievement * weight
    """
    user_id = user.get("user_id", user.get("id", ""))
    user_name = user.get("name", "")
    
    result = await kpi_results.find_one({"id": result_id})
    if not result:
        raise HTTPException(status_code=404, detail="KPI result tidak ditemukan")
    
    target_value = result.get("target_value", 1)
    if target_value == 0:
        target_value = 1  # Prevent division by zero
    
    # Calculate achievement and score
    achievement = data.actual_value / target_value
    weighted_score = achievement * result.get("weight", 1)
    
    # Determine rating based on achievement
    if achievement >= 1.2:
        rating = "exceeds"
    elif achievement >= 0.9:
        rating = "meets"
    elif achievement >= 0.7:
        rating = "below"
    else:
        rating = "unsatisfactory"
    
    update_data = {
        "actual_value": data.actual_value,
        "achievement": round(achievement, 4),
        "weighted_score": round(weighted_score, 4),
        "rating": rating,
        "notes": data.notes or result.get("notes"),
        "evidence_url": data.evidence_url,
        "updated_by": user_id,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await kpi_results.update_one({"id": result_id}, {"$set": update_data})
    
    await log_activity(
        db, user_id, user_name,
        "update", "kpi_result",
        f"KPI {result.get('kpi_name')} updated: {data.actual_value}/{target_value} = {achievement:.1%}",
        request.client.host if request.client else "",
        user.get("branch_id", "")
    )
    
    return {
        "status": "success",
        "message": "KPI result berhasil diupdate",
        "actual_value": data.actual_value,
        "target_value": target_value,
        "achievement": round(achievement * 100, 1),  # As percentage
        "weighted_score": round(weighted_score, 4),
        "rating": rating
    }


@router.get("/results")
async def get_kpi_results(
    employee_id: Optional[str] = None,
    department_id: Optional[str] = None,
    period: Optional[str] = None,
    status: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Get KPI results with filtering"""
    query = {}
    
    if employee_id:
        employee = await employees.find_one(
            {"$or": [{"id": employee_id}, {"employee_id": employee_id.upper()}]},
            {"_id": 0}
        )
        if employee:
            query["employee_id"] = employee["id"]
    
    if department_id:
        query["department_id"] = department_id
    if period:
        query["period"] = period
    if status:
        query["status"] = status
    
    results = await kpi_results.find(query, {"_id": 0}).sort("created_at", -1).to_list(200)
    
    # Calculate summary
    total_score = sum(r.get("weighted_score", 0) for r in results)
    avg_achievement = sum(r.get("achievement", 0) for r in results) / len(results) if results else 0
    
    return {
        "results": results,
        "count": len(results),
        "summary": {
            "total_weighted_score": round(total_score, 4),
            "average_achievement": round(avg_achievement * 100, 1)  # As percentage
        }
    }


@router.get("/results/{result_id}")
async def get_kpi_result(
    result_id: str,
    user: dict = Depends(get_current_user)
):
    """Get single KPI result"""
    result = await kpi_results.find_one({"id": result_id}, {"_id": 0})
    if not result:
        raise HTTPException(status_code=404, detail="KPI result tidak ditemukan")
    
    # Get reviews
    reviews = await kpi_reviews.find(
        {"kpi_result_id": result_id}, {"_id": 0}
    ).sort("created_at", -1).to_list(10)
    
    result["reviews"] = reviews
    return result


# ==================== KPI REVIEWS ====================

@router.post("/reviews")
async def create_kpi_review(
    data: KPIReviewCreate,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """
    Manager review for KPI result
    Can adjust score with justification
    """
    user_id = user.get("user_id", user.get("id", ""))
    user_name = user.get("name", "")
    
    result = await kpi_results.find_one({"id": data.kpi_result_id})
    if not result:
        raise HTTPException(status_code=404, detail="KPI result tidak ditemukan")
    
    # Create review
    review = {
        "id": str(uuid.uuid4()),
        "kpi_result_id": data.kpi_result_id,
        "employee_id": result.get("employee_id"),
        "employee_name": result.get("employee_name"),
        "kpi_name": result.get("kpi_name"),
        "period": result.get("period"),
        
        "original_achievement": result.get("achievement", 0),
        "original_score": result.get("weighted_score", 0),
        "score_adjustment": data.score_adjustment,
        "final_score": result.get("weighted_score", 0) + data.score_adjustment,
        
        "rating": data.rating,
        "review_notes": data.review_notes,
        
        "reviewer_id": user_id,
        "reviewer_name": user_name,
        "reviewed_at": datetime.now(timezone.utc).isoformat()
    }
    
    await kpi_reviews.insert_one(review)
    
    # Update result status and score
    await kpi_results.update_one(
        {"id": data.kpi_result_id},
        {"$set": {
            "status": "reviewed",
            "rating": data.rating,
            "final_score": review["final_score"],
            "reviewed_by": user_id,
            "reviewed_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    await log_activity(
        db, user_id, user_name,
        "review", "kpi",
        f"KPI Review: {result.get('employee_name')} - {result.get('kpi_name')} = {data.rating}",
        request.client.host if request.client else "",
        user.get("branch_id", "")
    )
    
    return {
        "status": "success",
        "message": "Review berhasil disimpan",
        "review_id": review["id"],
        "final_score": review["final_score"],
        "rating": data.rating
    }


# ==================== KPI DASHBOARD ====================

@router.get("/dashboard/employee/{employee_id}")
async def get_employee_kpi_dashboard(
    employee_id: str,
    period: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Get KPI dashboard for single employee"""
    employee = await employees.find_one(
        {"$or": [{"id": employee_id}, {"employee_id": employee_id.upper()}]},
        {"_id": 0}
    )
    if not employee:
        raise HTTPException(status_code=404, detail="Karyawan tidak ditemukan")
    
    query = {"employee_id": employee["id"]}
    if period:
        query["period"] = period
    
    results = await kpi_results.find(query, {"_id": 0}).to_list(50)
    
    # Calculate totals
    total_weight = sum(r.get("weight", 0) for r in results)
    total_score = sum(r.get("weighted_score", 0) for r in results)
    
    # Normalize score if weights don't sum to 1
    if total_weight > 0:
        normalized_score = (total_score / total_weight) * 100
    else:
        normalized_score = 0
    
    # Count by rating
    rating_counts = {}
    for r in results:
        rating = r.get("rating", "pending")
        rating_counts[rating] = rating_counts.get(rating, 0) + 1
    
    return {
        "employee": {
            "id": employee["id"],
            "employee_id": employee.get("employee_id"),
            "name": employee.get("full_name", employee.get("name")),
            "department": employee.get("department_name")
        },
        "period": period or "All",
        "summary": {
            "total_kpis": len(results),
            "total_weight": round(total_weight, 2),
            "total_score": round(total_score, 4),
            "normalized_score": round(normalized_score, 1),  # Out of 100
            "rating_distribution": rating_counts
        },
        "kpis": results
    }


@router.get("/dashboard/department/{department_id}")
async def get_department_kpi_dashboard(
    department_id: str,
    period: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Get KPI dashboard for department"""
    query = {"department_id": department_id}
    if period:
        query["period"] = period
    
    results = await kpi_results.find(query, {"_id": 0}).to_list(500)
    
    # Group by employee
    employee_scores = {}
    for r in results:
        emp_id = r.get("employee_id")
        emp_name = r.get("employee_name")
        
        if emp_id not in employee_scores:
            employee_scores[emp_id] = {
                "employee_name": emp_name,
                "kpis": [],
                "total_score": 0,
                "total_weight": 0
            }
        
        employee_scores[emp_id]["kpis"].append(r)
        employee_scores[emp_id]["total_score"] += r.get("weighted_score", 0)
        employee_scores[emp_id]["total_weight"] += r.get("weight", 0)
    
    # Calculate normalized scores and rank
    rankings = []
    for emp_id, data in employee_scores.items():
        if data["total_weight"] > 0:
            normalized = (data["total_score"] / data["total_weight"]) * 100
        else:
            normalized = 0
        
        rankings.append({
            "employee_id": emp_id,
            "employee_name": data["employee_name"],
            "kpi_count": len(data["kpis"]),
            "total_score": round(data["total_score"], 4),
            "normalized_score": round(normalized, 1)
        })
    
    # Sort by normalized score
    rankings.sort(key=lambda x: x["normalized_score"], reverse=True)
    
    # Add rank
    for i, r in enumerate(rankings):
        r["rank"] = i + 1
    
    return {
        "department_id": department_id,
        "period": period or "All",
        "summary": {
            "total_employees": len(rankings),
            "total_kpis": len(results),
            "average_score": round(sum(r["normalized_score"] for r in rankings) / len(rankings), 1) if rankings else 0
        },
        "rankings": rankings
    }
