from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import Optional
from datetime import datetime, timezone
import uuid

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: str  # owner, regional_manager, branch_manager, staff, customer_support
    company_id: Optional[str] = None
    branch_id: Optional[str] = None
    is_active: bool = True

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: str = "staff"
    company_id: Optional[str] = None
    branch_id: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(UserBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    company_id: Optional[str] = None
    branch_id: Optional[str] = None
    is_active: bool
    created_at: datetime

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse