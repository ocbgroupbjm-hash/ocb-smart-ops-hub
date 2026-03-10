# OCB TITAN AI - AI Store Open/Close Prediction
# Prediksi toko buka/tutup, analisa kelayakan cabang

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import uuid

router = APIRouter(prefix="/api/ai-store", tags=["AI Store Prediction"])

def get_db():
    from database import get_db as db_get
    return db_get()

def gen_id():
    return str(uuid.uuid4())

def now_iso():
    return datetime.now(timezone.utc).isoformat()

# Collections
def sales_col():
    return get_db()['transactions']

def branches_col():
    return get_db()['branches']

def employees_col():
    return get_db()['employees']

def payroll_col():
    return get_db()['payroll_slips']

def expenses_col():
    return get_db()['expenses']

def inventory_col():
    return get_db()['inventory']

def audit_col():
    return get_db()['audit_logs']

def predictions_col():
    return get_db()['store_predictions']


# ==================== STORE OPEN/CLOSE PREDICTION ====================

@router.get("/branch-viability")
async def analyze_branch_viability(branch_id: Optional[str] = None, period: str = "3months"):
    """
    Analisis kelayakan cabang - apakah layak dipertahankan, perlu efisiensi, atau tutup
    """
    today = datetime.now(timezone.utc).date()
    
    if period == "3months":
        start_date = today - timedelta(days=90)
    elif period == "6months":
        start_date = today - timedelta(days=180)
    else:
        start_date = today - timedelta(days=90)
    
    # Get branches
    query = {"is_active": True}
    if branch_id:
        query["id"] = branch_id
    
    branches = await branches_col().find(query, {"_id": 0}).to_list(length=100)
    employees = await employees_col().find({"status": "active"}, {"_id": 0}).to_list(length=500)
    
    # Get sales data
    sales = await sales_col().find({
        "created_at": {"$gte": f"{start_date}T00:00:00"}
    }, {"_id": 0}).to_list(length=50000)
    
    analysis_results = []
    
    for branch in branches:
        bid = branch.get("id")
        bname = branch.get("name", "Unknown")
        
        # === SALES ANALYSIS ===
        branch_sales = [s for s in sales if s.get("branch_id") == bid]
        total_revenue = sum(s.get("total", 0) for s in branch_sales)
        total_transactions = len(branch_sales)
        
        # Calculate monthly average
        days_in_period = (today - start_date).days
        monthly_revenue = (total_revenue / days_in_period) * 30 if days_in_period > 0 else 0
        monthly_transactions = (total_transactions / days_in_period) * 30 if days_in_period > 0 else 0
        
        # === COST ANALYSIS ===
        branch_employees = [e for e in employees if e.get("branch_id") == bid]
        employee_count = len(branch_employees)
        
        # Payroll cost (estimate)
        monthly_payroll = sum(
            e.get("gaji_pokok", 0) + e.get("tunjangan_total", 0) 
            for e in branch_employees
        )
        
        # Operating cost estimate (10% of revenue or minimum 2 juta)
        monthly_opex = max(monthly_revenue * 0.1, 2000000)
        
        # COGS (70% of revenue)
        monthly_cogs = monthly_revenue * 0.7
        
        # === PROFIT CALCULATION ===
        total_cost = monthly_payroll + monthly_opex + monthly_cogs
        monthly_profit = monthly_revenue - total_cost
        profit_margin = (monthly_profit / monthly_revenue * 100) if monthly_revenue > 0 else -100
        
        # === TREND ANALYSIS ===
        # Compare first half vs second half of period
        mid_date = start_date + timedelta(days=days_in_period // 2)
        first_half_sales = [s for s in branch_sales if s.get("created_at", "")[:10] < str(mid_date)]
        second_half_sales = [s for s in branch_sales if s.get("created_at", "")[:10] >= str(mid_date)]
        
        first_half_revenue = sum(s.get("total", 0) for s in first_half_sales)
        second_half_revenue = sum(s.get("total", 0) for s in second_half_sales)
        
        trend = "stable"
        trend_percentage = 0
        if first_half_revenue > 0:
            trend_percentage = ((second_half_revenue - first_half_revenue) / first_half_revenue) * 100
            if trend_percentage > 10:
                trend = "improving"
            elif trend_percentage < -10:
                trend = "declining"
        
        # === PRODUCTIVITY METRICS ===
        revenue_per_employee = monthly_revenue / employee_count if employee_count > 0 else 0
        transactions_per_employee = monthly_transactions / employee_count if employee_count > 0 else 0
        payroll_ratio = (monthly_payroll / monthly_revenue * 100) if monthly_revenue > 0 else 100
        
        # === STATUS DETERMINATION ===
        issues = []
        recommendations = []
        
        # Scoring system
        score = 100
        
        # Revenue scoring
        if monthly_revenue < 5000000:
            score -= 30
            issues.append("Penjualan sangat rendah (< 5 juta/bulan)")
        elif monthly_revenue < 10000000:
            score -= 15
            issues.append("Penjualan rendah (< 10 juta/bulan)")
        
        # Profit scoring
        if monthly_profit < -5000000:
            score -= 35
            issues.append(f"Rugi berat: Rp {abs(monthly_profit):,.0f}/bulan")
        elif monthly_profit < 0:
            score -= 20
            issues.append(f"Rugi: Rp {abs(monthly_profit):,.0f}/bulan")
        
        # Trend scoring
        if trend == "declining" and trend_percentage < -20:
            score -= 15
            issues.append(f"Trend penjualan turun {abs(trend_percentage):.1f}%")
        
        # Payroll ratio scoring
        if payroll_ratio > 40:
            score -= 20
            issues.append(f"Payroll ratio terlalu tinggi ({payroll_ratio:.1f}%)")
        elif payroll_ratio > 30:
            score -= 10
            issues.append(f"Payroll ratio tinggi ({payroll_ratio:.1f}%)")
        
        # Employee productivity
        if revenue_per_employee < 3000000 and employee_count > 0:
            score -= 10
            issues.append(f"Produktivitas karyawan rendah (Rp {revenue_per_employee:,.0f}/org)")
        
        # Determine status
        if score >= 80:
            status = "SEHAT"
            status_color = "green"
        elif score >= 60:
            status = "WARNING"
            status_color = "yellow"
        elif score >= 40:
            status = "RUGI"
            status_color = "orange"
        else:
            status = "KRITIS"
            status_color = "red"
        
        # Generate recommendations
        if status == "KRITIS":
            recommendations.append("PERTIMBANGKAN PENUTUPAN CABANG")
            recommendations.append("Lakukan audit menyeluruh sebelum keputusan final")
            if payroll_ratio > 35:
                recommendations.append("Efisiensi karyawan drastis jika tidak tutup")
        elif status == "RUGI":
            recommendations.append("PERLU EFISIENSI SEGERA")
            if payroll_ratio > 30:
                recommendations.append(f"Kurangi {max(1, employee_count - int(monthly_revenue / 5000000))} karyawan")
            if monthly_revenue < 10000000:
                recommendations.append("Tingkatkan penjualan dengan promo agresif")
            if trend == "declining":
                recommendations.append("Evaluasi lokasi dan strategi marketing")
        elif status == "WARNING":
            if payroll_ratio > 25:
                recommendations.append("Pertimbangkan efisiensi karyawan")
            if trend == "declining":
                recommendations.append("Perbaiki strategi penjualan")
            recommendations.append("Monitor ketat performa bulanan")
        else:
            recommendations.append("Pertahankan performa")
            if trend == "improving":
                recommendations.append("Pertimbangkan ekspansi atau bonus karyawan")
        
        # Final recommendation
        if score < 30:
            final_recommendation = "TUTUP"
        elif score < 50:
            final_recommendation = "EFISIENSI_BERAT"
        elif score < 65:
            final_recommendation = "EFISIENSI"
        elif score < 80:
            final_recommendation = "MONITOR"
        else:
            final_recommendation = "PERTAHANKAN"
        
        analysis_results.append({
            "branch_id": bid,
            "branch_name": bname,
            "period_analyzed": period,
            "metrics": {
                "monthly_revenue": round(monthly_revenue),
                "monthly_transactions": round(monthly_transactions),
                "monthly_profit": round(monthly_profit),
                "profit_margin": round(profit_margin, 2),
                "total_cost": round(total_cost),
                "monthly_payroll": round(monthly_payroll),
                "monthly_opex": round(monthly_opex),
                "employee_count": employee_count,
                "revenue_per_employee": round(revenue_per_employee),
                "payroll_ratio": round(payroll_ratio, 2),
                "trend": trend,
                "trend_percentage": round(trend_percentage, 2)
            },
            "status": status,
            "status_color": status_color,
            "score": max(0, score),
            "issues": issues,
            "recommendations": recommendations,
            "final_recommendation": final_recommendation
        })
    
    # Sort by score (worst first for attention)
    analysis_results.sort(key=lambda x: x["score"])
    
    # Summary
    status_counts = {
        "sehat": len([a for a in analysis_results if a["status"] == "SEHAT"]),
        "warning": len([a for a in analysis_results if a["status"] == "WARNING"]),
        "rugi": len([a for a in analysis_results if a["status"] == "RUGI"]),
        "kritis": len([a for a in analysis_results if a["status"] == "KRITIS"])
    }
    
    return {
        "analysis_period": period,
        "total_branches_analyzed": len(analysis_results),
        "status_summary": status_counts,
        "branches": analysis_results,
        "generated_at": now_iso()
    }


@router.get("/new-branch-recommendation")
async def recommend_new_branch_location():
    """
    Rekomendasi lokasi cabang baru berdasarkan data performa cabang existing
    """
    today = datetime.now(timezone.utc).date()
    start_date = today - timedelta(days=90)
    
    branches = await branches_col().find({"is_active": True}, {"_id": 0}).to_list(length=100)
    employees = await employees_col().find({"status": "active"}, {"_id": 0}).to_list(length=500)
    
    sales = await sales_col().find({
        "created_at": {"$gte": f"{start_date}T00:00:00"}
    }, {"_id": 0}).to_list(length=50000)
    
    # Analyze existing branches performance by region
    region_analysis = {}
    
    for branch in branches:
        bid = branch.get("id")
        bname = branch.get("name", "Unknown")
        region = branch.get("region") or branch.get("city") or bname.split()[0] if bname else "Unknown"
        
        branch_sales = [s for s in sales if s.get("branch_id") == bid]
        total_revenue = sum(s.get("total", 0) for s in branch_sales)
        
        if region not in region_analysis:
            region_analysis[region] = {
                "branch_count": 0,
                "total_revenue": 0,
                "branches": []
            }
        
        region_analysis[region]["branch_count"] += 1
        region_analysis[region]["total_revenue"] += total_revenue
        region_analysis[region]["branches"].append({
            "name": bname,
            "revenue": total_revenue
        })
    
    # Generate recommendations
    recommendations = []
    
    for region, data in region_analysis.items():
        avg_revenue = data["total_revenue"] / data["branch_count"] if data["branch_count"] > 0 else 0
        monthly_avg = (avg_revenue / 90) * 30
        
        potential_score = 0
        notes = []
        
        # High performing regions with few branches = expansion opportunity
        if monthly_avg > 20000000 and data["branch_count"] < 3:
            potential_score = 90
            notes.append("Region performa tinggi dengan sedikit cabang")
        elif monthly_avg > 15000000 and data["branch_count"] < 2:
            potential_score = 80
            notes.append("Region performa bagus, potensi ekspansi")
        elif monthly_avg > 10000000 and data["branch_count"] == 1:
            potential_score = 70
            notes.append("Cabang tunggal performa baik, bisa tambah")
        elif monthly_avg > 8000000:
            potential_score = 50
            notes.append("Performa moderate, pertimbangkan dengan hati-hati")
        else:
            potential_score = 30
            notes.append("Region performa rendah, tidak disarankan ekspansi")
        
        # Estimate for new branch
        estimated_monthly_sales = monthly_avg * 0.7  # 70% of existing avg
        estimated_initial_employees = max(2, int(estimated_monthly_sales / 5000000))
        estimated_startup_cost = 50000000 + (estimated_initial_employees * 3500000 * 3)  # Setup + 3 bulan gaji
        estimated_bep_months = (estimated_startup_cost / (estimated_monthly_sales * 0.15)) if estimated_monthly_sales > 0 else 999
        
        recommendations.append({
            "region": region,
            "existing_branches": data["branch_count"],
            "avg_monthly_revenue": round(monthly_avg),
            "potential_score": potential_score,
            "recommendation_level": "SANGAT_DISARANKAN" if potential_score >= 80 else "DISARANKAN" if potential_score >= 60 else "PERTIMBANGKAN" if potential_score >= 40 else "TIDAK_DISARANKAN",
            "estimates": {
                "monthly_sales": round(estimated_monthly_sales),
                "initial_employees": estimated_initial_employees,
                "startup_cost": round(estimated_startup_cost),
                "bep_months": round(estimated_bep_months, 1),
                "initial_stock_value": round(estimated_monthly_sales * 0.5)
            },
            "notes": notes,
            "existing_branch_names": [b["name"] for b in data["branches"]]
        })
    
    # Sort by potential
    recommendations.sort(key=lambda x: x["potential_score"], reverse=True)
    
    return {
        "recommendations": recommendations,
        "top_recommendation": recommendations[0] if recommendations else None,
        "generated_at": now_iso()
    }


@router.post("/save-analysis/{branch_id}")
async def save_branch_analysis(branch_id: str):
    """Save branch analysis for historical tracking"""
    analysis = await analyze_branch_viability(branch_id=branch_id)
    
    if not analysis.get("branches"):
        raise HTTPException(status_code=404, detail="Branch not found")
    
    branch_data = analysis["branches"][0]
    
    record = {
        "id": gen_id(),
        "branch_id": branch_id,
        "branch_name": branch_data["branch_name"],
        "analysis_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "status": branch_data["status"],
        "score": branch_data["score"],
        "metrics": branch_data["metrics"],
        "recommendation": branch_data["final_recommendation"],
        "created_at": now_iso()
    }
    
    await predictions_col().insert_one(record)
    
    return {"message": "Analisis berhasil disimpan", "record_id": record["id"]}


@router.get("/history/{branch_id}")
async def get_branch_analysis_history(branch_id: str):
    """Get historical analysis for a branch"""
    history = await predictions_col().find(
        {"branch_id": branch_id}, {"_id": 0}
    ).sort("analysis_date", -1).to_list(length=50)
    
    return {"history": history}
