# OCB TITAN - System Info API
# Provides current tenant/database information for UI display

from fastapi import APIRouter, Depends
from database import get_active_db_name, get_db
from utils.auth import get_current_user
from routes.tenant_blueprint import CURRENT_BLUEPRINT_VERSION
import json
import os

router = APIRouter(prefix="/api/system", tags=["System Info"])

BUSINESS_FILE = "/app/backend/data/businesses.json"

def load_businesses():
    """Load business registry"""
    try:
        with open(BUSINESS_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

@router.get("/current-tenant")
async def get_current_tenant():
    """
    Get current active tenant information for header display.
    Source of truth: Tenant Registry (businesses.json)
    """
    current_db = get_active_db_name()
    businesses = load_businesses()
    
    # Find current tenant in registry
    current_tenant = None
    for b in businesses:
        if b.get("db_name") == current_db:
            current_tenant = b
            break
    
    # If not found in registry, create minimal info
    if not current_tenant:
        current_tenant = {
            "id": current_db,
            "name": current_db.replace("_", " ").upper(),
            "db_name": current_db,
            "business_type": "Unknown",
            "is_internal": True
        }
    
    # Determine status
    status = "active"
    if current_tenant.get("is_test"):
        status = "test"
    elif current_tenant.get("is_internal"):
        status = "internal"
    
    return {
        "tenant_id": current_tenant.get("id"),
        "tenant_name": current_tenant.get("name"),
        "database": current_db,
        "tenant_type": current_tenant.get("business_type", "Unknown"),
        "description": current_tenant.get("description", ""),
        "status": status,
        "blueprint_version": CURRENT_BLUEPRINT_VERSION,
        "icon": current_tenant.get("icon", "building"),
        "color": current_tenant.get("color", "#991B1B")
    }


@router.get("/current-tenant/debug")
async def get_current_tenant_debug(user: dict = Depends(get_current_user)):
    """
    Get detailed tenant info for admin/debug purposes.
    Only accessible by super_admin and owner roles.
    """
    current_db = get_active_db_name()
    businesses = load_businesses()
    db = get_db()
    
    # Get tenant from registry
    current_tenant = None
    for b in businesses:
        if b.get("db_name") == current_db:
            current_tenant = b
            break
    
    # Get metadata from database
    metadata = await db["_tenant_metadata"].find_one({}, {"_id": 0})
    
    # Get counts
    stats = {
        "users": await db["users"].count_documents({}),
        "roles": await db["roles"].count_documents({}),
        "branches": await db["branches"].count_documents({}),
        "products": await db["products"].count_documents({}),
        "transactions": await db["transactions"].count_documents({})
    }
    
    # Check if user is admin
    is_admin = user.get("role") in ["super_admin", "owner", "admin"]
    
    response = {
        "tenant_id": current_tenant.get("id") if current_tenant else current_db,
        "tenant_name": current_tenant.get("name") if current_tenant else current_db,
        "database": current_db,
        "tenant_type": current_tenant.get("business_type") if current_tenant else "Unknown",
        "status": "active",
        "blueprint_version": CURRENT_BLUEPRINT_VERSION
    }
    
    # Add debug info for admin only
    if is_admin:
        response["debug"] = {
            "cluster": "MongoDB Local",
            "blueprint_version": metadata.get("blueprint_version") if metadata else "N/A",
            "migration_version": metadata.get("migration_version") if metadata else "N/A",
            "last_migrated_at": metadata.get("last_migrated_at") if metadata else "N/A",
            "stats": stats,
            "registry_entry": current_tenant
        }
    
    return response
