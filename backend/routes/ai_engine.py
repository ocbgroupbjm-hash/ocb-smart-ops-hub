# OCB TITAN ERP - AI Business Engine API
# =====================================
# Version: 1.0.0

"""
AI BUSINESS ENGINE API

Endpoints:
- GET /api/ai/sales/insights
- GET /api/ai/inventory/insights
- GET /api/ai/finance/insights
- GET /api/ai/ceo/dashboard
- GET /api/ai/config
- GET /api/ai/logs

All endpoints are READ-ONLY
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime, timezone
from database import get_db
from utils.auth import get_current_user
import time
import os

from ai_service import (
    AIDataAccessLayer,
    AIInsightsEngine,
    AIDecisionLogger,
    AIRBACGateway,
    AIKillSwitch,
    AIEngineDisabledException,
    get_ai_config,
    is_ai_enabled
)

router = APIRouter(prefix="/api/ai", tags=["AI Business Engine"])


def get_ai_services():
    """Initialize AI services"""
    db = get_db()
    data_layer = AIDataAccessLayer(db)
    insights = AIInsightsEngine(data_layer)
    logger = AIDecisionLogger(db)
    return data_layer, insights, logger


# ==================== CONFIG ====================

@router.get("/config")
async def get_ai_configuration(
    user: dict = Depends(get_current_user)
):
    """
    Get AI Engine configuration
    """
    AIRBACGateway.check_access(user, "config")
    
    config = get_ai_config()
    return {
        "enabled": config["enabled"],
        "version": config["version"],
        "model_version": config["model_version"],
        "read_only": config["read_only"],
        "allowed_roles": ["owner", "super_admin", "auditor", "manager"],
        "your_role": user.get("role_code") or user.get("role"),
        "your_modules": AIRBACGateway.get_allowed_modules(user)
    }


@router.get("/status")
async def get_ai_status():
    """
    Get AI Engine status (public endpoint for health check)
    """
    return {
        "status": "enabled" if is_ai_enabled() else "disabled",
        "version": get_ai_config()["version"],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# ==================== SALES AI ====================

@router.get("/sales/insights")
async def get_sales_insights(
    days: int = Query(30, ge=1, le=365, description="Analysis period in days"),
    user: dict = Depends(get_current_user)
):
    """
    SALES AI - Get sales insights
    
    Returns:
    - top_products: Best selling products
    - slow_products: Products with low sales
    - sales_trend: Daily sales trend
    - margin_analysis: Profit margin by product
    """
    try:
        AIKillSwitch.check_or_raise()
        AIRBACGateway.check_access(user, "sales")
        
        start_time = time.time()
        
        data_layer, insights, logger = get_ai_services()
        result = await insights.get_sales_insights(days)
        
        execution_time = (time.time() - start_time) * 1000
        
        # Log decision
        await logger.log_decision(
            tenant_id=user.get("tenant_id", ""),
            user_id=user.get("user_id") or user.get("id", ""),
            endpoint="/api/ai/sales/insights",
            model_version=result["model_version"],
            data_window=f"{days} days",
            features_used=["sales_invoices", "products"],
            output=result,
            execution_time_ms=execution_time
        )
        
        return result
        
    except AIEngineDisabledException:
        raise HTTPException(status_code=503, detail="AI Engine is disabled")


# ==================== INVENTORY AI ====================

@router.get("/inventory/insights")
async def get_inventory_insights(
    user: dict = Depends(get_current_user)
):
    """
    INVENTORY AI - Get inventory insights
    
    Returns:
    - dead_stock: Products with no movement
    - restock_recommendation: Products needing restock
    - demand_anomaly: Unusual demand patterns
    - branch_imbalance: Stock distribution issues
    """
    try:
        AIKillSwitch.check_or_raise()
        AIRBACGateway.check_access(user, "inventory")
        
        start_time = time.time()
        
        data_layer, insights, logger = get_ai_services()
        result = await insights.get_inventory_insights()
        
        execution_time = (time.time() - start_time) * 1000
        
        # Log decision
        await logger.log_decision(
            tenant_id=user.get("tenant_id", ""),
            user_id=user.get("user_id") or user.get("id", ""),
            endpoint="/api/ai/inventory/insights",
            model_version=result["model_version"],
            data_window="current",
            features_used=["stock_movements", "stock", "products"],
            output=result,
            execution_time_ms=execution_time
        )
        
        return result
        
    except AIEngineDisabledException:
        raise HTTPException(status_code=503, detail="AI Engine is disabled")


# ==================== FINANCE AI ====================

@router.get("/finance/insights")
async def get_finance_insights(
    days: int = Query(30, ge=1, le=365, description="Analysis period in days"),
    user: dict = Depends(get_current_user)
):
    """
    FINANCE AI - Get finance insights
    
    Returns:
    - expense_anomaly: Unusual expense patterns
    - margin_analysis: Profit margin trends
    - cash_variance: Cash flow analysis
    - profit_trend: Profitability over time
    """
    try:
        AIKillSwitch.check_or_raise()
        AIRBACGateway.check_access(user, "finance")
        
        start_time = time.time()
        
        data_layer, insights, logger = get_ai_services()
        result = await insights.get_finance_insights(days)
        
        execution_time = (time.time() - start_time) * 1000
        
        # Log decision
        await logger.log_decision(
            tenant_id=user.get("tenant_id", ""),
            user_id=user.get("user_id") or user.get("id", ""),
            endpoint="/api/ai/finance/insights",
            model_version=result["model_version"],
            data_window=f"{days} days",
            features_used=["journal_entries", "chart_of_accounts", "cash_transactions"],
            output=result,
            execution_time_ms=execution_time
        )
        
        return result
        
    except AIEngineDisabledException:
        raise HTTPException(status_code=503, detail="AI Engine is disabled")


# ==================== CEO DASHBOARD ====================

@router.get("/ceo/dashboard")
async def get_ceo_dashboard(
    user: dict = Depends(get_current_user)
):
    """
    CEO AI DASHBOARD - Executive summary
    
    Returns:
    - omzet_hari_ini: Today's revenue
    - cabang_terbaik: Best performing branch
    - produk_terbaik: Top selling product
    - cabang_minus: Underperforming branches
    - cash_variance: Cash anomalies
    """
    try:
        AIKillSwitch.check_or_raise()
        AIRBACGateway.check_access(user, "ceo")
        
        start_time = time.time()
        
        data_layer, insights, logger = get_ai_services()
        result = await insights.get_ceo_dashboard()
        
        execution_time = (time.time() - start_time) * 1000
        
        # Log decision
        await logger.log_decision(
            tenant_id=user.get("tenant_id", ""),
            user_id=user.get("user_id") or user.get("id", ""),
            endpoint="/api/ai/ceo/dashboard",
            model_version=result["model_version"],
            data_window="today + historical",
            features_used=["sales_invoices", "branches", "products"],
            output=result,
            execution_time_ms=execution_time
        )
        
        return result
        
    except AIEngineDisabledException:
        raise HTTPException(status_code=503, detail="AI Engine is disabled")


# ==================== AI LOGS ====================

@router.get("/logs")
async def get_ai_decision_logs(
    limit: int = Query(50, ge=1, le=500),
    user: dict = Depends(get_current_user)
):
    """
    Get AI decision logs for audit
    """
    AIRBACGateway.check_access(user, "logs")
    
    data_layer, insights, logger = get_ai_services()
    
    logs = await logger.get_recent_decisions(
        tenant_id=user.get("tenant_id"),
        limit=limit
    )
    
    stats = await logger.get_decision_stats(
        tenant_id=user.get("tenant_id")
    )
    
    return {
        "logs": logs,
        "statistics": stats
    }


# ==================== KILL SWITCH ====================

@router.post("/kill-switch")
async def toggle_kill_switch(
    enabled: bool = Query(..., description="Enable or disable AI Engine"),
    user: dict = Depends(get_current_user)
):
    """
    Toggle AI Engine kill switch (admin only)
    """
    if not AIRBACGateway.is_admin(user):
        raise HTTPException(status_code=403, detail="Only admin can toggle kill switch")
    
    # Note: In production, this would update env or config file
    # For now, we just return the intended state
    return {
        "status": "acknowledged",
        "ai_enabled": enabled,
        "message": f"AI Engine {'enabled' if enabled else 'disabled'}. "
                   f"Set AI_ENGINE_ENABLED={str(enabled).lower()} in environment to persist.",
        "changed_by": user.get("email"),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
