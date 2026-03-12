"""
OCB TITAN ERP - PHASE 3 OPERATIONAL CONTROL SYSTEM
Module 7: DEPOSIT & CASH CONTROL ENHANCEMENT
Following OCB TITAN AI MASTER LAW - NON-DESTRUCTIVE Development

Fitur:
1. Monitoring setoran kasir
2. Bandingkan sales vs deposit
3. Deteksi selisih kas (shortage/overage)
4. Shift management per kasir
5. Audit trail lengkap

Data Flow:
1. Kasir mulai shift → Initial cash float dicatat
2. Transaksi berjalan → Sales dicatat
3. Kasir tutup shift → Actual cash dihitung
4. System compare: Expected vs Actual
5. Selisih dicatat dan di-flag untuk review
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
from database import get_db as get_database
from routes.auth import get_current_user
from routes.rbac_middleware import require_permission
import uuid

router = APIRouter(prefix="/api/cash-control", tags=["Deposit & Cash Control"])

# ==================== CONSTANTS ====================

SHIFT_STATUS = {
    "open": {"name": "Open", "color": "green"},
    "closing": {"name": "Closing", "color": "yellow"},
    "closed": {"name": "Closed", "color": "gray"},
    "reviewed": {"name": "Reviewed", "color": "blue"},
    "discrepancy": {"name": "Discrepancy", "color": "red"}
}

DISCREPANCY_TYPE = {
    "shortage": {"name": "Shortage (Kurang)", "severity": "high"},
    "overage": {"name": "Overage (Lebih)", "severity": "medium"},
    "none": {"name": "Match", "severity": "none"}
}

DEFAULT_TOLERANCE = 1000  # Rp 1.000 tolerance for rounding

# ==================== PYDANTIC MODELS ====================

class ShiftOpenRequest(BaseModel):
    branch_id: str
    initial_cash: float = Field(ge=0)
    notes: Optional[str] = ""

class ShiftCloseRequest(BaseModel):
    actual_cash: float = Field(ge=0)
    cash_denomination: Optional[Dict[str, int]] = None  # {"100000": 5, "50000": 10, ...}
    notes: Optional[str] = ""

class DepositRequest(BaseModel):
    shift_id: str
    deposit_amount: float = Field(ge=0)
    deposit_method: str = "cash"  # cash, bank_transfer
    bank_reference: Optional[str] = ""
    notes: Optional[str] = ""

class DiscrepancyResolveRequest(BaseModel):
    resolution_type: str  # explained, written_off, recovered
    resolution_notes: str
    recovery_amount: Optional[float] = 0

class CashToleranceUpdate(BaseModel):
    tolerance_amount: float = Field(ge=0)

class CashMovementRequest(BaseModel):
    shift_id: str
    amount: float = Field(gt=0)
    description: Optional[str] = ""
    reference: Optional[str] = ""

# ==================== HELPER FUNCTIONS ====================

async def get_shift_sales(db, shift_id: str) -> Dict[str, Any]:
    """Calculate total sales during a shift"""
    
    shift = await db.cashier_shifts.find_one({"id": shift_id}, {"_id": 0})
    if not shift:
        return {"cash_sales": 0, "non_cash_sales": 0, "total_sales": 0}
    
    cashier_id = shift.get("cashier_id")
    branch_id = shift.get("branch_id")
    shift_start = shift.get("start_time")
    shift_end = shift.get("end_time") or datetime.now(timezone.utc).isoformat()
    
    # Query POS transactions
    query = {
        "cashier_id": cashier_id,
        "branch_id": branch_id,
        "transaction_date": {"$gte": shift_start[:10], "$lte": shift_end[:10]},
        "created_at": {"$gte": shift_start, "$lte": shift_end},
        "status": {"$nin": ["cancelled", "void"]}
    }
    
    # Aggregate by payment method
    pipeline = [
        {"$match": query},
        {"$group": {
            "_id": "$payment_method",
            "total": {"$sum": "$grand_total"},
            "count": {"$sum": 1}
        }}
    ]
    
    results = await db.pos_transactions.aggregate(pipeline).to_list(10)
    
    cash_sales = 0
    non_cash_sales = 0
    tx_count = 0
    
    for r in results:
        if r["_id"] in ["cash", "tunai"]:
            cash_sales += r["total"]
        else:
            non_cash_sales += r["total"]
        tx_count += r["count"]
    
    # Also check sales_invoices
    invoice_results = await db.sales_invoices.aggregate(pipeline).to_list(10)
    for r in invoice_results:
        if r["_id"] in ["cash", "tunai"]:
            cash_sales += r["total"]
        else:
            non_cash_sales += r["total"]
        tx_count += r["count"]
    
    return {
        "cash_sales": cash_sales,
        "non_cash_sales": non_cash_sales,
        "total_sales": cash_sales + non_cash_sales,
        "transaction_count": tx_count
    }

async def calculate_expected_cash(db, shift_id: str) -> Dict[str, Any]:
    """Calculate expected cash at end of shift"""
    
    shift = await db.cashier_shifts.find_one({"id": shift_id}, {"_id": 0})
    if not shift:
        return {"expected_cash": 0}
    
    initial_cash = shift.get("initial_cash", 0)
    sales_data = await get_shift_sales(db, shift_id)
    cash_sales = sales_data.get("cash_sales", 0)
    
    # Get cash paid out during shift (refunds, expenses, etc.)
    cash_paid_out_query = {
        "shift_id": shift_id,
        "type": "cash_out"
    }
    cash_outs = await db.cash_movements.find(cash_paid_out_query, {"_id": 0}).to_list(100)
    total_cash_out = sum(c.get("amount", 0) for c in cash_outs)
    
    # Get cash received (other than sales)
    cash_in_query = {
        "shift_id": shift_id,
        "type": "cash_in"
    }
    cash_ins = await db.cash_movements.find(cash_in_query, {"_id": 0}).to_list(100)
    total_cash_in = sum(c.get("amount", 0) for c in cash_ins)
    
    expected_cash = initial_cash + cash_sales + total_cash_in - total_cash_out
    
    return {
        "initial_cash": initial_cash,
        "cash_sales": cash_sales,
        "cash_in": total_cash_in,
        "cash_out": total_cash_out,
        "expected_cash": expected_cash,
        "sales_data": sales_data
    }

# ==================== API ENDPOINTS ====================

@router.post("/shift/open")
async def open_shift(
    data: ShiftOpenRequest,
    user: dict = Depends(require_permission("cash_control", "create"))
):
    """Open a new cashier shift"""
    db = get_database()
    
    # Check if user already has an open shift
    existing = await db.cashier_shifts.find_one({
        "cashier_id": user.get("user_id"),
        "status": "open"
    })
    
    if existing:
        raise HTTPException(
            status_code=400, 
            detail="Anda sudah memiliki shift yang terbuka. Tutup shift sebelumnya terlebih dahulu."
        )
    
    shift = {
        "id": str(uuid.uuid4()),
        "shift_no": f"SFT-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        "branch_id": data.branch_id,
        "cashier_id": user.get("user_id"),
        "cashier_name": user.get("name"),
        "start_time": datetime.now(timezone.utc).isoformat(),
        "initial_cash": data.initial_cash,
        "status": "open",
        "notes": data.notes,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.cashier_shifts.insert_one(shift)
    shift.pop("_id", None)
    
    # Audit log
    await db.audit_logs.insert_one({
        "id": str(uuid.uuid4()),
        "action": "shift_open",
        "module": "cash_control",
        "target_id": shift["id"],
        "description": f"Shift opened with initial cash Rp {data.initial_cash:,.0f}",
        "user_id": user.get("user_id"),
        "user_name": user.get("name"),
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    return {
        "success": True,
        "shift": shift,
        "message": f"Shift {shift['shift_no']} opened"
    }

@router.get("/shift/current")
async def get_current_shift(user: dict = Depends(get_current_user)):
    """Get current open shift for the logged-in user"""
    db = get_database()
    
    shift = await db.cashier_shifts.find_one({
        "cashier_id": user.get("user_id"),
        "status": "open"
    }, {"_id": 0})
    
    if not shift:
        return {"has_open_shift": False, "shift": None}
    
    # Enrich with sales data
    expected = await calculate_expected_cash(db, shift["id"])
    shift["expected_cash"] = expected["expected_cash"]
    shift["sales_data"] = expected["sales_data"]
    
    return {"has_open_shift": True, "shift": shift}

@router.post("/shift/{shift_id}/close")
async def close_shift(
    shift_id: str,
    data: ShiftCloseRequest,
    user: dict = Depends(require_permission("cash_control", "edit"))
):
    """Close a shift and calculate discrepancy"""
    db = get_database()
    
    shift = await db.cashier_shifts.find_one({"id": shift_id})
    if not shift:
        raise HTTPException(status_code=404, detail="Shift tidak ditemukan")
    
    if shift["status"] != "open":
        raise HTTPException(status_code=400, detail=f"Shift sudah {shift['status']}")
    
    # Only owner of shift or supervisor can close
    if shift["cashier_id"] != user.get("user_id") and user.get("role") not in ["owner", "admin", "supervisor"]:
        raise HTTPException(status_code=403, detail="Tidak berhak menutup shift ini")
    
    # Calculate expected cash
    expected_data = await calculate_expected_cash(db, shift_id)
    expected_cash = expected_data["expected_cash"]
    actual_cash = data.actual_cash
    
    # Calculate discrepancy
    discrepancy = actual_cash - expected_cash
    tolerance = DEFAULT_TOLERANCE
    
    if abs(discrepancy) <= tolerance:
        discrepancy_type = "none"
        status = "closed"
    elif discrepancy < 0:
        discrepancy_type = "shortage"
        status = "discrepancy"
    else:
        discrepancy_type = "overage"
        status = "discrepancy"
    
    # Update shift
    update_data = {
        "end_time": datetime.now(timezone.utc).isoformat(),
        "actual_cash": actual_cash,
        "expected_cash": expected_cash,
        "discrepancy": discrepancy,
        "discrepancy_type": discrepancy_type,
        "status": status,
        "cash_denomination": data.cash_denomination,
        "closing_notes": data.notes,
        "closed_by": user.get("user_id"),
        "closed_by_name": user.get("name"),
        "sales_summary": expected_data["sales_data"]
    }
    
    await db.cashier_shifts.update_one({"id": shift_id}, {"$set": update_data})
    
    # If discrepancy, create discrepancy record
    if discrepancy_type != "none":
        discrepancy_record = {
            "id": str(uuid.uuid4()),
            "shift_id": shift_id,
            "shift_no": shift["shift_no"],
            "branch_id": shift["branch_id"],
            "cashier_id": shift["cashier_id"],
            "cashier_name": shift["cashier_name"],
            "discrepancy_type": discrepancy_type,
            "expected_amount": expected_cash,
            "actual_amount": actual_cash,
            "discrepancy_amount": abs(discrepancy),
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.cash_discrepancies.insert_one(discrepancy_record)
    
    # Audit log
    await db.audit_logs.insert_one({
        "id": str(uuid.uuid4()),
        "action": "shift_close",
        "module": "cash_control",
        "target_id": shift_id,
        "description": f"Shift closed. Expected: Rp {expected_cash:,.0f}, Actual: Rp {actual_cash:,.0f}, Discrepancy: Rp {discrepancy:,.0f} ({discrepancy_type})",
        "user_id": user.get("user_id"),
        "user_name": user.get("name"),
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    return {
        "success": True,
        "shift_id": shift_id,
        "expected_cash": expected_cash,
        "actual_cash": actual_cash,
        "discrepancy": discrepancy,
        "discrepancy_type": discrepancy_type,
        "status": status,
        "message": "Shift closed" + (f" with {discrepancy_type}" if discrepancy_type != "none" else "")
    }

@router.get("/shifts")
async def list_shifts(
    status: Optional[str] = None,
    branch_id: Optional[str] = None,
    cashier_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    has_discrepancy: Optional[bool] = None,
    limit: int = 100,
    user: dict = Depends(get_current_user)
):
    """List cashier shifts"""
    db = get_database()
    
    query = {}
    if status:
        query["status"] = status
    if branch_id:
        query["branch_id"] = branch_id
    if cashier_id:
        query["cashier_id"] = cashier_id
    if date_from:
        query["start_time"] = {"$gte": date_from}
    if date_to:
        if "start_time" in query:
            query["start_time"]["$lte"] = date_to + "T23:59:59"
        else:
            query["start_time"] = {"$lte": date_to + "T23:59:59"}
    if has_discrepancy is True:
        query["discrepancy_type"] = {"$in": ["shortage", "overage"]}
    elif has_discrepancy is False:
        query["discrepancy_type"] = "none"
    
    shifts = await db.cashier_shifts.find(query, {"_id": 0}).sort("start_time", -1).limit(limit).to_list(limit)
    
    # Summary
    summary = {
        "total": len(shifts),
        "open": sum(1 for s in shifts if s.get("status") == "open"),
        "closed": sum(1 for s in shifts if s.get("status") == "closed"),
        "discrepancy": sum(1 for s in shifts if s.get("status") == "discrepancy"),
        "total_sales": sum(s.get("sales_summary", {}).get("total_sales", 0) for s in shifts if s.get("sales_summary")),
        "total_discrepancy": sum(s.get("discrepancy", 0) for s in shifts)
    }
    
    return {"items": shifts, "summary": summary}

@router.get("/shift/{shift_id}")
async def get_shift_detail(
    shift_id: str,
    user: dict = Depends(get_current_user)
):
    """Get shift detail with full breakdown"""
    db = get_database()
    
    shift = await db.cashier_shifts.find_one({"id": shift_id}, {"_id": 0})
    if not shift:
        raise HTTPException(status_code=404, detail="Shift tidak ditemukan")
    
    # Get expected cash calculation
    expected_data = await calculate_expected_cash(db, shift_id)
    shift["calculation"] = expected_data
    
    # Get discrepancy record if exists
    discrepancy = await db.cash_discrepancies.find_one({"shift_id": shift_id}, {"_id": 0})
    shift["discrepancy_record"] = discrepancy
    
    # Get deposits for this shift
    deposits = await db.cash_deposits.find({"shift_id": shift_id}, {"_id": 0}).to_list(10)
    shift["deposits"] = deposits
    
    return shift

@router.post("/deposit")
async def record_deposit(
    data: DepositRequest,
    user: dict = Depends(require_permission("cash_control", "create"))
):
    """Record a cash deposit from shift"""
    db = get_database()
    
    shift = await db.cashier_shifts.find_one({"id": data.shift_id})
    if not shift:
        raise HTTPException(status_code=404, detail="Shift tidak ditemukan")
    
    deposit = {
        "id": str(uuid.uuid4()),
        "deposit_no": f"DEP-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        "shift_id": data.shift_id,
        "shift_no": shift.get("shift_no"),
        "branch_id": shift.get("branch_id"),
        "cashier_id": shift.get("cashier_id"),
        "cashier_name": shift.get("cashier_name"),
        "deposit_amount": data.deposit_amount,
        "deposit_method": data.deposit_method,
        "bank_reference": data.bank_reference,
        "notes": data.notes,
        "status": "deposited",
        "deposited_at": datetime.now(timezone.utc).isoformat(),
        "deposited_by": user.get("user_id"),
        "deposited_by_name": user.get("name"),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.cash_deposits.insert_one(deposit)
    deposit.pop("_id", None)
    
    # Update shift with deposit info
    await db.cashier_shifts.update_one(
        {"id": data.shift_id},
        {"$push": {"deposit_ids": deposit["id"]}, "$inc": {"total_deposited": data.deposit_amount}}
    )
    
    # Audit log
    await db.audit_logs.insert_one({
        "id": str(uuid.uuid4()),
        "action": "cash_deposit",
        "module": "cash_control",
        "target_id": deposit["id"],
        "description": f"Deposit Rp {data.deposit_amount:,.0f} from shift {shift['shift_no']}",
        "user_id": user.get("user_id"),
        "user_name": user.get("name"),
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    return {
        "success": True,
        "deposit": deposit,
        "message": f"Deposit {deposit['deposit_no']} recorded"
    }

@router.get("/deposits")
async def list_deposits(
    branch_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = 100,
    user: dict = Depends(get_current_user)
):
    """List deposits"""
    db = get_database()
    
    query = {}
    if branch_id:
        query["branch_id"] = branch_id
    if date_from:
        query["deposited_at"] = {"$gte": date_from}
    if date_to:
        if "deposited_at" in query:
            query["deposited_at"]["$lte"] = date_to + "T23:59:59"
        else:
            query["deposited_at"] = {"$lte": date_to + "T23:59:59"}
    
    deposits = await db.cash_deposits.find(query, {"_id": 0}).sort("deposited_at", -1).limit(limit).to_list(limit)
    
    summary = {
        "total": len(deposits),
        "total_amount": sum(d.get("deposit_amount", 0) for d in deposits)
    }
    
    return {"items": deposits, "summary": summary}

@router.get("/discrepancies")
async def list_discrepancies(
    status: Optional[str] = None,
    discrepancy_type: Optional[str] = None,
    branch_id: Optional[str] = None,
    limit: int = 100,
    user: dict = Depends(get_current_user)
):
    """List cash discrepancies"""
    db = get_database()
    
    query = {}
    if status:
        query["status"] = status
    if discrepancy_type:
        query["discrepancy_type"] = discrepancy_type
    if branch_id:
        query["branch_id"] = branch_id
    
    discrepancies = await db.cash_discrepancies.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    
    summary = {
        "total": len(discrepancies),
        "pending": sum(1 for d in discrepancies if d.get("status") == "pending"),
        "resolved": sum(1 for d in discrepancies if d.get("status") == "resolved"),
        "shortages": sum(1 for d in discrepancies if d.get("discrepancy_type") == "shortage"),
        "overages": sum(1 for d in discrepancies if d.get("discrepancy_type") == "overage"),
        "total_shortage_amount": sum(d.get("discrepancy_amount", 0) for d in discrepancies if d.get("discrepancy_type") == "shortage"),
        "total_overage_amount": sum(d.get("discrepancy_amount", 0) for d in discrepancies if d.get("discrepancy_type") == "overage")
    }
    
    return {"items": discrepancies, "summary": summary}

@router.post("/discrepancy/{discrepancy_id}/resolve")
async def resolve_discrepancy(
    discrepancy_id: str,
    data: DiscrepancyResolveRequest,
    user: dict = Depends(require_permission("cash_control", "approve"))
):
    """Resolve a cash discrepancy"""
    db = get_database()
    
    discrepancy = await db.cash_discrepancies.find_one({"id": discrepancy_id})
    if not discrepancy:
        raise HTTPException(status_code=404, detail="Discrepancy tidak ditemukan")
    
    if discrepancy["status"] == "resolved":
        raise HTTPException(status_code=400, detail="Discrepancy sudah di-resolve")
    
    # Validate resolution type
    valid_types = ["explained", "written_off", "recovered"]
    if data.resolution_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Resolution type tidak valid: {data.resolution_type}")
    
    update_data = {
        "status": "resolved",
        "resolution_type": data.resolution_type,
        "resolution_notes": data.resolution_notes,
        "recovery_amount": data.recovery_amount or 0,
        "resolved_at": datetime.now(timezone.utc).isoformat(),
        "resolved_by": user.get("user_id"),
        "resolved_by_name": user.get("name")
    }
    
    await db.cash_discrepancies.update_one({"id": discrepancy_id}, {"$set": update_data})
    
    # Update shift status to reviewed
    await db.cashier_shifts.update_one(
        {"id": discrepancy["shift_id"]},
        {"$set": {"status": "reviewed", "reviewed_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Audit log
    await db.audit_logs.insert_one({
        "id": str(uuid.uuid4()),
        "action": "discrepancy_resolve",
        "module": "cash_control",
        "target_id": discrepancy_id,
        "description": f"Discrepancy resolved: {data.resolution_type}. Amount: Rp {discrepancy['discrepancy_amount']:,.0f}",
        "user_id": user.get("user_id"),
        "user_name": user.get("name"),
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    return {
        "success": True,
        "message": f"Discrepancy resolved: {data.resolution_type}"
    }

@router.get("/dashboard/summary")
async def get_cash_control_dashboard(
    branch_id: Optional[str] = None,
    date: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Get cash control dashboard summary"""
    db = get_database()
    
    today = date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Today's shifts
    shift_query = {"start_time": {"$gte": today, "$lt": today + "T23:59:59"}}
    if branch_id:
        shift_query["branch_id"] = branch_id
    
    shifts = await db.cashier_shifts.find(shift_query, {"_id": 0}).to_list(100)
    
    # Current open shifts
    open_shifts = [s for s in shifts if s.get("status") == "open"]
    
    # Discrepancies summary
    discrepancy_query = {"status": "pending"}
    if branch_id:
        discrepancy_query["branch_id"] = branch_id
    
    pending_discrepancies = await db.cash_discrepancies.find(discrepancy_query, {"_id": 0}).to_list(100)
    
    # Today's deposits
    deposit_query = {"deposited_at": {"$gte": today, "$lt": today + "T23:59:59"}}
    if branch_id:
        deposit_query["branch_id"] = branch_id
    
    deposits = await db.cash_deposits.find(deposit_query, {"_id": 0}).to_list(100)
    
    return {
        "date": today,
        "shifts": {
            "total": len(shifts),
            "open": len(open_shifts),
            "closed": sum(1 for s in shifts if s.get("status") in ["closed", "reviewed"]),
            "with_discrepancy": sum(1 for s in shifts if s.get("status") == "discrepancy")
        },
        "sales": {
            "total": sum(s.get("sales_summary", {}).get("total_sales", 0) for s in shifts if s.get("sales_summary")),
            "cash": sum(s.get("sales_summary", {}).get("cash_sales", 0) for s in shifts if s.get("sales_summary")),
            "non_cash": sum(s.get("sales_summary", {}).get("non_cash_sales", 0) for s in shifts if s.get("sales_summary"))
        },
        "discrepancies": {
            "pending_count": len(pending_discrepancies),
            "total_pending_amount": sum(d.get("discrepancy_amount", 0) for d in pending_discrepancies),
            "by_type": {
                "shortage": sum(1 for d in pending_discrepancies if d.get("discrepancy_type") == "shortage"),
                "overage": sum(1 for d in pending_discrepancies if d.get("discrepancy_type") == "overage")
            }
        },
        "deposits": {
            "count": len(deposits),
            "total_amount": sum(d.get("deposit_amount", 0) for d in deposits)
        },
        "open_shifts": [{
            "id": s["id"],
            "shift_no": s["shift_no"],
            "cashier_name": s["cashier_name"],
            "start_time": s["start_time"],
            "initial_cash": s["initial_cash"]
        } for s in open_shifts]
    }

# ==================== CASH MOVEMENT (Petty Cash In/Out) ====================

@router.post("/movement/in")
async def record_cash_in(
    data: CashMovementRequest,
    user: dict = Depends(require_permission("cash_control", "create"))
):
    """Record cash received during shift (other than sales)"""
    db = get_database()
    
    shift = await db.cashier_shifts.find_one({"id": data.shift_id, "status": "open"})
    if not shift:
        raise HTTPException(status_code=404, detail="Shift tidak ditemukan atau sudah ditutup")
    
    movement = {
        "id": str(uuid.uuid4()),
        "shift_id": data.shift_id,
        "type": "cash_in",
        "amount": data.amount,
        "description": data.description,
        "reference": data.reference,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user.get("user_id"),
        "created_by_name": user.get("name")
    }
    
    await db.cash_movements.insert_one(movement)
    movement.pop("_id", None)
    
    return {"success": True, "movement": movement}

@router.post("/movement/out")
async def record_cash_out(
    data: CashMovementRequest,
    user: dict = Depends(require_permission("cash_control", "create"))
):
    """Record cash paid out during shift"""
    db = get_database()
    
    shift = await db.cashier_shifts.find_one({"id": data.shift_id, "status": "open"})
    if not shift:
        raise HTTPException(status_code=404, detail="Shift tidak ditemukan atau sudah ditutup")
    
    movement = {
        "id": str(uuid.uuid4()),
        "shift_id": data.shift_id,
        "type": "cash_out",
        "amount": data.amount,
        "description": data.description,
        "reference": data.reference,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user.get("user_id"),
        "created_by_name": user.get("name")
    }
    
    await db.cash_movements.insert_one(movement)
    movement.pop("_id", None)
    
    return {"success": True, "movement": movement}
