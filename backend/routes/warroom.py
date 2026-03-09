# OCB GROUP SUPER AI - Warroom Dashboard Routes
# Real-time company monitoring and analytics

from fastapi import APIRouter, HTTPException
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import uuid

from database import get_db

router = APIRouter(prefix="/api/warroom", tags=["Warroom Dashboard"])

def gen_id() -> str:
    return str(uuid.uuid4())

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

# ==================== WARROOM ENDPOINTS ====================

@router.get("/snapshot")
async def get_warroom_snapshot():
    """Get real-time warroom snapshot of entire company"""
    db = get_db()
    
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday = today - timedelta(days=1)
    
    # Get branch counts
    total_branches = await db['branches'].count_documents({})
    active_branches = await db['branches'].count_documents({"is_active": True})
    
    # Today's transactions
    today_transactions = await db['transactions'].find({
        "created_at": {"$gte": today.isoformat()},
        "status": "completed"
    }).to_list(None)
    
    today_revenue = sum(t.get("total", 0) for t in today_transactions)
    today_profit = sum(t.get("profit", 0) for t in today_transactions)
    today_count = len(today_transactions)
    
    # Yesterday's transactions for comparison
    yesterday_transactions = await db['transactions'].find({
        "created_at": {"$gte": yesterday.isoformat(), "$lt": today.isoformat()},
        "status": "completed"
    }).to_list(None)
    
    yesterday_revenue = sum(t.get("total", 0) for t in yesterday_transactions)
    
    # Revenue change
    revenue_change = 0
    if yesterday_revenue > 0:
        revenue_change = ((today_revenue - yesterday_revenue) / yesterday_revenue) * 100
    
    # Top branches by revenue (today)
    branch_revenue = {}
    for t in today_transactions:
        branch_id = t.get("branch_id", "unknown")
        if branch_id not in branch_revenue:
            branch_revenue[branch_id] = {"revenue": 0, "transactions": 0}
        branch_revenue[branch_id]["revenue"] += t.get("total", 0)
        branch_revenue[branch_id]["transactions"] += 1
    
    # Get branch names
    branches = await db['branches'].find({}, {"_id": 0, "id": 1, "name": 1, "code": 1}).to_list(None)
    branch_map = {b["id"]: b for b in branches}
    
    top_branches = []
    for branch_id, data in sorted(branch_revenue.items(), key=lambda x: x[1]["revenue"], reverse=True)[:5]:
        branch_info = branch_map.get(branch_id, {})
        top_branches.append({
            "branch_id": branch_id,
            "branch_name": branch_info.get("name", "Unknown"),
            "branch_code": branch_info.get("code", ""),
            "revenue": data["revenue"],
            "transactions": data["transactions"]
        })
    
    # Stock alerts
    low_stock_count = await db['stock_alerts'].count_documents({
        "is_resolved": False,
        "alert_type": {"$in": ["low_stock", "out_of_stock"]}
    })
    
    # Active conversations
    active_conversations = await db['sales_conversations'].count_documents({
        "status": "active"
    })
    
    # Pending orders
    pending_orders = await db['orders'].count_documents({
        "status": {"$in": ["pending", "processing"]}
    })
    
    # Pending payments
    pending_payments = await db['invoices'].count_documents({
        "payment_status": "pending"
    })
    
    # Active campaigns
    active_campaigns = await db['marketing_campaigns'].count_documents({
        "status": "running"
    })
    
    return {
        "snapshot_time": now_iso(),
        
        # Branches
        "total_branches": total_branches,
        "active_branches": active_branches,
        
        # Today's Sales
        "today_revenue": today_revenue,
        "today_transactions": today_count,
        "today_profit": today_profit,
        
        # Comparison
        "yesterday_revenue": yesterday_revenue,
        "revenue_change_percent": round(revenue_change, 2),
        
        # Branch Performance
        "top_branches": top_branches,
        
        # Alerts
        "critical_stock_alerts": low_stock_count,
        
        # Active Operations
        "active_conversations": active_conversations,
        "pending_orders": pending_orders,
        "pending_payments": pending_payments,
        "active_campaigns": active_campaigns
    }

@router.get("/branches/performance")
async def get_branches_performance(period: str = "today"):
    """Get performance metrics for all branches"""
    db = get_db()
    
    # Calculate date range
    now = datetime.now(timezone.utc)
    if period == "today":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "week":
        start_date = now - timedelta(days=7)
    elif period == "month":
        start_date = now - timedelta(days=30)
    else:
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Get all branches
    branches = await db['branches'].find(
        {"is_active": True},
        {"_id": 0}
    ).to_list(None)
    
    # Get transactions
    transactions = await db['transactions'].find({
        "created_at": {"$gte": start_date.isoformat()},
        "status": "completed"
    }, {"_id": 0}).to_list(None)
    
    # Calculate per branch
    branch_metrics = {}
    for branch in branches:
        branch_id = branch["id"]
        branch_metrics[branch_id] = {
            "branch_id": branch_id,
            "branch_name": branch["name"],
            "branch_code": branch.get("code", ""),
            "city": branch.get("city", ""),
            "revenue": 0,
            "profit": 0,
            "transactions": 0,
            "average_transaction": 0,
            "target": branch.get("target_monthly", 0),
            "achievement_percent": 0
        }
    
    for t in transactions:
        branch_id = t.get("branch_id")
        if branch_id in branch_metrics:
            branch_metrics[branch_id]["revenue"] += t.get("total", 0)
            branch_metrics[branch_id]["profit"] += t.get("profit", 0)
            branch_metrics[branch_id]["transactions"] += 1
    
    # Calculate averages and achievement
    for branch_id, metrics in branch_metrics.items():
        if metrics["transactions"] > 0:
            metrics["average_transaction"] = metrics["revenue"] / metrics["transactions"]
        if metrics["target"] > 0:
            metrics["achievement_percent"] = (metrics["revenue"] / metrics["target"]) * 100
    
    # Sort by revenue
    sorted_branches = sorted(branch_metrics.values(), key=lambda x: x["revenue"], reverse=True)
    
    return {
        "period": period,
        "start_date": start_date.isoformat(),
        "branches": sorted_branches,
        "total_revenue": sum(b["revenue"] for b in sorted_branches),
        "total_transactions": sum(b["transactions"] for b in sorted_branches)
    }

@router.get("/sales/hourly")
async def get_hourly_sales():
    """Get hourly sales breakdown for today"""
    db = get_db()
    
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    
    transactions = await db['transactions'].find({
        "created_at": {"$gte": today.isoformat()},
        "status": "completed"
    }, {"_id": 0, "created_at": 1, "total": 1}).to_list(None)
    
    # Group by hour
    hourly_data = {h: {"hour": h, "revenue": 0, "transactions": 0} for h in range(24)}
    
    for t in transactions:
        try:
            created_at = datetime.fromisoformat(t["created_at"].replace("Z", "+00:00"))
            hour = created_at.hour
            hourly_data[hour]["revenue"] += t.get("total", 0)
            hourly_data[hour]["transactions"] += 1
        except:
            pass
    
    return {
        "date": today.isoformat(),
        "hourly_data": list(hourly_data.values())
    }

@router.get("/products/top")
async def get_top_products(limit: int = 10, period: str = "today"):
    """Get top selling products"""
    db = get_db()
    
    now = datetime.now(timezone.utc)
    if period == "today":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "week":
        start_date = now - timedelta(days=7)
    else:
        start_date = now - timedelta(days=30)
    
    transactions = await db['transactions'].find({
        "created_at": {"$gte": start_date.isoformat()},
        "status": "completed"
    }, {"_id": 0, "items": 1}).to_list(None)
    
    # Aggregate products
    product_sales = {}
    for t in transactions:
        for item in t.get("items", []):
            product_id = item.get("product_id")
            if product_id not in product_sales:
                product_sales[product_id] = {
                    "product_id": product_id,
                    "product_name": item.get("product_name", ""),
                    "product_code": item.get("product_code", ""),
                    "quantity_sold": 0,
                    "revenue": 0
                }
            product_sales[product_id]["quantity_sold"] += item.get("quantity", 0)
            product_sales[product_id]["revenue"] += item.get("total", item.get("subtotal", 0))
    
    # Sort by quantity sold
    top_products = sorted(product_sales.values(), key=lambda x: x["quantity_sold"], reverse=True)[:limit]
    
    return {
        "period": period,
        "top_products": top_products
    }

@router.get("/alerts")
async def get_alerts():
    """Get all active alerts"""
    db = get_db()
    
    # Stock alerts
    stock_alerts = await db['stock_alerts'].find(
        {"is_resolved": False},
        {"_id": 0}
    ).sort("created_at", -1).limit(20).to_list(None)
    
    # Payment alerts (pending > 24h)
    yesterday = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    pending_payments = await db['invoices'].find({
        "payment_status": "pending",
        "created_at": {"$lt": yesterday}
    }, {"_id": 0, "invoice_number": 1, "total": 1, "customer_name": 1, "created_at": 1}).limit(10).to_list(None)
    
    # Order alerts (processing > 2h)
    two_hours_ago = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    delayed_orders = await db['orders'].find({
        "status": "processing",
        "created_at": {"$lt": two_hours_ago}
    }, {"_id": 0, "order_number": 1, "customer_name": 1, "created_at": 1}).limit(10).to_list(None)
    
    return {
        "stock_alerts": stock_alerts,
        "pending_payments": pending_payments,
        "delayed_orders": delayed_orders,
        "total_alerts": len(stock_alerts) + len(pending_payments) + len(delayed_orders)
    }
