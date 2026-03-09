# OCB GROUP SUPER AI - AI CFO Routes
# Financial analysis and recommendations

from fastapi import APIRouter, HTTPException
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import uuid

from database import get_db

router = APIRouter(prefix="/api/ai-cfo", tags=["AI CFO"])

def gen_id() -> str:
    return str(uuid.uuid4())

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

# ==================== AI CFO ENDPOINTS ====================

@router.get("/summary")
async def get_financial_summary(period: str = "month"):
    """Get comprehensive financial summary"""
    db = get_db()
    
    now = datetime.now(timezone.utc)
    
    if period == "today":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        prev_start = start_date - timedelta(days=1)
        prev_end = start_date
    elif period == "week":
        start_date = now - timedelta(days=7)
        prev_start = start_date - timedelta(days=7)
        prev_end = start_date
    elif period == "month":
        start_date = now - timedelta(days=30)
        prev_start = start_date - timedelta(days=30)
        prev_end = start_date
    else:
        start_date = now - timedelta(days=365)
        prev_start = start_date - timedelta(days=365)
        prev_end = start_date
    
    # Current period transactions
    transactions = await db['transactions'].find({
        "created_at": {"$gte": start_date.isoformat()},
        "status": "completed"
    }, {"_id": 0}).to_list(None)
    
    # Previous period transactions
    prev_transactions = await db['transactions'].find({
        "created_at": {"$gte": prev_start.isoformat(), "$lt": prev_end.isoformat()},
        "status": "completed"
    }, {"_id": 0}).to_list(None)
    
    # Calculate current period
    gross_revenue = sum(t.get("total", 0) for t in transactions)
    cost_of_goods = sum(t.get("total_cost", 0) for t in transactions)
    discount_total = sum(t.get("discount_amount", 0) for t in transactions)
    tax_total = sum(t.get("tax_amount", 0) for t in transactions)
    
    gross_profit = gross_revenue - cost_of_goods
    gross_margin = (gross_profit / gross_revenue * 100) if gross_revenue > 0 else 0
    
    # Get expenses
    expenses = await db['expenses'].find({
        "created_at": {"$gte": start_date.isoformat()}
    }, {"_id": 0}).to_list(None)
    
    operating_expenses = sum(e.get("amount", 0) for e in expenses)
    net_profit = gross_profit - operating_expenses
    net_margin = (net_profit / gross_revenue * 100) if gross_revenue > 0 else 0
    
    # Previous period
    prev_revenue = sum(t.get("total", 0) for t in prev_transactions)
    revenue_growth = ((gross_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0
    
    # Cash flow
    cash_in = await db['cash_movements'].find({
        "created_at": {"$gte": start_date.isoformat()},
        "movement_type": "cash_in"
    }).to_list(None)
    
    cash_out = await db['cash_movements'].find({
        "created_at": {"$gte": start_date.isoformat()},
        "movement_type": "cash_out"
    }).to_list(None)
    
    total_cash_in = sum(c.get("amount", 0) for c in cash_in)
    total_cash_out = sum(c.get("amount", 0) for c in cash_out)
    
    # Receivables & Payables
    customers_with_debt = await db['customers'].find(
        {"credit_balance": {"$gt": 0}},
        {"_id": 0, "credit_balance": 1}
    ).to_list(None)
    
    suppliers_debt = await db['suppliers'].find(
        {"debt_balance": {"$gt": 0}},
        {"_id": 0, "debt_balance": 1}
    ).to_list(None)
    
    accounts_receivable = sum(c.get("credit_balance", 0) for c in customers_with_debt)
    accounts_payable = sum(s.get("debt_balance", 0) for s in suppliers_debt)
    
    # Unique customers
    customer_ids = set(t.get("customer_id") for t in transactions if t.get("customer_id"))
    
    return {
        "period": period,
        "period_start": start_date.isoformat(),
        "period_end": now.isoformat(),
        
        # Revenue
        "gross_revenue": gross_revenue,
        "discounts": discount_total,
        "taxes": tax_total,
        "net_revenue": gross_revenue - discount_total,
        
        # Costs
        "cost_of_goods": cost_of_goods,
        "operating_expenses": operating_expenses,
        
        # Profit
        "gross_profit": gross_profit,
        "gross_margin_percent": round(gross_margin, 2),
        "net_profit": net_profit,
        "net_margin_percent": round(net_margin, 2),
        
        # Cash Flow
        "cash_in": total_cash_in,
        "cash_out": total_cash_out,
        "net_cash_flow": total_cash_in - total_cash_out,
        
        # Receivables & Payables
        "accounts_receivable": accounts_receivable,
        "accounts_payable": accounts_payable,
        
        # Metrics
        "transaction_count": len(transactions),
        "average_transaction": gross_revenue / len(transactions) if transactions else 0,
        "customer_count": len(customer_ids),
        
        # Growth
        "prev_period_revenue": prev_revenue,
        "revenue_growth_percent": round(revenue_growth, 2)
    }

@router.get("/profit-analysis")
async def get_profit_analysis():
    """Analyze profit by category, product, and branch"""
    db = get_db()
    
    # Last 30 days
    start_date = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    
    transactions = await db['transactions'].find({
        "created_at": {"$gte": start_date},
        "status": "completed"
    }, {"_id": 0}).to_list(None)
    
    # Product profit analysis
    product_profit = {}
    branch_profit = {}
    
    for t in transactions:
        branch_id = t.get("branch_id", "unknown")
        
        if branch_id not in branch_profit:
            branch_profit[branch_id] = {"revenue": 0, "cost": 0, "profit": 0, "count": 0}
        
        branch_profit[branch_id]["revenue"] += t.get("total", 0)
        branch_profit[branch_id]["cost"] += t.get("total_cost", 0)
        branch_profit[branch_id]["profit"] += t.get("profit", t.get("total", 0) - t.get("total_cost", 0))
        branch_profit[branch_id]["count"] += 1
        
        for item in t.get("items", []):
            product_id = item.get("product_id", "unknown")
            
            if product_id not in product_profit:
                product_profit[product_id] = {
                    "product_name": item.get("product_name", ""),
                    "revenue": 0,
                    "cost": 0,
                    "profit": 0,
                    "qty": 0
                }
            
            revenue = item.get("total", item.get("subtotal", 0))
            cost = item.get("cost_price", 0) * item.get("quantity", 0)
            
            product_profit[product_id]["revenue"] += revenue
            product_profit[product_id]["cost"] += cost
            product_profit[product_id]["profit"] += revenue - cost
            product_profit[product_id]["qty"] += item.get("quantity", 0)
    
    # Get branch names
    branches = await db['branches'].find({}, {"_id": 0, "id": 1, "name": 1}).to_list(None)
    branch_map = {b["id"]: b["name"] for b in branches}
    
    # Format branch profit
    branch_analysis = []
    for branch_id, data in branch_profit.items():
        margin = (data["profit"] / data["revenue"] * 100) if data["revenue"] > 0 else 0
        branch_analysis.append({
            "branch_id": branch_id,
            "branch_name": branch_map.get(branch_id, "Unknown"),
            "revenue": data["revenue"],
            "cost": data["cost"],
            "profit": data["profit"],
            "margin_percent": round(margin, 2),
            "transactions": data["count"]
        })
    
    # Sort by profit
    branch_analysis = sorted(branch_analysis, key=lambda x: x["profit"], reverse=True)
    
    # Format product profit
    product_analysis = []
    for product_id, data in product_profit.items():
        margin = (data["profit"] / data["revenue"] * 100) if data["revenue"] > 0 else 0
        product_analysis.append({
            "product_id": product_id,
            "product_name": data["product_name"],
            "revenue": data["revenue"],
            "cost": data["cost"],
            "profit": data["profit"],
            "margin_percent": round(margin, 2),
            "quantity_sold": data["qty"]
        })
    
    # Sort by profit
    product_analysis = sorted(product_analysis, key=lambda x: x["profit"], reverse=True)
    
    return {
        "period": "last_30_days",
        "top_profit_branches": branch_analysis[:10],
        "low_profit_branches": branch_analysis[-10:] if len(branch_analysis) > 10 else [],
        "top_profit_products": product_analysis[:10],
        "low_profit_products": [p for p in product_analysis if p["profit"] < 0][:10]
    }

@router.get("/cashflow")
async def get_cashflow_report(period: str = "month"):
    """Get detailed cash flow report"""
    db = get_db()
    
    now = datetime.now(timezone.utc)
    if period == "week":
        start_date = now - timedelta(days=7)
    elif period == "month":
        start_date = now - timedelta(days=30)
    else:
        start_date = now - timedelta(days=365)
    
    # Get cash movements
    cash_movements = await db['cash_movements'].find({
        "created_at": {"$gte": start_date.isoformat()}
    }, {"_id": 0}).sort("created_at", -1).to_list(None)
    
    # Categorize
    categories = {}
    for movement in cash_movements:
        category = movement.get("category", "other")
        movement_type = movement.get("movement_type", "other")
        
        key = f"{movement_type}_{category}"
        if key not in categories:
            categories[key] = {
                "type": movement_type,
                "category": category,
                "total": 0,
                "count": 0
            }
        
        categories[key]["total"] += movement.get("amount", 0)
        categories[key]["count"] += 1
    
    # Calculate totals
    total_in = sum(c["total"] for c in categories.values() if c["type"] == "cash_in")
    total_out = sum(c["total"] for c in categories.values() if c["type"] == "cash_out")
    
    # Daily breakdown
    daily = {}
    for movement in cash_movements:
        date = movement.get("created_at", "")[:10]
        if date not in daily:
            daily[date] = {"date": date, "cash_in": 0, "cash_out": 0}
        
        if movement.get("movement_type") == "cash_in":
            daily[date]["cash_in"] += movement.get("amount", 0)
        else:
            daily[date]["cash_out"] += movement.get("amount", 0)
    
    daily_data = sorted(daily.values(), key=lambda x: x["date"])
    
    return {
        "period": period,
        "total_cash_in": total_in,
        "total_cash_out": total_out,
        "net_cash_flow": total_in - total_out,
        "categories": list(categories.values()),
        "daily_breakdown": daily_data,
        "recent_movements": cash_movements[:20]
    }

@router.get("/receivables")
async def get_receivables_report():
    """Get accounts receivable (piutang) report"""
    db = get_db()
    
    # Customers with credit balance
    customers = await db['customers'].find(
        {"credit_balance": {"$gt": 0}},
        {"_id": 0}
    ).sort("credit_balance", -1).to_list(None)
    
    total_receivable = sum(c.get("credit_balance", 0) for c in customers)
    
    return {
        "total_receivable": total_receivable,
        "customer_count": len(customers),
        "customers": customers[:50],
        "top_debtors": customers[:10]
    }

@router.get("/payables")
async def get_payables_report():
    """Get accounts payable (hutang) report"""
    db = get_db()
    
    # Suppliers with debt balance
    suppliers = await db['suppliers'].find(
        {"debt_balance": {"$gt": 0}},
        {"_id": 0}
    ).sort("debt_balance", -1).to_list(None)
    
    total_payable = sum(s.get("debt_balance", 0) for s in suppliers)
    
    return {
        "total_payable": total_payable,
        "supplier_count": len(suppliers),
        "suppliers": suppliers[:50]
    }

@router.get("/recommendations")
async def get_ai_recommendations():
    """Get AI-powered financial recommendations"""
    db = get_db()
    
    recommendations = []
    
    # Get financial summary
    summary = await get_financial_summary("month")
    
    # Revenue recommendations
    if summary["revenue_growth_percent"] < 0:
        recommendations.append({
            "type": "revenue",
            "priority": "high",
            "title": "Penurunan Revenue Terdeteksi",
            "description": f"Revenue turun {abs(summary['revenue_growth_percent']):.1f}% dibanding periode sebelumnya.",
            "action": "Pertimbangkan kampanye promosi atau review strategi harga."
        })
    
    # Margin recommendations
    if summary["gross_margin_percent"] < 20:
        recommendations.append({
            "type": "margin",
            "priority": "high",
            "title": "Margin Rendah",
            "description": f"Gross margin hanya {summary['gross_margin_percent']:.1f}%.",
            "action": "Review harga jual produk atau cari supplier dengan harga lebih baik."
        })
    
    # Cash flow recommendations
    if summary["net_cash_flow"] < 0:
        recommendations.append({
            "type": "cashflow",
            "priority": "high",
            "title": "Cash Flow Negatif",
            "description": f"Cash out lebih besar dari cash in sebesar Rp {abs(summary['net_cash_flow']):,.0f}.",
            "action": "Percepat penagihan piutang dan tunda pembelian non-esensial."
        })
    
    # Receivables recommendations
    if summary["accounts_receivable"] > summary["gross_revenue"] * 0.3:
        recommendations.append({
            "type": "receivables",
            "priority": "medium",
            "title": "Piutang Tinggi",
            "description": f"Total piutang Rp {summary['accounts_receivable']:,.0f} (>30% revenue).",
            "action": "Tingkatkan penagihan dan review kebijakan kredit."
        })
    
    # Get low performing products
    profit_analysis = await get_profit_analysis()
    low_profit_products = profit_analysis.get("low_profit_products", [])
    
    if low_profit_products:
        recommendations.append({
            "type": "product",
            "priority": "medium",
            "title": f"{len(low_profit_products)} Produk dengan Profit Negatif",
            "description": "Beberapa produk menghasilkan kerugian.",
            "action": "Review harga atau pertimbangkan untuk menghentikan produk tersebut.",
            "details": [p["product_name"] for p in low_profit_products[:5]]
        })
    
    # Stock value vs revenue
    stock_overview = await db['product_stocks'].aggregate([
        {"$lookup": {
            "from": "products",
            "localField": "product_id",
            "foreignField": "id",
            "as": "product"
        }},
        {"$unwind": "$product"},
        {"$group": {
            "_id": None,
            "total_value": {"$sum": {"$multiply": ["$quantity", "$product.selling_price"]}}
        }}
    ]).to_list(None)
    
    if stock_overview:
        stock_value = stock_overview[0].get("total_value", 0)
        if stock_value > summary["gross_revenue"] * 2:
            recommendations.append({
                "type": "inventory",
                "priority": "medium",
                "title": "Nilai Inventory Tinggi",
                "description": f"Total nilai stok Rp {stock_value:,.0f} (>2x revenue bulanan).",
                "action": "Optimalkan inventory turnover dengan promosi atau kurangi pembelian."
            })
    
    # Default positive recommendation
    if not recommendations:
        recommendations.append({
            "type": "general",
            "priority": "info",
            "title": "Keuangan Sehat",
            "description": "Tidak ada masalah keuangan yang terdeteksi.",
            "action": "Pertahankan performa dan pertimbangkan ekspansi."
        })
    
    return {
        "recommendations": recommendations,
        "total_recommendations": len(recommendations),
        "high_priority_count": len([r for r in recommendations if r["priority"] == "high"]),
        "generated_at": now_iso()
    }
