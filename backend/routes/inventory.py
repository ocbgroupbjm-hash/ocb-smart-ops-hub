# OCB TITAN - Inventory Management API
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from database import (
    products, product_stocks, stock_movements, stock_transfers, 
    stock_opnames, branches, get_next_sequence
)
from utils.auth import get_current_user
from models.titan_models import StockMovement, StockMovementType, StockTransfer, StockOpname, ProductStock
from datetime import datetime, timezone

router = APIRouter(prefix="/inventory", tags=["Inventory"])

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

@router.get("/stock")
async def get_branch_stock(
    branch_id: str = "",
    low_stock_only: bool = False,
    search: str = "",
    skip: int = 0,
    limit: int = 100,
    user: dict = Depends(get_current_user)
):
    """Get stock for a branch"""
    branch = branch_id or user.get("branch_id")
    
    # Get all products with stock
    pipeline = [
        {"$match": {"branch_id": branch}},
        {
            "$lookup": {
                "from": "products",
                "localField": "product_id",
                "foreignField": "id",
                "as": "product"
            }
        },
        {"$unwind": "$product"},
        {"$match": {"product.is_active": True}}
    ]
    
    if search:
        pipeline.append({
            "$match": {
                "$or": [
                    {"product.name": {"$regex": search, "$options": "i"}},
                    {"product.code": {"$regex": search, "$options": "i"}}
                ]
            }
        })
    
    if low_stock_only:
        pipeline.append({
            "$match": {
                "$expr": {"$lte": ["$quantity", "$product.min_stock"]}
            }
        })
    
    pipeline.extend([
        {"$sort": {"product.name": 1}},
        {"$skip": skip},
        {"$limit": limit},
        {
            "$project": {
                "_id": 0,
                "product_id": 1,
                "branch_id": 1,
                "quantity": 1,
                "available": 1,
                "reserved": 1,
                "product_code": "$product.code",
                "product_name": "$product.name",
                "min_stock": "$product.min_stock",
                "cost_price": "$product.cost_price",
                "selling_price": "$product.selling_price",
                "is_low_stock": {"$lte": ["$quantity", "$product.min_stock"]}
            }
        }
    ])
    
    items = await product_stocks.aggregate(pipeline).to_list(limit)
    
    # Count total
    count_pipeline = [
        {"$match": {"branch_id": branch}},
        {"$lookup": {"from": "products", "localField": "product_id", "foreignField": "id", "as": "product"}},
        {"$unwind": "$product"},
        {"$match": {"product.is_active": True}},
        {"$count": "total"}
    ]
    
    if low_stock_only:
        count_pipeline.insert(4, {"$match": {"$expr": {"$lte": ["$quantity", "$product.min_stock"]}}})
    
    count_result = await product_stocks.aggregate(count_pipeline).to_list(1)
    total = count_result[0]["total"] if count_result else 0
    
    return {"items": items, "total": total}

@router.get("/stock/low")
async def get_low_stock_alerts(user: dict = Depends(get_current_user)):
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
    user: dict = Depends(get_current_user)
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
        product = await products.find_one({"id": item["product_id"]}, {"_id": 0, "name": 1, "code": 1})
        item["product_name"] = product.get("name", "") if product else "Unknown"
        item["product_code"] = product.get("code", "") if product else ""
    
    total = await stock_movements.count_documents(query)
    
    return {"items": items, "total": total}

@router.post("/adjust")
async def adjust_stock(data: StockAdjustment, user: dict = Depends(get_current_user)):
    """Adjust stock quantity"""
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
async def stock_in(data: StockInOut, user: dict = Depends(get_current_user)):
    """Add stock (stock in)"""
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
async def stock_out(data: StockInOut, user: dict = Depends(get_current_user)):
    """Remove stock (stock out)"""
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
async def create_transfer(data: CreateTransfer, user: dict = Depends(get_current_user)):
    """Create a stock transfer request"""
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
    user: dict = Depends(get_current_user)
):
    """List stock transfers"""
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
async def send_transfer(transfer_id: str, user: dict = Depends(get_current_user)):
    """Mark transfer as sent (in transit)"""
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
async def receive_transfer(transfer_id: str, user: dict = Depends(get_current_user)):
    """Receive a transfer at destination branch"""
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

@router.post("/opname")
async def create_opname(data: CreateOpname, user: dict = Depends(get_current_user)):
    """Create stock opname (physical count)"""
    branch_id = user.get("branch_id")
    if not branch_id:
        raise HTTPException(status_code=400, detail="User not assigned to a branch")
    
    opname_items = []
    
    for item in data.items:
        product = await products.find_one({"id": item.product_id}, {"_id": 0})
        if not product:
            continue
        
        stock = await product_stocks.find_one(
            {"product_id": item.product_id, "branch_id": branch_id},
            {"_id": 0}
        )
        system_qty = stock.get("quantity", 0) if stock else 0
        
        opname_items.append({
            "product_id": item.product_id,
            "product_code": product.get("code", ""),
            "product_name": product.get("name", ""),
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
async def approve_opname(opname_id: str, user: dict = Depends(get_current_user)):
    """Approve and apply stock opname adjustments"""
    opname = await stock_opnames.find_one({"id": opname_id}, {"_id": 0})
    if not opname:
        raise HTTPException(status_code=404, detail="Opname not found")
    
    if opname.get("status") not in ["draft", "in_progress"]:
        raise HTTPException(status_code=400, detail="Opname already processed")
    
    # Apply adjustments
    for item in opname.get("items", []):
        if item["difference"] != 0:
            await product_stocks.update_one(
                {"product_id": item["product_id"], "branch_id": opname["branch_id"]},
                {"$set": {
                    "quantity": item["actual_qty"],
                    "available": item["actual_qty"],
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            
            movement = StockMovement(
                product_id=item["product_id"],
                branch_id=opname["branch_id"],
                movement_type=StockMovementType.OPNAME,
                quantity=item["difference"],
                reference_id=opname_id,
                reference_type="opname",
                notes=f"Stock opname adjustment: {opname.get('opname_number')}",
                user_id=user.get("user_id", "")
            )
            await stock_movements.insert_one(movement.model_dump())
    
    await stock_opnames.update_one(
        {"id": opname_id},
        {"$set": {
            "status": "approved",
            "approved_by": user.get("user_id", ""),
            "completed_date": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"message": "Opname approved and stock adjusted"}
