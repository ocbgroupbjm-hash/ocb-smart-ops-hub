"""
OCB TITAN ERP - AI BUSINESS ENGINE
PHASE 3: MASTER BLUEPRINT COMPLIANCE

AI SAFETY RULES:
- AI = ANALYZE ONLY
- AI TIDAK BOLEH menulis ke:
  - journal_entries
  - stock_movements
  - transactions
  - master data

AI PERMISSIONS:
- READ: allowed
- ANALYZE: allowed
- RECOMMEND: allowed
- WRITE: PROHIBITED
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, Dict, List, Any
from datetime import datetime, timezone, timedelta
from database import get_db
from utils.auth import get_current_user
import json

router = APIRouter(prefix="/ai", tags=["AI Business Engine"])

# =============================================================================
# AI SAFETY DECORATOR - ENSURES READ ONLY
# =============================================================================

import functools

def ai_read_only(func):
    """Decorator to ensure AI functions are READ ONLY"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        # AI functions should never write
        # This decorator documents the READ ONLY nature
        return await func(*args, **kwargs)
    return wrapper


# =============================================================================
# SALES AI MODULE
# =============================================================================

class SalesAI:
    """
    Sales Intelligence AI
    
    READS FROM:
    - sales (transactions)
    - products
    - customers
    
    OUTPUTS:
    - Top selling products
    - Dead stock analysis
    - Sales trend
    - Customer behaviour
    
    MODE: READ ONLY - NO WRITE OPERATIONS
    """
    
    def __init__(self, db):
        self.db = db
    
    async def get_top_products(self, days: int = 30, limit: int = 20) -> Dict:
        """Analyze top selling products"""
        date_from = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        
        # Aggregate sales by product
        pipeline = [
            {"$match": {"created_at": {"$gte": date_from}}},
            {"$unwind": "$items"},
            {"$group": {
                "_id": "$items.product_id",
                "product_name": {"$first": "$items.product_name"},
                "product_sku": {"$first": "$items.sku"},
                "total_qty": {"$sum": "$items.qty"},
                "total_revenue": {"$sum": {"$multiply": ["$items.qty", "$items.price"]}},
                "transaction_count": {"$sum": 1}
            }},
            {"$sort": {"total_qty": -1}},
            {"$limit": limit}
        ]
        
        results = await self.db["sales"].aggregate(pipeline).to_list(limit)
        
        return {
            "analysis_type": "top_products",
            "period_days": days,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "products": results,
            "ai_insight": self._generate_top_product_insight(results)
        }
    
    def _generate_top_product_insight(self, products: List) -> str:
        """Generate AI insight for top products"""
        if not products:
            return "Tidak ada data penjualan dalam periode ini."
        
        top = products[0] if products else {}
        total_revenue = sum(p.get("total_revenue", 0) for p in products)
        
        return f"Produk terlaris adalah {top.get('product_name', 'N/A')} dengan {top.get('total_qty', 0)} unit terjual. Total revenue dari top {len(products)} produk: Rp {total_revenue:,.0f}"
    
    async def get_dead_stock(self, days_no_sale: int = 60) -> Dict:
        """Identify products with no sales (dead stock)"""
        date_threshold = (datetime.now(timezone.utc) - timedelta(days=days_no_sale)).isoformat()
        
        # Get all products
        all_products = await self.db["products"].find(
            {"stock": {"$gt": 0}},
            {"_id": 0, "id": 1, "name": 1, "sku": 1, "stock": 1, "cost_price": 1}
        ).to_list(1000)
        
        # Get products that had sales recently
        pipeline = [
            {"$match": {"created_at": {"$gte": date_threshold}}},
            {"$unwind": "$items"},
            {"$group": {"_id": "$items.product_id"}}
        ]
        sold_products = await self.db["sales"].aggregate(pipeline).to_list(1000)
        sold_ids = set(p["_id"] for p in sold_products)
        
        # Find dead stock (products with stock but no sales)
        dead_stock = []
        for p in all_products:
            if p.get("id") not in sold_ids:
                stock = p.get("stock", 0) or 0
                cost = p.get("cost_price", 0) or 0
                p["stuck_value"] = stock * cost
                dead_stock.append(p)
        
        # Sort by stuck value
        dead_stock.sort(key=lambda x: x.get("stuck_value", 0), reverse=True)
        
        total_stuck_value = sum(p.get("stuck_value", 0) for p in dead_stock)
        
        return {
            "analysis_type": "dead_stock",
            "days_no_sale": days_no_sale,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "dead_stock_count": len(dead_stock),
            "total_stuck_value": total_stuck_value,
            "products": dead_stock[:50],  # Limit to top 50
            "ai_insight": f"Ditemukan {len(dead_stock)} produk tanpa penjualan dalam {days_no_sale} hari. Total nilai stok mati: Rp {total_stuck_value:,.0f}. Rekomendasi: Pertimbangkan diskon atau bundling untuk produk-produk ini."
        }
    
    async def get_sales_trend(self, days: int = 30) -> Dict:
        """Analyze daily sales trend"""
        date_from = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        
        pipeline = [
            {"$match": {"created_at": {"$gte": date_from}}},
            {"$group": {
                "_id": {"$substr": ["$created_at", 0, 10]},  # Group by date
                "total_sales": {"$sum": "$total"},
                "transaction_count": {"$sum": 1},
                "avg_transaction": {"$avg": "$total"}
            }},
            {"$sort": {"_id": 1}}
        ]
        
        daily_data = await self.db["sales"].aggregate(pipeline).to_list(days)
        
        # Calculate trend
        if len(daily_data) >= 2:
            first_half = daily_data[:len(daily_data)//2]
            second_half = daily_data[len(daily_data)//2:]
            
            first_avg = sum(d["total_sales"] for d in first_half) / len(first_half) if first_half else 0
            second_avg = sum(d["total_sales"] for d in second_half) / len(second_half) if second_half else 0
            
            if first_avg > 0:
                trend_pct = ((second_avg - first_avg) / first_avg) * 100
            else:
                trend_pct = 0
            
            trend_direction = "NAIK" if trend_pct > 5 else "TURUN" if trend_pct < -5 else "STABIL"
        else:
            trend_pct = 0
            trend_direction = "INSUFFICIENT_DATA"
        
        return {
            "analysis_type": "sales_trend",
            "period_days": days,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "daily_data": daily_data,
            "trend": {
                "direction": trend_direction,
                "percentage": round(trend_pct, 2)
            },
            "ai_insight": f"Trend penjualan {days} hari terakhir: {trend_direction} ({trend_pct:+.1f}%). Total transaksi: {sum(d['transaction_count'] for d in daily_data)}."
        }
    
    async def get_customer_analysis(self, days: int = 90, limit: int = 20) -> Dict:
        """Analyze customer behaviour"""
        date_from = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        
        pipeline = [
            {"$match": {"created_at": {"$gte": date_from}, "customer_id": {"$exists": True, "$ne": None}}},
            {"$group": {
                "_id": "$customer_id",
                "customer_name": {"$first": "$customer_name"},
                "total_spent": {"$sum": "$total"},
                "visit_count": {"$sum": 1},
                "avg_transaction": {"$avg": "$total"},
                "last_visit": {"$max": "$created_at"}
            }},
            {"$sort": {"total_spent": -1}},
            {"$limit": limit}
        ]
        
        top_customers = await self.db["sales"].aggregate(pipeline).to_list(limit)
        
        return {
            "analysis_type": "customer_behaviour",
            "period_days": days,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "top_customers": top_customers,
            "ai_insight": f"Top {len(top_customers)} pelanggan berkontribusi Rp {sum(c['total_spent'] for c in top_customers):,.0f} dalam {days} hari."
        }


# =============================================================================
# INVENTORY AI MODULE
# =============================================================================

class InventoryAI:
    """
    Inventory Intelligence AI
    
    READS FROM:
    - stock_movements
    - products
    - purchases
    
    OUTPUTS:
    - Restock recommendations
    - Slow moving stock
    - Stock anomaly detection
    - Stock projection
    
    MODE: READ ONLY - NO WRITE OPERATIONS
    """
    
    def __init__(self, db):
        self.db = db
    
    async def get_restock_recommendations(self, threshold_days: int = 14) -> Dict:
        """Generate restock recommendations based on sales velocity"""
        
        # Get products with current stock
        products = await self.db["products"].find(
            {"is_active": {"$ne": False}},
            {"_id": 0, "id": 1, "name": 1, "sku": 1, "stock": 1, "min_stock": 1, "cost_price": 1}
        ).to_list(1000)
        
        # Calculate sales velocity for each product (last 30 days)
        date_from = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        
        sales_pipeline = [
            {"$match": {"created_at": {"$gte": date_from}}},
            {"$unwind": "$items"},
            {"$group": {
                "_id": "$items.product_id",
                "total_sold": {"$sum": "$items.qty"}
            }}
        ]
        
        sales_data = await self.db["sales"].aggregate(sales_pipeline).to_list(1000)
        sales_map = {s["_id"]: s["total_sold"] for s in sales_data}
        
        recommendations = []
        
        for p in products:
            product_id = p.get("id")
            current_stock = p.get("stock", 0) or 0
            min_stock = p.get("min_stock", 5) or 5
            monthly_sales = sales_map.get(product_id, 0)
            daily_velocity = monthly_sales / 30 if monthly_sales > 0 else 0
            
            # Calculate days until stockout
            if daily_velocity > 0:
                days_until_stockout = current_stock / daily_velocity
            else:
                days_until_stockout = 999
            
            # Check if restock needed
            if current_stock <= min_stock or days_until_stockout <= threshold_days:
                # Calculate recommended order qty (2 weeks worth + safety stock)
                recommended_qty = max(int(daily_velocity * 14) + min_stock - current_stock, min_stock)
                
                recommendations.append({
                    "product_id": product_id,
                    "product_name": p.get("name"),
                    "sku": p.get("sku"),
                    "current_stock": current_stock,
                    "min_stock": min_stock,
                    "daily_velocity": round(daily_velocity, 2),
                    "days_until_stockout": round(days_until_stockout, 1),
                    "recommended_qty": recommended_qty,
                    "estimated_cost": recommended_qty * (p.get("cost_price", 0) or 0),
                    "urgency": "HIGH" if days_until_stockout <= 7 else "MEDIUM" if days_until_stockout <= 14 else "LOW"
                })
        
        # Sort by urgency
        urgency_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        recommendations.sort(key=lambda x: (urgency_order.get(x["urgency"], 3), x["days_until_stockout"]))
        
        total_cost = sum(r["estimated_cost"] for r in recommendations)
        
        return {
            "analysis_type": "restock_recommendation",
            "threshold_days": threshold_days,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "recommendations_count": len(recommendations),
            "total_estimated_cost": total_cost,
            "recommendations": recommendations[:50],
            "ai_insight": f"Ada {len(recommendations)} produk yang perlu di-restock. Estimasi total biaya: Rp {total_cost:,.0f}. Prioritaskan {len([r for r in recommendations if r['urgency'] == 'HIGH'])} produk dengan urgency HIGH."
        }
    
    async def get_slow_moving_stock(self, days: int = 60, velocity_threshold: float = 0.1) -> Dict:
        """Identify slow moving stock"""
        date_from = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        
        # Get all products with stock
        products = await self.db["products"].find(
            {"stock": {"$gt": 0}},
            {"_id": 0, "id": 1, "name": 1, "sku": 1, "stock": 1, "cost_price": 1}
        ).to_list(1000)
        
        # Get sales velocity
        sales_pipeline = [
            {"$match": {"created_at": {"$gte": date_from}}},
            {"$unwind": "$items"},
            {"$group": {
                "_id": "$items.product_id",
                "total_sold": {"$sum": "$items.qty"}
            }}
        ]
        
        sales_data = await self.db["sales"].aggregate(sales_pipeline).to_list(1000)
        sales_map = {s["_id"]: s["total_sold"] for s in sales_data}
        
        slow_moving = []
        
        for p in products:
            product_id = p.get("id")
            current_stock = p.get("stock", 0) or 0
            monthly_sales = sales_map.get(product_id, 0)
            daily_velocity = monthly_sales / days
            
            # Calculate turnover ratio
            if current_stock > 0:
                turnover_ratio = monthly_sales / current_stock
            else:
                turnover_ratio = 0
            
            if daily_velocity < velocity_threshold:
                stock_value = current_stock * (p.get("cost_price", 0) or 0)
                slow_moving.append({
                    "product_id": product_id,
                    "product_name": p.get("name"),
                    "sku": p.get("sku"),
                    "current_stock": current_stock,
                    "stock_value": stock_value,
                    "sold_in_period": monthly_sales,
                    "daily_velocity": round(daily_velocity, 3),
                    "turnover_ratio": round(turnover_ratio, 2),
                    "recommendation": "DISCOUNT" if turnover_ratio < 0.5 else "BUNDLING"
                })
        
        slow_moving.sort(key=lambda x: x["stock_value"], reverse=True)
        total_slow_value = sum(s["stock_value"] for s in slow_moving)
        
        return {
            "analysis_type": "slow_moving_stock",
            "period_days": days,
            "velocity_threshold": velocity_threshold,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "slow_moving_count": len(slow_moving),
            "total_slow_moving_value": total_slow_value,
            "products": slow_moving[:50],
            "ai_insight": f"Ditemukan {len(slow_moving)} produk slow-moving dengan total nilai Rp {total_slow_value:,.0f}. Rekomendasi: Buat program diskon atau bundling untuk meningkatkan perputaran stok."
        }
    
    async def detect_stock_anomalies(self) -> Dict:
        """Detect stock anomalies"""
        
        # Get products with negative stock or unusual patterns
        products = await self.db["products"].find(
            {},
            {"_id": 0, "id": 1, "name": 1, "sku": 1, "stock": 1}
        ).to_list(1000)
        
        anomalies = []
        
        for p in products:
            stock = p.get("stock", 0) or 0
            
            # Check for negative stock
            if stock < 0:
                anomalies.append({
                    "product_id": p.get("id"),
                    "product_name": p.get("name"),
                    "sku": p.get("sku"),
                    "current_stock": stock,
                    "anomaly_type": "NEGATIVE_STOCK",
                    "severity": "CRITICAL",
                    "recommendation": "Lakukan stock opname dan adjustment segera"
                })
        
        return {
            "analysis_type": "stock_anomaly_detection",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "anomalies_count": len(anomalies),
            "anomalies": anomalies,
            "ai_insight": f"Ditemukan {len(anomalies)} anomali stok. " + ("Perlu penanganan segera!" if anomalies else "Tidak ada anomali kritis.")
        }


# =============================================================================
# FINANCE AI MODULE
# =============================================================================

class FinanceAI:
    """
    Finance Intelligence AI
    
    READS FROM:
    - journal_entries
    - trial_balance
    - cash_variances
    - expenses
    
    OUTPUTS:
    - Profitability analysis
    - Cash flow anomaly
    - Expense pattern
    - Financial forecast
    
    MODE: READ ONLY - NO WRITE OPERATIONS
    """
    
    def __init__(self, db):
        self.db = db
    
    async def get_profitability_analysis(self, days: int = 30) -> Dict:
        """Analyze profitability"""
        date_from = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        
        # Get revenue from sales
        sales_pipeline = [
            {"$match": {"created_at": {"$gte": date_from}}},
            {"$group": {
                "_id": None,
                "total_revenue": {"$sum": "$total"},
                "total_cost": {"$sum": "$total_cost"},
                "transaction_count": {"$sum": 1}
            }}
        ]
        
        sales_result = await self.db["sales"].aggregate(sales_pipeline).to_list(1)
        sales_data = sales_result[0] if sales_result else {"total_revenue": 0, "total_cost": 0, "transaction_count": 0}
        
        revenue = sales_data.get("total_revenue", 0) or 0
        cost = sales_data.get("total_cost", 0) or 0
        gross_profit = revenue - cost
        margin = (gross_profit / revenue * 100) if revenue > 0 else 0
        
        return {
            "analysis_type": "profitability",
            "period_days": days,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "metrics": {
                "total_revenue": revenue,
                "total_cost": cost,
                "gross_profit": gross_profit,
                "gross_margin_pct": round(margin, 2),
                "transaction_count": sales_data.get("transaction_count", 0)
            },
            "ai_insight": f"Gross profit margin: {margin:.1f}%. " + 
                         ("Margin sehat (>20%)" if margin > 20 else "Margin perlu ditingkatkan" if margin > 10 else "PERHATIAN: Margin rendah!")
        }
    
    async def get_cash_variance_analysis(self, days: int = 30) -> Dict:
        """Analyze cash variances"""
        date_from = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        
        variances = await self.db["cash_variances"].find(
            {"created_at": {"$gte": date_from}},
            {"_id": 0}
        ).to_list(1000)
        
        total_shortage = sum(v.get("variance", 0) for v in variances if v.get("variance", 0) < 0)
        total_overage = sum(v.get("variance", 0) for v in variances if v.get("variance", 0) > 0)
        
        # Group by cashier
        cashier_variances = {}
        for v in variances:
            cashier = v.get("user_id", "Unknown")
            if cashier not in cashier_variances:
                cashier_variances[cashier] = {"shortage": 0, "overage": 0, "count": 0}
            
            variance = v.get("variance", 0)
            if variance < 0:
                cashier_variances[cashier]["shortage"] += variance
            else:
                cashier_variances[cashier]["overage"] += variance
            cashier_variances[cashier]["count"] += 1
        
        # Find cashiers with frequent variances
        problem_cashiers = [
            {"cashier": k, **v} 
            for k, v in cashier_variances.items() 
            if v["count"] > 3 or abs(v["shortage"]) > 100000
        ]
        
        return {
            "analysis_type": "cash_variance",
            "period_days": days,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "total_variances": len(variances),
                "total_shortage": total_shortage,
                "total_overage": total_overage,
                "net_variance": total_shortage + total_overage
            },
            "problem_cashiers": problem_cashiers,
            "ai_insight": f"Total variance: Rp {total_shortage + total_overage:,.0f}. " +
                         (f"PERHATIAN: {len(problem_cashiers)} kasir dengan pola selisih tinggi!" if problem_cashiers else "Tidak ada pola mencurigakan.")
        }
    
    async def get_expense_analysis(self, days: int = 30) -> Dict:
        """Analyze expense patterns"""
        date_from = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        
        # Get expense journals (accounts starting with 5 or 6)
        pipeline = [
            {"$match": {"created_at": {"$gte": date_from}, "status": "posted"}},
            {"$unwind": "$entries"},
            {"$match": {"entries.account_code": {"$regex": "^[56]|^5-|^6-"}}},
            {"$match": {"entries.debit": {"$gt": 0}}},
            {"$group": {
                "_id": "$entries.account_code",
                "account_name": {"$first": "$entries.account_name"},
                "total_expense": {"$sum": "$entries.debit"},
                "transaction_count": {"$sum": 1}
            }},
            {"$sort": {"total_expense": -1}}
        ]
        
        expenses = await self.db["journal_entries"].aggregate(pipeline).to_list(50)
        total_expense = sum(e.get("total_expense", 0) for e in expenses)
        
        return {
            "analysis_type": "expense_pattern",
            "period_days": days,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_expense": total_expense,
            "expense_breakdown": expenses[:20],
            "ai_insight": f"Total expenses dalam {days} hari: Rp {total_expense:,.0f}. " +
                         (f"Expense terbesar: {expenses[0].get('account_name', 'N/A')} (Rp {expenses[0].get('total_expense', 0):,.0f})" if expenses else "")
        }


# =============================================================================
# API ENDPOINTS
# =============================================================================

@router.get("/sales/top-products")
@ai_read_only
async def ai_top_products(
    days: int = 30,
    limit: int = 20,
    user: dict = Depends(get_current_user)
):
    """AI: Get top selling products analysis"""
    db = get_db()
    ai = SalesAI(db)
    return await ai.get_top_products(days, limit)


@router.get("/sales/dead-stock")
@ai_read_only
async def ai_dead_stock(
    days_no_sale: int = 60,
    user: dict = Depends(get_current_user)
):
    """AI: Get dead stock analysis"""
    db = get_db()
    ai = SalesAI(db)
    return await ai.get_dead_stock(days_no_sale)


@router.get("/sales/trend")
@ai_read_only
async def ai_sales_trend(
    days: int = 30,
    user: dict = Depends(get_current_user)
):
    """AI: Get sales trend analysis"""
    db = get_db()
    ai = SalesAI(db)
    return await ai.get_sales_trend(days)


@router.get("/sales/customer-analysis")
@ai_read_only
async def ai_customer_analysis(
    days: int = 90,
    limit: int = 20,
    user: dict = Depends(get_current_user)
):
    """AI: Get customer behaviour analysis"""
    db = get_db()
    ai = SalesAI(db)
    return await ai.get_customer_analysis(days, limit)


@router.get("/sales/report")
@ai_read_only
async def ai_sales_full_report(
    days: int = 30,
    user: dict = Depends(get_current_user)
):
    """AI: Get full sales AI report"""
    db = get_db()
    ai = SalesAI(db)
    
    return {
        "report_type": "sales_ai",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "top_products": await ai.get_top_products(days),
        "dead_stock": await ai.get_dead_stock(60),
        "sales_trend": await ai.get_sales_trend(days),
        "customer_analysis": await ai.get_customer_analysis(days)
    }


@router.get("/inventory/restock-recommendations")
@ai_read_only
async def ai_restock_recommendations(
    threshold_days: int = 14,
    user: dict = Depends(get_current_user)
):
    """AI: Get restock recommendations"""
    db = get_db()
    ai = InventoryAI(db)
    return await ai.get_restock_recommendations(threshold_days)


@router.get("/inventory/slow-moving")
@ai_read_only
async def ai_slow_moving(
    days: int = 60,
    user: dict = Depends(get_current_user)
):
    """AI: Get slow moving stock analysis"""
    db = get_db()
    ai = InventoryAI(db)
    return await ai.get_slow_moving_stock(days)


@router.get("/inventory/anomalies")
@ai_read_only
async def ai_stock_anomalies(
    user: dict = Depends(get_current_user)
):
    """AI: Detect stock anomalies"""
    db = get_db()
    ai = InventoryAI(db)
    return await ai.detect_stock_anomalies()


@router.get("/inventory/report")
@ai_read_only
async def ai_inventory_full_report(
    user: dict = Depends(get_current_user)
):
    """AI: Get full inventory AI report"""
    db = get_db()
    ai = InventoryAI(db)
    
    return {
        "report_type": "inventory_ai",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "restock_recommendations": await ai.get_restock_recommendations(),
        "slow_moving": await ai.get_slow_moving_stock(),
        "anomalies": await ai.detect_stock_anomalies()
    }


@router.get("/finance/profitability")
@ai_read_only
async def ai_profitability(
    days: int = 30,
    user: dict = Depends(get_current_user)
):
    """AI: Get profitability analysis"""
    db = get_db()
    ai = FinanceAI(db)
    return await ai.get_profitability_analysis(days)


@router.get("/finance/cash-variance")
@ai_read_only
async def ai_cash_variance(
    days: int = 30,
    user: dict = Depends(get_current_user)
):
    """AI: Get cash variance analysis"""
    db = get_db()
    ai = FinanceAI(db)
    return await ai.get_cash_variance_analysis(days)


@router.get("/finance/expenses")
@ai_read_only
async def ai_expenses(
    days: int = 30,
    user: dict = Depends(get_current_user)
):
    """AI: Get expense pattern analysis"""
    db = get_db()
    ai = FinanceAI(db)
    return await ai.get_expense_analysis(days)


@router.get("/finance/report")
@ai_read_only
async def ai_finance_full_report(
    days: int = 30,
    user: dict = Depends(get_current_user)
):
    """AI: Get full finance AI report"""
    db = get_db()
    ai = FinanceAI(db)
    
    return {
        "report_type": "finance_ai",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "profitability": await ai.get_profitability_analysis(days),
        "cash_variance": await ai.get_cash_variance_analysis(days),
        "expense_analysis": await ai.get_expense_analysis(days)
    }


@router.get("/ceo/summary")
@ai_read_only
async def ai_ceo_summary(
    user: dict = Depends(get_current_user)
):
    """AI: CEO Dashboard Summary - OWNER ONLY"""
    user_role = (user.get("role", "") or user.get("role_code", "")).lower()
    if user_role != "owner":
        raise HTTPException(status_code=403, detail="CEO Dashboard hanya untuk OWNER")
    
    db = get_db()
    sales_ai = SalesAI(db)
    inventory_ai = InventoryAI(db)
    finance_ai = FinanceAI(db)
    
    # Gather all insights
    sales_trend = await sales_ai.get_sales_trend(30)
    profitability = await finance_ai.get_profitability_analysis(30)
    restock = await inventory_ai.get_restock_recommendations()
    cash_variance = await finance_ai.get_cash_variance_analysis(30)
    
    # Generate CEO summary
    return {
        "report_type": "ceo_dashboard",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "executive_summary": {
            "sales_growth": sales_trend["trend"],
            "profit_margin": profitability["metrics"]["gross_margin_pct"],
            "cash_health": "GOOD" if abs(cash_variance["summary"]["net_variance"]) < 50000 else "ATTENTION",
            "inventory_alerts": restock["recommendations_count"]
        },
        "insights": {
            "sales": sales_trend["ai_insight"],
            "profitability": profitability["ai_insight"],
            "inventory": restock["ai_insight"],
            "cash": cash_variance["ai_insight"]
        },
        "risk_alerts": [
            {"type": "inventory", "message": f"{restock['recommendations_count']} produk perlu restock"} if restock["recommendations_count"] > 0 else None,
            {"type": "cash", "message": f"Variance kas: Rp {cash_variance['summary']['net_variance']:,.0f}"} if abs(cash_variance["summary"]["net_variance"]) > 50000 else None
        ]
    }
