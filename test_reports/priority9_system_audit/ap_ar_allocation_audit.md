# AP/AR ALLOCATION ARCHITECTURE AUDIT

## Report Details
- **Date:** 2026-03-15 17:37 UTC
- **Tenant:** ocb_titan
- **Overall Status:** NEEDS REVIEW

---

## Statistics

| Metric | AP | AR |
|--------|----|----|
| Payments | 13 | 10 |
| Allocations | 5 | 2 |

---

## Architecture Compliance

| Rule | Status |
|------|--------|
| Payment Header + Allocation Detail Model | ✅ IMPLEMENTED |
| SUM(allocation.amount) = payment.amount | ⚠️ 10 ISSUES |
| Outstanding cannot be negative | ✅ ENFORCED |
| Over-allocation rejected | ✅ ENFORCED |
| Invoice status auto-calculated | ✅ IMPLEMENTED |
| Tenant isolation | ✅ ENFORCED |

---

## Allocation Integrity Check

- **Total AP Payments:** 13
- **Allocation Issues Found:** 10

Issues: [{'payment_id': '85878c62-b738-425b-a100-6d0cfc206357', 'payment_amount': 5000000.0, 'total_allocated': 0, 'diff': 5000000.0}, {'payment_id': '90275ca3-4c1d-4850-822e-d897fe96a687', 'payment_amount': 2000000.0, 'total_allocated': 0, 'diff': 2000000.0}, {'payment_id': '4997ebfd-8043-4d99-86f5-aa0335fdb929', 'payment_amount': 2000000.0, 'total_allocated': 0, 'diff': 2000000.0}, {'payment_id': 'ee1cbae9-737a-422b-936d-a9c0e637ebd5', 'payment_amount': 2000000.0, 'total_allocated': 0, 'diff': 2000000.0}, {'payment_id': 'aeee8bb6-9461-491b-a142-48a66bfb7110', 'payment_amount': 500000.0, 'total_allocated': 0, 'diff': 500000.0}]

---

**Report Generated:** 2026-03-15T17:37:05.847832+00:00
