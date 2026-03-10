# OCB TITAN AI - Global Retail Operating System
## Product Requirements Document

**Last Updated:** 2026-03-10
**Version:** 2.0

---

## Original Problem Statement
Build a comprehensive ERP system for OCB GROUP with:
- Multi-branch retail operations management
- HR & Payroll system with GPS-based attendance
- AI-powered sales and customer insights
- Real-time monitoring via War Room
- Integration with WhatsApp for alerts

---

## User Personas
1. **Owner/Director** - Full access to all modules, War Room, strategic insights
2. **Admin** - Manage master data, employees, transactions
3. **Supervisor (SPV)** - Branch oversight, team management, KPI tracking
4. **Cashier** - POS operations, sales transactions
5. **Warehouse (Gudang)** - Inventory management, stock transfers

---

## Core Requirements

### Phase 1: Base ERP (COMPLETED)
- [x] Authentication & authorization system
- [x] Dashboard with AI insights
- [x] Multi-branch management (40+ cabang)
- [x] Product/Item management
- [x] Customer management
- [x] Supplier management
- [x] POS/Kasir module
- [x] Inventory/stock management
- [x] Purchase orders
- [x] Sales transactions
- [x] Basic reporting

### Phase 2: HR & Payroll (COMPLETED)
- [x] Employee management with CRUD
- [x] Master Shift (shift kerja) - **SIMPAN WORKS**
- [x] Master Jabatan (posisi) - **SIMPAN WORKS**
- [x] Master Lokasi Absensi (GPS location) - **SIMPAN WORKS**
- [x] Master Payroll Rules (aturan gaji) - **SIMPAN WORKS**
- [x] Attendance with GPS verification
- [x] Attendance with photo proof
- [x] Payroll period management
- [x] Payroll slip generation
- [x] HR Department management
- [x] HR Training management
- [x] HR Organization structure
- [x] HR Document generator (SK, SP, Referensi)

### Phase 3: OCB TITAN AI Features (COMPLETED)
- [x] Global Map visualization
- [x] AI Command Center
- [x] KPI & Performance ranking
- [x] CRM AI System
  - [x] Customer data management - **SIMPAN WORKS**
  - [x] Character analysis AI
  - [x] Auto response generator
  - [x] Complaint handler
  - [x] Product recommendations
  - [x] Marketing scripts
- [x] Advanced Export (Excel, PDF, CSV, JSON)
- [x] Import System with templates & validation
- [x] WhatsApp Alert System (9 trigger types)
- [x] War Room Alert Panel

---

## What's Been Implemented (as of 2026-03-10)

### Backend APIs (100% Tested - 69/69 tests passed)
| Module | Status | Notes |
|--------|--------|-------|
| Auth | PASS | Login, logout, session management |
| Master Shift CRUD | PASS | Create, read, update, soft-delete |
| Master Jabatan CRUD | PASS | Create, read, update, soft-delete |
| Master Lokasi Absensi CRUD | PASS | Create, read, update, delete |
| Master Payroll Rules | PASS | Upsert pattern for create/update |
| Employee CRUD | PASS | Full CRUD with search |
| CRM Customer CRUD | PASS | Create, read, update customers |
| CRM Character Analysis | PASS | AI-based buying pattern analysis |
| CRM Auto Response | PASS | Intent detection + smart replies |
| HR Training | PASS | Training CRUD |
| HR Departments | PASS | Department & org structure |
| Export System | PASS | XLSX, PDF, JSON, CSV |
| Import System | PASS | 8 templates with preview/validation |
| WhatsApp Alerts | PASS | 9 triggers, recipients, templates |
| War Room Alerts | PASS | Create, acknowledge, resolve alerts |

### Frontend Pages
- Dashboard
- Master ERP (Shift, Jabatan, Lokasi, Payroll Rules)
- Employee Management
- HR Management (Training, Structure, Documents)
- Attendance
- Payroll
- CRM AI (Customers, Character AI, Response Generator)
- KPI & Performance
- Export System
- Import System
- WhatsApp Alerts
- War Room Alert Panel
- Global Map
- AI Command Center

---

## Known Limitations / Mocked APIs
1. **WhatsApp Sending** - Queued but not sent (requires external API key)
2. **AI Image Enhancement** - Returns pending status (requires external AI API)

---

## Technology Stack
- **Backend:** Python FastAPI, MongoDB (motor async driver)
- **Frontend:** React 18, TailwindCSS, Shadcn/UI
- **File Generation:** openpyxl (Excel), reportlab/weasyprint (PDF)
- **Maps:** react-leaflet

---

## Test Coverage
- **Backend:** 100% (69/69 tests)
- **Frontend:** Visual testing completed
- **Test Reports:** 
  - /app/test_reports/iteration_10.json
  - /app/test_reports/iteration_11.json
  - /app/test_reports/iteration_12.json (latest)

---

## Prioritized Backlog

### P0 - Critical (Complete)
- [x] Fix HR & Payroll bugs
- [x] Master data save buttons
- [x] CRM customer save
- [x] Export/Import validation

### P1 - High Priority (For future)
- [ ] Real WhatsApp API integration (needs API key)
- [ ] AI Image Enhancement (needs AI API key)
- [ ] KPI evidence upload with GPS metadata

### P2 - Medium Priority
- [ ] Mass employee upload from Excel
- [ ] Attendance approval workflow UI
- [ ] Training certificate generation

### P3 - Low Priority / Enhancements
- [ ] Push notifications
- [ ] Mobile responsive improvements
- [ ] Dashboard customization

---

## API Documentation

### Key Endpoints
```
Auth:
POST /api/auth/login
POST /api/auth/logout

Master ERP:
GET/POST /api/erp/master/shifts
GET/POST /api/erp/master/jabatan
GET/POST /api/erp/master/lokasi-absensi
GET/POST /api/erp/master/payroll-rules

HR Advanced:
GET/POST /api/hr/trainings
GET/POST /api/hr/departments
GET /api/hr/organization/structure
GET /api/hr/documents/generate/{type}/{employee_id}

CRM AI:
GET/POST /api/crm-ai/customers
POST /api/crm-ai/customers/{id}/analyze
POST /api/crm-ai/generate-response

Export:
GET /api/export-v2/hr/employees?format=xlsx|pdf|json

Import:
GET /api/import/templates
GET /api/import/templates/{key}/download
POST /api/import/preview/{key}
POST /api/import/execute/{key}

WhatsApp Alerts:
GET /api/whatsapp-alerts/triggers
GET/POST /api/whatsapp-alerts/recipients
GET /api/whatsapp-alerts/templates

War Room:
GET /api/warroom-alerts/active
POST /api/warroom-alerts/create
POST /api/warroom-alerts/{id}/action
```

---

## Credentials
- **Email:** ocbgroupbjm@gmail.com
- **Password:** admin123

---

## Changelog
- **2026-03-10:** Phase 1-15 TITAN AI completed, all 69 tests pass
- **2026-03-09:** OCB TITAN AI Phase 2 scaffolding (Export, Import, Alerts)
- **2026-03-08:** OCB TITAN AI Phase 1 scaffolding (Map, KPI, CRM AI)
- **2026-03-07:** Base ERP completion, HR & Payroll system
