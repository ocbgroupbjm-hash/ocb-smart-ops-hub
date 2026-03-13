# OCB TITAN AI - AUDIT TOTAL MODUL DAN SUB MODUL
## Dokumen Audit Sistem v2.0 FINAL
## Tanggal: 2026-03-13
## Status: FINAL - SIAP UNTUK EKSEKUSI

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

## E. INVENTORY / STOK (8 sub modul)
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
- **Fungsi utama**: Membuat pesanan pembelian ke supplier
- **Input**: Supplier, item, qty, harga, tanggal kirim
- **Output**: PO untuk diterima, Outstanding PO
- **Terhubung ke**: Purchase Receiving, Inventory, AP
- **Status**: WAJIB
- **Dipakai**: AKTIF
- **Duplikasi**: TIDAK

### 2. Purchase List (PurchaseList.jsx)
- **Fungsi utama**: Daftar pembelian/invoice pembelian
- **Input**: Filter tanggal, supplier, status
- **Output**: Daftar invoice pembelian lengkap
- **Terhubung ke**: Purchase Orders, AP, Inventory
- **Status**: WAJIB
- **Dipakai**: AKTIF
- **Duplikasi**: TIDAK

### 3. Purchase Add/Enterprise (PurchaseEnterprise.jsx)
- **Fungsi utama**: Tambah invoice pembelian langsung
- **Input**: Supplier, item, qty, harga, pajak, diskon
- **Output**: Invoice pembelian baru, Update stok, Hutang baru
- **Terhubung ke**: Inventory, AP, Journal (otomatis)
- **Status**: WAJIB
- **Dipakai**: AKTIF
- **Duplikasi**: TIDAK

### 4. Purchase Receiving (PurchaseReceiving.jsx)
- **Fungsi utama**: Penerimaan barang dari PO
- **Input**: PO, qty diterima, kondisi barang
- **Output**: Good Receipt, stok bertambah, status PO updated
- **Terhubung ke**: Purchase Orders, Inventory, Stock Movements
- **Status**: WAJIB
- **Dipakai**: AKTIF
- **Duplikasi**: TIDAK

### 5. Purchase Payments (PurchasePayments.jsx)
- **Fungsi utama**: Pembayaran hutang ke supplier
- **Input**: Invoice, nominal, akun bank, tanggal bayar
- **Output**: Pelunasan hutang, Jurnal pembayaran
- **Terhubung ke**: AP, Cash/Bank, Journal
- **Status**: WAJIB
- **Dipakai**: AKTIF
- **Duplikasi**: TIDAK

### 6. Purchase Returns (PurchaseReturns.jsx)
- **Fungsi utama**: Retur pembelian ke supplier
- **Input**: Invoice, item, qty retur, alasan
- **Output**: Nota retur, stok berkurang, hutang berkurang
- **Terhubung ke**: Purchase, Inventory, AP, Journal
- **Status**: WAJIB
- **Dipakai**: AKTIF
- **Duplikasi**: TIDAK

### 7. Purchase Price History (PurchasePriceHistory.jsx)
- **Fungsi utama**: History harga beli per item per supplier
- **Input**: Item, supplier, periode
- **Output**: Trend harga beli (READ-ONLY)
- **Terhubung ke**: Purchase
- **Status**: OPSIONAL
- **Dipakai**: JARANG
- **Duplikasi**: TIDAK

### 8. Purchase Planning (PurchasePlanning.jsx)
- **Fungsi utama**: Perencanaan pembelian berdasarkan stok
- **Input**: Stok min, lead time, reorder point
- **Output**: Rekomendasi PO
- **Terhubung ke**: Inventory, Purchase Orders
- **Status**: OPSIONAL ADVANCED
- **Dipakai**: JARANG
- **Duplikasi**: **TUMPANG TINDIH** dengan Stock Reorder (perlu analisa)

---

## PENJUALAN / SALES

### 1. Sales Order List (SalesOrderList.jsx)
- **Fungsi utama**: Daftar pesanan penjualan (SO)
- **Input**: Filter keyword, gudang, tanggal
- **Output**: Daftar pesanan dengan status (Draft, Pending, Confirmed, Completed)
- **Terhubung ke**: Sales Order Add, Deliveries, AR
- **Status**: WAJIB
- **Dipakai**: AKTIF
- **Duplikasi**: TIDAK
- **ERPActionToolbar**: YA (Tambah, Edit, Hapus, Print, Approve)

### 2. Sales Order Add (SalesOrderAdd.jsx)
- **Fungsi utama**: Membuat pesanan penjualan baru
- **Input**: Pelanggan, item, qty, harga, tanggal kirim, sales person
- **Output**: SO baru, Reserved stock
- **Terhubung ke**: Sales Order List, Inventory, Customers
- **Status**: WAJIB
- **Dipakai**: AKTIF
- **Duplikasi**: TIDAK

### 3. Sales List (SalesList.jsx)
- **Fungsi utama**: Daftar invoice penjualan
- **Input**: Filter keyword, gudang, tanggal, status
- **Output**: Daftar invoice dengan summary (total, dibayar)
- **Terhubung ke**: Sales Add, AR, Journal
- **Status**: WAJIB
- **Dipakai**: AKTIF
- **Duplikasi**: TIDAK
- **ERPActionToolbar**: YA (Tambah, Edit, Hapus, Print, Retur)

### 4. Sales Add (SalesAdd.jsx)
- **Fungsi utama**: Membuat invoice penjualan
- **Input**: Pelanggan, item, qty, harga, diskon, pajak, cara bayar
- **Output**: Invoice, Update stok, Piutang/Kas masuk, Jurnal
- **Terhubung ke**: Inventory, AR, Cash, Journal
- **Status**: WAJIB
- **Dipakai**: AKTIF
- **Duplikasi**: TIDAK

### 5. Cashier List (CashierList.jsx)
- **Fungsi utama**: Riwayat transaksi kasir/POS
- **Input**: Filter keyword, tanggal, status pending
- **Output**: Daftar transaksi POS dengan summary
- **Terhubung ke**: POS, Sales Returns
- **Status**: WAJIB
- **Dipakai**: AKTIF
- **Duplikasi**: TIDAK
- **ERPActionToolbar**: YA (Tambah Transaksi, Edit, Hapus, Print, Retur)

### 6. Sales Price History (SalesPriceHistory.jsx)
- **Fungsi utama**: History harga jual per pelanggan per item
- **Input**: Item range, tanggal, pelanggan
- **Output**: Trend harga jual (READ-ONLY)
- **Terhubung ke**: Sales
- **Status**: OPSIONAL
- **Dipakai**: JARANG
- **Duplikasi**: TIDAK
- **Toolbar**: Export, Print, Refresh (read-only module)

### 7. Trade In List (TradeInList.jsx)
- **Fungsi utama**: Transaksi tukar tambah
- **Input**: Pelanggan, item masuk, item keluar, selisih
- **Output**: Transaksi tukar tambah (total masuk, keluar, selisih)
- **Terhubung ke**: Inventory, Sales
- **Status**: OPSIONAL
- **Dipakai**: AKTIF
- **Duplikasi**: TIDAK
- **ERPActionToolbar**: YA (Tambah, Edit, Hapus, Print)

### 8. AR Payments List (ARPaymentsList.jsx)
- **Fungsi utama**: Daftar pembayaran piutang dari pelanggan
- **Input**: Filter keyword, tanggal
- **Output**: Daftar pembayaran dengan summary (count, potongan, total)
- **Terhubung ke**: AR, Cash/Bank, Journal
- **Status**: WAJIB
- **Dipakai**: AKTIF
- **Duplikasi**: TIDAK
- **ERPActionToolbar**: YA (Tambah Pembayaran, Edit, Hapus, Print)

### 9. AR Payment Add (ARPaymentAdd.jsx)
- **Fungsi utama**: Mencatat pembayaran piutang
- **Input**: Pelanggan, invoice, nominal, potongan, akun kas/bank
- **Output**: Pembayaran tercatat, AR berkurang, Jurnal (Debit Kas, Kredit Piutang)
- **Terhubung ke**: AR, Cash/Bank, Journal
- **Status**: WAJIB
- **Dipakai**: AKTIF
- **Duplikasi**: TIDAK

### 10. Sales Return List (SalesReturnList.jsx)
- **Fungsi utama**: Daftar retur penjualan
- **Input**: Filter keyword, tanggal
- **Output**: Daftar nota retur dengan summary
- **Terhubung ke**: Sales, Inventory, AR
- **Status**: WAJIB
- **Dipakai**: AKTIF
- **Duplikasi**: TIDAK
- **ERPActionToolbar**: YA (Tambah Retur, Edit, Hapus, Print)

### 11. Sales Return Add (SalesReturnAdd.jsx)
- **Fungsi utama**: Membuat nota retur penjualan
- **Input**: Invoice, item, qty retur, alasan
- **Output**: Nota retur, Stok bertambah, Piutang berkurang, Jurnal
- **Terhubung ke**: Sales, Inventory, AR, Journal
- **Status**: WAJIB
- **Dipakai**: AKTIF
- **Duplikasi**: TIDAK

### 12. Point Transaksi (PointTransaksi.jsx)
- **Fungsi utama**: Tracking point pelanggan per transaksi
- **Input**: Pelanggan, periode
- **Output**: Daftar point per transaksi, sisa point
- **Terhubung ke**: Sales, Master Customer Points
- **Status**: OPSIONAL
- **Dipakai**: AKTIF
- **Duplikasi**: TIDAK
- **Aksi**: Ambil Point, Hapus Ambil Point

### 13. Commission Payments List (CommissionPaymentsList.jsx)
- **Fungsi utama**: Pembayaran komisi ke sales
- **Input**: Filter keyword, tanggal
- **Output**: Daftar pembayaran komisi
- **Terhubung ke**: Sales Persons, Cash, Journal
- **Status**: OPSIONAL
- **Dipakai**: AKTIF
- **Duplikasi**: TIDAK

### 14. Deliveries List (DeliveriesList.jsx)
- **Fungsi utama**: Daftar pengiriman/DO
- **Input**: Filter keyword, resi, kurir, status
- **Output**: Daftar DO dengan tracking
- **Terhubung ke**: Sales Orders, Customers
- **Status**: OPSIONAL
- **Dipakai**: AKTIF
- **Duplikasi**: TIDAK

### 15. Tax Export (TaxExport.jsx)
- **Fungsi utama**: Export faktur pajak keluaran (CSV/XML)
- **Input**: Format, jenis faktur, periode, filter taxable
- **Output**: File CSV/XML untuk e-Faktur DJP
- **Terhubung ke**: Sales Invoices
- **Status**: WAJIB (untuk PKP)
- **Dipakai**: AKTIF
- **Duplikasi**: TIDAK

---

## INVENTORY / STOK

### 1. Stock List / Inventory (Inventory.jsx)
- **Fungsi utama**: Daftar stok semua item real-time
- **Input**: Filter cabang, kategori, keyword
- **Output**: Daftar stok per item per cabang
- **Terhubung ke**: All transactions (Purchase, Sales, Transfer)
- **Status**: WAJIB
- **Dipakai**: AKTIF
- **Duplikasi**: TIDAK

### 2. Stock Cards (StockCards.jsx)
- **Fungsi utama**: Kartu stok per item - history pergerakan
- **Input**: Item, cabang, periode
- **Output**: Daftar mutasi stok (masuk, keluar, saldo)
- **Terhubung ke**: Stock Movements, Purchase, Sales
- **Status**: WAJIB
- **Dipakai**: AKTIF
- **Duplikasi**: **DUPLIKAT** dengan KartuStok dan MasterStockCards
- **ERPActionToolbar**: YA (Refresh, Print Kartu Stok, Export Excel)

### 3. Kartu Stok (KartuStok.jsx)
- **Fungsi utama**: Kartu stok (versi lain)
- **Input**: Item, cabang
- **Output**: History pergerakan stok
- **Terhubung ke**: Stock Movements
- **Status**: REDUNDANT
- **Dipakai**: JARANG
- **Duplikasi**: **DUPLIKAT** dengan StockCards - HARUS DIHAPUS

### 4. Stock Movements (StockMovements.jsx)
- **Fungsi utama**: Pencatatan stok masuk/keluar manual
- **Input**: Item, qty, tipe (in/out), alasan, referensi
- **Output**: Perubahan stok, Jurnal adjustment
- **Terhubung ke**: Inventory, Journal
- **Status**: WAJIB
- **Dipakai**: AKTIF
- **Duplikasi**: TIDAK
- **ERPActionToolbar**: YA (Tambah Movement, Edit, Hapus, Print)

### 5. Stock Transfers (StockTransfers.jsx)
- **Fungsi utama**: Transfer stok antar cabang/gudang
- **Input**: Cabang asal, cabang tujuan, item, qty
- **Output**: Stok berkurang di asal, bertambah di tujuan
- **Terhubung ke**: Inventory, Branches
- **Status**: WAJIB
- **Dipakai**: AKTIF
- **Duplikasi**: TIDAK
- **ERPActionToolbar**: YA (Tambah, Edit, Hapus, Print)

### 6. Stock Opname (StockOpname.jsx)
- **Fungsi utama**: Pencocokan stok fisik vs sistem
- **Input**: Cabang, tanggal opname, item, qty fisik
- **Output**: Selisih stok, Adjustment movement, Jurnal
- **Terhubung ke**: Inventory, Stock Movements, Journal
- **Status**: WAJIB
- **Dipakai**: AKTIF
- **Duplikasi**: TIDAK
- **ERPActionToolbar**: YA (Tambah Opname, Edit, Hapus, Print, Approve)

### 7. Serial Numbers (SerialNumbers.jsx)
- **Fungsi utama**: Tracking nomor seri per unit item
- **Input**: Item, serial number, status
- **Output**: Tracking per unit untuk warranty/service
- **Terhubung ke**: Inventory, Sales
- **Status**: OPSIONAL ADVANCED
- **Dipakai**: JARANG
- **Duplikasi**: TIDAK

### 8. Product Assembly (ProductAssembly.jsx)
- **Fungsi utama**: Rakitan produk (BOM - Bill of Material)
- **Input**: Komponen, qty per komponen, hasil rakitan
- **Output**: Produk rakitan dari komponen
- **Terhubung ke**: Inventory
- **Status**: OPSIONAL ADVANCED
- **Dipakai**: JARANG
- **Duplikasi**: TIDAK

---

## AKUNTANSI / ACCOUNTING

### 1. Chart of Accounts (ChartOfAccounts.jsx)
- **Fungsi utama**: Daftar akun perkiraan (COA)
- **Input**: Kode, nama, kategori (aset/kewajiban/modal/pendapatan/beban), tipe (header/detail), saldo normal
- **Output**: Master akun untuk jurnal
- **Terhubung ke**: All transactions, Journal, Reports
- **Status**: WAJIB
- **Dipakai**: AKTIF
- **Duplikasi**: TIDAK
- **ERPActionToolbar**: YA (Tambah Akun, Edit, Hapus, Print)
- **Summary Cards**: Aset, Kewajiban, Modal, Pendapatan, Beban

### 2. Cash Transactions (CashTransactions.jsx)
- **Fungsi utama**: Transaksi kas masuk/keluar/transfer
- **Input**: Tanggal, tipe (cash_in/cash_out/transfer), akun, jumlah, keterangan
- **Output**: Mutasi kas, Jurnal otomatis
- **Terhubung ke**: COA, Journal
- **Status**: WAJIB
- **Dipakai**: AKTIF
- **Duplikasi**: TIDAK
- **ERPActionToolbar**: YA (Tambah Transaksi, Edit, Hapus, Print)
- **Summary**: Kas Masuk, Kas Keluar, Saldo Bersih

### 3. Journal Entries (JournalEntries.jsx)
- **Fungsi utama**: Jurnal umum - pencatatan double-entry
- **Input**: Tanggal, referensi, keterangan, detail (akun, debit, kredit)
- **Output**: Jurnal dengan multiple line, Validasi balance
- **Terhubung ke**: COA, General Ledger
- **Status**: WAJIB
- **Dipakai**: AKTIF
- **Duplikasi**: TIDAK
- **ERPActionToolbar**: YA (Tambah Jurnal, Edit, Hapus, Print)
- **Fitur Khusus**: Validasi seimbang, Alert jurnal tidak seimbang

### 4. General Ledger (GeneralLedger.jsx)
- **Fungsi utama**: Buku besar - history transaksi per akun
- **Input**: Filter akun, periode
- **Output**: Daftar transaksi per akun dengan running balance
- **Terhubung ke**: COA, Journal
- **Status**: WAJIB
- **Dipakai**: AKTIF
- **Duplikasi**: TIDAK
- **Mode**: READ-ONLY (report)
- **Fitur**: Expandable per akun

### 5. Trial Balance (TrialBalance.jsx)
- **Fungsi utama**: Neraca saldo - ringkasan saldo semua akun
- **Input**: Filter periode
- **Output**: Daftar akun dengan saldo debit/kredit, Total, Status seimbang
- **Terhubung ke**: COA, Journal
- **Status**: WAJIB
- **Dipakai**: AKTIF
- **Duplikasi**: TIDAK
- **Mode**: READ-ONLY (report)
- **Fitur**: Validasi Balance, Export, Print

### 6. Balance Sheet (BalanceSheet.jsx)
- **Fungsi utama**: Neraca - laporan posisi keuangan
- **Input**: Per tanggal
- **Output**: Aset vs (Kewajiban + Modal), Status seimbang
- **Terhubung ke**: COA, Journal
- **Status**: WAJIB
- **Dipakai**: AKTIF
- **Duplikasi**: TIDAK
- **Mode**: READ-ONLY (report)
- **Layout**: 2 kolom (Aset | Kewajiban + Modal)

### 7. Income Statement (IncomeStatement.jsx)
- **Fungsi utama**: Laporan laba rugi
- **Input**: Periode (dari - sampai)
- **Output**: Pendapatan - Beban = Laba/Rugi Bersih
- **Terhubung ke**: COA, Journal
- **Status**: WAJIB
- **Dipakai**: AKTIF
- **Duplikasi**: TIDAK
- **Mode**: READ-ONLY (report)
- **Summary Cards**: Total Pendapatan, Total Beban, Laba/Rugi Bersih

### 8. Cash Flow (CashFlow.jsx)
- **Fungsi utama**: Laporan arus kas
- **Input**: Periode (dari - sampai)
- **Output**: Arus kas operasional, investasi, pendanaan, total bersih
- **Terhubung ke**: Cash Transactions, Journal
- **Status**: WAJIB
- **Dipakai**: AKTIF
- **Duplikasi**: TIDAK
- **Mode**: READ-ONLY (report)
- **Layout**: 3 kolom (Operasional | Investasi | Pendanaan)

### 9. Accounts Receivable (AccountsReceivable.jsx)
- **Fungsi utama**: Daftar piutang dagang (AR)
- **Input**: Filter keyword, customer, status, overdue
- **Output**: Daftar piutang dengan aging, summary
- **Terhubung ke**: Sales, AR Payments, Journal
- **Status**: WAJIB
- **Dipakai**: AKTIF
- **Duplikasi**: TIDAK
- **Fitur Khusus**: Aging report (Current, 1-30, 31-60, 61-90, >90 hari)
- **Aksi**: View Detail, Bayar

### 10. Accounts Payable (AccountsPayable.jsx)
- **Fungsi utama**: Daftar hutang dagang (AP)
- **Input**: Filter keyword, supplier, status
- **Output**: Daftar hutang dengan aging, summary
- **Terhubung ke**: Purchase, AP Payments, Journal
- **Status**: WAJIB
- **Dipakai**: AKTIF
- **Duplikasi**: TIDAK
- **Fitur Khusus**: Aging report (Current, 1-30, 31-60, 61-90, >90 hari)
- **Aksi**: View Detail, Bayar

### 11. Financial Reports (FinancialReports.jsx)
- **Fungsi utama**: Pusat laporan keuangan
- **Input**: Pilih jenis laporan, periode
- **Output**: Berbagai laporan keuangan
- **Terhubung ke**: All accounting modules
- **Status**: OPSIONAL
- **Dipakai**: AKTIF
- **Duplikasi**: MUNGKIN OVERLAP dengan individual reports

### 12. Financial Control (FinancialControl.jsx)
- **Fungsi utama**: Kontrol dan approval transaksi keuangan
- **Input**: Transaksi pending approval
- **Output**: Approved/Rejected transactions
- **Terhubung ke**: Journal, Cash
- **Status**: OPSIONAL ADVANCED
- **Dipakai**: JARANG
- **Duplikasi**: TIDAK

---

# BAGIAN 3 — TABEL AUDIT DUPLIKASI

| Modul A | Modul B | Modul C | Fungsi Sama? | Keputusan |
|---------|---------|---------|--------------|-----------|
| StockCards | KartuStok | MasterStockCards | YA - Semua tampilkan kartu stok | **MERGE** ke StockCards, hapus sisanya |
| Purchase Planning | Stock Reorder | - | PARTIAL - Lihat analisa | **ANALISA DULU** sebelum merge |
| Warroom | WarRoomV2 | AIWarRoomSuper | PARTIAL - Monitoring berbeda | **KEEP** Warroom, **HIDE** V2, **HOLD** AIWarRoom |
| Master Warehouses | Branches | - | PARTIAL - Gudang vs Cabang | **KEEP BOTH** (cabang bisa punya multi gudang) |
| Master Discounts | Master Promotions | - | PARTIAL - Keduanya promo/diskon | **KEEP** keduanya (berbeda konsep) |
| Purchase.jsx | PurchaseModule.jsx | PurchaseEnterprise | YA - Entry pembelian | **KEEP** PurchaseEnterprise, **DELETE** wrapper lama |
| Dashboard | ERPDashboard | OwnerDashboard | PARTIAL - Dashboard berbeda | **KEEP** sesuai role |
| Reports | ERPReports | ReportCenter | PARTIAL - Laporan berbeda | **EVALUATE** untuk merge ke ReportCenter |
| Payroll | PayrollAuto | - | PARTIAL - Mode berbeda | **KEEP** Payroll (tambah mode auto) |
| DataExport | AdvancedExport | - | YA - Export data | **KEEP** AdvancedExport, **HIDE** DataExport |
| CRM | CRMAI | - | PARTIAL - CRM dengan AI | **KEEP** CRM, **HOLD** CRMAI (Phase 6) |

---

# BAGIAN 4 — STATUS FINAL PER MODUL

| Modul | Status | Alasan |
|-------|--------|--------|
| **MASTER DATA** | | |
| MasterItems | KEEP | Fungsi inti |
| MasterCategories | KEEP | Fungsi inti |
| MasterUnits | KEEP | Fungsi inti |
| MasterBrands | KEEP | Fungsi pendukung |
| MasterWarehouses | KEEP | Tetap terpisah dari Branches |
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
| MasterDatasheet | HIDE | Jarang dipakai |
| SettingAkunERP | KEEP | Fungsi inti mapping akun |
| **PURCHASE** | | |
| PurchaseOrders | KEEP | Fungsi inti |
| PurchaseList | KEEP | Fungsi inti |
| PurchaseEnterprise | KEEP | Fungsi inti tambah |
| PurchaseReceiving | KEEP | Fungsi inti |
| PurchasePayments | KEEP | Fungsi inti |
| PurchaseReturns | KEEP | Fungsi inti |
| PurchasePriceHistory | KEEP | Fungsi analisis |
| PurchasePlanning | EVALUATE | Perlu analisa vs StockReorder |
| Purchase.jsx | DELETE | Wrapper lama |
| PurchaseModule.jsx | DELETE | Wrapper lama |
| **SALES** | | |
| SalesOrderList | KEEP | Fungsi inti |
| SalesOrderAdd | KEEP | Fungsi inti |
| SalesList | KEEP | Fungsi inti |
| SalesAdd | KEEP | Fungsi inti |
| CashierList | KEEP | Fungsi inti |
| SalesPriceHistory | KEEP | Fungsi analisis |
| TradeInList | KEEP | Fungsi khusus |
| ARPaymentsList | KEEP | Fungsi inti |
| ARPaymentAdd | KEEP | Fungsi inti |
| SalesReturnList | KEEP | Fungsi inti |
| SalesReturnAdd | KEEP | Fungsi inti |
| PointTransaksi | KEEP | Fungsi loyalti |
| CommissionPaymentsList | KEEP | Fungsi komisi |
| DeliveriesList | KEEP | Fungsi pengiriman |
| TaxExport | KEEP | Fungsi pajak |
| **INVENTORY** | | |
| Inventory | KEEP | Fungsi inti |
| StockCards | KEEP | Fungsi inti kartu stok |
| KartuStok | DELETE | Duplikat dengan StockCards |
| StockMovements | KEEP | Fungsi inti |
| StockTransfers | KEEP | Fungsi inti |
| StockOpname | KEEP | Fungsi inti |
| SerialNumbers | HIDE | Advanced, jarang dipakai |
| ProductAssembly | HIDE | Advanced, jarang dipakai |
| **ACCOUNTING** | | |
| ChartOfAccounts | KEEP | Fungsi inti |
| CashTransactions | KEEP | Fungsi inti |
| JournalEntries | KEEP | Fungsi inti |
| GeneralLedger | KEEP | Fungsi inti |
| TrialBalance | KEEP | Fungsi inti |
| BalanceSheet | KEEP | Fungsi inti |
| IncomeStatement | KEEP | Fungsi inti |
| CashFlow | KEEP | Fungsi inti |
| AccountsReceivable | KEEP | Fungsi inti |
| AccountsPayable | KEEP | Fungsi inti |
| FinancialReports | EVALUATE | Mungkin merge ke ReportCenter |
| FinancialControl | HIDE | Advanced |
| **AI TOOLS** | | |
| Semua modul AI | HOLD | Phase 6 - ON HOLD |
| **WAR ROOM** | | |
| Warroom | KEEP | Fungsi monitoring |
| WarRoomV2 | DELETE | Duplikat |
| WarRoomAlertPanel | KEEP | Fungsi alert |
| AIWarRoomSuper | HOLD | Phase 6 |
| **CONTROL MODULES** | | |
| CreditControl | KEEP | Fungsi kontrol kredit |
| StockReorder | KEEP | Fungsi reorder |
| WarehouseControl | HIDE | Tumpang tindih dengan Inventory |
| SalesTargetSystem | KEEP | Fungsi target |
| CommissionEngine | KEEP | Fungsi komisi |
| CashControl | KEEP | Fungsi kontrol kas |
| ERPHardening | KEEP | Fungsi periode/multi-currency |
| **REPORTS** | | |
| Reports | EVALUATE | Mungkin merge ke ReportCenter |
| ERPReports | EVALUATE | Mungkin merge ke ReportCenter |
| ReportCenter | KEEP | Pusat laporan |
| **SETTINGS** | | |
| Semua Settings | KEEP | Sudah standar |

---

# BAGIAN 5 — STRUKTUR MENU FINAL ERP

```
OCB TITAN AI - MENU STRUCTURE v2.0

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
   ├── Gudang
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
   └── Arus Kas

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

## PHASE A - HIDE DULU (Aman, tidak merusak sistem)
1. `MasterItemTypes.jsx` - Jarang dipakai, hide dari menu
2. `MasterDatasheet.jsx` - Jarang dipakai, hide dari menu
3. `SerialNumbers.jsx` - Advanced feature, hide
4. `ProductAssembly.jsx` - Advanced feature, hide
5. `WarehouseControl.jsx` - Tumpang tindih dengan Inventory
6. `DataExport.jsx` - Sudah ada AdvancedExport
7. `FinancialControl.jsx` - Advanced feature, hide

## PHASE B - PERLU VALIDASI SEBELUM DELETE
1. `KartuStok.jsx` - Validasi: StockCards sudah berfungsi penuh
2. `MasterStockCards.jsx` - Validasi: StockCards sudah berfungsi penuh
3. `WarRoomV2.jsx` - Validasi: Warroom sudah cukup
4. `Purchase.jsx` - Validasi: Tidak ada import aktif
5. `PurchaseModule.jsx` - Validasi: Tidak ada import aktif

## PHASE C - PERLU ANALISA MENDALAM
### Stock Reorder vs Purchase Planning

| Aspek | Stock Reorder | Purchase Planning |
|-------|--------------|-------------------|
| **Fungsi** | Rekomendasi item perlu beli | Perencanaan & generate PO |
| **Input** | Min stok, reorder point | Lead time, demand forecast |
| **Output** | Alert reorder | Draft PO |
| **User** | Gudang/Purchasing | Purchasing Manager |
| **Level** | Operasional | Tactical |

**Keputusan**: 
- Jika fungsi 100% sama → MERGE ke Stock Reorder
- Jika sequential flow → KEEP BOTH dengan link
- Sementara: KEEP BOTH sampai user konfirmasi

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
| Reports | ✅ YA | ✅ YA | KEEP (evaluate merge) |
| AI Tools | ⏸️ HOLD | - | HOLD |
| War Room | ✅ YA | ✅ YA | KEEP (clean duplicates) |

---

# BAGIAN 8 — PANDUAN PENGGUNAAN PER MODUL

## MASTER DATA

### Master Items
- **Siapa yang memakai**: Admin, Purchasing, Gudang
- **Kapan dipakai**: Setup awal, tambah produk baru
- **Langkah pakai**:
  1. Klik "Tambah" di toolbar
  2. Isi kode, nama, kategori, satuan
  3. Set harga beli dan harga jual
  4. Set minimum stok untuk reorder alert
  5. Simpan
- **Hasil yang diharapkan**: Item tersedia untuk transaksi
- **Modul terkait**: Categories, Units, Brands, Purchase, Sales, Inventory
- **Risiko jika salah**: Item tidak muncul di transaksi, harga salah

### Master Suppliers
- **Siapa yang memakai**: Admin, Purchasing
- **Kapan dipakai**: Tambah supplier baru
- **Langkah pakai**:
  1. Klik "Tambah" di toolbar
  2. Isi kode, nama, alamat, kontak
  3. Set NPWP jika PKP
  4. Set term pembayaran (hari)
  5. Simpan
- **Hasil yang diharapkan**: Supplier tersedia untuk PO dan pembelian
- **Modul terkait**: Purchase Orders, Purchase, AP
- **Risiko jika salah**: Supplier tidak muncul di dropdown

### Master Customers
- **Siapa yang memakai**: Admin, Sales
- **Kapan dipakai**: Tambah pelanggan baru
- **Langkah pakai**:
  1. Klik "Tambah" di toolbar
  2. Isi kode, nama, alamat, kontak
  3. Set NPWP jika PKP
  4. Set limit kredit
  5. Pilih grup pelanggan (opsional)
  6. Simpan
- **Hasil yang diharapkan**: Pelanggan tersedia untuk penjualan
- **Modul terkait**: Customer Groups, Sales, AR, Credit Control
- **Risiko jika salah**: Pelanggan tidak muncul, limit kredit tidak berfungsi

---

## PURCHASE

### Purchase Orders
- **Siapa yang memakai**: Purchasing
- **Kapan dipakai**: Pesan barang ke supplier
- **Langkah pakai**:
  1. Klik "Tambah" di toolbar
  2. Pilih supplier
  3. Set tanggal kirim
  4. Tambah item, qty, harga
  5. Review total
  6. Simpan (status: Draft)
  7. Approve untuk kirim ke supplier
- **Hasil yang diharapkan**: PO terkirim, outstanding PO tercatat
- **Modul terkait**: Suppliers, Items, Purchase Receiving
- **Risiko jika salah**: PO dobel, harga tidak sesuai

### Purchase Receiving
- **Siapa yang memakai**: Gudang
- **Kapan dipakai**: Terima barang dari supplier
- **Langkah pakai**:
  1. Pilih PO yang akan diterima
  2. Cek qty yang diterima
  3. Input qty actual jika berbeda
  4. Simpan penerimaan
- **Hasil yang diharapkan**: Stok bertambah, PO status updated
- **Modul terkait**: Purchase Orders, Inventory
- **Risiko jika salah**: Stok tidak update, PO tetap outstanding

### Purchase Payments (AP)
- **Siapa yang memakai**: Finance
- **Kapan dipakai**: Bayar hutang ke supplier
- **Langkah pakai**:
  1. Klik "Tambah Pembayaran"
  2. Pilih supplier
  3. Pilih invoice yang akan dibayar
  4. Input nominal pembayaran
  5. Pilih akun kas/bank
  6. Simpan
- **Hasil yang diharapkan**: Hutang berkurang, jurnal tercipta (Debit Hutang, Kredit Kas)
- **Modul terkait**: AP, Cash/Bank, Journal
- **Risiko jika salah**: Hutang tidak update, jurnal tidak balance

---

## SALES

### Sales Orders
- **Siapa yang memakai**: Sales
- **Kapan dipakai**: Terima pesanan dari pelanggan
- **Langkah pakai**:
  1. Klik "Tambah Pesanan"
  2. Pilih pelanggan
  3. Set tanggal kirim
  4. Tambah item, qty, harga
  5. Simpan (status: Draft)
  6. Approve untuk proses
- **Hasil yang diharapkan**: SO tercatat, bisa diproses ke invoice
- **Modul terkait**: Customers, Items, Deliveries
- **Risiko jika salah**: Pesanan hilang, stok tidak reserved

### Sales Add (Invoice)
- **Siapa yang memakai**: Sales, Kasir
- **Kapan dipakai**: Buat invoice penjualan
- **Langkah pakai**:
  1. Klik "Tambah Invoice"
  2. Pilih pelanggan (atau UMUM untuk cash)
  3. Tambah item, qty
  4. System hitung harga, diskon, pajak
  5. Pilih cara bayar
  6. Simpan
- **Hasil yang diharapkan**: Invoice tercipta, stok berkurang, piutang/kas bertambah, jurnal tercipta
- **Modul terkait**: Inventory, AR/Cash, Journal
- **Risiko jika salah**: Stok tidak update, jurnal tidak balance

### AR Payments
- **Siapa yang memakai**: Finance, Kasir
- **Kapan dipakai**: Terima pembayaran piutang
- **Langkah pakai**:
  1. Klik "Tambah Pembayaran"
  2. Pilih pelanggan
  3. Pilih invoice yang dibayar
  4. Input nominal
  5. Input potongan jika ada
  6. Pilih akun kas/bank
  7. Simpan
- **Hasil yang diharapkan**: Piutang berkurang, jurnal tercipta (Debit Kas, Kredit Piutang)
- **Modul terkait**: AR, Cash/Bank, Journal
- **Risiko jika salah**: Piutang tidak update, jurnal tidak balance

---

## INVENTORY

### Stock Movements
- **Siapa yang memakai**: Gudang
- **Kapan dipakai**: Adjustment stok manual
- **Langkah pakai**:
  1. Klik "Tambah Movement"
  2. Pilih tipe (IN/OUT)
  3. Pilih item
  4. Input qty
  5. Pilih alasan
  6. Simpan
- **Hasil yang diharapkan**: Stok terupdate, jurnal adjustment tercipta
- **Modul terkait**: Inventory, Journal
- **Risiko jika salah**: Stok tidak akurat

### Stock Opname
- **Siapa yang memakai**: Gudang, Supervisor
- **Kapan dipakai**: Pencocokan stok fisik
- **Langkah pakai**:
  1. Buat dokumen opname baru
  2. Pilih cabang
  3. System tampilkan stok sistem
  4. Input qty fisik
  5. System hitung selisih
  6. Simpan
  7. Approve untuk adjustment otomatis
- **Hasil yang diharapkan**: Stok sistem = stok fisik
- **Modul terkait**: Inventory, Stock Movements, Journal
- **Risiko jika salah**: Stok tidak akurat, jurnal tidak balance

### Stock Transfers
- **Siapa yang memakai**: Gudang
- **Kapan dipakai**: Pindah stok antar cabang
- **Langkah pakai**:
  1. Klik "Tambah Transfer"
  2. Pilih cabang asal
  3. Pilih cabang tujuan
  4. Pilih item, qty
  5. Simpan
- **Hasil yang diharapkan**: Stok berkurang di asal, bertambah di tujuan
- **Modul terkait**: Inventory, Branches
- **Risiko jika salah**: Stok tidak balance antar cabang

---

## ACCOUNTING

### Journal Entries
- **Siapa yang memakai**: Accounting
- **Kapan dipakai**: Entry jurnal manual
- **Langkah pakai**:
  1. Klik "Tambah Jurnal"
  2. Set tanggal
  3. Input referensi dan keterangan
  4. Tambah baris: pilih akun, debit/kredit
  5. System validasi balance
  6. Simpan jika sudah balance
- **Hasil yang diharapkan**: Jurnal tercatat, mempengaruhi buku besar
- **Modul terkait**: COA, General Ledger
- **Risiko jika salah**: Jurnal tidak balance, laporan tidak akurat

### Cash Transactions
- **Siapa yang memakai**: Kasir, Finance
- **Kapan dipakai**: Catat kas masuk/keluar/transfer
- **Langkah pakai**:
  1. Klik "Tambah Transaksi"
  2. Pilih tipe (Cash In/Out/Transfer)
  3. Pilih akun kas/bank
  4. Input jumlah
  5. Input keterangan
  6. Simpan
- **Hasil yang diharapkan**: Kas terupdate, jurnal tercipta otomatis
- **Modul terkait**: COA, Journal
- **Risiko jika salah**: Saldo kas tidak akurat

---

# BAGIAN 9 — FLOW INTEGRASI ANTAR MODUL

## FLOW 1: Master Item → Purchase → Receive → Stock → AP → Jurnal

```
┌─────────────┐     ┌─────────────────┐     ┌──────────────────┐
│ Master Item │────▶│ Purchase Order  │────▶│ Purchase Receive │
│ (Setup)     │     │ (PO ke Supplier)│     │ (Terima Barang)  │
└─────────────┘     └─────────────────┘     └────────┬─────────┘
                                                     │
                    ┌─────────────────┐              │
                    │   AP (Hutang)   │◀─────────────┤
                    │ Outstanding +   │              │
                    └────────┬────────┘              │
                             │                       ▼
                    ┌────────▼────────┐     ┌──────────────────┐
                    │ AP Payment      │     │ Inventory        │
                    │ (Bayar Hutang)  │     │ (Stock +)        │
                    └────────┬────────┘     └──────────────────┘
                             │
                    ┌────────▼────────┐
                    │ Journal Entry   │
                    │ D: Hutang       │
                    │ C: Kas/Bank     │
                    └─────────────────┘
```

**Langkah detail:**
1. Setup item di Master Items dengan harga beli
2. Buat PO di Purchase Orders, pilih supplier dan item
3. Approve PO → status jadi Confirmed
4. Terima barang di Purchase Receiving → Stok bertambah
5. Invoice pembelian tercipta → Hutang bertambah (AP)
6. Bayar hutang di Purchase Payments
7. Jurnal tercipta otomatis: Debit Hutang, Kredit Kas/Bank

---

## FLOW 2: Master Item → Sales → AR/Kas → Jurnal

```
┌─────────────┐     ┌─────────────────┐     ┌──────────────────┐
│ Master Item │────▶│ Sales Invoice   │────▶│ Inventory        │
│ (Harga Jual)│     │ (Jual Barang)   │     │ (Stock -)        │
└─────────────┘     └─────────────────┘     └──────────────────┘
                             │
            ┌────────────────┴────────────────┐
            ▼                                 ▼
    ┌───────────────┐                ┌───────────────┐
    │ Kredit?       │                │ Tunai?        │
    │ AR (Piutang)  │                │ Cash Masuk    │
    │ Outstanding + │                │ Langsung +    │
    └───────┬───────┘                └───────┬───────┘
            │                                 │
            ▼                                 │
    ┌───────────────┐                         │
    │ AR Payment    │                         │
    │ (Terima Bayar)│                         │
    └───────┬───────┘                         │
            │                                 │
            └─────────────┬───────────────────┘
                          ▼
                 ┌─────────────────┐
                 │ Journal Entry   │
                 │ D: Kas/Piutang  │
                 │ C: Penjualan    │
                 │ C: PPN (jika ada)│
                 └─────────────────┘
```

**Langkah detail:**
1. Item sudah ada di Master Items dengan harga jual
2. Buat invoice di Sales Add
3. Pilih pelanggan, tambah item
4. Stok berkurang otomatis
5. Jika kredit → Piutang bertambah (AR)
6. Jika tunai → Kas bertambah
7. Terima pembayaran piutang di AR Payments
8. Jurnal tercipta otomatis

---

## FLOW 3: Stock Opname → Stock Movement → Jurnal

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│ Stock Opname     │────▶│ Hitung Selisih   │────▶│ Stock Movement   │
│ (Input Stok      │     │ Sistem vs Fisik  │     │ (Adjustment)     │
│  Fisik)          │     │                  │     │                  │
└──────────────────┘     └──────────────────┘     └────────┬─────────┘
                                                           │
                                                           ▼
                         ┌──────────────────┐     ┌──────────────────┐
                         │ Journal Entry    │◀────│ Inventory Update │
                         │ D: Selisih Stok  │     │ Stock = Fisik    │
                         │ C: Persediaan    │     │                  │
                         └──────────────────┘     └──────────────────┘
```

**Langkah detail:**
1. Buat dokumen Stock Opname
2. System tampilkan stok sistem
3. Input qty fisik hasil hitung
4. System hitung selisih
5. Approve opname
6. Stock Movement adjustment tercipta otomatis
7. Stok system = stok fisik
8. Jurnal adjustment tercipta

---

## FLOW 4: Transfer Stok → Mutasi Cabang

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│ Stock Transfer   │────▶│ Cabang Asal      │────▶│ Cabang Tujuan    │
│ Request          │     │ Stock -          │     │ Stock +          │
└──────────────────┘     └──────────────────┘     └──────────────────┘
                                │                         │
                                └───────────┬─────────────┘
                                            ▼
                               ┌───────────────────────┐
                               │ Stock Movement        │
                               │ OUT di Asal           │
                               │ IN di Tujuan          │
                               └───────────────────────┘
```

**Langkah detail:**
1. Buat Transfer Request di Stock Transfers
2. Pilih cabang asal dan tujuan
3. Pilih item dan qty
4. Simpan dan approve
5. Stok berkurang di cabang asal
6. Stok bertambah di cabang tujuan
7. Stock Movement tercatat di kedua cabang

---

## FLOW 5: Kasir → Shift → Sales → Tutup Kas

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│ Login Kasir      │────▶│ Cek Shift        │────▶│ Buka Shift       │
│                  │     │ (Guard)          │     │ (Modal Awal)     │
└──────────────────┘     └──────────────────┘     └────────┬─────────┘
                                                           │
┌──────────────────┐     ┌──────────────────┐              │
│ Setoran Harian   │◀────│ Tutup Shift      │◀─────────────┤
│ (Setor ke Bank)  │     │ (Hitung Kas)     │              │
└──────────────────┘     └──────────────────┘              │
                                                           ▼
                         ┌──────────────────┐     ┌──────────────────┐
                         │ Cash Control     │◀────│ POS Transaction  │
                         │ (Selisih Kas?)   │     │ (Jual Barang)    │
                         └──────────────────┘     └──────────────────┘
```

**Langkah detail:**
1. Kasir login ke sistem
2. System cek apakah ada shift aktif
3. Jika belum, kasir harus buka shift (input modal awal)
4. Kasir bisa transaksi di POS
5. Akhir hari, kasir tutup shift
6. System hitung total penjualan
7. Bandingkan dengan kas fisik
8. Setor ke bank via Setoran Harian
9. Cash Control cek selisih

---

## FLOW 6: Pembayaran Piutang → Kas/Bank → AR → Buku Besar

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│ AR Payment       │────▶│ Pilih Invoice    │────▶│ Input Nominal    │
│ (Terima Bayar)   │     │ Outstanding      │     │ + Potongan       │
└──────────────────┘     └──────────────────┘     └────────┬─────────┘
                                                           │
┌──────────────────┐     ┌──────────────────┐              │
│ General Ledger   │◀────│ Journal Entry    │◀─────────────┤
│ (Buku Besar)     │     │ D: Kas/Bank      │              │
│                  │     │ D: Potongan      │              │
└──────────────────┘     │ C: Piutang       │              │
                         └──────────────────┘              │
                                                           ▼
                         ┌──────────────────┐     ┌──────────────────┐
                         │ Cash/Bank        │     │ AR Outstanding   │
                         │ Balance +        │     │ Berkurang        │
                         └──────────────────┘     └──────────────────┘
```

**Langkah detail:**
1. Buka AR Payments, klik "Tambah Pembayaran"
2. Pilih pelanggan
3. System tampilkan invoice outstanding
4. Pilih invoice yang dibayar
5. Input nominal pembayaran
6. Input potongan jika ada
7. Pilih akun kas/bank penerima
8. Simpan
9. Jurnal tercipta otomatis:
   - Debit: Kas/Bank (nominal dibayar)
   - Debit: Potongan Penjualan (jika ada potongan)
   - Kredit: Piutang Usaha
10. AR outstanding berkurang
11. Saldo kas/bank bertambah
12. Buku besar terupdate

---

# BAGIAN 10 — CHECKLIST IMPLEMENTASI CLEANUP

## DAFTAR MODUL YANG DI-HIDE

| No | File | Alasan | Menu Dihapus | Rute Tetap | Permission |
|----|------|--------|--------------|------------|------------|
| 1 | MasterItemTypes.jsx | Jarang dipakai | Master Data > Jenis Barang | /master/item-types | Tetap |
| 2 | MasterDatasheet.jsx | Jarang dipakai | Master Data > Datasheet | /master/datasheet | Tetap |
| 3 | SerialNumbers.jsx | Advanced | Inventory > Serial Numbers | /inventory/serial-numbers | Tetap |
| 4 | ProductAssembly.jsx | Advanced | Inventory > Assemblies | /inventory/assemblies | Tetap |
| 5 | WarehouseControl.jsx | Overlap | Control > Warehouse | /warehouse-control | Tetap |
| 6 | DataExport.jsx | Ada AdvancedExport | Reports > Data Export | /data-export | Tetap |
| 7 | FinancialControl.jsx | Advanced | Accounting > Control | /financial-control | Tetap |

**Dampak:**
- Route tetap aktif (bisa diakses langsung via URL)
- Hanya dihilangkan dari sidebar menu
- Permission tidak berubah
- Data tetap aman

---

## DAFTAR MODUL YANG PERLU VALIDASI SEBELUM DELETE

| No | File | Validasi Required | Status Validasi |
|----|------|-------------------|-----------------|
| 1 | KartuStok.jsx | ✓ StockCards berfungsi penuh | PENDING |
| 2 | MasterStockCards.jsx | ✓ StockCards berfungsi penuh | PENDING |
| 3 | WarRoomV2.jsx | ✓ Warroom v1 cukup | PENDING |
| 4 | Purchase.jsx | ✓ Tidak ada import aktif | PENDING |
| 5 | PurchaseModule.jsx | ✓ Tidak ada import aktif | PENDING |

**Checklist Validasi Per File:**
- [ ] Modul pengganti sudah ada dan berfungsi
- [ ] Route pengganti sudah aktif
- [ ] Menu sudah diarahkan ke modul final
- [ ] Tidak ada import aktif dari file lama (grep codebase)
- [ ] Tidak ada endpoint backend yang masih dipakai
- [ ] UI pengganti sudah lulus test
- [ ] Role permission di modul baru sudah benar
- [ ] Screenshot bukti modul final sudah ada

---

## DAFTAR MODUL YANG PERLU MERGE

| No | Modul Asal | Modul Tujuan | Route Final | Menu Final | Status |
|----|------------|--------------|-------------|------------|--------|
| 1 | KartuStok | StockCards | /inventory/stock-cards | Inventory > Kartu Stok | PENDING |
| 2 | MasterStockCards | StockCards | /inventory/stock-cards | Inventory > Kartu Stok | PENDING |
| 3 | WarRoomV2 | Warroom | /warroom | War Room > Monitor | PENDING |

**Note untuk Stock Reorder vs Purchase Planning:**
Keputusan DITUNDA sampai ada konfirmasi dari user tentang:
1. Apakah Stock Reorder = hanya alert?
2. Apakah Purchase Planning = generate PO?
3. Jika berbeda level, KEEP BOTH dengan link

---

## DAMPAK CLEANUP

### Route Changes
- Tidak ada route yang dihapus (hanya hide dari menu)
- Backward compatible

### Menu Changes
- 7 menu item akan di-hide
- Sidebar lebih bersih

### Permission Changes
- Tidak ada perubahan permission
- RBAC tetap berfungsi

### Data Changes
- Tidak ada data yang dihapus
- Semua data tetap accessible

### Testing Required
- [ ] Sidebar final screenshot
- [ ] Semua route pengganti berfungsi
- [ ] RBAC retest
- [ ] Transaksi utama tetap normal:
  - [ ] Purchase flow
  - [ ] Sales flow
  - [ ] AR Payment flow
  - [ ] Stock Movement flow
  - [ ] Journal flow

---

*Dokumen ini dibuat secara manual berdasarkan audit menyeluruh sistem OCB TITAN AI*
*Tanggal: 2026-03-13*
*Version: 2.0 FINAL*
*Status: SIAP UNTUK EKSEKUSI PHASE A (HIDE)*
