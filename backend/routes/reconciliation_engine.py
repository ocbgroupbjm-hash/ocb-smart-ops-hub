"""
OCB TITAN ERP - DATA RECONCILIATION ENGINE
Tool untuk memperbaiki data inconsistency sebelum Phase 3

Features:
1. Stock Reconciliation - Sync product_stocks dengan stock_movements
2. AR Reconciliation - Sync accounts_receivable dengan journal_entries
3. AP Reconciliation - Sync accounts_payable dengan journal_entries
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from database import get_db as get_database
from routes.auth import get_current_user
from routes.rbac_middleware import require_permission
import uuid

router = APIRouter(prefix="/api/reconciliation", tags=["Data Reconciliation"])

# ==================== PYDANTIC MODELS ====================

class ReconciliationResult(BaseModel):
    type: str
    status: str
    items_checked: int
    discrepancies_found: int
    items_fixed: int
    details: List[Dict[str, Any]] = []

class ReconciliationRequest(BaseModel):
    auto_fix: bool = False
    branch_id: Optional[str] = None

# ==================== STOCK RECONCILIATION ====================

@router.get("/stock/check")
async def check_stock_reconciliation(
    branch_id: Optional[str] = None,
    user: dict = Depends(require_permission("inventory", "view"))
):
    """Check stock discrepancies between product_stocks and stock_movements"""
    db = get_database()
    
    query = {}
    if branch_id:
        query["branch_id"] = branch_id
    
    product_stocks = await db.product_stocks.find(query, {"_id": 0}).to_list(1000)
    
    discrepancies = []
    total_checked = 0
    
    for ps in product_stocks:
        product_id = ps.get("product_id")
        ps_branch_id = ps.get("branch_id")
        recorded_qty = ps.get("quantity", 0)
        
        # Calculate from stock_movements
        movement_query = {"product_id": product_id}
        if ps_branch_id:
            movement_query["branch_id"] = ps_branch_id
        
        movements = await db.stock_movements.aggregate([
            {"$match": movement_query},
            {
                "$group": {
                    "_id": None,
                    "total_in": {
                        "$sum": {
                            "$cond": [
                                {"$in": ["$movement_type", ["purchase", "adjustment_in", "transfer_in", "return_in", "initial", "receive"]]},
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
        
        total_checked += 1
        
        if abs(recorded_qty - calculated_qty) > 0.01:
            # Get product name
            product = await db.products.find_one({"id": product_id}, {"_id": 0, "name": 1, "sku": 1})
            
            discrepancies.append({
                "product_id": product_id,
                "product_name": product.get("name", "Unknown") if product else "Unknown",
                "product_sku": product.get("sku", "") if product else "",
                "branch_id": ps_branch_id,
                "recorded_stock": recorded_qty,
                "calculated_stock": calculated_qty,
                "difference": recorded_qty - calculated_qty
            })
    
    return {
        "status": "pass" if not discrepancies else "fail",
        "items_checked": total_checked,
        "discrepancies_found": len(discrepancies),
        "discrepancies": discrepancies,
        "message": "Stok konsisten dengan stock_movements" if not discrepancies else f"Ditemukan {len(discrepancies)} discrepancy"
    }

@router.post("/stock/fix")
async def fix_stock_reconciliation(
    data: ReconciliationRequest,
    user: dict = Depends(require_permission("inventory", "edit"))
):
    """
    Fix stock discrepancies by:
    1. Creating adjustment stock_movements
    2. Updating product_stocks to match
    """
    db = get_database()
    
    # Get discrepancies first
    check_result = await check_stock_reconciliation(data.branch_id, user)
    discrepancies = check_result.get("discrepancies", [])
    
    if not discrepancies:
        return {"status": "pass", "message": "Tidak ada discrepancy yang perlu diperbaiki", "fixed": 0}
    
    fixed_count = 0
    fix_details = []
    user_id = user.get("user_id") or user.get("id")
    user_name = user.get("name", "System")
    
    for disc in discrepancies:
        product_id = disc["product_id"]
        branch_id = disc["branch_id"]
        difference = disc["difference"]
        calculated = disc["calculated_stock"]
        
        # Create adjustment movement to correct the difference
        if difference != 0:
            movement_type = "adjustment_in" if difference < 0 else "adjustment_out"
            adjustment_qty = abs(difference)
            
            # Create stock movement
            movement = {
                "id": str(uuid.uuid4()),
                "product_id": product_id,
                "branch_id": branch_id,
                "movement_type": movement_type,
                "quantity": adjustment_qty,
                "reference_type": "reconciliation",
                "reference_id": f"RECON-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "notes": f"Auto reconciliation adjustment. Difference: {difference}",
                "created_by": user_id,
                "created_by_name": user_name,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            await db.stock_movements.insert_one(movement)
            
            # Update product_stocks to match calculated value
            # After adjustment, new stock should be: calculated + adjustment = recorded
            # So we update to: calculated (which after adjustment becomes recorded)
            new_stock = calculated + (adjustment_qty if movement_type == "adjustment_in" else -adjustment_qty)
            
            await db.product_stocks.update_one(
                {"product_id": product_id, "branch_id": branch_id},
                {"$set": {
                    "quantity": new_stock,
                    "last_reconciled_at": datetime.now(timezone.utc).isoformat(),
                    "reconciled_by": user_id
                }}
            )
            
            fixed_count += 1
            fix_details.append({
                "product_id": product_id,
                "product_name": disc["product_name"],
                "branch_id": branch_id,
                "old_recorded": disc["recorded_stock"],
                "calculated": calculated,
                "adjustment_type": movement_type,
                "adjustment_qty": adjustment_qty,
                "new_stock": new_stock
            })
    
    # Log reconciliation
    await db.audit_logs.insert_one({
        "id": str(uuid.uuid4()),
        "action": "stock_reconciliation",
        "module": "inventory",
        "description": f"Stock reconciliation: {fixed_count} items adjusted",
        "details": fix_details,
        "user_id": user_id,
        "user_name": user_name,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    return {
        "status": "success",
        "message": f"Berhasil memperbaiki {fixed_count} discrepancy",
        "fixed": fixed_count,
        "details": fix_details
    }

# ==================== AR RECONCILIATION ====================

@router.get("/ar/check")
async def check_ar_reconciliation(
    branch_id: Optional[str] = None,
    user: dict = Depends(require_permission("ar", "view"))
):
    """Check AR discrepancies between accounts_receivable and journal_entries"""
    db = get_database()
    
    query = {"status": {"$in": ["open", "partial"]}}
    if branch_id:
        query["branch_id"] = branch_id
    
    # Total AR from collection
    ar_records = await db.accounts_receivable.find(query, {"_id": 0}).to_list(500)
    total_ar = sum(r.get("outstanding", r.get("amount", 0)) for r in ar_records)
    
    # Total AR from journals (1-13xx accounts)
    ar_journal = await db.journal_entries.aggregate([
        {"$unwind": "$entries"},
        {"$match": {"entries.account_code": {"$regex": "^1-13"}}},
        {
            "$group": {
                "_id": None,
                "total_debit": {"$sum": "$entries.debit"},
                "total_credit": {"$sum": "$entries.credit"}
            }
        }
    ]).to_list(1)
    
    journal_ar = 0
    if ar_journal:
        journal_ar = ar_journal[0].get("total_debit", 0) - ar_journal[0].get("total_credit", 0)
    
    difference = total_ar - journal_ar
    is_balanced = abs(difference) < 1
    
    # Check individual AR records
    ar_without_journal = []
    for ar in ar_records[:20]:
        ar_no = ar.get("ar_number") or ar.get("ar_no")
        journal = await db.journal_entries.find_one({
            "$or": [
                {"reference_no": ar_no},
                {"source_id": ar.get("id")},
                {"journal_no": {"$regex": ar_no if ar_no else "XXXXX"}}
            ]
        })
        if not journal and ar.get("outstanding", ar.get("amount", 0)) > 0:
            ar_without_journal.append({
                "ar_no": ar_no,
                "customer_name": ar.get("customer_name"),
                "amount": ar.get("amount"),
                "outstanding": ar.get("outstanding", ar.get("amount"))
            })
    
    return {
        "status": "pass" if is_balanced else "fail",
        "ar_from_collection": total_ar,
        "ar_from_journals": journal_ar,
        "difference": difference,
        "ar_records_count": len(ar_records),
        "ar_without_journal": ar_without_journal,
        "message": "AR seimbang dengan jurnal" if is_balanced else f"Selisih AR: Rp {difference:,.2f}"
    }

@router.post("/ar/fix")
async def fix_ar_reconciliation(
    data: ReconciliationRequest,
    user: dict = Depends(require_permission("ar", "edit"))
):
    """
    Fix AR discrepancies by creating missing journal entries
    """
    db = get_database()
    
    check_result = await check_ar_reconciliation(data.branch_id, user)
    ar_without_journal = check_result.get("ar_without_journal", [])
    
    if not ar_without_journal and check_result["status"] == "pass":
        return {"status": "pass", "message": "AR sudah seimbang", "fixed": 0}
    
    fixed_count = 0
    fix_details = []
    user_id = user.get("user_id") or user.get("id")
    user_name = user.get("name", "System")
    
    # Create missing journals for AR records
    for ar in ar_without_journal:
        ar_no = ar.get("ar_no")
        amount = ar.get("outstanding", ar.get("amount", 0))
        
        if amount <= 0:
            continue
        
        # Get full AR record
        ar_record = await db.accounts_receivable.find_one(
            {"$or": [{"ar_number": ar_no}, {"ar_no": ar_no}]},
            {"_id": 0}
        )
        
        if not ar_record:
            continue
        
        # Create journal entry
        journal_id = str(uuid.uuid4())
        journal_no = f"JV-AR-RECON-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"
        
        journal = {
            "id": journal_id,
            "journal_no": journal_no,
            "journal_date": datetime.now(timezone.utc).isoformat(),
            "source_type": "ar_reconciliation",
            "source_id": ar_record.get("id"),
            "reference_no": ar_no,
            "description": f"Jurnal koreksi AR {ar_no} - {ar.get('customer_name')}",
            "entries": [
                {
                    "account_code": "1-1300",
                    "account_name": "Piutang Usaha",
                    "debit": amount,
                    "credit": 0,
                    "description": f"Piutang {ar.get('customer_name')}"
                },
                {
                    "account_code": "4-1000",
                    "account_name": "Pendapatan Penjualan",
                    "debit": 0,
                    "credit": amount,
                    "description": f"Koreksi pendapatan {ar_no}"
                }
            ],
            "total_debit": amount,
            "total_credit": amount,
            "is_balanced": True,
            "status": "posted",
            "branch_id": ar_record.get("branch_id"),
            "created_by": user_id,
            "created_by_name": user_name,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "is_reconciliation": True
        }
        
        await db.journal_entries.insert_one(journal)
        
        fixed_count += 1
        fix_details.append({
            "ar_no": ar_no,
            "customer_name": ar.get("customer_name"),
            "amount": amount,
            "journal_no": journal_no
        })
    
    if fixed_count > 0:
        await db.audit_logs.insert_one({
            "id": str(uuid.uuid4()),
            "action": "ar_reconciliation",
            "module": "ar",
            "description": f"AR reconciliation: {fixed_count} journals created",
            "details": fix_details,
            "user_id": user_id,
            "user_name": user_name,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    
    return {
        "status": "success",
        "message": f"Berhasil membuat {fixed_count} jurnal koreksi AR",
        "fixed": fixed_count,
        "details": fix_details
    }

# ==================== AP RECONCILIATION ====================

@router.get("/ap/check")
async def check_ap_reconciliation(
    branch_id: Optional[str] = None,
    user: dict = Depends(require_permission("ap", "view"))
):
    """Check AP discrepancies between accounts_payable and journal_entries"""
    db = get_database()
    
    query = {"status": {"$in": ["open", "partial"]}}
    if branch_id:
        query["branch_id"] = branch_id
    
    # Total AP from collection
    ap_records = await db.accounts_payable.find(query, {"_id": 0}).to_list(500)
    total_ap = sum(r.get("outstanding", r.get("amount", 0)) for r in ap_records)
    
    # Total AP from journals (2-11xx accounts)
    ap_journal = await db.journal_entries.aggregate([
        {"$unwind": "$entries"},
        {"$match": {"entries.account_code": {"$regex": "^2-11"}}},
        {
            "$group": {
                "_id": None,
                "total_debit": {"$sum": "$entries.debit"},
                "total_credit": {"$sum": "$entries.credit"}
            }
        }
    ]).to_list(1)
    
    journal_ap = 0
    if ap_journal:
        journal_ap = ap_journal[0].get("total_credit", 0) - ap_journal[0].get("total_debit", 0)
    
    difference = total_ap - journal_ap
    is_balanced = abs(difference) < 1
    
    return {
        "status": "pass" if is_balanced else "fail",
        "ap_from_collection": total_ap,
        "ap_from_journals": journal_ap,
        "difference": difference,
        "ap_records_count": len(ap_records),
        "message": "AP seimbang dengan jurnal" if is_balanced else f"Selisih AP: Rp {difference:,.2f}"
    }

# ==================== FULL RECONCILIATION ====================

@router.get("/full-check")
async def run_full_reconciliation_check(
    branch_id: Optional[str] = None,
    user: dict = Depends(require_permission("accounting", "view"))
):
    """Run all reconciliation checks"""
    stock_check = await check_stock_reconciliation(branch_id, user)
    ar_check = await check_ar_reconciliation(branch_id, user)
    ap_check = await check_ap_reconciliation(branch_id, user)
    
    all_pass = (
        stock_check["status"] == "pass" and 
        ar_check["status"] == "pass" and 
        ap_check["status"] == "pass"
    )
    
    return {
        "overall_status": "pass" if all_pass else "fail",
        "checks": {
            "stock": stock_check,
            "ar": ar_check,
            "ap": ap_check
        },
        "ready_for_phase_3": all_pass,
        "message": "Semua validasi berhasil. Siap untuk Phase 3." if all_pass else "Ada discrepancy yang perlu diperbaiki sebelum Phase 3."
    }

@router.post("/fix-all")
async def fix_all_reconciliation(
    data: ReconciliationRequest,
    user: dict = Depends(require_permission("accounting", "edit"))
):
    """Fix all reconciliation issues"""
    results = {
        "stock": await fix_stock_reconciliation(data, user),
        "ar": await fix_ar_reconciliation(data, user)
    }
    
    total_fixed = sum(r.get("fixed", 0) for r in results.values())
    
    return {
        "status": "success",
        "total_fixed": total_fixed,
        "results": results,
        "message": f"Berhasil memperbaiki {total_fixed} discrepancy"
    }
