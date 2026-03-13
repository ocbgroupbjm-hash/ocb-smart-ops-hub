# OCB TITAN AI - ERP System PRD

## Original Problem Statement
Membangun sistem ERP retail komprehensif (OCB TITAN) dengan fitur POS, Inventory, Keuangan, dan Akuntansi. Sistem harus mengikuti standar ERP retail seperti iPOS/SAP B1/Odoo.

## Core Requirements
1. **Multi-tenant Architecture** - Support untuk multiple business units
2. **RBAC System** - Role-Based Access Control yang komprehensif
3. **Stock Single Source of Truth** - `stock_movements` sebagai satu-satunya sumber data stok
4. **Audit Trail** - Logging semua perubahan data penting
5. **Standard ERP UI** - Toolbar konsisten di semua modul

---

## What's Been Implemented

### Phase 1: System Architecture Control ✅
- **Stock SSOT**: `stock_movements` collection sebagai single source of truth
- **Owner Edit Control**: Sistem audit trail untuk edit data oleh owner
- **Recalculation Engine**: Auto-recalculate saat data di-edit
- **Module Cleanup**: Menyembunyikan modul tidak aktif dari UI

### Phase 2: RBAC & Cashier Flow Hardening ✅
- **Enforced Cashier Flow**: Login → Kontrol Kas → Buka Shift → Penjualan → Tutup Shift
- **Frontend Guards**: `KasirRouteGuard.jsx`, `useShiftGuard.js`
- **Permission Sync**: Sinkronisasi antara database, API, dan UI

### Phase 3: Transaction Engine Integration ✅
- **Discount/Promo Engine**: `discount_promo_engine.py`
- **Price Level Lookup**: Auto-lookup harga berdasarkan grup pelanggan
- **Owner Edit Button**: Tombol edit di PO, Sales, Master Items

### Phase 4: Standard ERP Toolbar ✅
**Completed (2026-03-13):**
- `ERPActionToolbar.jsx` - Komponen reusable
- `StockCardModal.jsx` - Modal kartu stok dari SSOT

**Master Data Modules:**
- Master Items - 7 tombol toolbar
- Master Suppliers - 3 tombol toolbar
- Master Customers - 3 tombol toolbar
- Master Categories - 3 tombol toolbar
- Master Brands - 3 tombol toolbar
- Master Units - 3 tombol toolbar
- Branches - 3 tombol + view switcher
- MasterWarehouses - 3 tombol toolbar

**Purchase Modules:**
- Purchase Orders - 6 tombol toolbar
- PurchaseList - 6 tombol (Tambah, Edit, Hapus, Print, Terima, Export)
- PurchaseReturns - 4 tombol (Tambah Retur, Edit, Hapus, Print)
- PurchasePriceHistory - Read-Only (Export, Print)

**Sales Modules:**
- SalesList - 5 tombol toolbar
- SalesOrderList - 5 tombol (Tambah Pesanan, Edit, Hapus, Print, Approve)
- CashierList - 5 tombol (Tambah Transaksi, Edit, Hapus, Print, Retur)
- TradeInList - 4 tombol (Tambah, Edit, Hapus, Print)
- ARPaymentsList - 4 tombol (Tambah Pembayaran, Edit, Hapus, Print)
- SalesReturnList - 4 tombol (Tambah Retur, Edit, Hapus, Print)
- SalesPriceHistory - Read-Only (Export, Print, Refresh)

**Accounting Modules (Batch 3 - 2026-03-13):**
- CashTransactions - 4 tombol (Tambah Transaksi, Edit, Hapus, Print)
- JournalEntries - 4 tombol (Tambah Jurnal, Edit, Hapus, Print)
- ChartOfAccounts - 4 tombol (Tambah Akun, Edit, Hapus, Print)

**Inventory Modules (Batch 5 - 2026-03-13):**
- StockMovements - 4 tombol (Tambah Movement, Edit, Hapus, Print) + row selection
- StockCards - 3 tombol (Refresh, Print Kartu Stok, Export Excel) + row selection
- StockTransfers - 4 tombol (Tambah, Edit, Hapus, Print)
- StockOpname - 6 tombol (Tambah Opname, Edit, Hapus, Print, Approve, + custom branch buttons)

**Bug Fixes (Batch 5 - 2026-03-13):**
- Fixed: User role_id null menyebabkan ERPActionToolbar tidak muncul
- Fixed: Login flow sekarang memastikan role_id selalu ada
- Fixed: Missing 'roles' collection export di database.py
- Added: DELETE /api/inventory/movements/{id} endpoint dengan reverse stock

**Bug Fixes (Batch 3-4 - 2026-03-13):**
- Fixed: AR Payment dropdown akun kas/bank kosong (endpoint /api/accounting/coa → /api/accounting/accounts)
- Fixed: RBAC middleware tidak bisa lookup role by role_code
- Fixed: Stock Opname icon rendering crash (Lucide icon passed as object instead of JSX)

**Database Initialization (Batch 4 - 2026-03-13):**
- Created `/app/backend/routes/database_init.py` - Service inisialisasi database
- Auto-init saat login: accounts, account_settings, numbering_settings, branches, company_profile, roles
- Endpoint: `/api/system/init-check` untuk verifikasi kesiapan database

**RBAC Validation (Batch 4 - 2026-03-13):**
- Owner role: Full access dengan permissions ['*']
- Kasir role: Limited - hanya POS, view products, tidak bisa delete master/edit jurnal
- RBAC middleware diperbaiki untuk support role_code lookup


### Phase 5: Multi-Tenant Blueprint System ✅
**Completed (2026-03-13):**
- `tenant_blueprint.py` - Tenant Blueprint & Migration Engine
- Blueprint Version: 1.0.0
- Migration Version: 1

**API Endpoints:**
- `GET /api/tenant/list` - Daftar semua tenant dengan status
- `POST /api/tenant/sync-all` - Sinkronisasi semua tenant
- `POST /api/tenant/create` - Buat tenant baru dengan blueprint lengkap
- `GET /api/tenant/health/{db}` - Cek kesehatan tenant

**Tenant Status (All Healthy):**
- ocb_titan: 17 accounts, 15 roles, 56 branches
- ocb_unit_4: 28 accounts, 7 roles, 1 branch
- ocb_unt_1: 22 accounts, 5 roles, 1 branch
- ocb_baju: 28 accounts, 7 roles, 1 branch
- ocb_counter: 28 accounts, 5 roles, 1 branch
- ocb_unit_test (NEW): 28 accounts, 5 roles, 1 branch

---

## Code Architecture

```
/app/
├── backend/
│   ├── routes/
│   │   ├── owner_control.py      # Owner edit & audit
│   │   ├── master_erp.py         # /calculate-pricing API
│   │   ├── pos.py                # Cashier shift validation
│   │   ├── sales_module.py       # Sales with shift validation
│   │   └── stock_card.py         # Stock card endpoints
│   └── services/
│       ├── stock_ssot.py         # Stock SSOT enforcement
│       ├── recalculation_engine.py
│       └── discount_promo_engine.py
└── frontend/
    └── src/
        ├── components/
        │   ├── ERPActionToolbar.jsx   # Standard toolbar
        │   ├── StockCardModal.jsx     # Stock card modal
        │   ├── KasirRouteGuard.jsx
        │   └── OwnerEditButton.jsx
        ├── hooks/
        │   └── useShiftGuard.js
        └── pages/
            ├── master/                 # All with toolbar
            ├── purchase/               # PO with toolbar
            ├── sales/                  # Sales with toolbar
            └── inventory/              # Transfers with toolbar
```

---

## Key API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/master/calculate-pricing` | POST | Calculate final pricing with discounts |
| `/api/owner/edit/{module}/{id}` | POST | Owner edit with audit trail |
| `/api/cash-control/check-shift` | GET | Check cashier active shift |
| `/api/inventory/stock-card-modal` | GET | Stock card data for modal |

---

## Database Collections
- `users` - User accounts with roles
- `permissions` - RBAC permission matrix
- `stock_movements` - **SSOT** for all stock
- `audit_log` - Edit history with old/new values
- `products` - Item master data
- `suppliers`, `customers` - Partner data
- `purchase_orders`, `sales_invoices` - Transactions

---

## Test Reports
- `/app/test_reports/iteration_52.json` - ERP Toolbar Batch 1 (100% PASS)
- `/app/test_reports/iteration_53.json` - ERP Toolbar Batch 2 - Purchase & Sales (100% PASS)
- `/app/test_reports/iteration_54.json` - ERP Toolbar Batch 3 - Accounting (100% PASS)
- `/app/test_reports/iteration_55.json` - RBAC, Stock Opname, DB Init (100% PASS)
- `/app/test_reports/iteration_56.json` - FINAL VALIDATION with Screenshots (100% PASS)
- `/app/test_reports/iteration_57.json` - Inventory Backend (100% PASS)
- `/app/test_reports/iteration_58.json` - Inventory Frontend Toolbar Fix (100% PASS)
- `/app/test_reports/iteration_59.json` - Multi-Tenant Blueprint System (100% PASS)

---

## Prioritized Backlog

### P0 - Critical ✅ COMPLETED
- [x] Kartu Stok Modal - Terimplementasi di Master Items
- [x] Standard Toolbar di semua modul Purchase & Sales
- [x] Standard Toolbar di modul Accounting (Kas, Jurnal, COA)
- [x] Fix dropdown Akun Kas/Bank di AR Payment
- [x] Stock Opname dengan ERPActionToolbar
- [x] Database Initialization Service
- [x] RBAC validation (Owner, Kasir)

### P1 - High Priority  
- [ ] Test jurnal AR Payment (double-entry Debit Kas, Credit Piutang)
- [ ] Export Excel implementation
- [ ] Print functionality implementation

### P2 - Medium Priority
- [ ] Import Excel untuk master data

### P3 - Future
- Phase 6: AI Business Engine (ON HOLD)

---

## UI Standards

### Toolbar Button Colors
| Action | Color | Class |
|--------|-------|-------|
| Tambah | Hijau | `bg-green-600` |
| Edit | Ungu | `bg-purple-600` |
| Hapus | Merah | `bg-red-600` |
| Duplikasi | Orange | `bg-orange-500` |
| Print | Biru | `bg-blue-600` |
| Approve | Cyan | `bg-cyan-600` |
| Terima | Teal | `bg-teal-600` |
| Kartu Stok | Amber | `bg-amber-600` |
| Import | Emerald | `bg-emerald-600` |
| Export | Sky | `bg-sky-600` |
| Retur | Rose | `bg-rose-600` |
| Disabled | Gray | `bg-gray-700/50` |

### Row Selection
- Klik baris = select (amber highlight)
- Radio button di kolom pertama
- Selection indicator di toolbar

---

## Credentials
- **Owner**: `ocbgroupbjm@gmail.com` / `admin123`
- **Business**: OCB GROUP

---

### Phase 6: Full System Audit ✅
**Completed (2026-03-13):**
- `AUDIT_MODUL_LENGKAP.md` v2.0 FINAL - Dokumen audit lengkap
- 108+ modul teridentifikasi dan dianalisa
- 10 bagian audit lengkap:
  1. Daftar lengkap modul dan sub modul
  2. Fungsi rinci masing-masing modul (Master, Purchase, Sales, Inventory, Accounting)
  3. Tabel audit duplikasi
  4. Status final per modul (KEEP/DELETE/HIDE/MERGE/HOLD)
  5. Struktur menu final ERP
  6. Rekomendasi tindakan
  7. Validasi kesesuaian roadmap
  8. Panduan penggunaan per modul
  9. Flow integrasi antar modul (6 flow diagram)
  10. Checklist implementasi cleanup

### Phase 7: Evidence-Based Cleanup Analysis ✅
**Completed (2026-03-13):**
- `CLEANUP_ANALYSIS_FINAL.md` - Analisis cleanup berbasis bukti teknis & bisnis

**Hasil Analisis Detail:**

#### A. KARTU STOK (3 file dianalisa)
| File | Keputusan | Alasan |
|------|-----------|--------|
| StockCards.jsx | KEEP | Overview stok realtime, ERPActionToolbar sudah ada |
| KartuStok.jsx | KEEP | Kartu stok akuntansi per periode, WAJIB untuk audit |
| MasterStockCards.jsx | DELETE | 100% duplikat dengan KartuStok, posisi salah di /master/ |

#### B. PURCHASE (2 file dianalisa)
| File | Keputusan | Alasan |
|------|-----------|--------|
| Purchase.jsx | DELETE | Subset dari PurchaseModule, tidak punya Payment/Return |
| PurchaseModule.jsx | KEEP | Enterprise module lengkap dengan 6 tab, Owner Edit |

#### C. WAR ROOM (2 file dianalisa)
| File | Keputusan | Alasan |
|------|-----------|--------|
| Warroom.jsx | KEEP | Monitoring basic stabil, API aktif |
| WarRoomV2.jsx | HIDE | Phase 6 (AI) HOLD, bisa diaktifkan kembali nanti |

### Phase 7.1: Cleanup Execution - PHASE A (HIDE) ✅
**Completed (2026-03-13):**

**8 Modul di-HIDE dari sidebar menu:**
1. WarRoomV2 - AI Tools submenu
2. AI War Room Super - AI Tools submenu
3. MasterItemTypes (Jenis Barang) - Master Data submenu
4. MasterDatasheet (Datasheet) - Master Data submenu
5. FinancialControl (Multi Tax Engine) - Akuntansi submenu
6. WarehouseControl (Branch Inventory Control) - top level
7. SerialNumbers - not in menu (already hidden)
8. ProductAssembly - not in menu (already hidden)

**File yang diubah:** `/app/frontend/src/components/layout/Sidebar.jsx`

### Phase 7.2: Cleanup Execution - PHASE B (DELETE) ✅
**Completed (2026-03-13):**

**2 File duplikat dihapus:**
1. `/app/frontend/src/pages/master/MasterStockCards.jsx` - DELETED
2. `/app/frontend/src/pages/Purchase.jsx` - DELETED

**Route redirects ditambahkan:**
- `/pembelian` → `/purchase` (Navigate component)
- `/master/stock-cards` → `/inventory/kartu-stok` (Navigate component)

**File yang diubah:**
- `/app/frontend/src/App.js` - import dan route
- `/app/frontend/src/pages/master/index.js` - export

**Test Report:** `/app/test_reports/iteration_60.json` - 100% PASS

### Kartu Stok - Keputusan Final

| Modul | Route | Fungsi | User Target | Status |
|-------|-------|--------|-------------|--------|
| **StockCards.jsx** | `/inventory/stock-cards` | Overview stok realtime dengan summary (aman/kritis/habis) | Gudang, kasir | KEEP |
| **KartuStok.jsx** | `/inventory/kartu-stok` | Kartu stok akuntansi per periode (bulan/tahun) dengan detail mutasi | Accounting, auditor | KEEP |
| ~~MasterStockCards.jsx~~ | ~~`/master/stock-cards`~~ | ~~Duplikat~~ | - | DELETED |

**Alasan dua modul tetap ada:**
- StockCards.jsx = monitoring realtime untuk operasional
- KartuStok.jsx = laporan akuntansi per periode untuk audit

---

### Phase 8: Multi-Tenant System Fix ✅
**Completed (2026-03-13):**

**Problem yang Diperbaiki:**
- Perubahan sistem hanya berlaku di `ocb_titan`, tenant lain tidak ikut update
- Collection wajib tidak ada di beberapa tenant
- User baru tidak punya `role_id` (menyebabkan gagal login)
- Blueprint version tidak sinkron antar tenant

**Solusi yang Diterapkan:**

1. **Blueprint Version Update: 1.0.0 → 2.0.0**
   - Ditambahkan daftar `REQUIRED_COLLECTIONS` (25 collection wajib)
   - Collection wajib otomatis dibuat jika tidak ada

2. **Global Tenant Sync (`sync_all_tenants()`)**
   - Menyinkronkan semua tenant database ke blueprint terbaru
   - Auto-create missing collections
   - Fix user `role_id` yang kosong
   - Update blueprint version

3. **API Endpoints Baru:**
   - `POST /api/tenant/sync-all` - Sync semua tenant
   - `GET /api/tenant/blueprint-status` - Status blueprint semua tenant
   - `POST /api/tenant/cleanup/{db_name}` - Hapus collection sampah

4. **Fix User Creation:**
   - `create_user` API sekarang auto-assign `role_id` dan `role_code`
   - User baru langsung bisa login tanpa masalah RBAC

**Hasil Sync:**
| Tenant | Blueprint | Collections | Status |
|--------|-----------|-------------|--------|
| ocb_titan | 2.0.0 | 126 | ✅ Healthy |
| ocb_unit_4 | 2.0.0 | 42 | ✅ Healthy |
| ocb_baju | 2.0.0 | 28 | ✅ Healthy |
| ocb_counter | 2.0.0 | 27 | ✅ Healthy |
| ocb_unt_1 | 2.0.0 | 29 | ✅ Healthy |
| ocb_unit_test | 2.0.0 | 27 | ✅ Healthy |
| ocb_test_clone | 2.0.0 | 28 | ✅ Healthy |
| ocb_ai_database | 2.0.0 | 42 | ✅ Healthy |

**Test Create User:**
- ✅ ocb_unit_4: User berhasil dibuat dengan role_id
- ✅ ocb_baju: User berhasil dibuat dengan role_id
- ✅ ocb_unt_1: User berhasil dibuat dengan role_id

**Files Updated:**
- `/app/backend/routes/tenant_blueprint.py` - Blueprint engine v2.0.0
- `/app/backend/routes/users.py` - Fix create_user dengan role_id

---

*Last Updated: 2026-03-13 (Phase 8 - Multi-Tenant System Fix Complete)*
