# OCB TITAN - Inventory Management API
# SECURITY: All operations require RBAC validation
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional, List, Dict
from database import (
    products, product_stocks, stock_movements, stock_transfers, 
    stock_opnames, branches, get_next_sequence, get_db
)
from utils.auth import get_current_user
from models.titan_models import StockMovement, StockMovementType, StockTransfer, StockOpname, ProductStock
from routes.rbac_middleware import require_permission, log_security_event
from datetime import datetime, timezone

router = APIRouter(prefix="/inventory", tags=["Inventory"])

# ==================== SINGLE SOURCE INVENTORY HELPER ====================
# Stock is calculated from stock_movements as the single source of truth

async def calculate_stock_from_movements(product_id: str, branch_id: str) -> int:
    """
    Calculate current stock from stock_movements collection.
    This is the SINGLE SOURCE OF TRUTH for inventory.
    
    Movement types that INCREASE stock:
    - purchase_in (goods receipt from PO)
    - assembly_in (output from assembly)
    - transfer_in (received from transfer)
    - adjustment (positive adjustment)
    - initial (initial stock setup)
    - stock_in (manual stock in)
    
    Movement types that DECREASE stock:
    - sales_out (sold to customer)
    - assembly_out (materials used in assembly)
    - transfer_out (sent to another branch)
    - adjustment (negative adjustment)
    - stock_out (manual stock out)
    """
    pipeline = [
        {"$match": {"product_id": product_id, "branch_id": branch_id}},
        {
            "$group": {
                "_id": None,
                "total": {"$sum": "$quantity"}  # quantity is +/- based on movement type
            }
        }
    ]
    
    result = await stock_movements.aggregate(pipeline).to_list(1)
    return result[0]["total"] if result else 0


async def calculate_bulk_stock_from_movements(product_ids: List[str], branch_id: str) -> Dict[str, int]:
    """Calculate stock for multiple products at once"""
    if not product_ids:
        return {}
    
    pipeline = [
        {"$match": {"product_id": {"$in": product_ids}, "branch_id": branch_id}},
        {
            "$group": {
                "_id": "$product_id",
                "total": {"$sum": "$quantity"}
            }
        }
    ]
    
    result = await stock_movements.aggregate(pipeline).to_list(len(product_ids))
    return {item["_id"]: item["total"] for item in result}


async def sync_product_stock_from_movements(product_id: str, branch_id: str) -> int:
    """
    Sync product_stocks collection with calculated stock from movements.
    This ensures product_stocks stays in sync with the source of truth.
    Returns the synced quantity.
    """
    calculated_qty = await calculate_stock_from_movements(product_id, branch_id)
    
    # Update product_stocks
    existing = await product_stocks.find_one({"product_id": product_id, "branch_id": branch_id})
    
    if existing:
        await product_stocks.update_one(
            {"product_id": product_id, "branch_id": branch_id},
            {"$set": {
                "quantity": calculated_qty,
                "available": calculated_qty - existing.get("reserved", 0),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
    else:
        new_stock = ProductStock(
            product_id=product_id,
            branch_id=branch_id,
            quantity=calculated_qty,
            available=calculated_qty,
            reserved=0
        )
        await product_stocks.insert_one(new_stock.model_dump())
    
    return calculated_qty

class StockAdjustment(BaseModel):
    product_id: str
    quantity: int  # Positive or negative
    reason: str = ""

class TransferItem(BaseModel):
    product_id: str
    quantity: int

class CreateTransfer(BaseModel):
    from_branch_id: str
    to_branch_id: str
    items: List[TransferItem]
    notes: str = ""

class OpnameItem(BaseModel):
    product_id: str
    actual_qty: int

class CreateOpname(BaseModel):
    items: List[OpnameItem]
    notes: str = ""

# ==================== STOCK OVERVIEW ====================

@router.get("/stock/calculated/{product_id}")
async def get_calculated_stock(
    product_id: str,
    branch_id: str = "",
    user: dict = Depends(require_permission("stock_card", "view"))
):
    """Get stock calculated from stock_movements (single source of truth)"""
    branch = branch_id or user.get("branch_id")
    if not branch:
        raise HTTPException(status_code=400, detail="Branch ID required")
    
    qty = await calculate_stock_from_movements(product_id, branch)
    
    # Get product info
    product = await products.find_one({"id": product_id}, {"_id": 0, "name": 1, "code": 1, "min_stock": 1})
    
    return {
        "product_id": product_id,
        "branch_id": branch,
        "quantity": qty,
        "product_name": product.get("name") if product else "Unknown",
        "product_code": product.get("code") if product else "",
        "min_stock": product.get("min_stock", 0) if product else 0,
        "is_low_stock": qty <= product.get("min_stock", 0) if product else False,
        "source": "stock_movements"
    }


@router.post("/stock/sync/{product_id}")
async def sync_product_stock(
    product_id: str,
    branch_id: str = "",
    user: dict = Depends(require_permission("stock_card", "edit"))
):
    """Sync product_stocks with calculated stock from movements"""
    branch = branch_id or user.get("branch_id")
    if not branch:
        raise HTTPException(status_code=400, detail="Branch ID required")
    
    qty = await sync_product_stock_from_movements(product_id, branch)
    
    return {
        "product_id": product_id,
        "branch_id": branch,
        "synced_quantity": qty,
        "message": "Stock synced from movements"
    }


@router.post("/stock/sync-all")
async def sync_all_stock(
    branch_id: str = "",
    user: dict = Depends(require_permission("stock_card", "edit"))
):
    """Sync all product_stocks with calculated stock from movements for a branch"""
    branch = branch_id or user.get("branch_id")
    if not branch:
        raise HTTPException(status_code=400, detail="Branch ID required")
    
    # Get all products
    all_products = await products.find({"is_active": True}, {"_id": 0, "id": 1}).to_list(10000)
    product_ids = [p["id"] for p in all_products]
    
    # Calculate stock for all products
    stock_map = await calculate_bulk_stock_from_movements(product_ids, branch)
    
    synced_count = 0
    for pid, qty in stock_map.items():
        existing = await product_stocks.find_one({"product_id": pid, "branch_id": branch})
        
        if existing:
            await product_stocks.update_one(
                {"product_id": pid, "branch_id": branch},
                {"$set": {
                    "quantity": qty,
                    "available": qty - existing.get("reserved", 0),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
        else:
            new_stock = ProductStock(
                product_id=pid,
                branch_id=branch,
                quantity=qty,
                available=qty,
                reserved=0
            )
            await product_stocks.insert_one(new_stock.model_dump())
        
        synced_count += 1
    
    return {
        "branch_id": branch,
        "synced_products": synced_count,
        "message": f"Synced {synced_count} products from stock_movements"
    }


@router.get("/stock")
async def get_branch_stock(
    branch_id: str = "",
    low_stock_only: bool = False,
    search: str = "",
    skip: int = 0,
    limit: int = 100,
    user: dict = Depends(require_permission("stock_card", "view"))
):
    """
    Get stock for a branch - SSOT: stock_movements
    
    ARSITEKTUR FINAL:
    - Source stok = stock_movements (sama dengan Daftar Item dan Kartu Stok)
    - Query dengan $or untuk backward compatibility (product_id atau item_id)
    - Agregasi per product
    - branch_id filter HANYA jika explicitly provided (tidak pakai default user branch)
    """
    db = get_db()
    
    # PENTING: branch_id hanya dipakai jika explicitly provided
    # Jangan pakai default user branch - agar konsisten dengan Daftar Item
    branch = branch_id if branch_id else ""
    
    # Step 1: Get all active products first
    product_query = {"is_active": True}
    if search:
        product_query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"code": {"$regex": search, "$options": "i"}}
        ]
    
    products_cursor = db["products"].find(product_query, {"_id": 0}).sort("name", 1).skip(skip).limit(limit)
    products_list = await products_cursor.to_list(limit)
    
    # Count total products
    total = await db["products"].count_documents(product_query)
    
    # Step 2: Calculate stock from stock_movements (SSOT)
    items = []
    for prod in products_list:
        product_id = prod.get("id")
        
        # Query stock_movements dengan $or untuk backward compatibility
        stock_query = {
            "$or": [
                {"product_id": product_id},
                {"item_id": product_id}
            ]
        }
        
        # HANYA filter branch jika explicitly provided
        if branch:
            stock_query["branch_id"] = branch
        
        # Aggregate stock from movements
        pipeline = [
            {"$match": stock_query},
            {"$group": {
                "_id": None,
                "total_qty": {"$sum": "$quantity"}
            }}
        ]
        
        agg_result = await db["stock_movements"].aggregate(pipeline).to_list(1)
        quantity = agg_result[0].get("total_qty", 0) if agg_result else 0
        
        # Check low stock
        min_stock = prod.get("min_stock", 0)
        is_low = quantity <= min_stock if min_stock > 0 else False
        
        # Skip if low_stock_only filter and not low
        if low_stock_only and not is_low:
            continue
        
        items.append({
            "product_id": product_id,
            "branch_id": branch if branch else "all",
            "quantity": quantity,
            "available": quantity,
            "reserved": 0,
            "product_code": prod.get("code", ""),
            "product_name": prod.get("name", ""),
            "min_stock": min_stock,
            "cost_price": prod.get("cost_price", 0),
            "selling_price": prod.get("selling_price", 0),
            "is_low_stock": is_low
        })
    
    # If low_stock_only, adjust total
    if low_stock_only:
        total = len(items)
    
    return {"items": items, "total": total}

@router.get("/stock/low")
async def get_low_stock_alerts(user: dict = Depends(require_permission("stock_card", "view"))):
    """Get products with low stock across all accessible branches"""
    branch_ids = user.get("branch_ids", [])
    if user.get("branch_id"):
        branch_ids.append(user["branch_id"])
    
    if not branch_ids:
        branch_ids = [b["id"] for b in await branches.find({"is_active": True}, {"_id": 0, "id": 1}).to_list(500)]
    
    pipeline = [
        {"$match": {"branch_id": {"$in": branch_ids}}},
        {
            "$lookup": {
                "from": "products",
                "localField": "product_id",
                "foreignField": "id",
                "as": "product"
            }
        },
        {"$unwind": "$product"},
        {"$match": {"product.is_active": True, "product.track_stock": True}},
        {"$match": {"$expr": {"$lte": ["$quantity", "$product.min_stock"]}}},
        {
            "$lookup": {
                "from": "branches",
                "localField": "branch_id",
                "foreignField": "id",
                "as": "branch"
            }
        },
        {"$unwind": "$branch"},
        {
            "$project": {
                "_id": 0,
                "product_id": 1,
                "product_code": "$product.code",
                "product_name": "$product.name",
                "branch_id": 1,
                "branch_name": "$branch.name",
                "quantity": 1,
                "min_stock": "$product.min_stock",
                "shortage": {"$subtract": ["$product.min_stock", "$quantity"]}
            }
        },
        {"$sort": {"shortage": -1}},
        {"$limit": 100}
    ]
    
    items = await product_stocks.aggregate(pipeline).to_list(100)
    return items

# ==================== STOCK MOVEMENTS ====================

@router.get("/movements")
async def get_stock_movements(
    product_id: str = "",
    branch_id: str = "",
    movement_type: str = "",
    date_from: str = "",
    date_to: str = "",
    skip: int = 0,
    limit: int = 100,
    user: dict = Depends(require_permission("stock_movement", "view"))
):
    """Get stock movement history"""
    query = {}
    
    if product_id:
        query["product_id"] = product_id
    
    if branch_id:
        query["branch_id"] = branch_id
    elif user.get("branch_id"):
        query["branch_id"] = user["branch_id"]
    
    if movement_type:
        query["movement_type"] = movement_type
    
    if date_from:
        query["created_at"] = {"$gte": date_from}
    
    if date_to:
        if "created_at" in query:
            query["created_at"]["$lte"] = date_to
        else:
            query["created_at"] = {"$lte": date_to}
    
    items = await stock_movements.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    # Enrich with product names
    for item in items:
        prod_id = item.get("product_id", "")
        if prod_id:
            product = await products.find_one({"id": prod_id}, {"_id": 0, "name": 1, "code": 1})
            item["product_name"] = product.get("name", "") if product else "Unknown"
            item["product_code"] = product.get("code", "") if product else ""
        else:
            item["product_name"] = "Unknown"
            item["product_code"] = ""
    
    total = await stock_movements.count_documents(query)
    
    return {"items": items, "total": total}


@router.delete("/movements/{movement_id}")
async def delete_movement(movement_id: str, user: dict = Depends(require_permission("stock_movement", "delete"))):
    """Delete a stock movement and reverse the stock change"""
    # Find the movement
    movement = await stock_movements.find_one({"id": movement_id}, {"_id": 0})
    if not movement:
        raise HTTPException(status_code=404, detail="Movement tidak ditemukan")
    
    product_id = movement.get("product_id")
    branch_id = movement.get("branch_id")
    quantity = movement.get("quantity", 0)
    movement_type = movement.get("movement_type", "")
    
    # Reverse the stock change
    stock = await product_stocks.find_one({"product_id": product_id, "branch_id": branch_id})
    if stock:
        current_qty = stock.get("quantity", 0)
        
        # Reverse: if was stock_in, subtract; if was stock_out, add back
        if movement_type in ["stock_in", "purchase", "transfer_in", "adjustment_in"]:
            new_qty = max(0, current_qty - quantity)
        else:  # stock_out, sales, transfer_out, adjustment_out
            new_qty = current_qty + quantity
        
        await product_stocks.update_one(
            {"product_id": product_id, "branch_id": branch_id},
            {"$set": {
                "quantity": new_qty,
                "available": new_qty - stock.get("reserved", 0),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
    
    # Delete the movement
    await stock_movements.delete_one({"id": movement_id})
    
    return {"message": "Movement berhasil dihapus dan stok disesuaikan"}



@router.post("/adjust")
async def adjust_stock(data: StockAdjustment, request: Request, user: dict = Depends(require_permission("stock_opname", "edit"))):
    """Adjust stock quantity - Requires stock_opname.edit permission"""
    branch_id = user.get("branch_id")
    if not branch_id:
        raise HTTPException(status_code=400, detail="User not assigned to a branch")
    
    stock = await product_stocks.find_one({"product_id": data.product_id, "branch_id": branch_id})
    
    if stock:
        new_qty = max(0, stock.get("quantity", 0) + data.quantity)
        await product_stocks.update_one(
            {"product_id": data.product_id, "branch_id": branch_id},
            {"$set": {
                "quantity": new_qty,
                "available": new_qty - stock.get("reserved", 0),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
    else:
        new_stock = ProductStock(
            product_id=data.product_id,
            branch_id=branch_id,
            quantity=max(0, data.quantity),
            available=max(0, data.quantity)
        )
        await product_stocks.insert_one(new_stock.model_dump())
        new_qty = max(0, data.quantity)
    
    # Record movement
    movement = StockMovement(
        product_id=data.product_id,
        branch_id=branch_id,
        movement_type=StockMovementType.ADJUSTMENT,
        quantity=data.quantity,
        notes=data.reason,
        user_id=user.get("user_id", "")
    )
    await stock_movements.insert_one(movement.model_dump())
    
    return {"message": "Stock adjusted", "new_quantity": new_qty}

# ==================== STOCK TRANSFERS ====================

class StockInOut(BaseModel):
    product_id: str
    quantity: int
    notes: str = ""

@router.post("/stock-in")
async def stock_in(data: StockInOut, request: Request, user: dict = Depends(require_permission("stock_in", "create"))):
    """Add stock (stock in) - Requires stock_in.create permission"""
    branch_id = user.get("branch_id")
    if not branch_id:
        raise HTTPException(status_code=400, detail="User tidak terhubung ke cabang")
    
    if data.quantity <= 0:
        raise HTTPException(status_code=400, detail="Jumlah harus lebih dari 0")
    
    # Get product info
    product = await products.find_one({"id": data.product_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Produk tidak ditemukan")
    
    # Update or create stock
    stock = await product_stocks.find_one({"product_id": data.product_id, "branch_id": branch_id})
    
    if stock:
        new_qty = stock.get("quantity", 0) + data.quantity
        await product_stocks.update_one(
            {"product_id": data.product_id, "branch_id": branch_id},
            {"$set": {
                "quantity": new_qty,
                "available": new_qty - stock.get("reserved", 0),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
    else:
        new_stock = ProductStock(
            product_id=data.product_id,
            branch_id=branch_id,
            quantity=data.quantity,
            available=data.quantity
        )
        await product_stocks.insert_one(new_stock.model_dump())
        new_qty = data.quantity
    
    # Record movement
    movement = StockMovement(
        product_id=data.product_id,
        branch_id=branch_id,
        movement_type=StockMovementType.STOCK_IN,
        quantity=data.quantity,
        quantity_after=new_qty,
        notes=data.notes or "Stok masuk",
        user_id=user.get("user_id", "")
    )
    await stock_movements.insert_one(movement.model_dump())
    
    return {"message": "Stok berhasil ditambahkan", "new_quantity": new_qty}

@router.post("/stock-out")
async def stock_out(data: StockInOut, request: Request, user: dict = Depends(require_permission("stock_out", "create"))):
    """Remove stock (stock out) - Requires stock_out.create permission"""
    branch_id = user.get("branch_id")
    if not branch_id:
        raise HTTPException(status_code=400, detail="User tidak terhubung ke cabang")
    
    if data.quantity <= 0:
        raise HTTPException(status_code=400, detail="Jumlah harus lebih dari 0")
    
    stock = await product_stocks.find_one({"product_id": data.product_id, "branch_id": branch_id})
    
    if not stock or stock.get("quantity", 0) < data.quantity:
        raise HTTPException(status_code=400, detail="Stok tidak mencukupi")
    
    new_qty = stock.get("quantity", 0) - data.quantity
    await product_stocks.update_one(
        {"product_id": data.product_id, "branch_id": branch_id},
        {"$set": {
            "quantity": new_qty,
            "available": new_qty - stock.get("reserved", 0),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Record movement
    movement = StockMovement(
        product_id=data.product_id,
        branch_id=branch_id,
        movement_type=StockMovementType.STOCK_OUT,
        quantity=-data.quantity,
        quantity_after=new_qty,
        notes=data.notes or "Stok keluar",
        user_id=user.get("user_id", "")
    )
    await stock_movements.insert_one(movement.model_dump())
    
    return {"message": "Stok berhasil dikurangi", "new_quantity": new_qty}

@router.post("/transfer")
async def create_transfer(data: CreateTransfer, request: Request, user: dict = Depends(require_permission("stock_transfer", "create"))):
    """Create a stock transfer request - Requires stock_transfer.create permission"""
    from_branch = await branches.find_one({"id": data.from_branch_id}, {"_id": 0})
    to_branch = await branches.find_one({"id": data.to_branch_id}, {"_id": 0})
    
    if not from_branch or not to_branch:
        raise HTTPException(status_code=400, detail="Invalid branch")
    
    # Validate stock availability
    transfer_items = []
    for item in data.items:
        product = await products.find_one({"id": item.product_id}, {"_id": 0})
        if not product:
            raise HTTPException(status_code=400, detail=f"Product not found: {item.product_id}")
        
        stock = await product_stocks.find_one(
            {"product_id": item.product_id, "branch_id": data.from_branch_id},
            {"_id": 0}
        )
        available = stock.get("available", 0) if stock else 0
        
        if available < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for {product['name']}. Available: {available}"
            )
        
        transfer_items.append({
            "product_id": item.product_id,
            "product_code": product.get("code", ""),
            "product_name": product.get("name", ""),
            "quantity": item.quantity
        })
    
    transfer_number = await get_next_sequence("transfer", "TRF")
    
    transfer = StockTransfer(
        transfer_number=transfer_number,
        from_branch_id=data.from_branch_id,
        from_branch_name=from_branch.get("name", ""),
        to_branch_id=data.to_branch_id,
        to_branch_name=to_branch.get("name", ""),
        items=transfer_items,
        notes=data.notes,
        requested_by=user.get("user_id", "")
    )
    
    await stock_transfers.insert_one(transfer.model_dump())
    
    # Reserve stock
    for item in data.items:
        await product_stocks.update_one(
            {"product_id": item.product_id, "branch_id": data.from_branch_id},
            {"$inc": {"reserved": item.quantity, "available": -item.quantity}}
        )
    
    return {"id": transfer.id, "transfer_number": transfer_number, "message": "Transfer created"}

@router.get("/transfers")
async def list_transfers(
    status: str = "",
    skip: int = 0,
    limit: int = 50,
    user: dict = Depends(require_permission("stock_transfer", "view"))
):
    """List stock transfers - Requires stock_transfer.view permission"""
    branch_id = user.get("branch_id")
    query = {
        "$or": [
            {"from_branch_id": branch_id},
            {"to_branch_id": branch_id}
        ]
    }
    
    if status:
        query["status"] = status
    
    items = await stock_transfers.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    total = await stock_transfers.count_documents(query)
    
    return {"items": items, "total": total}

@router.post("/transfer/{transfer_id}/send")
async def send_transfer(transfer_id: str, request: Request, user: dict = Depends(require_permission("stock_transfer", "edit"))):
    """Mark transfer as sent (in transit) - Requires stock_transfer.edit permission"""
    transfer = await stock_transfers.find_one({"id": transfer_id}, {"_id": 0})
    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer not found")
    
    if transfer.get("status") != "pending":
        raise HTTPException(status_code=400, detail="Transfer already processed")
    
    # Deduct stock from source
    for item in transfer.get("items", []):
        await product_stocks.update_one(
            {"product_id": item["product_id"], "branch_id": transfer["from_branch_id"]},
            {"$inc": {"quantity": -item["quantity"], "reserved": -item["quantity"]}}
        )
        
        movement = StockMovement(
            product_id=item["product_id"],
            branch_id=transfer["from_branch_id"],
            movement_type=StockMovementType.TRANSFER,
            quantity=-item["quantity"],
            reference_id=transfer_id,
            reference_type="transfer_out",
            to_branch_id=transfer["to_branch_id"],
            user_id=user.get("user_id", "")
        )
        await stock_movements.insert_one(movement.model_dump())
    
    await stock_transfers.update_one(
        {"id": transfer_id},
        {"$set": {
            "status": "in_transit",
            "sent_date": datetime.now(timezone.utc).isoformat(),
            "approved_by": user.get("user_id", "")
        }}
    )
    
    return {"message": "Transfer sent"}

@router.post("/transfer/{transfer_id}/receive")
async def receive_transfer(transfer_id: str, request: Request, user: dict = Depends(require_permission("stock_transfer", "edit"))):
    """Receive a transfer at destination branch - Requires stock_transfer.edit permission"""
    transfer = await stock_transfers.find_one({"id": transfer_id}, {"_id": 0})
    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer not found")
    
    if transfer.get("status") != "in_transit":
        raise HTTPException(status_code=400, detail="Transfer not in transit")
    
    # Add stock to destination
    for item in transfer.get("items", []):
        stock = await product_stocks.find_one(
            {"product_id": item["product_id"], "branch_id": transfer["to_branch_id"]}
        )
        
        if stock:
            await product_stocks.update_one(
                {"product_id": item["product_id"], "branch_id": transfer["to_branch_id"]},
                {"$inc": {"quantity": item["quantity"], "available": item["quantity"]}}
            )
        else:
            new_stock = ProductStock(
                product_id=item["product_id"],
                branch_id=transfer["to_branch_id"],
                quantity=item["quantity"],
                available=item["quantity"]
            )
            await product_stocks.insert_one(new_stock.model_dump())
        
        movement = StockMovement(
            product_id=item["product_id"],
            branch_id=transfer["to_branch_id"],
            movement_type=StockMovementType.TRANSFER,
            quantity=item["quantity"],
            reference_id=transfer_id,
            reference_type="transfer_in",
            from_branch_id=transfer["from_branch_id"],
            user_id=user.get("user_id", "")
        )
        await stock_movements.insert_one(movement.model_dump())
    
    await stock_transfers.update_one(
        {"id": transfer_id},
        {"$set": {
            "status": "received",
            "received_date": datetime.now(timezone.utc).isoformat(),
            "received_by": user.get("user_id", "")
        }}
    )
    
    return {"message": "Transfer received"}

# ==================== STOCK OPNAME ====================
# FINALIZED: Branch = Warehouse untuk operasional
# Flow: Pilih Cabang → Ambil stok dari stock_movements → Input fisik → Hitung selisih → Adjustment → Journal Entry

# Default Accounts untuk Stock Opname
OPNAME_ACCOUNTS = {
    "inventory": {"code": "1-1400", "name": "Persediaan Barang"},
    "adjustment_expense": {"code": "5-9100", "name": "Beban Selisih Persediaan"},  # Untuk selisih minus
    "adjustment_gain": {"code": "4-9100", "name": "Koreksi Persediaan"},  # Untuk selisih plus
}


@router.get("/opname/products")
async def get_products_for_opname(
    branch_id: str = "",
    search: str = "",
    user: dict = Depends(require_permission("stock_opname", "view"))
):
    """Get products with system stock for opname - stock calculated from stock_movements"""
    branch = branch_id or user.get("branch_id")
    if not branch:
        raise HTTPException(status_code=400, detail="Branch ID required")
    
    # Get all active products
    query = {"is_active": True}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"code": {"$regex": search, "$options": "i"}}
        ]
    
    all_products = await products.find(query, {"_id": 0}).to_list(1000)
    
    # Calculate stock from stock_movements (single source of truth)
    product_ids = [p["id"] for p in all_products]
    stock_map = await calculate_bulk_stock_from_movements(product_ids, branch)
    
    result = []
    for p in all_products:
        system_qty = stock_map.get(p["id"], 0)
        result.append({
            "product_id": p["id"],
            "product_code": p.get("code", ""),
            "product_name": p.get("name", ""),
            "unit": p.get("unit", "pcs"),
            "system_qty": system_qty,
            "cost_price": p.get("cost_price", 0)
        })
    
    return {"items": result, "branch_id": branch}


@router.post("/opname")
async def create_opname(data: CreateOpname, request: Request, user: dict = Depends(require_permission("stock_opname", "create"))):
    """Create stock opname (physical count) - stock from stock_movements"""
    branch_id = user.get("branch_id")
    if not branch_id:
        raise HTTPException(status_code=400, detail="User tidak terhubung ke cabang")
    
    opname_items = []
    
    for item in data.items:
        product = await products.find_one({"id": item.product_id}, {"_id": 0})
        if not product:
            continue
        
        # Get system stock from stock_movements (SINGLE SOURCE)
        system_qty = await calculate_stock_from_movements(item.product_id, branch_id)
        
        opname_items.append({
            "product_id": item.product_id,
            "product_code": product.get("code", ""),
            "product_name": product.get("name", ""),
            "unit": product.get("unit", "pcs"),
            "cost_price": product.get("cost_price", 0),
            "system_qty": system_qty,
            "actual_qty": item.actual_qty,
            "difference": item.actual_qty - system_qty
        })
    
    opname_number = await get_next_sequence("opname", "OPN")
    
    opname = StockOpname(
        opname_number=opname_number,
        branch_id=branch_id,
        items=opname_items,
        notes=data.notes,
        conducted_by=user.get("user_id", "")
    )
    
    await stock_opnames.insert_one(opname.model_dump())
    
    return {"id": opname.id, "opname_number": opname_number}


@router.post("/opname/{opname_id}/approve")
async def approve_opname(opname_id: str, request: Request, user: dict = Depends(require_permission("stock_opname", "approve"))):
    """
    Approve and apply stock opname adjustments
    - Creates stock_movement for each adjustment
    - Creates journal entry for accounting
    - Updates product_stocks (sync)
    """
    import uuid
    
    opname = await stock_opnames.find_one({"id": opname_id}, {"_id": 0})
    if not opname:
        raise HTTPException(status_code=404, detail="Opname tidak ditemukan")
    
    if opname.get("status") not in ["draft", "in_progress"]:
        raise HTTPException(status_code=400, detail="Opname sudah diproses")
    
    branch_id = opname["branch_id"]
    branch = await branches.find_one({"id": branch_id}, {"_id": 0})
    branch_name = branch.get("name", "Unknown") if branch else "Unknown"
    
    # Prepare totals for journal
    total_adjustment_expense = 0  # Selisih minus (stok hilang)
    total_adjustment_gain = 0     # Selisih plus (stok lebih)
    total_inventory_debit = 0
    total_inventory_credit = 0
    
    # Apply adjustments
    for item in opname.get("items", []):
        diff = item.get("difference", 0)
        if diff == 0:
            continue
        
        cost_price = item.get("cost_price", 0)
        value = abs(diff) * cost_price
        
        # Create stock movement
        if diff < 0:
            # SELISIH MINUS: Stok fisik < Stok sistem
            # Movement: Adjustment keluar (negative)
            movement_type = "opname_out"
            total_adjustment_expense += value
            total_inventory_credit += value
        else:
            # SELISIH PLUS: Stok fisik > Stok sistem
            # Movement: Adjustment masuk (positive)
            movement_type = "opname_in"
            total_adjustment_gain += value
            total_inventory_debit += value
        
        # Record movement (diff is already +/- based on actual - system)
        movement = {
            "id": str(uuid.uuid4()),
            "product_id": item["product_id"],
            "product_code": item.get("product_code", ""),
            "product_name": item.get("product_name", ""),
            "branch_id": branch_id,
            "movement_type": movement_type,
            "quantity": diff,  # Already +/- from actual - system
            "reference_id": opname_id,
            "reference_type": "stock_opname",
            "reference_number": opname.get("opname_number"),
            "cost_price": cost_price,
            "notes": f"Stock opname {opname.get('opname_number')}: {item.get('product_name')} ({item.get('system_qty')} → {item.get('actual_qty')})",
            "user_id": user.get("user_id", ""),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await stock_movements.insert_one(movement)
        
        # Sync product_stocks
        await sync_product_stock_from_movements(item["product_id"], branch_id)
    
    # Create journal entry if there are adjustments
    if total_adjustment_expense > 0 or total_adjustment_gain > 0:
        db = get_db()
        journal_id = str(uuid.uuid4())
        today = datetime.now(timezone.utc).strftime("%Y%m%d")
        
        # Use central number generator for journal
        from utils.number_generator import generate_transaction_number
        journal_number = await generate_transaction_number(db, "JV")
        
        entries = []
        
        # If there are losses (selisih minus)
        if total_adjustment_expense > 0:
            # Debit: Beban Selisih Persediaan
            entries.append({
                "account_code": OPNAME_ACCOUNTS["adjustment_expense"]["code"],
                "account_name": OPNAME_ACCOUNTS["adjustment_expense"]["name"],
                "debit": total_adjustment_expense,
                "credit": 0,
                "description": f"Selisih kurang persediaan - {opname.get('opname_number')}"
            })
            # Credit: Persediaan
            entries.append({
                "account_code": OPNAME_ACCOUNTS["inventory"]["code"],
                "account_name": OPNAME_ACCOUNTS["inventory"]["name"],
                "debit": 0,
                "credit": total_inventory_credit,
                "description": f"Penyesuaian persediaan kurang - {opname.get('opname_number')}"
            })
        
        # If there are gains (selisih plus)
        if total_adjustment_gain > 0:
            # Debit: Persediaan
            entries.append({
                "account_code": OPNAME_ACCOUNTS["inventory"]["code"],
                "account_name": OPNAME_ACCOUNTS["inventory"]["name"],
                "debit": total_inventory_debit,
                "credit": 0,
                "description": f"Penyesuaian persediaan lebih - {opname.get('opname_number')}"
            })
            # Credit: Koreksi Persediaan
            entries.append({
                "account_code": OPNAME_ACCOUNTS["adjustment_gain"]["code"],
                "account_name": OPNAME_ACCOUNTS["adjustment_gain"]["name"],
                "debit": 0,
                "credit": total_adjustment_gain,
                "description": f"Selisih lebih persediaan - {opname.get('opname_number')}"
            })
        
        total_debit = sum(e["debit"] for e in entries)
        total_credit = sum(e["credit"] for e in entries)
        
        journal = {
            "id": journal_id,
            "journal_number": journal_number,
            "journal_date": datetime.now(timezone.utc).isoformat(),
            "reference_type": "stock_opname",
            "reference_id": opname_id,
            "reference_number": opname.get("opname_number"),
            "description": f"Penyesuaian Stock Opname {opname.get('opname_number')} - {branch_name}",
            "branch_id": branch_id,
            "entries": entries,
            "total_debit": total_debit,
            "total_credit": total_credit,
            "is_balanced": abs(total_debit - total_credit) < 0.01,
            "status": "posted",
            "created_by": user.get("user_id", ""),
            "created_by_name": user.get("name", ""),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db["journal_entries"].insert_one(journal)
    
    # Update opname status
    await stock_opnames.update_one(
        {"id": opname_id},
        {"$set": {
            "status": "approved",
            "approved_by": user.get("user_id", ""),
            "approved_by_name": user.get("name", ""),
            "completed_date": datetime.now(timezone.utc).isoformat(),
            "journal_number": journal_number if (total_adjustment_expense > 0 or total_adjustment_gain > 0) else None,
            "total_adjustment_expense": total_adjustment_expense,
            "total_adjustment_gain": total_adjustment_gain
        }}
    )
    
    return {
        "message": "Stock opname disetujui dan stok disesuaikan",
        "opname_number": opname.get("opname_number"),
        "journal_number": journal_number if (total_adjustment_expense > 0 or total_adjustment_gain > 0) else None,
        "adjustment_expense": total_adjustment_expense,
        "adjustment_gain": total_adjustment_gain
    }

@router.get("/opnames")
async def list_opnames(
    search: str = "",
    status: str = "",
    skip: int = 0,
    limit: int = 50,
    user: dict = Depends(require_permission("stock_opname", "view"))
):
    """List stock opnames - Requires stock_opname.view permission"""
    query = {}
    
    branch_id = user.get("branch_id")
    if branch_id:
        query["branch_id"] = branch_id
    
    if status:
        query["status"] = status
    
    items = await stock_opnames.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    # Enrich with branch names and calculate totals
    for item in items:
        branch = await branches.find_one({"id": item.get("branch_id")}, {"_id": 0, "name": 1})
        item["branch_name"] = branch.get("name", "Unknown") if branch else "Unknown"
        item["total_items"] = len(item.get("items", []))
        item["total_difference"] = sum(i.get("difference", 0) for i in item.get("items", []))
    
    total = await stock_opnames.count_documents(query)
    
    return {"items": items, "total": total}

class CreateOpnameV2(BaseModel):
    branch_id: str
    notes: str = ""
    items: List[dict]

@router.post("/opnames")
async def create_opname_v2(data: CreateOpnameV2, request: Request, user: dict = Depends(require_permission("stock_opname", "create"))):
    """
    Create and auto-approve stock opname with journal entry
    Flow: Pilih Cabang → Stok dari stock_movements → Input fisik → Hitung selisih → Adjustment → Journal
    """
    import uuid
    
    branch_id = data.branch_id
    if not branch_id:
        raise HTTPException(status_code=400, detail="Branch ID required")
    
    branch = await branches.find_one({"id": branch_id}, {"_id": 0, "name": 1})
    if not branch:
        raise HTTPException(status_code=404, detail="Branch tidak ditemukan")
    
    branch_name = branch.get("name", "Unknown")
    
    opname_items = []
    
    for item in data.items:
        product = await products.find_one({"id": item.get("product_id")}, {"_id": 0})
        if not product:
            continue
        
        # Recalculate system_qty from stock_movements (SINGLE SOURCE)
        system_qty = await calculate_stock_from_movements(item.get("product_id"), branch_id)
        actual_qty = item.get("actual_qty", 0)
        
        opname_items.append({
            "product_id": item.get("product_id"),
            "product_code": product.get("code", ""),
            "product_name": product.get("name", ""),
            "unit": product.get("unit", "pcs"),
            "cost_price": product.get("cost_price", 0),
            "system_qty": system_qty,
            "actual_qty": actual_qty,
            "difference": actual_qty - system_qty
        })
    
    opname_number = await get_next_sequence("opname", "OPN")
    
    opname = StockOpname(
        opname_number=opname_number,
        branch_id=branch_id,
        items=opname_items,
        notes=data.notes,
        conducted_by=user.get("user_id", "")
    )
    
    await stock_opnames.insert_one(opname.model_dump())
    
    # Auto-approve with journal entry
    total_adjustment_expense = 0
    total_adjustment_gain = 0
    total_inventory_debit = 0
    total_inventory_credit = 0
    
    for item in opname_items:
        diff = item["difference"]
        if diff == 0:
            continue
        
        cost_price = item.get("cost_price", 0)
        value = abs(diff) * cost_price
        
        # Create stock movement
        if diff < 0:
            movement_type = "opname_out"
            total_adjustment_expense += value
            total_inventory_credit += value
        else:
            movement_type = "opname_in"
            total_adjustment_gain += value
            total_inventory_debit += value
        
        # Record stock movement
        movement = {
            "id": str(uuid.uuid4()),
            "product_id": item["product_id"],
            "product_code": item.get("product_code", ""),
            "product_name": item.get("product_name", ""),
            "branch_id": branch_id,
            "movement_type": movement_type,
            "quantity": diff,
            "reference_id": opname.id,
            "reference_type": "stock_opname",
            "reference_number": opname_number,
            "cost_price": cost_price,
            "notes": f"Stock opname {opname_number}: {item.get('product_name')} ({item.get('system_qty')} → {item.get('actual_qty')})",
            "user_id": user.get("user_id", ""),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await stock_movements.insert_one(movement)
        
        # Sync product_stocks
        await sync_product_stock_from_movements(item["product_id"], branch_id)
    
    # Create journal entry
    journal_number = None
    if total_adjustment_expense > 0 or total_adjustment_gain > 0:
        db = get_db()
        journal_id = str(uuid.uuid4())
        today = datetime.now(timezone.utc).strftime("%Y%m%d")
        
        # Use central number generator for journal
        from utils.number_generator import generate_transaction_number
        journal_number = await generate_transaction_number(db, "JV")
        
        entries = []
        
        # Selisih minus (stok hilang)
        if total_adjustment_expense > 0:
            entries.append({
                "account_code": OPNAME_ACCOUNTS["adjustment_expense"]["code"],
                "account_name": OPNAME_ACCOUNTS["adjustment_expense"]["name"],
                "debit": total_adjustment_expense,
                "credit": 0,
                "description": f"Selisih kurang persediaan - {opname_number}"
            })
            entries.append({
                "account_code": OPNAME_ACCOUNTS["inventory"]["code"],
                "account_name": OPNAME_ACCOUNTS["inventory"]["name"],
                "debit": 0,
                "credit": total_inventory_credit,
                "description": f"Penyesuaian persediaan kurang - {opname_number}"
            })
        
        # Selisih plus (stok lebih)
        if total_adjustment_gain > 0:
            entries.append({
                "account_code": OPNAME_ACCOUNTS["inventory"]["code"],
                "account_name": OPNAME_ACCOUNTS["inventory"]["name"],
                "debit": total_inventory_debit,
                "credit": 0,
                "description": f"Penyesuaian persediaan lebih - {opname_number}"
            })
            entries.append({
                "account_code": OPNAME_ACCOUNTS["adjustment_gain"]["code"],
                "account_name": OPNAME_ACCOUNTS["adjustment_gain"]["name"],
                "debit": 0,
                "credit": total_adjustment_gain,
                "description": f"Selisih lebih persediaan - {opname_number}"
            })
        
        total_debit = sum(e["debit"] for e in entries)
        total_credit = sum(e["credit"] for e in entries)
        
        journal = {
            "id": journal_id,
            "journal_number": journal_number,
            "journal_date": datetime.now(timezone.utc).isoformat(),
            "reference_type": "stock_opname",
            "reference_id": opname.id,
            "reference_number": opname_number,
            "description": f"Penyesuaian Stock Opname {opname_number} - {branch_name}",
            "branch_id": branch_id,
            "entries": entries,
            "total_debit": total_debit,
            "total_credit": total_credit,
            "is_balanced": abs(total_debit - total_credit) < 0.01,
            "status": "posted",
            "created_by": user.get("user_id", ""),
            "created_by_name": user.get("name", ""),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db["journal_entries"].insert_one(journal)
    
    # Update opname status
    await stock_opnames.update_one(
        {"id": opname.id},
        {"$set": {
            "status": "approved",
            "approved_by": user.get("user_id", ""),
            "approved_by_name": user.get("name", ""),
            "completed_date": datetime.now(timezone.utc).isoformat(),
            "journal_number": journal_number,
            "total_adjustment_expense": total_adjustment_expense,
            "total_adjustment_gain": total_adjustment_gain
        }}
    )
    
    return {
        "id": opname.id, 
        "opname_number": opname_number,
        "journal_number": journal_number,
        "message": "Stock opname berhasil disimpan dan adjustment diterapkan",
        "total_items": len(opname_items),
        "total_difference": sum(i["difference"] for i in opname_items),
        "adjustment_expense": total_adjustment_expense,
        "adjustment_gain": total_adjustment_gain
    }
