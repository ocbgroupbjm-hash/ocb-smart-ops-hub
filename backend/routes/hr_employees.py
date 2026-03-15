# OCB TITAN ERP - HR ENTERPRISE SYSTEM
# Blueprint: HR SUPER DUPER DEWA
# Employee Master Module - SSOT for all HR data

from fastapi import APIRouter, HTTPException, Depends, Request, Query, UploadFile, File
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, date
from database import db
from utils.auth import get_current_user
from routes.rbac_system import check_permission, log_activity
import uuid
import re
import os
import shutil

router = APIRouter(prefix="/api/hr", tags=["HR Enterprise System"])

# Collections
employees_collection = db["employees"]
departments_collection = db["departments"]
positions_collection = db["positions"]
branches_collection = db["branches"]

# ==================== PYDANTIC MODELS ====================

class DepartmentCreate(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    parent_id: Optional[str] = None
    manager_id: Optional[str] = None

class PositionCreate(BaseModel):
    name: str
    code: str
    department_id: str
    level: int = 1  # 1=Staff, 2=Supervisor, 3=Manager, 4=Director
    description: Optional[str] = None
    salary_min: float = 0
    salary_max: float = 0

class EmployeeCreate(BaseModel):
    """Employee Master - Single Source of Truth"""
    employee_id: str  # NIK Karyawan
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    
    # Employment Info
    department_id: str
    position_id: str
    branch_id: Optional[str] = None
    employment_type: str = "permanent"  # permanent, contract, probation
    join_date: str
    end_date: Optional[str] = None  # For contract employees
    
    # Personal Info
    birth_date: Optional[str] = None
    birth_place: Optional[str] = None
    gender: str = "male"  # male, female
    religion: Optional[str] = None
    marital_status: str = "single"  # single, married, divorced
    address: Optional[str] = None
    id_card_number: Optional[str] = None  # KTP
    npwp: Optional[str] = None
    
    # Payroll Info
    salary_base: float = 0
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    bank_account_name: Optional[str] = None
    
    # Emergency Contact
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relation: Optional[str] = None
    
    @validator('employee_id')
    def validate_employee_id(cls, v):
        if not v or len(v) < 3:
            raise ValueError('Employee ID minimal 3 karakter')
        return v.upper()
    
    @validator('email')
    def validate_email(cls, v):
        if v and not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', v):
            raise ValueError('Format email tidak valid')
        return v

class EmployeeUpdate(BaseModel):
    """Employee update - partial fields allowed"""
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    department_id: Optional[str] = None
    position_id: Optional[str] = None
    branch_id: Optional[str] = None
    employment_type: Optional[str] = None
    end_date: Optional[str] = None
    salary_base: Optional[float] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    bank_account_name: Optional[str] = None
    status: Optional[str] = None  # active, inactive, resigned, terminated


# ==================== DEPARTMENTS ====================

@router.post("/departments")
async def create_department(
    data: DepartmentCreate,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """Create new department"""
    user_id = user.get("user_id", user.get("id", ""))
    user_name = user.get("name", "")
    
    # Check duplicate code
    existing = await departments_collection.find_one({"code": data.code.upper()})
    if existing:
        raise HTTPException(status_code=400, detail=f"Kode department {data.code} sudah ada")
    
    department = {
        "id": str(uuid.uuid4()),
        "code": data.code.upper(),
        "name": data.name,
        "description": data.description,
        "parent_id": data.parent_id,
        "manager_id": data.manager_id,
        "is_active": True,
        "created_by": user_id,
        "created_by_name": user_name,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await departments_collection.insert_one(department)
    
    await log_activity(
        db, user_id, user_name,
        "create", "department",
        f"Department dibuat: {data.name} ({data.code})",
        request.client.host if request.client else "",
        user.get("branch_id", "")
    )
    
    return {"status": "success", "department_id": department["id"], "code": department["code"]}

@router.get("/departments")
async def get_departments(
    is_active: Optional[bool] = None,
    user: dict = Depends(get_current_user)
):
    """Get all departments"""
    query = {}
    if is_active is not None:
        query["is_active"] = is_active
    
    departments = await departments_collection.find(query, {"_id": 0}).to_list(100)
    return {"departments": departments, "count": len(departments)}


# ==================== POSITIONS ====================

@router.post("/positions")
async def create_position(
    data: PositionCreate,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """Create new position/job title"""
    user_id = user.get("user_id", user.get("id", ""))
    user_name = user.get("name", "")
    
    # Verify department exists
    dept = await departments_collection.find_one({"id": data.department_id})
    if not dept:
        raise HTTPException(status_code=404, detail="Department tidak ditemukan")
    
    position = {
        "id": str(uuid.uuid4()),
        "code": data.code.upper(),
        "name": data.name,
        "department_id": data.department_id,
        "department_name": dept.get("name", ""),
        "level": data.level,
        "description": data.description,
        "salary_min": data.salary_min,
        "salary_max": data.salary_max,
        "is_active": True,
        "created_by": user_id,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await positions_collection.insert_one(position)
    
    await log_activity(
        db, user_id, user_name,
        "create", "position",
        f"Posisi dibuat: {data.name} ({data.code})",
        request.client.host if request.client else "",
        user.get("branch_id", "")
    )
    
    return {"status": "success", "position_id": position["id"], "code": position["code"]}

@router.get("/positions")
async def get_positions(
    department_id: Optional[str] = None,
    is_active: Optional[bool] = None,
    user: dict = Depends(get_current_user)
):
    """Get all positions"""
    query = {}
    if department_id:
        query["department_id"] = department_id
    if is_active is not None:
        query["is_active"] = is_active
    
    positions = await positions_collection.find(query, {"_id": 0}).to_list(100)
    return {"positions": positions, "count": len(positions)}


# ==================== EMPLOYEES ====================

@router.post("/employees")
async def create_employee(
    data: EmployeeCreate,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """
    Create new employee - Single Source of Truth
    
    Employee Master adalah sumber kebenaran tunggal untuk:
    - Data personal karyawan
    - Data jabatan dan departemen
    - Data payroll base
    - Status kepegawaian
    """
    user_id = user.get("user_id", user.get("id", ""))
    user_name = user.get("name", "")
    
    # Check duplicate employee_id (NIK)
    existing = await employees_collection.find_one({"employee_id": data.employee_id.upper()})
    if existing:
        raise HTTPException(status_code=400, detail=f"NIK Karyawan {data.employee_id} sudah terdaftar")
    
    # Verify department
    dept = await departments_collection.find_one({"id": data.department_id})
    if not dept:
        raise HTTPException(status_code=404, detail="Department tidak ditemukan")
    
    # Verify position
    pos = await positions_collection.find_one({"id": data.position_id})
    if not pos:
        raise HTTPException(status_code=404, detail="Posisi tidak ditemukan")
    
    # Get branch info
    branch_name = ""
    if data.branch_id:
        branch = await branches_collection.find_one({"id": data.branch_id})
        branch_name = branch.get("name", "") if branch else ""
    
    employee = {
        "id": str(uuid.uuid4()),
        "employee_id": data.employee_id.upper(),  # NIK
        "full_name": data.full_name,
        "email": data.email,
        "phone": data.phone,
        
        # Employment
        "department_id": data.department_id,
        "department_name": dept.get("name", ""),
        "position_id": data.position_id,
        "position_name": pos.get("name", ""),
        "position_level": pos.get("level", 1),
        "branch_id": data.branch_id,
        "branch_name": branch_name,
        "employment_type": data.employment_type,
        "join_date": data.join_date,
        "end_date": data.end_date,
        "status": "active",
        
        # Personal
        "birth_date": data.birth_date,
        "birth_place": data.birth_place,
        "gender": data.gender,
        "religion": data.religion,
        "marital_status": data.marital_status,
        "address": data.address,
        "id_card_number": data.id_card_number,
        "npwp": data.npwp,
        
        # Payroll
        "salary_base": data.salary_base,
        "bank_name": data.bank_name,
        "bank_account": data.bank_account,
        "bank_account_name": data.bank_account_name,
        
        # Leave balances (initialized)
        "leave_balance": {
            "annual": 12,  # Cuti tahunan
            "sick": 12,    # Cuti sakit
            "maternity": 90,  # Cuti melahirkan
            "unpaid": 0
        },
        
        # Emergency Contact
        "emergency_contact": {
            "name": data.emergency_contact_name,
            "phone": data.emergency_contact_phone,
            "relation": data.emergency_contact_relation
        },
        
        # Metadata
        "created_by": user_id,
        "created_by_name": user_name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await employees_collection.insert_one(employee)
    
    # Create indexes for fast lookup
    await employees_collection.create_index("employee_id", unique=True)
    await employees_collection.create_index("department_id")
    await employees_collection.create_index("status")
    
    await log_activity(
        db, user_id, user_name,
        "create", "employee",
        f"Karyawan baru: {data.full_name} ({data.employee_id})",
        request.client.host if request.client else "",
        user.get("branch_id", "")
    )
    
    return {
        "status": "success",
        "message": f"Karyawan {data.full_name} berhasil ditambahkan",
        "employee_id": employee["employee_id"],
        "id": employee["id"]
    }


@router.get("/employees")
async def get_employees(
    status: Optional[str] = Query(None, description="active, inactive, resigned"),
    department_id: Optional[str] = None,
    branch_id: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
    user: dict = Depends(get_current_user)
):
    """Get all employees with filtering"""
    query = {}
    
    if status:
        query["status"] = status
    if department_id:
        query["department_id"] = department_id
    if branch_id:
        query["branch_id"] = branch_id
    if search:
        query["$or"] = [
            {"full_name": {"$regex": search, "$options": "i"}},
            {"employee_id": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}}
        ]
    
    skip = (page - 1) * limit
    
    employees = await employees_collection.find(
        query, 
        {"_id": 0}
    ).sort("full_name", 1).skip(skip).limit(limit).to_list(limit)
    
    total = await employees_collection.count_documents(query)
    
    return {
        "employees": employees,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit
    }


@router.get("/employees/{employee_id}")
async def get_employee(
    employee_id: str,
    user: dict = Depends(get_current_user)
):
    """Get single employee by ID or NIK"""
    employee = await employees_collection.find_one(
        {"$or": [{"id": employee_id}, {"employee_id": employee_id.upper()}]},
        {"_id": 0}
    )
    
    if not employee:
        raise HTTPException(status_code=404, detail="Karyawan tidak ditemukan")
    
    return employee


@router.put("/employees/{employee_id}")
async def update_employee(
    employee_id: str,
    data: EmployeeUpdate,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """Update employee data"""
    user_id = user.get("user_id", user.get("id", ""))
    user_name = user.get("name", "")
    
    employee = await employees_collection.find_one(
        {"$or": [{"id": employee_id}, {"employee_id": employee_id.upper()}]}
    )
    
    if not employee:
        raise HTTPException(status_code=404, detail="Karyawan tidak ditemukan")
    
    update_data = {}
    update_fields = []
    
    for field, value in data.dict(exclude_unset=True).items():
        if value is not None:
            update_data[field] = value
            update_fields.append(field)
    
    if update_data:
        # If department changed, update department_name
        if "department_id" in update_data:
            dept = await departments_collection.find_one({"id": update_data["department_id"]})
            if dept:
                update_data["department_name"] = dept.get("name", "")
        
        # If position changed, update position_name
        if "position_id" in update_data:
            pos = await positions_collection.find_one({"id": update_data["position_id"]})
            if pos:
                update_data["position_name"] = pos.get("name", "")
                update_data["position_level"] = pos.get("level", 1)
        
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        update_data["updated_by"] = user_id
        
        await employees_collection.update_one(
            {"id": employee["id"]},
            {"$set": update_data}
        )
        
        await log_activity(
            db, user_id, user_name,
            "update", "employee",
            f"Update karyawan {employee.get('full_name')}: {', '.join(update_fields)}",
            request.client.host if request.client else "",
            user.get("branch_id", "")
        )
    
    return {"status": "success", "message": "Data karyawan berhasil diupdate"}


@router.delete("/employees/{employee_id}")
async def delete_employee(
    employee_id: str,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """Soft delete employee (set status to inactive)"""
    user_id = user.get("user_id", user.get("id", ""))
    user_name = user.get("name", "")
    
    employee = await employees_collection.find_one(
        {"$or": [{"id": employee_id}, {"employee_id": employee_id.upper()}]}
    )
    
    if not employee:
        raise HTTPException(status_code=404, detail="Karyawan tidak ditemukan")
    
    # Check if employee has any linked data (payroll, attendance)
    # For now, we just soft delete
    
    await employees_collection.update_one(
        {"id": employee["id"]},
        {"$set": {
            "status": "inactive",
            "deleted_at": datetime.now(timezone.utc).isoformat(),
            "deleted_by": user_id,
            "is_deleted": True
        }}
    )
    
    await log_activity(
        db, user_id, user_name,
        "delete", "employee",
        f"Karyawan dinonaktifkan: {employee.get('full_name')} ({employee.get('employee_id')})",
        request.client.host if request.client else "",
        user.get("branch_id", "")
    )
    
    return {"status": "success", "message": "Karyawan berhasil dinonaktifkan"}


# ==================== STATISTICS ====================

@router.get("/statistics")
async def get_hr_statistics(user: dict = Depends(get_current_user)):
    """Get HR dashboard statistics"""
    
    total_employees = await employees_collection.count_documents({"status": "active"})
    total_departments = await departments_collection.count_documents({"is_active": True})
    total_positions = await positions_collection.count_documents({"is_active": True})
    
    # By employment type
    permanent = await employees_collection.count_documents({"status": "active", "employment_type": "permanent"})
    contract = await employees_collection.count_documents({"status": "active", "employment_type": "contract"})
    probation = await employees_collection.count_documents({"status": "active", "employment_type": "probation"})
    
    # By department
    dept_stats = await employees_collection.aggregate([
        {"$match": {"status": "active"}},
        {"$group": {
            "_id": "$department_name",
            "count": {"$sum": 1}
        }},
        {"$sort": {"count": -1}}
    ]).to_list(20)
    
    return {
        "summary": {
            "total_employees": total_employees,
            "total_departments": total_departments,
            "total_positions": total_positions
        },
        "by_employment_type": {
            "permanent": permanent,
            "contract": contract,
            "probation": probation
        },
        "by_department": dept_stats
    }


# ==================== DOCUMENT UPLOAD ====================

UPLOAD_DIR = "/app/backend/uploads/documents/employees"
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

@router.post("/employees/{employee_id}/documents")
async def upload_employee_document(
    employee_id: str,
    document_type: str = Query(..., description="ktp, npwp, contract, photo, other"),
    file: UploadFile = File(...),
    request: Request = None,
    user: dict = Depends(get_current_user)
):
    """
    Upload employee document
    Supported types: ktp, npwp, contract, photo, other
    Allowed formats: jpg, jpeg, png, pdf
    Max size: 5MB
    """
    user_id = user.get("user_id", user.get("id", ""))
    user_name = user.get("name", "")
    
    # Validate employee exists
    employee = await employees_collection.find_one({"id": employee_id})
    if not employee:
        raise HTTPException(status_code=404, detail="Karyawan tidak ditemukan")
    
    # Validate document type
    valid_types = ["ktp", "npwp", "contract", "photo", "other"]
    if document_type.lower() not in valid_types:
        raise HTTPException(status_code=400, detail=f"Document type harus salah satu dari: {', '.join(valid_types)}")
    
    # Validate file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Format file tidak didukung. Gunakan: {', '.join(ALLOWED_EXTENSIONS)}")
    
    # Check file size
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Ukuran file melebihi 5MB")
    
    # Create directory if not exists
    employee_dir = os.path.join(UPLOAD_DIR, employee_id)
    os.makedirs(employee_dir, exist_ok=True)
    
    # Generate unique filename
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"{document_type}_{timestamp}{file_ext}"
    filepath = os.path.join(employee_dir, filename)
    
    # Save file
    with open(filepath, "wb") as f:
        f.write(contents)
    
    # Update employee documents
    document_info = {
        "id": str(uuid.uuid4()),
        "type": document_type.lower(),
        "filename": filename,
        "original_filename": file.filename,
        "path": filepath,
        "size": len(contents),
        "uploaded_by": user_id,
        "uploaded_by_name": user_name,
        "uploaded_at": datetime.now(timezone.utc).isoformat()
    }
    
    await employees_collection.update_one(
        {"id": employee_id},
        {"$push": {"documents": document_info}}
    )
    
    # Audit log
    await log_activity(
        db, user_id, user_name,
        "upload_document", "employee",
        f"Document {document_type} uploaded for {employee.get('name', employee_id)}",
        request.client.host if request and request.client else "",
        user.get("branch_id", "")
    )
    
    return {
        "status": "success",
        "message": f"Dokumen {document_type} berhasil diupload",
        "document": document_info
    }

@router.get("/employees/{employee_id}/documents")
async def get_employee_documents(
    employee_id: str,
    user: dict = Depends(get_current_user)
):
    """Get all documents for an employee"""
    employee = await employees_collection.find_one({"id": employee_id}, {"_id": 0, "documents": 1})
    if not employee:
        raise HTTPException(status_code=404, detail="Karyawan tidak ditemukan")
    
    documents = employee.get("documents", [])
    return {"documents": documents, "total": len(documents)}

@router.delete("/employees/{employee_id}/documents/{document_id}")
async def delete_employee_document(
    employee_id: str,
    document_id: str,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """Delete an employee document"""
    user_id = user.get("user_id", user.get("id", ""))
    user_name = user.get("name", "")
    
    employee = await employees_collection.find_one({"id": employee_id})
    if not employee:
        raise HTTPException(status_code=404, detail="Karyawan tidak ditemukan")
    
    # Find document
    documents = employee.get("documents", [])
    doc_to_delete = next((d for d in documents if d.get("id") == document_id), None)
    
    if not doc_to_delete:
        raise HTTPException(status_code=404, detail="Dokumen tidak ditemukan")
    
    # Delete file from disk
    filepath = doc_to_delete.get("path")
    if filepath and os.path.exists(filepath):
        os.remove(filepath)
    
    # Remove from database
    await employees_collection.update_one(
        {"id": employee_id},
        {"$pull": {"documents": {"id": document_id}}}
    )
    
    # Audit log
    await log_activity(
        db, user_id, user_name,
        "delete_document", "employee",
        f"Document {doc_to_delete.get('type')} deleted for {employee.get('name', employee_id)}",
        request.client.host if request.client else "",
        user.get("branch_id", "")
    )
    
    return {"status": "success", "message": "Dokumen berhasil dihapus"}


# ==================== EMPLOYEE TYPE CONSTANTS ====================

EMPLOYEE_TYPES = ["permanent", "contract", "probation", "freelance"]
EMPLOYEE_STATUS = ["active", "inactive", "resigned", "terminated"]

@router.get("/employee-types")
async def get_employee_types():
    """Get list of employee types"""
    return {
        "types": [
            {"code": "permanent", "name": "Karyawan Tetap"},
            {"code": "contract", "name": "Karyawan Kontrak"},
            {"code": "probation", "name": "Masa Percobaan"},
            {"code": "freelance", "name": "Freelance"}
        ]
    }

@router.get("/employee-status-types")
async def get_employee_status_types():
    """Get list of employee status"""
    return {
        "statuses": [
            {"code": "active", "name": "Aktif"},
            {"code": "inactive", "name": "Tidak Aktif"},
            {"code": "resigned", "name": "Mengundurkan Diri"},
            {"code": "terminated", "name": "Diberhentikan"}
        ]
    }
