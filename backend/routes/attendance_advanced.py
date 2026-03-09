# OCB TITAN AI - Advanced Attendance System
# Role-based attendance with GPS and permissions

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel
import uuid

from database import get_db

router = APIRouter(prefix="/api/attendance-v2", tags=["Advanced Attendance"])

def gen_id():
    return str(uuid.uuid4())

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def get_wib_now():
    return datetime.now(timezone.utc) + timedelta(hours=7)

# Collections
def attendance_col():
    return get_db()['attendance']

def employees_col():
    return get_db()['employees']

def leaves_col():
    return get_db()['leave_requests']

def overtime_col():
    return get_db()['overtime_requests']

def shifts_col():
    return get_db()['master_shifts']

def locations_col():
    return get_db()['attendance_locations']

# ==================== ROLE-BASED PERMISSIONS ====================

ROLE_PERMISSIONS = {
    "employee": {
        "can_view_own": True,
        "can_checkin": True,
        "can_checkout": True,
        "can_request_leave": True,
        "can_request_overtime": True,
        "can_view_others": False,
        "can_approve": False,
        "can_edit": False,
        "can_delete": False,
        "can_export": False,
        "can_view_reports": False
    },
    "spv": {
        "can_view_own": True,
        "can_checkin": True,
        "can_checkout": True,
        "can_request_leave": True,
        "can_request_overtime": True,
        "can_view_others": True,  # Same branch only
        "can_approve": True,  # Leave requests
        "can_edit": False,
        "can_delete": False,
        "can_export": True,  # Own branch
        "can_view_reports": True  # Own branch
    },
    "manager": {
        "can_view_own": True,
        "can_checkin": True,
        "can_checkout": True,
        "can_request_leave": True,
        "can_request_overtime": True,
        "can_view_others": True,  # All branches in region
        "can_approve": True,  # All requests
        "can_edit": True,
        "can_delete": False,
        "can_export": True,
        "can_view_reports": True
    },
    "hrd": {
        "can_view_own": True,
        "can_checkin": True,
        "can_checkout": True,
        "can_request_leave": True,
        "can_request_overtime": True,
        "can_view_others": True,  # All employees
        "can_approve": True,
        "can_edit": True,
        "can_delete": True,
        "can_export": True,
        "can_view_reports": True,
        "can_manage_shifts": True,
        "can_manage_locations": True
    },
    "owner": {
        "can_view_own": True,
        "can_checkin": False,  # Owner doesn't need to check in
        "can_checkout": False,
        "can_request_leave": False,
        "can_request_overtime": False,
        "can_view_others": True,  # ALL
        "can_approve": True,
        "can_edit": True,
        "can_delete": True,
        "can_export": True,
        "can_view_reports": True,
        "can_manage_shifts": True,
        "can_manage_locations": True,
        "can_manage_payroll": True
    }
}

@router.get("/permissions/{role}")
async def get_role_permissions(role: str):
    """Get permissions for a role"""
    if role not in ROLE_PERMISSIONS:
        raise HTTPException(status_code=404, detail="Role tidak ditemukan")
    
    return {"role": role, "permissions": ROLE_PERMISSIONS[role]}

# ==================== LEAVE REQUESTS ====================

class LeaveRequest(BaseModel):
    employee_id: str
    employee_name: str
    branch_id: str
    branch_name: str
    leave_type: str  # cuti, sakit, izin
    start_date: str
    end_date: str
    reason: str
    attachment_url: str = ""

@router.post("/leave/request")
async def create_leave_request(data: LeaveRequest):
    """Create leave request"""
    # Calculate days
    start = datetime.strptime(data.start_date, "%Y-%m-%d")
    end = datetime.strptime(data.end_date, "%Y-%m-%d")
    days = (end - start).days + 1
    
    request = {
        "id": gen_id(),
        **data.dict(),
        "days": days,
        "status": "pending",  # pending, approved, rejected
        "requested_at": now_iso(),
        "approved_by": "",
        "approved_at": "",
        "rejection_reason": ""
    }
    
    await leaves_col().insert_one(request)
    return {"message": "Pengajuan cuti berhasil", "request": request}

@router.get("/leave/requests")
async def get_leave_requests(
    branch_id: Optional[str] = None,
    employee_id: Optional[str] = None,
    status: Optional[str] = None,
    role: str = "employee"
):
    """Get leave requests based on role permissions"""
    query = {}
    
    # Apply role-based filtering
    if role == "employee" and employee_id:
        query["employee_id"] = employee_id
    elif role == "spv" and branch_id:
        query["branch_id"] = branch_id
    # Manager, HRD, Owner can see all
    
    if status:
        query["status"] = status
    
    requests = await leaves_col().find(query, {"_id": 0}).sort("requested_at", -1).to_list(length=500)
    return {"requests": requests}

@router.put("/leave/approve/{request_id}")
async def approve_leave_request(request_id: str, approver_id: str, approver_name: str, approved: bool, rejection_reason: str = ""):
    """Approve or reject leave request"""
    update_data = {
        "status": "approved" if approved else "rejected",
        "approved_by": approver_name,
        "approver_id": approver_id,
        "approved_at": now_iso()
    }
    
    if not approved:
        update_data["rejection_reason"] = rejection_reason
    
    await leaves_col().update_one({"id": request_id}, {"$set": update_data})
    
    # If approved, create attendance records as "cuti/izin/sakit"
    if approved:
        request = await leaves_col().find_one({"id": request_id}, {"_id": 0})
        if request:
            start = datetime.strptime(request["start_date"], "%Y-%m-%d")
            end = datetime.strptime(request["end_date"], "%Y-%m-%d")
            
            current = start
            while current <= end:
                attendance_record = {
                    "id": gen_id(),
                    "employee_id": request["employee_id"],
                    "employee_name": request["employee_name"],
                    "branch_id": request["branch_id"],
                    "branch_name": request["branch_name"],
                    "tanggal": current.strftime("%Y-%m-%d"),
                    "status": request["leave_type"],  # cuti, sakit, izin
                    "keterangan": request["reason"],
                    "leave_request_id": request_id,
                    "created_at": now_iso()
                }
                await attendance_col().update_one(
                    {"employee_id": request["employee_id"], "tanggal": current.strftime("%Y-%m-%d")},
                    {"$set": attendance_record},
                    upsert=True
                )
                current += timedelta(days=1)
    
    return {"message": "Pengajuan cuti berhasil diproses"}

# ==================== OVERTIME REQUESTS ====================

class OvertimeRequest(BaseModel):
    employee_id: str
    employee_name: str
    branch_id: str
    branch_name: str
    tanggal: str
    start_time: str
    end_time: str
    reason: str

@router.post("/overtime/request")
async def create_overtime_request(data: OvertimeRequest):
    """Create overtime request"""
    # Calculate hours
    start = datetime.strptime(data.start_time, "%H:%M")
    end = datetime.strptime(data.end_time, "%H:%M")
    hours = (end - start).seconds / 3600
    
    request = {
        "id": gen_id(),
        **data.dict(),
        "hours": round(hours, 2),
        "status": "pending",
        "requested_at": now_iso()
    }
    
    await overtime_col().insert_one(request)
    return {"message": "Pengajuan lembur berhasil", "request": request}

@router.get("/overtime/requests")
async def get_overtime_requests(branch_id: Optional[str] = None, status: Optional[str] = None):
    """Get overtime requests"""
    query = {}
    if branch_id:
        query["branch_id"] = branch_id
    if status:
        query["status"] = status
    
    requests = await overtime_col().find(query, {"_id": 0}).sort("requested_at", -1).to_list(length=500)
    return {"requests": requests}

@router.put("/overtime/approve/{request_id}")
async def approve_overtime_request(request_id: str, approver_name: str, approved: bool):
    """Approve or reject overtime request"""
    await overtime_col().update_one(
        {"id": request_id},
        {"$set": {
            "status": "approved" if approved else "rejected",
            "approved_by": approver_name,
            "approved_at": now_iso()
        }}
    )
    
    # If approved, update attendance record
    if approved:
        request = await overtime_col().find_one({"id": request_id}, {"_id": 0})
        if request:
            await attendance_col().update_one(
                {"employee_id": request["employee_id"], "tanggal": request["tanggal"]},
                {"$set": {
                    "lembur_jam": request["hours"],
                    "lembur_approved": True,
                    "overtime_request_id": request_id
                }}
            )
    
    return {"message": "Pengajuan lembur berhasil diproses"}

# ==================== ATTENDANCE SUMMARY ====================

@router.get("/summary/employee/{employee_id}")
async def get_employee_attendance_summary(employee_id: str, month: int, year: int):
    """Get attendance summary for employee"""
    import calendar
    _, last_day = calendar.monthrange(year, month)
    start_date = f"{year}-{month:02d}-01"
    end_date = f"{year}-{month:02d}-{last_day}"
    
    attendance = await attendance_col().find({
        "employee_id": employee_id,
        "tanggal": {"$gte": start_date, "$lte": end_date}
    }, {"_id": 0}).to_list(length=50)
    
    summary = {
        "employee_id": employee_id,
        "period": f"{month}/{year}",
        "total_days": last_day,
        "hadir": len([a for a in attendance if a.get("status") == "hadir"]),
        "telat": len([a for a in attendance if a.get("status") == "telat"]),
        "alpha": len([a for a in attendance if a.get("status") == "alpha"]),
        "izin": len([a for a in attendance if a.get("status") == "izin"]),
        "cuti": len([a for a in attendance if a.get("status") == "cuti"]),
        "sakit": len([a for a in attendance if a.get("status") == "sakit"]),
        "libur": len([a for a in attendance if a.get("status") == "libur"]),
        "total_telat_menit": sum(a.get("telat_menit", 0) for a in attendance),
        "total_lembur_jam": sum(a.get("lembur_jam", 0) for a in attendance),
        "records": attendance
    }
    
    # Calculate working days
    summary["working_days"] = summary["hadir"] + summary["telat"]
    summary["attendance_rate"] = (summary["working_days"] / (last_day - summary["libur"])) * 100 if (last_day - summary["libur"]) > 0 else 0
    
    return summary

@router.get("/summary/branch/{branch_id}")
async def get_branch_attendance_summary(branch_id: str, tanggal: str):
    """Get attendance summary for branch on specific date"""
    attendance = await attendance_col().find({
        "branch_id": branch_id,
        "tanggal": tanggal
    }, {"_id": 0}).to_list(length=100)
    
    employees = await employees_col().find({
        "branch_id": branch_id,
        "status": "active"
    }, {"_id": 0}).to_list(length=100)
    
    # Find employees who haven't checked in
    checked_in_ids = set(a.get("employee_id") for a in attendance)
    not_checked_in = [e for e in employees if e.get("id") not in checked_in_ids]
    
    summary = {
        "branch_id": branch_id,
        "tanggal": tanggal,
        "total_employees": len(employees),
        "checked_in": len(attendance),
        "not_checked_in": len(not_checked_in),
        "hadir": len([a for a in attendance if a.get("status") == "hadir"]),
        "telat": len([a for a in attendance if a.get("status") == "telat"]),
        "izin": len([a for a in attendance if a.get("status") in ["izin", "cuti", "sakit"]]),
        "not_checked_in_list": [{"id": e.get("id"), "name": e.get("name")} for e in not_checked_in],
        "late_list": [{"id": a.get("employee_id"), "name": a.get("employee_name"), "minutes": a.get("telat_menit")} 
                      for a in attendance if a.get("status") == "telat"]
    }
    
    return summary

# ==================== ATTENDANCE REPORTS ====================

@router.get("/reports/monthly")
async def get_monthly_attendance_report(month: int, year: int, branch_id: Optional[str] = None, role: str = "owner"):
    """Get monthly attendance report"""
    import calendar
    _, last_day = calendar.monthrange(year, month)
    start_date = f"{year}-{month:02d}-01"
    end_date = f"{year}-{month:02d}-{last_day}"
    
    query = {"tanggal": {"$gte": start_date, "$lte": end_date}}
    if branch_id:
        query["branch_id"] = branch_id
    
    attendance = await attendance_col().find(query, {"_id": 0}).to_list(length=10000)
    
    # Group by employee
    employee_data = {}
    for a in attendance:
        eid = a.get("employee_id")
        if eid not in employee_data:
            employee_data[eid] = {
                "employee_id": eid,
                "employee_name": a.get("employee_name"),
                "branch_id": a.get("branch_id"),
                "branch_name": a.get("branch_name"),
                "hadir": 0,
                "telat": 0,
                "alpha": 0,
                "izin": 0,
                "cuti": 0,
                "sakit": 0,
                "total_telat_menit": 0,
                "total_lembur_jam": 0
            }
        
        status = a.get("status", "alpha")
        if status in employee_data[eid]:
            employee_data[eid][status] += 1
        employee_data[eid]["total_telat_menit"] += a.get("telat_menit", 0)
        employee_data[eid]["total_lembur_jam"] += a.get("lembur_jam", 0)
    
    # Calculate rates
    for eid, data in employee_data.items():
        total_work = data["hadir"] + data["telat"]
        data["attendance_rate"] = (total_work / last_day) * 100
        data["punctuality_rate"] = (data["hadir"] / total_work * 100) if total_work > 0 else 0
    
    report = list(employee_data.values())
    report.sort(key=lambda x: x["attendance_rate"], reverse=True)
    
    return {
        "period": f"{month}/{year}",
        "total_employees": len(report),
        "total_working_days": last_day,
        "summary": {
            "avg_attendance_rate": sum(e["attendance_rate"] for e in report) / len(report) if report else 0,
            "total_late_minutes": sum(e["total_telat_menit"] for e in report),
            "total_overtime_hours": sum(e["total_lembur_jam"] for e in report)
        },
        "employees": report
    }
