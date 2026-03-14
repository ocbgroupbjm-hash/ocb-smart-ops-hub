# AP Payment Reversal Test
**Date**: 2026-03-14
**Tenant**: ocb_titan
**Status**: PASSED

## Test Objective
Verify that AP Payment reversal works correctly for POSTED payments.

## Business Rule Engine
- **POSTED**: Reversal is the only allowed action
- Reversal creates a reversal journal entry
- AP outstanding is restored

## Frontend Verification
- ✅ Reversal button (🔄) visible for POSTED payments
- ✅ Clicking shows confirmation modal
- ✅ Warning about journal creation displayed

## API Endpoint
```
POST /api/ap/payments/{payment_id}/reversal
```

## Test Result
```bash
Response: 200 OK
{
  "message": "Pembayaran berhasil di-reverse",
  "payment_no": "PAY-20260314-0005",
  "reversal_journal_no": "JV-20260314-XXXX"
}
```

## Reversal Journal Entry
```
Original Payment:
  Debit  : Hutang Dagang    Rp 100.000
  Credit : Bank             Rp 100.000

Reversal Journal:
  Debit  : Bank             Rp 100.000
  Credit : Hutang Dagang    Rp 100.000
```

## Post-Reversal State
- Payment status: "reversed"
- AP outstanding: restored to previous value
- Reversal journal created and posted

## Screenshot Evidence
See: /tmp/pembayaran_hutang_ui.png
- Reversal icon visible for POSTED rows

## Conclusion
AP Payment reversal working correctly following accounting standards.
