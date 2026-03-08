# WhatsApp Integration - Message Handlers
from fastapi import HTTPException
from models_ocb.whatsapp import WhatsAppMessage, WhatsAppLog, TestMessageRequest
from models.customer import Customer
from models.conversation import Conversation, Message
from database import db
from services.ai_service_ocb import OCBAIService
from datetime import datetime, timezone
import re
import uuid

def normalize_phone_number(phone: str) -> str:
    """Normalize phone number"""
    digits = re.sub(r'\D', '', phone)
    if digits.startswith('0'):
        digits = '62' + digits[1:]
    if not digits.startswith('62'):
        digits = '62' + digits
    return '+' + digits

async def process_incoming_whatsapp_message(
    company_id: str,
    config: dict,
    phone_number: str,
    message_text: str,
    provider_message_id: str = None,
    customer_name: str = None,
    provider: str = "test"
) -> dict:
    """Process incoming WhatsApp message and generate AI reply"""
    
    # Normalize phone
    normalized_phone = normalize_phone_number(phone_number)
    
    # Log incoming message
    await db.whatsapp_logs.insert_one({
        "id": str(uuid.uuid4()),
        "company_id": company_id,
        "config_id": config['id'],
        "log_type": "webhook",
        "phone_number": normalized_phone,
        "message": f"Incoming message: {message_text[:50]}...",
        "details": {"provider": provider, "message_id": provider_message_id},
        "success": True,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    # Find or create CRM customer
    customer = await db.customers.find_one(
        {"company_id": company_id, "phone": normalized_phone},
        {"_id": 0}
    )
    
    crm_auto_created = False
    if not customer and config.get('auto_create_crm_customer', True):
        # Auto-create CRM customer
        customer_name = customer_name or f"WhatsApp {normalized_phone[-6:]}"
        
        new_customer = Customer(
            company_id=company_id,
            name=customer_name,
            phone=normalized_phone,
            segment="regular",
            tags=["whatsapp", "auto-created"],
            lifetime_value=0.0,
            total_orders=0
        )
        
        customer_dict = new_customer.model_dump()
        customer_dict['created_at'] = customer_dict['created_at'].isoformat()
        customer_dict['updated_at'] = customer_dict['updated_at'].isoformat()
        
        await db.customers.insert_one(customer_dict)
        customer = customer_dict
        crm_auto_created = True
        
        await db.whatsapp_logs.insert_one({
            "id": str(uuid.uuid4()),
            "company_id": company_id,
            "config_id": config['id'],
            "log_type": "crm",
            "phone_number": normalized_phone,
            "message": f"Auto-created CRM customer: {customer_name}",
            "success": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    
    customer_id = customer['id'] if customer else None
    
    # Find or create conversation
    conversation = await db.conversations.find_one(
        {
            "company_id": company_id,
            "customer_phone": normalized_phone,
            "channel": "whatsapp",
            "status": "active"
        },
        {"_id": 0}
    )
    
    if not conversation:
        conversation = Conversation(
            company_id=company_id,
            customer_id=customer_id,
            customer_name=customer['name'] if customer else customer_name,
            customer_phone=normalized_phone,
            agent_mode=config.get('default_reply_mode', 'customer_service'),
            channel="whatsapp",
            status="active"
        )
        
        conv_dict = conversation.model_dump()
        conv_dict['created_at'] = conv_dict['created_at'].isoformat()
        conv_dict['updated_at'] = conv_dict['updated_at'].isoformat()
        
        await db.conversations.insert_one(conv_dict)
    
    conversation_id = conversation['id'] if isinstance(conversation, dict) else conversation.id
    
    # Save incoming message
    incoming_msg = WhatsAppMessage(
        company_id=company_id,
        config_id=config['id'],
        conversation_id=conversation_id,
        customer_id=customer_id,
        direction="incoming",
        phone_number=normalized_phone,
        message_text=message_text,
        provider_message_id=provider_message_id,
        provider_type=provider,
        delivery_status="received",
        crm_auto_created=crm_auto_created
    )
    
    incoming_msg_dict = incoming_msg.model_dump()
    incoming_msg_dict['timestamp'] = incoming_msg_dict['timestamp'].isoformat()
    await db.whatsapp_messages.insert_one(incoming_msg_dict)
    
    # Save to messages collection
    user_msg = Message(
        conversation_id=conversation_id,
        role="user",
        content=message_text,
        language=config.get('language', 'id')
    )
    user_msg_dict = user_msg.model_dump()
    user_msg_dict['timestamp'] = user_msg_dict['timestamp'].isoformat()
    await db.messages.insert_one(user_msg_dict)
    
    # Generate AI reply if auto-reply enabled
    ai_response_text = None
    needs_human_handoff = False
    handoff_reason = None
    
    if config.get('auto_reply_enabled', True):
        try:
            # Get knowledge base context
            knowledge_docs = await db.knowledge_base.find(
                {"company_id": company_id, "is_active": True},
                {"_id": 0}
            ).limit(5).to_list(5)
            
            knowledge_context = "\n\n".join([
                f"Title: {doc['title']}\nContent: {doc['content'][:500]}..."
                for doc in knowledge_docs
            ])
            
            # Get product context
            products = await db.products.find(
                {"company_id": company_id, "is_active": True},
                {"_id": 0}
            ).limit(10).to_list(10)
            
            product_context = "\n\n".join([
                f"Product: {p['name']}\nHarga: Rp{p['selling_price']:,.0f}\nStock: {p['stock']} {p['unit']}"
                for p in products
            ])
            
            # Generate AI response
            ai_service = OCBAIService(
                company_id=company_id,
                agent_mode=config.get('default_reply_mode', 'customer_service')
            )
            
            ai_response_text = await ai_service.chat(
                user_message=message_text,
                session_id=conversation_id,
                language=config.get('language', 'id'),
                knowledge_context=knowledge_context,
                product_context=product_context
            )
            
            await db.whatsapp_logs.insert_one({
                "id": str(uuid.uuid4()),
                "company_id": company_id,
                "config_id": config['id'],
                "log_type": "ai",
                "phone_number": normalized_phone,
                "message": "AI response generated successfully",
                "success": True,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
        except Exception as e:
            # AI failed
            needs_human_handoff = config.get('human_handoff_enabled', False)
            handoff_reason = f"AI failed: {str(e)}"
            
            if not needs_human_handoff:
                ai_response_text = config.get(
                    'fallback_when_ai_fails',
                    "Mohon maaf, saat ini sistem sedang sibuk. Mohon tunggu sebentar."
                )
            
            await db.whatsapp_logs.insert_one({
                "id": str(uuid.uuid4()),
                "company_id": company_id,
                "config_id": config['id'],
                "log_type": "error",
                "phone_number": normalized_phone,
                "message": f"AI generation failed: {str(e)}",
                "success": False,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
    
    # Save AI response
    if ai_response_text:
        ai_msg = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=ai_response_text,
            language=config.get('language', 'id')
        )
        ai_msg_dict = ai_msg.model_dump()
        ai_msg_dict['timestamp'] = ai_msg_dict['timestamp'].isoformat()
        await db.messages.insert_one(ai_msg_dict)
        
        # Save outgoing WhatsApp message
        outgoing_msg = WhatsAppMessage(
            company_id=company_id,
            config_id=config['id'],
            conversation_id=conversation_id,
            customer_id=customer_id,
            direction="outgoing",
            phone_number=normalized_phone,
            message_text=ai_response_text,
            provider_type=config['provider_type'],
            delivery_status="pending",
            ai_mode_used=config.get('default_reply_mode'),
            needs_human_handoff=needs_human_handoff,
            handoff_reason=handoff_reason
        )
        
        outgoing_msg_dict = outgoing_msg.model_dump()
        outgoing_msg_dict['timestamp'] = outgoing_msg_dict['timestamp'].isoformat()
        await db.whatsapp_messages.insert_one(outgoing_msg_dict)
    
    return {
        "success": True,
        "conversation_id": conversation_id,
        "customer_id": customer_id,
        "crm_auto_created": crm_auto_created,
        "ai_response": ai_response_text,
        "needs_human_handoff": needs_human_handoff,
        "handoff_reason": handoff_reason
    }