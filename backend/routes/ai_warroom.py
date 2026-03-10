# OCB TITAN AI - AI Super War Room System
# Sistem analisis bisnis otomatis dengan prediksi dan rekomendasi

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import uuid

router = APIRouter(prefix="/api/ai-warroom", tags=["AI Super War Room"])

# Database connection
def get_db():
    from server import get_db as server_get_db
    return server_get_db()

def gen_id():
    return str(uuid.uuid4())

def now_iso():
    return datetime.now(timezone.utc).isoformat()

# Collections
def sales_col():
    return get_db()['transactions']

def products_col():
    return get_db()['products']

def branches_col():
    return get_db()['branches']

def employees_col():
    return get_db()['employees']

def inventory_col():
    return get_db()['inventory']

def payroll_col():
    return get_db()['payroll_slips']

def attendance_col():
    return get_db()['attendance']

def kpi_col():
    return get_db()['kpi_data']

# ==================== AI PREDICTION MODELS ====================

@router.get("/dashboard")
async def get_ai_warroom_dashboard():
    """Get comprehensive AI War Room dashboard with all analytics"""
    
    # Get date ranges
    today = datetime.now(timezone.utc).date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    three_months_ago = today - timedelta(days=90)
    
    # Fetch all data
    branches = await branches_col().find({"is_active": True}, {"_id": 0}).to_list(length=100)
    products = await products_col().find({"is_active": True}, {"_id": 0}).to_list(length=500)
    employees = await employees_col().find({"status": "active"}, {"_id": 0}).to_list(length=500)
    
    # Sales analysis
    sales_today = await sales_col().find({
        "created_at": {"$gte": f"{today}T00:00:00"}
    }, {"_id": 0}).to_list(length=1000)
    
    sales_month = await sales_col().find({
        "created_at": {"$gte": f"{month_ago}T00:00:00"}
    }, {"_id": 0}).to_list(length=10000)
    
    # Calculate metrics
    total_sales_today = sum(s.get("total", 0) for s in sales_today)
    total_sales_month = sum(s.get("total", 0) for s in sales_month)
    total_transactions_today = len(sales_today)
    total_transactions_month = len(sales_month)
    
    # Branch performance analysis
    branch_performance = []
    problem_branches = []
    best_branches = []
    
    for branch in branches:
        branch_id = branch.get("id")
        branch_name = branch.get("name", "Unknown")
        
        # Sales for this branch
        branch_sales = [s for s in sales_month if s.get("branch_id") == branch_id]
        branch_total = sum(s.get("total", 0) for s in branch_sales)
        branch_transactions = len(branch_sales)
        
        # Employee count
        branch_employees = len([e for e in employees if e.get("branch_id") == branch_id])
        
        # Calculate average
        avg_daily_sales = branch_total / 30 if branch_total > 0 else 0
        
        # Determine status
        status = "NORMAL"
        issues = []
        
        if avg_daily_sales < 500000:  # Low sales threshold
            status = "WARNING"
            issues.append("Penjualan rendah")
        
        if branch_transactions < 100:  # Low transaction
            if status != "KRITIS":
                status = "WARNING"
            issues.append("Transaksi sedikit")
        
        if branch_employees == 0:
            status = "KRITIS"
            issues.append("Tidak ada karyawan")
        
        perf = {
            "branch_id": branch_id,
            "branch_name": branch_name,
            "total_sales_month": branch_total,
            "total_transactions": branch_transactions,
            "avg_daily_sales": avg_daily_sales,
            "employee_count": branch_employees,
            "status": status,
            "issues": issues
        }
        
        branch_performance.append(perf)
        
        if status in ["WARNING", "KRITIS"]:
            problem_branches.append(perf)
        
        if branch_total > 10000000:  # Top performer
            best_branches.append(perf)
    
    # Sort branches
    branch_performance.sort(key=lambda x: x["total_sales_month"], reverse=True)
    best_branches.sort(key=lambda x: x["total_sales_month"], reverse=True)
    
    # Stock prediction
    low_stock_products = []
    for prod in products:
        stock = prod.get("stock", 0)
        min_stock = prod.get("min_stock", 5)
        
        if stock <= min_stock:
            # Estimate days until out of stock
            # Based on average sales
            prod_sales = [s for s in sales_month if prod.get("id") in str(s.get("items", []))]
            avg_daily_sale = len(prod_sales) / 30 if prod_sales else 0.5
            days_until_empty = int(stock / avg_daily_sale) if avg_daily_sale > 0 else 999
            
            low_stock_products.append({
                "product_id": prod.get("id"),
                "product_name": prod.get("name"),
                "current_stock": stock,
                "min_stock": min_stock,
                "days_until_empty": days_until_empty,
                "restock_recommendation": max(min_stock * 3, 10)
            })
    
    low_stock_products.sort(key=lambda x: x["days_until_empty"])
    
    # AI Recommendations
    recommendations = []
    
    if len(low_stock_products) > 5:
        recommendations.append({
            "type": "stock",
            "priority": "high",
            "message": f"{len(low_stock_products)} produk stok rendah, segera restock",
            "action": "Lakukan pembelian stok"
        })
    
    if len(problem_branches) > 0:
        recommendations.append({
            "type": "branch",
            "priority": "high",
            "message": f"{len(problem_branches)} cabang perlu perhatian khusus",
            "action": "Evaluasi cabang bermasalah"
        })
    
    if total_sales_today < (total_sales_month / 30) * 0.7:
        recommendations.append({
            "type": "sales",
            "priority": "medium",
            "message": "Penjualan hari ini di bawah rata-rata",
            "action": "Pertimbangkan promo atau push sales"
        })
    
    # Sales prediction (simple moving average)
    avg_daily = total_sales_month / 30
    predicted_weekly = avg_daily * 7
    predicted_monthly = avg_daily * 30
    
    return {
        "summary": {
            "total_branches": len(branches),
            "total_products": len(products),
            "total_employees": len(employees),
            "sales_today": total_sales_today,
            "sales_month": total_sales_month,
            "transactions_today": total_transactions_today,
            "transactions_month": total_transactions_month
        },
        "predictions": {
            "sales_next_week": predicted_weekly,
            "sales_next_month": predicted_monthly,
            "confidence": 75  # Simplified confidence
        },
        "branch_performance": branch_performance[:10],  # Top 10
        "problem_branches": problem_branches[:5],
        "best_branches": best_branches[:5],
        "low_stock_alerts": low_stock_products[:10],
        "ai_recommendations": recommendations,
        "generated_at": now_iso()
    }


@router.get("/predictions/sales")
async def predict_sales(period: str = "week", branch_id: Optional[str] = None):
    """Predict sales for given period"""
    
    # Get historical data
    days = 7 if period == "week" else 30 if period == "month" else 90
    start_date = datetime.now(timezone.utc).date() - timedelta(days=days*2)  # 2x period for history
    
    query = {"created_at": {"$gte": f"{start_date}T00:00:00"}}
    if branch_id:
        query["branch_id"] = branch_id
    
    sales = await sales_col().find(query, {"_id": 0}).to_list(length=10000)
    
    # Group by day
    daily_sales = {}
    for s in sales:
        date = s.get("created_at", "")[:10]
        if date not in daily_sales:
            daily_sales[date] = 0
        daily_sales[date] += s.get("total", 0)
    
    # Calculate averages
    if daily_sales:
        avg_daily = sum(daily_sales.values()) / len(daily_sales)
        trend = list(daily_sales.values())
        
        # Simple trend analysis
        if len(trend) > 7:
            recent = sum(trend[-7:]) / 7
            older = sum(trend[:-7]) / max(len(trend) - 7, 1)
            growth_rate = (recent - older) / older if older > 0 else 0
        else:
            growth_rate = 0
    else:
        avg_daily = 0
        growth_rate = 0
    
    # Predictions
    prediction_days = 7 if period == "week" else 30 if period == "month" else 90
    predicted_total = avg_daily * prediction_days * (1 + growth_rate)
    
    return {
        "period": period,
        "branch_id": branch_id,
        "historical_avg_daily": avg_daily,
        "growth_rate": round(growth_rate * 100, 2),
        "predicted_total": predicted_total,
        "predicted_daily_avg": predicted_total / prediction_days if prediction_days > 0 else 0,
        "confidence": min(85, 50 + len(daily_sales)),  # More data = more confidence
        "by_day": [
            {"day": i + 1, "predicted": avg_daily * (1 + growth_rate * (i / prediction_days))}
            for i in range(min(7, prediction_days))
        ]
    }


@router.get("/predictions/stock")
async def predict_stock_depletion(product_id: Optional[str] = None, branch_id: Optional[str] = None):
    """Predict when stock will run out"""
    
    query = {"is_active": True}
    if product_id:
        query["id"] = product_id
    
    products = await products_col().find(query, {"_id": 0}).to_list(length=500)
    
    # Get sales history for calculation
    month_ago = datetime.now(timezone.utc).date() - timedelta(days=30)
    sales = await sales_col().find({
        "created_at": {"$gte": f"{month_ago}T00:00:00"}
    }, {"_id": 0}).to_list(length=10000)
    
    predictions = []
    
    for prod in products:
        prod_id = prod.get("id")
        current_stock = prod.get("stock", 0)
        min_stock = prod.get("min_stock", 5)
        
        # Count how many times this product was sold
        sold_count = 0
        for s in sales:
            items = s.get("items", [])
            for item in items:
                if item.get("product_id") == prod_id:
                    sold_count += item.get("quantity", 1)
        
        avg_daily_sales = sold_count / 30 if sold_count > 0 else 0.1
        days_until_empty = int(current_stock / avg_daily_sales) if avg_daily_sales > 0 else 999
        days_until_min = int((current_stock - min_stock) / avg_daily_sales) if avg_daily_sales > 0 and current_stock > min_stock else 0
        
        # Restock recommendation
        restock_qty = max(int(avg_daily_sales * 30), min_stock * 2)  # 1 month supply
        
        status = "normal"
        if days_until_empty <= 3:
            status = "critical"
        elif days_until_min <= 7:
            status = "warning"
        
        predictions.append({
            "product_id": prod_id,
            "product_name": prod.get("name"),
            "current_stock": current_stock,
            "min_stock": min_stock,
            "avg_daily_sales": round(avg_daily_sales, 2),
            "days_until_empty": days_until_empty,
            "days_until_min_stock": days_until_min,
            "restock_recommendation": restock_qty,
            "status": status
        })
    
    # Sort by urgency
    predictions.sort(key=lambda x: x["days_until_empty"])
    
    return {
        "predictions": predictions[:20],  # Top 20 urgent
        "critical_count": len([p for p in predictions if p["status"] == "critical"]),
        "warning_count": len([p for p in predictions if p["status"] == "warning"]),
        "generated_at": now_iso()
    }


@router.get("/branch-analysis")
async def analyze_branches():
    """Comprehensive branch analysis with status classification"""
    
    branches = await branches_col().find({"is_active": True}, {"_id": 0}).to_list(length=100)
    employees = await employees_col().find({"status": "active"}, {"_id": 0}).to_list(length=500)
    
    # Get 30 day sales
    month_ago = datetime.now(timezone.utc).date() - timedelta(days=30)
    sales = await sales_col().find({
        "created_at": {"$gte": f"{month_ago}T00:00:00"}
    }, {"_id": 0}).to_list(length=10000)
    
    # Get payroll data
    payroll = await payroll_col().find({}, {"_id": 0}).to_list(length=1000)
    
    analysis = []
    
    for branch in branches:
        branch_id = branch.get("id")
        branch_name = branch.get("name", "Unknown")
        
        # Sales metrics
        branch_sales = [s for s in sales if s.get("branch_id") == branch_id]
        total_sales = sum(s.get("total", 0) for s in branch_sales)
        transaction_count = len(branch_sales)
        avg_transaction = total_sales / transaction_count if transaction_count > 0 else 0
        
        # Employee metrics
        branch_employees = [e for e in employees if e.get("branch_id") == branch_id]
        employee_count = len(branch_employees)
        total_payroll = sum(e.get("gaji_pokok", 0) + e.get("tunjangan_total", 0) for e in branch_employees)
        
        # KPI analysis (simplified)
        sales_per_employee = total_sales / employee_count if employee_count > 0 else 0
        payroll_ratio = (total_payroll / total_sales * 100) if total_sales > 0 else 100
        
        # Determine status
        issues = []
        status = "NORMAL"
        
        if total_sales < 5000000:  # < 5 juta/bulan
            issues.append("Penjualan sangat rendah")
            status = "WARNING"
        
        if transaction_count < 50:
            issues.append("Transaksi terlalu sedikit")
            if status != "KRITIS":
                status = "WARNING"
        
        if payroll_ratio > 30:  # Payroll > 30% of sales
            issues.append("Rasio payroll terlalu tinggi")
            if status != "KRITIS":
                status = "WARNING"
        
        if employee_count == 0:
            issues.append("Tidak ada karyawan")
            status = "KRITIS"
        
        if sales_per_employee < 2000000 and employee_count > 0:  # < 2 juta per karyawan
            issues.append("Produktivitas karyawan rendah")
            if status == "NORMAL":
                status = "WARNING"
        
        # AI Recommendations
        recommendations = []
        
        if payroll_ratio > 30 and employee_count > 2:
            recommendations.append("Pertimbangkan efisiensi karyawan")
        
        if total_sales < 5000000:
            recommendations.append("Buat program promo untuk meningkatkan penjualan")
        
        if sales_per_employee < 2000000:
            recommendations.append("Tingkatkan training dan target karyawan")
        
        analysis.append({
            "branch_id": branch_id,
            "branch_name": branch_name,
            "metrics": {
                "total_sales": total_sales,
                "transaction_count": transaction_count,
                "avg_transaction": round(avg_transaction),
                "employee_count": employee_count,
                "total_payroll": total_payroll,
                "sales_per_employee": round(sales_per_employee),
                "payroll_ratio": round(payroll_ratio, 2)
            },
            "status": status,
            "issues": issues,
            "recommendations": recommendations
        })
    
    # Sort by status priority
    status_order = {"KRITIS": 0, "WARNING": 1, "NORMAL": 2}
    analysis.sort(key=lambda x: (status_order.get(x["status"], 2), -x["metrics"]["total_sales"]))
    
    return {
        "total_branches": len(branches),
        "normal_count": len([a for a in analysis if a["status"] == "NORMAL"]),
        "warning_count": len([a for a in analysis if a["status"] == "WARNING"]),
        "critical_count": len([a for a in analysis if a["status"] == "KRITIS"]),
        "branches": analysis,
        "generated_at": now_iso()
    }


@router.get("/business-decisions")
async def get_ai_business_decisions():
    """Get AI-powered business decisions and recommendations"""
    
    # Get all analysis data
    dashboard = await get_ai_warroom_dashboard()
    branch_analysis = await analyze_branches()
    stock_predictions = await predict_stock_depletion()
    
    decisions = []
    
    # Stock decisions
    critical_stocks = stock_predictions.get("critical_count", 0)
    if critical_stocks > 0:
        decisions.append({
            "category": "inventory",
            "priority": "critical",
            "decision": "RESTOCK SEGERA",
            "detail": f"{critical_stocks} produk akan habis dalam 3 hari",
            "action_items": [
                "Buat PO untuk produk kritis",
                "Hubungi supplier",
                "Pertimbangkan transfer stok antar cabang"
            ]
        })
    
    # Branch decisions
    critical_branches = branch_analysis.get("critical_count", 0)
    warning_branches = branch_analysis.get("warning_count", 0)
    
    if critical_branches > 0:
        decisions.append({
            "category": "branch",
            "priority": "critical",
            "decision": "EVALUASI CABANG",
            "detail": f"{critical_branches} cabang dalam kondisi kritis",
            "action_items": [
                "Review performa cabang",
                "Audit keuangan cabang",
                "Pertimbangkan restrukturisasi"
            ]
        })
    
    if warning_branches > 0:
        decisions.append({
            "category": "branch",
            "priority": "high",
            "decision": "PERHATIAN KHUSUS",
            "detail": f"{warning_branches} cabang perlu perhatian",
            "action_items": [
                "Monitor KPI mingguan",
                "Buat target improvement",
                "Evaluasi karyawan"
            ]
        })
    
    # Employee decisions
    for branch in branch_analysis.get("branches", []):
        if branch.get("metrics", {}).get("payroll_ratio", 0) > 35:
            decisions.append({
                "category": "hr",
                "priority": "medium",
                "decision": "EFISIENSI KARYAWAN",
                "detail": f"Cabang {branch.get('branch_name')} rasio payroll {branch.get('metrics',{}).get('payroll_ratio')}%",
                "action_items": [
                    "Review beban kerja",
                    "Pertimbangkan rotasi karyawan",
                    "Evaluasi produktivitas"
                ]
            })
    
    # Sales decisions
    problem_branches = dashboard.get("problem_branches", [])
    if len(problem_branches) > 0:
        decisions.append({
            "category": "sales",
            "priority": "high",
            "decision": "PUSH SALES",
            "detail": f"{len(problem_branches)} cabang penjualan di bawah target",
            "action_items": [
                "Buat promo cabang",
                "Training sales team",
                "Review strategi penjualan"
            ]
        })
    
    # Sort by priority
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    decisions.sort(key=lambda x: priority_order.get(x["priority"], 3))
    
    return {
        "total_decisions": len(decisions),
        "critical_count": len([d for d in decisions if d["priority"] == "critical"]),
        "high_count": len([d for d in decisions if d["priority"] == "high"]),
        "decisions": decisions,
        "generated_at": now_iso()
    }
