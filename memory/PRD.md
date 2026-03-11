# OCB TITAN ERP - ENTERPRISE RETAIL OPERATING SYSTEM
## Product Requirements Document (PRD) v22.0

---

# OVERVIEW

OCB TITAN ERP adalah sistem ERP retail enterprise untuk bisnis multi-cabang dengan fitur lengkap:
- **Setting Akun ERP iPOS Style** dengan Account Derivation Engine - FULLY INTEGRATED!
- **Master Data iPOS Style** dengan 21 menu lengkap
- **POS / Penjualan** dengan multi-mode pricing + auto AR
- **Sales Module iPOS Style** dengan full integration
- **Pembelian Enterprise** dengan full lifecycle (PO→Receive→AP→Payment→Journal)
- **Modul Pembelian iPos Style** dengan form lengkap
- **Owner Dashboard** dengan KPI bisnis real-time
- **Finance Dashboard** dengan ringkasan keuangan lengkap
- **CFO Dashboard** dengan analisis keuangan executive
- **Inventory / Stok** dengan movement tracking
- **Setoran Harian** dengan security ketat
- **Hutang Piutang** (AR/AP) dengan aging + auto-journal
- **Akuntansi** dengan auto-journal + financial reports
- **Approval Engine** untuk otorisasi + approval center UI
- **RBAC** dengan FAIL-SAFE enforcement (Backend validation)
- **Audit Trail** untuk semua aktivitas sensitif
- **HR & Payroll** dengan tunjangan dan bonus tracking
- **18 Modul AI/KPI/CRM** yang terintegrasi dengan data ERP (VERIFIED!)

---

# LATEST UPDATE: March 11, 2026 - ACCOUNT DERIVATION ENGINE FULL INTEGRATION

## Account Derivation Engine - FULLY INTEGRATED TO ALL MODULES ✅

### Integration Status
| Module | File | Integration Status |
|--------|------|-------------------|
| Purchase | purchase.py | ✅ `derive_purchase_account()` |
| POS | pos.py | ✅ `derive_pos_account()` |
| Sales | sales_module.py | ✅ `derive_account()` |
| AP System | ap_system.py | ✅ `derive_ap_account()` |
| AR System | ar_system.py | ✅ `derive_ar_account()` |
| Accounting | accounting_engine.py | ✅ `derive_accounting_account()` |
| Deposit | deposit_system.py | ✅ `derive_deposit_account()` |

### Hard-coded Accounts Replaced
| Old Code | New iPOS Code | Account Name |
|----------|---------------|--------------|
| 1301 | 1-1400 | Persediaan Barang |
| 2101 | 2-1100 | Hutang Dagang |
| 1201 | 1-1300 | Piutang Usaha |
| 4101 | 4-1000 | Pendapatan Penjualan |
| 1101 | 1-1100 | Kas |
| 1102 | 1-1200 | Bank |
| 1104 | 1-1100 | Kas Cabang |
| 6201 | 5-9100 | Selisih Persediaan |
| 4201 | 4-9000 | Pendapatan Pembulatan |

### Account Derivation Priority Order
```
Priority (Highest to Lowest):
1. Branch Mapping     → specific to branch
2. Warehouse Mapping  → specific to warehouse  
3. Category Mapping   → specific to product category
4. Payment Mapping    → specific to payment method
5. Tax Mapping        → specific to tax type
6. Global Setting     → from account_settings table
7. Default Fallback   → hard-coded DEFAULT_*_ACCOUNTS
```

### Test Results (Iteration 37)
```
BACKEND: 94% - 16/17 tests passed (1 skipped due to no stock)
FRONTEND: 100% - All UI elements working

Verified:
✅ Purchase Module - derive_purchase_account() working
✅ POS Module - derive_pos_account() working
✅ Sales Module - derive_account() working
✅ Journal entries use iPOS-style X-XXXX codes
✅ Credit sale creates AR and journal with derived accounts
✅ Receive PO creates AP and journal with derived accounts
✅ Setting Akun ERP page with 12 tabs working
```

---

# PREVIOUS UPDATE: March 11, 2026 - SETTING AKUN ERP iPOS STYLE

## Account Settings Module - IMPLEMENTED & TESTED ✅

### Menu Location
```
Master Data
   └ Setting Akun ERP
```

### 12 Tabs (iPOS Structure)
| Tab | Purpose | Account Keys |
|-----|---------|--------------|
| Data Item | Akun inventory & HPP | hpp, pendapatan_jual, persediaan_barang, biaya_overhead |
| Pembelian | Akun purchase & AP | potongan_pembelian, ppn_masukan, hutang_dagang, uang_muka_po |
| Penjualan 1 | Akun sales & AR | potongan_penjualan, ppn_keluaran, pembayaran_tunai/debit/kredit |
| Penjualan 2 | Akun retur & donasi | retur_potongan, retur_ppn, donasi |
| Konsinyasi | Akun konsinyasi in/out | hutang_konsinyasi, piutang_konsinyasi |
| Hutang Piutang | Akun settlement | potongan_hutang/piutang, laba/rugi_selisih_kurs |
| Lain-lain | Akun modal & laba | prive, laba_ditahan, laba_tahun_berjalan |
| Cabang | Override per branch | kas, bank, pendapatan per cabang |
| Gudang | Override per warehouse | persediaan per gudang |
| Kategori | Override per category | pendapatan, hpp per kategori |
| Payment Method | Override per payment | kas, bank per metode bayar |
| Pajak | Override per tax type | ppn_masukan, ppn_keluaran per jenis pajak |

### API Endpoints
| Endpoint | Method | Purpose |
|----------|--------|---------|
| /api/account-settings/ | GET | List all settings by tab |
| /api/account-settings/by-tab/{tab} | GET | Get settings for specific tab |
| /api/account-settings/ | POST | Create/update account setting |
| /api/account-settings/initialize-defaults | POST | Bulk initialize defaults |
| /api/account-settings/derive-account | GET | Account Derivation Engine |
| /api/account-settings/chart-of-accounts | GET | COA for dropdown |
| /api/account-settings/branch-mapping | GET/POST | Branch account mapping |
| /api/account-settings/warehouse-mapping | GET/POST | Warehouse mapping |
| /api/account-settings/category-mapping | GET/POST | Category mapping |
| /api/account-settings/payment-mapping | GET/POST | Payment method mapping |
| /api/account-settings/tax-mapping | GET/POST | Tax type mapping |
| /api/account-settings/fiscal-periods | GET/POST | Fiscal period system |

---

# MODULES IMPLEMENTED

## 1. Sales Module iPOS Style ✅
- Sales Orders (Pesanan Jual)
- Sales Invoices (Penjualan) with auto stock & journal
- Sales Returns (Retur) with stock return & AR deduct
- Price History, Trade-in, Points, Commissions
- Tax Export (CSV/XML)

## 2. Purchase Module Enterprise ✅
- Purchase Orders with lifecycle
- Receive with auto AP & journal
- Payments, Returns, Price History

## 3. Master Data iPOS Style ✅
- 21 menu items per iPOS specification
- All CRUD operations working

## 4. Account Settings (Setting Akun ERP) ✅
- 12 configuration tabs
- Account Derivation Engine
- Branch/Warehouse/Category/Payment/Tax mapping

## 5. AI/KPI/CRM Modules ✅
- 18 modules verified working
- Owner/Finance/CFO Dashboards
- War Room, Command Center
- AI Business, AI Sales, AI Performance
- CRM AI, KPI Performance

---

# DATABASE COLLECTIONS

## Account Settings
- `account_settings` - Global account settings
- `account_mapping_branch` - Per-branch overrides
- `account_mapping_warehouse` - Per-warehouse overrides
- `account_mapping_category` - Per-category overrides
- `account_mapping_payment` - Per-payment method overrides
- `account_mapping_tax` - Per-tax type overrides
- `fiscal_periods` - Fiscal period management

## Transaction Modules
- `purchase_orders` - PO header + items
- `accounts_payable` - AP records
- `accounts_receivable` - AR records
- `journal_entries` - Journal headers
- `journal_entry_lines` - Debit/Credit lines
- `transactions` - POS transactions
- `sales_invoices` - Sales invoices
- `sales_orders` - Sales orders
- `sales_returns` - Sales returns

---

# FILES REFERENCE

## Backend Routes with Account Derivation
- `/app/backend/routes/account_settings.py` - Main Account Derivation Engine
- `/app/backend/routes/purchase.py` - Purchase with `derive_purchase_account()`
- `/app/backend/routes/pos.py` - POS with `derive_pos_account()`
- `/app/backend/routes/sales_module.py` - Sales with `derive_account()`
- `/app/backend/routes/ap_system.py` - AP with `derive_ap_account()`
- `/app/backend/routes/ar_system.py` - AR with `derive_ar_account()`
- `/app/backend/routes/accounting_engine.py` - Accounting with `derive_accounting_account()`
- `/app/backend/routes/deposit_system.py` - Deposit with `derive_deposit_account()`

## Frontend
- `/app/frontend/src/pages/master/SettingAkunERP.jsx` - Account Settings UI

---

# REMAINING TASKS

## P1 - ERP Hardening Phase 1
- [ ] Fiscal Period System - Status (OPEN/CLOSED/LOCKED) enforcement
- [ ] Multi-Currency System - currency_code, exchange_rate, Laba/Rugi Selisih Kurs

## P2 - Purchase Module iPOS Style
- [ ] Overhaul Purchase UI to match iPOS specification
- [ ] Add PO Approval Workflow

## P3 - Future Enhancements
- [ ] Multi-Tax Engine
- [ ] Auto Reversal Engine
- [ ] Fraud Detection Engine
- [ ] Audit Trail UI
- [ ] Excel Import for Purchases
- [ ] Konsinyasi Module
- [ ] Kas/Bank Module
- [ ] Laporan (Reports) Module

---

# TEST RESULTS

| Iteration | Module | Result |
|-----------|--------|--------|
| 34 | Sales Module | 100% PASS |
| 35 | Master Data | 94% PASS |
| 36 | Account Settings UI | 100% PASS |
| 37 | Account Derivation Integration | 94% PASS (16/17) |

---

# CREDENTIALS

| Role | Email | Password |
|------|-------|----------|
| Owner | ocbgroupbjm@gmail.com | admin123 |
| Kasir | kasir_test@ocb.com | password123 |
| Supervisor | supervisor_test@ocb.com | password123 |
| Viewer | viewer_test@ocb.com | password123 |

---

**Version:** 22.0 (Account Derivation Full Integration)
**Last Updated:** March 11, 2026
**Architecture:** SSOT, Non-Destructive, Additive
