# OCB TITAN ERP - MODUL OPERASIONAL SETORAN HARIAN
# Complete Daily Cash Deposit System with Strict Security & Accounting Integration

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, date
from database import db
from utils.auth import get_current_user
from routes.rbac_system import check_permission, log_activity, check_branch_access
import uuid

router = APIRouter(prefix="/api/deposit", tags=["Setoran Harian - Daily Cash Deposit"])

# Collections
deposits = db["deposits"]
deposit_details = db["deposit_details"]
sales_transactions = db["sales_transactions"]
account_mappings = db["deposit_account_mappings"]
journal_entries = db["journal_entries"]
users_collection = db["users"]
branches_collection = db["branches"]

# ==================== DEPOSIT STATUS ====================

DEPOSIT_STATUS = {
    "draft": {"name": "Draft", "color": "blue", "level": 0},
    "pending": {"name": "Menunggu Setor", "color": "yellow", "level": 1},
    "received": {"name": "Diterima", "color": "green", "level": 2},
    "verified": {"name": "Diverifikasi", "color": "green", "level": 3},
    "approved": {"name": "Approved", "color": "green", "level": 4},
    "posted": {"name": "Posted", "color": "green", "level": 5},
    "difference": {"name": "Selisih", "color": "red", "level": -1},
    "rejected": {"name": "Ditolak", "color": "red", "level": -2},
    "cancelled": {"name": "Batal", "color": "gray", "level": -3}
}

# ==================== DIFFERENCE STATUS ====================

DIFFERENCE_STATUS = {
    "match": {"name": "SESUAI", "color": "green"},
    "short": {"name": "SELISIH KURANG", "color": "red"},
    "over": {"name": "SELISIH LEBIH", "color": "yellow"}
}

# ==================== DEFAULT ACCOUNT MAPPING ====================

DEFAULT_ACCOUNT_MAPPING = {
    "kas_kecil_pusat": {"code": "1101", "name": "Kas Kecil Pusat"},
    "kas_cabang": {"code": "1102", "name": "Kas Cabang"},
    "kas_kasir": {"code": "1103", "name": "Kas Kasir"},
    "kas_dalam_perjalanan": {"code": "1104", "name": "Kas Dalam Perjalanan"},
    "piutang_karyawan": {"code": "1302", "name": "Piutang Karyawan"},
    "minus_kasir": {"code": "1303", "name": "Minus Kasir"},
    "selisih_kurang_kas": {"code": "6201", "name": "Selisih Kurang Kas"},
    "selisih_lebih_kas": {"code": "4201", "name": "Selisih Lebih Kas"},
    "beban_selisih_kas": {"code": "6202", "name": "Beban Selisih Kas"},
    "clearing_setoran": {"code": "2101", "name": "Clearing Setoran Harian"}
}

# ==================== PYDANTIC MODELS ====================

class DepositCreate(BaseModel):
    sales_date: str  # Tanggal penjualan yang akan disetor
    shift_id: str = ""
    notes: str = ""


class DepositUpdate(BaseModel):
    cash_received: float = 0  # Nominal cash fisik diterima
    difference_reason: str = ""  # Alasan selisih (wajib jika selisih != 0)
    admin_fee: float = 0  # Biaya admin/potongan
    notes: str = ""


class DepositVerify(BaseModel):
    verified: bool = True
    notes: str = ""


class DepositApprove(BaseModel):
    approved: bool = True
    notes: str = ""


class AccountMappingUpdate(BaseModel):
    account_code: str
    account_name: str


# ==================== SECURITY HELPERS ====================

async def get_user_deposit_scope(user: dict) -> Dict[str, Any]:
    """
    FAIL-SAFE: Determine user's deposit access scope
    Returns filter conditions and permissions
    """
    user_id = user.get("user_id") or user.get("id")
    role_code = user.get("role_code") or user.get("role")
    branch_id = user.get("branch_id")
    all_branches = user.get("all_branches", False)
    
    # Get user from DB for complete info
    db_user = await users_collection.find_one({"id": user_id}, {"_id": 0})
    if db_user:
        role_code = db_user.get("role_code") or role_code
        branch_id = db_user.get("branch_id") or branch_id
        all_branches = db_user.get("all_branches", False)
    
    # Get role info
    role = await db["roles"].find_one({"code": role_code}, {"_id": 0})
    role_level = role.get("level", 99) if role else 99
    inherit_all = role.get("inherit_all", False) if role else False
    
    # FAIL-SAFE: Default deny
    scope = {
        "can_view_own": False,
        "can_view_branch": False,
        "can_view_all": False,
        "can_create": False,
        "can_edit_own": False,
        "can_verify": False,
        "can_approve": False,
        "can_post": False,
        "user_id": user_id,
        "branch_id": branch_id,
        "role_level": role_level,
        "filter": {}
    }
    
    # PEMILIK / SUPER ADMIN = Full access
    if inherit_all or role_level <= 1:
        scope["can_view_own"] = True
        scope["can_view_branch"] = True
        scope["can_view_all"] = True
        scope["can_create"] = True
        scope["can_edit_own"] = True
        scope["can_verify"] = True
        scope["can_approve"] = True
        scope["can_post"] = True
        scope["filter"] = {}  # No filter = all data
        return scope
    
    # MANAGER / DIREKTUR (Level 2-3)
    if role_level <= 3:
        scope["can_view_own"] = True
        scope["can_view_branch"] = True
        scope["can_view_all"] = all_branches
        scope["can_create"] = True
        scope["can_edit_own"] = True
        scope["can_verify"] = True
        scope["can_approve"] = True
        scope["can_post"] = True
        if not all_branches:
            scope["filter"] = {"branch_id": branch_id}
        return scope
    
    # SUPERVISOR (Level 4)
    if role_level == 4:
        scope["can_view_own"] = True
        scope["can_view_branch"] = True
        scope["can_create"] = True
        scope["can_edit_own"] = True
        scope["can_verify"] = True
        scope["filter"] = {"branch_id": branch_id}
        return scope
    
    # ADMIN (Level 5)
    if role_level == 5:
        scope["can_view_own"] = True
        scope["can_view_branch"] = True
        scope["can_create"] = True
        scope["can_edit_own"] = True
        scope["filter"] = {"branch_id": branch_id}
        return scope
    
    # KASIR (Level 7) - ONLY OWN DATA
    if role_level >= 6:
        scope["can_view_own"] = True
        scope["can_create"] = True
        scope["can_edit_own"] = True
        scope["filter"] = {
            "cashier_id": user_id,
            "branch_id": branch_id
        }
        return scope
    
    return scope


async def validate_deposit_access(user: dict, deposit_id: str, action: str = "view") -> Dict[str, Any]:
    """
    FAIL-SAFE: Validate user can access specific deposit
    Returns deposit if allowed, raises 403 if not
    """
    scope = await get_user_deposit_scope(user)
    
    # Get deposit
    deposit = await deposits.find_one({"id": deposit_id}, {"_id": 0})
    if not deposit:
        raise HTTPException(status_code=404, detail="Setoran tidak ditemukan")
    
    user_id = scope["user_id"]
    branch_id = scope["branch_id"]
    
    # PEMILIK / SUPER ADMIN = Always allowed
    if scope["can_view_all"] and not scope["filter"]:
        return deposit
    
    # Check branch access
    if scope["filter"].get("branch_id"):
        if deposit.get("branch_id") != branch_id:
            raise HTTPException(
                status_code=403, 
                detail="AKSES DITOLAK. Anda tidak memiliki akses ke setoran cabang lain."
            )
    
    # Check own-data access for KASIR
    if scope["filter"].get("cashier_id"):
        if deposit.get("cashier_id") != user_id:
            raise HTTPException(
                status_code=403,
                detail="AKSES DITOLAK. Anda hanya dapat mengakses setoran milik Anda sendiri."
            )
    
    # Check action-specific permissions
    if action == "edit" and not scope["can_edit_own"]:
        raise HTTPException(status_code=403, detail="AKSES DITOLAK. Anda tidak dapat mengedit setoran.")
    
    if action == "verify" and not scope["can_verify"]:
        raise HTTPException(status_code=403, detail="AKSES DITOLAK. Anda tidak dapat memverifikasi setoran.")
    
    if action == "approve" and not scope["can_approve"]:
        raise HTTPException(status_code=403, detail="AKSES DITOLAK. Anda tidak dapat approve setoran.")
    
    if action == "post" and not scope["can_post"]:
        raise HTTPException(status_code=403, detail="AKSES DITOLAK. Anda tidak dapat posting setoran.")
    
    # Check edit status (only draft can be edited)
    if action == "edit" and deposit.get("status") not in ["draft", "pending"]:
        raise HTTPException(
            status_code=400, 
            detail="Setoran tidak dapat diedit karena sudah diverifikasi/approved."
        )
    
    return deposit


# ==================== GENERATE DEPOSIT NUMBER ====================

async def generate_deposit_number(branch_code: str = "HQ") -> str:
    """Generate unique deposit number: DEP-{BRANCH}-{YYYYMMDD}-{SEQ}"""
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    prefix = f"DEP-{branch_code}-{today}"
    
    # Find last sequence
    last = await deposits.find_one(
        {"deposit_number": {"$regex": f"^{prefix}"}},
        {"_id": 0, "deposit_number": 1},
        sort=[("deposit_number", -1)]
    )
    
    if last:
        try:
            seq = int(last["deposit_number"].split("-")[-1]) + 1
        except:
            seq = 1
    else:
        seq = 1
    
    return f"{prefix}-{seq:04d}"


# ==================== CALCULATE SALES SUMMARY ====================

async def calculate_sales_summary(
    cashier_id: str,
    branch_id: str,
    sales_date: str,
    shift_id: str = ""
) -> Dict[str, Any]:
    """
    Calculate sales summary from actual sales transactions
    NO MANUAL INPUT - All data from sales
    """
    # Build query
    query = {
        "cashier_id": cashier_id,
        "branch_id": branch_id,
        "transaction_date": sales_date,
        "status": {"$in": ["completed", "posted", "final"]},
        "deposit_id": {"$in": [None, ""]}  # Not yet deposited
    }
    
    if shift_id:
        query["shift_id"] = shift_id
    
    # Get transactions
    transactions = await sales_transactions.find(query, {"_id": 0}).to_list(1000)
    
    # Calculate summary
    summary = {
        "total_transactions": len(transactions),
        "gross_sales": 0,
        "total_discount": 0,
        "total_tax": 0,
        "net_sales": 0,
        "cash_received": 0,
        "cash_change": 0,
        "net_cash": 0,
        "transfer_amount": 0,
        "qris_amount": 0,
        "ewallet_amount": 0,
        "card_amount": 0,
        "credit_amount": 0,  # Piutang
        "void_amount": 0,
        "return_amount": 0,
        "cash_should_deposit": 0,
        "transactions": []
    }
    
    for trx in transactions:
        summary["gross_sales"] += trx.get("gross_amount", 0)
        summary["total_discount"] += trx.get("discount_amount", 0)
        summary["total_tax"] += trx.get("tax_amount", 0)
        summary["net_sales"] += trx.get("net_amount", 0)
        
        # Payment breakdown
        payments = trx.get("payments", {})
        summary["cash_received"] += payments.get("cash", 0)
        summary["cash_change"] += payments.get("change", 0)
        summary["transfer_amount"] += payments.get("transfer", 0)
        summary["qris_amount"] += payments.get("qris", 0)
        summary["ewallet_amount"] += payments.get("ewallet", 0)
        summary["card_amount"] += payments.get("card", 0)
        summary["credit_amount"] += payments.get("credit", 0)
        
        if trx.get("is_void"):
            summary["void_amount"] += trx.get("net_amount", 0)
        
        # Add transaction to list
        summary["transactions"].append({
            "id": trx.get("id"),
            "transaction_number": trx.get("transaction_number"),
            "transaction_date": trx.get("transaction_date"),
            "transaction_time": trx.get("transaction_time"),
            "customer_name": trx.get("customer_name", "-"),
            "gross_amount": trx.get("gross_amount", 0),
            "net_amount": trx.get("net_amount", 0),
            "cash": payments.get("cash", 0),
            "change": payments.get("change", 0),
            "transfer": payments.get("transfer", 0),
            "qris": payments.get("qris", 0),
            "ewallet": payments.get("ewallet", 0),
            "card": payments.get("card", 0),
            "credit": payments.get("credit", 0),
            "is_void": trx.get("is_void", False)
        })
    
    # Calculate net cash (cash received - change)
    summary["net_cash"] = summary["cash_received"] - summary["cash_change"]
    
    # Cash that should be deposited (only cash, not credit/transfer/etc)
    summary["cash_should_deposit"] = summary["net_cash"] - summary["void_amount"]
    
    return summary


# ==================== CREATE JOURNAL ENTRIES ====================

async def create_deposit_journal(
    deposit: Dict[str, Any],
    account_map: Dict[str, Dict],
    user: dict
) -> str:
    """
    Create journal entries for deposit
    Supports multiple scenarios with selisih handling
    """
    user_id = user.get("user_id") or user.get("id")
    user_name = user.get("name", "System")
    
    cash_should = deposit.get("cash_should_deposit", 0)
    cash_received = deposit.get("cash_received", 0)
    difference = deposit.get("difference_amount", 0)
    
    # Generate journal number
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    journal_number = f"JV-DEP-{today}-{uuid.uuid4().hex[:6].upper()}"
    
    entries = []
    
    # DEBIT: Kas Kecil Pusat (actual received)
    entries.append({
        "account_code": account_map.get("kas_kecil_pusat", {}).get("code", "1101"),
        "account_name": account_map.get("kas_kecil_pusat", {}).get("name", "Kas Kecil Pusat"),
        "debit": cash_received,
        "credit": 0,
        "description": f"Setoran dari {deposit.get('branch_name', '')} - {deposit.get('cashier_name', '')}"
    })
    
    # Handle difference
    if difference < 0:
        # SELISIH KURANG - Debit to employee receivable / minus kasir
        entries.append({
            "account_code": account_map.get("selisih_kurang_kas", {}).get("code", "6201"),
            "account_name": account_map.get("selisih_kurang_kas", {}).get("name", "Selisih Kurang Kas"),
            "debit": abs(difference),
            "credit": 0,
            "description": f"Selisih kurang setoran {deposit.get('deposit_number')}"
        })
    elif difference > 0:
        # SELISIH LEBIH - Credit to selisih lebih kas
        entries.append({
            "account_code": account_map.get("selisih_lebih_kas", {}).get("code", "4201"),
            "account_name": account_map.get("selisih_lebih_kas", {}).get("name", "Selisih Lebih Kas"),
            "debit": 0,
            "credit": abs(difference),
            "description": f"Selisih lebih setoran {deposit.get('deposit_number')}"
        })
    
    # CREDIT: Kas Cabang / Kas Kasir (should deposit amount)
    entries.append({
        "account_code": account_map.get("kas_cabang", {}).get("code", "1102"),
        "account_name": account_map.get("kas_cabang", {}).get("name", "Kas Cabang"),
        "debit": 0,
        "credit": cash_should,
        "description": f"Setoran dari kasir {deposit.get('cashier_name', '')}"
    })
    
    # Calculate totals
    total_debit = sum(e["debit"] for e in entries)
    total_credit = sum(e["credit"] for e in entries)
    
    # Create journal
    journal = {
        "id": str(uuid.uuid4()),
        "journal_number": journal_number,
        "journal_date": datetime.now(timezone.utc).isoformat(),
        "reference_type": "deposit",
        "reference_id": deposit.get("id"),
        "reference_number": deposit.get("deposit_number"),
        "description": f"Setoran Harian {deposit.get('deposit_number')} - {deposit.get('branch_name')}",
        "entries": entries,
        "total_debit": total_debit,
        "total_credit": total_credit,
        "is_balanced": abs(total_debit - total_credit) < 0.01,
        "status": "posted",
        "created_by": user_id,
        "created_by_name": user_name,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await journal_entries.insert_one(journal)
    
    return journal_number


# ==================== API ENDPOINTS ====================

@router.get("/list")
async def list_deposits(
    keyword: str = "",
    start_date: str = "",
    end_date: str = "",
    branch_id: str = "",
    cashier_id: str = "",
    shift_id: str = "",
    status: str = "",
    has_difference: str = "",
    skip: int = 0,
    limit: int = 50,
    request: Request = None,
    user: dict = Depends(get_current_user)
):
    """
    List deposits with ACCESS CONTROL based on user role
    FAIL-SAFE: Users can only see their authorized data
    """
    scope = await get_user_deposit_scope(user)
    
    # FAIL-SAFE: If no permissions at all
    if not scope["can_view_own"]:
        raise HTTPException(
            status_code=403,
            detail="AKSES DITOLAK. USER TIDAK MEMILIKI HAK AKSES SETORAN HARIAN."
        )
    
    # Build query with scope filter
    query = {}
    
    # Apply scope filter first (CRITICAL for security)
    if scope["filter"]:
        query.update(scope["filter"])
    
    # Additional filters (only if user has broader access)
    if keyword:
        query["$or"] = [
            {"deposit_number": {"$regex": keyword, "$options": "i"}},
            {"cashier_name": {"$regex": keyword, "$options": "i"}}
        ]
    
    if start_date:
        query["deposit_date"] = {"$gte": start_date}
    if end_date:
        if "deposit_date" in query:
            query["deposit_date"]["$lte"] = end_date
        else:
            query["deposit_date"] = {"$lte": end_date}
    
    # Branch filter (only if user can view all branches)
    if branch_id and scope["can_view_all"]:
        query["branch_id"] = branch_id
    
    # Cashier filter (only if user can view branch)
    if cashier_id and scope["can_view_branch"]:
        query["cashier_id"] = cashier_id
    
    if shift_id:
        query["shift_id"] = shift_id
    
    if status:
        query["status"] = status
    
    if has_difference == "yes":
        query["difference_amount"] = {"$ne": 0}
    elif has_difference == "no":
        query["difference_amount"] = 0
    
    # Execute query
    total = await deposits.count_documents(query)
    items = await deposits.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    return {
        "deposits": items,
        "total": total,
        "scope": {
            "can_view_own": scope["can_view_own"],
            "can_view_branch": scope["can_view_branch"],
            "can_view_all": scope["can_view_all"],
            "filter_applied": bool(scope["filter"])
        }
    }


@router.get("/my-sales")
async def get_my_sales_for_deposit(
    sales_date: str,
    shift_id: str = "",
    request: Request = None,
    user: dict = Depends(get_current_user)
):
    """
    Get sales transactions for current user to create deposit
    KASIR: Only their own sales
    This is the ONLY way to get sales data for deposit - NO MANUAL INPUT
    """
    scope = await get_user_deposit_scope(user)
    user_id = scope["user_id"]
    branch_id = scope["branch_id"]
    
    if not branch_id:
        raise HTTPException(
            status_code=400,
            detail="User tidak memiliki cabang yang di-assign"
        )
    
    # Calculate summary from actual sales
    summary = await calculate_sales_summary(user_id, branch_id, sales_date, shift_id)
    
    # Get branch and user info
    branch = await branches_collection.find_one({"id": branch_id}, {"_id": 0, "name": 1, "code": 1})
    db_user = await users_collection.find_one({"id": user_id}, {"_id": 0, "name": 1})
    
    return {
        "sales_date": sales_date,
        "shift_id": shift_id,
        "branch_id": branch_id,
        "branch_name": branch.get("name") if branch else "",
        "branch_code": branch.get("code") if branch else "",
        "cashier_id": user_id,
        "cashier_name": db_user.get("name") if db_user else "",
        "summary": summary
    }


@router.post("/create")
async def create_deposit(
    data: DepositCreate,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """
    Create new deposit
    KASIR: Automatically locked to their own data
    NO manual transaction input - pulls from actual sales
    """
    scope = await get_user_deposit_scope(user)
    
    if not scope["can_create"]:
        raise HTTPException(status_code=403, detail="AKSES DITOLAK. Anda tidak dapat membuat setoran.")
    
    user_id = scope["user_id"]
    branch_id = scope["branch_id"]
    user_name = user.get("name", "")
    
    if not branch_id:
        raise HTTPException(status_code=400, detail="User tidak memiliki cabang yang di-assign")
    
    # Get branch info
    branch = await branches_collection.find_one({"id": branch_id}, {"_id": 0})
    branch_name = branch.get("name", "") if branch else ""
    branch_code = branch.get("code", "HQ") if branch else "HQ"
    
    # Calculate sales summary
    summary = await calculate_sales_summary(user_id, branch_id, data.sales_date, data.shift_id)
    
    if summary["total_transactions"] == 0:
        raise HTTPException(
            status_code=400,
            detail="Tidak ada transaksi penjualan untuk tanggal tersebut yang belum disetor"
        )
    
    # Generate deposit number
    deposit_number = await generate_deposit_number(branch_code)
    
    # Create deposit
    deposit = {
        "id": str(uuid.uuid4()),
        "deposit_number": deposit_number,
        "deposit_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "sales_date": data.sales_date,
        "branch_id": branch_id,
        "branch_name": branch_name,
        "shift_id": data.shift_id,
        "cashier_id": user_id,
        "cashier_name": user_name,
        
        # Summary from actual sales (NO MANUAL INPUT)
        "total_transactions": summary["total_transactions"],
        "gross_sales": summary["gross_sales"],
        "total_discount": summary["total_discount"],
        "total_tax": summary["total_tax"],
        "net_sales": summary["net_sales"],
        "cash_received_sales": summary["cash_received"],
        "cash_change": summary["cash_change"],
        "net_cash": summary["net_cash"],
        "transfer_amount": summary["transfer_amount"],
        "qris_amount": summary["qris_amount"],
        "ewallet_amount": summary["ewallet_amount"],
        "card_amount": summary["card_amount"],
        "credit_amount": summary["credit_amount"],
        "void_amount": summary["void_amount"],
        "return_amount": summary["return_amount"],
        "cash_should_deposit": summary["cash_should_deposit"],
        
        # Manual input fields
        "cash_received": 0,  # Nominal fisik diterima - input manual
        "admin_fee": 0,
        "difference_amount": 0,
        "difference_percent": 0,
        "difference_status": "match",
        "difference_reason": "",
        
        # Status
        "status": "draft",
        "verification_status": "pending",
        "approval_status": "pending",
        
        # Receiver info
        "receiver_id": None,
        "receiver_name": None,
        "received_at": None,
        
        # Verification info
        "verified_by": None,
        "verified_by_name": None,
        "verified_at": None,
        "verification_notes": "",
        
        # Approval info
        "approved_by": None,
        "approved_by_name": None,
        "approved_at": None,
        "approval_notes": "",
        
        # Journal
        "journal_number": None,
        "posted_at": None,
        
        "notes": data.notes,
        "created_by": user_id,
        "created_by_name": user_name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_by": None,
        "updated_at": None
    }
    
    await deposits.insert_one(deposit)
    
    # Save transaction details
    for trx in summary["transactions"]:
        detail = {
            "id": str(uuid.uuid4()),
            "deposit_id": deposit["id"],
            "transaction_id": trx["id"],
            "transaction_number": trx["transaction_number"],
            "transaction_date": trx["transaction_date"],
            "transaction_time": trx.get("transaction_time", ""),
            "customer_name": trx.get("customer_name", "-"),
            "gross_amount": trx["gross_amount"],
            "net_amount": trx["net_amount"],
            "cash": trx.get("cash", 0),
            "change": trx.get("change", 0),
            "transfer": trx.get("transfer", 0),
            "qris": trx.get("qris", 0),
            "ewallet": trx.get("ewallet", 0),
            "card": trx.get("card", 0),
            "credit": trx.get("credit", 0),
            "is_void": trx.get("is_void", False),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await deposit_details.insert_one(detail)
        
        # Mark transaction as deposited
        await sales_transactions.update_one(
            {"id": trx["id"]},
            {"$set": {
                "deposit_id": deposit["id"],
                "deposit_number": deposit_number,
                "deposit_status": "draft"
            }}
        )
    
    # Log activity
    await log_activity(
        db, user_id, user_name,
        "create", "setoran_harian",
        f"Membuat setoran {deposit_number} untuk tanggal {data.sales_date}",
        request.client.host if request.client else "",
        branch_id
    )
    
    return {
        "id": deposit["id"],
        "deposit_number": deposit_number,
        "message": "Setoran berhasil dibuat"
    }


@router.get("/{deposit_id}")
async def get_deposit(
    deposit_id: str,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """
    Get deposit detail with ACCESS CONTROL
    """
    deposit = await validate_deposit_access(user, deposit_id, "view")
    
    # Get transaction details
    details = await deposit_details.find(
        {"deposit_id": deposit_id}, {"_id": 0}
    ).to_list(1000)
    
    deposit["transactions"] = details
    
    return deposit


@router.put("/{deposit_id}")
async def update_deposit(
    deposit_id: str,
    data: DepositUpdate,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """
    Update deposit (cash received, reason, etc)
    SECURITY: Only own deposit, only draft status
    """
    deposit = await validate_deposit_access(user, deposit_id, "edit")
    
    user_id = user.get("user_id") or user.get("id")
    user_name = user.get("name", "")
    
    # Calculate difference
    cash_should = deposit.get("cash_should_deposit", 0)
    cash_received = data.cash_received
    difference = cash_received - cash_should
    difference_percent = (abs(difference) / cash_should * 100) if cash_should > 0 else 0
    
    # Determine difference status
    if abs(difference) < 0.01:
        difference_status = "match"
    elif difference < 0:
        difference_status = "short"
    else:
        difference_status = "over"
    
    # Validate: If difference exists, reason is required
    if difference_status != "match" and not data.difference_reason.strip():
        raise HTTPException(
            status_code=400,
            detail="Alasan selisih WAJIB diisi karena ada selisih antara nominal fisik dan seharusnya"
        )
    
    # Update deposit
    update_data = {
        "cash_received": cash_received,
        "admin_fee": data.admin_fee,
        "difference_amount": difference,
        "difference_percent": round(difference_percent, 2),
        "difference_status": difference_status,
        "difference_reason": data.difference_reason,
        "notes": data.notes,
        "status": "pending" if deposit.get("status") == "draft" else deposit.get("status"),
        "updated_by": user_id,
        "updated_by_name": user_name,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await deposits.update_one({"id": deposit_id}, {"$set": update_data})
    
    # Log activity
    await log_activity(
        db, user_id, user_name,
        "edit", "setoran_harian",
        f"Update setoran {deposit.get('deposit_number')}: Cash Rp {cash_received:,.0f}, Selisih Rp {difference:,.0f}",
        request.client.host if request.client else "",
        deposit.get("branch_id"),
        severity="warning" if difference_status != "match" else "normal"
    )
    
    return {"message": "Setoran berhasil diupdate", "difference_status": difference_status}


@router.post("/{deposit_id}/receive")
async def receive_deposit(
    deposit_id: str,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """
    Mark deposit as received by pusat
    """
    deposit = await validate_deposit_access(user, deposit_id, "verify")
    
    if deposit.get("status") not in ["pending", "draft"]:
        raise HTTPException(status_code=400, detail="Setoran tidak dalam status menunggu setor")
    
    user_id = user.get("user_id") or user.get("id")
    user_name = user.get("name", "")
    
    await deposits.update_one(
        {"id": deposit_id},
        {"$set": {
            "status": "received",
            "receiver_id": user_id,
            "receiver_name": user_name,
            "received_at": datetime.now(timezone.utc).isoformat(),
            "updated_by": user_id,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    await log_activity(
        db, user_id, user_name,
        "edit", "setoran_harian",
        f"Menerima setoran {deposit.get('deposit_number')}",
        request.client.host if request.client else "",
        deposit.get("branch_id")
    )
    
    return {"message": "Setoran berhasil diterima"}


@router.post("/{deposit_id}/verify")
async def verify_deposit(
    deposit_id: str,
    data: DepositVerify,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """
    Verify deposit (SUPERVISOR level)
    """
    deposit = await validate_deposit_access(user, deposit_id, "verify")
    
    if deposit.get("status") not in ["received", "pending"]:
        raise HTTPException(status_code=400, detail="Setoran belum diterima atau sudah diverifikasi")
    
    user_id = user.get("user_id") or user.get("id")
    user_name = user.get("name", "")
    
    new_status = "verified" if data.verified else "rejected"
    
    await deposits.update_one(
        {"id": deposit_id},
        {"$set": {
            "status": new_status,
            "verification_status": "verified" if data.verified else "rejected",
            "verified_by": user_id,
            "verified_by_name": user_name,
            "verified_at": datetime.now(timezone.utc).isoformat(),
            "verification_notes": data.notes,
            "updated_by": user_id,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    await log_activity(
        db, user_id, user_name,
        "verify" if data.verified else "reject", "setoran_harian",
        f"{'Verifikasi' if data.verified else 'Tolak'} setoran {deposit.get('deposit_number')}",
        request.client.host if request.client else "",
        deposit.get("branch_id"),
        severity="normal" if data.verified else "warning"
    )
    
    return {"message": f"Setoran berhasil {'diverifikasi' if data.verified else 'ditolak'}"}


@router.post("/{deposit_id}/approve")
async def approve_deposit(
    deposit_id: str,
    data: DepositApprove,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """
    Approve deposit (MANAGER/OWNER level)
    """
    deposit = await validate_deposit_access(user, deposit_id, "approve")
    
    if deposit.get("status") != "verified":
        raise HTTPException(status_code=400, detail="Setoran belum diverifikasi")
    
    user_id = user.get("user_id") or user.get("id")
    user_name = user.get("name", "")
    
    new_status = "approved" if data.approved else "rejected"
    
    await deposits.update_one(
        {"id": deposit_id},
        {"$set": {
            "status": new_status,
            "approval_status": "approved" if data.approved else "rejected",
            "approved_by": user_id,
            "approved_by_name": user_name,
            "approved_at": datetime.now(timezone.utc).isoformat(),
            "approval_notes": data.notes,
            "updated_by": user_id,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    await log_activity(
        db, user_id, user_name,
        "approve" if data.approved else "reject", "setoran_harian",
        f"{'Approve' if data.approved else 'Tolak'} setoran {deposit.get('deposit_number')}",
        request.client.host if request.client else "",
        deposit.get("branch_id"),
        severity="normal" if data.approved else "warning"
    )
    
    return {"message": f"Setoran berhasil {'diapprove' if data.approved else 'ditolak'}"}


@router.post("/{deposit_id}/post")
async def post_deposit(
    deposit_id: str,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """
    Post deposit to accounting journal
    Creates journal entries: Kas Kecil Pusat, Selisih handling
    """
    deposit = await validate_deposit_access(user, deposit_id, "post")
    
    if deposit.get("status") != "approved":
        raise HTTPException(status_code=400, detail="Setoran belum diapprove")
    
    user_id = user.get("user_id") or user.get("id")
    user_name = user.get("name", "")
    
    # Get account mapping
    mapping = await account_mappings.find_one({"branch_id": deposit.get("branch_id")}, {"_id": 0})
    if not mapping:
        mapping = await account_mappings.find_one({"branch_id": "default"}, {"_id": 0})
    if not mapping:
        mapping = {"accounts": DEFAULT_ACCOUNT_MAPPING}
    
    account_map = mapping.get("accounts", DEFAULT_ACCOUNT_MAPPING)
    
    # Create journal entries
    journal_number = await create_deposit_journal(deposit, account_map, user)
    
    # Update deposit status
    await deposits.update_one(
        {"id": deposit_id},
        {"$set": {
            "status": "posted",
            "journal_number": journal_number,
            "posted_at": datetime.now(timezone.utc).isoformat(),
            "updated_by": user_id,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Update transaction deposit status
    await sales_transactions.update_many(
        {"deposit_id": deposit_id},
        {"$set": {"deposit_status": "posted"}}
    )
    
    await log_activity(
        db, user_id, user_name,
        "post", "setoran_harian",
        f"Posting setoran {deposit.get('deposit_number')} ke jurnal {journal_number}",
        request.client.host if request.client else "",
        deposit.get("branch_id"),
        severity="critical"
    )
    
    return {
        "message": "Setoran berhasil diposting ke jurnal akuntansi",
        "journal_number": journal_number
    }


@router.post("/{deposit_id}/cancel")
async def cancel_deposit(
    deposit_id: str,
    reason: str = "",
    request: Request = None,
    user: dict = Depends(get_current_user)
):
    """
    Cancel deposit (only draft/pending)
    """
    deposit = await validate_deposit_access(user, deposit_id, "edit")
    
    if deposit.get("status") not in ["draft", "pending"]:
        raise HTTPException(status_code=400, detail="Hanya setoran draft/pending yang dapat dibatalkan")
    
    user_id = user.get("user_id") or user.get("id")
    user_name = user.get("name", "")
    
    await deposits.update_one(
        {"id": deposit_id},
        {"$set": {
            "status": "cancelled",
            "cancel_reason": reason,
            "cancelled_by": user_id,
            "cancelled_at": datetime.now(timezone.utc).isoformat(),
            "updated_by": user_id,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Release transactions back
    await sales_transactions.update_many(
        {"deposit_id": deposit_id},
        {"$set": {
            "deposit_id": None,
            "deposit_number": None,
            "deposit_status": None
        }}
    )
    
    await log_activity(
        db, user_id, user_name,
        "cancel", "setoran_harian",
        f"Batalkan setoran {deposit.get('deposit_number')}: {reason}",
        request.client.host if request.client else "",
        deposit.get("branch_id"),
        severity="warning"
    )
    
    return {"message": "Setoran berhasil dibatalkan"}


# ==================== ACCOUNT MAPPING ====================

@router.get("/settings/account-mapping")
async def get_account_mapping(
    branch_id: str = "default",
    user: dict = Depends(get_current_user)
):
    """Get account mapping for deposit journal"""
    mapping = await account_mappings.find_one({"branch_id": branch_id}, {"_id": 0})
    if not mapping:
        mapping = {"branch_id": branch_id, "accounts": DEFAULT_ACCOUNT_MAPPING}
    return mapping


@router.put("/settings/account-mapping")
async def update_account_mapping(
    branch_id: str,
    account_key: str,
    data: AccountMappingUpdate,
    user: dict = Depends(get_current_user)
):
    """Update account mapping (requires permission)"""
    scope = await get_user_deposit_scope(user)
    if not scope["can_approve"]:
        raise HTTPException(status_code=403, detail="AKSES DITOLAK")
    
    await account_mappings.update_one(
        {"branch_id": branch_id},
        {
            "$set": {
                f"accounts.{account_key}": {
                    "code": data.account_code,
                    "name": data.account_name
                },
                "updated_at": datetime.now(timezone.utc).isoformat()
            },
            "$setOnInsert": {
                "id": str(uuid.uuid4()),
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        },
        upsert=True
    )
    
    return {"message": "Account mapping berhasil diupdate"}


# ==================== RECONCILIATION ====================

@router.get("/reconciliation/summary")
async def get_reconciliation_summary(
    start_date: str,
    end_date: str,
    branch_id: str = "",
    request: Request = None,
    user: dict = Depends(get_current_user)
):
    """
    Get reconciliation summary: sales vs deposits
    """
    scope = await get_user_deposit_scope(user)
    
    query = {
        "sales_date": {"$gte": start_date, "$lte": end_date}
    }
    
    if scope["filter"].get("branch_id"):
        query["branch_id"] = scope["filter"]["branch_id"]
    elif branch_id and scope["can_view_all"]:
        query["branch_id"] = branch_id
    
    # Get deposits
    deposit_list = await deposits.find(query, {"_id": 0}).to_list(1000)
    
    # Calculate summary
    summary = {
        "total_deposits": len(deposit_list),
        "total_should_deposit": sum(d.get("cash_should_deposit", 0) for d in deposit_list),
        "total_received": sum(d.get("cash_received", 0) for d in deposit_list),
        "total_difference": sum(d.get("difference_amount", 0) for d in deposit_list),
        "deposits_with_difference": len([d for d in deposit_list if d.get("difference_amount", 0) != 0]),
        "by_status": {},
        "by_difference_status": {}
    }
    
    # Group by status
    for d in deposit_list:
        status = d.get("status", "unknown")
        if status not in summary["by_status"]:
            summary["by_status"][status] = {"count": 0, "amount": 0}
        summary["by_status"][status]["count"] += 1
        summary["by_status"][status]["amount"] += d.get("cash_received", 0)
        
        diff_status = d.get("difference_status", "unknown")
        if diff_status not in summary["by_difference_status"]:
            summary["by_difference_status"][diff_status] = {"count": 0, "amount": 0}
        summary["by_difference_status"][diff_status]["count"] += 1
        summary["by_difference_status"][diff_status]["amount"] += d.get("difference_amount", 0)
    
    return summary


@router.get("/reconciliation/pending-sales")
async def get_pending_sales(
    sales_date: str = "",
    branch_id: str = "",
    request: Request = None,
    user: dict = Depends(get_current_user)
):
    """
    Get sales transactions not yet deposited
    """
    scope = await get_user_deposit_scope(user)
    
    query = {
        "status": {"$in": ["completed", "posted", "final"]},
        "deposit_id": {"$in": [None, ""]}
    }
    
    if scope["filter"].get("cashier_id"):
        query["cashier_id"] = scope["filter"]["cashier_id"]
    if scope["filter"].get("branch_id"):
        query["branch_id"] = scope["filter"]["branch_id"]
    elif branch_id and scope["can_view_all"]:
        query["branch_id"] = branch_id
    
    if sales_date:
        query["transaction_date"] = sales_date
    
    transactions = await sales_transactions.find(query, {"_id": 0}).to_list(1000)
    
    total_pending = sum(t.get("payments", {}).get("cash", 0) - t.get("payments", {}).get("change", 0) for t in transactions)
    
    return {
        "transactions": transactions,
        "total_pending": total_pending,
        "count": len(transactions)
    }


# ==================== DASHBOARD ====================

@router.get("/dashboard/summary")
async def get_deposit_dashboard(
    request: Request = None,
    user: dict = Depends(get_current_user)
):
    """
    Dashboard summary for deposit monitoring
    """
    scope = await get_user_deposit_scope(user)
    
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Build query with scope
    base_query = {}
    if scope["filter"]:
        base_query.update(scope["filter"])
    
    # Pending deposits
    pending_query = {**base_query, "status": {"$in": ["draft", "pending"]}}
    pending_count = await deposits.count_documents(pending_query)
    
    # Pending verification
    verify_query = {**base_query, "status": "received"}
    verify_count = await deposits.count_documents(verify_query)
    
    # Pending approval
    approve_query = {**base_query, "status": "verified"}
    approve_count = await deposits.count_documents(approve_query)
    
    # With difference
    diff_query = {**base_query, "difference_amount": {"$ne": 0}}
    diff_count = await deposits.count_documents(diff_query)
    
    # Today's deposits
    today_query = {**base_query, "deposit_date": today}
    today_deposits = await deposits.find(today_query, {"_id": 0}).to_list(100)
    
    today_amount = sum(d.get("cash_received", 0) for d in today_deposits)
    today_difference = sum(d.get("difference_amount", 0) for d in today_deposits)
    
    return {
        "pending_deposit": pending_count,
        "pending_verification": verify_count,
        "pending_approval": approve_count,
        "with_difference": diff_count,
        "today": {
            "count": len(today_deposits),
            "amount": today_amount,
            "difference": today_difference
        },
        "scope": {
            "view_own": scope["can_view_own"],
            "view_branch": scope["can_view_branch"],
            "view_all": scope["can_view_all"]
        }
    }


# ==================== INIT ====================

@router.post("/init")
async def initialize_deposit_system(user: dict = Depends(get_current_user)):
    """Initialize deposit system with default account mappings"""
    
    # Create default account mapping
    existing = await account_mappings.find_one({"branch_id": "default"})
    if not existing:
        await account_mappings.insert_one({
            "id": str(uuid.uuid4()),
            "branch_id": "default",
            "accounts": DEFAULT_ACCOUNT_MAPPING,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    
    # Create indexes
    await deposits.create_index("deposit_number", unique=True)
    await deposits.create_index("cashier_id")
    await deposits.create_index("branch_id")
    await deposits.create_index("status")
    await deposits.create_index("sales_date")
    await deposit_details.create_index("deposit_id")
    await deposit_details.create_index("transaction_id")
    
    return {
        "message": "Deposit system initialized",
        "default_accounts": list(DEFAULT_ACCOUNT_MAPPING.keys())
    }


@router.post("/seed-sales")
async def seed_sample_sales(
    count: int = Query(default=10, ge=1, le=50),
    sales_date: str = Query(default=""),
    request: Request = None,
    user: dict = Depends(get_current_user)
):
    """
    Seed sample sales transactions for testing deposit system
    Creates realistic POS transactions with various payment methods
    """
    import random
    
    user_id = user.get("user_id") or user.get("id")
    user_name = user.get("name", "Kasir Test")
    
    # Get user's branch
    db_user = await users_collection.find_one({"id": user_id}, {"_id": 0})
    branch_id = db_user.get("branch_id") if db_user else None
    
    if not branch_id:
        # Get first available branch
        branch = await branches_collection.find_one({}, {"_id": 0, "id": 1, "name": 1, "code": 1})
        if branch:
            branch_id = branch.get("id")
            branch_name = branch.get("name", "Cabang Default")
            branch_code = branch.get("code", "HQ")
        else:
            branch_id = "branch-default"
            branch_name = "Cabang Default"
            branch_code = "HQ"
    else:
        branch = await branches_collection.find_one({"id": branch_id}, {"_id": 0})
        branch_name = branch.get("name", "") if branch else "Cabang"
        branch_code = branch.get("code", "HQ") if branch else "HQ"
    
    # Use provided date or today
    if not sales_date:
        sales_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Sample products for transactions
    sample_items = [
        {"name": "Produk A", "price": 25000, "qty_range": (1, 5)},
        {"name": "Produk B", "price": 50000, "qty_range": (1, 3)},
        {"name": "Produk C", "price": 15000, "qty_range": (1, 10)},
        {"name": "Produk D", "price": 100000, "qty_range": (1, 2)},
        {"name": "Produk E", "price": 75000, "qty_range": (1, 3)},
        {"name": "Produk F", "price": 30000, "qty_range": (2, 8)},
    ]
    
    # Payment method distribution
    payment_methods = ["cash", "cash", "cash", "transfer", "qris", "ewallet"]
    
    created_transactions = []
    
    for i in range(count):
        # Generate transaction number
        seq = i + 1
        trx_number = f"POS-{branch_code}-{sales_date.replace('-', '')}-{seq:04d}"
        
        # Random items (1-4 items per transaction)
        num_items = random.randint(1, 4)
        selected_items = random.sample(sample_items, min(num_items, len(sample_items)))
        
        items = []
        gross_amount = 0
        
        for item in selected_items:
            qty = random.randint(*item["qty_range"])
            subtotal = item["price"] * qty
            gross_amount += subtotal
            items.append({
                "item_name": item["name"],
                "qty": qty,
                "price": item["price"],
                "subtotal": subtotal
            })
        
        # Random discount (0-10%)
        discount_percent = random.choice([0, 0, 0, 5, 10])
        discount_amount = gross_amount * discount_percent / 100
        
        # Tax (11%)
        tax_amount = (gross_amount - discount_amount) * 0.11
        net_amount = gross_amount - discount_amount + tax_amount
        
        # Payment method
        payment_method = random.choice(payment_methods)
        
        # Build payment info
        payments = {
            "cash": 0,
            "change": 0,
            "transfer": 0,
            "qris": 0,
            "ewallet": 0,
            "card": 0,
            "credit": 0
        }
        
        if payment_method == "cash":
            # Round up for cash
            cash_given = ((int(net_amount) // 10000) + 1) * 10000
            payments["cash"] = cash_given
            payments["change"] = cash_given - net_amount
        elif payment_method == "transfer":
            payments["transfer"] = net_amount
        elif payment_method == "qris":
            payments["qris"] = net_amount
        elif payment_method == "ewallet":
            payments["ewallet"] = net_amount
        
        # Generate random time
        hour = random.randint(8, 21)
        minute = random.randint(0, 59)
        trx_time = f"{hour:02d}:{minute:02d}:00"
        
        # Create transaction
        transaction = {
            "id": str(uuid.uuid4()),
            "transaction_number": trx_number,
            "transaction_date": sales_date,
            "transaction_time": trx_time,
            "branch_id": branch_id,
            "branch_name": branch_name,
            "cashier_id": user_id,
            "cashier_name": user_name,
            "customer_name": f"Pelanggan {random.randint(1, 100)}",
            "items": items,
            "gross_amount": gross_amount,
            "discount_percent": discount_percent,
            "discount_amount": discount_amount,
            "tax_percent": 11,
            "tax_amount": round(tax_amount, 2),
            "net_amount": round(net_amount, 2),
            "payment_method": payment_method,
            "payments": payments,
            "status": "completed",
            "is_void": False,
            "deposit_id": None,
            "deposit_number": None,
            "deposit_status": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": user_id
        }
        
        await sales_transactions.insert_one(transaction)
        created_transactions.append({
            "id": transaction["id"],
            "number": trx_number,
            "net_amount": round(net_amount, 2),
            "payment_method": payment_method
        })
    
    # Calculate summary
    total_cash = sum(t["net_amount"] for t in created_transactions if t["payment_method"] == "cash")
    total_non_cash = sum(t["net_amount"] for t in created_transactions if t["payment_method"] != "cash")
    
    return {
        "message": f"Berhasil membuat {count} transaksi penjualan sample",
        "sales_date": sales_date,
        "branch_id": branch_id,
        "branch_name": branch_name,
        "cashier_id": user_id,
        "cashier_name": user_name,
        "transactions": created_transactions,
        "summary": {
            "total_transactions": count,
            "total_cash": round(total_cash, 2),
            "total_non_cash": round(total_non_cash, 2),
            "total_all": round(total_cash + total_non_cash, 2)
        }
    }
