# OCB GROUP SUPER AI - Stock Monitoring Routes
# Monitor stock across 40 branches with alerts

from fastapi import APIRouter, HTTPException
from typing import Optional, List
from datetime import datetime, timezone
import uuid

from database import get_db

router = APIRouter(prefix="/api/stock-monitor", tags=["Stock Monitoring"])

def gen_id() -> str:
    return str(uuid.uuid4())

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

# ==================== STOCK MONITORING ====================

@router.get("/overview")
async def get_stock_overview():
    """Get stock overview for all branches"""
    db = get_db()
    
    # Get all branches
    branches = await db['branches'].find(
        {"is_active": True},
        {"_id": 0, "id": 1, "name": 1, "code": 1, "city": 1}
    ).to_list(None)
    
    # Get all products
    products = await db['products'].find(
        {"is_active": True, "track_stock": True},
        {"_id": 0, "id": 1, "name": 1, "code": 1, "min_stock": 1, "selling_price": 1}
    ).to_list(None)
    
    product_map = {p["id"]: p for p in products}
    
    # Get all stock
    stocks = await db['product_stocks'].find({}, {"_id": 0}).to_list(None)
    
    # Calculate per branch
    branch_stock = {}
    total_stock_value = 0
    low_stock_items = []
    out_of_stock_items = []
    
    for branch in branches:
        branch_id = branch["id"]
        branch_stock[branch_id] = {
            "branch_id": branch_id,
            "branch_name": branch["name"],
            "branch_code": branch.get("code", ""),
            "city": branch.get("city", ""),
            "total_items": 0,
            "total_value": 0,
            "low_stock_count": 0,
            "out_of_stock_count": 0
        }
    
    for stock in stocks:
        branch_id = stock.get("branch_id")
        product_id = stock.get("product_id")
        qty = stock.get("quantity", 0)
        
        if branch_id in branch_stock and product_id in product_map:
            product = product_map[product_id]
            value = qty * product.get("selling_price", 0)
            min_stock = product.get("min_stock", 5)
            
            branch_stock[branch_id]["total_items"] += qty
            branch_stock[branch_id]["total_value"] += value
            total_stock_value += value
            
            if qty == 0:
                branch_stock[branch_id]["out_of_stock_count"] += 1
                out_of_stock_items.append({
                    "branch_id": branch_id,
                    "branch_name": branch_stock[branch_id]["branch_name"],
                    "product_id": product_id,
                    "product_name": product["name"],
                    "product_code": product.get("code", ""),
                    "current_stock": qty,
                    "min_stock": min_stock
                })
            elif qty <= min_stock:
                branch_stock[branch_id]["low_stock_count"] += 1
                low_stock_items.append({
                    "branch_id": branch_id,
                    "branch_name": branch_stock[branch_id]["branch_name"],
                    "product_id": product_id,
                    "product_name": product["name"],
                    "product_code": product.get("code", ""),
                    "current_stock": qty,
                    "min_stock": min_stock
                })
    
    return {
        "total_branches": len(branches),
        "total_products": len(products),
        "total_stock_value": total_stock_value,
        "low_stock_count": len(low_stock_items),
        "out_of_stock_count": len(out_of_stock_items),
        "branches": list(branch_stock.values()),
        "low_stock_items": low_stock_items[:20],
        "out_of_stock_items": out_of_stock_items[:20]
    }

@router.get("/branch/{branch_id}")
async def get_branch_stock(branch_id: str):
    """Get detailed stock for a specific branch"""
    db = get_db()
    
    # Get branch
    branch = await db['branches'].find_one({"id": branch_id}, {"_id": 0})
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")
    
    # Get products
    products = await db['products'].find(
        {"is_active": True},
        {"_id": 0}
    ).to_list(None)
    product_map = {p["id"]: p for p in products}
    
    # Get stock for this branch
    stocks = await db['product_stocks'].find(
        {"branch_id": branch_id},
        {"_id": 0}
    ).to_list(None)
    
    stock_items = []
    total_value = 0
    low_stock = []
    out_of_stock = []
    
    for stock in stocks:
        product_id = stock.get("product_id")
        if product_id in product_map:
            product = product_map[product_id]
            qty = stock.get("quantity", 0)
            value = qty * product.get("selling_price", 0)
            min_stock = product.get("min_stock", 5)
            
            item = {
                "product_id": product_id,
                "product_name": product["name"],
                "product_code": product.get("code", ""),
                "category": product.get("category_id", ""),
                "quantity": qty,
                "min_stock": min_stock,
                "value": value,
                "status": "ok" if qty > min_stock else ("low" if qty > 0 else "out")
            }
            stock_items.append(item)
            total_value += value
            
            if qty == 0:
                out_of_stock.append(item)
            elif qty <= min_stock:
                low_stock.append(item)
    
    return {
        "branch": branch,
        "total_items": len(stock_items),
        "total_value": total_value,
        "low_stock_count": len(low_stock),
        "out_of_stock_count": len(out_of_stock),
        "stock_items": sorted(stock_items, key=lambda x: x["quantity"]),
        "low_stock": low_stock,
        "out_of_stock": out_of_stock
    }

@router.get("/product/{product_id}")
async def get_product_stock_all_branches(product_id: str):
    """Get stock of a product across all branches"""
    db = get_db()
    
    # Get product
    product = await db['products'].find_one({"id": product_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Get all branches
    branches = await db['branches'].find(
        {"is_active": True},
        {"_id": 0, "id": 1, "name": 1, "code": 1, "city": 1}
    ).to_list(None)
    branch_map = {b["id"]: b for b in branches}
    
    # Get stock for this product
    stocks = await db['product_stocks'].find(
        {"product_id": product_id},
        {"_id": 0}
    ).to_list(None)
    
    branch_stocks = []
    total_qty = 0
    
    for stock in stocks:
        branch_id = stock.get("branch_id")
        if branch_id in branch_map:
            branch = branch_map[branch_id]
            qty = stock.get("quantity", 0)
            total_qty += qty
            
            branch_stocks.append({
                "branch_id": branch_id,
                "branch_name": branch["name"],
                "branch_code": branch.get("code", ""),
                "city": branch.get("city", ""),
                "quantity": qty,
                "status": "ok" if qty > product.get("min_stock", 5) else ("low" if qty > 0 else "out")
            })
    
    # Sort by quantity
    branch_stocks = sorted(branch_stocks, key=lambda x: x["quantity"], reverse=True)
    
    return {
        "product": product,
        "total_quantity": total_qty,
        "total_branches": len(branch_stocks),
        "branch_stocks": branch_stocks
    }

@router.post("/alert/create")
async def create_stock_alert(
    branch_id: str,
    product_id: str,
    alert_type: str = "low_stock"
):
    """Create a stock alert"""
    db = get_db()
    
    # Get branch and product
    branch = await db['branches'].find_one({"id": branch_id}, {"_id": 0, "id": 1, "name": 1})
    product = await db['products'].find_one({"id": product_id}, {"_id": 0, "id": 1, "name": 1, "code": 1, "min_stock": 1})
    
    if not branch or not product:
        raise HTTPException(status_code=404, detail="Branch or product not found")
    
    # Get current stock
    stock = await db['product_stocks'].find_one(
        {"branch_id": branch_id, "product_id": product_id},
        {"_id": 0}
    )
    current_stock = stock.get("quantity", 0) if stock else 0
    
    alert = {
        "id": gen_id(),
        "branch_id": branch_id,
        "branch_name": branch["name"],
        "product_id": product_id,
        "product_name": product["name"],
        "product_code": product.get("code", ""),
        "alert_type": alert_type,
        "current_stock": current_stock,
        "min_stock": product.get("min_stock", 5),
        "recommended_order": max(0, product.get("min_stock", 5) * 2 - current_stock),
        "is_resolved": False,
        "resolved_at": None,
        "resolved_by": None,
        "created_at": now_iso()
    }
    
    await db['stock_alerts'].insert_one(alert)
    
    return alert

@router.get("/alerts")
async def get_stock_alerts(
    branch_id: Optional[str] = None,
    alert_type: Optional[str] = None,
    resolved: bool = False
):
    """Get stock alerts"""
    db = get_db()
    
    filter_query = {"is_resolved": resolved}
    if branch_id:
        filter_query["branch_id"] = branch_id
    if alert_type:
        filter_query["alert_type"] = alert_type
    
    alerts = await db['stock_alerts'].find(
        filter_query,
        {"_id": 0}
    ).sort("created_at", -1).to_list(None)
    
    return {"alerts": alerts, "total": len(alerts)}

@router.post("/alert/{alert_id}/resolve")
async def resolve_alert(alert_id: str, resolved_by: str = "system"):
    """Mark an alert as resolved"""
    db = get_db()
    
    result = await db['stock_alerts'].update_one(
        {"id": alert_id},
        {"$set": {
            "is_resolved": True,
            "resolved_at": now_iso(),
            "resolved_by": resolved_by
        }}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {"message": "Alert resolved", "alert_id": alert_id}

@router.post("/check-and-alert")
async def check_and_create_alerts():
    """Check all stock and create alerts for low/out of stock items"""
    db = get_db()
    
    # Get all products with stock tracking
    products = await db['products'].find(
        {"is_active": True, "track_stock": True},
        {"_id": 0, "id": 1, "name": 1, "code": 1, "min_stock": 1}
    ).to_list(None)
    product_map = {p["id"]: p for p in products}
    
    # Get all branches
    branches = await db['branches'].find(
        {"is_active": True},
        {"_id": 0, "id": 1, "name": 1}
    ).to_list(None)
    branch_map = {b["id"]: b for b in branches}
    
    # Get all stock
    stocks = await db['product_stocks'].find({}, {"_id": 0}).to_list(None)
    
    # Get existing unresolved alerts
    existing_alerts = await db['stock_alerts'].find(
        {"is_resolved": False},
        {"_id": 0, "branch_id": 1, "product_id": 1}
    ).to_list(None)
    existing_keys = {(a["branch_id"], a["product_id"]) for a in existing_alerts}
    
    new_alerts = []
    
    for stock in stocks:
        branch_id = stock.get("branch_id")
        product_id = stock.get("product_id")
        qty = stock.get("quantity", 0)
        
        if branch_id in branch_map and product_id in product_map:
            product = product_map[product_id]
            branch = branch_map[branch_id]
            min_stock = product.get("min_stock", 5)
            
            # Check if alert already exists
            if (branch_id, product_id) in existing_keys:
                continue
            
            alert_type = None
            if qty == 0:
                alert_type = "out_of_stock"
            elif qty <= min_stock:
                alert_type = "low_stock"
            
            if alert_type:
                alert = {
                    "id": gen_id(),
                    "branch_id": branch_id,
                    "branch_name": branch["name"],
                    "product_id": product_id,
                    "product_name": product["name"],
                    "product_code": product.get("code", ""),
                    "alert_type": alert_type,
                    "current_stock": qty,
                    "min_stock": min_stock,
                    "recommended_order": max(0, min_stock * 2 - qty),
                    "is_resolved": False,
                    "resolved_at": None,
                    "resolved_by": None,
                    "created_at": now_iso()
                }
                new_alerts.append(alert)
    
    # Insert new alerts
    if new_alerts:
        await db['stock_alerts'].insert_many(new_alerts)
    
    return {
        "message": f"Created {len(new_alerts)} new alerts",
        "new_alerts_count": len(new_alerts),
        "total_existing_alerts": len(existing_alerts)
    }

@router.get("/transfer/suggest")
async def suggest_stock_transfers():
    """Suggest stock transfers from overstocked to understocked branches"""
    db = get_db()
    
    # Get products
    products = await db['products'].find(
        {"is_active": True, "track_stock": True},
        {"_id": 0, "id": 1, "name": 1, "code": 1, "min_stock": 1}
    ).to_list(None)
    product_map = {p["id"]: p for p in products}
    
    # Get branches
    branches = await db['branches'].find(
        {"is_active": True},
        {"_id": 0, "id": 1, "name": 1, "code": 1, "is_warehouse": 1}
    ).to_list(None)
    branch_map = {b["id"]: b for b in branches}
    
    # Get stock
    stocks = await db['product_stocks'].find({}, {"_id": 0}).to_list(None)
    
    # Group by product
    product_stocks = {}
    for stock in stocks:
        product_id = stock.get("product_id")
        if product_id not in product_stocks:
            product_stocks[product_id] = []
        product_stocks[product_id].append(stock)
    
    suggestions = []
    
    for product_id, branch_stocks in product_stocks.items():
        if product_id not in product_map:
            continue
            
        product = product_map[product_id]
        min_stock = product.get("min_stock", 5)
        
        # Find branches with low stock and high stock
        low_branches = []
        high_branches = []
        
        for stock in branch_stocks:
            branch_id = stock.get("branch_id")
            qty = stock.get("quantity", 0)
            
            if branch_id not in branch_map:
                continue
            
            branch = branch_map[branch_id]
            
            if qty <= min_stock:
                low_branches.append({
                    "branch_id": branch_id,
                    "branch_name": branch["name"],
                    "is_warehouse": branch.get("is_warehouse", False),
                    "quantity": qty,
                    "needed": min_stock * 2 - qty
                })
            elif qty > min_stock * 3:  # Has excess stock
                high_branches.append({
                    "branch_id": branch_id,
                    "branch_name": branch["name"],
                    "is_warehouse": branch.get("is_warehouse", False),
                    "quantity": qty,
                    "excess": qty - min_stock * 2
                })
        
        # Generate suggestions
        for low in low_branches:
            for high in high_branches:
                if high["excess"] >= low["needed"]:
                    transfer_qty = min(high["excess"], low["needed"])
                    suggestions.append({
                        "product_id": product_id,
                        "product_name": product["name"],
                        "product_code": product.get("code", ""),
                        "from_branch_id": high["branch_id"],
                        "from_branch_name": high["branch_name"],
                        "to_branch_id": low["branch_id"],
                        "to_branch_name": low["branch_name"],
                        "suggested_quantity": transfer_qty,
                        "priority": "high" if low["quantity"] == 0 else "normal"
                    })
                    break  # Only one suggestion per low branch per product
    
    # Sort by priority
    suggestions = sorted(suggestions, key=lambda x: (0 if x["priority"] == "high" else 1))
    
    return {
        "suggestions": suggestions[:20],
        "total_suggestions": len(suggestions)
    }
