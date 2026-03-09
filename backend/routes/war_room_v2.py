# OCB GROUP SUPER ERP - War Room Command Center
# Real-time Dashboard untuk Owner

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel
import uuid

from database import get_db
from models.erp_models import (
    WarRoomSnapshot, AIInsight, SystemAlert, AlertType, AlertSeverity
)

router = APIRouter(prefix="/api/war-room", tags=["War Room"])

def gen_id():
    return str(uuid.uuid4())

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def get_wib_now():
    return datetime.now(timezone.utc) + timedelta(hours=7)

# Collections
def setoran_col():
    return get_db()['setoran_harian']

def selisih_col():
    return get_db()['selisih_kas']

def employees_col():
    return get_db()['employees']

def attendance_col():
    return get_db()['attendance']

def alerts_col():
    return get_db()['system_alerts']

def insights_col():
    return get_db()['ai_insights']

def branches_col():
    return get_db()['branches']

def transactions_col():
    return get_db()['transactions']

def target_cabang_col():
    return get_db()['master_target_cabang']

def snapshots_col():
    return get_db()['war_room_snapshots']

# ==================== MAIN DASHBOARD ====================

@router.get("/dashboard")
async def get_war_room_dashboard():
    today = get_wib_now().strftime("%Y-%m-%d")
    month = get_wib_now().month
    year = get_wib_now().year
    
    # Get first day of month
    month_start = f"{year}-{month:02d}-01"
    
    # === CABANG ===
    branches = await branches_col().find({}, {"_id": 0}).to_list(length=100)
    total_cabang = len(branches)
    
    # Setoran hari ini
    setoran_today = await setoran_col().find({"tanggal": today}, {"_id": 0}).to_list(length=100)
    cabang_sudah_setor = len(set(s["branch_id"] for s in setoran_today))
    cabang_belum_setor = total_cabang - cabang_sudah_setor
    
    # === KARYAWAN ===
    total_karyawan = await employees_col().count_documents({"status": "active"})
    
    # Attendance hari ini
    attendance_today = await attendance_col().find({"tanggal": today}, {"_id": 0}).to_list(length=500)
    karyawan_hadir = len([a for a in attendance_today if a.get("status") in ["hadir", "telat"]])
    karyawan_telat = len([a for a in attendance_today if a.get("status") == "telat"])
    
    # === PENJUALAN HARI INI ===
    penjualan_hari_ini = sum(s.get("total_penjualan", 0) for s in setoran_today)
    transaksi_hari_ini = sum(s.get("total_transaksi", 0) for s in setoran_today)
    rata_rata_transaksi = penjualan_hari_ini / transaksi_hari_ini if transaksi_hari_ini > 0 else 0
    
    # === SETORAN HARI INI ===
    total_setoran_hari_ini = sum(s.get("total_setoran", 0) for s in setoran_today)
    
    # === SELISIH ===
    total_minus_hari_ini = sum(s.get("selisih", 0) for s in setoran_today if s.get("selisih", 0) < 0)
    total_plus_hari_ini = sum(s.get("selisih", 0) for s in setoran_today if s.get("selisih", 0) > 0)
    
    # Selisih bulan ini
    setoran_month = await setoran_col().find({
        "tanggal": {"$gte": month_start, "$lte": today}
    }, {"_id": 0}).to_list(length=1000)
    
    total_minus_bulan_ini = sum(s.get("selisih", 0) for s in setoran_month if s.get("selisih", 0) < 0)
    total_plus_bulan_ini = sum(s.get("selisih", 0) for s in setoran_month if s.get("selisih", 0) > 0)
    
    # === PENJUALAN BULAN INI ===
    penjualan_bulan_ini = sum(s.get("total_penjualan", 0) for s in setoran_month)
    
    # Target bulan ini
    targets = await target_cabang_col().find({
        "period_month": month,
        "period_year": year
    }).to_list(length=100)
    target_bulan_ini = sum(t.get("target_revenue", 0) for t in targets)
    
    achievement_percent = (penjualan_bulan_ini / target_bulan_ini * 100) if target_bulan_ini > 0 else 0
    
    # === ALERTS ===
    pending_alerts = await alerts_col().find({"is_resolved": False}, {"_id": 0}).to_list(length=100)
    critical_alerts = len([a for a in pending_alerts if a.get("severity") == "critical"])
    urgent_alerts = len([a for a in pending_alerts if a.get("severity") == "urgent"])
    
    # === TOP & BOTTOM CABANG ===
    branch_sales = {}
    for s in setoran_month:
        bid = s.get("branch_id")
        if bid not in branch_sales:
            branch_sales[bid] = {
                "branch_id": bid,
                "branch_name": s.get("branch_name", ""),
                "total_penjualan": 0,
                "total_transaksi": 0,
                "total_minus": 0
            }
        branch_sales[bid]["total_penjualan"] += s.get("total_penjualan", 0)
        branch_sales[bid]["total_transaksi"] += s.get("total_transaksi", 0)
        if s.get("selisih", 0) < 0:
            branch_sales[bid]["total_minus"] += abs(s.get("selisih", 0))
    
    sorted_branches = sorted(branch_sales.values(), key=lambda x: x["total_penjualan"], reverse=True)
    top_cabang = sorted_branches[:5]
    bottom_cabang = sorted_branches[-5:] if len(sorted_branches) > 5 else []
    
    # === TOP KARYAWAN & BERMASALAH ===
    emp_selisih = {}
    for s in setoran_month:
        eid = s.get("penjaga_id")
        if eid and s.get("selisih", 0) < 0:
            if eid not in emp_selisih:
                emp_selisih[eid] = {
                    "employee_id": eid,
                    "employee_name": s.get("penjaga_name", ""),
                    "total_minus": 0,
                    "count": 0
                }
            emp_selisih[eid]["total_minus"] += abs(s.get("selisih", 0))
            emp_selisih[eid]["count"] += 1
    
    karyawan_bermasalah = sorted(emp_selisih.values(), key=lambda x: x["total_minus"], reverse=True)[:10]
    
    # === TREND 7 HARI ===
    trend_penjualan = []
    trend_minus = []
    
    for i in range(6, -1, -1):
        date = (get_wib_now() - timedelta(days=i)).strftime("%Y-%m-%d")
        day_setoran = [s for s in setoran_month if s.get("tanggal") == date]
        
        trend_penjualan.append({
            "tanggal": date,
            "total": sum(s.get("total_penjualan", 0) for s in day_setoran)
        })
        
        trend_minus.append({
            "tanggal": date,
            "total": sum(abs(s.get("selisih", 0)) for s in day_setoran if s.get("selisih", 0) < 0)
        })
    
    return {
        "tanggal": today,
        "overview": {
            "total_cabang": total_cabang,
            "cabang_sudah_setor": cabang_sudah_setor,
            "cabang_belum_setor": cabang_belum_setor,
            "total_karyawan": total_karyawan,
            "karyawan_hadir": karyawan_hadir,
            "karyawan_telat": karyawan_telat
        },
        "sales_today": {
            "penjualan": penjualan_hari_ini,
            "transaksi": transaksi_hari_ini,
            "rata_rata": round(rata_rata_transaksi)
        },
        "setoran_today": {
            "total_setoran": total_setoran_hari_ini,
            "total_minus": abs(total_minus_hari_ini),
            "total_plus": total_plus_hari_ini
        },
        "sales_mtd": {
            "penjualan": penjualan_bulan_ini,
            "target": target_bulan_ini,
            "achievement": round(achievement_percent, 1),
            "total_minus": abs(total_minus_bulan_ini),
            "total_plus": total_plus_bulan_ini
        },
        "alerts": {
            "total": len(pending_alerts),
            "critical": critical_alerts,
            "urgent": urgent_alerts,
            "recent": pending_alerts[:5]
        },
        "rankings": {
            "top_cabang": top_cabang,
            "bottom_cabang": bottom_cabang,
            "karyawan_bermasalah": karyawan_bermasalah
        },
        "trends": {
            "penjualan_7_hari": trend_penjualan,
            "minus_7_hari": trend_minus
        }
    }

# ==================== CABANG BELUM SETOR ====================

@router.get("/cabang-belum-setor")
async def get_cabang_belum_setor():
    today = get_wib_now().strftime("%Y-%m-%d")
    
    # Get all branches
    branches = await branches_col().find({}, {"_id": 0}).to_list(length=100)
    
    # Get setoran today
    setoran_today = await setoran_col().find({"tanggal": today}, {"_id": 0}).to_list(length=100)
    sudah_setor_ids = set(s["branch_id"] for s in setoran_today)
    
    belum_setor = []
    for b in branches:
        if b.get("id") not in sudah_setor_ids:
            belum_setor.append({
                "branch_id": b.get("id"),
                "branch_code": b.get("code", ""),
                "branch_name": b.get("name", ""),
                "address": b.get("address", ""),
                "phone": b.get("phone", "")
            })
    
    return {
        "tanggal": today,
        "total_belum_setor": len(belum_setor),
        "cabang": belum_setor
    }

# ==================== KARYAWAN TIDAK ABSEN ====================

@router.get("/karyawan-tidak-absen")
async def get_karyawan_tidak_absen():
    today = get_wib_now().strftime("%Y-%m-%d")
    
    # Get all active employees
    employees = await employees_col().find({"status": "active"}, {"_id": 0}).to_list(length=500)
    
    # Get attendance today
    attendance = await attendance_col().find({"tanggal": today}, {"_id": 0}).to_list(length=500)
    sudah_absen_ids = set(a["employee_id"] for a in attendance)
    
    tidak_absen = []
    for e in employees:
        if e.get("id") not in sudah_absen_ids:
            tidak_absen.append({
                "employee_id": e.get("id"),
                "nik": e.get("nik", ""),
                "name": e.get("name", ""),
                "jabatan": e.get("jabatan_name", ""),
                "branch_name": e.get("branch_name", ""),
                "phone": e.get("phone", "")
            })
    
    return {
        "tanggal": today,
        "total_tidak_absen": len(tidak_absen),
        "karyawan": tidak_absen
    }

# ==================== SELISIH KAS PENDING ====================

@router.get("/selisih-pending")
async def get_selisih_pending():
    selisih = await selisih_col().find({
        "resolution": "pending"
    }, {"_id": 0}).sort("tanggal", -1).to_list(length=100)
    
    total_minus = sum(s.get("nominal", 0) for s in selisih if s.get("jenis") == "minus")
    total_plus = sum(s.get("nominal", 0) for s in selisih if s.get("jenis") == "plus")
    
    return {
        "total_pending": len(selisih),
        "total_minus": total_minus,
        "total_plus": total_plus,
        "selisih": selisih
    }

# ==================== FRAUD DETECTION ====================

@router.get("/fraud-detection")
async def detect_fraud_patterns():
    """Detect potential fraud patterns"""
    month = get_wib_now().month
    year = get_wib_now().year
    month_start = f"{year}-{month:02d}-01"
    today = get_wib_now().strftime("%Y-%m-%d")
    
    alerts = []
    
    # Pattern 1: Karyawan dengan minus berulang
    selisih_month = await selisih_col().find({
        "tanggal": {"$gte": month_start, "$lte": today},
        "jenis": "minus"
    }, {"_id": 0}).to_list(length=1000)
    
    emp_minus_count = {}
    for s in selisih_month:
        eid = s.get("penjaga_id")
        if eid:
            if eid not in emp_minus_count:
                emp_minus_count[eid] = {
                    "employee_id": eid,
                    "employee_name": s.get("penjaga_name", ""),
                    "count": 0,
                    "total": 0
                }
            emp_minus_count[eid]["count"] += 1
            emp_minus_count[eid]["total"] += s.get("nominal", 0)
    
    # Flag employees with 3+ minus incidents
    for eid, data in emp_minus_count.items():
        if data["count"] >= 3:
            alerts.append({
                "pattern": "MINUS_BERULANG",
                "severity": "critical" if data["count"] >= 5 else "warning",
                "employee_id": eid,
                "employee_name": data["employee_name"],
                "count": data["count"],
                "total": data["total"],
                "message": f"{data['employee_name']} memiliki {data['count']}x minus kas total Rp {data['total']:,.0f}"
            })
    
    # Pattern 2: Penjualan menurun drastis
    # Get last 7 days vs previous 7 days
    today_dt = get_wib_now()
    last_7_start = (today_dt - timedelta(days=7)).strftime("%Y-%m-%d")
    prev_7_start = (today_dt - timedelta(days=14)).strftime("%Y-%m-%d")
    
    setoran_last7 = await setoran_col().find({
        "tanggal": {"$gte": last_7_start, "$lte": today}
    }).to_list(length=500)
    
    setoran_prev7 = await setoran_col().find({
        "tanggal": {"$gte": prev_7_start, "$lt": last_7_start}
    }).to_list(length=500)
    
    # Per branch comparison
    branch_last7 = {}
    for s in setoran_last7:
        bid = s.get("branch_id")
        if bid not in branch_last7:
            branch_last7[bid] = {"name": s.get("branch_name", ""), "total": 0}
        branch_last7[bid]["total"] += s.get("total_penjualan", 0)
    
    branch_prev7 = {}
    for s in setoran_prev7:
        bid = s.get("branch_id")
        if bid not in branch_prev7:
            branch_prev7[bid] = {"name": s.get("branch_name", ""), "total": 0}
        branch_prev7[bid]["total"] += s.get("total_penjualan", 0)
    
    # Check for significant drops
    for bid, data in branch_last7.items():
        if bid in branch_prev7:
            prev_total = branch_prev7[bid]["total"]
            curr_total = data["total"]
            if prev_total > 0:
                change = ((curr_total - prev_total) / prev_total) * 100
                if change < -30:  # More than 30% drop
                    alerts.append({
                        "pattern": "PENJUALAN_TURUN",
                        "severity": "warning",
                        "branch_id": bid,
                        "branch_name": data["name"],
                        "change_percent": round(change, 1),
                        "prev_total": prev_total,
                        "curr_total": curr_total,
                        "message": f"Penjualan {data['name']} turun {abs(round(change, 1))}% dalam 7 hari terakhir"
                    })
    
    # Pattern 3: Sering telat absen
    attendance_month = await attendance_col().find({
        "tanggal": {"$gte": month_start, "$lte": today},
        "status": "telat"
    }).to_list(length=1000)
    
    emp_telat_count = {}
    for a in attendance_month:
        eid = a.get("employee_id")
        if eid:
            if eid not in emp_telat_count:
                emp_telat_count[eid] = {
                    "employee_id": eid,
                    "employee_name": a.get("employee_name", ""),
                    "count": 0,
                    "total_menit": 0
                }
            emp_telat_count[eid]["count"] += 1
            emp_telat_count[eid]["total_menit"] += a.get("telat_menit", 0)
    
    # Flag employees with 5+ late days
    for eid, data in emp_telat_count.items():
        if data["count"] >= 5:
            alerts.append({
                "pattern": "SERING_TELAT",
                "severity": "warning",
                "employee_id": eid,
                "employee_name": data["employee_name"],
                "count": data["count"],
                "total_menit": data["total_menit"],
                "message": f"{data['employee_name']} telat {data['count']}x bulan ini, total {data['total_menit']} menit"
            })
    
    return {
        "total_alerts": len(alerts),
        "by_severity": {
            "critical": len([a for a in alerts if a.get("severity") == "critical"]),
            "warning": len([a for a in alerts if a.get("severity") == "warning"])
        },
        "alerts": alerts
    }

# ==================== AI INSIGHTS ====================

@router.get("/ai-insights")
async def get_ai_insights():
    """Get AI-generated business insights"""
    today = get_wib_now().strftime("%Y-%m-%d")
    
    insights = []
    
    # Get data for analysis
    dashboard = await get_war_room_dashboard()
    
    # Insight 1: Achievement status
    achievement = dashboard["sales_mtd"]["achievement"]
    if achievement < 50:
        insights.append({
            "type": "performance",
            "severity": "critical",
            "title": "Target Penjualan Dalam Bahaya",
            "summary": f"Achievement baru {achievement}% dari target bulanan",
            "recommendation": "Fokuskan promosi dan tingkatkan aktivitas penjualan segera"
        })
    elif achievement < 80:
        insights.append({
            "type": "performance",
            "severity": "warning",
            "title": "Target Penjualan Perlu Perhatian",
            "summary": f"Achievement {achievement}% - masih ada gap untuk mencapai target",
            "recommendation": "Review strategi penjualan dan identifikasi cabang underperform"
        })
    else:
        insights.append({
            "type": "performance",
            "severity": "info",
            "title": "Performa Penjualan Baik",
            "summary": f"Achievement sudah mencapai {achievement}%",
            "recommendation": "Pertahankan momentum dan siapkan target bulan depan"
        })
    
    # Insight 2: Selisih kas
    total_minus_mtd = abs(dashboard["sales_mtd"]["total_minus"])
    if total_minus_mtd > 1000000:
        insights.append({
            "type": "risk",
            "severity": "critical",
            "title": "Minus Kas Tinggi",
            "summary": f"Total minus kas bulan ini Rp {total_minus_mtd:,.0f}",
            "recommendation": "Audit segera cabang dan karyawan dengan minus terbanyak"
        })
    
    # Insight 3: Attendance
    karyawan_hadir = dashboard["overview"]["karyawan_hadir"]
    total_karyawan = dashboard["overview"]["total_karyawan"]
    attendance_rate = (karyawan_hadir / total_karyawan * 100) if total_karyawan > 0 else 0
    
    if attendance_rate < 80:
        insights.append({
            "type": "hr",
            "severity": "warning",
            "title": "Tingkat Kehadiran Rendah",
            "summary": f"Hanya {attendance_rate:.1f}% karyawan hadir hari ini",
            "recommendation": "Cek alasan ketidakhadiran dan evaluasi kebijakan absensi"
        })
    
    # Insight 4: Cabang belum setor
    belum_setor = dashboard["overview"]["cabang_belum_setor"]
    if belum_setor > 5:
        insights.append({
            "type": "operational",
            "severity": "warning",
            "title": "Banyak Cabang Belum Setor",
            "summary": f"{belum_setor} cabang belum input setoran hari ini",
            "recommendation": "Follow up segera ke cabang yang belum setor"
        })
    
    return {
        "tanggal": today,
        "total_insights": len(insights),
        "insights": insights
    }

# ==================== REAL-TIME FEED ====================

@router.get("/live-feed")
async def get_live_feed(limit: int = 20):
    """Get real-time activity feed"""
    
    # Combine recent activities
    activities = []
    
    # Recent setoran
    setoran = await setoran_col().find({}, {"_id": 0}).sort("created_at", -1).limit(10).to_list(length=10)
    for s in setoran:
        activities.append({
            "type": "setoran",
            "timestamp": s.get("created_at", ""),
            "title": f"Setoran {s.get('branch_name', '')}",
            "description": f"Rp {s.get('total_setoran', 0):,.0f} oleh {s.get('penjaga_name', '')}",
            "severity": "warning" if s.get("selisih", 0) < 0 else "info"
        })
    
    # Recent attendance
    attendance = await attendance_col().find({}, {"_id": 0}).sort("created_at", -1).limit(10).to_list(length=10)
    for a in attendance:
        activities.append({
            "type": "attendance",
            "timestamp": a.get("created_at", ""),
            "title": f"Check-in {a.get('employee_name', '')}",
            "description": f"di {a.get('branch_name', '')} - {a.get('status', '')}",
            "severity": "warning" if a.get("status") == "telat" else "info"
        })
    
    # Recent alerts
    alerts = await alerts_col().find({"is_resolved": False}, {"_id": 0}).sort("created_at", -1).limit(10).to_list(length=10)
    for a in alerts:
        activities.append({
            "type": "alert",
            "timestamp": a.get("created_at", ""),
            "title": a.get("title", ""),
            "description": a.get("message", ""),
            "severity": a.get("severity", "info")
        })
    
    # Sort by timestamp
    activities.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    
    return {"activities": activities[:limit]}
