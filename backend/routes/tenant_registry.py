# OCB TITAN ERP - Tenant Registry
# =================================
# SINGLE SOURCE OF TRUTH for all tenant information
# Version: 1.0.0
#
# This module provides:
# - Centralized tenant registry reading from _tenant_metadata
# - Login page tenant list (only ACTIVE tenants)
# - Tenant sync status monitoring
# - Auto-sync on tenant operations

"""
TENANT REGISTRY ARCHITECTURE
============================

Source of Truth: _tenant_metadata collection in each tenant database

Flow:
1. Login page calls /api/tenant-registry/list
2. System scans all ocb_* databases
3. Reads _tenant_metadata from each database
4. Returns only tenants with status = 'active'
5. businesses.json is NO LONGER authoritative

Tenant Status Values:
- active: Visible in login, fully operational
- inactive: Hidden from login, data preserved
- archived: Hidden from login, read-only
- deleted: Hidden from login, marked for cleanup
"""

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
from typing import List, Dict, Optional
from pydantic import BaseModel
import os

router = APIRouter(prefix="/api/tenant-registry", tags=["Tenant Registry"])


def get_mongo_client():
    """Get MongoDB client"""
    from motor.motor_asyncio import AsyncIOMotorClient
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    return AsyncIOMotorClient(mongo_url)


class TenantInfo(BaseModel):
    """Tenant information structure for login page"""
    id: str
    tenant_id: str
    name: str
    db_name: str
    description: Optional[str] = ""
    tenant_type: Optional[str] = "retail"
    business_type: Optional[str] = "Retail"
    icon: Optional[str] = "building"
    color: Optional[str] = "#991B1B"
    status: str = "active"
    blueprint_version: Optional[str] = None
    timezone: Optional[str] = "Asia/Jakarta"
    currency: Optional[str] = "IDR"


# Default tenant display configuration
TENANT_DISPLAY_CONFIG = {
    "ocb_titan": {
        "name": "OCB GROUP",
        "description": "Database utama - Pusat operasional",
        "business_type": "Retail & Distribusi",
        "icon": "building",
        "color": "#991B1B"
    },
    "ocb_unit_4": {
        "name": "OCB UNIT 4 MPC & MP3",
        "description": "Distribusi Indosat",
        "business_type": "Distribusi",
        "icon": "truck",
        "color": "#7C2D12"
    },
    "ocb_unt_1": {
        "name": "OCB UNIT 1 RETAIL",
        "description": "Unit retail",
        "business_type": "Retail",
        "icon": "store",
        "color": "#065F46"
    },
    "ocb_baju": {
        "name": "OCB BAJU",
        "description": "Unit fashion/pakaian",
        "business_type": "Fashion",
        "icon": "shirt",
        "color": "#5B21B6"
    },
    "ocb_counter": {
        "name": "OCB COUNTER",
        "description": "Unit counter/service",
        "business_type": "Counter",
        "icon": "monitor",
        "color": "#1E40AF"
    }
}


async def auto_init_default_tenant(client):
    """
    Auto-initialize default tenant (ocb_titan) if no ocb_* databases exist.
    This ensures LIVE deployments have at least one functional tenant.
    """
    from datetime import datetime, timezone
    from utils.auth import hash_password
    
    db_name = "ocb_titan"
    db = client[db_name]
    
    # Create tenant metadata
    metadata = {
        "id": "ocb_titan",
        "database_key": "ocb_titan",
        "company_name": "OCB GROUP",
        "notes": "Database utama - Auto-initialized",
        "status": "active",
        "show_in_login_selector": True,
        "tenant_type": "retail",
        "timezone": "Asia/Jakarta",
        "currency": "IDR",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "auto_initialized": True
    }
    
    await db["_tenant_metadata"].delete_many({})
    await db["_tenant_metadata"].insert_one(metadata)
    
    # Create default admin user
    admin_user = {
        "id": "admin-default",
        "email": "ocbgroupbjm@gmail.com",
        "password": hash_password("admin123"),
        "full_name": "Administrator",
        "role": "admin",
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    existing = await db["users"].find_one({"email": admin_user["email"]})
    if not existing:
        await db["users"].insert_one(admin_user)
    
    print(f"[TENANT_REGISTRY] Auto-initialized {db_name} with admin user")
    return True


async def get_all_tenants_from_registry() -> List[Dict]:
    """
    Read tenant list from _tenant_metadata collection in all databases.
    This is the SINGLE SOURCE OF TRUTH for tenant information.
    
    AUTO-INIT: If no ocb_* databases found, creates default ocb_titan tenant.
    """
    client = get_mongo_client()
    tenants = []
    
    try:
        all_dbs = await client.list_database_names()
        ocb_dbs = sorted([d for d in all_dbs if d.startswith("ocb_")])
        
        # AUTO-INIT: If no ocb_* databases exist, create default tenant
        if not ocb_dbs:
            print("[TENANT_REGISTRY] No ocb_* databases found. Auto-initializing ocb_titan...")
            await auto_init_default_tenant(client)
            all_dbs = await client.list_database_names()
            ocb_dbs = sorted([d for d in all_dbs if d.startswith("ocb_")])
        
        for db_name in ocb_dbs:
            db = client[db_name]
            metadata = await db["_tenant_metadata"].find_one({}, {"_id": 0})
            
            if metadata:
                # Get display config for this tenant
                display = TENANT_DISPLAY_CONFIG.get(db_name, {})
                
                tenant = {
                    "id": metadata.get("id") or db_name,
                    "tenant_id": metadata.get("database_key") or db_name,
                    "name": display.get("name") or metadata.get("company_name") or db_name.replace("_", " ").title(),
                    "db_name": db_name,
                    "description": display.get("description") or metadata.get("notes") or "",
                    "tenant_type": metadata.get("tenant_type") or "retail",
                    "business_type": display.get("business_type") or metadata.get("tenant_type", "").title() or "Retail",
                    "icon": display.get("icon") or "building",
                    "color": display.get("color") or "#991B1B",
                    "status": metadata.get("status") or "active",
                    "blueprint_version": metadata.get("blueprint_version"),
                    "timezone": metadata.get("timezone") or "Asia/Jakarta",
                    "currency": metadata.get("currency") or "IDR",
                    "ai_enabled": metadata.get("ai_enabled", False),
                    "initialized_at": metadata.get("initialized_at"),
                    "last_migrated_at": metadata.get("last_migrated_at"),
                    "is_active": metadata.get("status") in ["active", "ready"],
                    "show_in_login_selector": metadata.get("status") in ["active", "ready"]
                }
                tenants.append(tenant)
            else:
                # Database exists but no metadata - mark as uninitialized
                display = TENANT_DISPLAY_CONFIG.get(db_name, {})
                tenant = {
                    "id": db_name,
                    "tenant_id": db_name,
                    "name": display.get("name") or db_name.replace("_", " ").title(),
                    "db_name": db_name,
                    "description": display.get("description") or "Uninitialized tenant",
                    "tenant_type": "unknown",
                    "business_type": display.get("business_type") or "Unknown",
                    "icon": display.get("icon") or "building",
                    "color": display.get("color") or "#6B7280",
                    "status": "uninitialized",
                    "blueprint_version": None,
                    "timezone": "Asia/Jakarta",
                    "currency": "IDR",
                    "ai_enabled": False,
                    "initialized_at": None,
                    "last_migrated_at": None,
                    "is_active": False,
                    "show_in_login_selector": False
                }
                tenants.append(tenant)
    finally:
        client.close()
    
    return tenants


@router.get("/list")
async def list_tenants_for_login():
    """
    List all ACTIVE/READY tenants for login page.
    
    This is the PRIMARY endpoint for login page tenant selection.
    Returns tenants with status = 'active' OR 'ready'.
    
    Source of Truth: _tenant_metadata collection in each database
    """
    all_tenants = await get_all_tenants_from_registry()
    
    # Filter only active/ready tenants for login page
    active_tenants = [
        t for t in all_tenants 
        if t.get("status") in ["active", "ready"] and t.get("show_in_login_selector", True)
    ]
    
    # Get current active database
    from database import get_active_db_name
    current_db = get_active_db_name()
    
    return {
        "tenants": active_tenants,
        "businesses": active_tenants,  # Alias for backward compatibility
        "current_db": current_db,
        "total": len(active_tenants),
        "source": "tenant_registry"  # Indicate source of truth
    }


@router.get("/all")
async def list_all_tenants():
    """
    List ALL tenants regardless of status.
    For admin/monitoring purposes only.
    """
    all_tenants = await get_all_tenants_from_registry()
    
    # Group by status
    by_status = {
        "active": [t for t in all_tenants if t.get("status") == "active"],
        "inactive": [t for t in all_tenants if t.get("status") == "inactive"],
        "archived": [t for t in all_tenants if t.get("status") == "archived"],
        "deleted": [t for t in all_tenants if t.get("status") == "deleted"],
        "uninitialized": [t for t in all_tenants if t.get("status") == "uninitialized"]
    }
    
    return {
        "total": len(all_tenants),
        "by_status": by_status,
        "tenants": all_tenants,
        "source": "tenant_registry"
    }


@router.get("/status/{db_name}")
async def get_tenant_status(db_name: str):
    """Get status of a specific tenant"""
    client = get_mongo_client()
    
    try:
        all_dbs = await client.list_database_names()
        if db_name not in all_dbs:
            raise HTTPException(status_code=404, detail=f"Tenant database '{db_name}' not found")
        
        db = client[db_name]
        metadata = await db["_tenant_metadata"].find_one({}, {"_id": 0})
        
        if not metadata:
            return {
                "db_name": db_name,
                "status": "uninitialized",
                "message": "Tenant exists but has no metadata"
            }
        
        return {
            "db_name": db_name,
            "status": metadata.get("status", "unknown"),
            "metadata": metadata
        }
    finally:
        client.close()


@router.post("/sync-display-config")
async def sync_display_config():
    """
    Sync display configuration to _tenant_metadata.
    This ensures display info is stored in the database.
    """
    client = get_mongo_client()
    updates = []
    
    try:
        for db_name, config in TENANT_DISPLAY_CONFIG.items():
            all_dbs = await client.list_database_names()
            if db_name in all_dbs:
                db = client[db_name]
                result = await db["_tenant_metadata"].update_one(
                    {},
                    {"$set": {
                        "display_name": config.get("name"),
                        "display_description": config.get("description"),
                        "display_business_type": config.get("business_type"),
                        "display_icon": config.get("icon"),
                        "display_color": config.get("color"),
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }},
                    upsert=False
                )
                updates.append({
                    "db_name": db_name,
                    "updated": result.modified_count > 0
                })
    finally:
        client.close()
    
    return {
        "message": "Display config synced",
        "updates": updates
    }


@router.get("/version-matrix")
async def get_tenant_version_matrix():
    """
    Get blueprint version matrix for all tenants.
    Used for monitoring tenant sync status.
    """
    all_tenants = await get_all_tenants_from_registry()
    
    matrix = []
    current_version = "2.0.0"  # Current blueprint version
    
    for tenant in all_tenants:
        version = tenant.get("blueprint_version")
        matrix.append({
            "db_name": tenant.get("db_name"),
            "name": tenant.get("name"),
            "blueprint_version": version,
            "is_current": version == current_version,
            "status": tenant.get("status"),
            "needs_sync": version != current_version and tenant.get("status") == "active",
            "last_migrated_at": tenant.get("last_migrated_at")
        })
    
    synced = sum(1 for m in matrix if m.get("is_current"))
    drift = sum(1 for m in matrix if m.get("needs_sync"))
    
    return {
        "current_blueprint_version": current_version,
        "total_tenants": len(matrix),
        "synced": synced,
        "drift": drift,
        "matrix": matrix
    }
