# OCB TITAN RETAIL AI OPERATING SYSTEM

## Product Requirements Document
### Versi: 2.0 | Update: 2026-03-08

---

## 1. Overview
OCB TITAN adalah sistem retail AI enterprise-grade untuk OCB GROUP yang menggantikan iPOS 5 Ultimate. Sistem mendukung 40+ cabang dengan pembatasan akses per role dan per cabang.

## 2. Tech Stack
- **Frontend:** React.js + Tailwind CSS
- **Backend:** FastAPI (Python)
- **Database:** MongoDB
- **Theme:** Dark mode dengan Red-Gold accent

## 3. Bahasa Sistem
**SEMUA INTERFACE DALAM BAHASA INDONESIA**

---

## 4. Menu Sidebar (15 Menu Lengkap)

| No | Menu | Path | Deskripsi |
|----|------|------|-----------|
| 1 | Dashboard | /dashboard | Ringkasan bisnis & AI Insights |
| 2 | Kasir | /kasir | Point of Sale |
| 3 | Produk | /produk | Manajemen produk |
| 4 | Stok | /stok | Manajemen inventory |
| 5 | Pembelian | /pembelian | Purchase order |
| 6 | Supplier | /supplier | Database supplier |
| 7 | Pelanggan | /pelanggan | CRM & loyalty |
| 8 | Keuangan | /keuangan | Kas & pengeluaran |
| 9 | Akuntansi | /akuntansi | Laba rugi & neraca |
| 10 | Laporan | /laporan | Business reports |
| 11 | AI Bisnis | /ai-bisnis | AI-powered analytics |
| 12 | Cabang | /cabang | Multi-branch management |
| 13 | Pengguna | /pengguna | User management |
| 14 | Hak Akses | /hak-akses | Role & Permission |
| 15 | Pengaturan | /pengaturan | System settings |

---

## 5. Modul yang Diimplementasi

### 5.1 AI Bisnis ✅
Tab yang tersedia:
- **Insight Penjualan** - Analisa trend & pertumbuhan
- **Rekomendasi Restock** - Produk yang perlu di-order
- **Produk Terlaris** - Top selling products
- **Produk Lambat** - Slow moving inventory
- **Analisa Stok** - Stock health analysis
- **Performa Cabang** - Branch comparison (owner/admin only)
- **Rekomendasi Bisnis** - AI-generated action items

### 5.2 Role & Hak Akses ✅
6 Role Default:
| Role | Kode | Akses |
|------|------|-------|
| Pemilik | owner | Akses penuh (15 menu) |
| Administrator | admin | Mengelola sistem (15 menu) |
| Supervisor | supervisor | Operasional cabang (10 menu) |
| Kasir | cashier | Transaksi penjualan (3 menu) |
| Keuangan | finance | Keuangan & laporan (8 menu) |
| Gudang | inventory | Stok & inventory (6 menu) |

Permission per menu:
- Lihat, Tambah, Edit, Hapus, Approve, Export, Cetak, dll.

### 5.3 Pengguna/Karyawan ✅
Fitur lengkap:
- Tambah user baru
- Edit informasi user
- Reset password
- Aktifkan/Nonaktifkan user
- Hapus user (owner only)
- Filter berdasarkan Role, Cabang, Status

Field user:
- Nama lengkap
- Email
- Password
- Nomor HP
- Role
- Cabang
- Status aktif

### 5.4 Pembatasan Akses ✅
**Per Role:**
- Sidebar menu dibatasi berdasarkan role
- Kasir: hanya Dashboard, Kasir, Pelanggan
- Supervisor: 10 menu operasional
- Finance: 8 menu keuangan

**Per Cabang:**
- User cabang hanya melihat data cabangnya
- Dashboard menampilkan nama cabang user
- Transaksi, stok, laporan filtered by branch
- Owner/Admin melihat semua data

---

## 6. Kredensial Test

| Email | Password | Role | Cabang |
|-------|----------|------|--------|
| admin@ocb.com | admin123 | Owner | Semua |
| supervisor@ocb.com | test123 | Supervisor | Cabang 1 |
| kasir@ocb.com | test123 | Kasir | Cabang 1 |
| finance@ocb.com | test123 | Finance | HQ |

---

## 7. API Endpoints

### Roles API
```
GET  /api/roles                    - List all roles
GET  /api/roles/{code}             - Get role detail
POST /api/roles                    - Create role
PUT  /api/roles/{code}             - Update permissions
DEL  /api/roles/{code}             - Delete custom role
GET  /api/roles/permissions-template
```

### AI Business API
```
GET /api/ai-bisnis/insight-penjualan
GET /api/ai-bisnis/rekomendasi-restock
GET /api/ai-bisnis/produk-terlaris
GET /api/ai-bisnis/produk-lambat
GET /api/ai-bisnis/analisa-stok
GET /api/ai-bisnis/performa-cabang
GET /api/ai-bisnis/rekomendasi-bisnis
GET /api/ai-bisnis/dashboard-widget
```

---

## 8. Testing Status

### Iteration 3 Results:
- **Backend:** 100% (21/21 tests passed)
- **Frontend:** 100% - All pages functional

### Features Verified:
- [x] Sidebar 15 menu (Bahasa Indonesia)
- [x] AI Bisnis dengan 7 tab
- [x] Role & Hak Akses (6 roles)
- [x] Pengguna lengkap
- [x] Pembatasan akses per role
- [x] Pembatasan data per cabang
- [x] Dashboard AI Insights widget

---

## 9. Files Reference

### Backend
- `/app/backend/routes/roles.py` - Role & Permission API
- `/app/backend/routes/ai_business.py` - AI Business API
- `/app/backend/routes/users.py` - User Management API

### Frontend
- `/app/frontend/src/components/layout/Sidebar.jsx` - 15 menu
- `/app/frontend/src/pages/AIBusiness.jsx` - AI Bisnis
- `/app/frontend/src/pages/RolePermission.jsx` - Hak Akses
- `/app/frontend/src/pages/Users.jsx` - Pengguna

---

## 10. Future Enhancement
1. WhatsApp AI Integration
2. Export Excel/PDF untuk laporan
3. Backup database otomatis
4. 2FA authentication
5. Audit log viewer
