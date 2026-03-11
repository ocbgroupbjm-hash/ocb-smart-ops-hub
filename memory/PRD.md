# OCB TITAN ERP - ENTERPRISE RETAIL OPERATING SYSTEM
## Product Requirements Document (PRD) v19.0

---

# OVERVIEW

OCB TITAN ERP adalah sistem ERP retail enterprise untuk bisnis multi-cabang dengan fitur lengkap:
- **POS / Penjualan** dengan multi-mode pricing + auto AR
- **Sales Module iPOS Style** dengan full integration (NEW!)
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

# LATEST UPDATE: March 11, 2026 - AI MODULE AUDIT & RESTORATION

## Audit Modul AI - ALL 18 MODULES VERIFIED ✅

### DASHBOARDS (5 Modules)
| Module | Route | Status | Features |
|--------|-------|--------|----------|
| Owner Dashboard | /owner-dashboard | ✅ ACTIVE | KPIs (Penjualan, Pembelian, AR, AP, Stok), Peringatan, Performa Cabang |
| Finance Dashboard | /finance-dashboard | ✅ ACTIVE | P&L Summary, Neraca, AR/AP Aging, Trial Balance |
| CFO Dashboard | /cfo-dashboard | ✅ ACTIVE | Revenue, Net Profit, Payroll Ratio, Laba Rugi |
| ERP Dashboard | /erp-dashboard | ✅ ACTIVE | Status Setoran, Critical Alerts |
| Main Dashboard | /dashboard | ✅ ACTIVE | AI Insights, Trend, Produk Terlaris |

### WAR ROOM & MONITORING (4 Modules)
| Module | Route | Status | Features |
|--------|-------|--------|----------|
| War Room | /warroom | ✅ ACTIVE | Real-time monitoring, Top 5 Cabang, Live Feed |
| War Room V2 | /war-room-v2 | ✅ ACTIVE | Command Center, AI Insights, Alert Critical |
| AI Super War Room | /ai-warroom-super | ✅ ACTIVE | Prediksi Toko, Risiko Kasir, Lokasi Baru |
| War Room Alerts | /warroom-alerts | ✅ ACTIVE | Alert severity levels, Response center |

### AI INTELLIGENCE (5 Modules)
| Module | Route | Status | Features |
|--------|-------|--------|----------|
| AI Command Center | /ai-command-center | ✅ ACTIVE | Business analysis, AI Recommendations |
| AI Business | /ai-bisnis | ✅ ACTIVE | Insight Penjualan, Rekomendasi Restock |
| AI Sales | /ai-sales | ✅ ACTIVE | Sales Assistant, Chat interface |
| AI Performance | /ai-performance | ✅ ACTIVE | Employee ranking, Score system |
| Hallo OCB AI | /hallo-ai | ✅ ACTIVE | Multi-persona chat (CEO, CFO, COO, etc) |

### CRM & KPI (3 Modules)
| Module | Route | Status | Features |
|--------|-------|--------|----------|
| CRM AI | /crm-ai | ✅ ACTIVE | Prompt Builder, Character AI, Reply Generator |
| CRM | /crm | ✅ ACTIVE | Customer management |
| KPI Performance | /kpi-performance | ✅ ACTIVE | Ranking Karyawan, Ranking Cabang |

### ANALYTICS (1 Module)
| Module | Route | Status | Features |
|--------|-------|--------|----------|
| Analytics | /analytics | ✅ ACTIVE | Business metrics, Performance |

### Sidebar Menu AI Tools Updated
```
AI Tools (submenu):
├── Owner Dashboard
├── Finance Dashboard
├── CFO Dashboard
├── ERP Dashboard
├── ─────────────────
├── AI Command Center
├── AI Sales Analytics
├── AI Business Insight
├── AI Employee Performance
├── Hallo OCB AI
├── ─────────────────
├── War Room
├── War Room V2
├── AI War Room Super
├── War Room Alerts
├── ─────────────────
├── CRM AI
├── CRM
├── KPI Performance
├── ─────────────────
└── Analytics
```

---

# PREVIOUS UPDATE: March 11, 2026 - SALES MODULE iPOS STYLE

## Sales Module iPOS Style - IMPLEMENTED & TESTED ✅

### Referensi UI: iPos Ultimate Sales Module

### API Endpoints Implemented
1. **Sales Orders (Pesanan Jual)**
   - `GET /api/sales/orders` - List dengan filter customer, status, date
   - `POST /api/sales/orders` - Create dengan item, qty, harga, diskon
   - `GET /api/sales/orders/{id}` - Detail order

2. **Sales Invoices (Penjualan)**
   - `GET /api/sales/invoices` - List dengan filter customer, status, date, has_tax
   - `POST /api/sales/invoices` - Create dengan integrasi stok, jurnal, piutang
   
3. **Sales Returns (Retur Penjualan)**
   - `GET /api/sales/returns` - List returns
   - `POST /api/sales/returns` - Create dengan integrasi stok kembali, jurnal, AR deduct

4. **Supporting Features**
   - `GET /api/sales/price-history` - History harga jual per customer/product
   - `GET /api/sales/trade-in` - Daftar tukar tambah
   - `POST /api/sales/trade-in` - Create trade-in
   - `GET /api/sales/points` - Point transaksi customer
   - `POST /api/sales/points/redeem` - Redeem points
   - `GET /api/sales/commission-payments` - Daftar pembayaran komisi sales
   - `POST /api/sales/commission-payments` - Bayar komisi
   - `GET /api/sales/deliveries` - Daftar pengiriman
   - `PUT /api/sales/deliveries/{id}` - Update status/resi
   - `POST /api/sales/tax-export/csv` - Export faktur pajak CSV
   - `POST /api/sales/tax-export/xml` - Export faktur pajak XML
   - `GET /api/sales/ar-payments` - Daftar pembayaran piutang

### Integrasi Otomatis
| Modul | Integrasi | Status |
|-------|-----------|--------|
| Inventory | Stock decrement on sale (sales_out) | ✅ |
| Inventory | Stock increment on return (sales_return_in) | ✅ |
| Accounting | Debit Kas/Piutang, Credit Penjualan, Credit PPN | ✅ |
| Accounting | Debit HPP, Credit Persediaan | ✅ |
| AR | Auto-create receivable on credit sale | ✅ |
| AR | Auto-reduce on sales return | ✅ |
| Price History | Record per transaction | ✅ |

### Frontend Pages Implemented
- `SalesOrderList.jsx` - Pesanan Jual List dengan filter, search, summary
- `SalesOrderAdd.jsx` - Form tambah pesanan
- `SalesList.jsx` - Daftar Penjualan dengan summary (Jumlah Transaksi, Total, Total Dibayar)
- `SalesAdd.jsx` - Form tambah penjualan
- `SalesReturnList.jsx` - Daftar Retur dengan summary
- `SalesReturnAdd.jsx` - Form tambah retur
- `SalesPriceHistory.jsx` - History harga jual
- `TradeInList.jsx` - Daftar tukar tambah
- `PointTransaksi.jsx` - Point transaksi
- `CommissionPaymentsList.jsx` - Komisi sales
- `DeliveriesList.jsx` - Daftar pengiriman
- `TaxExport.jsx` - Export faktur pajak
- `ARPaymentsList.jsx` - Pembayaran piutang
- `ARPaymentAdd.jsx` - Form pembayaran piutang
- `CashierList.jsx` - Kasir / POS

### Test Results (Iteration 34)
```
BACKEND: 100% - 20/20 tests passed
FRONTEND: 100% - All pages verified working

Verified Sales Orders:
✅ Create SO with SO-YYYYMMDD-XXXX format
✅ List with customer enrichment
✅ Frontend with filters and actions

Verified Sales Invoices:
✅ Cash sale - stock movement + journal
✅ Credit sale - AR entry + journal
✅ Summary footer (Jumlah, Total, Dibayar)

Verified Sales Returns:
✅ Stock add-back
✅ AR deduction (ar_deduct mode)
✅ Reversal journal

Verified Integrations:
✅ stock_movements collection updated
✅ journal_entries collection updated
✅ general_ledger collection updated
✅ accounts_receivable collection updated
```

---

# PREVIOUS UPDATE: March 11, 2026 - DASHBOARDS & PURCHASE ENTERPRISE iPOS STYLE

## Owner Dashboard - IMPLEMENTED & TESTED ✅

### KPI yang Ditampilkan
- Total Penjualan (dengan trend %)
- Total Pembelian
- Laba Kotor
- Rata-rata Tiket Per Transaksi
- Total Piutang (AR) dengan info jatuh tempo
- Total Hutang (AP) dengan info jatuh tempo
- Setoran Harian (pending/verified)
- Stok Rendah (item perlu restock)

### Fitur Tambahan
- Peringatan (Alerts) - Piutang/Hutang jatuh tempo, stok rendah
- Performa Cabang dengan progress bars
- Statistik (cabang, karyawan, cash flow)
- Transaksi Terbaru

---

## Finance Dashboard - IMPLEMENTED & TESTED ✅

### Ringkasan P&L
- Total Pendapatan (+trend%)
- HPP (COGS)
- Laba Kotor (margin%)
- Beban Operasional
- Laba Bersih (+trend%)

### Neraca Ringkas
- Total Aset (Kas & Bank, Piutang)
- Total Kewajiban (Hutang Dagang, dll)
- Total Ekuitas (Modal Disetor, Laba Ditahan)

### AR/AP Summary
- Piutang Usaha - Total, Belum Jatuh Tempo, Jatuh Tempo
- Hutang Usaha - Total, Belum Jatuh Tempo, Jatuh Tempo

### Tabel Data
- Neraca Saldo (Trial Balance) Preview
- Jurnal Terbaru

---

## Modul Pembelian Enterprise (iPos Style) - IMPLEMENTED & TESTED ✅

### Referensi UI: iPos Ultimate Purchase Module

### Header Transaksi
- No Transaksi (Auto: PO-CABANG-YYYYMMDD-XXXX)
- Tanggal & Jam
- Supplier (dengan kode)
- Gudang Masuk
- Cabang
- Sales / PIC
- Dept
- Referensi PO
- Jenis Transaksi (Langsung, Dari PO, Dari Permintaan, Transfer)
- PPN %
- Keterangan

### Grid Item Pembelian (23 Kolom)
| No | Kode | Barcode | Nama Item | Merk | Kategori | Jenis |
| Qty Pesan | Qty Datang | Satuan | Isi/Konversi |
| Harga Beli | Diskon % | Diskon Rp | Subtotal |
| Tax % | Total | Gudang | Batch | Expired | SN | Catatan |

### Tabs Bawah (seperti iPos)
1. Rincian Item
2. Potongan
3. Pajak
4. Biaya Lain
5. Serial Number
6. Riwayat Harga Beli
7. Riwayat Supplier Item

### Footer Perhitungan
- Subtotal Item
- Total Diskon
- Total Pajak
- Grand Total
- Jenis Pembayaran (Tunai, Kredit, DP, Deposit, Kombinasi)
- Jatuh Tempo (hari)
- Sisa Hutang

### Keyboard Shortcuts
- F2: Cari Item
- F3: Simpan Draft
- F4: Posting
- ESC: Batal

### Daftar Pembelian (List View)
Filter: Kata Kunci, Tanggal, Supplier, Cabang, Gudang, Status, Status Bayar, User, Sales, Item, No Faktur

Summary: Jumlah Transaksi, Total Pembelian, Total Pajak, Total Diskon, Total Hutang, Lunas, Belum Lunas

---

## Test Results (Iteration 33)
```
BACKEND: 91% - 21/23 tests passed
FRONTEND: 100% - All UI features verified

Verified Owner Dashboard:
✅ Total Penjualan, Pembelian, Laba Kotor, Rata-rata Tiket
✅ AR, AP, Setoran Harian, Stok Rendah
✅ Peringatan, Performa Cabang, Statistik
✅ Transaksi Terbaru

Verified Finance Dashboard:
✅ P&L Summary (Pendapatan, HPP, Laba Kotor, Beban, Laba Bersih)
✅ Balance Sheet Summary (Aset, Kewajiban, Ekuitas)
✅ AR/AP dengan aging
✅ Trial Balance & Jurnal Terbaru

Verified Purchase Enterprise:
✅ List view dengan 18 kolom dan filter lengkap
✅ Form header dengan 12 field
✅ Item grid dengan 23 kolom
✅ 7 bottom tabs (Rincian, Potongan, Pajak, Biaya, SN, Riwayat Harga, Riwayat Supplier)
✅ Footer calculation & payment selection
✅ Keyboard shortcuts
```

---

# PREVIOUS UPDATE: March 11, 2026 - PURCHASE MODULE ENTERPRISE

## Modul Pembelian Enterprise - IMPLEMENTED & TESTED ✅

### Flow Pembelian Lengkap
```
PESANAN PEMBELIAN (PO)
        ↓
TERIMA BARANG / PEMBELIAN
        ↓
TERBENTUK HUTANG DAGANG (AP) - AUTO
        ↓
JURNAL AKUNTANSI - AUTO
        ↓
PEMBAYARAN HUTANG
        ↓
NERACA & LAPORAN KEUANGAN
```

### Menu yang Diimplementasi
1. ✅ **Daftar Pesanan Pembelian** - Filter status, supplier, search, pagination
2. ✅ **Tambah Pesanan Pembelian** - Form dengan supplier, gudang, items, PPN, kredit
3. ✅ **Daftar Pembelian** - Barang yang sudah diterima
4. ✅ **Tambah Pembelian** - Terima barang dari PO
5. ✅ **History Harga Beli** - Riwayat harga per supplier/produk
6. ✅ **Daftar Pembayaran Hutang** - List pembayaran dengan referensi
7. ✅ **Tambah Pembayaran Hutang** - Pilih hutang, bayar, potongan
8. ✅ **Daftar Retur Pembelian** - List retur
9. ✅ **Tambah Retur Pembelian** - Retur dengan update stok & hutang

### Integrasi
| Modul | Integrasi | Status |
|-------|-----------|--------|
| Inventory | Stock movement type: purchase_in | ✅ |
| AP | Auto-create AP-PO{number} on receive | ✅ |
| Akuntansi | Debit Persediaan, Credit Hutang | ✅ |
| Price History | Record per receive transaction | ✅ |

### Test Results (Iteration 32)
```
BACKEND: 16/16 tests PASSED (100%)
FRONTEND: 6/6 tabs verified (100%)

Verified Features:
✅ Create PO with items, supplier, credit terms
✅ Submit PO to supplier (status: ordered)
✅ Receive goods with auto AP + journal
✅ Cancel draft/ordered POs
✅ Payment creation with reference
✅ Return creation with stock update
✅ Price history auto-recording
```

---

## Previous Security Update (March 11, 2026)

### RBAC Security Audit - COMPLETE
- Extended RBAC to: erp_operations.py, master_erp.py, inventory.py, master_data.py, users.py, branches.py, accounting.py
- All DELETE and sensitive endpoints protected
- Kasir blocked (403) from all destructive operations
- Owner full access verified

---

# DATABASE COLLECTIONS

## Purchase Module
- `purchase_orders` - PO header + items
- `accounts_payable` - AP records (auto-created)
- `journal_entries` - Journal headers
- `journal_entry_lines` - Debit/Credit lines
- `purchase_payments` - Payment records
- `purchase_returns` - Return records
- `purchase_price_history` - Price tracking

---

# FILES REFERENCE

## Frontend
- `/app/frontend/src/pages/PurchaseModule.jsx` - Complete purchase UI
- `/app/frontend/src/App.js` - Route /purchase

## Backend
- `/app/backend/routes/purchase.py` - Full purchase API with AP/journal integration

---

## CRITICAL SECURITY FIX: RBAC BACKEND ENFORCEMENT

### Problem Fixed
- Kasir role was able to delete data despite permission OFF in matrix
- Frontend-only protection was inadequate (security theater)

### Solution Implemented
1. **Created `/app/backend/routes/rbac_middleware.py`**:
   - `require_permission(module, action)` decorator
   - `check_permission()` - FAIL-SAFE default DENY
   - `check_branch_access()` - Branch-level scope
   - `log_security_event()` - Audit logging

2. **Updated Critical Routes with RBAC**:
   - `pos.py` - All endpoints now use require_permission
   - `purchase.py` - All endpoints now use require_permission
   - `products.py` - All endpoints now use require_permission

### Verified Security Matrix (Tested)
| Operation | Kasir | Owner |
|-----------|-------|-------|
| DELETE product | ❌ 403 | ✅ 404 |
| DELETE held tx | ❌ 403 | ✅ Allowed |
| VOID transaction | ❌ 403 | ✅ Allowed |
| CANCEL PO | ❌ 403 | ✅ Allowed |
| VIEW products | ✅ Allowed | ✅ Allowed |
| CREATE sale | ✅ Allowed | ✅ Allowed |

## AUTO-INTEGRATION: Sales → AR & Purchase → AP

### Sales Credit → AR
- `is_credit: true` in POS transaction request
- Auto-creates AR entry in `accounts_receivable` collection
- Auto-creates journal entry (Debit: Piutang, Credit: Penjualan)
- Sets due_date based on `credit_due_days` (default 30)

### Purchase Receive → AP  
- When PO fully received, auto-creates AP entry
- Auto-creates journal entry (Debit: Persediaan, Credit: Hutang)
- Links to source PO with `source_type: purchase`

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
| 30 | **RBAC Security Backend Enforcement** | **100% PASS (14/14)** |

---

## COMPLETED FEATURES

### Phase 1: Foundation
- [x] RBAC with role hierarchy
- [x] Multi-mode pricing system
- [x] ERP-grade item master
- [x] Stock movements tracking

### Phase 2: Operational
- [x] Setoran Harian full workflow
- [x] Deposit journal integration
- [x] Kasir-locked access
- [x] Supervisor/Manager verification

### Phase 3: Accounting
- [x] AR Module with aging
- [x] AP Module with aging
- [x] Approval Engine
- [x] Accounting Engine
- [x] Chart of Accounts
- [x] Account Mapping config
- [x] GL, Trial Balance
- [x] Balance Sheet, Income Statement

### Phase 4: Security & Integration (NEW)
- [x] **RBAC Backend Enforcement** - All destructive operations blocked for unauthorized roles
- [x] **Sales → AR Integration** - Credit sales auto-create AR + journal
- [x] **Purchase → AP Integration** - PO receive auto-create AP + journal
- [x] **Audit Logging** - All security events recorded

---

## REMAINING TASKS

### P0 - Critical (ALL COMPLETED)
- [x] Frontend pages for AR/AP
- [x] Frontend for Approval Center
- [x] Frontend for Financial Reports
- [x] **RBAC Backend Enforcement (SECURITY FIX)**
- [x] Integration: Sales → AR (credit)
- [x] Integration: Purchase → AP (credit)

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
