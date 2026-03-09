# OCB GROUP SUPER ERP - Reports System
# Comprehensive Reporting for All Modules

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel
import calendar

from database import get_db

router = APIRouter(prefix="/api/reports", tags=["Reports"])

def get_wib_now():
    return datetime.now(timezone.utc) + timedelta(hours=7)

# Collections
def setoran_col():
    return get_db()['setoran_harian']

def selisih_col():
    return get_db()['selisih_kas']

def employees_col():
    return get_db()['employees']

def attendance_col():
    return get_db()['attendance']

def payroll_col():
    return get_db()['payroll_details']

def branches_col():
    return get_db()['branches']

def transactions_col():
    return get_db()['transactions']

# ==================== SETORAN REPORTS ====================

@router.get("/setoran/daily")
async def report_setoran_daily(tanggal: str):
    """Daily setoran report by branch"""
    setoran = await setoran_col().find({"tanggal": tanggal}, {"_id": 0}).to_list(length=100)
    branches = await branches_col().find({}, {"_id": 0}).to_list(length=100)
    
    report = []
    sudah_setor_ids = set(s["branch_id"] for s in setoran)
    
    for b in branches:
        s = next((x for x in setoran if x.get("branch_id") == b.get("id")), None)
        report.append({
            "branch_id": b.get("id"),
            "branch_code": b.get("code", ""),
            "branch_name": b.get("name", ""),
            "status": "sudah_setor" if s else "belum_setor",
            "total_penjualan": s.get("total_penjualan", 0) if s else 0,
            "total_setoran": s.get("total_setoran", 0) if s else 0,
            "selisih": s.get("selisih", 0) if s else 0,
            "penjaga": s.get("penjaga_name", "") if s else "",
            "jam_setor": s.get("input_at", "") if s else ""
        })
    
    return {
        "tanggal": tanggal,
        "total_cabang": len(branches),
        "sudah_setor": len(sudah_setor_ids),
        "belum_setor": len(branches) - len(sudah_setor_ids),
        "total_penjualan": sum(s.get("total_penjualan", 0) for s in setoran),
        "total_setoran": sum(s.get("total_setoran", 0) for s in setoran),
        "total_minus": sum(s.get("selisih", 0) for s in setoran if s.get("selisih", 0) < 0),
        "total_plus": sum(s.get("selisih", 0) for s in setoran if s.get("selisih", 0) > 0),
        "detail": report
    }

@router.get("/setoran/monthly")
async def report_setoran_monthly(month: int, year: int):
    """Monthly setoran report"""
    _, last_day = calendar.monthrange(year, month)
    start_date = f"{year}-{month:02d}-01"
    end_date = f"{year}-{month:02d}-{last_day}"
    
    setoran = await setoran_col().find({
        "tanggal": {"$gte": start_date, "$lte": end_date}
    }, {"_id": 0}).to_list(length=1500)
    
    # Group by date
    daily_summary = {}
    for s in setoran:
        date = s.get("tanggal")
        if date not in daily_summary:
            daily_summary[date] = {
                "tanggal": date,
                "total_penjualan": 0,
                "total_setoran": 0,
                "total_minus": 0,
                "total_plus": 0,
                "cabang_count": 0
            }
        daily_summary[date]["total_penjualan"] += s.get("total_penjualan", 0)
        daily_summary[date]["total_setoran"] += s.get("total_setoran", 0)
        if s.get("selisih", 0) < 0:
            daily_summary[date]["total_minus"] += abs(s.get("selisih", 0))
        else:
            daily_summary[date]["total_plus"] += s.get("selisih", 0)
        daily_summary[date]["cabang_count"] += 1
    
    # Group by branch
    branch_summary = {}
    for s in setoran:
        bid = s.get("branch_id")
        if bid not in branch_summary:
            branch_summary[bid] = {
                "branch_id": bid,
                "branch_name": s.get("branch_name", ""),
                "total_penjualan": 0,
                "total_setoran": 0,
                "total_minus": 0,
                "total_plus": 0,
                "count": 0
            }
        branch_summary[bid]["total_penjualan"] += s.get("total_penjualan", 0)
        branch_summary[bid]["total_setoran"] += s.get("total_setoran", 0)
        if s.get("selisih", 0) < 0:
            branch_summary[bid]["total_minus"] += abs(s.get("selisih", 0))
        else:
            branch_summary[bid]["total_plus"] += s.get("selisih", 0)
        branch_summary[bid]["count"] += 1
    
    return {
        "period": f"{year}-{month:02d}",
        "total_records": len(setoran),
        "total_penjualan": sum(s.get("total_penjualan", 0) for s in setoran),
        "total_setoran": sum(s.get("total_setoran", 0) for s in setoran),
        "total_minus": sum(abs(s.get("selisih", 0)) for s in setoran if s.get("selisih", 0) < 0),
        "total_plus": sum(s.get("selisih", 0) for s in setoran if s.get("selisih", 0) > 0),
        "by_date": sorted(daily_summary.values(), key=lambda x: x["tanggal"]),
        "by_branch": sorted(branch_summary.values(), key=lambda x: x["total_penjualan"], reverse=True)
    }

# ==================== SELISIH KAS REPORTS ====================

@router.get("/selisih/by-employee")
async def report_selisih_by_employee(month: int, year: int):
    """Selisih kas report grouped by employee"""
    _, last_day = calendar.monthrange(year, month)
    start_date = f"{year}-{month:02d}-01"
    end_date = f"{year}-{month:02d}-{last_day}"
    
    selisih = await selisih_col().find({
        "tanggal": {"$gte": start_date, "$lte": end_date}
    }, {"_id": 0}).to_list(length=1000)
    
    # Group by employee
    emp_data = {}
    for s in selisih:
        eid = s.get("penjaga_id")
        if eid not in emp_data:
            emp_data[eid] = {
                "employee_id": eid,
                "employee_name": s.get("penjaga_name", ""),
                "total_minus": 0,
                "total_plus": 0,
                "minus_count": 0,
                "plus_count": 0,
                "pending_count": 0,
                "resolved_count": 0
            }
        if s.get("jenis") == "minus":
            emp_data[eid]["total_minus"] += s.get("nominal", 0)
            emp_data[eid]["minus_count"] += 1
        else:
            emp_data[eid]["total_plus"] += s.get("nominal", 0)
            emp_data[eid]["plus_count"] += 1
        
        if s.get("resolution") == "pending":
            emp_data[eid]["pending_count"] += 1
        else:
            emp_data[eid]["resolved_count"] += 1
    
    employees = sorted(emp_data.values(), key=lambda x: x["total_minus"], reverse=True)
    
    return {
        "period": f"{year}-{month:02d}",
        "total_minus": sum(e["total_minus"] for e in employees),
        "total_plus": sum(e["total_plus"] for e in employees),
        "employees": employees
    }

@router.get("/selisih/by-branch")
async def report_selisih_by_branch(month: int, year: int):
    """Selisih kas report grouped by branch"""
    _, last_day = calendar.monthrange(year, month)
    start_date = f"{year}-{month:02d}-01"
    end_date = f"{year}-{month:02d}-{last_day}"
    
    selisih = await selisih_col().find({
        "tanggal": {"$gte": start_date, "$lte": end_date}
    }, {"_id": 0}).to_list(length=1000)
    
    # Group by branch
    branch_data = {}
    for s in selisih:
        bid = s.get("branch_id")
        if bid not in branch_data:
            branch_data[bid] = {
                "branch_id": bid,
                "branch_name": s.get("branch_name", ""),
                "total_minus": 0,
                "total_plus": 0,
                "count": 0
            }
        if s.get("jenis") == "minus":
            branch_data[bid]["total_minus"] += s.get("nominal", 0)
        else:
            branch_data[bid]["total_plus"] += s.get("nominal", 0)
        branch_data[bid]["count"] += 1
    
    branches = sorted(branch_data.values(), key=lambda x: x["total_minus"], reverse=True)
    
    return {
        "period": f"{year}-{month:02d}",
        "total_minus": sum(b["total_minus"] for b in branches),
        "total_plus": sum(b["total_plus"] for b in branches),
        "branches": branches
    }

# ==================== ATTENDANCE REPORTS ====================

@router.get("/attendance/monthly")
async def report_attendance_monthly(month: int, year: int):
    """Monthly attendance report"""
    _, last_day = calendar.monthrange(year, month)
    start_date = f"{year}-{month:02d}-01"
    end_date = f"{year}-{month:02d}-{last_day}"
    
    attendance = await attendance_col().find({
        "tanggal": {"$gte": start_date, "$lte": end_date}
    }, {"_id": 0}).to_list(length=5000)
    
    # Group by employee
    emp_data = {}
    for a in attendance:
        eid = a.get("employee_id")
        if eid not in emp_data:
            emp_data[eid] = {
                "employee_id": eid,
                "employee_name": a.get("employee_name", ""),
                "employee_nik": a.get("employee_nik", ""),
                "branch_name": a.get("branch_name", ""),
                "hadir": 0,
                "telat": 0,
                "alpha": 0,
                "izin": 0,
                "cuti": 0,
                "sakit": 0,
                "total_telat_menit": 0,
                "total_lembur_menit": 0,
                "total_jam_kerja": 0
            }
        
        status = a.get("status", "")
        if status == "hadir":
            emp_data[eid]["hadir"] += 1
        elif status == "telat":
            emp_data[eid]["hadir"] += 1
            emp_data[eid]["telat"] += 1
        elif status == "izin":
            emp_data[eid]["izin"] += 1
        elif status == "cuti":
            emp_data[eid]["cuti"] += 1
        elif status == "sakit":
            emp_data[eid]["sakit"] += 1
        
        emp_data[eid]["total_telat_menit"] += a.get("telat_menit", 0)
        emp_data[eid]["total_lembur_menit"] += a.get("lembur_menit", 0)
        emp_data[eid]["total_jam_kerja"] += a.get("total_jam_kerja", 0)
    
    # Calculate working days
    hari_kerja = 0
    for day in range(1, last_day + 1):
        date = datetime(year, month, day)
        if date.weekday() < 5:
            hari_kerja += 1
    
    # Calculate alpha
    for eid in emp_data:
        total_records = emp_data[eid]["hadir"] + emp_data[eid]["izin"] + emp_data[eid]["cuti"] + emp_data[eid]["sakit"]
        emp_data[eid]["alpha"] = max(0, hari_kerja - total_records)
    
    employees = sorted(emp_data.values(), key=lambda x: x["hadir"], reverse=True)
    
    return {
        "period": f"{year}-{month:02d}",
        "hari_kerja": hari_kerja,
        "total_employees": len(employees),
        "summary": {
            "total_hadir": sum(e["hadir"] for e in employees),
            "total_telat": sum(e["telat"] for e in employees),
            "total_alpha": sum(e["alpha"] for e in employees),
            "total_izin": sum(e["izin"] for e in employees),
            "total_cuti": sum(e["cuti"] for e in employees),
            "total_sakit": sum(e["sakit"] for e in employees)
        },
        "employees": employees
    }

@router.get("/attendance/by-branch")
async def report_attendance_by_branch(month: int, year: int):
    """Attendance report grouped by branch"""
    _, last_day = calendar.monthrange(year, month)
    start_date = f"{year}-{month:02d}-01"
    end_date = f"{year}-{month:02d}-{last_day}"
    
    attendance = await attendance_col().find({
        "tanggal": {"$gte": start_date, "$lte": end_date}
    }, {"_id": 0}).to_list(length=5000)
    
    # Group by branch
    branch_data = {}
    for a in attendance:
        bid = a.get("branch_id")
        if bid not in branch_data:
            branch_data[bid] = {
                "branch_id": bid,
                "branch_name": a.get("branch_name", ""),
                "hadir": 0,
                "telat": 0,
                "total_telat_menit": 0
            }
        
        status = a.get("status", "")
        if status in ["hadir", "telat"]:
            branch_data[bid]["hadir"] += 1
        if status == "telat":
            branch_data[bid]["telat"] += 1
        branch_data[bid]["total_telat_menit"] += a.get("telat_menit", 0)
    
    branches = sorted(branch_data.values(), key=lambda x: x["hadir"], reverse=True)
    
    return {
        "period": f"{year}-{month:02d}",
        "branches": branches
    }

# ==================== PAYROLL REPORTS ====================

@router.get("/payroll/summary")
async def report_payroll_summary(year: int):
    """Annual payroll summary"""
    payroll = await payroll_col().find({}, {"_id": 0}).to_list(length=15000)
    
    # Filter by year
    payroll_year = [p for p in payroll if p.get("period_name", "").endswith(str(year))]
    
    # Group by month
    monthly = {}
    month_names = ["", "Januari", "Februari", "Maret", "April", "Mei", "Juni",
                   "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    
    for p in payroll_year:
        period = p.get("period_name", "")
        if period not in monthly:
            monthly[period] = {
                "period": period,
                "total_gross": 0,
                "total_deductions": 0,
                "total_net": 0,
                "employee_count": 0
            }
        monthly[period]["total_gross"] += p.get("total_earnings", 0)
        monthly[period]["total_deductions"] += p.get("total_deductions", 0)
        monthly[period]["total_net"] += p.get("take_home_pay", 0)
        monthly[period]["employee_count"] += 1
    
    return {
        "year": year,
        "total_gross": sum(m["total_gross"] for m in monthly.values()),
        "total_deductions": sum(m["total_deductions"] for m in monthly.values()),
        "total_net": sum(m["total_net"] for m in monthly.values()),
        "monthly": list(monthly.values())
    }

# ==================== EXECUTIVE SUMMARY ====================

@router.get("/executive/daily")
async def executive_summary_daily(tanggal: Optional[str] = None):
    """Executive summary for daily operations"""
    if not tanggal:
        tanggal = get_wib_now().strftime("%Y-%m-%d")
    
    # Setoran
    setoran = await setoran_col().find({"tanggal": tanggal}, {"_id": 0}).to_list(length=100)
    branches = await branches_col().find({}, {"_id": 0}).to_list(length=100)
    
    # Attendance
    attendance = await attendance_col().find({"tanggal": tanggal}, {"_id": 0}).to_list(length=500)
    employees = await employees_col().find({"status": "active"}, {"_id": 0}).to_list(length=500)
    
    return {
        "tanggal": tanggal,
        "operasional": {
            "total_cabang": len(branches),
            "sudah_setor": len(setoran),
            "belum_setor": len(branches) - len(setoran),
            "total_penjualan": sum(s.get("total_penjualan", 0) for s in setoran),
            "total_setoran": sum(s.get("total_setoran", 0) for s in setoran),
            "total_minus": sum(abs(s.get("selisih", 0)) for s in setoran if s.get("selisih", 0) < 0),
            "total_plus": sum(s.get("selisih", 0) for s in setoran if s.get("selisih", 0) > 0)
        },
        "kehadiran": {
            "total_karyawan": len(employees),
            "hadir": len([a for a in attendance if a.get("status") in ["hadir", "telat"]]),
            "telat": len([a for a in attendance if a.get("status") == "telat"]),
            "izin": len([a for a in attendance if a.get("status") in ["izin", "cuti", "sakit"]])
        }
    }

@router.get("/executive/monthly")
async def executive_summary_monthly(month: int, year: int):
    """Executive summary for monthly operations"""
    _, last_day = calendar.monthrange(year, month)
    start_date = f"{year}-{month:02d}-01"
    end_date = f"{year}-{month:02d}-{last_day}"
    
    # Setoran
    setoran = await setoran_col().find({
        "tanggal": {"$gte": start_date, "$lte": end_date}
    }, {"_id": 0}).to_list(length=1500)
    
    # Selisih
    selisih = await selisih_col().find({
        "tanggal": {"$gte": start_date, "$lte": end_date}
    }, {"_id": 0}).to_list(length=1000)
    
    # Attendance
    attendance = await attendance_col().find({
        "tanggal": {"$gte": start_date, "$lte": end_date}
    }, {"_id": 0}).to_list(length=5000)
    
    # Payroll
    payroll = await payroll_col().find({}, {"_id": 0}).to_list(length=1000)
    month_names = ["", "Januari", "Februari", "Maret", "April", "Mei", "Juni",
                   "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    period_name = f"{month_names[month]} {year}"
    payroll_month = [p for p in payroll if p.get("period_name") == period_name]
    
    return {
        "period": f"{year}-{month:02d}",
        "penjualan": {
            "total": sum(s.get("total_penjualan", 0) for s in setoran),
            "rata_rata_harian": sum(s.get("total_penjualan", 0) for s in setoran) / last_day if setoran else 0,
            "total_transaksi": sum(s.get("total_transaksi", 0) for s in setoran)
        },
        "selisih_kas": {
            "total_minus": sum(s.get("nominal", 0) for s in selisih if s.get("jenis") == "minus"),
            "total_plus": sum(s.get("nominal", 0) for s in selisih if s.get("jenis") == "plus"),
            "pending_count": len([s for s in selisih if s.get("resolution") == "pending"])
        },
        "kehadiran": {
            "total_hadir": len([a for a in attendance if a.get("status") in ["hadir", "telat"]]),
            "total_telat": len([a for a in attendance if a.get("status") == "telat"]),
            "total_menit_telat": sum(a.get("telat_menit", 0) for a in attendance)
        },
        "payroll": {
            "total_gross": sum(p.get("total_earnings", 0) for p in payroll_month),
            "total_deductions": sum(p.get("total_deductions", 0) for p in payroll_month),
            "total_net": sum(p.get("take_home_pay", 0) for p in payroll_month),
            "employee_count": len(payroll_month)
        }
    }
