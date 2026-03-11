"""
OCB TITAN ERP - PHASE 3 OPERATIONAL CONTROL SYSTEM
Module 4: WAREHOUSE CONTROL
Following OCB TITAN AI MASTER LAW - NON-DESTRUCTIVE Development

Reference: iPOS Ultimate multi-gudang concept

Features:
1. Multi-Warehouse Management per Branch
2. Stock Transfer between Warehouses
3. Warehouse-level Stock Tracking
4. Transfer Request & Approval Flow
5. Stock Movement History per Warehouse
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from database import get_db as get_database
from routes.auth import get_current_user
from routes.rbac_middleware import require_permission
import uuid

router = APIRouter(prefix="/api/warehouse", tags=["Warehouse Control"])

# ==================== PYDANTIC MODELS ====================

class WarehouseCreate(BaseModel):
    name: str
    code: str
    branch_id: str
    address: Optional[str] = ""
    type: str = "storage"  # storage, retail, distribution
    is_default: bool = False

class WarehouseUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    type: Optional[str] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None

class StockTransferRequest(BaseModel):
    source_warehouse_id: str
    destination_warehouse_id: str
    items: List[Dict[str, Any]]  # [{product_id, quantity, notes}]
    transfer_reason: str
    requested_date: Optional[str] = None

class StockTransferAction(BaseModel):
    action: str  # approve, reject, complete, cancel
    notes: Optional[str] = ""

# ==================== HELPER FUNCTIONS ====================

async def get_warehouse_stock(db, warehouse_id: str, product_id: str = None) -> Dict[str, Any]:
    """Get stock levels for a warehouse"""
    
    query = {"warehouse_id": warehouse_id}
    if product_id:
        query["product_id"] = product_id
    
    pipeline = [
        {"$match": query},
        {"$group": {
            "_id": "$product_id",
            "total_in": {"$sum": {"$cond": [{"$eq": ["$movement_type", "in"]}, "$quantity", 0]}},
            "total_out": {"$sum": {"$cond": [{"$eq": ["$movement_type", "out"]}, "$quantity", 0]}}
        }}
    ]
    
    result = await db.stock_movements.aggregate(pipeline).to_list(500)
    
    stock_data = {}
    for item in result:
        stock_data[item["_id"]] = item["total_in"] - item["total_out"]
    
    return stock_data

async def generate_transfer_number(db) -> str:
    """Generate unique transfer number"""
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    count = await db.stock_transfers.count_documents({"transfer_no": {"$regex": f"^TRF-{today}"}})
    return f"TRF-{today}-{str(count + 1).zfill(4)}"

# ==================== WAREHOUSE CRUD ====================

@router.post("")
async def create_warehouse(
    data: WarehouseCreate,
    user: dict = Depends(require_permission("warehouse", "create"))
):
    """Create a new warehouse"""
    db = get_database()
    
    # Check duplicate code
    existing = await db.warehouses.find_one({"code": data.code, "branch_id": data.branch_id})
    if existing:
        raise HTTPException(status_code=400, detail="Kode gudang sudah digunakan di cabang ini")
    
    # If setting as default, unset other defaults
    if data.is_default:
        await db.warehouses.update_many(
            {"branch_id": data.branch_id, "is_default": True},
            {"$set": {"is_default": False}}
        )
    
    warehouse = {
        "id": str(uuid.uuid4()),
        "code": data.code,
        "name": data.name,
        "branch_id": data.branch_id,
        "address": data.address,
        "type": data.type,
        "is_default": data.is_default,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user.get("user_id")
    }
    
    await db.warehouses.insert_one(warehouse)
    
    # Audit log
    await db.audit_logs.insert_one({
        "id": str(uuid.uuid4()),
        "action": "warehouse_create",
        "module": "warehouse",
        "target_id": warehouse["id"],
        "target_name": data.name,
        "description": f"Gudang baru: {data.name} ({data.code})",
        "user_id": user.get("user_id"),
        "user_name": user.get("name"),
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    return {"success": True, "warehouse_id": warehouse["id"], "message": f"Gudang {data.name} berhasil dibuat"}

@router.get("")
async def list_warehouses(
    branch_id: Optional[str] = None,
    is_active: Optional[bool] = True,
    user: dict = Depends(get_current_user)
):
    """List all warehouses"""
    db = get_database()
    
    query = {}
    if branch_id:
        query["branch_id"] = branch_id
    if is_active is not None:
        query["is_active"] = is_active
    
    warehouses = await db.warehouses.find(query, {"_id": 0}).to_list(100)
    
    # Add stock count to each warehouse
    for wh in warehouses:
        stock = await get_warehouse_stock(db, wh["id"])
        wh["total_products"] = len(stock)
        wh["total_stock_items"] = sum(stock.values())
    
    return {"items": warehouses, "total": len(warehouses)}

@router.get("/transfers")
async def list_stock_transfers(
    status: Optional[str] = None,
    source_warehouse_id: Optional[str] = None,
    destination_warehouse_id: Optional[str] = None,
    limit: int = 50,
    user: dict = Depends(get_current_user)
):
    """List stock transfers"""
    db = get_database()
    
    query = {}
    if status:
        query["status"] = status
    if source_warehouse_id:
        query["source_warehouse_id"] = source_warehouse_id
    if destination_warehouse_id:
        query["destination_warehouse_id"] = destination_warehouse_id
    
    transfers = await db.stock_transfers.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    
    return {"items": transfers, "total": len(transfers)}

@router.get("/{warehouse_id}")
async def get_warehouse(
    warehouse_id: str,
    user: dict = Depends(get_current_user)
):
    """Get warehouse details"""
    db = get_database()
    
    warehouse = await db.warehouses.find_one({"id": warehouse_id}, {"_id": 0})
    if not warehouse:
        raise HTTPException(status_code=404, detail="Gudang tidak ditemukan")
    
    # Get stock summary
    stock = await get_warehouse_stock(db, warehouse_id)
    warehouse["stock_summary"] = {
        "total_products": len(stock),
        "total_stock_items": sum(stock.values())
    }
    
    return warehouse

@router.put("/{warehouse_id}")
async def update_warehouse(
    warehouse_id: str,
    data: WarehouseUpdate,
    user: dict = Depends(require_permission("warehouse", "edit"))
):
    """Update warehouse"""
    db = get_database()
    
    warehouse = await db.warehouses.find_one({"id": warehouse_id})
    if not warehouse:
        raise HTTPException(status_code=404, detail="Gudang tidak ditemukan")
    
    update_data = {k: v for k, v in data.dict().items() if v is not None}
    
    # If setting as default
    if update_data.get("is_default"):
        await db.warehouses.update_many(
            {"branch_id": warehouse["branch_id"], "is_default": True},
            {"$set": {"is_default": False}}
        )
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    update_data["updated_by"] = user.get("user_id")
    
    await db.warehouses.update_one({"id": warehouse_id}, {"$set": update_data})
    
    return {"success": True, "message": "Gudang berhasil diupdate"}

@router.get("/{warehouse_id}/stock")
async def get_warehouse_stock_list(
    warehouse_id: str,
    category: Optional[str] = None,
    low_stock_only: bool = False,
    user: dict = Depends(get_current_user)
):
    """Get detailed stock list for a warehouse"""
    db = get_database()
    
    # Verify warehouse exists
    warehouse = await db.warehouses.find_one({"id": warehouse_id}, {"_id": 0})
    if not warehouse:
        raise HTTPException(status_code=404, detail="Gudang tidak ditemukan")
    
    # Get stock levels
    pipeline = [
        {"$match": {"warehouse_id": warehouse_id}},
        {"$group": {
            "_id": "$product_id",
            "total_in": {"$sum": {"$cond": [{"$eq": ["$movement_type", "in"]}, "$quantity", 0]}},
            "total_out": {"$sum": {"$cond": [{"$eq": ["$movement_type", "out"]}, "$quantity", 0]}},
            "last_movement": {"$max": "$created_at"}
        }}
    ]
    
    movements = await db.stock_movements.aggregate(pipeline).to_list(500)
    
    # Enrich with product info
    products = await db.products.find({}, {"_id": 0}).to_list(500)
    product_map = {p["id"]: p for p in products}
    
    stock_list = []
    for m in movements:
        product = product_map.get(m["_id"], {})
        current_stock = m["total_in"] - m["total_out"]
        
        if category and product.get("category") != category:
            continue
        
        min_stock = product.get("minimum_stock", 0)
        if low_stock_only and current_stock > min_stock:
            continue
        
        stock_list.append({
            "product_id": m["_id"],
            "product_code": product.get("code", ""),
            "product_name": product.get("name", ""),
            "category": product.get("category", ""),
            "unit": product.get("unit", "pcs"),
            "current_stock": current_stock,
            "minimum_stock": min_stock,
            "maximum_stock": product.get("maximum_stock", 0),
            "is_low_stock": current_stock <= min_stock if min_stock > 0 else False,
            "last_movement": m["last_movement"]
        })
    
    stock_list.sort(key=lambda x: x["product_name"])
    
    return {
        "warehouse": warehouse,
        "items": stock_list,
        "total": len(stock_list),
        "low_stock_count": sum(1 for s in stock_list if s["is_low_stock"])
    }

# ==================== STOCK TRANSFER ====================

@router.post("/transfer")
async def create_stock_transfer(
    data: StockTransferRequest,
    user: dict = Depends(require_permission("stock_transfer", "create"))
):
    """Create a stock transfer request"""
    db = get_database()
    
    # Validate warehouses
    source = await db.warehouses.find_one({"id": data.source_warehouse_id}, {"_id": 0})
    dest = await db.warehouses.find_one({"id": data.destination_warehouse_id}, {"_id": 0})
    
    if not source:
        raise HTTPException(status_code=404, detail="Gudang asal tidak ditemukan")
    if not dest:
        raise HTTPException(status_code=404, detail="Gudang tujuan tidak ditemukan")
    if source["id"] == dest["id"]:
        raise HTTPException(status_code=400, detail="Gudang asal dan tujuan tidak boleh sama")
    
    # Validate stock availability
    source_stock = await get_warehouse_stock(db, data.source_warehouse_id)
    
    validated_items = []
    for item in data.items:
        product_id = item.get("product_id")
        qty = item.get("quantity", 0)
        
        product = await db.products.find_one({"id": product_id}, {"_id": 0, "name": 1, "code": 1, "unit": 1})
        if not product:
            raise HTTPException(status_code=404, detail=f"Produk {product_id} tidak ditemukan")
        
        available = source_stock.get(product_id, 0)
        if qty > available:
            raise HTTPException(
                status_code=400, 
                detail=f"Stok {product['name']} tidak cukup. Tersedia: {available}, Diminta: {qty}"
            )
        
        validated_items.append({
            "product_id": product_id,
            "product_code": product.get("code", ""),
            "product_name": product.get("name", ""),
            "unit": product.get("unit", "pcs"),
            "quantity": qty,
            "notes": item.get("notes", "")
        })
    
    transfer_no = await generate_transfer_number(db)
    
    transfer = {
        "id": str(uuid.uuid4()),
        "transfer_no": transfer_no,
        "source_warehouse_id": data.source_warehouse_id,
        "source_warehouse_name": source["name"],
        "destination_warehouse_id": data.destination_warehouse_id,
        "destination_warehouse_name": dest["name"],
        "items": validated_items,
        "total_items": len(validated_items),
        "total_quantity": sum(i["quantity"] for i in validated_items),
        "transfer_reason": data.transfer_reason,
        "requested_date": data.requested_date or datetime.now(timezone.utc).isoformat(),
        "status": "pending",  # pending, approved, in_transit, completed, rejected, cancelled
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user.get("user_id"),
        "created_by_name": user.get("name")
    }
    
    await db.stock_transfers.insert_one(transfer)
    
    # Audit log
    await db.audit_logs.insert_one({
        "id": str(uuid.uuid4()),
        "action": "stock_transfer_create",
        "module": "warehouse",
        "target_id": transfer["id"],
        "target_name": transfer_no,
        "description": f"Transfer request {transfer_no}: {source['name']} -> {dest['name']} ({len(validated_items)} items)",
        "user_id": user.get("user_id"),
        "user_name": user.get("name"),
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    return {
        "success": True,
        "transfer_id": transfer["id"],
        "transfer_no": transfer_no,
        "status": "pending",
        "message": f"Transfer request {transfer_no} berhasil dibuat"
    }

@router.get("/transfer/{transfer_id}")
async def get_stock_transfer(
    transfer_id: str,
    user: dict = Depends(get_current_user)
):
    """Get transfer details"""
    db = get_database()
    
    transfer = await db.stock_transfers.find_one({"id": transfer_id}, {"_id": 0})
    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer tidak ditemukan")
    
    return transfer

@router.post("/transfer/{transfer_id}/action")
async def process_transfer_action(
    transfer_id: str,
    data: StockTransferAction,
    user: dict = Depends(require_permission("stock_transfer", "approve"))
):
    """Process transfer action (approve, reject, complete, cancel)"""
    db = get_database()
    
    transfer = await db.stock_transfers.find_one({"id": transfer_id})
    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer tidak ditemukan")
    
    current_status = transfer["status"]
    new_status = current_status
    
    valid_transitions = {
        "pending": ["approved", "rejected", "cancelled"],
        "approved": ["in_transit", "cancelled"],
        "in_transit": ["completed", "cancelled"]
    }
    
    action_status_map = {
        "approve": "approved",
        "reject": "rejected",
        "complete": "completed",
        "cancel": "cancelled"
    }
    
    target_status = action_status_map.get(data.action)
    if not target_status:
        raise HTTPException(status_code=400, detail=f"Action tidak valid: {data.action}")
    
    if target_status not in valid_transitions.get(current_status, []):
        raise HTTPException(
            status_code=400, 
            detail=f"Tidak dapat melakukan {data.action} dari status {current_status}"
        )
    
    new_status = target_status
    
    update_data = {
        "status": new_status,
        f"{data.action}_at": datetime.now(timezone.utc).isoformat(),
        f"{data.action}_by": user.get("user_id"),
        f"{data.action}_by_name": user.get("name"),
        f"{data.action}_notes": data.notes
    }
    
    # If completing, create stock movements
    if data.action == "complete":
        for item in transfer["items"]:
            # Out from source
            await db.stock_movements.insert_one({
                "id": str(uuid.uuid4()),
                "product_id": item["product_id"],
                "warehouse_id": transfer["source_warehouse_id"],
                "branch_id": transfer.get("source_branch_id"),
                "movement_type": "out",
                "quantity": item["quantity"],
                "reference_type": "transfer",
                "reference_id": transfer_id,
                "reference_no": transfer["transfer_no"],
                "notes": f"Transfer ke {transfer['destination_warehouse_name']}",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "created_by": user.get("user_id")
            })
            
            # In to destination
            await db.stock_movements.insert_one({
                "id": str(uuid.uuid4()),
                "product_id": item["product_id"],
                "warehouse_id": transfer["destination_warehouse_id"],
                "branch_id": transfer.get("destination_branch_id"),
                "movement_type": "in",
                "quantity": item["quantity"],
                "reference_type": "transfer",
                "reference_id": transfer_id,
                "reference_no": transfer["transfer_no"],
                "notes": f"Transfer dari {transfer['source_warehouse_name']}",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "created_by": user.get("user_id")
            })
        
        update_data["completed_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.stock_transfers.update_one({"id": transfer_id}, {"$set": update_data})
    
    # Audit log
    await db.audit_logs.insert_one({
        "id": str(uuid.uuid4()),
        "action": f"stock_transfer_{data.action}",
        "module": "warehouse",
        "target_id": transfer_id,
        "target_name": transfer["transfer_no"],
        "description": f"Transfer {transfer['transfer_no']}: {current_status} -> {new_status}. Notes: {data.notes}",
        "user_id": user.get("user_id"),
        "user_name": user.get("name"),
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    return {
        "success": True,
        "transfer_id": transfer_id,
        "transfer_no": transfer["transfer_no"],
        "old_status": current_status,
        "new_status": new_status,
        "message": f"Transfer berhasil di-{data.action}"
    }

# ==================== DASHBOARD ====================

@router.get("/dashboard/summary")
async def get_warehouse_dashboard(
    branch_id: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Get warehouse dashboard summary"""
    db = get_database()
    
    # Get warehouses
    query = {"is_active": True}
    if branch_id:
        query["branch_id"] = branch_id
    
    warehouses = await db.warehouses.find(query, {"_id": 0}).to_list(100)
    
    # Enrich with stock data
    for wh in warehouses:
        stock = await get_warehouse_stock(db, wh["id"])
        wh["total_products"] = len(stock)
        wh["total_stock"] = sum(stock.values())
    
    # Get pending transfers
    pending_transfers = await db.stock_transfers.count_documents({"status": "pending"})
    in_transit = await db.stock_transfers.count_documents({"status": "in_transit"})
    
    # Get recent transfers
    recent_transfers = await db.stock_transfers.find({}, {"_id": 0}).sort("created_at", -1).limit(5).to_list(5)
    
    return {
        "warehouses": warehouses,
        "total_warehouses": len(warehouses),
        "pending_transfers": pending_transfers,
        "in_transit_transfers": in_transit,
        "recent_transfers": recent_transfers
    }
