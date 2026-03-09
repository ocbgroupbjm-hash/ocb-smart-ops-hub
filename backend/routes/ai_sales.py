# OCB GROUP SUPER AI - Sales Engine Routes
# AI-powered automated sales system

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime, timezone, timedelta
import uuid
import json
import os

from database import get_db, get_active_db_name
from models.super_ai_models import (
    SalesConversation, SalesMessage, Invoice, InvoiceItem,
    Order, OrderItem, DeliveryInfo, ConversationStatus, 
    PaymentStatus, OrderStatus, DeliveryMethod
)

router = APIRouter(prefix="/api/ai-sales", tags=["AI Sales"])

# ==================== HELPER FUNCTIONS ====================

def gen_id() -> str:
    return str(uuid.uuid4())

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

async def get_product_by_id(product_id: str):
    db = get_db()
    return await db['products'].find_one({"id": product_id}, {"_id": 0})

async def get_customer_by_phone(phone: str):
    db = get_db()
    return await db['customers'].find_one({"phone": phone}, {"_id": 0})

async def generate_invoice_number():
    db = get_db()
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    
    # Get sequence
    result = await db['sequences'].find_one_and_update(
        {"_id": f"invoice_{today}"},
        {"$inc": {"value": 1}},
        upsert=True,
        return_document=True
    )
    seq = result.get("value", 1)
    return f"INV{today}{seq:04d}"

async def generate_order_number():
    db = get_db()
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    
    result = await db['sequences'].find_one_and_update(
        {"_id": f"order_{today}"},
        {"$inc": {"value": 1}},
        upsert=True,
        return_document=True
    )
    seq = result.get("value", 1)
    return f"ORD{today}{seq:04d}"

# ==================== AI SALES LOGIC ====================

async def analyze_customer_message(message: str, conversation: dict) -> dict:
    """Analyze customer message and determine intent"""
    message_lower = message.lower()
    
    # Intent detection
    intent = "browsing"
    if any(word in message_lower for word in ["beli", "pesan", "order", "mau", "ambil", "checkout"]):
        intent = "buying"
    elif any(word in message_lower for word in ["harga", "berapa", "price", "diskon", "promo"]):
        intent = "price_inquiry"
    elif any(word in message_lower for word in ["stok", "ada", "ready", "tersedia"]):
        intent = "stock_inquiry"
    elif any(word in message_lower for word in ["komplain", "rusak", "kecewa", "refund"]):
        intent = "complaint"
    
    # Sentiment
    sentiment = "neutral"
    if any(word in message_lower for word in ["terima kasih", "bagus", "mantap", "ok", "oke", "siap"]):
        sentiment = "positive"
    elif any(word in message_lower for word in ["kecewa", "buruk", "jelek", "lambat"]):
        sentiment = "negative"
    
    return {
        "intent": intent,
        "sentiment": sentiment,
        "urgency": "normal"
    }

async def get_product_recommendations(query: str = "", limit: int = 5) -> list:
    """Get product recommendations based on query"""
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
        {"_id": 0, "id": 1, "code": 1, "name": 1, "selling_price": 1, "image_url": 1}
    ).limit(limit).to_list(None)
    
    return products

async def generate_ai_response(conversation: dict, customer_message: str, analysis: dict) -> str:
    """Generate AI sales response"""
    intent = analysis.get("intent", "browsing")
    
    # Get recommended products
    products = await get_product_recommendations(customer_message, 3)
    
    if intent == "buying":
        if conversation.get("cart_items"):
            total = sum(item.get("subtotal", 0) for item in conversation["cart_items"])
            return f"""Baik kak, pesanan sudah saya catat:

{chr(10).join([f"• {item['product_name']} x {item['qty']} = Rp {item['subtotal']:,.0f}" for item in conversation['cart_items']])}

**Total: Rp {total:,.0f}**

Untuk melanjutkan, silakan ketik "CHECKOUT" atau tambah produk lain."""
        else:
            return "Silakan pilih produk yang ingin dibeli kak. Ketik nama produk atau kode produk."
    
    elif intent == "price_inquiry":
        if products:
            product_list = "\n".join([f"• {p['name']}: Rp {p['selling_price']:,.0f}" for p in products])
            return f"Berikut harga produk yang tersedia:\n\n{product_list}\n\nMau pesan yang mana kak?"
        return "Produk apa yang ingin kakak tanyakan harganya?"
    
    elif intent == "stock_inquiry":
        return "Stok tersedia kak. Mau langsung diorder?"
    
    elif intent == "complaint":
        return "Mohon maaf atas ketidaknyamanannya kak. Bisa dijelaskan lebih detail masalahnya? Kami akan segera bantu."
    
    else:
        # Default browsing response with recommendations
        if products:
            product_list = "\n".join([f"• {p['name']} - Rp {p['selling_price']:,.0f}" for p in products[:3]])
            return f"""Halo kak! Selamat datang di OCB GROUP 😊

Berikut produk yang mungkin kakak cari:

{product_list}

Ketik nama produk untuk info lebih detail, atau langsung ketik "BELI [nama produk]" untuk order."""
        
        return """Halo kak! Selamat datang di OCB GROUP 😊

Ada yang bisa saya bantu? Silakan tanyakan produk yang kakak cari atau ketik "PROMO" untuk lihat promo hari ini."""

# ==================== REQUEST MODELS ====================

class StartConversationRequest(BaseModel):
    customer_name: str = ""
    customer_phone: str = ""
    channel: str = "internal_chat"
    branch_id: Optional[str] = None

class SendMessageRequest(BaseModel):
    content: str
    message_type: str = "text"

class AddToCartRequest(BaseModel):
    product_id: str
    quantity: int = 1

class CheckoutRequest(BaseModel):
    delivery_method: str = "pickup"
    delivery_address: str = ""
    delivery_city: str = ""
    recipient_name: str = ""
    recipient_phone: str = ""
    pickup_branch_id: Optional[str] = None
    notes: str = ""

# ==================== ENDPOINTS ====================

@router.post("/conversation/start")
async def start_conversation(data: StartConversationRequest):
    """Start a new sales conversation"""
    db = get_db()
    
    conversation_id = gen_id()
    
    # Check if customer exists
    customer = None
    if data.customer_phone:
        customer = await get_customer_by_phone(data.customer_phone)
    
    conversation = {
        "id": conversation_id,
        "channel": data.channel,
        "status": "active",
        "customer_id": customer["id"] if customer else None,
        "customer_name": data.customer_name or (customer["name"] if customer else ""),
        "customer_phone": data.customer_phone,
        "customer_whatsapp": data.customer_phone,
        "messages": [],
        "interested_products": [],
        "recommended_products": [],
        "cart_items": [],
        "order_id": None,
        "invoice_id": None,
        "branch_id": data.branch_id,
        "assigned_agent_id": None,
        "customer_intent": "",
        "sentiment": "neutral",
        "urgency": "normal",
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "last_message_at": now_iso()
    }
    
    # Add welcome message
    welcome_msg = {
        "id": gen_id(),
        "role": "ai",
        "content": f"""Halo{' ' + data.customer_name if data.customer_name else ''} 👋

Selamat datang di **OCB GROUP** - Toko Handphone & Aksesoris Terlengkap!

Saya AI Sales Assistant yang siap membantu kakak. Silakan:
• Ketik nama produk untuk cari
• Ketik "PROMO" untuk lihat promo
• Ketik "KATALOG" untuk lihat semua produk

Ada yang bisa saya bantu?""",
        "message_type": "text",
        "metadata": {},
        "timestamp": now_iso()
    }
    conversation["messages"].append(welcome_msg)
    
    await db['sales_conversations'].insert_one(conversation)
    
    # Audit log
    await db['audit_logs'].insert_one({
        "id": gen_id(),
        "action": "create",
        "module": "ai_sales",
        "entity_type": "conversation",
        "entity_id": conversation_id,
        "is_system_action": True,
        "ai_module": "ai_sales",
        "new_value": {"customer_phone": data.customer_phone},
        "status": "completed",
        "timestamp": now_iso()
    })
    
    return {
        "conversation_id": conversation_id,
        "messages": conversation["messages"],
        "status": "active"
    }

@router.post("/conversation/{conversation_id}/message")
async def send_message(conversation_id: str, data: SendMessageRequest):
    """Send message to conversation and get AI response"""
    db = get_db()
    
    # Get conversation
    conversation = await db['sales_conversations'].find_one(
        {"id": conversation_id},
        {"_id": 0}
    )
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Add customer message
    customer_msg = {
        "id": gen_id(),
        "role": "customer",
        "content": data.content,
        "message_type": data.message_type,
        "metadata": {},
        "timestamp": now_iso()
    }
    
    # Analyze message
    analysis = await analyze_customer_message(data.content, conversation)
    
    # Handle special commands
    content_lower = data.content.lower().strip()
    ai_response = ""
    
    if content_lower == "checkout" and conversation.get("cart_items"):
        # Process checkout
        ai_response = """Siap kak, lanjut ke pembayaran ya!

Pilih metode pengiriman:
1. **PICKUP** - Ambil di toko
2. **KIRIM** - Dikirim ke alamat

Ketik pilihan (1/2) atau langsung ketik alamat lengkap untuk pengiriman."""
        
        await db['sales_conversations'].update_one(
            {"id": conversation_id},
            {"$set": {"status": "waiting_payment"}}
        )
    
    elif content_lower in ["1", "pickup", "ambil"]:
        if conversation.get("cart_items"):
            # Create invoice for pickup
            invoice = await create_invoice_from_cart(conversation, "pickup")
            ai_response = f"""Pesanan siap diproses! 🎉

**Invoice: {invoice['invoice_number']}**
Total: **Rp {invoice['total']:,.0f}**

Silakan bayar dengan QRIS di bawah ini:
[QRIS Payment akan muncul di sini]

Setelah bayar, ketik "SUDAH BAYAR" untuk konfirmasi."""
    
    elif content_lower.startswith("beli ") or content_lower.startswith("order "):
        # Try to add product to cart
        product_query = data.content[5:].strip() if content_lower.startswith("beli ") else data.content[6:].strip()
        products = await get_product_recommendations(product_query, 1)
        
        if products:
            product = products[0]
            cart_item = {
                "product_id": product["id"],
                "product_name": product["name"],
                "product_code": product.get("code", ""),
                "qty": 1,
                "unit_price": product["selling_price"],
                "subtotal": product["selling_price"]
            }
            
            # Add to cart
            current_cart = conversation.get("cart_items", [])
            current_cart.append(cart_item)
            
            await db['sales_conversations'].update_one(
                {"id": conversation_id},
                {"$set": {"cart_items": current_cart}}
            )
            
            conversation["cart_items"] = current_cart
            
            total = sum(item["subtotal"] for item in current_cart)
            ai_response = f"""✅ Berhasil ditambahkan ke keranjang!

**{product['name']}**
Harga: Rp {product['selling_price']:,.0f}

🛒 **Keranjang Belanja:**
{chr(10).join([f"• {item['product_name']} x {item['qty']} = Rp {item['subtotal']:,.0f}" for item in current_cart])}

**Total: Rp {total:,.0f}**

Tambah produk lain atau ketik "CHECKOUT" untuk bayar."""
        else:
            ai_response = f"Maaf kak, produk '{product_query}' tidak ditemukan. Coba ketik nama lain atau ketik 'KATALOG' untuk lihat semua produk."
    
    elif content_lower == "katalog" or content_lower == "produk":
        products = await get_product_recommendations("", 10)
        if products:
            product_list = "\n".join([f"• **{p['name']}** - Rp {p['selling_price']:,.0f}" for p in products])
            ai_response = f"""📦 **Katalog Produk OCB GROUP:**

{product_list}

Ketik "BELI [nama produk]" untuk order."""
        else:
            ai_response = "Katalog sedang dimuat, coba lagi nanti ya kak."
    
    elif content_lower == "promo":
        ai_response = """🔥 **PROMO HARI INI:**

• Diskon 10% untuk pembelian HP
• Gratis Tempered Glass untuk pembelian > Rp 2jt
• Cashback 5% untuk member VIP

Mau order sekarang kak?"""
    
    elif content_lower == "keranjang" or content_lower == "cart":
        cart = conversation.get("cart_items", [])
        if cart:
            total = sum(item["subtotal"] for item in cart)
            ai_response = f"""🛒 **Keranjang Belanja:**

{chr(10).join([f"• {item['product_name']} x {item['qty']} = Rp {item['subtotal']:,.0f}" for item in cart])}

**Total: Rp {total:,.0f}**

Ketik "CHECKOUT" untuk bayar atau tambah produk lain."""
        else:
            ai_response = "Keranjang masih kosong kak. Ketik 'KATALOG' untuk lihat produk atau 'BELI [nama produk]' untuk order."
    
    else:
        # Generate AI response
        ai_response = await generate_ai_response(conversation, data.content, analysis)
    
    # Add AI response
    ai_msg = {
        "id": gen_id(),
        "role": "ai",
        "content": ai_response,
        "message_type": "text",
        "metadata": {"analysis": analysis},
        "timestamp": now_iso()
    }
    
    # Update conversation
    await db['sales_conversations'].update_one(
        {"id": conversation_id},
        {
            "$push": {"messages": {"$each": [customer_msg, ai_msg]}},
            "$set": {
                "customer_intent": analysis["intent"],
                "sentiment": analysis["sentiment"],
                "updated_at": now_iso(),
                "last_message_at": now_iso()
            }
        }
    )
    
    return {
        "customer_message": customer_msg,
        "ai_response": ai_msg,
        "cart_items": conversation.get("cart_items", []),
        "analysis": analysis
    }

@router.get("/conversation/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get conversation details"""
    db = get_db()
    
    conversation = await db['sales_conversations'].find_one(
        {"id": conversation_id},
        {"_id": 0}
    )
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return conversation

@router.get("/conversations")
async def list_conversations(
    status: Optional[str] = None,
    channel: Optional[str] = None,
    limit: int = 50
):
    """List all conversations"""
    db = get_db()
    
    filter_query = {}
    if status:
        filter_query["status"] = status
    if channel:
        filter_query["channel"] = channel
    
    conversations = await db['sales_conversations'].find(
        filter_query,
        {"_id": 0}
    ).sort("last_message_at", -1).limit(limit).to_list(None)
    
    return {"conversations": conversations, "total": len(conversations)}

@router.post("/conversation/{conversation_id}/cart/add")
async def add_to_cart(conversation_id: str, data: AddToCartRequest):
    """Add product to cart"""
    db = get_db()
    
    # Get product
    product = await get_product_by_id(data.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Get conversation
    conversation = await db['sales_conversations'].find_one(
        {"id": conversation_id},
        {"_id": 0}
    )
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Add to cart
    cart_item = {
        "product_id": product["id"],
        "product_name": product["name"],
        "product_code": product.get("code", ""),
        "qty": data.quantity,
        "unit_price": product["selling_price"],
        "subtotal": product["selling_price"] * data.quantity
    }
    
    current_cart = conversation.get("cart_items", [])
    
    # Check if product already in cart
    existing_idx = next((i for i, item in enumerate(current_cart) if item["product_id"] == data.product_id), None)
    if existing_idx is not None:
        current_cart[existing_idx]["qty"] += data.quantity
        current_cart[existing_idx]["subtotal"] = current_cart[existing_idx]["unit_price"] * current_cart[existing_idx]["qty"]
    else:
        current_cart.append(cart_item)
    
    await db['sales_conversations'].update_one(
        {"id": conversation_id},
        {"$set": {"cart_items": current_cart, "updated_at": now_iso()}}
    )
    
    total = sum(item["subtotal"] for item in current_cart)
    
    return {
        "cart_items": current_cart,
        "total": total,
        "message": f"{product['name']} ditambahkan ke keranjang"
    }

async def create_invoice_from_cart(conversation: dict, delivery_method: str = "pickup") -> dict:
    """Create invoice from cart items"""
    db = get_db()
    
    invoice_number = await generate_invoice_number()
    
    items = []
    subtotal = 0
    for cart_item in conversation.get("cart_items", []):
        item = {
            "product_id": cart_item["product_id"],
            "product_name": cart_item["product_name"],
            "quantity": cart_item["qty"],
            "unit_price": cart_item["unit_price"],
            "discount": 0,
            "subtotal": cart_item["subtotal"]
        }
        items.append(item)
        subtotal += cart_item["subtotal"]
    
    # Calculate tax (11%)
    tax_amount = subtotal * 0.11
    total = subtotal + tax_amount
    
    # Generate mock QRIS
    qris_code = f"QRIS{invoice_number}"
    qris_expired = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
    
    invoice = {
        "id": gen_id(),
        "invoice_number": invoice_number,
        "customer_id": conversation.get("customer_id"),
        "customer_name": conversation.get("customer_name", ""),
        "customer_phone": conversation.get("customer_phone", ""),
        "customer_email": "",
        "items": items,
        "subtotal": subtotal,
        "discount_amount": 0,
        "tax_amount": tax_amount,
        "shipping_cost": 0,
        "total": total,
        "payment_status": "pending",
        "payment_method": "qris",
        "qris_code": qris_code,
        "qris_image_url": f"/api/qris/generate/{qris_code}",
        "qris_expired_at": qris_expired,
        "conversation_id": conversation["id"],
        "channel": conversation.get("channel", "internal_chat"),
        "branch_id": conversation.get("branch_id"),
        "created_at": now_iso(),
        "updated_at": now_iso()
    }
    
    await db['invoices'].insert_one(invoice)
    
    # Update conversation
    await db['sales_conversations'].update_one(
        {"id": conversation["id"]},
        {"$set": {"invoice_id": invoice["id"], "status": "waiting_payment"}}
    )
    
    return invoice

@router.post("/conversation/{conversation_id}/checkout")
async def checkout(conversation_id: str, data: CheckoutRequest):
    """Process checkout and create invoice"""
    db = get_db()
    
    conversation = await db['sales_conversations'].find_one(
        {"id": conversation_id},
        {"_id": 0}
    )
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if not conversation.get("cart_items"):
        raise HTTPException(status_code=400, detail="Cart is empty")
    
    # Create invoice
    invoice = await create_invoice_from_cart(conversation, data.delivery_method)
    
    # Create order
    order_number = await generate_order_number()
    
    order_items = []
    for cart_item in conversation.get("cart_items", []):
        order_items.append({
            "product_id": cart_item["product_id"],
            "product_name": cart_item["product_name"],
            "product_code": cart_item.get("product_code", ""),
            "quantity": cart_item["qty"],
            "unit_price": cart_item["unit_price"],
            "subtotal": cart_item["subtotal"],
            "serial_numbers": []
        })
    
    order = {
        "id": gen_id(),
        "order_number": order_number,
        "customer_id": conversation.get("customer_id"),
        "customer_name": conversation.get("customer_name", ""),
        "customer_phone": conversation.get("customer_phone", ""),
        "items": order_items,
        "subtotal": invoice["subtotal"],
        "discount_amount": 0,
        "tax_amount": invoice["tax_amount"],
        "shipping_cost": 0,
        "total": invoice["total"],
        "invoice_id": invoice["id"],
        "payment_status": "pending",
        "delivery": {
            "method": data.delivery_method,
            "courier_name": "",
            "tracking_number": "",
            "pickup_code": f"PCK{order_number[-6:]}" if data.delivery_method == "pickup" else "",
            "recipient_name": data.recipient_name or conversation.get("customer_name", ""),
            "recipient_phone": data.recipient_phone or conversation.get("customer_phone", ""),
            "address": data.delivery_address,
            "city": data.delivery_city,
            "postal_code": "",
            "pickup_branch_id": data.pickup_branch_id,
            "pickup_branch_name": ""
        },
        "status": "pending",
        "conversation_id": conversation_id,
        "channel": conversation.get("channel", "internal_chat"),
        "branch_id": conversation.get("branch_id"),
        "customer_notes": data.notes,
        "internal_notes": "",
        "created_at": now_iso(),
        "updated_at": now_iso()
    }
    
    await db['orders'].insert_one(order)
    
    # Update conversation
    await db['sales_conversations'].update_one(
        {"id": conversation_id},
        {"$set": {"order_id": order["id"]}}
    )
    
    return {
        "order": order,
        "invoice": invoice,
        "message": f"Order {order_number} berhasil dibuat. Silakan lakukan pembayaran."
    }

@router.post("/payment/confirm/{invoice_id}")
async def confirm_payment(invoice_id: str):
    """Confirm payment (for testing/mock)"""
    db = get_db()
    
    invoice = await db['invoices'].find_one({"id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Update invoice
    await db['invoices'].update_one(
        {"id": invoice_id},
        {"$set": {
            "payment_status": "paid",
            "paid_at": now_iso(),
            "updated_at": now_iso()
        }}
    )
    
    # Update order
    if invoice.get("conversation_id"):
        conversation = await db['sales_conversations'].find_one(
            {"id": invoice["conversation_id"]},
            {"_id": 0}
        )
        
        if conversation and conversation.get("order_id"):
            await db['orders'].update_one(
                {"id": conversation["order_id"]},
                {"$set": {
                    "payment_status": "paid",
                    "status": "processing",
                    "updated_at": now_iso()
                }}
            )
        
        # Update conversation
        await db['sales_conversations'].update_one(
            {"id": invoice["conversation_id"]},
            {"$set": {"status": "completed", "updated_at": now_iso()}}
        )
    
    # Record to ERP (create transaction record)
    transaction = {
        "id": gen_id(),
        "invoice_number": invoice["invoice_number"],
        "branch_id": invoice.get("branch_id"),
        "cashier_id": "AI_SALES",
        "cashier_name": "AI Sales System",
        "customer_id": invoice.get("customer_id"),
        "customer_name": invoice.get("customer_name", ""),
        "customer_phone": invoice.get("customer_phone", ""),
        "items": invoice["items"],
        "subtotal": invoice["subtotal"],
        "discount_amount": invoice["discount_amount"],
        "tax_amount": invoice["tax_amount"],
        "total": invoice["total"],
        "payments": [{"method": "qris", "amount": invoice["total"], "reference": invoice.get("qris_code", "")}],
        "paid_amount": invoice["total"],
        "change_amount": 0,
        "status": "completed",
        "created_at": now_iso(),
        "updated_at": now_iso()
    }
    
    await db['transactions'].insert_one(transaction)
    
    # Audit log
    await db['audit_logs'].insert_one({
        "id": gen_id(),
        "action": "payment_confirmed",
        "module": "ai_sales",
        "entity_type": "invoice",
        "entity_id": invoice_id,
        "is_system_action": True,
        "ai_module": "ai_sales",
        "new_value": {"total": invoice["total"], "payment_method": "qris"},
        "status": "completed",
        "timestamp": now_iso()
    })
    
    return {
        "message": "Pembayaran berhasil dikonfirmasi",
        "invoice": invoice,
        "transaction_id": transaction["id"]
    }

@router.get("/orders")
async def list_orders(
    status: Optional[str] = None,
    limit: int = 50
):
    """List all orders"""
    db = get_db()
    
    filter_query = {}
    if status:
        filter_query["status"] = status
    
    orders = await db['orders'].find(
        filter_query,
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(None)
    
    return {"orders": orders, "total": len(orders)}

@router.get("/invoices")
async def list_invoices(
    status: Optional[str] = None,
    limit: int = 50
):
    """List all invoices"""
    db = get_db()
    
    filter_query = {}
    if status:
        filter_query["payment_status"] = status
    
    invoices = await db['invoices'].find(
        filter_query,
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(None)
    
    return {"invoices": invoices, "total": len(invoices)}
