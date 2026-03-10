# OCB TITAN AI - GLOBAL RETAIL OPERATING SYSTEM
## Product Requirements Document (PRD)

### Overview
Enterprise AI-powered retail operating system for OCB GROUP managing multi-branch retail operations with comprehensive HR, Payroll, Sales, Inventory, and AI analytics capabilities.

---

## AUDIT STATUS: COMPLETE ✅
**Last Audit Date:** March 10, 2026
**Audit Result:** 
- Backend: 100% (40/40 tests passed)
- Frontend: 100% (19/19 menus functional)
- Data Flow: 100% (3/3 flows verified)

---

## Core Modules Implemented

### 1. AI CFO & War Room
- **CFO Dashboard**: Revenue, Net Profit, Payroll Ratio, Profit-Loss, Cash Flow
- **AI Super War Room**: Real-time branch monitoring, Sales predictions, Branch analysis
- **Global Map**: 46 branches on interactive map with status indicators

### 2. OCB TITAN AI Modules
- **AI Command Center**: AI Insights, Recommendations, Anomaly Detection
- **KPI Performance**: Employee/Branch ranking, KPI templates
- **CRM AI**: Customer management, Character AI, Reply Generator, Marketing
- **Advanced Export**: XLSX, PDF, CSV, JSON export for all modules
- **Import Data**: Excel/CSV import with templates and validation
- **WhatsApp Alerts**: Configuration placeholder (requires API key)

### 3. Operasional
- **Setoran Harian**: Daily deposit tracking per branch
- **Selisih Kas**: Cash discrepancy monitoring
- **Dashboard ERP**: Overview of ERP operations
- **Laporan ERP**: ERP reports

### 4. Kasir (POS)
- Point of Sale system with transaction processing

### 5. Master Data
- **Daftar Item**: 24+ products with categories, brands, units
- **Kategori Item**: 6 categories
- **Satuan**: 6 units
- **Merk**: 6 brands
- **Dept/Gudang**: 4 warehouses
- **Supplier**: 6 suppliers
- **Pelanggan**: 20 customers
- **Sales**: 6 sales persons
- **Grup Pelanggan**: 4 groups
- **Banks**: 5 banks

### 6. Pembelian (Purchase)
- Purchase Orders
- Purchase List
- Goods Receipt
- Purchase Payments
- Purchase Returns

### 7. Penjualan (Sales)
- Sales Orders
- Sales List (1949+ transactions)
- Cashier Sales
- Price History
- Trade-in
- Payments
- Returns
- Delivery

### 8. Persediaan (Inventory)
- Stock List
- Stock Card
- Stock In/Out
- Stock Transfer
- Stock Mutation
- Stock Opname
- Serial Numbers
- Product Assembly

### 9. Akuntansi (Accounting)
- Chart of Accounts (12 accounts)
- Cash In/Out
- Cash Transfer
- Customer/Supplier Deposits
- Journals
- General Ledger
- Opening Balance
- Year Close

### 10. HR & Payroll
- **Data Karyawan**: 37 employees
- **HR Management**: Training, Organization Structure
- **Absensi**: GPS Check-in/out (288+ records)
- **Payroll**: Period-based payroll
- **AI Performance**: Employee ranking with categories (ELITE, SANGAT_BAIK, etc)
- **Payroll Otomatis**: Auto-calculate from attendance
- **Master Shift**: 10+ shifts
- **Master Jabatan**: 8 positions
- **Aturan Payroll**: 8 payroll rules

---

## Technology Stack
- **Backend**: FastAPI, MongoDB (motor), Pydantic
- **Frontend**: React, TailwindCSS, Shadcn/UI, Axios
- **File Generation**: ReportLab (PDF), OpenPyXL (Excel)
- **Maps**: react-leaflet
- **Authentication**: JWT

---

## Database Collections
- employees, attendance, transactions, branches, jabatan
- payroll_rules, payroll_results, employee_performance
- products, categories, units, brands, warehouses
- suppliers, customers, sales_persons, customer_groups
- purchases, inventory_movements, cash_transactions
- setoran_harian, selisih_kas, chart_of_accounts
- crm_customers, kpi_targets, system_alerts

---

## API Endpoints (Key)

### Seed & Audit Data
- POST `/api/seed/all` - Seed HR data
- POST `/api/audit-data/all` - Seed comprehensive audit data
- GET `/api/audit-data/check` - Check data counts

### HR & Payroll
- GET `/api/erp/employees` - List employees
- GET `/api/attendance-advanced` - Attendance records
- GET `/api/payroll-auto/calculate/{id}` - Calculate payroll
- GET `/api/payroll-auto/calculate-all` - Bulk calculate
- GET `/api/ai-employee/analyze/{id}` - AI performance analysis
- GET `/api/ai-employee/ranking` - Employee ranking

### Export
- GET `/api/export-v2/{module}/{type}` - Export data

### AI Modules
- GET `/api/ai-command/dashboard` - AI Command Center
- GET `/api/ai-cfo/dashboard` - CFO Dashboard
- GET `/api/ai-warroom/dashboard` - War Room

---

## Test Reports
- `/app/test_reports/iteration_17.json` - HR/Payroll tests
- `/app/test_reports/iteration_18.json` - Comprehensive audit
- `/app/test_reports/iteration_19.json` - Data flow tests

---

## Known Issues
- Session timeout needs extending
- Dashboard employee count filter may need verification

---

## Future/Backlog
- AI Store Open/Close Prediction
- AI New Branch Location Prediction
- AI Cashier Fraud Detection Enhancement
- AI Missing Stock Detection
- WhatsApp Alert Integration (requires API key)
- Photo Enhancement (requires external API)

---

**Version:** 4.1.0
**Last Updated:** March 10, 2026
