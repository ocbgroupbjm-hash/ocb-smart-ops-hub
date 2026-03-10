# OCB TITAN ERP - ENTERPRISE ARCHITECTURE BLUEPRINT
## Version 1.0 - Enterprise Retail Multi-Branch System

---

# BAGIAN I: ARSITEKTUR SISTEM

## 1. LAYER ARSITEKTUR

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI INSIGHT LAYER (L10)                       │
│  Anomaly Detection │ Recommendations │ Fraud Indicators         │
├─────────────────────────────────────────────────────────────────┤
│                    REPORTING LAYER (L9)                         │
│  Financial Reports │ Operational Reports │ Dashboard            │
├─────────────────────────────────────────────────────────────────┤
│                    INTEGRATION LAYER (L8)                       │
│  WhatsApp │ External APIs │ Export/Import │ Backup              │
├─────────────────────────────────────────────────────────────────┤
│                    AUDIT & SECURITY LAYER (L7)                  │
│  Audit Logs │ Permission Checks │ Activity Tracking             │
├─────────────────────────────────────────────────────────────────┤
│                    APPROVAL LAYER (L6)                          │
│  Approval Engine │ Workflow Rules │ Authorization               │
├─────────────────────────────────────────────────────────────────┤
│                    OPERATIONAL CONTROL LAYER (L5)               │
│  Cash Deposits │ Reconciliation │ Shift Management              │
├─────────────────────────────────────────────────────────────────┤
│                    ACCOUNTING ENGINE LAYER (L4)                 │
│  Journal Entries │ GL │ Trial Balance │ Financial Statements    │
├─────────────────────────────────────────────────────────────────┤
│                    INVENTORY CONTROL LAYER (L3)                 │
│  Stock Movements │ Valuations │ Adjustments │ Transfers         │
├─────────────────────────────────────────────────────────────────┤
│                    TRANSACTION LAYER (L2)                       │
│  Sales/POS │ Purchases │ Returns │ Payments │ AR/AP             │
├─────────────────────────────────────────────────────────────────┤
│                    MASTER DATA LAYER (L1)                       │
│  Products │ Customers │ Suppliers │ Branches │ Users │ Accounts │
└─────────────────────────────────────────────────────────────────┘
```

## 2. SINGLE SOURCE OF TRUTH (SSOT)

| Data Domain | Primary Collection | Status |
|-------------|-------------------|--------|
| Master Barang | `products` | ✅ EXISTS |
| Pergerakan Stok | `stock_movements` | ✅ EXISTS (23 docs) |
| Penjualan | `sales_transactions` | ✅ EXISTS (42 docs) |
| Pembelian | `purchases` | ✅ EXISTS (3 docs) |
| Jurnal Akuntansi | `journal_entries` | ✅ EXISTS (2 docs) |
| Setoran Harian | `deposits` | ✅ EXISTS (5 docs) |
| Piutang Dagang | `accounts_receivable` | ⚠️ NEED CREATE |
| Hutang Dagang | `accounts_payable` | ⚠️ NEED CREATE |
| Audit Logs | `audit_logs` | ✅ EXISTS (64 docs) |
| Chart of Accounts | `chart_of_accounts` | ✅ EXISTS (12 docs) |

## 3. EXISTING COMPONENTS STATUS

### ✅ SUDAH ADA & JANGAN DIUBAH:
- RBAC System (`rbac_system.py`) - 10 roles, 11341 permissions
- Pricing System (`pricing_system.py`) - 4 modes
- Deposit System (`deposit_system.py`) - Full workflow
- Products (`products.py`) - Master items
- Stock Movements (`stock_movements`) - Movement tracking
- Audit Logs (`audit_logs`) - Activity logging

### ⚠️ PERLU DISEMPURNAKAN (NON-DESTRUCTIVE):
- Purchase cycle - Tambah receipt, invoice, payment tracking
- Sales - Tambah link ke deposit, AR integration
- Accounting Engine - Expand auto-journal sources
- AP/AR Module - Create new collections
- Approval Engine - Create workflow rules
- Dashboard - Expand metrics

---

# BAGIAN II: DATABASE SCHEMA BLUEPRINT

## 1. COLLECTIONS YANG SUDAH ADA (PERTAHANKAN)

```
MASTER DATA:
├── products (31) ────────── Master barang global
├── categories (5) ────────── Kategori produk
├── brands (6) ──────────── Merek produk
├── units (7) ──────────── Satuan
├── customers (20) ────────── Master pelanggan
├── customer_levels (5) ───── Level harga pelanggan
├── suppliers (6) ────────── Master supplier
├── branches (46) ────────── Cabang/toko
├── warehouses (4) ────────── Gudang
├── users (9) ──────────── Master user
├── roles (10) ─────────── Role definitions
├── role_permissions (11341) ─ Permission matrix
├── chart_of_accounts (12) ── Akun keuangan

TRANSAKSI:
├── sales_transactions (42) ─ Penjualan/POS
├── purchases (3) ────────── Pembelian
├── stock_movements (23) ──── Pergerakan stok
├── deposits (5) ────────── Setoran harian
├── deposit_details (29) ──── Detail transaksi setoran
├── journal_entries (2) ───── Jurnal akuntansi

OPERATIONAL:
├── audit_logs (64) ────────── Jejak aktivitas
├── security_alerts (6) ───── Alert keamanan
├── attendance (289) ────────── Absensi
├── employees (37) ────────── Karyawan
```

## 2. COLLECTIONS BARU YANG PERLU DITAMBAHKAN

```javascript
// ============================================
// ACCOUNTS RECEIVABLE (PIUTANG)
// ============================================
accounts_receivable: {
  id: UUID,
  ar_no: "AR-{BRANCH}-{YYYYMMDD}-{SEQ}",
  ar_date: Date,
  due_date: Date,
  customer_id: UUID,
  customer_name: String,
  branch_id: UUID,
  source_type: "sales" | "other",
  source_id: UUID,
  source_no: String,
  currency: "IDR",
  original_amount: Number,
  paid_amount: Number,
  outstanding_amount: Number,
  status: "open" | "partial" | "paid" | "overdue" | "written_off",
  payment_term_days: Number,
  notes: String,
  created_by: UUID,
  created_at: DateTime,
  updated_at: DateTime
}

ar_payments: {
  id: UUID,
  payment_no: String,
  payment_date: Date,
  ar_id: UUID,
  ar_no: String,
  customer_id: UUID,
  branch_id: UUID,
  amount: Number,
  payment_method: String,
  bank_account_id: UUID,
  reference_no: String,
  notes: String,
  journal_id: UUID,
  created_by: UUID,
  created_at: DateTime
}

// ============================================
// ACCOUNTS PAYABLE (HUTANG)
// ============================================
accounts_payable: {
  id: UUID,
  ap_no: "AP-{BRANCH}-{YYYYMMDD}-{SEQ}",
  ap_date: Date,
  due_date: Date,
  supplier_id: UUID,
  supplier_name: String,
  branch_id: UUID,
  source_type: "purchase" | "expense" | "other",
  source_id: UUID,
  source_no: String,
  currency: "IDR",
  original_amount: Number,
  paid_amount: Number,
  outstanding_amount: Number,
  status: "open" | "partial" | "paid" | "overdue",
  payment_term_days: Number,
  supplier_invoice_no: String,
  notes: String,
  created_by: UUID,
  created_at: DateTime,
  updated_at: DateTime
}

ap_payments: {
  id: UUID,
  payment_no: String,
  payment_date: Date,
  ap_id: UUID,
  ap_no: String,
  supplier_id: UUID,
  branch_id: UUID,
  amount: Number,
  payment_method: String,
  bank_account_id: UUID,
  reference_no: String,
  notes: String,
  journal_id: UUID,
  created_by: UUID,
  created_at: DateTime
}

// ============================================
// PURCHASE ENHANCEMENTS
// ============================================
purchase_receipts: {
  id: UUID,
  receipt_no: String,
  receipt_date: Date,
  purchase_id: UUID,
  purchase_no: String,
  supplier_id: UUID,
  branch_id: UUID,
  warehouse_id: UUID,
  status: "draft" | "received" | "posted",
  total_qty: Number,
  notes: String,
  received_by: UUID,
  created_at: DateTime
}

purchase_receipt_items: {
  id: UUID,
  receipt_id: UUID,
  purchase_item_id: UUID,
  product_id: UUID,
  product_name: String,
  qty_ordered: Number,
  qty_received: Number,
  unit_id: UUID,
  batch_no: String,
  expiry_date: Date,
  rack_id: UUID,
  notes: String
}

purchase_invoices: {
  id: UUID,
  invoice_no: String,
  invoice_date: Date,
  purchase_id: UUID,
  supplier_id: UUID,
  supplier_invoice_no: String,
  due_date: Date,
  subtotal: Number,
  tax_total: Number,
  grand_total: Number,
  status: "draft" | "posted",
  ap_id: UUID,
  journal_id: UUID,
  created_by: UUID,
  created_at: DateTime
}

// ============================================
// APPROVAL ENGINE
// ============================================
approval_rules: {
  id: UUID,
  rule_name: String,
  module: String,  // "purchase", "sales_void", "deposit", "adjustment", "discount"
  condition_type: "amount" | "percentage" | "quantity",
  condition_operator: ">" | ">=" | "<" | "<=" | "=",
  condition_value: Number,
  approval_levels: [{
    level: Number,
    role_code: String,
    can_skip: Boolean
  }],
  active: Boolean,
  branch_id: UUID | null,  // null = all branches
  created_by: UUID,
  created_at: DateTime
}

approval_requests: {
  id: UUID,
  request_no: String,
  module: String,
  document_type: String,
  document_id: UUID,
  document_no: String,
  branch_id: UUID,
  requested_by: UUID,
  requested_by_name: String,
  request_date: DateTime,
  amount: Number,
  reason: String,
  current_level: Number,
  max_level: Number,
  status: "pending" | "approved" | "rejected" | "cancelled",
  steps: [{
    level: Number,
    role_code: String,
    status: "pending" | "approved" | "rejected",
    actioned_by: UUID,
    actioned_by_name: String,
    actioned_at: DateTime,
    notes: String
  }],
  completed_at: DateTime,
  created_at: DateTime
}

// ============================================
// ENHANCED AUDIT LOGS
// ============================================
// Extend existing audit_logs with:
audit_logs_extended: {
  // ... existing fields ...
  document_type: String,
  document_id: UUID,
  document_no: String,
  old_values: Object,
  new_values: Object,
  changed_fields: [String],
  severity: "normal" | "warning" | "critical",
  ip_address: String,
  device_info: String,
  checksum: String
}

// ============================================
// RECONCILIATION
// ============================================
reconciliation_logs: {
  id: UUID,
  reconciliation_date: Date,
  branch_id: UUID,
  period_start: Date,
  period_end: Date,
  type: "sales_vs_deposit" | "stock" | "cash",
  expected_value: Number,
  actual_value: Number,
  difference: Number,
  status: "matched" | "discrepancy" | "resolved",
  resolved_by: UUID,
  resolved_at: DateTime,
  resolution_notes: String,
  created_by: UUID,
  created_at: DateTime
}

// ============================================
// ACCOUNT MAPPING SETTINGS
// ============================================
account_mapping_settings: {
  id: UUID,
  branch_id: UUID | "default",
  mapping_type: String,
  mappings: {
    // Sales
    sales_cash_account: UUID,
    sales_revenue_account: UUID,
    sales_tax_account: UUID,
    sales_discount_account: UUID,
    cogs_account: UUID,
    inventory_account: UUID,
    
    // Purchase
    purchase_inventory_account: UUID,
    purchase_tax_account: UUID,
    ap_account: UUID,
    
    // AR/AP
    ar_account: UUID,
    ap_account: UUID,
    
    // Deposit
    central_cash_account: UUID,
    branch_cash_account: UUID,
    cashier_cash_account: UUID,
    cash_in_transit_account: UUID,
    shortage_account: UUID,
    overage_account: UUID,
    employee_receivable_account: UUID
  },
  updated_by: UUID,
  updated_at: DateTime
}
```

---

# BAGIAN III: API ENDPOINTS BLUEPRINT

## 1. EXISTING ENDPOINTS (PERTAHANKAN)

```
DEPOSIT SYSTEM (/api/deposit):
✅ POST /init
✅ POST /seed-sales
✅ GET  /my-sales
✅ POST /create
✅ GET  /{id}
✅ PUT  /{id}
✅ POST /{id}/receive
✅ POST /{id}/verify
✅ POST /{id}/approve
✅ POST /{id}/post
✅ POST /{id}/cancel
✅ GET  /list
✅ GET  /dashboard/summary
✅ GET  /reconciliation/summary

RBAC SYSTEM (/api/rbac):
✅ GET  /roles
✅ GET  /roles/{id}
✅ POST /roles
✅ PUT  /roles/{id}
✅ DELETE /roles/{id}
✅ GET  /permissions/modules
✅ GET  /permissions/matrix/{role_id}
✅ POST /permissions/{role_id}
✅ GET  /user/permissions
✅ GET  /check
✅ GET  /check-branch
✅ GET  /audit-logs
✅ GET  /security-alerts

PRICING SYSTEM (/api/pricing):
✅ GET  /config/{product_id}
✅ POST /config/{product_id}
✅ GET  /calculate
```

## 2. NEW ENDPOINTS TO ADD

```
// ============================================
// ACCOUNTS RECEIVABLE (/api/ar)
// ============================================
GET    /api/ar/list                    // List AR with filters
GET    /api/ar/{id}                    // Get AR detail
POST   /api/ar/create                  // Create AR (usually auto from sales)
PUT    /api/ar/{id}                    // Update AR
POST   /api/ar/{id}/payment            // Record payment
GET    /api/ar/aging                   // AR Aging report
GET    /api/ar/customer/{customer_id}  // AR by customer
GET    /api/ar/overdue                 // Overdue AR list
POST   /api/ar/{id}/write-off          // Write off bad debt

// ============================================
// ACCOUNTS PAYABLE (/api/ap)
// ============================================
GET    /api/ap/list                    // List AP with filters
GET    /api/ap/{id}                    // Get AP detail
POST   /api/ap/create                  // Create AP (usually auto from purchase)
PUT    /api/ap/{id}                    // Update AP
POST   /api/ap/{id}/payment            // Record payment
GET    /api/ap/aging                   // AP Aging report
GET    /api/ap/supplier/{supplier_id}  // AP by supplier
GET    /api/ap/due-soon                // AP due within X days

// ============================================
// PURCHASE ENHANCEMENTS (/api/purchase)
// ============================================
POST   /api/purchase/{id}/receive      // Create receipt
GET    /api/purchase/{id}/receipts     // List receipts
POST   /api/purchase/{id}/invoice      // Create invoice
GET    /api/purchase/{id}/invoices     // List invoices
POST   /api/purchase/{id}/payment      // Record payment
GET    /api/purchase/price-history/{product_id}

// ============================================
// APPROVAL ENGINE (/api/approval)
// ============================================
GET    /api/approval/rules             // List rules
POST   /api/approval/rules             // Create rule
PUT    /api/approval/rules/{id}        // Update rule
DELETE /api/approval/rules/{id}        // Delete rule
GET    /api/approval/pending           // My pending approvals
GET    /api/approval/requests          // All requests (by scope)
POST   /api/approval/request           // Create approval request
POST   /api/approval/{id}/approve      // Approve
POST   /api/approval/{id}/reject       // Reject
GET    /api/approval/history           // Approval history

// ============================================
// RECONCILIATION (/api/reconciliation)
// ============================================
GET    /api/reconciliation/sales-vs-deposit  // Compare sales to deposits
GET    /api/reconciliation/cash-position     // Cash position by branch
GET    /api/reconciliation/stock             // Stock reconciliation
POST   /api/reconciliation/resolve           // Mark discrepancy resolved

// ============================================
// ENHANCED ACCOUNTING (/api/accounting)
// ============================================
GET    /api/accounting/gl/{account_id}       // General Ledger
GET    /api/accounting/trial-balance         // Trial Balance
GET    /api/accounting/balance-sheet         // Neraca
GET    /api/accounting/income-statement      // Laba Rugi
GET    /api/accounting/cash-flow             // Arus Kas
POST   /api/accounting/period-close          // Close period
GET    /api/accounting/account-mapping       // Get mappings
PUT    /api/accounting/account-mapping       // Update mappings

// ============================================
// DASHBOARDS (/api/dashboard)
// ============================================
GET    /api/dashboard/owner                  // Owner dashboard
GET    /api/dashboard/finance                // Finance dashboard
GET    /api/dashboard/operational            // Operational dashboard
GET    /api/dashboard/branch/{branch_id}     // Branch specific
GET    /api/dashboard/kpi                    // KPI metrics
```

---

# BAGIAN IV: JURNAL AKUNTANSI STANDAR

## 1. SALES JOURNALS

```
PENJUALAN CASH:
┌────────────────────────────┬──────────┬──────────┐
│ Account                    │ Debit    │ Credit   │
├────────────────────────────┼──────────┼──────────┤
│ Kas Cabang / Kasir         │ XXX      │          │
│ Penjualan                  │          │ XXX      │
│ Pajak Keluaran             │          │ XXX      │
│ HPP                        │ XXX      │          │
│ Persediaan                 │          │ XXX      │
└────────────────────────────┴──────────┴──────────┘

PENJUALAN KREDIT:
┌────────────────────────────┬──────────┬──────────┐
│ Account                    │ Debit    │ Credit   │
├────────────────────────────┼──────────┼──────────┤
│ Piutang Dagang             │ XXX      │          │
│ Penjualan                  │          │ XXX      │
│ Pajak Keluaran             │          │ XXX      │
│ HPP                        │ XXX      │          │
│ Persediaan                 │          │ XXX      │
└────────────────────────────┴──────────┴──────────┘
```

## 2. PURCHASE JOURNALS

```
PEMBELIAN CASH:
┌────────────────────────────┬──────────┬──────────┐
│ Account                    │ Debit    │ Credit   │
├────────────────────────────┼──────────┼──────────┤
│ Persediaan                 │ XXX      │          │
│ Pajak Masukan              │ XXX      │          │
│ Kas / Bank                 │          │ XXX      │
└────────────────────────────┴──────────┴──────────┘

PEMBELIAN KREDIT:
┌────────────────────────────┬──────────┬──────────┐
│ Account                    │ Debit    │ Credit   │
├────────────────────────────┼──────────┼──────────┤
│ Persediaan                 │ XXX      │          │
│ Pajak Masukan              │ XXX      │          │
│ Hutang Dagang              │          │ XXX      │
└────────────────────────────┴──────────┴──────────┘
```

## 3. DEPOSIT JOURNALS

```
SETORAN NORMAL (SESUAI):
┌────────────────────────────┬──────────┬──────────┐
│ Account                    │ Debit    │ Credit   │
├────────────────────────────┼──────────┼──────────┤
│ Kas Kecil Pusat            │ XXX      │          │
│ Kas Cabang / Transit       │          │ XXX      │
└────────────────────────────┴──────────┴──────────┘

SETORAN SELISIH KURANG:
┌────────────────────────────┬──────────┬──────────┐
│ Account                    │ Debit    │ Credit   │
├────────────────────────────┼──────────┼──────────┤
│ Kas Kecil Pusat            │ XXX      │          │
│ Selisih Kurang Kas         │ XXX      │          │
│ Kas Cabang / Transit       │          │ XXX      │
└────────────────────────────┴──────────┴──────────┘

SETORAN SELISIH LEBIH:
┌────────────────────────────┬──────────┬──────────┐
│ Account                    │ Debit    │ Credit   │
├────────────────────────────┼──────────┼──────────┤
│ Kas Kecil Pusat            │ XXX      │          │
│ Kas Cabang / Transit       │          │ XXX      │
│ Selisih Lebih Kas          │          │ XXX      │
└────────────────────────────┴──────────┴──────────┘
```

## 4. AR/AP JOURNALS

```
PELUNASAN PIUTANG:
┌────────────────────────────┬──────────┬──────────┐
│ Account                    │ Debit    │ Credit   │
├────────────────────────────┼──────────┼──────────┤
│ Kas / Bank                 │ XXX      │          │
│ Piutang Dagang             │          │ XXX      │
└────────────────────────────┴──────────┴──────────┘

PEMBAYARAN HUTANG:
┌────────────────────────────┬──────────┬──────────┐
│ Account                    │ Debit    │ Credit   │
├────────────────────────────┼──────────┼──────────┤
│ Hutang Dagang              │ XXX      │          │
│ Kas / Bank                 │          │ XXX      │
└────────────────────────────┴──────────┴──────────┘
```

---

# BAGIAN V: SECURITY MATRIX

## 1. ROLE HIERARCHY (EXISTING)

```
Level 0: Super Admin     ─── Full system access
Level 1: Pemilik        ─── Full business access (inherit_all)
Level 2: Direktur       ─── All branches
Level 3: Manager        ─── Assigned branches
Level 4: Supervisor     ─── Branch level
Level 5: Admin          ─── Branch level, limited actions
Level 6: Gudang/Finance ─── Specific modules
Level 7: Kasir          ─── Own data only
Level 8: Viewer         ─── View only
```

## 2. DATA SCOPE RULES

```javascript
SCOPE_RULES = {
  "kasir": {
    scope: "own_only",
    filter: { cashier_id: user_id, branch_id: user_branch_id },
    can_view_cost: false,
    can_view_margin: false,
    can_override_price: false
  },
  "supervisor": {
    scope: "branch_only",
    filter: { branch_id: user_branch_id },
    can_view_cost: true,
    can_view_margin: false,
    can_override_price: true  // with approval
  },
  "manager": {
    scope: "assigned_branches",
    filter: { branch_id: { $in: user_branch_ids } },
    can_view_cost: true,
    can_view_margin: true,
    can_override_price: true
  },
  "pemilik": {
    scope: "all",
    filter: {},
    can_view_cost: true,
    can_view_margin: true,
    can_override_price: true
  }
}
```

## 3. PERMISSION MODULES (EXTENDED)

```
EXISTING MODULES (99):
- master_*, purchase_*, sales_*, inventory_*, accounting_*, report_*, menu_*, ai_*, hr_*, security_*

NEW MODULES TO ADD:
- accounts_receivable
- accounts_payable
- approval_engine
- reconciliation
- financial_reports
- operational_dashboard
- finance_dashboard
- owner_dashboard
```

---

# BAGIAN VI: IMPLEMENTATION ROADMAP

## FASE 1: FOUNDATION (Minggu 1-2)
**Status: PARTIALLY COMPLETE**

| Task | Status | Priority |
|------|--------|----------|
| RBAC System | ✅ DONE | P0 |
| Pricing System | ✅ DONE | P0 |
| Deposit System | ✅ DONE | P0 |
| Master Products enhanced | ⚠️ CHECK | P0 |
| Stock Movements core | ✅ EXISTS | P0 |
| Sales Transactions | ✅ EXISTS | P0 |

## FASE 2: ACCOUNTING INTEGRATION (Minggu 3-4)
**Status: IN PROGRESS**

| Task | Status | Priority |
|------|--------|----------|
| Chart of Accounts expand | ⚠️ NEEDED | P0 |
| Account Mapping Settings | ⚠️ NEEDED | P0 |
| AR Module | 🔴 TODO | P0 |
| AP Module | 🔴 TODO | P0 |
| Auto-Journal Enhancement | ⚠️ PARTIAL | P0 |
| GL Reports | ⚠️ PARTIAL | P1 |

## FASE 3: OPERATIONAL CONTROL (Minggu 5-6)

| Task | Status | Priority |
|------|--------|----------|
| Reconciliation Module | 🔴 TODO | P0 |
| Approval Engine | 🔴 TODO | P1 |
| Enhanced Audit | ⚠️ PARTIAL | P1 |
| Exception Dashboard | 🔴 TODO | P1 |

## FASE 4: DASHBOARDS (Minggu 7-8)

| Task | Status | Priority |
|------|--------|----------|
| Owner Dashboard | 🔴 TODO | P1 |
| Finance Dashboard | 🔴 TODO | P1 |
| Operational Dashboard | 🔴 TODO | P1 |
| KPI Tracking | ⚠️ PARTIAL | P2 |

## FASE 5: AI INSIGHTS (Minggu 9+)

| Task | Status | Priority |
|------|--------|----------|
| Anomaly Detection | 🔴 TODO | P2 |
| Fraud Indicators | ⚠️ PARTIAL | P2 |
| Recommendations | 🔴 TODO | P2 |

---

# BAGIAN VII: TEST REQUIREMENTS

## 1. EXISTING TESTS TO PROTECT

```
✅ Pricing System - iteration_25.json - 100% PASS
✅ RBAC System - iteration_24.json - 100% PASS
✅ Form Tambah Item - iteration_26.json - 100% PASS
✅ Deposit System - iteration_27.json - 100% PASS
```

## 2. NEW TESTS TO ADD

```
AR/AP Module Tests:
- Create AR from sales credit
- AR payment reduces outstanding
- AR aging calculation
- Create AP from purchase credit
- AP payment reduces outstanding
- AP aging calculation

Integration Tests:
- Sales → Stock Movement → Journal
- Purchase → Stock Movement → AP → Journal
- Deposit → Central Cash → Journal
- AR Payment → Journal
- AP Payment → Journal

Security Tests:
- Kasir cannot access other cashier's deposits
- Kasir cannot see cost price
- Supervisor cannot access other branches
- All scope filtering verified
- 403 returned for unauthorized access

Reconciliation Tests:
- Sales vs Deposit matches
- Stock balance accuracy
- Cash position accuracy
```

---

# BAGIAN VIII: FILES REFERENCE

## Backend Files Structure

```
/app/backend/routes/
├── deposit_system.py      ✅ Complete
├── rbac_system.py         ✅ Complete
├── pricing_system.py      ✅ Complete
├── accounting.py          ⚠️ Enhance
├── purchase.py            ⚠️ Enhance
├── pos.py                 ⚠️ Enhance
├── inventory.py           ⚠️ Enhance
├── finance.py             ⚠️ Enhance
├── ar_system.py           🔴 Create NEW
├── ap_system.py           🔴 Create NEW
├── approval_engine.py     🔴 Create NEW
├── reconciliation.py      🔴 Create NEW
├── dashboard_enhanced.py  🔴 Create NEW
└── accounting_engine.py   🔴 Create NEW

/app/frontend/src/pages/
├── operasional/
│   └── SetoranHarian.jsx  ✅ Complete
├── accounting/
│   ├── AR.jsx             🔴 Create NEW
│   ├── AP.jsx             🔴 Create NEW
│   └── Reconciliation.jsx 🔴 Create NEW
├── dashboard/
│   ├── OwnerDashboard.jsx 🔴 Create NEW
│   └── FinanceDashboard.jsx 🔴 Create NEW
└── approval/
    └── ApprovalCenter.jsx 🔴 Create NEW
```

---

# BAGIAN IX: IMMEDIATE ACTION ITEMS

## P0 - CRITICAL (Do First)

1. **Create AR Module** (`ar_system.py`)
   - Collections: accounts_receivable, ar_payments
   - Auto-create from sales credit
   - Payment recording
   - Aging report

2. **Create AP Module** (`ap_system.py`)
   - Collections: accounts_payable, ap_payments
   - Auto-create from purchase credit
   - Payment recording
   - Aging report

3. **Expand Chart of Accounts**
   - Add required accounts for AR/AP
   - Add account mapping settings

4. **Enhance Auto-Journal**
   - Sales → Journal (with AR if credit)
   - Purchase → Journal (with AP if credit)
   - AR Payment → Journal
   - AP Payment → Journal

## P1 - HIGH (Do Next)

5. **Approval Engine** (`approval_engine.py`)
   - Approval rules configuration
   - Request/approve workflow
   - Integration with modules

6. **Reconciliation Module** (`reconciliation.py`)
   - Sales vs Deposit comparison
   - Cash position tracking
   - Exception reporting

7. **Enhanced Dashboards**
   - Owner Dashboard with key metrics
   - Finance Dashboard with cash flow
   - Operational Dashboard with alerts

## P2 - MEDIUM (Future)

8. AI Insights integration
9. Advanced reporting
10. Mobile optimization

---

**Document Version:** 1.0
**Created:** March 10, 2026
**Status:** ACTIVE BLUEPRINT
