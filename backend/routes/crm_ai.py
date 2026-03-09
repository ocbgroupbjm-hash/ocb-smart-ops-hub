# OCB TITAN AI - CRM AI Prompt Builder
# Custom AI prompts for CRM tasks

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel
import uuid

from database import get_db

router = APIRouter(prefix="/api/crm-ai", tags=["CRM AI"])

def gen_id():
    return str(uuid.uuid4())

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def get_wib_now():
    return datetime.now(timezone.utc) + timedelta(hours=7)

# Collections
def prompts_col():
    return get_db()['ai_prompts']

def chat_history_col():
    return get_db()['crm_chat_history']

def customers_col():
    return get_db()['customers']

def products_col():
    return get_db()['products']

# ==================== MODELS ====================

class AIPromptTemplate(BaseModel):
    name: str
    category: str  # customer_reply, marketing_script, product_recommendation, complaint_handling
    description: str = ""
    prompt_template: str
    variables: List[str] = []  # Variables that can be replaced
    is_active: bool = True

class ChatMessage(BaseModel):
    customer_id: str
    customer_name: str
    message: str
    is_from_customer: bool = True

class GenerateReply(BaseModel):
    prompt_id: str
    customer_id: str
    customer_name: str
    context: dict = {}

# ==================== AI PROMPT TEMPLATES ====================

@router.get("/prompts")
async def get_prompts(category: Optional[str] = None):
    """Get all AI prompt templates"""
    query = {"is_active": True}
    if category:
        query["category"] = category
    
    prompts = await prompts_col().find(query, {"_id": 0}).to_list(length=100)
    return {"prompts": prompts}

@router.post("/prompts")
async def create_prompt(data: AIPromptTemplate):
    """Create AI prompt template"""
    prompt = {
        "id": gen_id(),
        **data.dict(),
        "usage_count": 0,
        "created_at": now_iso()
    }
    await prompts_col().insert_one(prompt)
    return {"message": "Prompt berhasil dibuat", "prompt": prompt}

@router.put("/prompts/{prompt_id}")
async def update_prompt(prompt_id: str, data: AIPromptTemplate):
    """Update AI prompt template"""
    update_data = {**data.dict(), "updated_at": now_iso()}
    await prompts_col().update_one({"id": prompt_id}, {"$set": update_data})
    return {"message": "Prompt berhasil diupdate"}

@router.delete("/prompts/{prompt_id}")
async def delete_prompt(prompt_id: str):
    """Delete AI prompt template"""
    await prompts_col().update_one({"id": prompt_id}, {"$set": {"is_active": False}})
    return {"message": "Prompt berhasil dihapus"}

# ==================== AI CHAT ====================

@router.post("/chat/message")
async def save_chat_message(data: ChatMessage):
    """Save chat message"""
    message = {
        "id": gen_id(),
        **data.dict(),
        "created_at": now_iso()
    }
    await chat_history_col().insert_one(message)
    return {"message": "Pesan disimpan", "chat": message}

@router.get("/chat/history/{customer_id}")
async def get_chat_history(customer_id: str, limit: int = 50):
    """Get chat history for customer"""
    history = await chat_history_col().find(
        {"customer_id": customer_id}, {"_id": 0}
    ).sort("created_at", -1).to_list(length=limit)
    
    return {"customer_id": customer_id, "messages": list(reversed(history))}

@router.post("/chat/generate-reply")
async def generate_ai_reply(data: GenerateReply):
    """Generate AI reply using prompt template"""
    # Get prompt template
    prompt = await prompts_col().find_one({"id": data.prompt_id}, {"_id": 0})
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt tidak ditemukan")
    
    # Get customer info
    customer = await customers_col().find_one({"id": data.customer_id}, {"_id": 0})
    
    # Get recent chat history
    history = await chat_history_col().find(
        {"customer_id": data.customer_id}, {"_id": 0}
    ).sort("created_at", -1).to_list(length=10)
    
    # Build context
    context = {
        "customer_name": data.customer_name,
        "customer_phone": customer.get("phone", "") if customer else "",
        "customer_email": customer.get("email", "") if customer else "",
        "purchase_history": customer.get("total_purchases", 0) if customer else 0,
        "last_purchase": customer.get("last_purchase_date", "") if customer else "",
        **data.context
    }
    
    # Replace variables in template
    reply_template = prompt["prompt_template"]
    for var in prompt.get("variables", []):
        if var in context:
            reply_template = reply_template.replace(f"{{{var}}}", str(context[var]))
    
    # Update usage count
    await prompts_col().update_one(
        {"id": data.prompt_id},
        {"$inc": {"usage_count": 1}}
    )
    
    # In production, this would call an AI service
    # For now, return the filled template
    return {
        "prompt_used": prompt["name"],
        "generated_reply": reply_template,
        "context_used": context,
        "note": "Silakan edit reply sebelum mengirim ke customer"
    }

# ==================== PRODUCT RECOMMENDATIONS ====================

@router.get("/recommend-products/{customer_id}")
async def recommend_products(customer_id: str):
    """Get AI product recommendations for customer"""
    # Get customer purchase history
    customer = await customers_col().find_one({"id": customer_id}, {"_id": 0})
    
    # Get transaction history
    transactions_col = get_db()['transaction_items']
    purchase_history = await transactions_col.find(
        {"customer_id": customer_id}, {"_id": 0}
    ).to_list(length=100)
    
    # Get popular products
    products = await products_col().find(
        {"stock": {"$gt": 0}}, {"_id": 0}
    ).sort("sold_count", -1).to_list(length=20)
    
    # Simple recommendation logic
    purchased_ids = set(p.get("product_id") for p in purchase_history)
    
    recommendations = []
    for p in products:
        if p.get("id") not in purchased_ids:
            recommendations.append({
                "id": p.get("id"),
                "name": p.get("name"),
                "price": p.get("price"),
                "category": p.get("category"),
                "reason": "Produk populer yang belum pernah dibeli"
            })
    
    # Get products from same categories as previous purchases
    if purchase_history:
        purchased_categories = set()
        for ph in purchase_history:
            if ph.get("category"):
                purchased_categories.add(ph["category"])
        
        related = await products_col().find({
            "category": {"$in": list(purchased_categories)},
            "id": {"$nin": list(purchased_ids)},
            "stock": {"$gt": 0}
        }, {"_id": 0}).limit(10).to_list(length=10)
        
        for p in related:
            recommendations.append({
                "id": p.get("id"),
                "name": p.get("name"),
                "price": p.get("price"),
                "category": p.get("category"),
                "reason": f"Berdasarkan pembelian kategori {p.get('category')}"
            })
    
    return {
        "customer_id": customer_id,
        "customer_name": customer.get("name") if customer else "Unknown",
        "total_recommendations": len(recommendations),
        "recommendations": recommendations[:10]
    }

# ==================== MARKETING SCRIPTS ====================

@router.get("/marketing-scripts")
async def get_marketing_scripts():
    """Get marketing script templates"""
    scripts = await prompts_col().find({
        "category": "marketing_script",
        "is_active": True
    }, {"_id": 0}).to_list(length=50)
    
    return {"scripts": scripts}

@router.post("/marketing-scripts/generate")
async def generate_marketing_script(product_ids: List[str], campaign_type: str = "promo"):
    """Generate marketing script for products"""
    products = await products_col().find(
        {"id": {"$in": product_ids}}, {"_id": 0}
    ).to_list(length=10)
    
    if not products:
        raise HTTPException(status_code=404, detail="Produk tidak ditemukan")
    
    # Get script template
    template = await prompts_col().find_one({
        "category": "marketing_script",
        "is_active": True
    }, {"_id": 0})
    
    product_list = "\n".join([f"- {p['name']}: Rp {p.get('price', 0):,.0f}" for p in products])
    
    script = f"""
🎉 PROMO SPESIAL OCB GROUP! 🎉

Hai Kak! Ada promo menarik nih untuk produk favorit:

{product_list}

Yuk buruan order sebelum kehabisan! 
Hubungi kami sekarang untuk info lebih lanjut.

📱 WhatsApp: [NOMOR]
📍 Kunjungi toko kami terdekat

#OCBGroup #PromoSpesial #BelanjaSeru
"""
    
    return {
        "campaign_type": campaign_type,
        "products": products,
        "generated_script": script.strip(),
        "note": "Edit script sesuai kebutuhan sebelum digunakan"
    }

# ==================== COMPLAINT HANDLING ====================

@router.post("/complaint/analyze")
async def analyze_complaint(complaint_text: str, customer_id: str = ""):
    """Analyze customer complaint and suggest response"""
    # Keywords for categorization
    categories = {
        "produk_rusak": ["rusak", "cacat", "tidak berfungsi", "pecah", "patah"],
        "pelayanan_lambat": ["lambat", "lama", "tidak responsif", "menunggu"],
        "harga": ["mahal", "harga", "diskon", "promo"],
        "pengiriman": ["kirim", "delivery", "paket", "belum sampai"],
        "kualitas": ["kualitas", "jelek", "buruk", "tidak sesuai"]
    }
    
    detected_category = "umum"
    complaint_lower = complaint_text.lower()
    
    for cat, keywords in categories.items():
        if any(kw in complaint_lower for kw in keywords):
            detected_category = cat
            break
    
    # Suggested responses
    responses = {
        "produk_rusak": "Mohon maaf atas ketidaknyamanan ini. Kami akan segera memproses penggantian produk. Bisa kirimkan foto produk yang rusak?",
        "pelayanan_lambat": "Terima kasih atas masukannya. Kami akan meningkatkan kecepatan pelayanan kami. Apakah ada yang bisa kami bantu sekarang?",
        "harga": "Terima kasih sudah menghubungi kami. Saat ini kami memiliki program promo yang mungkin cocok untuk Anda. Boleh kami infokan?",
        "pengiriman": "Mohon maaf atas keterlambatan pengiriman. Kami akan segera cek status pengiriman dan menghubungi Anda kembali.",
        "kualitas": "Kami mohon maaf jika produk tidak sesuai harapan. Kami akan investigasi dan memberikan solusi terbaik.",
        "umum": "Terima kasih sudah menghubungi kami. Tim kami akan segera membantu menyelesaikan masalah Anda."
    }
    
    return {
        "complaint_text": complaint_text,
        "detected_category": detected_category,
        "sentiment": "negative",
        "suggested_response": responses.get(detected_category, responses["umum"]),
        "recommended_action": f"Tindak lanjut untuk kategori: {detected_category}",
        "priority": "high" if detected_category in ["produk_rusak", "pengiriman"] else "medium"
    }

# ==================== SEED DEFAULT PROMPTS ====================

@router.post("/seed-prompts")
async def seed_default_prompts():
    """Create default AI prompts"""
    prompts = [
        {
            "id": gen_id(),
            "name": "Salam Pembuka Customer",
            "category": "customer_reply",
            "description": "Template salam pembuka untuk customer baru",
            "prompt_template": "Halo Kak {customer_name}! 👋\n\nTerima kasih sudah menghubungi OCB Group.\nAda yang bisa kami bantu hari ini?",
            "variables": ["customer_name"],
            "is_active": True,
            "usage_count": 0,
            "created_at": now_iso()
        },
        {
            "id": gen_id(),
            "name": "Follow Up Pembelian",
            "category": "customer_reply",
            "description": "Template follow up setelah pembelian",
            "prompt_template": "Halo Kak {customer_name}! 😊\n\nTerima kasih sudah berbelanja di OCB Group.\nBagaimana produknya? Semoga sesuai dengan harapan ya!\n\nJika ada kendala, jangan ragu untuk menghubungi kami.",
            "variables": ["customer_name"],
            "is_active": True,
            "usage_count": 0,
            "created_at": now_iso()
        },
        {
            "id": gen_id(),
            "name": "Promo Bulanan",
            "category": "marketing_script",
            "description": "Template script promo bulanan",
            "prompt_template": "🎉 PROMO SPESIAL BULAN INI! 🎉\n\nHai Kak {customer_name}!\n\nKami punya penawaran spesial untuk Anda:\n{promo_details}\n\nYuk buruan sebelum kehabisan!\n📱 Hubungi kami sekarang",
            "variables": ["customer_name", "promo_details"],
            "is_active": True,
            "usage_count": 0,
            "created_at": now_iso()
        },
        {
            "id": gen_id(),
            "name": "Penanganan Komplain",
            "category": "complaint_handling",
            "description": "Template respons untuk komplain customer",
            "prompt_template": "Halo Kak {customer_name},\n\nMohon maaf atas ketidaknyamanan yang dialami.\nKami akan segera menindaklanjuti masalah ini.\n\nBisa diinformasikan detail masalahnya:\n1. Nomor transaksi\n2. Tanggal pembelian\n3. Foto produk (jika ada)\n\nTerima kasih atas kesabarannya 🙏",
            "variables": ["customer_name"],
            "is_active": True,
            "usage_count": 0,
            "created_at": now_iso()
        },
        {
            "id": gen_id(),
            "name": "Rekomendasi Produk",
            "category": "product_recommendation",
            "description": "Template rekomendasi produk",
            "prompt_template": "Hai Kak {customer_name}! 🛍️\n\nBerdasarkan pembelian Anda sebelumnya, kami rekomendasikan:\n\n{product_recommendations}\n\nTertarik? Yuk order sekarang!",
            "variables": ["customer_name", "product_recommendations"],
            "is_active": True,
            "usage_count": 0,
            "created_at": now_iso()
        }
    ]
    
    for p in prompts:
        await prompts_col().update_one({"name": p["name"]}, {"$set": p}, upsert=True)
    
    return {"message": f"{len(prompts)} prompt berhasil dibuat"}
