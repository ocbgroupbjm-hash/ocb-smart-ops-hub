# OCB TITAN ERP - HR ATTENDANCE SYSTEM
# Check-in/Check-out dengan multi-method support

from fastapi import APIRouter, HTTPException, Depends, Request, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta, date
from database import db
from utils.auth import get_current_user
from routes.rbac_system import log_activity
import uuid

router = APIRouter(prefix="/api/hr/attendance", tags=["HR Attendance System"])

# Collections
attendance_logs = db["attendance_logs"]
employees = db["employees"]
shifts = db["shifts"]

# ==================== PYDANTIC MODELS ====================

class ShiftCreate(BaseModel):
    """Shift/jadwal kerja"""
    name: str
    code: str
    start_time: str  # "08:00"
    end_time: str    # "17:00"
    break_start: Optional[str] = "12:00"
    break_end: Optional[str] = "13:00"
    work_hours: float = 8.0
    is_overnight: bool = False  # Untuk shift malam
    description: Optional[str] = None

class CheckInRequest(BaseModel):
    """Check-in attendance"""
    employee_id: str  # NIK atau ID
    check_in_time: Optional[str] = None  # ISO datetime, if not provided use current time
    method: str = "manual"  # manual, fingerprint, face, gps
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    notes: Optional[str] = None
    shift_id: Optional[str] = None

class CheckOutRequest(BaseModel):
    """Check-out attendance"""
    employee_id: str
    check_out_time: Optional[str] = None
    method: str = "manual"
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    notes: Optional[str] = None
    overtime_hours: Optional[float] = 0

class BulkAttendanceRequest(BaseModel):
    """Import attendance data (for migration)"""
    records: List[Dict[str, Any]]


# ==================== SHIFTS ====================

@router.post("/shifts")
async def create_shift(
    data: ShiftCreate,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """Create new work shift"""
    user_id = user.get("user_id", user.get("id", ""))
    user_name = user.get("name", "")
    
    existing = await shifts.find_one({"code": data.code.upper()})
    if existing:
        raise HTTPException(status_code=400, detail=f"Kode shift {data.code} sudah ada")
    
    shift = {
        "id": str(uuid.uuid4()),
        "code": data.code.upper(),
        "name": data.name,
        "start_time": data.start_time,
        "end_time": data.end_time,
        "break_start": data.break_start,
        "break_end": data.break_end,
        "work_hours": data.work_hours,
        "is_overnight": data.is_overnight,
        "description": data.description,
        "is_active": True,
        "created_by": user_id,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await shifts.insert_one(shift)
    
    return {"status": "success", "shift_id": shift["id"], "code": shift["code"]}

@router.get("/shifts")
async def get_shifts(
    is_active: Optional[bool] = True,
    user: dict = Depends(get_current_user)
):
    """Get all shifts"""
    query = {}
    if is_active is not None:
        query["is_active"] = is_active
    
    shift_list = await shifts.find(query, {"_id": 0}).to_list(50)
    return {"shifts": shift_list, "count": len(shift_list)}


# ==================== ATTENDANCE ====================

@router.post("/checkin")
async def check_in(
    data: CheckInRequest,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """
    Record employee check-in
    
    Business Rules:
    - One check-in per day per employee
    - Can check late status against shift
    - Location tracking optional
    """
    user_id = user.get("user_id", user.get("id", ""))
    user_name = user.get("name", "")
    
    # Find employee (support both id, employee_id, and nik field)
    employee = await employees.find_one(
        {"$or": [{"id": data.employee_id}, {"employee_id": data.employee_id.upper()}, {"nik": data.employee_id.upper()}]},
        {"_id": 0}
    )
    
    if not employee:
        raise HTTPException(status_code=404, detail="Karyawan tidak ditemukan")
    
    if employee.get("status") != "active":
        raise HTTPException(status_code=400, detail="Karyawan tidak aktif")
    
    # Parse check-in time
    if data.check_in_time:
        check_in_dt = datetime.fromisoformat(data.check_in_time.replace("Z", "+00:00"))
    else:
        check_in_dt = datetime.now(timezone.utc)
    
    attendance_date = check_in_dt.strftime("%Y-%m-%d")
    
    # Check if already checked in today
    existing = await attendance_logs.find_one({
        "employee_id": employee["id"],
        "date": attendance_date
    })
    
    if existing and existing.get("check_in"):
        raise HTTPException(
            status_code=400, 
            detail=f"Sudah check-in hari ini pada {existing.get('check_in_time', 'N/A')}"
        )
    
    # Get shift info for late calculation
    shift_info = None
    is_late = False
    late_minutes = 0
    
    if data.shift_id:
        shift_info = await shifts.find_one({"id": data.shift_id}, {"_id": 0})
    
    if shift_info:
        shift_start = shift_info.get("start_time", "08:00")
        # Parse shift start time
        shift_hour, shift_minute = map(int, shift_start.split(":"))
        check_hour = check_in_dt.hour
        check_minute = check_in_dt.minute
        
        # Calculate late (simple logic, not considering overnight shifts)
        if check_hour > shift_hour or (check_hour == shift_hour and check_minute > shift_minute):
            is_late = True
            late_minutes = (check_hour - shift_hour) * 60 + (check_minute - shift_minute)
    
    # Create attendance record
    attendance = {
        "id": str(uuid.uuid4()),
        "employee_id": employee["id"],
        "employee_nik": employee.get("nik") or employee.get("employee_id"),  # Fixed: use 'nik' field
        "employee_name": employee.get("name") or employee.get("full_name"),  # Fixed: use 'name' field
        "department_id": employee.get("department_id") or employee.get("jabatan_id"),
        "department_name": employee.get("department") or employee.get("department_name"),  # Fixed: use 'department' field
        "branch_id": employee.get("branch_id"),
        "date": attendance_date,
        
        # Check-in
        "check_in": check_in_dt.isoformat(),
        "check_in_time": check_in_dt.strftime("%H:%M:%S"),
        "check_in_method": data.method,
        "check_in_location": data.location,
        "check_in_lat": data.latitude,
        "check_in_lng": data.longitude,
        "check_in_notes": data.notes,
        
        # Check-out (will be filled later)
        "check_out": None,
        "check_out_time": None,
        "check_out_method": None,
        "check_out_location": None,
        
        # Shift
        "shift_id": data.shift_id,
        "shift_name": shift_info.get("name") if shift_info else None,
        
        # Status
        "is_late": is_late,
        "late_minutes": late_minutes,
        "work_hours": 0,
        "overtime_hours": 0,
        "status": "present",  # present, absent, leave, sick, holiday
        
        # Metadata
        "created_by": user_id,
        "created_by_name": user_name,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    if existing:
        # Update existing record
        await attendance_logs.update_one(
            {"id": existing["id"]},
            {"$set": attendance}
        )
        attendance["id"] = existing["id"]
    else:
        await attendance_logs.insert_one(attendance)
    
    await log_activity(
        db, user_id, user_name,
        "checkin", "attendance",
        f"Check-in: {employee.get('full_name')} pada {check_in_dt.strftime('%H:%M')}",
        request.client.host if request.client else "",
        user.get("branch_id", "")
    )
    
    response = {
        "status": "success",
        "message": f"Check-in berhasil",
        "employee_name": employee.get("name") or employee.get("full_name"),
        "check_in_time": check_in_dt.strftime("%H:%M:%S"),
        "date": attendance_date,
        "is_late": is_late
    }
    
    if is_late:
        response["late_minutes"] = late_minutes
    
    return response


@router.post("/checkout")
async def check_out(
    data: CheckOutRequest,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """
    Record employee check-out
    
    Business Rules:
    - Must have checked in first
    - Calculate work hours
    - Record overtime if any
    """
    user_id = user.get("user_id", user.get("id", ""))
    user_name = user.get("name", "")
    
    # Find employee (support both id, employee_id, and nik field)
    employee = await employees.find_one(
        {"$or": [{"id": data.employee_id}, {"employee_id": data.employee_id.upper()}, {"nik": data.employee_id.upper()}]},
        {"_id": 0}
    )
    
    if not employee:
        raise HTTPException(status_code=404, detail="Karyawan tidak ditemukan")
    
    # Parse check-out time
    if data.check_out_time:
        check_out_dt = datetime.fromisoformat(data.check_out_time.replace("Z", "+00:00"))
    else:
        check_out_dt = datetime.now(timezone.utc)
    
    attendance_date = check_out_dt.strftime("%Y-%m-%d")
    
    # Find today's check-in
    attendance = await attendance_logs.find_one({
        "employee_id": employee["id"],
        "date": attendance_date,
        "check_in": {"$ne": None}
    })
    
    if not attendance:
        raise HTTPException(status_code=400, detail="Belum check-in hari ini")
    
    if attendance.get("check_out"):
        raise HTTPException(
            status_code=400, 
            detail=f"Sudah check-out hari ini pada {attendance.get('check_out_time', 'N/A')}"
        )
    
    # Calculate work hours
    check_in_dt = datetime.fromisoformat(attendance["check_in"].replace("Z", "+00:00"))
    work_duration = check_out_dt - check_in_dt
    work_hours = work_duration.total_seconds() / 3600  # Convert to hours
    
    # Update attendance record
    update_data = {
        "check_out": check_out_dt.isoformat(),
        "check_out_time": check_out_dt.strftime("%H:%M:%S"),
        "check_out_method": data.method,
        "check_out_location": data.location,
        "check_out_lat": data.latitude,
        "check_out_lng": data.longitude,
        "check_out_notes": data.notes,
        "work_hours": round(work_hours, 2),
        "overtime_hours": data.overtime_hours or 0,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "updated_by": user_id
    }
    
    await attendance_logs.update_one(
        {"id": attendance["id"]},
        {"$set": update_data}
    )
    
    await log_activity(
        db, user_id, user_name,
        "checkout", "attendance",
        f"Check-out: {employee.get('full_name')} pada {check_out_dt.strftime('%H:%M')} ({work_hours:.1f} jam)",
        request.client.host if request.client else "",
        user.get("branch_id", "")
    )
    
    return {
        "status": "success",
        "message": "Check-out berhasil",
        "employee_name": employee.get("name") or employee.get("full_name"),
        "check_in_time": attendance.get("check_in_time"),
        "check_out_time": check_out_dt.strftime("%H:%M:%S"),
        "work_hours": round(work_hours, 2),
        "overtime_hours": data.overtime_hours or 0
    }


@router.get("/today")
async def get_today_attendance(
    department_id: Optional[str] = None,
    branch_id: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Get today's attendance summary"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    query = {"date": today}
    if department_id:
        query["department_id"] = department_id
    if branch_id:
        query["branch_id"] = branch_id
    
    records = await attendance_logs.find(query, {"_id": 0}).to_list(500)
    
    present = len([r for r in records if r.get("check_in")])
    checked_out = len([r for r in records if r.get("check_out")])
    late = len([r for r in records if r.get("is_late")])
    
    # Get total active employees
    emp_query = {"status": "active"}
    if department_id:
        emp_query["department_id"] = department_id
    if branch_id:
        emp_query["branch_id"] = branch_id
    
    total_employees = await employees.count_documents(emp_query)
    
    return {
        "date": today,
        "summary": {
            "total_employees": total_employees,
            "present": present,
            "absent": total_employees - present,
            "checked_out": checked_out,
            "still_working": present - checked_out,
            "late": late
        },
        "records": records[:50]  # Limit response
    }


@router.get("/report")
async def get_attendance_report(
    start_date: str,
    end_date: str,
    employee_id: Optional[str] = None,
    department_id: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Get attendance report for date range"""
    query = {
        "date": {"$gte": start_date, "$lte": end_date}
    }
    
    if employee_id:
        employee = await employees.find_one(
            {"$or": [{"id": employee_id}, {"employee_id": employee_id.upper()}, {"nik": employee_id.upper()}]},
            {"_id": 0}
        )
        if employee:
            query["employee_id"] = employee["id"]
    
    if department_id:
        query["department_id"] = department_id
    
    records = await attendance_logs.find(query, {"_id": 0}).sort("date", 1).to_list(1000)
    
    # Calculate summary
    total_days = len(set([r["date"] for r in records]))
    total_late = sum(1 for r in records if r.get("is_late"))
    total_work_hours = sum(r.get("work_hours", 0) for r in records)
    total_overtime = sum(r.get("overtime_hours", 0) for r in records)
    
    return {
        "period": {"start": start_date, "end": end_date},
        "summary": {
            "total_days": total_days,
            "total_records": len(records),
            "total_late": total_late,
            "total_work_hours": round(total_work_hours, 2),
            "total_overtime": round(total_overtime, 2),
            "average_work_hours": round(total_work_hours / len(records), 2) if records else 0
        },
        "records": records
    }


@router.get("/employee/{employee_id}")
async def get_employee_attendance(
    employee_id: str,
    month: Optional[str] = None,  # Format: "2026-03"
    user: dict = Depends(get_current_user)
):
    """Get attendance history for specific employee"""
    employee = await employees.find_one(
        {"$or": [{"id": employee_id}, {"employee_id": employee_id.upper()}, {"nik": employee_id.upper()}]},
        {"_id": 0}
    )
    
    if not employee:
        raise HTTPException(status_code=404, detail="Karyawan tidak ditemukan")
    
    query = {"employee_id": employee["id"]}
    
    if month:
        query["date"] = {"$regex": f"^{month}"}
    else:
        # Default: current month
        current_month = datetime.now(timezone.utc).strftime("%Y-%m")
        query["date"] = {"$regex": f"^{current_month}"}
    
    records = await attendance_logs.find(query, {"_id": 0}).sort("date", -1).to_list(100)
    
    # Calculate summary
    present_days = len([r for r in records if r.get("check_in")])
    late_days = len([r for r in records if r.get("is_late")])
    total_work_hours = sum(r.get("work_hours", 0) for r in records)
    total_overtime = sum(r.get("overtime_hours", 0) for r in records)
    
    return {
        "employee": {
            "id": employee["id"],
            "employee_id": employee.get("nik") or employee.get("employee_id"),  # Fixed: use 'nik' field
            "name": employee.get("name") or employee.get("full_name"),  # Fixed: use 'name' field
            "department": employee.get("department") or employee.get("department_name")  # Fixed: use 'department' field
        },
        "summary": {
            "present_days": present_days,
            "late_days": late_days,
            "total_work_hours": round(total_work_hours, 2),
            "total_overtime": round(total_overtime, 2)
        },
        "records": records
    }
