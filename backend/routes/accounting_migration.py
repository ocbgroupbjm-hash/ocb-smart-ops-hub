# OCB TITAN - Accounting Migration & Journal Generator
# This script ensures all transactions have proper journal entries

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from database import get_db, get_active_db_name
from utils.auth import get_current_user
import uuid
import os

router = APIRouter(prefix="/api/accounting/migration", tags=["Accounting Migration"])

# ==================== STANDARD CHART OF ACCOUNTS ====================
STANDARD_COA = [
    # ASET (1-xxxx)
    {"code": "1-1000", "name": "Kas", "type": "asset", "category": "current_asset", "normal_balance": "debit"},
    {"code": "1-1001", "name": "Kas Kecil", "type": "asset", "category": "current_asset", "normal_balance": "debit"},
    {"code": "1-1002", "name": "Bank BCA", "type": "asset", "category": "current_asset", "normal_balance": "debit"},
    {"code": "1-1003", "name": "Bank Mandiri", "type": "asset", "category": "current_asset", "normal_balance": "debit"},
    {"code": "1-1010", "name": "Kas Penjualan", "type": "asset", "category": "current_asset", "normal_balance": "debit"},
    {"code": "1-2000", "name": "Piutang Usaha", "type": "asset", "category": "current_asset", "normal_balance": "debit"},
    {"code": "1-2001", "name": "Piutang Karyawan", "type": "asset", "category": "current_asset", "normal_balance": "debit"},
    {"code": "1-3000", "name": "Persediaan Barang", "type": "asset", "category": "current_asset", "normal_balance": "debit"},
    {"code": "1-4000", "name": "Uang Muka", "type": "asset", "category": "current_asset", "normal_balance": "debit"},
    {"code": "1-5000", "name": "Aktiva Tetap", "type": "asset", "category": "fixed_asset", "normal_balance": "debit"},
    {"code": "1-5001", "name": "Akumulasi Penyusutan", "type": "asset", "category": "fixed_asset", "normal_balance": "credit"},
    
    # KEWAJIBAN (2-xxxx)
    {"code": "2-1000", "name": "Hutang Usaha", "type": "liability", "category": "current_liability", "normal_balance": "credit"},
    {"code": "2-1001", "name": "Hutang Gaji", "type": "liability", "category": "current_liability", "normal_balance": "credit"},
    {"code": "2-1002", "name": "Hutang Pajak", "type": "liability", "category": "current_liability", "normal_balance": "credit"},
    {"code": "2-2000", "name": "Hutang Jangka Panjang", "type": "liability", "category": "long_term_liability", "normal_balance": "credit"},
    
    # EKUITAS (3-xxxx)
    {"code": "3-1000", "name": "Modal Disetor", "type": "equity", "category": "equity", "normal_balance": "credit"},
    {"code": "3-2000", "name": "Laba Ditahan", "type": "equity", "category": "equity", "normal_balance": "credit"},
    {"code": "3-3000", "name": "Laba Tahun Berjalan", "type": "equity", "category": "equity", "normal_balance": "credit"},
    
    # PENDAPATAN (4-xxxx)
    {"code": "4-1000", "name": "Penjualan", "type": "revenue", "category": "revenue", "normal_balance": "credit"},
    {"code": "4-1001", "name": "Diskon Penjualan", "type": "revenue", "category": "revenue", "normal_balance": "debit"},
    {"code": "4-1002", "name": "Retur Penjualan", "type": "revenue", "category": "revenue", "normal_balance": "debit"},
    {"code": "4-2000", "name": "Pendapatan Lain-lain", "type": "revenue", "category": "other_revenue", "normal_balance": "credit"},
    
    # HPP (5-xxxx)
    {"code": "5-1000", "name": "Harga Pokok Penjualan", "type": "expense", "category": "cogs", "normal_balance": "debit"},
    {"code": "5-1001", "name": "Pembelian", "type": "expense", "category": "cogs", "normal_balance": "debit"},
    {"code": "5-1002", "name": "Diskon Pembelian", "type": "expense", "category": "cogs", "normal_balance": "credit"},
    {"code": "5-1003", "name": "Retur Pembelian", "type": "expense", "category": "cogs", "normal_balance": "credit"},
    
    # BEBAN OPERASIONAL (6-xxxx)
    {"code": "6-1000", "name": "Beban Gaji", "type": "expense", "category": "operating_expense", "normal_balance": "debit"},
    {"code": "6-1001", "name": "Beban Sewa", "type": "expense", "category": "operating_expense", "normal_balance": "debit"},
    {"code": "6-1002", "name": "Beban Listrik & Air", "type": "expense", "category": "operating_expense", "normal_balance": "debit"},
    {"code": "6-1003", "name": "Beban Telepon & Internet", "type": "expense", "category": "operating_expense", "normal_balance": "debit"},
    {"code": "6-1004", "name": "Beban Penyusutan", "type": "expense", "category": "operating_expense", "normal_balance": "debit"},
    {"code": "6-1005", "name": "Beban Administrasi", "type": "expense", "category": "operating_expense", "normal_balance": "debit"},
    {"code": "6-2000", "name": "Beban Selisih Kas", "type": "expense", "category": "other_expense", "normal_balance": "debit"},
    {"code": "6-2001", "name": "Beban Selisih Stok", "type": "expense", "category": "other_expense", "normal_balance": "debit"},
    {"code": "6-3000", "name": "Beban Lain-lain", "type": "expense", "category": "other_expense", "normal_balance": "debit"},
]


async def ensure_standard_coa(db):
    """Ensure all standard accounts exist"""
    now = datetime.now(timezone.utc).isoformat()
    created = 0
    
    for acc in STANDARD_COA:
        existing = await db["accounts"].find_one({"code": acc["code"]})
        if not existing:
            acc_doc = {
                **acc,
                "id": str(uuid.uuid4()),
                "balance": 0,
                "is_active": True,
                "created_at": now
            }
            await db["accounts"].insert_one(acc_doc)
            created += 1
    
    return created


async def get_account_by_code(db, code):
    """Get account ID by code"""
    acc = await db["accounts"].find_one({"code": code})
    return acc.get("id") if acc else None


async def create_sales_journal(db, transaction):
    """Create journal entry for a sales transaction"""
    now = datetime.now(timezone.utc).isoformat()
    
    # Get account IDs
    cash_account = await get_account_by_code(db, "1-1010")  # Kas Penjualan
    ar_account = await get_account_by_code(db, "1-2000")    # Piutang Usaha
    sales_account = await get_account_by_code(db, "4-1000") # Penjualan
    
    if not cash_account or not sales_account:
        return None
    
    total = transaction.get("total", 0)
    payment_method = transaction.get("payment_method", "cash")
    is_credit = payment_method == "credit" or transaction.get("is_credit", False)
    
    # Determine debit account
    debit_account = ar_account if is_credit else cash_account
    
    journal_number = f"JV-SALES-{transaction.get('invoice_number', str(uuid.uuid4())[:8])}"
    
    journal = {
        "id": str(uuid.uuid4()),
        "journal_number": journal_number,
        "date": transaction.get("transaction_date") or transaction.get("created_at") or now,
        "description": f"Penjualan {transaction.get('invoice_number', 'N/A')}",
        "reference_type": "sales",
        "reference_id": transaction.get("id"),
        "lines": [
            {
                "id": str(uuid.uuid4()),
                "account_id": debit_account,
                "description": f"Penjualan - {transaction.get('invoice_number')}",
                "debit": total,
                "credit": 0
            },
            {
                "id": str(uuid.uuid4()),
                "account_id": sales_account,
                "description": f"Penjualan - {transaction.get('invoice_number')}",
                "debit": 0,
                "credit": total
            }
        ],
        "total_debit": total,
        "total_credit": total,
        "status": "posted",
        "created_by": "system_migration",
        "created_at": now,
        "posted_at": now
    }
    
    await db["journal_entries"].insert_one(journal)
    
    # Update transaction with journal_id
    await db["transactions"].update_one(
        {"id": transaction.get("id")},
        {"$set": {"journal_id": journal["id"]}}
    )
    
    return journal["id"]


async def create_purchase_journal(db, po):
    """Create journal entry for a purchase order"""
    now = datetime.now(timezone.utc).isoformat()
    
    # Get account IDs
    inventory_account = await get_account_by_code(db, "1-3000")  # Persediaan
    cash_account = await get_account_by_code(db, "1-1000")       # Kas
    ap_account = await get_account_by_code(db, "2-1000")         # Hutang Usaha
    
    if not inventory_account:
        return None
    
    total = po.get("total", 0) or po.get("grand_total", 0)
    is_credit = po.get("payment_terms") == "credit" or po.get("is_credit", False)
    
    # Determine credit account
    credit_account = ap_account if is_credit else cash_account
    
    journal_number = f"JV-PO-{po.get('po_number', str(uuid.uuid4())[:8])}"
    
    journal = {
        "id": str(uuid.uuid4()),
        "journal_number": journal_number,
        "date": po.get("received_at") or po.get("created_at") or now,
        "description": f"Pembelian {po.get('po_number', 'N/A')}",
        "reference_type": "purchase",
        "reference_id": po.get("id"),
        "lines": [
            {
                "id": str(uuid.uuid4()),
                "account_id": inventory_account,
                "description": f"Pembelian - {po.get('po_number')}",
                "debit": total,
                "credit": 0
            },
            {
                "id": str(uuid.uuid4()),
                "account_id": credit_account,
                "description": f"Pembelian - {po.get('po_number')}",
                "debit": 0,
                "credit": total
            }
        ],
        "total_debit": total,
        "total_credit": total,
        "status": "posted",
        "created_by": "system_migration",
        "created_at": now,
        "posted_at": now
    }
    
    await db["journal_entries"].insert_one(journal)
    
    # Update PO with journal_id
    await db["purchase_orders"].update_one(
        {"id": po.get("id")},
        {"$set": {"journal_id": journal["id"]}}
    )
    
    return journal["id"]


@router.post("/run")
async def run_accounting_migration(user: dict = Depends(get_current_user)):
    """
    Run accounting migration:
    1. Ensure standard Chart of Accounts exists
    2. Generate journals for transactions without journal_id
    3. Generate journals for purchase orders without journal_id
    """
    if user.get("role") not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Only owner/admin can run migration")
    
    db = get_db()
    db_name = get_active_db_name()
    results = {
        "database": db_name,
        "coa_created": 0,
        "sales_journals_created": 0,
        "purchase_journals_created": 0,
        "errors": []
    }
    
    # Step 1: Ensure COA
    try:
        results["coa_created"] = await ensure_standard_coa(db)
    except Exception as e:
        results["errors"].append(f"COA error: {str(e)}")
    
    # Step 2: Create sales journals (batch process, limit to 500 at a time)
    try:
        txns = await db["transactions"].find(
            {"journal_id": {"$exists": False}},
            {"_id": 0}
        ).limit(500).to_list(500)
        
        for txn in txns:
            try:
                journal_id = await create_sales_journal(db, txn)
                if journal_id:
                    results["sales_journals_created"] += 1
            except Exception as e:
                results["errors"].append(f"Sales journal error for {txn.get('invoice_number')}: {str(e)}")
    except Exception as e:
        results["errors"].append(f"Sales batch error: {str(e)}")
    
    # Step 3: Create purchase journals
    try:
        pos = await db["purchase_orders"].find(
            {"journal_id": {"$exists": False}, "status": {"$in": ["received", "completed"]}},
            {"_id": 0}
        ).limit(100).to_list(100)
        
        for po in pos:
            try:
                journal_id = await create_purchase_journal(db, po)
                if journal_id:
                    results["purchase_journals_created"] += 1
            except Exception as e:
                results["errors"].append(f"Purchase journal error for {po.get('po_number')}: {str(e)}")
    except Exception as e:
        results["errors"].append(f"Purchase batch error: {str(e)}")
    
    return results


@router.get("/status")
async def get_migration_status(user: dict = Depends(get_current_user)):
    """Get current accounting migration status"""
    db = get_db()
    db_name = get_active_db_name()
    
    # Count transactions without journal
    txn_total = await db["transactions"].count_documents({})
    txn_without_journal = await db["transactions"].count_documents({"journal_id": {"$exists": False}})
    
    # Count POs without journal
    po_total = await db["purchase_orders"].count_documents({"status": {"$in": ["received", "completed"]}})
    po_without_journal = await db["purchase_orders"].count_documents({
        "status": {"$in": ["received", "completed"]},
        "journal_id": {"$exists": False}
    })
    
    # Count COA
    coa_count = await db["accounts"].count_documents({})
    coa_standard = len(STANDARD_COA)
    
    # Count journals
    journal_count = await db["journal_entries"].count_documents({})
    
    return {
        "database": db_name,
        "transactions": {
            "total": txn_total,
            "without_journal": txn_without_journal,
            "with_journal": txn_total - txn_without_journal,
            "percentage_complete": round((txn_total - txn_without_journal) / txn_total * 100, 2) if txn_total > 0 else 100
        },
        "purchase_orders": {
            "total": po_total,
            "without_journal": po_without_journal,
            "with_journal": po_total - po_without_journal,
            "percentage_complete": round((po_total - po_without_journal) / po_total * 100, 2) if po_total > 0 else 100
        },
        "chart_of_accounts": {
            "current": coa_count,
            "standard": coa_standard,
            "complete": coa_count >= coa_standard
        },
        "journal_entries": journal_count,
        "migration_needed": txn_without_journal > 0 or po_without_journal > 0 or coa_count < coa_standard
    }


@router.get("/trial-balance")
async def get_trial_balance_from_journals(user: dict = Depends(get_current_user)):
    """
    Generate Trial Balance from journal_entries.lines
    Single Source of Truth: journal_entries collection
    """
    db = get_db()
    
    # Get all accounts for lookup
    accounts_list = await db["accounts"].find({}, {"_id": 0, "id": 1, "code": 1, "name": 1, "type": 1}).to_list(100)
    accounts_map = {acc["id"]: acc for acc in accounts_list}
    
    # Aggregate journal lines by account_id
    pipeline = [
        {"$match": {"status": "posted"}},
        {"$unwind": "$lines"},
        {"$group": {
            "_id": "$lines.account_id",
            "total_debit": {"$sum": "$lines.debit"},
            "total_credit": {"$sum": "$lines.credit"}
        }}
    ]
    
    aggregated = await db["journal_entries"].aggregate(pipeline).to_list(100)
    
    # Build trial balance
    trial_balance = []
    total_debit = 0
    total_credit = 0
    
    for item in aggregated:
        acc_id = item["_id"]
        acc = accounts_map.get(acc_id, {})
        
        debit = item["total_debit"]
        credit = item["total_credit"]
        
        # Determine balance based on account type
        acc_type = acc.get("type", "asset")
        if acc_type in ["asset", "expense"]:
            balance = debit - credit
            if balance >= 0:
                final_debit = balance
                final_credit = 0
            else:
                final_debit = 0
                final_credit = abs(balance)
        else:  # liability, equity, revenue
            balance = credit - debit
            if balance >= 0:
                final_debit = 0
                final_credit = balance
            else:
                final_debit = abs(balance)
                final_credit = 0
        
        if abs(final_debit) < 0.01 and abs(final_credit) < 0.01:
            continue
        
        trial_balance.append({
            "account_id": acc_id,
            "account_code": acc.get("code", "N/A"),
            "account_name": acc.get("name", "Unknown"),
            "account_type": acc_type,
            "debit": final_debit,
            "credit": final_credit
        })
        
        total_debit += final_debit
        total_credit += final_credit
    
    # Sort by account code
    trial_balance.sort(key=lambda x: x["account_code"])
    
    return {
        "items": trial_balance,
        "total_debit": total_debit,
        "total_credit": total_credit,
        "is_balanced": abs(total_debit - total_credit) < 0.01
    }
