from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime, timezone
import uuid

class KnowledgeBase(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str
    title: str
    content: str
    file_type: Optional[str] = None  # pdf, txt, excel, url
    file_url: Optional[str] = None
    category: Optional[str] = None  # product, faq, policy, sop
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class KnowledgeCreate(BaseModel):
    company_id: str
    title: str
    content: str
    file_type: Optional[str] = None
    file_url: Optional[str] = None
    category: Optional[str] = None

class KnowledgeResponse(BaseModel):
    id: str
    company_id: str
    title: str
    content: str
    file_type: Optional[str] = None
    file_url: Optional[str] = None
    category: Optional[str] = None
    is_active: bool
    created_at: datetime