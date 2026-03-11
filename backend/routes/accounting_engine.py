# OCB TITAN ERP - ACCOUNTING ENGINE
# Enhanced accounting with configurable account mapping and auto-journal

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from database import db
from utils.auth import get_current_user
from routes.rbac_system import check_permission, log_activity
import uuid

router = APIRouter(prefix="/api/accounting", tags=["Accounting Engine"])

# Collections
chart_of_accounts = db["chart_of_accounts"]
account_mappings = db["account_mapping_settings"]
journal_entries = db["journal_entries"]
fiscal_periods = db["fiscal_periods"]
branches_collection = db["branches"]

# ==================== DEFAULT CHART OF ACCOUNTS ====================
DEFAULT_ACCOUNTS = {
    # ASSETS
    "1101": {"name": "Kas", "type": "asset", "category": "current_asset"},
    "1102": {"name": "Bank", "type": "asset", "category": "current_asset"},
    "1103": {"name": "Kas Kecil Pusat", "type": "asset", "category": "current_asset"},
    "1104": {"name": "Kas Cabang", "type": "asset", "category": "current_asset"},
    "1105": {"name": "Kas Kasir", "type": "asset", "category": "current_asset"},
    "1106": {"name": "Kas Dalam Perjalanan", "type": "asset", "category": "current_asset"},
    "1201": {"name": "Piutang Dagang", "type": "asset", "category": "current_asset"},
    "1202": {"name": "Piutang Karyawan", "type": "asset", "category": "current_asset"},
    "1301": {"name": "Persediaan Barang Dagang", "type": "asset", "category": "current_asset"},
    "1401": {"name": "Uang Muka Pembelian", "type": "asset", "category": "current_asset"},
    "1501": {"name": "Pajak Masukan", "type": "asset", "category": "current_asset"},
    
    # LIABILITIES
    "2101": {"name": "Hutang Dagang", "type": "liability", "category": "current_liability"},
    "2102": {"name": "Hutang Bank", "type": "liability", "category": "current_liability"},
    "2201": {"name": "Pajak Keluaran", "type": "liability", "category": "current_liability"},
    "2202": {"name": "Hutang Pajak", "type": "liability", "category": "current_liability"},
    
    # EQUITY
    "3101": {"name": "Modal Disetor", "type": "equity", "category": "equity"},
    "3102": {"name": "Laba Ditahan", "type": "equity", "category": "equity"},
    
    # REVENUE
    "4101": {"name": "Penjualan", "type": "revenue", "category": "operating_revenue"},
    "4102": {"name": "Diskon Penjualan", "type": "revenue", "category": "operating_revenue"},
    "4103": {"name": "Retur Penjualan", "type": "revenue", "category": "operating_revenue"},
    "4201": {"name": "Selisih Lebih Kas", "type": "revenue", "category": "other_revenue"},
    "4202": {"name": "Pendapatan Lain-lain", "type": "revenue", "category": "other_revenue"},
    
    # COST OF GOODS SOLD
    "5101": {"name": "Harga Pokok Penjualan", "type": "expense", "category": "cogs"},
    "5102": {"name": "Pembelian", "type": "expense", "category": "cogs"},
    "5103": {"name": "Diskon Pembelian", "type": "expense", "category": "cogs"},
    "5104": {"name": "Retur Pembelian", "type": "expense", "category": "cogs"},
    
    # OPERATING EXPENSES
    "6101": {"name": "Beban Gaji", "type": "expense", "category": "operating_expense"},
    "6102": {"name": "Beban Sewa", "type": "expense", "category": "operating_expense"},
    "6103": {"name": "Beban Listrik", "type": "expense", "category": "operating_expense"},
    "6104": {"name": "Beban Telepon", "type": "expense", "category": "operating_expense"},
    "6105": {"name": "Beban Perlengkapan", "type": "expense", "category": "operating_expense"},
    "6201": {"name": "Selisih Kurang Kas", "type": "expense", "category": "operating_expense"},
    "6202": {"name": "Beban Selisih Kas", "type": "expense", "category": "operating_expense"},
    "6301": {"name": "Beban Piutang Tak Tertagih", "type": "expense", "category": "operating_expense"},
}

# ==================== DEFAULT ACCOUNT MAPPING ====================
# Updated to use new iPOS-style account codes (Setting Akun ERP)
DEFAULT_MAPPING = {
    # Sales
    "sales_cash_account": {"code": "1-1100", "name": "Kas"},
    "sales_revenue_account": {"code": "4-1000", "name": "Pendapatan Penjualan"},
    "sales_tax_account": {"code": "2-1400", "name": "PPN Keluaran"},
    "sales_discount_account": {"code": "4-2000", "name": "Potongan Penjualan"},
    "cogs_account": {"code": "5-1000", "name": "Harga Pokok Penjualan"},
    "inventory_account": {"code": "1-1400", "name": "Persediaan Barang"},
    
    # Purchase
    "purchase_inventory_account": {"code": "1-1400", "name": "Persediaan Barang"},
    "purchase_expense_account": {"code": "5-1000", "name": "Harga Pokok Penjualan"},
    "purchase_tax_account": {"code": "1-1500", "name": "PPN Masukan"},
    
    # AR/AP
    "ar_account": {"code": "1-1300", "name": "Piutang Usaha"},
    "ap_account": {"code": "2-1100", "name": "Hutang Dagang"},
    "employee_receivable_account": {"code": "1-1310", "name": "Piutang Karyawan"},
    
    # Deposit / Cash
    "central_cash_account": {"code": "1-1100", "name": "Kas"},
    "branch_cash_account": {"code": "1-1100", "name": "Kas"},
    "cashier_cash_account": {"code": "1-1100", "name": "Kas"},
    "cash_in_transit_account": {"code": "1-1110", "name": "Kas Dalam Perjalanan"},
    "shortage_account": {"code": "5-9100", "name": "Selisih Persediaan"},
    "overage_account": {"code": "4-9000", "name": "Pendapatan Pembulatan"},
    
    # Bank
    "bank_account": {"code": "1-1200", "name": "Bank"},
    "cash_account": {"code": "1-1100", "name": "Kas"}
}

# ==================== ACCOUNT DERIVATION ENGINE ====================
async def derive_accounting_account(account_key: str, branch_id: str = None, 
                                    warehouse_id: str = None, category_id: str = None) -> Dict[str, str]:
    """
    ACCOUNT DERIVATION ENGINE for Accounting Module
    Priority: Branch > Warehouse > Category > Global > Default
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
    
    # Priority 3: Category mapping
    if category_id:
        mapping = await db.account_mapping_category.find_one({
            "category_id": category_id, "account_key": account_key
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
    default = DEFAULT_MAPPING.get(account_key)
    if default:
        return default
    
    # Final fallback
    return {"code": "9-9999", "name": f"Unknown Account ({account_key})"}

# ==================== PYDANTIC MODELS ====================

class AccountCreate(BaseModel):
    code: str
    name: str
    type: str  # asset, liability, equity, revenue, expense
    category: str
    parent_code: str = ""
    is_active: bool = True

class AccountMappingUpdate(BaseModel):
    mappings: Dict[str, Dict[str, str]]

class JournalEntryCreate(BaseModel):
    journal_date: str
    description: str
    entries: List[Dict[str, Any]]  # [{account_code, debit, credit, description}]
    reference_type: str = "manual"
    reference_id: str = ""
    reference_number: str = ""

# ==================== HELPER FUNCTIONS ====================

async def get_user_accounting_scope(user: dict) -> Dict[str, Any]:
    """Get user's accounting access scope"""
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
    
    return {
        "user_id": user_id,
        "user_name": user.get("name", ""),
        "role_code": role_code,
        "role_level": role_level,
        "branch_id": branch_id,
        "is_admin": inherit_all or role_level <= 1,
        "can_view_all": inherit_all or role_level <= 3,
        "can_manage_accounts": inherit_all or role_level <= 2,
        "can_create_journal": role_level <= 5,
        "can_post_journal": role_level <= 3,
        "can_view_gl": role_level <= 5
    }


async def generate_journal_number(prefix: str = "JV") -> str:
    """Generate unique journal number"""
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    full_prefix = f"{prefix}-{today}"
    
    last = await journal_entries.find_one(
        {"journal_number": {"$regex": f"^{full_prefix}"}},
        {"_id": 0, "journal_number": 1},
        sort=[("journal_number", -1)]
    )
    
    if last:
        try:
            seq = int(last["journal_number"].split("-")[-1]) + 1
        except:
            seq = 1
    else:
        seq = 1
    
    return f"{full_prefix}-{seq:04d}"


async def get_account_mapping(branch_id: str = "") -> Dict:
    """Get account mapping for a branch (or default)"""
    if branch_id:
        mapping = await account_mappings.find_one({"branch_id": branch_id}, {"_id": 0})
        if mapping:
            return mapping.get("mappings", DEFAULT_MAPPING)
    
    # Fallback to default
    mapping = await account_mappings.find_one({"branch_id": "default"}, {"_id": 0})
    return mapping.get("mappings", DEFAULT_MAPPING) if mapping else DEFAULT_MAPPING


# ==================== CHART OF ACCOUNTS ENDPOINTS ====================

@router.get("/accounts")
async def list_accounts(
    type_filter: str = "",
    active_only: str = "yes",
    user: dict = Depends(get_current_user)
):
    """List all accounts"""
    scope = await get_user_accounting_scope(user)
    
    if not scope["can_view_gl"]:
        raise HTTPException(status_code=403, detail="AKSES DITOLAK")
    
    query = {}
    if type_filter:
        query["type"] = type_filter
    if active_only == "yes":
        query["is_active"] = True
    
    accounts = await chart_of_accounts.find(query, {"_id": 0}).sort("code", 1).to_list(500)
    
    return {"accounts": accounts}


@router.get("/accounts/{code}")
async def get_account(
    code: str,
    user: dict = Depends(get_current_user)
):
    """Get account detail"""
    account = await chart_of_accounts.find_one({"code": code}, {"_id": 0})
    if not account:
        raise HTTPException(status_code=404, detail="Akun tidak ditemukan")
    return account


@router.post("/accounts")
async def create_account(
    data: AccountCreate,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """Create new account"""
    scope = await get_user_accounting_scope(user)
    
    if not scope["can_manage_accounts"]:
        raise HTTPException(status_code=403, detail="AKSES DITOLAK")
    
    existing = await chart_of_accounts.find_one({"code": data.code})
    if existing:
        raise HTTPException(status_code=400, detail="Kode akun sudah ada")
    
    account = {
        "id": str(uuid.uuid4()),
        "code": data.code,
        "name": data.name,
        "type": data.type,
        "category": data.category,
        "parent_code": data.parent_code,
        "is_active": data.is_active,
        "created_by": scope["user_id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await chart_of_accounts.insert_one(account)
    
    await log_activity(
        db, scope["user_id"], scope["user_name"],
        "create", "chart_of_accounts",
        f"Membuat akun {data.code} - {data.name}",
        request.client.host if request.client else "",
        scope["branch_id"]
    )
    
    return {"code": data.code, "message": "Akun berhasil dibuat"}


# ==================== ACCOUNT MAPPING ENDPOINTS ====================

@router.get("/mapping")
async def get_account_mappings(
    branch_id: str = "",
    user: dict = Depends(get_current_user)
):
    """Get account mapping settings"""
    scope = await get_user_accounting_scope(user)
    
    if not scope["can_view_gl"]:
        raise HTTPException(status_code=403, detail="AKSES DITOLAK")
    
    target_branch = branch_id if branch_id else "default"
    mapping = await account_mappings.find_one({"branch_id": target_branch}, {"_id": 0})
    
    if not mapping:
        return {
            "branch_id": target_branch,
            "mappings": DEFAULT_MAPPING,
            "is_default": True
        }
    
    return {
        "branch_id": target_branch,
        "mappings": mapping.get("mappings", DEFAULT_MAPPING),
        "is_default": target_branch == "default"
    }


@router.put("/mapping")
async def update_account_mappings(
    data: AccountMappingUpdate,
    branch_id: str = "default",
    request: Request = None,
    user: dict = Depends(get_current_user)
):
    """Update account mapping settings"""
    scope = await get_user_accounting_scope(user)
    
    if not scope["can_manage_accounts"]:
        raise HTTPException(status_code=403, detail="AKSES DITOLAK")
    
    existing = await account_mappings.find_one({"branch_id": branch_id})
    
    if existing:
        await account_mappings.update_one(
            {"branch_id": branch_id},
            {"$set": {
                "mappings": data.mappings,
                "updated_by": scope["user_id"],
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
    else:
        await account_mappings.insert_one({
            "id": str(uuid.uuid4()),
            "branch_id": branch_id,
            "mappings": data.mappings,
            "created_by": scope["user_id"],
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    
    await log_activity(
        db, scope["user_id"], scope["user_name"],
        "update", "account_mapping",
        f"Update mapping akun untuk branch {branch_id}",
        request.client.host if request and request.client else "",
        scope["branch_id"]
    )
    
    return {"message": "Mapping akun berhasil diupdate"}


# ==================== JOURNAL ENDPOINTS ====================

@router.get("/journals")
async def list_journals(
    start_date: str = "",
    end_date: str = "",
    reference_type: str = "",
    status: str = "",
    skip: int = 0,
    limit: int = 50,
    user: dict = Depends(get_current_user)
):
    """List journal entries"""
    scope = await get_user_accounting_scope(user)
    
    if not scope["can_view_gl"]:
        raise HTTPException(status_code=403, detail="AKSES DITOLAK")
    
    query = {}
    
    if not scope["can_view_all"]:
        query["branch_id"] = scope["branch_id"]
    
    if start_date:
        query["journal_date"] = {"$gte": start_date}
    if end_date:
        if "journal_date" in query:
            query["journal_date"]["$lte"] = end_date + "T23:59:59"
        else:
            query["journal_date"] = {"$lte": end_date + "T23:59:59"}
    
    if reference_type:
        query["reference_type"] = reference_type
    if status:
        query["status"] = status
    
    total = await journal_entries.count_documents(query)
    journals = await journal_entries.find(query, {"_id": 0}).sort("journal_date", -1).skip(skip).limit(limit).to_list(limit)
    
    return {"journals": journals, "total": total}


@router.get("/journals/{journal_id}")
async def get_journal(
    journal_id: str,
    user: dict = Depends(get_current_user)
):
    """Get journal detail"""
    journal = await journal_entries.find_one({"id": journal_id}, {"_id": 0})
    if not journal:
        raise HTTPException(status_code=404, detail="Jurnal tidak ditemukan")
    return journal


@router.post("/journals")
async def create_journal(
    data: JournalEntryCreate,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """Create manual journal entry"""
    scope = await get_user_accounting_scope(user)
    
    if not scope["can_create_journal"]:
        raise HTTPException(status_code=403, detail="AKSES DITOLAK")
    
    # Validate entries
    total_debit = sum(e.get("debit", 0) for e in data.entries)
    total_credit = sum(e.get("credit", 0) for e in data.entries)
    
    if abs(total_debit - total_credit) > 0.01:
        raise HTTPException(status_code=400, detail=f"Jurnal tidak balance. Debit: {total_debit}, Credit: {total_credit}")
    
    journal_number = await generate_journal_number("JV-MAN")
    
    journal = {
        "id": str(uuid.uuid4()),
        "journal_number": journal_number,
        "journal_date": data.journal_date,
        "reference_type": data.reference_type,
        "reference_id": data.reference_id,
        "reference_number": data.reference_number,
        "description": data.description,
        "branch_id": scope["branch_id"],
        "entries": data.entries,
        "total_debit": total_debit,
        "total_credit": total_credit,
        "is_balanced": True,
        "status": "draft",
        "created_by": scope["user_id"],
        "created_by_name": scope["user_name"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await journal_entries.insert_one(journal)
    
    await log_activity(
        db, scope["user_id"], scope["user_name"],
        "create", "journal_entries",
        f"Membuat jurnal manual {journal_number}",
        request.client.host if request.client else "",
        scope["branch_id"]
    )
    
    return {"journal_number": journal_number, "message": "Jurnal berhasil dibuat"}


@router.post("/journals/{journal_id}/post")
async def post_journal(
    journal_id: str,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """Post draft journal"""
    scope = await get_user_accounting_scope(user)
    
    if not scope["can_post_journal"]:
        raise HTTPException(status_code=403, detail="AKSES DITOLAK")
    
    journal = await journal_entries.find_one({"id": journal_id}, {"_id": 0})
    if not journal:
        raise HTTPException(status_code=404, detail="Jurnal tidak ditemukan")
    
    if journal.get("status") == "posted":
        raise HTTPException(status_code=400, detail="Jurnal sudah diposting")
    
    await journal_entries.update_one(
        {"id": journal_id},
        {"$set": {
            "status": "posted",
            "posted_by": scope["user_id"],
            "posted_by_name": scope["user_name"],
            "posted_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    await log_activity(
        db, scope["user_id"], scope["user_name"],
        "post", "journal_entries",
        f"Posting jurnal {journal.get('journal_number')}",
        request.client.host if request.client else "",
        scope["branch_id"]
    )
    
    return {"message": "Jurnal berhasil diposting"}


# ==================== GENERAL LEDGER ====================

@router.get("/gl/{account_code}")
async def get_general_ledger(
    account_code: str,
    start_date: str = "",
    end_date: str = "",
    branch_id: str = "",
    user: dict = Depends(get_current_user)
):
    """Get general ledger for an account"""
    scope = await get_user_accounting_scope(user)
    
    if not scope["can_view_gl"]:
        raise HTTPException(status_code=403, detail="AKSES DITOLAK")
    
    # Get account info
    account = await chart_of_accounts.find_one({"code": account_code}, {"_id": 0})
    if not account:
        raise HTTPException(status_code=404, detail="Akun tidak ditemukan")
    
    # Build query for journal entries containing this account
    query = {
        "status": "posted",
        "entries.account_code": account_code
    }
    
    if not scope["can_view_all"]:
        query["branch_id"] = scope["branch_id"]
    elif branch_id:
        query["branch_id"] = branch_id
    
    if start_date:
        query["journal_date"] = {"$gte": start_date}
    if end_date:
        if "journal_date" in query:
            query["journal_date"]["$lte"] = end_date + "T23:59:59"
        else:
            query["journal_date"] = {"$lte": end_date + "T23:59:59"}
    
    journals = await journal_entries.find(query, {"_id": 0}).sort("journal_date", 1).to_list(10000)
    
    # Extract entries for this account
    ledger_entries = []
    running_balance = 0
    total_debit = 0
    total_credit = 0
    
    for journal in journals:
        for entry in journal.get("entries", []):
            if entry.get("account_code") == account_code:
                debit = entry.get("debit", 0)
                credit = entry.get("credit", 0)
                
                # Calculate balance based on account type
                if account.get("type") in ["asset", "expense"]:
                    running_balance += debit - credit
                else:
                    running_balance += credit - debit
                
                total_debit += debit
                total_credit += credit
                
                ledger_entries.append({
                    "date": journal.get("journal_date", "")[:10],
                    "journal_number": journal.get("journal_number"),
                    "reference": journal.get("reference_number", ""),
                    "description": entry.get("description") or journal.get("description", ""),
                    "debit": debit,
                    "credit": credit,
                    "balance": running_balance
                })
    
    return {
        "account_code": account_code,
        "account_name": account.get("name", ""),
        "account_type": account.get("type", ""),
        "period": {
            "start": start_date or "All",
            "end": end_date or "All"
        },
        "entries": ledger_entries,
        "summary": {
            "total_debit": total_debit,
            "total_credit": total_credit,
            "ending_balance": running_balance
        }
    }


# ==================== FINANCIAL REPORTS ====================

@router.get("/trial-balance")
async def get_trial_balance(
    as_of_date: str = "",
    branch_id: str = "",
    user: dict = Depends(get_current_user)
):
    """Get trial balance"""
    scope = await get_user_accounting_scope(user)
    
    if not scope["can_view_gl"]:
        raise HTTPException(status_code=403, detail="AKSES DITOLAK")
    
    if not as_of_date:
        as_of_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Get all posted journals up to as_of_date
    query = {
        "status": "posted",
        "journal_date": {"$lte": as_of_date + "T23:59:59"}
    }
    
    if not scope["can_view_all"]:
        query["branch_id"] = scope["branch_id"]
    elif branch_id:
        query["branch_id"] = branch_id
    
    journals = await journal_entries.find(query, {"_id": 0}).to_list(100000)
    
    # Aggregate by account
    account_balances = {}
    
    for journal in journals:
        for entry in journal.get("entries", []):
            code = entry.get("account_code", "")
            if not code:
                continue
            
            if code not in account_balances:
                account_balances[code] = {"debit": 0, "credit": 0}
            
            account_balances[code]["debit"] += entry.get("debit", 0)
            account_balances[code]["credit"] += entry.get("credit", 0)
    
    # Get account names
    all_accounts = await chart_of_accounts.find({}, {"_id": 0}).to_list(500)
    account_map = {a["code"]: a for a in all_accounts}
    
    # Build trial balance
    trial_balance = []
    total_debit = 0
    total_credit = 0
    
    for code in sorted(account_balances.keys()):
        acc_info = account_map.get(code, {})
        debit = account_balances[code]["debit"]
        credit = account_balances[code]["credit"]
        
        # Calculate balance
        acc_type = acc_info.get("type", "")
        if acc_type in ["asset", "expense"]:
            balance = debit - credit
            if balance >= 0:
                debit_balance = balance
                credit_balance = 0
            else:
                debit_balance = 0
                credit_balance = abs(balance)
        else:
            balance = credit - debit
            if balance >= 0:
                debit_balance = 0
                credit_balance = balance
            else:
                debit_balance = abs(balance)
                credit_balance = 0
        
        total_debit += debit_balance
        total_credit += credit_balance
        
        trial_balance.append({
            "code": code,
            "name": acc_info.get("name", "Unknown"),
            "type": acc_type,
            "debit": debit_balance,
            "credit": credit_balance
        })
    
    return {
        "as_of_date": as_of_date,
        "accounts": trial_balance,
        "totals": {
            "debit": total_debit,
            "credit": total_credit,
            "is_balanced": abs(total_debit - total_credit) < 0.01
        }
    }


@router.get("/balance-sheet")
async def get_balance_sheet(
    as_of_date: str = "",
    branch_id: str = "",
    user: dict = Depends(get_current_user)
):
    """Get balance sheet (Neraca)"""
    scope = await get_user_accounting_scope(user)
    
    if not scope["can_view_gl"]:
        raise HTTPException(status_code=403, detail="AKSES DITOLAK")
    
    if not as_of_date:
        as_of_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Get trial balance first
    tb_result = await get_trial_balance(as_of_date, branch_id, user)
    accounts = tb_result.get("accounts", [])
    
    # Group by type
    assets = []
    liabilities = []
    equity = []
    
    for acc in accounts:
        balance = acc["debit"] - acc["credit"]
        if acc["type"] == "asset":
            assets.append({**acc, "balance": acc["debit"]})
        elif acc["type"] == "liability":
            liabilities.append({**acc, "balance": acc["credit"]})
        elif acc["type"] == "equity":
            equity.append({**acc, "balance": acc["credit"]})
    
    total_assets = sum(a["balance"] for a in assets)
    total_liabilities = sum(l["balance"] for l in liabilities)
    total_equity = sum(e["balance"] for e in equity)
    
    return {
        "as_of_date": as_of_date,
        "assets": {
            "items": assets,
            "total": total_assets
        },
        "liabilities": {
            "items": liabilities,
            "total": total_liabilities
        },
        "equity": {
            "items": equity,
            "total": total_equity
        },
        "is_balanced": abs(total_assets - (total_liabilities + total_equity)) < 0.01
    }


@router.get("/income-statement")
async def get_income_statement(
    start_date: str = "",
    end_date: str = "",
    branch_id: str = "",
    user: dict = Depends(get_current_user)
):
    """Get income statement (Laba Rugi)"""
    scope = await get_user_accounting_scope(user)
    
    if not scope["can_view_gl"]:
        raise HTTPException(status_code=403, detail="AKSES DITOLAK")
    
    if not end_date:
        end_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if not start_date:
        # Default to first day of current month
        start_date = datetime.now(timezone.utc).replace(day=1).strftime("%Y-%m-%d")
    
    # Get journals in period
    query = {
        "status": "posted",
        "journal_date": {"$gte": start_date, "$lte": end_date + "T23:59:59"}
    }
    
    if not scope["can_view_all"]:
        query["branch_id"] = scope["branch_id"]
    elif branch_id:
        query["branch_id"] = branch_id
    
    journals = await journal_entries.find(query, {"_id": 0}).to_list(100000)
    
    # Get accounts
    all_accounts = await chart_of_accounts.find({}, {"_id": 0}).to_list(500)
    account_map = {a["code"]: a for a in all_accounts}
    
    # Aggregate
    account_totals = {}
    
    for journal in journals:
        for entry in journal.get("entries", []):
            code = entry.get("account_code", "")
            if not code:
                continue
            
            if code not in account_totals:
                account_totals[code] = 0
            
            acc_info = account_map.get(code, {})
            if acc_info.get("type") == "revenue":
                account_totals[code] += entry.get("credit", 0) - entry.get("debit", 0)
            elif acc_info.get("type") == "expense":
                account_totals[code] += entry.get("debit", 0) - entry.get("credit", 0)
    
    # Build report
    revenues = []
    expenses = []
    
    for code, total in account_totals.items():
        acc_info = account_map.get(code, {})
        if acc_info.get("type") == "revenue":
            revenues.append({"code": code, "name": acc_info.get("name", ""), "amount": total})
        elif acc_info.get("type") == "expense":
            expenses.append({"code": code, "name": acc_info.get("name", ""), "amount": total})
    
    total_revenue = sum(r["amount"] for r in revenues)
    total_expense = sum(e["amount"] for e in expenses)
    net_income = total_revenue - total_expense
    
    return {
        "period": {
            "start": start_date,
            "end": end_date
        },
        "revenues": {
            "items": revenues,
            "total": total_revenue
        },
        "expenses": {
            "items": expenses,
            "total": total_expense
        },
        "net_income": net_income,
        "is_profit": net_income >= 0
    }


# ==================== INIT ====================

@router.post("/init")
async def initialize_accounting_system(user: dict = Depends(get_current_user)):
    """Initialize accounting system with default accounts"""
    
    # Create indexes
    await chart_of_accounts.create_index("code", unique=True)
    await journal_entries.create_index("journal_number", unique=True)
    await journal_entries.create_index("journal_date")
    await journal_entries.create_index("status")
    await account_mappings.create_index("branch_id", unique=True)
    
    # Create default accounts if none exist
    existing = await chart_of_accounts.count_documents({})
    if existing == 0:
        for code, info in DEFAULT_ACCOUNTS.items():
            await chart_of_accounts.insert_one({
                "id": str(uuid.uuid4()),
                "code": code,
                "name": info["name"],
                "type": info["type"],
                "category": info["category"],
                "parent_code": "",
                "is_active": True,
                "created_by": "system",
                "created_at": datetime.now(timezone.utc).isoformat()
            })
    
    # Create default mapping if none exist
    mapping_exists = await account_mappings.find_one({"branch_id": "default"})
    if not mapping_exists:
        await account_mappings.insert_one({
            "id": str(uuid.uuid4()),
            "branch_id": "default",
            "mappings": DEFAULT_MAPPING,
            "created_by": "system",
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    
    return {
        "message": "Accounting system initialized",
        "accounts_created": existing == 0,
        "mapping_created": not mapping_exists
    }
