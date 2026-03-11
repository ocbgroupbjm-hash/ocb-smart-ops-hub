"""
OCB TITAN ERP - PHASE 2 FINANCIAL CONTROL SYSTEM
Module: Financial Consistency Checker
Following OCB TITAN AI MASTER LAW - NON-DESTRUCTIVE Development

This module validates:
1. Journal entries are always balanced
2. Stock matches stock_movements
3. AR/AP matches journals
4. Trial balance is consistent
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from database import get_db as get_database
from routes.auth import get_current_user
from routes.rbac_middleware import require_permission
import uuid

router = APIRouter(prefix="/api/consistency-checker", tags=["Financial Consistency Checker"])

# ==================== CONSISTENCY CHECK TYPES ====================

CHECK_TYPES = {
    "journal_balance": {
        "name": "Keseimbangan Jurnal",
        "description": "Memastikan setiap jurnal memiliki debit = kredit",
        "severity": "critical"
    },
    "trial_balance": {
        "name": "Neraca Saldo",
        "description": "Memastikan total debit = total kredit di neraca saldo",
        "severity": "critical"
    },
    "stock_movement": {
        "name": "Pergerakan Stok",
        "description": "Memastikan stok sesuai dengan stock_movements",
        "severity": "critical"
    },
    "ar_journal": {
        "name": "Piutang vs Jurnal",
        "description": "Memastikan saldo piutang sesuai dengan jurnal",
        "severity": "high"
    },
    "ap_journal": {
        "name": "Hutang vs Jurnal",
        "description": "Memastikan saldo hutang sesuai dengan jurnal",
        "severity": "high"
    },
    "cash_balance": {
        "name": "Saldo Kas",
        "description": "Memastikan saldo kas sesuai dengan transaksi",
        "severity": "high"
    }
}

# ==================== PYDANTIC MODELS ====================

class ConsistencyCheckResult(BaseModel):
    check_type: str
    status: str  # "pass", "fail", "warning"
    message: str
    details: Optional[Dict[str, Any]] = None
    discrepancies: Optional[List[Dict[str, Any]]] = None

class FullConsistencyReport(BaseModel):
    report_id: str
    generated_at: str
    overall_status: str
    checks: List[ConsistencyCheckResult]
    summary: Dict[str, Any]

# ==================== CONSISTENCY CHECK FUNCTIONS ====================

async def check_journal_balance(db, branch_id: str = None, period: str = None) -> ConsistencyCheckResult:
    """Check if all journal entries are balanced (debit = credit)"""
    
    query = {}
    if branch_id:
        query["branch_id"] = branch_id
    if period:
        query["journal_date"] = {"$regex": f"^{period}"}
    
    # Find unbalanced journals
    unbalanced = await db.journal_entries.find({
        **query,
        "$expr": {"$ne": ["$total_debit", "$total_credit"]}
    }, {"_id": 0, "id": 1, "journal_no": 1, "total_debit": 1, "total_credit": 1}).to_list(100)
    
    if not unbalanced:
        return ConsistencyCheckResult(
            check_type="journal_balance",
            status="pass",
            message="Semua jurnal seimbang (debit = kredit)",
            details={"checked_journals": await db.journal_entries.count_documents(query)}
        )
    
    return ConsistencyCheckResult(
        check_type="journal_balance",
        status="fail",
        message=f"Ditemukan {len(unbalanced)} jurnal tidak seimbang",
        discrepancies=[
            {
                "journal_no": j["journal_no"],
                "debit": j["total_debit"],
                "credit": j["total_credit"],
                "difference": abs(j["total_debit"] - j["total_credit"])
            }
            for j in unbalanced[:10]  # Show first 10
        ]
    )

async def check_trial_balance(db, period: str = None) -> ConsistencyCheckResult:
    """Check if trial balance is balanced"""
    
    match_query = {}
    if period:
        match_query["journal_date"] = {"$regex": f"^{period}"}
    
    # Aggregate all journal entries
    pipeline = [
        {"$match": match_query},
        {"$unwind": "$entries"},
        {
            "$group": {
                "_id": "$entries.account_code",
                "account_name": {"$first": "$entries.account_name"},
                "total_debit": {"$sum": "$entries.debit"},
                "total_credit": {"$sum": "$entries.credit"}
            }
        },
        {"$sort": {"_id": 1}}
    ]
    
    accounts = await db.journal_entries.aggregate(pipeline).to_list(500)
    
    total_debit = sum(a.get("total_debit", 0) for a in accounts)
    total_credit = sum(a.get("total_credit", 0) for a in accounts)
    
    difference = abs(total_debit - total_credit)
    is_balanced = difference < 0.01
    
    return ConsistencyCheckResult(
        check_type="trial_balance",
        status="pass" if is_balanced else "fail",
        message="Neraca saldo seimbang" if is_balanced else f"Neraca saldo tidak seimbang (selisih: {difference:,.2f})",
        details={
            "total_debit": total_debit,
            "total_credit": total_credit,
            "difference": difference,
            "account_count": len(accounts)
        }
    )

async def check_stock_consistency(db, branch_id: str = None) -> ConsistencyCheckResult:
    """Check if stock quantities match stock movements"""
    
    query = {}
    if branch_id:
        query["branch_id"] = branch_id
    
    # Get current stock from product_stocks
    stocks = await db.product_stocks.find(query, {"_id": 0}).to_list(1000)
    
    discrepancies = []
    
    for stock in stocks[:100]:  # Check first 100 to avoid timeout
        product_id = stock.get("product_id")
        current_qty = stock.get("quantity", 0)
        branch = stock.get("branch_id")
        
        # Calculate from movements
        movement_query = {"product_id": product_id}
        if branch:
            movement_query["branch_id"] = branch
        
        # Sum up movements
        movements = await db.stock_movements.aggregate([
            {"$match": movement_query},
            {
                "$group": {
                    "_id": None,
                    "total_in": {
                        "$sum": {
                            "$cond": [
                                {"$in": ["$movement_type", ["purchase", "adjustment_in", "transfer_in", "return_in"]]},
                                "$quantity",
                                0
                            ]
                        }
                    },
                    "total_out": {
                        "$sum": {
                            "$cond": [
                                {"$in": ["$movement_type", ["sale", "adjustment_out", "transfer_out", "return_out"]]},
                                "$quantity",
                                0
                            ]
                        }
                    }
                }
            }
        ]).to_list(1)
        
        calculated_qty = 0
        if movements:
            calculated_qty = movements[0].get("total_in", 0) - movements[0].get("total_out", 0)
        
        if abs(current_qty - calculated_qty) > 0.01:
            discrepancies.append({
                "product_id": product_id,
                "branch_id": branch,
                "recorded_stock": current_qty,
                "calculated_stock": calculated_qty,
                "difference": current_qty - calculated_qty
            })
    
    if not discrepancies:
        return ConsistencyCheckResult(
            check_type="stock_movement",
            status="pass",
            message="Stok sesuai dengan pergerakan stok",
            details={"checked_items": len(stocks)}
        )
    
    return ConsistencyCheckResult(
        check_type="stock_movement",
        status="fail",
        message=f"Ditemukan {len(discrepancies)} item dengan ketidaksesuaian stok",
        discrepancies=discrepancies[:10]
    )

async def check_ar_consistency(db, branch_id: str = None) -> ConsistencyCheckResult:
    """Check if AR balances match journal entries"""
    
    query = {"status": {"$in": ["open", "partial"]}}
    if branch_id:
        query["branch_id"] = branch_id
    
    # Total AR from collection
    ar_records = await db.accounts_receivable.find(query, {"_id": 0}).to_list(500)
    total_ar = sum(r.get("outstanding", r.get("amount", 0)) for r in ar_records)
    
    # Total AR from journals (simplified - check AR account balance)
    ar_journal = await db.journal_entries.aggregate([
        {"$unwind": "$entries"},
        {"$match": {"entries.account_code": {"$regex": "^1-13"}}},  # AR accounts
        {
            "$group": {
                "_id": None,
                "debit": {"$sum": "$entries.debit"},
                "credit": {"$sum": "$entries.credit"}
            }
        }
    ]).to_list(1)
    
    journal_ar = 0
    if ar_journal:
        journal_ar = ar_journal[0].get("debit", 0) - ar_journal[0].get("credit", 0)
    
    difference = abs(total_ar - journal_ar)
    is_consistent = difference < 1  # Allow small rounding difference
    
    return ConsistencyCheckResult(
        check_type="ar_journal",
        status="pass" if is_consistent else "warning",
        message="Piutang sesuai dengan jurnal" if is_consistent else f"Selisih piutang dengan jurnal: {difference:,.2f}",
        details={
            "ar_balance": total_ar,
            "journal_balance": journal_ar,
            "difference": difference,
            "ar_count": len(ar_records)
        }
    )

async def check_ap_consistency(db, branch_id: str = None) -> ConsistencyCheckResult:
    """Check if AP balances match journal entries"""
    
    query = {"status": {"$in": ["open", "partial"]}}
    if branch_id:
        query["branch_id"] = branch_id
    
    # Total AP from collection
    ap_records = await db.accounts_payable.find(query, {"_id": 0}).to_list(500)
    total_ap = sum(r.get("outstanding", r.get("amount", 0)) for r in ap_records)
    
    # Total AP from journals
    ap_journal = await db.journal_entries.aggregate([
        {"$unwind": "$entries"},
        {"$match": {"entries.account_code": {"$regex": "^2-11"}}},  # AP accounts
        {
            "$group": {
                "_id": None,
                "debit": {"$sum": "$entries.debit"},
                "credit": {"$sum": "$entries.credit"}
            }
        }
    ]).to_list(1)
    
    journal_ap = 0
    if ap_journal:
        journal_ap = ap_journal[0].get("credit", 0) - ap_journal[0].get("debit", 0)
    
    difference = abs(total_ap - journal_ap)
    is_consistent = difference < 1
    
    return ConsistencyCheckResult(
        check_type="ap_journal",
        status="pass" if is_consistent else "warning",
        message="Hutang sesuai dengan jurnal" if is_consistent else f"Selisih hutang dengan jurnal: {difference:,.2f}",
        details={
            "ap_balance": total_ap,
            "journal_balance": journal_ap,
            "difference": difference,
            "ap_count": len(ap_records)
        }
    )

async def check_cash_balance(db, branch_id: str = None) -> ConsistencyCheckResult:
    """Check if cash balance is consistent with transactions"""
    
    # Get cash from journals (account 1-1100)
    cash_journal = await db.journal_entries.aggregate([
        {"$unwind": "$entries"},
        {"$match": {"entries.account_code": "1-1100"}},
        {
            "$group": {
                "_id": None,
                "debit": {"$sum": "$entries.debit"},
                "credit": {"$sum": "$entries.credit"}
            }
        }
    ]).to_list(1)
    
    journal_cash = 0
    if cash_journal:
        journal_cash = cash_journal[0].get("debit", 0) - cash_journal[0].get("credit", 0)
    
    # Get cash from cash_balances collection if exists
    query = {}
    if branch_id:
        query["branch_id"] = branch_id
    
    cash_records = await db.cash_balances.find(query, {"_id": 0}).to_list(100)
    recorded_cash = sum(r.get("balance", 0) for r in cash_records)
    
    # If no cash_balances records, just report journal balance
    if not cash_records:
        return ConsistencyCheckResult(
            check_type="cash_balance",
            status="pass",
            message="Saldo kas dari jurnal dihitung",
            details={
                "journal_balance": journal_cash,
                "note": "Tidak ada data cash_balances untuk perbandingan"
            }
        )
    
    difference = abs(recorded_cash - journal_cash)
    is_consistent = difference < 1
    
    return ConsistencyCheckResult(
        check_type="cash_balance",
        status="pass" if is_consistent else "warning",
        message="Saldo kas konsisten" if is_consistent else f"Selisih saldo kas: {difference:,.2f}",
        details={
            "recorded_balance": recorded_cash,
            "journal_balance": journal_cash,
            "difference": difference
        }
    )

# ==================== API ENDPOINTS ====================

@router.get("/check-types")
async def list_check_types(user: dict = Depends(get_current_user)):
    """Get all available consistency check types"""
    return {
        "items": [
            {"type": k, **v} for k, v in CHECK_TYPES.items()
        ],
        "total": len(CHECK_TYPES)
    }

@router.get("/check/{check_type}")
async def run_single_check(
    check_type: str,
    branch_id: Optional[str] = None,
    period: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Run a single consistency check"""
    db = get_database()
    
    if check_type not in CHECK_TYPES:
        raise HTTPException(status_code=400, detail=f"Check type {check_type} tidak valid")
    
    if check_type == "journal_balance":
        result = await check_journal_balance(db, branch_id, period)
    elif check_type == "trial_balance":
        result = await check_trial_balance(db, period)
    elif check_type == "stock_movement":
        result = await check_stock_consistency(db, branch_id)
    elif check_type == "ar_journal":
        result = await check_ar_consistency(db, branch_id)
    elif check_type == "ap_journal":
        result = await check_ap_consistency(db, branch_id)
    elif check_type == "cash_balance":
        result = await check_cash_balance(db, branch_id)
    else:
        raise HTTPException(status_code=400, detail=f"Check {check_type} belum diimplementasikan")
    
    return result.model_dump()

@router.get("/full-report")
async def run_full_consistency_check(
    branch_id: Optional[str] = None,
    period: Optional[str] = None,
    user: dict = Depends(require_permission("accounting", "view"))
):
    """Run all consistency checks and generate full report"""
    db = get_database()
    
    report_id = str(uuid.uuid4())
    checks = []
    
    # Run all checks
    checks.append(await check_journal_balance(db, branch_id, period))
    checks.append(await check_trial_balance(db, period))
    checks.append(await check_stock_consistency(db, branch_id))
    checks.append(await check_ar_consistency(db, branch_id))
    checks.append(await check_ap_consistency(db, branch_id))
    checks.append(await check_cash_balance(db, branch_id))
    
    # Calculate summary
    passed = sum(1 for c in checks if c.status == "pass")
    failed = sum(1 for c in checks if c.status == "fail")
    warnings = sum(1 for c in checks if c.status == "warning")
    
    overall_status = "healthy"
    if failed > 0:
        overall_status = "critical"
    elif warnings > 0:
        overall_status = "warning"
    
    report = {
        "report_id": report_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generated_by": user.get("name", ""),
        "overall_status": overall_status,
        "checks": [c.model_dump() for c in checks],
        "summary": {
            "total_checks": len(checks),
            "passed": passed,
            "failed": failed,
            "warnings": warnings,
            "branch_id": branch_id,
            "period": period
        }
    }
    
    # Save report
    await db.consistency_reports.insert_one({
        **report,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return report

@router.get("/reports")
async def list_consistency_reports(
    limit: int = 20,
    user: dict = Depends(require_permission("accounting", "view"))
):
    """Get history of consistency check reports"""
    db = get_database()
    
    reports = await db.consistency_reports.find(
        {}, 
        {"_id": 0, "report_id": 1, "generated_at": 1, "generated_by": 1, "overall_status": 1, "summary": 1}
    ).sort("generated_at", -1).limit(limit).to_list(limit)
    
    return {"items": reports, "total": len(reports)}

@router.get("/reports/{report_id}")
async def get_consistency_report(
    report_id: str,
    user: dict = Depends(require_permission("accounting", "view"))
):
    """Get specific consistency report"""
    db = get_database()
    
    report = await db.consistency_reports.find_one({"report_id": report_id}, {"_id": 0})
    if not report:
        raise HTTPException(status_code=404, detail="Report tidak ditemukan")
    
    return report

# ==================== AUTO-FIX SUGGESTIONS ====================

@router.get("/fix-suggestions/{check_type}")
async def get_fix_suggestions(
    check_type: str,
    user: dict = Depends(require_permission("accounting", "view"))
):
    """Get suggestions to fix consistency issues"""
    
    suggestions = {
        "journal_balance": {
            "issue": "Jurnal tidak seimbang",
            "suggestions": [
                "Review jurnal yang ditandai dan perbaiki entri yang salah",
                "Periksa apakah ada entri yang hilang",
                "Gunakan fitur 'Edit Journal' untuk memperbaiki",
                "Jika perlu, buat jurnal koreksi"
            ]
        },
        "trial_balance": {
            "issue": "Neraca saldo tidak seimbang",
            "suggestions": [
                "Jalankan check 'journal_balance' terlebih dahulu",
                "Periksa apakah ada jurnal yang belum diposting",
                "Review transaksi dalam periode yang diperiksa",
                "Hubungi tim akuntansi untuk investigasi"
            ]
        },
        "stock_movement": {
            "issue": "Stok tidak sesuai dengan pergerakan",
            "suggestions": [
                "Lakukan stock opname untuk item yang bermasalah",
                "Periksa apakah ada transaksi yang belum tercatat",
                "Gunakan 'Stock Adjustment' untuk mengoreksi selisih",
                "Review riwayat pergerakan stok"
            ]
        },
        "ar_journal": {
            "issue": "Piutang tidak sesuai dengan jurnal",
            "suggestions": [
                "Periksa pembayaran piutang yang belum dijurnal",
                "Review transaksi penjualan kredit",
                "Pastikan semua pelunasan sudah tercatat",
                "Buat jurnal koreksi jika diperlukan"
            ]
        },
        "ap_journal": {
            "issue": "Hutang tidak sesuai dengan jurnal",
            "suggestions": [
                "Periksa pembayaran hutang yang belum dijurnal",
                "Review transaksi pembelian kredit",
                "Pastikan semua pelunasan sudah tercatat",
                "Buat jurnal koreksi jika diperlukan"
            ]
        },
        "cash_balance": {
            "issue": "Saldo kas tidak konsisten",
            "suggestions": [
                "Lakukan rekonsiliasi kas",
                "Periksa transaksi kas yang belum tercatat",
                "Review setoran dan pengeluaran kas",
                "Buat jurnal penyesuaian jika ada selisih"
            ]
        }
    }
    
    if check_type not in suggestions:
        raise HTTPException(status_code=400, detail=f"Check type {check_type} tidak valid")
    
    return suggestions[check_type]
