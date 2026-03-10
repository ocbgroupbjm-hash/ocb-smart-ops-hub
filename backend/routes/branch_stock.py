# OCB TITAN AI - Branch Stock Management
# Stok per cabang dengan minimum dan maximum

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
import uuid

router = APIRouter(prefix="/inventory", tags=["Branch Stock"])

def get_db():
    from database import get_db as db_get
    return db_get()

from routes.auth import get_current_user

# Collections
def branch_stocks():
    return get_db()["item_branch_stock"]

def items_col():
    return get_db()["items"]

def branches_col():
    return get_db()["branches"]


# Models
class BranchStockItem(BaseModel):
    branch_id: str
    branch_name: Optional[str] = ""
    stock_current: int = 0
    stock_minimum: int = 0
    stock_maximum: int = 0


class BranchStockUpdate(BaseModel):
    branch_stocks: List[BranchStockItem]


# ==================== BRANCH STOCK ENDPOINTS ====================

@router.get("/branch-stock/{item_id}")
async def get_item_branch_stocks(item_id: str, user: dict = Depends(get_current_user)):
    """Get all branch stocks for an item"""
    db = get_db()
    
    # Verify item exists (use products collection)
    item = await db["products"].find_one({"id": item_id}, {"_id": 0, "name": 1})
    if not item:
        raise HTTPException(status_code=404, detail="Item tidak ditemukan")
    
    # Get branch stock configs (min/max)
    configs = await db["item_branch_stock"].find(
        {"item_id": item_id}, 
        {"_id": 0}
    ).to_list(1000)
    
    # Get all branches
    branches = await db["branches"].find({}, {"_id": 0, "id": 1, "name": 1}).to_list(500)
    branch_map = {b["id"]: b["name"] for b in branches}
    config_map = {c["branch_id"]: c for c in configs}
    
    # Calculate stock_current from stock_movements (SSOT)
    pipeline = [
        {"$match": {"item_id": item_id}},
        {"$group": {"_id": "$branch_id", "stock_current": {"$sum": "$quantity"}}}
    ]
    stock_results = await db["stock_movements"].aggregate(pipeline).to_list(500)
    stock_map = {s["_id"]: s["stock_current"] for s in stock_results}
    
    # Build result with calculated stock
    stocks = []
    for branch in branches:
        config = config_map.get(branch["id"], {})
        stocks.append({
            "id": config.get("id", str(uuid.uuid4())),
            "item_id": item_id,
            "branch_id": branch["id"],
            "branch_name": branch.get("name", ""),
            "stock_current": stock_map.get(branch["id"], 0),  # Calculated from movements (SSOT)
            "stock_minimum": config.get("stock_minimum", 0),
            "stock_maximum": config.get("stock_maximum", 0)
        })
    
    return {
        "item_id": item_id,
        "item_name": item.get("name"),
        "branch_stocks": stocks
    }


@router.post("/branch-stock/{item_id}")
async def save_item_branch_stocks(
    item_id: str, 
    data: BranchStockUpdate, 
    user: dict = Depends(get_current_user)
):
    """Save branch stocks for an item (ONLY min/max - stock_current is managed by transactions)"""
    db = get_db()
    
    # Verify item exists (use products collection)
    item = await db["products"].find_one({"id": item_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Item tidak ditemukan")
    
    # Update or insert each branch stock - ONLY min and max (stock_current tidak boleh diubah manual)
    for bs in data.branch_stocks:
        # Get existing stock_current (don't overwrite it)
        existing = await db["item_branch_stock"].find_one(
            {"item_id": item_id, "branch_id": bs.branch_id},
            {"_id": 0, "stock_current": 1}
        )
        current_stock = existing.get("stock_current", 0) if existing else 0
        
        stock_doc = {
            "item_id": item_id,
            "branch_id": bs.branch_id,
            "branch_name": bs.branch_name,
            "stock_current": current_stock,  # Preserve existing stock, tidak terima dari frontend
            "stock_minimum": bs.stock_minimum,
            "stock_maximum": bs.stock_maximum,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Upsert
        await db["item_branch_stock"].update_one(
            {"item_id": item_id, "branch_id": bs.branch_id},
            {"$set": stock_doc, "$setOnInsert": {"id": str(uuid.uuid4()), "created_at": datetime.now(timezone.utc).isoformat()}},
            upsert=True
        )
    
    return {"message": "Stok per cabang berhasil disimpan", "count": len(data.branch_stocks)}


@router.get("/branch-stock-alerts")
async def get_branch_stock_alerts(
    branch_id: str = "",
    user: dict = Depends(get_current_user)
):
    """Get low stock alerts per branch"""
    db = get_db()
    
    query = {"stock_current": {"$lte": "$stock_minimum"}}
    if branch_id:
        query["branch_id"] = branch_id
    
    # Find items below minimum stock per branch
    pipeline = [
        {"$match": {"stock_minimum": {"$gt": 0}}},
        {"$addFields": {
            "is_low_stock": {"$lte": ["$stock_current", "$stock_minimum"]},
            "shortage": {"$subtract": ["$stock_minimum", "$stock_current"]}
        }},
        {"$match": {"is_low_stock": True}},
        {"$sort": {"shortage": -1}},
        {"$limit": 100}
    ]
    
    if branch_id:
        pipeline.insert(0, {"$match": {"branch_id": branch_id}})
    
    alerts = await db["item_branch_stock"].aggregate(pipeline).to_list(100)
    
    # Enrich with item info
    for alert in alerts:
        item = await db["products"].find_one({"id": alert["item_id"]}, {"_id": 0, "code": 1, "name": 1})
        if item:
            alert["item_code"] = item.get("code")
            alert["item_name"] = item.get("name")
        
        if "_id" in alert:
            del alert["_id"]
    
    return {
        "alerts": alerts,
        "total": len(alerts)
    }


@router.get("/ai-restock-recommendations")
async def get_ai_restock_recommendations(
    branch_id: str = "",
    user: dict = Depends(get_current_user)
):
    """AI-powered restock recommendations based on branch stock levels"""
    db = get_db()
    
    # Get items with low stock per branch
    pipeline = [
        {"$match": {"stock_minimum": {"$gt": 0}}},
        {"$addFields": {
            "is_low_stock": {"$lte": ["$stock_current", "$stock_minimum"]},
            "shortage": {"$subtract": ["$stock_minimum", "$stock_current"]},
            "restock_qty": {"$subtract": ["$stock_maximum", "$stock_current"]}
        }},
        {"$match": {"is_low_stock": True, "shortage": {"$gt": 0}}},
        {"$sort": {"shortage": -1}},
        {"$limit": 50}
    ]
    
    if branch_id:
        pipeline.insert(0, {"$match": {"branch_id": branch_id}})
    
    low_stocks = await db["item_branch_stock"].aggregate(pipeline).to_list(50)
    
    recommendations = []
    for stock in low_stocks:
        item = await db["products"].find_one({"id": stock["item_id"]}, {"_id": 0, "code": 1, "name": 1, "cost_price": 1})
        if not item:
            continue
        
        restock_qty = max(0, stock.get("restock_qty", 0))
        est_cost = restock_qty * (item.get("cost_price", 0) or 0)
        
        rec = {
            "item_id": stock["item_id"],
            "item_code": item.get("code"),
            "item_name": item.get("name"),
            "branch_id": stock["branch_id"],
            "branch_name": stock.get("branch_name"),
            "current_stock": stock["stock_current"],
            "minimum_stock": stock["stock_minimum"],
            "maximum_stock": stock.get("stock_maximum", 0),
            "shortage": stock["shortage"],
            "recommended_restock_qty": restock_qty,
            "estimated_cost": est_cost,
            "priority": "HIGH" if stock["shortage"] > stock["stock_minimum"] else "MEDIUM",
            "reason": f"Stok saat ini ({stock['stock_current']}) di bawah minimum ({stock['stock_minimum']})"
        }
        recommendations.append(rec)
    
    # Calculate totals
    total_items = len(recommendations)
    total_cost = sum(r["estimated_cost"] for r in recommendations)
    high_priority = sum(1 for r in recommendations if r["priority"] == "HIGH")
    
    return {
        "recommendations": recommendations,
        "summary": {
            "total_items_need_restock": total_items,
            "high_priority_items": high_priority,
            "estimated_total_cost": total_cost
        }
    }


# Auto-initialize branch stocks when item is created
@router.post("/branch-stock/initialize/{item_id}")
async def initialize_branch_stocks(item_id: str, user: dict = Depends(get_current_user)):
    """Initialize branch stocks for a new item (all branches)"""
    db = get_db()
    
    # Verify item exists (use products collection)
    item = await db["products"].find_one({"id": item_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Item tidak ditemukan")
    
    # Get all branches
    branches = await db["branches"].find({}, {"_id": 0, "id": 1, "name": 1}).to_list(500)
    
    # Check existing stocks
    existing = await db["item_branch_stock"].find({"item_id": item_id}, {"branch_id": 1}).to_list(500)
    existing_branch_ids = {e["branch_id"] for e in existing}
    
    # Create stocks for missing branches
    new_stocks = []
    for branch in branches:
        if branch["id"] not in existing_branch_ids:
            new_stocks.append({
                "id": str(uuid.uuid4()),
                "item_id": item_id,
                "branch_id": branch["id"],
                "branch_name": branch.get("name", ""),
                "stock_current": 0,
                "stock_minimum": 0,
                "stock_maximum": 0,
                "created_at": datetime.now(timezone.utc).isoformat()
            })
    
    if new_stocks:
        await db["item_branch_stock"].insert_many(new_stocks)
    
    return {
        "message": f"Initialized stocks for {len(new_stocks)} branches",
        "total_branches": len(branches),
        "new_stocks_created": len(new_stocks)
    }


# ==================== STOCK MOVEMENT FROM TRANSACTIONS ====================
# Endpoint ini HANYA untuk dipanggil dari transaksi inventory internal

class StockMovementRequest(BaseModel):
    branch_id: str
    quantity: int  # Positif untuk masuk, negatif untuk keluar
    transaction_type: str  # purchase, sale, stock_in, stock_out, transfer_in, transfer_out, opname, retur_sale, retur_purchase, assembly
    reference_id: str = ""  # ID transaksi referensi
    notes: str = ""


@router.post("/branch-stock/{item_id}/movement")
async def record_stock_movement(
    item_id: str,
    data: StockMovementRequest,
    user: dict = Depends(get_current_user)
):
    """
    Record stock movement from inventory transaction.
    This is the ONLY way to update stock_current.
    
    Transaction types:
    - purchase: Pembelian/Penerimaan Barang (+)
    - stock_in: Stok Masuk (+)
    - sale: Penjualan (-)
    - stock_out: Stok Keluar (-)
    - transfer_in: Transfer Masuk (+)
    - transfer_out: Transfer Keluar (-)
    - opname: Stok Opname (adjustment)
    - retur_sale: Retur Penjualan (+)
    - retur_purchase: Retur Pembelian (-)
    - assembly: Rakitan Produk (-)
    """
    db = get_db()
    
    # Verify item exists
    item = await db["products"].find_one({"id": item_id}, {"_id": 0, "name": 1})
    if not item:
        raise HTTPException(status_code=404, detail="Item tidak ditemukan")
    
    # Get or create branch stock
    branch_stock = await db["item_branch_stock"].find_one(
        {"item_id": item_id, "branch_id": data.branch_id},
        {"_id": 0}
    )
    
    if not branch_stock:
        # Initialize branch stock if not exists
        branch = await db["branches"].find_one({"id": data.branch_id}, {"_id": 0, "name": 1})
        branch_name = branch.get("name", "") if branch else ""
        branch_stock = {
            "id": str(uuid.uuid4()),
            "item_id": item_id,
            "branch_id": data.branch_id,
            "branch_name": branch_name,
            "stock_current": 0,
            "stock_minimum": 0,
            "stock_maximum": 0,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db["item_branch_stock"].insert_one(branch_stock)
    
    # Calculate new stock
    current_stock = branch_stock.get("stock_current", 0)
    new_stock = current_stock + data.quantity
    
    # Prevent negative stock (optional - depends on business rules)
    if new_stock < 0:
        raise HTTPException(
            status_code=400, 
            detail=f"Stok tidak mencukupi. Stok saat ini: {current_stock}, permintaan: {data.quantity}"
        )
    
    # Update stock_current
    await db["item_branch_stock"].update_one(
        {"item_id": item_id, "branch_id": data.branch_id},
        {
            "$set": {
                "stock_current": new_stock,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    # Record movement history
    movement_record = {
        "id": str(uuid.uuid4()),
        "item_id": item_id,
        "branch_id": data.branch_id,
        "transaction_type": data.transaction_type,
        "quantity": data.quantity,
        "stock_before": current_stock,
        "stock_after": new_stock,
        "reference_id": data.reference_id,
        "notes": data.notes,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user.get("id")
    }
    await db["stock_movements"].insert_one(movement_record)
    
    return {
        "message": "Stok berhasil diupdate",
        "item_id": item_id,
        "branch_id": data.branch_id,
        "transaction_type": data.transaction_type,
        "quantity": data.quantity,
        "stock_before": current_stock,
        "stock_after": new_stock
    }


@router.get("/branch-stock/{item_id}/movements")
async def get_stock_movements(
    item_id: str,
    branch_id: str = "",
    limit: int = 50,
    user: dict = Depends(get_current_user)
):
    """Get stock movement history for an item"""
    db = get_db()
    
    query = {"item_id": item_id}
    if branch_id:
        query["branch_id"] = branch_id
    
    movements = await db["stock_movements"].find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    return {
        "movements": movements,
        "total": len(movements)
    }

