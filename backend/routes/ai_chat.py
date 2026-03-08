from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from models.conversation import ConversationCreate, ConversationResponse, ConversationWithMessages, MessageCreate, MessageResponse
from database import conversations_collection, messages_collection, knowledge_base_collection
from utils.dependencies import get_current_user
from services.ai_service import AIService
from datetime import datetime, timezone

router = APIRouter(prefix="/ai", tags=["AI Chat"])

class ChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    message: str
    agent_mode: str = "customer_service"  # customer_service, sales, marketing
    channel: str = "webchat"
    language: str = "en"

class ChatResponse(BaseModel):
    conversation_id: str
    response: str
    sentiment: Optional[str] = None

@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    company_id = current_user.get("company_id")
    
    if not company_id:
        raise HTTPException(status_code=400, detail="User must be associated with a company")
    
    conversation_id = request.conversation_id
    
    # Create new conversation if not exists
    if not conversation_id:
        conversation = ConversationCreate(
            company_id=company_id,
            customer_name=request.customer_name,
            customer_phone=request.customer_phone,
            agent_mode=request.agent_mode,
            channel=request.channel,
            status="active"
        )
        from models.conversation import Conversation
        conv_obj = Conversation(**conversation.model_dump())
        conv_dict = conv_obj.model_dump()
        conv_dict['created_at'] = conv_dict['created_at'].isoformat()
        conv_dict['updated_at'] = conv_dict['updated_at'].isoformat()
        await conversations_collection.insert_one(conv_dict)
        conversation_id = conv_obj.id
    
    # Save user message
    user_msg = MessageCreate(
        conversation_id=conversation_id,
        role="user",
        content=request.message,
        language=request.language
    )
    from models.conversation import Message
    user_msg_obj = Message(**user_msg.model_dump())
    user_msg_dict = user_msg_obj.model_dump()
    user_msg_dict['timestamp'] = user_msg_dict['timestamp'].isoformat()
    await messages_collection.insert_one(user_msg_dict)
    
    # Get knowledge base context
    knowledge_docs = await knowledge_base_collection.find(
        {"company_id": company_id, "is_active": True},
        {"_id": 0}
    ).limit(5).to_list(5)
    
    knowledge_context = "\n\n".join([f"Title: {doc['title']}\nContent: {doc['content'][:500]}..." for doc in knowledge_docs])
    
    # Get AI response
    ai_service = AIService(company_id=company_id, agent_mode=request.agent_mode)
    
    try:
        ai_response = await ai_service.chat(
            user_message=request.message,
            session_id=conversation_id,
            language=request.language,
            knowledge_context=knowledge_context
        )
        
        # Save AI response
        ai_msg = MessageCreate(
            conversation_id=conversation_id,
            role="assistant",
            content=ai_response,
            language=request.language
        )
        ai_msg_obj = Message(**ai_msg.model_dump())
        ai_msg_dict = ai_msg_obj.model_dump()
        ai_msg_dict['timestamp'] = ai_msg_dict['timestamp'].isoformat()
        await messages_collection.insert_one(ai_msg_dict)
        
        # Update conversation timestamp
        await conversations_collection.update_one(
            {"id": conversation_id},
            {"$set": {"updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        
        return ChatResponse(
            conversation_id=conversation_id,
            response=ai_response
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")

@router.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(current_user: dict = Depends(get_current_user)):
    company_id = current_user.get("company_id")
    
    conversations = await conversations_collection.find(
        {"company_id": company_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(100).to_list(100)
    
    for conv in conversations:
        if isinstance(conv.get('created_at'), str):
            conv['created_at'] = datetime.fromisoformat(conv['created_at'])
        if isinstance(conv.get('updated_at'), str):
            conv['updated_at'] = datetime.fromisoformat(conv['updated_at'])
    
    return conversations

@router.get("/conversations/{conversation_id}", response_model=ConversationWithMessages)
async def get_conversation_detail(conversation_id: str, current_user: dict = Depends(get_current_user)):
    company_id = current_user.get("company_id")
    
    conversation = await conversations_collection.find_one(
        {"id": conversation_id, "company_id": company_id},
        {"_id": 0}
    )
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Get messages
    messages = await messages_collection.find(
        {"conversation_id": conversation_id},
        {"_id": 0}
    ).sort("timestamp", 1).to_list(1000)
    
    for msg in messages:
        if isinstance(msg.get('timestamp'), str):
            msg['timestamp'] = datetime.fromisoformat(msg['timestamp'])
    
    if isinstance(conversation.get('created_at'), str):
        conversation['created_at'] = datetime.fromisoformat(conversation['created_at'])
    if isinstance(conversation.get('updated_at'), str):
        conversation['updated_at'] = datetime.fromisoformat(conversation['updated_at'])
    
    return ConversationWithMessages(**conversation, messages=messages)