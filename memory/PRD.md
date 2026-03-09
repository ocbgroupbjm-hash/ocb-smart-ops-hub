# OCB GROUP SUPER ERP + AI TITAN WAR ROOM OPERATING SYSTEM
## Product Requirements Document (PRD)

---

## 1. Overview

**System Name:** OCB GROUP SUPER ERP + AI TITAN WAR ROOM  
**Version:** 2.0  
**Last Updated:** March 10, 2026  

The OCB GROUP SUPER ERP is a comprehensive, enterprise-grade system that serves as the central command center for OCB GROUP business operations. It integrates retail operations, finance, HR management, and advanced AI analytics into a single unified platform.

---

## 2. Core Architecture

### Tech Stack
- **Backend:** FastAPI (Python 3.12+)
- **Frontend:** React 18 with TailwindCSS
- **Database:** MongoDB (Motor async driver)
- **Architecture:** Multi-tenant with dynamic database connections

### Key Directories
```
/app/
├── backend/
│   ├── models/erp_models.py      # All ERP data models
│   ├── routes/
│   │   ├── erp_operations.py     # Master data, Setoran, Selisih Kas
│   │   ├── attendance.py         # GPS attendance system
│   │   ├── payroll.py            # Integrated payroll
│   │   ├── war_room_v2.py        # Owner command center
│   │   ├── erp_reports.py        # Comprehensive reporting
│   │   └── ... (other routes)
│   └── server.py
└── frontend/
    └── src/
        ├── pages/
        │   ├── SetoranHarian.jsx    # Daily deposits
        │   ├── SelisihKas.jsx       # Cash variance
        │   ├── Employees.jsx        # Employee management
        │   ├── Absensi.jsx          # GPS attendance
        │   ├── Payroll.jsx          # Payroll management
        │   ├── WarRoomV2.jsx        # Owner dashboard
        │   ├── ERPDashboard.jsx     # ERP summary
        │   ├── MasterERP.jsx        # Master data management
        │   └── ERPReports.jsx       # Reports
        └── components/
```

---

## 3. Implemented Modules (Phase 1)

### 3.1 Master ERP ✅
- **Employees:** Complete CRUD with personal info, employment details, salary
- **Master Shift:** Shift management (Pagi, Siang, Malam, Full Day)
- **Master Jabatan:** Position/role hierarchy with levels
- **Master Lokasi Absensi:** GPS coordinates for attendance validation
- **Master Payroll Rules:** Salary structure per position

### 3.2 Setoran Harian (Daily Deposits) ✅
- Input daily cash deposits from branches
- Breakdown by payment method (Cash, Transfer, E-Wallet, Debit, Credit, Piutang)
- Auto-calculate selisih kas (cash variance)
- Verification and approval workflow
- Filter by date, branch, status

### 3.3 Selisih Kas (Cash Variance Tracking) ✅
- Track plus/minus cash discrepancies
- Resolution options: Beban Perusahaan, Piutang Karyawan, Potong Gaji
- Link to payroll for salary deductions
- Audit trail for all variances

### 3.4 Attendance System ✅
- GPS-based check-in/check-out
- Location validation against registered coordinates
- Auto-detect late arrivals (telat_menit calculation)
- Early leave and overtime tracking
- Support for izin/cuti/sakit with approval workflow
- Daily and monthly summaries

### 3.5 Payroll Terintegrasi ✅
- Period-based payroll (monthly)
- Auto-generate based on:
  - Attendance data (hadir, telat, alpha)
  - Overtime hours
  - Cash variance deductions (minus kas)
- Components: Gaji Pokok, Tunjangan, Bonus, Potongan
- Slip gaji generation
- Approval and payment tracking

### 3.6 War Room Command Center ✅
- Real-time owner dashboard
- KPIs: Sales, Setoran, Attendance, Alerts
- Top/Bottom branch rankings
- Problem employee tracking
- 7-day trend visualization
- Live activity feed
- Target achievement progress

### 3.7 AI Insights & Fraud Detection ✅
- AI-generated business insights
- Pattern detection: Minus berulang, Sering telat, Penjualan turun
- Severity-based alerts (Critical, Warning, Info)
- Automated recommendations

### 3.8 Comprehensive Reports ✅
- Executive Summary (Daily & Monthly)
- Setoran Reports (by date, by branch)
- Selisih Kas Reports (by employee, by branch)
- Attendance Reports (monthly recap)
- Payroll Reports (annual summary)

### 3.9 System Alerts ✅
- Real-time alert creation for:
  - Cash variance (minus kas)
  - Late arrivals (>30 min)
  - Fraud patterns detected
- Alert resolution tracking

---

## 4. API Endpoints

### ERP Operations
- `GET/POST /api/erp/employees` - Employee CRUD
- `GET/POST /api/erp/master/shifts` - Shift management
- `GET/POST /api/erp/master/jabatan` - Position management
- `GET/POST /api/erp/master/lokasi-absensi` - GPS locations
- `GET/POST /api/erp/master/payroll-rules` - Payroll rules
- `GET/POST /api/erp/setoran` - Daily deposits
- `GET/PUT /api/erp/selisih-kas` - Cash variance
- `GET /api/erp/alerts` - System alerts
- `GET /api/erp/dashboard/summary` - ERP summary

### Attendance
- `POST /api/attendance/check-in` - Check-in with GPS
- `POST /api/attendance/check-out` - Check-out with GPS
- `GET /api/attendance/list` - Attendance list
- `GET /api/attendance/employee/{id}` - Employee attendance
- `GET /api/attendance/summary/daily` - Daily summary
- `POST /api/attendance/izin` - Leave request

### Payroll
- `GET/POST /api/payroll/periods` - Payroll periods
- `POST /api/payroll/periods/{id}/generate` - Generate payroll
- `POST /api/payroll/periods/{id}/approve` - Approve payroll
- `POST /api/payroll/periods/{id}/pay` - Mark as paid
- `GET /api/payroll/details` - Payroll details
- `GET /api/payroll/slip/{id}` - Salary slip

### War Room
- `GET /api/war-room/dashboard` - Main dashboard
- `GET /api/war-room/cabang-belum-setor` - Pending branches
- `GET /api/war-room/karyawan-tidak-absen` - Absent employees
- `GET /api/war-room/selisih-pending` - Pending variances
- `GET /api/war-room/fraud-detection` - Fraud alerts
- `GET /api/war-room/ai-insights` - AI insights
- `GET /api/war-room/live-feed` - Live activity

### Reports
- `GET /api/reports/executive/daily` - Daily executive summary
- `GET /api/reports/executive/monthly` - Monthly executive summary
- `GET /api/reports/setoran/daily` - Daily setoran report
- `GET /api/reports/setoran/monthly` - Monthly setoran report
- `GET /api/reports/selisih/by-employee` - Selisih by employee
- `GET /api/reports/selisih/by-branch` - Selisih by branch
- `GET /api/reports/attendance/monthly` - Monthly attendance
- `GET /api/reports/payroll/summary` - Annual payroll summary

---

## 5. Testing Credentials

- **Email:** ocbgroupbjm@gmail.com
- **Password:** admin123
- **Login Flow:** Select Business (OCB GROUP) → Enter Credentials

---

## 6. Future Roadmap (P1-P2)

### Phase 2 (P1)
- [ ] AI Business Analyst integration with LLM
- [ ] Real-time WhatsApp notifications
- [ ] Advanced approval workflows
- [ ] Mobile-responsive attendance app
- [ ] Export to Excel/PDF

### Phase 3 (P2)
- [ ] AI Auditor automated checks
- [ ] Multi-level approval matrix
- [ ] Budget vs Actual tracking
- [ ] Branch performance scoring
- [ ] Employee KPI dashboard

---

## 7. Change Log

### March 10, 2026
- ✅ Implemented Phase 1 SUPER ERP modules
- ✅ Created Master ERP (Employees, Shifts, Jabatan, Lokasi, Payroll Rules)
- ✅ Built Setoran Harian with auto selisih calculation
- ✅ Developed Selisih Kas tracking with resolution workflow
- ✅ Implemented GPS-based Attendance system
- ✅ Built integrated Payroll with attendance & minus kas deductions
- ✅ Created War Room V2 Command Center
- ✅ Added AI Insights and Fraud Detection
- ✅ Built Comprehensive Reporting system
- ✅ All frontend pages with professional UI

### March 9, 2026
- Fixed multi-business database switching
- Implemented "Select Business First" login flow
- Created WhatsApp webhook for n8n integration
- Completed 40 branch seeding script

---

## 8. Known Issues & Notes

- QRIS payment integration is **MOCKED**
- Branch data is seeded/dummy for testing
- Photo upload in attendance stores filename only (no actual file storage)
- All existing POS, inventory, accounting features preserved
