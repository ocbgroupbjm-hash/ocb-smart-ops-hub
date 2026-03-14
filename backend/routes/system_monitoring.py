# OCB TITAN ERP - System Monitoring Endpoints
# Provides health check, metrics, and observability APIs

from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone
from database import get_db, get_active_db_name, client as mongo_client
from utils.auth import get_current_user
from routes.request_trace_middleware import get_metrics, reset_metrics
import psutil
import os

router = APIRouter(prefix="/api/system", tags=["System"])

def get_mongo_client():
    """Get the MongoDB client"""
    return mongo_client


@router.get("/health")
async def health_check():
    """
    System health check endpoint.
    Returns status of all critical components.
    """
    health = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "components": {}
    }
    
    # Check MongoDB
    try:
        client = get_mongo_client()
        await client.admin.command('ping')
        health["components"]["mongodb"] = {"status": "up"}
    except Exception as e:
        health["components"]["mongodb"] = {"status": "down", "error": str(e)}
        health["status"] = "degraded"
    
    # Check database connection
    try:
        db = get_db()
        await db.command('ping')
        health["components"]["database"] = {
            "status": "up",
            "active_db": get_active_db_name()
        }
    except Exception as e:
        health["components"]["database"] = {"status": "down", "error": str(e)}
        health["status"] = "degraded"
    
    # System resources
    try:
        health["components"]["system"] = {
            "status": "up",
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent
        }
    except Exception:
        health["components"]["system"] = {"status": "unknown"}
    
    return health


@router.get("/metrics")
async def get_system_metrics(
    user: dict = Depends(get_current_user)
):
    """
    Get system metrics including:
    - API latency
    - Error rate
    - Request count
    - Slow query detection
    """
    metrics = get_metrics()
    
    # Add database stats
    try:
        db = get_db()
        db_stats = await db.command('dbStats')
        metrics["database"] = {
            "collections": db_stats.get("collections", 0),
            "objects": db_stats.get("objects", 0),
            "dataSize": db_stats.get("dataSize", 0),
            "indexSize": db_stats.get("indexSize", 0)
        }
    except Exception:
        metrics["database"] = {"error": "Unable to fetch stats"}
    
    return metrics


@router.post("/metrics/reset")
async def reset_system_metrics(
    user: dict = Depends(get_current_user)
):
    """Reset system metrics (admin only)"""
    role = user.get("role_code") or user.get("role") or ""
    if role not in ["owner", "super_admin", "admin"]:
        raise HTTPException(status_code=403, detail="Admin only")
    
    reset_metrics()
    return {"message": "Metrics reset successfully"}


@router.get("/logs")
async def get_recent_logs(
    limit: int = 100,
    level: str = "",
    user: dict = Depends(get_current_user)
):
    """
    Get recent application logs.
    Requires admin permission.
    """
    role = user.get("role_code") or user.get("role") or ""
    if role not in ["owner", "super_admin", "admin"]:
        raise HTTPException(status_code=403, detail="Admin only")
    
    logs = []
    
    # Read from log file if exists
    log_paths = [
        "/var/log/supervisor/backend.out.log",
        "/var/log/supervisor/backend.err.log"
    ]
    
    for log_path in log_paths:
        if os.path.exists(log_path):
            try:
                with open(log_path, 'r') as f:
                    lines = f.readlines()[-limit:]
                    for line in lines:
                        line = line.strip()
                        if line:
                            # Try to parse as JSON
                            try:
                                import json
                                entry = json.loads(line)
                                if level and entry.get("level", "").lower() != level.lower():
                                    continue
                                logs.append(entry)
                            except Exception:
                                logs.append({"raw": line})
            except Exception:
                pass
    
    return {
        "logs": logs[-limit:],
        "total": len(logs),
        "log_files": log_paths
    }


@router.get("/info")
async def get_system_info():
    """Get system information (public)"""
    return {
        "app": "OCB TITAN ERP",
        "version": "3.7.0",
        "status": "PRODUCTION READY",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": os.environ.get("ENV", "production")
    }


@router.get("/database/stats")
async def get_database_stats(
    user: dict = Depends(get_current_user)
):
    """Get detailed database statistics"""
    db = get_db()
    
    stats = {
        "active_database": get_active_db_name(),
        "collections": []
    }
    
    try:
        db_stats = await db.command('dbStats')
        stats["database_stats"] = {
            "collections": db_stats.get("collections", 0),
            "objects": db_stats.get("objects", 0),
            "avgObjSize": db_stats.get("avgObjSize", 0),
            "dataSize": db_stats.get("dataSize", 0),
            "storageSize": db_stats.get("storageSize", 0),
            "indexes": db_stats.get("indexes", 0),
            "indexSize": db_stats.get("indexSize", 0)
        }
    except Exception as e:
        stats["error"] = str(e)
    
    # Get collection stats
    try:
        collections = await db.list_collection_names()
        for coll_name in collections[:20]:  # Limit to 20
            try:
                count = await db[coll_name].count_documents({})
                stats["collections"].append({
                    "name": coll_name,
                    "count": count
                })
            except Exception:
                pass
    except Exception:
        pass
    
    return stats


@router.get("/tenants")
async def get_tenant_list(
    user: dict = Depends(get_current_user)
):
    """Get list of all tenants (admin only)"""
    role = user.get("role_code") or user.get("role") or ""
    if role not in ["owner", "super_admin"]:
        raise HTTPException(status_code=403, detail="Owner/Super Admin only")
    
    client = get_mongo_client()
    
    # Get all ocb_ databases
    all_dbs = await client.list_database_names()
    tenants = []
    
    for db_name in all_dbs:
        if db_name.startswith("ocb_"):
            db = client[db_name]
            
            # Get tenant metadata
            metadata = await db["_tenant_metadata"].find_one({}, {"_id": 0})
            
            # Get basic stats
            try:
                collections = await db.list_collection_names()
                users_count = await db["users"].count_documents({})
            except Exception:
                collections = []
                users_count = 0
            
            tenants.append({
                "database": db_name,
                "tenant_id": metadata.get("tenant_id") if metadata else db_name,
                "business_name": metadata.get("business_name") if metadata else db_name,
                "status": metadata.get("status", "active") if metadata else "active",
                "collections": len(collections),
                "users": users_count
            })
    
    return {
        "tenants": tenants,
        "total": len(tenants)
    }
