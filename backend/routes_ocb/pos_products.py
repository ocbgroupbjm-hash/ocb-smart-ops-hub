from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from models_ocb.product import ProductCreate, ProductUpdate, ProductResponse, Product
from database import db
from utils.dependencies import get_current_user
from datetime import datetime, timezone

router = APIRouter(prefix="/pos/products", tags=["POS - Products"])

@router.post("/", response_model=ProductResponse)
async def create_product(product_data: ProductCreate, current_user: dict = Depends(get_current_user)):
    company_id = current_user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=400, detail="User must be associated with a company")
    
    product_data.company_id = company_id
    product = Product(**product_data.model_dump())
    product_dict = product.model_dump()
    product_dict['created_at'] = product_dict['created_at'].isoformat()
    product_dict['updated_at'] = product_dict['updated_at'].isoformat()
    
    await db.products.insert_one(product_dict)
    
    profit_margin = None
    if product.selling_price > 0 and product.purchase_price > 0:
        profit_margin = ((product.selling_price - product.purchase_price) / product.selling_price) * 100
    
    return ProductResponse(**product.model_dump(), profit_margin=profit_margin)

@router.get("/", response_model=List[ProductResponse])
async def get_products(
    search: Optional[str] = None,
    category: Optional[str] = None,
    branch_id: Optional[str] = None,
    low_stock: bool = False,
    current_user: dict = Depends(get_current_user)
):
    company_id = current_user.get("company_id")
    query = {"company_id": company_id}
    
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"barcode": {"$regex": search, "$options": "i"}},
            {"sku": {"$regex": search, "$options": "i"}}
        ]
    
    if category:
        query["category"] = category
    
    if branch_id:
        query["branch_id"] = branch_id
    
    if low_stock:
        query["$expr"] = {"$lte": ["$stock", "$min_stock"]}
    
    products = await db.products.find(query, {"_id": 0}).sort("name", 1).to_list(1000)
    
    result = []
    for p in products:
        if isinstance(p.get('created_at'), str):
            p['created_at'] = datetime.fromisoformat(p['created_at'])
        if isinstance(p.get('updated_at'), str):
            p['updated_at'] = datetime.fromisoformat(p['updated_at'])
        
        profit_margin = None
        if p.get('selling_price', 0) > 0 and p.get('purchase_price', 0) > 0:
            profit_margin = ((p['selling_price'] - p['purchase_price']) / p['selling_price']) * 100
        
        result.append(ProductResponse(**p, profit_margin=profit_margin))
    
    return result

@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str, current_user: dict = Depends(get_current_user)):
    company_id = current_user.get("company_id")
    product = await db.products.find_one({"id": product_id, "company_id": company_id}, {"_id": 0})
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if isinstance(product.get('created_at'), str):
        product['created_at'] = datetime.fromisoformat(product['created_at'])
    if isinstance(product.get('updated_at'), str):
        product['updated_at'] = datetime.fromisoformat(product['updated_at'])
    
    profit_margin = None
    if product.get('selling_price', 0) > 0 and product.get('purchase_price', 0) > 0:
        profit_margin = ((product['selling_price'] - product['purchase_price']) / product['selling_price']) * 100
    
    return ProductResponse(**product, profit_margin=profit_margin)

@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    update_data: ProductUpdate,
    current_user: dict = Depends(get_current_user)
):
    company_id = current_user.get("company_id")
    product = await db.products.find_one({"id": product_id, "company_id": company_id}, {"_id": 0})
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    update_dict = {k: v for k, v in update_data.model_dump(exclude_unset=True).items() if v is not None}
    update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.products.update_one({"id": product_id}, {"$set": update_dict})
    
    updated_product = await db.products.find_one({"id": product_id}, {"_id": 0})
    
    if isinstance(updated_product.get('created_at'), str):
        updated_product['created_at'] = datetime.fromisoformat(updated_product['created_at'])
    if isinstance(updated_product.get('updated_at'), str):
        updated_product['updated_at'] = datetime.fromisoformat(updated_product['updated_at'])
    
    profit_margin = None
    if updated_product.get('selling_price', 0) > 0 and updated_product.get('purchase_price', 0) > 0:
        profit_margin = ((updated_product['selling_price'] - updated_product['purchase_price']) / updated_product['selling_price']) * 100
    
    return ProductResponse(**updated_product, profit_margin=profit_margin)

@router.delete("/{product_id}")
async def delete_product(product_id: str, current_user: dict = Depends(get_current_user)):
    company_id = current_user.get("company_id")
    result = await db.products.delete_one({"id": product_id, "company_id": company_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return {"message": "Product deleted successfully"}