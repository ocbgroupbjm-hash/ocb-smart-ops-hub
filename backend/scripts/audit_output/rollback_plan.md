# OCB TITAN ERP - ROLLBACK PLAN

**Version:** 3.2.0
**Created:** 2026-03-13T21:53:43.339578+00:00

## Rollback Triggers

Rollback jika:
1. Trial Balance tidak balance setelah production
2. Data corruption terdeteksi
3. Critical security issue
4. Performance degradation > 50%

## Rollback Steps

### Step 1: Stop Services
```bash
sudo supervisorctl stop backend frontend
```

### Step 2: Restore Database
```bash
# List available backups
ls -la /app/backend/backups/

# Restore from latest backup
mongorestore --uri="$MONGO_URL" --archive=/app/backend/backups/[BACKUP_FILE] --gzip --drop
```

### Step 3: Rollback Code
```bash
# Use Emergent Platform rollback feature
# Or git checkout to previous stable commit
```

### Step 4: Restart Services
```bash
sudo supervisorctl start backend frontend
```

### Step 5: Verify
```bash
# Run health check
curl $API_URL/api/health

# Run trial balance check
python3 scripts/test_phase2_verification.py
```

## Backup Schedule

- Daily: 01:00 UTC
- Weekly: Sunday 02:00 UTC
- Monthly: 1st 03:00 UTC

## Contact

- Technical Lead: Developer
- Business Owner: CEO

---

*Rollback plan for OCB TITAN ERP v3.2.0*
