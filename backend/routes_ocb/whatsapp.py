from fastapi import APIRouter, Depends, HTTPException, Request
from typing import List, Optional
from models_ocb.whatsapp import (
    WhatsAppConfigCreate, WhatsAppConfigResponse, WhatsAppConfig,
    TestMessageRequest
)
from database import db
from utils.dependencies import get_current_user
from datetime import datetime, timezone
import re

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp Integration"])

def normalize_phone_number(phone: str) -> str:
    """Normalize phone number to E.164 format"""
    digits = re.sub(r'\D', '', phone)
    if digits.startswith('0'):
        digits = '62' + digits[1:]
    if not digits.startswith('62'):
        digits = '62' + digits
    return '+' + digits

def mask_token(token: Optional[str]) -> Optional[str]:
    """Mask sensitive tokens for display"""
    if not token or len(token) < 8:
        return "****" if token else None
    return token[:4] + "*" * (len(token) - 8) + token[-4:]

@router.post("/config/", response_model=WhatsAppConfigResponse)
async def save_whatsapp_config(
    config_data: WhatsAppConfigCreate,
    current_user: dict = Depends(get_current_user)
):
    """Save or update WhatsApp integration configuration"""
    company_id = current_user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=400, detail="User must be associated with a company")
    
    existing = await db.whatsapp_integrations.find_one({"company_id": company_id}, {"_id": 0})
    
    if existing:
        update_data = config_data.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        await db.whatsapp_integrations.update_one(
            {"company_id": company_id},
            {"$set": update_data}
        )
        
        config = await db.whatsapp_integrations.find_one({"company_id": company_id}, {"_id": 0})
    else:
        config = WhatsAppConfig(
            company_id=company_id,
            **config_data.model_dump()
        )
        
        config_dict = config.model_dump()
        config_dict['created_at'] = config_dict['created_at'].isoformat()
        config_dict['updated_at'] = config_dict['updated_at'].isoformat()
        
        await db.whatsapp_integrations.insert_one(config_dict)
        config = config_dict
    
    if isinstance(config.get('created_at'), str):
        config['created_at'] = datetime.fromisoformat(config['created_at'])
    
    response = WhatsAppConfigResponse(
        id=config['id'],
        company_id=config['company_id'],
        provider_type=config['provider_type'],
        business_phone_number=config.get('business_phone_number'),
        phone_number_id=config.get('phone_number_id'),
        webhook_url=config.get('webhook_url'),
        verify_token=config['verify_token'],
        default_reply_mode=config['default_reply_mode'],
        language=config['language'],
        auto_reply_enabled=config['auto_reply_enabled'],
        auto_create_crm_customer=config['auto_create_crm_customer'],
        human_handoff_enabled=config['human_handoff_enabled'],
        active_status=config['active_status'],
        created_at=config['created_at'],
        api_token_masked=mask_token(config.get('api_token')),
        access_token_masked=mask_token(config.get('access_token'))
    )
    
    return response

@router.get("/config/", response_model=WhatsAppConfigResponse)
async def get_whatsapp_config(current_user: dict = Depends(get_current_user)):
    """Get WhatsApp integration configuration"""
    company_id = current_user.get("company_id")
    
    config = await db.whatsapp_integrations.find_one({"company_id": company_id}, {"_id": 0})
    
    if not config:
        raise HTTPException(status_code=404, detail="WhatsApp configuration not found")
    
    if isinstance(config.get('created_at'), str):
        config['created_at'] = datetime.fromisoformat(config['created_at'])
    
    response = WhatsAppConfigResponse(
        id=config['id'],
        company_id=config['company_id'],
        provider_type=config['provider_type'],
        business_phone_number=config.get('business_phone_number'),
        phone_number_id=config.get('phone_number_id'),
        webhook_url=config.get('webhook_url'),
        verify_token=config['verify_token'],
        default_reply_mode=config['default_reply_mode'],
        language=config['language'],
        auto_reply_enabled=config['auto_reply_enabled'],
        auto_create_crm_customer=config['auto_create_crm_customer'],
        human_handoff_enabled=config['human_handoff_enabled'],
        active_status=config['active_status'],
        created_at=config['created_at'],
        api_token_masked=mask_token(config.get('api_token')),
        access_token_masked=mask_token(config.get('access_token'))
    )
    
    return response

@router.get("/status/")
async def get_whatsapp_status(current_user: dict = Depends(get_current_user)):
    """Get WhatsApp integration status"""
    company_id = current_user.get("company_id")
    
    config = await db.whatsapp_integrations.find_one({"company_id": company_id}, {"_id": 0})
    
    if not config:
        return {
            "configured": False,
            "active": False,
            "provider": None,
            "message": "WhatsApp integration not configured"
        }
    
    has_credentials = False
    if config['provider_type'] == 'meta':
        has_credentials = bool(config.get('access_token') and config.get('phone_number_id'))
    elif config['provider_type'] == 'twilio':
        has_credentials = bool(config.get('account_sid') and config.get('auth_token'))
    elif config['provider_type'] in ['360dialog', 'custom']:
        has_credentials = bool(config.get('api_token'))
    
    return {
        "configured": True,
        "active": config['active_status'],
        "provider": config['provider_type'],
        "has_credentials": has_credentials,
        "auto_reply_enabled": config['auto_reply_enabled'],
        "message": "WhatsApp integration configured" if has_credentials else "Credentials required"
    }
