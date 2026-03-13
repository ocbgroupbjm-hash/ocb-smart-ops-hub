#!/usr/bin/env python3
"""
OCB TITAN ERP - OFFICIAL RESTORE SYSTEM
MASTER BLUEPRINT: restore_system.py

Command restore:
mongorestore --gzip --archive=backup_file.gz --drop

CRITICAL: This script restores database from backup.
All existing data will be REPLACED.
"""

import asyncio
import os
import json
import subprocess
import hashlib
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional, Dict

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
BACKUP_DIR = "/app/backend/backups"


class RestoreSystem:
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
    
    async def verify_backup_before_restore(self, backup_file: str) -> Dict:
        """Verify backup integrity before restore"""
        if not os.path.exists(backup_file):
            return {
                "valid": False,
                "error": f"Backup file not found: {backup_file}"
            }
        
        # Check file is not empty
        file_size = os.path.getsize(backup_file)
        if file_size == 0:
            return {
                "valid": False,
                "error": "Backup file is empty"
            }
        
        # Check metadata file
        metadata_file = backup_file.replace(".gz", "_metadata.json")
        if os.path.exists(metadata_file):
            with open(metadata_file, "r") as f:
                metadata = json.load(f)
            
            stored_checksum = metadata.get("checksum_sha256", "")
            current_checksum = self._calculate_checksum(backup_file)
            
            if stored_checksum and stored_checksum != current_checksum:
                return {
                    "valid": False,
                    "error": "Checksum mismatch - backup may be corrupted",
                    "stored_checksum": stored_checksum,
                    "current_checksum": current_checksum
                }
            
            return {
                "valid": True,
                "metadata": metadata,
                "file_size_mb": round(file_size / (1024 * 1024), 2)
            }
        
        # No metadata - still valid but warn
        return {
            "valid": True,
            "warning": "No metadata file found - cannot verify checksum",
            "file_size_mb": round(file_size / (1024 * 1024), 2)
        }
    
    async def restore_full_database(
        self,
        backup_file: str,
        target_db: str = None,
        drop_existing: bool = True,
        skip_validation: bool = False,
        restored_by: str = "system"
    ) -> Dict:
        """
        Restore database from mongodump archive
        
        Args:
            backup_file: Path to backup .gz file
            target_db: If specified, restore to this database only
            drop_existing: If True, drop existing collections before restore
            skip_validation: If True, skip pre-restore validation
            restored_by: User who initiated restore
        
        Returns:
            Restore result dict
        """
        timestamp = datetime.now(timezone.utc)
        timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
        
        print(f"\n{'='*70}")
        print("OCB TITAN - DATABASE RESTORE")
        print(f"{'='*70}")
        print(f"Backup File: {backup_file}")
        print(f"Target DB: {target_db or 'ALL'}")
        print(f"Drop Existing: {drop_existing}")
        print(f"Timestamp: {timestamp.isoformat()}")
        print(f"{'='*70}\n")
        
        # Step 1: Verify backup
        if not skip_validation:
            print("[RESTORE] Step 1: Verifying backup integrity...")
            verification = await self.verify_backup_before_restore(backup_file)
            
            if not verification.get("valid"):
                return {
                    "success": False,
                    "error": verification.get("error", "Backup verification failed"),
                    "step": "verification",
                    "timestamp": timestamp.isoformat()
                }
            
            print(f"[RESTORE] ✅ Backup verified: {verification.get('file_size_mb', 0)} MB")
        else:
            print("[RESTORE] Step 1: Skipping verification (--skip-validation)")
        
        # Step 2: Build restore command
        print("[RESTORE] Step 2: Building restore command...")
        
        # Base command with --drop to replace existing data
        cmd_parts = [
            "mongorestore",
            f'--uri="{self.mongo_url}"',
            "--gzip",
            f"--archive={backup_file}"
        ]
        
        if drop_existing:
            cmd_parts.append("--drop")
        
        # If restoring to specific database, use nsFrom/nsTo
        # Note: This works with single-db archives only
        if target_db:
            cmd_parts.append(f"--nsInclude='{target_db}.*'")
        
        cmd = " ".join(cmd_parts)
        print(f"[RESTORE] Command: {cmd[:100]}...")
        
        # Step 3: Execute restore
        print("[RESTORE] Step 3: Executing mongorestore...")
        start_time = datetime.now()
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        end_time = datetime.now()
        duration_seconds = (end_time - start_time).total_seconds()
        
        if result.returncode != 0:
            error_msg = result.stderr if result.stderr else "Unknown error"
            print(f"[RESTORE] ❌ FAILED: {error_msg[:500]}")
            return {
                "success": False,
                "error": error_msg[:1000],
                "step": "mongorestore",
                "duration_seconds": duration_seconds,
                "timestamp": timestamp.isoformat()
            }
        
        print(f"[RESTORE] ✅ mongorestore completed in {duration_seconds:.2f}s")
        
        # Step 4: Return result (validation will be done by validate_restore.py)
        restore_result = {
            "success": True,
            "restore_id": f"RST-{timestamp_str}",
            "backup_file": backup_file,
            "target_db": target_db or "ALL",
            "drop_existing": drop_existing,
            "duration_seconds": round(duration_seconds, 2),
            "restored_by": restored_by,
            "timestamp": timestamp.isoformat(),
            "mongorestore_output": result.stderr[:2000] if result.stderr else result.stdout[:2000],
            "status": "pending_validation"
        }
        
        # Save restore report
        report_path = f"{BACKUP_DIR}/restore_report_{timestamp_str}.json"
        with open(report_path, "w") as f:
            json.dump(restore_result, f, indent=2, default=str)
        
        print(f"[RESTORE] Report saved: {report_path}")
        print(f"\n[RESTORE] ⚠️  NEXT STEP: Run validate_restore.py to verify data integrity")
        
        return restore_result
    
    async def restore_single_tenant(
        self,
        backup_file: str,
        source_db: str,
        target_db: str = None,
        drop_existing: bool = True,
        restored_by: str = "system"
    ) -> Dict:
        """
        Restore a single tenant database from a multi-tenant backup
        
        Uses --nsFrom and --nsTo to remap namespace
        """
        if not target_db:
            target_db = source_db
        
        timestamp = datetime.now(timezone.utc)
        timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
        
        print(f"\n{'='*70}")
        print("OCB TITAN - SINGLE TENANT RESTORE")
        print(f"{'='*70}")
        print(f"Backup File: {backup_file}")
        print(f"Source DB: {source_db}")
        print(f"Target DB: {target_db}")
        print(f"{'='*70}\n")
        
        # Verify backup exists
        if not os.path.exists(backup_file):
            return {
                "success": False,
                "error": f"Backup file not found: {backup_file}"
            }
        
        # Drop target database first if drop_existing is True
        if drop_existing:
            try:
                client = AsyncIOMotorClient(self.mongo_url)
                await client.drop_database(target_db)
                client.close()
                print(f"[RESTORE] Dropped existing database: {target_db}")
            except Exception as e:
                print(f"[RESTORE] Warning: Could not drop database: {e}")
        
        # Build command with namespace remapping
        # Using --drop within mongorestore for collection-level dropping
        cmd_parts = [
            "mongorestore",
            f'--uri="{self.mongo_url}"',
            "--gzip",
            f"--archive={backup_file}",
            f"--nsFrom='{source_db}.*'",
            f"--nsTo='{target_db}.*'",
            "--drop"  # Drop each collection before restoring
        ]
        
        cmd = " ".join(cmd_parts)
        print(f"[RESTORE] Command: {cmd[:120]}...")
        
        start_time = datetime.now()
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Check for actual errors (mongorestore outputs to stderr even on success)
        stderr_output = result.stderr if result.stderr else ""
        has_error = "error" in stderr_output.lower() and "0 document(s) restored" not in stderr_output
        
        # If return code is non-zero OR there's an actual error message
        if result.returncode != 0 and has_error:
            return {
                "success": False,
                "error": stderr_output[:1000],
                "duration_seconds": duration
            }
        
        return {
            "success": True,
            "restore_id": f"RST-{timestamp_str}",
            "source_db": source_db,
            "target_db": target_db,
            "duration_seconds": round(duration, 2),
            "restored_by": restored_by,
            "timestamp": timestamp.isoformat(),
            "status": "pending_validation"
        }


# ==================== CLI ====================

async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="OCB TITAN Restore System")
    parser.add_argument("backup_file", type=str, help="Path to backup file (.gz)")
    parser.add_argument("--target-db", type=str, help="Restore to specific database")
    parser.add_argument("--no-drop", action="store_true", help="Don't drop existing collections")
    parser.add_argument("--skip-validation", action="store_true", help="Skip pre-restore validation")
    parser.add_argument("--user", type=str, default="system", help="User initiating restore")
    parser.add_argument("--source-db", type=str, help="Source DB name for single tenant restore")
    
    args = parser.parse_args()
    
    restore_system = RestoreSystem()
    
    if args.source_db:
        # Single tenant restore
        result = await restore_system.restore_single_tenant(
            backup_file=args.backup_file,
            source_db=args.source_db,
            target_db=args.target_db,
            drop_existing=not args.no_drop,
            restored_by=args.user
        )
    else:
        # Full restore
        result = await restore_system.restore_full_database(
            backup_file=args.backup_file,
            target_db=args.target_db,
            drop_existing=not args.no_drop,
            skip_validation=args.skip_validation,
            restored_by=args.user
        )
    
    print(f"\n{'='*70}")
    print("RESTORE RESULT")
    print(f"{'='*70}")
    print(json.dumps(result, indent=2, default=str))
    
    if result.get("success"):
        print("\n✅ RESTORE COMPLETED")
        print("⚠️  Run: python validate_restore.py to verify data integrity")
    else:
        print("\n❌ RESTORE FAILED")


if __name__ == "__main__":
    asyncio.run(main())
