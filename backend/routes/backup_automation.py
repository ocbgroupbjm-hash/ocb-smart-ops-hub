"""
OCB TITAN ERP - BACKUP AUTOMATION SYSTEM
MASTER BLUEPRINT: Enterprise Hardening Phase - Guard System 7

Automated backup system dengan scheduler:
- Daily backup (setiap hari jam 01:00)
- Weekly backup (setiap Minggu)
- Monthly backup (tanggal 1 setiap bulan)

Config: backup_schedule_config.yml
Log: backup_run_log.json
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Optional, Dict, List
from datetime import datetime, timezone, timedelta
from database import get_db
from utils.auth import get_current_user
import os
import json
import yaml
import subprocess
import shutil
import asyncio
import uuid

router = APIRouter(prefix="/backup-automation", tags=["Backup Automation"])

# Configuration paths
CONFIG_PATH = "/app/backend/config/backup_schedule_config.yml"
BACKUP_DIR = "/app/backend/backups"
LOG_PATH = "/app/backend/backups/backup_run_log.json"

# Default configuration
DEFAULT_CONFIG = {
    "backup_schedule": {
        "daily": {
            "enabled": True,
            "time": "01:00",
            "retention_days": 7
        },
        "weekly": {
            "enabled": True,
            "day": "Sunday",
            "time": "02:00",
            "retention_weeks": 4
        },
        "monthly": {
            "enabled": True,
            "day": 1,
            "time": "03:00",
            "retention_months": 12
        }
    },
    "backup_settings": {
        "backup_directory": BACKUP_DIR,
        "include_tenants": ["ocb_titan", "ocb_baju", "ocb_counter", "ocb_unit_4", "ocb_unt_1"],
        "compression": True,
        "encryption": False,
        "max_concurrent_backups": 2
    },
    "notifications": {
        "on_success": True,
        "on_failure": True,
        "email_recipients": []
    }
}


class BackupAutomation:
    """Automated backup system for OCB TITAN ERP"""
    
    def __init__(self):
        self.config = self.load_config()
        os.makedirs(BACKUP_DIR, exist_ok=True)
    
    def load_config(self) -> Dict:
        """Load or create configuration"""
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r") as f:
                return yaml.safe_load(f) or DEFAULT_CONFIG
        else:
            self.save_config(DEFAULT_CONFIG)
            return DEFAULT_CONFIG
    
    def save_config(self, config: Dict):
        """Save configuration to file"""
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w") as f:
            yaml.dump(config, f, default_flow_style=False)
    
    def log_run(self, run_type: str, status: str, details: Dict):
        """Log backup run to JSON file"""
        entry = {
            "id": str(uuid.uuid4()),
            "run_type": run_type,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": details
        }
        
        # Load existing log
        existing = []
        if os.path.exists(LOG_PATH):
            try:
                with open(LOG_PATH, "r") as f:
                    existing = json.load(f)
            except:
                existing = []
        
        # Append and save
        existing.append(entry)
        
        # Keep last 500 entries
        if len(existing) > 500:
            existing = existing[-500:]
        
        with open(LOG_PATH, "w") as f:
            json.dump(existing, f, indent=2, default=str)
        
        return entry
    
    async def create_backup(self, backup_type: str, tenants: List[str] = None) -> Dict:
        """
        Create backup for specified tenants
        
        Args:
            backup_type: daily, weekly, monthly, manual
            tenants: List of tenant database names (None = all configured)
        """
        start_time = datetime.now(timezone.utc)
        backup_id = f"BKP-{backup_type.upper()}-{start_time.strftime('%Y%m%d_%H%M%S')}"
        
        settings = self.config.get("backup_settings", {})
        target_tenants = tenants or settings.get("include_tenants", ["ocb_titan"])
        
        results = {
            "backup_id": backup_id,
            "backup_type": backup_type,
            "start_time": start_time.isoformat(),
            "tenants": [],
            "total_size_bytes": 0
        }
        
        for tenant in target_tenants:
            tenant_result = await self._backup_tenant(tenant, backup_id)
            results["tenants"].append(tenant_result)
            results["total_size_bytes"] += tenant_result.get("size_bytes", 0)
        
        results["end_time"] = datetime.now(timezone.utc).isoformat()
        results["duration_seconds"] = (datetime.now(timezone.utc) - start_time).total_seconds()
        results["status"] = "SUCCESS" if all(t["status"] == "SUCCESS" for t in results["tenants"]) else "PARTIAL" if any(t["status"] == "SUCCESS" for t in results["tenants"]) else "FAILED"
        
        # Log the run
        self.log_run(backup_type, results["status"], results)
        
        return results
    
    async def _backup_tenant(self, tenant: str, backup_id: str) -> Dict:
        """Backup a single tenant database"""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"{tenant}_{backup_id}.gz"
        filepath = os.path.join(BACKUP_DIR, filename)
        
        try:
            # Get MongoDB connection details from environment
            mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
            
            # Use mongodump with gzip
            cmd = f"mongodump --uri='{mongo_url}' --db={tenant} --archive={filepath} --gzip"
            
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            
            if result.returncode == 0 and os.path.exists(filepath):
                size = os.path.getsize(filepath)
                return {
                    "tenant": tenant,
                    "status": "SUCCESS",
                    "filename": filename,
                    "filepath": filepath,
                    "size_bytes": size,
                    "size_mb": round(size / 1024 / 1024, 2)
                }
            else:
                return {
                    "tenant": tenant,
                    "status": "FAILED",
                    "error": result.stderr or "Unknown error"
                }
                
        except subprocess.TimeoutExpired:
            return {
                "tenant": tenant,
                "status": "FAILED",
                "error": "Backup timed out after 10 minutes"
            }
        except Exception as e:
            return {
                "tenant": tenant,
                "status": "FAILED",
                "error": str(e)
            }
    
    async def restore_backup(self, filepath: str, target_tenant: str = None) -> Dict:
        """
        Restore from backup file
        
        Args:
            filepath: Path to backup file
            target_tenant: Target database name (optional, uses original if not specified)
        """
        if not os.path.exists(filepath):
            return {"status": "FAILED", "error": f"Backup file not found: {filepath}"}
        
        try:
            mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
            
            # Determine target database
            if target_tenant:
                cmd = f"mongorestore --uri='{mongo_url}' --archive={filepath} --gzip --nsFrom='*' --nsTo='{target_tenant}.*' --drop"
            else:
                cmd = f"mongorestore --uri='{mongo_url}' --archive={filepath} --gzip --drop"
            
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=1200  # 20 minute timeout
            )
            
            if result.returncode == 0:
                return {
                    "status": "SUCCESS",
                    "filepath": filepath,
                    "target_tenant": target_tenant,
                    "message": "Restore completed successfully"
                }
            else:
                return {
                    "status": "FAILED",
                    "error": result.stderr or "Unknown restore error"
                }
                
        except Exception as e:
            return {
                "status": "FAILED",
                "error": str(e)
            }
    
    def cleanup_old_backups(self) -> Dict:
        """Remove old backups based on retention policy"""
        schedule = self.config.get("backup_schedule", {})
        
        deleted = []
        kept = []
        now = datetime.now()
        
        if not os.path.exists(BACKUP_DIR):
            return {"deleted": [], "kept": [], "message": "Backup directory not found"}
        
        for filename in os.listdir(BACKUP_DIR):
            if not filename.endswith('.gz'):
                continue
            
            filepath = os.path.join(BACKUP_DIR, filename)
            file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
            age_days = (now - file_time).days
            
            # Determine retention based on backup type
            should_delete = False
            
            if "DAILY" in filename:
                retention = schedule.get("daily", {}).get("retention_days", 7)
                should_delete = age_days > retention
            elif "WEEKLY" in filename:
                retention_weeks = schedule.get("weekly", {}).get("retention_weeks", 4)
                should_delete = age_days > (retention_weeks * 7)
            elif "MONTHLY" in filename:
                retention_months = schedule.get("monthly", {}).get("retention_months", 12)
                should_delete = age_days > (retention_months * 30)
            else:
                # Manual backups - keep 30 days by default
                should_delete = age_days > 30
            
            if should_delete:
                try:
                    os.remove(filepath)
                    deleted.append(filename)
                except Exception as e:
                    kept.append({"filename": filename, "error": str(e)})
            else:
                kept.append(filename)
        
        return {
            "deleted_count": len(deleted),
            "deleted": deleted,
            "kept_count": len([k for k in kept if isinstance(k, str)]),
            "kept": kept
        }
    
    def list_backups(self) -> List[Dict]:
        """List all available backups"""
        backups = []
        
        if not os.path.exists(BACKUP_DIR):
            return []
        
        for filename in os.listdir(BACKUP_DIR):
            if filename.endswith(('.gz', '.dump', '.ocb')):
                filepath = os.path.join(BACKUP_DIR, filename)
                stat = os.stat(filepath)
                
                # Parse backup type from filename
                backup_type = "manual"
                if "DAILY" in filename:
                    backup_type = "daily"
                elif "WEEKLY" in filename:
                    backup_type = "weekly"
                elif "MONTHLY" in filename:
                    backup_type = "monthly"
                
                # Parse tenant from filename
                tenant = filename.split("_BKP")[0] if "_BKP" in filename else filename.split("_")[0]
                
                backups.append({
                    "filename": filename,
                    "filepath": filepath,
                    "tenant": tenant,
                    "backup_type": backup_type,
                    "size_bytes": stat.st_size,
                    "size_mb": round(stat.st_size / 1024 / 1024, 2),
                    "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
        
        backups.sort(key=lambda x: x["created_at"], reverse=True)
        return backups
    
    def get_run_history(self, limit: int = 50) -> List[Dict]:
        """Get backup run history"""
        if not os.path.exists(LOG_PATH):
            return []
        
        try:
            with open(LOG_PATH, "r") as f:
                history = json.load(f)
            return history[-limit:][::-1]  # Latest first
        except:
            return []


# Global instance
backup_automation = BackupAutomation()


# ==================== API ENDPOINTS ====================

@router.get("/config")
async def get_backup_config(
    user: dict = Depends(get_current_user)
):
    """Get current backup configuration"""
    return {
        "config": backup_automation.config,
        "config_path": CONFIG_PATH
    }


@router.put("/config")
async def update_backup_config(
    config: Dict,
    user: dict = Depends(get_current_user)
):
    """Update backup configuration (owner only)"""
    user_role = (user.get("role", "") or user.get("role_code", "")).lower()
    if user_role not in ["owner", "admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="AKSES DITOLAK")
    
    backup_automation.save_config(config)
    backup_automation.config = config
    
    return {
        "success": True,
        "message": "Configuration updated",
        "config": config
    }


@router.get("/list")
async def list_backups(
    user: dict = Depends(get_current_user)
):
    """List all available backups"""
    backups = backup_automation.list_backups()
    
    return {
        "backups": backups,
        "total": len(backups),
        "backup_directory": BACKUP_DIR
    }


@router.get("/history")
async def get_backup_history(
    limit: int = 50,
    user: dict = Depends(get_current_user)
):
    """Get backup run history"""
    history = backup_automation.get_run_history(limit)
    
    return {
        "history": history,
        "total": len(history)
    }


@router.post("/run/daily")
async def run_daily_backup(
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user)
):
    """Trigger daily backup manually"""
    user_role = (user.get("role", "") or user.get("role_code", "")).lower()
    if user_role not in ["owner", "admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="AKSES DITOLAK")
    
    result = await backup_automation.create_backup("daily")
    
    return result


@router.post("/run/weekly")
async def run_weekly_backup(
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user)
):
    """Trigger weekly backup manually"""
    user_role = (user.get("role", "") or user.get("role_code", "")).lower()
    if user_role not in ["owner", "admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="AKSES DITOLAK")
    
    result = await backup_automation.create_backup("weekly")
    
    return result


@router.post("/run/monthly")
async def run_monthly_backup(
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user)
):
    """Trigger monthly backup manually"""
    user_role = (user.get("role", "") or user.get("role_code", "")).lower()
    if user_role not in ["owner", "admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="AKSES DITOLAK")
    
    result = await backup_automation.create_backup("monthly")
    
    return result


@router.post("/run/manual")
async def run_manual_backup(
    tenants: List[str] = None,
    user: dict = Depends(get_current_user)
):
    """Run manual backup for specified tenants"""
    user_role = (user.get("role", "") or user.get("role_code", "")).lower()
    if user_role not in ["owner", "admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="AKSES DITOLAK")
    
    result = await backup_automation.create_backup("manual", tenants)
    
    return result


@router.post("/restore")
async def restore_from_backup(
    filename: str,
    target_tenant: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Restore from a backup file (owner only)"""
    user_role = (user.get("role", "") or user.get("role_code", "")).lower()
    if user_role != "owner":
        raise HTTPException(status_code=403, detail="AKSES DITOLAK: Hanya OWNER yang dapat melakukan restore")
    
    filepath = os.path.join(BACKUP_DIR, filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"Backup file tidak ditemukan: {filename}")
    
    result = await backup_automation.restore_backup(filepath, target_tenant)
    
    return result


@router.post("/cleanup")
async def cleanup_old_backups(
    user: dict = Depends(get_current_user)
):
    """Remove old backups based on retention policy"""
    user_role = (user.get("role", "") or user.get("role_code", "")).lower()
    if user_role not in ["owner", "admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="AKSES DITOLAK")
    
    result = backup_automation.cleanup_old_backups()
    
    return result


@router.get("/status")
async def get_backup_status(
    user: dict = Depends(get_current_user)
):
    """Get current backup system status"""
    backups = backup_automation.list_backups()
    history = backup_automation.get_run_history(10)
    
    # Find latest backups by type
    latest_daily = next((b for b in backups if b["backup_type"] == "daily"), None)
    latest_weekly = next((b for b in backups if b["backup_type"] == "weekly"), None)
    latest_monthly = next((b for b in backups if b["backup_type"] == "monthly"), None)
    
    # Calculate total backup size
    total_size = sum(b["size_bytes"] for b in backups)
    
    return {
        "status": "HEALTHY" if latest_daily else "WARNING",
        "total_backups": len(backups),
        "total_size_mb": round(total_size / 1024 / 1024, 2),
        "latest_backups": {
            "daily": latest_daily,
            "weekly": latest_weekly,
            "monthly": latest_monthly
        },
        "recent_runs": history[:5],
        "config": backup_automation.config.get("backup_schedule", {})
    }


@router.post("/verify/{filename}")
async def verify_backup(
    filename: str,
    user: dict = Depends(get_current_user)
):
    """Verify backup file integrity"""
    filepath = os.path.join(BACKUP_DIR, filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"Backup file tidak ditemukan: {filename}")
    
    # Check if file is valid gzip
    try:
        import gzip
        with gzip.open(filepath, 'rb') as f:
            # Read first few bytes to verify
            f.read(1024)
        
        stat = os.stat(filepath)
        
        return {
            "filename": filename,
            "status": "VALID",
            "size_bytes": stat.st_size,
            "size_mb": round(stat.st_size / 1024 / 1024, 2),
            "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
        }
    except Exception as e:
        return {
            "filename": filename,
            "status": "INVALID",
            "error": str(e)
        }
