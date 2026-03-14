# OCB TITAN ERP - HR LEAVE MANAGEMENT
# Pengajuan cuti dengan approval workflow

from fastapi import APIRouter, HTTPException, Depends, Request, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from database import db
from utils.auth import get_current_user
from routes.rbac_system import log_activity
import uuid

router = APIRouter(prefix="/api/hr/leave", tags=["HR Leave Management"])

# Collections
leave_requests = db["leave_requests"]
leave_types = db["leave_types"]
employees = db["employees"]

# ==================== PYDANTIC MODELS ====================

class LeaveTypeCreate(BaseModel):
    name: str
    code: str
    max_days: int = 12
    is_paid: bool = True
    requires_approval: bool = True
    description: Optional[str] = None

class LeaveRequestCreate(BaseModel):
    employee_id: str
    leave_type_id: str
    start_date: str
    end_date: str
    reason: str
    notes: Optional[str] = None
    attachment_url: Optional[str] = None  # For sick leave medical certificate
    delegate_to: Optional[str] = None  # Employee ID of delegate

class LeaveApprovalRequest(BaseModel):
    status: str  # approved, rejected
    notes: Optional[str] = None


# ==================== LEAVE TYPES ====================

@router.post("/types")
async def create_leave_type(
    data: LeaveTypeCreate,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """Create leave type"""
    user_id = user.get("user_id", user.get("id", ""))
    
    existing = await leave_types.find_one({"code": data.code.upper()})
    if existing:
        raise HTTPException(status_code=400, detail=f"Kode cuti {data.code} sudah ada")
    
    leave_type = {
        "id": str(uuid.uuid4()),
        "code": data.code.upper(),
        "name": data.name,
        "max_days": data.max_days,
        "is_paid": data.is_paid,
        "requires_approval": data.requires_approval,
        "description": data.description,
        "is_active": True,
        "created_by": user_id,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await leave_types.insert_one(leave_type)
    
    return {"status": "success", "leave_type_id": leave_type["id"]}

@router.get("/types")
async def get_leave_types(user: dict = Depends(get_current_user)):
    """Get all leave types"""
    types = await leave_types.find({"is_active": True}, {"_id": 0}).to_list(20)
    return {"leave_types": types}


# ==================== LEAVE REQUESTS ====================

def calculate_leave_days(start_date: str, end_date: str) -> int:
    """Calculate number of leave days (excluding weekends)"""
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    
    days = 0
    current = start
    while current <= end:
        if current.weekday() < 5:  # Monday to Friday
            days += 1
        current += timedelta(days=1)
    
    return days


@router.post("/requests")
async def create_leave_request(
    data: LeaveRequestCreate,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """
    Submit leave request
    
    Business Rules:
    - Check leave balance
    - No overlapping leave
    - Auto-approval for certain types
    """
    user_id = user.get("user_id", user.get("id", ""))
    user_name = user.get("name", "")
    
    # Find employee
    employee = await employees.find_one(
        {"$or": [{"id": data.employee_id}, {"employee_id": data.employee_id.upper()}]},
        {"_id": 0}
    )
    
    if not employee:
        raise HTTPException(status_code=404, detail="Karyawan tidak ditemukan")
    
    # Get leave type
    leave_type = await leave_types.find_one({"id": data.leave_type_id}, {"_id": 0})
    if not leave_type:
        raise HTTPException(status_code=404, detail="Jenis cuti tidak ditemukan")
    
    # Calculate leave days
    leave_days = calculate_leave_days(data.start_date, data.end_date)
    
    if leave_days <= 0:
        raise HTTPException(status_code=400, detail="Tanggal cuti tidak valid")
    
    # Check leave balance
    leave_balance = employee.get("leave_balance", {})
    leave_code = leave_type.get("code", "ANNUAL").lower()
    
    # Map code to balance key
    balance_map = {
        "annual": "annual",
        "sick": "sick",
        "maternity": "maternity",
        "unpaid": "unpaid"
    }
    
    balance_key = balance_map.get(leave_code, "annual")
    current_balance = leave_balance.get(balance_key, 0)
    
    if leave_type.get("is_paid") and leave_days > current_balance:
        raise HTTPException(
            status_code=400, 
            detail=f"Sisa cuti tidak mencukupi. Saldo: {current_balance} hari, Pengajuan: {leave_days} hari"
        )
    
    # Check overlapping leave
    existing = await leave_requests.find_one({
        "employee_id": employee["id"],
        "status": {"$in": ["pending", "approved"]},
        "$or": [
            {"start_date": {"$lte": data.end_date, "$gte": data.start_date}},
            {"end_date": {"$lte": data.end_date, "$gte": data.start_date}},
            {"$and": [
                {"start_date": {"$lte": data.start_date}},
                {"end_date": {"$gte": data.end_date}}
            ]}
        ]
    })
    
    if existing:
        raise HTTPException(
            status_code=400, 
            detail=f"Sudah ada pengajuan cuti yang overlap pada tanggal tersebut"
        )
    
    # Generate request number
    from utils.number_generator import generate_transaction_number
    request_no = await generate_transaction_number(db, "LV")
    
    # Create leave request
    leave_request = {
        "id": str(uuid.uuid4()),
        "request_no": request_no,
        "employee_id": employee["id"],
        "employee_nik": employee.get("employee_id"),
        "employee_name": employee.get("full_name"),
        "department_id": employee.get("department_id"),
        "department_name": employee.get("department_name"),
        "branch_id": employee.get("branch_id"),
        
        "leave_type_id": data.leave_type_id,
        "leave_type_name": leave_type.get("name"),
        "leave_type_code": leave_type.get("code"),
        
        "start_date": data.start_date,
        "end_date": data.end_date,
        "total_days": leave_days,
        
        "reason": data.reason,
        "notes": data.notes,
        "attachment_url": data.attachment_url,
        "delegate_to": data.delegate_to,
        
        "status": "pending",  # pending, approved, rejected, cancelled
        "approved_by": None,
        "approved_by_name": None,
        "approved_at": None,
        "approval_notes": None,
        
        "created_by": user_id,
        "created_by_name": user_name,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Auto-approve if leave type doesn't require approval
    if not leave_type.get("requires_approval"):
        leave_request["status"] = "approved"
        leave_request["approved_at"] = datetime.now(timezone.utc).isoformat()
        leave_request["approval_notes"] = "Auto-approved"
    
    await leave_requests.insert_one(leave_request)
    
    await log_activity(
        db, user_id, user_name,
        "create", "leave_request",
        f"Pengajuan cuti {leave_type.get('name')}: {employee.get('full_name')} ({leave_days} hari)",
        request.client.host if request.client else "",
        user.get("branch_id", "")
    )
    
    return {
        "status": "success",
        "message": f"Pengajuan cuti berhasil disubmit",
        "request_no": request_no,
        "leave_days": leave_days,
        "approval_status": leave_request["status"]
    }


@router.get("/requests")
async def get_leave_requests(
    status: Optional[str] = None,  # pending, approved, rejected, cancelled
    employee_id: Optional[str] = None,
    department_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
    user: dict = Depends(get_current_user)
):
    """Get leave requests with filtering"""
    query = {}
    
    if status:
        query["status"] = status
    if employee_id:
        employee = await employees.find_one(
            {"$or": [{"id": employee_id}, {"employee_id": employee_id.upper()}]},
            {"_id": 0}
        )
        if employee:
            query["employee_id"] = employee["id"]
    if department_id:
        query["department_id"] = department_id
    if start_date:
        query["start_date"] = {"$gte": start_date}
    if end_date:
        if "start_date" in query:
            query["start_date"]["$lte"] = end_date
        else:
            query["start_date"] = {"$lte": end_date}
    
    skip = (page - 1) * limit
    
    requests = await leave_requests.find(
        query, {"_id": 0}
    ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    total = await leave_requests.count_documents(query)
    
    return {
        "requests": requests,
        "total": total,
        "page": page,
        "limit": limit
    }


@router.get("/requests/{request_id}")
async def get_leave_request(
    request_id: str,
    user: dict = Depends(get_current_user)
):
    """Get single leave request"""
    leave = await leave_requests.find_one(
        {"$or": [{"id": request_id}, {"request_no": request_id}]},
        {"_id": 0}
    )
    
    if not leave:
        raise HTTPException(status_code=404, detail="Pengajuan cuti tidak ditemukan")
    
    return leave


@router.put("/requests/{request_id}/approve")
async def approve_leave_request(
    request_id: str,
    data: LeaveApprovalRequest,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """
    Approve or reject leave request
    
    Business Rules:
    - Only pending requests can be processed
    - Update leave balance on approval
    - Send notification (future)
    """
    user_id = user.get("user_id", user.get("id", ""))
    user_name = user.get("name", "")
    
    leave = await leave_requests.find_one(
        {"$or": [{"id": request_id}, {"request_no": request_id}]}
    )
    
    if not leave:
        raise HTTPException(status_code=404, detail="Pengajuan cuti tidak ditemukan")
    
    if leave.get("status") != "pending":
        raise HTTPException(status_code=400, detail=f"Pengajuan sudah {leave.get('status')}")
    
    if data.status not in ["approved", "rejected"]:
        raise HTTPException(status_code=400, detail="Status harus 'approved' atau 'rejected'")
    
    # Update request
    update_data = {
        "status": data.status,
        "approved_by": user_id,
        "approved_by_name": user_name,
        "approved_at": datetime.now(timezone.utc).isoformat(),
        "approval_notes": data.notes
    }
    
    await leave_requests.update_one(
        {"id": leave["id"]},
        {"$set": update_data}
    )
    
    # If approved, deduct leave balance
    if data.status == "approved":
        leave_type = await leave_types.find_one({"id": leave.get("leave_type_id")}, {"_id": 0})
        
        if leave_type and leave_type.get("is_paid"):
            leave_code = leave_type.get("code", "ANNUAL").lower()
            balance_map = {"annual": "annual", "sick": "sick", "maternity": "maternity", "unpaid": "unpaid"}
            balance_key = balance_map.get(leave_code, "annual")
            
            await employees.update_one(
                {"id": leave.get("employee_id")},
                {"$inc": {f"leave_balance.{balance_key}": -leave.get("total_days", 0)}}
            )
    
    await log_activity(
        db, user_id, user_name,
        "approve" if data.status == "approved" else "reject", "leave_request",
        f"Cuti {data.status}: {leave.get('employee_name')} - {leave.get('leave_type_name')}",
        request.client.host if request.client else "",
        user.get("branch_id", "")
    )
    
    return {
        "status": "success",
        "message": f"Pengajuan cuti {data.status}",
        "request_no": leave.get("request_no")
    }


@router.put("/requests/{request_id}/cancel")
async def cancel_leave_request(
    request_id: str,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """Cancel leave request (only by requester, only if pending)"""
    user_id = user.get("user_id", user.get("id", ""))
    user_name = user.get("name", "")
    
    leave = await leave_requests.find_one(
        {"$or": [{"id": request_id}, {"request_no": request_id}]}
    )
    
    if not leave:
        raise HTTPException(status_code=404, detail="Pengajuan cuti tidak ditemukan")
    
    if leave.get("status") != "pending":
        raise HTTPException(status_code=400, detail="Hanya pengajuan pending yang bisa dibatalkan")
    
    await leave_requests.update_one(
        {"id": leave["id"]},
        {"$set": {
            "status": "cancelled",
            "cancelled_by": user_id,
            "cancelled_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    await log_activity(
        db, user_id, user_name,
        "cancel", "leave_request",
        f"Cuti dibatalkan: {leave.get('employee_name')}",
        request.client.host if request.client else "",
        user.get("branch_id", "")
    )
    
    return {"status": "success", "message": "Pengajuan cuti dibatalkan"}


@router.get("/balance/{employee_id}")
async def get_leave_balance(
    employee_id: str,
    user: dict = Depends(get_current_user)
):
    """Get employee leave balance"""
    employee = await employees.find_one(
        {"$or": [{"id": employee_id}, {"employee_id": employee_id.upper()}]},
        {"_id": 0}
    )
    
    if not employee:
        raise HTTPException(status_code=404, detail="Karyawan tidak ditemukan")
    
    leave_balance = employee.get("leave_balance", {})
    
    # Get pending leaves
    pending = await leave_requests.find({
        "employee_id": employee["id"],
        "status": "pending"
    }, {"_id": 0}).to_list(20)
    
    pending_days = sum(l.get("total_days", 0) for l in pending)
    
    return {
        "employee_id": employee.get("employee_id"),
        "employee_name": employee.get("full_name"),
        "balance": {
            "annual": leave_balance.get("annual", 0),
            "sick": leave_balance.get("sick", 0),
            "maternity": leave_balance.get("maternity", 0),
            "unpaid": leave_balance.get("unpaid", 0)
        },
        "pending_requests": len(pending),
        "pending_days": pending_days
    }
