# OCB AI TITAN - Hallo AI Service
# AI Enterprise yang terhubung dengan seluruh database sistem

from emergentintegrations.llm.chat import LlmChat, UserMessage
from database import db
from datetime import datetime, timezone, timedelta
import os
import json

class HalloAIService:
    """
    Hallo AI - AI Enterprise OCB AI TITAN
    Bertindak sebagai CEO, CFO, COO, CMO, Sales Manager, Customer Service, Business Analyst
    """
    
    AI_PERSONAS = {
        "ceo": {
            "name": "CEO AI",
            "description": "AI yang bertindak sebagai CEO - memberikan rekomendasi strategi bisnis, analisa performa cabang, dan keputusan eksekutif",
            "system_prompt": """Anda adalah CEO AI dari OCB AI TITAN - Enterprise Retail AI System.
            
Anda bertindak sebagai CEO virtual yang membantu pemilik bisnis dengan:
- Analisis performa perusahaan secara keseluruhan
- Rekomendasi strategi bisnis dan ekspansi
- Evaluasi performa cabang dan karyawan
- Keputusan strategis level eksekutif
- Efisiensi operasional dan optimasi biaya

Selalu berikan jawaban dalam Bahasa Indonesia yang profesional.
Gunakan data real dari sistem untuk mendukung analisis Anda.
Berikan rekomendasi yang actionable dan terukur."""
        },
        "cfo": {
            "name": "CFO AI",
            "description": "AI yang bertindak sebagai CFO - analisa keuangan, laba rugi, arus kas, dan margin keuntungan",
            "system_prompt": """Anda adalah CFO AI dari OCB AI TITAN - Enterprise Retail AI System.

Anda bertindak sebagai CFO virtual yang membantu dengan:
- Analisis laporan laba rugi
- Monitoring arus kas dan cashflow
- Analisis margin keuntungan per produk/cabang
- Evaluasi kesehatan keuangan perusahaan
- Rekomendasi optimasi keuangan

Selalu berikan jawaban dalam Bahasa Indonesia yang profesional.
Gunakan data real dari sistem untuk mendukung analisis Anda.
Format angka keuangan dalam Rupiah (Rp) dengan pemisah ribuan."""
        },
        "coo": {
            "name": "COO AI", 
            "description": "AI yang bertindak sebagai COO - monitoring operasional, stok, transaksi, dan efisiensi",
            "system_prompt": """Anda adalah COO AI dari OCB AI TITAN - Enterprise Retail AI System.

Anda bertindak sebagai COO virtual yang membantu dengan:
- Monitoring operasional cabang secara real-time
- Analisis transaksi dan performa kasir
- Monitoring stok dan peringatan stok menipis
- Optimasi proses operasional
- Rekomendasi perbaikan efisiensi

Selalu berikan jawaban dalam Bahasa Indonesia yang profesional.
Berikan peringatan proaktif jika ada masalah operasional."""
        },
        "cmo": {
            "name": "Marketing AI",
            "description": "AI yang bertindak sebagai CMO - analisa produk terlaris, rekomendasi promo, dan strategi marketing",
            "system_prompt": """Anda adalah CMO/Marketing AI dari OCB AI TITAN - Enterprise Retail AI System.

Anda bertindak sebagai Marketing AI virtual yang membantu dengan:
- Analisis produk terlaris dan trend penjualan
- Rekomendasi strategi promosi dan diskon
- Ide bundling produk yang optimal
- Analisis perilaku pelanggan
- Strategi marketing berbasis data

Selalu berikan jawaban dalam Bahasa Indonesia yang profesional.
Berikan rekomendasi marketing yang kreatif dan data-driven."""
        },
        "sales": {
            "name": "Sales AI",
            "description": "AI yang membantu tim sales dengan upselling, cross-selling, dan rekomendasi produk",
            "system_prompt": """Anda adalah Sales AI dari OCB AI TITAN - Enterprise Retail AI System.

Anda bertindak sebagai Sales Assistant AI yang membantu kasir dan tim sales dengan:
- Rekomendasi upselling untuk meningkatkan nilai transaksi
- Saran cross-selling produk yang relevan
- Rekomendasi produk tambahan berdasarkan pembelian
- Tips closing penjualan
- Informasi produk untuk membantu penjualan

Selalu berikan jawaban dalam Bahasa Indonesia yang ramah dan persuasif.
Fokus pada meningkatkan kepuasan pelanggan dan nilai transaksi."""
        },
        "customer_service": {
            "name": "Customer Service AI",
            "description": "AI yang melayani pelanggan - cek harga, stok, dan informasi produk",
            "system_prompt": """Anda adalah Customer Service AI dari OCB AI TITAN - Enterprise Retail AI System.

Anda bertindak sebagai Customer Service virtual yang membantu pelanggan dengan:
- Informasi harga produk
- Cek ketersediaan stok
- Informasi detail produk
- Bantuan umum tentang toko
- Rekomendasi produk berdasarkan kebutuhan

Selalu berikan jawaban dalam Bahasa Indonesia yang ramah dan helpful.
Jaga kerahasiaan data internal perusahaan - hanya informasi publik untuk pelanggan."""
        },
        "analyst": {
            "name": "Business Analyst AI",
            "description": "AI yang menganalisis data bisnis secara mendalam",
            "system_prompt": """Anda adalah Business Analyst AI dari OCB AI TITAN - Enterprise Retail AI System.

Anda bertindak sebagai Business Analyst virtual yang membantu dengan:
- Analisis data penjualan mendalam
- Identifikasi trend dan pola bisnis
- Forecasting dan prediksi
- Report generation dan insight
- KPI monitoring dan evaluasi

Selalu berikan jawaban dalam Bahasa Indonesia yang profesional dan analitis.
Sertakan data pendukung dan visualisasi jika memungkinkan."""
        }
    }
    
    def __init__(self, user_id: str, branch_id: str = None, user_role: str = "owner"):
        self.user_id = user_id
        self.branch_id = branch_id
        self.user_role = user_role
        self.api_key = os.environ.get('EMERGENT_LLM_KEY')
        
    async def get_business_context(self) -> dict:
        """Ambil konteks bisnis dari database untuk AI"""
        context = {}
        
        try:
            # Filter berdasarkan cabang jika bukan owner/admin
            branch_filter = {}
            if self.user_role not in ["owner", "admin"] and self.branch_id:
                branch_filter["branch_id"] = self.branch_id
            
            # 1. Ringkasan Penjualan Hari Ini
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            today_start = f"{today}T00:00:00"
            
            sales_pipeline = [
                {"$match": {
                    **branch_filter,
                    "created_at": {"$gte": today_start},
                    "status": "completed"
                }},
                {"$group": {
                    "_id": None,
                    "total_penjualan": {"$sum": "$total"},
                    "total_laba": {"$sum": "$profit"},
                    "jumlah_transaksi": {"$sum": 1}
                }}
            ]
            sales_result = await db.transactions.aggregate(sales_pipeline).to_list(1)
            context["penjualan_hari_ini"] = sales_result[0] if sales_result else {
                "total_penjualan": 0, "total_laba": 0, "jumlah_transaksi": 0
            }
            
            # 2. Stok Menipis
            low_stock_pipeline = [
                {"$match": branch_filter} if branch_filter else {"$match": {}},
                {"$lookup": {
                    "from": "products",
                    "localField": "product_id",
                    "foreignField": "id",
                    "as": "product"
                }},
                {"$unwind": "$product"},
                {"$match": {"$expr": {"$lte": ["$quantity", "$product.min_stock"]}}},
                {"$project": {
                    "_id": 0,
                    "product_name": "$product.name",
                    "quantity": 1,
                    "min_stock": "$product.min_stock"
                }},
                {"$limit": 10}
            ]
            low_stock = await db.product_stocks.aggregate(low_stock_pipeline).to_list(10)
            context["stok_menipis"] = low_stock
            
            # 3. Produk Terlaris (7 hari terakhir)
            week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
            best_sellers_pipeline = [
                {"$match": {
                    **branch_filter,
                    "created_at": {"$gte": week_ago},
                    "status": "completed"
                }},
                {"$unwind": "$items"},
                {"$group": {
                    "_id": "$items.product_id",
                    "nama_produk": {"$first": "$items.product_name"},
                    "total_terjual": {"$sum": "$items.quantity"},
                    "total_pendapatan": {"$sum": {"$multiply": ["$items.quantity", "$items.price"]}}
                }},
                {"$sort": {"total_terjual": -1}},
                {"$limit": 5}
            ]
            best_sellers = await db.transactions.aggregate(best_sellers_pipeline).to_list(5)
            context["produk_terlaris"] = best_sellers
            
            # 4. Total Produk dan Stok
            total_products = await db.products.count_documents({"is_active": True})
            context["total_produk"] = total_products
            
            # 5. Total Pelanggan
            total_customers = await db.customers.count_documents({})
            context["total_pelanggan"] = total_customers
            
            # 6. Cabang (untuk owner/admin)
            if self.user_role in ["owner", "admin"]:
                branches = await db.branches.find({}, {"_id": 0, "id": 1, "name": 1, "code": 1}).to_list(50)
                context["cabang"] = branches
                
                # Performa per cabang
                branch_perf_pipeline = [
                    {"$match": {"created_at": {"$gte": week_ago}, "status": "completed"}},
                    {"$group": {
                        "_id": "$branch_id",
                        "total_penjualan": {"$sum": "$total"},
                        "jumlah_transaksi": {"$sum": 1}
                    }},
                    {"$sort": {"total_penjualan": -1}}
                ]
                branch_perf = await db.transactions.aggregate(branch_perf_pipeline).to_list(20)
                context["performa_cabang"] = branch_perf
            
            # 7. Saldo Kas
            if branch_filter:
                cash_balance = await db.branches.find_one(
                    {"id": self.branch_id},
                    {"_id": 0, "cash_balance": 1}
                )
                context["saldo_kas"] = cash_balance.get("cash_balance", 0) if cash_balance else 0
            else:
                # Total saldo semua cabang
                cash_pipeline = [
                    {"$group": {"_id": None, "total": {"$sum": "$cash_balance"}}}
                ]
                cash_result = await db.branches.aggregate(cash_pipeline).to_list(1)
                context["saldo_kas"] = cash_result[0]["total"] if cash_result else 0
            
            # 8. Supplier
            suppliers = await db.suppliers.find({}, {"_id": 0, "id": 1, "name": 1, "code": 1}).to_list(20)
            context["suppliers"] = suppliers
            
        except Exception as e:
            print(f"Error getting business context: {e}")
            
        return context
    
    async def chat(self, message: str, session_id: str, persona: str = "analyst") -> dict:
        """Chat dengan Hallo AI"""
        
        # Dapatkan persona
        persona_config = self.AI_PERSONAS.get(persona, self.AI_PERSONAS["analyst"])
        
        # Dapatkan konteks bisnis real-time
        business_context = await self.get_business_context()
        
        # Build system message dengan konteks
        system_message = f"""{persona_config['system_prompt']}

=== DATA BISNIS REAL-TIME ===
Tanggal: {datetime.now(timezone.utc).strftime("%d %B %Y, %H:%M")} WIB

PENJUALAN HARI INI:
- Total Penjualan: Rp {business_context.get('penjualan_hari_ini', {}).get('total_penjualan', 0):,.0f}
- Total Laba: Rp {business_context.get('penjualan_hari_ini', {}).get('total_laba', 0):,.0f}
- Jumlah Transaksi: {business_context.get('penjualan_hari_ini', {}).get('jumlah_transaksi', 0)}

STOK MENIPIS ({len(business_context.get('stok_menipis', []))} produk):
{chr(10).join([f"- {p['product_name']}: {p['quantity']} sisa (min: {p['min_stock']})" for p in business_context.get('stok_menipis', [])[:5]])}

PRODUK TERLARIS (7 hari):
{chr(10).join([f"- {p['nama_produk']}: {p['total_terjual']} terjual (Rp {p['total_pendapatan']:,.0f})" for p in business_context.get('produk_terlaris', [])[:5]])}

RINGKASAN:
- Total Produk Aktif: {business_context.get('total_produk', 0)}
- Total Pelanggan: {business_context.get('total_pelanggan', 0)}
- Saldo Kas: Rp {business_context.get('saldo_kas', 0):,.0f}

Gunakan data di atas untuk menjawab pertanyaan pengguna dengan akurat dan relevan.
"""
        
        try:
            # Inisialisasi chat dengan Emergent LLM
            chat = LlmChat(
                api_key=self.api_key,
                session_id=session_id,
                system_message=system_message
            ).with_model("openai", "gpt-4o")
            
            # Kirim pesan
            user_msg = UserMessage(text=message)
            response = await chat.send_message(user_msg)
            
            return {
                "success": True,
                "response": response,
                "persona": persona_config["name"],
                "session_id": session_id
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": f"Maaf, terjadi kesalahan dalam memproses permintaan Anda: {str(e)}"
            }
    
    async def get_quick_insight(self, insight_type: str) -> dict:
        """Dapatkan insight cepat tanpa chat"""
        
        business_context = await self.get_business_context()
        
        insights = {
            "sales_today": {
                "title": "Penjualan Hari Ini",
                "data": business_context.get("penjualan_hari_ini", {}),
                "message": f"Total penjualan hari ini: Rp {business_context.get('penjualan_hari_ini', {}).get('total_penjualan', 0):,.0f} dari {business_context.get('penjualan_hari_ini', {}).get('jumlah_transaksi', 0)} transaksi"
            },
            "low_stock": {
                "title": "Stok Menipis",
                "data": business_context.get("stok_menipis", []),
                "message": f"Ada {len(business_context.get('stok_menipis', []))} produk yang perlu di-restock segera"
            },
            "best_sellers": {
                "title": "Produk Terlaris",
                "data": business_context.get("produk_terlaris", []),
                "message": f"Produk terlaris minggu ini: {business_context.get('produk_terlaris', [{}])[0].get('nama_produk', '-') if business_context.get('produk_terlaris') else '-'}"
            }
        }
        
        return insights.get(insight_type, {"title": "Unknown", "data": {}, "message": "Insight tidak ditemukan"})
