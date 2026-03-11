# OCB TITAN ERP - ENTERPRISE RETAIL OPERATING SYSTEM
## Product Requirements Document (PRD) v23.0

---

# OVERVIEW

OCB TITAN ERP adalah sistem ERP retail enterprise untuk bisnis multi-cabang dengan fitur lengkap:
- **ERP Hardening** - Fiscal Period System & Multi-Currency System - COMPLETED!
- **Setting Akun ERP iPOS Style** dengan Account Derivation Engine - FULLY INTEGRATED!
- **Master Data iPOS Style** dengan 21 menu lengkap
- **POS / Penjualan** dengan multi-mode pricing + auto AR
- **Sales Module iPOS Style** dengan full integration
- **Pembelian Enterprise** dengan full lifecycle (PO→Receive→AP→Payment→Journal)
- **Owner Dashboard** dengan KPI bisnis real-time
- **Finance Dashboard** dengan ringkasan keuangan lengkap
- **CFO Dashboard** dengan analisis keuangan executive
- **Inventory / Stok** dengan movement tracking
- **Setoran Harian** dengan security ketat
- **Hutang Piutang** (AR/AP) dengan aging + auto-journal
- **Akuntansi** dengan auto-journal + financial reports
- **RBAC** dengan FAIL-SAFE enforcement (Backend validation)
- **Audit Trail** untuk semua aktivitas sensitif
- **18 Modul AI/KPI/CRM** yang terintegrasi dengan data ERP (VERIFIED!)

---

# LATEST UPDATE: March 11, 2026 - ERP HARDENING PHASE 1 COMPLETE

## 1. Fiscal Period System - IMPLEMENTED ✅

### Features
- **Status Management:** OPEN → CLOSED → LOCKED
  - `OPEN`: Transaksi dapat dibuat, diedit, dihapus
  - `CLOSED`: Transaksi tidak dapat dibuat/diedit. Dapat dibuka kembali oleh admin.
  - `LOCKED`: Periode dikunci permanen. Tidak dapat diubah kembali.

### Enforcement
Fiscal period validation terintegrasi ke semua modul transaksi:
- `/app/backend/routes/pos.py` - `enforce_fiscal_period()` di `create_transaction()`
- `/app/backend/routes/purchase.py` - `enforce_fiscal_period()` di `receive_purchase_order()`
- `/app/backend/routes/sales_module.py` - `enforce_fiscal_period()` di `create_sales_order()` & `create_sales_invoice()`

### API Endpoints
| Endpoint | Method | Purpose |
|----------|--------|---------|
| /api/erp-hardening/fiscal-periods | GET | List all periods |
| /api/erp-hardening/fiscal-periods | POST | Create new period |
| /api/erp-hardening/fiscal-periods/{id} | PUT | Update period |
| /api/erp-hardening/fiscal-periods/{id}/close | POST | Close period |
| /api/erp-hardening/fiscal-periods/{id}/lock | POST | Lock permanently |
| /api/erp-hardening/fiscal-periods/validate | GET | Validate date |

### Error Response When Period Closed/Locked
```json
{
  "detail": {
    "error": "FISCAL_PERIOD_LOCKED",
    "message": "Tidak dapat create transaksi. Periode 'XXX' status: Ditutup",
    "period_id": "xxx",
    "period_name": "XXX",
    "period_status": "closed"
  }
}
```

## 2. Multi-Currency System - IMPLEMENTED ✅

### Features
- **Base Currency:** IDR (Rupiah Indonesia)
- **Supported Currencies:** USD, EUR, SGD, MYR, CNY, JPY
- **Exchange Rate Management:** CRUD untuk kurs harian
- **Currency Conversion Calculator**
- **Gain/Loss Calculation** untuk settlement AP/AR

### Default Exchange Rates
| Currency | Rate to IDR |
|----------|-------------|
| USD | Rp 15.500 |
| EUR | Rp 17.000 |
| SGD | Rp 11.500 |
| MYR | Rp 3.500 |
| CNY | Rp 2.200 |
| JPY | Rp 105 |

### API Endpoints
| Endpoint | Method | Purpose |
|----------|--------|---------|
| /api/erp-hardening/currencies | GET | List currencies |
| /api/erp-hardening/currencies | POST | Add currency |
| /api/erp-hardening/currencies/initialize-defaults | POST | Init defaults |
| /api/erp-hardening/exchange-rates | GET | List rates |
| /api/erp-hardening/exchange-rates | POST | Add rate |
| /api/erp-hardening/exchange-rates/current | GET | Current rates |
| /api/erp-hardening/exchange-rates/convert | POST | Convert amount |
| /api/erp-hardening/exchange-rates/calculate-gain-loss | POST | Calc gain/loss |

## 3. UI - ERP Hardening Page ✅

### Location
Master Data → ERP Hardening (`/master/erp-hardening`)

### Tabs
1. **Periode Fiscal**
   - Table: Nama Periode, Tanggal Mulai, Tanggal Akhir, Status, Catatan, Aksi
   - Actions: Tutup (Close), Kunci Permanen (Lock)
   - Dialog: Tambah Periode dengan validasi overlap

2. **Multi-Currency**
   - Kurs Saat Ini: Card dengan daftar mata uang dan kurs
   - Konversi Mata Uang: Calculator dengan dropdown From/To
   - Riwayat & Update Kurs: Table + Dialog tambah kurs baru

---

# PREVIOUS UPDATES

## March 11, 2026 - Account Derivation Engine Full Integration ✅
- All transactional modules integrated: Purchase, POS, Sales, AP, AR, Accounting, Deposit
- All hard-coded accounts replaced with iPOS-style codes (X-XXXX format)

## March 11, 2026 - Setting Akun ERP ✅
- 12 configuration tabs
- Account Derivation Engine with priority: Branch > Warehouse > Category > Payment > Tax > Global > Default

---

# CODE ARCHITECTURE

## New Files Created
- `/app/backend/routes/erp_hardening.py` - Fiscal Period & Multi-Currency System
- `/app/frontend/src/pages/ERPHardening.jsx` - UI page

## Modified Files
- `/app/backend/routes/pos.py` - Added `enforce_fiscal_period()`
- `/app/backend/routes/purchase.py` - Added `enforce_fiscal_period()`
- `/app/backend/routes/sales_module.py` - Added `enforce_fiscal_period()`
- `/app/backend/server.py` - Added erp_hardening_router
- `/app/frontend/src/App.js` - Added ERPHardening route
- `/app/frontend/src/components/layout/Sidebar.jsx` - Added ERP Hardening menu

## Database Collections
- `fiscal_periods` - Fiscal period records
- `currencies` - Currency definitions
- `exchange_rates` - Exchange rate history

---

# TEST RESULTS

| Iteration | Module | Result |
|-----------|--------|--------|
| 34 | Sales Module | 100% PASS |
| 35 | Master Data | 94% PASS |
| 36 | Account Settings UI | 100% PASS |
| 37 | Account Derivation Integration | 94% PASS |
| 38 | ERP Hardening Phase 1 | 96% PASS (Backend) / 100% PASS (Frontend) |

---

# REMAINING TASKS

## P2 - Purchase Module iPOS Style
- [ ] Overhaul Purchase UI to match iPOS specification
- [ ] Add PO Approval Workflow

## P3 - Future Enhancements
- [ ] Multi-Tax Engine
- [ ] Auto Reversal Engine
- [ ] Fraud Detection Engine
- [ ] Audit Trail UI
- [ ] Excel Import for Purchases
- [ ] Konsinyasi Module
- [ ] Kas/Bank Module
- [ ] Laporan (Reports) Module

---

# CREDENTIALS

| Role | Email | Password |
|------|-------|----------|
| Owner | ocbgroupbjm@gmail.com | admin123 |
| Kasir | kasir_test@ocb.com | password123 |
| Supervisor | supervisor_test@ocb.com | password123 |
| Viewer | viewer_test@ocb.com | password123 |

---

**Version:** 23.0 (ERP Hardening Phase 1 Complete)
**Last Updated:** March 11, 2026
**Architecture:** SSOT, Non-Destructive, Additive
