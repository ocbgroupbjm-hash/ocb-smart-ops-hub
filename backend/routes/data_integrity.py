# OCB TITAN ERP - Data Integrity Reconciliation Engine
# Automatic validation for critical financial data

from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone
from database import get_db
from utils.auth import get_current_user
from typing import Dict, List, Any
import uuid

router = APIRouter(prefix="/api/integrity", tags=["Data Integrity"])


# ==================== INVENTORY vs GL RECONCILIATION ====================

@router.get("/inventory-vs-gl")
async def inventory_vs_gl_reconciliation(
    user: dict = Depends(get_current_user)
):
    """
    Compare inventory value (from stock_movements) with GL inventory account.
    Generates alert if variance exceeds threshold.
    """
    db = get_db()
    
    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "checking",
        "inventory_value": {},
        "gl_value": {},
        "variance": {},
        "alerts": []
    }
    
    # 1. Calculate inventory value from stock_movements
    # Sum of (quantity * unit_cost) for all IN movements
    # Minus (quantity * unit_cost) for all OUT movements
    
    inventory_pipeline = [
        {
            "$group": {
                "_id": None,
                "total_in_value": {
                    "$sum": {
                        "$cond": [
                            {"$in": ["$movement_type", ["stock_in", "purchase_in", "adjustment_in", "return_in"]]},
                            {"$multiply": ["$quantity", {"$ifNull": ["$unit_cost", 0]}]},
                            0
                        ]
                    }
                },
                "total_out_value": {
                    "$sum": {
                        "$cond": [
                            {"$in": ["$movement_type", ["stock_out", "sales_out", "adjustment_out", "return_out"]]},
                            {"$multiply": ["$quantity", {"$ifNull": ["$unit_cost", 0]}]},
                            0
                        ]
                    }
                },
                "total_in_qty": {
                    "$sum": {
                        "$cond": [
                            {"$in": ["$movement_type", ["stock_in", "purchase_in", "adjustment_in", "return_in"]]},
                            "$quantity",
                            0
                        ]
                    }
                },
                "total_out_qty": {
                    "$sum": {
                        "$cond": [
                            {"$in": ["$movement_type", ["stock_out", "sales_out", "adjustment_out", "return_out"]]},
                            "$quantity",
                            0
                        ]
                    }
                }
            }
        }
    ]
    
    inv_result = await db["stock_movements"].aggregate(inventory_pipeline).to_list(1)
    
    if inv_result:
        inv_data = inv_result[0]
        inventory_net_value = inv_data["total_in_value"] - inv_data["total_out_value"]
        inventory_net_qty = inv_data["total_in_qty"] - inv_data["total_out_qty"]
    else:
        inventory_net_value = 0
        inventory_net_qty = 0
    
    result["inventory_value"] = {
        "total_in_value": inv_data["total_in_value"] if inv_result else 0,
        "total_out_value": inv_data["total_out_value"] if inv_result else 0,
        "net_value": inventory_net_value,
        "net_quantity": inventory_net_qty
    }
    
    # 2. Get GL Inventory Account balance
    # Typically account code 1-14xx or similar for inventory
    
    gl_pipeline = [
        {"$unwind": "$entries"},
        {
            "$match": {
                "$or": [
                    {"entries.account_code": {"$regex": "^1-14|^14", "$options": "i"}},
                    {"entries.account_name": {"$regex": "persediaan|inventory|stock", "$options": "i"}}
                ]
            }
        },
        {
            "$group": {
                "_id": None,
                "total_debit": {"$sum": "$entries.debit"},
                "total_credit": {"$sum": "$entries.credit"}
            }
        }
    ]
    
    gl_result = await db["journal_entries"].aggregate(gl_pipeline).to_list(1)
    
    if gl_result:
        gl_data = gl_result[0]
        gl_balance = gl_data["total_debit"] - gl_data["total_credit"]
    else:
        gl_balance = 0
    
    result["gl_value"] = {
        "total_debit": gl_data["total_debit"] if gl_result else 0,
        "total_credit": gl_data["total_credit"] if gl_result else 0,
        "net_balance": gl_balance
    }
    
    # 3. Calculate variance
    variance = abs(inventory_net_value - gl_balance)
    variance_percent = (variance / max(abs(inventory_net_value), 1)) * 100 if inventory_net_value != 0 else 0
    
    result["variance"] = {
        "amount": variance,
        "percentage": round(variance_percent, 2),
        "inventory_value": inventory_net_value,
        "gl_balance": gl_balance
    }
    
    # 4. Generate alerts
    VARIANCE_THRESHOLD = 1000  # Rp 1,000 tolerance
    VARIANCE_PERCENT_THRESHOLD = 1  # 1% tolerance
    
    if variance > VARIANCE_THRESHOLD or variance_percent > VARIANCE_PERCENT_THRESHOLD:
        result["alerts"].append({
            "type": "INVENTORY_GL_MISMATCH",
            "severity": "HIGH" if variance_percent > 5 else "MEDIUM",
            "message": f"Inventory vs GL variance: Rp {variance:,.0f} ({variance_percent:.2f}%)",
            "action": "Review stock movements and journal entries for reconciliation"
        })
        result["status"] = "mismatch"
    else:
        result["status"] = "matched"
    
    return result


# ==================== TRIAL BALANCE VALIDATOR ====================

@router.get("/trial-balance")
async def validate_trial_balance(
    user: dict = Depends(get_current_user)
):
    """
    Validate trial balance - total debit must equal total credit.
    """
    db = get_db()
    
    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "checking",
        "totals": {},
        "by_account_type": {},
        "alerts": []
    }
    
    # Calculate total debit and credit from all journal entries
    pipeline = [
        {"$unwind": "$entries"},
        {
            "$group": {
                "_id": None,
                "total_debit": {"$sum": "$entries.debit"},
                "total_credit": {"$sum": "$entries.credit"},
                "entry_count": {"$sum": 1}
            }
        }
    ]
    
    tb_result = await db["journal_entries"].aggregate(pipeline).to_list(1)
    
    if tb_result:
        data = tb_result[0]
        total_debit = data["total_debit"]
        total_credit = data["total_credit"]
        entry_count = data["entry_count"]
    else:
        total_debit = 0
        total_credit = 0
        entry_count = 0
    
    difference = abs(total_debit - total_credit)
    is_balanced = difference < 0.01  # Allow 1 cent tolerance for rounding
    
    result["totals"] = {
        "total_debit": total_debit,
        "total_credit": total_credit,
        "difference": difference,
        "entry_count": entry_count,
        "is_balanced": is_balanced
    }
    
    # Get breakdown by account type
    type_pipeline = [
        {"$unwind": "$entries"},
        {
            "$group": {
                "_id": {"$ifNull": ["$entries.account_type", "unknown"]},
                "debit": {"$sum": "$entries.debit"},
                "credit": {"$sum": "$entries.credit"}
            }
        }
    ]
    
    type_result = await db["journal_entries"].aggregate(type_pipeline).to_list(100)
    
    result["by_account_type"] = {
        r["_id"]: {"debit": r["debit"], "credit": r["credit"]}
        for r in type_result
    }
    
    # Generate alerts
    if not is_balanced:
        result["alerts"].append({
            "type": "TRIAL_BALANCE_IMBALANCE",
            "severity": "CRITICAL",
            "message": f"Trial Balance tidak seimbang! Selisih: Rp {difference:,.2f}",
            "action": "Review jurnal entries untuk menemukan kesalahan posting"
        })
        result["status"] = "imbalanced"
    else:
        result["status"] = "balanced"
    
    return result


# ==================== ORPHAN TRANSACTION DETECTOR ====================

@router.get("/orphan-transactions")
async def detect_orphan_transactions(
    user: dict = Depends(get_current_user)
):
    """
    Detect:
    - Transactions without journal entries
    - Journal entries without source transaction
    - Duplicate postings
    """
    db = get_db()
    
    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "checking",
        "orphans": {
            "sales_without_journal": [],
            "purchases_without_journal": [],
            "journals_without_source": [],
            "duplicate_postings": []
        },
        "counts": {},
        "alerts": []
    }
    
    # 1. Check sales without journal
    # Get all sales invoice IDs
    sales_ids = await db["sales_invoices"].distinct("id")
    
    # Get all journal reference IDs for sales
    journal_sales_refs = await db["journal_entries"].distinct(
        "reference_id",
        {"reference_type": {"$in": ["sales", "sales_invoice", "invoice"]}}
    )
    
    sales_without_journal = [s for s in sales_ids if s not in journal_sales_refs][:20]
    result["orphans"]["sales_without_journal"] = sales_without_journal
    
    # 2. Check purchases without journal
    purchase_ids = await db["purchase_orders"].distinct("id", {"status": {"$in": ["received", "posted", "completed"]}})
    
    journal_purchase_refs = await db["journal_entries"].distinct(
        "reference_id",
        {"reference_type": {"$in": ["purchase", "purchase_order", "po"]}}
    )
    
    purchases_without_journal = [p for p in purchase_ids if p not in journal_purchase_refs][:20]
    result["orphans"]["purchases_without_journal"] = purchases_without_journal
    
    # 3. Check journals without source
    # Get journal entries that reference non-existent documents
    orphan_journals = []
    
    sample_journals = await db["journal_entries"].find(
        {"reference_id": {"$exists": True, "$ne": ""}},
        {"_id": 0, "id": 1, "journal_number": 1, "reference_type": 1, "reference_id": 1}
    ).limit(100).to_list(100)
    
    for j in sample_journals:
        ref_type = j.get("reference_type", "")
        ref_id = j.get("reference_id", "")
        
        if not ref_id:
            continue
        
        # Check if reference exists
        exists = False
        if "sales" in ref_type.lower():
            exists = await db["sales_invoices"].find_one({"id": ref_id}) is not None
        elif "purchase" in ref_type.lower():
            exists = await db["purchase_orders"].find_one({"id": ref_id}) is not None
        elif "ap" in ref_type.lower() or "payable" in ref_type.lower():
            exists = await db["accounts_payable"].find_one({"id": ref_id}) is not None
        elif "ar" in ref_type.lower() or "receivable" in ref_type.lower():
            exists = await db["accounts_receivable"].find_one({"id": ref_id}) is not None
        
        if not exists and ref_type:
            orphan_journals.append({
                "journal_id": j.get("id"),
                "journal_number": j.get("journal_number"),
                "reference_type": ref_type,
                "reference_id": ref_id
            })
    
    result["orphans"]["journals_without_source"] = orphan_journals[:20]
    
    # 4. Check duplicate postings
    dup_pipeline = [
        {
            "$group": {
                "_id": "$reference_id",
                "count": {"$sum": 1},
                "journals": {"$push": "$journal_number"}
            }
        },
        {"$match": {"count": {"$gt": 1}, "_id": {"$nin": [None, ""]}}},
        {"$limit": 20}
    ]
    
    duplicates = await db["journal_entries"].aggregate(dup_pipeline).to_list(20)
    result["orphans"]["duplicate_postings"] = [
        {"reference_id": d["_id"], "count": d["count"], "journals": d["journals"][:5]}
        for d in duplicates
    ]
    
    # Summary counts
    result["counts"] = {
        "sales_without_journal": len(sales_without_journal),
        "purchases_without_journal": len(purchases_without_journal),
        "journals_without_source": len(orphan_journals),
        "duplicate_postings": len(duplicates)
    }
    
    # Generate alerts
    total_orphans = sum(result["counts"].values())
    if total_orphans > 0:
        result["status"] = "issues_found"
        
        if len(sales_without_journal) > 0:
            result["alerts"].append({
                "type": "SALES_NO_JOURNAL",
                "severity": "HIGH",
                "message": f"{len(sales_without_journal)} penjualan tidak memiliki jurnal",
                "action": "Jalankan re-posting untuk transaksi yang tidak memiliki jurnal"
            })
        
        if len(duplicates) > 0:
            result["alerts"].append({
                "type": "DUPLICATE_POSTING",
                "severity": "CRITICAL",
                "message": f"{len(duplicates)} transaksi dengan jurnal duplikat",
                "action": "Review dan hapus jurnal duplikat (yang lebih baru)"
            })
    else:
        result["status"] = "clean"
    
    return result


# ==================== INTEGRITY SUMMARY DASHBOARD ====================

@router.get("/summary")
async def integrity_summary(
    user: dict = Depends(get_current_user)
):
    """
    Get summary of all integrity checks for dashboard widget.
    """
    db = get_db()
    
    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "overall_status": "healthy",
        "checks": {
            "trial_balance": {"status": "unknown"},
            "inventory_vs_gl": {"status": "unknown"},
            "orphan_transactions": {"status": "unknown"}
        },
        "critical_alerts": []
    }
    
    # Quick trial balance check
    tb_result = await db["journal_entries"].aggregate([
        {"$unwind": "$entries"},
        {"$group": {"_id": None, "d": {"$sum": "$entries.debit"}, "c": {"$sum": "$entries.credit"}}}
    ]).to_list(1)
    
    if tb_result:
        diff = abs(tb_result[0]["d"] - tb_result[0]["c"])
        is_balanced = diff < 0.01
        summary["checks"]["trial_balance"] = {
            "status": "balanced" if is_balanced else "imbalanced",
            "difference": diff
        }
        if not is_balanced:
            summary["overall_status"] = "critical"
            summary["critical_alerts"].append("Trial Balance tidak seimbang")
    
    # Quick orphan check
    sales_count = await db["sales_invoices"].count_documents({})
    journal_sales_count = await db["journal_entries"].count_documents({
        "reference_type": {"$in": ["sales", "sales_invoice", "invoice"]}
    })
    
    orphan_estimate = max(0, sales_count - journal_sales_count)
    summary["checks"]["orphan_transactions"] = {
        "status": "clean" if orphan_estimate < 5 else "issues_found",
        "estimated_orphans": orphan_estimate
    }
    
    if orphan_estimate > 10:
        summary["overall_status"] = "warning" if summary["overall_status"] == "healthy" else summary["overall_status"]
    
    return summary


# ==================== AUTOMATIC FIX ENDPOINTS ====================

@router.post("/fix/missing-journals")
async def fix_missing_journals(
    limit: int = 10,
    user: dict = Depends(get_current_user)
):
    """
    Attempt to create missing journal entries for posted transactions.
    USE WITH CAUTION - only for recovery purposes.
    """
    role = user.get("role_code") or user.get("role") or ""
    if role not in ["owner", "super_admin"]:
        raise HTTPException(status_code=403, detail="Owner/Super Admin only")
    
    # This is a placeholder - actual implementation would need
    # to go through BRE to properly create journal entries
    return {
        "message": "This feature requires manual review. Please contact system administrator.",
        "recommendation": "Run data migration script with proper BRE integration"
    }
