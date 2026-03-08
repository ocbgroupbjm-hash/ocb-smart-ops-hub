# OCB AI TITAN - Accounting Routes
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
from database import db
from auth import get_current_user
import uuid

router = APIRouter(prefix="/api/accounting", tags=["Accounting"])

# Collections
accounts = db["accounts"]  # Chart of Accounts / Daftar Perkiraan
journals = db["journals"]  # Journal Entries
cash_transactions = db["cash_transactions"]  # Kas Masuk/Keluar/Transfer
deposits = db["deposits"]  # Deposit Pelanggan/Supplier

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
    user: dict = Depends(get_current_user)
):
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
async def get_account(account_id: str, user: dict = Depends(get_current_user)):
    account = await accounts.find_one({"id": account_id}, {"_id": 0})
    if not account:
        raise HTTPException(status_code=404, detail="Akun tidak ditemukan")
    return account

@router.post("/accounts")
async def create_account(data: AccountCreate, user: dict = Depends(get_current_user)):
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
async def update_account(account_id: str, data: AccountCreate, user: dict = Depends(get_current_user)):
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

@router.delete("/journals/{journal_id}")
async def delete_journal(journal_id: str, user: dict = Depends(get_current_user)):
    journal = await journals.find_one({"id": journal_id}, {"_id": 0})
    if not journal:
        raise HTTPException(status_code=404, detail="Jurnal tidak ditemukan")
    
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
    return {"message": "Jurnal berhasil dihapus"}

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
    
    # Create journal entry
    entries = []
    if data.transaction_type == "cash_in":
        entries = [
            {"account_id": data.account_id, "debit": data.amount, "credit": 0},
            {"account_id": data.account_id, "debit": 0, "credit": data.amount}  # Will be replaced with proper contra account
        ]
    elif data.transaction_type == "cash_out":
        entries = [
            {"account_id": data.account_id, "debit": 0, "credit": data.amount},
        ]
    elif data.transaction_type == "transfer":
        entries = [
            {"account_id": data.to_account_id, "debit": data.amount, "credit": 0},
            {"account_id": data.account_id, "debit": 0, "credit": data.amount}
        ]
    
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

# ==================== BUKU BESAR (General Ledger) ====================

@router.get("/ledger")
async def get_general_ledger(
    account_id: str = "",
    date_from: str = "",
    date_to: str = "",
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

@router.get("/trial-balance")
async def get_trial_balance(
    date_from: str = "",
    date_to: str = "",
    user: dict = Depends(get_current_user)
):
    """Neraca Saldo"""
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

@router.get("/financial/balance-sheet")
async def get_balance_sheet(date: str = "", user: dict = Depends(get_current_user)):
    """Neraca"""
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    
    all_accounts = await accounts.find({"is_active": True}, {"_id": 0}).to_list(500)
    all_journals = await journals.find({"date": {"$lte": date}}, {"_id": 0}).to_list(1000)
    
    # Calculate balances
    balances = {}
    for journal in all_journals:
        for entry in journal.get("entries", []):
            acc_id = entry.get("account_id")
            if acc_id not in balances:
                balances[acc_id] = 0
            if entry.get("debit", 0) > 0:
                balances[acc_id] += entry.get("debit", 0)
            if entry.get("credit", 0) > 0:
                balances[acc_id] -= entry.get("credit", 0)
    
    assets = []
    liabilities = []
    equity = []
    
    total_assets = 0
    total_liabilities = 0
    total_equity = 0
    
    for account in all_accounts:
        acc_id = account.get("id")
        balance = balances.get(acc_id, 0)
        if account.get("normal_balance") == "credit":
            balance = -balance
        
        item = {
            "account_code": account.get("code"),
            "account_name": account.get("name"),
            "balance": balance
        }
        
        if account.get("category") == "asset":
            assets.append(item)
            total_assets += balance
        elif account.get("category") == "liability":
            liabilities.append(item)
            total_liabilities += balance
        elif account.get("category") == "equity":
            equity.append(item)
            total_equity += balance
    
    return {
        "date": date,
        "assets": assets,
        "liabilities": liabilities,
        "equity": equity,
        "total_assets": total_assets,
        "total_liabilities": total_liabilities,
        "total_equity": total_equity,
        "is_balanced": abs(total_assets - (total_liabilities + total_equity)) < 0.01
    }

@router.get("/financial/income-statement")
async def get_income_statement(
    date_from: str = "",
    date_to: str = "",
    user: dict = Depends(get_current_user)
):
    """Laba Rugi"""
    if not date_from:
        date_from = datetime.now().strftime("%Y-01-01")
    if not date_to:
        date_to = datetime.now().strftime("%Y-%m-%d")
    
    all_accounts = await accounts.find({"is_active": True}, {"_id": 0}).to_list(500)
    all_journals = await journals.find({
        "date": {"$gte": date_from, "$lte": date_to}
    }, {"_id": 0}).to_list(1000)
    
    # Calculate balances
    balances = {}
    for journal in all_journals:
        for entry in journal.get("entries", []):
            acc_id = entry.get("account_id")
            if acc_id not in balances:
                balances[acc_id] = 0
            balances[acc_id] += entry.get("credit", 0) - entry.get("debit", 0)
    
    revenues = []
    expenses = []
    total_revenue = 0
    total_expense = 0
    
    for account in all_accounts:
        acc_id = account.get("id")
        balance = balances.get(acc_id, 0)
        
        item = {
            "account_code": account.get("code"),
            "account_name": account.get("name"),
            "amount": abs(balance)
        }
        
        if account.get("category") == "revenue" and balance != 0:
            revenues.append(item)
            total_revenue += balance
        elif account.get("category") == "expense" and balance != 0:
            item["amount"] = -balance
            expenses.append(item)
            total_expense += -balance
    
    net_income = total_revenue - total_expense
    
    return {
        "period": {"from": date_from, "to": date_to},
        "revenues": revenues,
        "expenses": expenses,
        "total_revenue": total_revenue,
        "total_expense": total_expense,
        "net_income": net_income
    }

@router.get("/financial/cash-flow")
async def get_cash_flow(
    date_from: str = "",
    date_to: str = "",
    user: dict = Depends(get_current_user)
):
    """Arus Kas"""
    if not date_from:
        date_from = datetime.now().strftime("%Y-01-01")
    if not date_to:
        date_to = datetime.now().strftime("%Y-%m-%d")
    
    transactions = await cash_transactions.find({
        "date": {"$gte": date_from, "$lte": date_to}
    }, {"_id": 0}).sort("date", 1).to_list(1000)
    
    operating = []
    investing = []
    financing = []
    
    total_operating = 0
    total_investing = 0
    total_financing = 0
    
    for trans in transactions:
        item = {
            "date": trans.get("date"),
            "description": trans.get("description"),
            "amount": trans.get("amount", 0) if trans.get("transaction_type") == "cash_in" else -trans.get("amount", 0)
        }
        # Categorize based on description or account type
        operating.append(item)
        total_operating += item["amount"]
    
    return {
        "period": {"from": date_from, "to": date_to},
        "operating": {"items": operating, "total": total_operating},
        "investing": {"items": investing, "total": total_investing},
        "financing": {"items": financing, "total": total_financing},
        "net_cash_flow": total_operating + total_investing + total_financing
    }
