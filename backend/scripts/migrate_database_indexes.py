"""
OCB TITAN AI - Database Index Migration Script
===============================================
PERINTAH 2: HARDENING INDEX DATABASE

Sesuai MASTER BLUEPRINT:
- Index idempotent untuk semua collection kritis
- Jalankan explain plan
- Benchmark query performance

Author: E1 Agent
Date: 2026-03-13
"""

import asyncio
import os
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING
import json

# Active tenants
ACTIVE_TENANTS = [
    "ocb_titan",
    "ocb_baju",
    "ocb_counter",
    "ocb_unit_4",
    "ocb_unt_1"
]

# Index definitions as per Master Blueprint
INDEX_DEFINITIONS = {
    "journal_entries": [
        {"keys": [("status", ASCENDING), ("posted_at", DESCENDING)], "name": "idx_status_posted"},
        {"keys": [("reference_type", ASCENDING), ("reference_id", ASCENDING)], "name": "idx_ref_type_id"},
        {"keys": [("reference", ASCENDING)], "name": "idx_reference"},
        {"keys": [("created_at", DESCENDING)], "name": "idx_created_at"},
        {"keys": [("journal_number", ASCENDING)], "name": "idx_journal_number", "unique": True},
    ],
    "journal_lines": [
        {"keys": [("account_id", ASCENDING), ("posted_at", DESCENDING)], "name": "idx_account_posted"},
        {"keys": [("journal_entry_id", ASCENDING)], "name": "idx_journal_entry"},
        {"keys": [("account_code", ASCENDING)], "name": "idx_account_code"},
    ],
    "stock_movements": [
        {"keys": [("warehouse_id", ASCENDING), ("product_id", ASCENDING), ("created_at", DESCENDING)], "name": "idx_wh_prod_date"},
        {"keys": [("reference_type", ASCENDING), ("reference_id", ASCENDING)], "name": "idx_ref_type_id"},
        {"keys": [("product_id", ASCENDING)], "name": "idx_product"},
        {"keys": [("branch_id", ASCENDING)], "name": "idx_branch"},
    ],
    "transactions": [
        {"keys": [("branch_id", ASCENDING), ("created_at", DESCENDING)], "name": "idx_branch_date"},
        {"keys": [("transaction_number", ASCENDING)], "name": "idx_transaction_number"},
        {"keys": [("customer_id", ASCENDING)], "name": "idx_customer"},
        {"keys": [("status", ASCENDING)], "name": "idx_status"},
    ],
    "sales_invoices": [
        {"keys": [("branch_id", ASCENDING), ("posted_at", DESCENDING)], "name": "idx_branch_posted"},
        {"keys": [("invoice_number", ASCENDING)], "name": "idx_invoice_number"},
        {"keys": [("customer_id", ASCENDING)], "name": "idx_customer"},
        {"keys": [("status", ASCENDING)], "name": "idx_status"},
    ],
    "purchase_invoices": [
        {"keys": [("branch_id", ASCENDING), ("posted_at", DESCENDING)], "name": "idx_branch_posted"},
        {"keys": [("invoice_number", ASCENDING)], "name": "idx_invoice_number"},
        {"keys": [("supplier_id", ASCENDING)], "name": "idx_supplier"},
        {"keys": [("status", ASCENDING)], "name": "idx_status"},
    ],
    "users": [
        {"keys": [("email", ASCENDING)], "name": "idx_email", "unique": True},
        {"keys": [("role_id", ASCENDING)], "name": "idx_role"},
        {"keys": [("branch_id", ASCENDING)], "name": "idx_branch"},
        {"keys": [("username", ASCENDING)], "name": "idx_username"},
    ],
    "products": [
        {"keys": [("code", ASCENDING)], "name": "idx_code"},
        {"keys": [("name", ASCENDING)], "name": "idx_name"},
        {"keys": [("category", ASCENDING)], "name": "idx_category"},
        {"keys": [("is_active", ASCENDING)], "name": "idx_active"},
    ],
    "accounts": [
        {"keys": [("code", ASCENDING)], "name": "idx_code", "unique": True},
        {"keys": [("type", ASCENDING)], "name": "idx_type"},
        {"keys": [("parent_code", ASCENDING)], "name": "idx_parent"},
    ],
    "shifts": [
        {"keys": [("branch_id", ASCENDING), ("opened_at", DESCENDING)], "name": "idx_branch_opened"},
        {"keys": [("cashier_id", ASCENDING)], "name": "idx_cashier"},
        {"keys": [("status", ASCENDING)], "name": "idx_status"},
    ],
    "deposits": [
        {"keys": [("shift_id", ASCENDING)], "name": "idx_shift"},
        {"keys": [("branch_id", ASCENDING), ("created_at", DESCENDING)], "name": "idx_branch_date"},
    ],
}


async def create_indexes_for_tenant(client, db_name: str) -> dict:
    """Create indexes for a single tenant database"""
    db = client[db_name]
    results = {
        "tenant": db_name,
        "collections_processed": 0,
        "indexes_created": 0,
        "indexes_existed": 0,
        "errors": [],
        "details": []
    }
    
    for collection_name, indexes in INDEX_DEFINITIONS.items():
        # Check if collection exists
        collections = await db.list_collection_names()
        if collection_name not in collections:
            results["details"].append({
                "collection": collection_name,
                "status": "skipped",
                "reason": "collection does not exist"
            })
            continue
        
        results["collections_processed"] += 1
        collection = db[collection_name]
        
        # Get existing indexes
        existing = await collection.index_information()
        existing_names = set(existing.keys())
        
        for index_def in indexes:
            index_name = index_def["name"]
            
            try:
                if index_name in existing_names:
                    results["indexes_existed"] += 1
                    results["details"].append({
                        "collection": collection_name,
                        "index": index_name,
                        "status": "existed"
                    })
                else:
                    # Create index
                    kwargs = {"name": index_name}
                    if index_def.get("unique"):
                        kwargs["unique"] = True
                    if index_def.get("sparse"):
                        kwargs["sparse"] = True
                    
                    await collection.create_index(index_def["keys"], **kwargs)
                    results["indexes_created"] += 1
                    results["details"].append({
                        "collection": collection_name,
                        "index": index_name,
                        "status": "created"
                    })
            except Exception as e:
                results["errors"].append({
                    "collection": collection_name,
                    "index": index_name,
                    "error": str(e)
                })
    
    return results


async def run_explain_plans(client, db_name: str) -> dict:
    """Run explain plans for common queries"""
    db = client[db_name]
    explains = []
    
    # Query 1: Ledger per account
    try:
        explain = await db.command({
            "explain": {
                "aggregate": "journal_entries",
                "pipeline": [
                    {"$match": {"status": "posted"}},
                    {"$unwind": "$lines"},
                    {"$group": {
                        "_id": "$lines.account_code",
                        "total_debit": {"$sum": "$lines.debit"},
                        "total_credit": {"$sum": "$lines.credit"}
                    }}
                ],
                "cursor": {}
            },
            "verbosity": "executionStats"
        })
        explains.append({
            "query": "Ledger aggregation",
            "uses_index": "winningPlan" in str(explain),
            "execution_time_ms": explain.get("executionStats", {}).get("executionTimeMillis", "N/A")
        })
    except Exception as e:
        explains.append({"query": "Ledger aggregation", "error": str(e)})
    
    # Query 2: Stock balance per product
    try:
        explain = await db.command({
            "explain": {
                "aggregate": "stock_movements",
                "pipeline": [
                    {"$group": {
                        "_id": {"product_id": "$product_id", "warehouse_id": "$warehouse_id"},
                        "total_qty": {"$sum": "$quantity"}
                    }}
                ],
                "cursor": {}
            },
            "verbosity": "executionStats"
        })
        explains.append({
            "query": "Stock balance aggregation",
            "uses_index": "winningPlan" in str(explain),
            "execution_time_ms": explain.get("executionStats", {}).get("executionTimeMillis", "N/A")
        })
    except Exception as e:
        explains.append({"query": "Stock balance aggregation", "error": str(e)})
    
    # Query 3: Transactions by branch and date
    try:
        explain = await db.command({
            "explain": {
                "find": "transactions",
                "filter": {"branch_id": "test", "created_at": {"$gte": "2026-01-01"}},
                "sort": {"created_at": -1}
            },
            "verbosity": "executionStats"
        })
        explains.append({
            "query": "Transactions by branch/date",
            "uses_index": "IXSCAN" in str(explain.get("queryPlanner", {}).get("winningPlan", {})),
            "execution_time_ms": explain.get("executionStats", {}).get("executionTimeMillis", "N/A")
        })
    except Exception as e:
        explains.append({"query": "Transactions by branch/date", "error": str(e)})
    
    return {"tenant": db_name, "explains": explains}


async def run_migration():
    """Run the full index migration"""
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    client = AsyncIOMotorClient(mongo_url)
    
    print("=" * 60)
    print("OCB TITAN AI - DATABASE INDEX MIGRATION")
    print("=" * 60)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print()
    
    all_results = {
        "migration_timestamp": datetime.now(timezone.utc).isoformat(),
        "tenants": {}
    }
    
    # Create indexes for each tenant
    for tenant in ACTIVE_TENANTS:
        print(f"\n{'='*40}")
        print(f"Processing: {tenant}")
        print(f"{'='*40}")
        
        result = await create_indexes_for_tenant(client, tenant)
        all_results["tenants"][tenant] = result
        
        print(f"Collections processed: {result['collections_processed']}")
        print(f"Indexes created: {result['indexes_created']}")
        print(f"Indexes existed: {result['indexes_existed']}")
        if result['errors']:
            print(f"Errors: {len(result['errors'])}")
            for err in result['errors']:
                print(f"  - {err['collection']}.{err['index']}: {err['error']}")
    
    # Run explain plans on pilot tenant
    print(f"\n{'='*60}")
    print("EXPLAIN PLANS (ocb_titan)")
    print("=" * 60)
    
    explains = await run_explain_plans(client, "ocb_titan")
    all_results["explain_plans"] = explains
    
    for exp in explains.get("explains", []):
        print(f"\n{exp.get('query')}:")
        if "error" in exp:
            print(f"  Error: {exp['error']}")
        else:
            print(f"  Uses Index: {exp.get('uses_index')}")
            print(f"  Execution Time: {exp.get('execution_time_ms')} ms")
    
    # Save results
    output_dir = "/app/backend/scripts/audit_output"
    with open(f"{output_dir}/index_migration_results.json", "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    
    print(f"\n{'='*60}")
    print("INDEX MIGRATION COMPLETE")
    print(f"{'='*60}")
    print(f"Results saved to: {output_dir}/index_migration_results.json")
    
    return all_results


async def list_all_indexes():
    """List all indexes in pilot tenant"""
    mongo_url = os.environ.get("MONGO_URL")
    client = AsyncIOMotorClient(mongo_url)
    db = client["ocb_titan"]
    
    print("=" * 60)
    print("CURRENT INDEXES IN ocb_titan")
    print("=" * 60)
    
    collections = await db.list_collection_names()
    
    for col_name in sorted(collections):
        col = db[col_name]
        indexes = await col.index_information()
        
        if len(indexes) > 1:  # More than just _id index
            print(f"\n{col_name}:")
            for idx_name, idx_info in indexes.items():
                if idx_name != "_id_":
                    keys = idx_info.get("key", [])
                    print(f"  - {idx_name}: {keys}")


if __name__ == "__main__":
    asyncio.run(run_migration())
    print("\n")
    asyncio.run(list_all_indexes())
