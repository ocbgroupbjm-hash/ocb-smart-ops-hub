# OCB GROUP SUPER ERP - Attendance Routes
# Absensi Karyawan dengan GPS & Selfie

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel
import uuid
import math
import base64

from database import get_db
from models.erp_models import (
    Attendance, AttendanceStatus, ApprovalStatus,
    SystemAlert, AlertType, AlertSeverity
)

router = APIRouter(prefix="/api/attendance", tags=["Attendance"])

def gen_id():
    return str(uuid.uuid4())

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def get_wib_now():
    """Get current time in WIB (UTC+7)"""
    return datetime.now(timezone.utc) + timedelta(hours=7)

# Collections
def attendance_col():
    return get_db()['attendance']

def employees_col():
    return get_db()['employees']

def shifts_col():
    return get_db()['master_shifts']

def lokasi_col():
    return get_db()['master_lokasi_absensi']

def alerts_col():
    return get_db()['system_alerts']

# Helper: Calculate distance between two coordinates
def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in meters between two GPS coordinates"""
    R = 6371000  # Earth's radius in meters
    
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

# ==================== CHECK IN ====================

class CheckInRequest(BaseModel):
    employee_id: str
    employee_nik: str
    employee_name: str
    jabatan: str = ""
    branch_id: str
    branch_name: str
    shift_id: str = ""
    shift_name: str = ""
    latitude: float
    longitude: float
    address: str = ""
    photo_base64: str = ""  # Base64 encoded selfie
    device: str = ""
    keterangan: str = ""

@router.post("/check-in")
async def check_in(data: CheckInRequest):
    tanggal = get_wib_now().strftime("%Y-%m-%d")
    waktu = get_wib_now().strftime("%H:%M:%S")
    
    # Check if already checked in today
    existing = await attendance_col().find_one({
        "employee_id": data.employee_id,
        "tanggal": tanggal
    })
    
    if existing and existing.get("check_in_time"):
        raise HTTPException(status_code=400, detail="Anda sudah melakukan check-in hari ini")
    
    # Get shift info
    shift = None
    jadwal_masuk = "08:00"
    jadwal_pulang = "17:00"
    
    if data.shift_id:
        shift = await shifts_col().find_one({"id": data.shift_id})
        if shift:
            jadwal_masuk = shift.get("start_time", "08:00")
            jadwal_pulang = shift.get("end_time", "17:00")
    
    # Validate location
    valid_location = False
    distance = 0
    
    lokasi = await lokasi_col().find_one({"branch_id": data.branch_id, "is_active": True})
    if lokasi:
        distance = haversine_distance(
            data.latitude, data.longitude,
            lokasi.get("latitude", 0), lokasi.get("longitude", 0)
        )
        valid_location = distance <= lokasi.get("radius_meters", 100)
    
    # Calculate late minutes
    telat_menit = 0
    status = AttendanceStatus.HADIR
    
    try:
        jadwal_masuk_time = datetime.strptime(jadwal_masuk, "%H:%M").time()
        check_in_time = datetime.strptime(waktu, "%H:%M:%S").time()
        
        if check_in_time > jadwal_masuk_time:
            delta = datetime.combine(datetime.today(), check_in_time) - datetime.combine(datetime.today(), jadwal_masuk_time)
            telat_menit = int(delta.total_seconds() / 60)
            if telat_menit > 0:
                status = AttendanceStatus.TELAT
    except:
        pass
    
    # Save photo (in real scenario, upload to cloud storage)
    photo_url = ""
    if data.photo_base64:
        # For now, just store indicator that photo exists
        photo_url = f"selfie_{data.employee_id}_{tanggal}_checkin.jpg"
    
    if existing:
        # Update existing record
        await attendance_col().update_one(
            {"id": existing["id"]},
            {"$set": {
                "check_in_time": waktu,
                "check_in_lat": data.latitude,
                "check_in_lng": data.longitude,
                "check_in_address": data.address,
                "check_in_photo_url": photo_url,
                "check_in_device": data.device,
                "check_in_valid_location": valid_location,
                "check_in_distance_meters": int(distance),
                "telat_menit": telat_menit,
                "status": status.value,
                "keterangan": data.keterangan,
                "updated_at": now_iso()
            }}
        )
        attendance_id = existing["id"]
    else:
        # Create new attendance record
        attendance = Attendance(
            id=gen_id(),
            employee_id=data.employee_id,
            employee_nik=data.employee_nik,
            employee_name=data.employee_name,
            jabatan=data.jabatan,
            branch_id=data.branch_id,
            branch_name=data.branch_name,
            shift_id=data.shift_id,
            shift_name=data.shift_name,
            jadwal_masuk=jadwal_masuk,
            jadwal_pulang=jadwal_pulang,
            tanggal=tanggal,
            check_in_time=waktu,
            check_in_lat=data.latitude,
            check_in_lng=data.longitude,
            check_in_address=data.address,
            check_in_photo_url=photo_url,
            check_in_device=data.device,
            check_in_valid_location=valid_location,
            check_in_distance_meters=int(distance),
            status=status,
            telat_menit=telat_menit,
            keterangan=data.keterangan,
            created_at=now_iso(),
            updated_at=now_iso()
        )
        await attendance_col().insert_one(attendance.model_dump())
        attendance_id = attendance.id
    
    # Create alert if late > 30 minutes or invalid location
    if telat_menit > 30:
        alert = SystemAlert(
            id=gen_id(),
            alert_type=AlertType.SERING_TELAT,
            severity=AlertSeverity.WARNING,
            title=f"Telat: {data.employee_name}",
            message=f"Telat {telat_menit} menit di {data.branch_name}",
            branch_id=data.branch_id,
            branch_name=data.branch_name,
            employee_id=data.employee_id,
            employee_name=data.employee_name,
            reference_type="attendance",
            reference_id=attendance_id,
            data={"telat_menit": telat_menit, "tanggal": tanggal},
            created_at=now_iso()
        )
        await alerts_col().insert_one(alert.model_dump())
    
    return {
        "message": "Check-in berhasil",
        "attendance_id": attendance_id,
        "tanggal": tanggal,
        "waktu": waktu,
        "status": status.value,
        "telat_menit": telat_menit,
        "valid_location": valid_location,
        "distance_meters": int(distance)
    }

# ==================== CHECK OUT ====================

class CheckOutRequest(BaseModel):
    employee_id: str
    latitude: float
    longitude: float
    address: str = ""
    photo_base64: str = ""
    device: str = ""
    keterangan: str = ""

@router.post("/check-out")
async def check_out(data: CheckOutRequest):
    tanggal = get_wib_now().strftime("%Y-%m-%d")
    waktu = get_wib_now().strftime("%H:%M:%S")
    
    # Find today's attendance
    existing = await attendance_col().find_one({
        "employee_id": data.employee_id,
        "tanggal": tanggal
    })
    
    if not existing:
        raise HTTPException(status_code=400, detail="Anda belum melakukan check-in hari ini")
    
    if existing.get("check_out_time"):
        raise HTTPException(status_code=400, detail="Anda sudah melakukan check-out hari ini")
    
    # Validate location
    valid_location = False
    distance = 0
    
    lokasi = await lokasi_col().find_one({"branch_id": existing.get("branch_id"), "is_active": True})
    if lokasi:
        distance = haversine_distance(
            data.latitude, data.longitude,
            lokasi.get("latitude", 0), lokasi.get("longitude", 0)
        )
        valid_location = distance <= lokasi.get("radius_meters", 100)
    
    # Calculate working hours and early leave
    pulang_cepat_menit = 0
    lembur_menit = 0
    total_jam_kerja = 0
    
    try:
        check_in_time = datetime.strptime(existing.get("check_in_time", "08:00:00"), "%H:%M:%S")
        check_out_time = datetime.strptime(waktu, "%H:%M:%S")
        jadwal_pulang = datetime.strptime(existing.get("jadwal_pulang", "17:00"), "%H:%M")
        
        # Calculate working hours
        work_delta = check_out_time - check_in_time
        total_jam_kerja = work_delta.total_seconds() / 3600
        
        # Check early leave or overtime
        if check_out_time.time() < jadwal_pulang.time():
            delta = jadwal_pulang - check_out_time
            pulang_cepat_menit = int(delta.total_seconds() / 60)
        elif check_out_time.time() > jadwal_pulang.time():
            delta = check_out_time - jadwal_pulang
            lembur_menit = int(delta.total_seconds() / 60)
    except:
        pass
    
    # Save photo
    photo_url = ""
    if data.photo_base64:
        photo_url = f"selfie_{data.employee_id}_{tanggal}_checkout.jpg"
    
    # Update attendance
    await attendance_col().update_one(
        {"id": existing["id"]},
        {"$set": {
            "check_out_time": waktu,
            "check_out_lat": data.latitude,
            "check_out_lng": data.longitude,
            "check_out_address": data.address,
            "check_out_photo_url": photo_url,
            "check_out_device": data.device,
            "check_out_valid_location": valid_location,
            "check_out_distance_meters": int(distance),
            "pulang_cepat_menit": pulang_cepat_menit,
            "lembur_menit": lembur_menit,
            "total_jam_kerja": round(total_jam_kerja, 2),
            "updated_at": now_iso()
        }}
    )
    
    return {
        "message": "Check-out berhasil",
        "attendance_id": existing["id"],
        "tanggal": tanggal,
        "waktu": waktu,
        "valid_location": valid_location,
        "distance_meters": int(distance),
        "total_jam_kerja": round(total_jam_kerja, 2),
        "pulang_cepat_menit": pulang_cepat_menit,
        "lembur_menit": lembur_menit
    }

# ==================== LIST ATTENDANCE ====================

@router.get("/list")
async def list_attendance(
    tanggal: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    employee_id: Optional[str] = None,
    branch_id: Optional[str] = None,
    status: Optional[str] = None
):
    query = {}
    
    if tanggal:
        query["tanggal"] = tanggal
    elif start_date and end_date:
        query["tanggal"] = {"$gte": start_date, "$lte": end_date}
    
    if employee_id:
        query["employee_id"] = employee_id
    if branch_id:
        query["branch_id"] = branch_id
    if status:
        query["status"] = status
    
    cursor = attendance_col().find(query, {"_id": 0}).sort([("tanggal", -1), ("check_in_time", -1)])
    attendance_list = await cursor.to_list(length=1000)
    
    # Summary
    total_hadir = len([a for a in attendance_list if a.get("status") in ["hadir", "telat"]])
    total_telat = len([a for a in attendance_list if a.get("status") == "telat"])
    total_alpha = len([a for a in attendance_list if a.get("status") == "alpha"])
    total_izin = len([a for a in attendance_list if a.get("status") in ["izin", "cuti", "sakit"]])
    total_telat_menit = sum(a.get("telat_menit", 0) for a in attendance_list)
    total_lembur_menit = sum(a.get("lembur_menit", 0) for a in attendance_list)
    
    return {
        "attendance": attendance_list,
        "total": len(attendance_list),
        "summary": {
            "hadir": total_hadir,
            "telat": total_telat,
            "alpha": total_alpha,
            "izin": total_izin,
            "total_telat_menit": total_telat_menit,
            "total_lembur_menit": total_lembur_menit
        }
    }

@router.get("/employee/{employee_id}")
async def get_employee_attendance(employee_id: str, month: Optional[int] = None, year: Optional[int] = None):
    if not month:
        month = get_wib_now().month
    if not year:
        year = get_wib_now().year
    
    # Generate date range
    start_date = f"{year}-{month:02d}-01"
    if month == 12:
        end_date = f"{year + 1}-01-01"
    else:
        end_date = f"{year}-{month + 1:02d}-01"
    
    cursor = attendance_col().find({
        "employee_id": employee_id,
        "tanggal": {"$gte": start_date, "$lt": end_date}
    }, {"_id": 0}).sort("tanggal", 1)
    
    attendance_list = await cursor.to_list(length=31)
    
    # Calculate summary
    hari_hadir = len([a for a in attendance_list if a.get("status") in ["hadir", "telat"]])
    hari_telat = len([a for a in attendance_list if a.get("status") == "telat"])
    hari_alpha = len([a for a in attendance_list if a.get("status") == "alpha"])
    hari_izin = len([a for a in attendance_list if a.get("status") == "izin"])
    hari_cuti = len([a for a in attendance_list if a.get("status") == "cuti"])
    hari_sakit = len([a for a in attendance_list if a.get("status") == "sakit"])
    total_telat_menit = sum(a.get("telat_menit", 0) for a in attendance_list)
    total_lembur_menit = sum(a.get("lembur_menit", 0) for a in attendance_list)
    total_jam_kerja = sum(a.get("total_jam_kerja", 0) for a in attendance_list)
    
    return {
        "employee_id": employee_id,
        "period": f"{year}-{month:02d}",
        "attendance": attendance_list,
        "summary": {
            "hari_hadir": hari_hadir,
            "hari_telat": hari_telat,
            "hari_alpha": hari_alpha,
            "hari_izin": hari_izin,
            "hari_cuti": hari_cuti,
            "hari_sakit": hari_sakit,
            "total_telat_menit": total_telat_menit,
            "total_lembur_menit": total_lembur_menit,
            "total_jam_kerja": round(total_jam_kerja, 2)
        }
    }

# ==================== IZIN / CUTI ====================

class IzinRequest(BaseModel):
    employee_id: str
    employee_nik: str
    employee_name: str
    jabatan: str = ""
    branch_id: str
    branch_name: str
    tanggal: str
    status: str  # izin, cuti, sakit
    keterangan: str
    dokumen_url: str = ""

@router.post("/izin")
async def create_izin(data: IzinRequest):
    # Check if already exists
    existing = await attendance_col().find_one({
        "employee_id": data.employee_id,
        "tanggal": data.tanggal
    })
    
    if existing:
        raise HTTPException(status_code=400, detail="Sudah ada data absensi untuk tanggal ini")
    
    status_map = {
        "izin": AttendanceStatus.IZIN,
        "cuti": AttendanceStatus.CUTI,
        "sakit": AttendanceStatus.SAKIT
    }
    
    attendance = Attendance(
        id=gen_id(),
        employee_id=data.employee_id,
        employee_nik=data.employee_nik,
        employee_name=data.employee_name,
        jabatan=data.jabatan,
        branch_id=data.branch_id,
        branch_name=data.branch_name,
        tanggal=data.tanggal,
        status=status_map.get(data.status, AttendanceStatus.IZIN),
        keterangan=data.keterangan,
        approval_status=ApprovalStatus.PENDING,
        created_at=now_iso(),
        updated_at=now_iso()
    )
    
    await attendance_col().insert_one(attendance.model_dump())
    
    return {"message": "Pengajuan izin berhasil", "attendance_id": attendance.id}

@router.put("/izin/{attendance_id}/approve")
async def approve_izin(attendance_id: str, approved_by: str):
    existing = await attendance_col().find_one({"id": attendance_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Data tidak ditemukan")
    
    await attendance_col().update_one(
        {"id": attendance_id},
        {"$set": {
            "approval_status": ApprovalStatus.APPROVED.value,
            "approved_by": approved_by,
            "approved_at": now_iso(),
            "updated_at": now_iso()
        }}
    )
    
    return {"message": "Izin disetujui"}

@router.put("/izin/{attendance_id}/reject")
async def reject_izin(attendance_id: str, rejected_by: str, alasan: str = ""):
    existing = await attendance_col().find_one({"id": attendance_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Data tidak ditemukan")
    
    await attendance_col().update_one(
        {"id": attendance_id},
        {"$set": {
            "approval_status": ApprovalStatus.REJECTED.value,
            "approved_by": rejected_by,
            "approved_at": now_iso(),
            "catatan_supervisor": f"DITOLAK: {alasan}",
            "updated_at": now_iso()
        }}
    )
    
    return {"message": "Izin ditolak"}

# ==================== DAILY SUMMARY ====================

@router.get("/summary/daily")
async def get_daily_summary(tanggal: Optional[str] = None):
    if not tanggal:
        tanggal = get_wib_now().strftime("%Y-%m-%d")
    
    # Get all attendance for today
    attendance_list = await attendance_col().find({"tanggal": tanggal}, {"_id": 0}).to_list(length=1000)
    
    # Get all active employees
    total_employees = await employees_col().count_documents({"status": "active"})
    
    # Count by status
    hadir = len([a for a in attendance_list if a.get("status") in ["hadir", "telat"]])
    telat = len([a for a in attendance_list if a.get("status") == "telat"])
    alpha = total_employees - len(attendance_list)  # Those without record
    izin = len([a for a in attendance_list if a.get("status") == "izin"])
    cuti = len([a for a in attendance_list if a.get("status") == "cuti"])
    sakit = len([a for a in attendance_list if a.get("status") == "sakit"])
    
    # Get employees who haven't checked in
    checked_in_ids = [a.get("employee_id") for a in attendance_list]
    not_checked_in = await employees_col().find(
        {"status": "active", "id": {"$nin": checked_in_ids}},
        {"_id": 0, "id": 1, "name": 1, "branch_name": 1}
    ).to_list(length=100)
    
    return {
        "tanggal": tanggal,
        "total_karyawan": total_employees,
        "summary": {
            "hadir": hadir,
            "telat": telat,
            "alpha": alpha,
            "izin": izin,
            "cuti": cuti,
            "sakit": sakit
        },
        "percentage": {
            "hadir": round(hadir / total_employees * 100, 1) if total_employees > 0 else 0,
            "telat": round(telat / total_employees * 100, 1) if total_employees > 0 else 0
        },
        "not_checked_in": not_checked_in
    }

@router.get("/summary/branch/{branch_id}")
async def get_branch_attendance_summary(branch_id: str, tanggal: Optional[str] = None):
    if not tanggal:
        tanggal = get_wib_now().strftime("%Y-%m-%d")
    
    attendance_list = await attendance_col().find({
        "tanggal": tanggal,
        "branch_id": branch_id
    }, {"_id": 0}).to_list(length=100)
    
    total_branch_employees = await employees_col().count_documents({
        "status": "active",
        "branch_id": branch_id
    })
    
    hadir = len([a for a in attendance_list if a.get("status") in ["hadir", "telat"]])
    telat = len([a for a in attendance_list if a.get("status") == "telat"])
    
    return {
        "branch_id": branch_id,
        "tanggal": tanggal,
        "total_karyawan": total_branch_employees,
        "hadir": hadir,
        "telat": telat,
        "alpha": total_branch_employees - len(attendance_list),
        "attendance_list": attendance_list
    }
