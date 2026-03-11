# OCB TITAN ERP - ENTERPRISE RETAIL OPERATING SYSTEM
## Product Requirements Document (PRD) v24.0

---

# OVERVIEW

OCB TITAN ERP adalah sistem ERP retail enterprise untuk bisnis multi-cabang dengan standar global setara:
- **SAP**
- **Oracle NetSuite**
- **Microsoft Dynamics**
- **iPOS Ultimate**

---

# LATEST UPDATE: March 11, 2026

## PHASE 2 - FINANCIAL CONTROL SYSTEM ✅ COMPLETE

### 1. Multi Tax Engine ✅
**6 Jenis Pajak Indonesia:**
| Kode | Nama | Tarif Default | Kategori |
|------|------|---------------|----------|
| PPN | Pajak Pertambahan Nilai | 11% | value_added_tax |
| PPNBM | Pajak Penjualan Barang Mewah | 10% | luxury_tax |
| PPH21 | PPh Pasal 21 | 5-35% Progressive | income_tax |
| PPH22 | PPh Pasal 22 | 1.5% | income_tax |
| PPH23 | PPh Pasal 23 | 2% | income_tax |
| PPH4_2 | PPh Final UMKM | 0.5% | final_tax |

**Fitur:**
- Kalkulator PPN (inclusive/exclusive)
- Kalkulator PPh 21 dengan tarif progresif
- PTKP 2024: TK/0 hingga K/I/3
- Auto account mapping untuk jurnal pajak

**API Endpoints:**
- `GET /api/tax-engine/tax-types`
- `POST /api/tax-engine/calculate`
- `POST /api/tax-engine/calculate-pph21`
- `GET /api/tax-engine/tax-accounts`

### 2. Financial Consistency Checker ✅
**6 Jenis Pengecekan:**
| Check Type | Severity | Keterangan |
|------------|----------|------------|
| journal_balance | critical | Setiap jurnal debit = kredit |
| trial_balance | critical | Total debit = total kredit |
| stock_movement | critical | Stok sesuai pergerakan |
| ar_journal | high | Piutang sesuai jurnal |
| ap_journal | high | Hutang sesuai jurnal |
| cash_balance | high | Saldo kas konsisten |

**Fitur:**
- Full consistency report
- Individual check per type
- Auto fix suggestions
- Branch filter support

**API Endpoints:**
- `GET /api/consistency-checker/check-types`
- `GET /api/consistency-checker/check/{type}`
- `GET /api/consistency-checker/full-report`
- `GET /api/consistency-checker/fix-suggestions/{type}`

### 3. Auto Journal Engine ✅
**21 Template Jurnal Standar:**

| Kategori | Templates |
|----------|-----------|
| SALES | sales_cash, sales_credit, sales_cogs, sales_return |
| PURCHASE | purchase_cash, purchase_credit, purchase_return |
| AR/AP | ar_payment_cash, ar_payment_bank, ap_payment_cash, ap_payment_bank |
| INVENTORY | stock_adjustment_in, stock_adjustment_out, stock_transfer |
| CASH/BANK | cash_receipt, cash_disbursement, bank_transfer_in, bank_transfer_out |
| PAYROLL | payroll_salary |
| DEPOSIT | deposit_cashier, deposit_confirm |

**Fitur:**
- Preview jurnal sebelum posting
- Integrasi Account Derivation Engine
- Balanced validation otomatis
- Template-based journal creation

**API Endpoints:**
- `GET /api/auto-journal/templates`
- `GET /api/auto-journal/templates/{code}`
- `GET /api/auto-journal/preview/{template}`
- `POST /api/auto-journal/generate`

### 4. Accounting Period Closing Enhancement ✅
**Role-based Access Control:**
- **CLOSE:** Owner, Admin, Finance Manager
- **REOPEN:** Owner only
- **LOCK:** Owner only

**Validations:**
- No unposted journals
- Balanced journal check
- Audit trail for all actions

### 5. UI - Financial Control Page ✅
**Location:** Akuntansi → Multi Tax Engine / Consistency Checker

**3 Tabs:**
1. **Multi Tax Engine** - Tax calculator, PPh 21 calculator, tax types table
2. **Consistency Checker** - Run checks, view report, status indicators
3. **Auto Journal** - Template selector, preview, balanced badge

---

# PHASE COMPLETION STATUS

| Phase | Name | Status | Completion |
|-------|------|--------|------------|
| 1 | Core Transaction Engine | ✅ Complete | 100% |
| 2 | Financial Control System | ✅ Complete | 100% |
| 3 | Operational Control System | ⏳ Pending | 0% |
| 4 | Business Intelligence | ⏳ Pending | 0% |
| 5 | KPI System | ✅ Partial | 60% |
| 6 | AI Business Engine | ✅ Partial | 70% |

---

# PHASE 2 MODULES DETAIL

## Fiscal Period System ✅
- Status: OPEN, CLOSED, LOCKED
- Enforcement di semua modul transaksi
- Role-based close/reopen/lock

## Multi Currency System ✅
- Base currency: IDR
- Supported: USD, EUR, SGD, MYR, CNY, JPY
- Exchange rate CRUD
- Currency converter

## Account Derivation Engine ✅
- Priority: Branch > Warehouse > Category > Payment > Tax > Global > Default
- Terintegrasi ke semua modul transaksi
- iPOS-style account codes (X-XXXX)

## Multi Tax Engine ✅
- 6 jenis pajak Indonesia
- PPh 21 progressive rate calculator
- Account mapping per tax type

## Financial Consistency Checker ✅
- 6 jenis validasi
- Full report generator
- Fix suggestions

## Auto Journal Engine ✅
- 21 template standar
- Preview before posting
- Account derivation integration

---

# TEST RESULTS

| Iteration | Module | Backend | Frontend |
|-----------|--------|---------|----------|
| 34 | Sales Module | 100% | 100% |
| 35 | Master Data | 94% | 100% |
| 36 | Account Settings UI | 100% | 100% |
| 37 | Account Derivation | 94% | 100% |
| 38 | ERP Hardening Phase 1 | 96% | 100% |
| 39 | Financial Control Phase 2 | **100%** | **100%** |

---

# FILES CREATED IN THIS SESSION

## Backend
- `/app/backend/routes/erp_hardening.py` - Fiscal Period & Multi-Currency
- `/app/backend/routes/tax_engine.py` - Multi Tax Engine
- `/app/backend/routes/consistency_checker.py` - Financial Consistency Checker
- `/app/backend/routes/auto_journal_engine.py` - Auto Journal Engine

## Frontend
- `/app/frontend/src/pages/ERPHardening.jsx` - Fiscal & Currency UI
- `/app/frontend/src/pages/FinancialControl.jsx` - Tax, Consistency, Journal UI

---

# NEXT PHASE: OPERATIONAL CONTROL SYSTEM

## P3 - Phase 3 Modules (Not Started)
- [ ] Approval Workflow Engine
- [ ] Branch Management Enhancement
- [ ] Warehouse Control
- [ ] Stock Reorder Engine
- [ ] Supplier Performance Analysis
- [ ] Customer Credit Limit Control
- [ ] Purchase Planning Engine
- [ ] Sales Target System
- [ ] Commission Engine Enhancement
- [ ] Deposit & Cash Control Enhancement

---

# CREDENTIALS

| Role | Email | Password |
|------|-------|----------|
| Owner | ocbgroupbjm@gmail.com | admin123 |
| Kasir | kasir_test@ocb.com | password123 |
| Supervisor | supervisor_test@ocb.com | password123 |
| Viewer | viewer_test@ocb.com | password123 |

---

**Version:** 24.0 (Phase 2 Financial Control Complete)
**Last Updated:** March 11, 2026
**Architecture:** SSOT, Non-Destructive, Additive
**Governance:** OCB TITAN AI MASTER LAW
