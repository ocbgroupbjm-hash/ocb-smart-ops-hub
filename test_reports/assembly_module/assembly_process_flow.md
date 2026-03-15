# ASSEMBLY PROCESS FLOW

## Report Details
- **Date:** 2026-03-15 17:45 UTC
- **Tenant:** ocb_titan
- **Test Status:** PASS

---

## Use Case Tested

**Input Components:**
- Saldo XL (cost: Rp 5,000/unit) x 10 = Rp 50,000
- Voucher Zero (cost: Rp 1,000/unit) x 10 = Rp 10,000

**Output Product:**
- Voucher XL 3GB 1H x 10 = Rp 60,000 (total component cost)

---

## Process Flow

```
[Formula/BOM]
     |
     v
[Check Stock] --> [Insufficient] --> [Error]
     |
     v (Sufficient)
[Create Stock Movements]
     |
     +-- assembly_out: Component 1 (-qty)
     +-- assembly_out: Component 2 (-qty)
     +-- assembly_in: Finished Product (+qty)
     |
     v
[Create Journal Entry]
     |
     +-- Debit: Inventory - Finished Product
     +-- Credit: Inventory - Component 1
     +-- Credit: Inventory - Component 2
     |
     v
[Record Assembly Transaction]
     |
     v
[SUCCESS]
```

---

## Accounting Entry Structure

| Account | Debit | Credit |
|---------|-------|--------|
| Persediaan - Voucher XL 3GB 1H | Rp 60,000 | - |
| Persediaan - Saldo XL | - | Rp 50,000 |
| Persediaan - Voucher Zero | - | Rp 10,000 |
| **TOTAL** | **Rp 60,000** | **Rp 60,000** |

✅ **BALANCED**

---

## Inventory Impact

| Product | Before | Change | After |
|---------|--------|--------|-------|
| Saldo XL | 100 | -10 | 90 |
| Voucher Zero | 100 | -10 | 90 |
| Voucher XL 3GB 1H | 0 | +10 | 10 |

---

## System Integrity

| Check | Status |
|-------|--------|
| Stock calculated from stock_movements (SSOT) | ✅ PASS |
| Journal entry balanced | ✅ PASS |
| Trial Balance balanced | ✅ PASS |
| Audit trail created | ✅ PASS |
| Tenant isolation enforced | ✅ PASS |

---

**Report Generated:** 2026-03-15T17:45:29.088110+00:00
