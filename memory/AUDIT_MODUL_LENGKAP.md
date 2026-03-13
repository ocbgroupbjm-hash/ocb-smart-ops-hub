# OCB TITAN AI - AUDIT TOTAL MODUL DAN SUB MODUL
## Dokumen Audit Sistem v1.0
## Tanggal: 2026-03-13

---

# BAGIAN 1 — DAFTAR LENGKAP MODUL DAN SUB MODUL

## A. DASHBOARD (3 sub modul)
1. Dashboard - Dashboard utama sistem
2. Owner Dashboard - Dashboard khusus pemilik
3. Finance Dashboard - Dashboard khusus keuangan

## B. MASTER DATA (21 sub modul)
1. Master Items - Daftar item/produk
2. Master Categories - Kategori produk
3. Master Units - Satuan produk
4. Master Brands - Merk produk
5. Master Warehouses - Gudang/cabang
6. Master Suppliers - Data supplier
7. Master Customers - Data pelanggan
8. Master Sales Persons - Data sales/pramuniaga
9. Master Customer Groups - Grup pelanggan
10. Master Regions - Wilayah/area
11. Master Banks - Data bank
12. Master E-Money - E-wallet/e-money
13. Master Shipping Costs - Ongkos kirim
14. Master Discounts - Diskon periode
15. Master Promotions - Promosi periode
16. Master Item Types - Jenis barang
17. Master Customer Points - Point pelanggan
18. Master Barcode - Cetak barcode
19. Master Stock Cards - Kartu stok (DUPLIKAT)
20. Master Datasheet - Datasheet item (DUPLIKAT?)
21. Setting Akun ERP - Mapping akun transaksi

## C. PEMBELIAN / PURCHASE (8 sub modul)
1. Purchase Orders - Pesanan pembelian
2. Purchase List - Daftar pembelian
3. Purchase Add/Enterprise - Tambah pembelian
4. Purchase Receiving - Penerimaan barang
5. Purchase Payments - Pembayaran hutang
6. Purchase Returns - Retur pembelian
7. Purchase Price History - History harga beli
8. Purchase Planning - Perencanaan pembelian

## D. PENJUALAN / SALES (14 sub modul)
1. Sales Order List - Pesanan penjualan
2. Sales Order Add - Tambah pesanan
3. Sales List - Daftar penjualan
4. Sales Add - Tambah penjualan
5. Cashier List - Daftar kasir/POS
6. Sales Price History - History harga jual
7. Trade In List - Tukar tambah
8. AR Payments List - Daftar pembayaran piutang
9. AR Payment Add - Tambah pembayaran piutang
10. Sales Return List - Retur penjualan
11. Sales Return Add - Tambah retur
12. Point Transaksi - Point per transaksi
13. Commission Payments - Pembayaran komisi
14. Deliveries List - Daftar pengiriman/DO

## E. INVENTORY / STOK (7 sub modul)
1. Stock List/Inventory - Daftar stok
2. Stock Cards - Kartu stok (DUPLIKAT dengan KartuStok)
3. Kartu Stok - Kartu stok (DUPLIKAT dengan StockCards)
4. Stock Movements - Stok masuk/keluar/mutasi
5. Stock Transfers - Transfer stok antar cabang
6. Stock Opname - Stock opname/adjustment
7. Serial Numbers - Nomor seri (ADVANCED)
8. Product Assembly - Rakitan produk (ADVANCED)

## F. AKUNTANSI / ACCOUNTING (12 sub modul)
1. Chart of Accounts - Daftar perkiraan
2. Cash Transactions - Kas masuk/keluar/transfer
3. Journal Entries - Jurnal umum
4. General Ledger - Buku besar
5. Trial Balance - Neraca saldo
6. Balance Sheet - Neraca
7. Income Statement - Laba rugi
8. Cash Flow - Arus kas
9. Accounts Receivable - Daftar piutang
10. Accounts Payable - Daftar hutang
11. Financial Reports - Laporan keuangan
12. Financial Control - Kontrol keuangan (ADVANCED)

## G. KAS / BANK (4 sub modul - menggunakan CashTransactions)
1. Kas Masuk - Cash In
2. Kas Keluar - Cash Out
3. Transfer Kas - Cash Transfer
4. Mutasi Kas - Cash Mutations

## H. OPERASIONAL (3 sub modul)
1. Setoran Harian - Setoran kasir ke bank
2. Selisih Kas - Laporan selisih kas
3. Cash Control - Kontrol kas harian

## I. HR / KEPEGAWAIAN (7 sub modul)
1. Employees - Data karyawan
2. Absensi - Absensi karyawan
3. Payroll - Penggajian manual
4. Payroll Auto - Penggajian otomatis
5. HR Management - Manajemen HR
6. Master Shifts - Shift kerja
7. Master Jabatan - Jabatan/posisi

## J. LAPORAN / REPORTS (7 sub modul)
1. Reports - Laporan umum
2. ERP Reports - Laporan ERP
3. Report Center - Pusat laporan
4. Tax Export - Export pajak
5. Data Export - Export data
6. Advanced Export - Export lanjutan
7. Import System - Import data

## K. PENGATURAN / SETTINGS (12 sub modul)
1. Users - Data pengguna
2. Roles/RBAC Management - Hak akses
3. Company Settings - Data perusahaan
4. Branches - Data cabang
5. Number Settings - Format nomor
6. Printer Settings - Pengaturan printer
7. Theme Settings - Tema tampilan
8. Import/Export Settings - Import export
9. Backup - Backup data
10. Activity Log - Log aktivitas
11. System Analysis - Analisis sistem
12. Business Manager - Kelola bisnis

## L. AI TOOLS (10 sub modul) - PHASE 6 ON HOLD
1. AI Business - AI Bisnis umum
2. Hallo AI - Chat AI
3. AI Sales - AI Penjualan
4. AI Command Center - Pusat komando AI
5. CRM AI - CRM dengan AI
6. AI Performance - AI Kinerja
7. AI War Room Super - War Room AI
8. CFO Dashboard - Dashboard CFO
9. KPI Dashboard - Dashboard KPI
10. KPI Performance - Kinerja KPI

## M. WAR ROOM (4 sub modul) - MONITORING
1. Warroom - War Room utama
2. War Room V2 - War Room versi 2 (DUPLIKAT)
3. War Room Alert Panel - Panel alert
4. Global Map - Peta global

## N. APPROVAL (1 sub modul)
1. Approval Center - Pusat persetujuan

## O. CONTROL MODULES (6 sub modul)
1. Credit Control - Kontrol kredit
2. Stock Reorder - Reorder stok
3. Warehouse Control - Kontrol gudang
4. Sales Target System - Target penjualan
5. Commission Engine - Engine komisi
6. ERP Hardening - Penguatan ERP

## P. LAINNYA (4 sub modul)
1. POS - Point of Sale
2. CRM - Customer Relationship Management
3. Analytics - Analitik
4. Knowledge Base - Basis pengetahuan

---

# BAGIAN 2 — FUNGSI RINCI MASING-MASING MODUL

## MASTER DATA

### 1. Master Items (MasterItems.jsx)
- **Fungsi utama**: Mengelola daftar produk/item yang dijual atau dibeli
- **Input**: Kode, nama, kategori, brand, satuan, supplier, harga beli, harga jual, min stok
- **Output**: Data item untuk transaksi pembelian, penjualan, stok
- **Terhubung ke**: Purchase, Sales, Inventory, Barcode, Stock Card, Accounting
- **Status**: WAJIB
- **Dipakai**: AKTIF
- **Duplikasi**: TIDAK

### 2. Master Categories (MasterCategories.jsx)
- **Fungsi utama**: Mengelola kategori produk
- **Input**: Kode, nama kategori
- **Output**: Kategori untuk filter dan grouping item
- **Terhubung ke**: Master Items
- **Status**: WAJIB
- **Dipakai**: AKTIF
- **Duplikasi**: TIDAK

### 3. Master Units (MasterUnits.jsx)
- **Fungsi utama**: Mengelola satuan produk
- **Input**: Kode, nama satuan, konversi
- **Output**: Satuan untuk pembelian dan penjualan
- **Terhubung ke**: Master Items, Purchase, Sales
- **Status**: WAJIB
- **Dipakai**: AKTIF
- **Duplikasi**: TIDAK

### 4. Master Brands (MasterBrands.jsx)
- **Fungsi utama**: Mengelola merk produk
- **Input**: Kode, nama merk
- **Output**: Merk untuk filter dan grouping item
- **Terhubung ke**: Master Items
- **Status**: OPSIONAL
- **Dipakai**: AKTIF
- **Duplikasi**: TIDAK

### 5. Master Warehouses (MasterWarehouses.jsx)
- **Fungsi utama**: Mengelola data gudang
- **Input**: Kode, nama, alamat, status warehouse
- **Output**: Lokasi penyimpanan untuk stok
- **Terhubung ke**: Inventory, Stock Transfers
- **Status**: WAJIB
- **Dipakai**: AKTIF
- **Duplikasi**: TUMPANG TINDIH dengan Branches

### 6. Master Suppliers (MasterSuppliers.jsx)
- **Fungsi utama**: Mengelola data supplier
- **Input**: Kode, nama, alamat, kontak, NPWP, term pembayaran
- **Output**: Data supplier untuk pembelian
- **Terhubung ke**: Purchase, AP
- **Status**: WAJIB
- **Dipakai**: AKTIF
- **Duplikasi**: TIDAK

### 7. Master Customers (MasterCustomers.jsx)
- **Fungsi utama**: Mengelola data pelanggan
- **Input**: Kode, nama, alamat, kontak, NPWP, limit kredit
- **Output**: Data pelanggan untuk penjualan
- **Terhubung ke**: Sales, AR, Credit Control
- **Status**: WAJIB
- **Dipakai**: AKTIF
- **Duplikasi**: TIDAK

### 8. Master Sales Persons (MasterSalesPersons.jsx)
- **Fungsi utama**: Mengelola data sales/pramuniaga
- **Input**: Kode, nama, target, komisi
- **Output**: Data sales untuk transaksi dan komisi
- **Terhubung ke**: Sales, Commission Engine
- **Status**: OPSIONAL
- **Dipakai**: AKTIF
- **Duplikasi**: TIDAK

### 9. Master Customer Groups (MasterCustomerGroups.jsx)
- **Fungsi utama**: Mengelola grup pelanggan
- **Input**: Kode, nama grup, diskon
- **Output**: Grup untuk price level
- **Terhubung ke**: Master Customers, Sales
- **Status**: OPSIONAL
- **Dipakai**: AKTIF
- **Duplikasi**: TIDAK

### 10. Master Regions (MasterRegions.jsx)
- **Fungsi utama**: Mengelola wilayah/area
- **Input**: Kode, nama wilayah, provinsi, kabupaten
- **Output**: Wilayah untuk pengiriman
- **Terhubung ke**: Master Customers, Shipping
- **Status**: OPSIONAL
- **Dipakai**: AKTIF
- **Duplikasi**: TIDAK

### 11. Master Banks (MasterBanks.jsx)
- **Fungsi utama**: Mengelola data bank
- **Input**: Kode, nama bank, rekening, saldo awal
- **Output**: Rekening untuk pembayaran
- **Terhubung ke**: Cash Transactions, Payments
- **Status**: WAJIB
- **Dipakai**: AKTIF
- **Duplikasi**: TIDAK

### 12. Master E-Money (MasterEmoney.jsx)
- **Fungsi utama**: Mengelola e-wallet
- **Input**: Kode, nama e-money, fee
- **Output**: Metode pembayaran digital
- **Terhubung ke**: POS, Sales
- **Status**: OPSIONAL
- **Dipakai**: AKTIF
- **Duplikasi**: TIDAK

### 13. Master Shipping Costs (MasterShippingCosts.jsx)
- **Fungsi utama**: Mengelola ongkos kirim
- **Input**: Wilayah asal, tujuan, berat, biaya
- **Output**: Tarif ongkir untuk penjualan
- **Terhubung ke**: Sales, Deliveries
- **Status**: OPSIONAL
- **Dipakai**: AKTIF
- **Duplikasi**: TIDAK

### 14. Master Discounts (MasterDiscounts.jsx)
- **Fungsi utama**: Mengelola diskon periode
- **Input**: Nama, periode, item, persentase/nominal
- **Output**: Diskon otomatis saat transaksi
- **Terhubung ke**: Sales, POS
- **Status**: OPSIONAL
- **Dipakai**: AKTIF
- **Duplikasi**: TIDAK

### 15. Master Promotions (MasterPromotions.jsx)
- **Fungsi utama**: Mengelola promosi periode
- **Input**: Nama, periode, syarat, hadiah
- **Output**: Promosi otomatis saat transaksi
- **Terhubung ke**: Sales, POS
- **Status**: OPSIONAL
- **Dipakai**: AKTIF
- **Duplikasi**: MIRIP dengan Discounts (perlu evaluasi)

### 16. Master Item Types (MasterItemTypes.jsx)
- **Fungsi utama**: Mengelola jenis barang
- **Input**: Kode, nama jenis
- **Output**: Tipe item (stok, jasa, non-stok)
- **Terhubung ke**: Master Items
- **Status**: OPSIONAL
- **Dipakai**: JARANG
- **Duplikasi**: TIDAK

### 17. Master Customer Points (MasterCustomerPoints.jsx)
- **Fungsi utama**: Mengelola aturan point pelanggan
- **Input**: Nama program, konversi rupiah ke point, expired
- **Output**: Point untuk loyalti
- **Terhubung ke**: Sales, Point Transaksi
- **Status**: OPSIONAL
- **Dipakai**: AKTIF
- **Duplikasi**: TIDAK

### 18. Master Barcode (MasterBarcode.jsx)
- **Fungsi utama**: Cetak label barcode
- **Input**: Item, template, jumlah
- **Output**: Label barcode untuk cetak
- **Terhubung ke**: Master Items
- **Status**: OPSIONAL PENTING
- **Dipakai**: AKTIF
- **Duplikasi**: TIDAK

### 19. Master Stock Cards (MasterStockCards.jsx)
- **Fungsi utama**: Menampilkan kartu stok
- **Input**: Item, cabang, periode
- **Output**: History pergerakan stok
- **Terhubung ke**: Inventory, Stock Movements
- **Status**: OPSIONAL
- **Dipakai**: JARANG
- **Duplikasi**: **DUPLIKAT** dengan StockCards dan KartuStok di Inventory

### 20. Master Datasheet (MasterDatasheet.jsx)
- **Fungsi utama**: Menampilkan datasheet item lengkap
- **Input**: Item
- **Output**: Spesifikasi lengkap item
- **Terhubung ke**: Master Items
- **Status**: OPSIONAL
- **Dipakai**: JARANG
- **Duplikasi**: **MUNGKIN DUPLIKAT** dengan detail item di Master Items

### 21. Setting Akun ERP (SettingAkunERP.jsx)
- **Fungsi utama**: Mapping akun transaksi ERP
- **Input**: Tipe transaksi, akun debit, akun kredit
- **Output**: Jurnal otomatis saat transaksi
- **Terhubung ke**: All transactions, Accounting
- **Status**: WAJIB
- **Dipakai**: AKTIF
- **Duplikasi**: TIDAK

---

## PEMBELIAN / PURCHASE

### 1. Purchase Orders (PurchaseOrders.jsx)
- **Fungsi utama**: Pesanan pembelian ke supplier
- **Input**: Supplier, item, qty, harga
- **Output**: PO untuk diterima
- **Terhubung ke**: Purchase Receiving, AP
- **Status**: WAJIB
- **Dipakai**: AKTIF
- **Duplikasi**: TIDAK

### 2. Purchase List (PurchaseList.jsx)
- **Fungsi utama**: Daftar pembelian/invoice pembelian
- **Input**: Filter tanggal, supplier
- **Output**: Daftar invoice pembelian
- **Terhubung ke**: Purchase Orders, AP
- **Status**: WAJIB
- **Dipakai**: AKTIF
- **Duplikasi**: TIDAK

### 3. Purchase Add/Enterprise (PurchaseEnterprise.jsx)
- **Fungsi utama**: Tambah invoice pembelian
- **Input**: Supplier, item, qty, harga, pajak
- **Output**: Invoice pembelian baru
- **Terhubung ke**: Inventory, AP, Journal
- **Status**: WAJIB
- **Dipakai**: AKTIF
- **Duplikasi**: TIDAK

### 4. Purchase Receiving (PurchaseReceiving.jsx)
- **Fungsi utama**: Penerimaan barang dari PO
- **Input**: PO, qty diterima
- **Output**: Good Receipt, stok bertambah
- **Terhubung ke**: Purchase Orders, Inventory
- **Status**: WAJIB
- **Dipakai**: AKTIF
- **Duplikasi**: TIDAK

### 5. Purchase Payments (PurchasePayments.jsx)
- **Fungsi utama**: Pembayaran hutang ke supplier
- **Input**: Invoice, nominal, akun bank
- **Output**: Pelunasan hutang
- **Terhubung ke**: AP, Cash, Journal
- **Status**: WAJIB
- **Dipakai**: AKTIF
- **Duplikasi**: TIDAK

### 6. Purchase Returns (PurchaseReturns.jsx)
- **Fungsi utama**: Retur pembelian
- **Input**: Invoice, item, qty retur
- **Output**: Nota retur, stok berkurang
- **Terhubung ke**: Purchase, Inventory, AP
- **Status**: WAJIB
- **Dipakai**: AKTIF
- **Duplikasi**: TIDAK

### 7. Purchase Price History (PurchasePriceHistory.jsx)
- **Fungsi utama**: History harga beli
- **Input**: Item, periode
- **Output**: Trend harga beli
- **Terhubung ke**: Purchase
- **Status**: OPSIONAL
- **Dipakai**: JARANG
- **Duplikasi**: TIDAK

### 8. Purchase Planning (PurchasePlanning.jsx)
- **Fungsi utama**: Perencanaan pembelian
- **Input**: Stok min, lead time
- **Output**: Rekomendasi PO
- **Terhubung ke**: Inventory, Purchase Orders
- **Status**: OPSIONAL ADVANCED
- **Dipakai**: JARANG
- **Duplikasi**: **TUMPANG TINDIH** dengan Stock Reorder

---

## PENJUALAN / SALES

### 1-14. (Detail serupa dengan Purchase - sudah ada ERPActionToolbar)

---

## INVENTORY

### 1. Stock List/Inventory (Inventory.jsx)
- **Fungsi utama**: Daftar stok semua item
- **Input**: Filter cabang, kategori
- **Output**: Daftar stok real-time
- **Terhubung ke**: All transactions
- **Status**: WAJIB
- **Dipakai**: AKTIF
- **Duplikasi**: TIDAK

### 2. Stock Cards (StockCards.jsx)
- **Fungsi utama**: Kartu stok per item
- **Input**: Item, cabang
- **Output**: History pergerakan stok
- **Terhubung ke**: Stock Movements
- **Status**: WAJIB
- **Dipakai**: AKTIF
- **Duplikasi**: **DUPLIKAT** dengan KartuStok dan MasterStockCards

### 3. Kartu Stok (KartuStok.jsx)
- **Fungsi utama**: Kartu stok (versi lain)
- **Input**: Item, cabang
- **Output**: History pergerakan stok
- **Terhubung ke**: Stock Movements
- **Status**: REDUNDANT
- **Dipakai**: JARANG
- **Duplikasi**: **DUPLIKAT** dengan StockCards - HARUS DIHAPUS

### 4. Stock Movements (StockMovements.jsx)
- **Fungsi utama**: Stok masuk/keluar manual
- **Input**: Item, qty, tipe movement
- **Output**: Perubahan stok
- **Terhubung ke**: Inventory, Journal
- **Status**: WAJIB
- **Dipakai**: AKTIF
- **Duplikasi**: TIDAK

### 5. Stock Transfers (StockTransfers.jsx)
- **Fungsi utama**: Transfer stok antar cabang
- **Input**: Cabang asal, tujuan, item, qty
- **Output**: Perpindahan stok
- **Terhubung ke**: Inventory
- **Status**: WAJIB
- **Dipakai**: AKTIF
- **Duplikasi**: TIDAK

### 6. Stock Opname (StockOpname.jsx)
- **Fungsi utama**: Pencocokan stok fisik vs sistem
- **Input**: Cabang, item, qty fisik
- **Output**: Selisih stok, adjustment
- **Terhubung ke**: Inventory, Journal
- **Status**: WAJIB
- **Dipakai**: AKTIF
- **Duplikasi**: TIDAK

### 7. Serial Numbers (SerialNumbers.jsx)
- **Fungsi utama**: Tracking nomor seri
- **Input**: Item, serial number
- **Output**: Tracking per unit
- **Terhubung ke**: Inventory, Sales
- **Status**: OPSIONAL ADVANCED
- **Dipakai**: JARANG
- **Duplikasi**: TIDAK

### 8. Product Assembly (ProductAssembly.jsx)
- **Fungsi utama**: Rakitan produk (BOM)
- **Input**: Komponen, hasil rakitan
- **Output**: Produk rakitan
- **Terhubung ke**: Inventory
- **Status**: OPSIONAL ADVANCED
- **Dipakai**: JARANG
- **Duplikasi**: TIDAK

---

# BAGIAN 3 — TABEL AUDIT DUPLIKASI

| Modul A | Modul B | Modul C | Fungsi Sama? | Keputusan |
|---------|---------|---------|--------------|-----------|
| StockCards | KartuStok | MasterStockCards | YA - Semua tampilkan kartu stok | **MERGE** ke StockCards, hapus sisanya |
| Purchase Planning | Stock Reorder | - | YA - Rekomendasi pembelian | **MERGE** ke Stock Reorder |
| Warroom | WarRoomV2 | AIWarRoomSuper | PARTIAL - Monitoring berbeda | **KEEP** Warroom, **HIDE** V2, **HOLD** AIWarRoom |
| Master Warehouses | Branches | - | PARTIAL - Gudang vs Cabang | **MERGE** ke Branches (cabang bisa punya gudang) |
| Master Discounts | Master Promotions | - | PARTIAL - Keduanya promo/diskon | **KEEP** keduanya (berbeda konsep) |
| Purchase | PurchaseModule | PurchaseEnterprise | PARTIAL - Entry pembelian | **MERGE** ke PurchaseEnterprise |
| Dashboard | ERPDashboard | OwnerDashboard | PARTIAL - Dashboard berbeda | **KEEP** sesuai role |
| Reports | ERPReports | ReportCenter | PARTIAL - Laporan berbeda | **MERGE** ke ReportCenter |
| Payroll | PayrollAuto | - | YA - Penggajian | **MERGE** ke Payroll (dengan mode auto) |
| DataExport | AdvancedExport | - | YA - Export data | **MERGE** ke AdvancedExport |
| CRM | CRMAI | - | PARTIAL - CRM dengan AI | **MERGE** ke CRM (fitur AI optional) |

---

# BAGIAN 4 — STATUS FINAL PER MODUL

| Modul | Status | Alasan |
|-------|--------|--------|
| **MASTER DATA** | | |
| MasterItems | KEEP | Fungsi inti |
| MasterCategories | KEEP | Fungsi inti |
| MasterUnits | KEEP | Fungsi inti |
| MasterBrands | KEEP | Fungsi pendukung |
| MasterWarehouses | MERGE→Branches | Tumpang tindih dengan Branches |
| MasterSuppliers | KEEP | Fungsi inti |
| MasterCustomers | KEEP | Fungsi inti |
| MasterSalesPersons | KEEP | Fungsi komisi |
| MasterCustomerGroups | KEEP | Fungsi price level |
| MasterRegions | KEEP | Fungsi pengiriman |
| MasterBanks | KEEP | Fungsi pembayaran |
| MasterEmoney | KEEP | Fungsi pembayaran |
| MasterShippingCosts | KEEP | Fungsi pengiriman |
| MasterDiscounts | KEEP | Fungsi berbeda dari Promotions |
| MasterPromotions | KEEP | Fungsi berbeda dari Discounts |
| MasterItemTypes | HIDE | Jarang dipakai |
| MasterCustomerPoints | KEEP | Fungsi loyalti |
| MasterBarcode | KEEP | Fungsi inti cetak |
| MasterStockCards | DELETE | Duplikat dengan StockCards |
| MasterDatasheet | HIDE | Jarang dipakai, bisa masuk detail item |
| SettingAkunERP | KEEP | Fungsi inti mapping akun |
| **PURCHASE** | | |
| PurchaseOrders | KEEP | Fungsi inti |
| PurchaseList | KEEP | Fungsi inti |
| PurchaseEnterprise | KEEP | Fungsi inti tambah |
| PurchaseReceiving | KEEP | Fungsi inti |
| PurchasePayments | KEEP | Fungsi inti |
| PurchaseReturns | KEEP | Fungsi inti |
| PurchasePriceHistory | KEEP | Fungsi analisis |
| PurchasePlanning | MERGE→StockReorder | Duplikat fungsi |
| Purchase.jsx | DELETE | Wrapper lama |
| PurchaseModule.jsx | DELETE | Wrapper lama |
| **INVENTORY** | | |
| Inventory | KEEP | Fungsi inti |
| StockCards | KEEP | Fungsi inti kartu stok |
| KartuStok | DELETE | Duplikat dengan StockCards |
| StockMovements | KEEP | Fungsi inti |
| StockTransfers | KEEP | Fungsi inti |
| StockOpname | KEEP | Fungsi inti |
| SerialNumbers | HIDE | Advanced, jarang dipakai |
| ProductAssembly | HIDE | Advanced, jarang dipakai |
| **SALES** | | |
| Semua modul Sales | KEEP | Sudah standar |
| **ACCOUNTING** | | |
| Semua modul Accounting | KEEP | Sudah standar |
| **AI TOOLS** | | |
| Semua modul AI | HOLD | Phase 6 - ON HOLD |
| **WAR ROOM** | | |
| Warroom | KEEP | Fungsi monitoring |
| WarRoomV2 | DELETE | Duplikat |
| WarRoomAlertPanel | MERGE→Warroom | Bisa digabung |
| AIWarRoomSuper | HOLD | Phase 6 |
| **CONTROL MODULES** | | |
| CreditControl | KEEP | Fungsi kontrol kredit |
| StockReorder | KEEP | Fungsi reorder (merge PurchasePlanning) |
| WarehouseControl | HIDE | Tumpang tindih dengan Inventory |
| SalesTargetSystem | KEEP | Fungsi target |
| CommissionEngine | KEEP | Fungsi komisi |
| CashControl | KEEP | Fungsi kontrol kas |
| ERPHardening | REWORK | Perlu evaluasi fungsi |
| **REPORTS** | | |
| Reports | MERGE→ReportCenter | Gabung ke pusat laporan |
| ERPReports | MERGE→ReportCenter | Gabung ke pusat laporan |
| ReportCenter | KEEP | Pusat laporan |
| **SETTINGS** | | |
| Semua Settings | KEEP | Sudah standar |

---

# BAGIAN 5 — STRUKTUR MENU FINAL ERP

```
OCB TITAN AI - MENU STRUCTURE

1. DASHBOARD
   ├── Dashboard Utama
   ├── Dashboard Owner (role: owner)
   └── Dashboard Keuangan (role: finance)

2. MASTER DATA
   ├── Daftar Item
   ├── Kategori
   ├── Satuan
   ├── Merk
   ├── Supplier
   ├── Pelanggan
   │   ├── Daftar Pelanggan
   │   ├── Grup Pelanggan
   │   └── Point Pelanggan
   ├── Sales/Pramuniaga
   ├── Cabang & Gudang (merged)
   ├── Bank
   ├── E-Money
   ├── Wilayah
   ├── Ongkos Kirim
   ├── Diskon Periode
   ├── Promosi Periode
   ├── Cetak Barcode
   └── Setting Akun ERP

3. PEMBELIAN
   ├── Pesanan Pembelian (PO)
   ├── Daftar Pembelian
   │   └── Tambah Pembelian
   ├── Penerimaan Barang
   ├── Retur Pembelian
   ├── History Harga Beli
   └── Pembayaran Hutang

4. PENJUALAN
   ├── Pesanan Penjualan (SO)
   │   └── Tambah Pesanan
   ├── Daftar Penjualan
   │   └── Tambah Penjualan
   ├── Kasir / POS
   ├── Tukar Tambah
   ├── Retur Penjualan
   ├── Pengiriman / DO
   ├── History Harga Jual
   ├── Point Transaksi
   └── Pembayaran Komisi

5. PIUTANG (AR)
   ├── Daftar Piutang
   ├── Pembayaran Piutang
   └── Aging Piutang

6. HUTANG (AP)
   ├── Daftar Hutang
   ├── Pembayaran Hutang
   └── Aging Hutang

7. INVENTORY
   ├── Daftar Stok
   ├── Kartu Stok
   ├── Stok Masuk/Keluar
   ├── Transfer Stok
   ├── Stock Opname
   └── Reorder Point

8. KAS / BANK
   ├── Kas Masuk
   ├── Kas Keluar
   ├── Transfer Kas
   ├── Setoran Harian
   └── Kontrol Kas

9. AKUNTANSI
   ├── Daftar Perkiraan (COA)
   ├── Jurnal Umum
   ├── Buku Besar
   ├── Neraca Saldo
   ├── Neraca
   ├── Laba Rugi
   ├── Arus Kas
   └── Kontrol Keuangan

10. LAPORAN
    ├── Laporan Penjualan
    ├── Laporan Pembelian
    ├── Laporan Stok
    ├── Laporan Keuangan
    ├── Laporan Kas
    ├── Laporan Piutang
    ├── Laporan Hutang
    ├── Export Pajak
    └── Export Data

11. HR / KEPEGAWAIAN
    ├── Data Karyawan
    ├── Absensi
    ├── Penggajian
    └── Target & Komisi

12. PENGATURAN
    ├── Data Pengguna
    ├── Hak Akses (RBAC)
    ├── Data Perusahaan
    ├── Cabang
    ├── Format Nomor
    ├── Printer & Struk
    ├── Kelola Bisnis
    └── Log Aktivitas

13. WAR ROOM (MONITORING)
    ├── Dashboard Monitor
    └── Alert Panel

14. AI TOOLS (PHASE 6 - HOLD)
    ├── AI Business
    ├── AI Chat
    ├── AI Sales
    ├── AI CFO
    └── AI War Room
```

---

# BAGIAN 6 — REKOMENDASI TINDAKAN

## HAPUS SEGERA (DELETE)
1. `KartuStok.jsx` - Duplikat dengan StockCards
2. `MasterStockCards.jsx` - Duplikat dengan StockCards
3. `WarRoomV2.jsx` - Duplikat dengan Warroom
4. `Purchase.jsx` - Wrapper lama
5. `PurchaseModule.jsx` - Wrapper lama
6. `SetoranHarian_old.jsx` - File lama

## SEMBUNYIKAN (HIDE)
1. `MasterItemTypes.jsx` - Jarang dipakai
2. `MasterDatasheet.jsx` - Jarang dipakai
3. `SerialNumbers.jsx` - Advanced
4. `ProductAssembly.jsx` - Advanced
5. `WarehouseControl.jsx` - Tumpang tindih

## GABUNG (MERGE)
1. `PurchasePlanning` → `StockReorder`
2. `MasterWarehouses` → `Branches`
3. `Reports + ERPReports` → `ReportCenter`
4. `Payroll + PayrollAuto` → `Payroll`
5. `DataExport + AdvancedExport` → `AdvancedExport`
6. `CRM + CRMAI` → `CRM`
7. `WarRoomAlertPanel` → `Warroom`

## HOLD (Phase 6)
1. Semua modul AI
2. AIWarRoomSuper
3. KPIDashboard
4. AIPerformance

---

# BAGIAN 7 — VALIDASI KESESUAIAN ROADMAP

| Modul | Sesuai Roadmap? | Terhubung? | Keputusan |
|-------|-----------------|------------|-----------|
| Master Data | ✅ YA | ✅ YA | KEEP |
| Purchase | ✅ YA | ✅ YA | KEEP |
| Sales | ✅ YA | ✅ YA | KEEP |
| Inventory | ✅ YA | ✅ YA | KEEP |
| Accounting | ✅ YA | ✅ YA | KEEP |
| HR/Payroll | ✅ YA | ✅ YA | KEEP |
| Reports | ✅ YA | ✅ YA | KEEP (merge) |
| AI Tools | ⏸️ HOLD | - | HOLD |
| War Room | ✅ YA | ✅ YA | KEEP (clean) |

---

*Dokumen ini dibuat secara otomatis oleh sistem audit OCB TITAN AI*
*Tanggal: 2026-03-13*
*Version: 1.0*
