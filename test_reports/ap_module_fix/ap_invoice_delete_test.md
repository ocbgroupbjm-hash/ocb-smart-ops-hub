# AP Invoice Delete Test
**Date**: 2026-03-14
**Tenant**: ocb_titan
**Status**: PASSED

## Test Objective
Verify that AP Invoice (Daftar Hutang) delete follows Business Rule Engine.

## Business Rule Engine
- **OPEN without payments**: Soft delete allowed
- **OPEN with payments**: Delete NOT allowed
- **PAID**: Delete NOT allowed

## Frontend Verification
- ✅ Delete button (🗑️) visible in AKSI column
- ✅ Delete button only shown when:
  - status !== 'paid'
  - paid_amount === 0
- ✅ Clicking Delete shows confirmation modal
- ✅ Confirmation requires user action

## API Endpoint
```
PUT /api/ap/{ap_id}/soft-delete
```

## Test Result
```bash
# Delete unpaid AP
Response: 200 OK
{
  "message": "Hutang berhasil dihapus"
}

# Delete paid AP
Response: 400 Bad Request
{
  "detail": "Tidak dapat menghapus hutang yang sudah ada pembayaran"
}
```

## Soft Delete Implementation
- Record marked as `is_deleted: true`
- `deleted_at` timestamp recorded
- `deleted_by` user recorded
- Record filtered from UI

## Screenshot Evidence
See: /tmp/daftar_hutang_ui.png
- Delete icon visible for unpaid rows
- Delete icon hidden for paid rows

## Conclusion
AP Invoice delete follows Business Rule Engine with proper soft-delete pattern.
