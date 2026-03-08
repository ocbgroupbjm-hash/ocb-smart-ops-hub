from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import uuid

# WhatsApp Integration Configuration
class WhatsAppConfigBase(BaseModel):
    company_id: str
    provider_type: str  # meta, twilio, 360dialog, custom, baileys
    business_phone_number: Optional[str] = None
    phone_number_id: Optional[str] = None
    business_account_id: Optional[str] = None
    api_token: Optional[str] = None
    access_token: Optional[str] = None
    account_sid: Optional[str] = None
    auth_token: Optional[str] = None
    webhook_url: Optional[str] = None
    verify_token: str = Field(default_factory=lambda: str(uuid.uuid4())[:16])
    default_reply_mode: str = "customer_service"  # customer_service, sales, marketing
    language: str = "id"
    auto_reply_enabled: bool = True
    auto_create_crm_customer: bool = True
    human_handoff_enabled: bool = False
    fallback_when_ai_fails: Optional[str] = "Mohon maaf, saat ini sistem sedang sibuk. Mohon tunggu sebentar."
    active_status: bool = False

class WhatsAppConfigCreate(BaseModel):
    provider_type: str
    business_phone_number: Optional[str] = None
    phone_number_id: Optional[str] = None
    business_account_id: Optional[str] = None
    api_token: Optional[str] = None
    access_token: Optional[str] = None
    account_sid: Optional[str] = None
    auth_token: Optional[str] = None
    default_reply_mode: str = "customer_service"
    language: str = "id"
    auto_reply_enabled: bool = True
    auto_create_crm_customer: bool = True
    human_handoff_enabled: bool = False
    fallback_when_ai_fails: Optional[str] = None
    active_status: bool = False

class WhatsAppConfig(WhatsAppConfigBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class WhatsAppConfigResponse(BaseModel):
    id: str
    company_id: str
    provider_type: str
    business_phone_number: Optional[str] = None
    phone_number_id: Optional[str] = None
    webhook_url: Optional[str] = None
    verify_token: str
    default_reply_mode: str
    language: str
    auto_reply_enabled: bool
    auto_create_crm_customer: bool
    human_handoff_enabled: bool
    active_status: bool
    created_at: datetime
    # Masked sensitive fields
    api_token_masked: Optional[str] = None
    access_token_masked: Optional[str] = None

# WhatsApp Messages
class WhatsAppMessageBase(BaseModel):
    company_id: str
    config_id: str
    conversation_id: Optional[str] = None
    customer_id: Optional[str] = None
    direction: str  # incoming, outgoing
    phone_number: str
    message_text: Optional[str] = None
    message_type: str = "text"  # text, image, audio, video, document
    provider_message_id: Optional[str] = None
    provider_type: str
    delivery_status: str = "pending"  # pending, sent, delivered, read, failed
    error_message: Optional[str] = None
    ai_mode_used: Optional[str] = None
    crm_auto_created: bool = False
    needs_human_handoff: bool = False
    handoff_reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class WhatsAppMessage(WhatsAppMessageBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class WhatsAppMessageResponse(BaseModel):
    id: str
    company_id: str
    direction: str
    phone_number: str
    message_text: Optional[str] = None
    delivery_status: str
    ai_mode_used: Optional[str] = None
    crm_auto_created: bool
    needs_human_handoff: bool
    timestamp: datetime

# WhatsApp Logs
class WhatsAppLogBase(BaseModel):
    company_id: str
    config_id: str
    log_type: str  # webhook, send, error, test
    phone_number: Optional[str] = None
    message: str
    details: Optional[Dict[str, Any]] = None
    success: bool = True

class WhatsAppLog(WhatsAppLogBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class WhatsAppLogResponse(BaseModel):
    id: str
    log_type: str
    phone_number: Optional[str] = None
    message: str
    success: bool
    timestamp: datetime

# Test Message Request
class TestMessageRequest(BaseModel):
    phone_number: str
    message_text: str
    provider_mode: str = "test"

# Webhook Incoming Message
class IncomingWebhookMessage(BaseModel):
    provider: str
    phone_number: str
    message_text: str
    message_id: Optional[str] = None
    customer_name: Optional[str] = None
    timestamp: Optional[str] = None
    raw_payload: Optional[Dict[str, Any]] = None