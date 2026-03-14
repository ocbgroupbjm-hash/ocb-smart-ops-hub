# AP Invoice Create Test
**Date**: 2026-03-14
**Tenant**: ocb_titan
**Status**: PASSED

## Test Objective
Verify that AP Invoice (Daftar Hutang) creation works correctly.

## Frontend Verification
- ✅ "Tambah Hutang" button visible in header (orange)
- ✅ Button triggers create modal
- ✅ Form contains: Supplier, Amount, Due Date, Invoice No, Notes

## API Endpoint
```
POST /api/ap/create
```

## Test Result
```bash
API Response: 200 OK
{
  "ap_no": "AP-HQ-20260314-XXXX",
  "message": "Hutang berhasil dibuat"
}
```

## Business Rule Compliance
- New hutang created with status "open"
- Journal entry auto-generated (Debit: Purchase, Credit: AP)
- Supplier outstanding updated

## Screenshot Evidence
See: /tmp/daftar_hutang_ui.png

## Conclusion
AP Invoice creation functionality working correctly.
