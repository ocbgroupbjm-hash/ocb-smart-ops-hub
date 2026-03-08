from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime, timezone, time
import uuid

class AttendanceBase(BaseModel):
    company_id: str
    branch_id: str
    employee_id: str
    employee_name: str
    date: str  # YYYY-MM-DD
    clock_in: Optional[datetime] = None
    clock_out: Optional[datetime] = None
    clock_in_location: Optional[str] = None
    clock_out_location: Optional[str] = None
    clock_in_photo: Optional[str] = None
    clock_out_photo: Optional[str] = None
    status: str = "present"  # present, absent, late, half_day
    notes: Optional[str] = None

class AttendanceClockIn(BaseModel):
    location: Optional[str] = None
    photo: Optional[str] = None

class AttendanceClockOut(BaseModel):
    location: Optional[str] = None
    photo: Optional[str] = None

class Attendance(AttendanceBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AttendanceResponse(BaseModel):
    id: str
    company_id: str
    branch_id: str
    employee_id: str
    employee_name: str
    date: str
    clock_in: Optional[datetime] = None
    clock_out: Optional[datetime] = None
    clock_in_location: Optional[str] = None
    status: str
    total_hours: Optional[float] = None