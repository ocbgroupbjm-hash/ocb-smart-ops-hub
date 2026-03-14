# AP Payment Delete Test
**Date**: 2026-03-14
**Tenant**: ocb_titan
**Status**: PASSED

## Test Objective
Verify that AP Payment delete follows Business Rule Engine.

## Business Rule Engine
- **DRAFT**: Delete allowed (soft delete)
- **POSTED**: Delete NOT allowed, must use Reversal
- **REVERSED**: No action allowed

## Frontend Verification
- ✅ Delete button (🗑️) only visible for DRAFT status
- ✅ Delete button hidden for POSTED status
- ✅ POSTED payments must use Reversal instead

## API Endpoint
```
DELETE /api/ap/payments/{payment_id}
```

## Test Results
```bash
# Delete DRAFT payment
Response: 200 OK
{
  "message": "Pembayaran berhasil dihapus"
}

# Delete POSTED payment
Response: 400 Bad Request
{
  "detail": "Pembayaran dengan status POSTED tidak dapat dihapus. Gunakan fitur Reversal."
}
```

## Soft Delete Implementation
- Payment marked as:
  - status: "deleted"
  - is_deleted: true
  - deleted_at: timestamp
  - deleted_by: user_id
- AP amounts restored (outstanding increased)

## Screenshot Evidence
See: /tmp/pembayaran_hutang_ui.png

## Conclusion
AP Payment delete follows Business Rule Engine with proper soft-delete.
