# OCB AI TITAN - Backup & Restore Routes
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
from database import db
from utils.auth import get_current_user
import json
import io
import uuid

router = APIRouter(prefix="/api/backup", tags=["Backup"])

class BackupInfo(BaseModel):
    id: str
    name: str
    created_at: str
    size: str
    collections: List[str]

# Store backup metadata
backups_collection = db["backups"]

@router.get("/list")
async def list_backups(user: dict = Depends(get_current_user)):
    """List all available backups"""
    if user.get("role") not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Hanya owner/admin yang dapat melihat backup")
    
    backups = await backups_collection.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return {"backups": backups}

@router.post("/create")
async def create_backup(user: dict = Depends(get_current_user)):
    """Create a new database backup"""
    if user.get("role") not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Hanya owner/admin yang dapat membuat backup")
    
    # Define collections to backup
    collections_to_backup = [
        "users", "branches", "categories", "products", "customers",
        "suppliers", "transactions", "purchase_orders", "stock_movements",
        "chart_of_accounts", "journal_entries", "cash_transactions",
        "settings", "shifts"
    ]
    
    backup_data = {
        "metadata": {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": user.get("name"),
            "version": "1.0"
        },
        "collections": {}
    }
    
    total_records = 0
    for coll_name in collections_to_backup:
        try:
            collection = db[coll_name]
            docs = await collection.find({}, {"_id": 0}).to_list(100000)
            backup_data["collections"][coll_name] = docs
            total_records += len(docs)
        except Exception as e:
            print(f"Error backing up {coll_name}: {e}")
    
    # Create backup metadata
    backup_id = str(uuid.uuid4())
    backup_json = json.dumps(backup_data, default=str, ensure_ascii=False)
    backup_size = len(backup_json.encode('utf-8'))
    
    backup_info = {
        "id": backup_id,
        "name": f"backup_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user.get("name"),
        "size": f"{backup_size / 1024 / 1024:.2f} MB",
        "total_records": total_records,
        "collections": list(backup_data["collections"].keys()),
        "data": backup_json
    }
    
    await backups_collection.insert_one(backup_info)
    
    return {
        "id": backup_id,
        "message": "Backup berhasil dibuat",
        "name": backup_info["name"],
        "size": backup_info["size"],
        "total_records": total_records
    }

@router.get("/download/{backup_id}")
async def download_backup(backup_id: str, user: dict = Depends(get_current_user)):
    """Download a backup file"""
    if user.get("role") not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Hanya owner/admin yang dapat mengunduh backup")
    
    backup = await backups_collection.find_one({"id": backup_id}, {"_id": 0})
    if not backup:
        raise HTTPException(status_code=404, detail="Backup tidak ditemukan")
    
    backup_data = backup.get("data", "{}")
    buffer = io.BytesIO(backup_data.encode('utf-8'))
    
    return StreamingResponse(
        buffer,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={backup['name']}.json"}
    )

@router.delete("/{backup_id}")
async def delete_backup(backup_id: str, user: dict = Depends(get_current_user)):
    """Delete a backup"""
    if user.get("role") not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Hanya owner/admin yang dapat menghapus backup")
    
    result = await backups_collection.delete_one({"id": backup_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Backup tidak ditemukan")
    
    return {"message": "Backup berhasil dihapus"}

@router.post("/restore/{backup_id}")
async def restore_backup(backup_id: str, user: dict = Depends(get_current_user)):
    """Restore database from backup"""
    if user.get("role") not in ["owner"]:
        raise HTTPException(status_code=403, detail="Hanya owner yang dapat melakukan restore")
    
    backup = await backups_collection.find_one({"id": backup_id}, {"_id": 0})
    if not backup:
        raise HTTPException(status_code=404, detail="Backup tidak ditemukan")
    
    try:
        backup_data = json.loads(backup.get("data", "{}"))
        collections_data = backup_data.get("collections", {})
        
        restored_count = 0
        for coll_name, docs in collections_data.items():
            if docs:
                collection = db[coll_name]
                # Clear existing data
                await collection.delete_many({})
                # Insert backup data
                await collection.insert_many(docs)
                restored_count += len(docs)
        
        return {
            "message": "Restore berhasil",
            "total_records_restored": restored_count,
            "collections_restored": list(collections_data.keys())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal restore: {str(e)}")

@router.post("/upload")
async def upload_backup(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    """Upload and restore from backup file"""
    if user.get("role") not in ["owner"]:
        raise HTTPException(status_code=403, detail="Hanya owner yang dapat upload backup")
    
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="File harus berformat JSON")
    
    try:
        content = await file.read()
        backup_data = json.loads(content.decode('utf-8'))
        
        # Validate backup structure
        if "collections" not in backup_data:
            raise HTTPException(status_code=400, detail="Format backup tidak valid")
        
        collections_data = backup_data.get("collections", {})
        restored_count = 0
        
        for coll_name, docs in collections_data.items():
            if docs:
                collection = db[coll_name]
                await collection.delete_many({})
                await collection.insert_many(docs)
                restored_count += len(docs)
        
        return {
            "message": "Upload dan restore berhasil",
            "total_records_restored": restored_count,
            "collections_restored": list(collections_data.keys())
        }
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="File JSON tidak valid")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal restore: {str(e)}")
