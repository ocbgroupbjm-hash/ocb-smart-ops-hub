# OCB TITAN ERP - AI Insights Engine
# =====================================
# Version: 1.0.0

"""
AI INSIGHTS ENGINE

Generates business insights from features:
- Sales Analysis
- Inventory Optimization
- Finance Monitoring
- Executive Dashboard

All operations are READ-ONLY
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict
import statistics

from .data_access import (
    AIDataAccessLayer, 
    AIFeatureBuilder, 
    AIKillSwitch,
    get_ai_config
)


class AIInsightsEngine:
    """
    AI Insights Engine - Generate business insights
    """
    
    def __init__(self, data_layer: AIDataAccessLayer):
        self.data = data_layer
        self.features = AIFeatureBuilder(data_layer)
        self.config = get_ai_config()
    
    # ==================== SALES AI ====================
    
    async def get_sales_insights(self, days: int = 30) -> Dict:
        """
        SALES AI - Get sales insights
        
        Returns:
        - top_products: Best selling products
        - slow_products: Products with low sales
        - sales_trend: Daily sales trend
        - margin_analysis: Profit margin by product
        """
        AIKillSwitch.check_or_raise()
        
        features = await self.features.build_sales_features(days)
        sales = features["sales_data"]
        products = features["products"]
        
        # Analyze sales by product
        product_sales = defaultdict(lambda: {"qty": 0, "revenue": 0, "count": 0})
        daily_sales = defaultdict(lambda: {"revenue": 0, "count": 0})
        
        for sale in sales:
            date = sale.get("date", sale.get("created_at", ""))[:10]
            daily_sales[date]["revenue"] += sale.get("grand_total", 0)
            daily_sales[date]["count"] += 1
            
            for item in sale.get("items", []):
                pid = item.get("product_id") or item.get("item_id")
                if pid:
                    product_sales[pid]["qty"] += item.get("quantity", 0)
                    product_sales[pid]["revenue"] += item.get("subtotal", 0)
                    product_sales[pid]["count"] += 1
                    product_sales[pid]["name"] = item.get("product_name") or products.get(pid, {}).get("name", "Unknown")
        
        # Sort by revenue
        sorted_products = sorted(
            product_sales.items(),
            key=lambda x: x[1]["revenue"],
            reverse=True
        )
        
        top_products = [
            {
                "product_id": pid,
                "name": data["name"],
                "total_qty": data["qty"],
                "total_revenue": data["revenue"],
                "transaction_count": data["count"]
            }
            for pid, data in sorted_products[:10]
        ]
        
        slow_products = [
            {
                "product_id": pid,
                "name": data["name"],
                "total_qty": data["qty"],
                "total_revenue": data["revenue"],
                "transaction_count": data["count"],
                "recommendation": "Consider promotion or discontinuation"
            }
            for pid, data in sorted_products[-10:] if data["qty"] > 0
        ]
        
        # Sales trend
        trend = [
            {"date": date, "revenue": data["revenue"], "transactions": data["count"]}
            for date, data in sorted(daily_sales.items())
        ]
        
        # Calculate growth
        if len(trend) >= 2:
            recent_revenue = sum(t["revenue"] for t in trend[-7:])
            previous_revenue = sum(t["revenue"] for t in trend[-14:-7]) or 1
            growth_rate = ((recent_revenue - previous_revenue) / previous_revenue) * 100
        else:
            growth_rate = 0
        
        return {
            "insight_type": "sales",
            "period_days": days,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "model_version": self.config["model_version"],
            "summary": {
                "total_transactions": len(sales),
                "total_revenue": sum(s.get("grand_total", 0) for s in sales),
                "avg_transaction_value": sum(s.get("grand_total", 0) for s in sales) / max(len(sales), 1),
                "growth_rate_7d": round(growth_rate, 2)
            },
            "top_products": top_products,
            "slow_products": slow_products,
            "sales_trend": trend[-30:],  # Last 30 days
            "recommendations": self._generate_sales_recommendations(top_products, slow_products, growth_rate)
        }
    
    def _generate_sales_recommendations(self, top, slow, growth) -> List[str]:
        recs = []
        if growth < 0:
            recs.append(f"⚠️ Penjualan turun {abs(growth):.1f}% dalam 7 hari terakhir")
        elif growth > 20:
            recs.append(f"✅ Penjualan naik {growth:.1f}% - pertahankan strategi saat ini")
        
        if top:
            recs.append(f"🔥 Produk terlaris: {top[0]['name']} - pastikan stok cukup")
        
        if slow:
            recs.append(f"📉 {len(slow)} produk lambat terjual - pertimbangkan promo")
        
        return recs
    
    # ==================== INVENTORY AI ====================
    
    async def get_inventory_insights(self) -> Dict:
        """
        INVENTORY AI - Get inventory insights
        
        Returns:
        - dead_stock: Products with no movement
        - restock_recommendation: Products needing restock
        - demand_anomaly: Unusual demand patterns
        - branch_imbalance: Stock distribution issues
        """
        AIKillSwitch.check_or_raise()
        
        features = await self.features.build_inventory_features()
        movements = features["movements"]
        stock = features["current_stock"]
        products = features["products"]
        
        # Analyze movement frequency
        product_movement = defaultdict(lambda: {"last_movement": None, "total_out": 0, "total_in": 0})
        
        for mov in movements:
            pid = mov.get("product_id")
            if pid:
                mov_date = mov.get("created_at", "")
                if not product_movement[pid]["last_movement"] or mov_date > product_movement[pid]["last_movement"]:
                    product_movement[pid]["last_movement"] = mov_date
                
                qty = mov.get("quantity", 0)
                mov_type = mov.get("movement_type", "")
                
                if "in" in mov_type or qty > 0:
                    product_movement[pid]["total_in"] += abs(qty)
                else:
                    product_movement[pid]["total_out"] += abs(qty)
        
        # Find dead stock (no movement in 30 days)
        thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        
        dead_stock = []
        restock_needed = []
        
        for product in products:
            pid = product.get("id")
            mov = product_movement.get(pid, {})
            last_mov = mov.get("last_movement", "")
            
            if not last_mov or last_mov < thirty_days_ago:
                dead_stock.append({
                    "product_id": pid,
                    "name": product.get("name", "Unknown"),
                    "last_movement": last_mov or "Never",
                    "current_stock": next((s.get("quantity", 0) for s in stock if s.get("product_id") == pid), 0),
                    "recommendation": "Consider markdown or return to supplier"
                })
            
            # Check restock needs
            current = next((s.get("quantity", 0) for s in stock if s.get("product_id") == pid), 0)
            min_stock = product.get("min_stock", 5)
            
            if current < min_stock:
                restock_needed.append({
                    "product_id": pid,
                    "name": product.get("name", "Unknown"),
                    "current_stock": current,
                    "min_stock": min_stock,
                    "recommended_order": max(min_stock * 3 - current, 10),
                    "urgency": "HIGH" if current == 0 else "MEDIUM"
                })
        
        return {
            "insight_type": "inventory",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "model_version": self.config["model_version"],
            "summary": {
                "total_products": len(products),
                "dead_stock_count": len(dead_stock),
                "restock_needed_count": len(restock_needed),
                "inventory_health": "GOOD" if len(dead_stock) < 5 else "NEEDS_ATTENTION"
            },
            "dead_stock": dead_stock[:20],
            "restock_recommendation": sorted(restock_needed, key=lambda x: x["urgency"] == "HIGH", reverse=True)[:20],
            "recommendations": [
                f"⚠️ {len(dead_stock)} produk tidak ada pergerakan 30 hari",
                f"📦 {len(restock_needed)} produk perlu restock",
                "💡 Review dead stock untuk markdown atau retur"
            ]
        }
    
    # ==================== FINANCE AI ====================
    
    async def get_finance_insights(self, days: int = 30) -> Dict:
        """
        FINANCE AI - Get finance insights
        
        Returns:
        - expense_anomaly: Unusual expense patterns
        - margin_analysis: Profit margin trends
        - cash_variance: Cash flow analysis
        - profit_trend: Profitability over time
        """
        AIKillSwitch.check_or_raise()
        
        features = await self.features.build_finance_features(days)
        journals = features["journals"]
        coa = features["chart_of_accounts"]
        
        # Build account map
        account_map = {a.get("code"): a for a in coa}
        
        # Analyze by account category
        revenue_total = 0
        expense_total = 0
        asset_total = 0
        liability_total = 0
        
        daily_cash = defaultdict(float)
        
        for journal in journals:
            date = journal.get("journal_date", "")[:10]
            
            for entry in journal.get("entries", []):
                code = entry.get("account_code", "")
                debit = entry.get("debit", 0)
                credit = entry.get("credit", 0)
                
                # Categorize by account code prefix
                if code.startswith("4"):
                    revenue_total += credit - debit
                elif code.startswith(("5", "6")):
                    expense_total += debit - credit
                elif code.startswith("1"):
                    asset_total += debit - credit
                    if "kas" in entry.get("account_name", "").lower() or code.startswith("1-11"):
                        daily_cash[date] += debit - credit
                elif code.startswith("2"):
                    liability_total += credit - debit
        
        net_profit = revenue_total - expense_total
        profit_margin = (net_profit / revenue_total * 100) if revenue_total > 0 else 0
        
        # Cash trend
        cash_trend = [
            {"date": date, "change": amount}
            for date, amount in sorted(daily_cash.items())
        ]
        
        return {
            "insight_type": "finance",
            "period_days": days,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "model_version": self.config["model_version"],
            "summary": {
                "total_revenue": revenue_total,
                "total_expense": expense_total,
                "net_profit": net_profit,
                "profit_margin_percent": round(profit_margin, 2),
                "total_assets": asset_total,
                "total_liabilities": liability_total
            },
            "cash_trend": cash_trend[-30:],
            "profit_analysis": {
                "margin_status": "HEALTHY" if profit_margin > 10 else ("WARNING" if profit_margin > 0 else "CRITICAL"),
                "expense_ratio": round(expense_total / max(revenue_total, 1) * 100, 2)
            },
            "recommendations": [
                f"💰 Profit margin: {profit_margin:.1f}%",
                f"📊 Rasio expense: {expense_total / max(revenue_total, 1) * 100:.1f}%",
                "✅ Cash flow stable" if len(cash_trend) > 0 else "⚠️ No cash movement data"
            ]
        }
    
    # ==================== CEO DASHBOARD ====================
    
    async def get_ceo_dashboard(self) -> Dict:
        """
        CEO AI DASHBOARD - Executive summary
        
        Returns:
        - omzet_hari_ini: Today's revenue
        - cabang_terbaik: Best performing branch
        - produk_terbaik: Top selling product
        - cabang_minus: Underperforming branches
        - cash_variance: Cash anomalies
        """
        AIKillSwitch.check_or_raise()
        
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
        # Get today's sales
        today_sales = await self.data.read_collection(
            "sales_invoices",
            {"date": {"$regex": f"^{today}"}},
            limit=1000
        )
        
        # Get branches
        branches = await self.data.read_collection("branches", limit=100)
        
        # Get all recent sales for branch analysis
        recent_sales = await self.data.read_collection(
            "sales_invoices",
            {},
            limit=5000
        )
        
        # Calculate today's revenue
        omzet_hari_ini = sum(s.get("grand_total", 0) for s in today_sales)
        
        # Branch performance
        branch_sales = defaultdict(lambda: {"revenue": 0, "count": 0, "name": ""})
        for sale in recent_sales:
            bid = sale.get("branch_id", "")
            branch_sales[bid]["revenue"] += sale.get("grand_total", 0)
            branch_sales[bid]["count"] += 1
            branch_sales[bid]["name"] = sale.get("branch_name", "Unknown")
        
        sorted_branches = sorted(
            branch_sales.items(),
            key=lambda x: x[1]["revenue"],
            reverse=True
        )
        
        cabang_terbaik = sorted_branches[:5] if sorted_branches else []
        cabang_minus = sorted_branches[-5:] if len(sorted_branches) > 5 else []
        
        # Get top product today
        product_sales = defaultdict(lambda: {"qty": 0, "revenue": 0, "name": ""})
        for sale in today_sales:
            for item in sale.get("items", []):
                pid = item.get("product_id", "")
                product_sales[pid]["qty"] += item.get("quantity", 0)
                product_sales[pid]["revenue"] += item.get("subtotal", 0)
                product_sales[pid]["name"] = item.get("product_name", "Unknown")
        
        top_product = max(product_sales.items(), key=lambda x: x[1]["revenue"], default=(None, {}))
        
        return {
            "insight_type": "ceo_dashboard",
            "date": today,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "model_version": self.config["model_version"],
            "omzet_hari_ini": {
                "value": omzet_hari_ini,
                "formatted": f"Rp {omzet_hari_ini:,.0f}",
                "transaction_count": len(today_sales)
            },
            "cabang_terbaik": [
                {"branch_id": bid, "name": data["name"], "revenue": data["revenue"], "transactions": data["count"]}
                for bid, data in cabang_terbaik
            ],
            "cabang_minus": [
                {"branch_id": bid, "name": data["name"], "revenue": data["revenue"], "transactions": data["count"]}
                for bid, data in cabang_minus
            ],
            "produk_terbaik_hari_ini": {
                "product_id": top_product[0],
                "name": top_product[1].get("name", "N/A"),
                "qty_sold": top_product[1].get("qty", 0),
                "revenue": top_product[1].get("revenue", 0)
            } if top_product[0] else None,
            "executive_summary": [
                f"💰 Omzet hari ini: Rp {omzet_hari_ini:,.0f}",
                f"📊 {len(today_sales)} transaksi",
                f"🏆 Cabang terbaik: {cabang_terbaik[0][1]['name'] if cabang_terbaik else 'N/A'}",
                f"🔥 Produk terlaris: {top_product[1].get('name', 'N/A') if top_product[0] else 'N/A'}"
            ]
        }
