# AP Invoice Edit Test
**Date**: 2026-03-14
**Tenant**: ocb_titan
**Status**: PASSED

## Test Objective
Verify that AP Invoice (Daftar Hutang) edit follows Business Rule Engine.

## Business Rule Engine
- **DRAFT/OPEN without payments**: Edit allowed
- **OPEN with payments**: Edit NOT allowed, use jurnal koreksi
- **PAID**: Edit NOT allowed

## Frontend Verification
- ✅ Edit button (✏️) visible in AKSI column
- ✅ Edit button only shown when:
  - status !== 'paid'
  - paid_amount === 0
- ✅ Clicking Edit opens edit modal

## API Endpoint
```
PUT /api/ap/{ap_id}/edit
```

## Test Result
```bash
# Edit unpaid AP
Response: 200 OK
{
  "message": "Hutang berhasil diupdate"
}

# Edit paid AP
Response: 400 Bad Request
{
  "detail": "Hutang yang sudah ada pembayaran tidak bisa diedit"
}
```

## Screenshot Evidence
See: /tmp/daftar_hutang_ui.png
- Edit icon visible for unpaid rows
- Edit icon hidden for paid rows

## Conclusion
AP Invoice edit follows Business Rule Engine correctly.
