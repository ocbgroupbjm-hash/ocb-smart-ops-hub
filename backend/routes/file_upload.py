# OCB TITAN AI - File Upload System
# For KPI evidence, item photos, etc.

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import uuid
import os
import aiofiles
import base64

from database import get_db

router = APIRouter(prefix="/api/files", tags=["File Upload"])

UPLOAD_DIR = "/app/uploads"

def gen_id():
    return str(uuid.uuid4())

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def get_wib_now():
    return datetime.now(timezone.utc) + timedelta(hours=7)

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(f"{UPLOAD_DIR}/kpi", exist_ok=True)
os.makedirs(f"{UPLOAD_DIR}/products", exist_ok=True)
os.makedirs(f"{UPLOAD_DIR}/enhanced", exist_ok=True)

# Collections
def files_col():
    return get_db()['uploaded_files']

def products_col():
    return get_db()['products']

def kpi_evidence_col():
    return get_db()['kpi_evidence']

# ==================== KPI EVIDENCE UPLOAD ====================

@router.post("/kpi/evidence")
async def upload_kpi_evidence(
    kpi_target_id: str = Form(...),
    employee_id: str = Form(...),
    employee_name: str = Form(...),
    kpi_name: str = Form(...),
    notes: str = Form(""),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    file: UploadFile = File(...)
):
    """Upload KPI evidence (photo/video)"""
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/webp", "video/mp4", "video/quicktime"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Tipe file tidak didukung. Gunakan JPEG, PNG, WEBP, atau MP4.")
    
    # Generate filename
    ext = file.filename.split(".")[-1].lower()
    file_id = gen_id()
    filename = f"{file_id}.{ext}"
    filepath = f"{UPLOAD_DIR}/kpi/{filename}"
    
    # Save file
    async with aiofiles.open(filepath, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    # Determine file type
    file_type = "photo" if file.content_type.startswith("image") else "video"
    
    # Create evidence record
    evidence = {
        "id": file_id,
        "kpi_target_id": kpi_target_id,
        "employee_id": employee_id,
        "employee_name": employee_name,
        "kpi_name": kpi_name,
        "file_type": file_type,
        "filename": filename,
        "original_filename": file.filename,
        "filepath": filepath,
        "file_url": f"/api/files/kpi/{filename}",
        "content_type": file.content_type,
        "file_size": len(content),
        "notes": notes,
        "location": {
            "latitude": latitude,
            "longitude": longitude
        } if latitude and longitude else None,
        "timestamp": now_iso(),
        "uploaded_at": now_iso(),
        "status": "pending_review"
    }
    
    await kpi_evidence_col().insert_one(evidence)
    
    # Update KPI target
    kpi_targets_col = get_db()['kpi_targets']
    await kpi_targets_col.update_one(
        {"id": kpi_target_id},
        {"$push": {"evidence_ids": file_id}, "$set": {"has_evidence": True, "updated_at": now_iso()}}
    )
    
    return {
        "message": "Evidence berhasil diupload",
        "evidence": {
            "id": evidence["id"],
            "file_url": evidence["file_url"],
            "file_type": file_type
        }
    }

@router.get("/kpi/evidence/{kpi_target_id}")
async def get_kpi_evidence(kpi_target_id: str):
    """Get all evidence for a KPI target"""
    evidence = await kpi_evidence_col().find({"kpi_target_id": kpi_target_id}, {"_id": 0}).to_list(length=50)
    return {"evidence": evidence}

@router.get("/kpi/{filename}")
async def get_kpi_file(filename: str):
    """Serve KPI evidence file"""
    from fastapi.responses import FileResponse
    filepath = f"{UPLOAD_DIR}/kpi/{filename}"
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File tidak ditemukan")
    return FileResponse(filepath)

# ==================== PRODUCT PHOTO UPLOAD ====================

@router.post("/products/photo")
async def upload_product_photo(
    product_id: str = Form(...),
    is_primary: bool = Form(False),
    file: UploadFile = File(...)
):
    """Upload product photo"""
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Tipe file tidak didukung. Gunakan JPEG, PNG, atau WEBP.")
    
    # Check product exists
    product = await products_col().find_one({"id": product_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Produk tidak ditemukan")
    
    # Generate filename
    ext = file.filename.split(".")[-1].lower()
    file_id = gen_id()
    filename = f"{product_id}_{file_id}.{ext}"
    filepath = f"{UPLOAD_DIR}/products/{filename}"
    
    # Save file
    async with aiofiles.open(filepath, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    # Create photo record
    photo = {
        "id": file_id,
        "product_id": product_id,
        "filename": filename,
        "original_filename": file.filename,
        "filepath": filepath,
        "file_url": f"/api/files/products/{filename}",
        "content_type": file.content_type,
        "file_size": len(content),
        "is_primary": is_primary,
        "is_enhanced": False,
        "uploaded_at": now_iso()
    }
    
    await files_col().insert_one(photo)
    
    # Update product
    update_data = {
        "$push": {"photo_ids": file_id},
        "$set": {"has_photos": True, "updated_at": now_iso()}
    }
    
    if is_primary:
        update_data["$set"]["primary_photo_url"] = photo["file_url"]
        update_data["$set"]["primary_photo_id"] = file_id
    
    await products_col().update_one({"id": product_id}, update_data)
    
    return {
        "message": "Foto produk berhasil diupload",
        "photo": {
            "id": file_id,
            "file_url": photo["file_url"],
            "is_primary": is_primary
        }
    }

@router.get("/products/photos/{product_id}")
async def get_product_photos(product_id: str):
    """Get all photos for a product"""
    photos = await files_col().find({"product_id": product_id}, {"_id": 0}).to_list(length=20)
    return {"photos": photos}

@router.put("/products/photo/{photo_id}/primary")
async def set_primary_photo(photo_id: str):
    """Set photo as primary"""
    photo = await files_col().find_one({"id": photo_id}, {"_id": 0})
    if not photo:
        raise HTTPException(status_code=404, detail="Foto tidak ditemukan")
    
    product_id = photo["product_id"]
    
    # Unset all primary
    await files_col().update_many(
        {"product_id": product_id},
        {"$set": {"is_primary": False}}
    )
    
    # Set this as primary
    await files_col().update_one({"id": photo_id}, {"$set": {"is_primary": True}})
    
    # Update product
    await products_col().update_one(
        {"id": product_id},
        {"$set": {
            "primary_photo_url": photo["file_url"],
            "primary_photo_id": photo_id,
            "updated_at": now_iso()
        }}
    )
    
    return {"message": "Foto utama berhasil diubah"}

@router.delete("/products/photo/{photo_id}")
async def delete_product_photo(photo_id: str):
    """Delete product photo"""
    photo = await files_col().find_one({"id": photo_id}, {"_id": 0})
    if not photo:
        raise HTTPException(status_code=404, detail="Foto tidak ditemukan")
    
    # Delete file
    if os.path.exists(photo["filepath"]):
        os.remove(photo["filepath"])
    
    # Delete record
    await files_col().delete_one({"id": photo_id})
    
    # Update product
    product_id = photo["product_id"]
    await products_col().update_one(
        {"id": product_id},
        {"$pull": {"photo_ids": photo_id}}
    )
    
    # If was primary, clear primary
    if photo.get("is_primary"):
        await products_col().update_one(
            {"id": product_id},
            {"$unset": {"primary_photo_url": "", "primary_photo_id": ""}}
        )
    
    return {"message": "Foto berhasil dihapus"}

@router.get("/products/{filename}")
async def get_product_file(filename: str):
    """Serve product photo file"""
    from fastapi.responses import FileResponse
    filepath = f"{UPLOAD_DIR}/products/{filename}"
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File tidak ditemukan")
    return FileResponse(filepath)

# ==================== AI IMAGE ENHANCEMENT ====================

@router.post("/products/photo/{photo_id}/enhance")
async def enhance_product_photo(photo_id: str, enhancement_type: str = "auto"):
    """AI-enhanced product photo (placeholder for AI integration)"""
    photo = await files_col().find_one({"id": photo_id}, {"_id": 0})
    if not photo:
        raise HTTPException(status_code=404, detail="Foto tidak ditemukan")
    
    # Create enhanced version record
    enhanced_id = gen_id()
    ext = photo["filename"].split(".")[-1]
    enhanced_filename = f"enhanced_{photo_id}_{enhanced_id}.{ext}"
    
    enhanced_photo = {
        "id": enhanced_id,
        "product_id": photo["product_id"],
        "original_photo_id": photo_id,
        "filename": enhanced_filename,
        "file_url": f"/api/files/enhanced/{enhanced_filename}",
        "enhancement_type": enhancement_type,
        "is_enhanced": True,
        "is_primary": False,
        "status": "pending",  # Will be "completed" after AI processing
        "created_at": now_iso()
    }
    
    await files_col().insert_one(enhanced_photo)
    
    # In production, this would trigger AI enhancement
    # For now, return pending status
    return {
        "message": "Enhancement sedang diproses",
        "enhanced_photo": {
            "id": enhanced_id,
            "status": "pending",
            "enhancement_type": enhancement_type
        },
        "note": "AI enhancement membutuhkan API key eksternal. Silakan konfigurasi di Settings."
    }

@router.get("/enhanced/{filename}")
async def get_enhanced_file(filename: str):
    """Serve enhanced photo file"""
    from fastapi.responses import FileResponse
    filepath = f"{UPLOAD_DIR}/enhanced/{filename}"
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File tidak ditemukan")
    return FileResponse(filepath)
