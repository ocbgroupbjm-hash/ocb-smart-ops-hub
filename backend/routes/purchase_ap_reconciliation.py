"""
OCB TITAN ERP - PURCHASE ↔ AP RECONCILIATION ENGINE
====================================================
P0: Sinkronisasi penuh Purchase ↔ AP ↔ Accounting

RULES:
1. Hutang = AP Invoice - Payment Allocation (NOT manual field)
2. Tidak boleh hitung hutang di UI pembelian
3. UI pembelian → ambil dari AP module
4. Semua PO received/posted HARUS punya AP
"""

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
from typing import Optional, Dict, List, Any
from database import get_db
from utils.auth import get_current_user
import uuid

router = APIRouter(prefix="/api/purchase-ap-reconciliation", tags=["Purchase AP Reconciliation"])


@router.get("/reconcile")
async def reconcile_purchase_ap(
    supplier_id: str = None,
    user: dict = Depends(get_current_user)
):
    """
    Full reconciliation between Purchase Orders and Accounts Payable
    
    Returns:
    - Total Purchase value
    - Total AP value
    - GAP analysis
    - List of POs without AP
    - List of AP without PO
    """
    db = get_db()
    
    # Build query
    po_query = {"status": {"$in": ["received", "posted", "completed"]}}
    ap_query = {"source_type": "purchase", "status": {"$ne": "cancelled"}}
    
    if supplier_id:
        po_query["supplier_id"] = supplier_id
        ap_query["supplier_id"] = supplier_id
    
    # Get all completed POs
    pos = await db["purchase_orders"].find(po_query, {"_id": 0}).to_list(1000)
    
    # Get all APs from purchase
    aps = await db["accounts_payable"].find(ap_query, {"_id": 0}).to_list(1000)
    
    # Build lookup maps
    po_map = {po.get("id"): po for po in pos}
    ap_by_po = {}
    ap_by_po_number = {}
    
    for ap in aps:
        source_id = ap.get("source_id")
        source_no = ap.get("source_no")
        if source_id:
            ap_by_po[source_id] = ap
        if source_no:
            ap_by_po_number[source_no] = ap
    
    # Analysis
    pos_without_ap = []
    pos_with_ap = []
    mismatched_amounts = []
    
    total_po_value = 0
    total_ap_original = 0
    total_ap_outstanding = 0
    total_ap_paid = 0
    
    for po in pos:
        po_id = po.get("id")
        po_number = po.get("po_number")
        po_total = po.get("total", 0)
        total_po_value += po_total
        
        # Find matching AP
        ap = ap_by_po.get(po_id) or ap_by_po_number.get(po_number)
        
        if not ap:
            pos_without_ap.append({
                "po_id": po_id,
                "po_number": po_number,
                "supplier_name": po.get("supplier_name"),
                "total": po_total,
                "status": po.get("status"),
                "issue": "NO AP CREATED"
            })
        else:
            ap_original = ap.get("original_amount", ap.get("amount", 0))
            ap_outstanding = ap.get("outstanding_amount", ap_original)
            ap_paid = ap.get("paid_amount", 0)
            
            total_ap_original += ap_original
            total_ap_outstanding += ap_outstanding
            total_ap_paid += ap_paid
            
            # Check amount match
            diff = abs(po_total - ap_original)
            if diff > 1:  # More than Rp 1 difference
                mismatched_amounts.append({
                    "po_number": po_number,
                    "po_total": po_total,
                    "ap_no": ap.get("ap_no"),
                    "ap_original": ap_original,
                    "difference": po_total - ap_original
                })
            
            pos_with_ap.append({
                "po_number": po_number,
                "po_total": po_total,
                "ap_no": ap.get("ap_no"),
                "ap_original": ap_original,
                "ap_outstanding": ap_outstanding,
                "ap_paid": ap_paid,
                "ap_status": ap.get("status")
            })
    
    # Find orphan APs (APs without PO)
    orphan_aps = []
    for ap in aps:
        source_id = ap.get("source_id")
        source_no = ap.get("source_no")
        
        if source_id and source_id in po_map:
            continue
        if source_no:
            po_by_number = next((p for p in pos if p.get("po_number") == source_no), None)
            if po_by_number:
                continue
        
        orphan_aps.append({
            "ap_no": ap.get("ap_no"),
            "source_id": source_id,
            "source_no": source_no,
            "original_amount": ap.get("original_amount", 0),
            "issue": "AP without matching PO"
        })
    
    # Calculate GAP
    gap = total_po_value - total_ap_original
    
    return {
        "reconciliation_date": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_pos": len(pos),
            "total_aps": len(aps),
            "total_po_value": total_po_value,
            "total_ap_original": total_ap_original,
            "total_ap_outstanding": total_ap_outstanding,
            "total_ap_paid": total_ap_paid,
            "gap": gap,
            "status": "RECONCILED" if abs(gap) < 1 and len(pos_without_ap) == 0 else "GAP_DETECTED"
        },
        "issues": {
            "pos_without_ap": pos_without_ap,
            "pos_without_ap_count": len(pos_without_ap),
            "mismatched_amounts": mismatched_amounts,
            "mismatched_count": len(mismatched_amounts),
            "orphan_aps": orphan_aps,
            "orphan_aps_count": len(orphan_aps)
        },
        "detail": {
            "matched_pos": pos_with_ap[:20]  # Limit for response size
        }
    }


@router.post("/fix-missing-ap")
async def fix_missing_ap(
    po_id: str = None,
    fix_all: bool = False,
    user: dict = Depends(get_current_user)
):
    """
    Create missing AP entries for POs that don't have them
    """
    db = get_db()
    now = datetime.now(timezone.utc).isoformat()
    
    # Find POs without AP
    query = {"status": {"$in": ["received", "posted", "completed"]}}
    if po_id:
        query["id"] = po_id
    
    pos = await db["purchase_orders"].find(query, {"_id": 0}).to_list(1000)
    
    fixed = []
    skipped = []
    
    for po in pos:
        po_id_val = po.get("id")
        po_number = po.get("po_number")
        
        # Check if AP exists
        existing_ap = await db["accounts_payable"].find_one({
            "$or": [
                {"source_id": po_id_val},
                {"source_no": po_number}
            ]
        })
        
        if existing_ap:
            if not fix_all:
                skipped.append({
                    "po_number": po_number,
                    "reason": "AP already exists",
                    "ap_no": existing_ap.get("ap_no")
                })
            continue
        
        # Create AP
        from datetime import timedelta
        from routes.ap_system import generate_ap_number
        
        branch_id = po.get("branch_id")
        branch = await db["branches"].find_one({"id": branch_id}, {"_id": 0})
        branch_code = branch.get("code", "HQ") if branch else "HQ"
        
        ap_no = await generate_ap_number(branch_code)
        credit_due_days = po.get("credit_due_days", 30)
        due_date = datetime.now(timezone.utc) + timedelta(days=credit_due_days)
        
        ap_entry = {
            "id": str(uuid.uuid4()),
            "ap_no": ap_no,
            "ap_date": po.get("received_date", po.get("order_date", now))[:10],
            "due_date": due_date.strftime("%Y-%m-%d"),
            "supplier_id": po.get("supplier_id"),
            "supplier_name": po.get("supplier_name", ""),
            "supplier_invoice_no": "",
            "branch_id": branch_id,
            "source_type": "purchase",
            "source_id": po_id_val,
            "source_no": po_number,
            "currency": "IDR",
            "original_amount": po.get("total", 0),
            "paid_amount": 0,
            "outstanding_amount": po.get("total", 0),
            "status": "open",
            "payment_term_days": credit_due_days,
            "notes": f"AP dibuat otomatis untuk PO {po_number}",
            "created_by": user.get("user_id", ""),
            "created_by_name": user.get("name", "System"),
            "created_at": now,
            "updated_at": now,
            "auto_created": True
        }
        
        await db["accounts_payable"].insert_one(ap_entry)
        
        fixed.append({
            "po_number": po_number,
            "ap_no": ap_no,
            "amount": po.get("total", 0)
        })
    
    return {
        "success": True,
        "message": f"Fixed {len(fixed)} POs, skipped {len(skipped)}",
        "fixed": fixed,
        "skipped": skipped[:10]  # Limit response
    }


@router.get("/supplier-hutang/{supplier_id}")
async def get_supplier_hutang(
    supplier_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Get supplier hutang (payable) from AP module
    
    This is the CORRECT way to get hutang - from AP, NOT from manual field
    """
    db = get_db()
    
    # Get supplier info
    supplier = await db["suppliers"].find_one({"id": supplier_id}, {"_id": 0})
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier tidak ditemukan")
    
    # Get all open AP for this supplier
    aps = await db["accounts_payable"].find({
        "supplier_id": supplier_id,
        "status": {"$in": ["open", "partial", "overdue"]}
    }, {"_id": 0}).sort("due_date", 1).to_list(100)
    
    total_hutang = sum(ap.get("outstanding_amount", 0) for ap in aps)
    total_overdue = sum(
        ap.get("outstanding_amount", 0) 
        for ap in aps 
        if ap.get("due_date", "9999-12-31") < datetime.now(timezone.utc).strftime("%Y-%m-%d")
    )
    
    # Get payment history
    payments = await db["ap_payments"].find({
        "supplier_id": supplier_id
    }, {"_id": 0}).sort("payment_date", -1).limit(10).to_list(10)
    
    total_paid_this_month = sum(
        p.get("amount", 0) 
        for p in payments 
        if p.get("payment_date", "")[:7] == datetime.now(timezone.utc).strftime("%Y-%m")
    )
    
    return {
        "supplier_id": supplier_id,
        "supplier_name": supplier.get("name"),
        "supplier_code": supplier.get("code"),
        "total_hutang": total_hutang,
        "total_overdue": total_overdue,
        "open_invoices": len(aps),
        "total_paid_this_month": total_paid_this_month,
        "invoices": [{
            "ap_no": ap.get("ap_no"),
            "ap_date": ap.get("ap_date"),
            "due_date": ap.get("due_date"),
            "original_amount": ap.get("original_amount"),
            "outstanding_amount": ap.get("outstanding_amount"),
            "status": ap.get("status"),
            "source_no": ap.get("source_no"),
            "is_overdue": ap.get("due_date", "9999-12-31") < datetime.now(timezone.utc).strftime("%Y-%m-%d")
        } for ap in aps],
        "recent_payments": payments
    }


@router.get("/total-hutang")
async def get_total_hutang(
    branch_id: str = None,
    user: dict = Depends(get_current_user)
):
    """
    Get total hutang (payable) summary
    
    SOURCE: AP module (accounts_payable collection)
    """
    db = get_db()
    
    query = {"status": {"$in": ["open", "partial", "overdue"]}}
    if branch_id:
        query["branch_id"] = branch_id
    
    # Aggregate by supplier
    pipeline = [
        {"$match": query},
        {"$group": {
            "_id": {
                "supplier_id": "$supplier_id",
                "supplier_name": "$supplier_name"
            },
            "total_outstanding": {"$sum": "$outstanding_amount"},
            "invoice_count": {"$sum": 1},
            "oldest_due": {"$min": "$due_date"}
        }},
        {"$sort": {"total_outstanding": -1}}
    ]
    
    by_supplier = await db["accounts_payable"].aggregate(pipeline).to_list(100)
    
    # Get overdue total
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    overdue_query = {**query, "due_date": {"$lt": today}}
    
    overdue_pipeline = [
        {"$match": overdue_query},
        {"$group": {
            "_id": None,
            "total": {"$sum": "$outstanding_amount"},
            "count": {"$sum": 1}
        }}
    ]
    
    overdue_result = await db["accounts_payable"].aggregate(overdue_pipeline).to_list(1)
    
    total_hutang = sum(s["total_outstanding"] for s in by_supplier)
    total_overdue = overdue_result[0]["total"] if overdue_result else 0
    overdue_count = overdue_result[0]["count"] if overdue_result else 0
    
    return {
        "total_hutang": total_hutang,
        "total_overdue": total_overdue,
        "overdue_count": overdue_count,
        "supplier_count": len(by_supplier),
        "by_supplier": [{
            "supplier_id": s["_id"].get("supplier_id") if s.get("_id") else None,
            "supplier_name": s["_id"].get("supplier_name", "Unknown") if s.get("_id") else "Unknown",
            "total_outstanding": s.get("total_outstanding", 0),
            "invoice_count": s.get("invoice_count", 0),
            "oldest_due": s.get("oldest_due")
        } for s in by_supplier[:20]],
        "source": "accounts_payable",
        "note": "Hutang dihitung dari AP module, BUKAN dari field manual"
    }
