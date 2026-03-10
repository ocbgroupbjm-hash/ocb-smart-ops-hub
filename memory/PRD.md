# OCB TITAN ERP - ENTERPRISE RETAIL OPERATING SYSTEM
## Product Requirements Document (PRD) v12.0

---

# OVERVIEW

OCB TITAN ERP adalah sistem ERP retail enterprise untuk bisnis multi-cabang dengan fitur lengkap:
- **POS / Penjualan** dengan multi-mode pricing
- **Pembelian** dengan AP integration
- **Inventory / Stok** dengan movement tracking
- **Setoran Harian** dengan security ketat
- **Hutang Piutang** (AR/AP) dengan aging
- **Akuntansi** dengan auto-journal
- **Approval Engine** untuk otorisasi
- **RBAC** dengan role hierarchy
- **Audit Trail** untuk semua aktivitas

---

# LATEST UPDATE: March 10, 2026

## ENTERPRISE BLUEPRINT IMPLEMENTED

### ✅ NEW MODULES CREATED

#### 1. Accounts Receivable (AR) - `/api/ar`
- **File**: `/app/backend/routes/ar_system.py`
- **Features**:
  - Create AR dari penjualan kredit
  - Payment recording dengan auto-journal
  - Aging report (Current, 1-30, 31-60, 61-90, >90 days)
  - Customer credit limit tracking
  - Write-off dengan approval
  - Role-based access (Finance/Manager level)

#### 2. Accounts Payable (AP) - `/api/ap`
- **File**: `/app/backend/routes/ap_system.py`
- **Features**:
  - Create AP dari pembelian kredit
  - Payment recording dengan auto-journal
  - Aging report
  - Supplier outstanding tracking
  - Due soon alerts
  - Role-based access

#### 3. Approval Engine - `/api/approval`
- **File**: `/app/backend/routes/approval_engine.py`
- **Features**:
  - Configurable approval rules by module
  - Multi-level approval hierarchy
  - Condition-based triggers (amount, percentage)
  - Default rules created:
    - Pembelian > 10 Juta: Supervisor → Manager
    - Void Penjualan > 1 Juta: Supervisor
    - Diskon > 20%: Supervisor
    - Selisih Setoran > 100rb: Supervisor → Finance

#### 4. Accounting Engine - `/api/accounting`
- **File**: `/app/backend/routes/accounting_engine.py`
- **Features**:
  - Chart of Accounts management
  - Configurable Account Mapping per branch
  - Manual journal entry creation
  - General Ledger (GL)
  - Trial Balance
  - Balance Sheet (Neraca)
  - Income Statement (Laba Rugi)
  - Journal posting workflow

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
| 24 | Enterprise RBAC | ✅ 100% PASS |
| 25 | Multi-Mode Pricing | ✅ 100% PASS |
| 26 | Form Tambah Item | ✅ 100% PASS |
| 27 | Setoran Harian | ✅ 100% PASS |
| 28 | AR/AP/Approval/Accounting | ✅ INITIALIZED |

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

### P0 - Critical
- [ ] Frontend pages for AR/AP
- [ ] Frontend for Approval Center
- [ ] Frontend for Financial Reports
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
├── ar_system.py           ✅ NEW - AR
├── ap_system.py           ✅ NEW - AP
├── approval_engine.py     ✅ NEW - Approval
├── accounting_engine.py   ✅ NEW - Accounting
├── pos.py                 ✅ POS
├── purchase.py            ✅ Purchase
└── ... (other modules)

/app/frontend/src/pages/
├── operasional/
│   └── SetoranHarian.jsx  ✅ Complete
├── accounting/            🔴 TODO
├── approval/              🔴 TODO
└── dashboard/             🔴 TODO
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
