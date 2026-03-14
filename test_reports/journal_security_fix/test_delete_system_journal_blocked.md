# TEST DELETE SYSTEM JOURNAL BLOCKED
## PRIORITAS 1: Journal Security Fix

**Date:** 2026-03-14
**Tenant:** ocb_titan
**Status:** IMPLEMENTED ✅

---

## Test Case: Delete System Journal (Should be BLOCKED)

### Protected Journal Types
- Purchase journals
- Payment journals
- AP journals
- AR journals
- Inventory journals
- Payroll journals
- Sales journals
- Cash/Bank journals

### Expected Behavior

When attempting to delete a system-generated journal:

**Request:**
```bash
DELETE /api/accounting/journals/{system_journal_id}
```

**Expected Response:**
```json
{
  "detail": "System generated journal cannot be deleted. Jurnal yang dihasilkan sistem tidak dapat dihapus."
}
```

**HTTP Status:** 403 Forbidden

---

## Frontend Security

### Button State
- Delete button DISABLED for system journals
- Tooltip: "Jurnal sistem tidak dapat dihapus"
- Gray color indicator for disabled state

### Implementation
```javascript
const isJournalDeletable = (journal) => {
  const journalSource = (journal.journal_source || journal.reference_type || journal.source || 'manual').toLowerCase();
  const protectedSources = ['purchase', 'pembelian', 'payment', 'pembayaran', 'ap', 'ar', 'inventory', 'payroll', 'sales', 'penjualan', 'cash', 'bank', 'pos'];
  return !protectedSources.some(s => journalSource.includes(s)) && !(journal.reference_id && journalSource !== 'manual');
};
```

---

## Check Deletable Endpoint

New endpoint for frontend validation:
```bash
GET /api/accounting/journals/{journal_id}/can-delete
```

**Response:**
```json
{
  "can_delete": false,
  "journal_source": "purchase",
  "is_system_journal": true,
  "reason": "Jurnal sistem (purchase) tidak dapat dihapus"
}
```

---

## Files Modified
- `/app/backend/routes/accounting.py` - Delete security check
- `/app/backend/routes/accounting_engine.py` - journal_source field
- `/app/frontend/src/pages/accounting/JournalEntries.jsx` - UI security

---

**SYSTEM JOURNALS PROTECTED FROM DELETION ✅**
