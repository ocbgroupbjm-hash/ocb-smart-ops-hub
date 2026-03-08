from fastapi import APIRouter, Depends, HTTPException
from typing import List
from models_ocb.attendance import AttendanceClockIn, AttendanceClockOut, AttendanceResponse, Attendance
from database import db
from utils.dependencies import get_current_user
from datetime import datetime, timezone

router = APIRouter(prefix="/attendance", tags=["Employee Attendance"])

@router.post("/clock-in", response_model=AttendanceResponse)
async def clock_in(clock_in_data: AttendanceClockIn, current_user: dict = Depends(get_current_user)):
    company_id = current_user.get("company_id")
    branch_id = current_user.get("branch_id")
    employee_id = current_user.get("id")
    employee_name = current_user.get("full_name")
    
    if not company_id:
        raise HTTPException(status_code=400, detail="User must be associated with a company")
    
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Check if already clocked in today
    existing = await db.attendance.find_one({
        "company_id": company_id,
        "employee_id": employee_id,
        "date": today
    }, {"_id": 0})
    
    if existing and existing.get('clock_in'):
        raise HTTPException(status_code=400, detail="Already clocked in today")
    
    now = datetime.now(timezone.utc)
    
    attendance = Attendance(
        company_id=company_id,
        branch_id=branch_id or "",
        employee_id=employee_id,
        employee_name=employee_name,
        date=today,
        clock_in=now,
        clock_in_location=clock_in_data.location,
        clock_in_photo=clock_in_data.photo,
        status="present"
    )
    
    attendance_dict = attendance.model_dump()
    attendance_dict['created_at'] = attendance_dict['created_at'].isoformat()
    if attendance_dict.get('clock_in'):
        attendance_dict['clock_in'] = attendance_dict['clock_in'].isoformat()
    
    await db.attendance.insert_one(attendance_dict)
    
    return AttendanceResponse(**attendance.model_dump(), total_hours=None)

@router.post("/clock-out", response_model=AttendanceResponse)
async def clock_out(clock_out_data: AttendanceClockOut, current_user: dict = Depends(get_current_user)):
    company_id = current_user.get("company_id")
    employee_id = current_user.get("id")
    
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    attendance = await db.attendance.find_one({
        "company_id": company_id,
        "employee_id": employee_id,
        "date": today
    }, {"_id": 0})
    
    if not attendance:
        raise HTTPException(status_code=404, detail="No clock-in record found for today")
    
    if attendance.get('clock_out'):
        raise HTTPException(status_code=400, detail="Already clocked out today")
    
    now = datetime.now(timezone.utc)
    
    await db.attendance.update_one(
        {"id": attendance['id']},
        {"$set": {
            "clock_out": now.isoformat(),
            "clock_out_location": clock_out_data.location,
            "clock_out_photo": clock_out_data.photo
        }}
    )
    
    updated = await db.attendance.find_one({"id": attendance['id']}, {"_id": 0})
    
    if isinstance(updated.get('clock_in'), str):
        updated['clock_in'] = datetime.fromisoformat(updated['clock_in'])
    if isinstance(updated.get('clock_out'), str):
        updated['clock_out'] = datetime.fromisoformat(updated['clock_out'])
    if isinstance(updated.get('created_at'), str):
        updated['created_at'] = datetime.fromisoformat(updated['created_at'])
    
    total_hours = None
    if updated.get('clock_in') and updated.get('clock_out'):
        delta = updated['clock_out'] - updated['clock_in']
        total_hours = delta.total_seconds() / 3600
    
    return AttendanceResponse(**updated, total_hours=total_hours)

@router.get("/", response_model=List[AttendanceResponse])
async def get_attendance(
    employee_id: str = None,
    branch_id: str = None,
    date_from: str = None,
    date_to: str = None,
    current_user: dict = Depends(get_current_user)
):
    company_id = current_user.get("company_id")
    query = {"company_id": company_id}
    
    if employee_id:
        query["employee_id"] = employee_id
    
    if branch_id:
        query["branch_id"] = branch_id
    
    if date_from and date_to:
        query["date"] = {"$gte": date_from, "$lte": date_to}
    
    attendances = await db.attendance.find(query, {"_id": 0}).sort("date", -1).limit(200).to_list(200)
    
    result = []
    for att in attendances:
        if isinstance(att.get('clock_in'), str):
            att['clock_in'] = datetime.fromisoformat(att['clock_in'])
        if isinstance(att.get('clock_out'), str):
            att['clock_out'] = datetime.fromisoformat(att['clock_out'])
        if isinstance(att.get('created_at'), str):
            att['created_at'] = datetime.fromisoformat(att['created_at'])
        
        total_hours = None
        if att.get('clock_in') and att.get('clock_out'):
            delta = att['clock_out'] - att['clock_in']
            total_hours = delta.total_seconds() / 3600
        
        result.append(AttendanceResponse(**att, total_hours=total_hours))
    
    return result

@router.get("/today")
async def get_today_attendance(current_user: dict = Depends(get_current_user)):
    company_id = current_user.get("company_id")
    employee_id = current_user.get("id")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    attendance = await db.attendance.find_one({
        "company_id": company_id,
        "employee_id": employee_id,
        "date": today
    }, {"_id": 0})
    
    if not attendance:
        return {"clocked_in": False, "clocked_out": False}
    
    return {
        "clocked_in": bool(attendance.get('clock_in')),
        "clocked_out": bool(attendance.get('clock_out')),
        "clock_in_time": attendance.get('clock_in'),
        "clock_out_time": attendance.get('clock_out')
    }