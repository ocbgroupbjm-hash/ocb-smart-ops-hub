# OCB TITAN ERP - AI Insight Engine
# AI-powered business analytics - READ ONLY, NO WRITE ACCESS
# MASTER BLUEPRINT: AI can only read, analyze, recommend - never write to database

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from database import get_db
from utils.auth import get_current_user
from routes.rbac_middleware import require_permission
import os
import json
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/ai", tags=["AI Insight Engine"])

# ==================== AI TOOLS FOR DATA RETRIEVAL ====================

class AITools:
    """
    AI Tools - READ ONLY functions for data retrieval
    These tools are used by AI to gather data for analysis
    """
    
    def __init__(self, db, user: dict):
        self.db = db
        self.user = user
        self.tenant_id = db.name
    
    async def get_trial_balance(self, as_of_date: str = None) -> dict:
        """Get trial balance data"""
        query = {"status": "posted"}
        if as_of_date:
            query["journal_date"] = {"$lte": as_of_date + "T23:59:59"}
        
        journals = await self.db["journal_entries"].find(query, {"_id": 0}).to_list(100000)
        
        account_balances = {}
        for journal in journals:
            for entry in journal.get("entries", []):
                code = entry.get("account_code", "")
                name = entry.get("account_name", "")
                if not code:
                    continue
                
                if code not in account_balances:
                    account_balances[code] = {"name": name, "debit": 0, "credit": 0}
                
                account_balances[code]["debit"] += entry.get("debit", 0)
                account_balances[code]["credit"] += entry.get("credit", 0)
        
        total_debit = sum(a["debit"] for a in account_balances.values())
        total_credit = sum(a["credit"] for a in account_balances.values())
        
        return {
            "as_of_date": as_of_date or datetime.now().strftime("%Y-%m-%d"),
            "accounts": [
                {"code": k, "name": v["name"], "debit": v["debit"], "credit": v["credit"]}
                for k, v in sorted(account_balances.items())
            ],
            "total_debit": total_debit,
            "total_credit": total_credit,
            "is_balanced": abs(total_debit - total_credit) < 0.01
        }
    
    async def get_sales_summary(self, days: int = 30, branch_id: str = None) -> dict:
        """Get sales summary for last N days"""
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        query = {
            "invoice_date": {"$gte": start_date.isoformat(), "$lte": end_date.isoformat()},
            "status": {"$in": ["completed", "posted", "paid"]}
        }
        if branch_id:
            query["branch_id"] = branch_id
        
        pipeline = [
            {"$match": query},
            {"$group": {
                "_id": None,
                "total_sales": {"$sum": "$total"},
                "total_transactions": {"$sum": 1},
                "avg_transaction": {"$avg": "$total"},
                "total_items": {"$sum": {"$size": {"$ifNull": ["$items", []]}}}
            }}
        ]
        
        result = await self.db["sales_invoices"].aggregate(pipeline).to_list(1)
        data = result[0] if result else {"total_sales": 0, "total_transactions": 0, "avg_transaction": 0, "total_items": 0}
        
        # Top products
        top_pipeline = [
            {"$match": query},
            {"$unwind": "$items"},
            {"$group": {
                "_id": "$items.product_name",
                "qty": {"$sum": "$items.quantity"},
                "revenue": {"$sum": "$items.subtotal"}
            }},
            {"$sort": {"revenue": -1}},
            {"$limit": 10}
        ]
        top_products = await self.db["sales_invoices"].aggregate(top_pipeline).to_list(10)
        
        return {
            "period": {"days": days, "start": start_date.strftime("%Y-%m-%d"), "end": end_date.strftime("%Y-%m-%d")},
            "total_sales": data.get("total_sales", 0),
            "total_transactions": data.get("total_transactions", 0),
            "avg_transaction": round(data.get("avg_transaction", 0), 0),
            "top_products": [{"name": p["_id"], "qty": p["qty"], "revenue": p["revenue"]} for p in top_products]
        }
    
    async def get_stock_status(self, branch_id: str = None) -> dict:
        """Get current stock status from SSOT (stock_movements)"""
        match_stage = {"branch_id": branch_id} if branch_id else {}
        
        pipeline = [
            {"$match": match_stage} if match_stage else {"$match": {}},
            {"$group": {
                "_id": "$product_id",
                "current_stock": {"$sum": "$quantity"},
                "product_code": {"$first": "$product_code"},
                "product_name": {"$first": "$product_name"}
            }},
            {"$match": {"current_stock": {"$ne": 0}}}
        ]
        
        stock_data = await self.db["stock_movements"].aggregate(pipeline).to_list(10000)
        
        # Get product costs
        total_value = 0
        low_stock = []
        high_stock = []
        
        for s in stock_data:
            product = await self.db["products"].find_one(
                {"id": s["_id"]}, 
                {"_id": 0, "cost_price": 1, "min_stock": 1}
            )
            cost = product.get("cost_price", 0) if product else 0
            min_stock = product.get("min_stock", 5) if product else 5
            value = s["current_stock"] * cost
            total_value += value
            
            if s["current_stock"] < min_stock:
                low_stock.append({
                    "product": s["product_name"],
                    "current": s["current_stock"],
                    "min": min_stock
                })
            elif s["current_stock"] > min_stock * 10:
                high_stock.append({
                    "product": s["product_name"],
                    "current": s["current_stock"]
                })
        
        return {
            "total_sku": len(stock_data),
            "total_value": total_value,
            "low_stock_count": len(low_stock),
            "low_stock_items": low_stock[:10],
            "excess_stock_count": len(high_stock),
            "excess_stock_items": high_stock[:10]
        }
    
    async def get_cash_variance(self, days: int = 30) -> dict:
        """Get cash variance data"""
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        pipeline = [
            {"$match": {"created_at": {"$gte": start_date.isoformat(), "$lte": end_date.isoformat()}}},
            {"$group": {
                "_id": "$discrepancy_type",
                "total_amount": {"$sum": "$discrepancy_amount"},
                "count": {"$sum": 1}
            }}
        ]
        
        data = await self.db["cash_discrepancies"].aggregate(pipeline).to_list(10)
        
        result = {
            "period": {"days": days},
            "shortage": {"total": 0, "count": 0},
            "overage": {"total": 0, "count": 0}
        }
        
        for d in data:
            if d["_id"] == "shortage":
                result["shortage"] = {"total": d["total_amount"], "count": d["count"]}
            elif d["_id"] == "overage":
                result["overage"] = {"total": d["total_amount"], "count": d["count"]}
        
        result["net_variance"] = result["overage"]["total"] - result["shortage"]["total"]
        
        return result
    
    async def get_kpi_summary(self, days: int = 30) -> dict:
        """Get comprehensive KPI summary"""
        sales = await self.get_sales_summary(days)
        stock = await self.get_stock_status()
        cash = await self.get_cash_variance(days)
        
        return {
            "sales": {
                "revenue": sales["total_sales"],
                "transactions": sales["total_transactions"],
                "avg_basket": sales["avg_transaction"]
            },
            "inventory": {
                "total_value": stock["total_value"],
                "low_stock_alerts": stock["low_stock_count"]
            },
            "cash_control": {
                "shortage": cash["shortage"]["total"],
                "overage": cash["overage"]["total"],
                "net": cash["net_variance"]
            }
        }


# ==================== PYDANTIC MODELS ====================

class InsightRequest(BaseModel):
    query: str = Field(..., description="Business question or area to analyze")
    focus_area: Optional[str] = Field(None, description="Specific focus: sales, inventory, cash, profitability")
    date_range_days: Optional[int] = Field(30, description="Number of days to analyze")
    branch_id: Optional[str] = Field(None, description="Specific branch to analyze")


class InsightResponse(BaseModel):
    query: str
    analysis: str
    recommendations: List[str]
    data_summary: Dict[str, Any]
    generated_at: str


# ==================== AI INSIGHT ENDPOINT ====================

@router.post("/insights")
async def get_ai_insights(
    request: InsightRequest,
    user: dict = Depends(require_permission("ai_insights", "view"))
):
    """
    Get AI-powered business insights
    
    AI ONLY READS data - never writes to database.
    Uses function calling to gather relevant data, then analyzes.
    """
    db = get_db()
    
    # Initialize AI tools
    tools = AITools(db, user)
    
    # Gather relevant data based on focus area
    data_context = {}
    
    if request.focus_area == "sales" or not request.focus_area:
        data_context["sales"] = await tools.get_sales_summary(request.date_range_days, request.branch_id)
    
    if request.focus_area == "inventory" or not request.focus_area:
        data_context["inventory"] = await tools.get_stock_status(request.branch_id)
    
    if request.focus_area == "cash" or not request.focus_area:
        data_context["cash_variance"] = await tools.get_cash_variance(request.date_range_days)
    
    if request.focus_area == "profitability" or not request.focus_area:
        data_context["trial_balance"] = await tools.get_trial_balance()
    
    if not request.focus_area:
        data_context["kpi"] = await tools.get_kpi_summary(request.date_range_days)
    
    # Build prompt for AI
    system_prompt = """Anda adalah AI Business Analyst untuk OCB TITAN ERP.

ATURAN KETAT:
1. Anda HANYA boleh MEMBACA dan MENGANALISIS data
2. Anda TIDAK PERNAH boleh menyarankan perubahan langsung ke database
3. Semua rekomendasi harus berupa saran strategis, bukan aksi teknis
4. Gunakan bahasa Indonesia yang profesional
5. Fokus pada insight bisnis yang actionable

Format output Anda:
1. ANALISIS: Jelaskan temuan utama dari data
2. INSIGHT: Berikan interpretasi bisnis dari data
3. REKOMENDASI: 3-5 saran strategis yang dapat ditindaklanjuti
4. PERINGATAN: Jika ada yang perlu diwaspadai

Data disajikan dalam format JSON. Analisis dengan cermat."""

    user_prompt = f"""Pertanyaan pengguna: {request.query}

Data yang tersedia untuk analisis:
{json.dumps(data_context, indent=2, default=str)}

Berikan analisis bisnis yang komprehensif berdasarkan data di atas.
Fokus pada insight yang dapat ditindaklanjuti."""

    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        api_key = os.environ.get("EMERGENT_LLM_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="AI service not configured")
        
        chat = LlmChat(
            api_key=api_key,
            session_id=f"insight-{user.get('user_id', 'anon')}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            system_message=system_prompt
        ).with_model("openai", "gpt-4o")
        
        message = UserMessage(text=user_prompt)
        response = await chat.send_message(message)
        
        # Parse response into structured format
        analysis_text = response if isinstance(response, str) else str(response)
        
        # Extract recommendations (simple parsing)
        recommendations = []
        lines = analysis_text.split("\n")
        in_recommendations = False
        for line in lines:
            if "REKOMENDASI" in line.upper() or "SARAN" in line.upper():
                in_recommendations = True
                continue
            if in_recommendations and line.strip().startswith(("-", "•", "*", "1", "2", "3", "4", "5")):
                rec = line.strip().lstrip("-•*0123456789. ")
                if rec:
                    recommendations.append(rec)
            if len(recommendations) >= 5:
                break
        
        if not recommendations:
            recommendations = ["Lakukan review rutin terhadap data penjualan", "Monitor stok rendah secara berkala"]
        
        return {
            "query": request.query,
            "analysis": analysis_text,
            "recommendations": recommendations,
            "data_summary": {
                "focus_area": request.focus_area or "comprehensive",
                "date_range_days": request.date_range_days,
                "data_points_analyzed": len(data_context)
            },
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
    except ImportError:
        # Fallback if emergentintegrations not available
        return {
            "query": request.query,
            "analysis": f"Berdasarkan data {request.date_range_days} hari terakhir, berikut ringkasan:\n\n" + 
                       json.dumps(data_context, indent=2, default=str),
            "recommendations": [
                "Review data penjualan untuk identifikasi tren",
                "Periksa produk dengan stok rendah",
                "Evaluasi cash variance untuk mencegah kerugian"
            ],
            "data_summary": data_context,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "note": "AI analysis not available - showing raw data"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI analysis error: {str(e)}")


# ==================== AI TOOLS ENDPOINTS (Read-Only) ====================

@router.get("/tools/trial-balance")
async def ai_tool_trial_balance(
    as_of_date: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """AI Tool: Get trial balance - READ ONLY"""
    db = get_db()
    tools = AITools(db, user)
    return await tools.get_trial_balance(as_of_date)


@router.get("/tools/sales-summary")
async def ai_tool_sales_summary(
    days: int = 30,
    branch_id: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """AI Tool: Get sales summary - READ ONLY"""
    db = get_db()
    tools = AITools(db, user)
    return await tools.get_sales_summary(days, branch_id)


@router.get("/tools/stock-status")
async def ai_tool_stock_status(
    branch_id: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """AI Tool: Get stock status - READ ONLY"""
    db = get_db()
    tools = AITools(db, user)
    return await tools.get_stock_status(branch_id)


@router.get("/tools/cash-variance")
async def ai_tool_cash_variance(
    days: int = 30,
    user: dict = Depends(get_current_user)
):
    """AI Tool: Get cash variance - READ ONLY"""
    db = get_db()
    tools = AITools(db, user)
    return await tools.get_cash_variance(days)


@router.get("/tools/kpi-summary")
async def ai_tool_kpi_summary(
    days: int = 30,
    user: dict = Depends(get_current_user)
):
    """AI Tool: Get KPI summary - READ ONLY"""
    db = get_db()
    tools = AITools(db, user)
    return await tools.get_kpi_summary(days)
