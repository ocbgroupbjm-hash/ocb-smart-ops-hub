from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, timezone
import uuid

class KPITargetBase(BaseModel):
    company_id: str
    employee_id: str
    employee_name: str
    target_type: str  # sales, tasks, attendance, custom
    target_value: float
    current_value: float = 0.0
    period: str  # daily, weekly, monthly
    start_date: str
    end_date: str
    is_active: bool = True

class KPITargetCreate(KPITargetBase):
    pass

class KPITarget(KPITargetBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    achievement_percentage: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class KPITaskBase(BaseModel):
    company_id: str
    employee_id: str
    employee_name: str
    assigned_by: str
    title: str
    description: Optional[str] = None
    due_date: str
    priority: str = "medium"  # low, medium, high
    status: str = "pending"  # pending, in_progress, completed, cancelled
    completion_notes: Optional[str] = None

class KPITaskCreate(BaseModel):
    employee_id: str
    title: str
    description: Optional[str] = None
    due_date: str
    priority: str = "medium"

class KPITask(KPITaskBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

class KPITaskResponse(BaseModel):
    id: str
    employee_id: str
    employee_name: str
    assigned_by: str
    title: str
    description: Optional[str] = None
    due_date: str
    priority: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None