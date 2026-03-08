from fastapi import APIRouter, Depends
from typing import Dict, List
from models.analytics import DashboardStats
from database import (
    customers_collection, 
    conversations_collection, 
    branches_collection,
    messages_collection
)
from utils.dependencies import get_current_user
from datetime import datetime, timedelta, timezone

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    company_id = current_user.get("company_id")
    
    # Total customers
    total_customers = await customers_collection.count_documents({"company_id": company_id})
    
    # Total conversations
    total_conversations = await conversations_collection.count_documents({"company_id": company_id})
    
    # Active branches
    active_branches = await branches_collection.count_documents(
        {"company_id": company_id, "is_active": True}
    )
    
    # AI queries today
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    ai_queries_today = await messages_collection.count_documents({
        "timestamp": {"$gte": today_start.isoformat()}
    })
    
    return DashboardStats(
        total_customers=total_customers,
        total_conversations=total_conversations,
        total_sales=0.0,  # Mock for now
        active_branches=active_branches,
        ai_queries_today=ai_queries_today,
        avg_sentiment="positive"
    )

@router.get("/conversations-over-time")
async def get_conversations_over_time(current_user: dict = Depends(get_current_user)):
    company_id = current_user.get("company_id")
    
    # Get last 7 days
    days = []
    for i in range(6, -1, -1):
        day = datetime.now(timezone.utc) - timedelta(days=i)
        days.append(day.strftime("%Y-%m-%d"))
    
    # Mock data for now
    data = []
    for day in days:
        count = await conversations_collection.count_documents({
            "company_id": company_id,
            "created_at": {"$regex": f"^{day}"}
        })
        data.append({"date": day, "count": count})
    
    return data

@router.get("/customer-segments")
async def get_customer_segments(current_user: dict = Depends(get_current_user)):
    company_id = current_user.get("company_id")
    
    segments = ["vip", "regular", "new", "at_risk"]
    data = []
    
    for segment in segments:
        count = await customers_collection.count_documents({
            "company_id": company_id,
            "segment": segment
        })
        data.append({"segment": segment, "count": count})
    
    return data

@router.get("/branch-performance")
async def get_branch_performance(current_user: dict = Depends(get_current_user)):
    company_id = current_user.get("company_id")
    
    branches = await branches_collection.find(
        {"company_id": company_id, "is_active": True},
        {"_id": 0}
    ).to_list(100)
    
    # Mock sales data
    import random
    for branch in branches:
        branch["sales"] = random.randint(50000, 500000)
        branch["customers"] = random.randint(50, 500)
    
    # Sort by sales
    branches.sort(key=lambda x: x.get("sales", 0), reverse=True)
    
    return branches[:10]  # Top 10