# OCB TITAN AI - AI Command Center
# AI-powered business analysis and recommendations

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel
import uuid

from database import get_db

router = APIRouter(prefix="/api/ai-command", tags=["AI Command Center"])

def gen_id():
    return str(uuid.uuid4())

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def get_wib_now():
    return datetime.now(timezone.utc) + timedelta(hours=7)

# Collections
def insights_col():
    return get_db()['ai_insights']

def recommendations_col():
    return get_db()['ai_recommendations']

def analysis_col():
    return get_db()['ai_analysis']

# ==================== AI BUSINESS ANALYSIS ====================

@router.get("/dashboard")
async def get_ai_dashboard():
    """Get AI Command Center dashboard"""
    today = get_wib_now().strftime("%Y-%m-%d")
    month_start = get_wib_now().strftime("%Y-%m-01")
    
    # Collect all data for analysis
    setoran_col = get_db()['setoran_harian']
    employees_col = get_db()['employees']
    attendance_col = get_db()['attendance']
    branches_col = get_db()['branches']
    products_col = get_db()['products']
    
    # Get setoran data
    setoran_today = await setoran_col.find({"tanggal": today}, {"_id": 0}).to_list(length=100)
    setoran_month = await setoran_col.find({
        "tanggal": {"$gte": month_start, "$lte": today}
    }, {"_id": 0}).to_list(length=3000)
    
    # Get attendance
    attendance_today = await attendance_col.find({"tanggal": today}, {"_id": 0}).to_list(length=500)
    
    # Get branches
    branches = await branches_col.find({}, {"_id": 0}).to_list(length=100)
    
    # Get employees
    employees = await employees_col.find({"status": "active"}, {"_id": 0}).to_list(length=500)
    
    # Get products with low stock
    low_stock = await products_col.find({
        "$expr": {"$lt": ["$stock", "$min_stock"]}
    }, {"_id": 0}).to_list(length=100)
    
    # Calculate metrics
    total_sales_today = sum(s.get("total_penjualan", 0) for s in setoran_today)
    total_sales_month = sum(s.get("total_penjualan", 0) for s in setoran_month)
    total_minus_today = sum(s.get("selisih", 0) for s in setoran_today if s.get("selisih", 0) < 0)
    total_minus_month = sum(s.get("selisih", 0) for s in setoran_month if s.get("selisih", 0) < 0)
    
    attendance_rate = len([a for a in attendance_today if a.get("status") == "hadir"]) / len(employees) * 100 if employees else 0
    late_rate = len([a for a in attendance_today if a.get("status") == "telat"]) / len(attendance_today) * 100 if attendance_today else 0
    
    branches_reported = len(set(s.get("branch_id") for s in setoran_today))
    
    # Generate AI Insights
    insights = []
    
    # Sales insight
    if total_sales_today > 0:
        avg_daily = total_sales_month / get_wib_now().day if get_wib_now().day > 0 else 0
        if total_sales_today > avg_daily * 1.2:
            insights.append({
                "type": "positive",
                "category": "sales",
                "title": "Penjualan Hari Ini Meningkat!",
                "message": f"Penjualan hari ini Rp {total_sales_today:,.0f} lebih tinggi 20% dari rata-rata harian",
                "priority": "info"
            })
        elif total_sales_today < avg_daily * 0.8:
            insights.append({
                "type": "warning",
                "category": "sales",
                "title": "Penjualan Hari Ini Menurun",
                "message": f"Penjualan hari ini Rp {total_sales_today:,.0f} lebih rendah dari rata-rata harian",
                "priority": "warning"
            })
    
    # Minus insight
    if total_minus_today < -100000:
        insights.append({
            "type": "critical",
            "category": "finance",
            "title": "Alert: Minus Kas Signifikan",
            "message": f"Total minus kas hari ini Rp {abs(total_minus_today):,.0f}. Perlu investigasi segera.",
            "priority": "critical"
        })
    
    # Attendance insight
    if attendance_rate < 80:
        insights.append({
            "type": "warning",
            "category": "hr",
            "title": "Tingkat Kehadiran Rendah",
            "message": f"Hanya {attendance_rate:.1f}% karyawan yang hadir hari ini",
            "priority": "warning"
        })
    
    if late_rate > 20:
        insights.append({
            "type": "warning",
            "category": "hr",
            "title": "Banyak Karyawan Terlambat",
            "message": f"{late_rate:.1f}% karyawan terlambat hari ini",
            "priority": "warning"
        })
    
    # Stock insight
    if len(low_stock) > 10:
        insights.append({
            "type": "warning",
            "category": "inventory",
            "title": "Banyak Produk Stok Rendah",
            "message": f"{len(low_stock)} produk memiliki stok di bawah minimum",
            "priority": "warning"
        })
    
    # Branch coverage
    if branches_reported < len(branches) * 0.8:
        insights.append({
            "type": "warning",
            "category": "operational",
            "title": "Cabang Belum Lapor",
            "message": f"Baru {branches_reported} dari {len(branches)} cabang yang sudah lapor setoran",
            "priority": "info"
        })
    
    return {
        "generated_at": now_iso(),
        "summary": {
            "total_branches": len(branches),
            "total_employees": len(employees),
            "branches_reported_today": branches_reported,
            "attendance_rate": round(attendance_rate, 1),
            "late_rate": round(late_rate, 1)
        },
        "financials": {
            "sales_today": total_sales_today,
            "sales_month": total_sales_month,
            "minus_today": total_minus_today,
            "minus_month": total_minus_month
        },
        "inventory": {
            "low_stock_count": len(low_stock),
            "low_stock_items": low_stock[:10]
        },
        "insights": insights,
        "insights_count": {
            "critical": len([i for i in insights if i["priority"] == "critical"]),
            "warning": len([i for i in insights if i["priority"] == "warning"]),
            "info": len([i for i in insights if i["priority"] == "info"])
        }
    }

# ==================== AI RECOMMENDATIONS ====================

@router.get("/recommendations")
async def get_ai_recommendations():
    """Get AI-powered business recommendations"""
    today = get_wib_now()
    month_start = today.strftime("%Y-%m-01")
    
    setoran_col = get_db()['setoran_harian']
    employees_col = get_db()['employees']
    products_col = get_db()['products']
    
    # Get data for analysis
    setoran_month = await setoran_col.find({
        "tanggal": {"$gte": month_start}
    }, {"_id": 0}).to_list(length=3000)
    
    employees = await employees_col.find({"status": "active"}, {"_id": 0}).to_list(length=500)
    
    low_stock = await products_col.find({
        "$expr": {"$lt": ["$stock", "$min_stock"]}
    }, {"_id": 0}).to_list(length=100)
    
    recommendations = []
    
    # Branch performance recommendations
    branch_sales = {}
    for s in setoran_month:
        bid = s.get("branch_id")
        if bid not in branch_sales:
            branch_sales[bid] = {"sales": 0, "count": 0, "minus": 0, "name": s.get("branch_name")}
        branch_sales[bid]["sales"] += s.get("total_penjualan", 0)
        branch_sales[bid]["count"] += 1
        if s.get("selisih", 0) < 0:
            branch_sales[bid]["minus"] += 1
    
    # Find underperforming branches
    if branch_sales:
        avg_sales = sum(b["sales"] for b in branch_sales.values()) / len(branch_sales)
        underperforming = [b for bid, b in branch_sales.items() if b["sales"] < avg_sales * 0.7]
        
        if underperforming:
            recommendations.append({
                "id": gen_id(),
                "category": "sales",
                "priority": "high",
                "title": "Tingkatkan Performa Cabang",
                "description": f"{len(underperforming)} cabang memiliki penjualan di bawah rata-rata",
                "action": "Review operasional cabang tersebut dan berikan pelatihan tambahan",
                "impact": "Potensi peningkatan revenue 15-25%",
                "branches": [b["name"] for b in underperforming[:5]]
            })
    
    # Stock recommendations
    if len(low_stock) > 0:
        recommendations.append({
            "id": gen_id(),
            "category": "inventory",
            "priority": "high",
            "title": "Restock Produk Segera",
            "description": f"{len(low_stock)} produk perlu di-restock",
            "action": "Buat PO untuk produk dengan stok rendah",
            "impact": "Mencegah kehilangan penjualan karena stok habis",
            "items": [{"name": p.get("name"), "stock": p.get("stock")} for p in low_stock[:10]]
        })
    
    # Employee recommendations
    employees_with_minus = {}
    for s in setoran_month:
        if s.get("selisih", 0) < 0:
            eid = s.get("penjaga_id")
            if eid not in employees_with_minus:
                employees_with_minus[eid] = {"name": s.get("penjaga_name"), "count": 0, "total": 0}
            employees_with_minus[eid]["count"] += 1
            employees_with_minus[eid]["total"] += abs(s.get("selisih", 0))
    
    repeat_offenders = [e for e in employees_with_minus.values() if e["count"] >= 3]
    if repeat_offenders:
        recommendations.append({
            "id": gen_id(),
            "category": "hr",
            "priority": "medium",
            "title": "Evaluasi Karyawan dengan Minus Berulang",
            "description": f"{len(repeat_offenders)} karyawan memiliki minus kas berulang",
            "action": "Lakukan coaching dan evaluasi prosedur kas",
            "impact": "Mengurangi kerugian dari selisih kas",
            "employees": [e["name"] for e in repeat_offenders[:5]]
        })
    
    # General recommendations
    recommendations.append({
        "id": gen_id(),
        "category": "operational",
        "priority": "low",
        "title": "Review Target Bulanan",
        "description": "Evaluasi pencapaian target bulan ini",
        "action": "Sesuaikan strategi untuk sisa bulan",
        "impact": "Optimasi pencapaian target"
    })
    
    return {
        "generated_at": now_iso(),
        "total_recommendations": len(recommendations),
        "by_priority": {
            "high": len([r for r in recommendations if r["priority"] == "high"]),
            "medium": len([r for r in recommendations if r["priority"] == "medium"]),
            "low": len([r for r in recommendations if r["priority"] == "low"])
        },
        "recommendations": recommendations
    }

# ==================== AI TREND ANALYSIS ====================

@router.get("/trends")
async def get_trend_analysis(days: int = 30):
    """Get AI trend analysis"""
    end_date = get_wib_now()
    start_date = end_date - timedelta(days=days)
    
    setoran_col = get_db()['setoran_harian']
    
    setoran = await setoran_col.find({
        "tanggal": {"$gte": start_date.strftime("%Y-%m-%d"), "$lte": end_date.strftime("%Y-%m-%d")}
    }, {"_id": 0}).sort("tanggal", 1).to_list(length=10000)
    
    # Group by date
    daily_data = {}
    for s in setoran:
        date = s.get("tanggal")
        if date not in daily_data:
            daily_data[date] = {"sales": 0, "transactions": 0, "minus": 0, "branches": 0}
        daily_data[date]["sales"] += s.get("total_penjualan", 0)
        daily_data[date]["transactions"] += s.get("total_transaksi", 0)
        if s.get("selisih", 0) < 0:
            daily_data[date]["minus"] += abs(s.get("selisih", 0))
        daily_data[date]["branches"] += 1
    
    # Convert to list
    trend_data = [{"date": k, **v} for k, v in sorted(daily_data.items())]
    
    # Calculate trends
    if len(trend_data) >= 7:
        recent_7 = trend_data[-7:]
        prev_7 = trend_data[-14:-7] if len(trend_data) >= 14 else trend_data[:7]
        
        recent_avg = sum(d["sales"] for d in recent_7) / 7
        prev_avg = sum(d["sales"] for d in prev_7) / 7
        
        sales_trend = ((recent_avg - prev_avg) / prev_avg * 100) if prev_avg > 0 else 0
        
        trend_direction = "up" if sales_trend > 5 else "down" if sales_trend < -5 else "stable"
    else:
        sales_trend = 0
        trend_direction = "stable"
    
    return {
        "period": f"{days} hari terakhir",
        "data_points": len(trend_data),
        "trend_direction": trend_direction,
        "sales_trend_percentage": round(sales_trend, 2),
        "daily_data": trend_data,
        "summary": {
            "total_sales": sum(d["sales"] for d in trend_data),
            "avg_daily_sales": sum(d["sales"] for d in trend_data) / len(trend_data) if trend_data else 0,
            "total_transactions": sum(d["transactions"] for d in trend_data),
            "total_minus": sum(d["minus"] for d in trend_data)
        }
    }

# ==================== AI ANOMALY DETECTION ====================

@router.get("/anomalies")
async def detect_anomalies():
    """Detect anomalies in business data"""
    today = get_wib_now().strftime("%Y-%m-%d")
    month_start = get_wib_now().strftime("%Y-%m-01")
    
    setoran_col = get_db()['setoran_harian']
    attendance_col = get_db()['attendance']
    
    setoran = await setoran_col.find({
        "tanggal": {"$gte": month_start}
    }, {"_id": 0}).to_list(length=5000)
    
    anomalies = []
    
    # Detect unusual minus patterns
    employee_minus = {}
    for s in setoran:
        if s.get("selisih", 0) < -100000:  # Significant minus
            eid = s.get("penjaga_id")
            if eid not in employee_minus:
                employee_minus[eid] = {"name": s.get("penjaga_name"), "incidents": []}
            employee_minus[eid]["incidents"].append({
                "date": s.get("tanggal"),
                "amount": s.get("selisih"),
                "branch": s.get("branch_name")
            })
    
    for eid, data in employee_minus.items():
        if len(data["incidents"]) >= 2:
            anomalies.append({
                "type": "repeated_minus",
                "severity": "high",
                "entity_type": "employee",
                "entity_id": eid,
                "entity_name": data["name"],
                "description": f"Karyawan ini memiliki {len(data['incidents'])} insiden minus kas signifikan",
                "details": data["incidents"],
                "recommended_action": "Investigasi dan audit transaksi"
            })
    
    # Detect unusual sales patterns
    branch_sales = {}
    for s in setoran:
        bid = s.get("branch_id")
        if bid not in branch_sales:
            branch_sales[bid] = {"name": s.get("branch_name"), "daily_sales": []}
        branch_sales[bid]["daily_sales"].append(s.get("total_penjualan", 0))
    
    for bid, data in branch_sales.items():
        if len(data["daily_sales"]) >= 5:
            avg = sum(data["daily_sales"]) / len(data["daily_sales"])
            std_dev = (sum((x - avg) ** 2 for x in data["daily_sales"]) / len(data["daily_sales"])) ** 0.5
            
            # Check for outliers
            for i, sales in enumerate(data["daily_sales"]):
                if abs(sales - avg) > 2 * std_dev and std_dev > 0:
                    anomalies.append({
                        "type": "sales_anomaly",
                        "severity": "medium",
                        "entity_type": "branch",
                        "entity_id": bid,
                        "entity_name": data["name"],
                        "description": f"Penjualan tidak normal: Rp {sales:,.0f} (avg: Rp {avg:,.0f})",
                        "recommended_action": "Verifikasi data penjualan"
                    })
                    break  # One anomaly per branch
    
    return {
        "generated_at": now_iso(),
        "total_anomalies": len(anomalies),
        "by_severity": {
            "high": len([a for a in anomalies if a["severity"] == "high"]),
            "medium": len([a for a in anomalies if a["severity"] == "medium"]),
            "low": len([a for a in anomalies if a["severity"] == "low"])
        },
        "anomalies": anomalies
    }
