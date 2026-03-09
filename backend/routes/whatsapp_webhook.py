# OCB GROUP SUPER AI - WhatsApp Webhook for n8n Integration
# Endpoint khusus untuk menerima pesan dari WhatsApp via n8n

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime, timezone
import uuid
import os

from database import get_db

router = APIRouter(prefix="/api/webhook", tags=["WhatsApp Webhook"])

# Simple API Key for webhook security (optional)
WEBHOOK_API_KEY = os.environ.get("WEBHOOK_API_KEY", "ocb-webhook-secret-2026")

def gen_id() -> str:
    return str(uuid.uuid4())

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

# ==================== REQUEST/RESPONSE MODELS ====================

class WhatsAppIncomingMessage(BaseModel):
    phone_number: str  # Format: 628xxxxxxxxxx
    message: str
    customer_name: Optional[str] = None  # Opsional, bisa diisi dari WA profile

class WhatsAppResponse(BaseModel):
    success: bool
    phone_number: str
    reply_message: str
    conversation_id: str
    customer_name: str
    intent: str
    cart_total: float = 0
    cart_items: int = 0

# ==================== AI LOGIC ====================

async def get_or_create_conversation(phone: str, name: str = "") -> dict:
    """Get existing conversation or create new one for this phone number"""
    db = get_db()
    
    # Find active conversation for this phone
    conversation = await db['sales_conversations'].find_one(
        {"customer_phone": phone, "status": {"$in": ["active", "waiting_payment"]}},
        {"_id": 0}
    )
    
    if conversation:
        return conversation
    
    # Create new conversation
    conversation_id = gen_id()
    
    # Check if customer exists
    customer = await db['customers'].find_one({"phone": phone}, {"_id": 0})
    
    conversation = {
        "id": conversation_id,
        "channel": "whatsapp",
        "status": "active",
        "customer_id": customer["id"] if customer else None,
        "customer_name": name or (customer["name"] if customer else ""),
        "customer_phone": phone,
        "customer_whatsapp": phone,
        "messages": [],
        "interested_products": [],
        "recommended_products": [],
        "cart_items": [],
        "order_id": None,
        "invoice_id": None,
        "branch_id": None,
        "assigned_agent_id": None,
        "customer_intent": "",
        "sentiment": "neutral",
        "urgency": "normal",
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "last_message_at": now_iso()
    }
    
    await db['sales_conversations'].insert_one(conversation)
    return conversation

async def analyze_message(message: str) -> dict:
    """Analyze customer message intent"""
    msg_lower = message.lower().strip()
    
    intent = "browsing"
    if any(word in msg_lower for word in ["beli", "pesan", "order", "mau", "ambil", "checkout", "bayar"]):
        intent = "buying"
    elif any(word in msg_lower for word in ["harga", "berapa", "price", "diskon", "promo"]):
        intent = "price_inquiry"
    elif any(word in msg_lower for word in ["stok", "ada", "ready", "tersedia", "available"]):
        intent = "stock_inquiry"
    elif any(word in msg_lower for word in ["komplain", "rusak", "kecewa", "refund", "cancel"]):
        intent = "complaint"
    elif any(word in msg_lower for word in ["katalog", "produk", "list", "daftar"]):
        intent = "catalog_request"
    elif any(word in msg_lower for word in ["keranjang", "cart"]):
        intent = "cart_check"
    elif any(word in msg_lower for word in ["promo", "diskon", "sale"]):
        intent = "promo_inquiry"
    
    sentiment = "neutral"
    if any(word in msg_lower for word in ["terima kasih", "bagus", "mantap", "ok", "oke", "siap", "makasih"]):
        sentiment = "positive"
    elif any(word in msg_lower for word in ["kecewa", "buruk", "jelek", "lambat", "mahal"]):
        sentiment = "negative"
    
    return {"intent": intent, "sentiment": sentiment}

async def get_product_list(query: str = "", limit: int = 5) -> list:
    """Get products for recommendation"""
    db = get_db()
    
    filter_query = {"is_active": True}
    if query:
        filter_query["$or"] = [
            {"name": {"$regex": query, "$options": "i"}},
            {"code": {"$regex": query, "$options": "i"}},
            {"brand": {"$regex": query, "$options": "i"}}
        ]
    
    products = await db['products'].find(
        filter_query,
        {"_id": 0, "id": 1, "code": 1, "name": 1, "selling_price": 1}
    ).limit(limit).to_list(None)
    
    return products

async def generate_ai_reply(conversation: dict, message: str, analysis: dict) -> str:
    """Generate AI response based on message intent"""
    intent = analysis.get("intent", "browsing")
    msg_lower = message.lower().strip()
    
    # Handle special commands
    if intent == "catalog_request" or msg_lower in ["katalog", "produk", "menu"]:
        products = await get_product_list("", 10)
        if products:
            product_list = "\n".join([f"• {p['name']} - Rp {p['selling_price']:,.0f}" for p in products])
            return f"""📦 *KATALOG PRODUK OCB GROUP*

{product_list}

Ketik *BELI [nama produk]* untuk order.
Contoh: BELI Telkomsel 10GB"""
        return "Maaf, katalog sedang dimuat. Coba lagi nanti ya kak."
    
    if intent == "promo_inquiry" or msg_lower == "promo":
        return """🔥 *PROMO HARI INI!*

• Diskon 10% untuk pembelian HP
• Gratis Tempered Glass pembelian > Rp 2jt
• Cashback 5% untuk member VIP

Mau order sekarang kak? Ketik *KATALOG* untuk lihat produk."""
    
    if intent == "cart_check" or msg_lower in ["keranjang", "cart"]:
        cart = conversation.get("cart_items", [])
        if cart:
            total = sum(item.get("subtotal", 0) for item in cart)
            items = "\n".join([f"• {item['product_name']} x {item['qty']} = Rp {item['subtotal']:,.0f}" for item in cart])
            return f"""🛒 *KERANJANG BELANJA*

{items}

*Total: Rp {total:,.0f}*

Ketik *CHECKOUT* untuk bayar atau tambah produk lain."""
        return "Keranjang masih kosong kak. Ketik *KATALOG* untuk lihat produk."
    
    if msg_lower.startswith("beli ") or msg_lower.startswith("order "):
        product_query = message[5:].strip() if msg_lower.startswith("beli ") else message[6:].strip()
        products = await get_product_list(product_query, 1)
        
        if products:
            product = products[0]
            return f"""✅ *PRODUK DITEMUKAN!*

*{product['name']}*
Harga: Rp {product['selling_price']:,.0f}

Ketik *YA* untuk tambah ke keranjang.
Ketik *KATALOG* untuk lihat produk lain."""
        return f"Maaf kak, produk '{product_query}' tidak ditemukan. Coba ketik *KATALOG* untuk lihat daftar produk."
    
    if msg_lower in ["ya", "ok", "oke", "yes", "iya"]:
        return """✅ Produk ditambahkan ke keranjang!

Ketik *KERANJANG* untuk lihat isi.
Ketik *CHECKOUT* untuk bayar.
Atau tambah produk lain dengan *BELI [nama produk]*."""
    
    if msg_lower == "checkout":
        cart = conversation.get("cart_items", [])
        if cart:
            total = sum(item.get("subtotal", 0) for item in cart)
            return f"""💳 *CHECKOUT*

Total: *Rp {total:,.0f}*

Pilih metode:
1️⃣ *PICKUP* - Ambil di toko
2️⃣ *KIRIM* - Dikirim ke alamat

Ketik pilihan (1 atau 2)."""
        return "Keranjang kosong. Ketik *KATALOG* untuk lihat produk."
    
    if msg_lower in ["1", "pickup"]:
        return """📍 *PICKUP DI TOKO*

Pesanan Anda akan disiapkan.
Kode pickup: *PCK123456*

Silakan datang ke OCB Store terdekat dengan menunjukkan kode ini.

Terima kasih sudah berbelanja! 🙏"""
    
    if msg_lower in ["2", "kirim"]:
        return """🚚 *PENGIRIMAN*

Silakan kirim alamat lengkap Anda:
- Nama penerima
- Alamat
- Kota
- Kode pos
- No HP

Contoh:
Budi
Jl. Sudirman No. 123
Banjarmasin
70111
08123456789"""
    
    if intent == "complaint":
        return """Mohon maaf atas ketidaknyamanannya kak 🙏

Bisa dijelaskan lebih detail masalahnya? Tim kami akan segera membantu.

Atau hubungi CS kami di:
📞 0812-3456-7890
📧 cs@ocbgroup.co.id"""
    
    # Default greeting/browsing response
    return f"""Halo kak! 👋 Selamat datang di *OCB GROUP*

Saya AI Assistant yang siap membantu.

Ketik salah satu:
• *KATALOG* - Lihat daftar produk
• *PROMO* - Lihat promo hari ini
• *BELI [nama]* - Order produk

Ada yang bisa saya bantu?"""

# ==================== WEBHOOK ENDPOINT ====================

@router.post("/whatsapp/incoming", response_model=WhatsAppResponse)
async def handle_whatsapp_message(
    data: WhatsAppIncomingMessage,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
):
    """
    Endpoint untuk menerima pesan WhatsApp dari n8n
    
    Request:
    POST /api/webhook/whatsapp/incoming
    Headers:
        Content-Type: application/json
        X-API-Key: ocb-webhook-secret-2026 (optional)
    Body:
        {
            "phone_number": "628123456789",
            "message": "Halo",
            "customer_name": "Budi" (optional)
        }
    
    Response:
        {
            "success": true,
            "phone_number": "628123456789",
            "reply_message": "Halo kak! Selamat datang...",
            "conversation_id": "uuid",
            "customer_name": "Budi",
            "intent": "browsing",
            "cart_total": 0,
            "cart_items": 0
        }
    """
    db = get_db()
    
    # Validate API key (optional - can be disabled)
    # if x_api_key != WEBHOOK_API_KEY:
    #     raise HTTPException(status_code=401, detail="Invalid API Key")
    
    # Normalize phone number
    phone = data.phone_number.strip()
    if phone.startswith("0"):
        phone = "62" + phone[1:]
    if not phone.startswith("62"):
        phone = "62" + phone
    
    try:
        # Get or create conversation
        conversation = await get_or_create_conversation(phone, data.customer_name or "")
        
        # Analyze message
        analysis = await analyze_message(data.message)
        
        # Generate AI reply
        reply = await generate_ai_reply(conversation, data.message, analysis)
        
        # Save messages to conversation
        customer_msg = {
            "id": gen_id(),
            "role": "customer",
            "content": data.message,
            "message_type": "text",
            "channel": "whatsapp",
            "timestamp": now_iso()
        }
        
        ai_msg = {
            "id": gen_id(),
            "role": "ai",
            "content": reply,
            "message_type": "text",
            "channel": "whatsapp",
            "timestamp": now_iso()
        }
        
        # Update conversation
        await db['sales_conversations'].update_one(
            {"id": conversation["id"]},
            {
                "$push": {"messages": {"$each": [customer_msg, ai_msg]}},
                "$set": {
                    "customer_intent": analysis["intent"],
                    "sentiment": analysis["sentiment"],
                    "customer_name": data.customer_name or conversation.get("customer_name", ""),
                    "updated_at": now_iso(),
                    "last_message_at": now_iso()
                }
            }
        )
        
        # Log to audit
        await db['audit_logs'].insert_one({
            "id": gen_id(),
            "action": "whatsapp_message",
            "module": "ai_sales",
            "entity_type": "conversation",
            "entity_id": conversation["id"],
            "is_system_action": True,
            "ai_module": "whatsapp_webhook",
            "new_value": {
                "phone": phone,
                "message": data.message[:100],
                "intent": analysis["intent"]
            },
            "status": "completed",
            "timestamp": now_iso()
        })
        
        # Calculate cart info
        cart = conversation.get("cart_items", [])
        cart_total = sum(item.get("subtotal", 0) for item in cart)
        
        return WhatsAppResponse(
            success=True,
            phone_number=phone,
            reply_message=reply,
            conversation_id=conversation["id"],
            customer_name=data.customer_name or conversation.get("customer_name", "Customer"),
            intent=analysis["intent"],
            cart_total=cart_total,
            cart_items=len(cart)
        )
        
    except Exception as e:
        # Return error response
        return WhatsAppResponse(
            success=False,
            phone_number=phone,
            reply_message=f"Maaf, terjadi kesalahan. Silakan coba lagi atau hubungi CS kami.",
            conversation_id="",
            customer_name=data.customer_name or "Customer",
            intent="error",
            cart_total=0,
            cart_items=0
        )

@router.get("/whatsapp/health")
async def webhook_health():
    """Health check endpoint untuk n8n"""
    return {
        "status": "healthy",
        "service": "OCB GROUP WhatsApp Webhook",
        "timestamp": now_iso()
    }

@router.get("/whatsapp/conversation/{phone}")
async def get_conversation_by_phone(phone: str):
    """Get conversation history by phone number"""
    db = get_db()
    
    # Normalize phone
    if phone.startswith("0"):
        phone = "62" + phone[1:]
    if not phone.startswith("62"):
        phone = "62" + phone
    
    conversation = await db['sales_conversations'].find_one(
        {"customer_phone": phone},
        {"_id": 0}
    )
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return conversation
