# OCB TITAN ERP - Mobile API Layer
# Lightweight endpoints for Android/iOS apps
# Optimized for mobile network conditions

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from database import get_db
from utils.auth import get_current_user

router = APIRouter(prefix="/mobile", tags=["Mobile API"])


# ==================== MOBILE DASHBOARD ====================

@router.get("/dashboard")
async def mobile_dashboard(
    user: dict = Depends(get_current_user)
):
    """
    Mobile Dashboard - Lightweight summary for quick loading
    
    Returns: Sales today, pending tasks, alerts count
    """
    db = get_db()
    
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    branch_id = user.get("branch_id")
    
    # Build branch filter
    branch_filter = {"branch_id": branch_id} if branch_id and user.get("role") not in ["owner", "admin"] else {}
    
    # Today's sales
    sales_query = {
        **branch_filter,
        "invoice_date": {"$gte": today},
        "status": {"$in": ["completed", "posted", "paid"]}
    }
    
    sales_pipeline = [
        {"$match": sales_query},
        {"$group": {
            "_id": None,
            "total": {"$sum": "$total"},
            "count": {"$sum": 1}
        }}
    ]
    sales_result = await db["sales_invoices"].aggregate(sales_pipeline).to_list(1)
    sales_today = sales_result[0] if sales_result else {"total": 0, "count": 0}
    
    # Pending PO
    pending_po = await db["purchase_orders"].count_documents({
        **branch_filter,
        "status": {"$in": ["draft", "ordered"]}
    })
    
    # Low stock alerts (from SSOT)
    low_stock_pipeline = [
        {"$match": branch_filter} if branch_filter else {"$match": {}},
        {"$group": {"_id": "$product_id", "qty": {"$sum": "$quantity"}}},
        {"$match": {"qty": {"$lt": 5, "$gt": 0}}}
    ]
    low_stock = await db["stock_movements"].aggregate(low_stock_pipeline).to_list(1000)
    
    # Unpaid AR
    unpaid_ar = await db["accounts_receivable"].count_documents({
        **branch_filter,
        "status": {"$in": ["unpaid", "partial"]}
    })
    
    return {
        "sales_today": {
            "total": sales_today.get("total", 0),
            "transactions": sales_today.get("count", 0)
        },
        "alerts": {
            "pending_po": pending_po,
            "low_stock": len(low_stock),
            "unpaid_ar": unpaid_ar
        },
        "user": {
            "name": user.get("name", ""),
            "role": user.get("role", ""),
            "branch_id": branch_id
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# ==================== MOBILE SALES ====================

@router.get("/sales")
async def mobile_sales_list(
    date: Optional[str] = Query(None, description="Filter by date (YYYY-MM-DD)"),
    limit: int = Query(20, le=50),
    skip: int = Query(0),
    user: dict = Depends(get_current_user)
):
    """Mobile Sales List - Paginated, lightweight"""
    db = get_db()
    
    query = {}
    
    if user.get("role") not in ["owner", "admin"] and user.get("branch_id"):
        query["branch_id"] = user["branch_id"]
    
    if date:
        query["invoice_date"] = {"$gte": date, "$lte": date + "T23:59:59"}
    
    # Lightweight projection
    projection = {
        "_id": 0,
        "id": 1,
        "invoice_number": 1,
        "invoice_date": 1,
        "customer_name": 1,
        "total": 1,
        "status": 1,
        "payment_method": 1
    }
    
    total = await db["sales_invoices"].count_documents(query)
    
    sales = await db["sales_invoices"].find(
        query, projection
    ).sort("invoice_date", -1).skip(skip).limit(limit).to_list(limit)
    
    return {
        "items": sales,
        "total": total,
        "skip": skip,
        "limit": limit,
        "has_more": skip + limit < total
    }


@router.get("/sales/{invoice_id}")
async def mobile_sales_detail(
    invoice_id: str,
    user: dict = Depends(get_current_user)
):
    """Mobile Sales Detail"""
    db = get_db()
    
    invoice = await db["sales_invoices"].find_one(
        {"id": invoice_id},
        {"_id": 0}
    )
    
    if not invoice:
        invoice = await db["sales_invoices"].find_one(
            {"invoice_number": invoice_id},
            {"_id": 0}
        )
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice tidak ditemukan")
    
    return invoice


@router.post("/sales/quick")
async def mobile_quick_sale(
    items: List[dict],
    payment_method: str = "cash",
    customer_name: Optional[str] = "Walk-in",
    user: dict = Depends(get_current_user)
):
    """
    Quick Sale from Mobile
    
    Minimal payload for fast transactions
    items: [{"product_id": "xxx", "qty": 1}]
    """
    db = get_db()
    import uuid
    
    branch_id = user.get("branch_id")
    if not branch_id:
        raise HTTPException(status_code=400, detail="Branch ID required")
    
    # Build invoice items
    invoice_items = []
    subtotal = 0
    
    for item in items:
        product = await db["products"].find_one(
            {"id": item["product_id"]},
            {"_id": 0}
        )
        
        if not product:
            continue
        
        qty = item.get("qty", 1)
        price = product.get("selling_price", 0)
        item_subtotal = qty * price
        
        invoice_items.append({
            "product_id": product["id"],
            "product_code": product.get("code", ""),
            "product_name": product.get("name", ""),
            "quantity": qty,
            "unit_price": price,
            "discount_amount": 0,
            "subtotal": item_subtotal
        })
        
        subtotal += item_subtotal
    
    if not invoice_items:
        raise HTTPException(status_code=400, detail="No valid items")
    
    # Generate invoice number
    from utils.number_generator import generate_transaction_number
    invoice_number = await generate_transaction_number(db, "INV")
    
    invoice = {
        "id": str(uuid.uuid4()),
        "invoice_number": invoice_number,
        "invoice_date": datetime.now(timezone.utc).isoformat(),
        "branch_id": branch_id,
        "customer_name": customer_name,
        "items": invoice_items,
        "subtotal": subtotal,
        "discount_amount": 0,
        "tax_amount": 0,
        "total": subtotal,
        "payment_method": payment_method,
        "status": "completed",
        "cashier_id": user.get("user_id", ""),
        "cashier_name": user.get("name", ""),
        "source": "mobile",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db["sales_invoices"].insert_one(invoice)
    
    # Create stock movements
    for item in invoice_items:
        movement = {
            "id": str(uuid.uuid4()),
            "product_id": item["product_id"],
            "product_code": item.get("product_code", ""),
            "product_name": item.get("product_name", ""),
            "branch_id": branch_id,
            "movement_type": "sales_out",
            "quantity": -item["quantity"],
            "reference_type": "sales_invoice",
            "reference_id": invoice["id"],
            "reference_number": invoice_number,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db["stock_movements"].insert_one(movement)
    
    return {
        "success": True,
        "invoice_id": invoice["id"],
        "invoice_number": invoice_number,
        "total": subtotal
    }


# ==================== MOBILE INVENTORY ====================

@router.get("/inventory")
async def mobile_inventory(
    search: Optional[str] = None,
    category_id: Optional[str] = None,
    limit: int = Query(30, le=100),
    skip: int = Query(0),
    user: dict = Depends(get_current_user)
):
    """Mobile Inventory - Products with stock from SSOT"""
    db = get_db()
    
    branch_id = user.get("branch_id")
    branch_filter = {"branch_id": branch_id} if branch_id else {}
    
    # Get stock from SSOT
    stock_pipeline = [
        {"$match": branch_filter} if branch_filter else {"$match": {}},
        {"$group": {
            "_id": "$product_id",
            "stock": {"$sum": "$quantity"}
        }}
    ]
    stock_data = await db["stock_movements"].aggregate(stock_pipeline).to_list(100000)
    stock_map = {s["_id"]: s["stock"] for s in stock_data}
    
    # Get products
    product_query = {"is_active": True}
    if search:
        product_query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"code": {"$regex": search, "$options": "i"}}
        ]
    if category_id:
        product_query["category_id"] = category_id
    
    total = await db["products"].count_documents(product_query)
    
    products = await db["products"].find(
        product_query,
        {"_id": 0, "id": 1, "code": 1, "name": 1, "selling_price": 1, "cost_price": 1, "category_name": 1}
    ).skip(skip).limit(limit).to_list(limit)
    
    # Add stock info
    for p in products:
        p["stock"] = stock_map.get(p["id"], 0)
    
    return {
        "items": products,
        "total": total,
        "skip": skip,
        "limit": limit,
        "has_more": skip + limit < total
    }


@router.get("/inventory/{product_id}")
async def mobile_inventory_detail(
    product_id: str,
    user: dict = Depends(get_current_user)
):
    """Mobile Product Detail with stock history"""
    db = get_db()
    
    product = await db["products"].find_one({"id": product_id}, {"_id": 0})
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Get stock from SSOT
    branch_id = user.get("branch_id")
    match_query = {"product_id": product_id}
    if branch_id:
        match_query["branch_id"] = branch_id
    
    pipeline = [
        {"$match": match_query},
        {"$group": {"_id": "$branch_id", "stock": {"$sum": "$quantity"}}}
    ]
    stock_by_branch = await db["stock_movements"].aggregate(pipeline).to_list(100)
    
    # Recent movements
    movements = await db["stock_movements"].find(
        match_query,
        {"_id": 0, "movement_type": 1, "quantity": 1, "created_at": 1, "reference_number": 1}
    ).sort("created_at", -1).limit(10).to_list(10)
    
    product["stock_by_branch"] = {s["_id"]: s["stock"] for s in stock_by_branch if s["_id"]}
    product["total_stock"] = sum(s["stock"] for s in stock_by_branch)
    product["recent_movements"] = movements
    
    return product


# ==================== MOBILE NOTIFICATIONS ====================

@router.get("/notifications")
async def mobile_notifications(
    limit: int = Query(20, le=50),
    user: dict = Depends(get_current_user)
):
    """Mobile Notifications - Alerts and reminders"""
    db = get_db()
    
    branch_id = user.get("branch_id")
    notifications = []
    
    # Low stock alerts
    branch_filter = {"branch_id": branch_id} if branch_id else {}
    
    low_stock_pipeline = [
        {"$match": branch_filter} if branch_filter else {"$match": {}},
        {"$group": {
            "_id": "$product_id",
            "qty": {"$sum": "$quantity"},
            "name": {"$first": "$product_name"}
        }},
        {"$match": {"qty": {"$lt": 5, "$gt": 0}}},
        {"$limit": 5}
    ]
    low_stock = await db["stock_movements"].aggregate(low_stock_pipeline).to_list(5)
    
    for ls in low_stock:
        notifications.append({
            "type": "low_stock",
            "title": "Stok Rendah",
            "message": f"{ls['name']} hanya tersisa {ls['qty']} unit",
            "severity": "warning",
            "product_id": ls["_id"]
        })
    
    # Overdue AR
    today = datetime.now(timezone.utc).isoformat()[:10]
    overdue_ar = await db["accounts_receivable"].find(
        {**branch_filter, "due_date": {"$lt": today}, "status": {"$in": ["unpaid", "partial"]}},
        {"_id": 0, "ar_number": 1, "customer_name": 1, "amount": 1, "due_date": 1}
    ).limit(5).to_list(5)
    
    for ar in overdue_ar:
        notifications.append({
            "type": "overdue_ar",
            "title": "Piutang Jatuh Tempo",
            "message": f"{ar['customer_name']} - Rp {ar['amount']:,.0f}",
            "severity": "danger",
            "due_date": ar["due_date"]
        })
    
    # Cash variance alerts (today)
    variance = await db["cash_discrepancies"].find_one(
        {"created_at": {"$gte": today}, "discrepancy_type": "shortage"},
        {"_id": 0}
    )
    
    if variance:
        notifications.append({
            "type": "cash_shortage",
            "title": "Selisih Kas",
            "message": f"Shortage Rp {variance.get('discrepancy_amount', 0):,.0f}",
            "severity": "danger"
        })
    
    return {
        "notifications": notifications[:limit],
        "total": len(notifications),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# ==================== MOBILE SYNC ====================

@router.get("/sync/products")
async def mobile_sync_products(
    last_sync: Optional[str] = Query(None, description="Last sync timestamp"),
    user: dict = Depends(get_current_user)
):
    """Sync products for offline use"""
    db = get_db()
    
    query = {"is_active": True}
    if last_sync:
        query["updated_at"] = {"$gt": last_sync}
    
    products = await db["products"].find(
        query,
        {"_id": 0, "id": 1, "code": 1, "name": 1, "selling_price": 1, "category_name": 1, "unit_name": 1}
    ).to_list(10000)
    
    return {
        "products": products,
        "count": len(products),
        "sync_timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/sync/customers")
async def mobile_sync_customers(
    last_sync: Optional[str] = Query(None),
    user: dict = Depends(get_current_user)
):
    """Sync customers for offline use"""
    db = get_db()
    
    query = {"is_active": True}
    if last_sync:
        query["updated_at"] = {"$gt": last_sync}
    
    customers = await db["customers"].find(
        query,
        {"_id": 0, "id": 1, "code": 1, "name": 1, "phone": 1}
    ).to_list(10000)
    
    return {
        "customers": customers,
        "count": len(customers),
        "sync_timestamp": datetime.now(timezone.utc).isoformat()
    }
