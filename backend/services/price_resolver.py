# OCB TITAN - Price Resolver Service
# Centralized price lookup for Purchase module
# SINGLE SOURCE OF TRUTH for purchase price resolution

from database import db, products
from datetime import datetime, timezone

async def resolve_purchase_price(
    product_id: str, 
    supplier_id: str = None
) -> dict:
    """
    Resolve purchase price for a product.
    Priority:
    1. Last purchase price by supplier + item
    2. Supplier item price from supplier_products
    3. Product.cost_price (purchase_price)
    4. 0 (requires manual input)
    
    Returns:
        {
            "price": float,
            "source": str,  # "last_purchase", "supplier_price", "product_cost", "manual_required"
            "supplier_id": str,
            "supplier_name": str
        }
    """
    result = {
        "price": 0,
        "source": "manual_required",
        "supplier_id": supplier_id,
        "supplier_name": ""
    }
    
    # Get product info
    product = await products.find_one({"id": product_id}, {"_id": 0})
    if not product:
        return result
    
    # Priority 1: Last purchase price by supplier + item
    if supplier_id:
        last_purchase = await db["purchase_price_history"].find_one(
            {"product_id": product_id, "supplier_id": supplier_id},
            {"_id": 0},
            sort=[("created_at", -1)]
        )
        if last_purchase and last_purchase.get("unit_cost", 0) > 0:
            result["price"] = last_purchase["unit_cost"]
            result["source"] = "last_purchase"
            result["supplier_name"] = last_purchase.get("supplier_name", "")
            return result
    
    # Priority 2: Supplier item price (supplier_products relation)
    if supplier_id:
        supplier_product = await db["supplier_products"].find_one(
            {"product_id": product_id, "supplier_id": supplier_id},
            {"_id": 0}
        )
        if supplier_product and supplier_product.get("price", 0) > 0:
            result["price"] = supplier_product["price"]
            result["source"] = "supplier_price"
            return result
    
    # Priority 3: Any last purchase for this product (from any supplier)
    any_last_purchase = await db["purchase_price_history"].find_one(
        {"product_id": product_id},
        {"_id": 0},
        sort=[("created_at", -1)]
    )
    if any_last_purchase and any_last_purchase.get("unit_cost", 0) > 0:
        result["price"] = any_last_purchase["unit_cost"]
        result["source"] = "last_purchase"
        if not supplier_id:
            result["supplier_id"] = any_last_purchase.get("supplier_id")
            result["supplier_name"] = any_last_purchase.get("supplier_name", "")
        return result
    
    # Priority 4: Product cost price
    cost_price = product.get("cost_price", 0) or product.get("purchase_price", 0)
    if cost_price > 0:
        result["price"] = cost_price
        result["source"] = "product_cost"
        return result
    
    # No price found - requires manual input
    return result


async def resolve_supplier_for_product(product_id: str) -> dict:
    """
    Resolve best supplier for a product.
    Priority:
    1. Product.supplier_id (default supplier)
    2. Last purchase supplier
    3. Any supplier in supplier_products
    4. None (requires manual selection)
    
    Returns:
        {
            "supplier_id": str or None,
            "supplier_name": str,
            "supplier_code": str,
            "source": str  # "product_default", "last_purchase", "supplier_products", "manual_required"
        }
    """
    result = {
        "supplier_id": None,
        "supplier_name": "",
        "supplier_code": "",
        "source": "manual_required"
    }
    
    # Get product info
    product = await products.find_one({"id": product_id}, {"_id": 0})
    if not product:
        return result
    
    # Priority 1: Product default supplier
    if product.get("supplier_id"):
        supplier = await db["suppliers"].find_one(
            {"id": product["supplier_id"]},
            {"_id": 0, "id": 1, "name": 1, "code": 1}
        )
        if supplier:
            result["supplier_id"] = supplier["id"]
            result["supplier_name"] = supplier.get("name", "")
            result["supplier_code"] = supplier.get("code", "")
            result["source"] = "product_default"
            return result
    
    # Priority 2: Last purchase supplier
    last_purchase = await db["purchase_price_history"].find_one(
        {"product_id": product_id},
        {"_id": 0, "supplier_id": 1, "supplier_name": 1},
        sort=[("created_at", -1)]
    )
    if last_purchase and last_purchase.get("supplier_id"):
        supplier = await db["suppliers"].find_one(
            {"id": last_purchase["supplier_id"]},
            {"_id": 0, "id": 1, "name": 1, "code": 1}
        )
        if supplier:
            result["supplier_id"] = supplier["id"]
            result["supplier_name"] = supplier.get("name", "")
            result["supplier_code"] = supplier.get("code", "")
            result["source"] = "last_purchase"
            return result
    
    # Priority 3: Last PO with this product
    last_po = await db["purchase_orders"].find_one(
        {"items.product_id": product_id, "status": {"$in": ["received", "partial", "ordered"]}},
        {"_id": 0, "supplier_id": 1, "supplier_name": 1},
        sort=[("created_at", -1)]
    )
    if last_po and last_po.get("supplier_id"):
        supplier = await db["suppliers"].find_one(
            {"id": last_po["supplier_id"]},
            {"_id": 0, "id": 1, "name": 1, "code": 1}
        )
        if supplier:
            result["supplier_id"] = supplier["id"]
            result["supplier_name"] = supplier.get("name", "")
            result["supplier_code"] = supplier.get("code", "")
            result["source"] = "last_po"
            return result
    
    # Priority 4: Any supplier in supplier_products
    supplier_product = await db["supplier_products"].find_one(
        {"product_id": product_id},
        {"_id": 0, "supplier_id": 1}
    )
    if supplier_product and supplier_product.get("supplier_id"):
        supplier = await db["suppliers"].find_one(
            {"id": supplier_product["supplier_id"]},
            {"_id": 0, "id": 1, "name": 1, "code": 1}
        )
        if supplier:
            result["supplier_id"] = supplier["id"]
            result["supplier_name"] = supplier.get("name", "")
            result["supplier_code"] = supplier.get("code", "")
            result["source"] = "supplier_products"
            return result
    
    # No supplier found
    return result


async def get_complete_product_purchase_info(product_id: str, supplier_id: str = None) -> dict:
    """
    Get complete purchase information for a product.
    Combines supplier and price resolution.
    """
    # Resolve supplier first if not provided
    supplier_info = {"supplier_id": supplier_id, "supplier_name": "", "supplier_code": "", "source": "provided"}
    
    if not supplier_id:
        supplier_info = await resolve_supplier_for_product(product_id)
        supplier_id = supplier_info.get("supplier_id")
    else:
        # Get supplier name
        supplier = await db["suppliers"].find_one({"id": supplier_id}, {"_id": 0, "name": 1, "code": 1})
        if supplier:
            supplier_info["supplier_name"] = supplier.get("name", "")
            supplier_info["supplier_code"] = supplier.get("code", "")
    
    # Resolve price
    price_info = await resolve_purchase_price(product_id, supplier_id)
    
    # Get product info
    product = await products.find_one({"id": product_id}, {"_id": 0})
    
    return {
        "product_id": product_id,
        "product_code": product.get("code", "") if product else "",
        "product_name": product.get("name", "") if product else "",
        "unit": product.get("unit", "PCS") if product else "PCS",
        "supplier_id": supplier_info.get("supplier_id"),
        "supplier_name": supplier_info.get("supplier_name", ""),
        "supplier_code": supplier_info.get("supplier_code", ""),
        "supplier_source": supplier_info.get("source", ""),
        "unit_cost": price_info.get("price", 0),
        "price_source": price_info.get("source", ""),
        "is_valid": bool(supplier_info.get("supplier_id")) and price_info.get("price", 0) > 0,
        "needs_supplier": not bool(supplier_info.get("supplier_id")),
        "needs_price": price_info.get("price", 0) <= 0
    }
