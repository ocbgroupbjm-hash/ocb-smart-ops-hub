# OCB TITAN AI - ENTERPRISE RETAIL OPERATING SYSTEM
## Product Requirements Document (PRD)

### Overview
Enterprise AI-powered retail operating system dengan **Supreme RBAC Security**, **Multi-Mode Pricing**, **ERP-Grade Item Management**, dan **Operasional Setoran Harian**.

---

## LATEST UPDATE: March 10, 2026

### ✅ OPERASIONAL SETORAN HARIAN (Daily Cash Deposit) - COMPLETE (100%)

#### Key Features Implemented
1. **Strict Role-Based Access Control**
   - KASIR: Only see/create own deposits (filtered by user_id + branch_id)
   - SUPERVISOR: View/verify all deposits within branch
   - MANAGER/OWNER: View all deposits across branches
   - FAIL-SAFE: Default DENY if user mapping incorrect

2. **No Manual Sales Input**
   - Auto-pull dari transaksi penjualan yang sudah ada
   - Prevents fraud dari input manual
   - Sales transaction marked with deposit_id setelah di-include

3. **Full Status Workflow**
   - Draft → Pending → Received → Verified → Approved → Posted
   - Each status change logged in audit trail
   - Cancel only allowed for draft/pending

4. **Correct Accounting Journal Entries**
   - Debit: Kas Kecil Pusat (actual received)
   - Debit: Selisih Kurang Kas (if shortage)
   - Credit: Selisih Lebih Kas (if overage)
   - Credit: Kas Cabang (expected amount)
   - Configurable account mapping per branch

5. **Security Features**
   - Server-side JWT validation on every request
   - User scope derived from session, not frontend params
   - IP address logging for audit trail
   - Activity logging with severity levels

#### API Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| /api/deposit/init | POST | Initialize system with default accounts |
| /api/deposit/seed-sales | POST | Create sample sales for testing |
| /api/deposit/my-sales | GET | Get un-deposited sales for current user |
| /api/deposit/create | POST | Create new deposit (auto-pull sales) |
| /api/deposit/{id} | GET | Get deposit detail |
| /api/deposit/{id} | PUT | Update cash received & notes |
| /api/deposit/{id}/receive | POST | Mark as received |
| /api/deposit/{id}/verify | POST | Verify deposit |
| /api/deposit/{id}/approve | POST | Approve deposit |
| /api/deposit/{id}/post | POST | Post to accounting journal |
| /api/deposit/{id}/cancel | POST | Cancel deposit |
| /api/deposit/list | GET | List deposits with filters |
| /api/deposit/dashboard/summary | GET | Dashboard metrics |
| /api/deposit/reconciliation/summary | GET | Reconciliation report |

#### Frontend Components
- `/pages/operasional/SetoranHarian.jsx` - List page with dashboard cards
- `/components/operasional/SetoranForm.jsx` - Form modal with 4 tabs
  - Ringkasan: Summary with READ-ONLY branch/cashier info
  - Transaksi: List of included sales transactions
  - Selisih: Difference analysis
  - Jurnal: Accounting journal entries

#### Test Results
| Test Category | Result |
|---------------|--------|
| Backend API | 100% PASS (20/20) |
| Frontend UI | 100% PASS |
| Security (RBAC) | PASS - Kasir can only access own deposits |
| Accounting | PASS - Journal entries balanced |

---

### ✅ FORM TAMBAH ITEM REVISI - COMPLETE (100%)

#### Struktur Form Baru (4 Tabs)
- TAB 1: Data Umum (Kode, Nama, Tipe, Kategori, Satuan, Merek, etc.)
- TAB 2: Harga Jual (Multi-Mode Pricing integrated)
- TAB 3: Stok & Gudang
- TAB 4: Akunting

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
| RBAC Modules | 104 (including Setoran Harian) |
| RBAC Actions | 13 |
| Pricing Modes | 4 |
| Customer Levels | 5 |

---

## Key Components

### Setoran Harian (NEW)
- `/app/backend/routes/deposit_system.py`
- `/app/frontend/src/pages/operasional/SetoranHarian.jsx`
- `/app/frontend/src/components/operasional/SetoranForm.jsx`

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
| 27 | Setoran Harian | 100% PASS |

---

## Test Credentials

| Role | Email | Password |
|------|-------|----------|
| Owner/Admin | ocbgroupbjm@gmail.com | admin123 |
| Kasir Test | kasir_test@ocb.com | password123 |

---

## Deployment Readiness

| Feature | Status |
|---------|--------|
| Global Master Item | ✅ READY |
| Form 4 Tabs | ✅ READY |
| Multi-Mode Pricing | ✅ READY |
| Enterprise RBAC | ✅ READY |
| Branch Stock Module | ✅ READY |
| Setoran Harian | ✅ READY |

---

## BACKLOG / Future Tasks

### P1 - High Priority
- [ ] Advanced reconciliation dashboard
- [ ] Security alerts for large discrepancies
- [ ] Export laporan setoran (Excel/PDF)

### P2 - Medium Priority
- [ ] Audit trail UI tab
- [ ] Shift management integration
- [ ] Multi-currency support

### P3 - Nice to Have
- [ ] Mobile-optimized setoran form
- [ ] WhatsApp notification for pending deposits
- [ ] Dashboard analytics with trends

---

**Version:** 11.0.0 (Setoran Harian Module Added)
**Last Updated:** March 10, 2026
**Test Coverage:** 100%
