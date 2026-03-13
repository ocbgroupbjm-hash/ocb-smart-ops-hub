# OCB TITAN ERP - BACKUP & RESTORE API
# MASTER BLUEPRINT: Backup System API Endpoints
# RBAC: OWNER, SUPER_ADMIN only

from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from database import get_db
from utils.auth import get_current_user
import os
import sys
import json
import asyncio

# Add scripts path for imports
sys.path.append("/app/backend/scripts")

router = APIRouter(prefix="/system", tags=["Backup & Restore System"])

BACKUP_DIR = "/app/backend/backups"
ALLOWED_ROLES = ["owner", "super_admin"]

# ==================== PYDANTIC MODELS ====================

class BackupRequest(BaseModel):
    db_name: Optional[str] = None  # Specific database, or None for all
    include_all_tenants: bool = False
    backup_name: Optional[str] = None

class RestoreRequest(BaseModel):
    backup_file: str
    target_db: Optional[str] = None
    drop_existing: bool = True
    skip_validation: bool = False

class BackupStatus(BaseModel):
    backup_id: str
    status: str  # pending, in_progress, completed, failed
    progress: int  # 0-100
    message: str

# In-memory backup status tracking
backup_status_store: Dict[str, Dict] = {}


# ==================== RBAC CHECK ====================

def require_backup_role():
    """Middleware to check if user has backup permission"""
    async def check_role(request: Request, user: dict = Depends(get_current_user)):
        user_role = user.get("role", "").lower()
        user_role_code = user.get("role_code", "").lower()
        
        if user_role not in ALLOWED_ROLES and user_role_code not in ALLOWED_ROLES:
            # Also check permissions array
            permissions = user.get("permissions", [])
            if "*" not in permissions and "backup" not in permissions:
                raise HTTPException(
                    status_code=403,
                    detail="AKSES DITOLAK: Hanya OWNER atau SUPER_ADMIN yang dapat mengakses backup/restore"
                )
        return user
    return check_role


# ==================== AUDIT HELPER ====================

async def log_backup_audit(
    db,
    user_id: str,
    user_name: str,
    action: str,  # BACKUP_CREATED, RESTORE_EXECUTED, etc
    details: dict,
    ip_address: str = ""
):
    """Log backup/restore actions to audit log (append-only)"""
    import uuid
    
    audit_entry = {
        "id": str(uuid.uuid4()),
        "tenant_id": db.name,
        "user_id": user_id,
        "user_name": user_name,
        "action": action,
        "module": "backup_restore",
        "entity_type": "system",
        "entity_id": details.get("backup_id", ""),
        "before_data": None,
        "after_data": details,
        "description": f"{action} by {user_name}",
        "ip_address": ip_address,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "timestamp_unix": int(datetime.now(timezone.utc).timestamp() * 1000)
    }
    
    await db["audit_logs"].insert_one(audit_entry)


# ==================== API ENDPOINTS ====================

@router.post("/backup")
async def create_backup(
    data: BackupRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    user: dict = Depends(require_backup_role())
):
    """
    POST /api/system/backup
    
    Create database backup.
    
    RBAC: OWNER, SUPER_ADMIN only
    
    Body:
    - db_name: Specific database to backup (optional)
    - include_all_tenants: If true, backup all active tenants
    - backup_name: Custom backup name (optional)
    
    Returns backup metadata with backup_id for status tracking.
    """
    from backup_system import BackupSystem
    
    db = get_db()
    user_id = user.get("user_id", "")
    user_name = user.get("name", "Unknown")
    ip_address = request.client.host if request.client else ""
    
    # Create backup synchronously (fast operation)
    backup_system = BackupSystem()
    
    try:
        result = await backup_system.create_full_backup(
            db_name=data.db_name,
            include_all_tenants=data.include_all_tenants,
            backup_name=data.backup_name,
            created_by=user_name
        )
        
        if result.get("success"):
            # Log to audit
            await log_backup_audit(
                db=db,
                user_id=user_id,
                user_name=user_name,
                action="BACKUP_CREATED",
                details={
                    "backup_id": result["metadata"].get("backup_id"),
                    "file_name": result["metadata"].get("file_name"),
                    "file_size_mb": result["metadata"].get("file_size_mb"),
                    "databases": result["metadata"].get("databases_backed_up", [])
                },
                ip_address=ip_address
            )
            
            return {
                "success": True,
                "message": "Backup created successfully",
                "backup_id": result["metadata"].get("backup_id"),
                "backup_file": result.get("backup_file"),
                "metadata": result.get("metadata")
            }
        else:
            # Log failure
            await log_backup_audit(
                db=db,
                user_id=user_id,
                user_name=user_name,
                action="BACKUP_FAILED",
                details={"error": result.get("error", "Unknown error")},
                ip_address=ip_address
            )
            
            raise HTTPException(
                status_code=500,
                detail=f"Backup failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backup error: {str(e)}")


@router.post("/restore")
async def restore_database(
    data: RestoreRequest,
    request: Request,
    user: dict = Depends(require_backup_role())
):
    """
    POST /api/system/restore
    
    Restore database from backup.
    
    RBAC: OWNER, SUPER_ADMIN only
    
    Body:
    - backup_file: Path to backup .gz file
    - target_db: Restore to specific database (optional)
    - drop_existing: Drop existing collections before restore (default: true)
    - skip_validation: Skip pre-restore checksum validation (default: false)
    
    WARNING: This will REPLACE existing data!
    """
    from restore_system import RestoreSystem
    from validate_restore import RestoreValidator
    
    db = get_db()
    user_id = user.get("user_id", "")
    user_name = user.get("name", "Unknown")
    ip_address = request.client.host if request.client else ""
    
    # Verify backup file exists
    if not os.path.exists(data.backup_file):
        raise HTTPException(
            status_code=404,
            detail=f"Backup file not found: {data.backup_file}"
        )
    
    restore_system = RestoreSystem()
    
    try:
        # Execute restore
        result = await restore_system.restore_full_database(
            backup_file=data.backup_file,
            target_db=data.target_db,
            drop_existing=data.drop_existing,
            skip_validation=data.skip_validation,
            restored_by=user_name
        )
        
        if not result.get("success"):
            await log_backup_audit(
                db=db,
                user_id=user_id,
                user_name=user_name,
                action="RESTORE_FAILED",
                details={"error": result.get("error", "Unknown error"), "backup_file": data.backup_file},
                ip_address=ip_address
            )
            
            raise HTTPException(
                status_code=500,
                detail=f"Restore failed: {result.get('error', 'Unknown error')}"
            )
        
        # Run post-restore validation
        validator = RestoreValidator()
        target_db = data.target_db or "ocb_titan"
        validation_result = await validator.validate_database(target_db)
        
        # Check if validation passed
        if validation_result.get("status") == "CRITICAL_FAIL":
            await log_backup_audit(
                db=db,
                user_id=user_id,
                user_name=user_name,
                action="RESTORE_VALIDATION_FAILED",
                details={
                    "restore_id": result.get("restore_id"),
                    "backup_file": data.backup_file,
                    "validation": validation_result
                },
                ip_address=ip_address
            )
            
            raise HTTPException(
                status_code=500,
                detail="RESTORE FAIL: Trial Balance tidak balance! SUM(debit) != SUM(credit)"
            )
        
        # Log success
        await log_backup_audit(
            db=db,
            user_id=user_id,
            user_name=user_name,
            action="RESTORE_EXECUTED",
            details={
                "restore_id": result.get("restore_id"),
                "backup_file": data.backup_file,
                "target_db": target_db,
                "duration_seconds": result.get("duration_seconds"),
                "validation_status": validation_result.get("status")
            },
            ip_address=ip_address
        )
        
        return {
            "success": True,
            "message": "Database restored and validated successfully",
            "restore_id": result.get("restore_id"),
            "validation": validation_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Restore error: {str(e)}")


@router.get("/backup/status")
async def get_backup_status(
    backup_id: Optional[str] = None,
    user: dict = Depends(require_backup_role())
):
    """
    GET /api/system/backup/status
    
    Get backup status and list of available backups.
    
    Query params:
    - backup_id: Specific backup ID to check (optional)
    
    RBAC: OWNER, SUPER_ADMIN only
    """
    from backup_system import BackupSystem
    
    backup_system = BackupSystem()
    
    if backup_id:
        # Get specific backup status
        if backup_id in backup_status_store:
            return backup_status_store[backup_id]
        
        # Check in backup files
        backups = await backup_system.list_backups()
        for b in backups:
            if b.get("backup_id") == backup_id:
                return {
                    "backup_id": backup_id,
                    "status": "completed" if b.get("exists") else "file_missing",
                    "metadata": b
                }
        
        raise HTTPException(status_code=404, detail=f"Backup not found: {backup_id}")
    
    # List all backups
    backups = await backup_system.list_backups()
    
    return {
        "backups": backups,
        "total": len(backups),
        "backup_directory": BACKUP_DIR
    }


@router.get("/backup/list")
async def list_backups(
    user: dict = Depends(require_backup_role())
):
    """
    GET /api/system/backup/list
    
    List all available backup files.
    
    RBAC: OWNER, SUPER_ADMIN only
    """
    from backup_system import BackupSystem
    
    backup_system = BackupSystem()
    backups = await backup_system.list_backups()
    
    return {
        "success": True,
        "backups": backups,
        "total": len(backups)
    }


@router.get("/backup/verify/{backup_id}")
async def verify_backup(
    backup_id: str,
    user: dict = Depends(require_backup_role())
):
    """
    GET /api/system/backup/verify/{backup_id}
    
    Verify backup file integrity (checksum validation).
    
    RBAC: OWNER, SUPER_ADMIN only
    """
    from backup_system import BackupSystem
    
    backup_system = BackupSystem()
    backups = await backup_system.list_backups()
    
    # Find backup by ID
    target_backup = None
    for b in backups:
        if b.get("backup_id") == backup_id:
            target_backup = b
            break
    
    if not target_backup:
        raise HTTPException(status_code=404, detail=f"Backup not found: {backup_id}")
    
    backup_file = target_backup.get("file_path", "")
    result = await backup_system.verify_backup(backup_file)
    
    return {
        "backup_id": backup_id,
        "verification": result
    }


@router.delete("/backup/{backup_id}")
async def delete_backup(
    backup_id: str,
    request: Request,
    user: dict = Depends(require_backup_role())
):
    """
    DELETE /api/system/backup/{backup_id}
    
    Delete a backup file.
    
    RBAC: OWNER only
    """
    # Only owner can delete
    if user.get("role", "").lower() != "owner":
        raise HTTPException(
            status_code=403,
            detail="AKSES DITOLAK: Hanya OWNER yang dapat menghapus backup"
        )
    
    from backup_system import BackupSystem
    
    db = get_db()
    backup_system = BackupSystem()
    backups = await backup_system.list_backups()
    
    # Find backup by ID
    target_backup = None
    for b in backups:
        if b.get("backup_id") == backup_id:
            target_backup = b
            break
    
    if not target_backup:
        raise HTTPException(status_code=404, detail=f"Backup not found: {backup_id}")
    
    backup_file = target_backup.get("file_path", "")
    result = await backup_system.delete_backup(backup_file)
    
    # Audit log
    await log_backup_audit(
        db=db,
        user_id=user.get("user_id", ""),
        user_name=user.get("name", "Unknown"),
        action="BACKUP_DELETED",
        details={
            "backup_id": backup_id,
            "file_name": target_backup.get("file_name"),
            "deleted_files": result.get("deleted", [])
        },
        ip_address=request.client.host if request.client else ""
    )
    
    return {
        "success": result.get("success", False),
        "message": "Backup deleted" if result.get("success") else "Delete failed",
        "details": result
    }


@router.post("/validate")
async def validate_database_endpoint(
    db_name: str = "ocb_titan",
    user: dict = Depends(require_backup_role())
):
    """
    POST /api/system/validate
    
    Run post-restore validation on a database.
    
    Query params:
    - db_name: Database to validate (default: ocb_titan)
    
    RBAC: OWNER, SUPER_ADMIN only
    """
    from validate_restore import RestoreValidator
    
    validator = RestoreValidator()
    result = await validator.validate_database(db_name)
    
    return {
        "success": result.get("status") == "VALID",
        "validation": result
    }
