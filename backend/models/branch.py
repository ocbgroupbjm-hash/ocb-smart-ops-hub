from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime, timezone
import uuid

class BranchBase(BaseModel):
    company_id: str
    name: str
    location: str
    address: Optional[str] = None
    phone: Optional[str] = None
    manager_name: Optional[str] = None
    is_active: bool = True

class BranchCreate(BranchBase):
    pass

class BranchUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    manager_name: Optional[str] = None
    is_active: Optional[bool] = None

class Branch(BranchBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class BranchResponse(BaseModel):
    id: str
    company_id: str
    name: str
    location: str
    address: Optional[str] = None
    phone: Optional[str] = None
    manager_name: Optional[str] = None
    is_active: bool
    created_at: datetime