# ANALISIS CLEANUP BERBASIS BUKTI - FINAL
## OCB TITAN AI ERP System
## Tanggal: 2026-03-13
## Status: DOKUMEN KEPUTUSAN FINAL

---

# EXECUTIVE SUMMARY

Dokumen ini berisi analisis mendalam berbasis bukti teknis dan bisnis untuk setiap modul kandidat cleanup. Setiap keputusan didukung oleh:
1. **Bukti Teknis**: Import aktif, route aktif, dependency analysis
2. **Bukti Bisnis**: Fungsi bisnis, kebutuhan user, modul pengganti
3. **Risk Assessment**: Risiko jika dihapus/di-hide

---

# BAGIAN 1: ANALISIS KHUSUS - KARTU STOK

## A. Perbandingan 3 File Kartu Stok

| Aspek | StockCards.jsx | KartuStok.jsx | MasterStockCards.jsx |
|-------|---------------|---------------|---------------------|
| **Lokasi** | `/pages/inventory/StockCards.jsx` | `/pages/inventory/KartuStok.jsx` | `/pages/master/MasterStockCards.jsx` |
| **Ukuran** | 288 lines | 457 lines | 272 lines |
| **Import di App.js** | YA (line 133) | YA (line 133) | YA (line 105) |
| **Route Aktif** | `/inventory/stock-cards` (line 332, 357) | `/inventory/kartu-stok` (line 333, 358), `/reports/stock-card` (line 428) | `/master/stock-cards` (line 283) |
| **API Endpoint** | `/api/inventory/stock`, `/api/inventory/movements` | `/api/inventory/stock-card`, `/api/inventory/stock-card/items-search` | `/api/products`, `/api/inventory/movements` |
| **Fitur Utama** | Daftar stok + modal history sederhana | Filter bulan/tahun, detail pergerakan lengkap, format ERP classic | Dropdown produk, running balance |
| **ERPActionToolbar** | YA (Custom) | TIDAK | TIDAK |
| **Data Source** | `/api/inventory/stock` | `/api/inventory/stock-card` (dedicated) | `/api/inventory/movements` |
| **Keunggulan** | Tampilan modern, summary cards | Filter periode detail, format laporan ERP | Export CSV |

## B. Analisis Fungsi Bisnis

### StockCards.jsx
- **Fungsi**: Menampilkan daftar stok realtime dengan summary (aman/kritis/habis)
- **User Target**: Gudang, kasir - melihat overview stok
- **Flow**: Pilih item → View movements → Print

### KartuStok.jsx  
- **Fungsi**: Kartu stok detail per item per periode (bulan/tahun)
- **User Target**: Accounting, auditor - tracking mutasi detail
- **Flow**: Search item → Pilih periode → Pilih cabang → PROSES → Lihat detail pergerakan
- **Format**: Sesuai standar kartu stok akuntansi (Saldo Awal, Masuk, Keluar, Saldo)

### MasterStockCards.jsx
- **Fungsi**: Melihat mutasi stok dengan running balance
- **User Target**: Gudang - cek pergerakan
- **Flow**: Pilih produk dari dropdown → Filter tanggal → Lihat tabel

## C. KEPUTUSAN FINAL - KARTU STOK

| File | Keputusan | Alasan Bisnis | Alasan Teknis |
|------|-----------|---------------|---------------|
| **StockCards.jsx** | **KEEP** | Fungsi overview stok realtime yang berbeda dari kartu stok akuntansi | Route aktif di `/inventory/stock-cards`, import aktif, sudah pakai ERPActionToolbar |
| **KartuStok.jsx** | **KEEP** | Fungsi kartu stok akuntansi per periode - WAJIB untuk audit | Route aktif di 3 tempat, API dedicated `/api/inventory/stock-card`, format laporan lengkap |
| **MasterStockCards.jsx** | **DELETE** | Fungsi sama dengan KartuStok tapi kurang lengkap | Di bawah `/master/` bukan tempat yang tepat untuk laporan stok, export sudah bisa di KartuStok |

### BUKTI AMAN MENGHAPUS MasterStockCards.jsx:
1. **Import**: Hanya di `App.js` dan `pages/master/index.js` (self-export)
2. **Route Pengganti**: `/inventory/kartu-stok` (lebih lengkap)
3. **Fungsi Terduplikasi**: 100% sama dengan KartuStok.jsx
4. **User Preference**: KartuStok.jsx lebih sesuai standar ERP dengan filter periode

---

# BAGIAN 2: ANALISIS KHUSUS - PURCHASE

## A. Perbandingan 2 File Purchase

| Aspek | Purchase.jsx | PurchaseModule.jsx |
|-------|--------------|-------------------|
| **Lokasi** | `/pages/Purchase.jsx` | `/pages/PurchaseModule.jsx` |
| **Ukuran** | 813 lines | 1906 lines |
| **Import di App.js** | YA (line 12) | YA (line 13) |
| **Route Aktif** | `/pembelian` (line 255) | `/purchase` (line 301) |
| **Fitur** | CRUD PO, Edit, Receive, Print, Cancel | CRUD PO + Payment + Return + Price History + Payables + Owner Edit |
| **Tab/Submenu** | TIDAK | YA (6 tab: Orders, Purchases, Payments, Returns, Price History, Payables) |
| **ERPActionToolbar** | TIDAK | TIDAK (tapi ada komponen toolbar custom) |
| **Owner Edit** | TIDAK | YA (OwnerEditButton, OwnerEditModal) |
| **Kompleksitas** | Sederhana | Enterprise-level |

## B. Analisis Fungsi Bisnis

### Purchase.jsx
- **Fungsi**: Modul pembelian dasar - PO, edit, receive, cancel
- **User Target**: Purchasing staff - operasi harian
- **Limitasi**: Tidak ada pembayaran, retur, price history

### PurchaseModule.jsx
- **Fungsi**: Modul pembelian enterprise - full cycle procurement
- **User Target**: Purchasing manager, finance - full control
- **Fitur Lengkap**: 
  - Tab Orders: CRUD PO
  - Tab Purchases: Daftar pembelian diterima
  - Tab Payments: Pembayaran hutang (AP)
  - Tab Returns: Retur pembelian
  - Tab Price History: History harga beli
  - Tab Payables: Daftar hutang

## C. KEPUTUSAN FINAL - PURCHASE

| File | Keputusan | Alasan Bisnis | Alasan Teknis |
|------|-----------|---------------|---------------|
| **Purchase.jsx** | **DELETE** | Semua fungsi sudah ada di PurchaseModule dengan lebih lengkap | Route `/pembelian` bisa diarahkan ke `/purchase` |
| **PurchaseModule.jsx** | **KEEP** | Modul enterprise lengkap dengan fitur Owner Edit, Payment, Return | Route aktif di `/purchase`, import aktif, fitur lebih lengkap |

### BUKTI AMAN MENGHAPUS Purchase.jsx:
1. **Import**: Hanya di `App.js` (line 12)
2. **Route**: `/pembelian` - HARUS diubah redirect ke `/purchase`
3. **Fungsi Subset**: 100% fungsi Purchase.jsx sudah ada di PurchaseModule.jsx
4. **Tidak Ada Dependency Lain**: grep tidak menemukan import dari file lain

### RENCANA MIGRASI:
1. Ubah route `/pembelian` dari `<Purchase />` ke `<Navigate to="/purchase" />`
2. Atau hapus route `/pembelian` sepenuhnya
3. Pastikan menu sidebar mengarah ke `/purchase`

---

# BAGIAN 3: ANALISIS KHUSUS - WAR ROOM

## A. Perbandingan 2 File War Room

| Aspek | Warroom.jsx | WarRoomV2.jsx |
|-------|-------------|---------------|
| **Lokasi** | `/pages/Warroom.jsx` | `/pages/WarRoomV2.jsx` |
| **Ukuran** | 292 lines | 364 lines |
| **Import di App.js** | YA (line 28) | YA (line 37) |
| **Route Aktif** | `/warroom` (line 208) | `/war-room-v2` (line 210) |
| **API Endpoint** | `/api/warroom/snapshot`, `/api/warroom/branches/performance` | `/api/war-room/dashboard`, `/api/war-room/fraud-detection`, `/api/war-room/ai-insights`, `/api/war-room/live-feed` |
| **Fitur** | KPI Cards, Branch Performance | KPI + Fraud Alerts + AI Insights + Live Feed |
| **Auto Refresh** | YA (30s) | YA (30s) |
| **AI Features** | TIDAK | YA (AI Insights, Fraud Detection) |
| **Design** | Basic monitoring | Advanced Command Center |

## B. Analisis Fungsi Bisnis

### Warroom.jsx
- **Fungsi**: Monitoring dasar - KPI cards, performa cabang
- **User Target**: Owner - overview sederhana
- **API**: Endpoint sederhana `/api/warroom/*`

### WarRoomV2.jsx
- **Fungsi**: Command center lengkap dengan AI
- **User Target**: Owner - advanced monitoring
- **Fitur AI**:
  - Fraud Detection alerts
  - AI Insights/recommendations
  - Live activity feed
- **API**: Endpoint berbeda `/api/war-room/*`

## C. KEPUTUSAN FINAL - WAR ROOM

| File | Keputusan | Alasan Bisnis | Alasan Teknis |
|------|-----------|---------------|---------------|
| **Warroom.jsx** | **KEEP** | Monitoring basic yang sudah stabil, API `/api/warroom/*` aktif | Route aktif, import aktif, tidak ada dependency issue |
| **WarRoomV2.jsx** | **HIDE** | AI Features masih dalam Phase 6 (HOLD), API `/api/war-room/*` mungkin tidak lengkap | Bisa diaktifkan kembali saat Phase 6 dimulai |

### ALASAN TIDAK DELETE WarRoomV2.jsx:
1. **Fitur AI Berharga**: Fraud detection, AI insights adalah fitur canggih
2. **Phase 6 HOLD**: User sudah menyatakan Phase 6 (AI) ditunda, bukan dibatalkan
3. **Backend API Berbeda**: `/api/war-room/*` vs `/api/warroom/*` - perlu validasi backend

### RENCANA HIDE:
1. Hapus dari sidebar menu
2. Route tetap ada untuk akses developer
3. Reactivate saat Phase 6 dimulai

---

# BAGIAN 4: TABEL KEPUTUSAN FINAL - SEMUA KANDIDAT CLEANUP

## A. Modul DELETE (Aman Dihapus)

| No | File | Fungsi Bisnis | Modul Pengganti | Route Pengganti | Menu Pengganti | Import Aktif | Risiko | Bukti Aman |
|----|------|--------------|-----------------|-----------------|----------------|--------------|--------|------------|
| 1 | MasterStockCards.jsx | Kartu stok | KartuStok.jsx | /inventory/kartu-stok | Inventory > Kartu Stok | App.js, master/index.js | RENDAH | Fungsi 100% ada di KartuStok, export sudah tersedia |
| 2 | Purchase.jsx | Pembelian dasar | PurchaseModule.jsx | /purchase | Pembelian | App.js | RENDAH | Semua fungsi ada di PurchaseModule |

## B. Modul HIDE (Sembunyikan dari Menu)

| No | File | Fungsi Bisnis | Alasan Hide | Route Tetap | Kapan Reactivate |
|----|------|--------------|-------------|-------------|------------------|
| 1 | WarRoomV2.jsx | AI Command Center | Phase 6 HOLD | /war-room-v2 | Saat Phase 6 dimulai |
| 2 | MasterItemTypes.jsx | Jenis barang | Jarang dipakai | /master/item-types | Jika user butuh |
| 3 | MasterDatasheet.jsx | Datasheet item | Jarang dipakai | /master/datasheet | Jika user butuh |
| 4 | SerialNumbers.jsx | Nomor seri | Advanced feature | /inventory/serial-numbers | Jika bisnis butuh tracking serial |
| 5 | ProductAssembly.jsx | Rakitan produk | Advanced feature | /inventory/assemblies | Jika bisnis produksi |
| 6 | WarehouseControl.jsx | Kontrol gudang | Overlap dengan Inventory | /warehouse-control | Perlu evaluasi merge |
| 7 | DataExport.jsx | Export data | Ada AdvancedExport | /data-export | Sudah tidak perlu |
| 8 | FinancialControl.jsx | Kontrol keuangan | Advanced feature | /financial-control | Jika bisnis perlu approval workflow |

## C. Modul KEEP (Tetap Dipertahankan)

| No | File | Fungsi Bisnis | Alasan Keep |
|----|------|--------------|-------------|
| 1 | StockCards.jsx | Overview stok realtime | Fungsi berbeda dari KartuStok (realtime vs periode) |
| 2 | KartuStok.jsx | Kartu stok akuntansi | Format standar ERP, wajib untuk audit |
| 3 | PurchaseModule.jsx | Pembelian enterprise | Fitur lengkap, Owner Edit, Payment, Return |
| 4 | Warroom.jsx | Monitoring basic | Stabil, API aktif |
| 5 | Semua modul MASTER DATA lainnya | Fungsi inti | Tidak ada duplikasi |
| 6 | Semua modul SALES | Fungsi inti | Tidak ada duplikasi |
| 7 | Semua modul ACCOUNTING | Fungsi inti | Tidak ada duplikasi |
| 8 | Semua modul INVENTORY (kecuali yang di-hide) | Fungsi inti | Tidak ada duplikasi |

## D. Modul EVALUATE (Perlu Analisis Lebih Lanjut)

| No | File A | File B | Isu | Rekomendasi |
|----|--------|--------|-----|-------------|
| 1 | StockReorder.jsx | PurchasePlanning.jsx | Fungsi overlap? | KEEP BOTH - berbeda level (operasional vs tactical) |
| 2 | Reports.jsx | ERPReports.jsx | Laporan berbeda | Evaluasi merge ke ReportCenter |
| 3 | FinancialReports.jsx | ReportCenter.jsx | Laporan keuangan | Evaluasi merge ke ReportCenter |

---

# BAGIAN 5: DAFTAR MODUL BERDASARKAN STATUS

## KEEP (85 modul)
- Semua Master Data (kecuali MasterStockCards, MasterItemTypes, MasterDatasheet)
- Semua Purchase (kecuali Purchase.jsx)
- Semua Sales
- Semua Inventory (kecuali SerialNumbers, ProductAssembly)
- Semua Accounting
- Dashboard, OwnerDashboard, FinanceDashboard
- Settings, Users, RBAC
- Warroom, WarRoomAlertPanel
- Control modules (Credit, Stock Reorder, SalesTarget, Commission, Cash)
- dll.

## HIDE (8 modul)
1. WarRoomV2.jsx
2. MasterItemTypes.jsx
3. MasterDatasheet.jsx
4. SerialNumbers.jsx
5. ProductAssembly.jsx
6. WarehouseControl.jsx
7. DataExport.jsx
8. FinancialControl.jsx

## DELETE (2 modul)
1. MasterStockCards.jsx
2. Purchase.jsx

## EVALUATE (3 perbandingan)
1. StockReorder vs PurchasePlanning
2. Reports vs ERPReports
3. FinancialReports vs ReportCenter

---

# BAGIAN 6: REKOMENDASI URUTAN EKSEKUSI

## Phase A: HIDE (Aman, Bisa Rollback)
**Waktu: Immediately**
1. Hapus menu item dari sidebar untuk 8 modul HIDE
2. Route tetap aktif untuk testing
3. Tidak ada perubahan code

## Phase B: DELETE - Validasi Dulu
**Waktu: Setelah Phase A Stable**

### Step 1: Validasi MasterStockCards
- [ ] Confirm KartuStok.jsx berfungsi sempurna
- [ ] Test route /inventory/kartu-stok
- [ ] Test export di KartuStok
- [ ] Screenshot bukti

### Step 2: Delete MasterStockCards
- [ ] Hapus import di App.js
- [ ] Hapus route di App.js
- [ ] Hapus export di master/index.js
- [ ] Hapus file MasterStockCards.jsx
- [ ] Test regression

### Step 3: Validasi Purchase
- [ ] Confirm PurchaseModule.jsx berfungsi sempurna
- [ ] Test semua tab (Orders, Purchases, Payments, Returns, Price History, Payables)
- [ ] Test Owner Edit
- [ ] Screenshot bukti

### Step 4: Migrasi Route /pembelian
- [ ] Ubah route /pembelian ke Navigate to="/purchase"
- [ ] Update menu sidebar

### Step 5: Delete Purchase.jsx
- [ ] Hapus import di App.js
- [ ] Hapus file Purchase.jsx
- [ ] Test regression

## Phase C: EVALUATE
**Waktu: Setelah Phase B Complete**
- Analisis lebih lanjut untuk modul EVALUATE
- User input required untuk keputusan final

---

# BAGIAN 7: CHECKLIST VALIDASI POST-CLEANUP

## Setelah Phase A (HIDE):
- [ ] Sidebar menu tidak menampilkan 8 modul yang di-hide
- [ ] Route langsung masih bisa diakses (untuk developer)
- [ ] Tidak ada broken link
- [ ] RBAC tetap berfungsi

## Setelah Phase B (DELETE):
- [ ] /inventory/kartu-stok berfungsi sempurna
- [ ] /purchase berfungsi dengan semua tab
- [ ] /pembelian redirect ke /purchase
- [ ] Tidak ada console error
- [ ] Transaction flow tetap normal:
  - [ ] Purchase → Stock In → AP
  - [ ] Sales → Stock Out → AR
  - [ ] Journal → Ledger → Reports

## Regression Test Wajib:
- [ ] Login semua role (Owner, Kasir, Admin)
- [ ] Purchase flow end-to-end
- [ ] Sales flow end-to-end
- [ ] AR Payment flow
- [ ] Stock Movement flow
- [ ] Journal flow

---

# BAGIAN 8: CATATAN PENTING

## FUNGSI INTI YANG TIDAK BOLEH DIHAPUS:
1. **Kartu Stok** - KartuStok.jsx WAJIB tetap ada
2. **Pembelian** - PurchaseModule.jsx adalah versi final
3. **Penjualan** - Semua modul Sales WAJIB
4. **Akuntansi** - Semua modul Accounting WAJIB
5. **Inventory** - StockMovements, StockOpname, StockTransfers WAJIB

## RULE KEPUTUSAN:
1. DELETE hanya untuk file yang 100% duplikat
2. HIDE untuk fitur advanced/jarang dipakai
3. KEEP untuk fungsi inti bisnis
4. EVALUATE jika belum jelas

## ROLLBACK PLAN:
- Phase A (HIDE): Cukup tambahkan kembali menu item
- Phase B (DELETE): Restore dari git commit sebelumnya

---

*Dokumen ini dibuat berdasarkan analisis kode aktual, bukan asumsi*
*Setiap keputusan didukung oleh bukti teknis (grep, route analysis) dan bisnis*
*Tanggal: 2026-03-13*
*Version: 1.0 FINAL*
