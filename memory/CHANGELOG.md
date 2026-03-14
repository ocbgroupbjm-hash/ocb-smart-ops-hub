# CHANGELOG - OCB TITAN ERP

## 2026-03-14 (Session 2)

### AP/AR Bug Fix - TASK 1-5
- **TASK 1:** Invoice delete flow fixed - status = VOID (bukan PAID)
- **TASK 2:** Invoice reversal for PAID invoices implemented
- **TASK 3:** Payment VOID with reversal journal
- **TASK 4:** Income Statement safeguard fix
- **TASK 5:** Accounting validation after fix - BALANCED

### HR Frontend UI - TASK 6
- `HREmployees.jsx` - Full CRUD employee management
- `HRAttendance.jsx` - Check-in/out dashboard
- `HRLeave.jsx` - Leave request & approval
- `HRPayroll.jsx` - Payroll processing UI

### Files Modified
- `/app/backend/routes/ap_system.py` - New endpoints: void, reversal, payment void
- `/app/frontend/src/pages/accounting/AccountsPayable.jsx` - New status support
- `/app/frontend/src/pages/accounting/IncomeStatement.jsx` - Safeguards added

### Files Created
- `/app/test_reports/task1_6_ap_ar_bugfix/` - 9 evidence files
- `/app/test_reports/task6_hr_frontend/` - 3 evidence files

---

## 2026-03-14 (Session 1)

### AP/AR Enterprise Architecture
- `payment_allocation_engine.py` - Multi-invoice payment support
- Collections: `ap_payment_allocations`, `ar_payment_allocations`

### HR Enterprise System Backend
- `hr_employees.py` - Employee master CRUD
- `hr_attendance.py` - Check-in/out logic
- `hr_leave.py` - Leave request workflow
- `hr_payroll.py` - Payroll with auto-journal
- `hr_kpi.py` - KPI engine

### UI Dark Theme Validation
- 84 violations fixed
- 0 violations remaining

---

## 2026-03-13

### Phase 4: Standard ERP Toolbar
- `ERPActionToolbar.jsx` - Reusable component
- `StockCardModal.jsx` - Stock card from SSOT
