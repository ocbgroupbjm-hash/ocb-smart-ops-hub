# AP Payment Create Test
**Date**: 2026-03-14
**Tenant**: ocb_titan
**Status**: PASSED

## Test Objective
Verify that AP Payment creation works correctly with proper journal generation.

## Test Steps
1. Navigate to Hutang > Pembayaran Hutang
2. Click "Tambah Pembayaran"
3. Select Supplier
4. Select outstanding AP
5. Enter payment amount
6. Select payment method
7. Select Bank/Kas account
8. Submit payment

## API Test Results
```bash
API_URL: https://smart-ops-hub-6.preview.emergentagent.com

# Create Payment Test
POST /api/ap/{ap_id}/payment
Request:
{
  "amount": 100000,
  "payment_method": "transfer",
  "bank_account_id": "1-1002",
  "reference_no": "TEST-001",
  "notes": "Test payment"
}

Response:
{
  "payment_no": "PAY-20260314-0005",
  "journal_no": "JV-20260314-0010",
  "new_outstanding": 5150000.0,
  "message": "Pembayaran berhasil dicatat"
}
```

## Verification
- Payment created with unique number: PAY-20260314-0005
- Journal entry auto-created: JV-20260314-0010
- AP outstanding updated correctly
- Payment appears in list

## Business Rule Compliance
- Payment amount validated against outstanding
- Journal auto-generated with correct accounts:
  - Debit: Hutang Usaha
  - Credit: Kas/Bank

## Conclusion
AP Payment creation functionality is working correctly.
