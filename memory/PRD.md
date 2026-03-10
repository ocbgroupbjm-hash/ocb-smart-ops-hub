# OCB TITAN AI - GLOBAL RETAIL OPERATING SYSTEM
## Product Requirements Document (PRD)

### Overview
Enterprise AI-powered retail operating system for OCB GROUP managing multi-branch retail operations with comprehensive HR, Payroll, Sales, Inventory, and AI analytics capabilities.

---

## LATEST UPDATE: March 10, 2026

### New Features Implemented:

#### 1. Daftar Item Page Redesign (ERP-Style)
- **Comprehensive Filter Bar:**
  - Row 1: Kata Kunci + Cari + Reset + Export (Excel/CSV) + Tambah Item
  - Row 2: Tipe Item (radio: Semua/Barang/Jasa/Rakitan/Non-Inv/Biaya) + Cabang + Jenis + Pilihan Item
  - Row 3: Rak + Merek + Discontinued checkbox
  - Row 4: Sort By dropdown + Total Data display
- **Data Table:** KODE, BARCODE, NAMA ITEM, TIPE, CABANG, RAK, MEREK, H.BELI, H.JUAL, STOK, STATUS, AKSI
- **Action Buttons:** Edit, AI Photo Studio, Stok Per Cabang, Hapus
- **Pagination:** 50 items per page, navigation controls

#### 2. Per-Branch Stock System
- **Konsep Utama:** GUDANG = CABANG (menggunakan Cabang sebagai lokasi stok utama)
- **Database:** `item_branch_stock` collection
- **Schema:** item_id, branch_id, branch_name, stock_current, stock_minimum, stock_maximum
- **Features:**
  - Auto-initialize branch stocks (46 cabang) saat item baru dibuat
  - Modal manajemen stok per cabang untuk setiap item
  - Stock alerts untuk stok di bawah minimum
  - AI restock recommendations

#### 3. AI Product Photo Studio
- **Upload:** JPG, PNG, WEBP (max 5MB)
- **AI Enhancement Tools:**
  - Enhance (improve lighting, sharpness, color)
  - Remove Background
  - White Background
  - Catalog Style Photo
- **Before/After Comparison:** Side-by-side preview
- **Gallery Management:** Multiple images per product
- **Database:** `item_images` collection
- **API:** Uses Emergent LLM Key with OpenAI GPT Image 1

---

## AUDIT STATUS: COMPLETE (March 10, 2026)

### Final Test Results (Iteration 22):
- **Backend:** 100% (25/25 tests passed)
- **Frontend:** 100% (All menus functional)
- **Daftar Item Page:** All filters verified working
- **Branch Stock System:** 46 branches, CRUD verified
- **AI Photo Studio:** Modal, upload, API verified

---

## System Stats

| Metric | Value |
|--------|-------|
| Total Branches | 46 |
| Total Employees | 37 |
| Total Products | 31 |
| Total Transactions | 232+ |
| Total Kas | Rp 1,008,004,086 |

---

## Core Modules

### 1. AI CFO & War Room
- CFO Dashboard: Revenue, Profit, Payroll Ratio
- AI Super War Room: Branch monitoring
- Global Map: 46 branches with status

### 2. OCB TITAN AI
- AI Command Center: Insights, Recommendations
- KPI Performance: Employee/Branch rankings
- CRM AI: Customer management
- Advanced Export: XLSX, PDF, CSV, JSON
- Import Data: Templates, Upload, Preview

### 3. Operasional
- Setoran Harian: Daily deposit tracking
- Selisih Kas: Cash discrepancy monitoring
- Dashboard ERP: Overview

### 4. Master Data (CRUD Verified)
- **Daftar Item (NEW):** ERP-style dengan comprehensive filters
- Kategori: 6 items
- Satuan: 6 items
- Merk: 6 items
- Supplier: 6 items
- Pelanggan: 20 items

### 5. Persediaan
- Stok Masuk/Keluar: Working
- Transfer Stok: Working
- **Stok Per Cabang (NEW):** Min/Max per 46 branches
- Branch Stock Alerts
- AI Restock Recommendations

### 6. Akuntansi
- COA: Chart of Accounts
- Kas Masuk/Keluar
- Jurnal
- Neraca Saldo
- Laba Rugi

### 7. HR & Payroll
- Data Karyawan: 37 employees
- Absensi: 288+ records
- Payroll Auto
- AI Performance
- Master Jabatan/Shift

---

## API Endpoints (Key)

### Master Data CRUD
- GET/POST/PUT/DELETE `/api/master/items` (with branch_id support)
- GET/POST/PUT/DELETE `/api/master/categories`
- GET/POST/PUT/DELETE `/api/master/units`
- GET/POST/PUT/DELETE `/api/master/brands`

### Branch Stock Management
- GET `/api/inventory/branch-stock/{item_id}` - Get branch stocks
- POST `/api/inventory/branch-stock/{item_id}` - Save branch stocks
- GET `/api/inventory/branch-stock-alerts` - Low stock alerts
- GET `/api/inventory/ai-restock-recommendations` - AI recommendations

### AI Photo Studio
- POST `/api/ai-photo-studio/upload/{item_id}` - Upload photo
- GET `/api/ai-photo-studio/images/{item_id}` - Get all images
- POST `/api/ai-photo-studio/enhance` - AI enhance photo
- POST `/api/ai-photo-studio/save-enhanced/{item_id}` - Save enhanced
- DELETE `/api/ai-photo-studio/images/{image_id}` - Delete image

### Export
- GET `/api/export-v2/{module}/{data_type}?format=xlsx|csv|pdf`

---

## Key Files

### Frontend
- `/app/frontend/src/pages/master/MasterItems.jsx` - Main item list page (ERP-style)
- `/app/frontend/src/components/layout/Sidebar.jsx` - Navigation

### Backend
- `/app/backend/routes/master_erp.py` - Master data CRUD with branch_id
- `/app/backend/routes/branch_stock.py` - Per-branch stock management
- `/app/backend/routes/ai_photo_studio.py` - AI photo processing

---

## Test Reports
- `/app/test_reports/iteration_22.json` - Final verification (100% pass)

---

## Deployment Readiness

| Aspect | Status |
|--------|--------|
| 46 Branches Support | READY |
| Per-Branch Stock | READY |
| AI Photo Studio | READY |
| CRUD Operations | VERIFIED |
| Data Consistency | VERIFIED |

---

**Version:** 6.0.0 (Major Feature Update)
**Last Updated:** March 10, 2026
