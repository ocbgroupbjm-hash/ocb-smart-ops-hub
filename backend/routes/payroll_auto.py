# OCB TITAN AI - Automatic Payroll Calculation System
# Menghitung gaji otomatis berdasarkan absensi, bonus, dan potongan

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import uuid

router = APIRouter(prefix="/api/payroll-auto", tags=["Automatic Payroll"])

def get_db():
    from database import get_db as db_get
    return db_get()

def gen_id():
    return str(uuid.uuid4())

def now_iso():
    return datetime.now(timezone.utc).isoformat()

# Collections
def employees_col():
    return get_db()['employees']

def attendance_col():
    return get_db()['attendance']

def payroll_rules_col():
    return get_db()['payroll_rules']

def transactions_col():
    return get_db()['transactions']

def branches_col():
    return get_db()['branches']

def payroll_results_col():
    return get_db()['payroll_results']

def kpi_col():
    return get_db()['kpi_targets']


# ==================== CALCULATE PAYROLL FROM ATTENDANCE ====================

@router.get("/calculate/{employee_id}")
async def calculate_employee_payroll(
    employee_id: str,
    month: int,
    year: int,
    working_days: int = 26
):
    """
    Hitung payroll otomatis untuk satu karyawan berdasarkan:
    - Data absensi (hadir, telat, alpha, lembur)
    - Aturan payroll per jabatan
    - Bonus penjualan
    """
    
    # Get employee data
    emp = await employees_col().find_one({"id": employee_id}, {"_id": 0})
    if not emp:
        raise HTTPException(status_code=404, detail="Karyawan tidak ditemukan")
    
    # Get payroll rules for this jabatan
    jabatan_id = emp.get("jabatan_id", "")
    rules = await payroll_rules_col().find_one({"jabatan_id": jabatan_id}, {"_id": 0})
    if not rules:
        # Use employee's own salary data as fallback
        rules = {
            "gaji_pokok": emp.get("gaji_pokok", 0),
            "tunjangan_jabatan": emp.get("tunjangan_jabatan", 0),
            "tunjangan_transport": emp.get("tunjangan_transport", 0),
            "tunjangan_makan": emp.get("tunjangan_makan", 0),
            "bonus_kehadiran_full": emp.get("bonus_kehadiran", 0),
            "potongan_telat_per_menit": 1000,
            "potongan_alpha_per_hari": 50000
        }
    
    # Get attendance data for the month
    start_date = f"{year}-{month:02d}-01"
    if month == 12:
        end_date = f"{year + 1}-01-01"
    else:
        end_date = f"{year}-{month + 1:02d}-01"
    
    attendance_records = await attendance_col().find({
        "employee_id": employee_id,
        "tanggal": {"$gte": start_date, "$lt": end_date}
    }, {"_id": 0}).to_list(length=50)
    
    # Calculate attendance metrics
    total_hadir = 0
    total_alpha = 0
    total_izin = 0
    total_sakit = 0
    total_telat_menit = 0
    total_lembur_menit = 0
    
    for att in attendance_records:
        status = att.get("status", "").lower()
        if status == "hadir":
            total_hadir += 1
            total_telat_menit += att.get("telat_menit", 0)
            total_lembur_menit += att.get("lembur_menit", 0)
        elif status == "alpha":
            total_alpha += 1
        elif status == "izin":
            total_izin += 1
        elif status == "sakit":
            total_sakit += 1
        elif status == "cuti":
            total_izin += 1  # Count as izin
    
    # === SALARY CALCULATION ===
    salary_type = emp.get("salary_type", "monthly")
    
    if salary_type == "daily":
        # Gaji harian = upah harian x jumlah hadir
        upah_harian = emp.get("upah_harian", 0) or rules.get("gaji_pokok", 0) / working_days
        gaji_dasar = upah_harian * total_hadir
    else:
        # Gaji bulanan tetap
        gaji_dasar = rules.get("gaji_pokok", 0) or emp.get("gaji_pokok", 0)
    
    # === TUNJANGAN ===
    tunjangan_jabatan = rules.get("tunjangan_jabatan", 0) or emp.get("tunjangan_jabatan", 0)
    tunjangan_transport = rules.get("tunjangan_transport", 0) or emp.get("tunjangan_transport", 0)
    tunjangan_makan = rules.get("tunjangan_makan", 0) or emp.get("tunjangan_makan", 0)
    tunjangan_keluarga = emp.get("tunjangan_keluarga", 0)
    tunjangan_lainnya = emp.get("tunjangan_lainnya", 0)
    total_tunjangan = tunjangan_jabatan + tunjangan_transport + tunjangan_makan + tunjangan_keluarga + tunjangan_lainnya
    
    # === BONUS ===
    # Bonus kehadiran full (jika tidak ada alpha dan tidak telat > 30 menit)
    bonus_kehadiran = 0
    if total_alpha == 0 and total_telat_menit < 30:
        bonus_kehadiran = rules.get("bonus_kehadiran_full", 0) or emp.get("bonus_kehadiran", 0)
    
    # Bonus lembur (1.5x per jam)
    lembur_jam = total_lembur_menit / 60
    tarif_lembur_per_jam = (gaji_dasar / working_days / 8) * 1.5 if gaji_dasar > 0 else 15000
    bonus_lembur = lembur_jam * tarif_lembur_per_jam
    
    # Get sales bonus
    sales_bonus = await calculate_sales_bonus(employee_id, month, year)
    
    bonus_performance = emp.get("bonus_performance", 0)
    bonus_target = emp.get("bonus_target", 0)
    bonus_lainnya = emp.get("bonus_lainnya", 0)
    
    total_bonus = bonus_kehadiran + bonus_lembur + sales_bonus + bonus_performance + bonus_target + bonus_lainnya
    
    # === POTONGAN ===
    # Potongan telat
    potongan_telat = total_telat_menit * rules.get("potongan_telat_per_menit", 1000)
    
    # Potongan alpha
    potongan_alpha = total_alpha * rules.get("potongan_alpha_per_hari", 50000)
    
    # Potongan BPJS
    potongan_bpjs_kes = emp.get("potongan_bpjs_kes", 0)
    potongan_bpjs_tk = emp.get("potongan_bpjs_tk", 0)
    
    # Potongan lainnya
    potongan_pinjaman = emp.get("potongan_pinjaman", 0)
    potongan_lainnya = emp.get("potongan_lainnya", 0)
    
    total_potongan = potongan_telat + potongan_alpha + potongan_bpjs_kes + potongan_bpjs_tk + potongan_pinjaman + potongan_lainnya
    
    # === TAKE HOME PAY ===
    gross = gaji_dasar + total_tunjangan + total_bonus
    take_home_pay = gross - total_potongan
    
    return {
        "employee": {
            "id": emp.get("id"),
            "nik": emp.get("nik"),
            "name": emp.get("name"),
            "jabatan": emp.get("jabatan_name"),
            "branch": emp.get("branch_name"),
            "salary_type": salary_type,
            "bank_name": emp.get("bank_name"),
            "bank_account": emp.get("bank_account"),
            "payment_method": emp.get("payment_method", "transfer")
        },
        "period": {
            "month": month,
            "year": year,
            "working_days": working_days
        },
        "attendance": {
            "total_hadir": total_hadir,
            "total_alpha": total_alpha,
            "total_izin": total_izin,
            "total_sakit": total_sakit,
            "total_telat_menit": total_telat_menit,
            "total_lembur_menit": total_lembur_menit,
            "lembur_jam": round(lembur_jam, 2)
        },
        "calculation": {
            "gaji_dasar": round(gaji_dasar),
            "tunjangan": {
                "jabatan": round(tunjangan_jabatan),
                "transport": round(tunjangan_transport),
                "makan": round(tunjangan_makan),
                "keluarga": round(tunjangan_keluarga),
                "lainnya": round(tunjangan_lainnya),
                "total": round(total_tunjangan)
            },
            "bonus": {
                "kehadiran": round(bonus_kehadiran),
                "lembur": round(bonus_lembur),
                "penjualan": round(sales_bonus),
                "performance": round(bonus_performance),
                "target": round(bonus_target),
                "lainnya": round(bonus_lainnya),
                "total": round(total_bonus)
            },
            "potongan": {
                "telat": round(potongan_telat),
                "alpha": round(potongan_alpha),
                "bpjs_kes": round(potongan_bpjs_kes),
                "bpjs_tk": round(potongan_bpjs_tk),
                "pinjaman": round(potongan_pinjaman),
                "lainnya": round(potongan_lainnya),
                "total": round(total_potongan)
            },
            "gross": round(gross),
            "take_home_pay": round(take_home_pay)
        },
        "generated_at": now_iso()
    }


async def calculate_sales_bonus(employee_id: str, month: int, year: int) -> float:
    """Calculate sales bonus from transactions"""
    start_date = f"{year}-{month:02d}-01"
    if month == 12:
        end_date = f"{year + 1}-01-01"
    else:
        end_date = f"{year}-{month + 1:02d}-01"
    
    # Get employee's sales
    sales = await transactions_col().find({
        "$or": [
            {"cashier_id": employee_id},
            {"sales_id": employee_id},
            {"created_by": employee_id}
        ],
        "created_at": {"$gte": f"{start_date}T00:00:00", "$lt": f"{end_date}T00:00:00"},
        "status": "completed"
    }, {"_id": 0}).to_list(length=5000)
    
    total_sales = sum(s.get("total", 0) for s in sales)
    
    # Calculate commission (1% of sales, max 2 million)
    commission_rate = 0.01
    commission = min(total_sales * commission_rate, 2000000)
    
    # Bonus target (if sales > 50 million, get 500k bonus)
    target_bonus = 500000 if total_sales >= 50000000 else 0
    
    return commission + target_bonus


# ==================== BULK PAYROLL CALCULATION ====================

@router.get("/calculate-branch/{branch_id}")
async def calculate_branch_payroll(branch_id: str, month: int, year: int):
    """Calculate payroll for all employees in a branch"""
    employees = await employees_col().find({
        "branch_id": branch_id,
        "status": "active"
    }, {"_id": 0}).to_list(length=500)
    
    results = []
    total_gross = 0
    total_thp = 0
    
    for emp in employees:
        try:
            payroll = await calculate_employee_payroll(emp["id"], month, year)
            results.append(payroll)
            total_gross += payroll["calculation"]["gross"]
            total_thp += payroll["calculation"]["take_home_pay"]
        except Exception as e:
            results.append({
                "employee": {"id": emp.get("id"), "name": emp.get("name")},
                "error": str(e)
            })
    
    branch = await branches_col().find_one({"id": branch_id}, {"_id": 0})
    
    return {
        "branch_id": branch_id,
        "branch_name": branch.get("name") if branch else "Unknown",
        "period": f"{month:02d}/{year}",
        "total_employees": len(results),
        "summary": {
            "total_gross": round(total_gross),
            "total_take_home_pay": round(total_thp)
        },
        "employees": results,
        "generated_at": now_iso()
    }


@router.get("/calculate-all")
async def calculate_all_payroll(month: int, year: int):
    """Calculate payroll for all active employees"""
    employees = await employees_col().find({"status": "active"}, {"_id": 0}).to_list(length=2000)
    
    results = []
    total_gross = 0
    total_thp = 0
    by_branch = {}
    
    for emp in employees:
        try:
            payroll = await calculate_employee_payroll(emp["id"], month, year)
            results.append(payroll)
            total_gross += payroll["calculation"]["gross"]
            total_thp += payroll["calculation"]["take_home_pay"]
            
            # Group by branch
            branch = emp.get("branch_name", "Unknown")
            if branch not in by_branch:
                by_branch[branch] = {"count": 0, "gross": 0, "thp": 0}
            by_branch[branch]["count"] += 1
            by_branch[branch]["gross"] += payroll["calculation"]["gross"]
            by_branch[branch]["thp"] += payroll["calculation"]["take_home_pay"]
        except Exception as e:
            results.append({
                "employee": {"id": emp.get("id"), "name": emp.get("name")},
                "error": str(e)
            })
    
    branch_summary = [{"branch": k, **v} for k, v in by_branch.items()]
    branch_summary.sort(key=lambda x: x["thp"], reverse=True)
    
    return {
        "period": f"{month:02d}/{year}",
        "total_employees": len(results),
        "summary": {
            "total_gross": round(total_gross),
            "total_take_home_pay": round(total_thp)
        },
        "by_branch": branch_summary,
        "employees": results,
        "generated_at": now_iso()
    }


# ==================== SAVE PAYROLL RESULT ====================

@router.post("/save/{employee_id}")
async def save_payroll_result(employee_id: str, month: int, year: int):
    """Save calculated payroll to database"""
    payroll = await calculate_employee_payroll(employee_id, month, year)
    
    record = {
        "id": gen_id(),
        "employee_id": employee_id,
        "employee_nik": payroll["employee"]["nik"],
        "employee_name": payroll["employee"]["name"],
        "period_month": month,
        "period_year": year,
        "period": f"{month:02d}/{year}",
        "salary_type": payroll["employee"]["salary_type"],
        "attendance": payroll["attendance"],
        "calculation": payroll["calculation"],
        "status": "draft",  # draft, approved, paid
        "created_at": now_iso(),
        "updated_at": now_iso()
    }
    
    # Upsert - update if exists
    await payroll_results_col().update_one(
        {"employee_id": employee_id, "period_month": month, "period_year": year},
        {"$set": record},
        upsert=True
    )
    
    return {"message": "Payroll berhasil disimpan", "payroll_id": record["id"]}


@router.post("/save-branch/{branch_id}")
async def save_branch_payroll(branch_id: str, month: int, year: int):
    """Save payroll for all employees in a branch"""
    branch_payroll = await calculate_branch_payroll(branch_id, month, year)
    
    saved = 0
    for emp_payroll in branch_payroll["employees"]:
        if "error" not in emp_payroll:
            record = {
                "id": gen_id(),
                "employee_id": emp_payroll["employee"]["id"],
                "employee_nik": emp_payroll["employee"]["nik"],
                "employee_name": emp_payroll["employee"]["name"],
                "branch_id": branch_id,
                "branch_name": branch_payroll["branch_name"],
                "period_month": month,
                "period_year": year,
                "period": f"{month:02d}/{year}",
                "salary_type": emp_payroll["employee"]["salary_type"],
                "attendance": emp_payroll["attendance"],
                "calculation": emp_payroll["calculation"],
                "status": "draft",
                "created_at": now_iso(),
                "updated_at": now_iso()
            }
            
            await payroll_results_col().update_one(
                {"employee_id": emp_payroll["employee"]["id"], "period_month": month, "period_year": year},
                {"$set": record},
                upsert=True
            )
            saved += 1
    
    return {
        "message": f"Payroll {saved} karyawan berhasil disimpan",
        "branch": branch_payroll["branch_name"],
        "period": f"{month:02d}/{year}"
    }


# ==================== GET SAVED PAYROLL ====================

@router.get("/results")
async def get_payroll_results(
    month: Optional[int] = None,
    year: Optional[int] = None,
    branch_id: Optional[str] = None,
    status: Optional[str] = None
):
    """Get saved payroll results"""
    query = {}
    if month:
        query["period_month"] = month
    if year:
        query["period_year"] = year
    if branch_id:
        query["branch_id"] = branch_id
    if status:
        query["status"] = status
    
    results = await payroll_results_col().find(query, {"_id": 0}).sort("created_at", -1).to_list(length=500)
    
    return {"results": results, "total": len(results)}


@router.put("/results/{payroll_id}/status")
async def update_payroll_status(payroll_id: str, status: str):
    """Update payroll status (draft -> approved -> paid)"""
    await payroll_results_col().update_one(
        {"id": payroll_id},
        {"$set": {"status": status, "updated_at": now_iso()}}
    )
    return {"message": f"Status payroll diubah menjadi {status}"}
