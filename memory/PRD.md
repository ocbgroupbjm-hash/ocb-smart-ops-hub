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

### Phase 4: Standard ERP Toolbar (IN PROGRESS)
**Completed:**
- `ERPActionToolbar.jsx` - Komponen reusable
- `StockCardModal.jsx` - Modal kartu stok dari SSOT
- Master Items - 7 tombol toolbar
- Master Suppliers - 3 tombol toolbar
- Master Customers - 3 tombol toolbar
- Master Categories - 3 tombol toolbar
- Master Brands - 3 tombol toolbar
- Master Units - 3 tombol toolbar
- Branches - 3 tombol + view switcher
- MasterWarehouses - 3 tombol toolbar
- Purchase Orders - 6 tombol toolbar
- Sales List - 5 tombol toolbar
- Stock Transfers - 3 tombol toolbar

**Remaining:**
- Stock Opname / Inventory Adjustment
- Kas / Bank transactions
- Jurnal Akuntansi

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
- `/app/test_reports/iteration_47.json` - P1 Backend tests
- `/app/test_reports/iteration_48.json` - RBAC sync tests
- `/app/test_reports/iteration_49.json` - Owner Edit UI tests
- `/app/test_reports/iteration_50.json` - Transaction engine tests
- `/app/test_reports/iteration_51.json` - Full integration tests
- `/app/test_reports/iteration_52.json` - ERP Toolbar tests (100% PASS)

---

## Prioritized Backlog

### P0 - Critical
- [ ] Kartu Stok Modal - Test fitur di Master Items

### P1 - High Priority  
- [ ] Duplikasi Item - Test auto-generate kode
- [ ] Stock Opname toolbar
- [ ] Kas / Bank toolbar

### P2 - Medium Priority
- [ ] Jurnal Akuntansi toolbar
- [ ] Print functionality
- [ ] Import/Export Excel

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

*Last Updated: 2026-03-13*
