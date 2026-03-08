from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, timezone
import uuid

class CompanyBase(BaseModel):
    name: str
    industry: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    plan: str = "starter"  # starter, business, enterprise
    ai_quota: int = 10000
    ai_quota_used: int = 0

class CompanyCreate(CompanyBase):
    pass

class Company(CompanyBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CompanyResponse(BaseModel):
    id: str
    name: str
    industry: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    plan: str
    ai_quota: int
    ai_quota_used: int
    created_at: datetime