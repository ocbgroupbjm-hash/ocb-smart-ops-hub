# ROLLBACK PLAN - OCB TITAN ERP v2.4.3
**Generated:** 2026-03-30T10:35:00Z
**Blueprint:** v2.4.3
**Lock ID:** BP-LOCK-1774866673409

---

## ROLLBACK TRIGGERS

Rollback diperlukan jika:
1. Critical bug ditemukan setelah deployment
2. Data corruption terdeteksi
3. Cross-tenant leak terjadi
4. Journal imbalance muncul
5. Business operation terganggu

---

## ROLLBACK STEPS

### Step 1: Stop All Services
```bash
sudo supervisorctl stop backend frontend
```

### Step 2: Restore Database dari Backup
```bash
# Restore setiap tenant
for tenant in ocb_titan ocb_unit_4 ocb_unt_1 ocb_test_new; do
  mongorestore --db $tenant \
    --dir /app/backups/production_deployment_20260330/$tenant/ \
    --drop
done
```

### Step 3: Verify Restore
```bash
mongosh --eval "
  var tenants = ['ocb_titan', 'ocb_unit_4', 'ocb_unt_1'];
  tenants.forEach(function(t) {
    var count = db.getSiblingDB(t).products.countDocuments();
    print(t + ': ' + count + ' products');
  });
"
```

### Step 4: Restart Services
```bash
sudo supervisorctl start backend frontend
```

### Step 5: Smoke Test
- Login ke setiap tenant
- Verify dashboard loads
- Check journal balance

---

## BACKUP LOCATIONS

| Tenant | Path | Size |
|--------|------|------|
| ocb_titan | /app/backups/production_deployment_20260330/ocb_titan/ | 494M |
| ocb_unit_4 | /app/backups/production_deployment_20260330/ocb_unit_4/ | 520K |
| ocb_unt_1 | /app/backups/production_deployment_20260330/ocb_unt_1/ | 49M |
| ocb_test_new | /app/backups/production_deployment_20260330/ocb_test_new/ | 276K |

---

## ROLLBACK VALIDATION

After rollback, verify:
- [ ] All tenants accessible
- [ ] Login works
- [ ] Dashboard shows correct data
- [ ] Journal balance is BALANCED
- [ ] No error in backend logs

---

## CONTACT

**Rollback Authority:** TITAN (System Architect)
**Execution:** E1 Autonomous Agent

---

**IMPORTANT:** Do NOT delete backup files until v2.4.3 is confirmed stable in production for 7 days.
