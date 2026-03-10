# OCB TITAN AI - GLOBAL RETAIL OPERATING SYSTEM
## Product Requirements Document (PRD)

### Overview
Enterprise AI-powered retail operating system for OCB GROUP managing multi-branch retail operations with comprehensive HR, Payroll, Sales, and AI analytics capabilities.

### Core Modules Implemented

#### 1. HR & Payroll System (Phase 4 - COMPLETE)

**Payroll Otomatis dari Absensi** ✅
- Calculate payroll (daily/monthly) based on attendance data
- Track: days present (hadir), alpha, leave (izin), sick days (sakit), lateness, overtime
- Automatic deductions for lateness (per minute rate) and absences (per day rate)
- Automatic bonuses for full attendance
- Final take-home pay calculation

**Bonus Otomatis dari Penjualan** ✅
- Calculate bonuses based on individual sales data
- Commission rate: 1% of sales (max 2 million)
- Target bonus: 500k if sales >= 50 million
- Integrated into payroll calculation

**AI Analisa Performa Karyawan** ✅
- AI module analyzing employee performance
- Data sources: attendance, sales, KPIs, minus kas
- Performance categories: ELITE, SANGAT_BAIK, BAIK, NORMAL, PERLU_PERHATIAN, BURUK
- Automated strengths/weaknesses analysis
- AI recommendations (bonus, training, promotion)

**Slip Gaji Otomatis** ✅
- Detailed payslips with all earnings/deductions
- Export formats: PDF, Excel, CSV, JSON
- Individual and bulk generation
- Attendance summary included

**Dummy Data Generator** ✅
- 5 branches, 8 job positions, 24 employees
- 1 month of attendance data (288+ records)
- 1 month of sales transactions (1632+ records)
- Realistic salary and attendance patterns

#### 2. AI War Room & CFO Dashboard (Phase 3 - COMPLETE)
- Real-time branch monitoring
- AI fraud detection
- CFO financial analytics
- Store prediction

#### 3. Core ERP Modules (COMPLETE)
- POS/Sales
- Inventory Management
- Purchase Management
- Finance/Accounting
- CRM with AI

### API Endpoints (Phase 4)

**Seed Data:**
- POST `/api/seed/all` - Generate all dummy data
- POST `/api/seed/branches`, `/api/seed/employees`, etc.

**Payroll Auto:**
- GET `/api/payroll-auto/calculate/{employee_id}` - Calculate individual payroll
- GET `/api/payroll-auto/calculate-all` - Calculate all employees
- GET `/api/payroll-auto/calculate-branch/{branch_id}` - Calculate by branch
- POST `/api/payroll-auto/save/{employee_id}` - Save payroll result
- GET `/api/payroll-auto/results` - Get saved payroll

**AI Employee Performance:**
- GET `/api/ai-employee/analyze/{employee_id}` - Analyze individual
- GET `/api/ai-employee/analyze-all` - Analyze all employees
- GET `/api/ai-employee/ranking` - Get employee ranking
- POST `/api/ai-employee/save-analysis/{employee_id}` - Save analysis
- GET `/api/ai-employee/history/{employee_id}` - Get analysis history

**Payslip Files:**
- GET `/api/payroll-files/payslip/{employee_id}` - Generate payslip (json/pdf/excel)
- GET `/api/payroll-files/report/branch/{branch_id}` - Branch payroll report
- GET `/api/payroll-files/report/company` - Company-wide report

### Frontend Pages (Phase 4)

**AI Performance Analysis** (`/ai-performance`)
- Category summary cards (ELITE to BURUK)
- Employee ranking list with scores
- Detail panel with metrics, strengths, weaknesses, recommendations
- Filter by period (1/3/6 months) and branch

**Payroll Otomatis** (`/payroll-auto`)
- Summary cards (total employees, gross, THP)
- Employee payroll list with attendance metrics
- Detail slip gaji panel
- Download PDF/Excel per employee
- Period and branch filters

### Database Collections

- `employees` - Employee master data with salary info
- `attendance` - Daily attendance records
- `transactions` - Sales transactions
- `branches` - Branch master data
- `jabatan` - Job positions
- `payroll_rules` - Salary rules per position
- `payroll_results` - Calculated payroll records
- `employee_performance` - Performance analysis history

### Technology Stack

- **Backend:** FastAPI, MongoDB (motor), Pydantic
- **Frontend:** React, TailwindCSS, Shadcn/UI, Axios
- **File Generation:** ReportLab (PDF), OpenPyXL (Excel)

### Testing Status

**Backend Tests:** 100% (27/27 passed)
- Seed data generation
- Payroll calculations
- AI performance analysis
- File generation

**Frontend Tests:** 95%
- AI Performance dashboard working
- Payroll Otomatis working
- Minor: dropdown loading fixed

### Known Issues
- None critical

### Future/Backlog
- AI Store Open/Close Prediction
- AI New Branch Location Prediction
- AI Cashier Fraud Detection Enhancement
- AI Missing Stock Detection
- WhatsApp Alert Integration (requires API key)
- Photo Enhancement (requires external API)

---
**Last Updated:** March 10, 2026
**Version:** 4.0.0
