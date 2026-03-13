"""
OCB TITAN AI - Backup Manager API Routes
========================================
Endpoints untuk backup & restore system
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import os
import sys

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.backup_restore_system import BackupManager, BACKUP_DIR, ACTIVE_TENANTS
from utils.auth import get_current_user

router = APIRouter(prefix="/api/backup", tags=["Backup & Restore"])

# Request models
class CreateBackupRequest(BaseModel):
    backup_type: str  # "database", "snapshot", "full"
    tenants: Optional[List[str]] = None

class RestoreRequest(BaseModel):
    filename: str
    dry_run: bool = True

class ScheduleBackupRequest(BaseModel):
    frequency: str  # "daily", "weekly", "monthly"
    time: str  # "02:00"
    enabled: bool = True


def get_backup_manager():
    mongo_url = os.environ.get("MONGO_URL")
    return BackupManager(mongo_url)


@router.get("/list")
async def list_backups(user: dict = Depends(get_current_user)):
    """List all available backups"""
    user_role = user.get("role_code") or user.get("role")
    if user_role not in ["owner", "super_admin"]:
        raise HTTPException(status_code=403, detail="Only owner/super_admin can access backups")
    
    manager = get_backup_manager()
    backups = await manager.list_backups()
    
    return {
        "total": len(backups),
        "backups": backups
    }


@router.post("/create")
async def create_backup(
    request: CreateBackupRequest,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user)
):
    """Create a new backup"""
    user_role = user.get("role_code") or user.get("role")
    if user_role not in ["owner", "super_admin"]:
        raise HTTPException(status_code=403, detail="Only owner/super_admin can create backups")
    
    manager = get_backup_manager()
    
    if request.backup_type == "database":
        # Single database backup
        tenant = request.tenants[0] if request.tenants else "ocb_titan"
        result = await manager.create_database_backup(tenant)
    
    elif request.backup_type == "snapshot":
        # Business snapshot
        tenant = request.tenants[0] if request.tenants else "ocb_titan"
        result = await manager.create_business_snapshot(tenant)
    
    elif request.backup_type == "full":
        # Full restore package
        tenants = request.tenants or ACTIVE_TENANTS
        result = await manager.create_full_restore_package(tenants)
    
    else:
        raise HTTPException(status_code=400, detail="Invalid backup type")
    
    return result


@router.get("/download/{filename}")
async def download_backup(filename: str, user: dict = Depends(get_current_user)):
    """Download a backup file"""
    user_role = user.get("role_code") or user.get("role")
    if user_role not in ["owner", "super_admin"]:
        raise HTTPException(status_code=403, detail="Only owner/super_admin can download backups")
    
    filepath = f"{BACKUP_DIR}/{filename}"
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Backup file not found")
    
    return FileResponse(
        filepath,
        filename=filename,
        media_type="application/octet-stream"
    )


@router.post("/restore")
async def restore_backup(
    request: RestoreRequest,
    user: dict = Depends(get_current_user)
):
    """Restore from a backup file"""
    user_role = user.get("role_code") or user.get("role")
    if user_role not in ["owner", "super_admin"]:
        raise HTTPException(status_code=403, detail="Only owner/super_admin can restore backups")
    
    filepath = f"{BACKUP_DIR}/{request.filename}"
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Backup file not found")
    
    if not request.filename.endswith(".ocb"):
        raise HTTPException(status_code=400, detail="Only .ocb packages can be restored")
    
    manager = get_backup_manager()
    result = await manager.restore_from_package(filepath, dry_run=request.dry_run)
    
    return result


@router.delete("/{filename}")
async def delete_backup(filename: str, user: dict = Depends(get_current_user)):
    """Delete a backup file"""
    user_role = user.get("role_code") or user.get("role")
    if user_role not in ["owner", "super_admin"]:
        raise HTTPException(status_code=403, detail="Only owner/super_admin can delete backups")
    
    filepath = f"{BACKUP_DIR}/{filename}"
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Backup file not found")
    
    os.remove(filepath)
    
    return {"status": "deleted", "filename": filename}


@router.get("/schedule")
async def get_backup_schedule(user: dict = Depends(get_current_user)):
    """Get current backup schedule"""
    user_role = user.get("role_code") or user.get("role")
    if user_role not in ["owner", "super_admin"]:
        raise HTTPException(status_code=403, detail="Only owner/super_admin can view schedule")
    
    # Load from config file or return default
    config_path = f"{BACKUP_DIR}/schedule_config.json"
    
    if os.path.exists(config_path):
        import json
        with open(config_path) as f:
            return json.load(f)
    
    return {
        "frequency": "daily",
        "time": "02:00",
        "enabled": False,
        "last_backup": None
    }


@router.post("/schedule")
async def set_backup_schedule(
    request: ScheduleBackupRequest,
    user: dict = Depends(get_current_user)
):
    """Set backup schedule"""
    user_role = user.get("role_code") or user.get("role")
    if user_role not in ["owner", "super_admin"]:
        raise HTTPException(status_code=403, detail="Only owner/super_admin can set schedule")
    
    import json
    config_path = f"{BACKUP_DIR}/schedule_config.json"
    
    config = {
        "frequency": request.frequency,
        "time": request.time,
        "enabled": request.enabled,
        "updated_by": user.get("email"),
        "updated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
    }
    
    os.makedirs(BACKUP_DIR, exist_ok=True)
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    
    return {"status": "updated", "schedule": config}
