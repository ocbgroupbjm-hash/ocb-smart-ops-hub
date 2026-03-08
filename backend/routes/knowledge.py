from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import List
from models.knowledge import KnowledgeCreate, KnowledgeResponse, KnowledgeBase
from database import knowledge_base_collection
from utils.dependencies import get_current_user
from datetime import datetime

router = APIRouter(prefix="/knowledge", tags=["Knowledge Base"])

@router.post("/", response_model=KnowledgeResponse)
async def create_knowledge(
    knowledge_data: KnowledgeCreate,
    current_user: dict = Depends(get_current_user)
):
    company_id = current_user.get("company_id")
    
    if not company_id:
        raise HTTPException(status_code=400, detail="User must be associated with a company")
    
    knowledge_data.company_id = company_id
    
    knowledge = KnowledgeBase(**knowledge_data.model_dump())
    knowledge_dict = knowledge.model_dump()
    knowledge_dict['created_at'] = knowledge_dict['created_at'].isoformat()
    knowledge_dict['updated_at'] = knowledge_dict['updated_at'].isoformat()
    
    await knowledge_base_collection.insert_one(knowledge_dict)
    
    return KnowledgeResponse(**knowledge.model_dump())

@router.post("/upload")
async def upload_knowledge_file(
    file: UploadFile = File(...),
    title: str = "",
    category: str = "general",
    current_user: dict = Depends(get_current_user)
):
    """Upload and process knowledge file (PDF, TXT, etc.)"""
    company_id = current_user.get("company_id")
    
    if not company_id:
        raise HTTPException(status_code=400, detail="User must be associated with a company")
    
    # Read file content
    content = await file.read()
    content_text = content.decode('utf-8', errors='ignore')
    
    # Create knowledge entry
    knowledge_data = KnowledgeCreate(
        company_id=company_id,
        title=title or file.filename,
        content=content_text[:50000],  # Limit to 50k chars
        file_type=file.content_type,
        category=category
    )
    
    knowledge = KnowledgeBase(**knowledge_data.model_dump())
    knowledge_dict = knowledge.model_dump()
    knowledge_dict['created_at'] = knowledge_dict['created_at'].isoformat()
    knowledge_dict['updated_at'] = knowledge_dict['updated_at'].isoformat()
    
    await knowledge_base_collection.insert_one(knowledge_dict)
    
    return {
        "message": "File uploaded successfully",
        "id": knowledge.id,
        "title": knowledge.title
    }

@router.get("/", response_model=List[KnowledgeResponse])
async def get_knowledge_base(current_user: dict = Depends(get_current_user)):
    company_id = current_user.get("company_id")
    
    knowledge = await knowledge_base_collection.find(
        {"company_id": company_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(1000)
    
    for item in knowledge:
        if isinstance(item.get('created_at'), str):
            item['created_at'] = datetime.fromisoformat(item['created_at'])
        if isinstance(item.get('updated_at'), str):
            item['updated_at'] = datetime.fromisoformat(item['updated_at'])
    
    return knowledge

@router.get("/{knowledge_id}", response_model=KnowledgeResponse)
async def get_knowledge_detail(knowledge_id: str, current_user: dict = Depends(get_current_user)):
    company_id = current_user.get("company_id")
    
    knowledge = await knowledge_base_collection.find_one(
        {"id": knowledge_id, "company_id": company_id},
        {"_id": 0}
    )
    
    if not knowledge:
        raise HTTPException(status_code=404, detail="Knowledge not found")
    
    if isinstance(knowledge.get('created_at'), str):
        knowledge['created_at'] = datetime.fromisoformat(knowledge['created_at'])
    if isinstance(knowledge.get('updated_at'), str):
        knowledge['updated_at'] = datetime.fromisoformat(knowledge['updated_at'])
    
    return knowledge

@router.delete("/{knowledge_id}")
async def delete_knowledge(knowledge_id: str, current_user: dict = Depends(get_current_user)):
    company_id = current_user.get("company_id")
    
    result = await knowledge_base_collection.delete_one(
        {"id": knowledge_id, "company_id": company_id}
    )
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Knowledge not found")
    
    return {"message": "Knowledge deleted successfully"}