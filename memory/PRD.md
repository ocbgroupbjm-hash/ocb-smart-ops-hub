# OCB TITAN RETAIL AI OPERATING SYSTEM

## Product Requirements Document

### 1. Overview
OCB TITAN adalah sistem retail AI enterprise-grade yang dibangun untuk OCB GROUP. Sistem ini menggantikan iPOS 5 Ultimate dengan solusi modern yang mendukung 40+ cabang.

### 2. Tech Stack
- **Frontend:** React.js dengan Tailwind CSS
- **Backend:** FastAPI (Python)
- **Database:** MongoDB
- **Styling:** Dark theme dengan Red-Gold accent

### 3. Bahasa Sistem
**SEMUA INTERFACE DALAM BAHASA INDONESIA**

Menu Utama:
- Dashboard
- Kasir (POS)
- Produk
- Stok
- Pembelian
- Supplier
- Pelanggan
- Keuangan
- Akuntansi
- Laporan
- Cabang
- Pengguna
- Pengaturan

### 4. Modul yang Telah Diimplementasi

#### 4.1 Dashboard ✅
- Penjualan Hari Ini
- Laba Hari Ini
- Total Transaksi
- Total Saldo Kas
- Total Cabang, Produk, Pelanggan, Karyawan
- Trend Penjualan (7 Hari)
- Produk Terlaris
- Peringatan Stok Menipis

#### 4.2 Kasir (POS) ✅
- Scan barcode / cari produk
- Keranjang belanja
- Diskon produk & transaksi
- Multi-payment (Tunai, Transfer, QRIS, E-wallet, Split Payment)
- Hold/Recall/Void transaksi
- Retur transaksi
- Cetak struk

#### 4.3 Produk ✅
- CRUD produk lengkap
- Field: Kode, Nama, Kategori, Brand, Barcode
- Multi-harga: Modal, Jual, Grosir, Member, Reseller
- Stok minimum
- Kategori & Sub-kategori

#### 4.4 Inventory ✅
- Stok per cabang
- Stok gudang
- Transfer stok cabang
- Stok opname
- Kartu stok / mutasi
- Peringatan stok menipis

#### 4.5 Pembelian ✅
- Purchase Order (PO)
- Penerimaan barang
- Status: Draft, Dipesan, Sebagian, Diterima, Dibatalkan

#### 4.6 Supplier ✅
- Database supplier lengkap
- Kontak, Alamat, Kota
- Informasi Bank
- Term pembayaran

#### 4.7 Pelanggan (CRM) ✅
- Data pelanggan (Nama, HP, Email, Alamat)
- Segmen: Reguler, Member, VIP, Reseller, Grosir
- Loyalty points
- Riwayat transaksi

#### 4.8 Keuangan ✅
- Saldo Kas
- Kas Masuk/Keluar
- Pengeluaran
- Laporan harian

#### 4.9 Akuntansi ✅
- Laporan Laba Rugi
- Neraca (dalam pengembangan)
- Jurnal Umum (dalam pengembangan)

#### 4.10 Laporan ✅
- Laporan Penjualan (Harian, Per Cabang, Per Produk)
- Laporan Produk (Terlaris, Performa)
- Laporan Stok
- Laporan Cabang
- Laporan Pelanggan

#### 4.11 Multi-Cabang ✅
- CRUD cabang
- Saldo kas per cabang
- Gudang

#### 4.12 Pengguna ✅
- Role: Owner, Admin, Supervisor, Kasir, Finance, Inventory
- Aktivasi/Nonaktifkan user
- Assign ke cabang

#### 4.13 Pengaturan ✅
- Info Toko
- Pengaturan POS
- Notifikasi
- Keamanan (2FA, Audit Log)
- Backup

### 5. API Endpoints

#### Authentication
- POST /api/auth/login
- POST /api/auth/register
- GET /api/auth/me

#### Dashboard
- GET /api/dashboard/owner
- GET /api/dashboard/branch
- GET /api/dashboard/sales-trend
- GET /api/dashboard/top-products
- GET /api/dashboard/low-stock

#### Products
- GET/POST /api/products
- GET/PUT/DELETE /api/products/{id}
- GET/POST /api/products/categories
- GET /api/products/search

#### Inventory
- GET /api/inventory/stock
- GET /api/inventory/stock/low
- GET /api/inventory/movements
- POST /api/inventory/stock-in
- POST /api/inventory/stock-out
- GET/POST /api/inventory/transfers
- GET/POST /api/inventory/opnames

#### POS
- POST /api/pos/transactions
- GET /api/pos/transactions
- POST /api/pos/transactions/{id}/void
- POST /api/pos/transactions/{id}/return
- GET/POST /api/pos/held
- GET /api/pos/summary/today

#### Finance
- GET /api/finance/cash/balance
- POST /api/finance/cash/in
- POST /api/finance/cash/out
- GET /api/finance/cash/movements
- GET/POST /api/finance/expenses
- GET /api/finance/reports/daily
- GET /api/finance/reports/profit-loss

#### Reports
- GET /api/reports/sales
- GET /api/reports/product-performance
- GET /api/reports/inventory
- GET /api/reports/branch-comparison
- GET /api/reports/customer-analysis

#### Master Data
- GET/POST /api/branches
- GET/POST /api/customers
- GET/POST /api/suppliers

#### Users
- GET/POST /api/users
- PUT /api/users/{id}

### 6. Kredensial Test
- **Email:** admin@ocb.com
- **Password:** admin123
- **Role:** Owner

### 7. Status Testing
- **Backend:** 100% PASSED (34/34 tests)
- **Frontend:** 100% PASSED (All pages functional)

### 8. Tanggal Update
- **Terakhir diupdate:** 2026-03-08
- **Status:** Sistem siap digunakan

### 9. Catatan untuk Pengembangan Selanjutnya

#### Fitur yang Perlu Dikembangkan:
1. **WhatsApp AI Integration** - Kirim struk, cek stok, balas chat
2. **AI Business** - Analisa penjualan, rekomendasi produk
3. **Neraca & Jurnal** - Akuntansi lengkap
4. **Export Excel/PDF** - Laporan downloadable
5. **Backup Database** - Sistem backup otomatis

#### Integrasi yang Dibutuhkan:
- WhatsApp API untuk notifikasi
- Payment Gateway (QRIS)
- Printer thermal untuk struk
