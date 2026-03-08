# OCB AI TITAN - Business Management Routes
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
import os
import json
from database import set_active_db_name, get_active_db_name

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
    """List all available businesses/databases"""
    businesses = load_businesses()
    # Get current active database from memory
    current_db = get_active_db_name()
    return {
        "businesses": businesses,
        "current_db": current_db
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
    businesses = load_businesses()
    
    # Verify business exists
    business = next((b for b in businesses if b['db_name'] == db_name), None)
    if not business:
        raise HTTPException(status_code=404, detail="Database bisnis tidak ditemukan")
    
    # Update active database in memory (RUNTIME SWITCH - no restart needed!)
    set_active_db_name(db_name)
    
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
        
        return {
            "message": f"Berhasil switch ke bisnis '{business['name']}'",
            "db_name": db_name,
            "business": business,
            "restart_required": False  # No restart needed anymore!
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal switch database: {str(e)}")

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
