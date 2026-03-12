"""
OCB TITAN ERP - PHASE 3 OPERATIONAL CONTROL SYSTEM
Module 5: PURCHASE PLANNING ENGINE
Following OCB TITAN AI MASTER LAW - NON-DESTRUCTIVE Development

Fitur:
1. Forecast purchasing berdasarkan sales history
2. Supplier lead time integration
3. Rekomendasi qty pembelian
4. Rekomendasi supplier
5. Rekomendasi tanggal order
6. Status planning: draft / reviewed / approved

Data Sources:
- stock_movements (SSOT)
- stock_reorder / reorder suggestions
- purchase history
- sales history
- supplier master
- warehouse stock
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

router = APIRouter(prefix="/api/purchase-planning", tags=["Purchase Planning Engine"])

# ==================== CONSTANTS ====================

PLANNING_STATUS = {
    "draft": {"name": "Draft", "color": "gray"},
    "reviewed": {"name": "Reviewed", "color": "blue"},
    "approved": {"name": "Approved", "color": "green"},
    "po_created": {"name": "PO Created", "color": "purple"},
    "cancelled": {"name": "Cancelled", "color": "red"}
}

DEFAULT_LEAD_TIME_DAYS = 7
DEFAULT_VELOCITY_PERIOD = 30
DEFAULT_SAFETY_DAYS = 7

# ==================== PYDANTIC MODELS ====================

class PlanningGenerateRequest(BaseModel):
    branch_id: Optional[str] = None
    warehouse_id: Optional[str] = None
    category: Optional[str] = None
    supplier_id: Optional[str] = None
    include_all_low_stock: bool = True

class PlanningItemUpdate(BaseModel):
    recommended_qty: Optional[float] = None
    supplier_id: Optional[str] = None
    suggested_order_date: Optional[str] = None
    notes: Optional[str] = None

class PlanningStatusUpdate(BaseModel):
    status: str  # draft, reviewed, approved, cancelled
    notes: Optional[str] = ""

class CreatePOFromPlanning(BaseModel):
    planning_ids: List[str]
    supplier_id: Optional[str] = None

# ==================== HELPER FUNCTIONS ====================

async def get_sales_velocity(db, product_id: str, branch_id: str = None, days: int = DEFAULT_VELOCITY_PERIOD) -> float:
    """Calculate average daily sales velocity"""
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
        {"$group": {"_id": None, "total_sold": {"$sum": "$quantity"}}}
    ]
    
    result = await db.stock_movements.aggregate(pipeline).to_list(1)
    total_sold = result[0]["total_sold"] if result else 0
    
    return round(total_sold / days, 2)

async def get_current_stock(db, product_id: str, branch_id: str = None, warehouse_id: str = None) -> float:
    """Get current stock from stock_movements (SSOT)"""
    query = {"product_id": product_id}
    if branch_id:
        query["branch_id"] = branch_id
    if warehouse_id:
        query["warehouse_id"] = warehouse_id
    
    pipeline = [
        {"$match": query},
        {"$group": {
            "_id": None,
            "total_in": {"$sum": {"$cond": [{"$eq": ["$movement_type", "in"]}, "$quantity", 0]}},
            "total_out": {"$sum": {"$cond": [{"$eq": ["$movement_type", "out"]}, "$quantity", 0]}}
        }}
    ]
    
    result = await db.stock_movements.aggregate(pipeline).to_list(1)
    if not result:
        return 0
    
    return result[0]["total_in"] - result[0]["total_out"]

async def get_open_po_qty(db, product_id: str, supplier_id: str = None) -> float:
    """Get quantity from open POs (not yet received)"""
    query = {
        "items.product_id": product_id,
        "status": {"$in": ["pending", "approved", "partial"]}
    }
    if supplier_id:
        query["supplier_id"] = supplier_id
    
    pipeline = [
        {"$match": query},
        {"$unwind": "$items"},
        {"$match": {"items.product_id": product_id}},
        {"$group": {
            "_id": None,
            "total_ordered": {"$sum": "$items.quantity"},
            "total_received": {"$sum": {"$ifNull": ["$items.received_qty", 0]}}
        }}
    ]
    
    result = await db.purchase_orders.aggregate(pipeline).to_list(1)
    if not result:
        return 0
    
    return result[0]["total_ordered"] - result[0]["total_received"]

async def get_supplier_info(db, supplier_id: str) -> Dict[str, Any]:
    """Get supplier information including lead time"""
    supplier = await db.suppliers.find_one({"id": supplier_id}, {"_id": 0})
    return supplier

async def calculate_planning_recommendation(db, product_id: str, branch_id: str = None, warehouse_id: str = None) -> Dict[str, Any]:
    """Calculate purchase planning recommendation for a product"""
    
    # Get product info
    product = await products.find_one({"id": product_id}, {"_id": 0})
    if not product:
        return None
    
    # Get stock settings
    settings = await db.stock_settings.find_one({"product_id": product_id}, {"_id": 0})
    
    # Get values
    min_stock = (settings or {}).get("minimum_stock", product.get("minimum_stock", 0))
    max_stock = (settings or {}).get("maximum_stock", product.get("maximum_stock", 0))
    lead_time = (settings or {}).get("lead_time_days", DEFAULT_LEAD_TIME_DAYS)
    
    # Get supplier - priority: stock_settings.preferred_supplier_id > product.supplier_id > last_po_supplier
    supplier_id = (settings or {}).get("preferred_supplier_id") or product.get("supplier_id")
    
    # Fallback: get supplier from last purchase order for this product
    if not supplier_id:
        last_po = await db.purchase_orders.find_one(
            {"items.product_id": product_id, "status": {"$in": ["completed", "partial", "approved"]}},
            {"_id": 0, "supplier_id": 1, "supplier_name": 1},
            sort=[("created_at", -1)]
        )
        if last_po and last_po.get("supplier_id"):
            supplier_id = last_po["supplier_id"]
    
    # Get supplier info
    supplier = await get_supplier_info(db, supplier_id) if supplier_id else None
    if supplier:
        lead_time = supplier.get("lead_time_days", lead_time)
    
    # Get current stock
    current_stock = await get_current_stock(db, product_id, branch_id, warehouse_id)
    
    # Get sales velocity
    velocity = await get_sales_velocity(db, product_id, branch_id)
    
    # Get open PO quantity
    open_po_qty = await get_open_po_qty(db, product_id, supplier_id)
    
    # Calculate reorder point
    safety_stock = velocity * DEFAULT_SAFETY_DAYS
    reorder_point = (velocity * lead_time) + safety_stock
    
    # Calculate effective stock (including pending POs)
    effective_stock = current_stock + open_po_qty
    
    # Calculate recommended order qty
    recommended_qty = 0
    needs_planning = False
    
    if effective_stock <= reorder_point and max_stock > 0:
        recommended_qty = max_stock - effective_stock
        needs_planning = True
    elif effective_stock <= min_stock and min_stock > 0:
        recommended_qty = (min_stock * 2) - effective_stock
        needs_planning = True
    
    # Calculate suggested order date - more realistic calculation
    if velocity > 0:
        days_until_stockout = current_stock / velocity
        # Order date should be: stockout date - lead_time, but at least today
        days_to_order = max(0, days_until_stockout - lead_time)
        # Cap at 30 days max in the future
        days_to_order = min(days_to_order, 30)
    else:
        # No velocity = no urgency, suggest order in 7 days
        days_until_stockout = 999
        days_to_order = 7
    
    suggested_order_date = (datetime.now(timezone.utc) + timedelta(days=int(days_to_order))).strftime("%Y-%m-%d")
    
    # Determine urgency
    urgency = "none"
    if current_stock <= 0:
        urgency = "critical"
    elif min_stock > 0 and current_stock <= min_stock * 0.5:
        urgency = "critical"
    elif min_stock > 0 and current_stock <= min_stock:
        urgency = "high"
    elif reorder_point > 0 and current_stock <= reorder_point:
        urgency = "medium"
    
    return {
        "product_id": product_id,
        "product_code": product.get("code", ""),
        "product_name": product.get("name", ""),
        "category": product.get("category", ""),
        "unit": product.get("unit", "pcs"),
        "branch_id": branch_id,
        "warehouse_id": warehouse_id,
        "current_stock": current_stock,
        "minimum_stock": min_stock,
        "maximum_stock": max_stock,
        "reorder_point": round(reorder_point, 2),
        "safety_stock": round(safety_stock, 2),
        "sales_velocity": velocity,
        "lead_time_days": lead_time,
        "open_po_qty": open_po_qty,
        "effective_stock": effective_stock,
        "recommended_qty": max(0, round(recommended_qty, 0)),
        "suggested_order_date": suggested_order_date,
        "days_until_stockout": round(days_until_stockout, 1),
        "supplier_id": supplier_id,
        "supplier_name": supplier.get("name", "") if supplier else "(Perlu dipilih)",
        "supplier_code": supplier.get("code", "") if supplier else "",
        "urgency": urgency,
        "needs_planning": needs_planning
    }

# ==================== API ENDPOINTS ====================

@router.post("/generate")
async def generate_purchase_planning(
    data: PlanningGenerateRequest,
    user: dict = Depends(require_permission("purchase_planning", "create"))
):
    """Generate purchase planning recommendations"""
    db = get_database()
    
    # Get all products that need planning
    query = {"is_active": True}
    if data.category:
        query["category"] = data.category
    if data.supplier_id:
        query["supplier_id"] = data.supplier_id
    
    all_products = await products.find(query, {"_id": 0, "id": 1}).to_list(500)
    
    planning_items = []
    skipped = 0
    
    for product in all_products:
        recommendation = await calculate_planning_recommendation(
            db, product["id"], data.branch_id, data.warehouse_id
        )
        
        if not recommendation:
            continue
        
        # Skip if no planning needed
        if not data.include_all_low_stock and not recommendation["needs_planning"]:
            skipped += 1
            continue
        
        if recommendation["recommended_qty"] <= 0:
            skipped += 1
            continue
        
        # Check if planning already exists for this product (prevent duplicate)
        # Include po_created to prevent re-generating for items already planned
        existing = await db.purchase_planning.find_one({
            "product_id": product["id"],
            "status": {"$in": ["draft", "reviewed", "approved"]},
            # Only check recent (last 7 days) to allow re-planning old items
            "created_at": {"$gte": (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()}
        })
        
        if existing:
            skipped += 1
            continue
        
        # Create planning item
        planning_item = {
            "id": str(uuid.uuid4()),
            **recommendation,
            "status": "draft",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": user.get("user_id"),
            "created_by_name": user.get("name")
        }
        
        await db.purchase_planning.insert_one(planning_item)
        # Remove _id added by MongoDB to avoid ObjectId serialization error
        planning_item.pop("_id", None)
        planning_items.append(planning_item)
    
    # Audit log
    await db.audit_logs.insert_one({
        "id": str(uuid.uuid4()),
        "action": "purchase_planning_generate",
        "module": "purchase_planning",
        "description": f"Generated {len(planning_items)} planning items, skipped {skipped}",
        "user_id": user.get("user_id"),
        "user_name": user.get("name"),
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    return {
        "success": True,
        "generated": len(planning_items),
        "skipped": skipped,
        "items": planning_items[:20],  # Return first 20 for preview
        "message": f"Generated {len(planning_items)} planning recommendations"
    }


class ManualPlanningCreate(BaseModel):
    product_id: str
    recommended_qty: float
    supplier_id: Optional[str] = None
    suggested_order_date: Optional[str] = None
    notes: Optional[str] = ""
    branch_id: Optional[str] = None
    warehouse_id: Optional[str] = None

@router.post("/manual")
async def create_manual_planning(
    data: ManualPlanningCreate,
    user: dict = Depends(require_permission("purchase_planning", "create"))
):
    """Create manual planning item"""
    db = get_database()
    
    # Get product info
    product = await products.find_one({"id": data.product_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Product tidak ditemukan")
    
    # Get supplier info
    supplier = None
    if data.supplier_id:
        supplier = await db.suppliers.find_one({"id": data.supplier_id}, {"_id": 0})
    
    # Get current stock
    current_stock = await get_current_stock(db, data.product_id, data.branch_id, data.warehouse_id)
    
    # Create planning item
    planning_item = {
        "id": str(uuid.uuid4()),
        "product_id": data.product_id,
        "product_code": product.get("code", ""),
        "product_name": product.get("name", ""),
        "category": product.get("category", ""),
        "unit": product.get("unit", "pcs"),
        "branch_id": data.branch_id,
        "warehouse_id": data.warehouse_id,
        "current_stock": current_stock,
        "minimum_stock": product.get("minimum_stock", 0),
        "maximum_stock": product.get("maximum_stock", 0),
        "reorder_point": 0,
        "safety_stock": 0,
        "sales_velocity": 0,
        "lead_time_days": supplier.get("lead_time_days", 7) if supplier else 7,
        "open_po_qty": 0,
        "effective_stock": current_stock,
        "recommended_qty": data.recommended_qty,
        "suggested_order_date": data.suggested_order_date or (datetime.now(timezone.utc) + timedelta(days=7)).strftime("%Y-%m-%d"),
        "days_until_stockout": 999,
        "supplier_id": data.supplier_id,
        "supplier_name": supplier.get("name", "") if supplier else "(Perlu dipilih)",
        "supplier_code": supplier.get("code", "") if supplier else "",
        "urgency": "medium",
        "needs_planning": True,
        "notes": data.notes,
        "status": "draft",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user.get("user_id"),
        "created_by_name": user.get("name"),
        "manual_entry": True
    }
    
    await db.purchase_planning.insert_one(planning_item)
    planning_item.pop("_id", None)
    
    return {
        "success": True,
        "planning": planning_item,
        "message": "Manual planning created"
    }

@router.get("/list")
async def list_purchase_planning(
    status: Optional[str] = None,
    supplier_id: Optional[str] = None,
    category: Optional[str] = None,
    warehouse_id: Optional[str] = None,
    urgency: Optional[str] = None,
    limit: int = 100,
    user: dict = Depends(get_current_user)
):
    """List purchase planning items"""
    db = get_database()
    
    query = {}
    if status:
        query["status"] = status
    if supplier_id:
        query["supplier_id"] = supplier_id
    if category:
        query["category"] = category
    if warehouse_id:
        query["warehouse_id"] = warehouse_id
    if urgency:
        query["urgency"] = urgency
    
    items = await db.purchase_planning.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    
    # Get summary stats
    summary = {
        "total": len(items),
        "draft": sum(1 for i in items if i.get("status") == "draft"),
        "reviewed": sum(1 for i in items if i.get("status") == "reviewed"),
        "approved": sum(1 for i in items if i.get("status") == "approved"),
        "critical": sum(1 for i in items if i.get("urgency") == "critical"),
        "high": sum(1 for i in items if i.get("urgency") == "high"),
        "total_recommended_qty": sum(i.get("recommended_qty", 0) for i in items)
    }
    
    return {"items": items, "summary": summary}

@router.get("/{planning_id}")
async def get_planning_detail(
    planning_id: str,
    user: dict = Depends(get_current_user)
):
    """Get planning item detail"""
    db = get_database()
    
    item = await db.purchase_planning.find_one({"id": planning_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Planning tidak ditemukan")
    
    return item

@router.put("/{planning_id}")
async def update_planning_item(
    planning_id: str,
    data: PlanningItemUpdate,
    user: dict = Depends(require_permission("purchase_planning", "edit"))
):
    """Update planning item"""
    db = get_database()
    
    item = await db.purchase_planning.find_one({"id": planning_id})
    if not item:
        raise HTTPException(status_code=404, detail="Planning tidak ditemukan")
    
    if item["status"] in ["po_created", "cancelled"]:
        raise HTTPException(status_code=400, detail=f"Tidak dapat edit planning dengan status {item['status']}")
    
    update_data = {k: v for k, v in data.dict().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    update_data["updated_by"] = user.get("user_id")
    
    await db.purchase_planning.update_one({"id": planning_id}, {"$set": update_data})
    
    return {"success": True, "message": "Planning updated"}

@router.post("/{planning_id}/status")
async def update_planning_status(
    planning_id: str,
    data: PlanningStatusUpdate,
    user: dict = Depends(require_permission("purchase_planning", "approve"))
):
    """Update planning status"""
    db = get_database()
    
    item = await db.purchase_planning.find_one({"id": planning_id})
    if not item:
        raise HTTPException(status_code=404, detail="Planning tidak ditemukan")
    
    if data.status not in PLANNING_STATUS:
        raise HTTPException(status_code=400, detail=f"Status tidak valid: {data.status}")
    
    old_status = item["status"]
    
    # Validate transitions
    valid_transitions = {
        "draft": ["reviewed", "cancelled"],
        "reviewed": ["approved", "draft", "cancelled"],
        "approved": ["po_created", "reviewed", "cancelled"]
    }
    
    if data.status not in valid_transitions.get(old_status, []):
        raise HTTPException(status_code=400, detail=f"Tidak dapat ubah status dari {old_status} ke {data.status}")
    
    await db.purchase_planning.update_one(
        {"id": planning_id},
        {"$set": {
            "status": data.status,
            f"{data.status}_at": datetime.now(timezone.utc).isoformat(),
            f"{data.status}_by": user.get("user_id"),
            f"{data.status}_by_name": user.get("name"),
            f"{data.status}_notes": data.notes
        }}
    )
    
    # Audit log
    await db.audit_logs.insert_one({
        "id": str(uuid.uuid4()),
        "action": f"purchase_planning_{data.status}",
        "module": "purchase_planning",
        "target_id": planning_id,
        "description": f"Planning status: {old_status} -> {data.status}. Notes: {data.notes}",
        "user_id": user.get("user_id"),
        "user_name": user.get("name"),
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    return {"success": True, "old_status": old_status, "new_status": data.status}

@router.post("/create-po")
async def create_po_from_planning(
    data: CreatePOFromPlanning,
    user: dict = Depends(require_permission("purchase", "create"))
):
    """Create draft PO from approved planning items"""
    db = get_database()
    
    # Get planning items
    items = await db.purchase_planning.find({
        "id": {"$in": data.planning_ids},
        "status": "approved"
    }, {"_id": 0}).to_list(len(data.planning_ids))
    
    if not items:
        raise HTTPException(status_code=400, detail="Tidak ada planning yang approved")
    
    # Group by supplier
    by_supplier = {}
    for item in items:
        supplier_id = data.supplier_id or item.get("supplier_id") or "unknown"
        if supplier_id not in by_supplier:
            supplier = await db.suppliers.find_one({"id": supplier_id}, {"_id": 0})
            by_supplier[supplier_id] = {
                "supplier_id": supplier_id,
                "supplier_name": supplier.get("name", "Unknown") if supplier else "Unknown",
                "items": []
            }
        by_supplier[supplier_id]["items"].append({
            "product_id": item["product_id"],
            "product_code": item["product_code"],
            "product_name": item["product_name"],
            "unit": item["unit"],
            "quantity": item["recommended_qty"],
            "planning_id": item["id"]
        })
    
    # Create PO drafts
    created_pos = []
    for supplier_id, supplier_data in by_supplier.items():
        po_number = f"PO-PLAN-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{len(created_pos)+1}"
        
        po = {
            "id": str(uuid.uuid4()),
            "po_number": po_number,  # Use po_number to match Purchase module
            "po_no": po_number,  # Keep for backward compatibility
            "supplier_id": supplier_id,
            "supplier_name": supplier_data["supplier_name"],
            "items": supplier_data["items"],
            "total_items": len(supplier_data["items"]),
            "total_qty": sum(i["quantity"] for i in supplier_data["items"]),
            "subtotal": 0,
            "total": 0,
            "status": "draft",
            "source": "purchase_planning",
            "branch_id": user.get("branch_id"),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": user.get("user_id"),
            "created_by_name": user.get("name"),
            "user_id": user.get("user_id")
        }
        
        await db.purchase_orders.insert_one(po)
        # Remove _id added by MongoDB to avoid ObjectId serialization error
        po.pop("_id", None)
        created_pos.append(po)
        
        # Update planning items status
        planning_ids_for_supplier = [i["planning_id"] for i in supplier_data["items"]]
        await db.purchase_planning.update_many(
            {"id": {"$in": planning_ids_for_supplier}},
            {"$set": {
                "status": "po_created",
                "po_id": po["id"],
                "po_no": po_number,
                "po_number": po_number,
                "po_created_at": datetime.now(timezone.utc).isoformat()
            }}
        )
    
    # Audit log
    await db.audit_logs.insert_one({
        "id": str(uuid.uuid4()),
        "action": "create_po_from_planning",
        "module": "purchase_planning",
        "description": f"Created {len(created_pos)} PO drafts from {len(items)} planning items",
        "user_id": user.get("user_id"),
        "user_name": user.get("name"),
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    return {
        "success": True,
        "created_pos": len(created_pos),
        "po_list": [{"po_number": po["po_number"], "supplier": po["supplier_name"], "items": po["total_items"]} for po in created_pos],
        "message": f"Created {len(created_pos)} PO drafts"
    }

@router.delete("/{planning_id}")
async def delete_planning_item(
    planning_id: str,
    user: dict = Depends(require_permission("purchase_planning", "delete"))
):
    """Delete planning item (only draft status)"""
    db = get_database()
    
    item = await db.purchase_planning.find_one({"id": planning_id})
    if not item:
        raise HTTPException(status_code=404, detail="Planning tidak ditemukan")
    
    if item["status"] != "draft":
        raise HTTPException(status_code=400, detail="Hanya planning dengan status draft yang dapat dihapus")
    
    await db.purchase_planning.delete_one({"id": planning_id})
    
    return {"success": True, "message": "Planning deleted"}

# ==================== DASHBOARD ====================

@router.get("/dashboard/summary")
async def get_planning_dashboard(
    user: dict = Depends(get_current_user)
):
    """Get purchase planning dashboard summary"""
    db = get_database()
    
    # Count by status
    status_pipeline = [
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]
    status_result = await db.purchase_planning.aggregate(status_pipeline).to_list(10)
    by_status = {item["_id"]: item["count"] for item in status_result}
    
    # Count by urgency
    urgency_pipeline = [
        {"$match": {"status": {"$in": ["draft", "reviewed", "approved"]}}},
        {"$group": {"_id": "$urgency", "count": {"$sum": 1}}}
    ]
    urgency_result = await db.purchase_planning.aggregate(urgency_pipeline).to_list(10)
    by_urgency = {item["_id"]: item["count"] for item in urgency_result}
    
    # Top suppliers with pending planning
    supplier_pipeline = [
        {"$match": {"status": {"$in": ["draft", "reviewed", "approved"]}}},
        {"$group": {
            "_id": "$supplier_id",
            "supplier_name": {"$first": "$supplier_name"},
            "count": {"$sum": 1},
            "total_qty": {"$sum": "$recommended_qty"}
        }},
        {"$sort": {"count": -1}},
        {"$limit": 5}
    ]
    top_suppliers = await db.purchase_planning.aggregate(supplier_pipeline).to_list(5)
    
    # Critical items
    critical_items = await db.purchase_planning.find(
        {"urgency": "critical", "status": {"$in": ["draft", "reviewed"]}},
        {"_id": 0}
    ).limit(5).to_list(5)
    
    return {
        "by_status": by_status,
        "by_urgency": by_urgency,
        "top_suppliers": top_suppliers,
        "critical_items": critical_items,
        "total_pending": by_status.get("draft", 0) + by_status.get("reviewed", 0) + by_status.get("approved", 0)
    }
