# AP Payment Create Test
**Date**: 2026-03-14
**Tenant**: ocb_titan
**Status**: PASSED

## Test Objective
Verify that AP Payment creation works correctly with journal generation.

## Frontend Verification
- ✅ "Tambah Pembayaran" button visible (orange)
- ✅ Button opens create payment modal
- ✅ Form contains: Supplier, Select AP, Amount, Payment Method, Bank/Kas

## API Endpoint
```
POST /api/ap/{ap_id}/payment
```

## Test Result
```bash
Request:
{
  "amount": 100000,
  "payment_method": "transfer",
  "bank_account_id": "1-1002"
}

Response: 200 OK
{
  "payment_no": "PAY-20260314-0005",
  "journal_no": "JV-20260314-XXXX",
  "new_outstanding": 5150000.0,
  "message": "Pembayaran berhasil dicatat"
}
```

## Journal Entry Generated
```
Debit  : 2-1100 Hutang Dagang    Rp 100.000
Credit : 1-1200 Bank              Rp 100.000
```

## Business Rule Compliance
- Payment created with status "posted"
- Journal auto-generated and balanced
- AP outstanding updated automatically

## Screenshot Evidence
See: /tmp/pembayaran_hutang_ui.png

## Conclusion
AP Payment creation working correctly with proper journal generation.
