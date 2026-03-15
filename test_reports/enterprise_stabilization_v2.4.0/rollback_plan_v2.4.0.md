# Rollback Plan - Blueprint v2.4.0

## Overview
Prosedur rollback jika ditemukan masalah setelah deployment v2.4.0.

## Pre-Rollback Checklist
- [ ] Identifikasi masalah dan dampaknya
- [ ] Komunikasikan ke semua user tentang downtime
- [ ] Backup database terbaru sebelum rollback
- [ ] Siapkan tim support untuk monitoring post-rollback

## Rollback Steps

### Step 1: Revert Blueprint Version
```python
# File: /app/backend/routes/tenant_blueprint.py
# Line 16

# Change FROM:
CURRENT_BLUEPRINT_VERSION = "2.4.0"  # Enterprise Stabilization

# Change TO:
CURRENT_BLUEPRINT_VERSION = "2.3.0"  # Previous stable
```

### Step 2: Restart Backend
```bash
sudo supervisorctl restart backend
sleep 5
sudo supervisorctl status backend
```

### Step 3: Sync Tenants to Previous Version
```bash
curl -X POST "$API_URL/api/tenant/sync-all" \
  -H "Authorization: Bearer $TOKEN"
```

### Step 4: Frontend Rollback (if needed)

#### Revert Quick Create Supplier
```javascript
// File: /app/frontend/src/components/master/ItemFormModal.jsx
// Revert SearchableSelectWithCreate to SearchableSelect for supplier field
```

### Step 5: Verify Rollback
```bash
# Check blueprint status
curl "$API_URL/api/tenant/blueprint-status" \
  -H "Authorization: Bearer $TOKEN"

# Should show v2.3.0 for all tenants
```

## Changes in v2.4.0 to Rollback

| Component | Change | Rollback Action |
|-----------|--------|-----------------|
| tenant_blueprint.py | Version → 2.4.0 | Change to 2.3.0 |
| QuickCreateModal.jsx | Added supplier type | Remove supplier config |
| ItemFormModal.jsx | SearchableSelectWithCreate | Revert to SearchableSelect |

## File Backup Locations

| File | Backup |
|------|--------|
| tenant_blueprint.py | /app/backups/v2.3.0/ |
| QuickCreateModal.jsx | /app/backups/v2.3.0/ |
| ItemFormModal.jsx | /app/backups/v2.3.0/ |

## Post-Rollback Verification

| Check | Command | Expected |
|-------|---------|----------|
| Blueprint version | `/api/tenant/blueprint-status` | v2.3.0 |
| Login | `/api/auth/login` | Token received |
| Products | `/api/products` | Data returned |
| Suppliers | `/api/suppliers` | Data returned |

## Recovery Time Estimate
- Rollback execution: ~5 minutes
- Verification: ~10 minutes
- Total: ~15 minutes

## Contact Information
- System Architect: [Contact info]
- DevOps: [Contact info]
- Database Admin: [Contact info]

## Notes
- Rollback hanya dilakukan jika ada masalah critical
- Pastikan backup database tersedia sebelum rollback
- Monitor sistem setelah rollback selama minimal 1 jam

---
Created: 2026-03-15
Blueprint: v2.4.0
Previous: v2.3.0
