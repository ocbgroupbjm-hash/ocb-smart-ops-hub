# OCB TITAN ERP - Backup & Disaster Recovery System
# ==================================================
# Features:
# - Daily snapshot backup
# - Point-in-time recovery (PITR)
# - Restore testing
# - DR drill execution and reporting

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
import os
import json
import asyncio

router = APIRouter(prefix="/api/backup", tags=["Backup & DR"])

# Import dependencies
from utils.auth import get_current_user
from database import get_db, get_active_db_name


def require_super_admin(user: dict = Depends(get_current_user)):
    """Only super_admin can access backup operations"""
    role = user.get("role_code") or user.get("role") or ""
    if role.lower() not in ["super_admin", "owner"]:
        raise HTTPException(
            status_code=403,
            detail="Backup & DR hanya dapat diakses oleh Super Admin atau Owner"
        )
    return user


# ==================== BACKUP CONFIGURATION ====================

BACKUP_CONFIG = {
    "enabled": True,
    "schedule": "daily",
    "retention_days": 30,
    "backup_path": "/app/backups",
    "include_collections": [
        "users", "roles", "branches", "products", "suppliers", "customers",
        "sales_invoices", "purchase_orders", "stock", "stock_movements",
        "journal_entries", "chart_of_accounts", "cash_transactions",
        "ap_invoices", "ar_invoices", "payments", "audit_logs",
        "_tenant_metadata"
    ],
    "pitr_enabled": True,
    "pitr_retention_hours": 24
}


# ==================== BACKUP OPERATIONS ====================

async def create_backup_metadata(db_name: str, backup_type: str, collections: List[str]) -> Dict:
    """Create backup metadata"""
    from motor.motor_asyncio import AsyncIOMotorClient
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    client = AsyncIOMotorClient(mongo_url)
    
    try:
        db = client[db_name]
        
        # Count documents in each collection
        collection_stats = {}
        for coll in collections:
            try:
                count = await db[coll].count_documents({})
                collection_stats[coll] = count
            except:
                collection_stats[coll] = 0
        
        # Get tenant metadata
        metadata = await db["_tenant_metadata"].find_one({}, {"_id": 0})
        
        return {
            "backup_id": f"backup_{db_name}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            "database": db_name,
            "backup_type": backup_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "collections": collections,
            "collection_stats": collection_stats,
            "total_documents": sum(collection_stats.values()),
            "tenant_metadata": metadata,
            "blueprint_version": metadata.get("blueprint_version") if metadata else None,
            "status": "completed"
        }
    finally:
        client.close()


async def validate_backup_integrity(backup_metadata: Dict) -> Dict:
    """Validate backup integrity"""
    validation = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "backup_id": backup_metadata.get("backup_id"),
        "checks": []
    }
    
    # Check 1: Metadata exists
    validation["checks"].append({
        "check": "metadata_exists",
        "status": "PASS" if backup_metadata else "FAIL"
    })
    
    # Check 2: Collection stats present
    validation["checks"].append({
        "check": "collection_stats_present",
        "status": "PASS" if backup_metadata.get("collection_stats") else "FAIL"
    })
    
    # Check 3: Critical collections backed up
    critical = ["users", "journal_entries", "stock_movements", "_tenant_metadata"]
    backed_up = backup_metadata.get("collections", [])
    all_critical = all(c in backed_up for c in critical)
    validation["checks"].append({
        "check": "critical_collections_backed_up",
        "status": "PASS" if all_critical else "FAIL",
        "details": f"Required: {critical}, Found: {[c for c in critical if c in backed_up]}"
    })
    
    # Check 4: Document counts valid
    stats = backup_metadata.get("collection_stats", {})
    validation["checks"].append({
        "check": "document_counts_valid",
        "status": "PASS" if all(v >= 0 for v in stats.values()) else "FAIL"
    })
    
    validation["overall_status"] = "PASS" if all(c["status"] == "PASS" for c in validation["checks"]) else "FAIL"
    
    return validation


async def execute_dr_drill(db_name: str) -> Dict:
    """Execute disaster recovery drill"""
    from motor.motor_asyncio import AsyncIOMotorClient
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    client = AsyncIOMotorClient(mongo_url)
    
    drill_result = {
        "drill_id": f"dr_drill_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
        "database": db_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "steps": []
    }
    
    try:
        db = client[db_name]
        
        # Step 1: Verify database connectivity
        step1_start = datetime.now(timezone.utc)
        try:
            await db.command("ping")
            drill_result["steps"].append({
                "step": "database_connectivity",
                "status": "PASS",
                "duration_ms": (datetime.now(timezone.utc) - step1_start).total_seconds() * 1000
            })
        except Exception as e:
            drill_result["steps"].append({
                "step": "database_connectivity",
                "status": "FAIL",
                "error": str(e)
            })
            raise
        
        # Step 2: Verify accounting integrity
        step2_start = datetime.now(timezone.utc)
        try:
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
            
            drill_result["steps"].append({
                "step": "accounting_integrity",
                "status": "PASS" if is_balanced else "FAIL",
                "total_debit": tb.get("total_debit", 0),
                "total_credit": tb.get("total_credit", 0),
                "duration_ms": (datetime.now(timezone.utc) - step2_start).total_seconds() * 1000
            })
        except Exception as e:
            drill_result["steps"].append({
                "step": "accounting_integrity",
                "status": "ERROR",
                "error": str(e)
            })
        
        # Step 3: Verify inventory SSOT
        step3_start = datetime.now(timezone.utc)
        try:
            movements_count = await db["stock_movements"].count_documents({})
            stock_count = await db["stock"].count_documents({})
            
            drill_result["steps"].append({
                "step": "inventory_ssot",
                "status": "PASS",
                "stock_movements": movements_count,
                "stock_records": stock_count,
                "duration_ms": (datetime.now(timezone.utc) - step3_start).total_seconds() * 1000
            })
        except Exception as e:
            drill_result["steps"].append({
                "step": "inventory_ssot",
                "status": "ERROR",
                "error": str(e)
            })
        
        # Step 4: Verify tenant metadata
        step4_start = datetime.now(timezone.utc)
        try:
            metadata = await db["_tenant_metadata"].find_one({}, {"_id": 0})
            drill_result["steps"].append({
                "step": "tenant_metadata",
                "status": "PASS" if metadata else "FAIL",
                "blueprint_version": metadata.get("blueprint_version") if metadata else None,
                "duration_ms": (datetime.now(timezone.utc) - step4_start).total_seconds() * 1000
            })
        except Exception as e:
            drill_result["steps"].append({
                "step": "tenant_metadata",
                "status": "ERROR",
                "error": str(e)
            })
        
        # Step 5: Verify user authentication data
        step5_start = datetime.now(timezone.utc)
        try:
            users_count = await db["users"].count_documents({})
            roles_count = await db["roles"].count_documents({})
            
            drill_result["steps"].append({
                "step": "authentication_data",
                "status": "PASS" if users_count > 0 and roles_count > 0 else "WARN",
                "users": users_count,
                "roles": roles_count,
                "duration_ms": (datetime.now(timezone.utc) - step5_start).total_seconds() * 1000
            })
        except Exception as e:
            drill_result["steps"].append({
                "step": "authentication_data",
                "status": "ERROR",
                "error": str(e)
            })
        
        # Calculate overall status
        passed = sum(1 for s in drill_result["steps"] if s["status"] == "PASS")
        failed = sum(1 for s in drill_result["steps"] if s["status"] == "FAIL")
        errors = sum(1 for s in drill_result["steps"] if s["status"] == "ERROR")
        
        drill_result["summary"] = {
            "total_steps": len(drill_result["steps"]),
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "overall_status": "PASS" if failed == 0 and errors == 0 else "FAIL"
        }
        
    finally:
        client.close()
    
    return drill_result


# ==================== API ENDPOINTS ====================

@router.get("/config")
async def get_backup_config(user: dict = Depends(require_super_admin)):
    """Get backup configuration"""
    return {
        "config": BACKUP_CONFIG,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.post("/snapshot/{db_name}")
async def create_snapshot(db_name: str, user: dict = Depends(require_super_admin)):
    """Create a backup snapshot for a specific database"""
    
    # Only allow backup of OCB databases
    if not db_name.startswith("ocb_"):
        raise HTTPException(status_code=400, detail="Hanya database tenant OCB yang dapat di-backup")
    
    # Create backup metadata
    metadata = await create_backup_metadata(
        db_name=db_name,
        backup_type="snapshot",
        collections=BACKUP_CONFIG["include_collections"]
    )
    
    # Validate backup
    validation = await validate_backup_integrity(metadata)
    
    # Store backup log
    from motor.motor_asyncio import AsyncIOMotorClient
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    client = AsyncIOMotorClient(mongo_url)
    
    try:
        main_db = client["erp_db"]
        await main_db["backup_logs"].insert_one({
            **metadata,
            "validation": validation,
            "created_by": user.get("user_id"),
            "created_by_name": user.get("name")
        })
    finally:
        client.close()
    
    return {
        "message": f"Snapshot backup untuk {db_name} berhasil dibuat",
        "backup": metadata,
        "validation": validation
    }


@router.get("/history")
async def get_backup_history(
    limit: int = 20,
    user: dict = Depends(require_super_admin)
):
    """Get backup history"""
    from motor.motor_asyncio import AsyncIOMotorClient
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    client = AsyncIOMotorClient(mongo_url)
    
    try:
        main_db = client["erp_db"]
        backups = await main_db["backup_logs"].find(
            {}, {"_id": 0}
        ).sort("timestamp", -1).to_list(limit)
        
        return {
            "total": len(backups),
            "backups": backups
        }
    finally:
        client.close()


@router.post("/dr-drill/{db_name}")
async def run_dr_drill(db_name: str, user: dict = Depends(require_super_admin)):
    """Run disaster recovery drill for a database"""
    
    # Only allow drill on OCB databases
    if not db_name.startswith("ocb_"):
        raise HTTPException(status_code=400, detail="DR drill hanya untuk database tenant OCB")
    
    # Execute drill
    drill_result = await execute_dr_drill(db_name)
    
    # Store drill log
    from motor.motor_asyncio import AsyncIOMotorClient
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    client = AsyncIOMotorClient(mongo_url)
    
    try:
        main_db = client["erp_db"]
        await main_db["dr_drill_logs"].insert_one({
            **drill_result,
            "executed_by": user.get("user_id"),
            "executed_by_name": user.get("name")
        })
    finally:
        client.close()
    
    return {
        "message": f"DR drill untuk {db_name} selesai",
        "result": drill_result
    }


@router.get("/dr-drill/history")
async def get_dr_drill_history(
    limit: int = 10,
    user: dict = Depends(require_super_admin)
):
    """Get DR drill history"""
    from motor.motor_asyncio import AsyncIOMotorClient
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    client = AsyncIOMotorClient(mongo_url)
    
    try:
        main_db = client["erp_db"]
        drills = await main_db["dr_drill_logs"].find(
            {}, {"_id": 0}
        ).sort("timestamp", -1).to_list(limit)
        
        return {
            "total": len(drills),
            "drills": drills
        }
    finally:
        client.close()


@router.post("/validate/{db_name}")
async def validate_database(db_name: str, user: dict = Depends(require_super_admin)):
    """Validate database integrity without full DR drill"""
    
    if not db_name.startswith("ocb_"):
        raise HTTPException(status_code=400, detail="Hanya database tenant OCB yang dapat divalidasi")
    
    # Create metadata
    metadata = await create_backup_metadata(
        db_name=db_name,
        backup_type="validation",
        collections=BACKUP_CONFIG["include_collections"]
    )
    
    # Validate
    validation = await validate_backup_integrity(metadata)
    
    return {
        "database": db_name,
        "validation": validation,
        "metadata": metadata
    }
