# OCB TITAN ERP - Dashboard Intelligence
# AI-driven analytics dashboard - READ ONLY from SSOT
# MASTER BLUEPRINT: Data from journal_entries, stock_movements, sales_invoices, cash_variances

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from database import get_db
from utils.auth import get_current_user
from routes.rbac_middleware import require_permission
import asyncio

router = APIRouter(prefix="/dashboard-intel", tags=["Dashboard Intelligence"])


# ==================== HELPER FUNCTIONS ====================

async def get_date_range(days: int = 30):
    """Get date range for queries"""
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    return start_date.isoformat(), end_date.isoformat()


# ==================== TOP SELLING PRODUCTS ====================

@router.get("/top-selling")
async def get_top_selling_products(
    days: int = Query(30, description="Number of days to analyze"),
    limit: int = Query(20, description="Number of products to return"),
    branch_id: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """
    Get top selling products based on sales_invoices (SSOT)
    
    Data source: sales_invoices.items
    """
    db = get_db()
    
    start_date, end_date = await get_date_range(days)
    
    # Build match stage
    match_stage = {
        "invoice_date": {"$gte": start_date, "$lte": end_date},
        "status": {"$in": ["completed", "posted", "paid"]}
    }
    
    if branch_id:
        match_stage["branch_id"] = branch_id
    elif user.get("role") not in ["owner", "admin"] and user.get("branch_id"):
        match_stage["branch_id"] = user["branch_id"]
    
    pipeline = [
        {"$match": match_stage},
        {"$unwind": "$items"},
        {"$group": {
            "_id": {
                "product_id": "$items.product_id",
                "product_code": "$items.product_code",
                "product_name": "$items.product_name"
            },
            "total_qty": {"$sum": "$items.quantity"},
            "total_revenue": {"$sum": "$items.subtotal"},
            "transaction_count": {"$sum": 1}
        }},
        {"$sort": {"total_qty": -1}},
        {"$limit": limit},
        {"$project": {
            "_id": 0,
            "product_id": "$_id.product_id",
            "product_code": "$_id.product_code",
            "product_name": "$_id.product_name",
            "total_qty": 1,
            "total_revenue": 1,
            "transaction_count": 1,
            "avg_per_transaction": {"$divide": ["$total_qty", "$transaction_count"]}
        }}
    ]
    
    results = await db["sales_invoices"].aggregate(pipeline).to_list(limit)
    
    return {
        "period": {"start": start_date[:10], "end": end_date[:10], "days": days},
        "total_products": len(results),
        "items": results
    }


# ==================== DEAD STOCK ====================

@router.get("/dead-stock")
async def get_dead_stock(
    days: int = Query(60, description="Days without sales to consider dead"),
    branch_id: Optional[str] = None,
    limit: int = Query(50, description="Number of products to return"),
    user: dict = Depends(get_current_user)
):
    """
    Get dead stock (products with no sales in X days)
    
    Data source: stock_movements + sales_invoices cross-reference
    """
    db = get_db()
    
    start_date, _ = await get_date_range(days)
    
    # Branch filter
    branch_filter = {}
    if branch_id:
        branch_filter["branch_id"] = branch_id
    elif user.get("role") not in ["owner", "admin"] and user.get("branch_id"):
        branch_filter["branch_id"] = user["branch_id"]
    
    # Get products with stock (from SSOT: stock_movements)
    stock_pipeline = [
        {"$match": branch_filter} if branch_filter else {"$match": {}},
        {"$group": {
            "_id": {"product_id": "$product_id", "branch_id": "$branch_id"},
            "current_stock": {"$sum": "$quantity"},
            "product_code": {"$first": "$product_code"},
            "product_name": {"$first": "$product_name"}
        }},
        {"$match": {"current_stock": {"$gt": 0}}}
    ]
    
    products_with_stock = await db["stock_movements"].aggregate(stock_pipeline).to_list(10000)
    product_stock_map = {
        (p["_id"]["product_id"], p["_id"]["branch_id"]): p
        for p in products_with_stock
    }
    
    # Get products that HAVE been sold in the period
    sales_match = {"invoice_date": {"$gte": start_date}, "status": {"$in": ["completed", "posted", "paid"]}}
    if branch_filter:
        sales_match.update(branch_filter)
    
    sales_pipeline = [
        {"$match": sales_match},
        {"$unwind": "$items"},
        {"$group": {
            "_id": {"product_id": "$items.product_id", "branch_id": "$branch_id"},
            "last_sale_date": {"$max": "$invoice_date"},
            "total_sold": {"$sum": "$items.quantity"}
        }}
    ]
    
    sold_products = await db["sales_invoices"].aggregate(sales_pipeline).to_list(10000)
    sold_map = {(s["_id"]["product_id"], s["_id"]["branch_id"]): s for s in sold_products}
    
    # Find dead stock (has stock but no sales)
    dead_stock = []
    for key, product in product_stock_map.items():
        product_id, branch_id = key
        if key not in sold_map:
            # Get product details
            prod_info = await db["products"].find_one({"id": product_id}, {"_id": 0, "cost_price": 1, "selling_price": 1, "category_name": 1})
            
            dead_stock.append({
                "product_id": product_id,
                "product_code": product.get("product_code", ""),
                "product_name": product.get("product_name", ""),
                "branch_id": branch_id,
                "current_stock": product["current_stock"],
                "cost_price": prod_info.get("cost_price", 0) if prod_info else 0,
                "stock_value": product["current_stock"] * (prod_info.get("cost_price", 0) if prod_info else 0),
                "category": prod_info.get("category_name", "") if prod_info else "",
                "days_without_sale": days,
                "severity": "high" if product["current_stock"] > 10 else "medium"
            })
    
    # Sort by stock value
    dead_stock.sort(key=lambda x: x["stock_value"], reverse=True)
    
    # Calculate totals
    total_value = sum(d["stock_value"] for d in dead_stock)
    total_qty = sum(d["current_stock"] for d in dead_stock)
    
    return {
        "period": {"days_without_sale": days},
        "summary": {
            "total_dead_stock_items": len(dead_stock),
            "total_dead_stock_qty": total_qty,
            "total_dead_stock_value": total_value
        },
        "items": dead_stock[:limit]
    }


# ==================== OUTLET/BRANCH LOSS/PROFIT ====================

@router.get("/outlet-performance")
async def get_outlet_performance(
    days: int = Query(30, description="Number of days to analyze"),
    user: dict = Depends(require_permission("dashboard", "view"))
):
    """
    Get profit/loss per outlet/branch
    
    Data source: journal_entries (SSOT for accounting)
    """
    db = get_db()
    
    start_date, end_date = await get_date_range(days)
    
    # Get revenue by branch from journal entries
    revenue_pipeline = [
        {"$match": {
            "status": "posted",
            "journal_date": {"$gte": start_date, "$lte": end_date}
        }},
        {"$unwind": "$entries"},
        {"$match": {
            "entries.account_code": {"$regex": "^4"}  # Revenue accounts start with 4
        }},
        {"$group": {
            "_id": "$branch_id",
            "total_revenue": {"$sum": "$entries.credit"}
        }}
    ]
    
    revenue_data = await db["journal_entries"].aggregate(revenue_pipeline).to_list(100)
    revenue_map = {r["_id"]: r["total_revenue"] for r in revenue_data if r["_id"]}
    
    # Get expenses by branch
    expense_pipeline = [
        {"$match": {
            "status": "posted",
            "journal_date": {"$gte": start_date, "$lte": end_date}
        }},
        {"$unwind": "$entries"},
        {"$match": {
            "entries.account_code": {"$regex": "^[5678]"}  # Expense accounts
        }},
        {"$group": {
            "_id": "$branch_id",
            "total_expense": {"$sum": "$entries.debit"}
        }}
    ]
    
    expense_data = await db["journal_entries"].aggregate(expense_pipeline).to_list(100)
    expense_map = {e["_id"]: e["total_expense"] for e in expense_data if e["_id"]}
    
    # Get branches
    branches = await db["branches"].find({"is_active": True}, {"_id": 0}).to_list(100)
    
    # Combine data
    results = []
    for branch in branches:
        branch_id = branch.get("id")
        revenue = revenue_map.get(branch_id, 0)
        expense = expense_map.get(branch_id, 0)
        profit = revenue - expense
        margin = (profit / revenue * 100) if revenue > 0 else 0
        
        results.append({
            "branch_id": branch_id,
            "branch_name": branch.get("name", ""),
            "branch_code": branch.get("code", ""),
            "total_revenue": revenue,
            "total_expense": expense,
            "profit_loss": profit,
            "margin_percent": round(margin, 2),
            "status": "profit" if profit > 0 else ("loss" if profit < 0 else "break_even")
        })
    
    # Sort by profit
    results.sort(key=lambda x: x["profit_loss"], reverse=True)
    
    # Summary
    total_revenue = sum(r["total_revenue"] for r in results)
    total_expense = sum(r["total_expense"] for r in results)
    total_profit = total_revenue - total_expense
    
    return {
        "period": {"start": start_date[:10], "end": end_date[:10], "days": days},
        "summary": {
            "total_branches": len(results),
            "total_revenue": total_revenue,
            "total_expense": total_expense,
            "total_profit": total_profit,
            "profitable_branches": sum(1 for r in results if r["profit_loss"] > 0),
            "loss_branches": sum(1 for r in results if r["profit_loss"] < 0)
        },
        "branches": results
    }


# ==================== CASH VARIANCE RANKING ====================

@router.get("/cash-variance-ranking")
async def get_cash_variance_ranking(
    days: int = Query(30, description="Number of days to analyze"),
    user: dict = Depends(require_permission("cash_control", "view"))
):
    """
    Rank cashiers/branches by cash variance
    
    Data source: cash_discrepancies, cashier_shifts
    """
    db = get_db()
    
    start_date, end_date = await get_date_range(days)
    
    # Get variance data
    pipeline = [
        {"$match": {
            "created_at": {"$gte": start_date, "$lte": end_date}
        }},
        {"$group": {
            "_id": {
                "cashier_id": "$cashier_id",
                "cashier_name": "$cashier_name",
                "branch_id": "$branch_id"
            },
            "total_shortage": {
                "$sum": {
                    "$cond": [{"$eq": ["$discrepancy_type", "shortage"]}, "$discrepancy_amount", 0]
                }
            },
            "total_overage": {
                "$sum": {
                    "$cond": [{"$eq": ["$discrepancy_type", "overage"]}, "$discrepancy_amount", 0]
                }
            },
            "shortage_count": {
                "$sum": {"$cond": [{"$eq": ["$discrepancy_type", "shortage"]}, 1, 0]}
            },
            "overage_count": {
                "$sum": {"$cond": [{"$eq": ["$discrepancy_type", "overage"]}, 1, 0]}
            },
            "total_shifts": {"$sum": 1}
        }},
        {"$sort": {"total_shortage": -1}}
    ]
    
    variance_data = await db["cash_discrepancies"].aggregate(pipeline).to_list(100)
    
    # Enrich with branch names
    results = []
    for v in variance_data:
        _id = v.get("_id", {})
        if not _id:
            continue
        
        branch_id = _id.get("branch_id", "")
        branch = None
        if branch_id:
            branch = await db["branches"].find_one({"id": branch_id}, {"_id": 0, "name": 1})
        
        net_variance = v["total_overage"] - v["total_shortage"]
        
        results.append({
            "cashier_id": _id.get("cashier_id", ""),
            "cashier_name": _id.get("cashier_name", "Unknown"),
            "branch_id": branch_id,
            "branch_name": branch.get("name", "") if branch else "",
            "total_shortage": v["total_shortage"],
            "total_overage": v["total_overage"],
            "net_variance": net_variance,
            "shortage_count": v["shortage_count"],
            "overage_count": v["overage_count"],
            "total_variance_events": v["total_shifts"],
            "risk_level": "high" if v["total_shortage"] > 100000 else ("medium" if v["total_shortage"] > 50000 else "low")
        })
    
    # Summary
    total_shortage = sum(r["total_shortage"] for r in results)
    total_overage = sum(r["total_overage"] for r in results)
    
    return {
        "period": {"start": start_date[:10], "end": end_date[:10], "days": days},
        "summary": {
            "total_shortage": total_shortage,
            "total_overage": total_overage,
            "net_variance": total_overage - total_shortage,
            "cashiers_with_variance": len(results),
            "high_risk_count": sum(1 for r in results if r["risk_level"] == "high")
        },
        "ranking": results
    }


# ==================== STOCK TURNOVER ====================

@router.get("/stock-turnover")
async def get_stock_turnover(
    days: int = Query(30, description="Number of days to analyze"),
    branch_id: Optional[str] = None,
    limit: int = Query(50, description="Number of products to return"),
    user: dict = Depends(get_current_user)
):
    """
    Calculate stock turnover ratio per product
    
    Turnover = Cost of Goods Sold / Average Inventory
    
    Data source: stock_movements (SSOT)
    """
    db = get_db()
    
    start_date, end_date = await get_date_range(days)
    
    # Branch filter
    branch_filter = {}
    if branch_id:
        branch_filter["branch_id"] = branch_id
    elif user.get("role") not in ["owner", "admin"] and user.get("branch_id"):
        branch_filter["branch_id"] = user["branch_id"]
    
    # Calculate COGS from stock movements (sales_out movements)
    cogs_pipeline = [
        {"$match": {
            **branch_filter,
            "movement_type": {"$in": ["sales_out", "sale"]},
            "created_at": {"$gte": start_date, "$lte": end_date}
        }},
        {"$group": {
            "_id": "$product_id",
            "total_sold": {"$sum": {"$abs": "$quantity"}},
            "total_cogs": {"$sum": {"$multiply": [{"$abs": "$quantity"}, {"$ifNull": ["$cost_price", 0]}]}},
            "product_code": {"$first": "$product_code"},
            "product_name": {"$first": "$product_name"}
        }}
    ]
    
    cogs_data = await db["stock_movements"].aggregate(cogs_pipeline).to_list(10000)
    cogs_map = {c["_id"]: c for c in cogs_data}
    
    # Get current stock
    stock_pipeline = [
        {"$match": branch_filter} if branch_filter else {"$match": {}},
        {"$group": {
            "_id": "$product_id",
            "current_stock": {"$sum": "$quantity"}
        }}
    ]
    
    stock_data = await db["stock_movements"].aggregate(stock_pipeline).to_list(10000)
    stock_map = {s["_id"]: s["current_stock"] for s in stock_data}
    
    # Calculate turnover
    results = []
    for product_id, cogs in cogs_map.items():
        current_stock = stock_map.get(product_id, 0)
        avg_inventory = current_stock  # Simplified - should use beginning + ending / 2
        
        if avg_inventory > 0:
            turnover_ratio = cogs["total_sold"] / avg_inventory
            days_to_sell = days / turnover_ratio if turnover_ratio > 0 else 999
        else:
            turnover_ratio = float('inf') if cogs["total_sold"] > 0 else 0
            days_to_sell = 0 if cogs["total_sold"] > 0 else 999
        
        results.append({
            "product_id": product_id,
            "product_code": cogs.get("product_code", ""),
            "product_name": cogs.get("product_name", ""),
            "total_sold": cogs["total_sold"],
            "current_stock": current_stock,
            "turnover_ratio": round(turnover_ratio, 2) if turnover_ratio != float('inf') else "∞",
            "days_to_sell_stock": round(days_to_sell, 1),
            "performance": "excellent" if turnover_ratio > 4 else ("good" if turnover_ratio > 2 else ("slow" if turnover_ratio > 0.5 else "dead"))
        })
    
    # Sort by turnover ratio descending
    results.sort(key=lambda x: x["turnover_ratio"] if isinstance(x["turnover_ratio"], (int, float)) else 999999, reverse=True)
    
    return {
        "period": {"start": start_date[:10], "end": end_date[:10], "days": days},
        "total_products": len(results),
        "items": results[:limit]
    }


# ==================== BEST SALESPERSON ====================

@router.get("/best-salesperson")
async def get_best_salesperson(
    days: int = Query(30, description="Number of days to analyze"),
    branch_id: Optional[str] = None,
    limit: int = Query(20, description="Number of salespeople to return"),
    user: dict = Depends(require_permission("reports", "view"))
):
    """
    Rank salespeople by performance
    
    Data source: sales_invoices (SSOT)
    """
    db = get_db()
    
    start_date, end_date = await get_date_range(days)
    
    # Build match
    match_stage = {
        "invoice_date": {"$gte": start_date, "$lte": end_date},
        "status": {"$in": ["completed", "posted", "paid"]}
    }
    
    if branch_id:
        match_stage["branch_id"] = branch_id
    
    pipeline = [
        {"$match": match_stage},
        {"$group": {
            "_id": {
                "cashier_id": "$cashier_id",
                "cashier_name": "$cashier_name"
            },
            "total_sales": {"$sum": "$total"},
            "total_transactions": {"$sum": 1},
            "total_items": {"$sum": {"$size": {"$ifNull": ["$items", []]}}},
            "avg_transaction": {"$avg": "$total"}
        }},
        {"$sort": {"total_sales": -1}},
        {"$limit": limit}
    ]
    
    results = await db["sales_invoices"].aggregate(pipeline).to_list(limit)
    
    salespeople = []
    rank = 0
    for r in results:
        rank += 1
        salespeople.append({
            "rank": rank,
            "cashier_id": r["_id"]["cashier_id"],
            "cashier_name": r["_id"]["cashier_name"],
            "total_sales": r["total_sales"],
            "total_transactions": r["total_transactions"],
            "total_items": r["total_items"],
            "avg_transaction": round(r["avg_transaction"], 0),
            "items_per_transaction": round(r["total_items"] / r["total_transactions"], 1) if r["total_transactions"] > 0 else 0
        })
    
    return {
        "period": {"start": start_date[:10], "end": end_date[:10], "days": days},
        "total_salespeople": len(salespeople),
        "ranking": salespeople
    }


# ==================== LOW MARGIN ALERT ====================

@router.get("/low-margin-alert")
async def get_low_margin_products(
    margin_threshold: float = Query(15.0, description="Margin threshold percentage"),
    days: int = Query(30, description="Number of days to analyze"),
    branch_id: Optional[str] = None,
    user: dict = Depends(require_permission("products", "view"))
):
    """
    Get products with margin below threshold
    
    Data source: sales_invoices + products (for cost)
    """
    db = get_db()
    
    start_date, end_date = await get_date_range(days)
    
    match_stage = {
        "invoice_date": {"$gte": start_date, "$lte": end_date},
        "status": {"$in": ["completed", "posted", "paid"]}
    }
    
    if branch_id:
        match_stage["branch_id"] = branch_id
    
    # Get sales data
    pipeline = [
        {"$match": match_stage},
        {"$unwind": "$items"},
        {"$group": {
            "_id": "$items.product_id",
            "product_code": {"$first": "$items.product_code"},
            "product_name": {"$first": "$items.product_name"},
            "total_qty": {"$sum": "$items.quantity"},
            "total_revenue": {"$sum": "$items.subtotal"},
            "avg_selling_price": {"$avg": "$items.unit_price"}
        }}
    ]
    
    sales_data = await db["sales_invoices"].aggregate(pipeline).to_list(10000)
    
    # Get cost prices and calculate margin
    low_margin_products = []
    
    for sale in sales_data:
        product = await db["products"].find_one(
            {"id": sale["_id"]}, 
            {"_id": 0, "cost_price": 1, "category_name": 1}
        )
        
        cost_price = product.get("cost_price", 0) if product else 0
        avg_sell = sale["avg_selling_price"]
        
        if cost_price > 0 and avg_sell > 0:
            margin = ((avg_sell - cost_price) / avg_sell) * 100
        else:
            margin = 0
        
        if margin < margin_threshold:
            low_margin_products.append({
                "product_id": sale["_id"],
                "product_code": sale["product_code"],
                "product_name": sale["product_name"],
                "category": product.get("category_name", "") if product else "",
                "cost_price": cost_price,
                "avg_selling_price": round(avg_sell, 0),
                "margin_percent": round(margin, 2),
                "total_qty_sold": sale["total_qty"],
                "total_revenue": sale["total_revenue"],
                "potential_loss": round((margin_threshold - margin) / 100 * sale["total_revenue"], 0),
                "severity": "critical" if margin < 5 else ("high" if margin < 10 else "medium")
            })
    
    # Sort by margin ascending (worst first)
    low_margin_products.sort(key=lambda x: x["margin_percent"])
    
    return {
        "period": {"start": start_date[:10], "end": end_date[:10], "days": days},
        "threshold": margin_threshold,
        "total_products_below_threshold": len(low_margin_products),
        "items": low_margin_products[:50]
    }


# ==================== COMPREHENSIVE KPI SUMMARY ====================

@router.get("/kpi-summary")
async def get_kpi_summary(
    days: int = Query(30, description="Number of days to analyze"),
    user: dict = Depends(require_permission("dashboard", "view"))
):
    """
    Get comprehensive KPI summary for the dashboard
    
    All data from SSOT sources
    """
    db = get_db()
    
    start_date, end_date = await get_date_range(days)
    
    # Sales KPIs
    sales_match = {
        "invoice_date": {"$gte": start_date, "$lte": end_date},
        "status": {"$in": ["completed", "posted", "paid"]}
    }
    
    sales_pipeline = [
        {"$match": sales_match},
        {"$group": {
            "_id": None,
            "total_sales": {"$sum": "$total"},
            "total_transactions": {"$sum": 1},
            "avg_transaction": {"$avg": "$total"}
        }}
    ]
    
    sales_kpi = await db["sales_invoices"].aggregate(sales_pipeline).to_list(1)
    sales_kpi = sales_kpi[0] if sales_kpi else {"total_sales": 0, "total_transactions": 0, "avg_transaction": 0}
    
    # Purchase KPIs
    purchase_match = {
        "order_date": {"$gte": start_date, "$lte": end_date},
        "status": {"$in": ["received", "completed"]}
    }
    
    purchase_pipeline = [
        {"$match": purchase_match},
        {"$group": {
            "_id": None,
            "total_purchase": {"$sum": "$total"},
            "total_po": {"$sum": 1}
        }}
    ]
    
    purchase_kpi = await db["purchase_orders"].aggregate(purchase_pipeline).to_list(1)
    purchase_kpi = purchase_kpi[0] if purchase_kpi else {"total_purchase": 0, "total_po": 0}
    
    # Cash variance KPIs
    variance_pipeline = [
        {"$match": {"created_at": {"$gte": start_date, "$lte": end_date}}},
        {"$group": {
            "_id": None,
            "total_shortage": {"$sum": {"$cond": [{"$eq": ["$discrepancy_type", "shortage"]}, "$discrepancy_amount", 0]}},
            "total_overage": {"$sum": {"$cond": [{"$eq": ["$discrepancy_type", "overage"]}, "$discrepancy_amount", 0]}},
            "variance_count": {"$sum": 1}
        }}
    ]
    
    variance_kpi = await db["cash_discrepancies"].aggregate(variance_pipeline).to_list(1)
    variance_kpi = variance_kpi[0] if variance_kpi else {"total_shortage": 0, "total_overage": 0, "variance_count": 0}
    
    # Inventory value from SSOT (stock_movements)
    inv_pipeline = [
        {"$group": {"_id": "$product_id", "total_qty": {"$sum": "$quantity"}}}
    ]
    stock_by_product = await db["stock_movements"].aggregate(inv_pipeline).to_list(100000)
    
    total_inventory_value = 0
    for s in stock_by_product:
        if s["total_qty"] > 0:
            product = await db["products"].find_one({"id": s["_id"]}, {"_id": 0, "cost_price": 1})
            if product:
                total_inventory_value += s["total_qty"] * product.get("cost_price", 0)
    
    # Active branches
    active_branches = await db["branches"].count_documents({"is_active": True})
    
    # Active products
    active_products = await db["products"].count_documents({"is_active": True})
    
    return {
        "period": {"start": start_date[:10], "end": end_date[:10], "days": days},
        "sales": {
            "total_revenue": sales_kpi.get("total_sales", 0),
            "total_transactions": sales_kpi.get("total_transactions", 0),
            "avg_transaction_value": round(sales_kpi.get("avg_transaction", 0), 0)
        },
        "purchase": {
            "total_purchase": purchase_kpi.get("total_purchase", 0),
            "total_po_count": purchase_kpi.get("total_po", 0)
        },
        "cash_variance": {
            "total_shortage": variance_kpi.get("total_shortage", 0),
            "total_overage": variance_kpi.get("total_overage", 0),
            "net_variance": variance_kpi.get("total_overage", 0) - variance_kpi.get("total_shortage", 0),
            "variance_events": variance_kpi.get("variance_count", 0)
        },
        "inventory": {
            "total_value": total_inventory_value
        },
        "entity_counts": {
            "active_branches": active_branches,
            "active_products": active_products
        },
        "gross_profit_estimate": sales_kpi.get("total_sales", 0) - purchase_kpi.get("total_purchase", 0)
    }
