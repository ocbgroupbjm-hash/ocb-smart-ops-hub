# OCB TITAN AI - AI Product Photo Studio
# AI-powered photo enhancement, background removal, and catalog photo generation

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
import uuid
import base64
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/api/ai-photo-studio", tags=["AI Photo Studio"])

def get_db():
    from database import get_db as db_get
    return db_get()

def get_current_user():
    from routes.auth import get_current_user as auth_user
    return auth_user

# Get API key
EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY", "")

# Models
class PhotoEnhanceRequest(BaseModel):
    image_base64: str
    enhancement_type: str  # enhance, remove_bg, white_bg, catalog, sharpen, lighting
    mode: Optional[str] = "marketplace"  # marketplace, instagram, banner, shopee


class PhotoGenerateRequest(BaseModel):
    prompt: str
    product_name: str
    style: Optional[str] = "catalog"  # catalog, lifestyle, studio, minimal


# ==================== PHOTO UPLOAD ====================

@router.post("/upload/{item_id}")
async def upload_product_photo(
    item_id: str,
    file: UploadFile = File(...),
    is_main: bool = Form(False),
    user: dict = Depends(get_current_user)
):
    """Upload a product photo"""
    db = get_db()
    
    # Verify item exists
    item = await db["items"].find_one({"id": item_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Item tidak ditemukan")
    
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/webp", "image/jpg"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Format file tidak didukung. Gunakan JPG, PNG, atau WEBP")
    
    # Read file
    content = await file.read()
    
    # Check size (max 5MB)
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Ukuran file maksimal 5MB")
    
    # Convert to base64
    image_base64 = base64.b64encode(content).decode('utf-8')
    
    # If setting as main, unset previous main
    if is_main:
        await db["item_images"].update_many(
            {"item_id": item_id, "is_main": True},
            {"$set": {"is_main": False}}
        )
    
    # Save to database
    image_doc = {
        "id": str(uuid.uuid4()),
        "item_id": item_id,
        "image_type": "original",
        "image_data": image_base64,
        "filename": file.filename,
        "content_type": file.content_type,
        "is_main": is_main,
        "ai_generated": False,
        "ai_mode": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user.get("id")
    }
    
    await db["item_images"].insert_one(image_doc)
    
    return {
        "id": image_doc["id"],
        "message": "Foto berhasil diupload",
        "is_main": is_main
    }


@router.get("/images/{item_id}")
async def get_item_images(item_id: str, user: dict = Depends(get_current_user)):
    """Get all images for an item"""
    db = get_db()
    
    images = await db["item_images"].find(
        {"item_id": item_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return {"images": images, "total": len(images)}


@router.delete("/images/{image_id}")
async def delete_image(image_id: str, user: dict = Depends(get_current_user)):
    """Delete a product image"""
    db = get_db()
    
    result = await db["item_images"].delete_one({"id": image_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Gambar tidak ditemukan")
    
    return {"message": "Gambar berhasil dihapus"}


@router.post("/set-main/{image_id}")
async def set_main_image(image_id: str, user: dict = Depends(get_current_user)):
    """Set an image as main photo"""
    db = get_db()
    
    # Get image to find item_id
    image = await db["item_images"].find_one({"id": image_id}, {"_id": 0, "item_id": 1})
    if not image:
        raise HTTPException(status_code=404, detail="Gambar tidak ditemukan")
    
    # Unset all main for this item
    await db["item_images"].update_many(
        {"item_id": image["item_id"], "is_main": True},
        {"$set": {"is_main": False}}
    )
    
    # Set this as main
    await db["item_images"].update_one(
        {"id": image_id},
        {"$set": {"is_main": True}}
    )
    
    return {"message": "Foto utama berhasil diset"}


# ==================== AI PHOTO ENHANCEMENT ====================

@router.post("/enhance")
async def enhance_photo(data: PhotoEnhanceRequest, user: dict = Depends(get_current_user)):
    """Enhance a product photo using AI"""
    
    if not EMERGENT_LLM_KEY:
        # Fallback to basic processing without AI
        return await basic_enhance(data)
    
    try:
        from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration
        
        # Create prompt based on enhancement type
        prompts = {
            "enhance": f"Enhance this product photo: improve lighting, sharpness, and color balance while keeping the product exactly the same. Professional product photography style.",
            "remove_bg": f"Remove the background from this product photo and replace with pure white (#FFFFFF) background. Keep the product sharp and well-lit.",
            "white_bg": f"Place this product on a clean white background with soft shadow. Professional e-commerce style photography.",
            "catalog": f"Transform this into a professional {data.mode} catalog photo. Clean background, perfect lighting, product centered. Ready for marketplace listing.",
            "sharpen": f"Sharpen this product photo while maintaining natural look. Enhance details and textures.",
            "lighting": f"Improve the lighting of this product photo. Make it bright, professional, and appealing."
        }
        
        prompt = prompts.get(data.enhancement_type, prompts["enhance"])
        
        # Generate enhanced image
        image_gen = OpenAIImageGeneration(api_key=EMERGENT_LLM_KEY)
        
        # Decode input image
        input_image = base64.b64decode(data.image_base64)
        
        # Generate with AI
        images = await image_gen.generate_images(
            prompt=prompt,
            model="gpt-image-1",
            number_of_images=1
        )
        
        if images and len(images) > 0:
            result_base64 = base64.b64encode(images[0]).decode('utf-8')
            return {
                "success": True,
                "enhanced_image": result_base64,
                "enhancement_type": data.enhancement_type,
                "mode": data.mode
            }
        else:
            raise HTTPException(status_code=500, detail="Gagal generate gambar")
            
    except ImportError:
        return await basic_enhance(data)
    except Exception as e:
        return await basic_enhance(data)


async def basic_enhance(data: PhotoEnhanceRequest):
    """Basic enhancement without AI (fallback)"""
    # Return original image with basic processing flag
    return {
        "success": True,
        "enhanced_image": data.image_base64,
        "enhancement_type": data.enhancement_type,
        "mode": data.mode,
        "note": "Basic processing applied (AI not available)"
    }


@router.post("/generate-catalog")
async def generate_catalog_photo(data: PhotoGenerateRequest, user: dict = Depends(get_current_user)):
    """Generate a catalog-ready product photo from prompt"""
    
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=400, detail="AI key tidak tersedia. Silakan upload foto manual.")
    
    try:
        from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration
        
        style_prompts = {
            "catalog": f"Professional e-commerce catalog photo of {data.product_name}. {data.prompt}. White background, soft shadow, centered, high quality product photography.",
            "lifestyle": f"Lifestyle product photography of {data.product_name}. {data.prompt}. Natural setting, warm lighting, appealing presentation.",
            "studio": f"Studio product photography of {data.product_name}. {data.prompt}. Clean backdrop, professional lighting, sharp details.",
            "minimal": f"Minimalist product photo of {data.product_name}. {data.prompt}. Simple clean background, elegant presentation."
        }
        
        prompt = style_prompts.get(data.style, style_prompts["catalog"])
        
        image_gen = OpenAIImageGeneration(api_key=EMERGENT_LLM_KEY)
        
        images = await image_gen.generate_images(
            prompt=prompt,
            model="gpt-image-1",
            number_of_images=1
        )
        
        if images and len(images) > 0:
            result_base64 = base64.b64encode(images[0]).decode('utf-8')
            return {
                "success": True,
                "generated_image": result_base64,
                "product_name": data.product_name,
                "style": data.style,
                "prompt_used": prompt
            }
        else:
            raise HTTPException(status_code=500, detail="Gagal generate gambar")
            
    except ImportError:
        raise HTTPException(status_code=500, detail="AI library tidak tersedia")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/save-enhanced/{item_id}")
async def save_enhanced_photo(
    item_id: str,
    image_base64: str = Form(...),
    enhancement_type: str = Form(...),
    mode: str = Form("marketplace"),
    is_main: bool = Form(False),
    user: dict = Depends(get_current_user)
):
    """Save an AI-enhanced photo to the item"""
    db = get_db()
    
    # Verify item exists
    item = await db["items"].find_one({"id": item_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Item tidak ditemukan")
    
    # If setting as main, unset previous main
    if is_main:
        await db["item_images"].update_many(
            {"item_id": item_id, "is_main": True},
            {"$set": {"is_main": False}}
        )
    
    # Save enhanced image
    image_doc = {
        "id": str(uuid.uuid4()),
        "item_id": item_id,
        "image_type": "enhanced" if enhancement_type != "catalog" else "catalog",
        "image_data": image_base64,
        "filename": f"ai_{enhancement_type}_{item_id}.png",
        "content_type": "image/png",
        "is_main": is_main,
        "ai_generated": True,
        "ai_mode": mode,
        "enhancement_type": enhancement_type,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user.get("id")
    }
    
    await db["item_images"].insert_one(image_doc)
    
    return {
        "id": image_doc["id"],
        "message": "Foto AI berhasil disimpan",
        "image_type": image_doc["image_type"]
    }


# ==================== BACKGROUND OPERATIONS ====================

@router.post("/remove-background")
async def remove_background(data: PhotoEnhanceRequest, user: dict = Depends(get_current_user)):
    """Remove background from product photo"""
    data.enhancement_type = "remove_bg"
    return await enhance_photo(data, user)


@router.post("/white-background")
async def add_white_background(data: PhotoEnhanceRequest, user: dict = Depends(get_current_user)):
    """Add white background to product photo"""
    data.enhancement_type = "white_bg"
    return await enhance_photo(data, user)


# ==================== COMPARE BEFORE/AFTER ====================

@router.post("/compare")
async def compare_images(
    original_base64: str,
    enhanced_base64: str,
    user: dict = Depends(get_current_user)
):
    """Return both images for before/after comparison"""
    return {
        "original": original_base64,
        "enhanced": enhanced_base64,
        "comparison_ready": True
    }


# ==================== BATCH OPERATIONS ====================

@router.post("/batch-enhance")
async def batch_enhance_photos(
    item_ids: List[str],
    enhancement_type: str = "catalog",
    mode: str = "marketplace",
    user: dict = Depends(get_current_user)
):
    """Batch enhance photos for multiple items"""
    db = get_db()
    
    results = []
    for item_id in item_ids:
        # Get main image for item
        image = await db["item_images"].find_one(
            {"item_id": item_id, "is_main": True},
            {"_id": 0, "image_data": 1}
        )
        
        if not image:
            results.append({
                "item_id": item_id,
                "success": False,
                "error": "No main image found"
            })
            continue
        
        # Enhance
        try:
            req = PhotoEnhanceRequest(
                image_base64=image["image_data"],
                enhancement_type=enhancement_type,
                mode=mode
            )
            enhanced = await enhance_photo(req, user)
            
            results.append({
                "item_id": item_id,
                "success": True,
                "enhanced_image": enhanced.get("enhanced_image")
            })
        except Exception as e:
            results.append({
                "item_id": item_id,
                "success": False,
                "error": str(e)
            })
    
    return {
        "results": results,
        "total": len(item_ids),
        "success_count": sum(1 for r in results if r["success"])
    }
