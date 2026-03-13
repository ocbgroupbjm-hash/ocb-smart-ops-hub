# OCB TITAN - Auth Routes
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from database import users, branches, audit_logs, roles
from utils.auth import hash_password, verify_password, create_token, get_current_user
from models.titan_models import User, UserRole, AuditLog
from fastapi import Depends
from datetime import datetime, timezone

router = APIRouter(prefix="/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str
    phone: str = ""
    role: str = "cashier"
    branch_id: Optional[str] = None

class AuthResponse(BaseModel):
    token: str
    user: dict

@router.post("/login", response_model=AuthResponse)
async def login(data: LoginRequest):
    print(f"[DEBUG] Login attempt for: {data.email}")
    
    user = await users.find_one({"email": data.email}, {"_id": 0})
    if not user:
        print(f"[DEBUG] User not found: {data.email}")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    print(f"[DEBUG] User found: {user.get('name')}")
    
    stored_hash = user.get("password_hash", "")
    if not stored_hash:
        # Fallback to password field for backwards compatibility
        stored_hash = user.get("password", "")
    
    print(f"[DEBUG] Hash exists: {bool(stored_hash)}")
    
    if not verify_password(data.password, stored_hash):
        print("[DEBUG] Password verification failed")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    print("[DEBUG] Password verified successfully")
    
    if not user.get("is_active", True):
        raise HTTPException(status_code=401, detail="Account disabled")
    
    # INITIALIZE DATABASE IF NEEDED
    # This ensures all master data exists before user enters the system
    try:
        from routes.database_init import ensure_database_initialized
        was_init = await ensure_database_initialized()
        if was_init:
            print("[LOGIN] Database was initialized with default data")
    except Exception as e:
        print(f"[LOGIN] Database init check error (non-fatal): {e}")
    
    # Ensure user has role_id - fix data integrity
    if not user.get("role_id"):
        role_code = user.get("role_code") or user.get("role", "cashier")
        role = await roles.find_one({"code": role_code}, {"_id": 0, "id": 1})
        if role:
            await users.update_one(
                {"id": user["id"]},
                {"$set": {"role_id": role["id"], "role_code": role_code}}
            )
            user["role_id"] = role["id"]
            print(f"[LOGIN] Fixed role_id for user {user['email']}")
    
    # Update last login
    await users.update_one(
        {"id": user["id"]},
        {"$set": {"last_login": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Get branch info
    branch = None
    if user.get("branch_id"):
        branch = await branches.find_one({"id": user["branch_id"]}, {"_id": 0, "id": 1, "name": 1, "code": 1})
    
    token_data = {
        "user_id": user["id"],
        "email": user["email"],
        "name": user["name"],
        "role": user.get("role", "cashier"),
        "branch_id": user.get("branch_id"),
        "branch_ids": user.get("branch_ids", [])
    }
    
    token = create_token(token_data)
    
    return AuthResponse(
        token=token,
        user={
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "role": user.get("role", "cashier"),
            "branch_id": user.get("branch_id"),
            "branch": branch,
            "permissions": user.get("permissions", [])
        }
    )

@router.post("/register", response_model=AuthResponse)
async def register(data: RegisterRequest):
    existing = await users.find_one({"email": data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create default branch if needed
    default_branch = await branches.find_one({"code": "HQ"}, {"_id": 0})
    if not default_branch:
        from models.titan_models import Branch
        default_branch = Branch(
            code="HQ",
            name="Headquarters",
            address="Main Office",
            is_warehouse=True
        ).model_dump()
        await branches.insert_one(default_branch)
    
    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        name=data.name,
        phone=data.phone,
        role=UserRole(data.role) if data.role in [r.value for r in UserRole] else UserRole.CASHIER,
        branch_id=data.branch_id or default_branch["id"],
        branch_ids=[data.branch_id or default_branch["id"]]
    )
    
    await users.insert_one(user.model_dump())
    
    token_data = {
        "user_id": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role.value,
        "branch_id": user.branch_id,
        "branch_ids": user.branch_ids
    }
    
    return AuthResponse(
        token=create_token(token_data),
        user={
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role.value,
            "branch_id": user.branch_id,
            "branch": {"id": default_branch["id"], "name": default_branch["name"], "code": default_branch["code"]}
        }
    )

@router.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    user_data = await users.find_one({"id": user["user_id"]}, {"_id": 0, "password_hash": 0})
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")
    
    branch = None
    if user_data.get("branch_id"):
        branch = await branches.find_one({"id": user_data["branch_id"]}, {"_id": 0, "id": 1, "name": 1, "code": 1})
    
    user_data["branch"] = branch
    return user_data
