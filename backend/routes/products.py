# OCB TITAN - Products API
# SECURITY: All destructive operations require RBAC validation
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from pydantic import BaseModel
from typing import Optional, List
from database import products, categories, product_stocks, branches, get_next_sequence, get_db
from utils.auth import get_current_user
from models.titan_models import Product, ProductCategory, ProductStock
from routes.rbac_middleware import require_permission, log_security_event
from datetime import datetime, timezone

router = APIRouter(prefix="/products", tags=["Products"])

class ProductCreate(BaseModel):
    code: Optional[str] = None
    barcode: str = ""
    name: str
    description: str = ""
    category_id: Optional[str] = None
    brand: str = ""
    unit: str = "pcs"
    cost_price: float = 0
    selling_price: float = 0
    wholesale_price: float = 0
    member_price: float = 0
    reseller_price: float = 0
    min_stock: int = 5
    track_stock: bool = True
    tax_rate: float = 0
    is_bundle: bool = False
    bundle_items: List[dict] = []

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    barcode: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[str] = None
    brand: Optional[str] = None
    brand_id: Optional[str] = None
    unit: Optional[str] = None
    unit_id: Optional[str] = None
    supplier_id: Optional[str] = None
    item_type: Optional[str] = None
    cost_price: Optional[float] = None
    selling_price: Optional[float] = None
    wholesale_price: Optional[float] = None
    member_price: Optional[float] = None
    reseller_price: Optional[float] = None
    min_stock: Optional[int] = None
    max_stock: Optional[int] = None
    minimum_stock: Optional[int] = None
    maximum_stock: Optional[int] = None
    rack: Optional[str] = None
    sku_internal: Optional[str] = None
    is_active: Optional[bool] = None

class CategoryCreate(BaseModel):
    code: str
    name: str
    parent_id: Optional[str] = None
    description: str = ""

# ==================== CATEGORIES ====================

@router.get("/categories")
async def list_categories(user: dict = Depends(require_permission("master_category", "view"))):
    """List categories - Requires master_category.view permission"""
    items = await categories.find({"is_active": True}, {"_id": 0}).to_list(1000)
    return items

@router.post("/categories")
async def create_category(data: CategoryCreate, request: Request, user: dict = Depends(require_permission("master_category", "create"))):
    """Create category - Requires master_category.create permission"""
    existing = await categories.find_one({"code": data.code})
    if existing:
        raise HTTPException(status_code=400, detail="Category code already exists")
    
    cat = ProductCategory(**data.model_dump())
    await categories.insert_one(cat.model_dump())
    
    # Audit log
    db = get_db()
    await log_security_event(
        db, user.get("user_id", ""), user.get("name", ""),
        "create", "master_category",
        f"Membuat kategori {data.name}",
        request.client.host if request.client else ""
    )
    
    return {"id": cat.id, "message": "Category created"}

# ==================== PRODUCTS ====================

@router.get("")
async def list_products(
    search: str = "",
    category_id: str = "",
    brand: str = "",
    branch_id: str = "",
    is_active: bool = True,
    min_stock: Optional[int] = None,
    max_stock: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    user: dict = Depends(require_permission("master_item", "view"))
):
    """
    List products with optional branch filter
    
    Filters:
    - search: kode, barcode, nama
    - category_id: filter by category
    - brand: filter by brand
    - branch_id: filter stok untuk cabang tertentu (jika kosong, agregasi semua cabang)
    - is_active: status aktif
    - min_stock, max_stock: filter berdasarkan stok
    """
    query = {"is_active": is_active}
    
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"code": {"$regex": search, "$options": "i"}},
            {"barcode": {"$regex": search, "$options": "i"}}
        ]
    
    if category_id:
        query["category_id"] = category_id
    
    if brand:
        query["brand"] = {"$regex": brand, "$options": "i"}
    
    items = await products.find(query, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    total = await products.count_documents(query)
    
    # OPTIMIZED: Batch query untuk stock data (menghilangkan N+1)
    print("USING NEW BATCH QUERY VERSION - /api/products")
    product_ids = [item.get("id") for item in items]
    
    if branch_id:
        # Single batch query untuk stock per branch
        stock_records = await product_stocks.find(
            {"product_id": {"$in": product_ids}, "branch_id": branch_id},
            {"_id": 0}
        ).to_list(None)
        stock_map = {s["product_id"]: s for s in stock_records}
    else:
        # Single aggregate query untuk total stock semua branch
        stock_pipeline = [
            {"$match": {"product_id": {"$in": product_ids}}},
            {"$group": {
                "_id": "$product_id",
                "total_stock": {"$sum": "$quantity"},
                "total_available": {"$sum": {"$ifNull": ["$available", "$quantity"]}},
                "branches_count": {"$sum": 1}
            }}
        ]
        stock_agg = await product_stocks.aggregate(stock_pipeline).to_list(None)
        stock_map = {s["_id"]: s for s in stock_agg}
    
    # Enrich items dengan stock data dari map (O(1) lookup, tanpa query)
    result_items = []
    for item in items:
        product_id = item.get("id")
        
        if branch_id:
            stock_rec = stock_map.get(product_id)
            item["stock"] = stock_rec.get("quantity", 0) if stock_rec else 0
            item["available"] = stock_rec.get("available", 0) if stock_rec else 0
            item["branch_stock"] = stock_rec if stock_rec else None
        else:
            stock_data = stock_map.get(product_id)
            if stock_data:
                item["stock"] = stock_data.get("total_stock", 0)
                item["available"] = stock_data.get("total_available", 0)
                item["branches_count"] = stock_data.get("branches_count", 0)
            else:
                item["stock"] = 0
                item["available"] = 0
                item["branches_count"] = 0
        
        # Apply stock filters
        if min_stock is not None and item.get("stock", 0) < min_stock:
            continue
        if max_stock is not None and item.get("stock", 0) > max_stock:
            continue
        
        result_items.append(item)
    
    return {"items": result_items, "total": len(result_items), "original_total": total}

@router.get("/search")
async def search_products(
    q: str = Query(..., min_length=1),
    branch_id: str = "",
    user: dict = Depends(require_permission("master_item", "view"))
):
    """Fast product search for POS - Requires master_item.view permission"""
    query = {
        "is_active": True,
        "$or": [
            {"code": {"$regex": f"^{q}", "$options": "i"}},
            {"barcode": q},
            {"name": {"$regex": q, "$options": "i"}}
        ]
    }
    
    items = await products.find(query, {"_id": 0}).limit(20).to_list(20)
    
    # OPTIMIZED: Batch query untuk stock (menghilangkan N+1)
    print("USING NEW BATCH QUERY VERSION - /search")
    branch = branch_id or user.get("branch_id")
    if branch and items:
        product_ids = [item["id"] for item in items]
        stock_records = await product_stocks.find(
            {"product_id": {"$in": product_ids}, "branch_id": branch},
            {"_id": 0, "product_id": 1, "quantity": 1, "available": 1}
        ).to_list(None)
        stock_map = {s["product_id"]: s for s in stock_records}
        
        for item in items:
            stock = stock_map.get(item["id"])
            item["stock"] = stock.get("quantity", 0) if stock else 0
            item["available"] = stock.get("available", 0) if stock else 0
    
    return items

@router.get("/barcode/{barcode}")
async def get_by_barcode(barcode: str, branch_id: str = "", user: dict = Depends(require_permission("master_item", "view"))):
    """Get product by exact barcode match - Requires master_item.view permission"""
    product = await products.find_one({"barcode": barcode, "is_active": True}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    branch = branch_id or user.get("branch_id")
    if branch:
        stock = await product_stocks.find_one(
            {"product_id": product["id"], "branch_id": branch},
            {"_id": 0}
        )
        product["stock"] = stock.get("quantity", 0) if stock else 0
        product["available"] = stock.get("available", 0) if stock else 0
    
    return product

@router.get("/{product_id}")
async def get_product(product_id: str, user: dict = Depends(require_permission("master_item", "view"))):
    """Get product details - Requires master_item.view permission"""
    product = await products.find_one({"id": product_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Get stock across all branches
    stocks = await product_stocks.find(
        {"product_id": product_id},
        {"_id": 0}
    ).to_list(100)
    
    product["stocks"] = stocks
    product["total_stock"] = sum(s.get("quantity", 0) for s in stocks)
    
    return product

@router.post("")
async def create_product(data: ProductCreate, request: Request, user: dict = Depends(require_permission("master_item", "create"))):
    """Create product - Requires master_item.create permission"""
    # Generate code if not provided
    code = data.code or await get_next_sequence("product_code", "PRD")
    
    existing = await products.find_one({"code": code})
    if existing:
        raise HTTPException(status_code=400, detail="Product code already exists")
    
    if data.barcode:
        existing_barcode = await products.find_one({"barcode": data.barcode})
        if existing_barcode:
            raise HTTPException(status_code=400, detail="Barcode already exists")
    
    product = Product(
        code=code,
        **{k: v for k, v in data.model_dump().items() if k != "code"}
    )
    
    await products.insert_one(product.model_dump())
    
    # Initialize stock for all branches
    all_branches = await branches.find({"is_active": True}, {"_id": 0, "id": 1}).to_list(500)
    for branch in all_branches:
        stock = ProductStock(
            product_id=product.id,
            branch_id=branch["id"],
            quantity=0,
            available=0
        )
        await product_stocks.insert_one(stock.model_dump())
    
    # Audit log
    db = get_db()
    await log_security_event(
        db, user.get("user_id", ""), user.get("name", ""),
        "create", "master_item",
        f"Membuat produk {product.name} ({product.code})",
        request.client.host if request.client else ""
    )
    
    return {"id": product.id, "code": product.code, "message": "Product created"}

@router.put("/{product_id}")
async def update_product(product_id: str, data: ProductUpdate, request: Request, user: dict = Depends(require_permission("master_item", "edit"))):
    """Update product - Requires master_item.edit permission"""
    product = await products.find_one({"id": product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await products.update_one({"id": product_id}, {"$set": update_data})
    
    # Audit log
    db = get_db()
    await log_security_event(
        db, user.get("user_id", ""), user.get("name", ""),
        "edit", "master_item",
        f"Update produk {product.get('name', product_id)}",
        request.client.host if request.client else "",
        data_before=product,
        data_after=update_data
    )
    
    return {"message": "Product updated"}

@router.delete("/{product_id}")
async def delete_product(product_id: str, request: Request, user: dict = Depends(require_permission("master_item", "delete"))):
    """Delete product - Requires master_item.delete permission"""
    product = await products.find_one({"id": product_id}, {"_id": 0})
    
    # Soft delete
    result = await products.update_one(
        {"id": product_id},
        {"$set": {"is_active": False, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # CRITICAL: Audit log for delete
    db = get_db()
    await log_security_event(
        db, user.get("user_id", ""), user.get("name", ""),
        "delete", "master_item",
        f"DELETE produk {product.get('name', product_id) if product else product_id}",
        request.client.host if request.client else "",
        severity="critical"
    )
    
    return {"message": "Product deleted"}

# ==================== STOCK ====================

@router.get("/{product_id}/stock")
async def get_product_stock(product_id: str, user: dict = Depends(require_permission("stock_card", "view"))):
    """Get product stock - Requires stock_card.view permission"""
    print("USING NEW BATCH QUERY VERSION - /{product_id}/stock")
    stocks = await product_stocks.find(
        {"product_id": product_id},
        {"_id": 0}
    ).to_list(500)
    
    # OPTIMIZED: Batch query untuk branch names (menghilangkan N+1)
    if stocks:
        branch_ids = [s["branch_id"] for s in stocks]
        branch_records = await branches.find(
            {"id": {"$in": branch_ids}},
            {"_id": 0, "id": 1, "name": 1, "code": 1}
        ).to_list(None)
        branch_map = {b["id"]: b for b in branch_records}
        
        for stock in stocks:
            branch = branch_map.get(stock["branch_id"])
            stock["branch_name"] = branch.get("name", "Unknown") if branch else "Unknown"
            stock["branch_code"] = branch.get("code", "") if branch else ""
    
    return stocks

@router.post("/{product_id}/stock/adjust")
async def adjust_stock(
    product_id: str,
    branch_id: str,
    quantity: int,
    reason: str = "",
    request: Request = None,
    user: dict = Depends(require_permission("stock_opname", "edit"))
):
    """Adjust stock quantity - Requires stock_opname.edit permission"""
    from models.titan_models import StockMovement, StockMovementType
    
    stock = await product_stocks.find_one({"product_id": product_id, "branch_id": branch_id})
    
    if stock:
        new_qty = stock.get("quantity", 0) + quantity
        await product_stocks.update_one(
            {"product_id": product_id, "branch_id": branch_id},
            {"$set": {
                "quantity": new_qty,
                "available": new_qty - stock.get("reserved", 0),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
    else:
        new_stock = ProductStock(
            product_id=product_id,
            branch_id=branch_id,
            quantity=max(0, quantity),
            available=max(0, quantity)
        )
        await product_stocks.insert_one(new_stock.model_dump())
    
    # Record movement
    from database import stock_movements
    movement = StockMovement(
        product_id=product_id,
        branch_id=branch_id,
        movement_type=StockMovementType.ADJUSTMENT,
        quantity=quantity,
        notes=reason,
        user_id=user.get("user_id", "")
    )
    await stock_movements.insert_one(movement.model_dump())
    
    # Audit log for stock adjustment
    db = get_db()
    await log_security_event(
        db, user.get("user_id", ""), user.get("name", ""),
        "edit", "stock_opname",
        f"Stock adjustment {product_id} di branch {branch_id}: {quantity:+d}. Alasan: {reason}",
        request.client.host if request and request.client else "",
        severity="warning" if abs(quantity) > 100 else "normal"
    )
    
    return {"message": "Stock adjusted", "new_quantity": new_qty if stock else max(0, quantity)}
