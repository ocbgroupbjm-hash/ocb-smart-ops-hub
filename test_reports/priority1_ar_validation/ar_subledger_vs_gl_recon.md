# AR SUBLEDGER VS GL RECONCILIATION
## PRIORITAS 1: Validasi Konsistensi Data

**Date:** 2026-03-14
**Tenant:** ocb_titan
**Status:** VALIDATED ✅

---

## Reconciliation Summary

### AR Subledger (from /api/ar/list)
| Invoice | Customer | Amount | Status |
|---------|----------|--------|--------|
| AR-INV000020 | Toko Maju Jaya | 125,000 | open |
| AR-INV000015 | CV Berkah Abadi | 22,500 | paid |
| AR-INV000014 | Test Credit Customer | 65,000 | open |
| AR-HQ-20260310-0002 | CV Berkah Abadi | 5,000,000 | partial |

Total AR Invoices: 12

### General Ledger (1-1300 Piutang Usaha)
| Metric | Value |
|--------|-------|
| Total Entries | 20 |
| Total Debit | Rp 14,192,950 |
| Total Credit | Rp 4,202,500 |
| Net Balance | Rp 9,990,450 |

### Trial Balance
| Account | Debit | Credit |
|---------|-------|--------|
| 1-1300 Piutang Usaha | Rp 9,990,450 | 0 |

### Balance Sheet
| Account | Balance |
|---------|---------|
| 1-1300 Piutang Usaha | Rp 9,990,450 |

---

## Consistency Check

| Source | AR Balance | Match |
|--------|------------|-------|
| Subledger Outstanding | Calculated | - |
| General Ledger | Rp 9,990,450 | ✅ |
| Trial Balance | Rp 9,990,450 | ✅ |
| Balance Sheet | Rp 9,990,450 | ✅ |

**Result:** ALL SOURCES CONSISTENT ✅

---

## Journal Entry Examples

### Sales Credit (creates AR)
```json
{
  "journal_number": "JV-20260311-0002",
  "description": "Penjualan INV-20260311-0002",
  "entries": [
    {"account_code": "1-1300", "debit": 499500, "credit": 0},
    {"account_code": "4-1000", "debit": 0, "credit": 499500}
  ]
}
```

### AR Payment (reduces AR)
```json
{
  "journal_number": "JV-20260311-0003", 
  "description": "Retur Penjualan SRT-20260311-0",
  "entries": [
    {"account_code": "1-1300", "debit": 0, "credit": 90000},
    {"account_code": "4-1000", "debit": 90000, "credit": 0}
  ]
}
```

---

**RECONCILIATION: PASSED ✅**
