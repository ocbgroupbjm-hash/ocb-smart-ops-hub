"""
OCB TITAN ERP - ACCOUNTING PERIOD LOCK SYSTEM
MASTER BLUEPRINT: Enterprise Hardening Phase

Rule:
- Jika periode sudah CLOSE, transaksi tidak boleh diubah
- Periode lock mencegah backdating
- Hanya OWNER/ADMIN yang bisa lock/unlock periode
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime, timezone, date
from database import get_db
from utils.auth import get_current_user
import uuid

router = APIRouter(prefix="/accounting", tags=["Accounting Period Lock"])

# RBAC - Only OWNER and ADMIN can manage periods
ALLOWED_ROLES = ["owner", "admin", "super_admin"]


class PeriodLockRequest(BaseModel):
    year: int
    month: int
    reason: Optional[str] = None


class PeriodUnlockRequest(BaseModel):
    year: int
    month: int
    reason: str  # Unlock requires reason


def require_period_admin():
    """Check if user can manage accounting periods"""
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
                detail="AKSES DITOLAK: Hanya OWNER atau ADMIN yang dapat mengelola periode akuntansi"
            )
        return user
    return check_role


async def is_period_locked(db, year: int, month: int) -> bool:
    """Check if accounting period is locked"""
    period = await db["accounting_periods"].find_one({
        "year": year,
        "month": month
    })
    
    if period:
        return period.get("status") == "locked"
    
    return False


async def validate_transaction_period(db, transaction_date: str) -> Dict:
    """
    Validate if transaction can be posted to this period
    Returns: {"allowed": bool, "reason": str}
    """
    try:
        if isinstance(transaction_date, str):
            dt = datetime.fromisoformat(transaction_date.replace("Z", "+00:00"))
        else:
            dt = transaction_date
        
        year = dt.year
        month = dt.month
        
        locked = await is_period_locked(db, year, month)
        
        if locked:
            return {
                "allowed": False,
                "reason": f"Periode {year}-{month:02d} sudah di-LOCK. Transaksi tidak dapat diubah.",
                "period": f"{year}-{month:02d}",
                "status": "locked"
            }
        
        return {
            "allowed": True,
            "reason": "Periode masih terbuka",
            "period": f"{year}-{month:02d}",
            "status": "open"
        }
        
    except Exception as e:
        return {
            "allowed": True,
            "reason": f"Error parsing date: {e}",
            "status": "unknown"
        }


# ==================== API ENDPOINTS ====================

@router.get("/periods")
async def list_accounting_periods(
    year: Optional[int] = None,
    user: dict = Depends(get_current_user)
):
    """List all accounting periods and their status"""
    db = get_db()
    
    query = {}
    if year:
        query["year"] = year
    
    periods = await db["accounting_periods"].find(
        query,
        {"_id": 0}
    ).sort([("year", -1), ("month", -1)]).to_list(100)
    
    return {
        "periods": periods,
        "total": len(periods)
    }


@router.get("/periods/{year}/{month}")
async def get_period_status(
    year: int,
    month: int,
    user: dict = Depends(get_current_user)
):
    """Get specific period status"""
    db = get_db()
    
    period = await db["accounting_periods"].find_one(
        {"year": year, "month": month},
        {"_id": 0}
    )
    
    if not period:
        return {
            "year": year,
            "month": month,
            "status": "open",
            "message": "Periode belum pernah di-lock"
        }
    
    return period


@router.post("/periods/lock")
async def lock_accounting_period(
    data: PeriodLockRequest,
    user: dict = Depends(require_period_admin())
):
    """
    Lock an accounting period
    
    Once locked:
    - No new transactions can be posted to this period
    - Existing transactions cannot be modified
    - Journals cannot be voided or adjusted
    """
    db = get_db()
    
    # Check if already locked
    existing = await db["accounting_periods"].find_one({
        "year": data.year,
        "month": data.month
    })
    
    if existing and existing.get("status") == "locked":
        raise HTTPException(
            status_code=400,
            detail=f"Periode {data.year}-{data.month:02d} sudah di-lock"
        )
    
    # Get period statistics before lock
    start_date = f"{data.year}-{data.month:02d}-01"
    if data.month == 12:
        end_date = f"{data.year + 1}-01-01"
    else:
        end_date = f"{data.year}-{data.month + 1:02d}-01"
    
    # Count transactions in period
    journal_count = await db["journal_entries"].count_documents({
        "posted_at": {"$gte": start_date, "$lt": end_date},
        "status": "posted"
    })
    
    sales_count = await db["sales"].count_documents({
        "created_at": {"$gte": start_date, "$lt": end_date}
    })
    
    # Calculate totals
    pipeline = [
        {"$match": {"posted_at": {"$gte": start_date, "$lt": end_date}, "status": "posted"}},
        {"$unwind": "$entries"},
        {"$group": {
            "_id": None,
            "total_debit": {"$sum": "$entries.debit"},
            "total_credit": {"$sum": "$entries.credit"}
        }}
    ]
    
    totals_result = await db["journal_entries"].aggregate(pipeline).to_list(1)
    totals = totals_result[0] if totals_result else {"total_debit": 0, "total_credit": 0}
    
    # Create/update period record
    period_doc = {
        "id": str(uuid.uuid4()),
        "year": data.year,
        "month": data.month,
        "period_name": f"{data.year}-{data.month:02d}",
        "status": "locked",
        "locked_at": datetime.now(timezone.utc).isoformat(),
        "locked_by": user.get("user_id"),
        "locked_by_name": user.get("name"),
        "lock_reason": data.reason or "Period closing",
        "statistics": {
            "journal_count": journal_count,
            "sales_count": sales_count,
            "total_debit": totals.get("total_debit", 0),
            "total_credit": totals.get("total_credit", 0),
            "balanced": abs(totals.get("total_debit", 0) - totals.get("total_credit", 0)) < 1
        }
    }
    
    await db["accounting_periods"].update_one(
        {"year": data.year, "month": data.month},
        {"$set": period_doc},
        upsert=True
    )
    
    # Create audit log
    await db["audit_logs"].insert_one({
        "id": str(uuid.uuid4()),
        "tenant_id": db.name,
        "user_id": user.get("user_id"),
        "user_name": user.get("name"),
        "action": "ACCOUNTING_PERIOD_LOCKED",
        "module": "accounting_period",
        "entity_type": "period",
        "entity_id": period_doc["id"],
        "before_data": {"status": "open"},
        "after_data": {"status": "locked", "period": f"{data.year}-{data.month:02d}"},
        "description": f"Locked accounting period {data.year}-{data.month:02d}",
        "ip_address": "system",
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {
        "success": True,
        "message": f"Periode {data.year}-{data.month:02d} berhasil di-LOCK",
        "period": period_doc
    }


@router.post("/periods/unlock")
async def unlock_accounting_period(
    data: PeriodUnlockRequest,
    user: dict = Depends(require_period_admin())
):
    """
    Unlock an accounting period (requires reason)
    
    WARNING: Unlocking allows modifications to closed period.
    This should only be done for corrections.
    """
    db = get_db()
    
    # Check user is owner (only owner can unlock)
    if user.get("role", "").lower() != "owner":
        raise HTTPException(
            status_code=403,
            detail="AKSES DITOLAK: Hanya OWNER yang dapat membuka periode yang sudah di-lock"
        )
    
    # Find period
    period = await db["accounting_periods"].find_one({
        "year": data.year,
        "month": data.month
    })
    
    if not period:
        raise HTTPException(
            status_code=404,
            detail=f"Periode {data.year}-{data.month:02d} tidak ditemukan"
        )
    
    if period.get("status") != "locked":
        raise HTTPException(
            status_code=400,
            detail=f"Periode {data.year}-{data.month:02d} tidak dalam status locked"
        )
    
    # Update period
    await db["accounting_periods"].update_one(
        {"year": data.year, "month": data.month},
        {"$set": {
            "status": "open",
            "unlocked_at": datetime.now(timezone.utc).isoformat(),
            "unlocked_by": user.get("user_id"),
            "unlocked_by_name": user.get("name"),
            "unlock_reason": data.reason
        }}
    )
    
    # Create audit log
    await db["audit_logs"].insert_one({
        "id": str(uuid.uuid4()),
        "tenant_id": db.name,
        "user_id": user.get("user_id"),
        "user_name": user.get("name"),
        "action": "ACCOUNTING_PERIOD_UNLOCKED",
        "module": "accounting_period",
        "entity_type": "period",
        "entity_id": period.get("id"),
        "before_data": {"status": "locked"},
        "after_data": {"status": "open", "reason": data.reason},
        "description": f"Unlocked accounting period {data.year}-{data.month:02d}: {data.reason}",
        "ip_address": "system",
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {
        "success": True,
        "message": f"Periode {data.year}-{data.month:02d} berhasil di-UNLOCK",
        "reason": data.reason
    }


@router.post("/periods/validate")
async def validate_transaction_date(
    transaction_date: str,
    user: dict = Depends(get_current_user)
):
    """
    Validate if a transaction date is allowed (period not locked)
    
    Use this before posting any transaction to check period status.
    """
    db = get_db()
    
    result = await validate_transaction_period(db, transaction_date)
    
    return result


# ==================== HELPER FOR OTHER MODULES ====================

async def check_period_before_posting(db, transaction_date: str):
    """
    Helper function for other modules to check period before posting
    Raises HTTPException if period is locked
    """
    result = await validate_transaction_period(db, transaction_date)
    
    if not result.get("allowed"):
        raise HTTPException(
            status_code=403,
            detail=result.get("reason", "Periode sudah di-lock")
        )
    
    return True
