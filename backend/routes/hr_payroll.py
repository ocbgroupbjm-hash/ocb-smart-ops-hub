# OCB TITAN ERP - HR PAYROLL ENGINE ENTERPRISE
# Kalkulasi gaji dengan auto-journal ke Accounting
# BLUEPRINT v2.4.8 - AUDIT READY + TENANT SAFE + ACCOUNTING CONSISTENT
# MULTI-TENANT FIX: All collection access via dynamic getters

from fastapi import APIRouter, HTTPException, Depends, Request, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from database import get_db
from utils.auth import get_current_user
from routes.rbac_system import log_activity
import uuid

router = APIRouter(prefix="/api/hr/payroll", tags=["HR Payroll Engine"])

# ============ DYNAMIC COLLECTION ACCESS (Multi-Tenant) ============
# All collection access MUST use these getters to ensure tenant isolation

def _get_payroll_coll():
    return get_db()["payroll"]

def _get_payroll_items_coll():
    return get_db()["payroll_items"]

def _get_employees_coll():
    return get_db()["employees"]

def _get_attendance_logs_coll():
    return get_db()["attendance_logs"]

def _get_leave_requests_coll():
    return get_db()["leave_requests"]

def _get_journal_entries_coll():
    return get_db()["journal_entries"]

def _get_audit_logs_coll():
    return get_db()["audit_logs"]

def _get_payroll_components_coll():
    return get_db()["payroll_components"]

def _get_kpi_results_coll():
    return get_db()["kpi_results"]

def _get_contracts_coll():
    return get_db()["employee_contracts"]

# ============ PAYROLL STATUS ============
class PayrollStatus:
    DRAFT = "draft"
    CALCULATED = "calculated"
    POSTED = "posted"
    PAID = "paid"
    REVERSED = "reversed"

# ============ RBAC ROLES FOR PAYROLL ============
HR_ADMIN_ROLES = ["owner", "admin", "hr_admin", "super_admin"]
PAYROLL_VIEW_ROLES = ["owner", "admin", "hr_admin", "super_admin", "hr_staff", "supervisor"]

# ==================== PYDANTIC MODELS ====================

class PayrollItemCreate(BaseModel):
    """Komponen gaji (tunjangan/potongan)"""
    code: str
    name: str
    type: str  # allowance, deduction, tax
    calculation_type: str = "fixed"  # fixed, percentage, formula
    amount: float = 0
    percentage: float = 0  # Untuk persentase
    base_field: Optional[str] = None  # Field untuk perhitungan persentase
    is_taxable: bool = True
    is_active: bool = True
    description: Optional[str] = None

class PayrollRunRequest(BaseModel):
    """Request untuk menjalankan payroll"""
    period_month: int  # 1-12
    period_year: int
    branch_id: Optional[str] = None
    department_id: Optional[str] = None
    employee_ids: Optional[List[str]] = None  # Specific employees, null = all

class PayrollAdjustment(BaseModel):
    """Penyesuaian manual"""
    employee_id: str
    payroll_id: str
    item_code: str
    item_name: str
    type: str  # allowance, deduction
    amount: float
    notes: Optional[str] = None


# ==================== PAYROLL COMPONENTS ====================

@router.post("/components")
async def create_payroll_component(
    data: PayrollItemCreate,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """Create payroll component (tunjangan/potongan)"""
    user_id = user.get("user_id", user.get("id", ""))
    
    payroll_components = _get_payroll_components_coll()
    
    existing = await payroll_components.find_one({"code": data.code.upper()})
    if existing:
        raise HTTPException(status_code=400, detail=f"Kode komponen {data.code} sudah ada")
    
    component = {
        "id": str(uuid.uuid4()),
        "code": data.code.upper(),
        "name": data.name,
        "type": data.type,
        "calculation_type": data.calculation_type,
        "amount": data.amount,
        "percentage": data.percentage,
        "base_field": data.base_field,
        "is_taxable": data.is_taxable,
        "is_active": data.is_active,
        "description": data.description,
        "created_by": user_id,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await payroll_components.insert_one(component)
    
    return {"status": "success", "component_id": component["id"]}

@router.get("/components")
async def get_payroll_components(
    type: Optional[str] = None,  # allowance, deduction, tax
    user: dict = Depends(get_current_user)
):
    """Get all payroll components"""
    payroll_components = _get_payroll_components_coll()
    
    query = {"is_active": True}
    if type:
        query["type"] = type
    
    components = await payroll_components.find(query, {"_id": 0}).to_list(50)
    return {"components": components}


# ==================== PAYROLL RUN ====================

# ============================================================
# PHASE 3: ATTENDANCE PERIOD LOCK CHECK
# ============================================================
def _get_attendance_periods_coll():
    return get_db()["attendance_periods"]


async def check_attendance_period_locked(month: int, year: int) -> Dict:
    """
    Check if attendance period is locked
    
    Returns:
        {
            "is_locked": bool,
            "is_immutable": bool (True if payroll already posted),
            "locked_at": datetime or None,
            "locked_by": str or None,
            "message": str
        }
    """
    attendance_periods = _get_attendance_periods_coll()
    payroll_coll = _get_payroll_coll()
    
    period_key = f"{year}-{month:02d}"
    
    period_record = await attendance_periods.find_one(
        {"period": period_key},
        {"_id": 0}
    )
    
    # Check if payroll already posted for this period (makes lock IMMUTABLE)
    posted_payroll = await payroll_coll.find_one({
        "period": period_key,
        "status": "posted"
    })
    
    is_immutable = posted_payroll is not None
    
    if not period_record:
        return {
            "is_locked": False,
            "is_immutable": is_immutable,
            "locked_at": None,
            "locked_by": None,
            "message": f"Periode {period_key} belum ada di sistem. Silakan lock terlebih dahulu."
        }
    
    is_locked = period_record.get("is_locked", False)
    
    return {
        "is_locked": is_locked,
        "is_immutable": is_immutable,
        "locked_at": period_record.get("locked_at"),
        "locked_by": period_record.get("locked_by"),
        "locked_by_name": period_record.get("locked_by_name"),
        "message": f"Periode {period_key} {'sudah' if is_locked else 'belum'} dikunci" + 
                   (" (IMMUTABLE - payroll sudah diposting)" if is_immutable else "")
    }


# ============================================================
# PHASE 3.1: VALIDATE EMPLOYEE FOR PAYROLL
# - Must be ACTIVE status
# - Must have valid contract for the period
# ============================================================
async def validate_employee_for_payroll(employee_id: str, period_month: int, period_year: int) -> Dict:
    """
    Validate if employee can be included in payroll
    
    Rules:
    1. Employee status must be ACTIVE
    2. Employee must have valid contract covering the payroll period
    
    Returns:
        {
            "is_valid": bool,
            "reason": str or None,
            "employee": dict or None
        }
    """
    employees_coll = _get_employees_coll()
    contracts_coll = _get_contracts_coll()
    
    # Get employee
    employee = await employees_coll.find_one({"id": employee_id}, {"_id": 0})
    
    if not employee:
        return {
            "is_valid": False,
            "reason": "Karyawan tidak ditemukan",
            "employee": None
        }
    
    # Check status
    emp_status = employee.get("status", "").lower()
    if emp_status != "active":
        return {
            "is_valid": False,
            "reason": f"Karyawan tidak aktif (status: {emp_status})",
            "employee": employee
        }
    
    # Check contract validity
    period_date = f"{period_year}-{period_month:02d}-01"
    
    valid_contract = await contracts_coll.find_one({
        "employee_id": employee_id,
        "status": "active",
        "$or": [
            {"valid_until": {"$gte": period_date}},
            {"valid_until": None},
            {"valid_until": ""}
        ]
    })
    
    # If no contracts collection or no contract, assume valid (for backward compatibility)
    # But log a warning
    if not valid_contract:
        # Try to check if contracts collection exists
        contract_count = await contracts_coll.count_documents({})
        if contract_count > 0:
            # Contracts exist but none valid for this employee
            return {
                "is_valid": False,
                "reason": f"Tidak ada kontrak aktif yang valid untuk periode {period_month}/{period_year}",
                "employee": employee
            }
        # No contracts in system - allow (backward compatibility)
    
    return {
        "is_valid": True,
        "reason": None,
        "employee": employee
    }


# ============================================================
# PHASE 3.2: CHECK DUPLICATE PAYROLL
# ============================================================
async def check_payroll_duplicate(employee_id: str, period_month: int, period_year: int) -> Dict:
    """
    Check if payroll already exists for this employee and period
    
    Returns:
        {
            "has_duplicate": bool,
            "existing_status": str or None,
            "existing_batch_no": str or None
        }
    """
    payroll_coll = _get_payroll_coll()
    
    period_key = f"{period_year}-{period_month:02d}"
    
    existing = await payroll_coll.find_one({
        "employee_id": employee_id,
        "period": period_key,
        "status": {"$ne": "reversed"}  # Reversed payroll doesn't count
    }, {"_id": 0, "status": 1, "batch_no": 1})
    
    if existing:
        return {
            "has_duplicate": True,
            "existing_status": existing.get("status"),
            "existing_batch_no": existing.get("batch_no")
        }
    
    return {
        "has_duplicate": False,
        "existing_status": None,
        "existing_batch_no": None
    }


# ============================================================
# PHASE 3: KPI INTEGRATION FOR BONUS CALCULATION
# SOURCE OF TRUTH: kpi_results collection ONLY
# ============================================================
async def calculate_kpi_bonus(employee_id: str, month: int, year: int, base_salary: float = 0) -> Dict:
    """
    Calculate KPI-based bonus for employee
    
    SOURCE OF TRUTH: kpi_results collection
    - Only approved KPI results are considered
    - Bonus calculated based on final_score
    
    KPI Score Ranges (Blueprint HR v2.4.8):
    - 90-100: 20% of base salary as bonus (Excellent)
    - 80-89: 15% of base salary as bonus (Very Good)
    - 70-79: 10% of base salary as bonus (Good)
    - 60-69: 5% of base salary as bonus (Satisfactory)
    - Below 60: No bonus (Needs Improvement)
    
    Returns:
        {
            "has_kpi": bool,
            "kpi_id": str or None,
            "kpi_score": float,
            "kpi_rating": str,
            "bonus_percentage": float,
            "bonus_amount": float,
            "source": "kpi_results"
        }
    """
    kpi_results = _get_kpi_results_coll()
    employees_coll = _get_employees_coll()
    
    # Get KPI result for this employee and period - SOURCE OF TRUTH
    period_key = f"{year}-{month:02d}"
    
    kpi_record = await kpi_results.find_one({
        "employee_id": employee_id,
        "period": period_key,
        "status": "approved"  # Only approved KPI
    }, {"_id": 0})
    
    if not kpi_record:
        return {
            "has_kpi": False,
            "kpi_id": None,
            "kpi_score": 0,
            "kpi_rating": "N/A",
            "bonus_percentage": 0,
            "bonus_amount": 0,
            "source": "kpi_results"
        }
    
    # Get employee base salary if not provided
    if base_salary == 0:
        employee = await employees_coll.find_one({"id": employee_id}, {"_id": 0, "salary_base": 1})
        base_salary = employee.get("salary_base", 0) if employee else 0
    
    kpi_score = kpi_record.get("final_score", kpi_record.get("score", 0))
    kpi_id = kpi_record.get("id", kpi_record.get("kpi_id"))
    
    # Calculate bonus based on KPI score - FIXED TIERS
    if kpi_score >= 90:
        bonus_pct = 20
        rating = "Excellent"
    elif kpi_score >= 80:
        bonus_pct = 15
        rating = "Very Good"
    elif kpi_score >= 70:
        bonus_pct = 10
        rating = "Good"
    elif kpi_score >= 60:
        bonus_pct = 5
        rating = "Satisfactory"
    else:
        bonus_pct = 0
        rating = "Needs Improvement"
    
    bonus_amount = base_salary * (bonus_pct / 100)
    
    return {
        "has_kpi": True,
        "kpi_id": kpi_id,
        "kpi_score": kpi_score,
        "kpi_rating": rating,
        "bonus_percentage": bonus_pct,
        "bonus_amount": bonus_amount,
        "source": "kpi_results"
    }


async def calculate_attendance_data(employee_id: str, month: int, year: int) -> Dict:
    """Calculate attendance metrics for payroll"""
    attendance_logs = _get_attendance_logs_coll()
    
    period_start = f"{year}-{month:02d}-01"
    if month == 12:
        period_end = f"{year + 1}-01-01"
    else:
        period_end = f"{year}-{month + 1:02d}-01"
    
    records = await attendance_logs.find({
        "employee_id": employee_id,
        "date": {"$gte": period_start, "$lt": period_end}
    }, {"_id": 0}).to_list(31)
    
    present_days = len([r for r in records if r.get("check_in")])
    late_days = len([r for r in records if r.get("is_late")])
    total_work_hours = sum(r.get("work_hours", 0) for r in records)
    total_overtime = sum(r.get("overtime_hours", 0) for r in records)
    
    return {
        "present_days": present_days,
        "late_days": late_days,
        "total_work_hours": total_work_hours,
        "total_overtime": total_overtime
    }


async def calculate_leave_data(employee_id: str, month: int, year: int) -> Dict:
    """Calculate approved leave days for the period"""
    leave_requests = _get_leave_requests_coll()
    
    period_start = f"{year}-{month:02d}-01"
    if month == 12:
        period_end = f"{year + 1}-01-01"
    else:
        period_end = f"{year}-{month + 1:02d}-01"
    
    leaves = await leave_requests.find({
        "employee_id": employee_id,
        "status": "approved",
        "$or": [
            {"start_date": {"$gte": period_start, "$lt": period_end}},
            {"end_date": {"$gte": period_start, "$lt": period_end}}
        ]
    }, {"_id": 0}).to_list(10)
    
    paid_leave_days = sum(leave.get("total_days", 0) for leave in leaves if leave.get("leave_type_code") != "UNPAID")
    unpaid_leave_days = sum(leave.get("total_days", 0) for leave in leaves if leave.get("leave_type_code") == "UNPAID")
    
    return {
        "paid_leave_days": paid_leave_days,
        "unpaid_leave_days": unpaid_leave_days
    }


async def create_payroll_journal(
    payroll_data: Dict,
    user_id: str,
    user_name: str,
    branch_id: str
) -> str:
    """Create journal entry for payroll"""
    from utils.number_generator import generate_transaction_number
    
    db = get_db()
    journal_entries = _get_journal_entries_coll()
    
    journal_number = await generate_transaction_number(db, "JV")
    
    # Get account codes
    salary_expense = "6-1100"  # Beban Gaji
    cash_account = "1-1100"   # Kas
    tax_payable = "2-1500"    # Hutang Pajak
    
    total_gross = payroll_data.get("total_gross", 0)
    # Note: total_deductions and net_salary are available in payroll_data but journal uses total_gross and tax for entries
    tax_amount = payroll_data.get("tax_amount", 0)
    
    entries = [
        {
            "account_code": salary_expense,
            "account_name": "Beban Gaji",
            "debit": total_gross,
            "credit": 0,
            "description": f"Gaji {payroll_data.get('period_display')} - {payroll_data.get('employee_count', 0)} karyawan"
        }
    ]
    
    if tax_amount > 0:
        entries.append({
            "account_code": tax_payable,
            "account_name": "Hutang PPh 21",
            "debit": 0,
            "credit": tax_amount,
            "description": f"PPh 21 {payroll_data.get('period_display')}"
        })
    
    entries.append({
        "account_code": cash_account,
        "account_name": "Kas/Bank",
        "debit": 0,
        "credit": total_gross - tax_amount,  # Net payout
        "description": f"Pembayaran Gaji {payroll_data.get('period_display')}"
    })
    
    total_debit = sum(e.get("debit", 0) for e in entries)
    total_credit = sum(e.get("credit", 0) for e in entries)
    
    journal = {
        "id": str(uuid.uuid4()),
        "journal_number": journal_number,
        "journal_no": journal_number,
        "journal_date": datetime.now(timezone.utc).isoformat(),
        "posted_at": datetime.now(timezone.utc).isoformat(),
        "reference_type": "payroll",
        "reference_id": payroll_data.get("batch_id"),
        "reference_no": payroll_data.get("batch_no"),
        "memo": f"Pembayaran Gaji {payroll_data.get('period_display')}",
        "description": f"Pembayaran Gaji {payroll_data.get('period_display')}",
        "branch_id": branch_id,
        "entries": entries,
        "lines": entries,
        "total_debit": total_debit,
        "total_credit": total_credit,
        "is_balanced": abs(total_debit - total_credit) < 0.01,
        "status": "posted",
        "created_by": user_id,
        "created_by_name": user_name,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await journal_entries.insert_one(journal)
    
    return journal_number


@router.post("/run")
async def run_payroll(
    data: PayrollRunRequest,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """
    Run payroll calculation for a period
    
    Business Rules (Blueprint v2.4.8 AUDIT READY):
    - Validate employee status = ACTIVE
    - Validate contract validity
    - Check duplicate payroll
    - Calculate basic salary
    - Add allowances (including KPI bonus from kpi_results)
    - Deduct absences (unpaid leave)
    - Calculate tax (PPh 21)
    - Generate journal entries
    - SSOT: salary_base from Employee Master
    - KPI bonus: kpi_results collection ONLY
    """
    user_id = user.get("user_id", user.get("id", ""))
    user_name = user.get("name", "")
    branch_id = data.branch_id or user.get("branch_id", "")
    
    # Get dynamic collections
    payroll_coll = _get_payroll_coll()
    payroll_items_coll = _get_payroll_items_coll()
    employees_coll = _get_employees_coll()
    payroll_components = _get_payroll_components_coll()
    db = get_db()
    
    period = f"{data.period_year}-{data.period_month:02d}"
    period_display = f"{datetime(data.period_year, data.period_month, 1).strftime('%B %Y')}"
    
    # ============================================================
    # VALIDATION 1: Check if payroll already exists (POSTED)
    # ============================================================
    existing_posted = await payroll_coll.find_one({
        "period": period,
        "status": "posted"
    })
    
    if existing_posted:
        raise HTTPException(
            status_code=400, 
            detail=f"Payroll periode {period_display} sudah diposting. Tidak bisa run ulang."
        )
    
    # Delete existing draft if any (allow re-run for draft)
    await payroll_coll.delete_many({"period": period, "status": "draft"})
    await payroll_items_coll.delete_many({"period": period})
    
    # Get employees to process
    emp_query = {"status": "active"}
    if data.branch_id:
        emp_query["branch_id"] = data.branch_id
    if data.department_id:
        emp_query["department_id"] = data.department_id
    if data.employee_ids:
        emp_query["id"] = {"$in": data.employee_ids}
    
    employee_list = await employees_coll.find(emp_query, {"_id": 0}).to_list(1000)
    
    if not employee_list:
        raise HTTPException(status_code=400, detail="Tidak ada karyawan yang diproses")
    
    # Get standard components
    components = await payroll_components.find(
        {"is_active": True}, {"_id": 0}
    ).to_list(50)
    
    allowance_components = [c for c in components if c.get("type") == "allowance"]
    deduction_components = [c for c in components if c.get("type") == "deduction"]
    
    # Generate batch ID
    from utils.number_generator import generate_transaction_number
    batch_no = await generate_transaction_number(db, "PAY")
    batch_id = str(uuid.uuid4())
    
    # Process each employee
    payroll_records = []
    item_records = []
    total_gross_all = 0
    total_deductions_all = 0
    total_tax_all = 0
    total_net_all = 0
    skipped_employees = []
    
    for emp in employee_list:
        # ============================================================
        # VALIDATION 2: Validate employee for payroll
        # ============================================================
        emp_validation = await validate_employee_for_payroll(emp["id"], data.period_month, data.period_year)
        
        if not emp_validation.get("is_valid"):
            skipped_employees.append({
                "employee_id": emp["id"],
                "employee_name": emp.get("full_name", emp.get("name", "")),
                "reason": emp_validation.get("reason")
            })
            continue  # Skip this employee
        
        # ============================================================
        # VALIDATION 3: Check duplicate payroll (extra safety)
        # ============================================================
        dup_check = await check_payroll_duplicate(emp["id"], data.period_month, data.period_year)
        if dup_check.get("has_duplicate"):
            skipped_employees.append({
                "employee_id": emp["id"],
                "employee_name": emp.get("full_name", emp.get("name", "")),
                "reason": f"Payroll sudah ada (status: {dup_check.get('existing_status')})"
            })
            continue  # Skip this employee
        
        # Get attendance and leave data
        attendance_data = await calculate_attendance_data(emp["id"], data.period_month, data.period_year)
        leave_data = await calculate_leave_data(emp["id"], data.period_month, data.period_year)
        
        # Calculate components
        salary_base = emp.get("salary_base", 0)
        
        # Calculate working days (assume 22 days standard)
        standard_work_days = 22
        absent_days = leave_data.get("unpaid_leave_days", 0)
        actual_work_days = min(attendance_data.get("present_days", standard_work_days), standard_work_days)
        
        # Calculate prorated salary if needed
        if absent_days > 0:
            daily_rate = salary_base / standard_work_days
            proration_deduction = daily_rate * absent_days
        else:
            proration_deduction = 0
        
        # Calculate allowances
        total_allowances = 0
        emp_items = []
        
        for comp in allowance_components:
            if comp.get("calculation_type") == "fixed":
                amount = comp.get("amount", 0)
            elif comp.get("calculation_type") == "percentage":
                base_value = salary_base  # Or other base
                amount = base_value * (comp.get("percentage", 0) / 100)
            else:
                amount = 0
            
            if amount > 0:
                emp_items.append({
                    "id": str(uuid.uuid4()),
                    "payroll_id": None,  # Will be set later
                    "employee_id": emp["id"],
                    "item_code": comp.get("code"),
                    "item_name": comp.get("name"),
                    "type": "allowance",
                    "amount": amount,
                    "is_taxable": comp.get("is_taxable", True)
                })
                total_allowances += amount
        
        # Calculate deductions
        total_deductions = 0
        
        for comp in deduction_components:
            if comp.get("calculation_type") == "fixed":
                amount = comp.get("amount", 0)
            elif comp.get("calculation_type") == "percentage":
                base_value = salary_base + total_allowances
                amount = base_value * (comp.get("percentage", 0) / 100)
            else:
                amount = 0
            
            if amount > 0:
                emp_items.append({
                    "id": str(uuid.uuid4()),
                    "payroll_id": None,
                    "employee_id": emp["id"],
                    "item_code": comp.get("code"),
                    "item_name": comp.get("name"),
                    "type": "deduction",
                    "amount": amount,
                    "is_taxable": False
                })
                total_deductions += amount
        
        # Add proration deduction
        if proration_deduction > 0:
            emp_items.append({
                "id": str(uuid.uuid4()),
                "payroll_id": None,
                "employee_id": emp["id"],
                "item_code": "UNPAID",
                "item_name": f"Potongan Tidak Hadir ({absent_days} hari)",
                "type": "deduction",
                "amount": proration_deduction,
                "is_taxable": False
            })
            total_deductions += proration_deduction
        
        # ============================================================
        # PHASE 3: KPI BONUS INTEGRATION
        # SOURCE OF TRUTH: kpi_results collection
        # Calculate and add KPI-based bonus
        # ============================================================
        kpi_bonus_data = await calculate_kpi_bonus(emp["id"], data.period_month, data.period_year, salary_base)
        kpi_bonus_amount = 0
        
        if kpi_bonus_data.get("has_kpi") and kpi_bonus_data.get("bonus_amount", 0) > 0:
            kpi_bonus_amount = kpi_bonus_data["bonus_amount"]
            emp_items.append({
                "id": str(uuid.uuid4()),
                "payroll_id": None,
                "employee_id": emp["id"],
                "item_code": "KPIBONUS",
                "item_name": f"Bonus KPI ({kpi_bonus_data['kpi_rating']} - Score {kpi_bonus_data['kpi_score']:.1f}%)",
                "type": "allowance",
                "amount": kpi_bonus_amount,
                "is_taxable": True,
                "kpi_id": kpi_bonus_data.get("kpi_id"),
                "kpi_score": kpi_bonus_data.get("kpi_score"),
                "kpi_rating": kpi_bonus_data.get("kpi_rating"),
                "kpi_source": "kpi_results"  # SOURCE OF TRUTH marker
            })
            total_allowances += kpi_bonus_amount
        
        # Calculate PPh 21 (simplified) - UPDATED to include KPI bonus
        gross_salary = salary_base + total_allowances
        taxable_income = gross_salary - total_deductions
        
        # Simple tax calculation (5% for income > 4.5M)
        if taxable_income > 4500000:
            tax_amount = (taxable_income - 4500000) * 0.05
        else:
            tax_amount = 0
        
        # Calculate net salary
        net_salary = gross_salary - total_deductions - tax_amount
        
        # Create payroll record
        payroll_id = str(uuid.uuid4())
        payroll_record = {
            "id": payroll_id,
            "batch_id": batch_id,
            "batch_no": batch_no,
            "period": period,
            "period_month": data.period_month,
            "period_year": data.period_year,
            
            "employee_id": emp["id"],
            "employee_nik": emp.get("employee_id"),
            "employee_name": emp.get("full_name"),
            "department_id": emp.get("department_id"),
            "department_name": emp.get("department_name"),
            "branch_id": emp.get("branch_id"),
            
            "salary_base": salary_base,
            "total_allowances": total_allowances,
            "total_deductions": total_deductions,
            "gross_salary": gross_salary,
            "tax_amount": tax_amount,
            "net_salary": net_salary,
            
            "attendance": attendance_data,
            "leave": leave_data,
            "work_days": actual_work_days,
            "absent_days": absent_days,
            
            # KPI Bonus info for audit trail
            "kpi_bonus": {
                "has_kpi": kpi_bonus_data.get("has_kpi", False),
                "kpi_id": kpi_bonus_data.get("kpi_id"),
                "kpi_score": kpi_bonus_data.get("kpi_score", 0),
                "kpi_rating": kpi_bonus_data.get("kpi_rating", "N/A"),
                "bonus_amount": kpi_bonus_amount,
                "source": "kpi_results"
            },
            
            "status": "draft",
            "paid_at": None,
            "journal_id": None,
            
            "created_by": user_id,
            "created_by_name": user_name,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        payroll_records.append(payroll_record)
        
        # Update items with payroll_id
        for item in emp_items:
            item["payroll_id"] = payroll_id
            item["period"] = period  # Add period for reference
        item_records.extend(emp_items)
        
        total_gross_all += gross_salary
        total_deductions_all += total_deductions
        total_tax_all += tax_amount
        total_net_all += net_salary
    
    # Check if any employees were processed
    if not payroll_records:
        return {
            "status": "warning",
            "message": f"Tidak ada karyawan yang diproses untuk periode {period_display}",
            "skipped_employees": skipped_employees
        }
    
    # Bulk insert payroll records
    if payroll_records:
        await payroll_coll.insert_many(payroll_records)
    
    if item_records:
        await payroll_items_coll.insert_many(item_records)
    
    await log_activity(
        db, user_id, user_name,
        "create", "payroll_run",
        f"Payroll {period_display}: {len(payroll_records)} karyawan, Total Rp {total_net_all:,.0f}",
        request.client.host if request.client else "",
        branch_id
    )
    
    return {
        "status": "success",
        "message": f"Payroll {period_display} berhasil diproses",
        "batch_no": batch_no,
        "batch_id": batch_id,
        "period": period,
        "summary": {
            "employee_count": len(payroll_records),
            "total_gross": total_gross_all,
            "total_deductions": total_deductions_all,
            "total_tax": total_tax_all,
            "total_net": total_net_all,
            "skipped_count": len(skipped_employees)
        },
        "skipped_employees": skipped_employees if skipped_employees else None
    }


@router.post("/post/{batch_id}")
async def post_payroll(
    batch_id: str,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """
    Post payroll and create journal entry
    
    BUSINESS RULES (Blueprint v2.4.7):
    - Attendance period MUST be locked before posting
    - KPI results are integrated for bonus calculation
    
    ACCOUNTING INTEGRATION:
    - Debit: Beban Gaji (6-1100)
    - Credit: Kas/Bank (1-1100)
    - Credit: Hutang PPh 21 (2-1500) if any
    """
    user_id = user.get("user_id", user.get("id", ""))
    user_name = user.get("name", "")
    branch_id = user.get("branch_id", "")
    
    payroll_coll = _get_payroll_coll()
    db = get_db()
    
    # Get payroll records
    payrolls = await payroll_coll.find(
        {"batch_id": batch_id, "status": "draft"},
        {"_id": 0}
    ).to_list(1000)
    
    if not payrolls:
        raise HTTPException(status_code=404, detail="Batch payroll tidak ditemukan atau sudah diposting")
    
    # ============================================================
    # PHASE 3: ATTENDANCE PERIOD LOCK VALIDATION
    # Payroll tidak boleh diposting jika periode attendance belum dikunci
    # ============================================================
    period_month = payrolls[0].get("period_month")
    period_year = payrolls[0].get("period_year")
    
    attendance_lock = await check_attendance_period_locked(period_month, period_year)
    
    if not attendance_lock.get("is_locked", False):
        raise HTTPException(
            status_code=400, 
            detail=f"Periode attendance {period_month}/{period_year} belum dikunci. "
                   f"Silakan kunci periode attendance terlebih dahulu sebelum posting payroll."
        )
    
    # Calculate totals
    total_gross = sum(p.get("gross_salary", 0) for p in payrolls)
    total_deductions = sum(p.get("total_deductions", 0) for p in payrolls)
    total_tax = sum(p.get("tax_amount", 0) for p in payrolls)
    total_net = sum(p.get("net_salary", 0) for p in payrolls)
    
    batch_no = payrolls[0].get("batch_no")
    # period variable is used in payroll_data
    payroll_period = payrolls[0].get("period")
    period_display = f"{datetime(period_year, period_month, 1).strftime('%B %Y')}"
    
    # Create journal
    payroll_data = {
        "batch_id": batch_id,
        "batch_no": batch_no,
        "period": payroll_period,
        "period_display": period_display,
        "employee_count": len(payrolls),
        "total_gross": total_gross,
        "total_deductions": total_deductions,
        "tax_amount": total_tax,
        "net_salary": total_net
    }
    
    journal_no = await create_payroll_journal(payroll_data, user_id, user_name, branch_id)
    
    # Update all payroll records to posted
    await payroll_coll.update_many(
        {"batch_id": batch_id},
        {"$set": {
            "status": "posted",
            "posted_at": datetime.now(timezone.utc).isoformat(),
            "posted_by": user_id,
            "journal_id": journal_no,
            "attendance_period_locked": True
        }}
    )
    
    await log_activity(
        db, user_id, user_name,
        "post", "payroll",
        f"Payroll posted: {batch_no} - {len(payrolls)} karyawan - Journal {journal_no}",
        request.client.host if request.client else "",
        branch_id
    )
    
    return {
        "status": "success",
        "message": f"Payroll {period_display} berhasil diposting",
        "batch_no": batch_no,
        "journal_no": journal_no,
        "attendance_period_verified": True,
        "summary": {
            "employee_count": len(payrolls),
            "total_gross": total_gross,
            "total_net": total_net
        }
    }


@router.get("/{period}")
async def get_payroll(
    period: str,  # Format: "2026-03"
    status: Optional[str] = None,
    department_id: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Get payroll data for a period"""
    payroll_coll = _get_payroll_coll()
    
    query = {"period": period}
    if status:
        query["status"] = status
    if department_id:
        query["department_id"] = department_id
    
    payrolls = await payroll_coll.find(query, {"_id": 0}).to_list(500)
    
    # Calculate summary
    total_gross = sum(p.get("gross_salary", 0) for p in payrolls)
    total_deductions = sum(p.get("total_deductions", 0) for p in payrolls)
    total_tax = sum(p.get("tax_amount", 0) for p in payrolls)
    total_net = sum(p.get("net_salary", 0) for p in payrolls)
    
    return {
        "period": period,
        "payrolls": payrolls,
        "summary": {
            "employee_count": len(payrolls),
            "total_gross": total_gross,
            "total_deductions": total_deductions,
            "total_tax": total_tax,
            "total_net": total_net
        }
    }


@router.get("/employee/{employee_id}/history")
async def get_employee_payroll_history(
    employee_id: str,
    year: Optional[int] = None,
    user: dict = Depends(get_current_user)
):
    """Get payroll history for an employee"""
    employees_coll = _get_employees_coll()
    payroll_coll = _get_payroll_coll()
    
    employee = await employees_coll.find_one(
        {"$or": [{"id": employee_id}, {"employee_id": employee_id.upper()}]},
        {"_id": 0}
    )
    
    if not employee:
        raise HTTPException(status_code=404, detail="Karyawan tidak ditemukan")
    
    query = {"employee_id": employee["id"], "status": "posted"}
    if year:
        query["period_year"] = year
    
    payrolls = await payroll_coll.find(
        query, {"_id": 0}
    ).sort("period", -1).to_list(24)
    
    return {
        "employee": {
            "id": employee["id"],
            "name": employee.get("full_name"),
            "employee_id": employee.get("employee_id")
        },
        "history": payrolls,
        "total_records": len(payrolls)
    }


@router.get("/slip/{payroll_id}")
async def get_payroll_slip(
    payroll_id: str,
    user: dict = Depends(get_current_user)
):
    """Get payroll slip detail with all items"""
    payroll_coll = _get_payroll_coll()
    payroll_items_coll = _get_payroll_items_coll()
    
    payroll = await payroll_coll.find_one({"id": payroll_id}, {"_id": 0})
    if not payroll:
        raise HTTPException(status_code=404, detail="Slip gaji tidak ditemukan")
    
    items = await payroll_items_coll.find(
        {"payroll_id": payroll_id},
        {"_id": 0}
    ).to_list(50)
    
    allowances = [i for i in items if i.get("type") == "allowance"]
    deductions = [i for i in items if i.get("type") == "deduction"]
    
    payroll["items"] = {
        "allowances": allowances,
        "deductions": deductions
    }
    
    return payroll



# ============================================================
# PHASE 3: ATTENDANCE PERIOD LOCK ENDPOINTS
# ============================================================

class AttendancePeriodLock(BaseModel):
    """Request to lock attendance period"""
    period_month: int
    period_year: int


@router.post("/attendance-period/lock")
async def lock_attendance_period(
    data: AttendancePeriodLock,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """
    Lock attendance period for payroll processing
    
    BUSINESS RULES:
    - Once locked, attendance for this period cannot be modified
    - Payroll can only be posted if attendance period is locked
    """
    user_id = user.get("user_id", user.get("id", ""))
    user_name = user.get("name", "")
    
    attendance_periods = _get_attendance_periods_coll()
    db = get_db()
    
    period_key = f"{data.period_year}-{data.period_month:02d}"
    
    # Check if period exists
    existing = await attendance_periods.find_one({"period": period_key})
    
    if existing and existing.get("is_locked"):
        return {
            "status": "already_locked",
            "message": f"Periode {period_key} sudah dikunci sebelumnya",
            "locked_at": existing.get("locked_at"),
            "locked_by": existing.get("locked_by_name")
        }
    
    now = datetime.now(timezone.utc).isoformat()
    
    if existing:
        # Update existing record
        await attendance_periods.update_one(
            {"period": period_key},
            {"$set": {
                "is_locked": True,
                "locked_at": now,
                "locked_by": user_id,
                "locked_by_name": user_name
            }}
        )
    else:
        # Create new record
        await attendance_periods.insert_one({
            "id": str(uuid.uuid4()),
            "period": period_key,
            "period_month": data.period_month,
            "period_year": data.period_year,
            "is_locked": True,
            "locked_at": now,
            "locked_by": user_id,
            "locked_by_name": user_name,
            "created_at": now
        })
    
    await log_activity(
        db, user_id, user_name,
        "lock", "attendance_period",
        f"Attendance period {period_key} locked for payroll",
        request.client.host if request.client else "",
        user.get("branch_id", "")
    )
    
    return {
        "status": "success",
        "message": f"Periode attendance {period_key} berhasil dikunci",
        "period": period_key,
        "locked_at": now,
        "locked_by": user_name
    }


@router.post("/attendance-period/unlock")
async def unlock_attendance_period(
    data: AttendancePeriodLock,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """
    Unlock attendance period (for corrections)
    
    BUSINESS RULES (AUDIT READY):
    - RBAC: Only HR_ADMIN or SUPER_ADMIN can unlock
    - IMMUTABLE: Cannot unlock if payroll already POSTED
    - All unlock actions are logged for audit trail
    
    WARNING: This will allow attendance modifications
    """
    user_id = user.get("user_id", user.get("id", ""))
    user_name = user.get("name", "")
    user_role = user.get("role", "").lower()
    
    # ============================================================
    # RBAC CHECK: Only HR_ADMIN / SUPER_ADMIN can unlock
    # ============================================================
    if user_role not in ["owner", "admin", "hr_admin", "super_admin"]:
        raise HTTPException(
            status_code=403,
            detail="Hanya HR Admin atau Super Admin yang dapat unlock periode attendance."
        )
    
    attendance_periods = _get_attendance_periods_coll()
    payroll_coll = _get_payroll_coll()
    db = get_db()
    
    period_key = f"{data.period_year}-{data.period_month:02d}"
    
    # ============================================================
    # IMMUTABLE CHECK: Cannot unlock if payroll already POSTED
    # ============================================================
    posted_payroll = await payroll_coll.find_one({
        "period": period_key,
        "status": "posted"
    })
    
    if posted_payroll:
        raise HTTPException(
            status_code=400,
            detail=f"IMMUTABLE: Periode {period_key} tidak dapat di-unlock karena payroll sudah diposting (Journal: {posted_payroll.get('journal_id', 'N/A')})."
        )
    
    await attendance_periods.update_one(
        {"period": period_key},
        {"$set": {
            "is_locked": False,
            "unlocked_at": datetime.now(timezone.utc).isoformat(),
            "unlocked_by": user_id,
            "unlocked_by_name": user_name,
            "unlock_reason": "Manual unlock by authorized user"
        }}
    )
    
    # AUDIT LOG for unlock action
    await log_activity(
        db, user_id, user_name,
        "unlock", "attendance_period",
        f"[AUDIT] Attendance period {period_key} unlocked by {user_name} (role: {user_role})",
        request.client.host if request.client else "",
        user.get("branch_id", "")
    )
    
    return {
        "status": "success",
        "message": f"Periode attendance {period_key} berhasil di-unlock",
        "period": period_key,
        "unlocked_by": user_name,
        "unlocked_by_role": user_role
    }


@router.get("/attendance-period/status/{period}")
async def get_attendance_period_status(
    period: str,  # Format: "2026-03"
    user: dict = Depends(get_current_user)
):
    """Get attendance period lock status"""
    parts = period.split("-")
    if len(parts) != 2:
        raise HTTPException(status_code=400, detail="Format periode tidak valid. Gunakan YYYY-MM")
    
    year = int(parts[0])
    month = int(parts[1])
    
    lock_status = await check_attendance_period_locked(month, year)
    
    return {
        "period": period,
        **lock_status
    }
