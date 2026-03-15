# ROLLBACK PLAN - ERP STABILIZATION FIX
## OCB TITAN ERP × AI - Blueprint v2.4.3
## Date: 2026-03-15

---

## 1. PERUBAHAN YANG DILAKUKAN

### TASK 1: Multi-Tenant Routing
| File | Change | Reversible |
|------|--------|------------|
| `/app/backend/database.py` | Changed from global variable to contextvars | YES |
| `/app/backend/middleware/tenant_isolation.py` | NEW: Tenant isolation middleware | YES (delete file) |
| `/app/backend/server.py` | Added TenantIsolationMiddleware | YES |
| `/app/backend/routes/auth.py` | JWT now includes tenant_id | YES |
| `/app/backend/utils/auth.py` | get_current_user sets db from token | YES |

### TASK 2: Purchase Module
| File | Change | Reversible |
|------|--------|------------|
| `/app/frontend/src/pages/purchase/PurchaseOrders.jsx` | Added warehouse, PIC, payment account, item search flow | YES |
| `/app/backend/routes/purchase.py` | Added new fields and validation | YES |
| `/app/backend/models/titan_models.py` | Updated PurchaseOrder model | YES |

### Database Changes
No direct data changes. All changes are schema/code level.

---

## 2. ROLLBACK STEPS

### Step 1: Restore database.py (if tenant issues)
```python
# Restore global variable approach
_active_db_name = os.environ.get('DB_NAME', 'ocb_titan')

def get_active_db_name() -> str:
    return _active_db_name

def set_active_db_name(db_name: str):
    global _active_db_name
    _active_db_name = db_name

def get_db():
    return client[_active_db_name]
```

### Step 2: Remove middleware (if issues)
```bash
# Delete middleware file
rm /app/backend/middleware/tenant_isolation.py

# Remove from server.py
# Comment out: from middleware.tenant_isolation import TenantIsolationMiddleware
# Comment out: app.add_middleware(TenantIsolationMiddleware)
```

### Step 3: Restore auth.py (if JWT issues)
```python
# Remove tenant_id from token_data
# Remove current_tenant = get_active_db_name()
```

### Step 4: Restore purchase form (if UI issues)
```bash
# Git revert the changes to PurchaseOrders.jsx
# Or manually remove new dropdowns
```

---

## 3. VERIFICATION AFTER ROLLBACK

1. Login should work for all tenants
2. Data should go to correct database
3. Purchase orders can be created
4. Assembly transactions work

---

## 4. CONTACTS

- System Architect: [Contact Info]
- DevOps: [Contact Info]

---

## 5. NOTES

- All changes are code-level, no data was modified
- Database schema additions are backward compatible
- New fields use default values
