# Bank/Kas Dropdown Fix Test Report
**Date**: 2026-03-14
**Tenant**: ocb_titan
**Status**: PASSED

## Bug Description
Field Bank/Kas dalam form Pembayaran Hutang tidak menampilkan daftar akun.

## Root Cause Analysis
Frontend memanggil endpoint yang salah:
- **Wrong**: `/api/accounting/coa?type=kas` (endpoint tidak ada)
- **Correct**: `/api/accounts/cash-bank` (endpoint yang benar)

## Fix Applied
Updated `PurchasePayments.jsx`:
```javascript
// Changed from wrong endpoint
const bankRes = await api('/api/accounting/coa?type=kas');

// To correct endpoint
const bankRes = await api('/api/accounts/cash-bank');
```

## API Verification
```bash
GET /api/accounts/cash-bank
Authorization: Bearer {token}

Response (200 OK):
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

## Filter Logic
```sql
SELECT * FROM chart_of_accounts
WHERE account_type IN ('cash', 'bank')
AND status = 'active'
```

## Visual Verification
Screenshot shows dropdown populated with:
- 1-1001 - Kas
- 1-1002 - Bank BCA
- 1-1003 - Bank BRI
- 1101 - Kas
- 1102 - Bank
- 1103 - Kas Kecil Pusat

## UI Styling (per design guideline)
- Background: #1E293B (card dark)
- Text: #E5E7EB (primary light)
- Border: #334155 (subtle slate)
- NO white background
- NO yellow text

## Conclusion
Bank/Kas dropdown now correctly fetches and displays Cash/Bank accounts with proper styling.
