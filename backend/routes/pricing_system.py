# OCB TITAN ERP - MULTI-MODE SELLING PRICE SYSTEM
# Supports: Single Price, Quantity Pricing, Price Levels, Unit-based Pricing

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from database import db
from utils.auth import get_current_user
from routes.rbac_system import require_permission, log_activity, check_permission
from datetime import datetime, timezone
import uuid

router = APIRouter(prefix="/api/pricing", tags=["Multi-Mode Pricing System"])

# Collections
products = db["products"]
price_configs = db["price_configs"]
customer_levels = db["customer_levels"]

# ==================== PRICING MODE DEFINITIONS ====================

PRICING_MODES = {
    "single": {
        "code": "single",
        "name": "Satu Harga",
        "description": "Produk hanya memiliki satu harga jual tetap"
    },
    "quantity": {
        "code": "quantity",
        "name": "Berdasarkan Jumlah",
        "description": "Harga berubah berdasarkan jumlah pembelian (quantity pricing)"
    },
    "level": {
        "code": "level",
        "name": "Level Harga",
        "description": "Harga berbeda berdasarkan tipe customer (retail, member, reseller, distributor)"
    },
    "unit": {
        "code": "unit",
        "name": "Berdasarkan Satuan",
        "description": "Harga berbeda berdasarkan satuan (PCS, PACK, DUS)"
    }
}

# Default customer levels
DEFAULT_CUSTOMER_LEVELS = [
    {"code": "retail", "name": "Retail", "level": 1, "discount_percent": 0},
    {"code": "member", "name": "Member", "level": 2, "discount_percent": 5},
    {"code": "reseller", "name": "Reseller", "level": 3, "discount_percent": 10},
    {"code": "distributor", "name": "Distributor", "level": 4, "discount_percent": 15},
    {"code": "grosir", "name": "Grosir", "level": 5, "discount_percent": 20}
]


# ==================== PYDANTIC MODELS ====================

class QuantityPriceRule(BaseModel):
    min_qty: int
    max_qty: Optional[int] = None  # None = unlimited
    price: float


class PriceLevelConfig(BaseModel):
    retail: float = 0
    member: float = 0
    reseller: float = 0
    distributor: float = 0
    grosir: float = 0


class UnitPriceConfig(BaseModel):
    unit_id: str
    unit_name: str
    conversion: int = 1  # 1 PACK = 10 PCS -> conversion = 10
    price: float


class ProductPricingConfig(BaseModel):
    pricing_mode: str = "single"  # single, quantity, level, unit
    selling_price: float = 0  # Base price for single mode
    quantity_prices: List[QuantityPriceRule] = []
    price_levels: Optional[PriceLevelConfig] = None
    unit_prices: List[UnitPriceConfig] = []
    allow_price_selection: bool = False  # Allow cashier to select price level
    default_level: str = "retail"  # Default price level if not specified


class PriceCalculationRequest(BaseModel):
    product_id: str
    quantity: int = 1
    customer_level: str = "retail"
    unit_id: str = ""


# ==================== CUSTOMER LEVELS MANAGEMENT ====================

@router.get("/customer-levels")
async def get_customer_levels(user: dict = Depends(get_current_user)):
    """Get all customer price levels"""
    levels = await customer_levels.find({}, {"_id": 0}).sort("level", 1).to_list(100)
    
    if not levels:
        # Initialize default levels
        for lvl in DEFAULT_CUSTOMER_LEVELS:
            lvl["id"] = str(uuid.uuid4())
            lvl["created_at"] = datetime.now(timezone.utc).isoformat()
            await customer_levels.insert_one(lvl)
        levels = DEFAULT_CUSTOMER_LEVELS
    
    return {"levels": levels, "total": len(levels)}


@router.post("/customer-levels")
async def create_customer_level(
    code: str,
    name: str,
    level: int,
    discount_percent: float = 0,
    request: Request = None,
    user: dict = Depends(require_permission("master_customer", "create"))
):
    """Create new customer level"""
    existing = await customer_levels.find_one({"code": code})
    if existing:
        raise HTTPException(status_code=400, detail="Kode level sudah ada")
    
    new_level = {
        "id": str(uuid.uuid4()),
        "code": code,
        "name": name,
        "level": level,
        "discount_percent": discount_percent,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await customer_levels.insert_one(new_level)
    
    return {"id": new_level["id"], "message": "Customer level berhasil dibuat"}


# ==================== PRICING CONFIGURATION ====================

@router.get("/modes")
async def get_pricing_modes(user: dict = Depends(get_current_user)):
    """Get all available pricing modes"""
    return {
        "modes": list(PRICING_MODES.values()),
        "total": len(PRICING_MODES)
    }


@router.get("/product/{product_id}")
async def get_product_pricing(product_id: str, user: dict = Depends(get_current_user)):
    """Get pricing configuration for a product"""
    product = await products.find_one({"id": product_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Produk tidak ditemukan")
    
    # Get pricing config
    config = await price_configs.find_one({"product_id": product_id}, {"_id": 0})
    
    if not config:
        # Return default config (single price mode)
        config = {
            "product_id": product_id,
            "pricing_mode": "single",
            "selling_price": product.get("selling_price", 0),
            "quantity_prices": [],
            "price_levels": None,
            "unit_prices": [],
            "allow_price_selection": False,
            "default_level": "retail"
        }
    
    return {
        "product": {
            "id": product.get("id"),
            "code": product.get("code"),
            "name": product.get("name"),
            "cost_price": product.get("cost_price", 0),
            "base_selling_price": product.get("selling_price", 0)
        },
        "pricing": config,
        "modes": PRICING_MODES
    }


@router.put("/product/{product_id}")
async def update_product_pricing(
    product_id: str,
    config: ProductPricingConfig,
    request: Request,
    user: dict = Depends(require_permission("master_item", "edit"))
):
    """Update pricing configuration for a product"""
    product = await products.find_one({"id": product_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Produk tidak ditemukan")
    
    # Validate pricing mode
    if config.pricing_mode not in PRICING_MODES:
        raise HTTPException(status_code=400, detail="Mode harga tidak valid")
    
    # Validate quantity prices if mode is quantity
    if config.pricing_mode == "quantity" and not config.quantity_prices:
        raise HTTPException(status_code=400, detail="Quantity pricing memerlukan minimal 1 rule")
    
    # Validate unit prices if mode is unit
    if config.pricing_mode == "unit" and not config.unit_prices:
        raise HTTPException(status_code=400, detail="Unit pricing memerlukan minimal 1 unit")
    
    # Prepare config data
    config_data = {
        "product_id": product_id,
        "pricing_mode": config.pricing_mode,
        "selling_price": config.selling_price,
        "quantity_prices": [qp.model_dump() for qp in config.quantity_prices],
        "price_levels": config.price_levels.model_dump() if config.price_levels else None,
        "unit_prices": [up.model_dump() for up in config.unit_prices],
        "allow_price_selection": config.allow_price_selection,
        "default_level": config.default_level,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Upsert config
    existing = await price_configs.find_one({"product_id": product_id})
    if existing:
        await price_configs.update_one(
            {"product_id": product_id},
            {"$set": config_data}
        )
    else:
        config_data["id"] = str(uuid.uuid4())
        config_data["created_at"] = datetime.now(timezone.utc).isoformat()
        await price_configs.insert_one(config_data)
    
    # Also update base selling_price in products collection
    await products.update_one(
        {"id": product_id},
        {"$set": {
            "selling_price": config.selling_price,
            "pricing_mode": config.pricing_mode,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Log activity
    user_id = user.get("user_id") or user.get("id")
    await log_activity(
        db, user_id, user.get("name", ""),
        "edit", "master_item",
        f"Update pricing config: {product.get('name')} -> mode {config.pricing_mode}",
        request.client.host if request.client else ""
    )
    
    return {"message": "Konfigurasi harga berhasil diupdate", "pricing_mode": config.pricing_mode}


# ==================== PRICE CALCULATION ENGINE ====================

async def calculate_price(
    product_id: str,
    quantity: int = 1,
    customer_level: str = "retail",
    unit_id: str = "",
    allow_override: bool = False
) -> Dict[str, Any]:
    """
    CORE PRICE CALCULATION ENGINE
    Returns the correct price based on product's pricing mode
    """
    # Get product
    product = await products.find_one({"id": product_id}, {"_id": 0})
    if not product:
        return {"error": "Produk tidak ditemukan", "price": 0}
    
    # Get pricing config
    config = await price_configs.find_one({"product_id": product_id}, {"_id": 0})
    
    # Default to single price mode if no config
    if not config:
        return {
            "price": product.get("selling_price", 0),
            "mode": "single",
            "rule_applied": "default",
            "original_price": product.get("selling_price", 0),
            "discount": 0
        }
    
    pricing_mode = config.get("pricing_mode", "single")
    base_price = config.get("selling_price", product.get("selling_price", 0))
    
    result = {
        "mode": pricing_mode,
        "original_price": base_price,
        "price": base_price,
        "discount": 0,
        "rule_applied": "default",
        "allow_selection": config.get("allow_price_selection", False),
        "available_levels": []
    }
    
    # ===== MODE: SINGLE PRICE =====
    if pricing_mode == "single":
        result["price"] = base_price
        result["rule_applied"] = "single_price"
    
    # ===== MODE: QUANTITY PRICING =====
    elif pricing_mode == "quantity":
        quantity_prices = config.get("quantity_prices", [])
        applied_price = base_price
        rule_name = "default"
        
        for rule in sorted(quantity_prices, key=lambda x: x.get("min_qty", 0)):
            min_qty = rule.get("min_qty", 1)
            max_qty = rule.get("max_qty")
            
            if quantity >= min_qty:
                if max_qty is None or quantity <= max_qty:
                    applied_price = rule.get("price", base_price)
                    if max_qty:
                        rule_name = f"qty_{min_qty}-{max_qty}"
                    else:
                        rule_name = f"qty_{min_qty}+"
        
        result["price"] = applied_price
        result["rule_applied"] = rule_name
        result["quantity_tiers"] = quantity_prices
    
    # ===== MODE: LEVEL PRICING =====
    elif pricing_mode == "level":
        price_levels = config.get("price_levels", {})
        
        # Get price for customer level
        level_price = price_levels.get(customer_level, base_price)
        if level_price == 0:
            level_price = price_levels.get("retail", base_price)
        
        result["price"] = level_price
        result["rule_applied"] = f"level_{customer_level}"
        result["available_levels"] = [
            {"code": k, "price": v} for k, v in price_levels.items() if v > 0
        ]
    
    # ===== MODE: UNIT PRICING =====
    elif pricing_mode == "unit":
        unit_prices = config.get("unit_prices", [])
        
        if unit_id:
            # Find specific unit price
            for up in unit_prices:
                if up.get("unit_id") == unit_id:
                    result["price"] = up.get("price", base_price)
                    result["rule_applied"] = f"unit_{up.get('unit_name', unit_id)}"
                    result["conversion"] = up.get("conversion", 1)
                    break
        else:
            # Use first unit (base unit)
            if unit_prices:
                result["price"] = unit_prices[0].get("price", base_price)
                result["rule_applied"] = f"unit_{unit_prices[0].get('unit_name', 'base')}"
        
        result["available_units"] = unit_prices
    
    # Calculate discount from base
    if result["price"] < result["original_price"]:
        result["discount"] = result["original_price"] - result["price"]
        result["discount_percent"] = round((result["discount"] / result["original_price"]) * 100, 2)
    
    return result


@router.post("/calculate")
async def calculate_product_price(
    data: PriceCalculationRequest,
    user: dict = Depends(get_current_user)
):
    """Calculate price for a product based on quantity, customer level, or unit"""
    result = await calculate_price(
        product_id=data.product_id,
        quantity=data.quantity,
        customer_level=data.customer_level,
        unit_id=data.unit_id
    )
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


@router.post("/calculate-batch")
async def calculate_batch_prices(
    items: List[PriceCalculationRequest],
    user: dict = Depends(get_current_user)
):
    """Calculate prices for multiple products at once"""
    results = []
    for item in items:
        result = await calculate_price(
            product_id=item.product_id,
            quantity=item.quantity,
            customer_level=item.customer_level,
            unit_id=item.unit_id
        )
        result["product_id"] = item.product_id
        results.append(result)
    
    return {"prices": results, "count": len(results)}


# ==================== POS PRICE SELECTION ====================

@router.post("/pos/select-price")
async def pos_select_price(
    product_id: str,
    selected_level: str,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """
    POS: Select price level for a product
    Requires override_price permission if not using default level
    """
    # Get product pricing config
    config = await price_configs.find_one({"product_id": product_id}, {"_id": 0})
    product = await products.find_one({"id": product_id}, {"_id": 0})
    
    if not product:
        raise HTTPException(status_code=404, detail="Produk tidak ditemukan")
    
    # Check if price selection is allowed
    if config and not config.get("allow_price_selection", False):
        raise HTTPException(status_code=400, detail="Produk ini tidak mengizinkan pemilihan harga")
    
    # Check if user is selecting non-default level
    default_level = config.get("default_level", "retail") if config else "retail"
    
    if selected_level != default_level:
        # Check override_price permission
        user_id = user.get("user_id") or user.get("id")
        has_override = await check_permission(user_id, "sales", "override_price")
        
        if not has_override:
            # Log failed attempt
            await log_activity(
                db, user_id, user.get("name", ""),
                "access_denied", "sales",
                f"Mencoba mengubah harga {product.get('name')} ke level {selected_level}",
                request.client.host if request.client else "",
                severity="warning"
            )
            raise HTTPException(
                status_code=403,
                detail="ANDA TIDAK MEMILIKI IZIN MENGUBAH HARGA"
            )
    
    # Calculate price for selected level
    result = await calculate_price(
        product_id=product_id,
        customer_level=selected_level
    )
    
    # Log the price selection
    user_id = user.get("user_id") or user.get("id")
    await log_activity(
        db, user_id, user.get("name", ""),
        "edit", "sales",
        f"Memilih harga {selected_level} untuk {product.get('name')}: Rp {result['price']:,.0f}",
        request.client.host if request.client else ""
    )
    
    return {
        "product_id": product_id,
        "product_name": product.get("name"),
        "selected_level": selected_level,
        "price": result["price"],
        "original_price": result["original_price"],
        "discount": result.get("discount", 0)
    }


# ==================== BULK PRICING SETUP ====================

@router.post("/bulk-setup")
async def bulk_pricing_setup(
    product_ids: List[str],
    pricing_mode: str,
    config_template: Dict[str, Any],
    request: Request,
    user: dict = Depends(require_permission("master_item", "edit"))
):
    """Apply pricing configuration to multiple products"""
    if pricing_mode not in PRICING_MODES:
        raise HTTPException(status_code=400, detail="Mode harga tidak valid")
    
    updated = 0
    for product_id in product_ids:
        product = await products.find_one({"id": product_id})
        if not product:
            continue
        
        config_data = {
            "product_id": product_id,
            "pricing_mode": pricing_mode,
            **config_template,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        existing = await price_configs.find_one({"product_id": product_id})
        if existing:
            await price_configs.update_one(
                {"product_id": product_id},
                {"$set": config_data}
            )
        else:
            config_data["id"] = str(uuid.uuid4())
            config_data["created_at"] = datetime.now(timezone.utc).isoformat()
            await price_configs.insert_one(config_data)
        
        # Update product
        await products.update_one(
            {"id": product_id},
            {"$set": {"pricing_mode": pricing_mode, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        updated += 1
    
    user_id = user.get("user_id") or user.get("id")
    await log_activity(
        db, user_id, user.get("name", ""),
        "edit", "master_item",
        f"Bulk pricing setup: {updated} produk -> mode {pricing_mode}",
        request.client.host if request.client else ""
    )
    
    return {"message": f"Berhasil update {updated} produk", "pricing_mode": pricing_mode}


# ==================== PRICE HISTORY ====================

@router.get("/history/{product_id}")
async def get_price_history(
    product_id: str,
    limit: int = 20,
    user: dict = Depends(get_current_user)
):
    """Get price change history for a product"""
    # Get from audit logs
    logs = await db["audit_logs"].find(
        {
            "module": "master_item",
            "description": {"$regex": product_id, "$options": "i"}
        },
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    return {"history": logs, "product_id": product_id}


# ==================== INITIALIZATION ====================

@router.post("/init")
async def initialize_pricing_system(user: dict = Depends(get_current_user)):
    """Initialize pricing system with default customer levels"""
    # Create default customer levels
    levels_created = 0
    for lvl in DEFAULT_CUSTOMER_LEVELS:
        existing = await customer_levels.find_one({"code": lvl["code"]})
        if not existing:
            lvl["id"] = str(uuid.uuid4())
            lvl["created_at"] = datetime.now(timezone.utc).isoformat()
            await customer_levels.insert_one(lvl)
            levels_created += 1
    
    # Create indexes
    await price_configs.create_index("product_id", unique=True)
    await customer_levels.create_index("code", unique=True)
    
    return {
        "message": "Pricing system initialized",
        "customer_levels_created": levels_created,
        "pricing_modes": list(PRICING_MODES.keys())
    }
