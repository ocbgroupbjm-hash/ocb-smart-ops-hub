"""
OCB TITAN ERP - ACCOUNTS API
Endpoint untuk akses akun kas/bank untuk pembayaran
ARSITEKTUR: Tenant-aware, Active only, CASH & BANK type filtering
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict
from datetime import datetime, timezone
from database import get_db
from utils.auth import get_current_user
import uuid
import re

router = APIRouter(prefix="/api/accounts", tags=["Accounts"])


@router.get("/cash-bank")
async def get_cash_bank_accounts(
    payment_method: str = "",
    user: dict = Depends(get_current_user)
):
    """
    Get all active Cash and Bank accounts for payment selection.
    Used by AR Payment and AP Payment modals.
    
    ARSITEKTUR AP/AR Enterprise:
    - Filter: tenant-aware
    - Hanya akun aktif
    - Hanya akun dengan tipe CASH atau BANK
    - Jika metode = cash/tunai → prioritas kas
    - Jika metode = transfer → prioritas bank
    - Jika tidak ada hasil → tampilkan error operasional yang jelas
    """
    db = get_db()
    
    # Get tenant_id from user context if available
    tenant_id = user.get("tenant_id")
    
    # Build query for cash/bank accounts
    # STRICT filtering - only accounts explicitly marked as cash/bank
    # OR accounts with specific code patterns (1-100x for cash, 1-12xx but NOT 1201+ piutang)
    # AND name MUST contain 'Kas' or 'Bank' (not 'Piutang')
    
    base_query = {
        "$and": [
            # Only active accounts
            {"$or": [
                {"is_active": True},
                {"is_active": {"$exists": False}},
                {"status": "active"}
            ]},
            # MUST NOT be piutang/hutang
            {"name": {"$not": {"$regex": "Piutang|Hutang|Receivable|Payable", "$options": "i"}}},
            # Cash/Bank identification
            {"$or": [
                # Method 1: Explicit sub_type (primary)
                {"sub_type": {"$in": ["cash", "bank", "CASH", "BANK"]}},
                # Method 2: Name explicitly contains Kas or Bank
                {"$and": [
                    {"name": {"$regex": "^Kas|^Bank|Kas Kecil|Kas Besar|Kas Kasir|Kas Cabang|Bank BCA|Bank BRI|Bank Mandiri|Bank BNI", "$options": "i"}},
                    {"type": "asset"}
                ]}
            ]}
        ]
    }
    
    # Add tenant filter if available
    if tenant_id:
        base_query["$and"].append({"$or": [
            {"tenant_id": tenant_id},
            {"tenant_id": {"$exists": False}}
        ]})
    
    accounts = await db.chart_of_accounts.find(base_query, {"_id": 0}).sort("code", 1).to_list(100)
    
    # Process accounts - ensure each has id and determine sub_type
    processed_accounts = []
    for acc in accounts:
        account = dict(acc)
        
        # Ensure id exists
        if not account.get("id"):
            account["id"] = account.get("code", str(uuid.uuid4()))
        
        # Determine sub_type based on code or name
        code = account.get("code", "").lower()
        name = account.get("name", "").lower()
        
        if not account.get("sub_type"):
            if "bank" in name or code.startswith("1-12") or code.startswith("120"):
                account["sub_type"] = "bank"
            else:
                account["sub_type"] = "cash"
        
        processed_accounts.append(account)
    
    # Sort by payment method priority
    if payment_method in ["cash", "tunai", "kas"]:
        # Cash accounts first
        processed_accounts.sort(key=lambda x: (0 if x.get("sub_type") == "cash" else 1, x.get("code", "")))
    elif payment_method in ["transfer", "bank", "giro"]:
        # Bank accounts first
        processed_accounts.sort(key=lambda x: (0 if x.get("sub_type") == "bank" else 1, x.get("code", "")))
    
    # If still no accounts found, return proper error message
    if not processed_accounts:
        return {
            "accounts": [],
            "total": 0,
            "error": "TIDAK ADA AKUN KAS/BANK AKTIF",
            "message": "Tidak ditemukan akun Kas atau Bank yang aktif di sistem. Silakan tambahkan akun Kas/Bank di menu Chart of Accounts terlebih dahulu."
        }
    
    return {
        "accounts": processed_accounts,
        "total": len(processed_accounts)
    }


@router.get("/by-type/{account_type}")
async def get_accounts_by_type(
    account_type: str,
    user: dict = Depends(get_current_user)
):
    """Get accounts by type (cash, bank, ar, ap, asset, liability, equity, revenue, expense)"""
    db = get_db()
    
    # Get tenant_id from user context if available
    tenant_id = user.get("tenant_id")
    
    query = {
        "$or": [
            {"type": account_type},
            {"account_type": account_type},
            {"category": account_type},
            {"sub_type": account_type}
        ]
    }
    
    # Add tenant filter if available
    if tenant_id:
        query = {
            "$and": [
                query,
                {"$or": [
                    {"tenant_id": tenant_id},
                    {"tenant_id": {"$exists": False}}
                ]}
            ]
        }
    
    accounts = await db.chart_of_accounts.find(query, {"_id": 0}).sort("code", 1).to_list(100)
    
    # Ensure each account has an id
    for acc in accounts:
        if not acc.get("id"):
            acc["id"] = acc.get("code", str(uuid.uuid4()))
    
    return {
        "accounts": accounts,
        "account_type": account_type,
        "total": len(accounts)
    }


@router.post("/setup-cash-bank")
async def setup_cash_bank_accounts(
    user: dict = Depends(get_current_user)
):
    """
    Setup default cash and bank accounts if not exist.
    This ensures the system always has payment accounts available.
    """
    db = get_db()
    tenant_id = user.get("tenant_id")
    
    # Default cash/bank accounts to create
    default_accounts = [
        {
            "code": "1-1001",
            "name": "Kas",
            "type": "asset",
            "sub_type": "cash",
            "description": "Kas Umum",
            "is_active": True
        },
        {
            "code": "1-1002", 
            "name": "Bank BCA",
            "type": "asset",
            "sub_type": "bank",
            "description": "Rekening Bank BCA",
            "is_active": True
        },
        {
            "code": "1-1003",
            "name": "Bank BRI",
            "type": "asset",
            "sub_type": "bank", 
            "description": "Rekening Bank BRI",
            "is_active": True
        },
        {
            "code": "1-1004",
            "name": "Kas Kecil",
            "type": "asset",
            "sub_type": "cash",
            "description": "Kas Kecil untuk pengeluaran harian",
            "is_active": True
        }
    ]
    
    created = []
    updated = []
    
    for acc_data in default_accounts:
        # Check if account exists
        existing = await db.chart_of_accounts.find_one({"code": acc_data["code"]})
        
        if existing:
            # Update to add sub_type if missing
            if not existing.get("sub_type"):
                await db.chart_of_accounts.update_one(
                    {"code": acc_data["code"]},
                    {"$set": {"sub_type": acc_data["sub_type"], "is_active": True}}
                )
                updated.append(acc_data["code"])
        else:
            # Create new account
            acc_data["id"] = str(uuid.uuid4())
            acc_data["created_at"] = datetime.now(timezone.utc).isoformat()
            if tenant_id:
                acc_data["tenant_id"] = tenant_id
            await db.chart_of_accounts.insert_one(acc_data)
            created.append(acc_data["code"])
    
    return {
        "message": "Setup cash/bank accounts complete",
        "created": created,
        "updated": updated
    }
