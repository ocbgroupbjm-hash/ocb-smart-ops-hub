# OCB TITAN AI - KPI & AI Performance System
# Employee KPI tracking with AI ranking

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel
import uuid
import os

from database import get_db

router = APIRouter(prefix="/api/kpi", tags=["KPI & Performance"])

def gen_id():
    return str(uuid.uuid4())

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def get_wib_now():
    return datetime.now(timezone.utc) + timedelta(hours=7)

# Collections
def kpi_col():
    return get_db()['kpi_templates']

def kpi_targets_col():
    return get_db()['kpi_targets']

def kpi_submissions_col():
    return get_db()['kpi_submissions']

def employees_col():
    return get_db()['employees']

def branches_col():
    return get_db()['branches']

def ai_rankings_col():
    return get_db()['ai_rankings']

# ==================== MODELS ====================

class KPITemplate(BaseModel):
    name: str
    category: str  # sales, attendance, service, operational
    description: str = ""
    weight: float = 1.0
    target_type: str = "number"  # number, percentage, boolean
    target_value: float = 0
    measurement_period: str = "monthly"  # daily, weekly, monthly
    requires_evidence: bool = False
    evidence_type: str = ""  # photo, video, document
    jabatan_applicable: List[str] = []

class KPITarget(BaseModel):
    employee_id: str
    employee_name: str
    branch_id: str
    branch_name: str
    kpi_template_id: str
    kpi_name: str
    period_month: int
    period_year: int
    target_value: float
    weight: float = 1.0

class KPISubmission(BaseModel):
    target_id: str
    employee_id: str
    employee_name: str
    kpi_name: str
    achieved_value: float
    evidence_url: str = ""
    evidence_type: str = ""
    notes: str = ""

# ==================== KPI TEMPLATES ====================

@router.get("/templates")
async def get_kpi_templates():
    """Get all KPI templates"""
    templates = await kpi_col().find({}, {"_id": 0}).to_list(length=100)
    return {"templates": templates}

@router.post("/templates")
async def create_kpi_template(data: KPITemplate):
    """Create KPI template"""
    template = {
        "id": gen_id(),
        **data.dict(),
        "is_active": True,
        "created_at": now_iso()
    }
    await kpi_col().insert_one(template)
    return {"message": "Template KPI berhasil dibuat", "template": template}

@router.put("/templates/{template_id}")
async def update_kpi_template(template_id: str, data: KPITemplate):
    """Update KPI template"""
    update_data = {**data.dict(), "updated_at": now_iso()}
    await kpi_col().update_one({"id": template_id}, {"$set": update_data})
    return {"message": "Template KPI berhasil diupdate"}

@router.delete("/templates/{template_id}")
async def delete_kpi_template(template_id: str):
    """Delete KPI template"""
    await kpi_col().update_one({"id": template_id}, {"$set": {"is_active": False}})
    return {"message": "Template KPI berhasil dihapus"}

# ==================== KPI TARGETS ====================

@router.get("/targets")
async def get_kpi_targets(month: Optional[int] = None, year: Optional[int] = None, employee_id: Optional[str] = None):
    """Get KPI targets"""
    query = {}
    if month:
        query["period_month"] = month
    if year:
        query["period_year"] = year
    if employee_id:
        query["employee_id"] = employee_id
    
    targets = await kpi_targets_col().find(query, {"_id": 0}).to_list(length=1000)
    return {"targets": targets}

@router.post("/targets")
async def create_kpi_target(data: KPITarget):
    """Create KPI target for employee"""
    target = {
        "id": gen_id(),
        **data.dict(),
        "achieved_value": 0,
        "achievement_percentage": 0,
        "status": "pending",
        "created_at": now_iso()
    }
    await kpi_targets_col().insert_one(target)
    return {"message": "Target KPI berhasil dibuat", "target": target}

@router.post("/targets/bulk")
async def create_bulk_targets(template_id: str, month: int, year: int, branch_id: Optional[str] = None):
    """Create KPI targets for all employees based on template"""
    template = await kpi_col().find_one({"id": template_id}, {"_id": 0})
    if not template:
        raise HTTPException(status_code=404, detail="Template tidak ditemukan")
    
    query = {"status": "active"}
    if branch_id:
        query["branch_id"] = branch_id
    
    employees = await employees_col().find(query, {"_id": 0}).to_list(length=500)
    
    targets_created = 0
    for emp in employees:
        # Check if template applies to this jabatan
        if template.get("jabatan_applicable") and emp.get("jabatan_name") not in template["jabatan_applicable"]:
            continue
        
        # Check if target already exists
        existing = await kpi_targets_col().find_one({
            "employee_id": emp["id"],
            "kpi_template_id": template_id,
            "period_month": month,
            "period_year": year
        })
        
        if existing:
            continue
        
        target = {
            "id": gen_id(),
            "employee_id": emp["id"],
            "employee_name": emp["name"],
            "branch_id": emp.get("branch_id", ""),
            "branch_name": emp.get("branch_name", ""),
            "kpi_template_id": template_id,
            "kpi_name": template["name"],
            "kpi_category": template["category"],
            "period_month": month,
            "period_year": year,
            "target_value": template["target_value"],
            "weight": template["weight"],
            "requires_evidence": template.get("requires_evidence", False),
            "achieved_value": 0,
            "achievement_percentage": 0,
            "status": "pending",
            "created_at": now_iso()
        }
        await kpi_targets_col().insert_one(target)
        targets_created += 1
    
    return {"message": f"{targets_created} target KPI berhasil dibuat"}

# ==================== KPI SUBMISSIONS ====================

@router.post("/submit")
async def submit_kpi(data: KPISubmission):
    """Submit KPI achievement"""
    target = await kpi_targets_col().find_one({"id": data.target_id}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="Target KPI tidak ditemukan")
    
    # Calculate achievement percentage
    achievement_pct = 0
    if target["target_value"] > 0:
        achievement_pct = (data.achieved_value / target["target_value"]) * 100
    
    # Determine status
    status = "pending_review"
    if achievement_pct >= 100:
        status = "achieved"
    elif achievement_pct >= 80:
        status = "on_track"
    elif achievement_pct >= 50:
        status = "below_target"
    else:
        status = "critical"
    
    submission = {
        "id": gen_id(),
        **data.dict(),
        "achievement_percentage": achievement_pct,
        "status": status,
        "reviewed": False,
        "submitted_at": now_iso()
    }
    
    await kpi_submissions_col().insert_one(submission)
    
    # Update target
    await kpi_targets_col().update_one(
        {"id": data.target_id},
        {"$set": {
            "achieved_value": data.achieved_value,
            "achievement_percentage": achievement_pct,
            "status": status,
            "last_submission_id": submission["id"],
            "updated_at": now_iso()
        }}
    )
    
    return {"message": "KPI berhasil disubmit", "submission": submission}

@router.get("/submissions")
async def get_submissions(employee_id: Optional[str] = None, status: Optional[str] = None):
    """Get KPI submissions"""
    query = {}
    if employee_id:
        query["employee_id"] = employee_id
    if status:
        query["status"] = status
    
    submissions = await kpi_submissions_col().find(query, {"_id": 0}).sort("submitted_at", -1).to_list(length=500)
    return {"submissions": submissions}

@router.put("/submissions/{submission_id}/review")
async def review_submission(submission_id: str, approved: bool, reviewer_name: str, notes: str = ""):
    """Review KPI submission"""
    await kpi_submissions_col().update_one(
        {"id": submission_id},
        {"$set": {
            "reviewed": True,
            "approved": approved,
            "reviewer_name": reviewer_name,
            "review_notes": notes,
            "reviewed_at": now_iso()
        }}
    )
    return {"message": "Review berhasil disimpan"}

# ==================== AI PERFORMANCE RANKING ====================

@router.get("/ai-ranking/employees")
async def get_ai_employee_ranking(month: Optional[int] = None, year: Optional[int] = None):
    """Get AI-powered employee performance ranking"""
    if not month:
        month = get_wib_now().month
    if not year:
        year = get_wib_now().year
    
    # Get all targets for the period
    targets = await kpi_targets_col().find({
        "period_month": month,
        "period_year": year
    }, {"_id": 0}).to_list(length=5000)
    
    # Group by employee
    employee_scores = {}
    for t in targets:
        eid = t.get("employee_id")
        if eid not in employee_scores:
            employee_scores[eid] = {
                "employee_id": eid,
                "employee_name": t.get("employee_name"),
                "branch_id": t.get("branch_id"),
                "branch_name": t.get("branch_name"),
                "total_targets": 0,
                "total_achieved": 0,
                "total_weight": 0,
                "weighted_score": 0,
                "kpis": []
            }
        
        weight = t.get("weight", 1.0)
        achievement = t.get("achievement_percentage", 0)
        
        employee_scores[eid]["total_targets"] += 1
        employee_scores[eid]["total_weight"] += weight
        employee_scores[eid]["weighted_score"] += achievement * weight
        employee_scores[eid]["kpis"].append({
            "name": t.get("kpi_name"),
            "target": t.get("target_value"),
            "achieved": t.get("achieved_value"),
            "percentage": achievement
        })
        
        if achievement >= 100:
            employee_scores[eid]["total_achieved"] += 1
    
    # Calculate final scores
    rankings = []
    for eid, data in employee_scores.items():
        if data["total_weight"] > 0:
            final_score = data["weighted_score"] / data["total_weight"]
        else:
            final_score = 0
        
        # AI Ranking Category
        if final_score >= 120:
            rank_category = "Elite Performer"
            rank_color = "gold"
        elif final_score >= 100:
            rank_category = "Top Performer"
            rank_color = "green"
        elif final_score >= 80:
            rank_category = "Good Performer"
            rank_color = "blue"
        elif final_score >= 60:
            rank_category = "Average Performer"
            rank_color = "yellow"
        elif final_score >= 40:
            rank_category = "Under Performance"
            rank_color = "orange"
        else:
            rank_category = "Needs Improvement"
            rank_color = "red"
        
        rankings.append({
            **data,
            "final_score": round(final_score, 2),
            "rank_category": rank_category,
            "rank_color": rank_color
        })
    
    # Sort by score
    rankings.sort(key=lambda x: x["final_score"], reverse=True)
    
    # Add rank numbers
    for i, r in enumerate(rankings):
        r["rank"] = i + 1
    
    # Save to AI rankings collection
    ranking_record = {
        "id": gen_id(),
        "type": "employee_ranking",
        "period_month": month,
        "period_year": year,
        "total_employees": len(rankings),
        "rankings": rankings[:50],  # Top 50
        "summary": {
            "elite": len([r for r in rankings if r["rank_category"] == "Elite Performer"]),
            "top": len([r for r in rankings if r["rank_category"] == "Top Performer"]),
            "good": len([r for r in rankings if r["rank_category"] == "Good Performer"]),
            "average": len([r for r in rankings if r["rank_category"] == "Average Performer"]),
            "under": len([r for r in rankings if r["rank_category"] == "Under Performance"]),
            "needs_improvement": len([r for r in rankings if r["rank_category"] == "Needs Improvement"])
        },
        "generated_at": now_iso()
    }
    
    await ai_rankings_col().update_one(
        {"type": "employee_ranking", "period_month": month, "period_year": year},
        {"$set": ranking_record},
        upsert=True
    )
    
    return {
        "period": f"{month}/{year}",
        "total_employees": len(rankings),
        "summary": ranking_record["summary"],
        "rankings": rankings
    }

@router.get("/ai-ranking/branches")
async def get_ai_branch_ranking(month: Optional[int] = None, year: Optional[int] = None):
    """Get AI-powered branch performance ranking"""
    if not month:
        month = get_wib_now().month
    if not year:
        year = get_wib_now().year
    
    # Get setoran data
    import calendar
    _, last_day = calendar.monthrange(year, month)
    start_date = f"{year}-{month:02d}-01"
    end_date = f"{year}-{month:02d}-{last_day}"
    
    setoran_col = get_db()['setoran_harian']
    setoran = await setoran_col.find({
        "tanggal": {"$gte": start_date, "$lte": end_date}
    }, {"_id": 0}).to_list(length=5000)
    
    # Group by branch
    branch_data = {}
    for s in setoran:
        bid = s.get("branch_id")
        if bid not in branch_data:
            branch_data[bid] = {
                "branch_id": bid,
                "branch_code": s.get("branch_code"),
                "branch_name": s.get("branch_name"),
                "total_sales": 0,
                "total_transactions": 0,
                "total_setoran": 0,
                "total_selisih": 0,
                "days_reported": 0,
                "minus_count": 0
            }
        
        branch_data[bid]["total_sales"] += s.get("total_penjualan", 0)
        branch_data[bid]["total_transactions"] += s.get("total_transaksi", 0)
        branch_data[bid]["total_setoran"] += s.get("total_setoran", 0)
        branch_data[bid]["total_selisih"] += s.get("selisih", 0)
        branch_data[bid]["days_reported"] += 1
        if s.get("selisih", 0) < 0:
            branch_data[bid]["minus_count"] += 1
    
    # Get targets
    targets_col = get_db()['branch_targets']
    targets = await targets_col.find({
        "period_month": month, "period_year": year
    }, {"_id": 0}).to_list(length=100)
    targets_map = {t.get("branch_id"): t for t in targets}
    
    # Calculate scores
    rankings = []
    for bid, data in branch_data.items():
        target = targets_map.get(bid, {})
        target_revenue = target.get("target_revenue", data["total_sales"])  # Use actual if no target
        
        # Score calculation
        achievement_pct = (data["total_sales"] / target_revenue * 100) if target_revenue > 0 else 0
        avg_transaction = data["total_sales"] / data["total_transactions"] if data["total_transactions"] > 0 else 0
        reporting_rate = (data["days_reported"] / last_day) * 100
        minus_rate = (data["minus_count"] / data["days_reported"] * 100) if data["days_reported"] > 0 else 0
        
        # Final score (weighted)
        final_score = (
            achievement_pct * 0.4 +
            reporting_rate * 0.3 +
            (100 - minus_rate) * 0.3
        )
        
        # AI Ranking Category
        if final_score >= 95:
            rank_category = "Elite Branch"
            rank_color = "gold"
        elif final_score >= 85:
            rank_category = "Top Branch"
            rank_color = "green"
        elif final_score >= 70:
            rank_category = "Good Branch"
            rank_color = "blue"
        elif final_score >= 50:
            rank_category = "Average Branch"
            rank_color = "yellow"
        else:
            rank_category = "Needs Attention"
            rank_color = "red"
        
        rankings.append({
            **data,
            "target_revenue": target_revenue,
            "achievement_percentage": round(achievement_pct, 2),
            "avg_transaction": round(avg_transaction, 0),
            "reporting_rate": round(reporting_rate, 2),
            "minus_rate": round(minus_rate, 2),
            "final_score": round(final_score, 2),
            "rank_category": rank_category,
            "rank_color": rank_color
        })
    
    # Sort
    rankings.sort(key=lambda x: x["final_score"], reverse=True)
    
    for i, r in enumerate(rankings):
        r["rank"] = i + 1
    
    return {
        "period": f"{month}/{year}",
        "total_branches": len(rankings),
        "rankings": rankings
    }

# ==================== DEFAULT KPI TEMPLATES ====================

@router.post("/seed-templates")
async def seed_default_templates():
    """Create default KPI templates"""
    templates = [
        {
            "id": gen_id(),
            "name": "Target Penjualan Bulanan",
            "category": "sales",
            "description": "Target penjualan per bulan per karyawan",
            "weight": 2.0,
            "target_type": "number",
            "target_value": 50000000,
            "measurement_period": "monthly",
            "requires_evidence": False,
            "jabatan_applicable": ["sales", "kasir", "spv"],
            "is_active": True,
            "created_at": now_iso()
        },
        {
            "id": gen_id(),
            "name": "Kehadiran Tepat Waktu",
            "category": "attendance",
            "description": "Persentase kehadiran tepat waktu",
            "weight": 1.5,
            "target_type": "percentage",
            "target_value": 95,
            "measurement_period": "monthly",
            "requires_evidence": False,
            "jabatan_applicable": [],
            "is_active": True,
            "created_at": now_iso()
        },
        {
            "id": gen_id(),
            "name": "Akurasi Setoran",
            "category": "operational",
            "description": "Setoran tanpa minus/selisih",
            "weight": 2.0,
            "target_type": "percentage",
            "target_value": 100,
            "measurement_period": "monthly",
            "requires_evidence": False,
            "jabatan_applicable": ["kasir", "penjaga"],
            "is_active": True,
            "created_at": now_iso()
        },
        {
            "id": gen_id(),
            "name": "Customer Service Rating",
            "category": "service",
            "description": "Rating dari customer",
            "weight": 1.0,
            "target_type": "number",
            "target_value": 4.5,
            "measurement_period": "monthly",
            "requires_evidence": True,
            "evidence_type": "photo",
            "jabatan_applicable": ["sales", "kasir"],
            "is_active": True,
            "created_at": now_iso()
        },
        {
            "id": gen_id(),
            "name": "Jumlah Customer Baru",
            "category": "sales",
            "description": "Jumlah customer baru yang didapat",
            "weight": 1.5,
            "target_type": "number",
            "target_value": 10,
            "measurement_period": "monthly",
            "requires_evidence": True,
            "evidence_type": "document",
            "jabatan_applicable": ["sales", "marketing"],
            "is_active": True,
            "created_at": now_iso()
        }
    ]
    
    for t in templates:
        await kpi_col().update_one({"name": t["name"]}, {"$set": t}, upsert=True)
    
    return {"message": f"{len(templates)} template KPI berhasil dibuat"}
