from fastapi import APIRouter, HTTPException, status
from models.user import UserCreate, UserLogin, UserResponse, TokenResponse, User
from models.company import CompanyCreate, Company
from database import users_collection, companies_collection
from utils.auth import hash_password, verify_password, create_access_token
from datetime import datetime, timezone

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    # Check if user exists
    existing_user = await users_collection.find_one({"email": user_data.email}, {"_id": 0})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create company if role is owner and no company_id provided
    company_id = user_data.company_id
    if user_data.role == "owner" and not company_id:
        company_data = CompanyCreate(
            name=f"{user_data.full_name}'s Company",
            plan="starter",
            ai_quota=10000
        )
        company = Company(**company_data.model_dump())
        company_dict = company.model_dump()
        company_dict['created_at'] = company_dict['created_at'].isoformat()
        company_dict['updated_at'] = company_dict['updated_at'].isoformat()
        await companies_collection.insert_one(company_dict)
        company_id = company.id
    
    # Create user
    hashed_password = hash_password(user_data.password)
    user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        role=user_data.role,
        company_id=company_id,
        branch_id=user_data.branch_id,
        is_active=True
    )
    
    user_dict = user.model_dump()
    user_dict['password'] = hashed_password
    user_dict['created_at'] = user_dict['created_at'].isoformat()
    user_dict['updated_at'] = user_dict['updated_at'].isoformat()
    
    await users_collection.insert_one(user_dict)
    
    # Create token
    token = create_access_token({"sub": user.id, "email": user.email, "role": user.role})
    
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            company_id=user.company_id,
            branch_id=user.branch_id,
            is_active=user.is_active,
            created_at=user.created_at
        )
    )

@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    user = await users_collection.find_one({"email": credentials.email}, {"_id": 0})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not verify_password(credentials.password, user.get("password", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not user.get("is_active", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )
    
    # Create token
    token = create_access_token({"sub": user["id"], "email": user["email"], "role": user["role"]})
    
    # Convert ISO string to datetime if needed
    created_at = user['created_at']
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at)
    
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user["id"],
            email=user["email"],
            full_name=user["full_name"],
            role=user["role"],
            company_id=user.get("company_id"),
            branch_id=user.get("branch_id"),
            is_active=user["is_active"],
            created_at=created_at
        )
    )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = None):
    from utils.dependencies import get_current_user
    from fastapi import Depends
    
    async def get_me(user: dict = Depends(get_current_user)):
        created_at = user['created_at']
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        
        return UserResponse(
            id=user["id"],
            email=user["email"],
            full_name=user["full_name"],
            role=user["role"],
            company_id=user.get("company_id"),
            branch_id=user.get("branch_id"),
            is_active=user["is_active"],
            created_at=created_at
        )
    
    return await get_me()