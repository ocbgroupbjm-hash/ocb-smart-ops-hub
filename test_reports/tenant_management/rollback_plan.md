# OCB TITAN ERP - Tenant Management Rollback Plan

**Generated:** 2026-03-14
**Version:** 4.0.0

---

## PURPOSE

Dokumen ini menjelaskan prosedur rollback jika terjadi masalah pada modul Tenant Management.

---

## PRE-DEPLOYMENT CHECKLIST

- [x] Backup database ocb_titan sebelum deployment
- [x] Test semua endpoint di staging
- [x] Verify RBAC protection
- [x] Verify audit logging

---

## ROLLBACK TRIGGERS

Rollback diperlukan jika:
1. Delete tenant menghapus data tanpa konfirmasi
2. Edit tenant mengubah data yang salah
3. Tenant creation gagal membuat database
4. RBAC bypass terdeteksi

---

## ROLLBACK PROCEDURE

### Step 1: Identifikasi Masalah
```bash
# Check backend logs
tail -100 /var/log/supervisor/backend.err.log

# Check audit logs
db.audit_logs.find({entity_type: "tenant"}).sort({timestamp: -1}).limit(10)
```

### Step 2: Stop Traffic
```bash
# Set maintenance mode
curl -X POST "$API_URL/api/system/maintenance-mode" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"mode": "EMERGENCY_ROLLBACK"}'
```

### Step 3: Restore Database (jika diperlukan)
```bash
# Restore dari backup terakhir
cd /app/backend/scripts/backup
bash restore_drill.sh
```

### Step 4: Rollback Code
```bash
# Jika menggunakan git
git log --oneline -10
git revert <commit_hash>

# Atau restore dari backup file
cp /app/backup/TenantManagement.jsx.bak /app/frontend/src/pages/settings/TenantManagement.jsx
```

### Step 5: Verify
```bash
# Test endpoint
curl -s "$API_URL/api/tenant/tenants" -H "Authorization: Bearer $TOKEN"

# Check tenant count
db.tenants.countDocuments()
```

### Step 6: Resume Operation
```bash
# Deactivate maintenance mode
curl -X DELETE "$API_URL/api/system/maintenance-mode" \
  -H "Authorization: Bearer $TOKEN"
```

---

## ROLLBACK CONTACTS

| Role | Name | Contact |
|------|------|---------|
| CTO | - | - |
| DevOps | - | - |
| DBA | - | - |

---

## POST-ROLLBACK ACTIONS

1. Investigate root cause
2. Create incident report
3. Update test cases
4. Re-deploy with fix

---

*Document maintained by OCB TITAN DevOps Team*
