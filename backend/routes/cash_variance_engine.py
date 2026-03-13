"""
OCB TITAN ERP - CASH VARIANCE ENGINE
MASTER BLUEPRINT: Enterprise Hardening Phase

Flow:
POS CLOSE → TOTAL SALES → TOTAL SETORAN → Variance Calculation → Auto Journal

Contoh:
Sales   : 3.053.000
Deposit : 3.000.000
Variance: -53.000

System otomatis:
Dr Cash Variance Expense
Cr Cash
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime, timezone, timedelta
from database import get_db
from utils.auth import get_current_user
import uuid

router = APIRouter(prefix="/cash-variance", tags=["Cash Variance Engine"])


class CashDepositRequest(BaseModel):
    shift_id: str
    deposit_amount: float
    deposit_method: str = "cash"  # cash, transfer
    notes: Optional[str] = None


class ShiftCloseRequest(BaseModel):
    shift_id: str
    actual_cash: float
    notes: Optional[str] = None


# ==================== CORE VARIANCE ENGINE ====================

async def calculate_shift_expected_cash(db, shift_id: str) -> Dict:
    """
    Calculate expected cash from shift sales
    
    Expected = Initial Cash + Cash Sales - Cash Refunds
    """
    # Get shift
    shift = await db["cashier_shifts"].find_one({"id": shift_id})
    if not shift:
        return {"error": "Shift not found"}
    
    initial_cash = shift.get("initial_cash", 0) or 0
    
    # Get cash sales during shift
    start_time = shift.get("start_time")
    end_time = shift.get("end_time") or datetime.now(timezone.utc).isoformat()
    branch_id = shift.get("branch_id")
    
    # Sum cash sales
    cash_sales_pipeline = [
        {"$match": {
            "branch_id": branch_id,
            "created_at": {"$gte": start_time, "$lte": end_time},
            "payment_method": {"$in": ["cash", "tunai"]},
            "status": {"$in": ["completed", "paid"]}
        }},
        {"$group": {
            "_id": None,
            "total_cash_sales": {"$sum": "$total_amount"},
            "count": {"$sum": 1}
        }}
    ]
    
    sales_result = await db["sales"].aggregate(cash_sales_pipeline).to_list(1)
    cash_sales = sales_result[0]["total_cash_sales"] if sales_result else 0
    sales_count = sales_result[0]["count"] if sales_result else 0
    
    # Sum cash refunds
    refunds_pipeline = [
        {"$match": {
            "branch_id": branch_id,
            "created_at": {"$gte": start_time, "$lte": end_time},
            "refund_method": {"$in": ["cash", "tunai"]}
        }},
        {"$group": {
            "_id": None,
            "total_refunds": {"$sum": "$refund_amount"}
        }}
    ]
    
    refunds_result = await db["sales_returns"].aggregate(refunds_pipeline).to_list(1)
    cash_refunds = refunds_result[0]["total_refunds"] if refunds_result else 0
    
    expected_cash = initial_cash + cash_sales - cash_refunds
    
    return {
        "shift_id": shift_id,
        "initial_cash": initial_cash,
        "cash_sales": cash_sales,
        "cash_refunds": cash_refunds,
        "expected_cash": expected_cash,
        "sales_count": sales_count
    }


async def create_variance_journal(
    db,
    shift_id: str,
    variance_amount: float,
    branch_id: str,
    branch_name: str,
    cashier_id: str,
    cashier_name: str
) -> Dict:
    """
    Create auto journal for cash variance
    
    If shortage (variance < 0):
        Dr Cash Variance Expense (5902)
        Cr Cash (1101)
    
    If overage (variance > 0):
        Dr Cash (1101)
        Cr Cash Variance Income (4902)
    """
    journal_id = str(uuid.uuid4())
    journal_number = f"JV-VAR-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    amount = abs(variance_amount)
    
    if variance_amount < 0:
        # Shortage - Kasir kurang setor
        entries = [
            {
                "account_code": "5902",
                "account_name": "Beban Selisih Kas",
                "debit": amount,
                "credit": 0,
                "description": f"Cash shortage shift {shift_id[:8]}"
            },
            {
                "account_code": "1101",
                "account_name": "Kas",
                "debit": 0,
                "credit": amount,
                "description": f"Cash shortage shift {shift_id[:8]}"
            }
        ]
        variance_type = "shortage"
    else:
        # Overage - Kasir lebih setor
        entries = [
            {
                "account_code": "1101",
                "account_name": "Kas",
                "debit": amount,
                "credit": 0,
                "description": f"Cash overage shift {shift_id[:8]}"
            },
            {
                "account_code": "4902",
                "account_name": "Pendapatan Selisih Kas",
                "debit": 0,
                "credit": amount,
                "description": f"Cash overage shift {shift_id[:8]}"
            }
        ]
        variance_type = "overage"
    
    journal = {
        "id": journal_id,
        "journal_number": journal_number,
        "transaction_type": "cash_variance",
        "reference_id": shift_id,
        "reference_type": "cashier_shift",
        "description": f"Auto journal: Cash {variance_type} Rp {amount:,.0f} - {cashier_name} @ {branch_name}",
        "entries": entries,
        "status": "posted",
        "total_debit": amount,
        "total_credit": amount,
        "branch_id": branch_id,
        "branch_name": branch_name,
        "created_by": "SYSTEM_BRE",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "posted_at": datetime.now(timezone.utc).isoformat(),
        "auto_generated": True,
        "variance_type": variance_type,
        "cashier_id": cashier_id,
        "cashier_name": cashier_name
    }
    
    await db["journal_entries"].insert_one(journal)
    
    return journal


async def record_cash_variance(
    db,
    shift_id: str,
    expected_cash: float,
    actual_cash: float,
    branch_id: str,
    branch_name: str,
    cashier_id: str,
    cashier_name: str
) -> Dict:
    """
    Record cash variance and create auto journal if needed
    """
    variance = actual_cash - expected_cash
    
    variance_record = {
        "id": str(uuid.uuid4()),
        "shift_id": shift_id,
        "branch_id": branch_id,
        "branch_name": branch_name,
        "cashier_id": cashier_id,
        "cashier_name": cashier_name,
        "expected_cash": expected_cash,
        "actual_cash": actual_cash,
        "variance": variance,
        "variance_type": "shortage" if variance < 0 else ("overage" if variance > 0 else "match"),
        "variance_percentage": (variance / expected_cash * 100) if expected_cash > 0 else 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "recorded"
    }
    
    await db["cash_variances"].insert_one(variance_record)
    
    # Create auto journal if variance exists
    journal = None
    if abs(variance) > 0:
        journal = await create_variance_journal(
            db=db,
            shift_id=shift_id,
            variance_amount=variance,
            branch_id=branch_id,
            branch_name=branch_name,
            cashier_id=cashier_id,
            cashier_name=cashier_name
        )
        variance_record["journal_id"] = journal["id"]
        variance_record["journal_number"] = journal["journal_number"]
        
        # Update variance record with journal reference
        await db["cash_variances"].update_one(
            {"id": variance_record["id"]},
            {"$set": {
                "journal_id": journal["id"],
                "journal_number": journal["journal_number"],
                "status": "journaled"
            }}
        )
    
    return {
        "variance_record": variance_record,
        "journal": journal,
        "auto_journaled": journal is not None
    }


# ==================== API ENDPOINTS ====================

@router.post("/close-shift")
async def close_shift_with_variance(
    data: ShiftCloseRequest,
    user: dict = Depends(get_current_user)
):
    """
    Close POS shift and calculate variance
    
    Flow:
    1. Get expected cash from sales
    2. Compare with actual cash
    3. Calculate variance
    4. Auto-create journal if variance exists
    """
    db = get_db()
    
    # Get shift
    shift = await db["cashier_shifts"].find_one({"id": data.shift_id})
    if not shift:
        raise HTTPException(status_code=404, detail="Shift tidak ditemukan")
    
    if shift.get("status") == "closed":
        raise HTTPException(status_code=400, detail="Shift sudah ditutup")
    
    # Calculate expected cash
    expected_data = await calculate_shift_expected_cash(db, data.shift_id)
    if "error" in expected_data:
        raise HTTPException(status_code=400, detail=expected_data["error"])
    
    expected_cash = expected_data["expected_cash"]
    
    # Record variance
    variance_result = await record_cash_variance(
        db=db,
        shift_id=data.shift_id,
        expected_cash=expected_cash,
        actual_cash=data.actual_cash,
        branch_id=shift.get("branch_id", ""),
        branch_name=shift.get("branch_name", ""),
        cashier_id=shift.get("cashier_id", ""),
        cashier_name=shift.get("cashier_name", "")
    )
    
    # Update shift status
    variance = data.actual_cash - expected_cash
    shift_status = "closed" if abs(variance) == 0 else "discrepancy"
    
    await db["cashier_shifts"].update_one(
        {"id": data.shift_id},
        {"$set": {
            "status": shift_status,
            "end_time": datetime.now(timezone.utc).isoformat(),
            "expected_cash": expected_cash,
            "actual_cash": data.actual_cash,
            "variance_amount": variance,
            "variance_id": variance_result["variance_record"]["id"],
            "closed_by": user.get("user_id"),
            "closed_by_name": user.get("name"),
            "close_notes": data.notes
        }}
    )
    
    # Create audit log
    await db["audit_logs"].insert_one({
        "id": str(uuid.uuid4()),
        "tenant_id": db.name,
        "user_id": user.get("user_id"),
        "user_name": user.get("name"),
        "action": "SHIFT_CLOSED_WITH_VARIANCE",
        "module": "cash_variance",
        "entity_type": "cashier_shift",
        "entity_id": data.shift_id,
        "before_data": {"status": "open"},
        "after_data": {
            "status": shift_status,
            "expected_cash": expected_cash,
            "actual_cash": data.actual_cash,
            "variance": variance
        },
        "description": f"Shift closed: Expected {expected_cash:,.0f}, Actual {data.actual_cash:,.0f}, Variance {variance:,.0f}",
        "ip_address": "system",
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {
        "success": True,
        "shift_id": data.shift_id,
        "expected_cash": expected_cash,
        "actual_cash": data.actual_cash,
        "variance": variance,
        "variance_type": "shortage" if variance < 0 else ("overage" if variance > 0 else "match"),
        "auto_journaled": variance_result["auto_journaled"],
        "journal_number": variance_result.get("journal", {}).get("journal_number") if variance_result["auto_journaled"] else None,
        "message": f"Shift ditutup dengan variance Rp {variance:,.0f}"
    }


@router.get("/shift/{shift_id}/preview")
async def preview_shift_variance(
    shift_id: str,
    actual_cash: float,
    user: dict = Depends(get_current_user)
):
    """Preview variance calculation before closing shift"""
    db = get_db()
    
    expected_data = await calculate_shift_expected_cash(db, shift_id)
    if "error" in expected_data:
        raise HTTPException(status_code=400, detail=expected_data["error"])
    
    expected_cash = expected_data["expected_cash"]
    variance = actual_cash - expected_cash
    
    return {
        "shift_id": shift_id,
        "initial_cash": expected_data["initial_cash"],
        "cash_sales": expected_data["cash_sales"],
        "cash_refunds": expected_data["cash_refunds"],
        "expected_cash": expected_cash,
        "actual_cash": actual_cash,
        "variance": variance,
        "variance_type": "shortage" if variance < 0 else ("overage" if variance > 0 else "match"),
        "will_create_journal": abs(variance) > 0,
        "journal_preview": {
            "debit_account": "5902 - Beban Selisih Kas" if variance < 0 else "1101 - Kas",
            "credit_account": "1101 - Kas" if variance < 0 else "4902 - Pendapatan Selisih Kas",
            "amount": abs(variance)
        } if abs(variance) > 0 else None
    }


@router.get("/report")
async def get_variance_report(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    branch_id: Optional[str] = None,
    cashier_id: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Get cash variance report"""
    db = get_db()
    
    query = {}
    if branch_id:
        query["branch_id"] = branch_id
    if cashier_id:
        query["cashier_id"] = cashier_id
    if date_from or date_to:
        query["created_at"] = {}
        if date_from:
            query["created_at"]["$gte"] = date_from
        if date_to:
            query["created_at"]["$lte"] = date_to + "T23:59:59"
    
    variances = await db["cash_variances"].find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).limit(100).to_list(100)
    
    # Calculate totals
    total_shortage = sum(v["variance"] for v in variances if v["variance"] < 0)
    total_overage = sum(v["variance"] for v in variances if v["variance"] > 0)
    
    return {
        "variances": variances,
        "summary": {
            "total_records": len(variances),
            "shortages": len([v for v in variances if v["variance"] < 0]),
            "overages": len([v for v in variances if v["variance"] > 0]),
            "matches": len([v for v in variances if v["variance"] == 0]),
            "total_shortage": total_shortage,
            "total_overage": total_overage,
            "net_variance": total_shortage + total_overage
        }
    }


@router.get("/cashier-ranking")
async def get_cashier_variance_ranking(
    days: int = 30,
    user: dict = Depends(get_current_user)
):
    """Get cashiers ranked by variance (most problematic first)"""
    db = get_db()
    
    date_from = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    
    pipeline = [
        {"$match": {"created_at": {"$gte": date_from}}},
        {"$group": {
            "_id": "$cashier_id",
            "cashier_name": {"$first": "$cashier_name"},
            "total_variance": {"$sum": "$variance"},
            "total_shortage": {"$sum": {"$cond": [{"$lt": ["$variance", 0]}, "$variance", 0]}},
            "total_overage": {"$sum": {"$cond": [{"$gt": ["$variance", 0]}, "$variance", 0]}},
            "variance_count": {"$sum": 1},
            "shortage_count": {"$sum": {"$cond": [{"$lt": ["$variance", 0]}, 1, 0]}}
        }},
        {"$sort": {"total_shortage": 1}}  # Most shortage first (negative values)
    ]
    
    ranking = await db["cash_variances"].aggregate(pipeline).to_list(50)
    
    return {
        "period_days": days,
        "ranking": ranking
    }
