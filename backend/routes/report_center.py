"""
OCB TITAN ERP - PHASE 4 BUSINESS INTELLIGENCE
REPORT CENTER - MASTER MODULE
Following OCB TITAN AI MASTER LAW - NON-DESTRUCTIVE Development

Scope:
1. Sales Reports
2. Purchase Reports
3. Inventory Reports
4. Financial Reports
5. AR/AP Aging Reports
6. Cash Flow Reports

Rules:
- Read-only queries (no data modification)
- Date range filtering
- Export capabilities (JSON format)
- Aggregation and summary statistics
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
from database import get_db as get_database
from routes.auth import get_current_user
import uuid

router = APIRouter(prefix="/api/reports", tags=["Report Center"])

# ==================== HELPER FUNCTIONS ====================

def get_date_range(period: str = "month", date_from: str = None, date_to: str = None):
    """Get date range based on period or custom dates"""
    now = datetime.now(timezone.utc)
    
    if date_from and date_to:
        return date_from, date_to
    
    if period == "today":
        start = now.strftime("%Y-%m-%d")
        end = start
    elif period == "week":
        start = (now - timedelta(days=now.weekday())).strftime("%Y-%m-%d")
        end = now.strftime("%Y-%m-%d")
    elif period == "month":
        start = now.replace(day=1).strftime("%Y-%m-%d")
        end = now.strftime("%Y-%m-%d")
    elif period == "quarter":
        quarter_start_month = ((now.month - 1) // 3) * 3 + 1
        start = now.replace(month=quarter_start_month, day=1).strftime("%Y-%m-%d")
        end = now.strftime("%Y-%m-%d")
    elif period == "year":
        start = now.replace(month=1, day=1).strftime("%Y-%m-%d")
        end = now.strftime("%Y-%m-%d")
    else:
        start = now.replace(day=1).strftime("%Y-%m-%d")
        end = now.strftime("%Y-%m-%d")
    
    return start, end

# ==================== 1. SALES REPORTS ====================

@router.get("/sales/summary")
async def sales_summary_report(
    period: str = "month",
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    branch_id: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Sales summary report with totals and trends"""
    db = get_database()
    start, end = get_date_range(period, date_from, date_to)
    
    # Base query
    query = {
        "transaction_date": {"$gte": start, "$lte": end},
        "status": {"$nin": ["cancelled", "void"]}
    }
    if branch_id:
        query["branch_id"] = branch_id
    
    # Get sales invoices
    invoices = await db.sales_invoices.find(query, {"_id": 0}).to_list(10000)
    
    # Get POS transactions
    pos_txns = await db.pos_transactions.find(query, {"_id": 0}).to_list(10000)
    
    # Combine
    total_sales = sum(i.get("grand_total", 0) for i in invoices) + sum(p.get("grand_total", 0) for p in pos_txns)
    total_qty = sum(i.get("total_qty", 0) for i in invoices) + sum(p.get("total_qty", 0) for p in pos_txns)
    total_transactions = len(invoices) + len(pos_txns)
    
    # By payment method
    by_payment = {}
    for inv in invoices:
        method = inv.get("payment_type", "unknown")
        if method not in by_payment:
            by_payment[method] = {"count": 0, "total": 0}
        by_payment[method]["count"] += 1
        by_payment[method]["total"] += inv.get("grand_total", 0)
    
    for pos in pos_txns:
        method = pos.get("payment_method", "cash")
        if method not in by_payment:
            by_payment[method] = {"count": 0, "total": 0}
        by_payment[method]["count"] += 1
        by_payment[method]["total"] += pos.get("grand_total", 0)
    
    # Daily breakdown
    daily_sales = {}
    for inv in invoices:
        date = inv.get("transaction_date", "")[:10]
        if date not in daily_sales:
            daily_sales[date] = {"invoices": 0, "pos": 0, "total": 0}
        daily_sales[date]["invoices"] += inv.get("grand_total", 0)
        daily_sales[date]["total"] += inv.get("grand_total", 0)
    
    for pos in pos_txns:
        date = pos.get("transaction_date", "")[:10]
        if date not in daily_sales:
            daily_sales[date] = {"invoices": 0, "pos": 0, "total": 0}
        daily_sales[date]["pos"] += pos.get("grand_total", 0)
        daily_sales[date]["total"] += pos.get("grand_total", 0)
    
    return {
        "report_type": "sales_summary",
        "period": {"start": start, "end": end, "type": period},
        "summary": {
            "total_sales": total_sales,
            "total_qty": total_qty,
            "total_transactions": total_transactions,
            "invoice_count": len(invoices),
            "pos_count": len(pos_txns),
            "average_transaction": total_sales / total_transactions if total_transactions > 0 else 0
        },
        "by_payment_method": by_payment,
        "daily_breakdown": [
            {"date": k, **v} for k, v in sorted(daily_sales.items())
        ]
    }

@router.get("/sales/by-product")
async def sales_by_product_report(
    period: str = "month",
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = 50,
    user: dict = Depends(get_current_user)
):
    """Sales breakdown by product"""
    db = get_database()
    start, end = get_date_range(period, date_from, date_to)
    
    # Aggregate from invoice items
    pipeline = [
        {"$match": {
            "transaction_date": {"$gte": start, "$lte": end},
            "status": {"$nin": ["cancelled", "void"]}
        }},
        {"$unwind": "$items"},
        {"$group": {
            "_id": "$items.product_id",
            "product_code": {"$first": "$items.product_code"},
            "product_name": {"$first": "$items.product_name"},
            "total_qty": {"$sum": "$items.quantity"},
            "total_sales": {"$sum": "$items.subtotal"},
            "transaction_count": {"$sum": 1}
        }},
        {"$sort": {"total_sales": -1}},
        {"$limit": limit}
    ]
    
    results = await db.sales_invoices.aggregate(pipeline).to_list(limit)
    
    return {
        "report_type": "sales_by_product",
        "period": {"start": start, "end": end},
        "items": results,
        "total_products": len(results)
    }

@router.get("/sales/by-customer")
async def sales_by_customer_report(
    period: str = "month",
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = 50,
    user: dict = Depends(get_current_user)
):
    """Sales breakdown by customer"""
    db = get_database()
    start, end = get_date_range(period, date_from, date_to)
    
    pipeline = [
        {"$match": {
            "transaction_date": {"$gte": start, "$lte": end},
            "status": {"$nin": ["cancelled", "void"]}
        }},
        {"$group": {
            "_id": "$customer_id",
            "customer_name": {"$first": "$customer_name"},
            "total_purchases": {"$sum": "$grand_total"},
            "total_qty": {"$sum": "$total_qty"},
            "transaction_count": {"$sum": 1}
        }},
        {"$sort": {"total_purchases": -1}},
        {"$limit": limit}
    ]
    
    results = await db.sales_invoices.aggregate(pipeline).to_list(limit)
    
    return {
        "report_type": "sales_by_customer",
        "period": {"start": start, "end": end},
        "items": results,
        "total_customers": len(results)
    }

@router.get("/sales/by-salesperson")
async def sales_by_salesperson_report(
    period: str = "month",
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Sales breakdown by salesperson"""
    db = get_database()
    start, end = get_date_range(period, date_from, date_to)
    
    pipeline = [
        {"$match": {
            "transaction_date": {"$gte": start, "$lte": end},
            "status": {"$nin": ["cancelled", "void"]},
            "sales_person_id": {"$ne": None}
        }},
        {"$group": {
            "_id": "$sales_person_id",
            "salesperson_name": {"$first": "$salesperson_name"},
            "total_sales": {"$sum": "$grand_total"},
            "transaction_count": {"$sum": 1},
            "average_sale": {"$avg": "$grand_total"}
        }},
        {"$sort": {"total_sales": -1}}
    ]
    
    results = await db.sales_invoices.aggregate(pipeline).to_list(100)
    
    # Enrich with salesperson data
    for r in results:
        if r["_id"]:
            sp = await db.sales_persons.find_one({"id": r["_id"]}, {"_id": 0, "name": 1})
            if sp:
                r["salesperson_name"] = sp.get("name", r.get("salesperson_name"))
    
    return {
        "report_type": "sales_by_salesperson",
        "period": {"start": start, "end": end},
        "items": results
    }

# ==================== 2. PURCHASE REPORTS ====================

@router.get("/purchase/summary")
async def purchase_summary_report(
    period: str = "month",
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Purchase summary report"""
    db = get_database()
    start, end = get_date_range(period, date_from, date_to)
    
    query = {
        "po_date": {"$gte": start, "$lte": end},
        "status": {"$nin": ["cancelled", "void"]}
    }
    
    pos = await db.purchase_orders.find(query, {"_id": 0}).to_list(10000)
    
    total_purchase = sum(p.get("total_amount", 0) for p in pos)
    
    # By supplier
    by_supplier = {}
    for po in pos:
        supplier = po.get("supplier_name", "Unknown")
        if supplier not in by_supplier:
            by_supplier[supplier] = {"count": 0, "total": 0}
        by_supplier[supplier]["count"] += 1
        by_supplier[supplier]["total"] += po.get("total_amount", 0)
    
    # By status
    by_status = {}
    for po in pos:
        status = po.get("status", "unknown")
        if status not in by_status:
            by_status[status] = {"count": 0, "total": 0}
        by_status[status]["count"] += 1
        by_status[status]["total"] += po.get("total_amount", 0)
    
    return {
        "report_type": "purchase_summary",
        "period": {"start": start, "end": end},
        "summary": {
            "total_purchase": total_purchase,
            "total_po": len(pos),
            "average_po": total_purchase / len(pos) if pos else 0
        },
        "by_supplier": [{"supplier": k, **v} for k, v in sorted(by_supplier.items(), key=lambda x: x[1]["total"], reverse=True)],
        "by_status": by_status
    }

@router.get("/purchase/by-product")
async def purchase_by_product_report(
    period: str = "month",
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = 50,
    user: dict = Depends(get_current_user)
):
    """Purchase breakdown by product"""
    db = get_database()
    start, end = get_date_range(period, date_from, date_to)
    
    pipeline = [
        {"$match": {
            "po_date": {"$gte": start, "$lte": end},
            "status": {"$nin": ["cancelled", "void"]}
        }},
        {"$unwind": "$items"},
        {"$group": {
            "_id": "$items.product_id",
            "product_code": {"$first": "$items.product_code"},
            "product_name": {"$first": "$items.product_name"},
            "total_qty": {"$sum": "$items.quantity"},
            "total_cost": {"$sum": {"$multiply": ["$items.quantity", "$items.unit_price"]}},
            "po_count": {"$sum": 1}
        }},
        {"$sort": {"total_cost": -1}},
        {"$limit": limit}
    ]
    
    results = await db.purchase_orders.aggregate(pipeline).to_list(limit)
    
    return {
        "report_type": "purchase_by_product",
        "period": {"start": start, "end": end},
        "items": results
    }

# ==================== 3. INVENTORY REPORTS ====================

@router.get("/inventory/stock-status")
async def inventory_stock_status_report(
    warehouse_id: Optional[str] = None,
    category_id: Optional[str] = None,
    low_stock_only: bool = False,
    user: dict = Depends(get_current_user)
):
    """Current stock status report"""
    db = get_database()
    
    query = {"is_active": {"$ne": False}}
    if category_id:
        query["category_id"] = category_id
    
    products = await db.products.find(query, {"_id": 0}).to_list(5000)
    
    # Enrich with stock data
    result = []
    low_stock_count = 0
    out_of_stock_count = 0
    total_value = 0
    
    for p in products:
        stock_query = {"product_id": p["id"]}
        if warehouse_id:
            stock_query["warehouse_id"] = warehouse_id
        
        stock_records = await db.stock.find(stock_query, {"_id": 0}).to_list(100)
        total_stock = sum(s.get("quantity", 0) for s in stock_records)
        
        min_stock = p.get("min_stock", 0)
        reorder_point = p.get("reorder_point", min_stock)
        cost_price = p.get("buy_price", 0) or p.get("cost_price", 0)
        stock_value = total_stock * cost_price
        
        is_low_stock = total_stock <= reorder_point and total_stock > 0
        is_out_of_stock = total_stock <= 0
        
        if is_low_stock:
            low_stock_count += 1
        if is_out_of_stock:
            out_of_stock_count += 1
        
        total_value += stock_value
        
        if low_stock_only and not (is_low_stock or is_out_of_stock):
            continue
        
        result.append({
            "product_id": p["id"],
            "product_code": p.get("code"),
            "product_name": p.get("name"),
            "category": p.get("category_name"),
            "current_stock": total_stock,
            "min_stock": min_stock,
            "reorder_point": reorder_point,
            "stock_value": stock_value,
            "unit": p.get("unit", "PCS"),
            "status": "out_of_stock" if is_out_of_stock else "low_stock" if is_low_stock else "normal"
        })
    
    return {
        "report_type": "inventory_stock_status",
        "summary": {
            "total_products": len(products),
            "low_stock_count": low_stock_count,
            "out_of_stock_count": out_of_stock_count,
            "total_stock_value": total_value
        },
        "items": sorted(result, key=lambda x: x["current_stock"])[:200]
    }

@router.get("/inventory/movement")
async def inventory_movement_report(
    period: str = "month",
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    product_id: Optional[str] = None,
    warehouse_id: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Stock movement report"""
    db = get_database()
    start, end = get_date_range(period, date_from, date_to)
    
    query = {
        "movement_date": {"$gte": start, "$lte": end}
    }
    if product_id:
        query["product_id"] = product_id
    if warehouse_id:
        query["warehouse_id"] = warehouse_id
    
    movements = await db.stock_movements.find(query, {"_id": 0}).sort("movement_date", -1).to_list(1000)
    
    # Summary by type
    by_type = {}
    for m in movements:
        mtype = m.get("movement_type", "unknown")
        if mtype not in by_type:
            by_type[mtype] = {"count": 0, "qty_in": 0, "qty_out": 0}
        by_type[mtype]["count"] += 1
        if m.get("quantity", 0) > 0:
            by_type[mtype]["qty_in"] += m.get("quantity", 0)
        else:
            by_type[mtype]["qty_out"] += abs(m.get("quantity", 0))
    
    return {
        "report_type": "inventory_movement",
        "period": {"start": start, "end": end},
        "summary": {
            "total_movements": len(movements),
            "by_type": by_type
        },
        "items": movements[:200]
    }

@router.get("/inventory/valuation")
async def inventory_valuation_report(
    warehouse_id: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Inventory valuation report"""
    db = get_database()
    
    products = await db.products.find({"is_active": {"$ne": False}}, {"_id": 0}).to_list(5000)
    
    result = []
    total_cost_value = 0
    total_sell_value = 0
    
    for p in products:
        stock_query = {"product_id": p["id"]}
        if warehouse_id:
            stock_query["warehouse_id"] = warehouse_id
        
        stock_records = await db.stock.find(stock_query, {"_id": 0}).to_list(100)
        total_stock = sum(s.get("quantity", 0) for s in stock_records)
        
        if total_stock <= 0:
            continue
        
        cost_price = p.get("buy_price", 0) or p.get("cost_price", 0)
        sell_price = p.get("sell_price", 0)
        
        cost_value = total_stock * cost_price
        sell_value = total_stock * sell_price
        potential_profit = sell_value - cost_value
        
        total_cost_value += cost_value
        total_sell_value += sell_value
        
        result.append({
            "product_id": p["id"],
            "product_code": p.get("code"),
            "product_name": p.get("name"),
            "current_stock": total_stock,
            "cost_price": cost_price,
            "sell_price": sell_price,
            "cost_value": cost_value,
            "sell_value": sell_value,
            "potential_profit": potential_profit,
            "margin_percent": (potential_profit / cost_value * 100) if cost_value > 0 else 0
        })
    
    return {
        "report_type": "inventory_valuation",
        "summary": {
            "total_products": len(result),
            "total_cost_value": total_cost_value,
            "total_sell_value": total_sell_value,
            "total_potential_profit": total_sell_value - total_cost_value,
            "average_margin": ((total_sell_value - total_cost_value) / total_cost_value * 100) if total_cost_value > 0 else 0
        },
        "items": sorted(result, key=lambda x: x["cost_value"], reverse=True)[:200]
    }

# ==================== 4. FINANCIAL REPORTS ====================

@router.get("/financial/profit-loss")
async def profit_loss_report(
    period: str = "month",
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Profit & Loss report"""
    db = get_database()
    start, end = get_date_range(period, date_from, date_to)
    
    # Revenue from sales
    sales_query = {
        "transaction_date": {"$gte": start, "$lte": end},
        "status": {"$nin": ["cancelled", "void"]}
    }
    sales = await db.sales_invoices.find(sales_query, {"_id": 0}).to_list(10000)
    pos_sales = await db.pos_transactions.find(sales_query, {"_id": 0}).to_list(10000)
    
    total_revenue = sum(s.get("grand_total", 0) for s in sales) + sum(p.get("grand_total", 0) for p in pos_sales)
    
    # COGS (Cost of Goods Sold) - simplified
    cogs = 0
    for s in sales:
        for item in s.get("items", []):
            # Get product cost
            prod = await db.products.find_one({"id": item.get("product_id")}, {"_id": 0, "buy_price": 1, "cost_price": 1})
            if prod:
                cost = prod.get("buy_price", 0) or prod.get("cost_price", 0)
                cogs += item.get("quantity", 0) * cost
    
    gross_profit = total_revenue - cogs
    
    # Operating expenses from journals
    expense_query = {
        "journal_date": {"$gte": start, "$lte": end},
        "entries.account_code": {"$regex": "^5-"}  # Expense accounts
    }
    expense_journals = await db.journals.find(expense_query, {"_id": 0}).to_list(1000)
    
    total_expenses = 0
    expense_breakdown = {}
    for j in expense_journals:
        for entry in j.get("entries", []):
            if entry.get("account_code", "").startswith("5-"):
                total_expenses += entry.get("debit", 0)
                acc_name = entry.get("account_name", "Other Expense")
                if acc_name not in expense_breakdown:
                    expense_breakdown[acc_name] = 0
                expense_breakdown[acc_name] += entry.get("debit", 0)
    
    net_profit = gross_profit - total_expenses
    
    return {
        "report_type": "profit_loss",
        "period": {"start": start, "end": end},
        "revenue": {
            "sales_revenue": total_revenue,
            "other_revenue": 0,
            "total_revenue": total_revenue
        },
        "cost_of_goods_sold": cogs,
        "gross_profit": gross_profit,
        "gross_margin_percent": (gross_profit / total_revenue * 100) if total_revenue > 0 else 0,
        "operating_expenses": {
            "total": total_expenses,
            "breakdown": expense_breakdown
        },
        "net_profit": net_profit,
        "net_margin_percent": (net_profit / total_revenue * 100) if total_revenue > 0 else 0
    }

@router.get("/financial/balance-sheet")
async def balance_sheet_report(
    as_of_date: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Balance sheet report"""
    db = get_database()
    
    date = as_of_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Get account balances
    accounts = await db.chart_of_accounts.find({}, {"_id": 0}).to_list(500)
    
    assets = []
    liabilities = []
    equity = []
    
    for acc in accounts:
        code = acc.get("code", "")
        balance = acc.get("balance", 0)
        
        item = {
            "code": code,
            "name": acc.get("name"),
            "balance": balance
        }
        
        if code.startswith("1-"):  # Assets
            assets.append(item)
        elif code.startswith("2-"):  # Liabilities
            liabilities.append(item)
        elif code.startswith("3-"):  # Equity
            equity.append(item)
    
    total_assets = sum(a["balance"] for a in assets)
    total_liabilities = sum(l["balance"] for l in liabilities)
    total_equity = sum(e["balance"] for e in equity)
    
    return {
        "report_type": "balance_sheet",
        "as_of_date": date,
        "assets": {
            "items": assets,
            "total": total_assets
        },
        "liabilities": {
            "items": liabilities,
            "total": total_liabilities
        },
        "equity": {
            "items": equity,
            "total": total_equity
        },
        "balance_check": total_assets - (total_liabilities + total_equity)
    }

# ==================== 5. AR/AP AGING REPORTS ====================

@router.get("/ar/aging")
async def ar_aging_report(
    as_of_date: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Accounts Receivable aging report"""
    db = get_database()
    
    date = as_of_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    today = datetime.strptime(date, "%Y-%m-%d")
    
    # Get unpaid invoices
    invoices = await db.sales_invoices.find({
        "payment_status": {"$in": ["unpaid", "partial"]},
        "status": {"$nin": ["cancelled", "void"]}
    }, {"_id": 0}).to_list(5000)
    
    aging_buckets = {
        "current": {"count": 0, "amount": 0, "items": []},
        "1_30": {"count": 0, "amount": 0, "items": []},
        "31_60": {"count": 0, "amount": 0, "items": []},
        "61_90": {"count": 0, "amount": 0, "items": []},
        "over_90": {"count": 0, "amount": 0, "items": []}
    }
    
    total_ar = 0
    
    for inv in invoices:
        due_date_str = inv.get("due_date") or inv.get("transaction_date")
        if not due_date_str:
            continue
        
        try:
            due_date = datetime.strptime(due_date_str[:10], "%Y-%m-%d")
        except:
            continue
        
        days_overdue = (today - due_date).days
        outstanding = inv.get("grand_total", 0) - inv.get("paid_amount", 0)
        
        if outstanding <= 0:
            continue
        
        total_ar += outstanding
        
        item = {
            "invoice_no": inv.get("invoice_number"),
            "customer": inv.get("customer_name"),
            "due_date": due_date_str[:10],
            "days_overdue": max(0, days_overdue),
            "amount": outstanding
        }
        
        if days_overdue <= 0:
            aging_buckets["current"]["count"] += 1
            aging_buckets["current"]["amount"] += outstanding
            aging_buckets["current"]["items"].append(item)
        elif days_overdue <= 30:
            aging_buckets["1_30"]["count"] += 1
            aging_buckets["1_30"]["amount"] += outstanding
            aging_buckets["1_30"]["items"].append(item)
        elif days_overdue <= 60:
            aging_buckets["31_60"]["count"] += 1
            aging_buckets["31_60"]["amount"] += outstanding
            aging_buckets["31_60"]["items"].append(item)
        elif days_overdue <= 90:
            aging_buckets["61_90"]["count"] += 1
            aging_buckets["61_90"]["amount"] += outstanding
            aging_buckets["61_90"]["items"].append(item)
        else:
            aging_buckets["over_90"]["count"] += 1
            aging_buckets["over_90"]["amount"] += outstanding
            aging_buckets["over_90"]["items"].append(item)
    
    # Limit items per bucket for response size
    for bucket in aging_buckets.values():
        bucket["items"] = bucket["items"][:20]
    
    return {
        "report_type": "ar_aging",
        "as_of_date": date,
        "total_ar": total_ar,
        "aging_buckets": aging_buckets
    }

@router.get("/ap/aging")
async def ap_aging_report(
    as_of_date: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Accounts Payable aging report"""
    db = get_database()
    
    date = as_of_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    today = datetime.strptime(date, "%Y-%m-%d")
    
    # Get unpaid purchase orders/invoices
    pos = await db.purchase_orders.find({
        "payment_status": {"$in": ["unpaid", "partial"]},
        "status": {"$nin": ["cancelled", "void"]}
    }, {"_id": 0}).to_list(5000)
    
    aging_buckets = {
        "current": {"count": 0, "amount": 0, "items": []},
        "1_30": {"count": 0, "amount": 0, "items": []},
        "31_60": {"count": 0, "amount": 0, "items": []},
        "61_90": {"count": 0, "amount": 0, "items": []},
        "over_90": {"count": 0, "amount": 0, "items": []}
    }
    
    total_ap = 0
    
    for po in pos:
        due_date_str = po.get("due_date") or po.get("po_date")
        if not due_date_str:
            continue
        
        try:
            due_date = datetime.strptime(due_date_str[:10], "%Y-%m-%d")
        except:
            continue
        
        days_overdue = (today - due_date).days
        outstanding = po.get("total_amount", 0) - po.get("paid_amount", 0)
        
        if outstanding <= 0:
            continue
        
        total_ap += outstanding
        
        item = {
            "po_no": po.get("po_number"),
            "supplier": po.get("supplier_name"),
            "due_date": due_date_str[:10],
            "days_overdue": max(0, days_overdue),
            "amount": outstanding
        }
        
        if days_overdue <= 0:
            aging_buckets["current"]["count"] += 1
            aging_buckets["current"]["amount"] += outstanding
            aging_buckets["current"]["items"].append(item)
        elif days_overdue <= 30:
            aging_buckets["1_30"]["count"] += 1
            aging_buckets["1_30"]["amount"] += outstanding
            aging_buckets["1_30"]["items"].append(item)
        elif days_overdue <= 60:
            aging_buckets["31_60"]["count"] += 1
            aging_buckets["31_60"]["amount"] += outstanding
            aging_buckets["31_60"]["items"].append(item)
        elif days_overdue <= 90:
            aging_buckets["61_90"]["count"] += 1
            aging_buckets["61_90"]["amount"] += outstanding
            aging_buckets["61_90"]["items"].append(item)
        else:
            aging_buckets["over_90"]["count"] += 1
            aging_buckets["over_90"]["amount"] += outstanding
            aging_buckets["over_90"]["items"].append(item)
    
    for bucket in aging_buckets.values():
        bucket["items"] = bucket["items"][:20]
    
    return {
        "report_type": "ap_aging",
        "as_of_date": date,
        "total_ap": total_ap,
        "aging_buckets": aging_buckets
    }

# ==================== 6. CASH FLOW REPORTS ====================

@router.get("/cashflow/summary")
async def cashflow_summary_report(
    period: str = "month",
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Cash flow summary report"""
    db = get_database()
    start, end = get_date_range(period, date_from, date_to)
    
    # Cash inflows
    # 1. Sales receipts
    sales_receipts = await db.sales_invoices.find({
        "transaction_date": {"$gte": start, "$lte": end},
        "payment_type": {"$in": ["cash", "tunai"]},
        "status": {"$nin": ["cancelled", "void"]}
    }, {"_id": 0}).to_list(10000)
    
    cash_from_sales = sum(s.get("cash_amount", 0) or s.get("grand_total", 0) for s in sales_receipts)
    
    # 2. POS cash sales
    pos_cash = await db.pos_transactions.find({
        "transaction_date": {"$gte": start, "$lte": end},
        "payment_method": {"$in": ["cash", "tunai"]},
        "status": {"$nin": ["cancelled", "void"]}
    }, {"_id": 0}).to_list(10000)
    
    cash_from_pos = sum(p.get("grand_total", 0) for p in pos_cash)
    
    # 3. AR collections
    ar_payments = await db.ar_payments.find({
        "payment_date": {"$gte": start, "$lte": end}
    }, {"_id": 0}).to_list(5000)
    
    cash_from_ar = sum(p.get("amount", 0) for p in ar_payments)
    
    total_inflows = cash_from_sales + cash_from_pos + cash_from_ar
    
    # Cash outflows
    # 1. Purchase payments
    purchase_payments = await db.ap_payments.find({
        "payment_date": {"$gte": start, "$lte": end}
    }, {"_id": 0}).to_list(5000)
    
    cash_to_suppliers = sum(p.get("amount", 0) for p in purchase_payments)
    
    # 2. Operating expenses (from journals)
    expense_journals = await db.journals.find({
        "journal_date": {"$gte": start, "$lte": end},
        "reference_type": {"$in": ["expense", "payment"]}
    }, {"_id": 0}).to_list(1000)
    
    operating_expenses = 0
    for j in expense_journals:
        for entry in j.get("entries", []):
            if entry.get("account_code", "").startswith("5-"):
                operating_expenses += entry.get("debit", 0)
    
    # 3. Commission payments
    commission_payments = await db.commissions.find({
        "paid_at": {"$gte": start, "$lte": end + "T23:59:59"},
        "status": "paid"
    }, {"_id": 0}).to_list(1000)
    
    cash_to_commission = sum(c.get("total_commission", 0) for c in commission_payments)
    
    total_outflows = cash_to_suppliers + operating_expenses + cash_to_commission
    
    net_cash_flow = total_inflows - total_outflows
    
    return {
        "report_type": "cashflow_summary",
        "period": {"start": start, "end": end},
        "inflows": {
            "cash_sales": cash_from_sales,
            "pos_cash": cash_from_pos,
            "ar_collections": cash_from_ar,
            "total": total_inflows
        },
        "outflows": {
            "supplier_payments": cash_to_suppliers,
            "operating_expenses": operating_expenses,
            "commission_payments": cash_to_commission,
            "total": total_outflows
        },
        "net_cash_flow": net_cash_flow
    }

# ==================== REPORT INDEX ====================

@router.get("/")
async def list_available_reports(user: dict = Depends(get_current_user)):
    """List all available reports"""
    return {
        "reports": [
            {"category": "Sales", "reports": [
                {"name": "Sales Summary", "endpoint": "/api/reports/sales/summary"},
                {"name": "Sales by Product", "endpoint": "/api/reports/sales/by-product"},
                {"name": "Sales by Customer", "endpoint": "/api/reports/sales/by-customer"},
                {"name": "Sales by Salesperson", "endpoint": "/api/reports/sales/by-salesperson"}
            ]},
            {"category": "Purchase", "reports": [
                {"name": "Purchase Summary", "endpoint": "/api/reports/purchase/summary"},
                {"name": "Purchase by Product", "endpoint": "/api/reports/purchase/by-product"}
            ]},
            {"category": "Inventory", "reports": [
                {"name": "Stock Status", "endpoint": "/api/reports/inventory/stock-status"},
                {"name": "Stock Movement", "endpoint": "/api/reports/inventory/movement"},
                {"name": "Inventory Valuation", "endpoint": "/api/reports/inventory/valuation"}
            ]},
            {"category": "Financial", "reports": [
                {"name": "Profit & Loss", "endpoint": "/api/reports/financial/profit-loss"},
                {"name": "Balance Sheet", "endpoint": "/api/reports/financial/balance-sheet"}
            ]},
            {"category": "Receivables", "reports": [
                {"name": "AR Aging", "endpoint": "/api/reports/ar/aging"}
            ]},
            {"category": "Payables", "reports": [
                {"name": "AP Aging", "endpoint": "/api/reports/ap/aging"}
            ]},
            {"category": "Cash Flow", "reports": [
                {"name": "Cash Flow Summary", "endpoint": "/api/reports/cashflow/summary"}
            ]}
        ]
    }
