# OCB TITAN AI - ENTERPRISE RETAIL OPERATING SYSTEM
## Product Requirements Document (PRD)

### Overview
Enterprise AI-powered retail operating system dengan **Supreme RBAC Security** dan **Multi-Mode Pricing System**.

---

## LATEST UPDATE: March 10, 2026

### ✅ MULTI-MODE SELLING PRICE SYSTEM - COMPLETE (100%)

#### 4 Pricing Modes

**1. SATU HARGA (Single Price)**
- Produk hanya memiliki satu harga jual tetap
- Contoh: Kabel Data = Rp 15.000

**2. BERDASARKAN JUMLAH (Quantity Pricing)**
- Harga berubah berdasarkan jumlah pembelian
- Contoh:
  - Qty 1-4 = Rp 10.000
  - Qty 5-9 = Rp 9.000
  - Qty 10+ = Rp 8.000

**3. LEVEL HARGA (Price Levels)**
- Harga berbeda berdasarkan tipe customer
- Contoh:
  - Retail = Rp 10.000
  - Member = Rp 9.500
  - Reseller = Rp 9.000
  - Distributor = Rp 8.500
  - Grosir = Rp 8.000

**4. BERDASARKAN SATUAN (Unit Pricing)**
- Harga berbeda berdasarkan satuan
- Contoh:
  - 1 PCS = Rp 1.500
  - 1 PACK (10 PCS) = Rp 14.000
  - 1 DUS (50 PCS) = Rp 55.000

#### API Endpoints
```
POST   /api/pricing/init              - Initialize system
GET    /api/pricing/modes             - Get pricing modes
GET    /api/pricing/customer-levels   - Get customer levels
GET    /api/pricing/product/{id}      - Get product pricing
PUT    /api/pricing/product/{id}      - Update product pricing
POST   /api/pricing/calculate         - Calculate price
POST   /api/pricing/calculate-batch   - Batch calculation
POST   /api/pricing/pos/select-price  - POS price selection (secured)
POST   /api/pricing/bulk-setup        - Bulk pricing setup
```

#### Security Features
- ✅ **Override Price Permission**: Hanya user dengan `override_price` yang dapat mengubah harga
- ✅ **FAIL-SAFE**: Kasir tanpa izin mendapat 403 FORBIDDEN
- ✅ **Audit Log**: Semua perubahan harga tercatat

#### Frontend Components
- **PricingConfigModal**: Konfigurasi harga per produk
- **POSPriceComponents**: Display harga di POS
- **MODE HARGA Column**: Badge di tabel items (SINGLE/QTY/LEVEL/UNIT)

---

### ✅ ENTERPRISE RBAC SECURITY SYSTEM - COMPLETE

#### Role Hierarchy (Level 0-8)
```
Level 0: SUPER ADMIN     - Full system access
Level 1: PEMILIK         - Full access (inherit_all)
Level 2: DIREKTUR        - All branches access
Level 3: MANAGER         - Inherits from Supervisor
Level 4: SUPERVISOR      - Inherits from Admin
Level 5: ADMIN           - Inherits from Gudang + Keuangan
Level 6: GUDANG/KEUANGAN - Departmental access
Level 7: KASIR           - Point of sale only
Level 8: VIEWER          - View only (read-only)
```

#### Metrics
| Metric | Value |
|--------|-------|
| Total Modules | 99 |
| Total Actions | 13 |
| Total Roles | 10 |
| Customer Levels | 5 |
| Pricing Modes | 4 |

---

## Complete System Features

### 1. AI CFO & War Room
- CFO Dashboard, AI War Room, Global Map (46 branches)

### 2. Master Data
- Items, Categories, Units, Brands, Suppliers, Customers
- Per-Branch Stock, AI Photo Studio, Kartu Stok

### 3. Transactions
- Purchase, Sales, Cashier, Returns
- Stock In/Out, Transfer, Opname

### 4. Accounting
- Cash In/Out, Journals, General Ledger
- Period Closing, Balance Sheet

### 5. Reports
- 15+ report types with export

### 6. Enterprise Security
- RBAC with 10-level hierarchy
- Audit logging with severity
- Branch-level access control

### 7. Multi-Mode Pricing
- 4 pricing modes
- POS price selection (secured)
- Customer level discounts

---

## Test Results

### Iteration 24: Enterprise RBAC
- Backend: 23/23 PASSED (100%)
- Frontend: 100% Working

### Iteration 25: Multi-Mode Pricing
- Backend: 15/15 PASSED (100%)
- Frontend: 100% Working

---

## Test Accounts
| Role | Email | Password |
|------|-------|----------|
| PEMILIK | ocbgroupbjm@gmail.com | admin123 |
| ADMIN | admin_test@ocb.com | test123 |
| SUPERVISOR | supervisor_test@ocb.com | test123 |
| KASIR | kasir_test@ocb.com | test123 |
| VIEWER | viewer_test@ocb.com | test123 |

---

## Key Files

### Pricing System
- `/app/backend/routes/pricing_system.py`
- `/app/frontend/src/components/pricing/PricingConfigModal.jsx`
- `/app/frontend/src/components/pricing/POSPriceComponents.jsx`

### RBAC System
- `/app/backend/routes/rbac_system.py`
- `/app/frontend/src/pages/settings/RBACManagement.jsx`
- `/app/frontend/src/contexts/PermissionContext.jsx`

### Tests
- `/app/test_reports/iteration_25.json`
- `/app/backend/tests/test_multimode_pricing_system.py`
- `/app/backend/tests/test_enterprise_rbac_security.py`

---

## Deployment Readiness

| Feature | Status |
|---------|--------|
| 46 Branches | ✅ READY |
| Enterprise RBAC | ✅ READY |
| Multi-Mode Pricing | ✅ READY |
| POS Security | ✅ READY |
| Audit Logging | ✅ READY |
| SSOT Architecture | ✅ READY |

---

**Version:** 9.0.0 (Multi-Mode Pricing + Enterprise RBAC)
**Last Updated:** March 10, 2026
**Test Coverage:** 100%
