from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, timezone
import uuid

class MessageBase(BaseModel):
    conversation_id: str
    role: str  # user, assistant, system
    content: str
    language: Optional[str] = "en"

class MessageCreate(MessageBase):
    pass

class Message(MessageBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    language: Optional[str] = None
    timestamp: datetime

class ConversationBase(BaseModel):
    company_id: str
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    agent_mode: str  # customer_service, sales, marketing
    channel: str  # whatsapp, instagram, telegram, webchat
    status: str = "active"  # active, closed, escalated
    sentiment: Optional[str] = None  # positive, neutral, negative

class ConversationCreate(ConversationBase):
    pass

class Conversation(ConversationBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ConversationResponse(BaseModel):
    id: str
    company_id: str
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    agent_mode: str
    channel: str
    status: str
    sentiment: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class ConversationWithMessages(ConversationResponse):
    messages: List[MessageResponse] = []