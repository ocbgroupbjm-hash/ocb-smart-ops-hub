# OCB TITAN ERP - ENTERPRISE RETAIL OPERATING SYSTEM
## Product Requirements Document (PRD) v13.0

---

# OVERVIEW

OCB TITAN ERP adalah sistem ERP retail enterprise untuk bisnis multi-cabang dengan fitur lengkap:
- **POS / Penjualan** dengan multi-mode pricing
- **Pembelian** dengan AP integration
- **Inventory / Stok** dengan movement tracking
- **Setoran Harian** dengan security ketat
- **Hutang Piutang** (AR/AP) dengan aging + frontend UI
- **Akuntansi** dengan auto-journal + financial reports
- **Approval Engine** untuk otorisasi + approval center UI
- **RBAC** dengan role hierarchy
- **Audit Trail** untuk semua aktivitas

---

# LATEST UPDATE: March 10, 2026

## FRONTEND MODULES COMPLETED

### ✅ NEW FRONTEND PAGES CREATED

#### 1. Accounts Receivable (AR) Page - `/accounting/receivables`
- **File**: `/app/frontend/src/pages/accounting/AccountsReceivable.jsx`
- **Components**:
  - ARDetailModal - `/app/frontend/src/components/accounting/ARDetailModal.jsx`
  - ARPaymentModal - `/app/frontend/src/components/accounting/ARPaymentModal.jsx`
- **Features**:
  - Summary cards (Total Piutang, Jatuh Tempo, Due 7 Days, Outstanding)
  - Aging report visual (Current, 1-30, 31-60, 61-90, >90 days)
  - Customer filter, status filter, search
  - View detail modal with payment history
  - Record payment modal with auto-journal

#### 2. Accounts Payable (AP) Page - `/accounting/payables`
- **File**: `/app/frontend/src/pages/accounting/AccountsPayable.jsx`
- **Components**:
  - APDetailModal - `/app/frontend/src/components/accounting/APDetailModal.jsx`
  - APPaymentModal - `/app/frontend/src/components/accounting/APPaymentModal.jsx`
- **Features**:
  - Summary cards (Total Hutang, Jatuh Tempo, Due 7 Days, Outstanding)
  - Aging report visual
  - Supplier filter, status filter, search
  - View detail modal with payment history
  - Record payment modal with auto-journal

#### 3. Approval Center - `/approval-center`
- **File**: `/app/frontend/src/pages/approval/ApprovalCenter.jsx`
- **Features**:
  - Summary cards (My Pending, Total Pending, Approved, Rejected)
  - Tab navigation (Pending Approval, All Requests, Approval Rules)
  - Approve/Reject actions with notes
  - Rule management view

#### 4. Financial Reports - `/accounting/financial-reports`
- **File**: `/app/frontend/src/pages/accounting/FinancialReports.jsx`
- **Features**:
  - Trial Balance with balanced/not balanced indicator
  - Neraca (Balance Sheet) with assets, liabilities, equity sections
  - Laba Rugi (Income Statement) with net profit/loss
  - Date filters and Generate button
  - Export to CSV

---

## SYSTEM ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI INSIGHT LAYER                             │
├─────────────────────────────────────────────────────────────────┤
│                    REPORTING LAYER                              │
│  GL │ Trial Balance │ Neraca │ Laba Rugi │ Dashboards          │
├─────────────────────────────────────────────────────────────────┤
│                    AUDIT & SECURITY LAYER                       │
│  Audit Logs │ RBAC │ Activity Tracking │ IP Logging            │
├─────────────────────────────────────────────────────────────────┤
│                    APPROVAL LAYER                               │
│  Multi-level Workflow │ Condition Rules │ Role-based           │
├─────────────────────────────────────────────────────────────────┤
│                    OPERATIONAL CONTROL                          │
│  Setoran Harian │ Reconciliation │ Shift Management            │
├─────────────────────────────────────────────────────────────────┤
│                    ACCOUNTING ENGINE                            │
│  Journal Entries │ Account Mapping │ Auto-Journal              │
├─────────────────────────────────────────────────────────────────┤
│                    INVENTORY CONTROL                            │
│  Stock Movements │ Valuations │ Adjustments │ Transfers        │
├─────────────────────────────────────────────────────────────────┤
│                    TRANSACTION LAYER                            │
│  Sales/POS │ Purchases │ Returns │ Payments │ AR/AP            │
├─────────────────────────────────────────────────────────────────┤
│                    MASTER DATA LAYER                            │
│  Products │ Customers │ Suppliers │ Branches │ Users │ COA     │
└─────────────────────────────────────────────────────────────────┘
```

---

## SINGLE SOURCE OF TRUTH

| Domain | Collection | Status |
|--------|------------|--------|
| Master Barang | `products` | ✅ ACTIVE |
| Pergerakan Stok | `stock_movements` | ✅ ACTIVE |
| Penjualan | `sales_transactions` | ✅ ACTIVE |
| Pembelian | `purchases` | ✅ ACTIVE |
| Jurnal | `journal_entries` | ✅ ACTIVE |
| Setoran | `deposits` | ✅ ACTIVE |
| Piutang | `accounts_receivable` | ✅ NEW |
| Hutang | `accounts_payable` | ✅ NEW |
| Audit Logs | `audit_logs` | ✅ ACTIVE |
| Approval | `approval_requests` | ✅ NEW |
| COA | `chart_of_accounts` | ✅ ENHANCED |

---

## API ENDPOINTS SUMMARY

### Core Modules
- `/api/auth` - Authentication
- `/api/products` - Product master
- `/api/pos` - Point of Sale
- `/api/purchase` - Purchasing
- `/api/inventory` - Inventory

### Enhanced Modules
- `/api/deposit` - Setoran Harian (12 endpoints)
- `/api/rbac` - Role-Based Access Control
- `/api/pricing` - Multi-mode Pricing

### NEW Modules (March 2026)
- `/api/ar` - Accounts Receivable (11 endpoints)
- `/api/ap` - Accounts Payable (10 endpoints)
- `/api/approval` - Approval Engine (12 endpoints)
- `/api/accounting` - Accounting Engine (15 endpoints)

---

## JOURNAL ENTRIES STANDARD

### 1. Penjualan Cash
```
Debit:  1104 Kas Cabang
Credit: 4101 Penjualan
Credit: 2201 Pajak Keluaran
Debit:  5101 HPP
Credit: 1301 Persediaan
```

### 2. Penjualan Kredit
```
Debit:  1201 Piutang Dagang
Credit: 4101 Penjualan
Credit: 2201 Pajak Keluaran
Debit:  5101 HPP
Credit: 1301 Persediaan
```

### 3. Setoran Normal
```
Debit:  1103 Kas Kecil Pusat
Credit: 1104 Kas Cabang
```

### 4. Setoran Selisih Kurang
```
Debit:  1103 Kas Kecil Pusat
Debit:  6201 Selisih Kurang Kas
Credit: 1104 Kas Cabang
```

### 5. Pelunasan Piutang
```
Debit:  1101 Kas
Credit: 1201 Piutang Dagang
```

### 6. Pembayaran Hutang
```
Debit:  2101 Hutang Dagang
Credit: 1102 Bank
```

---

## SECURITY MATRIX

| Role | Level | Scope | Special Access |
|------|-------|-------|----------------|
| Super Admin | 0 | All | Full system |
| Pemilik | 1 | All | inherit_all |
| Direktur | 2 | All | All branches |
| Manager | 3 | Assigned | View margin |
| Supervisor | 4 | Branch | Verify deposit |
| Admin | 5 | Branch | Create transactions |
| Finance | 6 | Branch | AP/AR payment |
| Kasir | 7 | Own | Own data only |
| Viewer | 8 | Limited | View only |

---

## TEST RESULTS

| Iteration | Module | Result |
|-----------|--------|--------|
| 24 | Enterprise RBAC | 100% PASS |
| 25 | Multi-Mode Pricing | 100% PASS |
| 26 | Form Tambah Item | 100% PASS |
| 27 | Setoran Harian | 100% PASS |
| 28 | AR/AP/Approval/Accounting Backend | 28/28 PASS |
| 29 | AR/AP/Approval/Financial Reports Frontend | 85% PASS |

---

## COMPLETED FEATURES

### Phase 1: Foundation ✅
- [x] RBAC with role hierarchy
- [x] Multi-mode pricing system
- [x] ERP-grade item master
- [x] Stock movements tracking

### Phase 2: Operational ✅
- [x] Setoran Harian full workflow
- [x] Deposit journal integration
- [x] Kasir-locked access
- [x] Supervisor/Manager verification

### Phase 3: Accounting ✅ (NEW)
- [x] AR Module with aging
- [x] AP Module with aging
- [x] Approval Engine
- [x] Accounting Engine
- [x] Chart of Accounts
- [x] Account Mapping config
- [x] GL, Trial Balance
- [x] Balance Sheet, Income Statement

---

## REMAINING TASKS

### P0 - Critical ✅ COMPLETED
- [x] Frontend pages for AR/AP
- [x] Frontend for Approval Center
- [x] Frontend for Financial Reports
- [ ] Integration: Sales → AR (credit)
- [ ] Integration: Purchase → AP (credit)

### P1 - High
- [ ] Owner Dashboard with KPIs
- [ ] Finance Dashboard
- [ ] Operational Dashboard
- [ ] Reconciliation reports

### P2 - Medium
- [ ] Cash flow statement
- [ ] Export to Excel/PDF
- [ ] Advanced audit trail UI
- [ ] Period closing

### P3 - Future
- [ ] AI anomaly detection
- [ ] Fraud indicators
- [ ] Pricing recommendations
- [ ] Restock suggestions

---

## FILE STRUCTURE

```
/app/backend/routes/
├── deposit_system.py      ✅ Setoran Harian
├── rbac_system.py         ✅ RBAC
├── pricing_system.py      ✅ Pricing
├── ar_system.py           ✅ AR Backend
├── ap_system.py           ✅ AP Backend
├── approval_engine.py     ✅ Approval Backend
├── accounting_engine.py   ✅ Accounting Backend
├── pos.py                 ✅ POS
├── purchase.py            ✅ Purchase
└── ... (other modules)

/app/frontend/src/pages/
├── operasional/
│   └── SetoranHarian.jsx  ✅ Complete
├── accounting/
│   ├── AccountsReceivable.jsx  ✅ NEW
│   ├── AccountsPayable.jsx     ✅ NEW
│   └── FinancialReports.jsx    ✅ NEW
├── approval/
│   └── ApprovalCenter.jsx      ✅ NEW
└── dashboard/             🔴 TODO

/app/frontend/src/components/accounting/
├── ARDetailModal.jsx      ✅ NEW
├── ARPaymentModal.jsx     ✅ NEW
├── APDetailModal.jsx      ✅ NEW
└── APPaymentModal.jsx     ✅ NEW
```

---

## CREDENTIALS

| Role | Email | Password |
|------|-------|----------|
| Owner | ocbgroupbjm@gmail.com | admin123 |
| Kasir | kasir_test@ocb.com | password123 |

---

## STATISTICS

| Metric | Value |
|--------|-------|
| Total Branches | 46 |
| Total Products | 31 |
| RBAC Modules | 109 |
| Chart of Accounts | 17 |
| Approval Rules | 4 |
| API Endpoints | 200+ |

---

**Version:** 12.0 (Enterprise Blueprint)
**Last Updated:** March 10, 2026
**Architecture:** SSOT, Non-Destructive, Additive
