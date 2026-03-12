# OCB AI TITAN - Complete Master Data API
# Categories, Units, Brands, Warehouses, Sales Persons, Customer Groups, etc.

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from pydantic import BaseModel
from typing import Optional, List
from database import db, get_next_sequence
from utils.auth import get_current_user
from routes.rbac_system import require_permission, log_activity
from datetime import datetime, timezone
import uuid

router = APIRouter(prefix="/master", tags=["Master Data ERP"])

# Collections
categories = db["categories"]
units = db["units"]
brands = db["brands"]
warehouses = db["warehouses"]
sales_persons = db["sales_persons"]
customer_groups = db["customer_groups"]
regions = db["regions"]
banks = db["banks"]
emoney = db["emoney"]
shipping_costs = db["shipping_costs"]
discounts = db["discounts"]
promotions = db["promotions"]
items = db["products"]  # Using products collection for items

# ==================== ITEMS (Products) ====================

class ItemCreate(BaseModel):
    code: str
    barcode: str = ""
    name: str
    category_id: str = ""
    unit_id: str = ""
    brand_id: str = ""
    branch_id: str = ""  # CABANG sebagai lokasi utama
    rack: str = ""
    item_type: str = "barang"
    cost_price: float = 0
    selling_price: float = 0
    # Price Levels untuk retail
    price_level_1: float = 0  # Harga umum/normal
    price_level_2: float = 0  # Harga member
    price_level_3: float = 0  # Harga grosir
    price_level_4: float = 0  # Harga reseller
    price_level_5: float = 0  # Harga VIP
    min_stock: int = 0
    max_stock: int = 0
    description: str = ""
    is_active: bool = True
    track_stock: bool = True
    discontinued: bool = False
    supplier_id: str = ""  # Default supplier
    supplier_name: str = ""

@router.get("/items")
async def list_items(
    page: int = 1,
    limit: int = 50,
    search: str = "",
    category_id: str = "",
    brand_id: str = "",
    branch_id: str = "",  # CABANG sebagai lokasi utama
    item_type: str = "",
    rack: str = "",
    is_active: str = "",
    has_stock: str = "",
    discontinued: str = "",
    sort_by: str = "code",
    sort_order: str = "asc",
    user: dict = Depends(get_current_user)
):
    query = {}
    
    # Search filter
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"code": {"$regex": search, "$options": "i"}},
            {"barcode": {"$regex": search, "$options": "i"}}
        ]
    
    # Category filter
    if category_id:
        query["category_id"] = category_id
    
    # Brand filter
    if brand_id:
        query["brand_id"] = brand_id
    
    # Branch filter (CABANG sebagai lokasi utama)
    if branch_id:
        query["branch_id"] = branch_id
    
    # Item type filter
    if item_type and item_type != "semua":
        query["item_type"] = item_type
    
    # Rack filter
    if rack:
        query["rack"] = {"$regex": rack, "$options": "i"}
    
    # Active filter
    if is_active == "true":
        query["is_active"] = True
    elif is_active == "false":
        query["is_active"] = False
    
    # Stock filter
    if has_stock == "true":
        query["stock"] = {"$gt": 0}
    elif has_stock == "false":
        query["$or"] = query.get("$or", []) + [{"stock": {"$lte": 0}}, {"stock": {"$exists": False}}]
    
    # Discontinued filter
    if discontinued == "true":
        query["discontinued"] = True
    
    # Sorting
    sort_field = sort_by if sort_by in ["code", "name", "selling_price", "cost_price", "stock", "brand_name"] else "code"
    sort_direction = 1 if sort_order == "asc" else -1
    
    skip = (page - 1) * limit
    cursor = items.find(query, {"_id": 0}).sort(sort_field, sort_direction).skip(skip).limit(limit)
    result = await cursor.to_list(limit)
    total = await items.count_documents(query)
    
    # Add category/unit/brand/branch names
    for item in result:
        if item.get("category_id"):
            cat = await categories.find_one({"id": item["category_id"]}, {"_id": 0, "name": 1})
            item["category_name"] = cat["name"] if cat else ""
        if item.get("unit_id"):
            unit = await units.find_one({"id": item["unit_id"]}, {"_id": 0, "name": 1})
            item["unit_name"] = unit["name"] if unit else ""
        if item.get("brand_id"):
            brand = await brands.find_one({"id": item["brand_id"]}, {"_id": 0, "name": 1})
            item["brand_name"] = brand["name"] if brand else ""
        if item.get("branch_id"):
            branch = await db["branches"].find_one({"id": item["branch_id"]}, {"_id": 0, "name": 1})
            item["branch_name"] = branch["name"] if branch else ""
    
    return {"items": result, "total": total, "page": page, "limit": limit}

@router.post("/items")
async def create_item(data: ItemCreate, user: dict = Depends(get_current_user)):
    existing = await items.find_one({"code": data.code})
    if existing:
        raise HTTPException(status_code=400, detail="Kode item sudah ada")
    
    # Get supplier name if supplier_id provided
    supplier_name = data.supplier_name
    if data.supplier_id and not supplier_name:
        supplier = await db["suppliers"].find_one({"id": data.supplier_id}, {"_id": 0, "name": 1})
        if supplier:
            supplier_name = supplier.get("name", "")
    
    item = {
        "id": str(uuid.uuid4()),
        **data.model_dump(),
        "supplier_name": supplier_name,  # Ensure supplier_name is saved
        # NOTE: stock tidak disimpan di item - dihitung dari stock_movements (SSOT)
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user.get("id")
    }
    await items.insert_one(item)
    
    # Auto-initialize branch stock CONFIG for all branches (min/max only, NOT stock_current)
    # stock_current dihitung dari stock_movements (SSOT principle)
    all_branches = await db["branches"].find({}, {"_id": 0, "id": 1, "name": 1}).to_list(500)
    if all_branches:
        branch_configs = []
        for branch in all_branches:
            branch_configs.append({
                "id": str(uuid.uuid4()),
                "item_id": item["id"],
                "branch_id": branch["id"],
                "branch_name": branch.get("name", ""),
                # stock_current dihilangkan - dihitung dari stock_movements
                "stock_minimum": 0,
                "stock_maximum": 0,
                "created_at": datetime.now(timezone.utc).isoformat()
            })
        await db["item_branch_stock"].insert_many(branch_configs)
    
    return {"id": item["id"], "message": "Item berhasil ditambahkan"}

@router.put("/items/{item_id}")
async def update_item(item_id: str, data: ItemCreate, user: dict = Depends(get_current_user)):
    update_data = data.model_dump()
    
    # Get supplier name if supplier_id provided and supplier_name not given
    if data.supplier_id and not data.supplier_name:
        supplier = await db["suppliers"].find_one({"id": data.supplier_id}, {"_id": 0, "name": 1})
        if supplier:
            update_data["supplier_name"] = supplier.get("name", "")
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await items.update_one({"id": item_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Item tidak ditemukan")
    return {"message": "Item berhasil diupdate"}

@router.delete("/items/{item_id}")
async def delete_item(
    item_id: str, 
    request: Request,
    user: dict = Depends(require_permission("master_item", "delete"))
):
    # Get item name for audit log
    item = await items.find_one({"id": item_id}, {"_id": 0, "name": 1, "code": 1})
    if not item:
        raise HTTPException(status_code=404, detail="Item tidak ditemukan")
    
    result = await items.delete_one({"id": item_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item tidak ditemukan")
    
    # Log activity
    await log_activity(
        db, user.get("user_id"), user.get("name", ""),
        "delete", "master_item",
        f"Menghapus item: {item.get('code')} - {item.get('name')}",
        request.client.host if request.client else ""
    )
    
    return {"message": "Item berhasil dihapus"}


# ==================== PRICE LEVEL SYSTEM ====================

@router.get("/items/{item_id}/price-for-customer/{customer_id}")
async def get_item_price_for_customer(item_id: str, customer_id: str, user: dict = Depends(get_current_user)):
    """
    Get the correct price for an item based on customer's group price level.
    Used by POS and Sales Invoice to auto-apply correct price.
    """
    # Get item
    item = await items.find_one({"id": item_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Item tidak ditemukan")
    
    # Get customer
    customer = await db["customers"].find_one({"id": customer_id}, {"_id": 0})
    if not customer:
        # Return default price if customer not found
        return {
            "item_id": item_id,
            "customer_id": customer_id,
            "price_level": 1,
            "price": item.get("selling_price", 0)
        }
    
    # Get customer group
    group_id = customer.get("group_id")
    price_level = 1  # Default
    
    if group_id:
        group = await customer_groups.find_one({"id": group_id}, {"_id": 0})
        if group:
            price_level = group.get("price_level", 1)
    
    # Get price based on level
    price_field = f"price_level_{price_level}"
    price = item.get(price_field, 0)
    
    # If price level is 0 or not set, fallback to selling_price
    if not price:
        price = item.get("selling_price", 0)
    
    return {
        "item_id": item_id,
        "item_code": item.get("code"),
        "item_name": item.get("name"),
        "customer_id": customer_id,
        "customer_name": customer.get("name"),
        "group_id": group_id,
        "price_level": price_level,
        "price": price,
        "original_price": item.get("selling_price", 0)
    }

@router.get("/price-levels")
async def get_price_level_info(user: dict = Depends(get_current_user)):
    """Get price level definitions"""
    return {
        "levels": [
            {"level": 1, "name": "Harga Umum", "description": "Harga normal untuk pelanggan umum"},
            {"level": 2, "name": "Harga Member", "description": "Harga untuk pelanggan member"},
            {"level": 3, "name": "Harga Grosir", "description": "Harga untuk pembelian grosir"},
            {"level": 4, "name": "Harga Reseller", "description": "Harga untuk reseller"},
            {"level": 5, "name": "Harga VIP", "description": "Harga khusus VIP"}
        ]
    }


# ==================== CATEGORIES ====================

class CategoryCreate(BaseModel):
    code: str
    name: str
    description: str = ""

class CategoryUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None

@router.get("/categories")
async def list_categories(search: str = "", user: dict = Depends(get_current_user)):
    query = {}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"code": {"$regex": search, "$options": "i"}}
        ]
    result = await categories.find(query, {"_id": 0}).sort("name", 1).to_list(500)
    return result

@router.post("/categories")
async def create_category(data: CategoryCreate, user: dict = Depends(get_current_user)):
    existing = await categories.find_one({"code": data.code})
    if existing:
        raise HTTPException(status_code=400, detail="Kode kategori sudah ada")
    
    category = {
        "id": str(uuid.uuid4()),
        **data.model_dump(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await categories.insert_one(category)
    return {"id": category["id"], "message": "Kategori berhasil ditambahkan"}

@router.put("/categories/{category_id}")
async def update_category(category_id: str, data: CategoryUpdate, user: dict = Depends(get_current_user)):
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Tidak ada data untuk diupdate")
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await categories.update_one({"id": category_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Kategori tidak ditemukan")
    return {"message": "Kategori berhasil diupdate"}

@router.delete("/categories/{category_id}")
async def delete_category(category_id: str, request: Request, user: dict = Depends(require_permission("master_category", "delete"))):
    """Delete category - Requires master_category.delete permission"""
    result = await categories.delete_one({"id": category_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Kategori tidak ditemukan")
    await log_activity(
        db, user.get("user_id"), user.get("name", ""),
        "delete", "master_category", f"Menghapus kategori: {category_id}",
        request.client.host if request.client else ""
    )
    return {"message": "Kategori berhasil dihapus"}

# ==================== UNITS ====================

class UnitCreate(BaseModel):
    code: str
    name: str
    description: str = ""

class UnitUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None

@router.get("/units")
async def list_units(search: str = "", user: dict = Depends(get_current_user)):
    query = {}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"code": {"$regex": search, "$options": "i"}}
        ]
    result = await units.find(query, {"_id": 0}).sort("name", 1).to_list(500)
    return result

@router.post("/units")
async def create_unit(data: UnitCreate, user: dict = Depends(get_current_user)):
    existing = await units.find_one({"code": data.code})
    if existing:
        raise HTTPException(status_code=400, detail="Kode satuan sudah ada")
    
    unit = {
        "id": str(uuid.uuid4()),
        **data.model_dump(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await units.insert_one(unit)
    return {"id": unit["id"], "message": "Satuan berhasil ditambahkan"}

@router.put("/units/{unit_id}")
async def update_unit(unit_id: str, data: UnitUpdate, user: dict = Depends(get_current_user)):
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Tidak ada data untuk diupdate")
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await units.update_one({"id": unit_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Satuan tidak ditemukan")
    return {"message": "Satuan berhasil diupdate"}

@router.delete("/units/{unit_id}")
async def delete_unit(unit_id: str, request: Request, user: dict = Depends(require_permission("master_unit", "delete"))):
    """Delete unit - Requires master_unit.delete permission"""
    result = await units.delete_one({"id": unit_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Satuan tidak ditemukan")
    await log_activity(db, user.get("user_id"), user.get("name", ""), "delete", "master_unit", f"Menghapus satuan: {unit_id}", request.client.host if request.client else "")
    return {"message": "Satuan berhasil dihapus"}

# ==================== BRANDS ====================

class BrandCreate(BaseModel):
    code: str
    name: str
    description: str = ""

class BrandUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None

@router.get("/brands")
async def list_brands(search: str = "", user: dict = Depends(get_current_user)):
    query = {}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"code": {"$regex": search, "$options": "i"}}
        ]
    result = await brands.find(query, {"_id": 0}).sort("name", 1).to_list(500)
    return result

@router.post("/brands")
async def create_brand(data: BrandCreate, user: dict = Depends(get_current_user)):
    existing = await brands.find_one({"code": data.code})
    if existing:
        raise HTTPException(status_code=400, detail="Kode merk sudah ada")
    
    brand = {
        "id": str(uuid.uuid4()),
        **data.model_dump(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await brands.insert_one(brand)
    return {"id": brand["id"], "message": "Merk berhasil ditambahkan"}

@router.put("/brands/{brand_id}")
async def update_brand(brand_id: str, data: BrandUpdate, user: dict = Depends(get_current_user)):
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Tidak ada data untuk diupdate")
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await brands.update_one({"id": brand_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Merk tidak ditemukan")
    return {"message": "Merk berhasil diupdate"}

@router.delete("/brands/{brand_id}")
async def delete_brand(brand_id: str, request: Request, user: dict = Depends(require_permission("master_brand", "delete"))):
    """Delete brand - Requires master_brand.delete permission"""
    result = await brands.delete_one({"id": brand_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Merk tidak ditemukan")
    await log_activity(db, user.get("user_id"), user.get("name", ""), "delete", "master_brand", f"Menghapus merk: {brand_id}", request.client.host if request.client else "")
    return {"message": "Merk berhasil dihapus"}

# ==================== WAREHOUSES ====================

class WarehouseCreate(BaseModel):
    code: str
    name: str
    branch_id: str = ""
    address: str = ""
    is_active: bool = True

@router.get("/warehouses")
async def list_warehouses(search: str = "", user: dict = Depends(get_current_user)):
    query = {}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"code": {"$regex": search, "$options": "i"}}
        ]
    result = await warehouses.find(query, {"_id": 0}).sort("name", 1).to_list(500)
    
    # Add branch name
    for wh in result:
        if wh.get("branch_id"):
            branch = await db["branches"].find_one({"id": wh["branch_id"]}, {"_id": 0, "name": 1})
            wh["branch_name"] = branch["name"] if branch else ""
    
    return result

@router.post("/warehouses")
async def create_warehouse(data: WarehouseCreate, user: dict = Depends(get_current_user)):
    existing = await warehouses.find_one({"code": data.code})
    if existing:
        raise HTTPException(status_code=400, detail="Kode gudang sudah ada")
    
    warehouse = {
        "id": str(uuid.uuid4()),
        **data.model_dump(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await warehouses.insert_one(warehouse)
    return {"id": warehouse["id"], "message": "Gudang berhasil ditambahkan"}

@router.put("/warehouses/{warehouse_id}")
async def update_warehouse(warehouse_id: str, data: WarehouseCreate, user: dict = Depends(get_current_user)):
    update_data = data.model_dump()
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await warehouses.update_one({"id": warehouse_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Gudang tidak ditemukan")
    return {"message": "Gudang berhasil diupdate"}

@router.delete("/warehouses/{warehouse_id}")
async def delete_warehouse(warehouse_id: str, request: Request, user: dict = Depends(require_permission("master_warehouse", "delete"))):
    """Delete warehouse - Requires master_warehouse.delete permission"""
    result = await warehouses.delete_one({"id": warehouse_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Gudang tidak ditemukan")
    await log_activity(db, user.get("user_id"), user.get("name", ""), "delete", "master_warehouse", f"Menghapus gudang: {warehouse_id}", request.client.host if request.client else "")
    return {"message": "Gudang berhasil dihapus"}

# ==================== SALES PERSONS ====================

class SalesPersonCreate(BaseModel):
    code: str
    name: str
    phone: str = ""
    email: str = ""
    branch_id: str = ""
    commission_percent: float = 0
    target_monthly: float = 0
    is_active: bool = True

@router.get("/sales-persons")
async def list_sales_persons(search: str = "", user: dict = Depends(get_current_user)):
    query = {}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"code": {"$regex": search, "$options": "i"}}
        ]
    result = await sales_persons.find(query, {"_id": 0}).sort("name", 1).to_list(500)
    
    for sp in result:
        if sp.get("branch_id"):
            branch = await db["branches"].find_one({"id": sp["branch_id"]}, {"_id": 0, "name": 1})
            sp["branch_name"] = branch["name"] if branch else ""
    
    return result

@router.post("/sales-persons")
async def create_sales_person(data: SalesPersonCreate, user: dict = Depends(get_current_user)):
    existing = await sales_persons.find_one({"code": data.code})
    if existing:
        raise HTTPException(status_code=400, detail="Kode sales sudah ada")
    
    sp = {
        "id": str(uuid.uuid4()),
        **data.model_dump(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await sales_persons.insert_one(sp)
    return {"id": sp["id"], "message": "Sales berhasil ditambahkan"}

@router.put("/sales-persons/{sp_id}")
async def update_sales_person(sp_id: str, data: SalesPersonCreate, user: dict = Depends(get_current_user)):
    update_data = data.model_dump()
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await sales_persons.update_one({"id": sp_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Sales tidak ditemukan")
    return {"message": "Sales berhasil diupdate"}

@router.delete("/sales-persons/{sp_id}")
async def delete_sales_person(sp_id: str, request: Request, user: dict = Depends(require_permission("master_sales_person", "delete"))):
    """Delete sales person - Requires master_sales_person.delete permission"""
    result = await sales_persons.delete_one({"id": sp_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Sales tidak ditemukan")
    await log_activity(db, user.get("user_id"), user.get("name", ""), "delete", "master_sales_person", f"Menghapus sales: {sp_id}", request.client.host if request.client else "")
    return {"message": "Sales berhasil dihapus"}

@router.get("/salesmen")
async def list_salesmen(search: str = "", user: dict = Depends(get_current_user)):
    """
    Get all active salesmen from users table.
    Query: SELECT * FROM users WHERE role = 'sales' AND status = 'active'
    Also includes kasir role as they can also make sales.
    """
    query = {
        "role": {"$in": ["sales", "kasir"]},
        "$or": [
            {"is_active": True},
            {"is_active": {"$exists": False}},  # Treat missing field as active
            {"status": "active"}
        ]
    }
    
    if search:
        query["$and"] = [
            {"$or": [
                {"name": {"$regex": search, "$options": "i"}},
                {"email": {"$regex": search, "$options": "i"}}
            ]}
        ]
    
    result = await db["users"].find(query, {"_id": 0, "password": 0}).sort("name", 1).to_list(500)
    return result

# ==================== CUSTOMER GROUPS ====================

class CustomerGroupCreate(BaseModel):
    code: str
    name: str
    discount_percent: float = 0
    price_level: int = 1  # 1-5 untuk mapping ke harga item
    description: str = ""

@router.get("/customer-groups")
async def list_customer_groups(search: str = "", user: dict = Depends(get_current_user)):
    query = {}
    if search:
        query["name"] = {"$regex": search, "$options": "i"}
    result = await customer_groups.find(query, {"_id": 0}).sort("name", 1).to_list(500)
    return result

@router.post("/customer-groups")
async def create_customer_group(data: CustomerGroupCreate, user: dict = Depends(get_current_user)):
    group = {
        "id": str(uuid.uuid4()),
        **data.model_dump(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await customer_groups.insert_one(group)
    return {"id": group["id"], "message": "Grup pelanggan berhasil ditambahkan"}

@router.put("/customer-groups/{group_id}")
async def update_customer_group(group_id: str, data: CustomerGroupCreate, user: dict = Depends(get_current_user)):
    update_data = data.model_dump()
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await customer_groups.update_one({"id": group_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Grup tidak ditemukan")
    return {"message": "Grup pelanggan berhasil diupdate"}

@router.delete("/customer-groups/{group_id}")
async def delete_customer_group(group_id: str, request: Request, user: dict = Depends(require_permission("master_customer_group", "delete"))):
    """Delete customer group - Requires master_customer_group.delete permission"""
    result = await customer_groups.delete_one({"id": group_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Grup tidak ditemukan")
    await log_activity(db, user.get("user_id"), user.get("name", ""), "delete", "master_customer_group", f"Menghapus grup: {group_id}", request.client.host if request.client else "")
    return {"message": "Grup pelanggan berhasil dihapus"}

# ==================== BANKS ====================

class BankCreate(BaseModel):
    code: str
    name: str
    account_number: str = ""
    account_name: str = ""
    branch: str = ""
    is_active: bool = True

@router.get("/banks")
async def list_banks(search: str = "", user: dict = Depends(get_current_user)):
    query = {}
    if search:
        query["name"] = {"$regex": search, "$options": "i"}
    result = await banks.find(query, {"_id": 0}).sort("name", 1).to_list(500)
    return result

@router.post("/banks")
async def create_bank(data: BankCreate, user: dict = Depends(get_current_user)):
    bank = {
        "id": str(uuid.uuid4()),
        **data.model_dump(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await banks.insert_one(bank)
    return {"id": bank["id"], "message": "Bank berhasil ditambahkan"}

@router.put("/banks/{bank_id}")
async def update_bank(bank_id: str, data: BankCreate, user: dict = Depends(get_current_user)):
    update_data = data.model_dump()
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await banks.update_one({"id": bank_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Bank tidak ditemukan")
    return {"message": "Bank berhasil diupdate"}

@router.delete("/banks/{bank_id}")
async def delete_bank(bank_id: str, request: Request, user: dict = Depends(require_permission("master_bank", "delete"))):
    """Delete bank - Requires master_bank.delete permission"""
    result = await banks.delete_one({"id": bank_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Bank tidak ditemukan")
    await log_activity(db, user.get("user_id"), user.get("name", ""), "delete", "master_bank", f"Menghapus bank: {bank_id}", request.client.host if request.client else "")
    return {"message": "Bank berhasil dihapus"}

# ==================== DISCOUNTS ====================

class DiscountCreate(BaseModel):
    code: str
    name: str
    discount_type: str = "percentage"  # percentage, nominal, per_pcs, per_item, per_transaction, tiered
    discount_value: float = 0
    target_type: str = "all"  # all, item, category, brand, customer_group, branch
    target_ids: List[str] = []
    min_purchase: float = 0
    min_qty: int = 0
    start_date: str = ""
    end_date: str = ""
    start_time: str = ""
    end_time: str = ""
    priority: int = 1
    stackable: bool = False
    max_usage: int = 0
    max_usage_per_customer: int = 0
    tiers: List[dict] = []  # [{min_qty, min_amount, discount_value}]
    is_active: bool = True
    description: str = ""

@router.get("/discounts")
async def list_discounts(search: str = "", user: dict = Depends(get_current_user)):
    query = {}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"code": {"$regex": search, "$options": "i"}}
        ]
    result = await discounts.find(query, {"_id": 0}).sort("priority", 1).to_list(500)
    return result

@router.post("/discounts")
async def create_discount(data: DiscountCreate, user: dict = Depends(get_current_user)):
    existing = await discounts.find_one({"code": data.code})
    if existing:
        raise HTTPException(status_code=400, detail="Kode diskon sudah ada")
    
    discount = {
        "id": str(uuid.uuid4()),
        **data.model_dump(),
        "usage_count": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user.get("id")
    }
    await discounts.insert_one(discount)
    return {"id": discount["id"], "message": "Diskon berhasil ditambahkan"}

@router.put("/discounts/{discount_id}")
async def update_discount(discount_id: str, data: DiscountCreate, user: dict = Depends(get_current_user)):
    update_data = data.model_dump()
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await discounts.update_one({"id": discount_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Diskon tidak ditemukan")
    return {"message": "Diskon berhasil diupdate"}

@router.delete("/discounts/{discount_id}")
async def delete_discount(discount_id: str, request: Request, user: dict = Depends(require_permission("master_discount", "delete"))):
    """Delete discount - Requires master_discount.delete permission"""
    result = await discounts.delete_one({"id": discount_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Diskon tidak ditemukan")
    await log_activity(db, user.get("user_id"), user.get("name", ""), "delete", "master_discount", f"Menghapus diskon: {discount_id}", request.client.host if request.client else "")
    return {"message": "Diskon berhasil dihapus"}

# ==================== PROMOTIONS ====================

class PromotionCreate(BaseModel):
    code: str
    name: str
    promo_type: str = "product"  # product, category, brand, bundle, buy_x_get_y, special_price, quota
    description: str = ""
    
    # Trigger
    trigger_type: str = "item"  # item, qty, subtotal
    trigger_item_ids: List[str] = []
    trigger_category_ids: List[str] = []
    trigger_brand_ids: List[str] = []
    trigger_min_qty: int = 0
    trigger_min_subtotal: float = 0
    
    # Benefit
    benefit_type: str = "discount"  # discount, free_item, bundle_price, special_price
    benefit_discount_type: str = "percentage"
    benefit_discount_value: float = 0
    benefit_free_item_ids: List[str] = []
    benefit_free_qty: int = 0
    benefit_bundle_price: float = 0
    benefit_special_price: float = 0
    
    # Quota
    quota_limit: int = 0
    quota_used: int = 0
    
    # Period
    start_date: str = ""
    end_date: str = ""
    start_time: str = ""
    end_time: str = ""
    
    # Advanced
    priority: int = 1
    stackable: bool = False
    max_usage: int = 0
    
    is_active: bool = True

@router.get("/promotions")
async def list_promotions(search: str = "", user: dict = Depends(get_current_user)):
    query = {}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"code": {"$regex": search, "$options": "i"}}
        ]
    result = await promotions.find(query, {"_id": 0}).sort("priority", 1).to_list(500)
    return result

@router.post("/promotions")
async def create_promotion(data: PromotionCreate, user: dict = Depends(get_current_user)):
    existing = await promotions.find_one({"code": data.code})
    if existing:
        raise HTTPException(status_code=400, detail="Kode promosi sudah ada")
    
    promo = {
        "id": str(uuid.uuid4()),
        **data.model_dump(),
        "usage_count": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user.get("id")
    }
    await promotions.insert_one(promo)
    return {"id": promo["id"], "message": "Promosi berhasil ditambahkan"}

@router.put("/promotions/{promo_id}")
async def update_promotion(promo_id: str, data: PromotionCreate, user: dict = Depends(get_current_user)):
    update_data = data.model_dump()
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await promotions.update_one({"id": promo_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Promosi tidak ditemukan")
    return {"message": "Promosi berhasil diupdate"}

@router.delete("/promotions/{promo_id}")
async def delete_promotion(promo_id: str, request: Request, user: dict = Depends(require_permission("master_promotion", "delete"))):
    """Delete promotion - Requires master_promotion.delete permission"""
    result = await promotions.delete_one({"id": promo_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Promosi tidak ditemukan")
    await log_activity(db, user.get("user_id"), user.get("name", ""), "delete", "master_promotion", f"Menghapus promosi: {promo_id}", request.client.host if request.client else "")
    return {"message": "Promosi berhasil dihapus"}

# ==================== REGIONS ====================

regions = db["regions"]

class RegionCreate(BaseModel):
    code: str
    name: str
    parent_id: str = ""
    type: str = "province"  # province, city, district, village

@router.get("/regions")
async def list_regions(search: str = "", user: dict = Depends(get_current_user)):
    query = {}
    if search:
        query["name"] = {"$regex": search, "$options": "i"}
    result = await regions.find(query, {"_id": 0}).sort("name", 1).to_list(500)
    return result

@router.post("/regions")
async def create_region(data: RegionCreate, user: dict = Depends(get_current_user)):
    region = {
        "id": str(uuid.uuid4()),
        **data.model_dump(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await regions.insert_one(region)
    return {"id": region["id"], "message": "Wilayah berhasil ditambahkan"}

@router.put("/regions/{region_id}")
async def update_region(region_id: str, data: RegionCreate, user: dict = Depends(get_current_user)):
    update_data = data.model_dump()
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await regions.update_one({"id": region_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Wilayah tidak ditemukan")
    return {"message": "Wilayah berhasil diupdate"}

@router.delete("/regions/{region_id}")
async def delete_region(region_id: str, request: Request, user: dict = Depends(require_permission("master_region", "delete"))):
    """Delete region - Requires master_region.delete permission"""
    result = await regions.delete_one({"id": region_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Wilayah tidak ditemukan")
    await log_activity(db, user.get("user_id"), user.get("name", ""), "delete", "master_region", f"Menghapus wilayah: {region_id}", request.client.host if request.client else "")
    return {"message": "Wilayah berhasil dihapus"}

# ==================== E-MONEY ====================

emoney = db["emoney"]

class EmoneyCreate(BaseModel):
    code: str
    name: str
    provider: str = ""
    fee_percent: float = 0
    fee_fixed: float = 0
    is_active: bool = True

@router.get("/emoney")
async def list_emoney(search: str = "", user: dict = Depends(get_current_user)):
    query = {}
    if search:
        query["name"] = {"$regex": search, "$options": "i"}
    result = await emoney.find(query, {"_id": 0}).sort("name", 1).to_list(500)
    return result

@router.post("/emoney")
async def create_emoney(data: EmoneyCreate, user: dict = Depends(get_current_user)):
    em = {
        "id": str(uuid.uuid4()),
        **data.model_dump(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await emoney.insert_one(em)
    return {"id": em["id"], "message": "E-Money berhasil ditambahkan"}

@router.put("/emoney/{emoney_id}")
async def update_emoney(emoney_id: str, data: EmoneyCreate, user: dict = Depends(get_current_user)):
    update_data = data.model_dump()
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await emoney.update_one({"id": emoney_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="E-Money tidak ditemukan")
    return {"message": "E-Money berhasil diupdate"}

@router.delete("/emoney/{emoney_id}")
async def delete_emoney(emoney_id: str, request: Request, user: dict = Depends(require_permission("master_emoney", "delete"))):
    """Delete e-money - Requires master_emoney.delete permission"""
    result = await emoney.delete_one({"id": emoney_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="E-Money tidak ditemukan")
    await log_activity(db, user.get("user_id"), user.get("name", ""), "delete", "master_emoney", f"Menghapus e-money: {emoney_id}", request.client.host if request.client else "")
    return {"message": "E-Money berhasil dihapus"}

# ==================== SHIPPING COSTS ====================

shipping_costs = db["shipping_costs"]

class ShippingCostCreate(BaseModel):
    code: str
    name: str
    destination: str = ""
    cost: float = 0
    min_weight: float = 0
    max_weight: float = 0
    is_active: bool = True

@router.get("/shipping-costs")
async def list_shipping_costs(search: str = "", user: dict = Depends(get_current_user)):
    query = {}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"destination": {"$regex": search, "$options": "i"}}
        ]
    result = await shipping_costs.find(query, {"_id": 0}).sort("name", 1).to_list(500)
    return result

@router.post("/shipping-costs")
async def create_shipping_cost(data: ShippingCostCreate, user: dict = Depends(get_current_user)):
    sc = {
        "id": str(uuid.uuid4()),
        **data.model_dump(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await shipping_costs.insert_one(sc)
    return {"id": sc["id"], "message": "Ongkir berhasil ditambahkan"}

@router.put("/shipping-costs/{sc_id}")
async def update_shipping_cost(sc_id: str, data: ShippingCostCreate, user: dict = Depends(get_current_user)):
    update_data = data.model_dump()
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await shipping_costs.update_one({"id": sc_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Ongkir tidak ditemukan")
    return {"message": "Ongkir berhasil diupdate"}

@router.delete("/shipping-costs/{sc_id}")
async def delete_shipping_cost(sc_id: str, request: Request, user: dict = Depends(require_permission("master_shipping", "delete"))):
    """Delete shipping cost - Requires master_shipping.delete permission"""
    result = await shipping_costs.delete_one({"id": sc_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Ongkir tidak ditemukan")
    await log_activity(db, user.get("user_id"), user.get("name", ""), "delete", "master_shipping", f"Menghapus ongkir: {sc_id}", request.client.host if request.client else "")
    return {"message": "Ongkir berhasil dihapus"}

# ==================== CUSTOMER POINTS ====================

customer_points = db["customer_points"]

class CustomerPointCreate(BaseModel):
    customer_id: str
    points: int = 0
    total_earned: int = 0
    total_redeemed: int = 0

@router.get("/customer-points")
async def list_customer_points(search: str = "", user: dict = Depends(get_current_user)):
    pipeline = [
        {"$lookup": {
            "from": "customers",
            "localField": "customer_id",
            "foreignField": "id",
            "as": "customer"
        }},
        {"$unwind": {"path": "$customer", "preserveNullAndEmptyArrays": True}},
        {"$project": {
            "_id": 0,
            "id": 1,
            "customer_id": 1,
            "customer_name": "$customer.name",
            "points": 1,
            "total_earned": 1,
            "total_redeemed": 1
        }}
    ]
    if search:
        pipeline.insert(0, {"$match": {"$or": [
            {"customer.name": {"$regex": search, "$options": "i"}}
        ]}})
    result = await customer_points.aggregate(pipeline).to_list(500)
    return result


# ==================== ITEM TYPES (JENIS BARANG) ====================

item_types = db["item_types"]

class ItemTypeCreate(BaseModel):
    code: str
    name: str
    description: str = ""

@router.get("/item-types")
async def list_item_types(search: str = "", user: dict = Depends(get_current_user)):
    query = {}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"code": {"$regex": search, "$options": "i"}}
        ]
    result = await item_types.find(query, {"_id": 0}).sort("name", 1).to_list(500)
    
    # Return default types if empty
    if not result:
        default_types = [
            {"id": "IT001", "code": "AKS", "name": "Aksesoris", "description": "Aksesoris HP dan gadget"},
            {"id": "IT002", "code": "PLS", "name": "Pulsa", "description": "Pulsa dan voucher"},
            {"id": "IT003", "code": "KOT", "name": "Kuota", "description": "Paket data internet"},
            {"id": "IT004", "code": "HP", "name": "Handphone", "description": "Handphone dan smartphone"},
            {"id": "IT005", "code": "TAB", "name": "Tablet", "description": "Tablet dan iPad"},
            {"id": "IT006", "code": "LAP", "name": "Laptop", "description": "Laptop dan notebook"},
        ]
        return {"items": default_types, "total": len(default_types)}
    
    return {"items": result, "total": len(result)}

@router.post("/item-types")
async def create_item_type(data: ItemTypeCreate, user: dict = Depends(get_current_user)):
    existing = await item_types.find_one({"code": data.code})
    if existing:
        raise HTTPException(status_code=400, detail="Kode jenis barang sudah ada")
    
    item_type = {
        "id": str(uuid.uuid4()),
        "code": data.code,
        "name": data.name,
        "description": data.description,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await item_types.insert_one(item_type)
    item_type.pop("_id", None)
    return item_type

@router.put("/item-types/{item_type_id}")
async def update_item_type(item_type_id: str, data: ItemTypeCreate, user: dict = Depends(get_current_user)):
    result = await item_types.update_one(
        {"id": item_type_id},
        {"$set": {
            "code": data.code,
            "name": data.name,
            "description": data.description,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Jenis barang tidak ditemukan")
    return {"success": True}

@router.delete("/item-types/{item_type_id}")
async def delete_item_type(item_type_id: str, user: dict = Depends(get_current_user)):
    result = await item_types.delete_one({"id": item_type_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Jenis barang tidak ditemukan")
    return {"success": True}
