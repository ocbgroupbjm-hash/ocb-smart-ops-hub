# WAHA WhatsApp Webhook Routes
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from database import db
from services.waha_service import waha_service
from services.ai_service_ocb import OCBAIService
from models.customer import Customer
from models.conversation import Conversation, Message
import uuid
import re
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/whatsapp/waha", tags=["WAHA WhatsApp"])

# Pydantic models for WAHA
class WAHAIncomingMessage(BaseModel):
    """Incoming message from WAHA webhook"""
    event: Optional[str] = None
    session: Optional[str] = "default"
    payload: Optional[Dict[str, Any]] = None
    # Direct fields for simpler payloads
    from_: Optional[str] = None
    body: Optional[str] = None
    
    class Config:
        # Allow 'from' field
        populate_by_name = True
        
class WAHATestMessage(BaseModel):
    """Test message request"""
    phone: str
    message: str

class WAHASendMessage(BaseModel):
    """Send message request"""
    phone: str
    text: str

def normalize_phone(phone: str) -> str:
    """Normalize phone number to +62 format"""
    digits = re.sub(r'\D', '', phone)
    if digits.startswith('0'):
        digits = '62' + digits[1:]
    elif digits.startswith('8'):
        digits = '62' + digits
    elif not digits.startswith('62'):
        digits = '62' + digits
    return '+' + digits

async def process_incoming_message(phone: str, message_text: str, company_id: str = None):
    """Process incoming WhatsApp message and generate AI response"""
    
    normalized_phone = normalize_phone(phone)
    
    # Use default company for WAHA messages
    if not company_id:
        # Get first active company or create default
        company = await db.users.find_one({}, {"_id": 0, "company_id": 1})
        company_id = company.get("company_id") if company else "default-company"
    
    # Log incoming message
    log_id = str(uuid.uuid4())
    await db.whatsapp_logs.insert_one({
        "id": log_id,
        "company_id": company_id,
        "log_type": "waha_incoming",
        "phone_number": normalized_phone,
        "message": f"WAHA incoming: {message_text[:100]}...",
        "provider": "waha",
        "success": True,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    # Find or create CRM customer
    customer = await db.customers.find_one(
        {"phone": normalized_phone},
        {"_id": 0}
    )
    
    crm_auto_created = False
    if not customer:
        # Auto-create customer
        customer_name = f"WhatsApp Customer"
        
        new_customer = {
            "id": str(uuid.uuid4()),
            "company_id": company_id,
            "name": customer_name,
            "phone": normalized_phone,
            "email": None,
            "location": None,
            "segment": "regular",
            "tags": ["whatsapp", "waha", "auto-created"],
            "lifetime_value": 0.0,
            "total_orders": 0,
            "source": "whatsapp",
            "first_contact_date": datetime.now(timezone.utc).isoformat(),
            "last_message_date": datetime.now(timezone.utc).isoformat(),
            "conversation_count": 1,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.customers.insert_one(new_customer)
        customer = new_customer
        crm_auto_created = True
        
        await db.whatsapp_logs.insert_one({
            "id": str(uuid.uuid4()),
            "company_id": company_id,
            "log_type": "crm_auto_create",
            "phone_number": normalized_phone,
            "message": f"Auto-created CRM customer: {customer_name}",
            "provider": "waha",
            "success": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    else:
        # Update existing customer
        await db.customers.update_one(
            {"phone": normalized_phone},
            {
                "$set": {
                    "last_message_date": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                },
                "$inc": {"conversation_count": 1}
            }
        )
    
    customer_id = customer['id']
    
    # Find or create conversation
    conversation = await db.conversations.find_one(
        {
            "customer_phone": normalized_phone,
            "channel": "whatsapp_waha",
            "status": "active"
        },
        {"_id": 0}
    )
    
    if not conversation:
        conversation_id = str(uuid.uuid4())
        conversation = {
            "id": conversation_id,
            "company_id": company_id,
            "customer_id": customer_id,
            "customer_name": customer.get('name', 'WhatsApp Customer'),
            "customer_phone": normalized_phone,
            "agent_mode": "customer_service",
            "channel": "whatsapp_waha",
            "status": "active",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await db.conversations.insert_one(conversation)
    else:
        conversation_id = conversation['id']
    
    # Store incoming message
    incoming_msg = {
        "id": str(uuid.uuid4()),
        "company_id": company_id,
        "conversation_id": conversation_id,
        "customer_id": customer_id,
        "direction": "incoming",
        "phone_number": normalized_phone,
        "message_text": message_text,
        "provider": "waha",
        "delivery_status": "received",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await db.whatsapp_messages.insert_one(incoming_msg)
    
    # Store in messages collection for AI context
    await db.messages.insert_one({
        "id": str(uuid.uuid4()),
        "conversation_id": conversation_id,
        "role": "user",
        "content": message_text,
        "language": "id",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    # Generate AI response
    ai_response = None
    try:
        # Get knowledge base context
        knowledge_docs = await db.knowledge_base.find(
            {"company_id": company_id, "is_active": True},
            {"_id": 0}
        ).limit(5).to_list(5)
        
        knowledge_context = "\n\n".join([
            f"Info: {doc['title']}\n{doc['content'][:500]}"
            for doc in knowledge_docs
        ]) if knowledge_docs else ""
        
        # Get product context
        products = await db.products.find(
            {"company_id": company_id, "is_active": True},
            {"_id": 0}
        ).limit(10).to_list(10)
        
        product_context = "\n".join([
            f"• {p['name']}: Rp{p.get('selling_price', 0):,.0f}"
            for p in products
        ]) if products else ""
        
        # Generate AI response
        ai_service = OCBAIService(
            company_id=company_id,
            agent_mode="customer_service"
        )
        
        ai_response = await ai_service.chat(
            user_message=message_text,
            session_id=conversation_id,
            language="id",
            knowledge_context=knowledge_context,
            product_context=product_context
        )
        
        await db.whatsapp_logs.insert_one({
            "id": str(uuid.uuid4()),
            "company_id": company_id,
            "log_type": "ai_response",
            "phone_number": normalized_phone,
            "message": "AI response generated successfully",
            "provider": "waha",
            "success": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"AI generation error: {str(e)}")
        ai_response = "Halo kak! 😊 Mohon maaf, sistem sedang sibuk. Silakan coba lagi sebentar ya!"
        
        await db.whatsapp_logs.insert_one({
            "id": str(uuid.uuid4()),
            "company_id": company_id,
            "log_type": "ai_error",
            "phone_number": normalized_phone,
            "message": f"AI error: {str(e)}",
            "provider": "waha",
            "success": False,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    
    # Store AI response in messages
    await db.messages.insert_one({
        "id": str(uuid.uuid4()),
        "conversation_id": conversation_id,
        "role": "assistant",
        "content": ai_response,
        "language": "id",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    # Store outgoing message
    outgoing_msg = {
        "id": str(uuid.uuid4()),
        "company_id": company_id,
        "conversation_id": conversation_id,
        "customer_id": customer_id,
        "direction": "outgoing",
        "phone_number": normalized_phone,
        "message_text": ai_response,
        "provider": "waha",
        "delivery_status": "pending",
        "ai_mode": "customer_service",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await db.whatsapp_messages.insert_one(outgoing_msg)
    
    # Send response via WAHA
    send_result = await waha_service.send_message(normalized_phone, ai_response)
    
    # Update delivery status based on result
    if send_result.get("success"):
        await db.whatsapp_messages.update_one(
            {"id": outgoing_msg["id"]},
            {"$set": {"delivery_status": "sent"}}
        )
        
        await db.whatsapp_logs.insert_one({
            "id": str(uuid.uuid4()),
            "company_id": company_id,
            "log_type": "waha_sent",
            "phone_number": normalized_phone,
            "message": "Message sent via WAHA successfully",
            "provider": "waha",
            "success": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    else:
        error_msg = send_result.get("error", "Unknown error")
        await db.whatsapp_messages.update_one(
            {"id": outgoing_msg["id"]},
            {"$set": {"delivery_status": "waha_pending", "error": error_msg}}
        )
        
        await db.whatsapp_logs.insert_one({
            "id": str(uuid.uuid4()),
            "company_id": company_id,
            "log_type": "waha_pending",
            "phone_number": normalized_phone,
            "message": f"WAHA send pending: {error_msg}. Message queued for retry.",
            "provider": "waha",
            "success": False,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    
    return {
        "success": True,
        "conversation_id": conversation_id,
        "customer_id": customer_id,
        "crm_auto_created": crm_auto_created,
        "ai_response": ai_response,
        "waha_sent": send_result.get("success", False),
        "waha_error": send_result.get("error") if not send_result.get("success") else None
    }


@router.post("/webhook/")
async def waha_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    WAHA Webhook endpoint - receives incoming WhatsApp messages
    
    Configure WAHA to send webhooks to:
    POST https://your-domain/api/whatsapp/waha/webhook/
    """
    try:
        body = await request.json()
        logger.info(f"WAHA Webhook received: {body}")
        
        # Handle different WAHA payload formats
        phone = None
        message_text = None
        
        # Format 1: Direct fields
        if "from" in body:
            phone = body.get("from")
            message_text = body.get("body") or body.get("text") or body.get("message")
        
        # Format 2: Nested payload (WAHA event format)
        elif "payload" in body:
            payload = body.get("payload", {})
            # Handle message event
            if "from" in payload:
                phone = payload.get("from")
                message_text = payload.get("body") or payload.get("text")
            # Handle other event structures
            elif "_data" in payload:
                data = payload.get("_data", {})
                phone = data.get("from", "").replace("@c.us", "")
                message_text = data.get("body")
        
        # Format 3: Message object with 'from' containing '@c.us'
        if not phone and "message" in body:
            msg = body.get("message", {})
            phone = msg.get("from", "").replace("@c.us", "")
            message_text = msg.get("body") or msg.get("text")
        
        if not phone or not message_text:
            logger.warning(f"WAHA webhook: Could not extract phone/message from payload: {body}")
            return {"status": "ignored", "reason": "No phone or message found"}
        
        # Clean phone number
        phone = phone.replace("@c.us", "").replace("@s.whatsapp.net", "")
        
        # Process in background for fast response
        background_tasks.add_task(process_incoming_message, phone, message_text)
        
        return {"status": "accepted", "phone": phone, "message_preview": message_text[:50]}
        
    except Exception as e:
        logger.error(f"WAHA webhook error: {str(e)}")
        return {"status": "error", "error": str(e)}


@router.get("/status/")
async def get_waha_status():
    """Check WAHA connection status"""
    result = await waha_service.check_connection()
    return result


@router.post("/send/")
async def send_waha_message(data: WAHASendMessage):
    """Manually send a WhatsApp message via WAHA"""
    result = await waha_service.send_message(data.phone, data.text)
    
    if result.get("success"):
        # Log the manual message
        await db.whatsapp_logs.insert_one({
            "id": str(uuid.uuid4()),
            "company_id": "manual",
            "log_type": "manual_send",
            "phone_number": normalize_phone(data.phone),
            "message": f"Manual message sent: {data.text[:50]}...",
            "provider": "waha",
            "success": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    
    return result


@router.post("/test/")
async def test_waha_flow(data: WAHATestMessage):
    """
    Test the complete WAHA WhatsApp flow
    Simulates incoming message and sends real response
    """
    try:
        # Process like a real incoming message
        result = await process_incoming_message(data.phone, data.message)
        
        return {
            "success": True,
            "test_mode": False,
            "result": result,
            "note": "Real message was sent via WAHA"
        }
        
    except Exception as e:
        logger.error(f"WAHA test error: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/conversations/")
async def get_waha_conversations(limit: int = 50):
    """Get recent WhatsApp conversations via WAHA"""
    conversations = await db.conversations.find(
        {"channel": "whatsapp_waha"},
        {"_id": 0}
    ).sort("updated_at", -1).limit(limit).to_list(limit)
    
    return conversations


@router.get("/conversations/{conversation_id}/messages/")
async def get_conversation_messages(conversation_id: str, limit: int = 100):
    """Get messages for a specific conversation"""
    messages = await db.messages.find(
        {"conversation_id": conversation_id},
        {"_id": 0}
    ).sort("timestamp", 1).limit(limit).to_list(limit)
    
    return messages


@router.get("/messages/")
async def get_waha_messages(
    phone: Optional[str] = None,
    direction: Optional[str] = None,
    limit: int = 100
):
    """Get WhatsApp messages with optional filters"""
    query = {"provider": "waha"}
    
    if phone:
        query["phone_number"] = {"$regex": phone}
    if direction:
        query["direction"] = direction
    
    messages = await db.whatsapp_messages.find(
        query,
        {"_id": 0}
    ).sort("timestamp", -1).limit(limit).to_list(limit)
    
    return messages


@router.get("/logs/")
async def get_waha_logs(limit: int = 100):
    """Get WAHA-related system logs"""
    logs = await db.whatsapp_logs.find(
        {"provider": "waha"},
        {"_id": 0}
    ).sort("timestamp", -1).limit(limit).to_list(limit)
    
    return logs


@router.get("/customers/")
async def get_whatsapp_customers(limit: int = 50):
    """Get customers created from WhatsApp"""
    customers = await db.customers.find(
        {"source": "whatsapp"},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    return customers


class WAHAConfigUpdate(BaseModel):
    """Update WAHA configuration"""
    base_url: Optional[str] = None
    api_key: Optional[str] = None


@router.get("/config/")
async def get_waha_config():
    """Get current WAHA server configuration"""
    return {
        "base_url": waha_service.base_url,
        "api_key_set": bool(waha_service.api_key),
        "api_key_preview": waha_service.api_key[:8] + "****" if waha_service.api_key else None,
        "session": waha_service.session
    }


@router.post("/config/")
async def update_waha_config(config: WAHAConfigUpdate):
    """Update WAHA server configuration"""
    if config.base_url:
        waha_service.base_url = config.base_url.rstrip('/')
    if config.api_key:
        waha_service.api_key = config.api_key
    
    # Test the new configuration
    status = await waha_service.check_connection()
    
    return {
        "success": True,
        "base_url": waha_service.base_url,
        "api_key_preview": waha_service.api_key[:8] + "****" if waha_service.api_key else None,
        "connection_test": status
    }


@router.post("/retry-pending/")
async def retry_pending_messages():
    """Retry sending pending WAHA messages"""
    pending = await db.whatsapp_messages.find(
        {"provider": "waha", "delivery_status": {"$in": ["waha_pending", "failed"]}},
        {"_id": 0}
    ).limit(50).to_list(50)
    
    results = []
    for msg in pending:
        if msg.get("direction") == "outgoing" and msg.get("message_text"):
            send_result = await waha_service.send_message(
                msg["phone_number"], 
                msg["message_text"]
            )
            
            if send_result.get("success"):
                await db.whatsapp_messages.update_one(
                    {"id": msg["id"]},
                    {"$set": {"delivery_status": "sent"}}
                )
                results.append({"id": msg["id"], "status": "sent"})
            else:
                results.append({"id": msg["id"], "status": "failed", "error": send_result.get("error")})
    
    return {
        "pending_count": len(pending),
        "results": results
    }

