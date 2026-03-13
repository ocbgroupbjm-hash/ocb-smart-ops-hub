# OCB TITAN ERP - Discount & Promotion Auto-Apply Engine
# Service untuk auto-apply diskon dan promosi saat transaksi POS/Sales
# WAJIB dipanggil saat membuat invoice atau POS transaction

from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
import uuid


class DiscountPromoEngine:
    """
    Engine untuk auto-apply diskon dan promosi.
    
    Flow:
    1. Saat item dipilih, evaluasi rule diskon dan promosi aktif
    2. Check: tanggal, jam, cabang, customer group, item/kategori/brand, min qty, min subtotal, priority, stackable
    3. Apply ke detail invoice
    """
    
    def __init__(self, db):
        self.db = db
        self.discounts = db["discounts"]
        self.promotions = db["promotions"]
        self.products = db["products"]
        self.customers = db["customers"]
        self.customer_groups = db["customer_groups"]
        self.categories = db["categories"]
        self.brands = db["brands"]
    
    # ==================== DISCOUNT ENGINE ====================
    
    async def get_active_discounts(
        self,
        branch_id: str = None,
        customer_group_id: str = None
    ) -> List[Dict]:
        """Get all active discounts"""
        now = datetime.now(timezone.utc)
        today = now.strftime("%Y-%m-%d")
        current_time = now.strftime("%H:%M")
        
        query = {"is_active": True}
        
        # Date filter
        query["$or"] = [
            {"start_date": {"$exists": False}},
            {"start_date": ""},
            {"start_date": {"$lte": today}}
        ]
        
        discounts = await self.discounts.find(query, {"_id": 0}).sort("priority", 1).to_list(100)
        
        # Filter by date/time and branch
        active_discounts = []
        for disc in discounts:
            # Check end date
            if disc.get("end_date") and disc["end_date"] < today:
                continue
            
            # Check time
            if disc.get("start_time") and disc["start_time"] > current_time:
                continue
            if disc.get("end_time") and disc["end_time"] < current_time:
                continue
            
            # Check branch
            if disc.get("target_type") == "branch" and disc.get("target_ids"):
                if branch_id not in disc["target_ids"]:
                    continue
            
            # Check customer group
            if disc.get("target_type") == "customer_group" and disc.get("target_ids"):
                if customer_group_id not in disc["target_ids"]:
                    continue
            
            # Check usage limit
            if disc.get("max_usage", 0) > 0 and disc.get("usage_count", 0) >= disc["max_usage"]:
                continue
            
            active_discounts.append(disc)
        
        return active_discounts
    
    async def apply_discount_to_item(
        self,
        item: Dict,
        discount: Dict,
        qty: int,
        subtotal: float
    ) -> Dict:
        """Apply discount to a single item"""
        discount_type = discount.get("discount_type", "percentage")
        discount_value = discount.get("discount_value", 0)
        
        # Check minimum requirements
        if discount.get("min_qty", 0) > 0 and qty < discount["min_qty"]:
            return {"applied": False, "reason": "Min qty not met"}
        
        if discount.get("min_purchase", 0) > 0 and subtotal < discount["min_purchase"]:
            return {"applied": False, "reason": "Min purchase not met"}
        
        # Calculate discount
        discount_amount = 0
        
        if discount_type == "percentage":
            discount_amount = subtotal * (discount_value / 100)
        elif discount_type == "nominal":
            discount_amount = discount_value
        elif discount_type == "per_pcs":
            discount_amount = discount_value * qty
        elif discount_type == "tiered":
            # Check tiers
            tiers = discount.get("tiers", [])
            applicable_tier = None
            for tier in sorted(tiers, key=lambda x: x.get("min_qty", 0), reverse=True):
                if qty >= tier.get("min_qty", 0) or subtotal >= tier.get("min_amount", 0):
                    applicable_tier = tier
                    break
            
            if applicable_tier:
                discount_amount = subtotal * (applicable_tier.get("discount_value", 0) / 100)
        
        return {
            "applied": True,
            "discount_id": discount.get("id"),
            "discount_code": discount.get("code"),
            "discount_name": discount.get("name"),
            "discount_type": discount_type,
            "discount_value": discount_value,
            "discount_amount": discount_amount,
            "priority": discount.get("priority", 1),
            "stackable": discount.get("stackable", False)
        }
    
    async def calculate_item_discounts(
        self,
        item: Dict,
        customer_id: str = None,
        branch_id: str = None
    ) -> List[Dict]:
        """
        Calculate all applicable discounts for an item.
        Returns list of applicable discounts sorted by priority.
        """
        product_id = item.get("product_id")
        qty = item.get("quantity", 0)
        unit_price = item.get("unit_price", 0)
        subtotal = qty * unit_price
        
        # Get product info
        product = await self.products.find_one({"id": product_id}, {"_id": 0})
        if not product:
            return []
        
        category_id = product.get("category_id")
        brand_id = product.get("brand_id")
        
        # Get customer group
        customer_group_id = None
        if customer_id:
            customer = await self.customers.find_one({"id": customer_id}, {"_id": 0})
            if customer:
                customer_group_id = customer.get("group_id")
        
        # Get active discounts
        active_discounts = await self.get_active_discounts(branch_id, customer_group_id)
        
        # Filter discounts by target
        applicable_discounts = []
        
        for disc in active_discounts:
            target_type = disc.get("target_type", "all")
            target_ids = disc.get("target_ids", [])
            
            applicable = False
            
            if target_type == "all":
                applicable = True
            elif target_type == "item" and product_id in target_ids:
                applicable = True
            elif target_type == "category" and category_id in target_ids:
                applicable = True
            elif target_type == "brand" and brand_id in target_ids:
                applicable = True
            elif target_type == "customer_group":
                # Already filtered in get_active_discounts
                applicable = True
            elif target_type == "branch":
                # Already filtered in get_active_discounts
                applicable = True
            
            if applicable:
                result = await self.apply_discount_to_item(item, disc, qty, subtotal)
                if result.get("applied"):
                    applicable_discounts.append(result)
        
        # Sort by priority and return
        applicable_discounts.sort(key=lambda x: x.get("priority", 999))
        
        return applicable_discounts
    
    # ==================== PROMOTION ENGINE ====================
    
    async def get_active_promotions(
        self,
        branch_id: str = None
    ) -> List[Dict]:
        """Get all active promotions"""
        now = datetime.now(timezone.utc)
        today = now.strftime("%Y-%m-%d")
        current_time = now.strftime("%H:%M")
        
        query = {"is_active": True}
        
        promotions = await self.promotions.find(query, {"_id": 0}).sort("priority", 1).to_list(100)
        
        # Filter by date/time
        active_promos = []
        for promo in promotions:
            # Check date
            if promo.get("start_date") and promo["start_date"] > today:
                continue
            if promo.get("end_date") and promo["end_date"] < today:
                continue
            
            # Check time
            if promo.get("start_time") and promo["start_time"] > current_time:
                continue
            if promo.get("end_time") and promo["end_time"] < current_time:
                continue
            
            # Check quota
            if promo.get("quota_limit", 0) > 0 and promo.get("quota_used", 0) >= promo["quota_limit"]:
                continue
            
            active_promos.append(promo)
        
        return active_promos
    
    async def check_promotion_trigger(
        self,
        promo: Dict,
        items: List[Dict],
        customer_id: str = None
    ) -> Dict:
        """Check if promotion trigger conditions are met"""
        trigger_type = promo.get("trigger_type", "item")
        trigger_item_ids = promo.get("trigger_item_ids", [])
        trigger_category_ids = promo.get("trigger_category_ids", [])
        trigger_brand_ids = promo.get("trigger_brand_ids", [])
        trigger_min_qty = promo.get("trigger_min_qty", 0)
        trigger_min_subtotal = promo.get("trigger_min_subtotal", 0)
        
        # Calculate totals
        total_qty = 0
        total_subtotal = 0
        trigger_items_found = []
        
        for item in items:
            product_id = item.get("product_id")
            qty = item.get("quantity", 0)
            subtotal = qty * item.get("unit_price", 0)
            
            # Get product info
            product = await self.products.find_one({"id": product_id}, {"_id": 0})
            if not product:
                continue
            
            # Check if item matches trigger
            matches_trigger = False
            
            if trigger_type == "item" and trigger_item_ids:
                if product_id in trigger_item_ids:
                    matches_trigger = True
            elif trigger_type == "category" and trigger_category_ids:
                if product.get("category_id") in trigger_category_ids:
                    matches_trigger = True
            elif trigger_type == "brand" and trigger_brand_ids:
                if product.get("brand_id") in trigger_brand_ids:
                    matches_trigger = True
            elif trigger_type == "qty":
                matches_trigger = True
            elif trigger_type == "subtotal":
                matches_trigger = True
            
            if matches_trigger:
                total_qty += qty
                total_subtotal += subtotal
                trigger_items_found.append(item)
        
        # Check minimum requirements
        if trigger_min_qty > 0 and total_qty < trigger_min_qty:
            return {"triggered": False, "reason": f"Min qty {trigger_min_qty} not met (current: {total_qty})"}
        
        if trigger_min_subtotal > 0 and total_subtotal < trigger_min_subtotal:
            return {"triggered": False, "reason": f"Min subtotal {trigger_min_subtotal} not met (current: {total_subtotal})"}
        
        if not trigger_items_found and trigger_type in ["item", "category", "brand"]:
            return {"triggered": False, "reason": "No matching items found"}
        
        return {
            "triggered": True,
            "trigger_qty": total_qty,
            "trigger_subtotal": total_subtotal,
            "trigger_items": trigger_items_found
        }
    
    async def calculate_promotion_benefit(
        self,
        promo: Dict,
        trigger_result: Dict,
        items: List[Dict]
    ) -> Dict:
        """Calculate promotion benefit"""
        benefit_type = promo.get("benefit_type", "discount")
        
        if benefit_type == "discount":
            # Percentage or nominal discount
            discount_type = promo.get("benefit_discount_type", "percentage")
            discount_value = promo.get("benefit_discount_value", 0)
            
            total_subtotal = sum(i.get("quantity", 0) * i.get("unit_price", 0) for i in items)
            
            if discount_type == "percentage":
                benefit_amount = total_subtotal * (discount_value / 100)
            else:
                benefit_amount = discount_value
            
            return {
                "benefit_type": "discount",
                "benefit_amount": benefit_amount,
                "description": f"Diskon {discount_value}{'%' if discount_type == 'percentage' else ''}"
            }
        
        elif benefit_type == "free_item":
            # Free item(s)
            free_item_ids = promo.get("benefit_free_item_ids", [])
            free_qty = promo.get("benefit_free_qty", 1)
            
            free_items = []
            for item_id in free_item_ids:
                product = await self.products.find_one({"id": item_id}, {"_id": 0})
                if product:
                    free_items.append({
                        "product_id": item_id,
                        "product_code": product.get("code", ""),
                        "product_name": product.get("name", ""),
                        "quantity": free_qty,
                        "unit_price": 0,  # Free
                        "is_promo_item": True,
                        "promo_code": promo.get("code")
                    })
            
            return {
                "benefit_type": "free_item",
                "free_items": free_items,
                "description": f"Gratis {free_qty} {', '.join([p.get('product_name', '') for p in free_items])}"
            }
        
        elif benefit_type == "bundle_price":
            # Special bundle price
            bundle_price = promo.get("benefit_bundle_price", 0)
            original_price = sum(i.get("quantity", 0) * i.get("unit_price", 0) for i in trigger_result.get("trigger_items", []))
            benefit_amount = original_price - bundle_price
            
            return {
                "benefit_type": "bundle_price",
                "bundle_price": bundle_price,
                "benefit_amount": benefit_amount,
                "description": f"Harga bundle Rp {bundle_price:,.0f}"
            }
        
        elif benefit_type == "special_price":
            # Special price for specific items
            special_price = promo.get("benefit_special_price", 0)
            
            return {
                "benefit_type": "special_price",
                "special_price": special_price,
                "description": f"Harga khusus Rp {special_price:,.0f}"
            }
        
        return {"benefit_type": "none", "benefit_amount": 0}
    
    async def calculate_promotions(
        self,
        items: List[Dict],
        customer_id: str = None,
        branch_id: str = None
    ) -> List[Dict]:
        """
        Calculate all applicable promotions for a transaction.
        Returns list of applicable promotions with benefits.
        """
        active_promos = await self.get_active_promotions(branch_id)
        
        applicable_promos = []
        applied_non_stackable = False
        
        for promo in active_promos:
            # Skip if non-stackable promo already applied
            if applied_non_stackable and not promo.get("stackable", False):
                continue
            
            # Check trigger conditions
            trigger_result = await self.check_promotion_trigger(promo, items, customer_id)
            
            if trigger_result.get("triggered"):
                # Calculate benefit
                benefit = await self.calculate_promotion_benefit(promo, trigger_result, items)
                
                applicable_promos.append({
                    "promo_id": promo.get("id"),
                    "promo_code": promo.get("code"),
                    "promo_name": promo.get("name"),
                    "promo_type": promo.get("promo_type"),
                    "trigger": trigger_result,
                    "benefit": benefit,
                    "priority": promo.get("priority", 1),
                    "stackable": promo.get("stackable", False)
                })
                
                if not promo.get("stackable", False):
                    applied_non_stackable = True
        
        return applicable_promos
    
    # ==================== PRICE LEVEL ENGINE ====================
    
    async def get_price_for_customer(
        self,
        product_id: str,
        customer_id: str
    ) -> Dict:
        """
        Get correct price for item based on customer's group price level.
        """
        # Get product
        product = await self.products.find_one({"id": product_id}, {"_id": 0})
        if not product:
            return {"price": 0, "price_level": 0, "source": "not_found"}
        
        default_price = product.get("selling_price", 0)
        
        if not customer_id:
            return {
                "price": default_price,
                "price_level": 1,
                "source": "default",
                "original_price": default_price
            }
        
        # Get customer
        customer = await self.customers.find_one({"id": customer_id}, {"_id": 0})
        if not customer:
            return {
                "price": default_price,
                "price_level": 1,
                "source": "default",
                "original_price": default_price
            }
        
        # Get customer group
        group_id = customer.get("group_id")
        if not group_id:
            return {
                "price": default_price,
                "price_level": 1,
                "source": "default",
                "original_price": default_price
            }
        
        group = await self.customer_groups.find_one({"id": group_id}, {"_id": 0})
        if not group:
            return {
                "price": default_price,
                "price_level": 1,
                "source": "default",
                "original_price": default_price
            }
        
        price_level = group.get("price_level", 1)
        
        # Get price based on level
        price_field = f"price_level_{price_level}"
        price = product.get(price_field, 0)
        
        # Fallback to selling_price if level price is 0
        if not price or price == 0:
            price = default_price
            source = "fallback_default"
        else:
            source = f"price_level_{price_level}"
        
        return {
            "price": price,
            "price_level": price_level,
            "source": source,
            "original_price": default_price,
            "group_id": group_id,
            "group_name": group.get("name", "")
        }
    
    # ==================== MAIN AUTO-APPLY METHOD ====================
    
    async def process_transaction(
        self,
        items: List[Dict],
        customer_id: str = None,
        branch_id: str = None
    ) -> Dict:
        """
        Main method to process a transaction with auto-applied discounts and promotions.
        
        Returns:
            - items: List of items with applied discounts/price levels
            - discounts: List of applied discounts
            - promotions: List of applied promotions
            - free_items: List of free items from promotions
            - totals: Calculated totals
        """
        processed_items = []
        all_discounts = []
        total_discount_amount = 0
        subtotal = 0
        
        # Process each item
        for item in items:
            product_id = item.get("product_id")
            qty = item.get("quantity", 0)
            
            # Get price based on customer's level
            price_info = await self.get_price_for_customer(product_id, customer_id)
            unit_price = item.get("unit_price") or price_info.get("price", 0)
            
            item_subtotal = qty * unit_price
            
            # Calculate discounts for this item
            item_discounts = await self.calculate_item_discounts(
                {"product_id": product_id, "quantity": qty, "unit_price": unit_price},
                customer_id,
                branch_id
            )
            
            # Apply best discount (by priority)
            item_discount_amount = 0
            applied_discount = None
            
            if item_discounts:
                # Get first (highest priority) discount
                applied_discount = item_discounts[0]
                item_discount_amount = applied_discount.get("discount_amount", 0)
                
                # Check if stackable, apply more
                if applied_discount.get("stackable"):
                    for disc in item_discounts[1:]:
                        if disc.get("stackable"):
                            item_discount_amount += disc.get("discount_amount", 0)
            
            item_total = item_subtotal - item_discount_amount
            
            processed_items.append({
                **item,
                "unit_price": unit_price,
                "price_level": price_info.get("price_level", 1),
                "price_source": price_info.get("source", "default"),
                "subtotal": item_subtotal,
                "discount_amount": item_discount_amount,
                "applied_discount": applied_discount,
                "total": item_total
            })
            
            if applied_discount:
                all_discounts.append(applied_discount)
            
            total_discount_amount += item_discount_amount
            subtotal += item_subtotal
        
        # Calculate promotions
        promotions = await self.calculate_promotions(items, customer_id, branch_id)
        
        # Get free items from promotions
        free_items = []
        promo_discount_amount = 0
        
        for promo in promotions:
            benefit = promo.get("benefit", {})
            
            if benefit.get("benefit_type") == "free_item":
                free_items.extend(benefit.get("free_items", []))
            elif benefit.get("benefit_type") in ["discount", "bundle_price"]:
                promo_discount_amount += benefit.get("benefit_amount", 0)
        
        # Calculate final totals
        grand_total = subtotal - total_discount_amount - promo_discount_amount
        
        return {
            "items": processed_items,
            "free_items": free_items,
            "discounts": all_discounts,
            "promotions": promotions,
            "totals": {
                "subtotal": subtotal,
                "item_discount_total": total_discount_amount,
                "promo_discount_total": promo_discount_amount,
                "total_discount": total_discount_amount + promo_discount_amount,
                "grand_total": grand_total
            }
        }


# Global instance getter
def get_discount_promo_engine(db):
    """Get Discount & Promo Engine instance"""
    return DiscountPromoEngine(db)
