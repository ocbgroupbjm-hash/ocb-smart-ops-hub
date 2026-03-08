# N8N WhatsApp Webhook - Simple & Stable API for n8n Integration
# POST /api/whatsapp/incoming/
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
import uuid
import re
import logging
import time

from database import db
from services.ai_service_ocb import OCBAIService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/whatsapp", tags=["N8N WhatsApp Webhook"])


class IncomingMessage(BaseModel):
    phone_number: str
    message: str


class ReplyResponse(BaseModel):
    reply: str


def normalize_phone(phone: str) -> str:
    """Normalize phone number to international format (62xxx)"""
    digits = re.sub(r'\D', '', phone)
    
    if digits.startswith('0'):
        digits = '62' + digits[1:]
    elif digits.startswith('8'):
        digits = '62' + digits
    elif not digits.startswith('62'):
        digits = '62' + digits
    
    return digits


async def find_or_create_customer(phone: str) -> dict:
    """Find existing customer or create new one"""
    normalized_phone = normalize_phone(phone)
    
    # Try to find existing customer
    customer = await db.customers.find_one(
        {"phone": {"$regex": normalized_phone[-10:]}},
        {"_id": 0}
    )
    
    if customer:
        logger.info(f"Found existing customer: {customer.get('name', 'Unknown')} - {normalized_phone}")
        return customer
    
    # Create new customer
    new_customer = {
        "id": str(uuid.uuid4()),
        "phone": normalized_phone,
        "name": f"WA-{normalized_phone[-4:]}",
        "email": "",
        "source": "whatsapp_n8n",
        "segment": "new",
        "company_id": "default",
        "notes": "Auto-created from WhatsApp via n8n",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.customers.insert_one(new_customer)
    logger.info(f"Created new customer: {new_customer['name']} - {normalized_phone}")
    
    return new_customer


async def get_or_create_conversation(customer_id: str, phone: str) -> str:
    """Get existing conversation or create new one"""
    conversation = await db.conversations.find_one(
        {"customer_id": customer_id},
        {"_id": 0}
    )
    
    if conversation:
        # Update last message timestamp
        await db.conversations.update_one(
            {"id": conversation["id"]},
            {"$set": {"last_message_at": datetime.now(timezone.utc).isoformat()}}
        )
        return conversation["id"]
    
    # Create new conversation
    conv_id = str(uuid.uuid4())
    new_conversation = {
        "id": conv_id,
        "customer_id": customer_id,
        "phone": phone,
        "channel": "whatsapp_n8n",
        "status": "active",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_message_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.conversations.insert_one(new_conversation)
    return conv_id


async def save_message(conversation_id: str, phone: str, text: str, direction: str, ai_reply: str = None) -> str:
    """Save message to database"""
    msg_id = str(uuid.uuid4())
    
    message = {
        "id": msg_id,
        "conversation_id": conversation_id,
        "phone": phone,
        "text": text,
        "direction": direction,
        "ai_reply": ai_reply,
        "status": "processed" if direction == "incoming" else "sent",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.whatsapp_messages.insert_one(message)
    return msg_id


async def get_knowledge_context() -> str:
    """Get knowledge base content for AI context"""
    try:
        knowledge_items = await db.knowledge_base.find(
            {"is_active": True},
            {"_id": 0, "title": 1, "content": 1, "category": 1}
        ).limit(10).to_list(10)
        
        if not knowledge_items:
            return ""
        
        context_parts = []
        for item in knowledge_items:
            title = item.get("title", "")
            content = item.get("content", "")[:2000]
            if title and content:
                context_parts.append(f"[{title}]\n{content}")
        
        return "\n\n".join(context_parts)
    except Exception as e:
        logger.error(f"Error getting knowledge context: {e}")
        return ""


async def log_event(message: str, level: str = "info", event_type: str = "n8n"):
    """Log event to database"""
    log_entry = {
        "id": str(uuid.uuid4()),
        "message": message,
        "level": level,
        "type": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await db.whatsapp_logs.insert_one(log_entry)


@router.post("/incoming/", response_model=ReplyResponse)
async def handle_incoming_message(data: IncomingMessage):
    """
    Handle incoming WhatsApp message from n8n
    
    Workflow:
    1. Receive incoming message
    2. Normalize phone number
    3. Find or create CRM customer
    4. Save conversation and incoming message
    5. Use AI engine + Knowledge Base
    6. Generate reply in natural Bahasa Indonesia
    7. Return JSON response
    """
    start_time = time.time()
    
    try:
        phone = data.phone_number
        message_text = data.message
        
        if not phone or not message_text:
            raise HTTPException(status_code=400, detail="phone_number and message are required")
        
        normalized_phone = normalize_phone(phone)
        logger.info(f"[N8N] Incoming message from {normalized_phone}: {message_text[:50]}...")
        
        # Log incoming
        await log_event(f"Received message from {normalized_phone}: {message_text[:100]}", "info", "n8n_incoming")
        
        # Step 1: Find or create customer
        customer = await find_or_create_customer(phone)
        customer_id = customer.get("id")
        
        # Step 2: Get or create conversation
        conversation_id = await get_or_create_conversation(customer_id, normalized_phone)
        
        # Step 3: Save incoming message
        await save_message(conversation_id, normalized_phone, message_text, "incoming")
        
        # Step 4: Get knowledge base context
        knowledge_context = await get_knowledge_context()
        
        # Step 5: Generate AI reply
        ai_service = OCBAIService(company_id="default", agent_mode="customer_service")
        session_id = f"n8n_{normalized_phone}"
        
        ai_reply = await ai_service.chat(
            user_message=message_text,
            session_id=session_id,
            language="id",
            knowledge_context=knowledge_context
        )
        
        # Step 6: Save AI reply
        await save_message(conversation_id, normalized_phone, ai_reply, "outgoing", ai_reply)
        
        # Log success
        elapsed = time.time() - start_time
        await log_event(f"Reply generated in {elapsed:.2f}s for {normalized_phone}", "info", "n8n_reply")
        
        logger.info(f"[N8N] Reply generated in {elapsed:.2f}s: {ai_reply[:50]}...")
        
        return ReplyResponse(reply=ai_reply)
        
    except HTTPException:
        raise
    except Exception as e:
        elapsed = time.time() - start_time
        error_msg = f"Error processing message: {str(e)}"
        logger.error(f"[N8N] {error_msg}")
        await log_event(error_msg, "error", "n8n_error")
        
        # Return friendly error message in Bahasa
        return ReplyResponse(
            reply="Maaf kak, sistem kami sedang maintenance sebentar. Coba lagi ya dalam beberapa menit! 🙏"
        )


@router.get("/incoming/health")
async def health_check():
    """Health check endpoint for n8n"""
    return {
        "status": "ok",
        "service": "n8n_whatsapp_webhook",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
