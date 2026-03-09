# OCB GROUP SUPER ERP - Payroll Routes
# Payroll Terintegrasi dengan Absensi & Selisih Kas

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel
import uuid
import calendar

from database import get_db
from models.erp_models import (
    PayrollPeriod, PayrollDetail, AttendanceStatus
)

router = APIRouter(prefix="/api/payroll", tags=["Payroll"])

def gen_id():
    return str(uuid.uuid4())

def now_iso():
    return datetime.now(timezone.utc).isoformat()

# Collections
def payroll_period_col():
    return get_db()['payroll_periods']

def payroll_detail_col():
    return get_db()['payroll_details']

def employees_col():
    return get_db()['employees']

def attendance_col():
    return get_db()['attendance']

def selisih_col():
    return get_db()['selisih_kas']

def payroll_rule_col():
    return get_db()['master_payroll_rules']

# ==================== PAYROLL PERIOD ====================

class PayrollPeriodCreate(BaseModel):
    period_month: int
    period_year: int

@router.get("/periods")
async def list_payroll_periods(year: Optional[int] = None):
    query = {}
    if year:
        query["period_year"] = year
    
    cursor = payroll_period_col().find(query, {"_id": 0}).sort([("period_year", -1), ("period_month", -1)])
    periods = await cursor.to_list(length=24)
    return {"periods": periods}

@router.get("/periods/{period_id}")
async def get_payroll_period(period_id: str):
    period = await payroll_period_col().find_one({"id": period_id}, {"_id": 0})
    if not period:
        raise HTTPException(status_code=404, detail="Periode tidak ditemukan")
    
    # Get details
    details = await payroll_detail_col().find({"period_id": period_id}, {"_id": 0}).to_list(length=1000)
    
    return {"period": period, "details": details}

@router.post("/periods")
async def create_payroll_period(data: PayrollPeriodCreate):
    # Check if period already exists
    existing = await payroll_period_col().find_one({
        "period_month": data.period_month,
        "period_year": data.period_year
    })
    if existing:
        raise HTTPException(status_code=400, detail="Periode payroll sudah ada")
    
    # Get month name
    month_names = ["", "Januari", "Februari", "Maret", "April", "Mei", "Juni",
                   "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    period_name = f"{month_names[data.period_month]} {data.period_year}"
    
    # Calculate dates
    _, last_day = calendar.monthrange(data.period_year, data.period_month)
    start_date = f"{data.period_year}-{data.period_month:02d}-01"
    end_date = f"{data.period_year}-{data.period_month:02d}-{last_day}"
    
    period = PayrollPeriod(
        id=gen_id(),
        period_month=data.period_month,
        period_year=data.period_year,
        period_name=period_name,
        start_date=start_date,
        end_date=end_date,
        status="draft",
        created_at=now_iso(),
        updated_at=now_iso()
    )
    
    await payroll_period_col().insert_one(period.model_dump())
    
    return {"message": "Periode payroll berhasil dibuat", "period": period.model_dump()}

# ==================== GENERATE PAYROLL ====================

@router.post("/periods/{period_id}/generate")
async def generate_payroll(period_id: str):
    period = await payroll_period_col().find_one({"id": period_id})
    if not period:
        raise HTTPException(status_code=404, detail="Periode tidak ditemukan")
    
    if period.get("status") not in ["draft", "processing"]:
        raise HTTPException(status_code=400, detail="Periode sudah diproses")
    
    # Update status
    await payroll_period_col().update_one(
        {"id": period_id},
        {"$set": {"status": "processing", "updated_at": now_iso()}}
    )
    
    # Get all active employees
    employees = await employees_col().find({"status": "active"}, {"_id": 0}).to_list(length=1000)
    
    # Get attendance for this period
    start_date = period["start_date"]
    end_date = period["end_date"]
    
    # Get working days (exclude weekends)
    year = period["period_year"]
    month = period["period_month"]
    _, last_day = calendar.monthrange(year, month)
    
    hari_kerja = 0
    for day in range(1, last_day + 1):
        date = datetime(year, month, day)
        if date.weekday() < 5:  # Monday = 0, Friday = 4
            hari_kerja += 1
    
    total_gross = 0
    total_deductions = 0
    total_net = 0
    
    payroll_details = []
    
    for emp in employees:
        # Get payroll rule
        rule = await payroll_rule_col().find_one({"jabatan_id": emp.get("jabatan_id")})
        if not rule:
            rule = {
                "gaji_pokok": emp.get("gaji_pokok", 0),
                "tunjangan_jabatan": 0,
                "tunjangan_transport": 0,
                "tunjangan_makan": 0,
                "bonus_kehadiran_full": 0,
                "potongan_telat_per_menit": 1000,
                "potongan_alpha_per_hari": 50000
            }
        
        # Get attendance summary
        attendance_list = await attendance_col().find({
            "employee_id": emp["id"],
            "tanggal": {"$gte": start_date, "$lte": end_date}
        }).to_list(length=31)
        
        hari_hadir = len([a for a in attendance_list if a.get("status") in ["hadir", "telat"]])
        hari_telat = len([a for a in attendance_list if a.get("status") == "telat"])
        hari_alpha = hari_kerja - len([a for a in attendance_list if a.get("status") not in ["libur"]])
        hari_izin = len([a for a in attendance_list if a.get("status") == "izin"])
        hari_cuti = len([a for a in attendance_list if a.get("status") == "cuti"])
        hari_sakit = len([a for a in attendance_list if a.get("status") == "sakit"])
        total_telat_menit = sum(a.get("telat_menit", 0) for a in attendance_list)
        total_lembur_menit = sum(a.get("lembur_menit", 0) for a in attendance_list)
        
        # Get minus kas for this employee this month
        selisih_list = await selisih_col().find({
            "penjaga_id": emp["id"],
            "tanggal": {"$gte": start_date, "$lte": end_date},
            "jenis": "minus",
            "is_potong_gaji": True
        }).to_list(length=100)
        
        potongan_minus_kas = sum(s.get("potong_gaji_amount", 0) for s in selisih_list)
        
        # Calculate earnings
        gaji_pokok = rule.get("gaji_pokok", 0) or emp.get("gaji_pokok", 0)
        tunjangan_jabatan = rule.get("tunjangan_jabatan", 0)
        tunjangan_transport = rule.get("tunjangan_transport", 0)
        tunjangan_makan = rule.get("tunjangan_makan", 0)
        
        # Bonus kehadiran (full attendance)
        bonus_kehadiran = 0
        if hari_hadir >= hari_kerja and hari_telat == 0:
            bonus_kehadiran = rule.get("bonus_kehadiran_full", 0)
        
        # Overtime
        lembur_nominal = 0
        if total_lembur_menit > 0:
            lembur_per_jam = gaji_pokok / (hari_kerja * 8) * 1.5  # 1.5x hourly rate
            lembur_nominal = (total_lembur_menit / 60) * lembur_per_jam
        
        # Calculate deductions
        potongan_telat = total_telat_menit * rule.get("potongan_telat_per_menit", 1000)
        potongan_alpha = hari_alpha * rule.get("potongan_alpha_per_hari", 50000)
        
        # Totals
        total_earnings = (gaji_pokok + tunjangan_jabatan + tunjangan_transport + 
                         tunjangan_makan + bonus_kehadiran + lembur_nominal)
        total_deductions_emp = potongan_telat + potongan_alpha + potongan_minus_kas
        take_home_pay = total_earnings - total_deductions_emp
        
        detail = PayrollDetail(
            id=gen_id(),
            period_id=period_id,
            period_name=period["period_name"],
            employee_id=emp["id"],
            employee_nik=emp.get("nik", ""),
            employee_name=emp.get("name", ""),
            jabatan=emp.get("jabatan_name", ""),
            branch_id=emp.get("branch_id", ""),
            branch_name=emp.get("branch_name", ""),
            bank_name=emp.get("bank_name", ""),
            bank_account=emp.get("bank_account", ""),
            gaji_pokok=gaji_pokok,
            tunjangan_jabatan=tunjangan_jabatan,
            tunjangan_transport=tunjangan_transport,
            tunjangan_makan=tunjangan_makan,
            bonus_kehadiran=bonus_kehadiran,
            lembur_jam=round(total_lembur_menit / 60, 2),
            lembur_nominal=round(lembur_nominal),
            potongan_telat=potongan_telat,
            potongan_alpha=potongan_alpha,
            potongan_minus_kas=potongan_minus_kas,
            hari_kerja=hari_kerja,
            hari_hadir=hari_hadir,
            hari_telat=hari_telat,
            hari_alpha=hari_alpha,
            hari_izin=hari_izin,
            hari_cuti=hari_cuti,
            hari_sakit=hari_sakit,
            total_menit_telat=total_telat_menit,
            total_menit_lembur=total_lembur_menit,
            total_earnings=round(total_earnings),
            total_deductions=round(total_deductions_emp),
            take_home_pay=round(take_home_pay),
            status="draft",
            created_at=now_iso(),
            updated_at=now_iso()
        )
        
        # Delete existing detail for this employee/period if regenerating
        await payroll_detail_col().delete_one({
            "period_id": period_id,
            "employee_id": emp["id"]
        })
        
        await payroll_detail_col().insert_one(detail.model_dump())
        payroll_details.append(detail.model_dump())
        
        total_gross += total_earnings
        total_deductions += total_deductions_emp
        total_net += take_home_pay
    
    # Update period summary
    await payroll_period_col().update_one(
        {"id": period_id},
        {"$set": {
            "total_employees": len(employees),
            "total_gross": round(total_gross),
            "total_deductions": round(total_deductions),
            "total_net": round(total_net),
            "status": "draft",
            "updated_at": now_iso()
        }}
    )
    
    return {
        "message": "Payroll berhasil digenerate",
        "period_id": period_id,
        "total_employees": len(employees),
        "total_gross": round(total_gross),
        "total_deductions": round(total_deductions),
        "total_net": round(total_net)
    }

# ==================== PAYROLL DETAILS ====================

@router.get("/details")
async def list_payroll_details(
    period_id: Optional[str] = None,
    employee_id: Optional[str] = None,
    branch_id: Optional[str] = None
):
    query = {}
    if period_id:
        query["period_id"] = period_id
    if employee_id:
        query["employee_id"] = employee_id
    if branch_id:
        query["branch_id"] = branch_id
    
    cursor = payroll_detail_col().find(query, {"_id": 0}).sort("employee_name", 1)
    details = await cursor.to_list(length=1000)
    
    return {"details": details, "total": len(details)}

@router.get("/details/{detail_id}")
async def get_payroll_detail(detail_id: str):
    detail = await payroll_detail_col().find_one({"id": detail_id}, {"_id": 0})
    if not detail:
        raise HTTPException(status_code=404, detail="Detail payroll tidak ditemukan")
    return detail

class PayrollAdjustment(BaseModel):
    bonus_performa: float = 0
    bonus_cabang: float = 0
    bonus_lainnya: float = 0
    tunjangan_lainnya: float = 0
    potongan_pinjaman: float = 0
    potongan_bpjs: float = 0
    potongan_pph21: float = 0
    potongan_lainnya: float = 0
    notes: str = ""

@router.put("/details/{detail_id}/adjust")
async def adjust_payroll_detail(detail_id: str, data: PayrollAdjustment):
    detail = await payroll_detail_col().find_one({"id": detail_id})
    if not detail:
        raise HTTPException(status_code=404, detail="Detail payroll tidak ditemukan")
    
    if detail.get("status") == "paid":
        raise HTTPException(status_code=400, detail="Payroll yang sudah dibayar tidak bisa diubah")
    
    # Recalculate totals
    total_earnings = (
        detail.get("gaji_pokok", 0) +
        detail.get("tunjangan_jabatan", 0) +
        detail.get("tunjangan_transport", 0) +
        detail.get("tunjangan_makan", 0) +
        data.tunjangan_lainnya +
        detail.get("bonus_kehadiran", 0) +
        data.bonus_performa +
        data.bonus_cabang +
        data.bonus_lainnya +
        detail.get("lembur_nominal", 0)
    )
    
    total_deductions = (
        detail.get("potongan_telat", 0) +
        detail.get("potongan_alpha", 0) +
        data.potongan_pinjaman +
        detail.get("potongan_minus_kas", 0) +
        data.potongan_bpjs +
        data.potongan_pph21 +
        data.potongan_lainnya
    )
    
    take_home_pay = total_earnings - total_deductions
    
    update_data = data.model_dump()
    update_data["total_earnings"] = round(total_earnings)
    update_data["total_deductions"] = round(total_deductions)
    update_data["take_home_pay"] = round(take_home_pay)
    update_data["updated_at"] = now_iso()
    
    await payroll_detail_col().update_one({"id": detail_id}, {"$set": update_data})
    
    # Update period totals
    period_id = detail["period_id"]
    all_details = await payroll_detail_col().find({"period_id": period_id}).to_list(length=1000)
    
    period_gross = sum(d.get("total_earnings", 0) for d in all_details)
    period_deductions = sum(d.get("total_deductions", 0) for d in all_details)
    period_net = sum(d.get("take_home_pay", 0) for d in all_details)
    
    await payroll_period_col().update_one(
        {"id": period_id},
        {"$set": {
            "total_gross": round(period_gross),
            "total_deductions": round(period_deductions),
            "total_net": round(period_net),
            "updated_at": now_iso()
        }}
    )
    
    return {"message": "Payroll berhasil disesuaikan", "take_home_pay": round(take_home_pay)}

# ==================== APPROVAL & PAYMENT ====================

@router.post("/periods/{period_id}/approve")
async def approve_payroll_period(period_id: str, approved_by: str):
    period = await payroll_period_col().find_one({"id": period_id})
    if not period:
        raise HTTPException(status_code=404, detail="Periode tidak ditemukan")
    
    if period.get("status") not in ["draft", "processing"]:
        raise HTTPException(status_code=400, detail="Periode tidak bisa diapprove")
    
    await payroll_period_col().update_one(
        {"id": period_id},
        {"$set": {
            "status": "approved",
            "approved_by": approved_by,
            "approved_at": now_iso(),
            "updated_at": now_iso()
        }}
    )
    
    # Update all details
    await payroll_detail_col().update_many(
        {"period_id": period_id},
        {"$set": {"status": "approved", "updated_at": now_iso()}}
    )
    
    return {"message": "Payroll berhasil diapprove"}

@router.post("/periods/{period_id}/pay")
async def mark_payroll_paid(period_id: str):
    period = await payroll_period_col().find_one({"id": period_id})
    if not period:
        raise HTTPException(status_code=404, detail="Periode tidak ditemukan")
    
    if period.get("status") != "approved":
        raise HTTPException(status_code=400, detail="Periode harus diapprove terlebih dahulu")
    
    await payroll_period_col().update_one(
        {"id": period_id},
        {"$set": {
            "status": "paid",
            "paid_at": now_iso(),
            "updated_at": now_iso()
        }}
    )
    
    # Update all details
    await payroll_detail_col().update_many(
        {"period_id": period_id},
        {"$set": {"status": "paid", "updated_at": now_iso()}}
    )
    
    return {"message": "Payroll berhasil ditandai sudah dibayar"}

# ==================== SLIP GAJI ====================

@router.get("/slip/{detail_id}")
async def get_slip_gaji(detail_id: str):
    detail = await payroll_detail_col().find_one({"id": detail_id}, {"_id": 0})
    if not detail:
        raise HTTPException(status_code=404, detail="Detail payroll tidak ditemukan")
    
    # Get employee info
    employee = await employees_col().find_one({"id": detail["employee_id"]}, {"_id": 0})
    
    return {
        "slip": detail,
        "employee": employee,
        "company": {
            "name": "OCB GROUP",
            "address": "Banjarmasin, Kalimantan Selatan"
        }
    }

# ==================== REPORTS ====================

@router.get("/reports/summary")
async def get_payroll_summary(year: int):
    periods = await payroll_period_col().find({"period_year": year}, {"_id": 0}).to_list(length=12)
    
    monthly_data = []
    for period in periods:
        monthly_data.append({
            "month": period["period_month"],
            "period_name": period["period_name"],
            "total_employees": period.get("total_employees", 0),
            "total_gross": period.get("total_gross", 0),
            "total_deductions": period.get("total_deductions", 0),
            "total_net": period.get("total_net", 0),
            "status": period.get("status", "draft")
        })
    
    return {
        "year": year,
        "monthly_data": monthly_data,
        "total_year": {
            "gross": sum(p.get("total_gross", 0) for p in periods),
            "deductions": sum(p.get("total_deductions", 0) for p in periods),
            "net": sum(p.get("total_net", 0) for p in periods)
        }
    }

@router.get("/reports/by-branch")
async def get_payroll_by_branch(period_id: str):
    details = await payroll_detail_col().find({"period_id": period_id}, {"_id": 0}).to_list(length=1000)
    
    # Group by branch
    branch_data = {}
    for d in details:
        branch_id = d.get("branch_id", "unassigned")
        branch_name = d.get("branch_name", "Tidak Ada Cabang")
        
        if branch_id not in branch_data:
            branch_data[branch_id] = {
                "branch_id": branch_id,
                "branch_name": branch_name,
                "employee_count": 0,
                "total_gross": 0,
                "total_deductions": 0,
                "total_net": 0
            }
        
        branch_data[branch_id]["employee_count"] += 1
        branch_data[branch_id]["total_gross"] += d.get("total_earnings", 0)
        branch_data[branch_id]["total_deductions"] += d.get("total_deductions", 0)
        branch_data[branch_id]["total_net"] += d.get("take_home_pay", 0)
    
    return {"branches": list(branch_data.values())}
