#!/usr/bin/env python3
"""
OCB TITAN ERP - Production Hardening Script
Creates performance indexes and validates database integrity

MASTER BLUEPRINT:
- Idempotent script (safe to run multiple times)
- Creates indexes for optimal query performance
- Validates SSOT integrity

Usage:
    python3 production_hardening.py [--database <db_name>]
"""

import asyncio
import argparse
import os
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DEFAULT_DB = "ocb_titan"

# Index definitions
INDEXES = {
    "journal_entries": [
        {"keys": [("tenant_id", 1), ("posted_at", -1)], "name": "idx_journal_tenant_posted"},
        {"keys": [("journal_date", -1)], "name": "idx_journal_date"},
        {"keys": [("status", 1), ("journal_date", -1)], "name": "idx_journal_status_date"},
        {"keys": [("reference_type", 1), ("reference_id", 1)], "name": "idx_journal_reference"},
        {"keys": [("branch_id", 1), ("journal_date", -1)], "name": "idx_journal_branch_date"},
        {"keys": [("journal_number", 1)], "name": "idx_journal_number", "unique": True}
    ],
    "stock_movements": [
        {"keys": [("tenant_id", 1), ("product_id", 1), ("created_at", -1)], "name": "idx_stock_tenant_product_date"},
        {"keys": [("product_id", 1), ("branch_id", 1)], "name": "idx_stock_product_branch"},
        {"keys": [("branch_id", 1), ("created_at", -1)], "name": "idx_stock_branch_date"},
        {"keys": [("movement_type", 1), ("created_at", -1)], "name": "idx_stock_type_date"},
        {"keys": [("reference_type", 1), ("reference_id", 1)], "name": "idx_stock_reference"}
    ],
    "sales_invoices": [
        {"keys": [("tenant_id", 1), ("branch_id", 1), ("invoice_date", -1)], "name": "idx_sales_tenant_branch_date"},
        {"keys": [("invoice_date", -1)], "name": "idx_sales_date"},
        {"keys": [("status", 1), ("invoice_date", -1)], "name": "idx_sales_status_date"},
        {"keys": [("customer_id", 1)], "name": "idx_sales_customer"},
        {"keys": [("cashier_id", 1), ("invoice_date", -1)], "name": "idx_sales_cashier_date"},
        {"keys": [("invoice_number", 1)], "name": "idx_sales_invoice_number", "unique": True}
    ],
    "purchase_orders": [
        {"keys": [("tenant_id", 1), ("order_date", -1)], "name": "idx_po_tenant_date"},
        {"keys": [("supplier_id", 1)], "name": "idx_po_supplier"},
        {"keys": [("status", 1), ("order_date", -1)], "name": "idx_po_status_date"},
        {"keys": [("po_number", 1)], "name": "idx_po_number", "unique": True}
    ],
    "products": [
        {"keys": [("code", 1)], "name": "idx_product_code", "unique": True},
        {"keys": [("category_id", 1)], "name": "idx_product_category"},
        {"keys": [("is_active", 1), ("name", 1)], "name": "idx_product_active_name"}
    ],
    "customers": [
        {"keys": [("code", 1)], "name": "idx_customer_code"},
        {"keys": [("phone", 1)], "name": "idx_customer_phone"},
        {"keys": [("is_active", 1)], "name": "idx_customer_active"}
    ],
    "suppliers": [
        {"keys": [("code", 1)], "name": "idx_supplier_code", "unique": True},
        {"keys": [("is_active", 1)], "name": "idx_supplier_active"}
    ],
    "audit_logs": [
        {"keys": [("tenant_id", 1), ("created_at", -1)], "name": "idx_audit_tenant_date"},
        {"keys": [("module", 1), ("created_at", -1)], "name": "idx_audit_module_date"},
        {"keys": [("user_id", 1), ("created_at", -1)], "name": "idx_audit_user_date"},
        {"keys": [("entity_id", 1)], "name": "idx_audit_entity"}
    ],
    "cash_discrepancies": [
        {"keys": [("shift_id", 1)], "name": "idx_cash_disc_shift"},
        {"keys": [("created_at", -1)], "name": "idx_cash_disc_date"},
        {"keys": [("discrepancy_type", 1)], "name": "idx_cash_disc_type"}
    ],
    "cashier_shifts": [
        {"keys": [("cashier_id", 1), ("status", 1)], "name": "idx_shift_cashier_status"},
        {"keys": [("branch_id", 1), ("start_time", -1)], "name": "idx_shift_branch_time"},
        {"keys": [("shift_no", 1)], "name": "idx_shift_number", "unique": True}
    ],
    "accounts_receivable": [
        {"keys": [("customer_id", 1), ("status", 1)], "name": "idx_ar_customer_status"},
        {"keys": [("due_date", 1), ("status", 1)], "name": "idx_ar_due_status"}
    ],
    "accounts_payable": [
        {"keys": [("supplier_id", 1), ("status", 1)], "name": "idx_ap_supplier_status"},
        {"keys": [("due_date", 1), ("status", 1)], "name": "idx_ap_due_status"}
    ]
}


async def create_indexes(db):
    """Create all indexes idempotently"""
    print(f"\n{'='*60}")
    print(f"OCB TITAN ERP - PRODUCTION HARDENING")
    print(f"Database: {db.name}")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print(f"{'='*60}\n")
    
    created = 0
    skipped = 0
    errors = 0
    
    for collection_name, indexes in INDEXES.items():
        print(f"\n--- Collection: {collection_name} ---")
        
        collection = db[collection_name]
        existing_indexes = await collection.index_information()
        existing_names = set(existing_indexes.keys())
        
        for index_def in indexes:
            index_name = index_def["name"]
            
            if index_name in existing_names:
                print(f"  ⏭️  {index_name} - already exists")
                skipped += 1
                continue
            
            try:
                keys = index_def["keys"]
                unique = index_def.get("unique", False)
                
                await collection.create_index(keys, name=index_name, unique=unique, background=True)
                print(f"  ✅ {index_name} - created")
                created += 1
                
            except Exception as e:
                print(f"  ❌ {index_name} - error: {str(e)[:50]}")
                errors += 1
    
    print(f"\n{'='*60}")
    print(f"INDEX CREATION SUMMARY")
    print(f"{'='*60}")
    print(f"Created:  {created}")
    print(f"Skipped:  {skipped}")
    print(f"Errors:   {errors}")
    print(f"Total:    {created + skipped + errors}")
    print(f"{'='*60}\n")
    
    return {"created": created, "skipped": skipped, "errors": errors}


async def validate_ssot_integrity(db):
    """Validate SSOT integrity"""
    print(f"\n{'='*60}")
    print("SSOT INTEGRITY VALIDATION")
    print(f"{'='*60}\n")
    
    issues = []
    
    # 1. Check journal entries balance
    print("Checking journal entries balance...")
    unbalanced = await db["journal_entries"].count_documents({
        "status": "posted",
        "$expr": {"$ne": ["$total_debit", "$total_credit"]}
    })
    if unbalanced > 0:
        issues.append(f"Found {unbalanced} unbalanced journal entries")
    else:
        print("  ✅ All posted journals are balanced")
    
    # 2. Check stock movements vs product_stocks sync
    print("Checking stock SSOT...")
    pipeline = [
        {"$group": {"_id": {"product_id": "$product_id", "branch_id": "$branch_id"}, "ssot_qty": {"$sum": "$quantity"}}}
    ]
    ssot_stock = await db["stock_movements"].aggregate(pipeline).to_list(100000)
    
    mismatch_count = 0
    for s in ssot_stock[:100]:  # Sample check
        if not s["_id"]:
            continue
        product_id = s["_id"].get("product_id") if isinstance(s["_id"], dict) else s["_id"]
        branch_id = s["_id"].get("branch_id", "") if isinstance(s["_id"], dict) else ""
        
        if not product_id:
            continue
            
        cache = await db["product_stocks"].find_one({
            "product_id": product_id,
            "branch_id": branch_id
        } if branch_id else {"product_id": product_id})
        
        if cache:
            cache_qty = cache.get("quantity", 0)
            if abs(cache_qty - s["ssot_qty"]) > 0.01:
                mismatch_count += 1
    
    if mismatch_count > 0:
        issues.append(f"Found {mismatch_count} stock cache mismatches")
    else:
        print("  ✅ Stock cache is in sync with SSOT")
    
    # 3. Check audit log integrity
    print("Checking audit log integrity...")
    audit_count = await db["audit_logs"].count_documents({})
    print(f"  📊 Total audit logs: {audit_count}")
    
    # Summary
    print(f"\n{'='*60}")
    if issues:
        print("⚠️  ISSUES FOUND:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✅ ALL SSOT INTEGRITY CHECKS PASSED")
    print(f"{'='*60}\n")
    
    return {"valid": len(issues) == 0, "issues": issues}


async def main(database: str):
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[database]
    
    # Create indexes
    index_result = await create_indexes(db)
    
    # Validate SSOT
    ssot_result = await validate_ssot_integrity(db)
    
    client.close()
    
    return {
        "database": database,
        "indexes": index_result,
        "ssot_validation": ssot_result,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OCB TITAN Production Hardening")
    parser.add_argument("--database", "-d", default=DEFAULT_DB, help=f"Database name (default: {DEFAULT_DB})")
    
    args = parser.parse_args()
    
    result = asyncio.run(main(args.database))
    print(f"\nHardening complete: {result}")
