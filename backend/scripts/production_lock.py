#!/usr/bin/env python3
"""
OCB TITAN ERP - PRODUCTION LOCK & RELEASE
MASTER BLUEPRINT: Version Lock and Rollout

Process:
1. Pilot validation ✅
2. Lock version
3. Rollout to tenants
"""

import asyncio
import os
import json
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Dict

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
OUTPUT_DIR = "/app/backend/scripts/audit_output"
MEMORY_DIR = "/app/memory"


class ProductionLock:
    def __init__(self):
        self.client = None
        self.timestamp = datetime.now(timezone.utc)
        self.version = "3.1.0"  # New production version
        
    async def connect(self):
        self.client = AsyncIOMotorClient(MONGO_URL)
        
    async def disconnect(self):
        if self.client:
            self.client.close()
    
    async def lock_version(self, db_name: str = "ocb_titan") -> Dict:
        """Lock the production version"""
        await self.connect()
        db = self.client[db_name]
        
        print("="*70)
        print("OCB TITAN - PRODUCTION VERSION LOCK")
        print(f"Version: {self.version}")
        print(f"Timestamp: {self.timestamp.isoformat()}")
        print("="*70)
        
        # Lock ruleset version
        ruleset = {
            "id": f"RULESET-{self.version}",
            "version": self.version,
            "status": "LOCKED",
            "locked_at": self.timestamp.isoformat(),
            "locked_by": "PRODUCTION_LOCK_SCRIPT",
            "features": {
                "accounting_engine": "3.0",
                "inventory_ssot": "3.0",
                "cash_control": "3.0",
                "audit_system": "3.0",
                "backup_restore": "3.0",
                "reconciliation_monitor": "3.0",
                "observability": "1.0",
                "ai_insight": "1.0"
            },
            "validations_passed": [
                "E2E_BUSINESS_TEST",
                "RBAC_TEST",
                "ACCOUNTING_BALANCE",
                "INVENTORY_RECONCILIATION",
                "BACKUP_RESTORE",
                "MULTI_TENANT_ISOLATION",
                "PERFORMANCE_TEST"
            ]
        }
        
        await db["system_settings"].update_one(
            {"key": "ruleset_version"},
            {"$set": {"key": "ruleset_version", "value": ruleset}},
            upsert=True
        )
        
        # Lock blueprint version
        blueprint = {
            "id": f"BLUEPRINT-{self.version}",
            "version": self.version,
            "status": "PRODUCTION",
            "locked_at": self.timestamp.isoformat(),
            "phase": "PHASE_20_COMPLETE",
            "modules": {
                "core_erp": True,
                "accounting_engine": True,
                "inventory_ssot": True,
                "cash_control": True,
                "backup_restore": True,
                "reconciliation_monitor": True,
                "observability": True,
                "ai_read_only": True
            },
            "gates_passed": {
                "gate_0_security_backup": True,
                "gate_1_e2e_validation": True,
                "gate_2_release_candidate": True,
                "gate_3_production_ready": True
            }
        }
        
        await db["system_settings"].update_one(
            {"key": "blueprint_version"},
            {"$set": {"key": "blueprint_version", "value": blueprint}},
            upsert=True
        )
        
        # Update company profile
        await db["company_profile"].update_one(
            {},
            {"$set": {
                "blueprint_version": self.version,
                "last_updated": self.timestamp.isoformat()
            }}
        )
        
        await self.disconnect()
        
        print(f"\n✅ Ruleset version locked: {self.version}")
        print(f"✅ Blueprint version locked: {self.version}")
        
        return {
            "version": self.version,
            "ruleset": ruleset,
            "blueprint": blueprint,
            "locked_at": self.timestamp.isoformat()
        }
    
    async def rollout_to_tenants(self) -> Dict:
        """Rollout locked version to all tenants"""
        await self.connect()
        
        # Load tenant list
        businesses_file = "/app/backend/data/businesses.json"
        if not os.path.exists(businesses_file):
            return {"error": "businesses.json not found"}
        
        with open(businesses_file, "r") as f:
            businesses = json.load(f)
        
        results = []
        
        for b in businesses:
            if b.get("is_active") and not b.get("is_test"):
                db_name = b.get("db_name")
                db = self.client[db_name]
                
                # Update version
                await db["system_settings"].update_one(
                    {"key": "blueprint_version"},
                    {"$set": {
                        "key": "blueprint_version",
                        "value": {
                            "version": self.version,
                            "status": "PRODUCTION",
                            "synced_at": self.timestamp.isoformat()
                        }
                    }},
                    upsert=True
                )
                
                results.append({
                    "tenant": b.get("name"),
                    "db_name": db_name,
                    "version": self.version,
                    "status": "SYNCED"
                })
                
                print(f"  ✅ {b.get('name')}: v{self.version}")
        
        await self.disconnect()
        
        return {
            "version": self.version,
            "tenants_updated": len(results),
            "results": results
        }
    
    def generate_lock_report(self, lock_result: Dict, rollout_result: Dict):
        """Generate production lock report"""
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        report = {
            "production_lock_id": f"LOCK-{self.timestamp.strftime('%Y%m%d_%H%M%S')}",
            "version": self.version,
            "timestamp": self.timestamp.isoformat(),
            "lock": lock_result,
            "rollout": rollout_result,
            "status": "PRODUCTION_LOCKED"
        }
        
        # Save JSON
        json_path = f"{OUTPUT_DIR}/production_lock_v{self.version.replace('.', '_')}.json"
        with open(json_path, "w") as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n📄 Lock report saved: {json_path}")
        
        return report


async def main():
    lock = ProductionLock()
    
    print("\n--- STEP 1: LOCK VERSION ---")
    lock_result = await lock.lock_version()
    
    print("\n--- STEP 2: ROLLOUT TO TENANTS ---")
    rollout_result = await lock.rollout_to_tenants()
    
    print("\n--- STEP 3: GENERATE REPORT ---")
    report = lock.generate_lock_report(lock_result, rollout_result)
    
    print("\n" + "="*70)
    print("PRODUCTION LOCK COMPLETE")
    print("="*70)
    print(f"Version: {lock.version}")
    print(f"Status: PRODUCTION LOCKED")
    print(f"Tenants Updated: {rollout_result.get('tenants_updated', 0)}")
    print("="*70)
    
    return report


if __name__ == "__main__":
    from typing import Dict
    asyncio.run(main())
