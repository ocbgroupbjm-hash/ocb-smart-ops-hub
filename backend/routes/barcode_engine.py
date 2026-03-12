# Barcode Template Management API
# OCB AI TITAN - Barcode Engine

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from database import db
from utils.auth import get_current_user
from datetime import datetime, timezone
import uuid

router = APIRouter(prefix="/barcode", tags=["Barcode Engine"])

barcode_templates = db["barcode_templates"]

class BarcodeTemplateCreate(BaseModel):
    template_name: str
    width: int = 58
    height: int = 40
    margin: int = 2
    gap: int = 2
    barcode_type: str = "CODE128"
    font_size: int = 10
    show_price: bool = True
    show_name: bool = True

class BarcodeTemplateUpdate(BaseModel):
    template_name: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    margin: Optional[int] = None
    gap: Optional[int] = None
    barcode_type: Optional[str] = None
    font_size: Optional[int] = None
    show_price: Optional[bool] = None
    show_name: Optional[bool] = None

@router.get("/templates")
async def list_barcode_templates(user: dict = Depends(get_current_user)):
    """Get all barcode templates"""
    result = await barcode_templates.find({}, {"_id": 0}).sort("template_name", 1).to_list(100)
    return result

@router.get("/templates/{template_id}")
async def get_barcode_template(template_id: str, user: dict = Depends(get_current_user)):
    """Get single barcode template"""
    template = await barcode_templates.find_one({"id": template_id}, {"_id": 0})
    if not template:
        raise HTTPException(status_code=404, detail="Template tidak ditemukan")
    return template

@router.post("/templates")
async def create_barcode_template(data: BarcodeTemplateCreate, user: dict = Depends(get_current_user)):
    """Create new barcode template"""
    # Check duplicate name
    existing = await barcode_templates.find_one({"template_name": data.template_name})
    if existing:
        raise HTTPException(status_code=400, detail="Nama template sudah ada")
    
    template = {
        "id": str(uuid.uuid4()),
        **data.model_dump(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user.get("id")
    }
    await barcode_templates.insert_one(template)
    
    return {"id": template["id"], "message": "Template berhasil ditambahkan"}

@router.put("/templates/{template_id}")
async def update_barcode_template(
    template_id: str, 
    data: BarcodeTemplateUpdate, 
    user: dict = Depends(get_current_user)
):
    """Update barcode template"""
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Tidak ada data untuk diupdate")
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await barcode_templates.update_one(
        {"id": template_id}, 
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Template tidak ditemukan")
    
    return {"message": "Template berhasil diupdate"}

@router.delete("/templates/{template_id}")
async def delete_barcode_template(template_id: str, user: dict = Depends(get_current_user)):
    """Delete barcode template"""
    result = await barcode_templates.delete_one({"id": template_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Template tidak ditemukan")
    return {"message": "Template berhasil dihapus"}

# Initialize default templates
@router.post("/templates/init-defaults")
async def init_default_templates(user: dict = Depends(get_current_user)):
    """Initialize default barcode templates"""
    defaults = [
        {
            "id": str(uuid.uuid4()),
            "template_name": "Label 58x40",
            "width": 58,
            "height": 40,
            "margin": 2,
            "gap": 2,
            "barcode_type": "CODE128",
            "font_size": 10,
            "show_price": True,
            "show_name": True,
            "is_default": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "template_name": "Label 38x25",
            "width": 38,
            "height": 25,
            "margin": 1,
            "gap": 1,
            "barcode_type": "CODE128",
            "font_size": 8,
            "show_price": True,
            "show_name": True,
            "is_default": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "template_name": "A4 30 Label",
            "width": 63,
            "height": 30,
            "margin": 2,
            "gap": 0,
            "barcode_type": "CODE128",
            "font_size": 9,
            "show_price": True,
            "show_name": True,
            "is_default": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "template_name": "Rak / Shelf",
            "width": 80,
            "height": 50,
            "margin": 3,
            "gap": 3,
            "barcode_type": "CODE128",
            "font_size": 12,
            "show_price": True,
            "show_name": True,
            "is_default": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    inserted = 0
    for template in defaults:
        existing = await barcode_templates.find_one({"template_name": template["template_name"]})
        if not existing:
            await barcode_templates.insert_one(template)
            inserted += 1
    
    return {"message": f"{inserted} template default berhasil ditambahkan"}
