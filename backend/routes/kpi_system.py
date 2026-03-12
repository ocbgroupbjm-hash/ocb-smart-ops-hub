"""
OCB TITAN ERP - PHASE 5 KPI SYSTEM
Following OCB TITAN AI MASTER LAW - NON-DESTRUCTIVE Development

KPI Categories:
1. Branch Performance - omzet, margin, setoran, shortage/overage, target achievement
2. Sales Performance - target, actual, achievement, commission, ranking
3. Inventory Performance - low stock, dead stock, slow moving, reorder pending, stock value
4. Finance Performance - AR/AP aging, cash position, profit, branch profitability
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
from database import get_db as get_database
from routes.auth import get_current_user
import uuid

router = APIRouter(prefix="/api/kpi", tags=["KPI System"])

# ==================== HELPER FUNCTIONS ====================

def get_period_dates(period: str = "month"):
    """Get start and end dates for a period"""
    now = datetime.now(timezone.utc)
    
    if period == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
    elif period == "week":
        start = now - timedelta(days=now.weekday())
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
    elif period == "month":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end = now
    elif period == "quarter":
        quarter_month = ((now.month - 1) // 3) * 3 + 1
        start = now.replace(month=quarter_month, day=1, hour=0, minute=0, second=0, microsecond=0)
        end = now
    elif period == "year":
        start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end = now
    else:
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end = now
    
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")

async def get_branch_sales(db, branch_id: str, start_date: str, end_date: str) -> Dict:
    """Get sales data for a branch"""
    query = {
        "branch_id": branch_id,
        "transaction_date": {"$gte": start_date, "$lte": end_date},
        "status": {"$nin": ["cancelled", "void"]}
    }
    
    # Sales invoices
    invoices = await db.sales_invoices.find(query, {"_id": 0}).to_list(10000)
    invoice_total = sum(i.get("grand_total", 0) for i in invoices)
    
    # POS transactions
    pos = await db.pos_transactions.find(query, {"_id": 0}).to_list(10000)
    pos_total = sum(p.get("grand_total", 0) for p in pos)
    
    return {
        "total_sales": invoice_total + pos_total,
        "invoice_sales": invoice_total,
        "pos_sales": pos_total,
        "invoice_count": len(invoices),
        "pos_count": len(pos)
    }

# ==================== 1. KPI BRANCH PERFORMANCE ====================

@router.get("/branch/overview")
async def kpi_branch_overview(
    period: str = "month",
    user: dict = Depends(get_current_user)
):
    """Get overview KPI for all branches"""
    db = get_database()
    start_date, end_date = get_period_dates(period)
    
    branches = await db.branches.find({"is_active": {"$ne": False}}, {"_id": 0}).to_list(100)
    
    branch_kpis = []
    total_sales = 0
    total_target = 0
    
    for branch in branches:
        # Get sales
        sales_data = await get_branch_sales(db, branch["id"], start_date, end_date)
        
        # Get target
        target = await db.sales_targets.find_one({
            "target_type": "branch",
            "target_ref_id": branch["id"],
            "period_start": {"$lte": end_date},
            "period_end": {"$gte": start_date}
        }, {"_id": 0})
        
        target_value = target.get("target_value", 0) if target else 0
        achievement = (sales_data["total_sales"] / target_value * 100) if target_value > 0 else 0
        
        # Get cash control data (shortage/overage)
        shifts = await db.cashier_shifts.find({
            "branch_id": branch["id"],
            "start_time": {"$gte": start_date, "$lte": end_date + "T23:59:59"},
            "status": {"$in": ["closed", "discrepancy", "reviewed"]}
        }, {"_id": 0}).to_list(500)
        
        total_shortage = sum(abs(s.get("discrepancy", 0)) for s in shifts if s.get("discrepancy_type") == "shortage")
        total_overage = sum(abs(s.get("discrepancy", 0)) for s in shifts if s.get("discrepancy_type") == "overage")
        
        # Get deposits
        deposits = await db.cash_deposits.find({
            "branch_id": branch["id"],
            "deposited_at": {"$gte": start_date, "$lte": end_date + "T23:59:59"}
        }, {"_id": 0}).to_list(500)
        
        total_deposit = sum(d.get("deposit_amount", 0) for d in deposits)
        
        branch_kpi = {
            "branch_id": branch["id"],
            "branch_name": branch.get("name"),
            "branch_code": branch.get("code"),
            "sales": {
                "total": sales_data["total_sales"],
                "invoice": sales_data["invoice_sales"],
                "pos": sales_data["pos_sales"],
                "transaction_count": sales_data["invoice_count"] + sales_data["pos_count"]
            },
            "target": {
                "value": target_value,
                "achievement_percent": round(achievement, 1),
                "gap": target_value - sales_data["total_sales"]
            },
            "cash_control": {
                "total_deposit": total_deposit,
                "shortage": total_shortage,
                "overage": total_overage,
                "net_discrepancy": total_overage - total_shortage
            },
            "status": "achieved" if achievement >= 100 else "on_track" if achievement >= 80 else "behind"
        }
        
        branch_kpis.append(branch_kpi)
        total_sales += sales_data["total_sales"]
        total_target += target_value
    
    # Sort by sales descending
    branch_kpis.sort(key=lambda x: x["sales"]["total"], reverse=True)
    
    return {
        "period": {"start": start_date, "end": end_date, "type": period},
        "summary": {
            "total_branches": len(branches),
            "total_sales": total_sales,
            "total_target": total_target,
            "overall_achievement": round((total_sales / total_target * 100) if total_target > 0 else 0, 1),
            "achieved_count": sum(1 for b in branch_kpis if b["status"] == "achieved"),
            "on_track_count": sum(1 for b in branch_kpis if b["status"] == "on_track"),
            "behind_count": sum(1 for b in branch_kpis if b["status"] == "behind")
        },
        "branches": branch_kpis
    }

@router.get("/branch/{branch_id}")
async def kpi_branch_detail(
    branch_id: str,
    period: str = "month",
    user: dict = Depends(get_current_user)
):
    """Get detailed KPI for a specific branch"""
    db = get_database()
    start_date, end_date = get_period_dates(period)
    
    branch = await db.branches.find_one({"id": branch_id}, {"_id": 0})
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")
    
    # Sales by day
    daily_sales = {}
    
    invoices = await db.sales_invoices.find({
        "branch_id": branch_id,
        "transaction_date": {"$gte": start_date, "$lte": end_date},
        "status": {"$nin": ["cancelled", "void"]}
    }, {"_id": 0}).to_list(10000)
    
    for inv in invoices:
        date = inv.get("transaction_date", "")[:10]
        if date not in daily_sales:
            daily_sales[date] = {"invoice": 0, "pos": 0, "total": 0}
        daily_sales[date]["invoice"] += inv.get("grand_total", 0)
        daily_sales[date]["total"] += inv.get("grand_total", 0)
    
    pos_txns = await db.pos_transactions.find({
        "branch_id": branch_id,
        "transaction_date": {"$gte": start_date, "$lte": end_date},
        "status": {"$nin": ["cancelled", "void"]}
    }, {"_id": 0}).to_list(10000)
    
    for pos in pos_txns:
        date = pos.get("transaction_date", "")[:10]
        if date not in daily_sales:
            daily_sales[date] = {"invoice": 0, "pos": 0, "total": 0}
        daily_sales[date]["pos"] += pos.get("grand_total", 0)
        daily_sales[date]["total"] += pos.get("grand_total", 0)
    
    # Top products
    product_sales = {}
    for inv in invoices:
        for item in inv.get("items", []):
            pid = item.get("product_id")
            if pid not in product_sales:
                product_sales[pid] = {
                    "product_name": item.get("product_name"),
                    "qty": 0,
                    "total": 0
                }
            product_sales[pid]["qty"] += item.get("quantity", 0)
            product_sales[pid]["total"] += item.get("subtotal", 0)
    
    top_products = sorted(product_sales.values(), key=lambda x: x["total"], reverse=True)[:10]
    
    # Salesmen performance
    salesman_sales = {}
    for inv in invoices:
        sid = inv.get("sales_person_id") or inv.get("salesman_id")
        if sid:
            if sid not in salesman_sales:
                salesman_sales[sid] = {
                    "name": inv.get("salesperson_name") or inv.get("salesman_name"),
                    "total": 0,
                    "count": 0
                }
            salesman_sales[sid]["total"] += inv.get("grand_total", 0)
            salesman_sales[sid]["count"] += 1
    
    top_salesmen = sorted(salesman_sales.values(), key=lambda x: x["total"], reverse=True)[:5]
    
    total_sales = sum(d["total"] for d in daily_sales.values())
    
    return {
        "branch": {"id": branch_id, "name": branch.get("name")},
        "period": {"start": start_date, "end": end_date},
        "summary": {
            "total_sales": total_sales,
            "invoice_count": len(invoices),
            "pos_count": len(pos_txns),
            "average_daily": total_sales / max(len(daily_sales), 1)
        },
        "daily_trend": [{"date": k, **v} for k, v in sorted(daily_sales.items())],
        "top_products": top_products,
        "top_salesmen": top_salesmen
    }

# ==================== 2. KPI SALES PERFORMANCE ====================

@router.get("/sales/overview")
async def kpi_sales_overview(
    period: str = "month",
    user: dict = Depends(get_current_user)
):
    """Get overview KPI for all salesmen"""
    db = get_database()
    start_date, end_date = get_period_dates(period)
    
    # Get all salespeople
    salespeople = await db.sales_persons.find({"is_active": {"$ne": False}}, {"_id": 0}).to_list(200)
    
    sales_kpis = []
    
    for sp in salespeople:
        # Get actual sales
        invoices = await db.sales_invoices.find({
            "$or": [
                {"sales_person_id": sp["id"]},
                {"salesman_id": sp["id"]}
            ],
            "transaction_date": {"$gte": start_date, "$lte": end_date},
            "status": {"$nin": ["cancelled", "void"]}
        }, {"_id": 0}).to_list(5000)
        
        actual_sales = sum(i.get("grand_total", 0) for i in invoices)
        total_qty = sum(i.get("total_qty", 0) for i in invoices)
        
        # Get target
        target = await db.sales_targets.find_one({
            "target_type": "salesman",
            "target_ref_id": sp["id"],
            "period_start": {"$lte": end_date},
            "period_end": {"$gte": start_date}
        }, {"_id": 0})
        
        target_value = target.get("target_value", 0) if target else 0
        achievement = (actual_sales / target_value * 100) if target_value > 0 else 0
        
        # Get commission
        commissions = await db.commissions.find({
            "ref_id": sp["id"],
            "ref_type": "salesman",
            "period_start": start_date
        }, {"_id": 0}).to_list(10)
        
        total_commission = sum(c.get("total_commission", 0) for c in commissions)
        
        sales_kpi = {
            "salesman_id": sp["id"],
            "salesman_name": sp.get("name"),
            "salesman_code": sp.get("code"),
            "actual_sales": actual_sales,
            "total_qty": total_qty,
            "transaction_count": len(invoices),
            "target_value": target_value,
            "achievement_percent": round(achievement, 1),
            "gap": target_value - actual_sales,
            "commission_generated": total_commission,
            "average_transaction": actual_sales / len(invoices) if invoices else 0,
            "status": "achieved" if achievement >= 100 else "on_track" if achievement >= 80 else "behind"
        }
        
        sales_kpis.append(sales_kpi)
    
    # Sort by achievement descending (ranking)
    sales_kpis.sort(key=lambda x: x["achievement_percent"], reverse=True)
    
    # Add ranking
    for i, kpi in enumerate(sales_kpis):
        kpi["rank"] = i + 1
    
    return {
        "period": {"start": start_date, "end": end_date, "type": period},
        "summary": {
            "total_salesmen": len(salespeople),
            "total_sales": sum(s["actual_sales"] for s in sales_kpis),
            "total_target": sum(s["target_value"] for s in sales_kpis),
            "total_commission": sum(s["commission_generated"] for s in sales_kpis),
            "achieved_count": sum(1 for s in sales_kpis if s["status"] == "achieved"),
            "behind_count": sum(1 for s in sales_kpis if s["status"] == "behind")
        },
        "ranking": sales_kpis
    }

@router.get("/sales/{salesman_id}")
async def kpi_sales_detail(
    salesman_id: str,
    period: str = "month",
    user: dict = Depends(get_current_user)
):
    """Get detailed KPI for a specific salesman"""
    db = get_database()
    start_date, end_date = get_period_dates(period)
    
    salesman = await db.sales_persons.find_one({"id": salesman_id}, {"_id": 0})
    if not salesman:
        raise HTTPException(status_code=404, detail="Salesman not found")
    
    # Daily sales
    invoices = await db.sales_invoices.find({
        "$or": [
            {"sales_person_id": salesman_id},
            {"salesman_id": salesman_id}
        ],
        "transaction_date": {"$gte": start_date, "$lte": end_date},
        "status": {"$nin": ["cancelled", "void"]}
    }, {"_id": 0}).to_list(5000)
    
    daily_sales = {}
    customer_sales = {}
    
    for inv in invoices:
        date = inv.get("transaction_date", "")[:10]
        if date not in daily_sales:
            daily_sales[date] = {"total": 0, "count": 0}
        daily_sales[date]["total"] += inv.get("grand_total", 0)
        daily_sales[date]["count"] += 1
        
        # Customer breakdown
        cid = inv.get("customer_id")
        if cid:
            if cid not in customer_sales:
                customer_sales[cid] = {"name": inv.get("customer_name"), "total": 0, "count": 0}
            customer_sales[cid]["total"] += inv.get("grand_total", 0)
            customer_sales[cid]["count"] += 1
    
    top_customers = sorted(customer_sales.values(), key=lambda x: x["total"], reverse=True)[:10]
    
    return {
        "salesman": {"id": salesman_id, "name": salesman.get("name")},
        "period": {"start": start_date, "end": end_date},
        "summary": {
            "total_sales": sum(d["total"] for d in daily_sales.values()),
            "transaction_count": len(invoices),
            "working_days": len(daily_sales),
            "average_daily": sum(d["total"] for d in daily_sales.values()) / max(len(daily_sales), 1)
        },
        "daily_trend": [{"date": k, **v} for k, v in sorted(daily_sales.items())],
        "top_customers": top_customers
    }

# ==================== 3. KPI INVENTORY PERFORMANCE ====================

@router.get("/inventory/overview")
async def kpi_inventory_overview(
    user: dict = Depends(get_current_user)
):
    """Get inventory KPI overview"""
    db = get_database()
    
    # Get all products
    products = await db.products.find({"is_active": {"$ne": False}}, {"_id": 0}).to_list(5000)
    
    low_stock_items = []
    dead_stock_items = []
    slow_moving_items = []
    total_stock_value = 0
    
    # Get date 90 days ago for dead stock check
    ninety_days_ago = (datetime.now(timezone.utc) - timedelta(days=90)).strftime("%Y-%m-%d")
    thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
    
    for product in products:
        # Get stock
        stock_records = await db.stock.find({"product_id": product["id"]}, {"_id": 0}).to_list(100)
        total_stock = sum(s.get("quantity", 0) for s in stock_records)
        
        cost_price = product.get("buy_price", 0) or product.get("cost_price", 0)
        stock_value = total_stock * cost_price
        total_stock_value += stock_value
        
        min_stock = product.get("min_stock", 0)
        reorder_point = product.get("reorder_point", min_stock)
        
        # Low stock check
        if total_stock <= reorder_point and total_stock > 0:
            low_stock_items.append({
                "product_id": product["id"],
                "product_name": product.get("name"),
                "product_code": product.get("code"),
                "current_stock": total_stock,
                "min_stock": min_stock,
                "reorder_point": reorder_point,
                "stock_value": stock_value
            })
        
        # Check last sale date for dead/slow stock
        if total_stock > 0:
            last_sale = await db.sales_invoices.find_one(
                {"items.product_id": product["id"], "status": {"$nin": ["cancelled", "void"]}},
                {"_id": 0, "transaction_date": 1},
                sort=[("transaction_date", -1)]
            )
            
            last_sale_date = last_sale.get("transaction_date", "2000-01-01")[:10] if last_sale else "2000-01-01"
            
            # Dead stock: no sale in 90 days
            if last_sale_date < ninety_days_ago:
                dead_stock_items.append({
                    "product_id": product["id"],
                    "product_name": product.get("name"),
                    "product_code": product.get("code"),
                    "current_stock": total_stock,
                    "stock_value": stock_value,
                    "last_sale_date": last_sale_date,
                    "days_no_sale": (datetime.now(timezone.utc) - datetime.strptime(last_sale_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)).days
                })
            # Slow moving: no sale in 30 days
            elif last_sale_date < thirty_days_ago:
                slow_moving_items.append({
                    "product_id": product["id"],
                    "product_name": product.get("name"),
                    "product_code": product.get("code"),
                    "current_stock": total_stock,
                    "stock_value": stock_value,
                    "last_sale_date": last_sale_date,
                    "days_no_sale": (datetime.now(timezone.utc) - datetime.strptime(last_sale_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)).days
                })
    
    # Get pending reorders
    pending_reorders = await db.purchase_planning.find({
        "status": {"$in": ["draft", "reviewed", "approved"]}
    }, {"_id": 0}).to_list(500)
    
    # Stock by warehouse
    warehouses = await db.warehouses.find({"is_active": {"$ne": False}}, {"_id": 0}).to_list(50)
    warehouse_stock = []
    
    for wh in warehouses:
        wh_stocks = await db.stock.find({"warehouse_id": wh["id"]}, {"_id": 0}).to_list(5000)
        wh_value = 0
        for s in wh_stocks:
            prod = await db.products.find_one({"id": s.get("product_id")}, {"_id": 0, "buy_price": 1, "cost_price": 1})
            if prod:
                cost = prod.get("buy_price", 0) or prod.get("cost_price", 0)
                wh_value += s.get("quantity", 0) * cost
        
        warehouse_stock.append({
            "warehouse_id": wh["id"],
            "warehouse_name": wh.get("name"),
            "total_items": len(wh_stocks),
            "total_value": wh_value
        })
    
    return {
        "summary": {
            "total_products": len(products),
            "total_stock_value": total_stock_value,
            "low_stock_count": len(low_stock_items),
            "dead_stock_count": len(dead_stock_items),
            "slow_moving_count": len(slow_moving_items),
            "pending_reorder_count": len(pending_reorders),
            "dead_stock_value": sum(d["stock_value"] for d in dead_stock_items),
            "slow_moving_value": sum(s["stock_value"] for s in slow_moving_items)
        },
        "low_stock": sorted(low_stock_items, key=lambda x: x["current_stock"])[:20],
        "dead_stock": sorted(dead_stock_items, key=lambda x: x["days_no_sale"], reverse=True)[:20],
        "slow_moving": sorted(slow_moving_items, key=lambda x: x["days_no_sale"], reverse=True)[:20],
        "pending_reorders": len(pending_reorders),
        "warehouse_stock": warehouse_stock
    }

# ==================== 4. KPI FINANCE PERFORMANCE ====================

@router.get("/finance/overview")
async def kpi_finance_overview(
    period: str = "month",
    user: dict = Depends(get_current_user)
):
    """Get finance KPI overview"""
    db = get_database()
    start_date, end_date = get_period_dates(period)
    today = datetime.now(timezone.utc)
    
    # AR Aging
    ar_invoices = await db.sales_invoices.find({
        "payment_status": {"$in": ["unpaid", "partial"]},
        "status": {"$nin": ["cancelled", "void"]}
    }, {"_id": 0}).to_list(10000)
    
    ar_aging = {"current": 0, "1_30": 0, "31_60": 0, "61_90": 0, "over_90": 0}
    total_ar = 0
    
    for inv in ar_invoices:
        due_date_str = inv.get("due_date") or inv.get("transaction_date")
        if not due_date_str:
            continue
        
        try:
            due_date = datetime.strptime(due_date_str[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        
        days = (today - due_date).days
        outstanding = inv.get("grand_total", 0) - inv.get("paid_amount", 0)
        
        if outstanding <= 0:
            continue
        
        total_ar += outstanding
        
        if days <= 0:
            ar_aging["current"] += outstanding
        elif days <= 30:
            ar_aging["1_30"] += outstanding
        elif days <= 60:
            ar_aging["31_60"] += outstanding
        elif days <= 90:
            ar_aging["61_90"] += outstanding
        else:
            ar_aging["over_90"] += outstanding
    
    # AP Aging
    ap_pos = await db.purchase_orders.find({
        "payment_status": {"$in": ["unpaid", "partial"]},
        "status": {"$nin": ["cancelled", "void"]}
    }, {"_id": 0}).to_list(10000)
    
    ap_aging = {"current": 0, "1_30": 0, "31_60": 0, "61_90": 0, "over_90": 0}
    total_ap = 0
    
    for po in ap_pos:
        due_date_str = po.get("due_date") or po.get("po_date")
        if not due_date_str:
            continue
        
        try:
            due_date = datetime.strptime(due_date_str[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        
        days = (today - due_date).days
        outstanding = po.get("total_amount", 0) - po.get("paid_amount", 0)
        
        if outstanding <= 0:
            continue
        
        total_ap += outstanding
        
        if days <= 0:
            ap_aging["current"] += outstanding
        elif days <= 30:
            ap_aging["1_30"] += outstanding
        elif days <= 60:
            ap_aging["31_60"] += outstanding
        elif days <= 90:
            ap_aging["61_90"] += outstanding
        else:
            ap_aging["over_90"] += outstanding
    
    # Cash Position
    # Get today's cash from shifts
    open_shifts = await db.cashier_shifts.find({
        "status": "open"
    }, {"_id": 0}).to_list(100)
    
    cash_in_register = 0
    for shift in open_shifts:
        # Estimate cash: initial + sales
        shift_detail = await db.cashier_shifts.find_one({"id": shift["id"]}, {"_id": 0})
        initial = shift_detail.get("initial_cash", 0) if shift_detail else 0
        # We'd need to calculate expected cash, simplified here
        cash_in_register += initial
    
    # Get deposits
    recent_deposits = await db.cash_deposits.find({
        "deposited_at": {"$gte": start_date}
    }, {"_id": 0}).to_list(500)
    
    total_deposited = sum(d.get("deposit_amount", 0) for d in recent_deposits)
    
    # Profit Summary
    sales = await db.sales_invoices.find({
        "transaction_date": {"$gte": start_date, "$lte": end_date},
        "status": {"$nin": ["cancelled", "void"]}
    }, {"_id": 0}).to_list(10000)
    
    pos_sales = await db.pos_transactions.find({
        "transaction_date": {"$gte": start_date, "$lte": end_date},
        "status": {"$nin": ["cancelled", "void"]}
    }, {"_id": 0}).to_list(10000)
    
    total_revenue = sum(s.get("grand_total", 0) for s in sales) + sum(p.get("grand_total", 0) for p in pos_sales)
    
    # Simplified COGS estimation
    cogs = 0
    for s in sales:
        for item in s.get("items", []):
            prod = await db.products.find_one({"id": item.get("product_id")}, {"_id": 0, "buy_price": 1})
            if prod:
                cogs += item.get("quantity", 0) * (prod.get("buy_price", 0) or 0)
    
    gross_profit = total_revenue - cogs
    
    # Branch profitability
    branches = await db.branches.find({"is_active": {"$ne": False}}, {"_id": 0}).to_list(100)
    branch_profit = []
    
    for branch in branches:
        branch_sales = await get_branch_sales(db, branch["id"], start_date, end_date)
        branch_profit.append({
            "branch_id": branch["id"],
            "branch_name": branch.get("name"),
            "revenue": branch_sales["total_sales"],
            "estimated_profit": branch_sales["total_sales"] * 0.15  # Simplified 15% margin estimate
        })
    
    branch_profit.sort(key=lambda x: x["revenue"], reverse=True)
    
    return {
        "period": {"start": start_date, "end": end_date, "type": period},
        "ar_summary": {
            "total": total_ar,
            "aging": ar_aging,
            "overdue_percent": round((ar_aging["1_30"] + ar_aging["31_60"] + ar_aging["61_90"] + ar_aging["over_90"]) / total_ar * 100 if total_ar > 0 else 0, 1)
        },
        "ap_summary": {
            "total": total_ap,
            "aging": ap_aging,
            "overdue_percent": round((ap_aging["1_30"] + ap_aging["31_60"] + ap_aging["61_90"] + ap_aging["over_90"]) / total_ap * 100 if total_ap > 0 else 0, 1)
        },
        "cash_position": {
            "cash_in_register": cash_in_register,
            "total_deposited": total_deposited,
            "open_shifts": len(open_shifts)
        },
        "profit_summary": {
            "revenue": total_revenue,
            "cogs": cogs,
            "gross_profit": gross_profit,
            "gross_margin_percent": round((gross_profit / total_revenue * 100) if total_revenue > 0 else 0, 1)
        },
        "branch_profitability": branch_profit[:10]
    }

# ==================== KPI DASHBOARD SUMMARY ====================

@router.get("/dashboard")
async def kpi_dashboard(
    period: str = "month",
    user: dict = Depends(get_current_user)
):
    """Get unified KPI dashboard"""
    db = get_database()
    start_date, end_date = get_period_dates(period)
    
    # Quick aggregations
    branches = await db.branches.find({"is_active": {"$ne": False}}, {"_id": 0}).to_list(100)
    salespeople = await db.sales_persons.find({"is_active": {"$ne": False}}, {"_id": 0}).to_list(200)
    products = await db.products.find({"is_active": {"$ne": False}}, {"_id": 0}).to_list(5000)
    
    # Total sales
    sales = await db.sales_invoices.find({
        "transaction_date": {"$gte": start_date, "$lte": end_date},
        "status": {"$nin": ["cancelled", "void"]}
    }, {"_id": 0}).to_list(10000)
    
    pos = await db.pos_transactions.find({
        "transaction_date": {"$gte": start_date, "$lte": end_date},
        "status": {"$nin": ["cancelled", "void"]}
    }, {"_id": 0}).to_list(10000)
    
    total_sales = sum(s.get("grand_total", 0) for s in sales) + sum(p.get("grand_total", 0) for p in pos)
    
    # Get targets
    targets = await db.sales_targets.find({
        "period_start": {"$lte": end_date},
        "period_end": {"$gte": start_date}
    }, {"_id": 0}).to_list(500)
    
    total_target = sum(t.get("target_value", 0) for t in targets)
    
    # Low stock count
    low_stock_count = 0
    for p in products:
        stocks = await db.stock.find({"product_id": p["id"]}, {"_id": 0}).to_list(100)
        total_stock = sum(s.get("quantity", 0) for s in stocks)
        if total_stock <= (p.get("reorder_point", 0) or p.get("min_stock", 0)):
            low_stock_count += 1
    
    # AR/AP
    ar = await db.sales_invoices.find({
        "payment_status": {"$in": ["unpaid", "partial"]}
    }, {"_id": 0}).to_list(10000)
    total_ar = sum(i.get("grand_total", 0) - i.get("paid_amount", 0) for i in ar)
    
    ap = await db.purchase_orders.find({
        "payment_status": {"$in": ["unpaid", "partial"]}
    }, {"_id": 0}).to_list(10000)
    total_ap = sum(p.get("total_amount", 0) - p.get("paid_amount", 0) for p in ap)
    
    return {
        "period": {"start": start_date, "end": end_date, "type": period},
        "kpi_cards": [
            {
                "title": "Total Sales",
                "value": total_sales,
                "format": "currency",
                "trend": None,
                "category": "sales"
            },
            {
                "title": "Target Achievement",
                "value": round((total_sales / total_target * 100) if total_target > 0 else 0, 1),
                "format": "percent",
                "target": total_target,
                "category": "sales"
            },
            {
                "title": "Active Branches",
                "value": len(branches),
                "format": "number",
                "category": "branch"
            },
            {
                "title": "Active Salesmen",
                "value": len(salespeople),
                "format": "number",
                "category": "sales"
            },
            {
                "title": "Low Stock Items",
                "value": low_stock_count,
                "format": "number",
                "alert": low_stock_count > 10,
                "category": "inventory"
            },
            {
                "title": "Total AR",
                "value": total_ar,
                "format": "currency",
                "category": "finance"
            },
            {
                "title": "Total AP",
                "value": total_ap,
                "format": "currency",
                "category": "finance"
            },
            {
                "title": "Net Position",
                "value": total_ar - total_ap,
                "format": "currency",
                "category": "finance"
            }
        ]
    }
