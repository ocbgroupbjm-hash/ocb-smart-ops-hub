# OCB TITAN - INTEGRITY MONITORING REPORT

**Generated:** 2026-03-13T21:31:06.549101+00:00
**Tenant:** ocb_titan
**Overall Status:** CRITICAL

## Summary

- Total Checks: 7
- Passed: 4
- Warnings: 1
- Failed: 2

## Check Results

### ✅ Journal Balance

- **Status:** PASS
- **Total Debit:** 74689867.5
- **Total Credit:** 74689867.5
- **Difference:** 0.0
- **Journal Count:** 70
- **Unbalanced Count:** 0
- **Unbalanced Journals:** []
- **Checked At:** 2026-03-13T21:31:06.558966+00:00

### ❌ Stock Drift

- **Status:** FAIL
- **Products Checked:** 60
- **Discrepancies Found:** 15
- **Discrepancies:** [{'product_id': '2ad75718-76d6-4b91-8cb3-b4a310ca94a3', 'name': 'XL Unlimited 30 Hari', 'sku': None, 'stored_stock': 296, 'calculated_stock': 0, 'difference': 296}, {'product_id': 'e1cd6253-04e6-4382-9e26-4dda3ebcd362', 'name': 'Kabel Data Type-C', 'sku': None, 'stored_stock': 1, 'calculated_stock': 0, 'difference': 1}, {'product_id': 'PRD-AUDIT-001', 'name': 'Charger Fast 20W USB-C', 'sku': 'CHG-001', 'stored_stock': 16, 'calculated_stock': 0, 'difference': 16}, {'product_id': 'PRD-AUDIT-002', 'name': 'Charger Fast 33W Dual Port', 'sku': 'CHG-002', 'stored_stock': 13, 'calculated_stock': 0, 'difference': 13}, {'product_id': '2881765d-83ab-4f9f-bd98-22bdb9c6e7b5', 'name': 'Saldo Server XL', 'sku': None, 'stored_stock': 17000000.0, 'calculated_stock': 0, 'difference': 17000000.0}, {'product_id': '6d1fd21f-d558-4751-b74c-b73316a03a8d', 'name': 'Voucher Zero XL 10GB', 'sku': None, 'stored_stock': 40.0, 'calculated_stock': 0, 'difference': 40.0}, {'product_id': '0dab5f74-cf6e-40e6-83c0-48ef5ea32c51', 'name': 'Voucher Fisik XL 10GB 30 Hari', 'sku': None, 'stored_stock': 58.0, 'calculated_stock': 0, 'difference': 58.0}, {'product_id': 'd072cb3d-dba8-47fc-925c-f4da72b99064', 'name': 'AUDIT-Pulsa Telkomsel 50K (Updated)', 'sku': None, 'stored_stock': 44, 'calculated_stock': 0, 'difference': 44}, {'product_id': '26185e7b-efac-4745-8d8d-c1e114a863ed', 'name': 'STRESS-Saldo Server Telkomsel', 'sku': None, 'stored_stock': 3750000.0, 'calculated_stock': 0, 'difference': 3750000.0}, {'product_id': 'c62a3f9c-cc19-469e-a783-3a0c0b354bf3', 'name': 'STRESS-Voucher Zero Telkomsel 5GB', 'sku': None, 'stored_stock': 50.0, 'calculated_stock': 0, 'difference': 50.0}, {'product_id': 'c64bcb0b-6dc7-4bf8-8478-2c612706d370', 'name': 'STRESS-Voucher Fisik Telkomsel 5GB 30H', 'sku': None, 'stored_stock': 47.0, 'calculated_stock': 0, 'difference': 47.0}, {'product_id': 'baa5a5fd-0fa2-4459-9a27-d32ec1412cf9', 'name': 'Kabel Data Type-C Test v2 (Edited)', 'sku': None, 'stored_stock': 50, 'calculated_stock': 0, 'difference': 50}, {'product_id': 'b0ec8a99-5555-4c92-8639-3b4e9fa8c92d', 'name': 'Kabel Data Premium Test', 'sku': None, 'stored_stock': 77, 'calculated_stock': 0, 'difference': 77}, {'product_id': 'a42b820d-d311-4a24-81c8-4afb423af027', 'name': 'Item Test P0', 'sku': None, 'stored_stock': 94, 'calculated_stock': 0, 'difference': 94}, {'product_id': 'a009a443-2e22-4597-91a6-cfd7d763b206', 'name': 'E2E Test Product', 'sku': None, 'stored_stock': 995, 'calculated_stock': 0, 'difference': 995}]
- **Checked At:** 2026-03-13T21:31:06.594164+00:00

### ❌ Inventory Vs Gl

- **Status:** FAIL
- **Inventory Value:** 48872000.0
- **Gl Balance:** -3750000.0
- **Difference:** 52622000.0
- **Percentage Diff:** -1403.25
- **Checked At:** 2026-03-13T21:31:06.598318+00:00

### ⚠️ Cash Variance

- **Status:** WARNING
- **Period Days:** 7
- **Variance Count:** 0
- **Total Shortage:** 0
- **Total Overage:** 0
- **Net Variance:** 0
- **Pending Discrepancies:** 5
- **Recent Variances:** []
- **Checked At:** 2026-03-13T21:31:06.599432+00:00

### ✅ Backup Status

- **Status:** PASS
- **Backup Count:** 12
- **Latest Backup:** {'filename': 'api_test_20260313_203456_metadata.json', 'size_bytes': 2184, 'size_mb': 0.0, 'created_at': '2026-03-13T20:34:57.278474'}
- **Has Recent Backup:** True
- **Backup Directory:** /app/backend/backups
- **Checked At:** 2026-03-13T21:31:06.599616+00:00

### ✅ Event Queue

- **Status:** PASS
- **Period Hours:** 1
- **Total Events:** 4
- **By Status:** {'no_listeners': 4}
- **Failed Count:** 0
- **Checked At:** 2026-03-13T21:31:06.600231+00:00

### ✅ System Health

- **Status:** PASS
- **Counts:** {'active_users': 12, 'products': 63, 'posted_journals': 2075, 'sales': 0}
- **Database:** ocb_titan
- **Checked At:** 2026-03-13T21:31:06.602555+00:00

---
*Report generated at 2026-03-13T21:31:06.549101+00:00*
