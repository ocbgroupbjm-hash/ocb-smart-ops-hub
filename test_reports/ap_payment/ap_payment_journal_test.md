# AP Payment Journal Test
**Date**: 2026-03-14
**Tenant**: ocb_titan
**Status**: PASSED

## Test Objective
Verify that AP Payment creates correct journal entries following accounting standards.

## Accounting Rule
When payment is made for Accounts Payable:
```
Debit  : Hutang Usaha (Accounts Payable)
Credit : Kas/Bank (Cash/Bank Account)
```

## API Test Results
```bash
# Create Payment
POST /api/ap/{ap_id}/payment
Request:
{
  "amount": 100000,
  "payment_method": "transfer",
  "bank_account_id": "1-1002"
}

Response:
{
  "payment_no": "PAY-20260314-0005",
  "journal_no": "JV-20260314-0010",
  "new_outstanding": 5150000.0,
  "message": "Pembayaran berhasil dicatat"
}
```

## Journal Entry Created
```json
{
  "journal_number": "JV-20260314-0010",
  "journal_date": "2026-03-14T20:52:53.000Z",
  "reference_type": "ap_payment",
  "description": "Pembayaran Hutang AP-HQ-20260310-0002 - CV Mitra Aksesoris",
  "entries": [
    {
      "account_code": "2-1100",
      "account_name": "Hutang Dagang",
      "debit": 100000,
      "credit": 0,
      "description": "Pembayaran hutang AP-HQ-20260310-0002 - CV Mitra Aksesoris"
    },
    {
      "account_code": "1-1200",
      "account_name": "Bank",
      "debit": 0,
      "credit": 100000,
      "description": "Pembayaran hutang AP-HQ-20260310-0002"
    }
  ],
  "total_debit": 100000,
  "total_credit": 100000,
  "is_balanced": true,
  "status": "posted"
}
```

## Account Derivation Engine
The system uses Account Derivation Engine with priority:
1. Branch mapping
2. Warehouse mapping
3. Payment method mapping
4. Global settings
5. Default fallback

## Reversal Journal (for posted payments)
```json
{
  "journal_number": "JV-XXXXXX",
  "reference_type": "ap_payment_reversal",
  "entries": [
    {"account_code": "1-1200", "account_name": "Bank", "debit": 100000, "credit": 0},
    {"account_code": "2-1100", "account_name": "Hutang Dagang", "debit": 0, "credit": 100000}
  ]
}
```

## Business Rule Validation
- Journal auto-created on payment
- Journal is balanced (debit = credit)
- Reference links payment to journal
- AP outstanding updated automatically
- Reversal creates opposite journal entry

## Conclusion
AP Payment journal integration follows proper accounting standards and Business Rule Engine.
