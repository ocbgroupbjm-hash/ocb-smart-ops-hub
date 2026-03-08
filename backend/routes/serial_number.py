# OCB AI TITAN - Serial Number Tracking Routes
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
from database import db
from utils.auth import get_current_user
import uuid

router = APIRouter(prefix="/api/serial", tags=["Serial Number"])

serial_numbers_collection = db["serial_numbers"]
products_collection = db["products"]

class SerialNumber(BaseModel):
    serial: str
    product_id: str
    product_name: Optional[str] = None
    product_code: Optional[str] = None
    status: str = "available"  # available, sold, returned, damaged, reserved
    cost_price: float = 0
    selling_price: float = 0
    warranty_until: Optional[str] = None
    notes: Optional[str] = None
    branch_id: Optional[str] = None

class SerialMovement(BaseModel):
    serial_id: str
    movement_type: str  # purchase_in, sale_out, transfer, return, adjustment
    reference_id: Optional[str] = None
    reference_type: Optional[str] = None  # po, transaction, transfer
    from_branch: Optional[str] = None
    to_branch: Optional[str] = None
    notes: Optional[str] = None

@router.get("/list")
async def list_serial_numbers(
    product_id: str = "",
    status: str = "",
    branch_id: str = "",
    search: str = "",
    skip: int = 0,
    limit: int = 50,
    user: dict = Depends(get_current_user)
):
    """List all serial numbers with filters"""
    query = {}
    if product_id:
        query["product_id"] = product_id
    if status:
        query["status"] = status
    if branch_id:
        query["branch_id"] = branch_id
    if search:
        query["$or"] = [
            {"serial": {"$regex": search, "$options": "i"}},
            {"product_name": {"$regex": search, "$options": "i"}}
        ]
    
    total = await serial_numbers_collection.count_documents(query)
    items = await serial_numbers_collection.find(query, {"_id": 0}).skip(skip).limit(limit).sort("created_at", -1).to_list(limit)
    
    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit
    }

@router.post("/add")
async def add_serial_number(data: SerialNumber, user: dict = Depends(get_current_user)):
    """Add new serial number"""
    # Check if serial already exists
    existing = await serial_numbers_collection.find_one({"serial": data.serial})
    if existing:
        raise HTTPException(status_code=400, detail="Serial number sudah ada")
    
    # Get product info
    product = await products_collection.find_one({"id": data.product_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Produk tidak ditemukan")
    
    serial_data = data.dict()
    serial_data["id"] = str(uuid.uuid4())
    serial_data["product_name"] = product.get("name")
    serial_data["product_code"] = product.get("code")
    serial_data["branch_id"] = user.get("branch_id") if not data.branch_id else data.branch_id
    serial_data["created_at"] = datetime.now(timezone.utc).isoformat()
    serial_data["created_by"] = user.get("name")
    
    await serial_numbers_collection.insert_one(serial_data)
    
    return {"id": serial_data["id"], "message": "Serial number berhasil ditambahkan"}

@router.post("/bulk-add")
async def bulk_add_serial_numbers(
    product_id: str,
    prefix: str,
    start_number: int,
    count: int,
    user: dict = Depends(get_current_user)
):
    """Bulk add serial numbers with prefix and sequence"""
    # Get product info
    product = await products_collection.find_one({"id": product_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Produk tidak ditemukan")
    
    added = 0
    for i in range(count):
        serial = f"{prefix}{str(start_number + i).zfill(6)}"
        
        # Skip if exists
        existing = await serial_numbers_collection.find_one({"serial": serial})
        if existing:
            continue
        
        serial_data = {
            "id": str(uuid.uuid4()),
            "serial": serial,
            "product_id": product_id,
            "product_name": product.get("name"),
            "product_code": product.get("code"),
            "status": "available",
            "branch_id": user.get("branch_id"),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": user.get("name")
        }
        await serial_numbers_collection.insert_one(serial_data)
        added += 1
    
    return {"message": f"{added} serial number berhasil ditambahkan"}

@router.put("/{serial_id}")
async def update_serial_number(serial_id: str, data: SerialNumber, user: dict = Depends(get_current_user)):
    """Update serial number"""
    update_data = data.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    update_data["updated_by"] = user.get("name")
    
    result = await serial_numbers_collection.update_one(
        {"id": serial_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Serial number tidak ditemukan")
    
    return {"message": "Serial number berhasil diupdate"}

@router.put("/{serial_id}/status")
async def update_serial_status(
    serial_id: str,
    status: str,
    notes: str = "",
    user: dict = Depends(get_current_user)
):
    """Update serial number status"""
    valid_statuses = ["available", "sold", "returned", "damaged", "reserved"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Status tidak valid")
    
    # Record movement
    serial = await serial_numbers_collection.find_one({"id": serial_id}, {"_id": 0})
    if serial:
        movement = {
            "id": str(uuid.uuid4()),
            "serial_id": serial_id,
            "serial": serial.get("serial"),
            "old_status": serial.get("status"),
            "new_status": status,
            "notes": notes,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": user.get("name")
        }
        await db["serial_movements"].insert_one(movement)
    
    result = await serial_numbers_collection.update_one(
        {"id": serial_id},
        {"$set": {
            "status": status,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "updated_by": user.get("name")
        }}
    )
    
    return {"message": "Status serial number berhasil diupdate"}

@router.delete("/{serial_id}")
async def delete_serial_number(serial_id: str, user: dict = Depends(get_current_user)):
    """Delete serial number"""
    if user.get("role") not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Tidak diizinkan")
    
    result = await serial_numbers_collection.delete_one({"id": serial_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Serial number tidak ditemukan")
    
    return {"message": "Serial number berhasil dihapus"}

@router.get("/history/{serial_id}")
async def get_serial_history(serial_id: str, user: dict = Depends(get_current_user)):
    """Get serial number movement history"""
    movements = await db["serial_movements"].find(
        {"serial_id": serial_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return {"movements": movements}

@router.get("/lookup/{serial}")
async def lookup_serial(serial: str, user: dict = Depends(get_current_user)):
    """Lookup serial number details"""
    serial_doc = await serial_numbers_collection.find_one({"serial": serial}, {"_id": 0})
    if not serial_doc:
        raise HTTPException(status_code=404, detail="Serial number tidak ditemukan")
    
    # Get movement history
    movements = await db["serial_movements"].find(
        {"serial_id": serial_doc["id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    
    serial_doc["history"] = movements
    return serial_doc

@router.get("/available/{product_id}")
async def get_available_serials(product_id: str, user: dict = Depends(get_current_user)):
    """Get available serial numbers for a product"""
    branch_id = user.get("branch_id")
    serials = await serial_numbers_collection.find(
        {
            "product_id": product_id,
            "status": "available",
            "branch_id": branch_id
        },
        {"_id": 0}
    ).to_list(500)
    
    return {"serials": serials, "count": len(serials)}
