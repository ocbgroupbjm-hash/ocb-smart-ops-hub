# SN GENERATION TEST
## PRIORITAS 5: Serial Number Range

**Date:** 2026-03-14
**Tenant:** ocb_titan
**Status:** IMPLEMENTED ✅

---

## Implementation

### Backend Endpoints

**1. Generate Serial Numbers**
```
POST /api/purchase/serial-numbers/generate
```

Request:
```json
{
  "item_id": "test-item-001",
  "product_id": "test-product-001", 
  "sn_start": "10001",
  "sn_end": "10010"
}
```

Response:
```json
{
  "success": true,
  "count": 10,
  "serial_numbers": ["10001", "10002", "10003", "10004", "10005", "10006", "10007", "10008", "10009", "10010"],
  "sn_start": "10001",
  "sn_end": "10010"
}
```

**2. List Serial Numbers**
```
GET /api/purchase/serial-numbers?product_id=xxx&status=available
```

**3. Update Serial Number Status**
```
PUT /api/purchase/serial-numbers/{sn_id}/status
```

---

## Database Schema

**Collection:** `inventory_serial_numbers`

| Field | Type | Description |
|-------|------|-------------|
| id | string | UUID |
| item_id | string | Purchase item ID |
| product_id | string | Product ID |
| serial_number | string | The serial number |
| purchase_id | string | Purchase order ID |
| status | string | available/sold/damaged/returned |
| created_at | datetime | Creation timestamp |

---

## Frontend Implementation

**File:** `/app/frontend/src/pages/purchase/PurchaseOrders.jsx`

Added columns:
- SN Awal (sn_start)
- SN Akhir (sn_end)
- Shows unit count when both filled

---

## Test Results

**Test 1: Generate 10 serial numbers**
- Input: SN Awal = 10001, SN Akhir = 10010
- Output: 10 serial numbers generated
- Status: PASS ✅

**Test 2: Validation**
- SN End < SN Start → Error
- Max 1000 per batch → Enforced
- Leading zeros preserved

---

**SERIAL NUMBER RANGE COMPLETED ✅**
