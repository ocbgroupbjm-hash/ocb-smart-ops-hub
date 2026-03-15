# OCB TITAN ERP - SYSTEM ARCHITECT GOVERNANCE RULEBOOK
## SUPERDEWA ULTRA GOVERNANCE - FINAL VERSION

---

> **DOKUMEN INI ADALAH RULEBOOK TERTINGGI**
> Tidak ada level di atas dokumen ini.
> Semua developer, system architect, AI agent, DevOps engineer, dan integrator WAJIB mengikuti aturan ini tanpa pengecualian.

---

## TUJUAN GOVERNANCE

1. Menjaga stabilitas sistem ERP
2. Memastikan integritas akuntansi
3. Mencegah kerusakan data lintas tenant
4. Memastikan audit dan kepatuhan
5. Menjaga keamanan sistem enterprise

---

# SYSTEM LAWS

## SYSTEM LAW 1: DATABASE TESTING LAW

### Aturan Wajib
- **SEMUA pengujian sistem HANYA BOLEH dilakukan pada database pilot:**
  ```
  OCB_GROUP DATABASE: ocb_titan
  ```
- **DILARANG** melakukan testing langsung pada tenant lain

### Flow Testing Wajib
```
1. Development (implement)
2. Testing di ocb_titan
3. Generate evidence
4. Validasi System Architect
5. Lock blueprint version
6. Sync ke semua tenant
```

### Larangan
- Deployment DILARANG tanpa evidence test
- Testing di tenant production DILARANG

---

## SYSTEM LAW 2: MULTI-TENANT CONSISTENCY

### Aturan Wajib
- Semua database tenant HARUS memiliki versi sistem yang SAMA
- Tidak ada tenant yang boleh memiliki blueprint berbeda

### Proses Update Sistem
```
1. Update dilakukan di ocb_titan terlebih dahulu
2. Testing diselesaikan
3. Blueprint version di-lock
4. Sync ke semua tenant
```

### Yang BOLEH Di-sync ke Tenant Lain
- Code
- Route
- Process logic
- Schema
- Blueprint version
- Menu/UI

### Yang TIDAK BOLEH Diubah saat Rollout
- Daftar items operasional
- Transaksi
- Customer data
- Supplier data
- Jurnal historis
- Isi data operasional tenant

---

## SYSTEM LAW 3: ACCOUNTING IMMUTABILITY LAW

### Aturan Wajib
- **Semua jurnal yang dibuat oleh sistem ERP TIDAK BOLEH DIHAPUS**

### Jurnal Sistem Termasuk:
- Pembelian
- Penjualan
- Hutang (AP)
- Piutang (AR)
- Inventory
- Payroll
- Kas/Bank

### Jika Terjadi Error
- Metode koreksi HARUS: **REVERSAL JOURNAL**
- BUKAN delete
- BUKAN edit langsung

---

## SYSTEM LAW 4: TRIAL BALANCE INTEGRITY

### Aturan Wajib
- Trial Balance HARUS SELALU balance: **Debit = Credit**

### Jika Sistem Mendeteksi Ketidakseimbangan:
```
1. Posting transaksi HARUS dihentikan
2. Audit error HARUS muncul
3. Transaksi TIDAK BOLEH diproses
```

---

## SYSTEM LAW 5: AUDIT LOG LAW

### Aturan Wajib
Setiap perubahan data penting HARUS dicatat dengan:
- User yang melakukan
- Timestamp
- Aksi yang dilakukan
- Field yang diubah
- Nilai lama (old value)
- Nilai baru (new value)

---

## SYSTEM LAW 6: DATE STANDARDIZATION

### Aturan Wajib
- Semua tanggal HARUS format: **DD/MM/YYYY**
- Jika field tanggal kosong, sistem HARUS auto-fill tanggal saat ini

---

## SYSTEM LAW 7: SERIAL NUMBER LAW

### Aturan Wajib
- Sistem HARUS support input SN_AWAL dan SN_AKHIR
- Sistem HARUS auto-generate sequence

---

## SYSTEM LAW 8: RBAC SECURITY LAW

### Aturan Wajib
- ERP HARUS menggunakan Role-Based Access Control (RBAC)
- Semua API endpoint HARUS verifikasi:
  - Role permission
  - Tenant identity
- Operasi sensitif HARUS require specific roles

---

## SYSTEM LAW 9: DATA EXPORT LAW

### Aturan Wajib
- Sistem HARUS menyediakan export data untuk modul:
  - Purchasing
  - Sales
  - Inventory
  - Accounting
  - HR
- Format export: **.xlsx**

---

## SYSTEM LAW 10: DISASTER RECOVERY LAW

### Aturan Wajib
- Implementasi backup otomatis:
  - Daily backup
  - Weekly backup
  - Monthly backup
- Backup HARUS dapat di-restore kapan saja

---

## SYSTEM LAW 11: AI GOVERNANCE LAW

### Aturan Wajib
- AI HARUS memiliki akses **READ ONLY**
- AI TIDAK BOLEH menulis langsung ke database
- Semua keputusan AI HARUS di-log ke `ai_decision_log`

---

## SYSTEM LAW 12: EVIDENCE LAW

### Aturan Wajib
- Semua perubahan sistem HARUS memiliki evidence
- Evidence HARUS disimpan di: `/app/test_reports/`
- Deployment DILARANG tanpa evidence

---

# SSOT (SINGLE SOURCE OF TRUTH)

## Inventory SSOT
- **Collection:** `stock_movements`
- Semua perubahan stok HARUS melalui stock_movements
- TIDAK BOLEH write stok langsung ke product master

## Accounting SSOT
- **Collection:** `journal_entries`
- Semua transaksi keuangan HARUS membuat journal entry
- Journal POSTED adalah immutable

---

# MODULE-SPECIFIC RULES

## DATA SHEET MODULE

### Fungsi Yang Benar
- Data Sheet = **Global Item Editor**
- Fungsi: Edit, Bulk Edit, Bulk Update, Export, Search, Filter

### Yang TIDAK BOLEH
- Create new item (harus via Master Data → Items)
- Delete item
- Create transaction

---

## AP/AR MODULE (HUTANG & PIUTANG)

### Rule untuk Transaksi LUNAS
- Invoice yang sudah LUNAS **TIDAK BOLEH di-edit langsung**
- Koreksi HARUS melalui: **REVERSAL JOURNAL**

### Flow Koreksi
```
1. Buat reversal journal
2. Buat payment correction
3. Update invoice status
4. Audit log tercatat
```

### Struktur Pembayaran Wajib
- Payment header
- Payment allocation
- Jika tidak ada allocation, aging akan rusak

---

## ASSEMBLY MODULE (PERAKITAN/BOM)

### Struktur Database
```
assembly_formulas      - Definisi resep/BOM
assembly_components    - Daftar bahan per formula
assembly_transactions  - Eksekusi perakitan
assembly_logs          - Audit perubahan
```

### Formula Requirements
- Minimal 1 komponen (direkomendasikan 2+)
- Produk hasil tidak boleh sama dengan komponen
- Result quantity > 0
- Quantity required > 0

### Status Transaksi
- **DRAFT:** Dapat di-edit dan di-delete
- **POSTED:** TIDAK BOLEH di-edit/delete, HARUS reversal
- **REVERSED:** Status final setelah koreksi
- **CANCELLED:** Soft delete dari DRAFT

### Stock Movement Types
```
ASSEMBLY_CONSUME          - Komponen keluar (POST)
ASSEMBLY_PRODUCE          - Hasil masuk (POST)
ASSEMBLY_CONSUME_REVERSAL - Komponen kembali (REVERSAL)
ASSEMBLY_PRODUCE_REVERSAL - Hasil dibatalkan (REVERSAL)
```

### Journal Entry
```
POST:
  Debit:  Persediaan Barang Jadi (1-1400)
  Credit: Persediaan Bahan Baku (1-1300)

REVERSAL:
  Kebalikan dari POST
```

---

# HR MODULE BLUEPRINT

## Employee Master Data (SSOT)
**Collection:** `employees`

### Fields Wajib
- employee_id (unique)
- employee_code
- full_name
- nik (NIK KTP)
- email
- phone
- address
- position_id
- department_id
- branch_id
- join_date
- status (ACTIVE/PROBATION/RESIGNED/TERMINATED)
- salary_base
- bank_account
- tax_status
- bpjs_number

## Attendance System
**Collection:** `attendance_logs`

### Methods
- GPS
- Face Recognition
- QR Code
- Manual Override

### Status
- ON_TIME
- LATE
- ABSENT
- LEAVE
- SICK

### Rules
- Late tolerance = 10 minutes
- Overtime start = 30 minutes after shift

## Shift Management
**Collection:** `shifts`

### Shifts
- SHIFT PAGI: 08:00 - 16:00
- SHIFT SIANG: 14:00 - 22:00
- SHIFT MALAM: 22:00 - 06:00

## Leave Management
**Collection:** `leave_requests`

### Types
- Annual Leave
- Sick Leave
- Maternity Leave
- Unpaid Leave
- Emergency Leave

### Approval Flow
```
Employee → Manager → HR
```

## Payroll Engine
**Collections:** `payroll`, `payroll_items`

### Components
- Base Salary
- Overtime
- Bonus
- Allowance
- BPJS
- Tax
- Deduction

### Formulas
```
Gross Salary = Base + Overtime + Allowance + Bonus
Net Salary = Gross - Tax - BPJS - Deduction
```

### Accounting Integration
- Automatic journal: Debit Salary Expense, Credit Cash/Bank

## HR RBAC Roles
- **HR_ADMIN:** Full access
- **HR_MANAGER:** Employee + Payroll + KPI
- **HR_STAFF:** Attendance + Employee
- **EMPLOYEE:** Self-service only

---

# DEFINITION OF DONE

Task dianggap SELESAI hanya jika memiliki evidence berikut:

| Evidence | Wajib |
|----------|-------|
| API test result | ✓ |
| UI screenshot | ✓ |
| Audit log proof | ✓ |
| Journal proof | ✓ |
| Tenant sync report | ✓ |
| Rollback plan | ✓ |

**Tanpa evidence di atas, task dianggap BELUM SELESAI.**

---

# SYSTEM CONTROL MATRIX

| Control Area | Status |
|--------------|--------|
| Database Governance | MANDATORY |
| Accounting Integrity | MANDATORY |
| RBAC Security | MANDATORY |
| Audit Log | MANDATORY |
| Evidence Based Deployment | MANDATORY |
| Multi Tenant Sync | MANDATORY |

---

# QUICK REFERENCE

## Tenant List
- `ocb_titan` (PILOT - untuk testing)
- `ocb_unit_4`
- `ocb_unt_1`
- `erp_db`

## Test Credentials (ocb_titan)
- Email: `ocbgroupbjm@gmail.com`
- Password: `admin123`
- Role: `owner`

## Evidence Directory
```
/app/test_reports/
```

## API Prefixes
- Legacy Assembly: `/api/assembly/*`
- Enterprise Assembly: `/api/assembly-enterprise/*`
- Payment Allocation: `/api/payment-allocation/*`
- Master Data: `/api/master/*`
- Products: `/api/products/*`
- Employees: `/api/employees/*`
- HR: `/api/hr/*`

---

# PESAN FINAL

> **Semua trial dan pengujian HANYA BOLEH dilakukan pada database OCB_GROUP / ocb_titan.**
> 
> **Setelah PASS, perubahan boleh di-rollout ke tenant lain HANYA dalam bentuk update code, process logic, schema, route, menu, dan blueprint version.**
> 
> **DILARANG mengubah isi data operasional tenant lain.**
> 
> **Tidak ada status SELESAI tanpa EVIDENCE nyata.**

---

*Document Version: SUPERDEWA ULTRA - FINAL*
*Last Updated: 2026-03-16*
*Source: System Architect PDF Documents*
