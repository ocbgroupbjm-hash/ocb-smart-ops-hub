#!/usr/bin/env python3
"""
OCB TITAN ERP - OFFICIAL BACKUP SYSTEM
MASTER BLUEPRINT: backup_system.py

Command:
mongodump --uri="mongodb://host:27017" --gzip --archive=/backups/ocb_backup_YYYYMMDD.gz

Output:
- backup_file.gz
- backup_metadata.json

Metadata wajib berisi:
- timestamp
- tenant_list
- blueprint_version
- db_version
- checksum
"""

import asyncio
import os
import json
import subprocess
import hashlib
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional, List, Dict

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
BACKUP_DIR = "/app/backend/backups"


class BackupSystem:
    def __init__(self, mongo_url: str = MONGO_URL):
        self.mongo_url = mongo_url
        self.client = None
        
    async def connect(self):
        self.client = AsyncIOMotorClient(self.mongo_url)
        
    async def disconnect(self):
        if self.client:
            self.client.close()
    
    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate SHA256 checksum of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    async def get_tenant_list(self) -> List[Dict]:
        """Get list of all active tenants"""
        tenants = []
        
        # Get from businesses.json registry
        businesses_file = "/app/backend/data/businesses.json"
        if os.path.exists(businesses_file):
            with open(businesses_file, "r") as f:
                businesses = json.load(f)
                for b in businesses:
                    if b.get("is_active") and not b.get("is_test") and not b.get("is_internal"):
                        tenants.append({
                            "id": b.get("id"),
                            "name": b.get("name"),
                            "db_name": b.get("db_name")
                        })
        
        return tenants
    
    async def get_blueprint_version(self, db_name: str) -> str:
        """Get blueprint version from tenant"""
        try:
            db = self.client[db_name]
            settings = await db["system_settings"].find_one({"key": "blueprint_version"})
            if settings:
                return settings.get("value", "unknown")
            
            # Check company_profile for version
            profile = await db["company_profile"].find_one({}, {"_id": 0, "blueprint_version": 1})
            if profile:
                return profile.get("blueprint_version", "unknown")
                
        except Exception:
            pass
        return "unknown"
    
    async def get_db_stats(self, db_name: str) -> Dict:
        """Get database statistics"""
        try:
            db = self.client[db_name]
            stats = await db.command("dbStats")
            return {
                "collections": stats.get("collections", 0),
                "objects": stats.get("objects", 0),
                "dataSize": stats.get("dataSize", 0),
                "storageSize": stats.get("storageSize", 0)
            }
        except Exception:
            return {}
    
    async def create_full_backup(
        self,
        db_name: str = None,
        include_all_tenants: bool = False,
        backup_name: str = None,
        created_by: str = "system"
    ) -> Dict:
        """
        Create full MongoDB dump backup
        
        Args:
            db_name: Specific database to backup (optional)
            include_all_tenants: If True, backup all tenant databases
            backup_name: Custom backup name
            created_by: User who initiated backup
        
        Returns:
            Backup metadata dict
        """
        await self.connect()
        
        timestamp = datetime.now(timezone.utc)
        timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
        
        # Ensure backup directory exists
        os.makedirs(BACKUP_DIR, exist_ok=True)
        
        # Determine backup file name
        if backup_name:
            archive_name = f"{backup_name}_{timestamp_str}.gz"
        elif db_name:
            archive_name = f"backup_{db_name}_{timestamp_str}.gz"
        else:
            archive_name = f"backup_full_{timestamp_str}.gz"
        
        archive_path = f"{BACKUP_DIR}/{archive_name}"
        metadata_path = f"{BACKUP_DIR}/{archive_name.replace('.gz', '_metadata.json')}"
        
        # Build mongodump command
        if db_name:
            # Single database backup
            cmd = f'mongodump --uri="{self.mongo_url}" --db={db_name} --gzip --archive={archive_path}'
            databases = [db_name]
        elif include_all_tenants:
            # All tenants backup
            tenants = await self.get_tenant_list()
            databases = [t["db_name"] for t in tenants]
            # For multiple databases, we backup all (no --db flag)
            cmd = f'mongodump --uri="{self.mongo_url}" --gzip --archive={archive_path}'
        else:
            # All databases
            cmd = f'mongodump --uri="{self.mongo_url}" --gzip --archive={archive_path}'
            db_list = await self.client.list_database_names()
            databases = [d for d in db_list if d not in ["admin", "local", "config"]]
        
        print(f"[BACKUP] Starting backup: {archive_name}")
        print(f"[BACKUP] Command: {cmd[:100]}...")
        
        # Execute mongodump
        start_time = datetime.now()
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        end_time = datetime.now()
        duration_seconds = (end_time - start_time).total_seconds()
        
        if result.returncode != 0:
            error_msg = result.stderr[:500] if result.stderr else "Unknown error"
            print(f"[BACKUP] FAILED: {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "timestamp": timestamp.isoformat()
            }
        
        # Get file size and checksum
        if not os.path.exists(archive_path):
            return {
                "success": False,
                "error": "Backup file was not created",
                "timestamp": timestamp.isoformat()
            }
        
        file_size = os.path.getsize(archive_path)
        checksum = self._calculate_checksum(archive_path)
        
        # Build metadata
        tenant_list = await self.get_tenant_list()
        
        # Get blueprint versions for backed up databases
        blueprint_versions = {}
        for db in databases:
            blueprint_versions[db] = await self.get_blueprint_version(db)
        
        # Get MongoDB server info
        try:
            server_info = await self.client.admin.command("serverStatus")
            db_version = server_info.get("version", "unknown")
        except Exception:
            db_version = "unknown"
        
        metadata = {
            "backup_id": f"BKP-{timestamp_str}",
            "backup_type": "full_dump",
            "timestamp": timestamp.isoformat(),
            "timestamp_unix": int(timestamp.timestamp()),
            "created_by": created_by,
            "tenant_list": tenant_list,
            "databases_backed_up": databases,
            "blueprint_versions": blueprint_versions,
            "db_version": db_version,
            "file_name": archive_name,
            "file_path": archive_path,
            "file_size_bytes": file_size,
            "file_size_mb": round(file_size / (1024 * 1024), 2),
            "checksum_sha256": checksum,
            "duration_seconds": round(duration_seconds, 2),
            "mongodump_output": result.stderr[:1000] if result.stderr else "",
            "status": "completed"
        }
        
        # Save metadata to JSON file
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2, default=str)
        
        print(f"[BACKUP] SUCCESS: {archive_name}")
        print(f"[BACKUP] Size: {metadata['file_size_mb']} MB")
        print(f"[BACKUP] Duration: {duration_seconds:.2f}s")
        print(f"[BACKUP] Checksum: {checksum[:16]}...")
        print(f"[BACKUP] Metadata: {metadata_path}")
        
        await self.disconnect()
        
        return {
            "success": True,
            "backup_file": archive_path,
            "metadata_file": metadata_path,
            "metadata": metadata
        }
    
    async def create_tenant_backup(
        self,
        db_name: str,
        created_by: str = "system"
    ) -> Dict:
        """Create backup for a specific tenant database"""
        return await self.create_full_backup(
            db_name=db_name,
            created_by=created_by
        )
    
    async def list_backups(self) -> List[Dict]:
        """List all available backups"""
        backups = []
        
        if not os.path.exists(BACKUP_DIR):
            return backups
        
        for filename in os.listdir(BACKUP_DIR):
            if filename.endswith("_metadata.json"):
                metadata_path = os.path.join(BACKUP_DIR, filename)
                try:
                    with open(metadata_path, "r") as f:
                        metadata = json.load(f)
                        # Check if backup file still exists
                        if os.path.exists(metadata.get("file_path", "")):
                            metadata["exists"] = True
                        else:
                            metadata["exists"] = False
                        backups.append(metadata)
                except Exception as e:
                    print(f"[BACKUP] Error reading {filename}: {e}")
        
        # Sort by timestamp descending
        backups.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return backups
    
    async def verify_backup(self, backup_file: str) -> Dict:
        """Verify backup file integrity"""
        if not os.path.exists(backup_file):
            return {
                "valid": False,
                "error": "Backup file not found"
            }
        
        # Look for metadata file
        metadata_file = backup_file.replace(".gz", "_metadata.json")
        
        if os.path.exists(metadata_file):
            with open(metadata_file, "r") as f:
                metadata = json.load(f)
            
            stored_checksum = metadata.get("checksum_sha256", "")
            current_checksum = self._calculate_checksum(backup_file)
            
            if stored_checksum == current_checksum:
                return {
                    "valid": True,
                    "checksum_match": True,
                    "stored_checksum": stored_checksum,
                    "current_checksum": current_checksum,
                    "metadata": metadata
                }
            else:
                return {
                    "valid": False,
                    "error": "Checksum mismatch - file may be corrupted",
                    "stored_checksum": stored_checksum,
                    "current_checksum": current_checksum
                }
        else:
            # Calculate checksum without metadata
            checksum = self._calculate_checksum(backup_file)
            return {
                "valid": True,
                "checksum_match": None,
                "current_checksum": checksum,
                "warning": "No metadata file found for verification"
            }
    
    async def delete_backup(self, backup_file: str) -> Dict:
        """Delete a backup file and its metadata"""
        deleted = []
        errors = []
        
        # Delete backup file
        if os.path.exists(backup_file):
            try:
                os.remove(backup_file)
                deleted.append(backup_file)
            except Exception as e:
                errors.append(f"Cannot delete {backup_file}: {e}")
        
        # Delete metadata file
        metadata_file = backup_file.replace(".gz", "_metadata.json")
        if os.path.exists(metadata_file):
            try:
                os.remove(metadata_file)
                deleted.append(metadata_file)
            except Exception as e:
                errors.append(f"Cannot delete {metadata_file}: {e}")
        
        return {
            "success": len(errors) == 0,
            "deleted": deleted,
            "errors": errors
        }


# ==================== CLI ====================

async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="OCB TITAN Backup System")
    parser.add_argument("--db", type=str, help="Specific database to backup")
    parser.add_argument("--all-tenants", action="store_true", help="Backup all tenants")
    parser.add_argument("--list", action="store_true", help="List all backups")
    parser.add_argument("--verify", type=str, help="Verify backup file")
    parser.add_argument("--user", type=str, default="system", help="User creating backup")
    
    args = parser.parse_args()
    
    backup_system = BackupSystem()
    
    if args.list:
        backups = await backup_system.list_backups()
        print(f"\n{'='*70}")
        print("OCB TITAN - AVAILABLE BACKUPS")
        print(f"{'='*70}\n")
        for b in backups:
            status = "EXISTS" if b.get("exists") else "MISSING"
            print(f"  [{status}] {b.get('backup_id')}")
            print(f"         File: {b.get('file_name')}")
            print(f"         Size: {b.get('file_size_mb')} MB")
            print(f"         Date: {b.get('timestamp')}")
            print()
    
    elif args.verify:
        result = await backup_system.verify_backup(args.verify)
        print(f"\n{'='*70}")
        print("BACKUP VERIFICATION")
        print(f"{'='*70}")
        print(json.dumps(result, indent=2, default=str))
    
    else:
        # Create backup
        print(f"\n{'='*70}")
        print("OCB TITAN - CREATE BACKUP")
        print(f"{'='*70}\n")
        
        result = await backup_system.create_full_backup(
            db_name=args.db,
            include_all_tenants=args.all_tenants,
            created_by=args.user
        )
        
        if result.get("success"):
            print(f"\nBACKUP SUCCESSFUL!")
            print(f"File: {result.get('backup_file')}")
            print(f"Metadata: {result.get('metadata_file')}")
        else:
            print(f"\nBACKUP FAILED: {result.get('error')}")


if __name__ == "__main__":
    asyncio.run(main())
