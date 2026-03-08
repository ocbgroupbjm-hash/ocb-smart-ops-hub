# OCB TITAN - Finance & Cash Management API
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from database import (
    branches, cash_movements, expenses, journal_entries, 
    transactions, get_next_sequence
)
from utils.auth import get_current_user
from models.titan_models import CashMovement, Expense, JournalEntry
from datetime import datetime, timezone

router = APIRouter(prefix="/finance", tags=["Finance"])

class CashIn(BaseModel):
    amount: float
    category: str = "other"
    description: str

class CashOut(BaseModel):
    amount: float
    category: str
    description: str

class ExpenseCreate(BaseModel):
    category: str
    description: str
    amount: float
    payment_method: str = "cash"
    reference: str = ""
    date: Optional[str] = None

# ==================== CASH MANAGEMENT ====================

@router.get("/cash/balance")
async def get_cash_balance(branch_id: str = "", user: dict = Depends(get_current_user)):
    """Get current cash balance for branch"""
    bid = branch_id or user.get("branch_id")
    
    branch = await branches.find_one({"id": bid}, {"_id": 0, "id": 1, "name": 1, "cash_balance": 1})
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")
    
    return {
        "branch_id": branch["id"],
        "branch_name": branch.get("name", ""),
        "cash_balance": branch.get("cash_balance", 0)
    }

@router.post("/cash/in")
async def cash_in(data: CashIn, user: dict = Depends(get_current_user)):
    """Record cash in (deposit, opening balance, etc)"""
    branch_id = user.get("branch_id")
    if not branch_id:
        raise HTTPException(status_code=400, detail="User not assigned to a branch")
    
    branch = await branches.find_one({"id": branch_id}, {"_id": 0})
    current_balance = branch.get("cash_balance", 0) if branch else 0
    new_balance = current_balance + data.amount
    
    await branches.update_one({"id": branch_id}, {"$set": {"cash_balance": new_balance}})
    
    movement = CashMovement(
        branch_id=branch_id,
        movement_type="cash_in",
        amount=data.amount,
        balance_after=new_balance,
        category=data.category,
        description=data.description,
        user_id=user.get("user_id", ""),
        user_name=user.get("name", "")
    )
    
    await cash_movements.insert_one(movement.model_dump())
    
    return {"message": "Cash in recorded", "new_balance": new_balance}

@router.post("/cash/out")
async def cash_out(data: CashOut, user: dict = Depends(get_current_user)):
    """Record cash out (withdrawal, expenses paid in cash)"""
    branch_id = user.get("branch_id")
    if not branch_id:
        raise HTTPException(status_code=400, detail="User not assigned to a branch")
    
    branch = await branches.find_one({"id": branch_id}, {"_id": 0})
    current_balance = branch.get("cash_balance", 0) if branch else 0
    
    if data.amount > current_balance:
        raise HTTPException(status_code=400, detail="Insufficient cash balance")
    
    new_balance = current_balance - data.amount
    
    await branches.update_one({"id": branch_id}, {"$set": {"cash_balance": new_balance}})
    
    movement = CashMovement(
        branch_id=branch_id,
        movement_type="cash_out",
        amount=data.amount,
        balance_after=new_balance,
        category=data.category,
        description=data.description,
        user_id=user.get("user_id", ""),
        user_name=user.get("name", "")
    )
    
    await cash_movements.insert_one(movement.model_dump())
    
    return {"message": "Cash out recorded", "new_balance": new_balance}

@router.get("/cash/movements")
async def get_cash_movements(
    branch_id: str = "",
    date_from: str = "",
    date_to: str = "",
    skip: int = 0,
    limit: int = 100,
    user: dict = Depends(get_current_user)
):
    """Get cash movement history"""
    bid = branch_id or user.get("branch_id")
    query = {"branch_id": bid}
    
    if date_from:
        query["created_at"] = {"$gte": date_from}
    if date_to:
        if "created_at" in query:
            query["created_at"]["$lte"] = date_to
        else:
            query["created_at"] = {"$lte": date_to}
    
    items = await cash_movements.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    total = await cash_movements.count_documents(query)
    
    return {"items": items, "total": total}

# ==================== EXPENSES ====================

@router.get("/expenses")
async def list_expenses(
    branch_id: str = "",
    category: str = "",
    date_from: str = "",
    date_to: str = "",
    skip: int = 0,
    limit: int = 100,
    user: dict = Depends(get_current_user)
):
    bid = branch_id or user.get("branch_id")
    query = {"branch_id": bid}
    
    if category:
        query["category"] = category
    
    if date_from:
        query["date"] = {"$gte": date_from}
    if date_to:
        if "date" in query:
            query["date"]["$lte"] = date_to
        else:
            query["date"] = {"$lte": date_to}
    
    items = await expenses.find(query, {"_id": 0}).sort("date", -1).skip(skip).limit(limit).to_list(limit)
    total = await expenses.count_documents(query)
    
    # Calculate totals
    total_amount = sum(item.get("amount", 0) for item in items)
    
    return {"items": items, "total": total, "total_amount": total_amount}

@router.post("/expenses")
async def create_expense(data: ExpenseCreate, user: dict = Depends(get_current_user)):
    branch_id = user.get("branch_id")
    if not branch_id:
        raise HTTPException(status_code=400, detail="User not assigned to a branch")
    
    expense = Expense(
        branch_id=branch_id,
        category=data.category,
        description=data.description,
        amount=data.amount,
        payment_method=data.payment_method,
        reference=data.reference,
        date=data.date or datetime.now(timezone.utc).isoformat()[:10],
        user_id=user.get("user_id", "")
    )
    
    await expenses.insert_one(expense.model_dump())
    
    # If paid by cash, record cash out
    if data.payment_method == "cash":
        branch = await branches.find_one({"id": branch_id}, {"_id": 0})
        current_balance = branch.get("cash_balance", 0) if branch else 0
        new_balance = current_balance - data.amount
        
        await branches.update_one({"id": branch_id}, {"$set": {"cash_balance": new_balance}})
        
        movement = CashMovement(
            branch_id=branch_id,
            movement_type="cash_out",
            amount=data.amount,
            balance_after=new_balance,
            category="expense",
            description=f"{data.category}: {data.description}",
            reference_id=expense.id,
            reference_type="expense",
            user_id=user.get("user_id", ""),
            user_name=user.get("name", "")
        )
        await cash_movements.insert_one(movement.model_dump())
    
    return {"id": expense.id, "message": "Expense recorded"}

# ==================== REPORTS ====================

@router.get("/reports/daily")
async def get_daily_report(date: str = "", branch_id: str = "", user: dict = Depends(get_current_user)):
    """Get daily financial summary"""
    bid = branch_id or user.get("branch_id")
    report_date = date or datetime.now(timezone.utc).isoformat()[:10]
    
    # Sales
    sales_pipeline = [
        {
            "$match": {
                "branch_id": bid,
                "status": "completed",
                "created_at": {"$regex": f"^{report_date}"}
            }
        },
        {
            "$group": {
                "_id": None,
                "total_sales": {"$sum": "$total"},
                "total_cost": {"$sum": "$total_cost"},
                "total_profit": {"$sum": "$profit"},
                "transaction_count": {"$sum": 1}
            }
        }
    ]
    
    sales_result = await transactions.aggregate(sales_pipeline).to_list(1)
    sales = sales_result[0] if sales_result else {
        "total_sales": 0,
        "total_cost": 0,
        "total_profit": 0,
        "transaction_count": 0
    }
    
    # Expenses
    expense_pipeline = [
        {
            "$match": {
                "branch_id": bid,
                "date": {"$regex": f"^{report_date}"}
            }
        },
        {
            "$group": {
                "_id": "$category",
                "amount": {"$sum": "$amount"}
            }
        }
    ]
    
    expense_result = await expenses.aggregate(expense_pipeline).to_list(100)
    expense_by_category = {item["_id"]: item["amount"] for item in expense_result}
    total_expenses = sum(item["amount"] for item in expense_result)
    
    # Cash movements summary
    cash_pipeline = [
        {
            "$match": {
                "branch_id": bid,
                "created_at": {"$regex": f"^{report_date}"}
            }
        },
        {
            "$group": {
                "_id": "$movement_type",
                "amount": {"$sum": "$amount"}
            }
        }
    ]
    
    cash_result = await cash_movements.aggregate(cash_pipeline).to_list(10)
    cash_summary = {item["_id"]: item["amount"] for item in cash_result}
    
    # Get current cash balance
    branch = await branches.find_one({"id": bid}, {"_id": 0, "name": 1, "cash_balance": 1})
    
    return {
        "date": report_date,
        "branch_id": bid,
        "branch_name": branch.get("name", "") if branch else "",
        "sales": {
            "total": sales.get("total_sales", 0),
            "cost": sales.get("total_cost", 0),
            "profit": sales.get("total_profit", 0),
            "transactions": sales.get("transaction_count", 0)
        },
        "expenses": {
            "total": total_expenses,
            "by_category": expense_by_category
        },
        "cash": {
            "in": cash_summary.get("cash_in", 0),
            "out": cash_summary.get("cash_out", 0),
            "current_balance": branch.get("cash_balance", 0) if branch else 0
        },
        "net_profit": sales.get("total_profit", 0) - total_expenses
    }

@router.get("/reports/profit-loss")
async def get_profit_loss(
    date_from: str,
    date_to: str,
    branch_id: str = "",
    user: dict = Depends(get_current_user)
):
    """Get profit & loss statement"""
    query_branches = [branch_id] if branch_id else []
    
    if not query_branches:
        # Get all accessible branches
        role = user.get("role", "")
        if role in ["owner", "admin"]:
            all_branches = await branches.find({"is_active": True}, {"_id": 0, "id": 1}).to_list(500)
            query_branches = [b["id"] for b in all_branches]
        else:
            query_branches = user.get("branch_ids", [])
            if user.get("branch_id"):
                query_branches.append(user["branch_id"])
    
    # Revenue (Sales)
    revenue_pipeline = [
        {
            "$match": {
                "branch_id": {"$in": query_branches},
                "status": "completed",
                "created_at": {"$gte": date_from, "$lte": date_to}
            }
        },
        {
            "$group": {
                "_id": None,
                "gross_sales": {"$sum": "$subtotal"},
                "discounts": {"$sum": "$discount_amount"},
                "net_sales": {"$sum": "$total"},
                "cost_of_goods": {"$sum": "$total_cost"},
                "gross_profit": {"$sum": "$profit"}
            }
        }
    ]
    
    revenue_result = await transactions.aggregate(revenue_pipeline).to_list(1)
    revenue = revenue_result[0] if revenue_result else {
        "gross_sales": 0,
        "discounts": 0,
        "net_sales": 0,
        "cost_of_goods": 0,
        "gross_profit": 0
    }
    
    # Expenses
    expense_pipeline = [
        {
            "$match": {
                "branch_id": {"$in": query_branches},
                "date": {"$gte": date_from, "$lte": date_to}
            }
        },
        {
            "$group": {
                "_id": "$category",
                "amount": {"$sum": "$amount"}
            }
        },
        {"$sort": {"amount": -1}}
    ]
    
    expense_result = await expenses.aggregate(expense_pipeline).to_list(100)
    total_expenses = sum(item["amount"] for item in expense_result)
    
    net_profit = revenue.get("gross_profit", 0) - total_expenses
    
    return {
        "period": {"from": date_from, "to": date_to},
        "revenue": {
            "gross_sales": revenue.get("gross_sales", 0),
            "discounts": revenue.get("discounts", 0),
            "net_sales": revenue.get("net_sales", 0)
        },
        "cost_of_goods_sold": revenue.get("cost_of_goods", 0),
        "gross_profit": revenue.get("gross_profit", 0),
        "operating_expenses": {
            "total": total_expenses,
            "breakdown": [{"category": item["_id"], "amount": item["amount"]} for item in expense_result]
        },
        "net_profit": net_profit,
        "profit_margin": (net_profit / revenue.get("net_sales", 1)) * 100 if revenue.get("net_sales", 0) > 0 else 0
    }
