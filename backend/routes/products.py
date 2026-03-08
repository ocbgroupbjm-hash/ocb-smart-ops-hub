# OCB TITAN - Products API
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, List
from database import products, categories, product_stocks, branches, get_next_sequence
from utils.auth import get_current_user
from models.titan_models import Product, ProductCategory, ProductStock
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
    cost_price: Optional[float] = None
    selling_price: Optional[float] = None
    wholesale_price: Optional[float] = None
    member_price: Optional[float] = None
    reseller_price: Optional[float] = None
    min_stock: Optional[int] = None
    is_active: Optional[bool] = None

class CategoryCreate(BaseModel):
    code: str
    name: str
    parent_id: Optional[str] = None
    description: str = ""

# ==================== CATEGORIES ====================

@router.get("/categories")
async def list_categories(user: dict = Depends(get_current_user)):
    items = await categories.find({"is_active": True}, {"_id": 0}).to_list(1000)
    return items

@router.post("/categories")
async def create_category(data: CategoryCreate, user: dict = Depends(get_current_user)):
    existing = await categories.find_one({"code": data.code})
    if existing:
        raise HTTPException(status_code=400, detail="Category code already exists")
    
    cat = ProductCategory(**data.model_dump())
    await categories.insert_one(cat.model_dump())
    return {"id": cat.id, "message": "Category created"}

# ==================== PRODUCTS ====================

@router.get("")
async def list_products(
    search: str = "",
    category_id: str = "",
    is_active: bool = True,
    skip: int = 0,
    limit: int = 100,
    user: dict = Depends(get_current_user)
):
    query = {"is_active": is_active}
    
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"code": {"$regex": search, "$options": "i"}},
            {"barcode": {"$regex": search, "$options": "i"}}
        ]
    
    if category_id:
        query["category_id"] = category_id
    
    items = await products.find(query, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    total = await products.count_documents(query)
    
    return {"items": items, "total": total}

@router.get("/search")
async def search_products(
    q: str = Query(..., min_length=1),
    branch_id: str = "",
    user: dict = Depends(get_current_user)
):
    """Fast product search for POS - search by code, barcode, or name"""
    query = {
        "is_active": True,
        "$or": [
            {"code": {"$regex": f"^{q}", "$options": "i"}},
            {"barcode": q},
            {"name": {"$regex": q, "$options": "i"}}
        ]
    }
    
    items = await products.find(query, {"_id": 0}).limit(20).to_list(20)
    
    # Get stock for branch if specified
    branch = branch_id or user.get("branch_id")
    if branch:
        for item in items:
            stock = await product_stocks.find_one(
                {"product_id": item["id"], "branch_id": branch},
                {"_id": 0, "quantity": 1, "available": 1}
            )
            item["stock"] = stock.get("quantity", 0) if stock else 0
            item["available"] = stock.get("available", 0) if stock else 0
    
    return items

@router.get("/barcode/{barcode}")
async def get_by_barcode(barcode: str, branch_id: str = "", user: dict = Depends(get_current_user)):
    """Get product by exact barcode match - for scanner"""
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
async def get_product(product_id: str, user: dict = Depends(get_current_user)):
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
async def create_product(data: ProductCreate, user: dict = Depends(get_current_user)):
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
    
    return {"id": product.id, "code": product.code, "message": "Product created"}

@router.put("/{product_id}")
async def update_product(product_id: str, data: ProductUpdate, user: dict = Depends(get_current_user)):
    product = await products.find_one({"id": product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await products.update_one({"id": product_id}, {"$set": update_data})
    
    return {"message": "Product updated"}

@router.delete("/{product_id}")
async def delete_product(product_id: str, user: dict = Depends(get_current_user)):
    # Soft delete
    result = await products.update_one(
        {"id": product_id},
        {"$set": {"is_active": False, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return {"message": "Product deleted"}

# ==================== STOCK ====================

@router.get("/{product_id}/stock")
async def get_product_stock(product_id: str, user: dict = Depends(get_current_user)):
    stocks = await product_stocks.find(
        {"product_id": product_id},
        {"_id": 0}
    ).to_list(500)
    
    # Enrich with branch names
    for stock in stocks:
        branch = await branches.find_one({"id": stock["branch_id"]}, {"_id": 0, "name": 1, "code": 1})
        stock["branch_name"] = branch.get("name", "Unknown") if branch else "Unknown"
        stock["branch_code"] = branch.get("code", "") if branch else ""
    
    return stocks

@router.post("/{product_id}/stock/adjust")
async def adjust_stock(
    product_id: str,
    branch_id: str,
    quantity: int,
    reason: str = "",
    user: dict = Depends(get_current_user)
):
    """Adjust stock quantity (positive or negative)"""
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
    
    return {"message": "Stock adjusted", "new_quantity": new_qty if stock else max(0, quantity)}
