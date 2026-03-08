# OCB AI TITAN - Hallo AI Routes
# API endpoints untuk Hallo AI - Enterprise AI System

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from services.hallo_ai_service import HalloAIService
from utils.auth import get_current_user
from database import db
from datetime import datetime, timezone
import uuid

router = APIRouter(prefix="/hallo-ai", tags=["Hallo AI"])

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    persona: str = "analyst"  # ceo, cfo, coo, cmo, sales, customer_service, analyst

class ChatResponse(BaseModel):
    success: bool
    response: str
    persona: str
    session_id: str

class QuickInsightRequest(BaseModel):
    insight_type: str  # sales_today, low_stock, best_sellers

# Store for chat sessions
chat_sessions = db["hallo_ai_sessions"]

@router.get("/personas")
async def get_personas(current_user: dict = Depends(get_current_user)):
    """Get available AI personas"""
    personas = [
        {
            "id": "ceo",
            "name": "CEO AI",
            "icon": "crown",
            "description": "Analisis strategis, performa cabang, rekomendasi bisnis",
            "color": "amber"
        },
        {
            "id": "cfo",
            "name": "CFO AI", 
            "icon": "dollar-sign",
            "description": "Laporan keuangan, laba rugi, arus kas, margin",
            "color": "green"
        },
        {
            "id": "coo",
            "name": "COO AI",
            "icon": "settings",
            "description": "Monitoring operasional, stok, transaksi kasir",
            "color": "blue"
        },
        {
            "id": "cmo",
            "name": "Marketing AI",
            "icon": "megaphone",
            "description": "Produk terlaris, strategi promo, bundling",
            "color": "purple"
        },
        {
            "id": "sales",
            "name": "Sales AI",
            "icon": "shopping-cart",
            "description": "Upselling, cross-selling, rekomendasi produk",
            "color": "orange"
        },
        {
            "id": "customer_service",
            "name": "Customer Service AI",
            "icon": "headphones",
            "description": "Cek harga, stok, informasi produk",
            "color": "cyan"
        },
        {
            "id": "analyst",
            "name": "Business Analyst AI",
            "icon": "bar-chart",
            "description": "Analisis data mendalam, trend, forecasting",
            "color": "pink"
        }
    ]
    return personas

@router.post("/chat", response_model=ChatResponse)
async def chat_with_hallo_ai(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    """Chat dengan Hallo AI"""
    
    # Generate session ID jika tidak ada
    session_id = request.session_id or f"session_{uuid.uuid4().hex[:12]}"
    
    # Inisialisasi service
    service = HalloAIService(
        user_id=current_user.get("id"),
        branch_id=current_user.get("branch_id"),
        user_role=current_user.get("role", "cashier")
    )
    
    # Chat dengan AI
    result = await service.chat(
        message=request.message,
        session_id=session_id,
        persona=request.persona
    )
    
    # Simpan ke history
    await chat_sessions.insert_one({
        "session_id": session_id,
        "user_id": current_user.get("id"),
        "persona": request.persona,
        "user_message": request.message,
        "ai_response": result.get("response", ""),
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return ChatResponse(
        success=result.get("success", False),
        response=result.get("response", "Maaf, terjadi kesalahan"),
        persona=result.get("persona", "AI"),
        session_id=session_id
    )

@router.get("/sessions")
async def get_chat_sessions(current_user: dict = Depends(get_current_user)):
    """Get user's chat sessions"""
    sessions = await chat_sessions.aggregate([
        {"$match": {"user_id": current_user.get("id")}},
        {"$sort": {"created_at": -1}},
        {"$group": {
            "_id": "$session_id",
            "persona": {"$first": "$persona"},
            "last_message": {"$first": "$user_message"},
            "last_response": {"$first": "$ai_response"},
            "created_at": {"$first": "$created_at"},
            "message_count": {"$sum": 1}
        }},
        {"$sort": {"created_at": -1}},
        {"$limit": 20}
    ]).to_list(20)
    
    return [
        {
            "session_id": s["_id"],
            "persona": s["persona"],
            "last_message": s["last_message"][:100] + "..." if len(s["last_message"]) > 100 else s["last_message"],
            "message_count": s["message_count"],
            "created_at": s["created_at"]
        }
        for s in sessions
    ]

@router.get("/sessions/{session_id}/history")
async def get_session_history(session_id: str, current_user: dict = Depends(get_current_user)):
    """Get chat history for a session"""
    messages = await chat_sessions.find(
        {"session_id": session_id, "user_id": current_user.get("id")},
        {"_id": 0}
    ).sort("created_at", 1).to_list(100)
    
    history = []
    for msg in messages:
        history.append({"role": "user", "content": msg["user_message"], "timestamp": msg["created_at"]})
        history.append({"role": "assistant", "content": msg["ai_response"], "timestamp": msg["created_at"]})
    
    return {"session_id": session_id, "messages": history}

@router.post("/quick-insight")
async def get_quick_insight(request: QuickInsightRequest, current_user: dict = Depends(get_current_user)):
    """Get quick AI insight without full chat"""
    
    service = HalloAIService(
        user_id=current_user.get("id"),
        branch_id=current_user.get("branch_id"),
        user_role=current_user.get("role", "cashier")
    )
    
    insight = await service.get_quick_insight(request.insight_type)
    return insight

@router.get("/suggested-questions")
async def get_suggested_questions(persona: str = "analyst", current_user: dict = Depends(get_current_user)):
    """Get suggested questions based on persona"""
    
    suggestions = {
        "ceo": [
            "Bagaimana performa bisnis bulan ini?",
            "Cabang mana yang paling menguntungkan?",
            "Apa rekomendasi strategi untuk meningkatkan penjualan?",
            "Apakah ada cabang yang perlu perhatian khusus?",
            "Berapa pertumbuhan bisnis dibanding bulan lalu?"
        ],
        "cfo": [
            "Berapa laba bersih bulan ini?",
            "Bagaimana arus kas perusahaan?",
            "Produk mana yang memiliki margin tertinggi?",
            "Berapa total pengeluaran operasional?",
            "Cabang mana yang paling efisien secara keuangan?"
        ],
        "coo": [
            "Produk apa saja yang stoknya menipis?",
            "Berapa total transaksi hari ini?",
            "Apakah ada masalah operasional di cabang?",
            "Kasir mana yang performanya terbaik?",
            "Berapa rata-rata waktu transaksi?"
        ],
        "cmo": [
            "Apa produk terlaris minggu ini?",
            "Rekomendasi promo untuk meningkatkan penjualan?",
            "Produk apa yang bisa di-bundling bersama?",
            "Bagaimana trend penjualan per kategori?",
            "Kapan waktu terbaik untuk promosi?"
        ],
        "sales": [
            "Produk apa yang cocok untuk upselling?",
            "Rekomendasi produk tambahan untuk pelanggan",
            "Tips untuk meningkatkan nilai transaksi?",
            "Produk apa yang sering dibeli bersamaan?",
            "Bagaimana cara closing yang efektif?"
        ],
        "customer_service": [
            "Berapa harga [nama produk]?",
            "Apakah [nama produk] tersedia?",
            "Produk apa yang cocok untuk [kebutuhan]?",
            "Berapa stok [nama produk]?",
            "Apa promo yang sedang berlangsung?"
        ],
        "analyst": [
            "Analisis trend penjualan 3 bulan terakhir",
            "Prediksi penjualan bulan depan",
            "Produk mana yang perlu di-discontinue?",
            "Analisis customer behavior",
            "KPI apa yang perlu diperbaiki?"
        ]
    }
    
    return {
        "persona": persona,
        "suggestions": suggestions.get(persona, suggestions["analyst"])
    }

@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a chat session"""
    result = await chat_sessions.delete_many({
        "session_id": session_id,
        "user_id": current_user.get("id")
    })
    
    return {"deleted": result.deleted_count > 0, "message": "Sesi chat dihapus"}
