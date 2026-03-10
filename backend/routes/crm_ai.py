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

# ==================== CUSTOMER MANAGEMENT ====================

class CustomerProfile(BaseModel):
    name: str
    phone: str = ""
    email: str = ""
    address: str = ""
    birth_date: str = ""
    gender: str = ""
    notes: str = ""
    tags: List[str] = []
    source: str = ""  # walk-in, online, referral, social_media

class CustomerCharacter(BaseModel):
    customer_id: str
    buying_frequency: str = "normal"  # rare, normal, frequent, vip
    price_sensitivity: str = "normal"  # price_sensitive, normal, premium
    communication_style: str = "formal"  # formal, casual, brief
    preferred_channel: str = "whatsapp"  # whatsapp, phone, email
    interests: List[str] = []
    special_notes: str = ""

@router.get("/customers")
async def list_customers(search: Optional[str] = None, tag: Optional[str] = None, limit: int = 100):
    """Get all customers with optional search"""
    query = {}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"phone": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}}
        ]
    if tag:
        query["tags"] = tag
    
    customers = await customers_col().find(query, {"_id": 0}).sort("name", 1).to_list(length=limit)
    return {"customers": customers, "total": len(customers)}

@router.get("/customers/{customer_id}")
async def get_customer_detail(customer_id: str):
    """Get customer detail with character analysis"""
    customer = await customers_col().find_one({"id": customer_id}, {"_id": 0})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer tidak ditemukan")
    
    # Get character profile
    char_col = get_db()['customer_characters']
    character = await char_col.find_one({"customer_id": customer_id}, {"_id": 0})
    
    # Get chat history
    chat_count = await chat_history_col().count_documents({"customer_id": customer_id})
    
    # Get purchase stats
    transactions_col = get_db()['transactions']
    purchases = await transactions_col.find(
        {"customer_id": customer_id}, {"_id": 0}
    ).to_list(length=100)
    
    total_spent = sum(p.get("total", 0) for p in purchases)
    avg_transaction = total_spent / len(purchases) if purchases else 0
    
    return {
        "customer": customer,
        "character": character,
        "stats": {
            "total_purchases": len(purchases),
            "total_spent": total_spent,
            "avg_transaction": avg_transaction,
            "chat_count": chat_count,
            "last_purchase": purchases[0].get("created_at") if purchases else None
        }
    }

@router.post("/customers")
async def create_customer(data: CustomerProfile):
    """Create new customer"""
    # Check duplicate phone
    if data.phone:
        existing = await customers_col().find_one({"phone": data.phone})
        if existing:
            raise HTTPException(status_code=400, detail="Nomor telepon sudah terdaftar")
    
    customer = {
        "id": gen_id(),
        **data.dict(),
        "total_purchases": 0,
        "total_spent": 0,
        "last_purchase_date": "",
        "created_at": now_iso(),
        "updated_at": now_iso()
    }
    
    await customers_col().insert_one(customer)
    customer.pop("_id", None)  # Remove MongoDB _id before returning
    return {"message": "Customer berhasil ditambahkan", "customer": customer}

@router.put("/customers/{customer_id}")
async def update_customer(customer_id: str, data: CustomerProfile):
    """Update customer data"""
    update_data = {**data.dict(), "updated_at": now_iso()}
    await customers_col().update_one({"id": customer_id}, {"$set": update_data})
    return {"message": "Customer berhasil diupdate"}

@router.post("/customers/{customer_id}/character")
async def save_customer_character(customer_id: str, data: CustomerCharacter):
    """Save/update customer character profile"""
    char_col = get_db()['customer_characters']
    
    character = {
        "id": gen_id(),
        **data.dict(),
        "analyzed_at": now_iso()
    }
    
    await char_col.update_one(
        {"customer_id": customer_id},
        {"$set": character},
        upsert=True
    )
    
    character.pop("_id", None)
    return {"message": "Karakter customer berhasil disimpan", "character": character}

@router.get("/customers/{customer_id}/character")
async def get_customer_character(customer_id: str):
    """Get customer character profile"""
    char_col = get_db()['customer_characters']
    character = await char_col.find_one({"customer_id": customer_id}, {"_id": 0})
    
    if not character:
        # Auto-analyze from history
        customer = await customers_col().find_one({"id": customer_id}, {"_id": 0})
        purchases = await get_db()['transactions'].find(
            {"customer_id": customer_id}
        ).to_list(length=100)
        
        # Simple analysis
        purchase_count = len(purchases)
        buying_freq = "rare" if purchase_count < 3 else "normal" if purchase_count < 10 else "frequent"
        
        total_spent = sum(p.get("total", 0) for p in purchases)
        avg_spent = total_spent / purchase_count if purchase_count else 0
        
        price_sens = "price_sensitive" if avg_spent < 100000 else "normal" if avg_spent < 500000 else "premium"
        
        character = {
            "customer_id": customer_id,
            "buying_frequency": buying_freq,
            "price_sensitivity": price_sens,
            "communication_style": "formal",
            "preferred_channel": "whatsapp",
            "interests": [],
            "special_notes": f"Auto-analyzed: {purchase_count} transaksi, avg Rp {avg_spent:,.0f}",
            "is_auto_analyzed": True
        }
    
    return {"character": character}

@router.post("/customers/{customer_id}/analyze")
async def analyze_customer_ai(customer_id: str):
    """AI analysis of customer behavior and preferences"""
    customer = await customers_col().find_one({"id": customer_id}, {"_id": 0})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer tidak ditemukan")
    
    # Get all data
    purchases = await get_db()['transactions'].find(
        {"customer_id": customer_id}, {"_id": 0}
    ).sort("created_at", -1).to_list(length=50)
    
    chats = await chat_history_col().find(
        {"customer_id": customer_id}, {"_id": 0}
    ).sort("created_at", -1).to_list(length=100)
    
    # Analyze patterns
    purchase_count = len(purchases)
    chat_count = len(chats)
    total_spent = sum(p.get("total", 0) for p in purchases)
    
    # Buying frequency analysis
    if purchase_count == 0:
        buying_freq = "new"
        freq_note = "Customer baru, belum ada pembelian"
    elif purchase_count < 3:
        buying_freq = "rare"
        freq_note = "Jarang belanja, perlu pendekatan khusus"
    elif purchase_count < 10:
        buying_freq = "normal"
        freq_note = "Frekuensi normal, maintain hubungan baik"
    elif purchase_count < 20:
        buying_freq = "frequent"
        freq_note = "Pelanggan loyal, berikan reward/diskon khusus"
    else:
        buying_freq = "vip"
        freq_note = "VIP Customer! Prioritaskan pelayanan"
    
    # Price sensitivity analysis
    avg_spent = total_spent / purchase_count if purchase_count else 0
    if avg_spent < 100000:
        price_sens = "price_sensitive"
        price_note = "Sensitif harga, tawarkan promo/diskon"
    elif avg_spent < 500000:
        price_sens = "normal"
        price_note = "Budget menengah, balance promo & kualitas"
    else:
        price_sens = "premium"
        price_note = "Customer premium, fokus ke kualitas & layanan"
    
    # Communication analysis
    customer_messages = [c for c in chats if c.get("is_from_customer")]
    if len(customer_messages) > 5:
        # Check message length
        avg_length = sum(len(m.get("message", "")) for m in customer_messages) / len(customer_messages)
        if avg_length < 20:
            comm_style = "brief"
            comm_note = "Suka pesan singkat, respons to the point"
        elif avg_length < 100:
            comm_style = "casual"
            comm_note = "Gaya santai, bisa lebih friendly"
        else:
            comm_style = "formal"
            comm_note = "Cenderung detail, berikan info lengkap"
    else:
        comm_style = "unknown"
        comm_note = "Belum cukup data untuk analisis"
    
    # Save analysis
    analysis = {
        "customer_id": customer_id,
        "buying_frequency": buying_freq,
        "buying_frequency_note": freq_note,
        "price_sensitivity": price_sens,
        "price_sensitivity_note": price_note,
        "communication_style": comm_style,
        "communication_note": comm_note,
        "preferred_channel": "whatsapp",
        "stats": {
            "total_purchases": purchase_count,
            "total_spent": total_spent,
            "avg_transaction": avg_spent,
            "total_chats": chat_count
        },
        "recommendations": [],
        "analyzed_at": now_iso()
    }
    
    # Generate recommendations
    if buying_freq == "new":
        analysis["recommendations"].append("Kirim welcome message dan info produk populer")
    if buying_freq == "rare":
        analysis["recommendations"].append("Kirim reminder dan promo khusus untuk re-engage")
    if buying_freq in ["frequent", "vip"]:
        analysis["recommendations"].append("Berikan loyalty reward atau early access promo")
    if price_sens == "price_sensitive":
        analysis["recommendations"].append("Prioritaskan info diskon dan bundle deals")
    if price_sens == "premium":
        analysis["recommendations"].append("Tawarkan produk premium dan layanan eksklusif")
    
    # Save to database
    char_col = get_db()['customer_characters']
    await char_col.update_one(
        {"customer_id": customer_id},
        {"$set": analysis},
        upsert=True
    )
    
    return {
        "customer": customer,
        "analysis": analysis,
        "message": "Analisis karakter customer berhasil"
    }

# ==================== AUTO RESPONSE GENERATOR ====================

@router.post("/generate-response")
async def generate_auto_response(customer_id: str, incoming_message: str):
    """Generate intelligent auto-response based on customer character and context"""
    # Get customer and character
    customer = await customers_col().find_one({"id": customer_id}, {"_id": 0})
    char_col = get_db()['customer_characters']
    character = await char_col.find_one({"customer_id": customer_id}, {"_id": 0})
    
    customer_name = customer.get("name", "Pelanggan") if customer else "Pelanggan"
    
    # Analyze incoming message intent
    message_lower = incoming_message.lower()
    
    intent = "general"
    if any(w in message_lower for w in ["harga", "berapa", "price", "cost"]):
        intent = "price_inquiry"
    elif any(w in message_lower for w in ["promo", "diskon", "sale", "murah"]):
        intent = "promo_inquiry"
    elif any(w in message_lower for w in ["stok", "stock", "ada", "tersedia", "available"]):
        intent = "stock_inquiry"
    elif any(w in message_lower for w in ["komplain", "rusak", "kecewa", "tidak sesuai"]):
        intent = "complaint"
    elif any(w in message_lower for w in ["terima kasih", "thanks", "makasih"]):
        intent = "gratitude"
    elif any(w in message_lower for w in ["hai", "halo", "hello", "pagi", "siang", "sore", "malam"]):
        intent = "greeting"
    
    # Build response based on character
    comm_style = character.get("communication_style", "formal") if character else "formal"
    price_sens = character.get("price_sensitivity", "normal") if character else "normal"
    
    responses = {
        "greeting": {
            "formal": f"Selamat datang, Kak {customer_name}! Ada yang bisa kami bantu?",
            "casual": f"Hai Kak {customer_name}! Apa kabar? Ada yang bisa dibantu?",
            "brief": f"Halo Kak {customer_name}! Butuh bantuan?"
        },
        "price_inquiry": {
            "formal": f"Terima kasih Kak {customer_name} atas pertanyaannya. Berikut informasi harga produk kami...",
            "casual": f"Oke Kak {customer_name}! Ini ya harganya...",
            "brief": "Cek harga:"
        },
        "promo_inquiry": {
            "formal": f"Kak {customer_name}, saat ini kami memiliki promo menarik...",
            "casual": f"Wah pas banget Kak {customer_name}! Lagi ada promo nih...",
            "brief": "Promo aktif:"
        },
        "stock_inquiry": {
            "formal": f"Baik Kak {customer_name}, kami akan cek ketersediaan stok untuk Anda.",
            "casual": f"Oke Kak {customer_name}! Cek stok dulu ya...",
            "brief": "Cek stok:"
        },
        "complaint": {
            "formal": f"Mohon maaf atas ketidaknyamanan yang dialami, Kak {customer_name}. Kami akan segera menindaklanjuti.",
            "casual": f"Waduh, maaf banget ya Kak {customer_name}! Kita cek dulu masalahnya...",
            "brief": f"Maaf Kak {customer_name}. Akan kami proses."
        },
        "gratitude": {
            "formal": f"Sama-sama, Kak {customer_name}. Terima kasih telah berbelanja di OCB Group.",
            "casual": f"Sama-sama Kak {customer_name}! Ditunggu orderan berikutnya ya!",
            "brief": "Sama-sama!"
        },
        "general": {
            "formal": f"Terima kasih sudah menghubungi kami, Kak {customer_name}. Ada yang bisa kami bantu?",
            "casual": f"Hai Kak {customer_name}! Ada yang bisa dibantu?",
            "brief": "Ada yang bisa dibantu?"
        }
    }
    
    response = responses.get(intent, responses["general"]).get(comm_style, responses["general"]["formal"])
    
    # Add extra for price-sensitive customers
    if price_sens == "price_sensitive" and intent not in ["complaint", "gratitude"]:
        response += "\n\n💰 Psst... Kak ada promo spesial lho!"
    
    return {
        "customer_name": customer_name,
        "incoming_message": incoming_message,
        "detected_intent": intent,
        "customer_style": comm_style,
        "generated_response": response,
        "can_auto_send": intent in ["greeting", "gratitude"],
        "needs_review": intent in ["complaint", "price_inquiry", "stock_inquiry"]
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
