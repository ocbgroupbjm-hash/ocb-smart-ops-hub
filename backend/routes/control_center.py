# OCB TITAN ERP - System Control Center
# ======================================
# SUPER ADMIN ONLY - Complete system monitoring and control
#
# Features:
# - Tenant Overview
# - System Health
# - Backup Monitor
# - Error Tracking
# - Sales Monitoring
# - Inventory Monitoring
# - Accounting Monitoring
# - AI Monitoring

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
import os
import psutil

router = APIRouter(prefix="/api/control-center", tags=["Control Center"])

# Import dependencies
from utils.auth import get_current_user
from database import get_db
from routes.tenant_registry import get_all_tenants_from_registry


def require_super_admin(user: dict = Depends(get_current_user)):
    """Only super_admin can access control center"""
    role = user.get("role_code") or user.get("role") or ""
    if role.lower() not in ["super_admin", "owner"]:
        raise HTTPException(
            status_code=403,
            detail="Control Center hanya dapat diakses oleh Super Admin atau Owner"
        )
    return user


# ==================== SYSTEM HEALTH ====================

@router.get("/health")
async def get_system_health(user: dict = Depends(require_super_admin)):
    """Get overall system health metrics"""
    
    # System metrics
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return {
        "status": "healthy" if cpu_percent < 80 and memory.percent < 80 else "degraded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metrics": {
            "cpu": {
                "percent": cpu_percent,
                "status": "healthy" if cpu_percent < 70 else "warning" if cpu_percent < 90 else "critical"
            },
            "memory": {
                "total_gb": round(memory.total / (1024**3), 2),
                "used_gb": round(memory.used / (1024**3), 2),
                "percent": memory.percent,
                "status": "healthy" if memory.percent < 70 else "warning" if memory.percent < 90 else "critical"
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "used_gb": round(disk.used / (1024**3), 2),
                "percent": disk.percent,
                "status": "healthy" if disk.percent < 80 else "warning" if disk.percent < 95 else "critical"
            }
        }
    }


# ==================== TENANT OVERVIEW ====================

@router.get("/tenants")
async def get_tenant_overview(user: dict = Depends(require_super_admin)):
    """Get overview of all tenants"""
    
    tenants = await get_all_tenants_from_registry()
    
    # Group by status
    by_status = {
        "active": [t for t in tenants if t.get("status") == "active"],
        "inactive": [t for t in tenants if t.get("status") == "inactive"],
        "other": [t for t in tenants if t.get("status") not in ["active", "inactive"]]
    }
    
    # Check AI enabled
    ai_enabled_count = sum(1 for t in tenants if t.get("ai_enabled"))
    
    return {
        "total": len(tenants),
        "active": len(by_status["active"]),
        "inactive": len(by_status["inactive"]),
        "ai_enabled": ai_enabled_count,
        "tenants": tenants,
        "by_status": by_status
    }


# ==================== BACKUP MONITOR ====================

@router.get("/backups")
async def get_backup_status(user: dict = Depends(require_super_admin)):
    """Get backup status and history"""
    
    from motor.motor_asyncio import AsyncIOMotorClient
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    client = AsyncIOMotorClient(mongo_url)
    
    try:
        main_db = client["erp_db"]
        
        # Get recent backups
        backups = await main_db["backup_logs"].find(
            {}, {"_id": 0}
        ).sort("timestamp", -1).to_list(20)
        
        # Calculate stats
        successful = sum(1 for b in backups if b.get("status") == "success")
        failed = sum(1 for b in backups if b.get("status") == "failed")
        
        last_backup = backups[0] if backups else None
        
        return {
            "last_backup": last_backup,
            "total_backups": len(backups),
            "successful": successful,
            "failed": failed,
            "recent_backups": backups[:10]
        }
    finally:
        client.close()


# ==================== ERROR TRACKING ====================

@router.get("/errors")
async def get_error_tracking(
    days: int = 7,
    user: dict = Depends(require_super_admin)
):
    """Get recent errors from audit logs"""
    
    db = get_db()
    since = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Find error logs
    errors = await db["audit_logs"].find(
        {
            "$or": [
                {"action": "error"},
                {"action": {"$regex": "fail", "$options": "i"}},
                {"module": "error"}
            ],
            "timestamp": {"$gte": since.isoformat()}
        },
        {"_id": 0}
    ).sort("timestamp", -1).to_list(100)
    
    # Group by module
    by_module = {}
    for e in errors:
        module = e.get("module", "unknown")
        if module not in by_module:
            by_module[module] = []
        by_module[module].append(e)
    
    return {
        "period_days": days,
        "total_errors": len(errors),
        "by_module": {k: len(v) for k, v in by_module.items()},
        "recent_errors": errors[:20]
    }


# ==================== SALES MONITORING ====================

@router.get("/sales")
async def get_sales_monitoring(
    days: int = 30,
    user: dict = Depends(require_super_admin)
):
    """Get sales monitoring data"""
    
    db = get_db()
    since = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Get sales statistics
    pipeline = [
        {"$match": {"created_at": {"$gte": since.isoformat()}}},
        {"$group": {
            "_id": None,
            "total_invoices": {"$sum": 1},
            "total_revenue": {"$sum": "$grand_total"},
            "avg_invoice": {"$avg": "$grand_total"}
        }}
    ]
    
    result = await db["sales_invoices"].aggregate(pipeline).to_list(1)
    stats = result[0] if result else {"total_invoices": 0, "total_revenue": 0, "avg_invoice": 0}
    
    # Get daily breakdown
    daily_pipeline = [
        {"$match": {"created_at": {"$gte": since.isoformat()}}},
        {"$project": {
            "date": {"$substr": ["$created_at", 0, 10]},
            "grand_total": 1
        }},
        {"$group": {
            "_id": "$date",
            "count": {"$sum": 1},
            "total": {"$sum": "$grand_total"}
        }},
        {"$sort": {"_id": -1}},
        {"$limit": 30}
    ]
    
    daily = await db["sales_invoices"].aggregate(daily_pipeline).to_list(30)
    
    return {
        "period_days": days,
        "total_invoices": stats.get("total_invoices", 0),
        "total_revenue": stats.get("total_revenue", 0),
        "avg_invoice": stats.get("avg_invoice", 0),
        "daily_breakdown": daily
    }


# ==================== INVENTORY MONITORING ====================

@router.get("/inventory")
async def get_inventory_monitoring(user: dict = Depends(require_super_admin)):
    """Get inventory monitoring data"""
    
    db = get_db()
    
    # Get stock statistics from stock collection (calculated from movements)
    total_products = await db["products"].count_documents({})
    
    # Low stock products
    low_stock = await db["stock"].find(
        {"quantity": {"$lt": 10, "$gt": 0}},
        {"_id": 0, "product_id": 1, "quantity": 1}
    ).to_list(20)
    
    # Out of stock
    out_of_stock = await db["stock"].count_documents({"quantity": {"$lte": 0}})
    
    # Recent movements
    movements = await db["stock_movements"].find(
        {}, {"_id": 0}
    ).sort("timestamp", -1).to_list(10)
    
    return {
        "total_products": total_products,
        "low_stock_count": len(low_stock),
        "out_of_stock_count": out_of_stock,
        "low_stock_items": low_stock,
        "recent_movements": movements
    }


# ==================== ACCOUNTING MONITORING ====================

@router.get("/accounting")
async def get_accounting_monitoring(user: dict = Depends(require_super_admin)):
    """Get accounting monitoring data"""
    
    db = get_db()
    
    # Trial balance
    pipeline = [
        {"$match": {"status": "posted"}},
        {"$unwind": "$lines"},
        {"$group": {
            "_id": None,
            "total_debit": {"$sum": "$lines.debit"},
            "total_credit": {"$sum": "$lines.credit"}
        }}
    ]
    
    tb_result = await db["journal_entries"].aggregate(pipeline).to_list(1)
    tb = tb_result[0] if tb_result else {"total_debit": 0, "total_credit": 0}
    
    is_balanced = abs(tb.get("total_debit", 0) - tb.get("total_credit", 0)) < 1
    
    # Journal counts
    total_journals = await db["journal_entries"].count_documents({})
    posted_journals = await db["journal_entries"].count_documents({"status": "posted"})
    draft_journals = await db["journal_entries"].count_documents({"status": "draft"})
    
    return {
        "trial_balance": {
            "total_debit": tb.get("total_debit", 0),
            "total_credit": tb.get("total_credit", 0),
            "is_balanced": is_balanced
        },
        "journal_counts": {
            "total": total_journals,
            "posted": posted_journals,
            "draft": draft_journals
        },
        "status": "healthy" if is_balanced else "warning"
    }


# ==================== AI MONITORING ====================

@router.get("/ai")
async def get_ai_monitoring(
    days: int = 7,
    user: dict = Depends(require_super_admin)
):
    """Get AI engine monitoring data"""
    
    db = get_db()
    since = datetime.now(timezone.utc) - timedelta(days=days)
    
    # AI decision logs
    ai_logs = await db["ai_decision_log"].find(
        {"timestamp": {"$gte": since.isoformat()}},
        {"_id": 0}
    ).sort("timestamp", -1).to_list(100)
    
    # Calculate stats
    total_requests = len(ai_logs)
    avg_execution_time = sum(log.get("execution_time_ms", 0) for log in ai_logs) / max(total_requests, 1)
    
    # Group by endpoint
    by_endpoint = {}
    for log in ai_logs:
        endpoint = log.get("endpoint", "unknown")
        if endpoint not in by_endpoint:
            by_endpoint[endpoint] = 0
        by_endpoint[endpoint] += 1
    
    # Check AI config
    from routes.ai_engine import AI_ENGINE_CONFIG
    
    return {
        "period_days": days,
        "total_requests": total_requests,
        "avg_execution_time_ms": round(avg_execution_time, 2),
        "by_endpoint": by_endpoint,
        "recent_logs": ai_logs[:10],
        "config": AI_ENGINE_CONFIG,
        "status": "enabled" if AI_ENGINE_CONFIG.get("enabled") else "disabled"
    }


# ==================== SECURITY CENTER ====================

@router.get("/security")
async def get_security_overview(
    days: int = 7,
    user: dict = Depends(require_super_admin)
):
    """Get security overview"""
    
    db = get_db()
    since = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Login attempts
    login_logs = await db["audit_logs"].find(
        {
            "action": {"$in": ["login", "login_failed", "logout"]},
            "timestamp": {"$gte": since.isoformat()}
        },
        {"_id": 0}
    ).sort("timestamp", -1).to_list(100)
    
    successful_logins = sum(1 for log in login_logs if log.get("action") == "login")
    failed_logins = sum(1 for log in login_logs if log.get("action") == "login_failed")
    
    # Security events
    security_events = await db["audit_logs"].find(
        {
            "action": {"$in": ["permission_denied", "unauthorized", "rbac_violation"]},
            "timestamp": {"$gte": since.isoformat()}
        },
        {"_id": 0}
    ).to_list(50)
    
    return {
        "period_days": days,
        "login_stats": {
            "successful": successful_logins,
            "failed": failed_logins,
            "total": len(login_logs)
        },
        "security_events": len(security_events),
        "recent_logins": login_logs[:20],
        "recent_security_events": security_events[:10]
    }


# ==================== DASHBOARD SUMMARY ====================

@router.get("/dashboard")
async def get_dashboard_summary(user: dict = Depends(require_super_admin)):
    """Get complete dashboard summary for Control Center"""
    
    # Get all monitoring data
    health = await get_system_health(user)
    tenants = await get_tenant_overview(user)
    sales = await get_sales_monitoring(7, user)
    inventory = await get_inventory_monitoring(user)
    accounting = await get_accounting_monitoring(user)
    
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "system_health": health,
        "tenant_overview": {
            "total": tenants["total"],
            "active": tenants["active"],
            "ai_enabled": tenants["ai_enabled"]
        },
        "sales_summary": {
            "total_invoices": sales["total_invoices"],
            "total_revenue": sales["total_revenue"]
        },
        "inventory_summary": {
            "total_products": inventory["total_products"],
            "low_stock": inventory["low_stock_count"],
            "out_of_stock": inventory["out_of_stock_count"]
        },
        "accounting_status": {
            "is_balanced": accounting["trial_balance"]["is_balanced"],
            "total_journals": accounting["journal_counts"]["total"]
        }
    }



# ==================== PRIORITAS 6: BLUEPRINT SYNC ====================

CURRENT_BLUEPRINT_VERSION = "2.2.0"  # Updated after PRIORITAS 7 (AP/AR Payment Allocation)

class BlueprintSyncRequest:
    pass

@router.post("/blueprint/lock")
async def lock_blueprint_version(
    version: str = CURRENT_BLUEPRINT_VERSION,
    user: dict = Depends(require_super_admin)
):
    """
    PRIORITAS 6: Lock blueprint version before sync
    This marks the current version as production-ready
    """
    from motor.motor_asyncio import AsyncIOMotorClient
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    client = AsyncIOMotorClient(mongo_url)
    
    try:
        main_db = client["erp_db"]
        
        # Create blueprint lock record
        lock_record = {
            "version": version,
            "locked_at": datetime.now(timezone.utc).isoformat(),
            "locked_by": user.get("user_id", user.get("id", "")),
            "locked_by_name": user.get("name", ""),
            "status": "locked",
            "features": [
                "PRIORITAS 1: Journal Security - System journals protected",
                "PRIORITAS 2: GL Search Improvement - Single letter search",
                "PRIORITAS 3: Date Format DD/MM/YYYY",
                "PRIORITAS 4: Purchase Export to Excel",
                "PRIORITAS 5: Serial Number Range",
                "PRIORITAS 6: Blueprint Sync v2.1.0",
                "PRIORITAS 7: AP/AR Payment Allocation Engine (Enterprise)",
                "HR KPI Engine UI",
                "HR Analytics Dashboard"
            ]
        }
        
        await main_db["blueprint_versions"].insert_one(lock_record)
        
        return {
            "success": True,
            "message": f"Blueprint version {version} locked successfully",
            "version": version,
            "locked_at": lock_record["locked_at"]
        }
    finally:
        client.close()


@router.post("/blueprint/sync")
async def sync_blueprint_to_tenants(
    user: dict = Depends(require_super_admin)
):
    """
    PRIORITAS 6: Sync blueprint to all tenants
    Updates all tenant databases to current blueprint version
    """
    from motor.motor_asyncio import AsyncIOMotorClient
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    client = AsyncIOMotorClient(mongo_url)
    
    sync_results = []
    
    try:
        # Get all tenants
        tenants = await get_all_tenants_from_registry()
        
        for tenant in tenants:
            tenant_id = tenant.get("id")
            tenant_name = tenant.get("name")
            db_name = tenant.get("db_name")  # Fixed: use db_name not database_name
            
            if not db_name:
                sync_results.append({
                    "tenant_id": tenant_id,
                    "tenant_name": tenant_name,
                    "status": "skipped",
                    "reason": "No db_name configured"
                })
                continue
            
            try:
                tenant_db = client[db_name]
                
                # Update tenant's blueprint_version in _tenant_metadata
                await tenant_db["_tenant_metadata"].update_one(
                    {},  # Update the single metadata document
                    {"$set": {
                        "blueprint_version": CURRENT_BLUEPRINT_VERSION,
                        "last_sync": datetime.now(timezone.utc).isoformat(),
                        "synced_by": user.get("name", "")
                    }},
                    upsert=True
                )
                
                # Ensure required collections exist
                required_collections = [
                    "journal_entries", "journal_lines", "accounts", "journals",
                    "ap_invoices", "ap_payments", "ap_payment_allocations",
                    "ar_invoices", "ar_payments", "ar_payment_allocations",
                    "employees", "attendance_logs", "payroll", "leave_requests",
                    "kpi_targets", "kpi_results",
                    "inventory_serial_numbers", "stock_movements", "products"
                ]
                
                existing_collections = await tenant_db.list_collection_names()
                
                for coll in required_collections:
                    if coll not in existing_collections:
                        await tenant_db.create_collection(coll)
                
                sync_results.append({
                    "tenant_id": tenant_id,
                    "tenant_name": tenant_name,
                    "database_name": db_name,
                    "status": "success",
                    "new_version": CURRENT_BLUEPRINT_VERSION,
                    "collections_verified": len(required_collections)
                })
                
            except Exception as e:
                sync_results.append({
                    "tenant_id": tenant_id,
                    "tenant_name": tenant_name,
                    "status": "failed",
                    "error": str(e)
                })
        
        # Summary
        success_count = sum(1 for r in sync_results if r["status"] == "success")
        failed_count = sum(1 for r in sync_results if r["status"] == "failed")
        
        return {
            "success": True,
            "blueprint_version": CURRENT_BLUEPRINT_VERSION,
            "total_tenants": len(tenants),
            "synced": success_count,
            "failed": failed_count,
            "results": sync_results,
            "synced_at": datetime.now(timezone.utc).isoformat()
        }
        
    finally:
        client.close()


@router.get("/blueprint/status")
async def get_blueprint_status(user: dict = Depends(require_super_admin)):
    """Get current blueprint sync status across all tenants"""
    
    tenants = await get_all_tenants_from_registry()
    
    tenant_versions = []
    for tenant in tenants:
        tenant_versions.append({
            "tenant_id": tenant.get("id"),
            "tenant_name": tenant.get("name"),
            "blueprint_version": tenant.get("blueprint_version", "unknown"),
            "last_sync": tenant.get("last_sync"),
            "is_current": tenant.get("blueprint_version") == CURRENT_BLUEPRINT_VERSION
        })
    
    all_synced = all(t["is_current"] for t in tenant_versions)
    
    return {
        "current_version": CURRENT_BLUEPRINT_VERSION,
        "all_synced": all_synced,
        "total_tenants": len(tenants),
        "synced_count": sum(1 for t in tenant_versions if t["is_current"]),
        "tenants": tenant_versions
    }


@router.post("/blueprint/smoke-test")
async def run_smoke_test_all_tenants(user: dict = Depends(require_super_admin)):
    """
    PRIORITAS 6: Run smoke test on all tenants
    Validates basic functionality after sync
    """
    from motor.motor_asyncio import AsyncIOMotorClient
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    client = AsyncIOMotorClient(mongo_url)
    
    test_results = []
    
    try:
        tenants = await get_all_tenants_from_registry()
        
        for tenant in tenants:
            tenant_id = tenant.get("id")
            tenant_name = tenant.get("name")
            db_name = tenant.get("db_name")  # Fixed: use db_name
            
            if not db_name:
                test_results.append({
                    "tenant_id": tenant_id,
                    "tenant_name": tenant_name,
                    "status": "skipped",
                    "reason": "No database"
                })
                continue
            
            try:
                tenant_db = client[db_name]
                
                # Test 1: Collection count
                collections = await tenant_db.list_collection_names()
                
                # Test 2: Journal entries count
                je_count = await tenant_db["journal_entries"].count_documents({})
                
                # Test 3: Accounts count
                acc_count = await tenant_db["accounts"].count_documents({})
                
                # Test 4: Products count
                prod_count = await tenant_db["products"].count_documents({})
                
                # Test 5: Check journal_source field exists (PRIORITAS 1)
                sample_journal = await tenant_db["journal_entries"].find_one({})
                has_journal_source = "journal_source" in sample_journal if sample_journal else True
                
                test_results.append({
                    "tenant_id": tenant_id,
                    "tenant_name": tenant_name,
                    "database_name": db_name,
                    "status": "pass",
                    "tests": {
                        "collections_exist": len(collections) > 0,
                        "collection_count": len(collections),
                        "journal_entries": je_count,
                        "accounts": acc_count,
                        "products": prod_count,
                        "journal_source_field": has_journal_source
                    }
                })
                
            except Exception as e:
                test_results.append({
                    "tenant_id": tenant_id,
                    "tenant_name": tenant_name,
                    "status": "fail",
                    "error": str(e)
                })
        
        pass_count = sum(1 for r in test_results if r.get("status") == "pass")
        
        return {
            "success": True,
            "total_tenants": len(tenants),
            "passed": pass_count,
            "failed": len(tenants) - pass_count,
            "results": test_results,
            "tested_at": datetime.now(timezone.utc).isoformat()
        }
        
    finally:
        client.close()
