# OCB AI TITAN - Enterprise Retail AI System
## Product Requirements Document

### Overview
OCB AI TITAN is a comprehensive Enterprise Resource Planning (ERP) system modeled after iPOS, designed for retail operations. The system integrates AI capabilities with traditional ERP functionality.

---

## Core Modules

### 1. Master Data (Completed in this session)
- **Daftar Item** - Full CRUD for products
- **Kategori Item** - Product categories
- **Satuan** - Units of measurement
- **Merk** - Brands
- **Dept/Gudang** - Warehouses/Departments
- **Daftar Supplier** - Supplier management
- **Daftar Pelanggan** - Customer management
- **Daftar Sales** - Sales personnel
- **Grup Pelanggan** - Customer groups (NEW)
- **Wilayah** - Regions (NEW)
- **E-Money** - Digital payment methods (NEW)
- **Bank** - Bank accounts (NEW)
- **Ongkir** - Shipping costs (NEW)
- **Diskon Periode** - Period discounts (NEW)
- **Promosi** - Promotions (NEW)

### 2. Pembelian (Purchase) - Completed
- **Pesanan Pembelian** - Purchase orders with full CRUD
- **Daftar Pembelian** - Purchase list with filters and export (NEW)
- **Penerimaan Barang** - Goods receiving with stock updates (NEW)
- **History Harga Beli** - Purchase price history (NEW)
- **Daftar Pembayaran** - Payment recording (NEW)
- **Status Lunas** - Payment status tracking
- **Retur Pembelian** - Purchase returns (NEW)

### 3. Penjualan (Sales) - Completed
- **Pesanan Penjualan** - Sales orders (linked to POS)
- **Daftar Penjualan** - Sales list with export (NEW)
- **Penjualan Kasir** - Cashier POS
- **Retur Penjualan** - Sales returns (NEW)
- **Data Pengiriman** - Delivery tracking (NEW)

### 4. Persediaan (Inventory) - Completed
- **Daftar Stok** - Stock list
- **Kartu Stok** - Stock cards with history (NEW)
- **Stok Masuk/Keluar** - Stock in/out movements (NEW)
- **Transfer Stok** - Inter-branch transfers (NEW)
- **Stok Opname** - Physical inventory count (NEW)
- **Serial Number** - Serial number tracking (placeholder)
- **Rakitan Produk** - Product assemblies (placeholder)

### 5. Akuntansi (Accounting) - Pending
- **Daftar Perkiraan (COA)** - Chart of Accounts
- **Kas Masuk/Keluar** - Cash management
- **Jurnal** - Journal entries
- **Buku Besar** - General Ledger
- **Saldo Awal** - Opening balances

### 6. Laporan (Reports) - Pending
- Sales, Purchase, Inventory, Financial reports
- Export to Excel/PDF

### 7. Pengaturan (Settings) - Partial
- **Pengaturan Printer** - Completed
- **Data User** - Existing
- **Data Perusahaan** - Pending
- **Backup & Restore** - Pending

### 8. AI Features (Existing/Retained)
- **Hallo AI** - Multi-persona chat interface
- **AI Bisnis** - Business insights
- **Dashboard/War Room** - Real-time KPIs

---

## Technical Stack
- **Frontend:** React, TailwindCSS, Shadcn UI
- **Backend:** FastAPI (Python)
- **Database:** MongoDB
- **Authentication:** JWT with RBAC

---

## What's Implemented (This Session - December 8, 2025)

### Frontend Pages Created:
1. MasterCustomerGroups.jsx
2. MasterRegions.jsx
3. MasterBanks.jsx
4. MasterEmoney.jsx
5. MasterShippingCosts.jsx
6. MasterDiscounts.jsx
7. MasterPromotions.jsx
8. PurchaseList.jsx
9. PurchasePayments.jsx
10. PurchaseReturns.jsx
11. PurchasePriceHistory.jsx
12. PurchaseReceiving.jsx
13. SalesList.jsx
14. SalesReturns.jsx
15. SalesDelivery.jsx
16. StockCards.jsx
17. StockMovements.jsx
18. StockTransfers.jsx
19. StockOpname.jsx

### Backend Endpoints Added:
- `/api/master/regions` - CRUD
- `/api/master/emoney` - CRUD
- `/api/master/shipping-costs` - CRUD
- `/api/master/customer-points` - Read
- `/api/purchase/payments` - CRUD
- `/api/purchase/returns` - CRUD
- `/api/purchase/price-history` - Read
- `/api/sales/returns` - CRUD (pending full implementation)
- `/api/sales/deliveries` - CRUD (pending full implementation)

---

## Test Results (December 8, 2025)
- **Backend:** 100% (19/19 tests passed)
- **Frontend:** 100% (7/7 features verified)
- **Bug Fixed:** Stock Cards API endpoint typo corrected

---

## Next Steps (Priority Order)

### P0 - High Priority
1. Complete Akuntansi module (Chart of Accounts, Journals, Ledgers)
2. Implement Sales backend routes (returns, deliveries)
3. Add inventory backend routes (transfers, opnames)

### P1 - Medium Priority
4. Build Reports module with export functionality
5. Complete Settings pages (Company data, Backup/Restore)
6. Implement print receipt functionality

### P2 - Low Priority
7. Serial number tracking for products
8. Product assemblies/kits
9. WhatsApp integration

---

## Credentials for Testing
- **Admin:** admin@ocb.com / admin123
- **Owner:** ocbgroupbjm@gmail.com / admin123
- **Kasir:** kasir@ocb.com / admin123

---

## UI Language
All user interface is in **Bahasa Indonesia** as per user requirement.
