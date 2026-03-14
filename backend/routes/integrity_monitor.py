# OCB TITAN ERP - Nightly Integrity Monitor
# Schedule: 03:00 server time via cron
# Runs comprehensive data integrity checks

from fastapi import APIRouter, Depends, BackgroundTasks
from datetime import datetime, timezone
from database import get_db
from utils.auth import get_current_user
import json
import os
import asyncio

router = APIRouter(prefix="/api/integrity-monitor", tags=["Integrity Monitor"])

# Output directory
OUTPUT_DIR = "/app/reports/integrity"
os.makedirs(OUTPUT_DIR, exist_ok=True)


async def run_inventory_vs_gl_check(db):
    """Check inventory SSOT vs GL inventory account"""
    # Get SSOT inventory value
    ssot_pipeline = [
        {
            "$lookup": {
                "from": "products",
                "localField": "product_id",
                "foreignField": "id",
                "as": "product"
            }
        },
        {
            "$addFields": {
                "cost": {"$ifNull": ["$cost_price", {"$arrayElemAt": ["$product.cost", 0]}]}
            }
        },
        {
            "$group": {
                "_id": None,
                "total_in": {
                    "$sum": {
                        "$cond": [
                            {"$or": [
                                {"$in": [{"$ifNull": ["$movement_type", "$transaction_type"]}, 
                                    ["stock_in", "purchase_in", "adjustment_in", "return_in", "transfer_in"]]},
                                {"$gt": ["$quantity", 0]}
                            ]},
                            {"$multiply": [{"$abs": "$quantity"}, {"$ifNull": ["$cost", 0]}]},
                            0
                        ]
                    }
                },
                "total_out": {
                    "$sum": {
                        "$cond": [
                            {"$or": [
                                {"$in": [{"$ifNull": ["$movement_type", "$transaction_type"]}, 
                                    ["stock_out", "sales_out", "adjustment_out", "return_out", "transfer_out"]]},
                                {"$lt": ["$quantity", 0]}
                            ]},
                            {"$multiply": [{"$abs": "$quantity"}, {"$ifNull": ["$cost", 0]}]},
                            0
                        ]
                    }
                }
            }
        }
    ]
    
    ssot_result = await db["stock_movements"].aggregate(ssot_pipeline).to_list(1)
    ssot_value = (ssot_result[0]["total_in"] - ssot_result[0]["total_out"]) if ssot_result else 0
    
    # Get GL inventory balance
    gl_pipeline = [
        {"$match": {"status": "posted"}},
        {"$unwind": "$entries"},
        {"$match": {
            "$or": [
                {"entries.account_code": {"$regex": "^1-14|^114", "$options": "i"}},
                {"entries.account_name": {"$regex": "persediaan|inventory", "$options": "i"}}
            ]
        }},
        {"$group": {"_id": None, "debit": {"$sum": "$entries.debit"}, "credit": {"$sum": "$entries.credit"}}}
    ]
    
    gl_result = await db["journal_entries"].aggregate(gl_pipeline).to_list(1)
    gl_balance = (gl_result[0]["debit"] - gl_result[0]["credit"]) if gl_result else 0
    
    variance = abs(ssot_value - gl_balance)
    
    return {
        "check": "inventory_vs_gl",
        "ssot_value": ssot_value,
        "gl_balance": gl_balance,
        "variance": variance,
        "status": "PASS" if variance < 1000 else "FAIL",
        "threshold": 1000
    }


async def run_trial_balance_check(db):
    """Validate trial balance: debit = credit"""
    pipeline = [
        {"$match": {"status": "posted"}},
        {"$unwind": "$entries"},
        {"$group": {"_id": None, "debit": {"$sum": "$entries.debit"}, "credit": {"$sum": "$entries.credit"}}}
    ]
    
    result = await db["journal_entries"].aggregate(pipeline).to_list(1)
    
    if result:
        debit = result[0]["debit"]
        credit = result[0]["credit"]
        diff = abs(debit - credit)
    else:
        debit = credit = diff = 0
    
    return {
        "check": "trial_balance",
        "total_debit": debit,
        "total_credit": credit,
        "difference": diff,
        "status": "PASS" if diff < 1 else "FAIL"
    }


async def run_orphan_transaction_check(db):
    """Detect transactions without journals and vice versa"""
    # Sales without journals
    sales_ids = await db["sales_invoices"].distinct("id", {"status": {"$in": ["posted", "completed", "paid"]}})
    journal_refs = await db["journal_entries"].distinct("reference_id")
    
    orphan_sales = [s for s in sales_ids if s not in journal_refs]
    
    # Journals without source
    journal_refs_with_type = await db["journal_entries"].find(
        {"reference_id": {"$exists": True, "$ne": ""}},
        {"_id": 0, "reference_id": 1, "reference_type": 1}
    ).limit(100).to_list(100)
    
    orphan_journals = 0
    for j in journal_refs_with_type:
        ref_type = j.get("reference_type", "").lower()
        ref_id = j.get("reference_id", "")
        
        if "sales" in ref_type:
            exists = await db["sales_invoices"].find_one({"id": ref_id})
            if not exists:
                orphan_journals += 1
    
    return {
        "check": "orphan_transactions",
        "sales_without_journal": len(orphan_sales),
        "journals_without_source": orphan_journals,
        "orphan_sales_sample": orphan_sales[:10],
        "status": "PASS" if len(orphan_sales) == 0 and orphan_journals < 5 else "FAIL"
    }


async def run_duplicate_journal_check(db):
    """Detect duplicate journal postings for same transaction"""
    pipeline = [
        {"$match": {"reference_id": {"$exists": True, "$ne": ""}}},
        {"$group": {"_id": "$reference_id", "count": {"$sum": 1}, "journals": {"$push": "$journal_number"}}},
        {"$match": {"count": {"$gt": 1}}}
    ]
    
    duplicates = await db["journal_entries"].aggregate(pipeline).to_list(100)
    
    return {
        "check": "duplicate_journals",
        "duplicate_count": len(duplicates),
        "duplicates": [{"reference_id": d["_id"], "count": d["count"], "journals": d["journals"][:3]} for d in duplicates[:10]],
        "status": "PASS" if len(duplicates) == 0 else "WARN"
    }


@router.get("/run-all")
async def run_all_integrity_checks(
    user: dict = Depends(get_current_user)
):
    """Run all integrity checks and generate reports"""
    db = get_db()
    timestamp = datetime.now(timezone.utc)
    
    results = {
        "timestamp": timestamp.isoformat(),
        "checks": {},
        "overall_status": "PASS"
    }
    
    # Run all checks
    inv_gl = await run_inventory_vs_gl_check(db)
    results["checks"]["inventory_vs_gl"] = inv_gl
    if inv_gl["status"] != "PASS":
        results["overall_status"] = "FAIL"
    
    tb = await run_trial_balance_check(db)
    results["checks"]["trial_balance"] = tb
    if tb["status"] != "PASS":
        results["overall_status"] = "FAIL"
    
    orphan = await run_orphan_transaction_check(db)
    results["checks"]["orphan_transactions"] = orphan
    if orphan["status"] != "PASS":
        results["overall_status"] = "FAIL"
    
    dup = await run_duplicate_journal_check(db)
    results["checks"]["duplicate_journals"] = dup
    if dup["status"] == "FAIL":
        results["overall_status"] = "FAIL"
    
    # Save reports
    date_str = timestamp.strftime("%Y%m%d")
    
    # Individual reports
    with open(f"{OUTPUT_DIR}/inventory_vs_gl_recon_report_{date_str}.json", "w") as f:
        json.dump(inv_gl, f, indent=2, default=str)
    
    with open(f"{OUTPUT_DIR}/trial_balance_validation_{date_str}.json", "w") as f:
        json.dump(tb, f, indent=2, default=str)
    
    with open(f"{OUTPUT_DIR}/orphan_transaction_report_{date_str}.json", "w") as f:
        json.dump(orphan, f, indent=2, default=str)
    
    # Summary report
    with open(f"{OUTPUT_DIR}/integrity_summary_{date_str}.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    return results


@router.get("/status")
async def get_integrity_status(
    user: dict = Depends(get_current_user)
):
    """Get current integrity status for dashboard widget"""
    db = get_db()
    
    # Quick checks
    tb = await run_trial_balance_check(db)
    
    # Count orphan sales quickly
    sales_count = await db["sales_invoices"].count_documents({"status": {"$in": ["posted", "completed", "paid"]}})
    journal_sales_count = await db["journal_entries"].count_documents({"reference_type": {"$regex": "sales", "$options": "i"}})
    orphan_estimate = max(0, sales_count - journal_sales_count)
    
    status = "HEALTHY"
    alerts = []
    
    if tb["status"] != "PASS":
        status = "CRITICAL"
        alerts.append(f"Trial Balance tidak seimbang: selisih Rp {tb['difference']:,.0f}")
    
    if orphan_estimate > 10:
        status = "WARNING" if status == "HEALTHY" else status
        alerts.append(f"Terdeteksi ~{orphan_estimate} transaksi tanpa jurnal")
    
    return {
        "status": status,
        "last_check": datetime.now(timezone.utc).isoformat(),
        "trial_balance": {
            "status": tb["status"],
            "debit": tb["total_debit"],
            "credit": tb["total_credit"]
        },
        "orphan_estimate": orphan_estimate,
        "alerts": alerts
    }
