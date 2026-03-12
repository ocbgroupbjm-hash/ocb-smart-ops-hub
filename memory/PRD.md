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
| 3 | Operational Control System | ✅ Complete | 100% |
| 4 | Business Intelligence | ✅ Complete | 100% |
| 5 | KPI System | ✅ Partial | 60% |
| 6 | AI Business Engine | ✅ Partial | 70% |

---

# PHASE 4 - REPORT CENTER ✅ COMPLETE

## Report Categories
| Category | Reports |
|----------|---------|
| Sales | Summary, By Product, By Customer, By Salesperson |
| Purchase | Summary, By Product |
| Inventory | Stock Status, Movement, Valuation |
| Financial | Profit & Loss, Balance Sheet |
| Receivables | AR Aging |
| Payables | AP Aging |
| Cash Flow | Summary |

## API Endpoints
- `GET /api/reports/` - List all reports
- `GET /api/reports/sales/summary` - Sales summary
- `GET /api/reports/sales/by-product` - Sales by product
- `GET /api/reports/sales/by-customer` - Sales by customer
- `GET /api/reports/sales/by-salesperson` - Sales by salesperson
- `GET /api/reports/purchase/summary` - Purchase summary
- `GET /api/reports/purchase/by-product` - Purchase by product
- `GET /api/reports/inventory/stock-status` - Stock status
- `GET /api/reports/inventory/movement` - Stock movement
- `GET /api/reports/inventory/valuation` - Inventory valuation
- `GET /api/reports/financial/profit-loss` - P&L report
- `GET /api/reports/financial/balance-sheet` - Balance sheet
- `GET /api/reports/ar/aging` - AR aging
- `GET /api/reports/ap/aging` - AP aging
- `GET /api/reports/cashflow/summary` - Cash flow summary

## Features
- Period filtering (today, week, month, quarter, year)
- Custom date range
- Export to JSON
- Interactive charts and tables
- Real-time data aggregation

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
| 40 | Approval Workflow Engine (P3) | **100%** | **100%** |
| 41 | Credit Control Engine (P3) | **100%** | **100%** |
| 42 | Stock Reorder & Warehouse (P3) | **100%** | **100%** |
| 43 | Purchase Planning & Sales Target (P3) | **95%** | **100%** |
| 44 | Commission Engine & Cash Control (P3) | **91%** | **100%** |
| 45 | Report Center (P4) | **100%** | **100%** |
| 46 | Stabilization + Commission Enhancement | **100%** | **100%** |

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
- `/app/frontend/src/pages/approval/ApprovalCenter.jsx` - Approval Workflow UI (Phase 3)

---

# PHASE 3 - APPROVAL WORKFLOW ENGINE ✅ COMPLETE

## 5 Tipe Approval
| Tipe | Deskripsi | Auto Approve Threshold |
|------|-----------|------------------------|
| Purchase Order | Approval untuk PO | < Rp 10.000.000 |
| Discount | Approval untuk diskon | < 10% |
| Void Transaction | Approval untuk pembatalan | Never (selalu butuh) |
| Price Override | Approval untuk perubahan harga | < 5% variance |
| Credit Override | Approval untuk melebihi credit limit | Never (selalu butuh) |

## Multi-Level Approval (Purchase Order Example)
| Level | Range | Approvers |
|-------|-------|-----------|
| L0 | Rp 0 - 10jt | Auto Approve |
| L1 | Rp 10jt - 50jt | purchasing_manager |
| L2 | Rp 50jt - 100jt | finance_manager, admin |
| L3 | Rp 100jt+ | owner |

## API Endpoints
- `GET /api/approval-workflow/types`
- `POST /api/approval-workflow/check`
- `POST /api/approval-workflow/request`
- `GET /api/approval-workflow/pending`
- `GET /api/approval-workflow/my-requests`
- `GET /api/approval-workflow/{id}`
- `POST /api/approval-workflow/{id}/action`
- `GET /api/approval-workflow/dashboard/summary`

## Frontend Features
- Dashboard dengan 4 summary cards
- 3 Tabs: Pending Approvals, My Requests, Approval Rules
- Detail Modal dengan approve/reject buttons
- Search & Filter functionality
- Audit trail display

---

# PHASE 3 - CUSTOMER CREDIT LIMIT CONTROL ✅ COMPLETE

## Credit Policy Configuration
| Segment | Default Limit | Max Overdue Days |
|---------|--------------|------------------|
| regular | Rp 0 | 0 |
| member | Rp 5.000.000 | 14 |
| vip | Rp 20.000.000 | 30 |
| corporate | Rp 100.000.000 | 45 |
| distributor | Rp 500.000.000 | 60 |

## Credit Status Types
| Status | Name | Can Transact |
|--------|------|--------------|
| active | Aktif | Yes |
| warning | Peringatan | Yes |
| hold | Ditahan | No |
| blocked | Diblokir | No |
| blacklist | Blacklist | No (cannot override) |

## Hard Stop Rules
1. **Credit Status Check:** Customer dalam status hold/blocked/blacklist tidak bisa transaksi kredit
2. **Credit Limit Check:** Outstanding + Transaction Amount > Credit Limit → DITOLAK
3. **Overdue Blocking:** Hari overdue > max segment + Amount > tolerance → DITOLAK

## API Endpoints
- `GET /api/credit-control/policy`
- `GET /api/credit-control/customer/{id}`
- `POST /api/credit-control/check` ← **HARD STOP ENDPOINT**
- `PUT /api/credit-control/customer/{id}/limit`
- `POST /api/credit-control/customer/{id}/hold`
- `GET /api/credit-control/dashboard`
- `GET /api/credit-control/at-risk`
- `GET /api/credit-control/audit-log`
- `POST /api/credit-control/override-request`
- `GET /api/credit-control/override-status/{id}`

## Integration Points
- **Sales Module:** Hard stop check di `sales_module.py` line 477-500
- **Approval Workflow:** Credit override request via `credit_override` approval type
- **Audit Trail:** Semua perubahan credit dicatat di `audit_logs` collection

---

# NEXT PHASE: OPERATIONAL CONTROL SYSTEM

## P3 - Phase 3 Modules
- [x] **Approval Workflow Engine** ✅ COMPLETE (March 11, 2026)
  - 5 tipe approval: Purchase Order, Discount, Void Transaction, Price Override, Credit Override
  - Multi-level approval berdasarkan threshold (L0-L3)
  - Role-based access control (Owner/Admin approve semua, Kasir tidak bisa approve)
  - Dashboard summary, Pending list, My Requests, Approval Rules
  - Audit trail untuk setiap action
- [x] **Customer Credit Limit Control** ✅ COMPLETE (March 11, 2026)
  - Credit limit per customer dengan segment-based defaults
  - Credit hold/block/blacklist status management
  - Overdue blocking (max days per segment)
  - HARD STOP di sales module - transaksi kredit ditolak jika melebihi limit
  - Approval override integration via Approval Workflow
  - Audit trail untuk semua perubahan credit
- [x] **Stock Reorder Engine** ✅ COMPLETE (March 11, 2026)
  - Min/Max stock settings per product
  - Sales velocity calculation (average daily sales)
  - Automatic reorder suggestions dengan urgency levels
  - Reorder point & safety stock calculation
  - Lead time consideration
  - Generate PO draft from suggestions
  - Low stock alerts
- [x] **Warehouse Control** ✅ COMPLETE (March 11, 2026)
  - Multi-warehouse management per branch
  - Warehouse stock tracking (per product)
  - Stock transfer between warehouses
  - Transfer approval workflow (pending → approved → completed)
  - Transfer status tracking
  - Dashboard summary
- [x] **Purchase Planning Engine** ✅ COMPLETE (March 11, 2026)
  - Forecast purchasing berdasarkan sales history
  - Supplier lead time integration
  - Rekomendasi qty pembelian & tanggal order
  - Urgency levels: critical, high, medium, low, none
  - Status workflow: draft → reviewed → approved → po_created
  - Create PO draft from approved planning items
  - Dashboard summary per status dan urgency
- [x] **Sales Target System** ✅ COMPLETE (March 11, 2026)
  - Target per Branch/Salesman/Category
  - Period types: daily, weekly, monthly, quarterly, yearly
  - Achievement tracking: actual_value, achievement_percent, gap
  - Status: on_track, behind, at_risk, achieved, exceeded, failed
  - Leaderboard dengan ranking per achievement
  - Dashboard summary dengan overall achievement
- [x] **Commission Engine** ✅ COMPLETE (March 12, 2026)
  - Komisi berdasarkan achievement target dan sales value
  - Bonus tambahan jika achievement >110% (Super Bonus)
  - Perhitungan per salesman, branch, period
  - Commission formula: Base (2%) + Achievement Bonus + Super Bonus
  - Integrasi accounting journal saat pembayaran
  - Status workflow: calculated → approved → paid
- [x] **Deposit & Cash Control Enhancement** ✅ COMPLETE (March 12, 2026)
  - Monitoring setoran kasir dengan shift management
  - Compare sales vs deposit (expected vs actual cash)
  - Deteksi selisih kas (shortage/overage) dengan tolerance Rp 1.000
  - Shift workflow: open → closing → closed/discrepancy → reviewed
  - Discrepancy resolution (explained/written_off/recovered)
  - Audit trail lengkap

---

# PHASE 3 COMPLETE ✅

Phase 3 - Operational Control System telah selesai 100%. Semua 6 modul berikut telah diimplementasikan dan ditest:
1. Approval Workflow Engine
2. Customer Credit Limit Control
3. Stock Reorder Engine
4. Warehouse Control
5. Purchase Planning Engine
6. Sales Target System
7. Commission Engine
8. Deposit & Cash Control Enhancement

---

# PHASE 3 - COMMISSION ENGINE ✅ COMPLETE

## Commission Formula
| Component | Calculation |
|-----------|-------------|
| Base Commission | Sales Value × Base Rate (2%) |
| Achievement Bonus | Base × (Achievement% - 100%) × Multiplier (if >100%) |
| Super Bonus | Sales × Super Rate (1%) (if achievement ≥110%) |
| Total | Base + Achievement Bonus + Super Bonus |

## Commission Status
| Status | Description |
|--------|-------------|
| calculated | Commission telah dihitung |
| approved | Disetujui untuk pembayaran |
| paid | Sudah dibayar (journal created) |
| cancelled | Dibatalkan |

## API Endpoints
- `GET /api/commission/policy` - Get commission policy
- `PUT /api/commission/policy` - Update policy
- `POST /api/commission/simulate` - Simulate calculation
- `POST /api/commission/calculate` - Calculate for period
- `GET /api/commission/list` - List commissions
- `GET /api/commission/dashboard/summary` - Dashboard
- `POST /api/commission/approve` - Approve commissions
- `POST /api/commission/pay` - Pay with journal creation

---

# PHASE 3 - DEPOSIT & CASH CONTROL ✅ COMPLETE

## Shift Workflow
| Status | Description |
|--------|-------------|
| open | Shift aktif |
| closing | Sedang tutup |
| closed | Sudah ditutup tanpa masalah |
| discrepancy | Ada selisih kas |
| reviewed | Sudah direview supervisor |

## Discrepancy Types
| Type | Description |
|------|-------------|
| none | Kas sesuai (within tolerance) |
| shortage | Kas kurang dari seharusnya |
| overage | Kas lebih dari seharusnya |

## Expected Cash Calculation
```
Expected Cash = Initial Cash + Cash Sales + Cash In - Cash Out
```

## API Endpoints
- `POST /api/cash-control/shift/open` - Open shift
- `GET /api/cash-control/shift/current` - Get current shift
- `POST /api/cash-control/shift/{id}/close` - Close shift
- `GET /api/cash-control/shifts` - List shifts
- `GET /api/cash-control/dashboard/summary` - Dashboard
- `GET /api/cash-control/discrepancies` - List discrepancies
- `POST /api/cash-control/discrepancy/{id}/resolve` - Resolve
- `POST /api/cash-control/deposit` - Record deposit

---

# PHASE 3 - PURCHASE PLANNING ENGINE ✅ COMPLETE

## Planning Workflow
| Status | Description | Transitions |
|--------|-------------|-------------|
| draft | Initial state | → reviewed, cancelled |
| reviewed | Manager reviewed | → approved, draft, cancelled |
| approved | Ready for PO | → po_created, reviewed, cancelled |
| po_created | PO already generated | Final state |
| cancelled | Cancelled | Final state |

## Urgency Levels
| Level | Condition |
|-------|-----------|
| critical | Stock = 0 OR stock ≤ 50% min_stock |
| high | Stock ≤ min_stock |
| medium | Stock ≤ reorder_point |
| low/none | Stock > reorder_point |

## API Endpoints
- `POST /api/purchase-planning/generate` - Generate planning recommendations
- `GET /api/purchase-planning/list` - List with filters
- `GET /api/purchase-planning/dashboard/summary` - Dashboard summary
- `GET /api/purchase-planning/{id}` - Get detail
- `POST /api/purchase-planning/{id}/status` - Update status
- `POST /api/purchase-planning/create-po` - Create PO from approved
- `DELETE /api/purchase-planning/{id}` - Delete draft

---

# PHASE 3 - SALES TARGET SYSTEM ✅ COMPLETE

## Target Types
| Type | Description |
|------|-------------|
| branch | Target per cabang |
| salesman | Target per sales |
| category | Target per kategori produk |

## Target Status (Auto-calculated)
| Status | Condition |
|--------|-----------|
| exceeded | Achievement ≥ 110% |
| achieved | Achievement ≥ 100% (period ended) |
| on_track | Achievement ≥ 80% |
| behind | Achievement 60-80% |
| at_risk | Achievement < 60% |
| failed | Period ended, achievement < 100% |

## API Endpoints
- `POST /api/sales-target` - Create target
- `GET /api/sales-target/list` - List with filters
- `GET /api/sales-target/dashboard/summary` - Dashboard
- `GET /api/sales-target/leaderboard` - Salesman ranking
- `GET /api/sales-target/{id}` - Get detail (enriched)
- `PUT /api/sales-target/{id}` - Update target
- `DELETE /api/sales-target/{id}` - Delete target

---

# CREDENTIALS

| Role | Email | Password |
|------|-------|----------|
| Owner | ocbgroupbjm@gmail.com | admin123 |
| Kasir | kasir_test@ocb.com | password123 |
| Supervisor | supervisor_test@ocb.com | password123 |
| Viewer | viewer_test@ocb.com | password123 |

---

**Version:** 31.0 (Stabilization + Commission Engine Enhancement)
**Last Updated:** March 12, 2026
**Architecture:** SSOT, Non-Destructive, Additive
**Governance:** OCB TITAN AI MASTER LAW
