from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, timezone
import uuid

class CustomerBase(BaseModel):
    company_id: str
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    location: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    segment: Optional[str] = None  # vip, regular, new, at_risk
    lifetime_value: float = 0.0
    total_orders: int = 0
    last_interaction: Optional[datetime] = None
    notes: Optional[str] = None

class CustomerCreate(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    location: Optional[str] = None
    segment: Optional[str] = None
    notes: Optional[str] = None

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    location: Optional[str] = None
    tags: Optional[List[str]] = None
    segment: Optional[str] = None
    notes: Optional[str] = None

class Customer(CustomerBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CustomerResponse(BaseModel):
    id: str
    company_id: str
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    location: Optional[str] = None
    tags: List[str]
    segment: Optional[str] = None
    lifetime_value: float
    total_orders: int
    last_interaction: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime