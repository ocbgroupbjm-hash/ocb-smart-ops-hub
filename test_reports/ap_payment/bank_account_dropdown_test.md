# Bank/Kas Account Dropdown Test
**Date**: 2026-03-14
**Tenant**: ocb_titan
**Status**: PASSED

## Test Objective
Verify that Bank/Kas dropdown correctly fetches and displays Cash and Bank accounts from chart_of_accounts.

## Bug Description (BUG 2 - FIXED)
Field Bank/Kas was not showing account list. The API call was incorrect.

## Root Cause
Frontend was calling wrong endpoint:
- Old: `/api/accounting/coa?type=kas` (does not exist)
- Fixed: `/api/accounts/cash-bank` (correct endpoint)

## API Test Results
```bash
GET /api/accounts/cash-bank

Response:
{
  "accounts": [
    {"id": "1-1001", "code": "1-1001", "name": "Kas", "sub_type": "cash"},
    {"id": "1-1002", "code": "1-1002", "name": "Bank BCA", "sub_type": "bank"},
    {"id": "1-1003", "code": "1-1003", "name": "Bank BRI", "sub_type": "bank"},
    {"id": "1101", "code": "1101", "name": "Kas", "sub_type": "cash"},
    {"id": "1102", "code": "1102", "name": "Bank", "sub_type": "bank"},
    {"id": "1103", "code": "1103", "name": "Kas Kecil Pusat", "sub_type": "cash"}
  ],
  "total": 9
}
```

## Query Logic
```javascript
// Filter from chart_of_accounts
WHERE account_type IN ('cash', 'bank')
  AND status = 'active'
  AND name NOT LIKE '%Piutang%'
  AND name NOT LIKE '%Hutang%'
```

## Frontend Fix
Updated PurchasePayments.jsx:
```javascript
// Before (wrong)
const bankRes = await api('/api/accounting/coa?type=kas');

// After (correct)
const bankRes = await api('/api/accounts/cash-bank');
```

## Visual Verification
Screenshot shows dropdown with all accounts:
- 1-1001 - Kas
- 1-1002 - Bank BCA
- 1-1003 - Bank BRI
- 1101 - Kas
- 1102 - Bank
- 1103 - Kas Kecil Pusat

## Conclusion
Bank/Kas dropdown now correctly fetches and displays Cash/Bank accounts.
