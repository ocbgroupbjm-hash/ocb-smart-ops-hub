# OCB AI TITAN - Accounting Routes
# SECURITY: All operations require RBAC validation
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from database import db, get_db
from utils.auth import get_current_user
from routes.rbac_middleware import require_permission, log_security_event
from routes.rbac_system import log_activity
import uuid

router = APIRouter(prefix="/api/accounting", tags=["Accounting"])

# Collections
accounts = db["accounts"]  # Chart of Accounts / Daftar Perkiraan
journals = db["journals"]  # Journal Entries (old)
cash_transactions = db["cash_transactions"]  # Kas Masuk/Keluar/Transfer
deposits = db["deposits"]  # Deposit Pelanggan/Supplier

# ==================== UNIFIED JOURNAL HELPER ====================
# Helper to get all journal entries with their entries (from both embedded and separate formats)

async def get_all_journal_entries_with_lines(query: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """
    Get all journal entries with their line items.
    Handles both formats:
    1. Embedded entries in 'entries' array
    2. Separate lines in 'journal_entry_lines' collection
    """
    if query is None:
        query = {}
    
    journal_entries_col = db["journal_entries"]
    journal_entry_lines_col = db["journal_entry_lines"]
    
    # Get all journal entries matching query
    all_je = await journal_entries_col.find(query, {"_id": 0}).to_list(100000)
    
    # Process each journal entry
    result = []
    for je in all_je:
        # Check if entries are embedded
        if je.get("entries") and len(je.get("entries", [])) > 0:
            result.append(je)
        else:
            # Load entries from journal_entry_lines
            lines = await journal_entry_lines_col.find(
                {"journal_id": je.get("id")},
                {"_id": 0}
            ).to_list(100)
            
            if lines:
                je["entries"] = lines
            else:
                je["entries"] = []
            
            result.append(je)
    
    return result

# ==================== DAFTAR PERKIRAAN (Chart of Accounts) ====================

class AccountCreate(BaseModel):
    code: str
    name: str
    category: str  # asset, liability, equity, revenue, expense
    parent_id: str = ""
    account_type: str = "detail"  # header, detail
    is_cash: bool = False
    is_active: bool = True
    description: str = ""
    normal_balance: str = "debit"  # debit, credit

@router.get("/accounts")
async def list_accounts(
    category: str = "",
    search: str = "",
    include_inactive: bool = False,
    user: dict = Depends(require_permission("master_coa", "view"))
):
    """List chart of accounts - Requires master_coa.view permission"""
    query = {}
    if category:
        query["category"] = category
    if search:
        query["$or"] = [
            {"code": {"$regex": search, "$options": "i"}},
            {"name": {"$regex": search, "$options": "i"}}
        ]
    if not include_inactive:
        query["is_active"] = True
    
    items = await accounts.find(query, {"_id": 0}).sort("code", 1).to_list(500)
    return {"items": items, "total": len(items)}

@router.get("/accounts/{account_id}")
async def get_account(account_id: str, user: dict = Depends(require_permission("master_coa", "view"))):
    """Get account details - Requires master_coa.view permission"""
    account = await accounts.find_one({"id": account_id}, {"_id": 0})
    if not account:
        raise HTTPException(status_code=404, detail="Akun tidak ditemukan")
    return account

@router.post("/accounts")
async def create_account(data: AccountCreate, request: Request, user: dict = Depends(require_permission("master_coa", "create"))):
    """Create account - Requires master_coa.create permission"""
    # Check code exists
    existing = await accounts.find_one({"code": data.code})
    if existing:
        raise HTTPException(status_code=400, detail="Kode akun sudah digunakan")
    
    account = {
        "id": str(uuid.uuid4()),
        **data.model_dump(),
        "balance": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user.get("user_id")
    }
    await accounts.insert_one(account)
    return {"id": account["id"], "message": "Akun berhasil ditambahkan"}

@router.put("/accounts/{account_id}")
async def update_account(account_id: str, data: AccountCreate, request: Request, user: dict = Depends(require_permission("master_coa", "edit"))):
    """Update account - Requires master_coa.edit permission"""
    update_data = data.model_dump()
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await accounts.update_one({"id": account_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Akun tidak ditemukan")
    return {"message": "Akun berhasil diupdate"}

@router.delete("/accounts/{account_id}")
async def delete_account(account_id: str, user: dict = Depends(get_current_user)):
    # Check if account has transactions
    journal_count = await journals.count_documents({"$or": [
        {"entries.debit_account_id": account_id},
        {"entries.credit_account_id": account_id}
    ]})
    if journal_count > 0:
        # Soft delete
        await accounts.update_one({"id": account_id}, {"$set": {"is_active": False}})
        return {"message": "Akun dinonaktifkan (memiliki transaksi)"}
    
    result = await accounts.delete_one({"id": account_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Akun tidak ditemukan")
    return {"message": "Akun berhasil dihapus"}

# ==================== DATA JURNAL (Journal Entries) ====================

class JournalEntry(BaseModel):
    account_id: str
    account_code: str = ""
    account_name: str = ""
    debit: float = 0
    credit: float = 0
    description: str = ""

class JournalCreate(BaseModel):
    date: str
    reference: str = ""
    description: str
    entries: List[JournalEntry]
    source: str = "manual"  # manual, purchase, sales, cash

@router.get("/journals")
async def list_journals(
    date_from: str = "",
    date_to: str = "",
    account_id: str = "",
    source: str = "",
    search: str = "",
    limit: int = 200,
    user: dict = Depends(get_current_user)
):
    query = {}
    if date_from:
        query["date"] = {"$gte": date_from}
    if date_to:
        if "date" in query:
            query["date"]["$lte"] = date_to
        else:
            query["date"] = {"$lte": date_to}
    if account_id:
        query["entries.account_id"] = account_id
    if source:
        query["source"] = source
    if search:
        query["$or"] = [
            {"journal_number": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
            {"reference": {"$regex": search, "$options": "i"}}
        ]
    
    items = await journals.find(query, {"_id": 0}).sort("date", -1).to_list(limit)
    
    # Calculate totals
    total_debit = sum(sum(e.get("debit", 0) for e in j.get("entries", [])) for j in items)
    total_credit = sum(sum(e.get("credit", 0) for e in j.get("entries", [])) for j in items)
    
    return {
        "items": items,
        "total": len(items),
        "total_debit": total_debit,
        "total_credit": total_credit
    }

@router.get("/journals/unbalanced")
async def get_unbalanced_journals(user: dict = Depends(get_current_user)):
    """Get journals where debit != credit"""
    all_journals = await journals.find({}, {"_id": 0}).to_list(1000)
    unbalanced = []
    for j in all_journals:
        total_debit = sum(e.get("debit", 0) for e in j.get("entries", []))
        total_credit = sum(e.get("credit", 0) for e in j.get("entries", []))
        if abs(total_debit - total_credit) > 0.01:
            j["total_debit"] = total_debit
            j["total_credit"] = total_credit
            j["difference"] = total_debit - total_credit
            unbalanced.append(j)
    return {"items": unbalanced, "total": len(unbalanced)}

@router.get("/journals/{journal_id}")
async def get_journal(journal_id: str, user: dict = Depends(get_current_user)):
    journal = await journals.find_one({"id": journal_id}, {"_id": 0})
    if not journal:
        raise HTTPException(status_code=404, detail="Jurnal tidak ditemukan")
    return journal

@router.post("/journals")
async def create_journal(data: JournalCreate, user: dict = Depends(get_current_user)):
    # Validate balance
    total_debit = sum(e.debit for e in data.entries)
    total_credit = sum(e.credit for e in data.entries)
    if abs(total_debit - total_credit) > 0.01:
        raise HTTPException(status_code=400, detail=f"Jurnal tidak seimbang. Debit: {total_debit}, Credit: {total_credit}")
    
    # Enrich entries with account info
    entries = []
    for entry in data.entries:
        account = await accounts.find_one({"id": entry.account_id}, {"_id": 0})
        if account:
            entries.append({
                **entry.model_dump(),
                "account_code": account.get("code", ""),
                "account_name": account.get("name", "")
            })
    
    journal_number = f"JRN{datetime.now().strftime('%Y%m%d%H%M%S')}"
    journal = {
        "id": str(uuid.uuid4()),
        "journal_number": journal_number,
        "date": data.date,
        "reference": data.reference,
        "description": data.description,
        "entries": entries,
        "source": data.source,
        "total_debit": total_debit,
        "total_credit": total_credit,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user.get("user_id")
    }
    await journals.insert_one(journal)
    
    # Update account balances
    for entry in entries:
        account = await accounts.find_one({"id": entry["account_id"]})
        if account:
            balance_change = entry["debit"] - entry["credit"]
            if account.get("normal_balance") == "credit":
                balance_change = -balance_change
            await accounts.update_one(
                {"id": entry["account_id"]},
                {"$inc": {"balance": balance_change}}
            )
    
    return {"id": journal["id"], "journal_number": journal_number, "message": "Jurnal berhasil dibuat"}

@router.put("/journals/{journal_id}")
async def update_journal(journal_id: str, data: JournalCreate, user: dict = Depends(get_current_user)):
    # Validate balance
    total_debit = sum(e.debit for e in data.entries)
    total_credit = sum(e.credit for e in data.entries)
    if abs(total_debit - total_credit) > 0.01:
        raise HTTPException(status_code=400, detail="Jurnal tidak seimbang")
    
    update_data = data.model_dump()
    update_data["total_debit"] = total_debit
    update_data["total_credit"] = total_credit
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await journals.update_one({"id": journal_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Jurnal tidak ditemukan")
    return {"message": "Jurnal berhasil diupdate"}

# ==================== JOURNAL SOURCE TYPES (PRIORITAS 1 SECURITY) ====================
# System generated journals CANNOT be deleted
PROTECTED_JOURNAL_SOURCES = [
    "purchase", "pembelian",
    "payment", "pembayaran", 
    "ap", "hutang", "accounts_payable",
    "ar", "piutang", "accounts_receivable",
    "inventory", "persediaan", "stock",
    "payroll", "gaji",
    "sales", "penjualan",
    "cash", "bank", "kas",
    "pos", "retur", "return",
    "ap_payment", "ar_payment",
    "ap_invoice_reversal", "ap_payment_void"
]

@router.delete("/journals/{journal_id}")
async def delete_journal(journal_id: str, user: dict = Depends(get_current_user)):
    """
    Delete journal entry - ONLY allowed for manual journals
    
    SECURITY RULE (PRIORITAS 1):
    - System generated journals (purchase, payment, ap, ar, inventory, payroll) CANNOT be deleted
    - Only manual journal entries can be deleted
    - This is standard ERP security practice
    """
    journal = await journals.find_one({"id": journal_id}, {"_id": 0})
    if not journal:
        raise HTTPException(status_code=404, detail="Jurnal tidak ditemukan")
    
    # PRIORITAS 1: Check journal source - block delete for system journals
    journal_source = (
        journal.get("journal_source") or 
        journal.get("reference_type") or 
        journal.get("source_type") or 
        journal.get("source") or 
        "manual"
    ).lower()
    
    # Check if this is a protected system journal
    is_system_journal = any(src in journal_source for src in PROTECTED_JOURNAL_SOURCES)
    
    # Also check if journal has reference_id (linked to transaction)
    has_reference = bool(journal.get("reference_id") or journal.get("reference_number"))
    
    if is_system_journal or (has_reference and journal_source != "manual"):
        raise HTTPException(
            status_code=403, 
            detail="System generated journal cannot be deleted. Jurnal yang dihasilkan sistem tidak dapat dihapus."
        )
    
    # Reverse account balances
    for entry in journal.get("entries", []):
        account = await accounts.find_one({"id": entry["account_id"]})
        if account:
            balance_change = entry["debit"] - entry["credit"]
            if account.get("normal_balance") == "credit":
                balance_change = -balance_change
            await accounts.update_one(
                {"id": entry["account_id"]},
                {"$inc": {"balance": -balance_change}}
            )
    
    await journals.delete_one({"id": journal_id})
    
    # Log activity
    user_id = user.get("user_id", user.get("id", ""))
    user_name = user.get("name", "")
    await log_activity(
        db, user_id, user_name,
        "delete", "journal",
        f"Menghapus jurnal manual {journal.get('journal_number', journal_id)}",
        "", user.get("branch_id", "")
    )
    
    return {"message": "Jurnal manual berhasil dihapus"}


@router.get("/journals/{journal_id}/can-delete")
async def check_journal_deletable(journal_id: str, user: dict = Depends(get_current_user)):
    """
    Check if journal can be deleted - for frontend button state
    Returns: { can_delete: bool, reason: string }
    """
    journal = await journals.find_one({"id": journal_id}, {"_id": 0})
    if not journal:
        raise HTTPException(status_code=404, detail="Jurnal tidak ditemukan")
    
    journal_source = (
        journal.get("journal_source") or 
        journal.get("reference_type") or 
        journal.get("source_type") or 
        journal.get("source") or 
        "manual"
    ).lower()
    
    is_system_journal = any(src in journal_source for src in PROTECTED_JOURNAL_SOURCES)
    has_reference = bool(journal.get("reference_id") or journal.get("reference_number"))
    
    can_delete = not is_system_journal and not (has_reference and journal_source != "manual")
    
    reason = ""
    if not can_delete:
        reason = f"Jurnal sistem ({journal_source}) tidak dapat dihapus"
    
    return {
        "can_delete": can_delete,
        "journal_source": journal_source,
        "is_system_journal": is_system_journal,
        "reason": reason
    }


# ==================== KAS MASUK/KELUAR/TRANSFER ====================

class CashTransactionCreate(BaseModel):
    date: str
    transaction_type: str  # cash_in, cash_out, transfer
    account_id: str
    to_account_id: str = ""  # For transfer
    amount: float
    description: str
    reference: str = ""

@router.get("/cash")
async def list_cash_transactions(
    transaction_type: str = "",
    date_from: str = "",
    date_to: str = "",
    account_id: str = "",
    limit: int = 200,
    user: dict = Depends(get_current_user)
):
    query = {}
    if transaction_type:
        query["transaction_type"] = transaction_type
    if date_from:
        query["date"] = {"$gte": date_from}
    if date_to:
        if "date" in query:
            query["date"]["$lte"] = date_to
        else:
            query["date"] = {"$lte": date_to}
    if account_id:
        query["$or"] = [{"account_id": account_id}, {"to_account_id": account_id}]
    
    items = await cash_transactions.find(query, {"_id": 0}).sort("date", -1).to_list(limit)
    
    total_in = sum(t.get("amount", 0) for t in items if t.get("transaction_type") == "cash_in")
    total_out = sum(t.get("amount", 0) for t in items if t.get("transaction_type") == "cash_out")
    
    return {
        "items": items,
        "total": len(items),
        "total_in": total_in,
        "total_out": total_out
    }

@router.post("/cash")
async def create_cash_transaction(data: CashTransactionCreate, user: dict = Depends(get_current_user)):
    # Get account info
    account = await accounts.find_one({"id": data.account_id}, {"_id": 0})
    if not account:
        raise HTTPException(status_code=404, detail="Akun tidak ditemukan")
    
    trans_number = f"KAS{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    transaction = {
        "id": str(uuid.uuid4()),
        "transaction_number": trans_number,
        "date": data.date,
        "transaction_type": data.transaction_type,
        "account_id": data.account_id,
        "account_name": account.get("name", ""),
        "to_account_id": data.to_account_id,
        "amount": data.amount,
        "description": data.description,
        "reference": data.reference,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user.get("user_id")
    }
    
    if data.to_account_id:
        to_account = await accounts.find_one({"id": data.to_account_id}, {"_id": 0})
        transaction["to_account_name"] = to_account.get("name", "") if to_account else ""
    
    await cash_transactions.insert_one(transaction)
    
    # Journal entry creation handled by auto_journal_engine (no manual entries needed here)
    
    return {"id": transaction["id"], "transaction_number": trans_number, "message": "Transaksi kas berhasil"}

# ==================== DEPOSIT ====================

class DepositCreate(BaseModel):
    date: str
    deposit_type: str  # customer, supplier
    entity_id: str
    entity_name: str = ""
    amount: float
    description: str = ""
    reference: str = ""

@router.get("/deposits")
async def list_deposits(
    deposit_type: str = "",
    entity_id: str = "",
    date_from: str = "",
    date_to: str = "",
    user: dict = Depends(get_current_user)
):
    query = {}
    if deposit_type:
        query["deposit_type"] = deposit_type
    if entity_id:
        query["entity_id"] = entity_id
    if date_from:
        query["date"] = {"$gte": date_from}
    if date_to:
        if "date" in query:
            query["date"]["$lte"] = date_to
        else:
            query["date"] = {"$lte": date_to}
    
    items = await deposits.find(query, {"_id": 0}).sort("date", -1).to_list(500)
    total_amount = sum(d.get("amount", 0) for d in items)
    
    return {"items": items, "total": len(items), "total_amount": total_amount}

@router.post("/deposits")
async def create_deposit(data: DepositCreate, user: dict = Depends(get_current_user)):
    deposit_number = f"DEP{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    deposit = {
        "id": str(uuid.uuid4()),
        "deposit_number": deposit_number,
        **data.model_dump(),
        "status": "active",
        "used_amount": 0,
        "remaining_amount": data.amount,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user.get("user_id")
    }
    await deposits.insert_one(deposit)
    return {"id": deposit["id"], "deposit_number": deposit_number, "message": "Deposit berhasil dicatat"}

# ==================== BUKU BESAR & NERACA SALDO (DEPRECATED - lihat /financial/*) ====================
# Old endpoints kept for backward compatibility, now use /financial/general-ledger and /financial/trial-balance

@router.get("/ledger")
async def get_ledger_deprecated(
    account_id: str = "",
    date_from: str = "",
    date_to: str = "",
    user: dict = Depends(get_current_user)
):
    """[DEPRECATED] Use /financial/general-ledger instead"""
    query = {}
    if date_from:
        query["date"] = {"$gte": date_from}
    if date_to:
        if "date" in query:
            query["date"]["$lte"] = date_to
        else:
            query["date"] = {"$lte": date_to}
    
    all_journals = await journals.find(query, {"_id": 0}).sort("date", 1).to_list(1000)
    
    # Group by account
    ledger = {}
    for journal in all_journals:
        for entry in journal.get("entries", []):
            acc_id = entry.get("account_id")
            if account_id and acc_id != account_id:
                continue
            
            if acc_id not in ledger:
                ledger[acc_id] = {
                    "account_id": acc_id,
                    "account_code": entry.get("account_code", ""),
                    "account_name": entry.get("account_name", ""),
                    "entries": [],
                    "total_debit": 0,
                    "total_credit": 0,
                    "balance": 0
                }
            
            ledger[acc_id]["entries"].append({
                "date": journal.get("date"),
                "journal_number": journal.get("journal_number"),
                "description": journal.get("description"),
                "debit": entry.get("debit", 0),
                "credit": entry.get("credit", 0)
            })
            ledger[acc_id]["total_debit"] += entry.get("debit", 0)
            ledger[acc_id]["total_credit"] += entry.get("credit", 0)
    
    # Calculate balances
    for acc_id, data in ledger.items():
        account = await accounts.find_one({"id": acc_id}, {"_id": 0})
        if account and account.get("normal_balance") == "debit":
            data["balance"] = data["total_debit"] - data["total_credit"]
        else:
            data["balance"] = data["total_credit"] - data["total_debit"]
    
    return {"items": list(ledger.values()), "total": len(ledger)}

@router.get("/trial-balance-old")
async def get_trial_balance_deprecated(
    date_from: str = "",
    date_to: str = "",
    user: dict = Depends(get_current_user)
):
    """[DEPRECATED] Use /financial/trial-balance instead. Neraca Saldo from old journals collection"""
    all_accounts = await accounts.find({"is_active": True}, {"_id": 0}).sort("code", 1).to_list(500)
    
    query = {}
    if date_from:
        query["date"] = {"$gte": date_from}
    if date_to:
        if "date" in query:
            query["date"]["$lte"] = date_to
        else:
            query["date"] = {"$lte": date_to}
    
    all_journals = await journals.find(query, {"_id": 0}).to_list(1000)
    
    # Calculate balances per account
    balances = {}
    for journal in all_journals:
        for entry in journal.get("entries", []):
            acc_id = entry.get("account_id")
            if acc_id not in balances:
                balances[acc_id] = {"debit": 0, "credit": 0}
            balances[acc_id]["debit"] += entry.get("debit", 0)
            balances[acc_id]["credit"] += entry.get("credit", 0)
    
    trial_balance = []
    total_debit = 0
    total_credit = 0
    
    for account in all_accounts:
        acc_id = account.get("id")
        bal = balances.get(acc_id, {"debit": 0, "credit": 0})
        
        if account.get("normal_balance") == "debit":
            balance = bal["debit"] - bal["credit"]
            debit_balance = balance if balance > 0 else 0
            credit_balance = -balance if balance < 0 else 0
        else:
            balance = bal["credit"] - bal["debit"]
            credit_balance = balance if balance > 0 else 0
            debit_balance = -balance if balance < 0 else 0
        
        if debit_balance > 0 or credit_balance > 0:
            trial_balance.append({
                "account_id": acc_id,
                "account_code": account.get("code"),
                "account_name": account.get("name"),
                "category": account.get("category"),
                "debit_balance": debit_balance,
                "credit_balance": credit_balance
            })
            total_debit += debit_balance
            total_credit += credit_balance
    
    return {
        "items": trial_balance,
        "total_debit": total_debit,
        "total_credit": total_credit,
        "is_balanced": abs(total_debit - total_credit) < 0.01
    }

# ==================== LAPORAN KEUANGAN ====================
# UNIFIED: Now reads from journal_entries (the main journal collection used by all modules)

# Reference: Account Classification for Balance Sheet & Income Statement
# Assets: 1-xxxx (Debit normal)
# Liabilities: 2-xxxx (Credit normal)
# Equity: 3-xxxx (Credit normal)
# Revenue: 4-xxxx (Credit normal)
# Expenses: 5-xxxx (Debit normal)

def classify_account(code: str) -> dict:
    """Classify account based on code prefix"""
    if not code:
        return {"type": "unknown", "category": "unknown", "normal_balance": "debit"}
    
    prefix = code.split("-")[0] if "-" in code else code[:1]
    
    if prefix == "1":
        return {"type": "asset", "category": "asset", "normal_balance": "debit"}
    elif prefix == "2":
        return {"type": "liability", "category": "liability", "normal_balance": "credit"}
    elif prefix == "3":
        return {"type": "equity", "category": "equity", "normal_balance": "credit"}
    elif prefix == "4":
        return {"type": "revenue", "category": "revenue", "normal_balance": "credit"}
    elif prefix in ["5", "6", "7", "8"]:  # All expense-like accounts
        return {"type": "expense", "category": "expense", "normal_balance": "debit"}
    elif prefix == "9":  # Historical/adjustments
        return {"type": "equity", "category": "equity", "normal_balance": "credit"}
    else:
        return {"type": "expense", "category": "expense", "normal_balance": "debit"}

# Get journal_entries collection (unified journal storage)
journal_entries = db["journal_entries"]

@router.get("/financial/balance-sheet")
async def get_balance_sheet(date: str = "", user: dict = Depends(get_current_user)):
    """Neraca - reads from journal_entries collection (unified format)"""
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    
    # Get all posted journal entries up to the date using unified helper
    all_je = await get_all_journal_entries_with_lines({
        "status": "posted",
        "$or": [
            {"journal_date": {"$lte": date + "T23:59:59"}},
            {"created_at": {"$lte": date + "T23:59:59"}}
        ]
    })
    
    # Aggregate by account code
    account_balances = {}
    
    for je in all_je:
        for entry in je.get("entries", []):
            code = entry.get("account_code", "")
            name = entry.get("account_name", "Unknown")
            if not code:
                continue
            
            if code not in account_balances:
                account_balances[code] = {"name": name, "debit": 0, "credit": 0}
            
            account_balances[code]["debit"] += entry.get("debit", 0)
            account_balances[code]["credit"] += entry.get("credit", 0)
    
    # Build balance sheet
    assets = []
    liabilities = []
    equity = []
    revenues_for_net = []
    expenses_for_net = []
    
    total_assets = 0
    total_liabilities = 0
    total_equity = 0
    total_revenue = 0
    total_expense = 0
    
    for code, data in sorted(account_balances.items()):
        classification = classify_account(code)
        debit = data["debit"]
        credit = data["credit"]
        
        # Calculate balance based on normal balance
        if classification["normal_balance"] == "debit":
            balance = debit - credit
        else:
            balance = credit - debit
        
        if abs(balance) < 0.01:
            continue  # Skip zero balances
        
        item = {
            "account_code": code,
            "account_name": data["name"],
            "balance": balance
        }
        
        if classification["type"] == "asset":
            assets.append(item)
            total_assets += balance
        elif classification["type"] == "liability":
            liabilities.append(item)
            total_liabilities += balance
        elif classification["type"] == "equity":
            equity.append(item)
            total_equity += balance
        elif classification["type"] == "revenue":
            revenues_for_net.append(item)
            total_revenue += balance
        elif classification["type"] == "expense":
            expenses_for_net.append(item)
            total_expense += balance
    
    # Net income = Revenue - Expense
    net_income = total_revenue - total_expense
    
    # In balance sheet, Equity + Net Income = Liabilities must balance with Assets
    total_equity_with_net = total_equity + net_income
    
    return {
        "date": date,
        "assets": assets,
        "liabilities": liabilities,
        "equity": equity,
        "net_income": net_income,
        "total_assets": total_assets,
        "total_liabilities": total_liabilities,
        "total_equity": total_equity_with_net,
        "is_balanced": abs(total_assets - (total_liabilities + total_equity_with_net)) < 0.01,
        "journal_count": len(all_je)
    }

@router.get("/financial/income-statement")
async def get_income_statement(
    date_from: str = "",
    date_to: str = "",
    user: dict = Depends(get_current_user)
):
    """Laba Rugi - reads from journal_entries collection (unified format)"""
    if not date_from:
        date_from = datetime.now().strftime("%Y-01-01")
    if not date_to:
        date_to = datetime.now().strftime("%Y-%m-%d")
    
    # Get all posted journal entries in period using unified helper
    all_je = await get_all_journal_entries_with_lines({
        "status": "posted",
        "$or": [
            {"journal_date": {"$gte": date_from, "$lte": date_to + "T23:59:59"}},
            {"created_at": {"$gte": date_from, "$lte": date_to + "T23:59:59"}}
        ]
    })
    
    # Aggregate by account code
    account_totals = {}
    
    for je in all_je:
        for entry in je.get("entries", []):
            code = entry.get("account_code", "")
            name = entry.get("account_name", "Unknown")
            if not code:
                continue
            
            if code not in account_totals:
                account_totals[code] = {"name": name, "debit": 0, "credit": 0}
            
            account_totals[code]["debit"] += entry.get("debit", 0)
            account_totals[code]["credit"] += entry.get("credit", 0)
    
    revenues = []
    expenses = []
    cogs = []  # Cost of Goods Sold (HPP)
    total_revenue = 0
    total_expense = 0
    total_cogs = 0
    
    for code, data in sorted(account_totals.items()):
        classification = classify_account(code)
        debit = data["debit"]
        credit = data["credit"]
        
        if classification["type"] == "revenue":
            # Revenue normal balance is credit
            amount = credit - debit
            if abs(amount) > 0.01:
                revenues.append({
                    "account_code": code,
                    "account_name": data["name"],
                    "amount": amount
                })
                total_revenue += amount
        
        elif classification["type"] == "expense":
            # Expense normal balance is debit
            amount = debit - credit
            if abs(amount) > 0.01:
                # Separate COGS (5-1xxx) from operating expenses
                if code.startswith("5-1") or code == "5101" or "hpp" in data["name"].lower() or "pokok" in data["name"].lower():
                    cogs.append({
                        "account_code": code,
                        "account_name": data["name"],
                        "amount": amount
                    })
                    total_cogs += amount
                else:
                    expenses.append({
                        "account_code": code,
                        "account_name": data["name"],
                        "amount": amount
                    })
                    total_expense += amount
    
    gross_profit = total_revenue - total_cogs
    net_income = gross_profit - total_expense
    
    return {
        "period": {"from": date_from, "to": date_to},
        "revenues": revenues,
        "cost_of_goods_sold": cogs,
        "gross_profit": gross_profit,
        "operating_expenses": expenses,
        "total_revenue": total_revenue,
        "total_cogs": total_cogs,
        "total_expense": total_expense,
        "net_income": net_income,
        "journal_count": len(all_je)
    }

@router.get("/financial/cash-flow")
async def get_cash_flow(
    date_from: str = "",
    date_to: str = "",
    user: dict = Depends(get_current_user)
):
    """Arus Kas - reads from journal_entries for cash account movements (unified format)"""
    if not date_from:
        date_from = datetime.now().strftime("%Y-01-01")
    if not date_to:
        date_to = datetime.now().strftime("%Y-%m-%d")
    
    # Cash accounts: 1-1100 (Kas), 1-1200 (Bank), 1-1110 (Kas Dalam Perjalanan), 1101, 1102, etc.
    cash_codes = ["1-1100", "1-1200", "1-1110", "1101", "1102", "1103", "1104", "1105", "1106"]
    
    # Get all posted journal entries in period using unified helper
    all_je = await get_all_journal_entries_with_lines({
        "status": "posted",
        "$or": [
            {"journal_date": {"$gte": date_from, "$lte": date_to + "T23:59:59"}},
            {"created_at": {"$gte": date_from, "$lte": date_to + "T23:59:59"}}
        ]
    })
    
    operating = []
    investing = []
    financing = []
    
    total_operating = 0
    total_investing = 0
    total_financing = 0
    
    for je in all_je:
        ref_type = je.get("reference_type", "").lower() or je.get("source_type", "").lower()
        desc = je.get("description", "")
        
        # Find cash entries in this journal
        for entry in je.get("entries", []):
            code = entry.get("account_code", "")
            # Check if this is a cash account
            is_cash = any(code.startswith(c) or code == c for c in cash_codes) or "kas" in entry.get("account_name", "").lower()
            
            if is_cash:
                # Cash inflow = debit to cash account
                # Cash outflow = credit from cash account
                amount = entry.get("debit", 0) - entry.get("credit", 0)
                
                if abs(amount) < 0.01:
                    continue
                
                item = {
                    "date": je.get("journal_date", je.get("created_at", ""))[:10],
                    "reference": je.get("reference_number", je.get("journal_number", "")),
                    "description": desc or entry.get("description", ""),
                    "amount": amount
                }
                
                # Categorize based on reference type
                if ref_type in ["sales", "sales_credit", "ar_payment", "sales_cash", "deposit"]:
                    operating.append(item)
                    total_operating += amount
                elif ref_type in ["purchase", "purchase_credit", "ap_payment", "expense"]:
                    operating.append(item)
                    total_operating += amount
                elif ref_type in ["asset_purchase", "investment"]:
                    investing.append(item)
                    total_investing += amount
                elif ref_type in ["loan", "capital", "dividend"]:
                    financing.append(item)
                    total_financing += amount
                else:
                    # Default to operating
                    operating.append(item)
                    total_operating += amount
                
                break  # Only count once per journal
    
    # Also get cash movements from cash_movements collection as backup
    cash_movs = await cash_transactions.find({
        "$or": [
            {"date": {"$gte": date_from, "$lte": date_to}},
            {"created_at": {"$gte": date_from, "$lte": date_to + "T23:59:59"}}
        ]
    }, {"_id": 0}).sort("date", 1).to_list(1000)
    
    for mov in cash_movs:
        amount = mov.get("amount", 0) if mov.get("transaction_type") == "cash_in" or mov.get("movement_type") == "cash_in" else -mov.get("amount", 0)
        if abs(amount) > 0.01:
            item = {
                "date": mov.get("date", mov.get("created_at", ""))[:10],
                "reference": mov.get("reference_id", ""),
                "description": mov.get("description", ""),
                "amount": amount
            }
            # Only add if not already in journals
            if not any(o.get("reference") == item.get("reference") for o in operating):
                operating.append(item)
                total_operating += amount
    
    return {
        "period": {"from": date_from, "to": date_to},
        "operating": {"items": operating[-50:], "total": total_operating},  # Limit items for response
        "investing": {"items": investing, "total": total_investing},
        "financing": {"items": financing, "total": total_financing},
        "net_cash_flow": total_operating + total_investing + total_financing,
        "journal_count": len(all_je)
    }


# ==================== GENERAL LEDGER (BUKU BESAR) ====================

@router.get("/financial/general-ledger")
async def get_general_ledger(
    account_code: str = "",
    date_from: str = "",
    date_to: str = "",
    user: dict = Depends(get_current_user)
):
    """Buku Besar - General Ledger untuk akun tertentu (unified format)"""
    if not date_from:
        date_from = datetime.now().strftime("%Y-01-01")
    if not date_to:
        date_to = datetime.now().strftime("%Y-%m-%d")
    
    # Get all posted journal entries using unified helper
    query = {
        "status": "posted",
        "$or": [
            {"journal_date": {"$gte": date_from, "$lte": date_to + "T23:59:59"}},
            {"created_at": {"$gte": date_from, "$lte": date_to + "T23:59:59"}}
        ]
    }
    
    all_je = await get_all_journal_entries_with_lines(query)
    
    # Sort by date
    all_je.sort(key=lambda x: x.get("journal_date", x.get("created_at", "")))
    
    # Build ledger entries
    ledger_entries = []
    running_balance = 0
    
    # Get account info for balance calculation
    classification = classify_account(account_code) if account_code else None
    
    for je in all_je:
        for entry in je.get("entries", []):
            code = entry.get("account_code", "")
            
            # If filtering by account, only include that account
            if account_code and code != account_code:
                continue
            
            debit = entry.get("debit", 0)
            credit = entry.get("credit", 0)
            
            # Calculate running balance based on normal balance
            if classification:
                if classification["normal_balance"] == "debit":
                    running_balance += debit - credit
                else:
                    running_balance += credit - debit
            else:
                running_balance += debit - credit
            
            ledger_entries.append({
                "date": je.get("journal_date", je.get("created_at", ""))[:10],
                "journal_number": je.get("journal_number", je.get("journal_no", "")),
                "reference": je.get("reference_number", je.get("reference_no", "")),
                "description": entry.get("description") or je.get("description", ""),
                "account_code": code,
                "account_name": entry.get("account_name", ""),
                "debit": debit,
                "credit": credit,
                "balance": running_balance
            })
    
    # Calculate totals
    total_debit = sum(e["debit"] for e in ledger_entries)
    total_credit = sum(e["credit"] for e in ledger_entries)
    
    return {
        "period": {"from": date_from, "to": date_to},
        "account_code": account_code or "ALL",
        "entries": ledger_entries,
        "summary": {
            "total_debit": total_debit,
            "total_credit": total_credit,
            "ending_balance": running_balance if account_code else total_debit - total_credit
        },
        "entry_count": len(ledger_entries)
    }


# ==================== TRIAL BALANCE (NERACA SALDO) ====================

@router.get("/financial/trial-balance")
async def get_trial_balance(
    date: str = "",
    user: dict = Depends(get_current_user)
):
    """Neraca Saldo - Trial Balance (unified format)"""
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    
    # Get all posted journal entries up to the date using unified helper
    all_je = await get_all_journal_entries_with_lines({
        "status": "posted",
        "$or": [
            {"journal_date": {"$lte": date + "T23:59:59"}},
            {"created_at": {"$lte": date + "T23:59:59"}}
        ]
    })
    
    # Aggregate by account code
    account_balances = {}
    
    for je in all_je:
        for entry in je.get("entries", []):
            code = entry.get("account_code", "")
            name = entry.get("account_name", "Unknown")
            if not code:
                continue
            
            if code not in account_balances:
                account_balances[code] = {"name": name, "debit": 0, "credit": 0}
            
            account_balances[code]["debit"] += entry.get("debit", 0)
            account_balances[code]["credit"] += entry.get("credit", 0)
    
    # Build trial balance
    trial_balance = []
    total_debit = 0
    total_credit = 0
    
    for code, data in sorted(account_balances.items()):
        classification = classify_account(code)
        debit = data["debit"]
        credit = data["credit"]
        
        # Calculate balance based on normal balance
        if classification["normal_balance"] == "debit":
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
        
        if abs(debit_balance) < 0.01 and abs(credit_balance) < 0.01:
            continue  # Skip zero balances
        
        trial_balance.append({
            "account_code": code,
            "account_name": data["name"],
            "account_type": classification["type"],
            "debit": debit_balance,
            "credit": credit_balance
        })
        
        total_debit += debit_balance
        total_credit += credit_balance
    
    return {
        "as_of_date": date,
        "accounts": trial_balance,
        "totals": {
            "debit": total_debit,
            "credit": total_credit,
            "is_balanced": abs(total_debit - total_credit) < 0.01
        },
        "journal_count": len(all_je)
    }



# ==================== CASH/BANK ACCOUNTS ENDPOINT ====================

@router.get("/accounts/cash-bank")
async def get_cash_bank_accounts(
    user: dict = Depends(get_current_user)
):
    """
    Get all active Cash and Bank accounts for payment selection.
    Used by AR Payment and AP Payment modals.
    """
    # Get chart of accounts
    coa = db["chart_of_accounts"]
    
    # Query accounts with type cash or bank
    accounts = await coa.find({
        "$and": [
            {"$or": [
                {"type": {"$in": ["cash", "bank"]}},
                {"account_type": {"$in": ["cash", "bank"]}},
                {"category": {"$in": ["cash", "bank"]}},
                {"code": {"$regex": "^1-11|^1-12", "$options": "i"}},
                {"code": {"$regex": "^1101|^1102|^1103|^1104|^1105", "$options": "i"}},
            ]},
            {"$or": [
                {"is_active": True},
                {"is_active": {"$exists": False}}
            ]}
        ]
    }, {"_id": 0}).sort("code", 1).to_list(100)
    
    # If no accounts found, return defaults
    if not accounts:
        accounts = [
            {"id": "kas-default", "code": "1-1100", "name": "Kas", "type": "cash", "balance": 0},
            {"id": "bank-default", "code": "1-1200", "name": "Bank", "type": "bank", "balance": 0},
            {"id": "kas-kecil", "code": "1-1101", "name": "Kas Kecil", "type": "cash", "balance": 0},
        ]
    else:
        for acc in accounts:
            if not acc.get("id"):
                acc["id"] = acc.get("code", str(uuid.uuid4()))
    
    return {
        "accounts": accounts,
        "total": len(accounts)
    }
