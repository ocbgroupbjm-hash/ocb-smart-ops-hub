# WhatsApp Test Mode & Message Endpoints
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from models_ocb.whatsapp import TestMessageRequest, WhatsAppMessageResponse, WhatsAppLogResponse
from database import db
from utils.dependencies import get_current_user
from routes_ocb.whatsapp_handlers import process_incoming_whatsapp_message
from datetime import datetime

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp Integration"])

@router.post("/test-message/")
async def send_test_message(
    test_data: TestMessageRequest,
    current_user: dict = Depends(get_current_user)
):
    """Test WhatsApp message flow (no real sending)"""
    company_id = current_user.get("company_id")
    
    # Get config
    config = await db.whatsapp_integrations.find_one({"company_id": company_id}, {"_id": 0})
    
    if not config:
        raise HTTPException(
            status_code=404,
            detail="WhatsApp configuration not found. Please configure WhatsApp integration first."
        )
    
    # Process message through full flow
    result = await process_incoming_whatsapp_message(
        company_id=company_id,
        config=config,
        phone_number=test_data.phone_number,
        message_text=test_data.message_text,
        provider_message_id=f"test_{datetime.now().timestamp()}",
        customer_name=None,
        provider=test_data.provider_mode
    )
    
    return {
        "test_mode": True,
        "success": True,
        "message": "Test message processed successfully",
        "result": result,
        "note": "No actual WhatsApp message was sent (test mode)"
    }

@router.get("/messages/", response_model=List[WhatsAppMessageResponse])
async def get_whatsapp_messages(
    direction: str = None,
    phone_number: str = None,
    status: str = None,
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """Get WhatsApp messages with optional filters"""
    company_id = current_user.get("company_id")
    
    query = {"company_id": company_id}
    
    if direction:
        query["direction"] = direction
    if phone_number:
        query["phone_number"] = {"$regex": phone_number}
    if status:
        query["delivery_status"] = status
    
    messages = await db.whatsapp_messages.find(
        query,
        {"_id": 0}
    ).sort("timestamp", -1).limit(limit).to_list(limit)
    
    # Convert timestamps
    for msg in messages:
        if isinstance(msg.get('timestamp'), str):
            msg['timestamp'] = datetime.fromisoformat(msg['timestamp'])
    
    return messages

@router.get("/logs/", response_model=List[WhatsAppLogResponse])
async def get_whatsapp_logs(
    log_type: str = None,
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """Get WhatsApp logs"""
    company_id = current_user.get("company_id")
    
    query = {"company_id": company_id}
    
    if log_type:
        query["log_type"] = log_type
    
    logs = await db.whatsapp_logs.find(
        query,
        {"_id": 0}
    ).sort("timestamp", -1).limit(limit).to_list(limit)
    
    # Convert timestamps
    for log in logs:
        if isinstance(log.get('timestamp'), str):
            log['timestamp'] = datetime.fromisoformat(log['timestamp'])
    
    return logs