# OCB AI TITAN - Business Management Routes
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
import os
import json
from database import set_active_db_name, get_active_db_name, client
from utils.auth import hash_password

router = APIRouter(prefix="/api/business", tags=["Business Management"])

# File to store business list
BUSINESS_FILE = "/app/backend/data/businesses.json"

class Business(BaseModel):
    id: str
    name: str
    db_name: str
    description: Optional[str] = ""
    icon: Optional[str] = "store"
    color: Optional[str] = "#991B1B"
    created_at: Optional[str] = None

class CloneBusinessRequest(BaseModel):
    source_db: str
    target_name: str
    target_db_name: str
    target_description: Optional[str] = ""
    target_icon: Optional[str] = "store"
    target_color: Optional[str] = "#991B1B"
    clone_products: bool = True
    clone_categories: bool = True
    clone_suppliers: bool = True
    clone_customers: bool = True
    clone_coa: bool = True
    clone_settings: bool = True
    create_admin_user: bool = True
    admin_email: Optional[str] = None
    admin_password: Optional[str] = None

def ensure_data_dir():
    os.makedirs("/app/backend/data", exist_ok=True)
    if not os.path.exists(BUSINESS_FILE):
        # Create default business
        default_businesses = [
            {
                "id": "default",
                "name": "OCB GROUP",
                "db_name": "ocb_titan",
                "description": "Database utama",
                "icon": "building",
                "color": "#991B1B",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        ]
        with open(BUSINESS_FILE, 'w') as f:
            json.dump(default_businesses, f, indent=2)

def load_businesses() -> List[dict]:
    ensure_data_dir()
    try:
        with open(BUSINESS_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_businesses(businesses: List[dict]):
    ensure_data_dir()
    with open(BUSINESS_FILE, 'w') as f:
        json.dump(businesses, f, indent=2)

@router.get("/list")
async def list_businesses():
    """
    List all available businesses/databases for login page.
    
    SOURCE OF TRUTH: tenant_registry (_tenant_metadata collection)
    
    This endpoint now reads from _tenant_metadata in each database,
    NOT from businesses.json file.
    
    Returns tenants with status = 'active' OR 'ready'.
    """
    from routes.tenant_registry import get_all_tenants_from_registry
    
    # Get tenants from registry (source of truth)
    all_tenants = await get_all_tenants_from_registry()
    
    # Filter only active/ready tenants for login page
    visible_businesses = [
        t for t in all_tenants 
        if t.get("status") in ["active", "ready"]
        and t.get("show_in_login_selector", True)
    ]
    
    # Get current active database from memory
    current_db = get_active_db_name()
    
    return {
        "businesses": visible_businesses,
        "current_db": current_db,
        "source": "tenant_registry"  # Indicate source of truth
    }

@router.post("/create")
async def create_business(business: Business):
    """Create a new business/database"""
    businesses = load_businesses()
    
    # Check if db_name already exists
    for b in businesses:
        if b['db_name'] == business.db_name:
            raise HTTPException(status_code=400, detail="Nama database sudah digunakan")
        if b['id'] == business.id:
            raise HTTPException(status_code=400, detail="ID bisnis sudah digunakan")
    
    new_business = {
        "id": business.id,
        "name": business.name,
        "db_name": business.db_name,
        "description": business.description or "",
        "icon": business.icon or "store",
        "color": business.color or "#991B1B",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    businesses.append(new_business)
    save_businesses(businesses)
    
    return {"message": f"Bisnis '{business.name}' berhasil dibuat", "business": new_business}

@router.put("/{business_id}")
async def update_business(business_id: str, business: Business):
    """Update business details"""
    businesses = load_businesses()
    
    for i, b in enumerate(businesses):
        if b['id'] == business_id:
            businesses[i] = {
                **b,
                "name": business.name,
                "description": business.description or b.get('description', ''),
                "icon": business.icon or b.get('icon', 'store'),
                "color": business.color or b.get('color', '#991B1B'),
            }
            save_businesses(businesses)
            return {"message": "Bisnis berhasil diupdate"}
    
    raise HTTPException(status_code=404, detail="Bisnis tidak ditemukan")

@router.delete("/{business_id}")
async def delete_business(business_id: str):
    """Delete a business (not the database, just the entry)"""
    if business_id == "default":
        raise HTTPException(status_code=400, detail="Tidak dapat menghapus bisnis default")
    
    businesses = load_businesses()
    businesses = [b for b in businesses if b['id'] != business_id]
    save_businesses(businesses)
    
    return {"message": "Bisnis berhasil dihapus dari daftar"}

@router.post("/switch/{db_name}")
async def switch_business(db_name: str):
    """Switch to a different business/database"""
    
    # First check tenant_metadata (source of truth)
    from motor.motor_asyncio import AsyncIOMotorClient
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    mongo_client = AsyncIOMotorClient(mongo_url)
    
    try:
        target_db = mongo_client[db_name]
        metadata = await target_db["_tenant_metadata"].find_one({})
        
        # Check if tenant exists and is ready
        if metadata:
            status = metadata.get("status", "unknown")
            if status not in ["ready", "active"]:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Tenant {db_name} status: {status}. Hanya tenant READY yang bisa dipilih."
                )
        else:
            # Fallback: check businesses.json for backward compatibility
            businesses = load_businesses()
            business = next((b for b in businesses if b['db_name'] == db_name), None)
            if not business:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Database bisnis {db_name} tidak ditemukan atau belum siap"
                )
        
        # Update active database in memory for this request context
        set_active_db_name(db_name)
        
        # Also update default database for new logins
        from database import set_default_db_name
        set_default_db_name(db_name)
        
        # Also update .env file for persistence across restarts
        env_path = "/app/backend/.env"
        
        try:
            with open(env_path, 'r') as f:
                lines = f.readlines()
            
            new_lines = []
            db_found = False
            for line in lines:
                if line.startswith('DB_NAME='):
                    new_lines.append(f'DB_NAME={db_name}\n')
                    db_found = True
                else:
                    new_lines.append(line)
            
            if not db_found:
                new_lines.append(f'DB_NAME={db_name}\n')
            
            with open(env_path, 'w') as f:
                f.writelines(new_lines)
            
            company_name = metadata.get("company_name", db_name) if metadata else db_name
            
            return {
                "message": f"Berhasil switch ke bisnis '{company_name}'",
                "db_name": db_name,
                "tenant_id": db_name,
                "status": metadata.get("status") if metadata else "legacy",
                "restart_required": False,
                "note": "Token baru akan berisi tenant_id setelah login ulang"
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Gagal switch database: {str(e)}")
    finally:
        mongo_client.close()


@router.post("/ensure-admin/{db_name}")
async def ensure_admin_user(db_name: str, email: str = "ocbgroupbjm@gmail.com", password: str = "admin123"):
    """Ensure admin user exists in the specified database"""
    import uuid
    
    businesses = load_businesses()
    business = next((b for b in businesses if b['db_name'] == db_name), None)
    if not business:
        raise HTTPException(status_code=404, detail="Database tidak ditemukan")
    
    # Get database reference
    target_db = client[db_name]
    
    # Check if admin user exists
    existing = await target_db['users'].find_one({"email": email})
    if existing:
        return {"message": "Admin user sudah ada", "exists": True}
    
    # Create default branch if not exists
    branch = await target_db['branches'].find_one({"code": "HQ"})
    if not branch:
        branch = {
            "id": str(uuid.uuid4()),
            "code": "HQ",
            "name": "Headquarters",
            "address": "Main Office",
            "phone": "",
            "is_active": True,
            "is_warehouse": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await target_db['branches'].insert_one(branch)
    
    # Create admin user
    admin_user = {
        "id": str(uuid.uuid4()),
        "email": email,
        "password_hash": hash_password(password),
        "name": "Admin",
        "phone": "",
        "role": "owner",
        "branch_id": branch["id"],
        "branch_ids": [branch["id"]],
        "is_active": True,
        "permissions": [],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await target_db['users'].insert_one(admin_user)
    
    return {
        "message": f"Admin user berhasil dibuat di {business['name']}",
        "created": True,
        "email": email
    }

@router.get("/current")
async def get_current_business():
    """Get current active business"""
    current_db = get_active_db_name()
    businesses = load_businesses()
    
    business = next((b for b in businesses if b['db_name'] == current_db), None)
    
    return {
        "current_db": current_db,
        "business": business
    }

@router.post("/clone")
async def clone_business(request: CloneBusinessRequest):
    """Clone master data from one business to a new business"""
    import uuid
    
    businesses = load_businesses()
    
    # Validate source exists
    source_biz = next((b for b in businesses if b['db_name'] == request.source_db), None)
    if not source_biz:
        raise HTTPException(status_code=404, detail="Database sumber tidak ditemukan")
    
    # Validate target doesn't exist
    if any(b['db_name'] == request.target_db_name for b in businesses):
        raise HTTPException(status_code=400, detail="Nama database target sudah digunakan")
    
    try:
        # Get source and target database references
        source_db = client[request.source_db]
        target_db = client[request.target_db_name]
        
        cloned_counts = {}
        
        # Clone Categories
        if request.clone_categories:
            categories = await source_db['categories'].find({}, {"_id": 0}).to_list(None)
            if categories:
                await target_db['categories'].insert_many(categories)
                cloned_counts['categories'] = len(categories)
        
        # Clone Products (without stock data)
        if request.clone_products:
            products = await source_db['products'].find({}, {"_id": 0}).to_list(None)
            if products:
                # Reset stock-related fields
                for p in products:
                    p['stock'] = 0
                    p['reserved_stock'] = 0
                await target_db['products'].insert_many(products)
                cloned_counts['products'] = len(products)
        
        # Clone Suppliers
        if request.clone_suppliers:
            suppliers = await source_db['suppliers'].find({}, {"_id": 0}).to_list(None)
            if suppliers:
                await target_db['suppliers'].insert_many(suppliers)
                cloned_counts['suppliers'] = len(suppliers)
        
        # Clone Customers
        if request.clone_customers:
            customers = await source_db['customers'].find({}, {"_id": 0}).to_list(None)
            if customers:
                # Reset balance/points
                for c in customers:
                    c['balance'] = 0
                    c['points'] = 0
                    c['total_purchases'] = 0
                await target_db['customers'].insert_many(customers)
                cloned_counts['customers'] = len(customers)
        
        # Clone Chart of Accounts
        if request.clone_coa:
            coa = await source_db['chart_of_accounts'].find({}, {"_id": 0}).to_list(None)
            if coa:
                # Reset balances
                for acc in coa:
                    acc['balance'] = 0
                await target_db['chart_of_accounts'].insert_many(coa)
                cloned_counts['chart_of_accounts'] = len(coa)
        
        # Clone Settings
        if request.clone_settings:
            settings = await source_db['settings'].find({}, {"_id": 0}).to_list(None)
            if settings:
                await target_db['settings'].insert_many(settings)
                cloned_counts['settings'] = len(settings)
            
            print_settings = await source_db['print_settings'].find({}, {"_id": 0}).to_list(None)
            if print_settings:
                await target_db['print_settings'].insert_many(print_settings)
                cloned_counts['print_settings'] = len(print_settings)
        
        # Create default branch
        default_branch = {
            "id": str(uuid.uuid4()),
            "code": "HQ",
            "name": "Headquarters",
            "address": "Main Office",
            "phone": "",
            "is_active": True,
            "is_warehouse": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await target_db['branches'].insert_one(default_branch)
        cloned_counts['branches'] = 1
        
        # Create admin user if requested
        if request.create_admin_user and request.admin_email and request.admin_password:
            admin_user = {
                "id": str(uuid.uuid4()),
                "email": request.admin_email,
                "password_hash": hash_password(request.admin_password),
                "name": "Admin",
                "phone": "",
                "role": "owner",
                "branch_id": default_branch["id"],
                "branch_ids": [default_branch["id"]],
                "is_active": True,
                "permissions": [],
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await target_db['users'].insert_one(admin_user)
            cloned_counts['users'] = 1
        
        # Create business entry
        new_business_id = request.target_db_name.lower().replace(' ', '_')
        new_business = {
            "id": new_business_id,
            "name": request.target_name,
            "db_name": request.target_db_name,
            "description": request.target_description or f"Clone dari {source_biz['name']}",
            "icon": request.target_icon or "store",
            "color": request.target_color or "#991B1B",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "cloned_from": request.source_db
        }
        businesses.append(new_business)
        save_businesses(businesses)
        
        return {
            "message": f"Bisnis '{request.target_name}' berhasil di-clone dari '{source_biz['name']}'",
            "business": new_business,
            "cloned_data": cloned_counts
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal clone bisnis: {str(e)}")
