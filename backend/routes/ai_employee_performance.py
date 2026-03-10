# OCB TITAN AI - AI Employee Performance Analysis
# Analisis performa karyawan berbasis AI

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import uuid

router = APIRouter(prefix="/api/ai-employee", tags=["AI Employee Analysis"])

def get_db():
    from database import get_db as db_get
    return db_get()

def gen_id():
    return str(uuid.uuid4())

def now_iso():
    return datetime.now(timezone.utc).isoformat()

# Collections
def employees_col():
    return get_db()['employees']

def attendance_col():
    return get_db()['attendance']

def transactions_col():
    return get_db()['transactions']

def kpi_col():
    return get_db()['kpi_targets']

def selisih_col():
    return get_db()['selisih_kas']

def performance_col():
    return get_db()['employee_performance']


# ==================== AI PERFORMANCE ANALYSIS ====================

@router.get("/analyze/{employee_id}")
async def analyze_employee_performance(employee_id: str, period: str = "3months"):
    """
    AI Analysis untuk performa karyawan
    Membaca: absensi, keterlambatan, lembur, penjualan, KPI, minus kas
    Output: Score, kategori, kelebihan, kelemahan, rekomendasi
    """
    
    # Calculate date range
    today = datetime.now(timezone.utc).date()
    if period == "1month":
        start_date = today - timedelta(days=30)
    elif period == "3months":
        start_date = today - timedelta(days=90)
    elif period == "6months":
        start_date = today - timedelta(days=180)
    else:
        start_date = today - timedelta(days=90)
    
    # Get employee data
    emp = await employees_col().find_one({"id": employee_id}, {"_id": 0})
    if not emp:
        raise HTTPException(status_code=404, detail="Karyawan tidak ditemukan")
    
    # === ATTENDANCE ANALYSIS ===
    attendance = await attendance_col().find({
        "employee_id": employee_id,
        "tanggal": {"$gte": str(start_date)}
    }, {"_id": 0}).to_list(length=200)
    
    total_hadir = 0
    total_alpha = 0
    total_telat = 0
    total_telat_menit = 0
    total_lembur_menit = 0
    
    for att in attendance:
        status = att.get("status", "").lower()
        if status == "hadir":
            total_hadir += 1
            if att.get("telat_menit", 0) > 0:
                total_telat += 1
                total_telat_menit += att.get("telat_menit", 0)
            total_lembur_menit += att.get("lembur_menit", 0)
        elif status == "alpha":
            total_alpha += 1
    
    # === SALES ANALYSIS ===
    sales = await transactions_col().find({
        "$or": [
            {"cashier_id": employee_id},
            {"sales_id": employee_id},
            {"created_by": employee_id}
        ],
        "created_at": {"$gte": f"{start_date}T00:00:00"},
        "status": "completed"
    }, {"_id": 0}).to_list(length=5000)
    
    total_sales = sum(s.get("total", 0) for s in sales)
    total_transactions = len(sales)
    avg_transaction = total_sales / total_transactions if total_transactions > 0 else 0
    
    # === MINUS KAS ANALYSIS ===
    selisih = await selisih_col().find({
        "penjaga_id": employee_id,
        "tanggal": {"$gte": str(start_date)}
    }, {"_id": 0}).to_list(length=100)
    
    total_minus = sum(s.get("nominal", 0) for s in selisih if s.get("jenis") == "minus")
    minus_count = len([s for s in selisih if s.get("jenis") == "minus"])
    
    # === SCORING ===
    score = 100
    strengths = []
    weaknesses = []
    recommendations = []
    
    # Attendance scoring (max 30 points deduction)
    days_in_period = (today - start_date).days
    expected_work_days = int(days_in_period * 26 / 30)  # Approx work days
    
    if total_hadir > 0:
        attendance_rate = (total_hadir / max(expected_work_days, 1)) * 100
        if attendance_rate >= 95:
            strengths.append("Kehadiran sangat baik (>95%)")
        elif attendance_rate < 80:
            score -= 15
            weaknesses.append(f"Kehadiran rendah ({attendance_rate:.1f}%)")
            recommendations.append("Tingkatkan kehadiran minimal 90%")
    
    # Alpha scoring
    if total_alpha >= 5:
        score -= 20
        weaknesses.append(f"Banyak alpha ({total_alpha} hari)")
        recommendations.append("Kurangi absensi tanpa keterangan")
    elif total_alpha >= 2:
        score -= 10
        weaknesses.append(f"Ada alpha ({total_alpha} hari)")
    elif total_alpha == 0:
        strengths.append("Tidak pernah alpha")
    
    # Tardiness scoring
    if total_telat >= 10:
        score -= 15
        weaknesses.append(f"Sering terlambat ({total_telat}x)")
        recommendations.append("Perbaiki ketepatan waktu")
    elif total_telat >= 5:
        score -= 8
        weaknesses.append(f"Kadang terlambat ({total_telat}x)")
    elif total_telat <= 2:
        strengths.append("Disiplin waktu baik")
    
    # Overtime (positive indicator)
    if total_lembur_menit > 600:  # > 10 jam
        strengths.append(f"Dedikasi tinggi (lembur {total_lembur_menit // 60} jam)")
        score += 5  # Bonus for dedication
    
    # Sales scoring
    if total_sales > 100000000:
        strengths.append(f"Penjualan sangat tinggi (Rp {total_sales:,.0f})")
        score += 10
    elif total_sales > 50000000:
        strengths.append(f"Penjualan baik (Rp {total_sales:,.0f})")
        score += 5
    elif total_sales < 10000000 and total_transactions > 0:
        weaknesses.append(f"Penjualan rendah (Rp {total_sales:,.0f})")
        recommendations.append("Tingkatkan nilai penjualan")
    
    # Transaction volume
    if total_transactions > 500:
        strengths.append(f"Produktivitas tinggi ({total_transactions} transaksi)")
    elif total_transactions < 50 and expected_work_days > 30:
        weaknesses.append(f"Transaksi sedikit ({total_transactions})")
    
    # Minus kas scoring (serious issue)
    if total_minus > 1000000:
        score -= 25
        weaknesses.append(f"Minus kas besar (Rp {total_minus:,.0f})")
        recommendations.append("PERLU INVESTIGASI minus kas")
    elif total_minus > 500000:
        score -= 15
        weaknesses.append(f"Ada minus kas (Rp {total_minus:,.0f})")
        recommendations.append("Monitor dan verifikasi kas")
    elif minus_count == 0:
        strengths.append("Tidak ada minus kas")
    
    # Normalize score
    score = max(0, min(100, score))
    
    # Determine category
    if score >= 90:
        category = "ELITE"
        category_color = "gold"
        category_desc = "Performa luar biasa, kandidat promosi"
    elif score >= 80:
        category = "SANGAT_BAIK"
        category_color = "green"
        category_desc = "Performa sangat baik, pertahankan"
    elif score >= 65:
        category = "BAIK"
        category_color = "blue"
        category_desc = "Performa baik dengan beberapa area perbaikan"
    elif score >= 50:
        category = "NORMAL"
        category_color = "yellow"
        category_desc = "Performa standar, ada ruang perbaikan"
    elif score >= 35:
        category = "PERLU_PERHATIAN"
        category_color = "orange"
        category_desc = "Perlu perbaikan dan monitoring ketat"
    else:
        category = "BURUK"
        category_color = "red"
        category_desc = "Performa buruk, perlu evaluasi serius"
    
    # Generate recommendations if not enough
    if len(recommendations) == 0:
        if category == "ELITE":
            recommendations.append("Pertimbangkan untuk promosi atau bonus")
        elif category == "SANGAT_BAIK":
            recommendations.append("Beri apresiasi dan pertahankan performa")
        elif category in ["BAIK", "NORMAL"]:
            recommendations.append("Lanjutkan dengan peningkatan bertahap")
    
    if category in ["PERLU_PERHATIAN", "BURUK"]:
        recommendations.append("Jadwalkan meeting evaluasi")
        recommendations.append("Buat performance improvement plan")
    
    return {
        "employee": {
            "id": emp.get("id"),
            "nik": emp.get("nik"),
            "name": emp.get("name"),
            "jabatan": emp.get("jabatan_name"),
            "branch": emp.get("branch_name"),
            "join_date": emp.get("join_date")
        },
        "analysis_period": period,
        "metrics": {
            "attendance": {
                "total_hadir": total_hadir,
                "total_alpha": total_alpha,
                "total_telat": total_telat,
                "total_telat_menit": total_telat_menit,
                "total_lembur_menit": total_lembur_menit
            },
            "sales": {
                "total_sales": round(total_sales),
                "total_transactions": total_transactions,
                "avg_transaction": round(avg_transaction)
            },
            "minus_kas": {
                "total": round(total_minus),
                "count": minus_count
            }
        },
        "score": score,
        "category": category,
        "category_color": category_color,
        "category_description": category_desc,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "recommendations": recommendations,
        "generated_at": now_iso()
    }


# ==================== BULK ANALYSIS ====================

@router.get("/analyze-all")
async def analyze_all_employees(period: str = "3months", branch_id: Optional[str] = None):
    """Analyze all employees and rank them"""
    query = {"status": "active"}
    if branch_id:
        query["branch_id"] = branch_id
    
    employees = await employees_col().find(query, {"_id": 0}).to_list(length=500)
    
    results = []
    categories = {"ELITE": 0, "SANGAT_BAIK": 0, "BAIK": 0, "NORMAL": 0, "PERLU_PERHATIAN": 0, "BURUK": 0}
    
    for emp in employees:
        try:
            analysis = await analyze_employee_performance(emp["id"], period)
            results.append({
                "employee_id": emp["id"],
                "nik": emp.get("nik"),
                "name": emp.get("name"),
                "jabatan": emp.get("jabatan_name"),
                "branch": emp.get("branch_name"),
                "score": analysis["score"],
                "category": analysis["category"],
                "category_color": analysis["category_color"],
                "strengths_count": len(analysis["strengths"]),
                "weaknesses_count": len(analysis["weaknesses"]),
                "total_sales": analysis["metrics"]["sales"]["total_sales"],
                "attendance_issues": analysis["metrics"]["attendance"]["total_alpha"] + analysis["metrics"]["attendance"]["total_telat"]
            })
            categories[analysis["category"]] = categories.get(analysis["category"], 0) + 1
        except Exception as e:
            pass
    
    # Sort by score (highest first)
    results.sort(key=lambda x: x["score"], reverse=True)
    
    # Add ranking
    for idx, r in enumerate(results, 1):
        r["rank"] = idx
    
    return {
        "total_analyzed": len(results),
        "period": period,
        "category_summary": categories,
        "top_performers": results[:10],
        "need_attention": [r for r in results if r["category"] in ["PERLU_PERHATIAN", "BURUK"]][:10],
        "all_employees": results,
        "generated_at": now_iso()
    }


# ==================== SAVE PERFORMANCE RECORD ====================

@router.post("/save-analysis/{employee_id}")
async def save_performance_analysis(employee_id: str, period: str = "3months"):
    """Save performance analysis to database"""
    analysis = await analyze_employee_performance(employee_id, period)
    
    record = {
        "id": gen_id(),
        "employee_id": employee_id,
        "employee_name": analysis["employee"]["name"],
        "analysis_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "period": period,
        "score": analysis["score"],
        "category": analysis["category"],
        "metrics": analysis["metrics"],
        "strengths": analysis["strengths"],
        "weaknesses": analysis["weaknesses"],
        "recommendations": analysis["recommendations"],
        "created_at": now_iso()
    }
    
    await performance_col().insert_one(record)
    
    return {"message": "Analisis performa berhasil disimpan", "record_id": record["id"]}


@router.get("/history/{employee_id}")
async def get_performance_history(employee_id: str):
    """Get historical performance records"""
    history = await performance_col().find(
        {"employee_id": employee_id}, {"_id": 0}
    ).sort("analysis_date", -1).to_list(length=20)
    
    return {"history": history}


# ==================== RANKING DASHBOARD ====================

@router.get("/ranking")
async def get_employee_ranking(limit: int = 20):
    """Get employee ranking for dashboard"""
    analysis = await analyze_all_employees()
    
    return {
        "top_performers": analysis["all_employees"][:limit],
        "category_distribution": analysis["category_summary"],
        "total_employees": analysis["total_analyzed"],
        "elite_count": analysis["category_summary"].get("ELITE", 0),
        "attention_needed": len(analysis["need_attention"]),
        "generated_at": now_iso()
    }
