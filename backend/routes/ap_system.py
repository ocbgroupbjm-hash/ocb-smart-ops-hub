# OCB TITAN ERP - ACCOUNTS PAYABLE (AP) MODULE
# Hutang Dagang dengan Auto-Journal Integration

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from database import db
from utils.auth import get_current_user
from routes.rbac_system import check_permission, log_activity, check_branch_access
import uuid

router = APIRouter(prefix="/api/ap", tags=["Accounts Payable - Hutang Dagang"])

# Collections
ap_collection = db["accounts_payable"]
ap_payments = db["ap_payments"]
suppliers_collection = db["suppliers"]
branches_collection = db["branches"]
journal_entries = db["journal_entries"]
account_mappings = db["account_mapping_settings"]
purchases_collection = db["purchases"]

# ==================== AP STATUS ====================
AP_STATUS = {
    "open": {"name": "Terbuka", "color": "blue"},
    "partial": {"name": "Sebagian", "color": "yellow"},
    "paid": {"name": "Lunas", "color": "green"},
    "overdue": {"name": "Jatuh Tempo", "color": "red"}
}

# ==================== DEFAULT ACCOUNTS ====================
DEFAULT_AP_ACCOUNTS = {
    "ap_account": {"code": "2101", "name": "Hutang Dagang"},
    "cash_account": {"code": "1101", "name": "Kas"},
    "bank_account": {"code": "1102", "name": "Bank"}
}

# ==================== PYDANTIC MODELS ====================

class APCreate(BaseModel):
    supplier_id: str
    amount: float
    due_date: str  # YYYY-MM-DD
    supplier_invoice_no: str = ""
    source_type: str = "manual"
    source_id: str = ""
    source_no: str = ""
    notes: str = ""

class APPayment(BaseModel):
    amount: float
    payment_method: str = "transfer"  # cash, transfer, bank
    bank_account_id: str = ""
    reference_no: str = ""
    notes: str = ""

# ==================== HELPER FUNCTIONS ====================

async def get_user_ap_scope(user: dict) -> Dict[str, Any]:
    """Get user's AP access scope based on role"""
    user_id = user.get("user_id") or user.get("id")
    role_code = user.get("role_code") or user.get("role")
    branch_id = user.get("branch_id")
    
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
        "user_id": user_id,
        "branch_id": branch_id,
        "filter": {}
    }
    
    # PEMILIK / SUPER ADMIN
    if inherit_all or role_level <= 1:
        scope["can_view"] = True
        scope["can_create"] = True
        scope["can_payment"] = True
        scope["filter"] = {}
        return scope
    
    # MANAGER / DIREKTUR (Level 2-3)
    if role_level <= 3:
        scope["can_view"] = True
        scope["can_create"] = True
        scope["can_payment"] = True
        if not all_branches:
            scope["filter"] = {"branch_id": branch_id}
        return scope
    
    # SUPERVISOR / ADMIN / FINANCE (Level 4-6)
    if role_level <= 6:
        scope["can_view"] = True
        scope["can_create"] = role_level <= 5
        scope["can_payment"] = role_level <= 6
        scope["filter"] = {"branch_id": branch_id}
        return scope
    
    # KASIR / VIEWER - Limited access
    scope["can_view"] = False  # AP tidak boleh dilihat kasir
    return scope


async def generate_ap_number(branch_code: str = "HQ") -> str:
    """Generate unique AP number"""
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    prefix = f"AP-{branch_code}-{today}"
    
    last = await ap_collection.find_one(
        {"ap_no": {"$regex": f"^{prefix}"}},
        {"_id": 0, "ap_no": 1},
        sort=[("ap_no", -1)]
    )
    
    if last:
        try:
            seq = int(last["ap_no"].split("-")[-1]) + 1
        except:
            seq = 1
    else:
        seq = 1
    
    return f"{prefix}-{seq:04d}"


async def generate_payment_number() -> str:
    """Generate unique payment number"""
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    prefix = f"APP-{today}"
    
    last = await ap_payments.find_one(
        {"payment_no": {"$regex": f"^{prefix}"}},
        {"_id": 0, "payment_no": 1},
        sort=[("payment_no", -1)]
    )
    
    if last:
        try:
            seq = int(last["payment_no"].split("-")[-1]) + 1
        except:
            seq = 1
    else:
        seq = 1
    
    return f"{prefix}-{seq:04d}"


async def create_ap_payment_journal(
    payment: Dict[str, Any],
    ap: Dict[str, Any],
    account_map: Dict,
    user: dict
) -> str:
    """Create journal entry for AP payment"""
    user_id = user.get("user_id") or user.get("id")
    user_name = user.get("name", "System")
    
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    journal_number = f"JV-APP-{today}-{uuid.uuid4().hex[:6].upper()}"
    
    # Debit AP, Credit Cash/Bank
    debit_account = account_map.get("ap_account", DEFAULT_AP_ACCOUNTS["ap_account"])
    
    if payment.get("payment_method") == "bank" or payment.get("payment_method") == "transfer":
        credit_account = account_map.get("bank_account", DEFAULT_AP_ACCOUNTS["bank_account"])
    else:
        credit_account = account_map.get("cash_account", DEFAULT_AP_ACCOUNTS["cash_account"])
    
    entries = [
        {
            "account_code": debit_account.get("code"),
            "account_name": debit_account.get("name"),
            "debit": payment.get("amount", 0),
            "credit": 0,
            "description": f"Pembayaran hutang {ap.get('ap_no')} - {ap.get('supplier_name')}"
        },
        {
            "account_code": credit_account.get("code"),
            "account_name": credit_account.get("name"),
            "debit": 0,
            "credit": payment.get("amount", 0),
            "description": f"Pembayaran hutang {ap.get('ap_no')}"
        }
    ]
    
    journal = {
        "id": str(uuid.uuid4()),
        "journal_number": journal_number,
        "journal_date": datetime.now(timezone.utc).isoformat(),
        "reference_type": "ap_payment",
        "reference_id": payment.get("id"),
        "reference_number": payment.get("payment_no"),
        "description": f"Pembayaran Hutang {ap.get('ap_no')} - {ap.get('supplier_name')}",
        "branch_id": ap.get("branch_id"),
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


async def update_ap_status(ap_id: str):
    """Update AP status based on outstanding amount"""
    ap = await ap_collection.find_one({"id": ap_id}, {"_id": 0})
    if not ap:
        return
    
    outstanding = ap.get("outstanding_amount", 0)
    original = ap.get("original_amount", 0)
    due_date = ap.get("due_date", "")
    
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    if outstanding <= 0:
        new_status = "paid"
    elif outstanding < original:
        new_status = "partial"
    elif due_date and due_date < today:
        new_status = "overdue"
    else:
        new_status = "open"
    
    await ap_collection.update_one(
        {"id": ap_id},
        {"$set": {"status": new_status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )


# ==================== API ENDPOINTS ====================

@router.get("/list")
async def list_ap(
    keyword: str = "",
    supplier_id: str = "",
    status: str = "",
    start_date: str = "",
    end_date: str = "",
    overdue_only: str = "",
    skip: int = 0,
    limit: int = 50,
    user: dict = Depends(get_current_user)
):
    """List AP with filters and role-based access"""
    scope = await get_user_ap_scope(user)
    
    if not scope["can_view"]:
        raise HTTPException(status_code=403, detail="AKSES DITOLAK")
    
    query = {}
    
    if scope["filter"]:
        query.update(scope["filter"])
    
    if keyword:
        query["$or"] = [
            {"ap_no": {"$regex": keyword, "$options": "i"}},
            {"supplier_name": {"$regex": keyword, "$options": "i"}},
            {"supplier_invoice_no": {"$regex": keyword, "$options": "i"}}
        ]
    
    if supplier_id:
        query["supplier_id"] = supplier_id
    
    if status:
        query["status"] = status
    
    if start_date:
        query["ap_date"] = {"$gte": start_date}
    if end_date:
        if "ap_date" in query:
            query["ap_date"]["$lte"] = end_date
        else:
            query["ap_date"] = {"$lte": end_date}
    
    if overdue_only == "yes":
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        query["due_date"] = {"$lt": today}
        query["status"] = {"$in": ["open", "partial"]}
    
    total = await ap_collection.count_documents(query)
    items = await ap_collection.find(query, {"_id": 0}).sort("due_date", 1).skip(skip).limit(limit).to_list(limit)
    
    total_original = sum(ap.get("original_amount", 0) for ap in items)
    total_outstanding = sum(ap.get("outstanding_amount", 0) for ap in items)
    
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
async def get_ap_aging(
    branch_id: str = "",
    as_of_date: str = "",
    user: dict = Depends(get_current_user)
):
    """Get AP Aging Report"""
    scope = await get_user_ap_scope(user)
    
    if not scope["can_view"]:
        raise HTTPException(status_code=403, detail="AKSES DITOLAK")
    
    if not as_of_date:
        as_of_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    query = {"status": {"$in": ["open", "partial", "overdue"]}}
    
    if scope["filter"]:
        query.update(scope["filter"])
    elif branch_id:
        query["branch_id"] = branch_id
    
    all_ap = await ap_collection.find(query, {"_id": 0}).to_list(10000)
    
    aging = {
        "current": {"count": 0, "amount": 0},
        "1_30": {"count": 0, "amount": 0},
        "31_60": {"count": 0, "amount": 0},
        "61_90": {"count": 0, "amount": 0},
        "over_90": {"count": 0, "amount": 0}
    }
    
    as_of = datetime.strptime(as_of_date, "%Y-%m-%d")
    
    for ap in all_ap:
        due_date_str = ap.get("due_date", "")
        if not due_date_str:
            continue
        
        due_date = datetime.strptime(due_date_str, "%Y-%m-%d")
        days_overdue = (as_of - due_date).days
        outstanding = ap.get("outstanding_amount", 0)
        
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


@router.get("/supplier/{supplier_id}")
async def get_ap_by_supplier(
    supplier_id: str,
    include_paid: str = "no",
    user: dict = Depends(get_current_user)
):
    """Get all AP for a specific supplier"""
    scope = await get_user_ap_scope(user)
    
    if not scope["can_view"]:
        raise HTTPException(status_code=403, detail="AKSES DITOLAK")
    
    query = {"supplier_id": supplier_id}
    
    if scope["filter"]:
        query.update(scope["filter"])
    
    if include_paid != "yes":
        query["status"] = {"$in": ["open", "partial", "overdue"]}
    
    items = await ap_collection.find(query, {"_id": 0}).sort("due_date", 1).to_list(1000)
    
    supplier = await suppliers_collection.find_one({"id": supplier_id}, {"_id": 0, "name": 1})
    
    total_outstanding = sum(ap.get("outstanding_amount", 0) for ap in items)
    
    return {
        "supplier_id": supplier_id,
        "supplier_name": supplier.get("name") if supplier else "",
        "total_outstanding": total_outstanding,
        "items": items
    }


@router.get("/due-soon")
async def get_ap_due_soon(
    days: int = 7,
    user: dict = Depends(get_current_user)
):
    """Get AP due within specified days"""
    scope = await get_user_ap_scope(user)
    
    if not scope["can_view"]:
        raise HTTPException(status_code=403, detail="AKSES DITOLAK")
    
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    due_by = (datetime.now(timezone.utc) + timedelta(days=days)).strftime("%Y-%m-%d")
    
    query = {
        "status": {"$in": ["open", "partial"]},
        "due_date": {"$gte": today, "$lte": due_by}
    }
    
    if scope["filter"]:
        query.update(scope["filter"])
    
    items = await ap_collection.find(query, {"_id": 0}).sort("due_date", 1).to_list(100)
    
    total_due = sum(ap.get("outstanding_amount", 0) for ap in items)
    
    return {
        "period": f"Due within {days} days",
        "from_date": today,
        "to_date": due_by,
        "count": len(items),
        "total_due": total_due,
        "items": items
    }


@router.get("/{ap_id}")
async def get_ap_detail(
    ap_id: str,
    user: dict = Depends(get_current_user)
):
    """Get AP detail with payment history"""
    scope = await get_user_ap_scope(user)
    
    if not scope["can_view"]:
        raise HTTPException(status_code=403, detail="AKSES DITOLAK")
    
    ap = await ap_collection.find_one({"id": ap_id}, {"_id": 0})
    if not ap:
        raise HTTPException(status_code=404, detail="Hutang tidak ditemukan")
    
    if scope["filter"].get("branch_id") and ap.get("branch_id") != scope["filter"]["branch_id"]:
        raise HTTPException(status_code=403, detail="AKSES DITOLAK")
    
    payments = await ap_payments.find({"ap_id": ap_id}, {"_id": 0}).sort("payment_date", 1).to_list(100)
    
    ap["payments"] = payments
    ap["payment_count"] = len(payments)
    
    return ap


@router.post("/create")
async def create_ap(
    data: APCreate,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """Create new AP manually"""
    scope = await get_user_ap_scope(user)
    
    if not scope["can_create"]:
        raise HTTPException(status_code=403, detail="AKSES DITOLAK")
    
    user_id = scope["user_id"]
    branch_id = scope["branch_id"]
    user_name = user.get("name", "")
    
    supplier = await suppliers_collection.find_one({"id": data.supplier_id}, {"_id": 0})
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier tidak ditemukan")
    
    branch = await branches_collection.find_one({"id": branch_id}, {"_id": 0})
    branch_code = branch.get("code", "HQ") if branch else "HQ"
    
    ap_no = await generate_ap_number(branch_code)
    
    ap = {
        "id": str(uuid.uuid4()),
        "ap_no": ap_no,
        "ap_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "due_date": data.due_date,
        "supplier_id": data.supplier_id,
        "supplier_name": supplier.get("name", ""),
        "supplier_invoice_no": data.supplier_invoice_no,
        "branch_id": branch_id,
        "source_type": data.source_type,
        "source_id": data.source_id,
        "source_no": data.source_no,
        "currency": "IDR",
        "original_amount": data.amount,
        "paid_amount": 0,
        "outstanding_amount": data.amount,
        "status": "open",
        "payment_term_days": supplier.get("payment_term_days", 30),
        "notes": data.notes,
        "created_by": user_id,
        "created_by_name": user_name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await ap_collection.insert_one(ap)
    
    await log_activity(
        db, user_id, user_name,
        "create", "accounts_payable",
        f"Membuat hutang {ap_no} untuk {supplier.get('name')} senilai Rp {data.amount:,.0f}",
        request.client.host if request.client else "",
        branch_id
    )
    
    return {"id": ap["id"], "ap_no": ap_no, "message": "Hutang berhasil dibuat"}


@router.post("/{ap_id}/payment")
async def record_ap_payment(
    ap_id: str,
    data: APPayment,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """Record payment for AP"""
    scope = await get_user_ap_scope(user)
    
    if not scope["can_payment"]:
        raise HTTPException(status_code=403, detail="AKSES DITOLAK")
    
    ap = await ap_collection.find_one({"id": ap_id}, {"_id": 0})
    if not ap:
        raise HTTPException(status_code=404, detail="Hutang tidak ditemukan")
    
    if scope["filter"].get("branch_id") and ap.get("branch_id") != scope["filter"]["branch_id"]:
        raise HTTPException(status_code=403, detail="AKSES DITOLAK")
    
    if ap.get("status") == "paid":
        raise HTTPException(status_code=400, detail="Hutang sudah lunas")
    
    if data.amount > ap.get("outstanding_amount", 0):
        raise HTTPException(status_code=400, detail="Jumlah pembayaran melebihi sisa hutang")
    
    user_id = scope["user_id"]
    user_name = user.get("name", "")
    
    payment_no = await generate_payment_number()
    
    payment = {
        "id": str(uuid.uuid4()),
        "payment_no": payment_no,
        "payment_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "ap_id": ap_id,
        "ap_no": ap.get("ap_no"),
        "supplier_id": ap.get("supplier_id"),
        "branch_id": ap.get("branch_id"),
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
    
    await ap_payments.insert_one(payment)
    
    new_paid = ap.get("paid_amount", 0) + data.amount
    new_outstanding = ap.get("original_amount", 0) - new_paid
    
    await ap_collection.update_one(
        {"id": ap_id},
        {"$set": {
            "paid_amount": new_paid,
            "outstanding_amount": new_outstanding,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    await update_ap_status(ap_id)
    
    mapping = await account_mappings.find_one({"branch_id": ap.get("branch_id")}, {"_id": 0})
    if not mapping:
        mapping = await account_mappings.find_one({"branch_id": "default"}, {"_id": 0})
    account_map = mapping.get("mappings", DEFAULT_AP_ACCOUNTS) if mapping else DEFAULT_AP_ACCOUNTS
    
    journal_no = await create_ap_payment_journal(payment, ap, account_map, user)
    
    await ap_payments.update_one({"id": payment["id"]}, {"$set": {"journal_id": journal_no}})
    
    await log_activity(
        db, user_id, user_name,
        "payment", "accounts_payable",
        f"Pembayaran hutang {ap.get('ap_no')} sebesar Rp {data.amount:,.0f}",
        request.client.host if request.client else "",
        ap.get("branch_id")
    )
    
    return {
        "payment_no": payment_no,
        "journal_no": journal_no,
        "new_outstanding": new_outstanding,
        "message": "Pembayaran berhasil dicatat"
    }


@router.get("/summary/dashboard")
async def get_ap_summary(
    user: dict = Depends(get_current_user)
):
    """Get AP summary for dashboard"""
    scope = await get_user_ap_scope(user)
    
    if not scope["can_view"]:
        raise HTTPException(status_code=403, detail="AKSES DITOLAK")
    
    query = {"status": {"$in": ["open", "partial", "overdue"]}}
    
    if scope["filter"]:
        query.update(scope["filter"])
    
    all_ap = await ap_collection.find(query, {"_id": 0}).to_list(10000)
    
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    summary = {
        "total_ap_count": len(all_ap),
        "total_outstanding": sum(ap.get("outstanding_amount", 0) for ap in all_ap),
        "overdue_count": len([ap for ap in all_ap if ap.get("due_date", "") < today]),
        "overdue_amount": sum(ap.get("outstanding_amount", 0) for ap in all_ap if ap.get("due_date", "") < today),
        "due_this_week": 0,
        "due_this_week_amount": 0
    }
    
    week_end = (datetime.now(timezone.utc) + timedelta(days=7)).strftime("%Y-%m-%d")
    for ap in all_ap:
        due = ap.get("due_date", "")
        if today <= due <= week_end:
            summary["due_this_week"] += 1
            summary["due_this_week_amount"] += ap.get("outstanding_amount", 0)
    
    return summary


# ==================== AUTO-CREATE FROM PURCHASE ====================

async def create_ap_from_purchase(purchase_data: Dict[str, Any], user: dict) -> Optional[str]:
    """
    Auto-create AP from credit purchase
    Called by purchase module when payment_type is credit
    """
    if purchase_data.get("payment_status") == "paid":
        return None
    
    payable_amount = purchase_data.get("outstanding_total", 0) or purchase_data.get("grand_total", 0)
    if payable_amount <= 0:
        return None
    
    supplier_id = purchase_data.get("supplier_id")
    if not supplier_id:
        return None
    
    supplier = await suppliers_collection.find_one({"id": supplier_id}, {"_id": 0})
    if not supplier:
        return None
    
    branch_id = purchase_data.get("branch_id", "")
    branch = await branches_collection.find_one({"id": branch_id}, {"_id": 0})
    branch_code = branch.get("code", "HQ") if branch else "HQ"
    
    payment_term = supplier.get("payment_term_days", 30)
    due_date = (datetime.now(timezone.utc) + timedelta(days=payment_term)).strftime("%Y-%m-%d")
    
    ap_no = await generate_ap_number(branch_code)
    user_id = user.get("user_id") or user.get("id")
    
    ap = {
        "id": str(uuid.uuid4()),
        "ap_no": ap_no,
        "ap_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "due_date": due_date,
        "supplier_id": supplier_id,
        "supplier_name": supplier.get("name", ""),
        "supplier_invoice_no": purchase_data.get("supplier_invoice_no", ""),
        "branch_id": branch_id,
        "source_type": "purchase",
        "source_id": purchase_data.get("id", ""),
        "source_no": purchase_data.get("purchase_no", ""),
        "currency": "IDR",
        "original_amount": payable_amount,
        "paid_amount": 0,
        "outstanding_amount": payable_amount,
        "status": "open",
        "payment_term_days": payment_term,
        "notes": f"Hutang dari pembelian {purchase_data.get('purchase_no', '')}",
        "created_by": user_id,
        "created_by_name": user.get("name", "System"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await ap_collection.insert_one(ap)
    
    return ap_no


# ==================== INIT ====================

@router.post("/init")
async def initialize_ap_system(user: dict = Depends(get_current_user)):
    """Initialize AP system"""
    
    await ap_collection.create_index("ap_no", unique=True)
    await ap_collection.create_index("supplier_id")
    await ap_collection.create_index("branch_id")
    await ap_collection.create_index("status")
    await ap_collection.create_index("due_date")
    await ap_payments.create_index("ap_id")
    await ap_payments.create_index("payment_date")
    
    return {
        "message": "AP system initialized",
        "indexes_created": True
    }
