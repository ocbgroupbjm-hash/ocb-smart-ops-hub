#!/usr/bin/env python3
"""
OCB TITAN ERP - VERIFY INVENTORY SSOT
Script untuk memverifikasi bahwa Inventory Single Source of Truth valid.

SSOT Rule:
- stock_movements adalah SATU-SATUNYA sumber kebenaran untuk stok
- product_stocks adalah CACHE yang harus sinkron dengan stock_movements
- Jika ada perbedaan, stock_movements yang benar

PENGGUNAAN:
    python3 verify_inventory_ssot.py [--database <db_name>] [--fix] [--output <dir>]

OPTIONS:
    --fix     Otomatis sinkronisasi product_stocks dengan stock_movements
    --output  Direktori output untuk report
"""

import asyncio
import argparse
import json
import os
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from collections import defaultdict

# Configuration
DEFAULT_DB = "ocb_titan"
DEFAULT_OUTPUT_DIR = "/app/backend/scripts/audit_output"
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")


async def calculate_stock_from_movements(db, product_id: str, branch_id: str) -> int:
    """Calculate current stock from stock_movements collection (SSOT)"""
    pipeline = [
        {"$match": {"product_id": product_id, "branch_id": branch_id}},
        {"$group": {"_id": None, "total": {"$sum": "$quantity"}}}
    ]
    result = await db["stock_movements"].aggregate(pipeline).to_list(1)
    return result[0]["total"] if result else 0


async def calculate_all_stock_from_movements(db, branch_id: str) -> dict:
    """Calculate stock for all products in a branch from stock_movements"""
    pipeline = [
        {"$match": {"branch_id": branch_id}},
        {"$group": {"_id": "$product_id", "total": {"$sum": "$quantity"}}}
    ]
    result = await db["stock_movements"].aggregate(pipeline).to_list(100000)
    return {item["_id"]: item["total"] for item in result}


async def verify_inventory_ssot(database: str, fix: bool, output_dir: str):
    """Main verification function"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[database]
    
    print(f"\n{'='*70}")
    print(f"OCB TITAN ERP - VERIFY INVENTORY SSOT")
    print(f"Database: {database}")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print(f"Mode: {'FIX' if fix else 'AUDIT ONLY'}")
    print(f"{'='*70}\n")
    
    # Get all branches
    branches = await db["branches"].find({"is_active": True}, {"_id": 0}).to_list(100)
    print(f"Total Active Branches: {len(branches)}")
    
    # Get all products
    products = await db["products"].find({"is_active": True}, {"_id": 0}).to_list(10000)
    product_map = {p["id"]: p for p in products}
    print(f"Total Active Products: {len(products)}")
    
    # Results tracking
    total_checked = 0
    total_mismatch = 0
    total_fixed = 0
    discrepancies = []
    
    for branch in branches:
        branch_id = branch["id"]
        branch_name = branch.get("name", "Unknown")
        
        print(f"\n--- Checking Branch: {branch_name} ({branch_id}) ---")
        
        # Calculate stock from SSOT (stock_movements)
        ssot_stock = await calculate_all_stock_from_movements(db, branch_id)
        
        # Get cached stock from product_stocks
        cached_stocks = await db["product_stocks"].find(
            {"branch_id": branch_id}, {"_id": 0}
        ).to_list(10000)
        cached_map = {s["product_id"]: s.get("quantity", 0) for s in cached_stocks}
        
        # Compare
        all_product_ids = set(ssot_stock.keys()) | set(cached_map.keys())
        branch_mismatches = []
        
        for pid in all_product_ids:
            ssot_qty = ssot_stock.get(pid, 0)
            cached_qty = cached_map.get(pid, 0)
            
            total_checked += 1
            
            if ssot_qty != cached_qty:
                total_mismatch += 1
                diff = ssot_qty - cached_qty
                product = product_map.get(pid, {})
                
                mismatch = {
                    "branch_id": branch_id,
                    "branch_name": branch_name,
                    "product_id": pid,
                    "product_code": product.get("code", ""),
                    "product_name": product.get("name", "Unknown"),
                    "ssot_qty": ssot_qty,
                    "cached_qty": cached_qty,
                    "difference": diff
                }
                branch_mismatches.append(mismatch)
                discrepancies.append(mismatch)
                
                if abs(diff) > 10:  # Only print significant differences
                    print(f"  ⚠️  {product.get('code', 'N/A')}: SSOT={ssot_qty} vs Cache={cached_qty} (diff={diff})")
                
                # Fix if requested
                if fix:
                    existing = await db["product_stocks"].find_one({
                        "product_id": pid, "branch_id": branch_id
                    })
                    
                    if existing:
                        await db["product_stocks"].update_one(
                            {"product_id": pid, "branch_id": branch_id},
                            {"$set": {
                                "quantity": ssot_qty,
                                "available": ssot_qty - existing.get("reserved", 0),
                                "updated_at": datetime.now(timezone.utc).isoformat(),
                                "synced_from_ssot": True
                            }}
                        )
                    else:
                        await db["product_stocks"].insert_one({
                            "id": f"{pid}_{branch_id}",
                            "product_id": pid,
                            "branch_id": branch_id,
                            "quantity": ssot_qty,
                            "available": ssot_qty,
                            "reserved": 0,
                            "created_at": datetime.now(timezone.utc).isoformat(),
                            "synced_from_ssot": True
                        })
                    
                    total_fixed += 1
        
        if branch_mismatches:
            print(f"  Branch {branch_name}: {len(branch_mismatches)} discrepancies found")
        else:
            print(f"  Branch {branch_name}: ✅ All stocks in sync")
    
    # Summary
    print(f"\n{'='*70}")
    print("SSOT VERIFICATION SUMMARY")
    print(f"{'='*70}")
    print(f"Total Stock Records Checked:   {total_checked}")
    print(f"Total Discrepancies Found:     {total_mismatch}")
    if fix:
        print(f"Total Records Fixed:           {total_fixed}")
    
    if total_mismatch == 0:
        print(f"\n✅ INVENTORY SSOT VALID - product_stocks sinkron dengan stock_movements")
    else:
        print(f"\n⚠️  INVENTORY SSOT VIOLATION - {total_mismatch} records tidak sinkron")
        if fix:
            print(f"✅ All discrepancies have been fixed")
    
    print(f"{'='*70}")
    
    # Generate report
    report = {
        "audit_timestamp": datetime.now(timezone.utc).isoformat(),
        "database": database,
        "mode": "FIX" if fix else "AUDIT",
        "summary": {
            "total_branches": len(branches),
            "total_products": len(products),
            "total_records_checked": total_checked,
            "total_discrepancies": total_mismatch,
            "total_fixed": total_fixed if fix else 0
        },
        "discrepancies": discrepancies[:100],  # First 100
        "validation": {
            "is_valid": total_mismatch == 0 or (fix and total_fixed == total_mismatch),
            "status": "PASS" if total_mismatch == 0 else ("FIXED" if fix else "FAIL")
        }
    }
    
    # Save report
    os.makedirs(output_dir, exist_ok=True)
    
    report_path = os.path.join(output_dir, "inventory_ssot_verification.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\n📄 Report saved: {report_path}")
    
    # Generate Markdown report
    md_report = generate_markdown_report(report)
    md_path = os.path.join(output_dir, "inventory_ssot_verification.md")
    with open(md_path, "w") as f:
        f.write(md_report)
    print(f"📄 Markdown report saved: {md_path}")
    
    client.close()
    return report


def generate_markdown_report(report: dict) -> str:
    """Generate Markdown formatted report"""
    md = []
    md.append("# OCB TITAN ERP - INVENTORY SSOT VERIFICATION REPORT")
    md.append(f"\n**Audit Timestamp:** {report['audit_timestamp']}")
    md.append(f"**Database:** {report['database']}")
    md.append(f"**Mode:** {report['mode']}")
    
    # Status
    status = report["validation"]["status"]
    status_icon = "✅" if status in ["PASS", "FIXED"] else "❌"
    md.append(f"\n## Status: {status_icon} {status}")
    
    # Summary
    s = report["summary"]
    md.append("\n## Summary")
    md.append(f"- **Total Branches:** {s['total_branches']}")
    md.append(f"- **Total Products:** {s['total_products']}")
    md.append(f"- **Total Records Checked:** {s['total_records_checked']}")
    md.append(f"- **Total Discrepancies:** {s['total_discrepancies']}")
    if report["mode"] == "FIX":
        md.append(f"- **Total Fixed:** {s['total_fixed']}")
    
    # SSOT Principle
    md.append("\n## SSOT Principle")
    md.append("```")
    md.append("Single Source of Truth: stock_movements")
    md.append("Cache Collection: product_stocks")
    md.append("")
    md.append("Rule:")
    md.append("- stock_movements adalah SUMBER KEBENARAN")
    md.append("- product_stocks adalah CACHE yang harus sinkron")
    md.append("- Semua query stok HARUS dari stock_movements")
    md.append("```")
    
    # Discrepancies
    discrepancies = report.get("discrepancies", [])
    if discrepancies:
        md.append(f"\n## Discrepancies ({len(discrepancies)} shown)")
        md.append("\n| Branch | Product | SSOT Qty | Cache Qty | Diff |")
        md.append("|--------|---------|----------|-----------|------|")
        for d in discrepancies[:50]:
            md.append(f"| {d['branch_name'][:15]} | {d['product_code']} | {d['ssot_qty']} | {d['cached_qty']} | {d['difference']} |")
    else:
        md.append("\n## ✅ No Discrepancies Found")
    
    # Recommendations
    md.append("\n## Recommendations")
    if report["validation"]["status"] == "PASS":
        md.append("- Inventory SSOT is valid")
        md.append("- Continue using stock_movements as source of truth")
        md.append("- product_stocks can be used for quick reads (cached)")
    else:
        md.append("- Run with `--fix` flag to synchronize product_stocks")
        md.append("- Review API endpoints that write directly to product_stocks")
        md.append("- Refactor APIs to use stock_movements for all calculations")
    
    md.append(f"\n---\n*Report generated: {report['audit_timestamp']}*")
    
    return "\n".join(md)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify Inventory SSOT for OCB TITAN ERP")
    parser.add_argument("--database", "-d", default=DEFAULT_DB, help=f"Database name (default: {DEFAULT_DB})")
    parser.add_argument("--fix", "-f", action="store_true", help="Fix discrepancies by syncing product_stocks")
    parser.add_argument("--output", "-o", default=DEFAULT_OUTPUT_DIR, help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})")
    
    args = parser.parse_args()
    
    asyncio.run(verify_inventory_ssot(args.database, args.fix, args.output))
