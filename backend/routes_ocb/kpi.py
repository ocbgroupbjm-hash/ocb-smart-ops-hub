from fastapi import APIRouter, Depends, HTTPException
from typing import List
from models_ocb.kpi import KPITaskCreate, KPITaskResponse, KPITask, KPITarget
from database import db
from utils.dependencies import get_current_user
from datetime import datetime, timezone

router = APIRouter(prefix="/kpi", tags=["KPI Management"])

@router.post("/tasks", response_model=KPITaskResponse)
async def create_task(task_data: KPITaskCreate, current_user: dict = Depends(get_current_user)):
    company_id = current_user.get("company_id")
    
    if not company_id:
        raise HTTPException(status_code=400, detail="User must be associated with a company")
    
    # Get employee info
    employee = await db.users.find_one({"id": task_data.employee_id, "company_id": company_id}, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    task = KPITask(
        company_id=company_id,
        employee_id=task_data.employee_id,
        employee_name=employee['full_name'],
        assigned_by=current_user['full_name'],
        title=task_data.title,
        description=task_data.description,
        due_date=task_data.due_date,
        priority=task_data.priority,
        status="pending"
    )
    
    task_dict = task.model_dump()
    task_dict['created_at'] = task_dict['created_at'].isoformat()
    
    await db.kpi_tasks.insert_one(task_dict)
    
    return KPITaskResponse(**task.model_dump())

@router.get("/tasks", response_model=List[KPITaskResponse])
async def get_tasks(
    employee_id: str = None,
    status: str = None,
    current_user: dict = Depends(get_current_user)
):
    company_id = current_user.get("company_id")
    query = {"company_id": company_id}
    
    if employee_id:
        query["employee_id"] = employee_id
    elif current_user.get('role') not in ['owner', 'regional_manager', 'branch_manager']:
        query["employee_id"] = current_user['id']
    
    if status:
        query["status"] = status
    
    tasks = await db.kpi_tasks.find(query, {"_id": 0}).sort("created_at", -1).limit(100).to_list(100)
    
    for task in tasks:
        if isinstance(task.get('created_at'), str):
            task['created_at'] = datetime.fromisoformat(task['created_at'])
        if task.get('completed_at') and isinstance(task['completed_at'], str):
            task['completed_at'] = datetime.fromisoformat(task['completed_at'])
    
    return tasks

@router.put("/tasks/{task_id}/complete")
async def complete_task(task_id: str, notes: str = None, current_user: dict = Depends(get_current_user)):
    company_id = current_user.get("company_id")
    
    task = await db.kpi_tasks.find_one({"id": task_id, "company_id": company_id}, {"_id": 0})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    now = datetime.now(timezone.utc)
    
    await db.kpi_tasks.update_one(
        {"id": task_id},
        {"$set": {
            "status": "completed",
            "completed_at": now.isoformat(),
            "completion_notes": notes
        }}
    )
    
    return {"message": "Task completed successfully"}

@router.get("/performance/{employee_id}")
async def get_employee_performance(employee_id: str, current_user: dict = Depends(get_current_user)):
    company_id = current_user.get("company_id")
    
    # Get tasks
    all_tasks = await db.kpi_tasks.find({
        "company_id": company_id,
        "employee_id": employee_id
    }, {"_id": 0}).to_list(1000)
    
    total_tasks = len(all_tasks)
    completed_tasks = len([t for t in all_tasks if t['status'] == 'completed'])
    pending_tasks = len([t for t in all_tasks if t['status'] == 'pending'])
    
    completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    # Get attendance
    from datetime import timedelta
    thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    attendance = await db.attendance.find({
        "company_id": company_id,
        "employee_id": employee_id,
        "date": {"$gte": thirty_days_ago, "$lte": today}
    }, {"_id": 0}).to_list(100)
    
    attendance_days = len(attendance)
    
    return {
        "employee_id": employee_id,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "pending_tasks": pending_tasks,
        "completion_rate": round(completion_rate, 2),
        "attendance_days_30d": attendance_days,
        "performance_score": round((completion_rate * 0.6) + (attendance_days * 3 * 0.4), 2)
    }