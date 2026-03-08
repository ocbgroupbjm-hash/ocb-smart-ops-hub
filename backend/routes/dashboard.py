# OCB TITAN - Dashboard & Analytics API
from fastapi import APIRouter, HTTPException, Depends
from database import (
    transactions, products, product_stocks, customers, branches, 
    users, expenses, cash_movements
)
from utils.auth import get_current_user
from datetime import datetime, timezone, timedelta

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/owner")
async def get_owner_dashboard(user: dict = Depends(get_current_user)):
    """Executive dashboard for owners - real-time business overview"""
    today = datetime.now(timezone.utc).isoformat()[:10]
    
    # Get all active branches
    all_branches = await branches.find({"is_active": True}, {"_id": 0}).to_list(500)
    branch_ids = [b["id"] for b in all_branches]
    
    # Today's Sales
    today_sales_pipeline = [
        {
            "$match": {
                "status": "completed",
                "created_at": {"$regex": f"^{today}"}
            }
        },
        {
            "$group": {
                "_id": None,
                "total_sales": {"$sum": "$total"},
                "total_profit": {"$sum": "$profit"},
                "transaction_count": {"$sum": 1}
            }
        }
    ]
    
    today_result = await transactions.aggregate(today_sales_pipeline).to_list(1)
    today_data = today_result[0] if today_result else {"total_sales": 0, "total_profit": 0, "transaction_count": 0}
    
    # Sales by Branch (Today)
    branch_sales_pipeline = [
        {
            "$match": {
                "status": "completed",
                "created_at": {"$regex": f"^{today}"}
            }
        },
        {
            "$group": {
                "_id": "$branch_id",
                "sales": {"$sum": "$total"},
                "profit": {"$sum": "$profit"},
                "transactions": {"$sum": 1}
            }
        },
        {"$sort": {"sales": -1}}
    ]
    
    branch_sales = await transactions.aggregate(branch_sales_pipeline).to_list(100)
    
    # Enrich with branch names
    for item in branch_sales:
        branch = await branches.find_one({"id": item["_id"]}, {"_id": 0, "name": 1, "code": 1})
        item["branch_name"] = branch.get("name", "Unknown") if branch else "Unknown"
        item["branch_code"] = branch.get("code", "") if branch else ""
    
    # Best Selling Products (Today)
    best_selling_pipeline = [
        {
            "$match": {
                "status": "completed",
                "created_at": {"$regex": f"^{today}"}
            }
        },
        {"$unwind": "$items"},
        {
            "$group": {
                "_id": "$items.product_id",
                "product_name": {"$first": "$items.product_name"},
                "product_code": {"$first": "$items.product_code"},
                "quantity_sold": {"$sum": "$items.quantity"},
                "revenue": {"$sum": "$items.total"}
            }
        },
        {"$sort": {"quantity_sold": -1}},
        {"$limit": 10}
    ]
    
    best_selling = await transactions.aggregate(best_selling_pipeline).to_list(10)
    
    # Low Stock Alerts
    low_stock_pipeline = [
        {
            "$lookup": {
                "from": "products",
                "localField": "product_id",
                "foreignField": "id",
                "as": "product"
            }
        },
        {"$unwind": "$product"},
        {"$match": {"product.is_active": True, "product.track_stock": True}},
        {"$match": {"$expr": {"$lte": ["$quantity", "$product.min_stock"]}}},
        {
            "$lookup": {
                "from": "branches",
                "localField": "branch_id",
                "foreignField": "id",
                "as": "branch"
            }
        },
        {"$unwind": "$branch"},
        {
            "$project": {
                "_id": 0,
                "product_name": "$product.name",
                "product_code": "$product.code",
                "branch_name": "$branch.name",
                "quantity": 1,
                "min_stock": "$product.min_stock"
            }
        },
        {"$sort": {"quantity": 1}},
        {"$limit": 20}
    ]
    
    low_stock = await product_stocks.aggregate(low_stock_pipeline).to_list(20)
    
    # Total Cash Balance (All Branches)
    total_cash = sum(b.get("cash_balance", 0) for b in all_branches)
    
    # Today's Expenses
    today_expenses_pipeline = [
        {
            "$match": {
                "date": {"$regex": f"^{today}"}
            }
        },
        {
            "$group": {
                "_id": None,
                "total": {"$sum": "$amount"}
            }
        }
    ]
    
    expense_result = await expenses.aggregate(today_expenses_pipeline).to_list(1)
    today_expenses = expense_result[0]["total"] if expense_result else 0
    
    # Counts
    total_products = await products.count_documents({"is_active": True})
    total_customers = await customers.count_documents({"is_active": True})
    total_employees = await users.count_documents({"is_active": True})
    
    return {
        "date": today,
        "summary": {
            "today_sales": today_data.get("total_sales", 0),
            "today_profit": today_data.get("total_profit", 0),
            "today_transactions": today_data.get("transaction_count", 0),
            "today_expenses": today_expenses,
            "net_profit": today_data.get("total_profit", 0) - today_expenses,
            "total_cash_balance": total_cash
        },
        "counts": {
            "branches": len(all_branches),
            "products": total_products,
            "customers": total_customers,
            "employees": total_employees
        },
        "sales_by_branch": branch_sales,
        "best_selling": best_selling,
        "low_stock_alerts": low_stock
    }

@router.get("/branch")
async def get_branch_dashboard(branch_id: str = "", user: dict = Depends(get_current_user)):
    """Dashboard for branch managers and cashiers"""
    bid = branch_id or user.get("branch_id")
    today = datetime.now(timezone.utc).isoformat()[:10]
    
    # Branch info
    branch = await branches.find_one({"id": bid}, {"_id": 0})
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")
    
    # Today's Sales
    today_pipeline = [
        {
            "$match": {
                "branch_id": bid,
                "status": "completed",
                "created_at": {"$regex": f"^{today}"}
            }
        },
        {
            "$group": {
                "_id": None,
                "total_sales": {"$sum": "$total"},
                "total_profit": {"$sum": "$profit"},
                "transaction_count": {"$sum": 1},
                "items_sold": {"$sum": {"$size": "$items"}}
            }
        }
    ]
    
    today_result = await transactions.aggregate(today_pipeline).to_list(1)
    today_data = today_result[0] if today_result else {
        "total_sales": 0, "total_profit": 0, "transaction_count": 0, "items_sold": 0
    }
    
    # Sales by Payment Method (Today)
    payment_pipeline = [
        {
            "$match": {
                "branch_id": bid,
                "status": "completed",
                "created_at": {"$regex": f"^{today}"}
            }
        },
        {"$unwind": "$payments"},
        {
            "$group": {
                "_id": "$payments.method",
                "amount": {"$sum": "$payments.amount"},
                "count": {"$sum": 1}
            }
        }
    ]
    
    payment_breakdown = await transactions.aggregate(payment_pipeline).to_list(10)
    
    # Recent Transactions
    recent_tx = await transactions.find(
        {"branch_id": bid},
        {"_id": 0, "id": 1, "invoice_number": 1, "total": 1, "status": 1, "customer_name": 1, "created_at": 1}
    ).sort("created_at", -1).limit(10).to_list(10)
    
    # Low Stock for this branch
    low_stock_pipeline = [
        {"$match": {"branch_id": bid}},
        {
            "$lookup": {
                "from": "products",
                "localField": "product_id",
                "foreignField": "id",
                "as": "product"
            }
        },
        {"$unwind": "$product"},
        {"$match": {"product.is_active": True}},
        {"$match": {"$expr": {"$lte": ["$quantity", "$product.min_stock"]}}},
        {
            "$project": {
                "_id": 0,
                "product_name": "$product.name",
                "product_code": "$product.code",
                "quantity": 1,
                "min_stock": "$product.min_stock"
            }
        },
        {"$limit": 10}
    ]
    
    low_stock = await product_stocks.aggregate(low_stock_pipeline).to_list(10)
    
    return {
        "date": today,
        "branch": {
            "id": branch["id"],
            "name": branch.get("name", ""),
            "code": branch.get("code", ""),
            "cash_balance": branch.get("cash_balance", 0)
        },
        "today": {
            "sales": today_data.get("total_sales", 0),
            "profit": today_data.get("total_profit", 0),
            "transactions": today_data.get("transaction_count", 0),
            "items_sold": today_data.get("items_sold", 0)
        },
        "payment_breakdown": payment_breakdown,
        "recent_transactions": recent_tx,
        "low_stock": low_stock
    }

@router.get("/sales-trend")
async def get_sales_trend(days: int = 7, branch_id: str = "", user: dict = Depends(get_current_user)):
    """Get sales trend for last N days"""
    bid = branch_id or user.get("branch_id")
    
    # Calculate date range
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    match_query = {
        "status": "completed",
        "created_at": {"$gte": start_date.isoformat(), "$lte": end_date.isoformat()}
    }
    
    if bid:
        match_query["branch_id"] = bid
    
    pipeline = [
        {"$match": match_query},
        {
            "$group": {
                "_id": {"$substr": ["$created_at", 0, 10]},
                "sales": {"$sum": "$total"},
                "profit": {"$sum": "$profit"},
                "transactions": {"$sum": 1}
            }
        },
        {"$sort": {"_id": 1}}
    ]
    
    result = await transactions.aggregate(pipeline).to_list(days + 1)
    
    return {
        "period": {"from": start_date.isoformat()[:10], "to": end_date.isoformat()[:10]},
        "data": [{"date": item["_id"], "sales": item["sales"], "profit": item["profit"], "transactions": item["transactions"]} for item in result]
    }

@router.get("/top-products")
async def get_top_products(
    days: int = 30,
    limit: int = 10,
    branch_id: str = "",
    user: dict = Depends(get_current_user)
):
    """Get top selling products"""
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    match_query = {
        "status": "completed",
        "created_at": {"$gte": start_date.isoformat()}
    }
    
    if branch_id:
        match_query["branch_id"] = branch_id
    
    pipeline = [
        {"$match": match_query},
        {"$unwind": "$items"},
        {
            "$group": {
                "_id": "$items.product_id",
                "product_name": {"$first": "$items.product_name"},
                "product_code": {"$first": "$items.product_code"},
                "quantity_sold": {"$sum": "$items.quantity"},
                "revenue": {"$sum": "$items.total"}
            }
        },
        {"$sort": {"revenue": -1}},
        {"$limit": limit}
    ]
    
    result = await transactions.aggregate(pipeline).to_list(limit)
    
    return result

@router.get("/top-customers")
async def get_top_customers(
    days: int = 30,
    limit: int = 10,
    user: dict = Depends(get_current_user)
):
    """Get top customers by spending"""
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    pipeline = [
        {
            "$match": {
                "status": "completed",
                "customer_id": {"$ne": None},
                "created_at": {"$gte": start_date.isoformat()}
            }
        },
        {
            "$group": {
                "_id": "$customer_id",
                "customer_name": {"$first": "$customer_name"},
                "total_spent": {"$sum": "$total"},
                "transaction_count": {"$sum": 1}
            }
        },
        {"$sort": {"total_spent": -1}},
        {"$limit": limit}
    ]
    
    result = await transactions.aggregate(pipeline).to_list(limit)
    
    # Enrich with customer details
    for item in result:
        if item["_id"]:
            customer = await customers.find_one({"id": item["_id"]}, {"_id": 0, "phone": 1, "segment": 1})
            if customer:
                item["phone"] = customer.get("phone", "")
                item["segment"] = customer.get("segment", "")
    
    return result

@router.get("/cashier-performance")
async def get_cashier_performance(date: str = "", branch_id: str = "", user: dict = Depends(get_current_user)):
    """Get cashier performance metrics"""
    report_date = date or datetime.now(timezone.utc).isoformat()[:10]
    
    match_query = {
        "status": "completed",
        "created_at": {"$regex": f"^{report_date}"}
    }
    
    if branch_id:
        match_query["branch_id"] = branch_id
    
    pipeline = [
        {"$match": match_query},
        {
            "$group": {
                "_id": "$cashier_id",
                "cashier_name": {"$first": "$cashier_name"},
                "total_sales": {"$sum": "$total"},
                "transaction_count": {"$sum": 1},
                "avg_transaction": {"$avg": "$total"}
            }
        },
        {"$sort": {"total_sales": -1}}
    ]
    
    result = await transactions.aggregate(pipeline).to_list(100)
    
    return {"date": report_date, "cashiers": result}
