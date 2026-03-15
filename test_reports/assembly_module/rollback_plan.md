# Assembly Module Enterprise - Rollback Plan

## Tanggal: 2026-03-16
## Tenant: ocb_titan (Pilot)
## Blueprint Version: v2.3.0 → v2.4.0

---

## Overview

Dokumen ini menjelaskan rencana rollback jika terjadi masalah pada Assembly Module Enterprise upgrade.

## Komponen Terdampak

1. **Backend Routes:**
   - `/app/backend/routes/assembly_enterprise.py` (NEW)
   - `/app/backend/server.py` (MODIFIED - added router)

2. **Database Collections (NEW):**
   - `assembly_formulas`
   - `assembly_components`
   - `assembly_transactions` (extended)
   - `assembly_logs`

3. **Existing Collections (UNCHANGED):**
   - `stock_movements` - movement types added
   - `journal_entries` - reference types added

---

## Rollback Steps

### Step 1: Remove New Router
```python
# Di server.py, hapus baris:
from routes.assembly_enterprise import router as assembly_enterprise_router
app.include_router(assembly_enterprise_router)
```

### Step 2: Preserve Old Assembly Module
File `/app/backend/routes/assembly.py` tetap berfungsi sebagai fallback.

### Step 3: Database Cleanup (Jika Diperlukan)
```javascript
// Di MongoDB, hapus collections baru:
db.assembly_formulas.drop()
db.assembly_components.drop()
db.assembly_logs.drop()

// Hapus transaksi v2:
db.assembly_transactions.deleteMany({"source_ref_type": "assembly"})

// Hapus stock movements yang terkait:
db.stock_movements.deleteMany({"movement_type": {"$in": [
  "ASSEMBLY_CONSUME", 
  "ASSEMBLY_PRODUCE",
  "ASSEMBLY_CONSUME_REVERSAL",
  "ASSEMBLY_PRODUCE_REVERSAL"
]}})

// Hapus journal entries yang terkait:
db.journal_entries.deleteMany({"reference_type": {"$in": [
  "assembly",
  "assembly_reversal"
]}})
```

### Step 4: Restart Services
```bash
sudo supervisorctl restart backend
```

---

## Verification After Rollback

1. Test old assembly endpoints:
   - GET /api/assembly/formulas ✓
   - POST /api/assembly/assemble ✓
   - POST /api/assembly/disassemble ✓

2. Verify no errors in logs:
   ```bash
   tail -n 50 /var/log/supervisor/backend.err.log
   ```

---

## Point of No Return

Rollback TIDAK disarankan setelah:
- Production data sudah diinput ke formula v2
- Transaksi assembly v2 sudah di-POST dengan journal entries

---

## Contact

System Architect: OCB TITAN
Developer: E1 Agent
