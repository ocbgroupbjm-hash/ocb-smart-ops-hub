# OCB TITAN ERP - HR PAYROLL ENGINE
# Kalkulasi gaji dengan auto-journal ke Accounting

from fastapi import APIRouter, HTTPException, Depends, Request, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from database import db
from utils.auth import get_current_user
from routes.rbac_system import log_activity
import uuid

router = APIRouter(prefix="/api/hr/payroll", tags=["HR Payroll Engine"])

# Collections
payroll_collection = db["payroll"]
payroll_items = db["payroll_items"]
employees = db["employees"]
attendance_logs = db["attendance_logs"]
leave_requests = db["leave_requests"]
journal_entries = db["journal_entries"]

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
    
    existing = await db.payroll_components.find_one({"code": data.code.upper()})
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
    
    await db.payroll_components.insert_one(component)
    
    return {"status": "success", "component_id": component["id"]}

@router.get("/components")
async def get_payroll_components(
    type: Optional[str] = None,  # allowance, deduction, tax
    user: dict = Depends(get_current_user)
):
    """Get all payroll components"""
    query = {"is_active": True}
    if type:
        query["type"] = type
    
    components = await db.payroll_components.find(query, {"_id": 0}).to_list(50)
    return {"components": components}


# ==================== PAYROLL RUN ====================

async def calculate_attendance_data(employee_id: str, month: int, year: int) -> Dict:
    """Calculate attendance metrics for payroll"""
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
    
    paid_leave_days = sum(l.get("total_days", 0) for l in leaves if l.get("leave_type_code") != "UNPAID")
    unpaid_leave_days = sum(l.get("total_days", 0) for l in leaves if l.get("leave_type_code") == "UNPAID")
    
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
    journal_number = await generate_transaction_number(db, "JV")
    
    # Get account codes
    salary_expense = "6-1100"  # Beban Gaji
    cash_account = "1-1100"   # Kas
    tax_payable = "2-1500"    # Hutang Pajak
    
    total_gross = payroll_data.get("total_gross", 0)
    total_deductions = payroll_data.get("total_deductions", 0)
    tax_amount = payroll_data.get("tax_amount", 0)
    net_salary = payroll_data.get("net_salary", 0)
    
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
    
    Business Rules:
    - Calculate basic salary
    - Add allowances
    - Deduct absences (unpaid leave)
    - Calculate tax (PPh 21)
    - Generate journal entries
    - SSOT: salary_base from Employee Master
    """
    user_id = user.get("user_id", user.get("id", ""))
    user_name = user.get("name", "")
    branch_id = data.branch_id or user.get("branch_id", "")
    
    period = f"{data.period_year}-{data.period_month:02d}"
    period_display = f"{datetime(data.period_year, data.period_month, 1).strftime('%B %Y')}"
    
    # Check if payroll already exists for this period
    existing = await payroll_collection.find_one({
        "period": period,
        "status": {"$in": ["draft", "posted"]}
    })
    
    if existing and existing.get("status") == "posted":
        raise HTTPException(
            status_code=400, 
            detail=f"Payroll periode {period_display} sudah diposting"
        )
    
    # Get employees to process
    emp_query = {"status": "active"}
    if data.branch_id:
        emp_query["branch_id"] = data.branch_id
    if data.department_id:
        emp_query["department_id"] = data.department_id
    if data.employee_ids:
        emp_query["id"] = {"$in": data.employee_ids}
    
    employee_list = await employees.find(emp_query, {"_id": 0}).to_list(1000)
    
    if not employee_list:
        raise HTTPException(status_code=400, detail="Tidak ada karyawan yang diproses")
    
    # Get standard components
    components = await db.payroll_components.find(
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
    
    for emp in employee_list:
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
        
        # Calculate PPh 21 (simplified)
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
        item_records.extend(emp_items)
        
        total_gross_all += gross_salary
        total_deductions_all += total_deductions
        total_tax_all += tax_amount
        total_net_all += net_salary
    
    # Bulk insert payroll records
    if payroll_records:
        await payroll_collection.insert_many(payroll_records)
    
    if item_records:
        await payroll_items.insert_many(item_records)
    
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
            "total_net": total_net_all
        }
    }


@router.post("/post/{batch_id}")
async def post_payroll(
    batch_id: str,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """
    Post payroll and create journal entry
    
    ACCOUNTING INTEGRATION:
    - Debit: Beban Gaji
    - Credit: Kas/Bank
    - Credit: Hutang PPh 21 (if any)
    """
    user_id = user.get("user_id", user.get("id", ""))
    user_name = user.get("name", "")
    branch_id = user.get("branch_id", "")
    
    # Get payroll records
    payrolls = await payroll_collection.find(
        {"batch_id": batch_id, "status": "draft"},
        {"_id": 0}
    ).to_list(1000)
    
    if not payrolls:
        raise HTTPException(status_code=404, detail="Batch payroll tidak ditemukan atau sudah diposting")
    
    # Calculate totals
    total_gross = sum(p.get("gross_salary", 0) for p in payrolls)
    total_deductions = sum(p.get("total_deductions", 0) for p in payrolls)
    total_tax = sum(p.get("tax_amount", 0) for p in payrolls)
    total_net = sum(p.get("net_salary", 0) for p in payrolls)
    
    batch_no = payrolls[0].get("batch_no")
    period = payrolls[0].get("period")
    period_month = payrolls[0].get("period_month")
    period_year = payrolls[0].get("period_year")
    period_display = f"{datetime(period_year, period_month, 1).strftime('%B %Y')}"
    
    # Create journal
    payroll_data = {
        "batch_id": batch_id,
        "batch_no": batch_no,
        "period_display": period_display,
        "employee_count": len(payrolls),
        "total_gross": total_gross,
        "total_deductions": total_deductions,
        "tax_amount": total_tax,
        "net_salary": total_net
    }
    
    journal_no = await create_payroll_journal(payroll_data, user_id, user_name, branch_id)
    
    # Update all payroll records to posted
    await payroll_collection.update_many(
        {"batch_id": batch_id},
        {"$set": {
            "status": "posted",
            "posted_at": datetime.now(timezone.utc).isoformat(),
            "posted_by": user_id,
            "journal_id": journal_no
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
    query = {"period": period}
    if status:
        query["status"] = status
    if department_id:
        query["department_id"] = department_id
    
    payrolls = await payroll_collection.find(query, {"_id": 0}).to_list(500)
    
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
    employee = await employees.find_one(
        {"$or": [{"id": employee_id}, {"employee_id": employee_id.upper()}]},
        {"_id": 0}
    )
    
    if not employee:
        raise HTTPException(status_code=404, detail="Karyawan tidak ditemukan")
    
    query = {"employee_id": employee["id"], "status": "posted"}
    if year:
        query["period_year"] = year
    
    payrolls = await payroll_collection.find(
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
    payroll = await payroll_collection.find_one({"id": payroll_id}, {"_id": 0})
    if not payroll:
        raise HTTPException(status_code=404, detail="Slip gaji tidak ditemukan")
    
    items = await payroll_items.find(
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
