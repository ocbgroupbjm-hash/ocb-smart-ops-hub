# OCB TITAN AI - GLOBAL RETAIL OPERATING SYSTEM
## Product Requirements Document (PRD)

### Overview
Enterprise AI-powered retail operating system for OCB GROUP managing multi-branch retail operations with comprehensive HR, Payroll, Sales, Inventory, and AI analytics capabilities.

---

## LATEST UPDATE: March 10, 2026

### ✅ RBAC System - COMPLETE

**Enterprise Role-Based Access Control (RBAC) System telah diimplementasikan dengan fitur lengkap:**

#### Backend (100% Complete)
- **95 modul** dengan permission terpisah
- **11 aksi**: view, create, edit, delete, approve, export, print, lock_number, lock_date, override_price, override_discount
- **13 role default**: Super Admin, Owner, Direktur, Manager, Supervisor, Admin, Kasir, Gudang, Akunting, Marketing, Viewer, Finance, Inventory
- **Audit Log**: Mencatat semua aktivitas user dengan timestamp, IP address, module, dan action

#### API Endpoints
| Endpoint | Description |
|----------|-------------|
| POST /api/rbac/init | Initialize RBAC system |
| GET /api/rbac/roles | List all roles |
| GET/POST/PUT/DELETE /api/rbac/roles/{id} | Role CRUD |
| GET /api/rbac/permissions/modules | List all modules & actions |
| GET /api/rbac/permissions/matrix/{role_id} | Get permission matrix |
| POST /api/rbac/permissions/{role_id} | Update permissions |
| POST /api/rbac/permissions/{role_id}/bulk | Bulk update |
| GET /api/rbac/user/permissions | Get current user permissions |
| PUT /api/rbac/user/{id}/role | Assign role to user |
| GET /api/rbac/check | Check specific permission |
| GET /api/rbac/audit-logs | View audit trail |

#### Frontend UI (100% Complete)
1. **Permission Matrix Tab**
   - Role list sidebar dengan 13 roles
   - Grid 95 modules x 7 actions dengan checkbox
   - Category grouping (Master Data, Pembelian, Penjualan, dll)
   - Search & filter by category
   - Quick actions (enable/disable all)
   - Save pending changes

2. **Assign Role Tab**
   - User list dengan current role badge
   - Role dropdown selection
   - Branch access control (semua/specific)
   - Save button

3. **Audit Log Tab**
   - Log table dengan filter
   - Columns: Waktu, User, Aksi, Modul, Deskripsi, IP
   - Action filter dropdown

#### Frontend Permission Control
- `usePermission` hook untuk check permission
- `PermissionGate` component untuk conditional rendering
- `hasPermission(module, action)` function
- Tombol Edit/Delete/Tambah tersembunyi jika tidak punya permission

#### API Protection
- `require_permission(module, action)` dependency
- Auto-log activity saat delete
- 403 response jika tidak ada permission

---

## SSOT Architecture - COMPLETE

**Single Source of Truth untuk data integrity:**

- **Stock**: Dihitung dari `stock_movements` collection
- **Item Branch Config**: Hanya min/max di `item_branch_stock`
- **No duplicate stock**: `products.stock` deprecated

---

## System Stats

| Metric | Value |
|--------|-------|
| Total Branches | 46 |
| Total Employees | 37 |
| Total Products | 32 |
| RBAC Modules | 95 |
| RBAC Actions | 11 |
| RBAC Roles | 13 |

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

### 3. Master Data (CRUD Verified)
- **Daftar Item**: ERP-style dengan comprehensive filters
- Per-Branch Stock dengan min/max configuration
- AI Photo Studio dengan image editing
- Kartu Stok (Stock Card)

### 4. Persediaan
- Stok Masuk/Keluar
- Transfer Stok
- Stok Per Cabang
- Kartu Stok dengan running balance

### 5. HR & Payroll
- Data Karyawan: 37 employees
- Absensi: GPS-based
- Payroll Auto
- AI Performance

### 6. RBAC System ✅ NEW
- Role Management
- Permission Matrix
- User Role Assignment
- Audit Log

---

## Key Files

### Backend
- `/app/backend/routes/rbac_system.py` - Complete RBAC system (950+ lines)
- `/app/backend/routes/ssot_service.py` - Single Source of Truth service
- `/app/backend/routes/master_erp.py` - Master data with RBAC protection

### Frontend
- `/app/frontend/src/pages/settings/RBACManagement.jsx` - RBAC UI
- `/app/frontend/src/contexts/PermissionContext.jsx` - Permission hooks
- `/app/frontend/src/pages/master/MasterItems.jsx` - With permission control

---

## Test Reports
- `/app/test_reports/iteration_23.json` - RBAC system verification (100% pass)

---

## Deployment Readiness

| Aspect | Status |
|--------|--------|
| 46 Branches Support | READY |
| RBAC System | READY |
| Permission Control | READY |
| Audit Logging | READY |
| SSOT Architecture | READY |

---

**Version:** 7.0.0 (RBAC System Complete)
**Last Updated:** March 10, 2026
