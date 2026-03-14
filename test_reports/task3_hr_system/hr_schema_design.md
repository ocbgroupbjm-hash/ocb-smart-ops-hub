# HR Enterprise System - Schema Design Document

## Version: 1.0.0
## Blueprint: SUPER DUPER DEWA
## Date: 2026-03-14

---

## Collections Overview

### 1. employees (Employee Master - SSOT)
```json
{
  "id": "uuid",
  "employee_id": "EMP-001",  // NIK Karyawan
  "full_name": "Ahmad Suhendra",
  "email": "ahmad@company.com",
  "phone": "081234567890",
  
  // Employment Info
  "department_id": "uuid",
  "department_name": "Finance",
  "position_id": "uuid", 
  "position_name": "Manager",
  "position_level": 3,
  "branch_id": "uuid",
  "branch_name": "Pusat",
  "employment_type": "permanent | contract | probation",
  "join_date": "2024-01-15",
  "end_date": null,
  "status": "active | inactive | resigned | terminated",
  
  // Payroll Info (SSOT for salary calculation)
  "salary_base": 15000000,
  "bank_name": "BCA",
  "bank_account": "1234567890",
  "bank_account_name": "Ahmad Suhendra",
  
  // Leave Balance
  "leave_balance": {
    "annual": 12,
    "sick": 12,
    "maternity": 90,
    "unpaid": 0
  },
  
  // Audit
  "created_at": "ISO datetime",
  "updated_at": "ISO datetime",
  "created_by": "user_id"
}
```

### 2. attendance_logs
```json
{
  "id": "uuid",
  "employee_id": "uuid",
  "employee_nik": "EMP-001",
  "employee_name": "Ahmad Suhendra",
  "date": "2026-03-14",
  
  // Check-in
  "check_in": "ISO datetime",
  "check_in_time": "08:30:00",
  "check_in_method": "manual | fingerprint | face | gps",
  "check_in_location": "Kantor Pusat",
  "check_in_lat": -6.123456,
  "check_in_lng": 106.123456,
  
  // Check-out
  "check_out": "ISO datetime",
  "check_out_time": "17:30:00",
  "check_out_method": "manual",
  
  // Metrics
  "shift_id": "uuid",
  "is_late": false,
  "late_minutes": 0,
  "work_hours": 8.0,
  "overtime_hours": 0.5,
  "status": "present | absent | leave | sick | holiday"
}
```

### 3. leave_requests
```json
{
  "id": "uuid",
  "request_no": "LV-20260314-0001",
  "employee_id": "uuid",
  "employee_name": "Ahmad Suhendra",
  
  "leave_type_id": "uuid",
  "leave_type_name": "Cuti Tahunan",
  "leave_type_code": "ANNUAL",
  
  "start_date": "2026-03-20",
  "end_date": "2026-03-22",
  "total_days": 2,
  "reason": "Keperluan keluarga",
  
  "status": "pending | approved | rejected | cancelled",
  "approved_by": "user_id",
  "approved_at": "ISO datetime",
  "approval_notes": "Disetujui"
}
```

### 4. payroll (Payment Header)
```json
{
  "id": "uuid",
  "batch_id": "uuid",
  "batch_no": "PAY-20260314-0007",
  "period": "2026-03",
  "period_month": 3,
  "period_year": 2026,
  
  "employee_id": "uuid",
  "employee_nik": "EMP-001",
  "employee_name": "Ahmad Suhendra",
  
  // Salary Components
  "salary_base": 15000000,
  "total_allowances": 500000,
  "total_deductions": 155000,
  "gross_salary": 15500000,
  "tax_amount": 50000,
  "net_salary": 15295000,
  
  // Attendance Metrics
  "attendance": {
    "present_days": 22,
    "late_days": 1,
    "total_work_hours": 176
  },
  "leave": {
    "paid_leave_days": 0,
    "unpaid_leave_days": 0
  },
  
  // Status
  "status": "draft | posted | paid",
  "journal_id": "JV-20260314-0014"
}
```

### 5. payroll_items (Detail Komponen)
```json
{
  "id": "uuid",
  "payroll_id": "uuid",
  "employee_id": "uuid",
  "item_code": "MEAL",
  "item_name": "Tunjangan Makan",
  "type": "allowance | deduction | tax",
  "amount": 500000,
  "is_taxable": true
}
```

---

## Business Rules

### Employee Master (SSOT)
1. employee_id (NIK) harus unik
2. salary_base adalah sumber kebenaran untuk perhitungan payroll
3. leave_balance di-maintain otomatis saat cuti diapprove
4. Soft delete only - status = inactive

### Attendance
1. Satu check-in per hari per karyawan
2. Keterlambatan dihitung dari shift start_time
3. work_hours = check_out - check_in (dalam jam)
4. Overtime dicatat manual atau dari shift

### Leave Management
1. Cek saldo cuti sebelum submit
2. Tidak boleh overlap dengan cuti lain
3. Update saldo otomatis saat approved
4. Approval wajib untuk tipe tertentu

### Payroll Engine
1. SSOT: salary_base dari Employee Master
2. Komponen tunjangan/potongan dari payroll_components
3. PPh 21 dihitung sederhana (5% di atas PTKP)
4. Auto-create journal saat posting:
   - Debit: Beban Gaji
   - Credit: Kas/Bank
   - Credit: Hutang PPh 21

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| /api/hr/employees | GET, POST | List/Create employees |
| /api/hr/employees/{id} | GET, PUT, DELETE | CRUD single employee |
| /api/hr/departments | GET, POST | Departments management |
| /api/hr/positions | GET, POST | Positions management |
| /api/hr/attendance/checkin | POST | Record check-in |
| /api/hr/attendance/checkout | POST | Record check-out |
| /api/hr/attendance/today | GET | Today's summary |
| /api/hr/attendance/report | GET | Period report |
| /api/hr/leave/types | GET, POST | Leave types |
| /api/hr/leave/requests | GET, POST | Leave requests |
| /api/hr/leave/requests/{id}/approve | PUT | Approve/reject |
| /api/hr/leave/balance/{employee_id} | GET | Leave balance |
| /api/hr/payroll/components | GET, POST | Payroll components |
| /api/hr/payroll/run | POST | Run payroll calculation |
| /api/hr/payroll/post/{batch_id} | POST | Post payroll + journal |
| /api/hr/payroll/{period} | GET | Get payroll data |
| /api/hr/payroll/slip/{id} | GET | Get payslip detail |

---

*Document generated by OCB TITAN ERP HR System*
