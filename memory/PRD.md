# OCB TITAN AI - ENTERPRISE RETAIL OPERATING SYSTEM
## Product Requirements Document (PRD)

### Overview
Enterprise AI-powered retail operating system dengan **Supreme RBAC Security**, **Multi-Mode Pricing**, dan **ERP-Grade Item Management**.

---

## LATEST UPDATE: March 10, 2026

### ✅ FORM TAMBAH ITEM REVISI - COMPLETE (100%)

#### Perubahan Utama
1. **HAPUS Field Cabang** - Master item bersifat global
2. **4 Tab Structure** - Form lebih terorganisir
3. **Multi-Mode Pricing Terintegrasi** - Langsung di form

#### Struktur Form Baru

**TAB 1: Data Umum**
- Kode Item* (wajib)
- Barcode
- Nama Item* (wajib)
- Tipe Item (Barang/Jasa/Rakitan/Non-Inventory/Biaya)
- Kategori
- Satuan* (wajib)
- Merek
- Rak Default
- SKU Internal
- Harga Beli
- Harga Jual Default
- Berat (dengan unit gr/kg/ml/l)
- Supplier Default
- Deskripsi
- Checkboxes: Aktif, Track Stok, Serial Number, Expired Date, Discontinued

**TAB 2: Harga Jual**
- Pilihan Mode Harga:
  - (●) Satu Harga
  - ( ) Berdasarkan Jumlah
  - ( ) Level Harga
  - ( ) Berdasarkan Satuan
- Form dinamis sesuai mode
- Checkbox: "Harga jual dipilih saat transaksi"
- Security warning untuk kasir tanpa izin

**TAB 3: Stok & Gudang**
- Minimal Stok (global)
- Maksimal Stok (global)
- Rak Default
- Info: "Pengaturan stok per cabang via modul Stok Per Cabang"

**TAB 4: Akunting**
- Akun Persediaan
- Akun Penjualan
- Akun HPP
- Akun Retur
- Akun Diskon
- Info: "Opsional - default dari pengaturan perusahaan"

#### Validasi
- ✅ Kode Item wajib
- ✅ Nama Item wajib
- ✅ Satuan wajib
- ✅ Harga tidak boleh negatif
- ✅ Mode pricing specific validations

---

### ✅ MULTI-MODE SELLING PRICE SYSTEM - COMPLETE

| Mode | Deskripsi |
|------|-----------|
| Satu Harga | Satu harga tetap |
| Berdasarkan Jumlah | Price tiers per qty |
| Level Harga | Per customer type |
| Berdasarkan Satuan | Per unit (PCS/PACK/DUS) |

---

### ✅ ENTERPRISE RBAC SECURITY SYSTEM - COMPLETE

| Level | Role |
|-------|------|
| 0 | Super Admin |
| 1 | Pemilik (inherit_all) |
| 2 | Direktur |
| 3 | Manager |
| 4 | Supervisor |
| 5 | Admin |
| 6 | Gudang/Keuangan |
| 7 | Kasir |
| 8 | Viewer |

---

## System Stats

| Metric | Value |
|--------|-------|
| Total Branches | 46 |
| Total Products | 34+ |
| RBAC Modules | 99 |
| RBAC Actions | 13 |
| Pricing Modes | 4 |
| Customer Levels | 5 |

---

## Key Components

### Form Tambah Item
- `/app/frontend/src/components/master/ItemFormModal.jsx`

### Pricing System
- `/app/backend/routes/pricing_system.py`
- `/app/frontend/src/components/pricing/PricingConfigModal.jsx`

### RBAC System
- `/app/backend/routes/rbac_system.py`
- `/app/frontend/src/pages/settings/RBACManagement.jsx`

---

## Test Results

| Iteration | Feature | Result |
|-----------|---------|--------|
| 24 | Enterprise RBAC | 100% PASS |
| 25 | Multi-Mode Pricing | 100% PASS |
| 26 | Form Tambah Item Revisi | 100% PASS |

---

## Deployment Readiness

| Feature | Status |
|---------|--------|
| Global Master Item | ✅ READY |
| Form 4 Tabs | ✅ READY |
| Multi-Mode Pricing | ✅ READY |
| Enterprise RBAC | ✅ READY |
| Branch Stock Module | ✅ READY |

---

**Version:** 10.0.0 (Form Item + Multi-Mode Pricing + RBAC)
**Last Updated:** March 10, 2026
**Test Coverage:** 100%
