"""
OCB TITAN ERP - RECONCILIATION MONITOR API
MASTER BLUEPRINT: Production Hardening Phase 20

Dashboard endpoints for:
1. Journal Balance Monitor - SUM(debit) vs SUM(credit)
2. Stock Integrity Monitor - movement_qty vs stock_view
3. Cash Variance Monitor - branch, shift, variance, user

Path: /system/reconciliation
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from database import get_db
from utils.auth import get_current_user
import os
import json

router = APIRouter(prefix="/system", tags=["System Reconciliation Monitor"])

# RBAC - Only OWNER and SUPER_ADMIN can access
ALLOWED_ROLES = ["owner", "super_admin", "admin", "auditor"]


def require_reconciliation_role():
    """Check if user has access to reconciliation dashboard"""
    async def check_role(user: dict = Depends(get_current_user)):
        user_role = (user.get("role", "") or "").lower()
        user_role_code = (user.get("role_code", "") or "").lower()
        permissions = user.get("permissions", [])
        
        has_access = (
            user_role in ALLOWED_ROLES or 
            user_role_code in ALLOWED_ROLES or 
            "*" in permissions
        )
        
        if not has_access:
            raise HTTPException(
                status_code=403,
                detail="AKSES DITOLAK: Hanya OWNER, SUPER_ADMIN, atau AUDITOR yang dapat mengakses reconciliation monitor"
            )
        return user
    return check_role


# ==================== JOURNAL BALANCE MONITOR ====================

@router.get("/reconciliation/journal-balance")
async def get_journal_balance_monitor(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    user: dict = Depends(require_reconciliation_role())
):
    """
    Panel 1: Journal Balance Monitor
    
    Menampilkan:
    - SUM(debit)
    - SUM(credit)
    - status
    
    Jika tidak balance: ALERT
    """
    db = get_db()
    
    # Build date filter
    match_filter = {"status": "posted"}
    if date_from or date_to:
        match_filter["posted_at"] = {}
        if date_from:
            match_filter["posted_at"]["$gte"] = date_from
        if date_to:
            match_filter["posted_at"]["$lte"] = date_to + "T23:59:59"
    
    # Aggregate totals
    pipeline = [
        {"$match": match_filter},
        {"$unwind": "$entries"},
        {"$group": {
            "_id": None,
            "total_debit": {"$sum": "$entries.debit"},
            "total_credit": {"$sum": "$entries.credit"},
            "journal_count": {"$sum": 1}
        }}
    ]
    
    result = await db["journal_entries"].aggregate(pipeline).to_list(1)
    
    if not result:
        return {
            "status": "OK",
            "message": "No journal entries found",
            "total_debit": 0,
            "total_credit": 0,
            "difference": 0,
            "balanced": True,
            "journal_count": 0
        }
    
    data = result[0]
    debit = data.get("total_debit", 0) or 0
    credit = data.get("total_credit", 0) or 0
    diff = abs(debit - credit)
    balanced = diff < 1
    
    return {
        "status": "OK" if balanced else "ALERT",
        "total_debit": debit,
        "total_credit": credit,
        "difference": diff,
        "balanced": balanced,
        "journal_count": data.get("journal_count", 0),
        "alert_message": None if balanced else f"IMBALANCE DETECTED: Difference of Rp {diff:,.0f}"
    }


@router.get("/reconciliation/journal-detail")
async def get_unbalanced_journals(
    limit: int = 50,
    user: dict = Depends(require_reconciliation_role())
):
    """Get list of unbalanced journal entries"""
    db = get_db()
    
    # Find journals where debit != credit
    journals = await db["journal_entries"].find(
        {"status": "posted"},
        {"_id": 0, "journal_number": 1, "entries": 1, "description": 1, "posted_at": 1, "transaction_type": 1}
    ).sort("posted_at", -1).limit(limit * 2).to_list(limit * 2)
    
    unbalanced = []
    for j in journals:
        entries = j.get("entries", [])
        total_d = sum(e.get("debit", 0) or 0 for e in entries)
        total_c = sum(e.get("credit", 0) or 0 for e in entries)
        diff = abs(total_d - total_c)
        
        if diff > 0.01:
            unbalanced.append({
                "journal_number": j.get("journal_number"),
                "description": j.get("description", ""),
                "transaction_type": j.get("transaction_type", ""),
                "posted_at": j.get("posted_at"),
                "total_debit": total_d,
                "total_credit": total_c,
                "difference": diff
            })
    
    return {
        "total_unbalanced": len(unbalanced),
        "journals": unbalanced[:limit]
    }


# ==================== STOCK INTEGRITY MONITOR ====================

@router.get("/reconciliation/stock-integrity")
async def get_stock_integrity_monitor(
    limit: int = 100,
    show_discrepancies_only: bool = True,
    user: dict = Depends(require_reconciliation_role())
):
    """
    Panel 2: Stock Integrity Monitor
    
    Menampilkan:
    - product_id
    - movement_qty (from SSOT)
    - stock_view (from cache)
    - difference
    """
    db = get_db()
    
    # Get stock from movements (SSOT)
    movement_pipeline = [
        {"$group": {
            "_id": "$product_id",
            "movement_qty": {"$sum": "$quantity"},
            "product_name": {"$first": "$product_name"}
        }},
        {"$sort": {"_id": 1}}
    ]
    
    movement_results = await db["stock_movements"].aggregate(movement_pipeline).to_list(10000)
    movement_map = {r["_id"]: {"qty": r["movement_qty"], "name": r.get("product_name", "")} for r in movement_results}
    
    # Get stock from products (cache)
    products = await db["products"].find({}, {"_id": 0, "id": 1, "name": 1, "stock": 1, "sku": 1}).to_list(10000)
    product_map = {p.get("id"): {"qty": p.get("stock", 0) or 0, "name": p.get("name", ""), "sku": p.get("sku", "")} for p in products}
    
    # Compare
    all_ids = set(movement_map.keys()) | set(product_map.keys())
    
    results = []
    discrepancy_count = 0
    
    for pid in all_ids:
        if not pid:
            continue
            
        movement_data = movement_map.get(pid, {"qty": 0, "name": ""})
        product_data = product_map.get(pid, {"qty": 0, "name": "", "sku": ""})
        
        movement_qty = movement_data["qty"] or 0
        cache_qty = product_data["qty"] or 0
        diff = movement_qty - cache_qty
        
        if show_discrepancies_only and abs(diff) < 0.01:
            continue
        
        if abs(diff) > 0:
            discrepancy_count += 1
        
        results.append({
            "product_id": pid,
            "product_name": product_data["name"] or movement_data["name"],
            "sku": product_data.get("sku", ""),
            "movement_qty": movement_qty,
            "stock_view": cache_qty,
            "difference": diff,
            "status": "DISCREPANCY" if abs(diff) > 0 else "OK"
        })
    
    # Sort by absolute difference descending
    results.sort(key=lambda x: abs(x["difference"]), reverse=True)
    
    return {
        "status": "ALERT" if discrepancy_count > 0 else "OK",
        "total_products": len(all_ids),
        "discrepancies_found": discrepancy_count,
        "items": results[:limit],
        "alert_message": None if discrepancy_count == 0 else f"STOCK DRIFT DETECTED: {discrepancy_count} products have discrepancies"
    }


# ==================== CASH VARIANCE MONITOR ====================

@router.get("/reconciliation/cash-variance")
async def get_cash_variance_monitor(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    branch_id: Optional[str] = None,
    limit: int = 100,
    user: dict = Depends(require_reconciliation_role())
):
    """
    Panel 3: Cash Variance Monitor
    
    Menampilkan:
    - branch
    - shift
    - variance
    - user (cashier)
    """
    db = get_db()
    
    # Build query
    query = {}
    if branch_id:
        query["branch_id"] = branch_id
    
    if date_from or date_to:
        query["end_time"] = {}
        if date_from:
            query["end_time"]["$gte"] = date_from
        if date_to:
            query["end_time"]["$lte"] = date_to + "T23:59:59"
    
    # Get closed shifts with variance
    shifts = await db["cashier_shifts"].find(
        {**query, "status": {"$in": ["closed", "reviewed", "discrepancy"]}},
        {"_id": 0}
    ).sort("end_time", -1).limit(limit).to_list(limit)
    
    results = []
    total_variance = 0
    shortage_count = 0
    overage_count = 0
    
    for shift in shifts:
        expected = shift.get("expected_cash", 0) or 0
        actual = shift.get("actual_cash", 0) or 0
        variance = actual - expected
        
        if variance < 0:
            shortage_count += 1
        elif variance > 0:
            overage_count += 1
        
        total_variance += variance
        
        results.append({
            "shift_id": shift.get("id"),
            "branch_id": shift.get("branch_id"),
            "branch_name": shift.get("branch_name", ""),
            "cashier_id": shift.get("cashier_id"),
            "cashier_name": shift.get("cashier_name", ""),
            "start_time": shift.get("start_time"),
            "end_time": shift.get("end_time"),
            "initial_cash": shift.get("initial_cash", 0),
            "expected_cash": expected,
            "actual_cash": actual,
            "variance": variance,
            "variance_type": "shortage" if variance < 0 else ("overage" if variance > 0 else "match"),
            "status": shift.get("status")
        })
    
    return {
        "status": "ALERT" if shortage_count > 0 else "OK",
        "total_shifts": len(results),
        "shortages": shortage_count,
        "overages": overage_count,
        "total_variance": total_variance,
        "items": results,
        "alert_message": None if shortage_count == 0 else f"CASH SHORTAGE DETECTED: {shortage_count} shifts with shortages, total Rp {abs(sum(r['variance'] for r in results if r['variance'] < 0)):,.0f}"
    }


# ==================== OVERALL RECONCILIATION DASHBOARD ====================

@router.get("/reconciliation/dashboard")
async def get_reconciliation_dashboard(
    user: dict = Depends(require_reconciliation_role())
):
    """
    Main reconciliation dashboard combining all monitors
    """
    db = get_db()
    
    # Get journal balance
    journal_pipeline = [
        {"$match": {"status": "posted"}},
        {"$unwind": "$entries"},
        {"$group": {
            "_id": None,
            "total_debit": {"$sum": "$entries.debit"},
            "total_credit": {"$sum": "$entries.credit"}
        }}
    ]
    journal_result = await db["journal_entries"].aggregate(journal_pipeline).to_list(1)
    
    if journal_result:
        j = journal_result[0]
        journal_debit = j.get("total_debit", 0) or 0
        journal_credit = j.get("total_credit", 0) or 0
        journal_balanced = abs(journal_debit - journal_credit) < 1
    else:
        journal_debit = 0
        journal_credit = 0
        journal_balanced = True
    
    # Get stock discrepancy count
    stock_result = await db["system_alerts"].count_documents({
        "type": "stock_discrepancy",
        "acknowledged": False
    })
    
    # Get cash variance summary
    today = datetime.now(timezone.utc).date().isoformat()
    cash_result = await db["cashier_shifts"].count_documents({
        "status": "discrepancy",
        "end_time": {"$gte": today}
    })
    
    # Get recent alerts
    alerts = await db["system_alerts"].find(
        {"acknowledged": False},
        {"_id": 0}
    ).sort("created_at", -1).limit(10).to_list(10)
    
    # Determine overall health
    issues = []
    if not journal_balanced:
        issues.append("Journal imbalance detected")
    if stock_result > 0:
        issues.append(f"{stock_result} stock discrepancies")
    if cash_result > 0:
        issues.append(f"{cash_result} cash variances today")
    
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "overall_status": "ALERT" if issues else "OK",
        "issues": issues,
        "monitors": {
            "journal_balance": {
                "status": "OK" if journal_balanced else "ALERT",
                "total_debit": journal_debit,
                "total_credit": journal_credit,
                "balanced": journal_balanced
            },
            "stock_integrity": {
                "status": "OK" if stock_result == 0 else "ALERT",
                "pending_discrepancies": stock_result
            },
            "cash_variance": {
                "status": "OK" if cash_result == 0 else "ALERT",
                "variances_today": cash_result
            }
        },
        "recent_alerts": alerts
    }


# ==================== SYSTEM HEALTH ====================

@router.get("/health")
async def get_system_health(
    user: dict = Depends(require_reconciliation_role())
):
    """Get overall system health status"""
    from utils.observability import get_system_health as get_health
    
    return await get_health()


@router.get("/health/traces")
async def get_recent_traces(
    limit: int = 100,
    operation: Optional[str] = None,
    status: Optional[str] = None,
    user: dict = Depends(require_reconciliation_role())
):
    """Get recent request traces"""
    from utils.observability import get_recent_traces as get_traces
    
    return {
        "traces": get_traces(limit, operation, status),
        "total": len(get_traces(limit * 10))
    }


@router.get("/health/metrics")
async def get_system_metrics(
    user: dict = Depends(require_reconciliation_role())
):
    """Get system metrics summary"""
    from utils.observability import get_metrics
    
    return get_metrics()


# ==================== REPORTS ====================

@router.get("/reconciliation/reports")
async def list_reconciliation_reports(
    user: dict = Depends(require_reconciliation_role())
):
    """List available reconciliation reports"""
    reports_dir = "/app/reports"
    
    if not os.path.exists(reports_dir):
        return {"reports": []}
    
    reports = []
    for filename in os.listdir(reports_dir):
        if filename.endswith(".json"):
            filepath = os.path.join(reports_dir, filename)
            stat = os.stat(filepath)
            reports.append({
                "filename": filename,
                "path": filepath,
                "size_bytes": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc).isoformat()
            })
    
    reports.sort(key=lambda x: x["created_at"], reverse=True)
    
    return {"reports": reports}


@router.get("/reconciliation/reports/{filename}")
async def get_reconciliation_report(
    filename: str,
    user: dict = Depends(require_reconciliation_role())
):
    """Get specific reconciliation report"""
    filepath = f"/app/reports/{filename}"
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"Report not found: {filename}")
    
    with open(filepath, "r") as f:
        return json.load(f)
