# OCB TITAN ERP - E2E BUSINESS TEST REPORT

**Validation ID:** VAL-20260313_210758
**Timestamp:** 2026-03-13T21:07:58.456882+00:00
**Database:** ocb_titan

## Summary

- **Total Tests:** 13
- **Passed:** 13
- **Failed:** 0
- **Pass Rate:** 100.0%
- **Status:** PASS

## Test Results

| Category | Test | Status | Details |
|----------|------|--------|--------|
| Accounting | Sales → Journal Entry | ✅ PASS | {'sales_checked': 0, 'all_have_journals': True}... |
| Accounting | Purchase → Journal Entry | ✅ PASS | {'purchases_checked': 1}... |
| Accounting | Returns Accounting | ✅ PASS | {'sales_returns': 6, 'purchase_returns': 5}... |
| Accounting | Adjustment Accounting | ✅ PASS | {'adjustments_count': 12}... |
| Accounting | Payroll Accounting | ✅ PASS | {'payroll_records': 0}... |
| Accounting | Cash Variance → Journal Entry | ✅ PASS | {'discrepancy_shifts': 6, 'variance_journals': 0}... |
| Accounting | Trial Balance Balanced | ✅ PASS | {'debit': 74689867.5, 'credit': 74689867.5, 'diffe... |
| Inventory | Stock Opname Records | ✅ PASS | {'opname_count': 12}... |
| Inventory | Stock Transfer | ✅ PASS | {'transfers': 3, 'transfer_movements': 4}... |
| Inventory | Purchase Receive → Stock IN | ✅ PASS | {'receive_movements': 5}... |
| Inventory | Sales → Stock OUT | ✅ PASS | {'out_movements': 23}... |
| Inventory | SSOT Integrity | ✅ PASS | {'products_checked': 10, 'discrepancies': 0}... |
| Multi-Tenant | Tenant Data Isolation | ✅ PASS | {'tenant_a': 'ocb_titan', 'tenant_b': 'ocb_unit_4'... |

## Evidence Files Generated

| File | Location |
|------|----------|
| journal_entries.json | /app/backend/scripts/audit_output/ |
| stock_movements.json | /app/backend/scripts/audit_output/ |
| stock_balance_view.json | /app/backend/scripts/audit_output/ |
| audit_logs.json | /app/backend/scripts/audit_output/ |
| multi_tenant_evidence.json | /app/backend/scripts/audit_output/ |
