# INVOICE REVERSAL FLOW TEST REPORT
## TASK 2: Perbaiki Edit Invoice yang Sudah LUNAS

**Date:** 2026-03-14
**Tenant:** ocb_titan
**Status:** IMPLEMENTED

---

## Problem Statement
Invoice yang sudah PAID tidak boleh diedit langsung.

Flow yang benar:
```
PAID → create reversal → create correction invoice
```

## Implementation

### New Endpoint: POST /api/ap/{ap_id}/reversal

```python
class APReversalRequest(BaseModel):
    reason: str = "Invoice correction"
    create_correction: bool = False
    correction_amount: Optional[float] = None
```

### Flow Steps:
1. Create reversal journal (reverse all payments)
2. Update invoice status to "reversed"
3. Optionally create correction invoice
4. Link ke invoice lama

### Business Rules
| Rule | Implementation |
|------|----------------|
| PAID invoice tidak bisa edit langsung | ✅ Blocked |
| Reversal creates journal | ✅ Dr. Kas, Cr. Hutang |
| All payments marked as reversed | ✅ status="reversed" |
| Correction invoice linked to original | ✅ original_invoice_id field |

---

## API Response Example
```json
{
  "message": "Invoice berhasil di-reverse",
  "ap_no": "AP-XXX",
  "new_status": "reversed",
  "reversed_payments": [
    {"payment_no": "PAY-XXX", "amount": 1000000, "reversal_journal_no": "JV-XXX"}
  ],
  "total_reversed": 1000000,
  "correction_invoice_no": "CORR-AP-XXX"
}
```

---

## Files Modified
- `/app/backend/routes/ap_system.py` - New reversal endpoint

**TASK 2: COMPLETED**
