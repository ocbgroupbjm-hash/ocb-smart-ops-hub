#!/usr/bin/env python3
"""
OCB TITAN ERP - LOCK BLUEPRINT VERSION 3.0.0
Lock blueprint and rollout to all tenants
"""

import asyncio
import os
import json
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
BLUEPRINT_VERSION = "3.0.0"
OUTPUT_FILE = "/app/test_reports/BLUEPRINT_LOCK_REPORT.json"


async def lock_blueprint():
    client = AsyncIOMotorClient(MONGO_URL)
    
    print("="*70)
    print("OCB TITAN ERP - LOCK BLUEPRINT VERSION 3.0.0")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print("="*70 + "\n")
    
    # Blueprint definition
    blueprint = {
        "version": BLUEPRINT_VERSION,
        "release_date": datetime.now(timezone.utc).isoformat(),
        "components": {
            "core_accounting": {
                "version": "3.0.0",
                "features": ["double_entry", "auto_journal", "trial_balance", "balance_sheet"],
                "ssot_collection": "journal_entries"
            },
            "inventory": {
                "version": "3.0.0",
                "features": ["stock_movements", "ssot_calculation", "dead_stock", "turnover"],
                "ssot_collection": "stock_movements"
            },
            "cash_control": {
                "version": "3.0.0",
                "features": ["shift_management", "variance_detection", "auto_journal"],
                "ssot_collection": "cashier_shifts"
            },
            "dashboard_intel": {
                "version": "3.0.0",
                "features": ["kpi_summary", "top_selling", "outlet_performance", "cash_ranking"]
            },
            "ai_engine": {
                "version": "3.0.0",
                "features": ["read_only", "insights", "recommendations"],
                "access_level": "read_only"
            },
            "audit_system": {
                "version": "3.0.0",
                "features": ["append_only", "integrity_hash", "tamper_detection"]
            },
            "export_import": {
                "version": "3.0.0",
                "features": ["excel_export", "excel_import", "pdf_reports"]
            },
            "print_engine": {
                "version": "3.0.0",
                "features": ["invoice_pdf", "po_pdf", "thermal_receipt"]
            }
        },
        "rules": {
            "ssot_mandatory": True,
            "accounting_first": True,
            "tenant_isolation": True,
            "ai_read_only": True,
            "audit_append_only": True
        },
        "locked_at": datetime.now(timezone.utc).isoformat(),
        "locked_by": "system_validation"
    }
    
    # Target tenants for rollout
    target_tenants = ["ocb_titan", "ocb_baju", "ocb_counter", "ocb_unit_4", "ocb_unt_1"]
    
    # List all databases
    all_dbs = await client.list_database_names()
    existing_tenants = [d for d in all_dbs if d.startswith("ocb_")]
    
    print(f"Blueprint Version: {BLUEPRINT_VERSION}")
    print(f"Target Tenants: {target_tenants}")
    print(f"Existing Tenants: {existing_tenants}")
    print()
    
    # Rollout to each tenant
    rollout_results = []
    
    for tenant in target_tenants:
        if tenant in existing_tenants:
            db = client[tenant]
            
            # Save blueprint to tenant
            await db["system_blueprint"].delete_many({})
            await db["system_blueprint"].insert_one({
                **blueprint,
                "tenant_id": tenant,
                "applied_at": datetime.now(timezone.utc).isoformat()
            })
            
            # Verify
            saved = await db["system_blueprint"].find_one({"version": BLUEPRINT_VERSION}, {"_id": 0})
            
            status = "SUCCESS" if saved else "FAILED"
            rollout_results.append({
                "tenant": tenant,
                "status": status,
                "applied_at": datetime.now(timezone.utc).isoformat()
            })
            
            print(f"  {tenant}: {status}")
        else:
            rollout_results.append({
                "tenant": tenant,
                "status": "NOT_FOUND",
                "message": "Database does not exist"
            })
            print(f"  {tenant}: NOT_FOUND (will be created when tenant registers)")
    
    # Summary
    success_count = sum(1 for r in rollout_results if r["status"] == "SUCCESS")
    
    print(f"\n{'='*70}")
    print(f"BLUEPRINT LOCK SUMMARY")
    print(f"{'='*70}")
    print(f"Version: {BLUEPRINT_VERSION}")
    print(f"Tenants Updated: {success_count}/{len(target_tenants)}")
    print(f"Status: {'LOCKED' if success_count > 0 else 'FAILED'}")
    print(f"{'='*70}")
    
    # Save report
    report = {
        "blueprint_version": BLUEPRINT_VERSION,
        "lock_timestamp": datetime.now(timezone.utc).isoformat(),
        "blueprint": blueprint,
        "rollout_results": rollout_results,
        "summary": {
            "target_tenants": len(target_tenants),
            "success": success_count,
            "not_found": sum(1 for r in rollout_results if r["status"] == "NOT_FOUND"),
            "failed": sum(1 for r in rollout_results if r["status"] == "FAILED")
        },
        "status": "LOCKED" if success_count > 0 else "FAILED"
    }
    
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n📄 Report saved: {OUTPUT_FILE}")
    
    # Also save to memory
    memory_file = "/app/memory/BLUEPRINT_V3.json"
    with open(memory_file, "w") as f:
        json.dump(blueprint, f, indent=2, default=str)
    print(f"📄 Blueprint saved: {memory_file}")
    
    client.close()
    return report


if __name__ == "__main__":
    asyncio.run(lock_blueprint())
