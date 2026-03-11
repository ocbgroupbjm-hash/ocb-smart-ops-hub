# OCB GROUP SUPER ERP - Operations Routes
# Setoran Harian, Selisih Kas, Master Data

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel
import uuid

from database import get_db
from models.erp_models import (
    Employee, SetoranHarian, SelisihKas, 
    MasterShift, MasterJabatan, MasterLokasiAbsensi,
    MasterTargetCabang, MasterTargetKaryawan, MasterBiayaOperasional,
    MasterPayrollRule, SelisihStatus, SelisihResolution, ApprovalStatus,
    SystemAlert, AlertType, AlertSeverity
)

router = APIRouter(prefix="/api/erp", tags=["ERP Operations"])

def gen_id():
    return str(uuid.uuid4())

def now_iso():
    return datetime.now(timezone.utc).isoformat()

# ==================== COLLECTIONS ====================

def employees_col():
    return get_db()['employees']

def setoran_col():
    return get_db()['setoran_harian']

def selisih_col():
    return get_db()['selisih_kas']

def shifts_col():
    return get_db()['master_shifts']

def jabatan_col():
    return get_db()['master_jabatan']

def lokasi_absensi_col():
    return get_db()['master_lokasi_absensi']

def target_cabang_col():
    return get_db()['master_target_cabang']

def target_karyawan_col():
    return get_db()['master_target_karyawan']

def biaya_operasional_col():
    return get_db()['master_biaya_operasional']

def payroll_rule_col():
    return get_db()['master_payroll_rules']

def alerts_col():
    return get_db()['system_alerts']

# ==================== EMPLOYEE CRUD ====================

class EmployeeCreate(BaseModel):
    nik: str
    name: str
    email: str = ""
    phone: str = ""
    whatsapp: str = ""
    jabatan_id: str = ""
    jabatan_name: str = ""
    department: str = ""
    branch_id: str = ""
    branch_name: str = ""
    ktp_number: str = ""
    birth_date: str = ""
    birth_place: str = ""
    gender: str = ""
    religion: str = ""
    marital_status: str = ""
    address: str = ""
    join_date: str = ""
    contract_type: str = "tetap"
    contract_end_date: str = ""
    bank_name: str = ""
    bank_account: str = ""
    bank_holder: str = ""
    gaji_pokok: float = 0
    # Enhanced Payroll Fields
    salary_type: str = "monthly"  # monthly atau daily
    upah_harian: float = 0
    tunjangan_jabatan: float = 0
    tunjangan_transport: float = 0
    tunjangan_makan: float = 0
    tunjangan_keluarga: float = 0
    tunjangan_lainnya: float = 0
    tunjangan_total: float = 0
    # Bonus Fields
    bonus_kehadiran: float = 0
    bonus_performance: float = 0
    bonus_target: float = 0
    bonus_lainnya: float = 0
    # Deduction Fields
    potongan_bpjs_kes: float = 0
    potongan_bpjs_tk: float = 0
    potongan_pinjaman: float = 0
    potongan_lainnya: float = 0
    # Payment
    payment_method: str = "transfer"  # transfer, cash, ewallet
    photo_url: str = ""
    user_id: str = ""

class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    whatsapp: Optional[str] = None
    jabatan_id: Optional[str] = None
    jabatan_name: Optional[str] = None
    department: Optional[str] = None
    branch_id: Optional[str] = None
    branch_name: Optional[str] = None
    ktp_number: Optional[str] = None
    birth_date: Optional[str] = None
    birth_place: Optional[str] = None
    gender: Optional[str] = None
    religion: Optional[str] = None
    marital_status: Optional[str] = None
    address: Optional[str] = None
    join_date: Optional[str] = None
    contract_type: Optional[str] = None
    contract_end_date: Optional[str] = None
    status: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    bank_holder: Optional[str] = None
    gaji_pokok: Optional[float] = None
    # Enhanced Payroll Fields
    salary_type: Optional[str] = None  # monthly atau daily
    upah_harian: Optional[float] = None
    tunjangan_jabatan: Optional[float] = None
    tunjangan_transport: Optional[float] = None
    tunjangan_makan: Optional[float] = None
    tunjangan_keluarga: Optional[float] = None
    tunjangan_lainnya: Optional[float] = None
    tunjangan_total: Optional[float] = None
    # Bonus Fields
    bonus_kehadiran: Optional[float] = None
    bonus_performance: Optional[float] = None
    bonus_target: Optional[float] = None
    bonus_lainnya: Optional[float] = None
    # Deduction Fields
    potongan_bpjs_kes: Optional[float] = None
    potongan_bpjs_tk: Optional[float] = None
    potongan_pinjaman: Optional[float] = None
    potongan_lainnya: Optional[float] = None
    # Payment
    payment_method: Optional[str] = None  # transfer, cash, ewallet
    photo_url: Optional[str] = None
    user_id: Optional[str] = None

@router.get("/employees")
async def list_employees(
    branch_id: Optional[str] = None,
    department: Optional[str] = None,
    status: str = "active",
    search: Optional[str] = None
):
    query = {}
    if branch_id:
        query["branch_id"] = branch_id
    if department:
        query["department"] = department
    if status:
        query["status"] = status
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"nik": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}}
        ]
    
    cursor = employees_col().find(query, {"_id": 0}).sort("name", 1)
    employees = await cursor.to_list(length=1000)
    return {"employees": employees, "total": len(employees)}

@router.get("/employees/{employee_id}")
async def get_employee(employee_id: str):
    emp = await employees_col().find_one({"id": employee_id}, {"_id": 0})
    if not emp:
        raise HTTPException(status_code=404, detail="Karyawan tidak ditemukan")
    return emp

@router.post("/employees")
async def create_employee(data: EmployeeCreate):
    # Check NIK unique
    existing = await employees_col().find_one({"nik": data.nik})
    if existing:
        raise HTTPException(status_code=400, detail="NIK sudah terdaftar")
    
    emp = Employee(
        id=gen_id(),
        **data.model_dump(),
        created_at=now_iso(),
        updated_at=now_iso()
    )
    await employees_col().insert_one(emp.model_dump())
    return {"message": "Karyawan berhasil ditambahkan", "employee": emp.model_dump()}

@router.put("/employees/{employee_id}")
async def update_employee(employee_id: str, data: EmployeeUpdate):
    emp = await employees_col().find_one({"id": employee_id})
    if not emp:
        raise HTTPException(status_code=404, detail="Karyawan tidak ditemukan")
    
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    update_data["updated_at"] = now_iso()
    
    await employees_col().update_one({"id": employee_id}, {"$set": update_data})
    updated = await employees_col().find_one({"id": employee_id}, {"_id": 0})
    return {"message": "Data karyawan berhasil diupdate", "employee": updated}

@router.delete("/employees/{employee_id}")
async def delete_employee(employee_id: str):
    result = await employees_col().delete_one({"id": employee_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Karyawan tidak ditemukan")
    return {"message": "Karyawan berhasil dihapus"}

# ==================== MASTER SHIFT ====================

class ShiftCreate(BaseModel):
    code: str
    name: str
    start_time: str
    end_time: str
    break_minutes: int = 60

class ShiftUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    break_minutes: Optional[int] = None

@router.get("/master/shifts")
async def list_shifts():
    cursor = shifts_col().find({"is_active": True}, {"_id": 0})
    shifts = await cursor.to_list(length=100)
    return {"shifts": shifts}

@router.post("/master/shifts")
async def create_shift(data: ShiftCreate):
    shift = MasterShift(id=gen_id(), **data.model_dump())
    await shifts_col().insert_one(shift.model_dump())
    return {"message": "Shift berhasil ditambahkan", "shift": shift.model_dump()}

@router.put("/master/shifts/{shift_id}")
async def update_shift(shift_id: str, data: ShiftUpdate):
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Tidak ada data untuk diupdate")
    await shifts_col().update_one({"id": shift_id}, {"$set": update_data})
    return {"message": "Shift berhasil diupdate"}

@router.delete("/master/shifts/{shift_id}")
async def delete_shift(shift_id: str):
    await shifts_col().update_one({"id": shift_id}, {"$set": {"is_active": False}})
    return {"message": "Shift berhasil dihapus"}

# ==================== MASTER JABATAN ====================

class JabatanCreate(BaseModel):
    code: str
    name: str
    level: int = 1
    department: str = ""

class JabatanUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    level: Optional[int] = None
    department: Optional[str] = None

@router.get("/master/jabatan")
async def list_jabatan():
    cursor = jabatan_col().find({"is_active": True}, {"_id": 0}).sort("level", 1)
    jabatan = await cursor.to_list(length=100)
    return {"jabatan": jabatan}

@router.post("/master/jabatan")
async def create_jabatan(data: JabatanCreate):
    jab = MasterJabatan(id=gen_id(), **data.model_dump())
    await jabatan_col().insert_one(jab.model_dump())
    return {"message": "Jabatan berhasil ditambahkan", "jabatan": jab.model_dump()}

@router.put("/master/jabatan/{jabatan_id}")
async def update_jabatan(jabatan_id: str, data: JabatanUpdate):
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Tidak ada data untuk diupdate")
    await jabatan_col().update_one({"id": jabatan_id}, {"$set": update_data})
    return {"message": "Jabatan berhasil diupdate"}

@router.delete("/master/jabatan/{jabatan_id}")
async def delete_jabatan(jabatan_id: str):
    await jabatan_col().update_one({"id": jabatan_id}, {"$set": {"is_active": False}})
    return {"message": "Jabatan berhasil dihapus"}

# ==================== MASTER LOKASI ABSENSI ====================

class LokasiAbsensiCreate(BaseModel):
    branch_id: str
    branch_name: str
    latitude: float
    longitude: float
    radius_meters: int = 100
    address: str = ""

class LokasiAbsensiUpdate(BaseModel):
    branch_id: Optional[str] = None
    branch_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius_meters: Optional[int] = None
    address: Optional[str] = None

@router.get("/master/lokasi-absensi")
async def list_lokasi_absensi():
    cursor = lokasi_absensi_col().find({"is_active": True}, {"_id": 0})
    lokasi = await cursor.to_list(length=100)
    return {"lokasi": lokasi}

@router.post("/master/lokasi-absensi")
async def create_lokasi_absensi(data: LokasiAbsensiCreate):
    lok = MasterLokasiAbsensi(id=gen_id(), **data.model_dump())
    await lokasi_absensi_col().insert_one(lok.model_dump())
    return {"message": "Lokasi absensi berhasil ditambahkan", "lokasi": lok.model_dump()}

@router.put("/master/lokasi-absensi/{lokasi_id}")
async def update_lokasi_absensi(lokasi_id: str, data: LokasiAbsensiUpdate):
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Tidak ada data untuk diupdate")
    await lokasi_absensi_col().update_one({"id": lokasi_id}, {"$set": update_data})
    return {"message": "Lokasi absensi berhasil diupdate"}

@router.delete("/master/lokasi-absensi/{lokasi_id}")
async def delete_lokasi_absensi(lokasi_id: str):
    await lokasi_absensi_col().update_one({"id": lokasi_id}, {"$set": {"is_active": False}})
    return {"message": "Lokasi absensi berhasil dihapus"}

# ==================== TARGET CABANG ====================

class TargetCabangCreate(BaseModel):
    branch_id: str
    branch_name: str
    period_month: int
    period_year: int
    target_revenue: float = 0
    target_transactions: int = 0
    target_profit: float = 0

@router.get("/master/target-cabang")
async def list_target_cabang(month: Optional[int] = None, year: Optional[int] = None):
    query = {}
    if month:
        query["period_month"] = month
    if year:
        query["period_year"] = year
    cursor = target_cabang_col().find(query, {"_id": 0})
    targets = await cursor.to_list(length=500)
    return {"targets": targets}

@router.post("/master/target-cabang")
async def create_target_cabang(data: TargetCabangCreate):
    # Upsert - update if exists
    existing = await target_cabang_col().find_one({
        "branch_id": data.branch_id,
        "period_month": data.period_month,
        "period_year": data.period_year
    })
    if existing:
        await target_cabang_col().update_one(
            {"id": existing["id"]},
            {"$set": data.model_dump()}
        )
        return {"message": "Target cabang berhasil diupdate"}
    
    target = MasterTargetCabang(id=gen_id(), **data.model_dump())
    await target_cabang_col().insert_one(target.model_dump())
    return {"message": "Target cabang berhasil ditambahkan", "target": target.model_dump()}

# ==================== TARGET KARYAWAN ====================

class TargetKaryawanCreate(BaseModel):
    employee_id: str
    employee_name: str
    period_month: int
    period_year: int
    target_revenue: float = 0
    target_transactions: int = 0
    bonus_percentage: float = 0

@router.get("/master/target-karyawan")
async def list_target_karyawan(month: Optional[int] = None, year: Optional[int] = None):
    query = {}
    if month:
        query["period_month"] = month
    if year:
        query["period_year"] = year
    cursor = target_karyawan_col().find(query, {"_id": 0})
    targets = await cursor.to_list(length=500)
    return {"targets": targets}

@router.post("/master/target-karyawan")
async def create_target_karyawan(data: TargetKaryawanCreate):
    existing = await target_karyawan_col().find_one({
        "employee_id": data.employee_id,
        "period_month": data.period_month,
        "period_year": data.period_year
    })
    if existing:
        await target_karyawan_col().update_one(
            {"id": existing["id"]},
            {"$set": data.model_dump()}
        )
        return {"message": "Target karyawan berhasil diupdate"}
    
    target = MasterTargetKaryawan(id=gen_id(), **data.model_dump())
    await target_karyawan_col().insert_one(target.model_dump())
    return {"message": "Target karyawan berhasil ditambahkan", "target": target.model_dump()}

# ==================== BIAYA OPERASIONAL ====================

class BiayaOperasionalCreate(BaseModel):
    code: str
    name: str
    category: str
    account_id: str = ""

@router.get("/master/biaya-operasional")
async def list_biaya_operasional():
    cursor = biaya_operasional_col().find({"is_active": True}, {"_id": 0})
    biaya = await cursor.to_list(length=100)
    return {"biaya": biaya}

@router.post("/master/biaya-operasional")
async def create_biaya_operasional(data: BiayaOperasionalCreate):
    biaya = MasterBiayaOperasional(id=gen_id(), **data.model_dump())
    await biaya_operasional_col().insert_one(biaya.model_dump())
    return {"message": "Biaya operasional berhasil ditambahkan", "biaya": biaya.model_dump()}

# ==================== PAYROLL RULES ====================

class PayrollRuleCreate(BaseModel):
    jabatan_id: str
    jabatan_name: str
    gaji_pokok: float = 0
    tunjangan_jabatan: float = 0
    tunjangan_transport: float = 0
    tunjangan_makan: float = 0
    bonus_kehadiran_full: float = 0
    potongan_telat_per_menit: float = 0
    potongan_alpha_per_hari: float = 0

@router.get("/master/payroll-rules")
async def list_payroll_rules():
    cursor = payroll_rule_col().find({"is_active": True}, {"_id": 0})
    rules = await cursor.to_list(length=100)
    return {"rules": rules}

@router.post("/master/payroll-rules")
async def create_payroll_rule(data: PayrollRuleCreate):
    # Upsert by jabatan
    existing = await payroll_rule_col().find_one({"jabatan_id": data.jabatan_id})
    if existing:
        await payroll_rule_col().update_one(
            {"id": existing["id"]},
            {"$set": data.model_dump()}
        )
        return {"message": "Aturan payroll berhasil diupdate"}
    
    rule = MasterPayrollRule(id=gen_id(), **data.model_dump())
    await payroll_rule_col().insert_one(rule.model_dump())
    return {"message": "Aturan payroll berhasil ditambahkan", "rule": rule.model_dump()}

@router.put("/master/payroll-rules/{rule_id}")
async def update_payroll_rule(rule_id: str, data: PayrollRuleCreate):
    """Update existing payroll rule"""
    existing = await payroll_rule_col().find_one({"id": rule_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Aturan payroll tidak ditemukan")
    
    update_data = data.model_dump()
    update_data["updated_at"] = now_iso()
    
    await payroll_rule_col().update_one(
        {"id": rule_id},
        {"$set": update_data}
    )
    return {"message": "Aturan payroll berhasil diupdate"}

@router.delete("/master/payroll-rules/{rule_id}")
async def delete_payroll_rule(rule_id: str):
    """Delete payroll rule (soft delete)"""
    existing = await payroll_rule_col().find_one({"id": rule_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Aturan payroll tidak ditemukan")
    
    await payroll_rule_col().update_one(
        {"id": rule_id},
        {"$set": {"is_active": False, "updated_at": now_iso()}}
    )
    return {"message": "Aturan payroll berhasil dihapus"}

# ==================== SETORAN HARIAN ====================

class SetoranCreate(BaseModel):
    tanggal: str
    jam_buka: str = ""
    jam_tutup: str = ""
    branch_id: str
    branch_code: str
    branch_name: str
    penjaga_id: str
    penjaga_name: str
    shift: str = ""
    total_penjualan: float = 0
    total_transaksi: int = 0
    penjualan_cash: float = 0
    penjualan_transfer: float = 0
    penjualan_ewallet: float = 0
    penjualan_debit: float = 0
    penjualan_credit: float = 0
    penjualan_piutang: float = 0
    total_setoran: float = 0
    metode_setoran: str = ""
    rekening_tujuan: str = ""
    bukti_setoran_url: str = ""
    catatan_penjaga: str = ""
    input_by_id: str = ""
    input_by_name: str = ""

@router.get("/setoran")
async def list_setoran(
    tanggal: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    branch_id: Optional[str] = None,
    status: Optional[str] = None,
    penjaga_id: Optional[str] = None
):
    query = {}
    
    if tanggal:
        query["tanggal"] = tanggal
    elif start_date and end_date:
        query["tanggal"] = {"$gte": start_date, "$lte": end_date}
    
    if branch_id:
        query["branch_id"] = branch_id
    if status:
        query["status"] = status
    if penjaga_id:
        query["penjaga_id"] = penjaga_id
    
    cursor = setoran_col().find(query, {"_id": 0}).sort("tanggal", -1)
    setoran = await cursor.to_list(length=1000)
    
    # Calculate summary
    total_penjualan = sum(s.get("total_penjualan", 0) for s in setoran)
    total_setoran = sum(s.get("total_setoran", 0) for s in setoran)
    total_selisih = sum(s.get("selisih", 0) for s in setoran)
    total_minus = sum(s.get("selisih", 0) for s in setoran if s.get("selisih", 0) < 0)
    total_plus = sum(s.get("selisih", 0) for s in setoran if s.get("selisih", 0) > 0)
    
    return {
        "setoran": setoran,
        "total": len(setoran),
        "summary": {
            "total_penjualan": total_penjualan,
            "total_setoran": total_setoran,
            "total_selisih": total_selisih,
            "total_minus": total_minus,
            "total_plus": total_plus
        }
    }

@router.get("/setoran/{setoran_id}")
async def get_setoran(setoran_id: str):
    setoran = await setoran_col().find_one({"id": setoran_id}, {"_id": 0})
    if not setoran:
        raise HTTPException(status_code=404, detail="Setoran tidak ditemukan")
    return setoran

@router.post("/setoran")
async def create_setoran(data: SetoranCreate):
    # Check duplicate
    existing = await setoran_col().find_one({
        "tanggal": data.tanggal,
        "branch_id": data.branch_id,
        "shift": data.shift
    })
    if existing:
        raise HTTPException(status_code=400, detail="Setoran untuk tanggal, cabang, dan shift ini sudah ada")
    
    # Calculate selisih
    # Setoran harusnya = penjualan cash (yang harus disetor)
    # Jika penjualan pakai transfer/ewallet/debit/credit, itu tidak perlu disetor cash
    expected_setoran = data.penjualan_cash
    selisih = data.total_setoran - expected_setoran
    
    selisih_status = SelisihStatus.BALANCE
    if selisih > 0:
        selisih_status = SelisihStatus.PLUS
    elif selisih < 0:
        selisih_status = SelisihStatus.MINUS
    
    setoran = SetoranHarian(
        id=gen_id(),
        **data.model_dump(),
        selisih=selisih,
        selisih_status=selisih_status,
        selisih_resolution=SelisihResolution.PENDING if selisih != 0 else SelisihResolution.CLOSED,
        status=ApprovalStatus.PENDING,
        input_at=now_iso(),
        created_at=now_iso(),
        updated_at=now_iso()
    )
    
    await setoran_col().insert_one(setoran.model_dump())
    
    # If ada selisih, create selisih record
    if selisih != 0:
        selisih_record = SelisihKas(
            id=gen_id(),
            setoran_id=setoran.id,
            tanggal=data.tanggal,
            branch_id=data.branch_id,
            branch_code=data.branch_code,
            branch_name=data.branch_name,
            penjaga_id=data.penjaga_id,
            penjaga_name=data.penjaga_name,
            shift=data.shift,
            nominal=abs(selisih),
            jenis=selisih_status,
            resolution=SelisihResolution.PENDING,
            created_at=now_iso(),
            updated_at=now_iso()
        )
        await selisih_col().insert_one(selisih_record.model_dump())
        
        # Create alert if minus
        if selisih < 0:
            alert = SystemAlert(
                id=gen_id(),
                alert_type=AlertType.MINUS_KAS,
                severity=AlertSeverity.WARNING if abs(selisih) < 100000 else AlertSeverity.CRITICAL,
                title=f"Minus Kas: {data.branch_name}",
                message=f"Selisih minus Rp {abs(selisih):,.0f} pada {data.tanggal} shift {data.shift}. Penjaga: {data.penjaga_name}",
                branch_id=data.branch_id,
                branch_name=data.branch_name,
                employee_id=data.penjaga_id,
                employee_name=data.penjaga_name,
                reference_type="setoran",
                reference_id=setoran.id,
                data={"selisih": selisih, "tanggal": data.tanggal},
                created_at=now_iso()
            )
            await alerts_col().insert_one(alert.model_dump())
            
            # Update employee total_minus
            await employees_col().update_one(
                {"id": data.penjaga_id},
                {"$inc": {"total_minus": abs(selisih)}}
            )
        elif selisih > 0:
            # Update employee total_plus
            await employees_col().update_one(
                {"id": data.penjaga_id},
                {"$inc": {"total_plus": selisih}}
            )
    
    return {
        "message": "Setoran berhasil dicatat",
        "setoran": setoran.model_dump(),
        "selisih": selisih,
        "selisih_status": selisih_status.value
    }

@router.put("/setoran/{setoran_id}")
async def update_setoran(setoran_id: str, data: SetoranCreate):
    existing = await setoran_col().find_one({"id": setoran_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Setoran tidak ditemukan")
    
    if existing.get("status") == "approved":
        raise HTTPException(status_code=400, detail="Setoran yang sudah diapprove tidak bisa diedit")
    
    # Recalculate selisih
    expected_setoran = data.penjualan_cash
    selisih = data.total_setoran - expected_setoran
    
    selisih_status = SelisihStatus.BALANCE
    if selisih > 0:
        selisih_status = SelisihStatus.PLUS
    elif selisih < 0:
        selisih_status = SelisihStatus.MINUS
    
    update_data = data.model_dump()
    update_data["selisih"] = selisih
    update_data["selisih_status"] = selisih_status.value
    update_data["updated_at"] = now_iso()
    
    await setoran_col().update_one({"id": setoran_id}, {"$set": update_data})
    
    # Update selisih record if exists
    await selisih_col().update_one(
        {"setoran_id": setoran_id},
        {"$set": {
            "nominal": abs(selisih),
            "jenis": selisih_status.value,
            "updated_at": now_iso()
        }}
    )
    
    return {"message": "Setoran berhasil diupdate"}

@router.post("/setoran/{setoran_id}/verify")
async def verify_setoran(setoran_id: str, verified_by_id: str, verified_by_name: str, catatan: str = ""):
    existing = await setoran_col().find_one({"id": setoran_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Setoran tidak ditemukan")
    
    await setoran_col().update_one(
        {"id": setoran_id},
        {"$set": {
            "verified_by_id": verified_by_id,
            "verified_by_name": verified_by_name,
            "verified_at": now_iso(),
            "catatan_admin": catatan,
            "status": ApprovalStatus.PENDING.value,
            "updated_at": now_iso()
        }}
    )
    return {"message": "Setoran berhasil diverifikasi"}

@router.post("/setoran/{setoran_id}/approve")
async def approve_setoran(setoran_id: str, approved_by_id: str, approved_by_name: str, catatan: str = ""):
    existing = await setoran_col().find_one({"id": setoran_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Setoran tidak ditemukan")
    
    await setoran_col().update_one(
        {"id": setoran_id},
        {"$set": {
            "approved_by_id": approved_by_id,
            "approved_by_name": approved_by_name,
            "approved_at": now_iso(),
            "catatan_supervisor": catatan,
            "status": ApprovalStatus.APPROVED.value,
            "updated_at": now_iso()
        }}
    )
    
    # Create auto journal entry if accounting integration enabled
    # TODO: Integrate with accounting module
    
    return {"message": "Setoran berhasil diapprove"}

@router.post("/setoran/{setoran_id}/reject")
async def reject_setoran(setoran_id: str, rejected_by_id: str, rejected_by_name: str, alasan: str):
    existing = await setoran_col().find_one({"id": setoran_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Setoran tidak ditemukan")
    
    await setoran_col().update_one(
        {"id": setoran_id},
        {"$set": {
            "status": ApprovalStatus.REJECTED.value,
            "catatan_supervisor": f"DITOLAK oleh {rejected_by_name}: {alasan}",
            "updated_at": now_iso()
        }}
    )
    return {"message": "Setoran ditolak"}

# ==================== SELISIH KAS ====================

@router.get("/selisih-kas")
async def list_selisih_kas(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    branch_id: Optional[str] = None,
    penjaga_id: Optional[str] = None,
    jenis: Optional[str] = None,
    resolution: Optional[str] = None
):
    query = {}
    
    if start_date and end_date:
        query["tanggal"] = {"$gte": start_date, "$lte": end_date}
    if branch_id:
        query["branch_id"] = branch_id
    if penjaga_id:
        query["penjaga_id"] = penjaga_id
    if jenis:
        query["jenis"] = jenis
    if resolution:
        query["resolution"] = resolution
    
    cursor = selisih_col().find(query, {"_id": 0}).sort("tanggal", -1)
    selisih_list = await cursor.to_list(length=1000)
    
    # Summary
    total_minus = sum(s.get("nominal", 0) for s in selisih_list if s.get("jenis") == "minus")
    total_plus = sum(s.get("nominal", 0) for s in selisih_list if s.get("jenis") == "plus")
    pending_count = len([s for s in selisih_list if s.get("resolution") == "pending"])
    
    return {
        "selisih": selisih_list,
        "total": len(selisih_list),
        "summary": {
            "total_minus": total_minus,
            "total_plus": total_plus,
            "net": total_plus - total_minus,
            "pending_count": pending_count
        }
    }

@router.get("/selisih-kas/{selisih_id}")
async def get_selisih_kas(selisih_id: str):
    selisih = await selisih_col().find_one({"id": selisih_id}, {"_id": 0})
    if not selisih:
        raise HTTPException(status_code=404, detail="Selisih kas tidak ditemukan")
    return selisih

class SelisihResolutionUpdate(BaseModel):
    resolution: str
    resolution_note: str = ""
    is_piutang: bool = False
    is_potong_gaji: bool = False
    potong_gaji_month: str = ""
    potong_gaji_amount: float = 0
    approved_by_id: str = ""
    approved_by_name: str = ""

@router.put("/selisih-kas/{selisih_id}/resolve")
async def resolve_selisih_kas(selisih_id: str, data: SelisihResolutionUpdate):
    existing = await selisih_col().find_one({"id": selisih_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Selisih kas tidak ditemukan")
    
    update_data = data.model_dump()
    update_data["updated_at"] = now_iso()
    update_data["approved_at"] = now_iso()
    
    # If piutang, update employee
    if data.is_piutang and data.resolution == "piutang_karyawan":
        update_data["piutang_remaining"] = existing.get("nominal", 0)
        await employees_col().update_one(
            {"id": existing["penjaga_id"]},
            {"$inc": {"piutang_karyawan": existing.get("nominal", 0)}}
        )
    
    await selisih_col().update_one({"id": selisih_id}, {"$set": update_data})
    
    # Update setoran resolution status
    await setoran_col().update_one(
        {"id": existing["setoran_id"]},
        {"$set": {"selisih_resolution": data.resolution}}
    )
    
    return {"message": "Resolusi selisih kas berhasil disimpan"}

# ==================== SYSTEM ALERTS ====================

@router.get("/alerts")
async def list_alerts(
    is_read: Optional[bool] = None,
    is_resolved: Optional[bool] = None,
    severity: Optional[str] = None,
    alert_type: Optional[str] = None,
    branch_id: Optional[str] = None,
    limit: int = 100
):
    query = {}
    if is_read is not None:
        query["is_read"] = is_read
    if is_resolved is not None:
        query["is_resolved"] = is_resolved
    if severity:
        query["severity"] = severity
    if alert_type:
        query["alert_type"] = alert_type
    if branch_id:
        query["branch_id"] = branch_id
    
    cursor = alerts_col().find(query, {"_id": 0}).sort("created_at", -1).limit(limit)
    alerts = await cursor.to_list(length=limit)
    
    # Count by severity
    critical = len([a for a in alerts if a.get("severity") == "critical"])
    urgent = len([a for a in alerts if a.get("severity") == "urgent"])
    warning = len([a for a in alerts if a.get("severity") == "warning"])
    
    return {
        "alerts": alerts,
        "total": len(alerts),
        "by_severity": {
            "critical": critical,
            "urgent": urgent,
            "warning": warning
        }
    }

@router.put("/alerts/{alert_id}/read")
async def mark_alert_read(alert_id: str, read_by: str):
    await alerts_col().update_one(
        {"id": alert_id},
        {"$set": {"is_read": True, "read_by": read_by, "read_at": now_iso()}}
    )
    return {"message": "Alert ditandai sudah dibaca"}

@router.put("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str, resolved_by: str, resolved_note: str = ""):
    await alerts_col().update_one(
        {"id": alert_id},
        {"$set": {
            "is_resolved": True,
            "resolved_by": resolved_by,
            "resolved_at": now_iso(),
            "resolved_note": resolved_note
        }}
    )
    return {"message": "Alert berhasil diselesaikan"}

# ==================== DASHBOARD SUMMARY ====================

@router.get("/dashboard/summary")
async def get_erp_dashboard_summary(tanggal: Optional[str] = None):
    if not tanggal:
        tanggal = datetime.now().strftime("%Y-%m-%d")
    
    # Get today's setoran
    setoran_today = await setoran_col().find({"tanggal": tanggal}, {"_id": 0}).to_list(length=100)
    
    # Get all branches
    branches = await get_db()['branches'].find({}, {"_id": 0}).to_list(length=100)
    total_branches = len(branches)
    
    # Setoran summary
    cabang_sudah_setor = len(set(s["branch_id"] for s in setoran_today))
    cabang_belum_setor = total_branches - cabang_sudah_setor
    
    total_penjualan = sum(s.get("total_penjualan", 0) for s in setoran_today)
    total_setoran = sum(s.get("total_setoran", 0) for s in setoran_today)
    total_minus = sum(s.get("selisih", 0) for s in setoran_today if s.get("selisih", 0) < 0)
    total_plus = sum(s.get("selisih", 0) for s in setoran_today if s.get("selisih", 0) > 0)
    
    # Pending alerts
    pending_alerts = await alerts_col().count_documents({"is_resolved": False})
    critical_alerts = await alerts_col().count_documents({"is_resolved": False, "severity": "critical"})
    
    # Employees
    total_employees = await employees_col().count_documents({"status": "active"})
    
    # Pending selisih
    pending_selisih = await selisih_col().count_documents({"resolution": "pending"})
    
    return {
        "tanggal": tanggal,
        "cabang": {
            "total": total_branches,
            "sudah_setor": cabang_sudah_setor,
            "belum_setor": cabang_belum_setor
        },
        "keuangan": {
            "total_penjualan": total_penjualan,
            "total_setoran": total_setoran,
            "total_minus": abs(total_minus),
            "total_plus": total_plus,
            "net_selisih": total_plus + total_minus
        },
        "alerts": {
            "total": pending_alerts,
            "critical": critical_alerts
        },
        "karyawan": {
            "total": total_employees
        },
        "selisih_pending": pending_selisih
    }
