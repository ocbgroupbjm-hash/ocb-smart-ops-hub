# E2E REGRESSION REPORT

**Test Date:** 2026-03-13T21:53:42.373593+00:00

## Flow Tests

| Flow | Endpoint | Status | HTTP Code |
|------|----------|--------|-----------|
| Sales | /api/sales | ⏭️ SKIP | 404 |
| Purchase | /api/purchases | ⏭️ SKIP | 404 |
| Stock Adjustment | /api/inventory/adjustments | ⏭️ SKIP | 404 |
| AR List | /api/ar/list | ✅ PASS | 200 |
| AP List | /api/ap/list | ✅ PASS | 200 |
| Trial Balance | /api/accounting/trial-balance | ✅ PASS | 200 |
| Cash Control | /api/cash/shifts | ⏭️ SKIP | 404 |

## Summary

- **Total Flows Tested:** 7
- **Passed:** 3
- **Skipped:** 4
