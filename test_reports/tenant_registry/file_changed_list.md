# OCB TITAN ERP - Files Changed (Tenant Login Fix)
**Date:** 2026-03-14
**Task:** TASK 1 - Fix Bug Tenant Login Page

---

## FILES CHANGED

### 1. NEW FILE: `/app/backend/routes/tenant_registry.py`
**Purpose:** Single Source of Truth for tenant list
**Lines:** ~250

**Key Functions:**
- `get_all_tenants_from_registry()` - Read _tenant_metadata from all databases
- `/api/tenant-registry/list` - List active tenants only
- `/api/tenant-registry/all` - List all tenants by status
- `/api/tenant-registry/version-matrix` - Blueprint sync status

---

### 2. MODIFIED: `/app/backend/routes/business.py`
**Change:** Updated `/api/business/list` endpoint

**Before:**
```python
@router.get("/list")
async def list_businesses():
    businesses = load_businesses()  # Read from JSON file
    visible_businesses = [b for b in businesses if b.get("show_in_login_selector", True)]
    return {"businesses": visible_businesses, "current_db": get_active_db_name()}
```

**After:**
```python
@router.get("/list")
async def list_businesses():
    from routes.tenant_registry import get_all_tenants_from_registry
    all_tenants = await get_all_tenants_from_registry()  # Read from _tenant_metadata
    visible_businesses = [t for t in all_tenants if t.get("status") == "active"]
    return {"businesses": visible_businesses, "current_db": get_active_db_name(), "source": "tenant_registry"}
```

---

### 3. MODIFIED: `/app/backend/routes/tenant_blueprint.py`
**Change:** Added businesses.json sync on tenant delete

**Addition:**
```python
# 5b. Sync businesses.json file (remove deleted tenant)
try:
    from routes.business import load_businesses, save_businesses
    businesses = load_businesses()
    businesses = [b for b in businesses if b.get("db_name") != target_db]
    save_businesses(businesses)
except Exception:
    pass
```

---

### 4. MODIFIED: `/app/backend/server.py`
**Change:** Register tenant_registry router

**Addition:**
```python
# Tenant Registry - SINGLE SOURCE OF TRUTH for tenant list
from routes.tenant_registry import router as tenant_registry_router
app.include_router(tenant_registry_router)
```

---

## API CHANGES

| Endpoint | Method | Change |
|----------|--------|--------|
| `/api/business/list` | GET | Source changed to tenant_registry |
| `/api/tenant-registry/list` | GET | NEW - Active tenants only |
| `/api/tenant-registry/all` | GET | NEW - All tenants by status |
| `/api/tenant-registry/version-matrix` | GET | NEW - Blueprint sync status |
| `/api/tenant-registry/status/{db_name}` | GET | NEW - Single tenant status |
| `/api/tenant-registry/sync-display-config` | POST | NEW - Sync display config |

---

## DATABASE CHANGES

No database migration needed. Uses existing `_tenant_metadata` collection.

---

## MIGRATION SCRIPT

Not required - uses existing data structure.

---

## ROLLBACK PLAN

1. Revert `/app/backend/routes/business.py`:
   - Change `list_businesses()` back to use `load_businesses()` directly
2. Remove import from server.py:
   - Remove tenant_registry router
3. Restart backend:
   - `sudo supervisorctl restart backend`

---

*Files Changed Report - OCB TITAN ERP*
