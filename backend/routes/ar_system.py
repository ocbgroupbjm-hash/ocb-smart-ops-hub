# OCB TITAN ERP - ACCOUNTS RECEIVABLE (AR) MODULE
# Piutang Dagang dengan Auto-Journal Integration
# INTEGRATED: Fiscal Period Validation & Multi-Currency Support

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from database import db
from utils.auth import get_current_user
from routes.rbac_system import check_permission, log_activity, check_branch_access
import uuid

router = APIRouter(prefix="/api/ar", tags=["Accounts Receivable - Piutang Dagang"])

# ==================== FISCAL PERIOD IMPORTS ====================
async def enforce_fiscal_period(transaction_date: str, action: str = "create"):
    """Enforce fiscal period validation"""
    from routes.erp_hardening import enforce_fiscal_period as _enforce
    return await _enforce(transaction_date, action)

async def get_exchange_rate(currency_code: str, transaction_date: str = None) -> float:
    """Get exchange rate for multi-currency"""
    from routes.erp_hardening import get_exchange_rate as _get_rate
    return await _get_rate(currency_code, transaction_date)

async def calculate_exchange_gain_loss(original_amount, original_rate, current_rate, currency_code) -> Dict:
    """Calculate exchange gain/loss"""
    from routes.erp_hardening import calculate_exchange_gain_loss as _calc
    return await _calc(original_amount, original_rate, current_rate, currency_code)

# Collections
ar_collection = db["accounts_receivable"]
ar_payments = db["ar_payments"]
customers_collection = db["customers"]
branches_collection = db["branches"]
journal_entries = db["journal_entries"]
account_mappings = db["account_mapping_settings"]
sales_collection = db["sales_transactions"]

# ==================== AR STATUS ====================
AR_STATUS = {
    "open": {"name": "Terbuka", "color": "blue"},
    "partial": {"name": "Sebagian", "color": "yellow"},
    "paid": {"name": "Lunas", "color": "green"},
    "overdue": {"name": "Jatuh Tempo", "color": "red"},
    "written_off": {"name": "Dihapuskan", "color": "gray"}
}

# ==================== DEFAULT ACCOUNTS ====================
DEFAULT_AR_ACCOUNTS = {
    "ar_account": {"code": "1-1300", "name": "Piutang Usaha"},
    "cash_account": {"code": "1-1100", "name": "Kas"},
    "bank_account": {"code": "1-1200", "name": "Bank"},
    "bad_debt_expense": {"code": "5-6000", "name": "Potongan Piutang"},
    "potongan_piutang": {"code": "5-6000", "name": "Potongan Piutang"},
}

# ==================== ACCOUNT DERIVATION ENGINE ====================
async def derive_ar_account(account_key: str, branch_id: str = None, 
                            warehouse_id: str = None, payment_method: str = None) -> Dict[str, str]:
    """
    ACCOUNT DERIVATION ENGINE for AR Module
    Priority: Branch > Warehouse > Payment > Global > Default
    """
    # Priority 1: Branch mapping
    if branch_id:
        mapping = await db.account_mapping_branch.find_one({
            "branch_id": branch_id, "account_key": account_key
        }, {"_id": 0})
        if mapping:
            return {"code": mapping["account_code"], "name": mapping["account_name"]}
    
    # Priority 2: Warehouse mapping
    if warehouse_id:
        mapping = await db.account_mapping_warehouse.find_one({
            "warehouse_id": warehouse_id, "account_key": account_key
        }, {"_id": 0})
        if mapping:
            return {"code": mapping["account_code"], "name": mapping["account_name"]}
    
    # Priority 3: Payment method mapping
    if payment_method:
        mapping = await db.account_mapping_payment.find_one({
            "payment_method_id": payment_method, "account_key": account_key
        }, {"_id": 0})
        if mapping:
            return {"code": mapping["account_code"], "name": mapping["account_name"]}
    
    # Priority 4: Global setting from account_settings
    global_setting = await db.account_settings.find_one({
        "account_key": account_key
    }, {"_id": 0})
    if global_setting:
        return {"code": global_setting["account_code"], "name": global_setting["account_name"]}
    
    # Priority 5: Default fallback
    default = DEFAULT_AR_ACCOUNTS.get(account_key)
    if default:
        return default
    
    # Final fallback
    return {"code": "9-9999", "name": f"Unknown Account ({account_key})"}

# ==================== PYDANTIC MODELS ====================

class ARCreate(BaseModel):
    customer_id: str
    amount: float
    due_date: str  # YYYY-MM-DD
    source_type: str = "manual"
    source_id: str = ""
    source_no: str = ""
    notes: str = ""

class ARPayment(BaseModel):
    amount: float
    payment_method: str = "cash"  # cash, transfer, bank
    bank_account_id: str = ""
    reference_no: str = ""
    notes: str = ""

class ARWriteOff(BaseModel):
    reason: str
    approved_by: str = ""

# ==================== HELPER FUNCTIONS ====================

async def get_user_ar_scope(user: dict) -> Dict[str, Any]:
    """Get user's AR access scope based on role"""
    user_id = user.get("user_id") or user.get("id")
    role_code = user.get("role_code") or user.get("role")
    branch_id = user.get("branch_id")
    
    # Get role info
    db_user = await db["users"].find_one({"id": user_id}, {"_id": 0})
    if db_user:
        role_code = db_user.get("role_code") or role_code
        branch_id = db_user.get("branch_id") or branch_id
    
    role = await db["roles"].find_one({"code": role_code}, {"_id": 0})
    role_level = role.get("level", 99) if role else 99
    inherit_all = role.get("inherit_all", False) if role else False
    all_branches = role.get("all_branches", False) if role else False
    
    scope = {
        "can_view": False,
        "can_create": False,
        "can_payment": False,
        "can_write_off": False,
        "user_id": user_id,
        "branch_id": branch_id,
        "filter": {}
    }
    
    # PEMILIK / SUPER ADMIN
    if inherit_all or role_level <= 1:
        scope["can_view"] = True
        scope["can_create"] = True
        scope["can_payment"] = True
        scope["can_write_off"] = True
        scope["filter"] = {}
        return scope
    
    # MANAGER / DIREKTUR (Level 2-3)
    if role_level <= 3:
        scope["can_view"] = True
        scope["can_create"] = True
        scope["can_payment"] = True
        scope["can_write_off"] = True
        if not all_branches:
            scope["filter"] = {"branch_id": branch_id}
        return scope
    
    # SUPERVISOR / ADMIN (Level 4-5)
    if role_level <= 5:
        scope["can_view"] = True
        scope["can_create"] = True
        scope["can_payment"] = True
        scope["filter"] = {"branch_id": branch_id}
        return scope
    
    # FINANCE (Level 6)
    if role_level == 6:
        scope["can_view"] = True
        scope["can_payment"] = True
        scope["filter"] = {"branch_id": branch_id}
        return scope
    
    # KASIR / VIEWER
    scope["can_view"] = True
    scope["filter"] = {"branch_id": branch_id}
    return scope


async def generate_ar_number(branch_code: str = "HQ") -> str:
    """Generate unique AR number using CENTRAL ENGINE"""
    from utils.number_generator import generate_transaction_number
    return await generate_transaction_number(db, "AR")


async def generate_payment_number() -> str:
    """Generate unique AR payment number using CENTRAL ENGINE"""
    from utils.number_generator import generate_transaction_number
    return await generate_transaction_number(db, "RECV")


async def create_ar_payment_journal(
    payment: Dict[str, Any],
    ar: Dict[str, Any],
    account_map: Dict,
    user: dict
) -> str:
    """Create journal entry for AR payment using Account Derivation Engine"""
    user_id = user.get("user_id") or user.get("id")
    user_name = user.get("name", "System")
    branch_id = ar.get("branch_id")
    payment_method = payment.get("payment_method", "cash")
    
    # Use central number generator for journal
    from utils.number_generator import generate_transaction_number
    journal_number = await generate_transaction_number(db, "JV")
    
    # Derive accounts using Account Derivation Engine
    # Debit account based on payment method
    if payment_method == "bank":
        debit_account = await derive_ar_account("pembayaran_debit", branch_id=branch_id, payment_method=payment_method)
        if debit_account["code"] == "9-9999":  # fallback if not found
            debit_account = {"code": "1-1200", "name": "Bank"}
    else:
        debit_account = await derive_ar_account("pembayaran_tunai", branch_id=branch_id, payment_method=payment_method)
    
    # Credit account is AR
    credit_account = await derive_ar_account("pembayaran_kredit", branch_id=branch_id)
    
    entries = [
        {
            "account_code": debit_account.get("code"),
            "account_name": debit_account.get("name"),
            "debit": payment.get("amount", 0),
            "credit": 0,
            "description": f"Pelunasan piutang {ar.get('ar_no')} - {ar.get('customer_name')}"
        },
        {
            "account_code": credit_account.get("code"),
            "account_name": credit_account.get("name"),
            "debit": 0,
            "credit": payment.get("amount", 0),
            "description": f"Pelunasan piutang {ar.get('ar_no')}"
        }
    ]
    
    journal = {
        "id": str(uuid.uuid4()),
        "journal_number": journal_number,
        "journal_date": datetime.now(timezone.utc).isoformat(),
        "reference_type": "ar_payment",
        "reference_id": payment.get("id"),
        "reference_number": payment.get("payment_no"),
        "description": f"Pelunasan Piutang {ar.get('ar_no')} - {ar.get('customer_name')}",
        "branch_id": branch_id,
        "entries": entries,
        "total_debit": payment.get("amount", 0),
        "total_credit": payment.get("amount", 0),
        "is_balanced": True,
        "status": "posted",
        "created_by": user_id,
        "created_by_name": user_name,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await journal_entries.insert_one(journal)
    return journal_number


async def update_ar_status(ar_id: str):
    """Update AR status based on outstanding amount"""
    ar = await ar_collection.find_one({"id": ar_id}, {"_id": 0})
    if not ar:
        return
    
    outstanding = ar.get("outstanding_amount", 0)
    original = ar.get("original_amount", 0)
    due_date = ar.get("due_date", "")
    
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    if outstanding <= 0:
        new_status = "paid"
    elif outstanding < original:
        new_status = "partial"
    elif due_date and due_date < today:
        new_status = "overdue"
    else:
        new_status = "open"
    
    await ar_collection.update_one(
        {"id": ar_id},
        {"$set": {"status": new_status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )


# ==================== API ENDPOINTS ====================

@router.get("/list")
async def list_ar(
    keyword: str = "",
    customer_id: str = "",
    status: str = "",
    start_date: str = "",
    end_date: str = "",
    overdue_only: str = "",
    include_deleted: str = "",
    skip: int = 0,
    limit: int = 50,
    user: dict = Depends(get_current_user)
):
    """List AR with filters and role-based access"""
    scope = await get_user_ar_scope(user)
    
    if not scope["can_view"]:
        raise HTTPException(status_code=403, detail="AKSES DITOLAK")
    
    query = {}
    
    # Exclude soft-deleted by default
    if include_deleted != "yes":
        query["$or"] = [
            {"is_deleted": {"$exists": False}},
            {"is_deleted": False}
        ]
    
    # Apply scope filter
    if scope["filter"]:
        query.update(scope["filter"])
    
    if keyword:
        query["$or"] = [
            {"ar_no": {"$regex": keyword, "$options": "i"}},
            {"customer_name": {"$regex": keyword, "$options": "i"}}
        ]
    
    if customer_id:
        query["customer_id"] = customer_id
    
    if status:
        query["status"] = status
    
    if start_date:
        query["ar_date"] = {"$gte": start_date}
    if end_date:
        if "ar_date" in query:
            query["ar_date"]["$lte"] = end_date
        else:
            query["ar_date"] = {"$lte": end_date}
    
    if overdue_only == "yes":
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        query["due_date"] = {"$lt": today}
        query["status"] = {"$in": ["open", "partial"]}
    
    total = await ar_collection.count_documents(query)
    items = await ar_collection.find(query, {"_id": 0}).sort("ar_date", -1).skip(skip).limit(limit).to_list(limit)
    
    # Calculate totals
    total_original = sum(ar.get("original_amount", 0) for ar in items)
    total_outstanding = sum(ar.get("outstanding_amount", 0) for ar in items)
    
    return {
        "items": items,
        "total": total,
        "summary": {
            "total_original": total_original,
            "total_outstanding": total_outstanding,
            "total_paid": total_original - total_outstanding
        }
    }


@router.get("/aging")
async def get_ar_aging(
    branch_id: str = "",
    as_of_date: str = "",
    user: dict = Depends(get_current_user)
):
    """Get AR Aging Report"""
    scope = await get_user_ar_scope(user)
    
    if not scope["can_view"]:
        raise HTTPException(status_code=403, detail="AKSES DITOLAK")
    
    if not as_of_date:
        as_of_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    query = {"status": {"$in": ["open", "partial", "overdue"]}}
    
    if scope["filter"]:
        query.update(scope["filter"])
    elif branch_id:
        query["branch_id"] = branch_id
    
    all_ar = await ar_collection.find(query, {"_id": 0}).to_list(10000)
    
    # Calculate aging buckets
    aging = {
        "current": {"count": 0, "amount": 0},
        "1_30": {"count": 0, "amount": 0},
        "31_60": {"count": 0, "amount": 0},
        "61_90": {"count": 0, "amount": 0},
        "over_90": {"count": 0, "amount": 0}
    }
    
    as_of = datetime.strptime(as_of_date, "%Y-%m-%d")
    
    for ar in all_ar:
        due_date_str = ar.get("due_date", "")
        if not due_date_str:
            continue
        
        # Handle both date formats: YYYY-MM-DD and ISO format
        try:
            if "T" in str(due_date_str):
                due_date = datetime.fromisoformat(str(due_date_str).replace("Z", "+00:00"))
            else:
                due_date = datetime.strptime(str(due_date_str)[:10], "%Y-%m-%d")
        except (ValueError, TypeError):
            continue
            
        days_overdue = (as_of - due_date.replace(tzinfo=None)).days
        outstanding = ar.get("outstanding_amount", 0)
        
        if days_overdue <= 0:
            aging["current"]["count"] += 1
            aging["current"]["amount"] += outstanding
        elif days_overdue <= 30:
            aging["1_30"]["count"] += 1
            aging["1_30"]["amount"] += outstanding
        elif days_overdue <= 60:
            aging["31_60"]["count"] += 1
            aging["31_60"]["amount"] += outstanding
        elif days_overdue <= 90:
            aging["61_90"]["count"] += 1
            aging["61_90"]["amount"] += outstanding
        else:
            aging["over_90"]["count"] += 1
            aging["over_90"]["amount"] += outstanding
    
    total_count = sum(b["count"] for b in aging.values())
    total_amount = sum(b["amount"] for b in aging.values())
    
    return {
        "as_of_date": as_of_date,
        "aging": aging,
        "total_count": total_count,
        "total_outstanding": total_amount
    }


@router.get("/customer/{customer_id}")
async def get_ar_by_customer(
    customer_id: str,
    include_paid: str = "no",
    user: dict = Depends(get_current_user)
):
    """Get all AR for a specific customer"""
    scope = await get_user_ar_scope(user)
    
    if not scope["can_view"]:
        raise HTTPException(status_code=403, detail="AKSES DITOLAK")
    
    query = {"customer_id": customer_id}
    
    if scope["filter"]:
        query.update(scope["filter"])
    
    if include_paid != "yes":
        query["status"] = {"$in": ["open", "partial", "overdue"]}
    
    items = await ar_collection.find(query, {"_id": 0}).sort("due_date", 1).to_list(1000)
    
    # Get customer info
    customer = await customers_collection.find_one({"id": customer_id}, {"_id": 0, "name": 1, "receivable_limit": 1})
    
    total_outstanding = sum(ar.get("outstanding_amount", 0) for ar in items)
    limit = customer.get("receivable_limit", 0) if customer else 0
    
    return {
        "customer_id": customer_id,
        "customer_name": customer.get("name") if customer else "",
        "receivable_limit": limit,
        "total_outstanding": total_outstanding,
        "available_credit": max(0, limit - total_outstanding) if limit > 0 else None,
        "is_over_limit": total_outstanding > limit if limit > 0 else False,
        "items": items
    }


@router.get("/{ar_id}")
async def get_ar_detail(
    ar_id: str,
    user: dict = Depends(get_current_user)
):
    """Get AR detail with payment history"""
    scope = await get_user_ar_scope(user)
    
    if not scope["can_view"]:
        raise HTTPException(status_code=403, detail="AKSES DITOLAK")
    
    ar = await ar_collection.find_one({"id": ar_id}, {"_id": 0})
    if not ar:
        raise HTTPException(status_code=404, detail="Piutang tidak ditemukan")
    
    # Check scope
    if scope["filter"].get("branch_id") and ar.get("branch_id") != scope["filter"]["branch_id"]:
        raise HTTPException(status_code=403, detail="AKSES DITOLAK. Anda tidak memiliki akses ke data ini.")
    
    # Get payments
    payments = await ar_payments.find({"ar_id": ar_id}, {"_id": 0}).sort("payment_date", 1).to_list(100)
    
    ar["payments"] = payments
    ar["payment_count"] = len(payments)
    
    return ar


@router.post("/create")
async def create_ar(
    data: ARCreate,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """Create new AR manually"""
    scope = await get_user_ar_scope(user)
    
    if not scope["can_create"]:
        raise HTTPException(status_code=403, detail="AKSES DITOLAK")
    
    user_id = scope["user_id"]
    branch_id = scope["branch_id"]
    user_name = user.get("name", "")
    
    # Get customer info
    customer = await customers_collection.find_one({"id": data.customer_id}, {"_id": 0})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer tidak ditemukan")
    
    # Get branch info
    branch = await branches_collection.find_one({"id": branch_id}, {"_id": 0})
    branch_code = branch.get("code", "HQ") if branch else "HQ"
    
    ar_no = await generate_ar_number(branch_code)
    
    ar = {
        "id": str(uuid.uuid4()),
        "ar_no": ar_no,
        "ar_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "due_date": data.due_date,
        "customer_id": data.customer_id,
        "customer_name": customer.get("name", ""),
        "branch_id": branch_id,
        "source_type": data.source_type,
        "source_id": data.source_id,
        "source_no": data.source_no,
        "currency": "IDR",
        "original_amount": data.amount,
        "paid_amount": 0,
        "outstanding_amount": data.amount,
        "status": "open",
        "payment_term_days": 0,
        "notes": data.notes,
        "created_by": user_id,
        "created_by_name": user_name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await ar_collection.insert_one(ar)
    
    await log_activity(
        db, user_id, user_name,
        "create", "accounts_receivable",
        f"Membuat piutang {ar_no} untuk {customer.get('name')} senilai Rp {data.amount:,.0f}",
        request.client.host if request.client else "",
        branch_id
    )
    
    return {"id": ar["id"], "ar_no": ar_no, "message": "Piutang berhasil dibuat"}


@router.post("/{ar_id}/payment")
async def record_ar_payment(
    ar_id: str,
    data: ARPayment,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """Record payment for AR"""
    scope = await get_user_ar_scope(user)
    
    if not scope["can_payment"]:
        raise HTTPException(status_code=403, detail="AKSES DITOLAK")
    
    ar = await ar_collection.find_one({"id": ar_id}, {"_id": 0})
    if not ar:
        raise HTTPException(status_code=404, detail="Piutang tidak ditemukan")
    
    # Check scope
    if scope["filter"].get("branch_id") and ar.get("branch_id") != scope["filter"]["branch_id"]:
        raise HTTPException(status_code=403, detail="AKSES DITOLAK")
    
    if ar.get("status") == "paid":
        raise HTTPException(status_code=400, detail="Piutang sudah lunas")
    
    if data.amount > ar.get("outstanding_amount", 0):
        raise HTTPException(status_code=400, detail="Jumlah pembayaran melebihi sisa piutang")
    
    user_id = scope["user_id"]
    user_name = user.get("name", "")
    
    payment_no = await generate_payment_number()
    
    # Create payment record
    payment = {
        "id": str(uuid.uuid4()),
        "payment_no": payment_no,
        "payment_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "ar_id": ar_id,
        "ar_no": ar.get("ar_no"),
        "customer_id": ar.get("customer_id"),
        "branch_id": ar.get("branch_id"),
        "amount": data.amount,
        "payment_method": data.payment_method,
        "bank_account_id": data.bank_account_id,
        "reference_no": data.reference_no,
        "notes": data.notes,
        "journal_id": None,
        "created_by": user_id,
        "created_by_name": user_name,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await ar_payments.insert_one(payment)
    
    # Update AR
    new_paid = ar.get("paid_amount", 0) + data.amount
    new_outstanding = ar.get("original_amount", 0) - new_paid
    
    await ar_collection.update_one(
        {"id": ar_id},
        {"$set": {
            "paid_amount": new_paid,
            "outstanding_amount": new_outstanding,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Update status
    await update_ar_status(ar_id)
    
    # Get account mapping
    mapping = await account_mappings.find_one({"branch_id": ar.get("branch_id")}, {"_id": 0})
    if not mapping:
        mapping = await account_mappings.find_one({"branch_id": "default"}, {"_id": 0})
    account_map = mapping.get("mappings", DEFAULT_AR_ACCOUNTS) if mapping else DEFAULT_AR_ACCOUNTS
    
    # Create journal entry
    journal_no = await create_ar_payment_journal(payment, ar, account_map, user)
    
    # Update payment with journal reference
    await ar_payments.update_one({"id": payment["id"]}, {"$set": {"journal_id": journal_no}})
    
    await log_activity(
        db, user_id, user_name,
        "payment", "accounts_receivable",
        f"Pembayaran piutang {ar.get('ar_no')} sebesar Rp {data.amount:,.0f}",
        request.client.host if request.client else "",
        ar.get("branch_id")
    )
    
    return {
        "payment_no": payment_no,
        "journal_no": journal_no,
        "new_outstanding": new_outstanding,
        "message": "Pembayaran berhasil dicatat"
    }


@router.post("/{ar_id}/write-off")
async def write_off_ar(
    ar_id: str,
    data: ARWriteOff,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """Write off uncollectible AR"""
    scope = await get_user_ar_scope(user)
    
    if not scope["can_write_off"]:
        raise HTTPException(status_code=403, detail="AKSES DITOLAK. Hanya manager/owner yang bisa write-off.")
    
    ar = await ar_collection.find_one({"id": ar_id}, {"_id": 0})
    if not ar:
        raise HTTPException(status_code=404, detail="Piutang tidak ditemukan")
    
    if ar.get("status") == "paid":
        raise HTTPException(status_code=400, detail="Piutang sudah lunas")
    
    user_id = scope["user_id"]
    user_name = user.get("name", "")
    
    await ar_collection.update_one(
        {"id": ar_id},
        {"$set": {
            "status": "written_off",
            "write_off_reason": data.reason,
            "write_off_by": user_id,
            "write_off_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    await log_activity(
        db, user_id, user_name,
        "write_off", "accounts_receivable",
        f"Write-off piutang {ar.get('ar_no')} sebesar Rp {ar.get('outstanding_amount', 0):,.0f}: {data.reason}",
        request.client.host if request.client else "",
        ar.get("branch_id"),
        severity="critical"
    )
    
    return {"message": "Piutang berhasil dihapuskan"}


@router.get("/summary/dashboard")
async def get_ar_summary(
    user: dict = Depends(get_current_user)
):
    """Get AR summary for dashboard"""
    scope = await get_user_ar_scope(user)
    
    if not scope["can_view"]:
        raise HTTPException(status_code=403, detail="AKSES DITOLAK")
    
    query = {"status": {"$in": ["open", "partial", "overdue"]}}
    
    if scope["filter"]:
        query.update(scope["filter"])
    
    all_ar = await ar_collection.find(query, {"_id": 0}).to_list(10000)
    
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    summary = {
        "total_ar_count": len(all_ar),
        "total_outstanding": sum(ar.get("outstanding_amount", 0) for ar in all_ar),
        "overdue_count": len([ar for ar in all_ar if ar.get("due_date", "") < today]),
        "overdue_amount": sum(ar.get("outstanding_amount", 0) for ar in all_ar if ar.get("due_date", "") < today),
        "due_this_week": 0,
        "due_this_week_amount": 0
    }
    
    # Calculate due this week
    week_end = (datetime.now(timezone.utc) + timedelta(days=7)).strftime("%Y-%m-%d")
    for ar in all_ar:
        due = ar.get("due_date", "")
        if today <= due <= week_end:
            summary["due_this_week"] += 1
            summary["due_this_week_amount"] += ar.get("outstanding_amount", 0)
    
    return summary


@router.put("/{ar_id}/soft-delete")
async def soft_delete_ar(
    ar_id: str,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """
    Soft delete AR - sets status to 'deleted' instead of hard delete.
    Only allowed for AR without any payments.
    
    ARSITEKTUR AP/AR Enterprise:
    - Soft delete only for AR without journal/audit trail
    - Hard delete NEVER allowed for posted transactions
    """
    scope = await get_user_ar_scope(user)
    
    if not scope["can_create"]:
        raise HTTPException(status_code=403, detail="AKSES DITOLAK")
    
    ar = await ar_collection.find_one({"id": ar_id}, {"_id": 0})
    if not ar:
        raise HTTPException(status_code=404, detail="Piutang tidak ditemukan")
    
    if scope["filter"].get("branch_id") and ar.get("branch_id") != scope["filter"]["branch_id"]:
        raise HTTPException(status_code=403, detail="AKSES DITOLAK")
    
    # Validation: Cannot delete if has payments
    if ar.get("paid_amount", 0) > 0:
        raise HTTPException(status_code=400, detail="Tidak dapat menghapus piutang yang sudah ada pembayaran")
    
    if ar.get("status") == "paid":
        raise HTTPException(status_code=400, detail="Tidak dapat menghapus piutang yang sudah lunas")
    
    if ar.get("status") == "written_off":
        raise HTTPException(status_code=400, detail="Tidak dapat menghapus piutang yang sudah dihapuskan")
    
    # Check if has any payments recorded
    payment_count = await ar_payments.count_documents({"ar_id": ar_id})
    if payment_count > 0:
        raise HTTPException(status_code=400, detail="Tidak dapat menghapus piutang yang sudah ada catatan pembayaran")
    
    user_id = scope["user_id"]
    user_name = user.get("name", "")
    
    # Soft delete - mark as deleted
    await ar_collection.update_one(
        {"id": ar_id},
        {"$set": {
            "status": "deleted",
            "is_deleted": True,
            "deleted_at": datetime.now(timezone.utc).isoformat(),
            "deleted_by": user_id,
            "deleted_by_name": user_name,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    await log_activity(
        db, user_id, user_name,
        "soft_delete", "accounts_receivable",
        f"Menghapus piutang {ar.get('ar_no')} customer {ar.get('customer_name')}",
        request.client.host if request.client else "",
        ar.get("branch_id")
    )
    
    return {
        "message": "Piutang berhasil dihapus (soft delete)",
        "ar_no": ar.get("ar_no")
    }


# ==================== AUTO-CREATE FROM SALES ====================

async def create_ar_from_sales(sales_data: Dict[str, Any], user: dict) -> Optional[str]:
    """
    Auto-create AR from credit sales
    Called by sales module when payment_type is credit
    """
    if sales_data.get("payment_status") == "paid":
        return None
    
    receivable_amount = sales_data.get("receivable_total", 0)
    if receivable_amount <= 0:
        return None
    
    customer_id = sales_data.get("customer_id")
    if not customer_id:
        return None
    
    customer = await customers_collection.find_one({"id": customer_id}, {"_id": 0})
    if not customer:
        return None
    
    branch_id = sales_data.get("branch_id", "")
    branch = await branches_collection.find_one({"id": branch_id}, {"_id": 0})
    branch_code = branch.get("code", "HQ") if branch else "HQ"
    
    # Calculate due date (default 30 days or from customer setting)
    payment_term = customer.get("payment_term_days", 30)
    due_date = (datetime.now(timezone.utc) + timedelta(days=payment_term)).strftime("%Y-%m-%d")
    
    ar_no = await generate_ar_number(branch_code)
    user_id = user.get("user_id") or user.get("id")
    
    ar = {
        "id": str(uuid.uuid4()),
        "ar_no": ar_no,
        "ar_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "due_date": due_date,
        "customer_id": customer_id,
        "customer_name": customer.get("name", ""),
        "branch_id": branch_id,
        "source_type": "sales",
        "source_id": sales_data.get("id", ""),
        "source_no": sales_data.get("sales_no", ""),
        "currency": "IDR",
        "original_amount": receivable_amount,
        "paid_amount": 0,
        "outstanding_amount": receivable_amount,
        "status": "open",
        "payment_term_days": payment_term,
        "notes": f"Piutang dari penjualan {sales_data.get('sales_no', '')}",
        "created_by": user_id,
        "created_by_name": user.get("name", "System"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await ar_collection.insert_one(ar)
    
    return ar_no


# ==================== INIT ====================

@router.post("/init")
async def initialize_ar_system(user: dict = Depends(get_current_user)):
    """Initialize AR system"""
    
    # Create indexes
    await ar_collection.create_index("ar_no", unique=True)
    await ar_collection.create_index("customer_id")
    await ar_collection.create_index("branch_id")
    await ar_collection.create_index("status")
    await ar_collection.create_index("due_date")
    await ar_payments.create_index("ar_id")
    await ar_payments.create_index("payment_date")
    
    return {
        "message": "AR system initialized",
        "indexes_created": True
    }
