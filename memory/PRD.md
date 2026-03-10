# OCB GROUP SUPER ERP + AI TITAN WAR ROOM OPERATING SYSTEM
## Product Requirements Document (PRD)

---

## 1. Overview

**System Name:** OCB TITAN AI - GLOBAL RETAIL OPERATING SYSTEM  
**Version:** 3.0  
**Last Updated:** March 10, 2026  

The OCB TITAN AI is a comprehensive, enterprise-grade system that serves as the central command center for OCB GROUP business operations. It integrates retail operations, finance, HR management, and advanced AI analytics into a single unified platform with support for 500+ branches.

---

## 2. Core Architecture

### Tech Stack
- **Backend:** FastAPI (Python 3.12+)
- **Frontend:** React 18 with TailwindCSS, React-Leaflet for maps
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
│   │   ├── global_map.py         # Global map monitoring
│   │   ├── data_export.py        # Basic data export
│   │   ├── kpi_performance.py    # KPI & AI ranking
│   │   ├── ai_command_center.py  # AI business analysis
│   │   ├── crm_ai.py             # CRM AI prompts
│   │   ├── attendance_advanced.py # Advanced attendance
│   │   ├── export_advanced.py    # Advanced Export (Excel/PDF)
│   │   ├── import_system.py      # Import System
│   │   ├── file_upload.py        # File Upload (KPI/Products)
│   │   ├── whatsapp_alerts.py    # WhatsApp Alerts
│   │   ├── warroom_alerts.py     # War Room Alert Panel
│   │   └── ... (other routes)
│   └── server.py
└── frontend/
    └── src/
        ├── pages/
        │   ├── GlobalMap.jsx         # Real-time branch map
        │   ├── AICommandCenter.jsx   # AI business analysis
        │   ├── KPIPerformance.jsx    # KPI & rankings
        │   ├── CRMAI.jsx             # CRM AI prompts
        │   ├── AdvancedExport.jsx    # Export Excel/PDF/CSV/JSON
        │   ├── ImportSystem.jsx      # Import Excel/CSV/JSON
        │   ├── WhatsAppAlerts.jsx    # WhatsApp configuration
        │   ├── WarRoomAlertPanel.jsx # Real-time alert panel
        │   ├── SetoranHarian.jsx     # Daily deposits
        │   ├── SelisihKas.jsx        # Cash variance
        │   ├── Employees.jsx         # Employee management
        │   ├── Absensi.jsx           # GPS attendance
        │   ├── Payroll.jsx           # Payroll management
        │   ├── WarRoomV2.jsx         # Owner dashboard
        │   ├── ERPDashboard.jsx      # ERP summary
        │   ├── MasterERP.jsx         # Master data management
        │   └── ERPReports.jsx        # Reports
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

## 4. OCB TITAN AI Modules (Phase 2) ✅

### 4.1 Global Map Monitoring System ✅
- Real-time map of Indonesia with all 41+ branches
- Branch status indicators (Normal/Green, Warning/Yellow, Problem/Red)
- Live GPS tracking for Sales & SPV personnel
- SPV movement alerts when leaving store
- Stock status map (Empty, Low, Normal)
- Stock alerts for out-of-stock items

### 4.2 Global Data Export System ✅
- Export to JSON and CSV formats
- Master Data exports (Products, Categories, Brands, Suppliers, Customers, Branches, Warehouses)
- Employee exports (All, Jabatan, Attendance, KPI)
- Sales exports (Transactions, Setoran, Selisih Kas)
- Inventory exports (Current Stock, Mutations)
- Accounting exports (Journals, Kas Masuk/Keluar)
- Payroll exports
- Audit exports (Kas, Stock)
- CRM exports (Customers, Complaints)
- Bulk export all data

### 4.3 KPI & AI Performance System ✅
- KPI Templates management (Sales, Attendance, Service, Operational)
- KPI Targets per employee
- KPI Submissions with evidence support
- AI-powered Employee Ranking with categories:
  - Elite Performer (≥120%)
  - Top Performer (≥100%)
  - Good Performer (≥80%)
  - Average Performer (≥60%)
  - Under Performance (≥40%)
  - Needs Improvement (<40%)
- AI-powered Branch Ranking
- Monthly performance reports

### 4.4 AI Command Center ✅
- Real-time business dashboard with AI insights
- Financial summary (Sales today/month, Minus kas)
- Attendance metrics (Rate, Late rate)
- Inventory alerts (Low stock count)
- AI-generated Insights with severity (Critical, Warning, Info)
- AI Recommendations with priority (High, Medium, Low)
- 30-day Trend Analysis with direction
- Anomaly Detection (Repeated minus, Sales anomalies)

### 4.5 CRM AI Prompt Builder ✅
- Customizable AI prompt templates
- Categories: Customer Reply, Marketing Script, Complaint Handling, Product Recommendation
- Reply Generator with variables
- Complaint Analyzer with category detection and suggested responses
- Product Recommendation engine
- Marketing Script generator

### 4.6 Advanced Attendance System ✅
- Role-based permissions (Employee, SPV, Manager, HRD, Owner)
- Leave Request management with approval workflow
- Overtime Request management
- Employee attendance summary
- Branch attendance summary
- Monthly attendance reports

---

## 4.7 Advanced Export System (Phase 2) ✅
- Export ke Excel (.xlsx), PDF, CSV, JSON
- Semua modul: Master Data, HR, KPI, Sales, Inventory, Accounting, Audit, CRM
- Special exports: Employee Ranking, Branch Ranking, Dashboard Summary
- Period selection dan date range filter

## 4.8 Import System (Phase 2) ✅
- Import dari Excel, CSV, JSON
- Templates untuk: Products, Suppliers, Customers, Branches, Employees, Stock Awal, Saldo Awal, KPI
- Preview data sebelum import
- Validasi kolom wajib dan duplicate checking
- Error report per baris
- Rollback support untuk undo import
- Import history tracking

## 4.9 File Upload System (Phase 2) ✅
- KPI Evidence upload (foto/video)
  - Timestamp otomatis
  - Lokasi GPS
  - Status tracking
- Product Photo upload
  - Multiple photos per product
  - Primary photo selection
  - AI Enhancement placeholder (butuh API key)

## 4.10 WhatsApp Alert System (Phase 2) ✅
- Alert triggers: Minus Kas, Stok Kosong, Stok Minimum, Cabang Belum Setor, SPV Leave Store, KPI Terlambat, Performance Rendah, Audit Minus, Cabang Bermasalah
- Recipient management by role (Owner, HRD, SPV, Gudang, Admin)
- Message templates with variables
- API configuration panel
- Alert logs and test functionality
- Ready for WhatsApp API integration

## 4.11 War Room Alert Panel (Phase 2) ✅
- Real-time active alerts dashboard
- Priority summary (Critical, High, Medium, Low)
- Alert actions: Acknowledge, In Progress, Escalate, Resolve
- Auto-check for minus kas, stock, unreported branches
- Top affected branches display
- Notification tracking per recipient role

---

## 5. API Endpoints

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

## 6. New API Endpoints (OCB TITAN AI)

### Global Map
- `GET /api/global-map/branches` - All branches with coordinates & status
- `GET /api/global-map/branches/{id}` - Branch detail
- `POST /api/global-map/gps/update` - Update GPS location
- `GET /api/global-map/gps/realtime` - Real-time GPS locations
- `GET /api/global-map/gps/history/{employee_id}` - GPS history
- `GET /api/global-map/stock/map` - Stock status map
- `POST /api/global-map/stock/alert` - Create stock alert
- `GET /api/global-map/stock/alerts` - Stock alerts
- `PUT /api/global-map/stock/alerts/{id}/resolve` - Resolve alert
- `GET /api/global-map/spv/alerts` - SPV movement alerts

### Data Export
- `GET /api/export/master/*` - Master data exports
- `GET /api/export/employees/*` - Employee exports
- `GET /api/export/sales/*` - Sales exports
- `GET /api/export/inventory/*` - Inventory exports
- `GET /api/export/accounting/*` - Accounting exports
- `GET /api/export/payroll/details` - Payroll exports
- `GET /api/export/audit/*` - Audit exports
- `GET /api/export/crm/*` - CRM exports
- `GET /api/export/bulk/all` - Full data export

### KPI & Performance
- `GET/POST /api/kpi/templates` - KPI templates
- `PUT/DELETE /api/kpi/templates/{id}` - Manage templates
- `GET/POST /api/kpi/targets` - KPI targets
- `POST /api/kpi/targets/bulk` - Bulk target creation
- `POST /api/kpi/submit` - Submit KPI achievement
- `GET /api/kpi/submissions` - KPI submissions
- `PUT /api/kpi/submissions/{id}/review` - Review submission
- `GET /api/kpi/ai-ranking/employees` - Employee ranking
- `GET /api/kpi/ai-ranking/branches` - Branch ranking
- `POST /api/kpi/seed-templates` - Create default templates

### AI Command Center
- `GET /api/ai-command/dashboard` - Main AI dashboard
- `GET /api/ai-command/recommendations` - AI recommendations
- `GET /api/ai-command/trends` - Trend analysis
- `GET /api/ai-command/anomalies` - Anomaly detection

### CRM AI
- `GET/POST /api/crm-ai/prompts` - Prompt templates
- `PUT/DELETE /api/crm-ai/prompts/{id}` - Manage prompts
- `POST /api/crm-ai/chat/message` - Save chat message
- `GET /api/crm-ai/chat/history/{customer_id}` - Chat history
- `POST /api/crm-ai/chat/generate-reply` - Generate AI reply
- `GET /api/crm-ai/recommend-products/{customer_id}` - Product recommendations
- `GET /api/crm-ai/marketing-scripts` - Marketing scripts
- `POST /api/crm-ai/marketing-scripts/generate` - Generate script
- `POST /api/crm-ai/complaint/analyze` - Analyze complaint
- `POST /api/crm-ai/seed-prompts` - Create default prompts

### Advanced Attendance
- `GET /api/attendance-v2/permissions/{role}` - Role permissions
- `POST /api/attendance-v2/leave/request` - Create leave request
- `GET /api/attendance-v2/leave/requests` - Leave requests
- `PUT /api/attendance-v2/leave/approve/{id}` - Approve/reject leave
- `POST /api/attendance-v2/overtime/request` - Create overtime request
- `GET /api/attendance-v2/overtime/requests` - Overtime requests
- `PUT /api/attendance-v2/overtime/approve/{id}` - Approve/reject overtime
- `GET /api/attendance-v2/summary/employee/{id}` - Employee summary
- `GET /api/attendance-v2/summary/branch/{id}` - Branch summary
- `GET /api/attendance-v2/reports/monthly` - Monthly report

---

## 7. Testing Credentials

- **Email:** ocbgroupbjm@gmail.com
- **Password:** admin123
- **Login Flow:** Select Business (OCB GROUP) → Enter Credentials

---

## 8. Future Roadmap (P1-P2)

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

## 9. Change Log

### March 10, 2026 (Phase 2 - OCB TITAN AI Continued)
- ✅ Implemented Advanced Export System (Excel, PDF, CSV, JSON)
- ✅ Built Import System with validation, preview, and rollback
- ✅ Created File Upload System for KPI evidence and product photos
- ✅ Developed WhatsApp Alert System with 9 trigger types
- ✅ Built War Room Alert Panel with real-time monitoring
- ✅ All new frontend pages with professional UI
- ✅ Testing passed 100% (iteration_11.json)

### March 10, 2026 (Phase 2 - OCB TITAN AI)
- ✅ Implemented Global Map Monitoring System with Leaflet
- ✅ Created Global Data Export System (JSON/CSV)
- ✅ Built KPI & AI Performance System with ranking
- ✅ Developed AI Command Center with insights & recommendations
- ✅ Created CRM AI Prompt Builder
- ✅ Added Advanced Attendance with role-based permissions
- ✅ All new frontend pages with professional UI
- ✅ Testing passed 100% (25/25 backend, 5/5 frontend)

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

## 10. Known Issues & Notes

- QRIS payment integration is **MOCKED**
- Branch data is seeded/dummy for testing
- Photo upload in attendance stores filename only (no actual file storage)
- All existing POS, inventory, accounting features preserved
