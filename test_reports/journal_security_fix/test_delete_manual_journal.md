# TEST DELETE MANUAL JOURNAL
## PRIORITAS 1: Journal Security Fix

**Date:** 2026-03-14
**Tenant:** ocb_titan
**Status:** PASSED ✅

---

## Test Case: Delete Manual Journal

### Precondition
- Journal dengan source = "manual"
- Journal tanpa reference_id

### Test Execution
```bash
DELETE /api/accounting/journals/{journal_id}
```

### Result
```json
{
  "message": "Jurnal manual berhasil dihapus"
}
```

### Status: PASS ✅

---

## Implementation Details

### Backend Changes
- Added `PROTECTED_JOURNAL_SOURCES` list
- Check `journal_source` or `reference_type` before delete
- Return 403 error for system journals

### Protected Sources
```python
PROTECTED_JOURNAL_SOURCES = [
    "purchase", "pembelian",
    "payment", "pembayaran", 
    "ap", "hutang", "accounts_payable",
    "ar", "piutang", "accounts_receivable",
    "inventory", "persediaan", "stock",
    "payroll", "gaji",
    "sales", "penjualan",
    "cash", "bank", "kas",
    "pos", "retur", "return"
]
```

### New Field: journal_source
All new manual journals now include:
```json
{
  "journal_source": "manual"
}
```

---

**TEST PASSED: Manual journals can be deleted ✅**
