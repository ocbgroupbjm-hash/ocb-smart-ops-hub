# OCB TITAN ERP - Maintenance Mode System
# WAJIB untuk perbaikan data integrity

from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone
from database import get_db
from utils.auth import get_current_user
from typing import Dict, Any
import uuid

router = APIRouter(prefix="/api/system", tags=["System Maintenance"])

# In-memory maintenance state (bisa diganti dengan Redis untuk production)
MAINTENANCE_STATE = {
    "active": False,
    "mode": None,
    "started_at": None,
    "started_by": None,
    "reason": None
}

ALLOWED_MODES = [
    "ACCOUNTING_FIX",
    "DATA_MIGRATION", 
    "BACKUP_RESTORE",
    "SYSTEM_UPGRADE"
]

@router.post("/maintenance-mode")
async def activate_maintenance_mode(
    data: Dict[str, Any],
    user: dict = Depends(get_current_user)
):
    """
    Aktifkan maintenance mode untuk mencegah transaksi baru.
    Hanya OWNER/SUPER_ADMIN yang bisa mengaktifkan.
    """
    role = user.get("role_code") or user.get("role") or ""
    if role not in ["owner", "super_admin"]:
        raise HTTPException(status_code=403, detail="Hanya Owner/Super Admin yang bisa mengaktifkan maintenance mode")
    
    mode = data.get("mode", "ACCOUNTING_FIX")
    if mode not in ALLOWED_MODES:
        raise HTTPException(status_code=400, detail=f"Mode tidak valid. Gunakan: {ALLOWED_MODES}")
    
    MAINTENANCE_STATE["active"] = True
    MAINTENANCE_STATE["mode"] = mode
    MAINTENANCE_STATE["started_at"] = datetime.now(timezone.utc).isoformat()
    MAINTENANCE_STATE["started_by"] = user.get("user_id") or user.get("id")
    MAINTENANCE_STATE["reason"] = data.get("reason", "Data integrity fix")
    
    # Log ke audit
    db = get_db()
    await db["audit_logs"].insert_one({
        "id": str(uuid.uuid4()),
        "action": "MAINTENANCE_MODE_ACTIVATED",
        "module": "system",
        "entity_type": "maintenance",
        "entity_id": mode,
        "user_id": user.get("user_id") or user.get("id"),
        "user_name": user.get("name") or user.get("email"),
        "details": {
            "mode": mode,
            "reason": MAINTENANCE_STATE["reason"]
        },
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {
        "status": "activated",
        "mode": mode,
        "started_at": MAINTENANCE_STATE["started_at"],
        "message": f"Maintenance mode '{mode}' diaktifkan. Transaksi baru diblokir."
    }


@router.delete("/maintenance-mode")
async def deactivate_maintenance_mode(
    user: dict = Depends(get_current_user)
):
    """
    Nonaktifkan maintenance mode.
    """
    role = user.get("role_code") or user.get("role") or ""
    if role not in ["owner", "super_admin"]:
        raise HTTPException(status_code=403, detail="Hanya Owner/Super Admin")
    
    if not MAINTENANCE_STATE["active"]:
        return {"status": "already_inactive", "message": "Maintenance mode sudah tidak aktif"}
    
    # Log ke audit
    db = get_db()
    await db["audit_logs"].insert_one({
        "id": str(uuid.uuid4()),
        "action": "MAINTENANCE_MODE_DEACTIVATED",
        "module": "system",
        "entity_type": "maintenance",
        "entity_id": MAINTENANCE_STATE["mode"],
        "user_id": user.get("user_id") or user.get("id"),
        "user_name": user.get("name") or user.get("email"),
        "details": {
            "mode": MAINTENANCE_STATE["mode"],
            "duration_seconds": (datetime.now(timezone.utc) - datetime.fromisoformat(MAINTENANCE_STATE["started_at"].replace('Z', '+00:00'))).total_seconds() if MAINTENANCE_STATE["started_at"] else 0
        },
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    MAINTENANCE_STATE["active"] = False
    MAINTENANCE_STATE["mode"] = None
    MAINTENANCE_STATE["started_at"] = None
    MAINTENANCE_STATE["started_by"] = None
    MAINTENANCE_STATE["reason"] = None
    
    return {
        "status": "deactivated",
        "message": "Maintenance mode dinonaktifkan. Sistem normal kembali."
    }


@router.get("/maintenance-mode/status")
async def get_maintenance_status():
    """
    Cek status maintenance mode.
    Endpoint ini public untuk semua user.
    """
    return {
        "active": MAINTENANCE_STATE["active"],
        "mode": MAINTENANCE_STATE["mode"],
        "started_at": MAINTENANCE_STATE["started_at"],
        "reason": MAINTENANCE_STATE["reason"]
    }


def is_maintenance_active() -> bool:
    """Helper untuk cek maintenance mode dari modul lain"""
    return MAINTENANCE_STATE["active"]


def get_maintenance_mode() -> str:
    """Helper untuk get current mode"""
    return MAINTENANCE_STATE["mode"]
