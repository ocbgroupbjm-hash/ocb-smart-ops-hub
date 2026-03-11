"""
OCB TITAN ERP - PHASE 3 OPERATIONAL CONTROL SYSTEM
Module 3: STOCK REORDER ENGINE
Following OCB TITAN AI MASTER LAW - NON-DESTRUCTIVE Development

Reference: iPOS Ultimate tbl_item.stokmin concept

Features:
1. Min/Max Stock Settings per Product per Branch/Warehouse
2. Sales Velocity Calculation (rata-rata penjualan harian)
3. Automatic Reorder Recommendations
4. Lead Time Consideration
5. Safety Stock Calculation
6. Purchase Suggestion Generation
7. Multi-Warehouse Support Ready
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
from database import get_db as get_database, products
from routes.auth import get_current_user
from routes.rbac_middleware import require_permission
import uuid
import math

router = APIRouter(prefix="/api/stock-reorder", tags=["Stock Reorder Engine"])

# ==================== REORDER POLICY DEFAULTS ====================

DEFAULT_REORDER_POLICY = {
    "safety_stock_days": 7,  # Hari buffer safety stock
    "lead_time_days": 3,  # Default lead time supplier
    "velocity_days": 30,  # Periode hitung sales velocity
    "auto_generate_po": False,  # Auto-generate PO draft
    "min_reorder_qty": 1,  # Minimum qty reorder
    "rounding_multiple": 1  # Pembulatan qty (misal ke kelipatan 10)
}

# ==================== PYDANTIC MODELS ====================

class StockSettingUpdate(BaseModel):
    product_id: str
    branch_id: Optional[str] = None  # null = semua cabang
    warehouse_id: Optional[str] = None  # null = warehouse utama
    minimum_stock: float = Field(ge=0)
    maximum_stock: float = Field(ge=0)
    reorder_point: Optional[float] = None  # auto-calculate if not set
    safety_stock: Optional[float] = None
    lead_time_days: Optional[int] = None
    preferred_supplier_id: Optional[str] = None

class BulkStockSettingUpdate(BaseModel):
    items: List[StockSettingUpdate]

class ReorderSuggestionFilter(BaseModel):
    branch_id: Optional[str] = None
    warehouse_id: Optional[str] = None
    category_id: Optional[str] = None
    supplier_id: Optional[str] = None
    urgency: Optional[str] = None  # critical, high, medium, low

class ReorderPolicyUpdate(BaseModel):
    safety_stock_days: Optional[int] = None
    lead_time_days: Optional[int] = None
    velocity_days: Optional[int] = None
    auto_generate_po: Optional[bool] = None
    min_reorder_qty: Optional[int] = None
    rounding_multiple: Optional[int] = None

# ==================== HELPER FUNCTIONS ====================

async def get_product_stock_level(db, product_id: str, branch_id: str = None, warehouse_id: str = None) -> Dict[str, Any]:
    """Get current stock level from stock_movements (SSOT)"""
    
    query = {"product_id": product_id}
    if branch_id:
        query["branch_id"] = branch_id
    if warehouse_id:
        query["warehouse_id"] = warehouse_id
    
    pipeline = [
        {"$match": query},
        {"$group": {
            "_id": {
                "product_id": "$product_id",
                "branch_id": {"$ifNull": ["$branch_id", "main"]},
                "warehouse_id": {"$ifNull": ["$warehouse_id", "main"]}
            },
            "total_in": {"$sum": {"$cond": [{"$eq": ["$movement_type", "in"]}, "$quantity", 0]}},
            "total_out": {"$sum": {"$cond": [{"$eq": ["$movement_type", "out"]}, "$quantity", 0]}}
        }}
    ]
    
    result = await db.stock_movements.aggregate(pipeline).to_list(100)
    
    stock_data = {}
    for item in result:
        branch = item['_id'].get('branch_id', 'main')
        warehouse = item['_id'].get('warehouse_id', 'main')
        key = f"{branch}_{warehouse}"
        stock_data[key] = {
            "branch_id": branch,
            "warehouse_id": warehouse,
            "current_stock": item['total_in'] - item['total_out']
        }
    
    return stock_data

async def calculate_sales_velocity(db, product_id: str, branch_id: str = None, days: int = 30) -> float:
    """Calculate average daily sales for a product"""
    
    start_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    
    query = {
        "product_id": product_id,
        "movement_type": "out",
        "reference_type": {"$in": ["sales", "pos"]},
        "created_at": {"$gte": start_date}
    }
    if branch_id:
        query["branch_id"] = branch_id
    
    pipeline = [
        {"$match": query},
        {"$group": {
            "_id": None,
            "total_sold": {"$sum": "$quantity"}
        }}
    ]
    
    result = await db.stock_movements.aggregate(pipeline).to_list(1)
    
    if not result:
        return 0
    
    total_sold = result[0].get("total_sold", 0)
    return round(total_sold / days, 2)

async def get_product_stock_settings(db, product_id: str, branch_id: str = None) -> Dict[str, Any]:
    """Get stock settings for a product"""
    
    # First check product-specific settings
    query = {"product_id": product_id}
    if branch_id:
        query["branch_id"] = branch_id
    
    settings = await db.stock_settings.find_one(query, {"_id": 0})
    
    if not settings:
        # Check if product has default min/max in products collection
        product = await products.find_one({"id": product_id}, {"_id": 0, "minimum_stock": 1, "maximum_stock": 1})
        if product:
            settings = {
                "product_id": product_id,
                "branch_id": branch_id,
                "minimum_stock": product.get("minimum_stock", 0),
                "maximum_stock": product.get("maximum_stock", 0),
                "reorder_point": None,
                "safety_stock": None,
                "lead_time_days": None
            }
    
    return settings

async def calculate_reorder_suggestion(db, product_id: str, branch_id: str = None) -> Dict[str, Any]:
    """Calculate reorder suggestion for a product"""
    
    # Get product info
    product = await products.find_one({"id": product_id}, {"_id": 0})
    if not product:
        return None
    
    # Get stock settings
    settings = await get_product_stock_settings(db, product_id, branch_id)
    
    # Get current stock
    stock_data = await get_product_stock_level(db, product_id, branch_id)
    
    # Get sales velocity
    velocity_days = DEFAULT_REORDER_POLICY["velocity_days"]
    sales_velocity = await calculate_sales_velocity(db, product_id, branch_id, velocity_days)
    
    # Get policy
    policy = await db.settings.find_one({"type": "reorder_policy"}, {"_id": 0})
    policy = policy.get("config", DEFAULT_REORDER_POLICY) if policy else DEFAULT_REORDER_POLICY
    
    # Calculate totals
    total_stock = sum(s["current_stock"] for s in stock_data.values()) if stock_data else 0
    
    # Get settings values
    minimum_stock = settings.get("minimum_stock", 0) if settings else 0
    maximum_stock = settings.get("maximum_stock", 0) if settings else 0
    lead_time = (settings.get("lead_time_days") if settings else None) or policy.get("lead_time_days", 3)
    safety_days = policy.get("safety_stock_days", 7)
    
    # Calculate reorder point if not set
    reorder_point = settings.get("reorder_point") if settings else None
    if reorder_point is None:
        # Reorder Point = (Sales Velocity * Lead Time) + Safety Stock
        safety_stock = sales_velocity * safety_days
        reorder_point = (sales_velocity * lead_time) + safety_stock
    
    # Calculate suggested quantity
    suggested_qty = 0
    if total_stock <= reorder_point and maximum_stock > 0:
        suggested_qty = maximum_stock - total_stock
    elif total_stock <= minimum_stock and minimum_stock > 0:
        # If no max set, order up to 2x minimum
        suggested_qty = (minimum_stock * 2) - total_stock
    
    # Round to multiple
    rounding = policy.get("rounding_multiple", 1)
    if rounding > 1 and suggested_qty > 0:
        suggested_qty = math.ceil(suggested_qty / rounding) * rounding
    
    # Determine urgency
    urgency = "none"
    if total_stock <= 0:
        urgency = "critical"
    elif minimum_stock > 0 and total_stock <= minimum_stock * 0.5:
        urgency = "critical"
    elif minimum_stock > 0 and total_stock <= minimum_stock:
        urgency = "high"
    elif reorder_point > 0 and total_stock <= reorder_point:
        urgency = "medium"
    elif minimum_stock > 0 and total_stock <= minimum_stock * 1.5:
        urgency = "low"
    
    # Days of stock remaining
    days_remaining = round(total_stock / sales_velocity, 1) if sales_velocity > 0 else 999
    
    return {
        "product_id": product_id,
        "product_code": product.get("code", ""),
        "product_name": product.get("name", ""),
        "category": product.get("category", ""),
        "unit": product.get("unit", "pcs"),
        "current_stock": total_stock,
        "minimum_stock": minimum_stock,
        "maximum_stock": maximum_stock,
        "reorder_point": round(reorder_point, 2),
        "safety_stock": round(sales_velocity * safety_days, 2),
        "sales_velocity": sales_velocity,
        "lead_time_days": lead_time,
        "days_remaining": days_remaining,
        "suggested_qty": max(0, round(suggested_qty, 0)),
        "urgency": urgency,
        "needs_reorder": suggested_qty > 0,
        "supplier_id": settings.get("preferred_supplier_id") if settings else product.get("supplier_id"),
        "supplier_name": product.get("supplier_name", "")
    }

# ==================== API ENDPOINTS ====================

@router.get("/policy")
async def get_reorder_policy(user: dict = Depends(get_current_user)):
    """Get reorder policy configuration"""
    db = get_database()
    
    policy = await db.settings.find_one({"type": "reorder_policy"}, {"_id": 0})
    
    if not policy:
        return DEFAULT_REORDER_POLICY
    
    return policy.get("config", DEFAULT_REORDER_POLICY)

@router.put("/policy")
async def update_reorder_policy(
    updates: ReorderPolicyUpdate,
    user: dict = Depends(require_permission("stock_reorder", "edit"))
):
    """Update reorder policy"""
    db = get_database()
    
    # Get current policy
    current = await db.settings.find_one({"type": "reorder_policy"}, {"_id": 0})
    config = current.get("config", DEFAULT_REORDER_POLICY) if current else DEFAULT_REORDER_POLICY.copy()
    
    # Update with new values
    for key, value in updates.dict(exclude_none=True).items():
        config[key] = value
    
    await db.settings.update_one(
        {"type": "reorder_policy"},
        {"$set": {
            "config": config,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "updated_by": user.get("user_id")
        }},
        upsert=True
    )
    
    return {"success": True, "message": "Reorder policy updated", "config": config}

@router.get("/settings/{product_id}")
async def get_stock_settings(
    product_id: str,
    branch_id: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Get stock settings for a product"""
    db = get_database()
    
    settings = await get_product_stock_settings(db, product_id, branch_id)
    
    # Get current stock and velocity for context
    stock_data = await get_product_stock_level(db, product_id, branch_id)
    velocity = await calculate_sales_velocity(db, product_id, branch_id)
    
    total_stock = sum(s["current_stock"] for s in stock_data.values()) if stock_data else 0
    
    return {
        "settings": settings or {"product_id": product_id, "minimum_stock": 0, "maximum_stock": 0},
        "current_stock": total_stock,
        "sales_velocity": velocity,
        "stock_by_location": list(stock_data.values()) if stock_data else []
    }

@router.put("/settings")
async def update_stock_settings(
    data: StockSettingUpdate,
    user: dict = Depends(require_permission("stock_reorder", "edit"))
):
    """Update stock settings for a product"""
    db = get_database()
    
    # Validate product exists
    product = await products.find_one({"id": data.product_id}, {"_id": 0, "name": 1})
    if not product:
        raise HTTPException(status_code=404, detail="Produk tidak ditemukan")
    
    # Validate max >= min
    if data.maximum_stock > 0 and data.maximum_stock < data.minimum_stock:
        raise HTTPException(status_code=400, detail="Maximum stock harus >= minimum stock")
    
    query = {"product_id": data.product_id}
    if data.branch_id:
        query["branch_id"] = data.branch_id
    if data.warehouse_id:
        query["warehouse_id"] = data.warehouse_id
    
    setting_data = {
        **query,
        "minimum_stock": data.minimum_stock,
        "maximum_stock": data.maximum_stock,
        "reorder_point": data.reorder_point,
        "safety_stock": data.safety_stock,
        "lead_time_days": data.lead_time_days,
        "preferred_supplier_id": data.preferred_supplier_id,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "updated_by": user.get("user_id")
    }
    
    await db.stock_settings.update_one(
        query,
        {"$set": setting_data},
        upsert=True
    )
    
    # Also update in products collection for easy access
    await products.update_one(
        {"id": data.product_id},
        {"$set": {
            "minimum_stock": data.minimum_stock,
            "maximum_stock": data.maximum_stock
        }}
    )
    
    # Audit log
    await db.audit_logs.insert_one({
        "id": str(uuid.uuid4()),
        "action": "stock_settings_update",
        "module": "stock_reorder",
        "target_id": data.product_id,
        "target_name": product.get("name"),
        "description": f"Update stock settings: Min={data.minimum_stock}, Max={data.maximum_stock}",
        "user_id": user.get("user_id"),
        "user_name": user.get("name"),
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    return {"success": True, "message": "Stock settings updated"}

@router.put("/settings/bulk")
async def bulk_update_stock_settings(
    data: BulkStockSettingUpdate,
    user: dict = Depends(require_permission("stock_reorder", "edit"))
):
    """Bulk update stock settings"""
    db = get_database()
    
    updated = 0
    errors = []
    
    for item in data.items:
        try:
            await update_stock_settings(item, user)
            updated += 1
        except Exception as e:
            errors.append({"product_id": item.product_id, "error": str(e)})
    
    return {
        "success": True,
        "updated": updated,
        "errors": errors
    }

@router.get("/suggestions")
async def get_reorder_suggestions(
    branch_id: Optional[str] = None,
    category: Optional[str] = None,
    urgency: Optional[str] = None,
    limit: int = 100,
    user: dict = Depends(get_current_user)
):
    """Get all products that need reorder"""
    db = get_database()
    
    # Get all products with min stock > 0
    query = {"is_active": True}
    if category:
        query["category"] = category
    
    all_products = await products.find(query, {"_id": 0, "id": 1}).to_list(500)
    
    suggestions = []
    for product in all_products:
        suggestion = await calculate_reorder_suggestion(db, product["id"], branch_id)
        if suggestion and suggestion["needs_reorder"]:
            if not urgency or suggestion["urgency"] == urgency:
                suggestions.append(suggestion)
    
    # Sort by urgency
    urgency_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "none": 4}
    suggestions.sort(key=lambda x: (urgency_order.get(x["urgency"], 4), -x["suggested_qty"]))
    
    # Apply limit
    suggestions = suggestions[:limit]
    
    # Summary stats
    summary = {
        "total_items": len(suggestions),
        "critical": sum(1 for s in suggestions if s["urgency"] == "critical"),
        "high": sum(1 for s in suggestions if s["urgency"] == "high"),
        "medium": sum(1 for s in suggestions if s["urgency"] == "medium"),
        "low": sum(1 for s in suggestions if s["urgency"] == "low"),
        "total_value": 0  # Would need cost price to calculate
    }
    
    return {
        "items": suggestions,
        "summary": summary
    }

@router.get("/suggestion/{product_id}")
async def get_single_product_suggestion(
    product_id: str,
    branch_id: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Get reorder suggestion for a single product"""
    db = get_database()
    
    suggestion = await calculate_reorder_suggestion(db, product_id, branch_id)
    
    if not suggestion:
        raise HTTPException(status_code=404, detail="Produk tidak ditemukan")
    
    return suggestion

@router.get("/velocity/{product_id}")
async def get_product_velocity(
    product_id: str,
    branch_id: Optional[str] = None,
    days: int = 30,
    user: dict = Depends(get_current_user)
):
    """Get sales velocity details for a product"""
    db = get_database()
    
    # Get daily sales for the period
    start_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    
    query = {
        "product_id": product_id,
        "movement_type": "out",
        "reference_type": {"$in": ["sales", "pos"]},
        "created_at": {"$gte": start_date}
    }
    if branch_id:
        query["branch_id"] = branch_id
    
    # Group by date
    pipeline = [
        {"$match": query},
        {"$addFields": {
            "date": {"$substr": ["$created_at", 0, 10]}
        }},
        {"$group": {
            "_id": "$date",
            "quantity": {"$sum": "$quantity"},
            "transactions": {"$sum": 1}
        }},
        {"$sort": {"_id": -1}}
    ]
    
    daily_data = await db.stock_movements.aggregate(pipeline).to_list(days)
    
    total_qty = sum(d["quantity"] for d in daily_data)
    total_transactions = sum(d["transactions"] for d in daily_data)
    avg_velocity = round(total_qty / days, 2) if days > 0 else 0
    
    # Get product info
    product = await products.find_one({"id": product_id}, {"_id": 0, "name": 1, "code": 1})
    
    return {
        "product_id": product_id,
        "product_name": product.get("name", "") if product else "",
        "product_code": product.get("code", "") if product else "",
        "period_days": days,
        "total_sold": total_qty,
        "total_transactions": total_transactions,
        "average_daily_velocity": avg_velocity,
        "daily_breakdown": daily_data
    }

@router.post("/generate-po-draft")
async def generate_purchase_order_draft(
    product_ids: Optional[List[str]] = None,
    branch_id: Optional[str] = None,
    urgency_filter: Optional[str] = None,  # critical, high
    user: dict = Depends(require_permission("purchase", "create"))
):
    """Generate draft purchase orders from reorder suggestions"""
    db = get_database()
    
    # Get suggestions
    if product_ids:
        suggestions = []
        for pid in product_ids:
            s = await calculate_reorder_suggestion(db, pid, branch_id)
            if s and s["needs_reorder"]:
                suggestions.append(s)
    else:
        result = await get_reorder_suggestions(branch_id, None, urgency_filter, 100, user)
        suggestions = result["items"]
    
    if not suggestions:
        return {"success": False, "message": "Tidak ada item yang perlu direorder"}
    
    # Group by supplier
    by_supplier = {}
    for s in suggestions:
        supplier_id = s.get("supplier_id") or "unknown"
        if supplier_id not in by_supplier:
            by_supplier[supplier_id] = {
                "supplier_id": supplier_id,
                "supplier_name": s.get("supplier_name", "Unknown"),
                "items": []
            }
        by_supplier[supplier_id]["items"].append({
            "product_id": s["product_id"],
            "product_code": s["product_code"],
            "product_name": s["product_name"],
            "unit": s["unit"],
            "quantity": s["suggested_qty"],
            "urgency": s["urgency"],
            "current_stock": s["current_stock"],
            "minimum_stock": s["minimum_stock"]
        })
    
    # Create draft POs (tidak disimpan, hanya preview)
    drafts = []
    for supplier_id, data in by_supplier.items():
        draft = {
            "draft_id": str(uuid.uuid4()),
            "supplier_id": supplier_id,
            "supplier_name": data["supplier_name"],
            "branch_id": branch_id or user.get("branch_id"),
            "items": data["items"],
            "total_items": len(data["items"]),
            "total_qty": sum(i["quantity"] for i in data["items"]),
            "status": "draft",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": user.get("name")
        }
        drafts.append(draft)
    
    return {
        "success": True,
        "drafts": drafts,
        "total_drafts": len(drafts),
        "total_items": sum(d["total_items"] for d in drafts),
        "message": f"Generated {len(drafts)} draft PO dari {len(suggestions)} item"
    }

# ==================== DASHBOARD & REPORTS ====================

@router.get("/dashboard")
async def get_reorder_dashboard(
    branch_id: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Get stock reorder dashboard summary"""
    db = get_database()
    
    # Get all suggestions
    result = await get_reorder_suggestions(branch_id, None, None, 500, user)
    suggestions = result["items"]
    
    # Count products with stock settings
    with_settings = await db.stock_settings.count_documents({})
    
    # Products below minimum
    below_min = [s for s in suggestions if s["urgency"] in ["critical", "high"]]
    
    # Products at reorder point
    at_reorder = [s for s in suggestions if s["urgency"] == "medium"]
    
    # Out of stock (current_stock <= 0)
    out_of_stock = [s for s in suggestions if s["current_stock"] <= 0]
    
    # Top 5 critical items
    critical_items = [s for s in suggestions if s["urgency"] == "critical"][:5]
    
    return {
        "summary": {
            "total_products": await products.count_documents({"is_active": True}),
            "with_stock_settings": with_settings,
            "needs_reorder": len(suggestions),
            "critical_count": len([s for s in suggestions if s["urgency"] == "critical"]),
            "high_count": len([s for s in suggestions if s["urgency"] == "high"]),
            "medium_count": len([s for s in suggestions if s["urgency"] == "medium"]),
            "out_of_stock": len(out_of_stock)
        },
        "critical_items": critical_items,
        "by_urgency": result["summary"]
    }

@router.get("/low-stock-alerts")
async def get_low_stock_alerts(
    branch_id: Optional[str] = None,
    limit: int = 20,
    user: dict = Depends(get_current_user)
):
    """Get low stock alerts for dashboard notifications"""
    db = get_database()
    
    result = await get_reorder_suggestions(branch_id, None, None, limit, user)
    
    alerts = []
    for s in result["items"]:
        if s["urgency"] in ["critical", "high"]:
            alerts.append({
                "product_id": s["product_id"],
                "product_name": s["product_name"],
                "product_code": s["product_code"],
                "current_stock": s["current_stock"],
                "minimum_stock": s["minimum_stock"],
                "urgency": s["urgency"],
                "days_remaining": s["days_remaining"],
                "suggested_qty": s["suggested_qty"],
                "message": f"Stok {s['product_name']} {'HABIS' if s['current_stock'] <= 0 else 'rendah'} - Sisa {s['current_stock']} {s['unit']}"
            })
    
    return {
        "alerts": alerts[:limit],
        "total": len(alerts)
    }
