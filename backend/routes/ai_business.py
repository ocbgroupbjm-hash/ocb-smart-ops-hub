# OCB TITAN - AI Business Analytics
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from database import db
from utils.auth import get_current_user
from datetime import datetime, timezone, timedelta

router = APIRouter(prefix="/ai-bisnis", tags=["AI Business"])

def get_date_range(days: int = 30):
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    return start.isoformat(), end.isoformat()

@router.get("/insight-penjualan")
async def get_sales_insights(days: int = 30, current_user: dict = Depends(get_current_user)):
    """AI-powered sales insights"""
    start_date, end_date = get_date_range(days)
    
    transactions = db["transactions"]
    branch_filter = {}
    if current_user.get("role") not in ["owner", "admin"] and current_user.get("branch_id"):
        branch_filter["branch_id"] = current_user["branch_id"]
    
    # Get sales data
    pipeline = [
        {"$match": {**branch_filter, "created_at": {"$gte": start_date, "$lte": end_date}, "status": "completed"}},
        {"$group": {
            "_id": None,
            "total_sales": {"$sum": "$total"},
            "total_profit": {"$sum": "$profit"},
            "total_transactions": {"$sum": 1},
            "avg_transaction": {"$avg": "$total"}
        }}
    ]
    result = await transactions.aggregate(pipeline).to_list(1)
    current = result[0] if result else {"total_sales": 0, "total_profit": 0, "total_transactions": 0, "avg_transaction": 0}
    
    # Get previous period for comparison
    prev_start = (datetime.fromisoformat(start_date.replace('Z', '+00:00')) - timedelta(days=days)).isoformat()
    pipeline[0]["$match"]["created_at"] = {"$gte": prev_start, "$lt": start_date}
    prev_result = await transactions.aggregate(pipeline).to_list(1)
    previous = prev_result[0] if prev_result else {"total_sales": 0, "total_profit": 0, "total_transactions": 0}
    
    # Calculate growth
    sales_growth = ((current["total_sales"] - previous["total_sales"]) / previous["total_sales"] * 100) if previous["total_sales"] > 0 else 0
    profit_growth = ((current["total_profit"] - previous["total_profit"]) / previous["total_profit"] * 100) if previous["total_profit"] > 0 else 0
    
    # Generate insights
    insights = []
    if sales_growth > 10:
        insights.append({"type": "positive", "message": f"Penjualan naik {sales_growth:.1f}% dibanding periode sebelumnya. Pertahankan strategi ini!"})
    elif sales_growth < -10:
        insights.append({"type": "warning", "message": f"Penjualan turun {abs(sales_growth):.1f}%. Perlu evaluasi strategi penjualan."})
    else:
        insights.append({"type": "info", "message": f"Penjualan stabil dengan perubahan {sales_growth:.1f}%."})
    
    if profit_growth > sales_growth:
        insights.append({"type": "positive", "message": "Margin keuntungan membaik. Efisiensi operasional meningkat."})
    elif profit_growth < sales_growth - 5:
        insights.append({"type": "warning", "message": "Margin keuntungan menurun. Periksa HPP dan diskon yang diberikan."})
    
    avg_trans = current.get("avg_transaction", 0)
    if avg_trans > 0:
        insights.append({"type": "info", "message": f"Rata-rata transaksi Rp {avg_trans:,.0f}. Pertimbangkan upselling untuk meningkatkan nilai."})
    
    return {
        "periode": f"{days} hari terakhir",
        "ringkasan": {
            "total_penjualan": current["total_sales"],
            "total_laba": current["total_profit"],
            "total_transaksi": current["total_transactions"],
            "rata_rata_transaksi": current.get("avg_transaction", 0),
            "pertumbuhan_penjualan": sales_growth,
            "pertumbuhan_laba": profit_growth
        },
        "insights": insights
    }

@router.get("/rekomendasi-restock")
async def get_restock_recommendations(current_user: dict = Depends(get_current_user)):
    """AI-powered restock recommendations"""
    products = db["products"]
    stock = db["stock"]
    transactions = db["transactions"]
    
    branch_filter = {}
    if current_user.get("role") not in ["owner", "admin"] and current_user.get("branch_id"):
        branch_filter["branch_id"] = current_user["branch_id"]
    
    # Get low stock products
    low_stock_pipeline = [
        {"$match": branch_filter} if branch_filter else {"$match": {}},
        {"$lookup": {"from": "products", "localField": "product_id", "foreignField": "id", "as": "product"}},
        {"$unwind": "$product"},
        {"$match": {"$expr": {"$lte": ["$quantity", "$product.min_stock"]}}},
        {"$project": {
            "_id": 0,
            "product_id": 1,
            "product_name": "$product.name",
            "product_code": "$product.code",
            "current_stock": "$quantity",
            "min_stock": "$product.min_stock",
            "cost_price": "$product.cost_price"
        }},
        {"$limit": 20}
    ]
    
    low_stock_items = await stock.aggregate(low_stock_pipeline).to_list(20)
    
    # Calculate recommended order quantities based on sales velocity
    recommendations = []
    start_date, _ = get_date_range(30)
    
    for item in low_stock_items:
        # Get sales velocity
        sales_pipeline = [
            {"$match": {"created_at": {"$gte": start_date}, "status": "completed", **branch_filter}},
            {"$unwind": "$items"},
            {"$match": {"items.product_id": item["product_id"]}},
            {"$group": {"_id": None, "total_sold": {"$sum": "$items.quantity"}}}
        ]
        sales_result = await transactions.aggregate(sales_pipeline).to_list(1)
        monthly_sales = sales_result[0]["total_sold"] if sales_result else 0
        daily_sales = monthly_sales / 30
        
        # Recommend 2 weeks stock + safety buffer
        recommended_qty = max(int(daily_sales * 14 + item["min_stock"]), item["min_stock"] * 2)
        order_qty = max(recommended_qty - item["current_stock"], 0)
        
        if order_qty > 0:
            recommendations.append({
                "product_id": item["product_id"],
                "nama_produk": item["product_name"],
                "kode_produk": item["product_code"],
                "stok_saat_ini": item["current_stock"],
                "stok_minimum": item["min_stock"],
                "penjualan_harian": round(daily_sales, 1),
                "rekomendasi_order": order_qty,
                "estimasi_biaya": order_qty * item.get("cost_price", 0),
                "urgensi": "tinggi" if item["current_stock"] == 0 else "sedang" if item["current_stock"] <= item["min_stock"] / 2 else "rendah"
            })
    
    # Sort by urgency
    urgency_order = {"tinggi": 0, "sedang": 1, "rendah": 2}
    recommendations.sort(key=lambda x: urgency_order[x["urgensi"]])
    
    total_biaya = sum(r["estimasi_biaya"] for r in recommendations)
    
    return {
        "total_produk_perlu_restock": len(recommendations),
        "total_estimasi_biaya": total_biaya,
        "rekomendasi": recommendations,
        "insight": f"Ada {len([r for r in recommendations if r['urgensi'] == 'tinggi'])} produk dengan urgensi tinggi yang perlu segera di-restock."
    }

@router.get("/produk-terlaris")
async def get_best_sellers(days: int = 30, limit: int = 10, current_user: dict = Depends(get_current_user)):
    """Get best selling products with AI insights"""
    start_date, end_date = get_date_range(days)
    transactions = db["transactions"]
    
    branch_filter = {}
    if current_user.get("role") not in ["owner", "admin"] and current_user.get("branch_id"):
        branch_filter["branch_id"] = current_user["branch_id"]
    
    pipeline = [
        {"$match": {**branch_filter, "created_at": {"$gte": start_date}, "status": "completed"}},
        {"$unwind": "$items"},
        {"$group": {
            "_id": "$items.product_id",
            "nama_produk": {"$first": "$items.product_name"},
            "total_terjual": {"$sum": "$items.quantity"},
            "total_pendapatan": {"$sum": {"$multiply": ["$items.quantity", "$items.price"]}},
            "total_laba": {"$sum": {"$multiply": ["$items.quantity", {"$subtract": ["$items.price", "$items.cost"]}]}}
        }},
        {"$sort": {"total_terjual": -1}},
        {"$limit": limit}
    ]
    
    result = await transactions.aggregate(pipeline).to_list(limit)
    
    # Add ranking and insights
    for i, item in enumerate(result):
        item["ranking"] = i + 1
        item["product_id"] = item.pop("_id")
        margin = (item["total_laba"] / item["total_pendapatan"] * 100) if item["total_pendapatan"] > 0 else 0
        item["margin_persen"] = round(margin, 1)
    
    insights = []
    if result:
        top = result[0]
        insights.append({"type": "info", "message": f"Produk terlaris: {top['nama_produk']} dengan {top['total_terjual']} unit terjual."})
        
        high_margin = [p for p in result if p["margin_persen"] > 30]
        if high_margin:
            insights.append({"type": "positive", "message": f"{len(high_margin)} produk terlaris memiliki margin di atas 30%. Fokus promosi pada produk ini."})
    
    return {
        "periode": f"{days} hari terakhir",
        "produk_terlaris": result,
        "insights": insights
    }

@router.get("/produk-lambat")
async def get_slow_movers(days: int = 30, limit: int = 10, current_user: dict = Depends(get_current_user)):
    """Get slow moving products"""
    start_date, end_date = get_date_range(days)
    transactions = db["transactions"]
    products = db["products"]
    stock = db["stock"]
    
    branch_filter = {}
    if current_user.get("role") not in ["owner", "admin"] and current_user.get("branch_id"):
        branch_filter["branch_id"] = current_user["branch_id"]
    
    # Get all products with stock
    all_products = await products.find({"is_active": True}, {"_id": 0, "id": 1, "name": 1, "code": 1, "sell_price": 1, "cost_price": 1}).to_list(500)
    
    # Get sales for each product
    slow_movers = []
    for prod in all_products:
        pipeline = [
            {"$match": {**branch_filter, "created_at": {"$gte": start_date}, "status": "completed"}},
            {"$unwind": "$items"},
            {"$match": {"items.product_id": prod["id"]}},
            {"$group": {"_id": None, "total_sold": {"$sum": "$items.quantity"}}}
        ]
        sales = await transactions.aggregate(pipeline).to_list(1)
        total_sold = sales[0]["total_sold"] if sales else 0
        
        # Get current stock
        stock_data = await stock.find_one({"product_id": prod["id"], **branch_filter}, {"_id": 0, "quantity": 1})
        current_stock = stock_data["quantity"] if stock_data else 0
        
        if total_sold < 5 and current_stock > 0:  # Slow if sold less than 5 in period
            stock_value = current_stock * prod.get("cost_price", 0)
            slow_movers.append({
                "product_id": prod["id"],
                "nama_produk": prod["name"],
                "kode_produk": prod["code"],
                "terjual": total_sold,
                "stok_saat_ini": current_stock,
                "nilai_stok": stock_value,
                "harga_jual": prod.get("sell_price", 0)
            })
    
    # Sort by stock value (highest first - most capital tied up)
    slow_movers.sort(key=lambda x: x["nilai_stok"], reverse=True)
    slow_movers = slow_movers[:limit]
    
    total_nilai = sum(p["nilai_stok"] for p in slow_movers)
    
    insights = []
    if slow_movers:
        insights.append({"type": "warning", "message": f"Modal Rp {total_nilai:,.0f} tertahan di {len(slow_movers)} produk lambat terjual."})
        insights.append({"type": "info", "message": "Pertimbangkan promo diskon atau bundling untuk menggerakkan stok ini."})
    
    return {
        "periode": f"{days} hari terakhir",
        "total_nilai_tertahan": total_nilai,
        "produk_lambat": slow_movers,
        "insights": insights
    }

@router.get("/analisa-stok")
async def get_stock_analysis(current_user: dict = Depends(get_current_user)):
    """AI stock analysis"""
    stock = db["stock"]
    products = db["products"]
    
    branch_filter = {}
    if current_user.get("role") not in ["owner", "admin"] and current_user.get("branch_id"):
        branch_filter["branch_id"] = current_user["branch_id"]
    
    # Get stock summary
    pipeline = [
        {"$match": branch_filter} if branch_filter else {"$match": {}},
        {"$lookup": {"from": "products", "localField": "product_id", "foreignField": "id", "as": "product"}},
        {"$unwind": "$product"},
        {"$group": {
            "_id": None,
            "total_items": {"$sum": "$quantity"},
            "total_products": {"$sum": 1},
            "total_value": {"$sum": {"$multiply": ["$quantity", "$product.cost_price"]}},
            "total_retail": {"$sum": {"$multiply": ["$quantity", "$product.sell_price"]}},
            "low_stock_count": {"$sum": {"$cond": [{"$lte": ["$quantity", "$product.min_stock"]}, 1, 0]}},
            "zero_stock_count": {"$sum": {"$cond": [{"$eq": ["$quantity", 0]}, 1, 0]}}
        }}
    ]
    
    result = await stock.aggregate(pipeline).to_list(1)
    summary = result[0] if result else {
        "total_items": 0, "total_products": 0, "total_value": 0, 
        "total_retail": 0, "low_stock_count": 0, "zero_stock_count": 0
    }
    
    potential_profit = summary["total_retail"] - summary["total_value"]
    
    insights = []
    if summary["zero_stock_count"] > 0:
        insights.append({"type": "warning", "message": f"{summary['zero_stock_count']} produk habis stok. Segera lakukan pembelian."})
    if summary["low_stock_count"] > 0:
        insights.append({"type": "warning", "message": f"{summary['low_stock_count']} produk stok menipis perlu di-restock."})
    
    stock_turnover = "baik" if summary["low_stock_count"] < summary["total_products"] * 0.1 else "perlu perhatian"
    insights.append({"type": "info", "message": f"Kondisi stok secara keseluruhan: {stock_turnover}."})
    insights.append({"type": "info", "message": f"Potensi keuntungan dari stok: Rp {potential_profit:,.0f}"})
    
    return {
        "ringkasan": {
            "total_jenis_produk": summary["total_products"],
            "total_item": summary["total_items"],
            "nilai_modal": summary["total_value"],
            "nilai_jual": summary["total_retail"],
            "potensi_laba": potential_profit,
            "produk_stok_menipis": summary["low_stock_count"],
            "produk_habis": summary["zero_stock_count"]
        },
        "insights": insights
    }

@router.get("/performa-cabang")
async def get_branch_performance(days: int = 30, current_user: dict = Depends(get_current_user)):
    """AI branch performance analysis"""
    if current_user.get("role") not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Akses ditolak. Hanya pemilik dan admin yang dapat melihat performa cabang.")
    
    start_date, end_date = get_date_range(days)
    transactions = db["transactions"]
    branches_col = db["branches"]
    
    # Get all branches
    branches = await branches_col.find({}, {"_id": 0}).to_list(100)
    
    branch_performance = []
    for branch in branches:
        pipeline = [
            {"$match": {"branch_id": branch["id"], "created_at": {"$gte": start_date}, "status": "completed"}},
            {"$group": {
                "_id": None,
                "total_penjualan": {"$sum": "$total"},
                "total_laba": {"$sum": "$profit"},
                "jumlah_transaksi": {"$sum": 1}
            }}
        ]
        result = await transactions.aggregate(pipeline).to_list(1)
        perf = result[0] if result else {"total_penjualan": 0, "total_laba": 0, "jumlah_transaksi": 0}
        
        margin = (perf["total_laba"] / perf["total_penjualan"] * 100) if perf["total_penjualan"] > 0 else 0
        
        branch_performance.append({
            "branch_id": branch["id"],
            "nama_cabang": branch.get("name", "Unknown"),
            "kode_cabang": branch.get("code", "-"),
            "total_penjualan": perf["total_penjualan"],
            "total_laba": perf["total_laba"],
            "jumlah_transaksi": perf["jumlah_transaksi"],
            "margin_persen": round(margin, 1)
        })
    
    # Sort by sales
    branch_performance.sort(key=lambda x: x["total_penjualan"], reverse=True)
    
    # Add ranking
    for i, bp in enumerate(branch_performance):
        bp["ranking"] = i + 1
    
    insights = []
    if branch_performance:
        best = branch_performance[0]
        worst = branch_performance[-1] if len(branch_performance) > 1 else None
        
        insights.append({"type": "positive", "message": f"Cabang terbaik: {best['nama_cabang']} dengan penjualan Rp {best['total_penjualan']:,.0f}"})
        if worst and worst["total_penjualan"] < best["total_penjualan"] * 0.5:
            insights.append({"type": "warning", "message": f"Cabang {worst['nama_cabang']} perlu perhatian. Penjualan jauh di bawah rata-rata."})
        
        avg_sales = sum(bp["total_penjualan"] for bp in branch_performance) / len(branch_performance)
        below_avg = [bp for bp in branch_performance if bp["total_penjualan"] < avg_sales * 0.7]
        if below_avg:
            insights.append({"type": "info", "message": f"{len(below_avg)} cabang memiliki penjualan di bawah 70% rata-rata."})
    
    return {
        "periode": f"{days} hari terakhir",
        "total_cabang": len(branch_performance),
        "performa_cabang": branch_performance,
        "insights": insights
    }

@router.get("/rekomendasi-bisnis")
async def get_business_recommendations(current_user: dict = Depends(get_current_user)):
    """AI-powered business recommendations"""
    recommendations = []
    
    # Get various insights
    sales = await get_sales_insights(30, current_user)
    restock = await get_restock_recommendations(current_user)
    stock_analysis = await get_stock_analysis(current_user)
    
    # Generate recommendations based on data
    if sales["ringkasan"]["pertumbuhan_penjualan"] < -5:
        recommendations.append({
            "prioritas": "tinggi",
            "kategori": "Penjualan",
            "rekomendasi": "Penjualan menurun. Pertimbangkan promosi atau diskon untuk meningkatkan traffic.",
            "aksi": ["Buat promo weekend", "Review harga kompetitor", "Tingkatkan aktivitas marketing"]
        })
    
    if restock["total_produk_perlu_restock"] > 5:
        recommendations.append({
            "prioritas": "tinggi",
            "kategori": "Stok",
            "rekomendasi": f"{restock['total_produk_perlu_restock']} produk perlu di-restock segera.",
            "aksi": ["Buat PO untuk supplier", "Prioritaskan produk dengan urgensi tinggi"]
        })
    
    if stock_analysis["ringkasan"]["produk_habis"] > 0:
        recommendations.append({
            "prioritas": "tinggi",
            "kategori": "Stok",
            "rekomendasi": f"{stock_analysis['ringkasan']['produk_habis']} produk kehabisan stok. Pelanggan mungkin kecewa.",
            "aksi": ["Segera order produk yang habis", "Aktifkan notifikasi stok menipis"]
        })
    
    if sales["ringkasan"]["pertumbuhan_laba"] > sales["ringkasan"]["pertumbuhan_penjualan"]:
        recommendations.append({
            "prioritas": "rendah",
            "kategori": "Keuangan",
            "rekomendasi": "Margin keuntungan membaik. Pertahankan strategi pricing saat ini.",
            "aksi": ["Dokumentasikan strategi yang berhasil", "Replikasi ke produk lain"]
        })
    
    # Sort by priority
    priority_order = {"tinggi": 0, "sedang": 1, "rendah": 2}
    recommendations.sort(key=lambda x: priority_order.get(x["prioritas"], 2))
    
    return {
        "tanggal": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "total_rekomendasi": len(recommendations),
        "rekomendasi": recommendations
    }

@router.get("/dashboard-widget")
async def get_dashboard_widget(current_user: dict = Depends(get_current_user)):
    """Get AI insights for dashboard widget"""
    insights = []
    
    # Quick sales insight
    sales = await get_sales_insights(7, current_user)
    if sales["ringkasan"]["pertumbuhan_penjualan"] > 0:
        insights.append({
            "icon": "trending_up",
            "color": "green",
            "title": "Penjualan Naik",
            "value": f"+{sales['ringkasan']['pertumbuhan_penjualan']:.1f}%",
            "description": "dibanding minggu lalu"
        })
    else:
        insights.append({
            "icon": "trending_down",
            "color": "red",
            "title": "Penjualan Turun",
            "value": f"{sales['ringkasan']['pertumbuhan_penjualan']:.1f}%",
            "description": "dibanding minggu lalu"
        })
    
    # Stock critical
    stock = await get_stock_analysis(current_user)
    if stock["ringkasan"]["produk_stok_menipis"] > 0:
        insights.append({
            "icon": "warning",
            "color": "amber",
            "title": "Stok Kritis",
            "value": str(stock["ringkasan"]["produk_stok_menipis"]),
            "description": "produk perlu restock"
        })
    
    # Branch performance (for owner/admin only)
    if current_user.get("role") in ["owner", "admin"]:
        try:
            branch_perf = await get_branch_performance(7, current_user)
            if branch_perf["performa_cabang"]:
                best = branch_perf["performa_cabang"][0]
                insights.append({
                    "icon": "store",
                    "color": "blue",
                    "title": "Cabang Terbaik",
                    "value": best["nama_cabang"],
                    "description": f"Rp {best['total_penjualan']:,.0f}"
                })
                
                if len(branch_perf["performa_cabang"]) > 1:
                    worst = branch_perf["performa_cabang"][-1]
                    insights.append({
                        "icon": "alert",
                        "color": "red",
                        "title": "Perlu Perhatian",
                        "value": worst["nama_cabang"],
                        "description": "Penjualan terendah"
                    })
        except:
            pass
    
    # Quick recommendation
    restock = await get_restock_recommendations(current_user)
    if restock["total_produk_perlu_restock"] > 0:
        insights.append({
            "icon": "shopping_cart",
            "color": "purple",
            "title": "Rekomendasi Order",
            "value": f"Rp {restock['total_estimasi_biaya']:,.0f}",
            "description": f"{restock['total_produk_perlu_restock']} produk"
        })
    
    return {"insights": insights[:5]}  # Max 5 insights
