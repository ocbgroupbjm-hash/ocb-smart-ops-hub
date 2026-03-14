# AR GL MAPPING VALIDATION
## PRIORITAS 1: Piutang Usaha di Buku Besar

**Date:** 2026-03-14
**Tenant:** ocb_titan
**Status:** VALIDATED ✅

---

## 1. COA Mapping Verification

### Akun Piutang yang Aktif:
| Code | Name | Type | Classification |
|------|------|------|----------------|
| 1-1300 | Piutang Usaha | Asset | Current Asset |
| 1201 | Piutang Dagang | Asset | Current Asset |

### Status:
- ✅ Akun ada di COA tenant
- ✅ Akun aktif
- ✅ Diklasifikasikan sebagai Aset Lancar
- ✅ Dipakai pada journal template AR

---

## 2. AR Journal Posting Verification

### Penjualan Kredit Journal:
```
Debit:  1-1300 Piutang Usaha
Credit: 4-1XXX Penjualan
```

### AR Payment Journal:
```
Debit:  1-1XXX Kas/Bank
Credit: 1-1300 Piutang Usaha
```

### Status:
- ✅ Sales credit creates correct journal
- ✅ AR payment creates correct journal
- ✅ Journal entries stored in `journal_entries` collection

---

## 3. Ledger Aggregation Verification

### Query Analysis:
- ✅ `get_all_journal_entries_with_lines()` fetches from `journal_entries`
- ✅ Filters by `tenant_id` (implicit via session)
- ✅ Groups by `account_code`
- ✅ AR accounts NOT excluded

### Frontend Fix Applied:
- Changed from deprecated `/api/accounting/ledger` (uses old `journals` collection)
- Now uses `/api/accounting/financial/general-ledger` (uses `journal_entries`)

---

## 4. Report Consistency

### Trial Balance:
- ✅ `1-1300 Piutang Usaha: Debit Rp 9,990,450`

### Balance Sheet:
- ✅ `1-1300 Piutang Usaha: Balance Rp 9,990,450`

### General Ledger:
- ✅ `1-1300` has 20 entries
- ✅ Total Debit: Rp 14,192,950
- ✅ Total Credit: Rp 4,202,500

---

## Root Cause & Fix

### Root Cause:
Frontend General Ledger was using deprecated endpoint `/api/accounting/ledger` which reads from old `journals` collection instead of `journal_entries`.

### Fix Applied:
Updated `GeneralLedger.jsx` to:
1. Use `/api/accounting/financial/trial-balance` for account list
2. Use `/api/accounting/financial/general-ledger?account_code={code}` for entry details
3. Load entries on-demand when expanding account

---

**PIUTANG USAHA NOW VISIBLE IN BUKU BESAR ✅**
