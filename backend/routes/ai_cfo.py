# OCB TITAN AI - AI CFO Module
# Analisis keuangan, laba rugi, cash flow, dan efisiensi bisnis

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import uuid

router = APIRouter(prefix="/api/ai-cfo", tags=["AI CFO Module"])

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

def expenses_col():
    return get_db()['expenses']

def payroll_col():
    return get_db()['payroll_slips']

def cash_flow_col():
    return get_db()['cash_flow']

def purchases_col():
    return get_db()['purchases']

# ==================== CFO DASHBOARD ====================

@router.get("/dashboard")
async def get_cfo_dashboard():
    """Get comprehensive CFO dashboard with financial analytics"""
    
    today = datetime.now(timezone.utc).date()
    month_start = today.replace(day=1)
    three_months_ago = today - timedelta(days=90)
    six_months_ago = today - timedelta(days=180)
    
    # Get all data
    branches = await branches_col().find({"is_active": True}, {"_id": 0}).to_list(length=100)
    employees = await employees_col().find({"status": "active"}, {"_id": 0}).to_list(length=500)
    
    # Sales data
    sales_today = await sales_col().find({
        "created_at": {"$gte": f"{today}T00:00:00"}
    }, {"_id": 0}).to_list(length=1000)
    
    sales_month = await sales_col().find({
        "created_at": {"$gte": f"{month_start}T00:00:00"}
    }, {"_id": 0}).to_list(length=10000)
    
    # Calculate revenue
    revenue_today = sum(s.get("total", 0) for s in sales_today)
    revenue_month = sum(s.get("total", 0) for s in sales_month)
    
    # Calculate COGS (simplified - 70% of revenue)
    cogs_today = revenue_today * 0.7
    cogs_month = revenue_month * 0.7
    
    # Payroll calculation
    total_payroll_month = 0
    employees_monthly = 0
    employees_daily = 0
    
    for emp in employees:
        salary_type = emp.get("salary_type", "monthly")
        gaji_pokok = emp.get("gaji_pokok", 0)
        upah_harian = emp.get("upah_harian", 0)
        tunjangan = emp.get("tunjangan_total", 0)
        
        if salary_type == "daily":
            # Estimate 26 working days
            monthly_salary = (upah_harian * 26) + tunjangan
            employees_daily += 1
        else:
            monthly_salary = gaji_pokok + tunjangan
            employees_monthly += 1
        
        total_payroll_month += monthly_salary
    
    # Operating expenses (estimate 10% of revenue)
    operating_expenses = revenue_month * 0.1
    
    # Calculate P&L
    gross_profit_today = revenue_today - cogs_today
    gross_profit_month = revenue_month - cogs_month
    
    net_profit_today = gross_profit_today - (total_payroll_month / 30) - (operating_expenses / 30)
    net_profit_month = gross_profit_month - total_payroll_month - operating_expenses
    
    # Payroll ratio
    payroll_ratio = (total_payroll_month / revenue_month * 100) if revenue_month > 0 else 0
    
    # Branch analysis
    branch_profitability = []
    most_profitable = None
    least_profitable = None
    
    for branch in branches:
        branch_id = branch.get("id")
        branch_name = branch.get("name", "Unknown")
        
        # Branch sales
        branch_sales = [s for s in sales_month if s.get("branch_id") == branch_id]
        branch_revenue = sum(s.get("total", 0) for s in branch_sales)
        
        # Branch employees payroll
        branch_employees = [e for e in employees if e.get("branch_id") == branch_id]
        branch_payroll = sum(e.get("gaji_pokok", 0) + e.get("tunjangan_total", 0) for e in branch_employees)
        
        # Branch profit (simplified)
        branch_cogs = branch_revenue * 0.7
        branch_opex = branch_revenue * 0.1
        branch_profit = branch_revenue - branch_cogs - branch_payroll - branch_opex
        
        branch_data = {
            "branch_id": branch_id,
            "branch_name": branch_name,
            "revenue": branch_revenue,
            "payroll": branch_payroll,
            "employee_count": len(branch_employees),
            "profit": branch_profit,
            "profit_margin": (branch_profit / branch_revenue * 100) if branch_revenue > 0 else 0
        }
        
        branch_profitability.append(branch_data)
    
    # Sort branches
    branch_profitability.sort(key=lambda x: x["profit"], reverse=True)
    
    if branch_profitability:
        most_profitable = branch_profitability[0]
        least_profitable = branch_profitability[-1]
    
    # Ideal employee calculation per branch
    ideal_employees = []
    for bp in branch_profitability:
        revenue = bp["revenue"]
        current_employees = bp["employee_count"]
        
        # Rule: 1 employee per 5 million revenue
        ideal = max(1, int(revenue / 5000000))
        diff = current_employees - ideal
        
        recommendation = ""
        if diff > 1:
            recommendation = f"Kurangi {diff} karyawan"
        elif diff < -1:
            recommendation = f"Tambah {abs(diff)} karyawan"
        else:
            recommendation = "Jumlah ideal"
        
        ideal_employees.append({
            "branch_name": bp["branch_name"],
            "current": current_employees,
            "ideal": ideal,
            "difference": diff,
            "recommendation": recommendation
        })
    
    return {
        "summary": {
            "revenue_today": revenue_today,
            "revenue_month": revenue_month,
            "gross_profit_today": gross_profit_today,
            "gross_profit_month": gross_profit_month,
            "net_profit_today": net_profit_today,
            "net_profit_month": net_profit_month,
            "total_payroll": total_payroll_month,
            "payroll_ratio": round(payroll_ratio, 2),
            "operating_expenses": operating_expenses,
            "employees_monthly": employees_monthly,
            "employees_daily": employees_daily,
            "total_employees": len(employees)
        },
        "most_profitable_branch": most_profitable,
        "least_profitable_branch": least_profitable,
        "branch_profitability": branch_profitability[:10],
        "ideal_employees": ideal_employees,
        "generated_at": now_iso()
    }


@router.get("/profit-loss")
async def get_profit_loss(
    period: str = "month",
    branch_id: Optional[str] = None
):
    """Get detailed profit & loss statement"""
    
    today = datetime.now(timezone.utc).date()
    
    if period == "day":
        start_date = today
    elif period == "week":
        start_date = today - timedelta(days=7)
    elif period == "month":
        start_date = today.replace(day=1)
    elif period == "quarter":
        start_date = today - timedelta(days=90)
    else:
        start_date = today.replace(day=1)
    
    # Build query
    query = {"created_at": {"$gte": f"{start_date}T00:00:00"}}
    if branch_id:
        query["branch_id"] = branch_id
    
    # Get sales
    sales = await sales_col().find(query, {"_id": 0}).to_list(length=10000)
    
    # Get employees for payroll
    emp_query = {"status": "active"}
    if branch_id:
        emp_query["branch_id"] = branch_id
    employees = await employees_col().find(emp_query, {"_id": 0}).to_list(length=500)
    
    # Calculate
    total_revenue = sum(s.get("total", 0) for s in sales)
    total_cogs = total_revenue * 0.7  # Simplified HPP
    gross_profit = total_revenue - total_cogs
    
    # Payroll (prorate based on period)
    total_payroll = sum(e.get("gaji_pokok", 0) + e.get("tunjangan_total", 0) for e in employees)
    days_in_period = (today - start_date).days + 1
    prorated_payroll = total_payroll * (days_in_period / 30)
    
    # Operating expenses
    operating_expenses = total_revenue * 0.1
    
    # Other expenses
    other_expenses = total_revenue * 0.02
    
    # Net profit
    total_expenses = prorated_payroll + operating_expenses + other_expenses
    net_profit = gross_profit - total_expenses
    
    # By category (if available)
    by_category = {}
    for s in sales:
        cat = s.get("category", "Umum")
        if cat not in by_category:
            by_category[cat] = {"revenue": 0, "count": 0}
        by_category[cat]["revenue"] += s.get("total", 0)
        by_category[cat]["count"] += 1
    
    return {
        "period": period,
        "start_date": str(start_date),
        "end_date": str(today),
        "days": days_in_period,
        "revenue": {
            "total": total_revenue,
            "by_category": by_category
        },
        "cost_of_goods_sold": total_cogs,
        "gross_profit": gross_profit,
        "gross_margin": round((gross_profit / total_revenue * 100) if total_revenue > 0 else 0, 2),
        "expenses": {
            "payroll": prorated_payroll,
            "operating": operating_expenses,
            "other": other_expenses,
            "total": total_expenses
        },
        "net_profit": net_profit,
        "net_margin": round((net_profit / total_revenue * 100) if total_revenue > 0 else 0, 2),
        "generated_at": now_iso()
    }


@router.get("/cash-flow")
async def get_cash_flow_analysis(
    period: str = "month",
    branch_id: Optional[str] = None
):
    """Get cash flow analysis with predictions"""
    
    today = datetime.now(timezone.utc).date()
    
    if period == "day":
        start_date = today
        days = 1
    elif period == "week":
        start_date = today - timedelta(days=7)
        days = 7
    elif period == "month":
        start_date = today.replace(day=1)
        days = (today - start_date).days + 1
    else:
        start_date = today.replace(day=1)
        days = 30
    
    query = {"created_at": {"$gte": f"{start_date}T00:00:00"}}
    if branch_id:
        query["branch_id"] = branch_id
    
    # Cash inflows (sales)
    sales = await sales_col().find(query, {"_id": 0}).to_list(length=10000)
    total_inflow = sum(s.get("total", 0) for s in sales)
    
    # Cash outflows (estimated)
    emp_query = {"status": "active"}
    if branch_id:
        emp_query["branch_id"] = branch_id
    employees = await employees_col().find(emp_query, {"_id": 0}).to_list(length=500)
    
    # Payroll outflow (prorated)
    total_payroll = sum(e.get("gaji_pokok", 0) + e.get("tunjangan_total", 0) for e in employees)
    payroll_outflow = total_payroll * (days / 30)
    
    # Purchases/COGS outflow
    cogs_outflow = total_inflow * 0.7
    
    # Operating outflow
    operating_outflow = total_inflow * 0.1
    
    total_outflow = payroll_outflow + cogs_outflow + operating_outflow
    net_cash_flow = total_inflow - total_outflow
    
    # Predictions (next 7 and 30 days)
    avg_daily_inflow = total_inflow / days if days > 0 else 0
    avg_daily_outflow = total_outflow / days if days > 0 else 0
    
    predicted_7_days = (avg_daily_inflow - avg_daily_outflow) * 7
    predicted_30_days = (avg_daily_inflow - avg_daily_outflow) * 30
    
    # Warnings
    warnings = []
    if net_cash_flow < 0:
        warnings.append({
            "level": "critical",
            "message": "Cash flow negatif! Segera review pengeluaran"
        })
    elif predicted_30_days < 0:
        warnings.append({
            "level": "warning",
            "message": "Prediksi cash flow 30 hari negatif"
        })
    
    if payroll_outflow > total_inflow * 0.3:
        warnings.append({
            "level": "warning",
            "message": f"Payroll ratio tinggi ({round(payroll_outflow/total_inflow*100 if total_inflow > 0 else 0)}%)"
        })
    
    # Recommendations
    recommendations = []
    if net_cash_flow < 0:
        recommendations.append("Tekan biaya operasional")
        recommendations.append("Tingkatkan penjualan")
        recommendations.append("Tunda pembelian tidak urgent")
    
    return {
        "period": period,
        "start_date": str(start_date),
        "end_date": str(today),
        "days": days,
        "inflows": {
            "sales": total_inflow,
            "other": 0,
            "total": total_inflow
        },
        "outflows": {
            "payroll": payroll_outflow,
            "purchases_cogs": cogs_outflow,
            "operating": operating_outflow,
            "other": 0,
            "total": total_outflow
        },
        "net_cash_flow": net_cash_flow,
        "predictions": {
            "next_7_days": predicted_7_days,
            "next_30_days": predicted_30_days,
            "avg_daily_net": avg_daily_inflow - avg_daily_outflow
        },
        "warnings": warnings,
        "recommendations": recommendations,
        "generated_at": now_iso()
    }


@router.get("/branch-loss-analysis")
async def analyze_loss_branches():
    """Analyze branches that are losing money"""
    
    today = datetime.now(timezone.utc).date()
    month_start = today.replace(day=1)
    
    branches = await branches_col().find({"is_active": True}, {"_id": 0}).to_list(length=100)
    employees = await employees_col().find({"status": "active"}, {"_id": 0}).to_list(length=500)
    
    sales = await sales_col().find({
        "created_at": {"$gte": f"{month_start}T00:00:00"}
    }, {"_id": 0}).to_list(length=10000)
    
    loss_branches = []
    
    for branch in branches:
        branch_id = branch.get("id")
        branch_name = branch.get("name", "Unknown")
        
        # Revenue
        branch_sales = [s for s in sales if s.get("branch_id") == branch_id]
        revenue = sum(s.get("total", 0) for s in branch_sales)
        
        # Costs
        branch_employees = [e for e in employees if e.get("branch_id") == branch_id]
        payroll = sum(e.get("gaji_pokok", 0) + e.get("tunjangan_total", 0) for e in branch_employees)
        
        cogs = revenue * 0.7
        operating = revenue * 0.1
        
        # Profit calculation
        total_cost = cogs + payroll + operating
        profit = revenue - total_cost
        margin = (profit / revenue * 100) if revenue > 0 else -100
        
        # Identify loss causes
        loss_causes = []
        
        if revenue < 5000000:
            loss_causes.append({
                "cause": "Penjualan rendah",
                "detail": f"Revenue: Rp {revenue:,.0f}",
                "impact": "high"
            })
        
        if payroll > revenue * 0.25:
            loss_causes.append({
                "cause": "Payroll terlalu besar",
                "detail": f"Payroll ratio: {payroll/revenue*100 if revenue > 0 else 100:.1f}%",
                "impact": "high"
            })
        
        if len(branch_employees) > 0 and revenue / len(branch_employees) < 3000000:
            loss_causes.append({
                "cause": "Produktivitas karyawan rendah",
                "detail": f"Revenue per karyawan: Rp {revenue/len(branch_employees):,.0f}",
                "impact": "medium"
            })
        
        # Determine status
        if profit < -2000000:
            status = "rugi_berat"
        elif profit < 0:
            status = "rugi_ringan"
        elif margin < 5:
            status = "perlu_perhatian"
        else:
            status = "sehat"
        
        # Recommendations
        recommendations = []
        if profit < 0:
            if payroll > revenue * 0.25:
                recommendations.append("Efisiensi karyawan")
            if revenue < 5000000:
                recommendations.append("Push sales dan promo")
            recommendations.append("Review struktur biaya")
        
        branch_data = {
            "branch_id": branch_id,
            "branch_name": branch_name,
            "revenue": revenue,
            "total_cost": total_cost,
            "profit": profit,
            "margin": round(margin, 2),
            "payroll": payroll,
            "payroll_ratio": round((payroll / revenue * 100) if revenue > 0 else 100, 2),
            "employee_count": len(branch_employees),
            "status": status,
            "loss_causes": loss_causes,
            "recommendations": recommendations
        }
        
        if profit < 0 or status in ["rugi_berat", "rugi_ringan", "perlu_perhatian"]:
            loss_branches.append(branch_data)
    
    # Sort by profit (most loss first)
    loss_branches.sort(key=lambda x: x["profit"])
    
    return {
        "total_branches": len(branches),
        "loss_branches_count": len(loss_branches),
        "total_loss": sum(b["profit"] for b in loss_branches if b["profit"] < 0),
        "branches": loss_branches,
        "summary": {
            "rugi_berat": len([b for b in loss_branches if b["status"] == "rugi_berat"]),
            "rugi_ringan": len([b for b in loss_branches if b["status"] == "rugi_ringan"]),
            "perlu_perhatian": len([b for b in loss_branches if b["status"] == "perlu_perhatian"])
        },
        "generated_at": now_iso()
    }


@router.get("/employee-efficiency")
async def analyze_employee_efficiency(
    analysis_period: str = "3months"
):
    """Analyze employee efficiency and ideal headcount per branch"""
    
    today = datetime.now(timezone.utc).date()
    
    if analysis_period == "3months":
        start_date = today - timedelta(days=90)
        period_days = 90
    elif analysis_period == "6months":
        start_date = today - timedelta(days=180)
        period_days = 180
    else:
        start_date = today - timedelta(days=90)
        period_days = 90
    
    branches = await branches_col().find({"is_active": True}, {"_id": 0}).to_list(length=100)
    employees = await employees_col().find({"status": "active"}, {"_id": 0}).to_list(length=500)
    
    sales = await sales_col().find({
        "created_at": {"$gte": f"{start_date}T00:00:00"}
    }, {"_id": 0}).to_list(length=50000)
    
    analysis = []
    
    for branch in branches:
        branch_id = branch.get("id")
        branch_name = branch.get("name", "Unknown")
        
        # Get branch data
        branch_sales = [s for s in sales if s.get("branch_id") == branch_id]
        total_revenue = sum(s.get("total", 0) for s in branch_sales)
        total_transactions = len(branch_sales)
        
        # Monthly average
        monthly_revenue = total_revenue / (period_days / 30)
        monthly_transactions = total_transactions / (period_days / 30)
        
        # Current employees
        branch_employees = [e for e in employees if e.get("branch_id") == branch_id]
        current_count = len(branch_employees)
        
        total_payroll = sum(e.get("gaji_pokok", 0) + e.get("tunjangan_total", 0) for e in branch_employees)
        
        # Calculate ideal employees
        # Rule: 1 employee per 5 million monthly revenue
        # Minimum 1, consider transactions too (1 per 200 transactions/month)
        ideal_by_revenue = max(1, int(monthly_revenue / 5000000))
        ideal_by_transactions = max(1, int(monthly_transactions / 200))
        ideal_count = max(ideal_by_revenue, ideal_by_transactions)
        
        # Calculate metrics
        revenue_per_employee = monthly_revenue / current_count if current_count > 0 else 0
        transactions_per_employee = monthly_transactions / current_count if current_count > 0 else 0
        payroll_ratio = (total_payroll / monthly_revenue * 100) if monthly_revenue > 0 else 100
        
        # Difference
        difference = current_count - ideal_count
        
        # Status and recommendation
        if difference >= 2:
            status = "kelebihan"
            recommendation = f"Kurangi {difference} karyawan atau rotasi ke cabang lain"
        elif difference <= -2:
            status = "kekurangan"
            recommendation = f"Tambah {abs(difference)} karyawan untuk support beban kerja"
        else:
            status = "ideal"
            recommendation = "Jumlah karyawan sudah ideal"
        
        # Efficiency score (0-100)
        efficiency_score = min(100, max(0, 100 - abs(difference) * 10 - max(0, payroll_ratio - 25)))
        
        analysis.append({
            "branch_id": branch_id,
            "branch_name": branch_name,
            "analysis_period": analysis_period,
            "period_days": period_days,
            "metrics": {
                "total_revenue": total_revenue,
                "monthly_revenue": round(monthly_revenue),
                "monthly_transactions": round(monthly_transactions),
                "total_payroll": total_payroll,
                "payroll_ratio": round(payroll_ratio, 2),
                "revenue_per_employee": round(revenue_per_employee),
                "transactions_per_employee": round(transactions_per_employee)
            },
            "headcount": {
                "current": current_count,
                "ideal": ideal_count,
                "difference": difference
            },
            "status": status,
            "efficiency_score": round(efficiency_score),
            "recommendation": recommendation
        })
    
    # Sort by efficiency score
    analysis.sort(key=lambda x: x["efficiency_score"])
    
    # Summary
    total_current = sum(a["headcount"]["current"] for a in analysis)
    total_ideal = sum(a["headcount"]["ideal"] for a in analysis)
    
    return {
        "analysis_period": analysis_period,
        "period_days": period_days,
        "summary": {
            "total_branches": len(branches),
            "total_current_employees": total_current,
            "total_ideal_employees": total_ideal,
            "overstaffed_branches": len([a for a in analysis if a["status"] == "kelebihan"]),
            "understaffed_branches": len([a for a in analysis if a["status"] == "kekurangan"]),
            "optimal_branches": len([a for a in analysis if a["status"] == "ideal"]),
            "potential_efficiency": total_current - total_ideal
        },
        "branches": analysis,
        "generated_at": now_iso()
    }


@router.get("/trend-analysis")
async def get_trend_analysis(
    period: str = "3months",
    metric: str = "all"
):
    """Get trend analysis for various metrics over time"""
    
    today = datetime.now(timezone.utc).date()
    
    if period == "3months":
        start_date = today - timedelta(days=90)
        group_by = "week"
    elif period == "6months":
        start_date = today - timedelta(days=180)
        group_by = "month"
    else:
        start_date = today - timedelta(days=90)
        group_by = "week"
    
    # Get sales data
    sales = await sales_col().find({
        "created_at": {"$gte": f"{start_date}T00:00:00"}
    }, {"_id": 0}).to_list(length=50000)
    
    # Group sales by period
    sales_trend = {}
    for s in sales:
        date_str = s.get("created_at", "")[:10]
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
            if group_by == "week":
                key = date.strftime("%Y-W%W")
            else:
                key = date.strftime("%Y-%m")
            
            if key not in sales_trend:
                sales_trend[key] = {"revenue": 0, "transactions": 0}
            sales_trend[key]["revenue"] += s.get("total", 0)
            sales_trend[key]["transactions"] += 1
        except:
            continue
    
    # Convert to list and sort
    trend_data = [
        {
            "period": k,
            "revenue": v["revenue"],
            "transactions": v["transactions"],
            "avg_transaction": v["revenue"] / v["transactions"] if v["transactions"] > 0 else 0
        }
        for k, v in sorted(sales_trend.items())
    ]
    
    # Calculate trend direction
    if len(trend_data) >= 2:
        recent = trend_data[-1]["revenue"]
        previous = trend_data[-2]["revenue"]
        growth_rate = ((recent - previous) / previous * 100) if previous > 0 else 0
        trend_direction = "up" if growth_rate > 0 else "down" if growth_rate < 0 else "stable"
    else:
        growth_rate = 0
        trend_direction = "insufficient_data"
    
    return {
        "period": period,
        "group_by": group_by,
        "trend_data": trend_data,
        "summary": {
            "total_revenue": sum(t["revenue"] for t in trend_data),
            "total_transactions": sum(t["transactions"] for t in trend_data),
            "avg_period_revenue": sum(t["revenue"] for t in trend_data) / len(trend_data) if trend_data else 0,
            "growth_rate": round(growth_rate, 2),
            "trend_direction": trend_direction
        },
        "generated_at": now_iso()
    }
