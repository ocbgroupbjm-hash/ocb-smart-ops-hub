"""
OCB TITAN ERP - ACCOUNTS API
Endpoint untuk akses akun kas/bank untuk pembayaran
"""

from fastapi import APIRouter, Depends
from typing import List, Dict
from datetime import datetime, timezone
from database import get_db
from utils.auth import get_current_user
import uuid

router = APIRouter(prefix="/api/accounts", tags=["Accounts"])


@router.get("/cash-bank")
async def get_cash_bank_accounts(
    user: dict = Depends(get_current_user)
):
    """
    Get all active Cash and Bank accounts for payment selection.
    Used by AR Payment and AP Payment modals.
    
    Query: chart_of_accounts WHERE account_type IN ('cash', 'bank') AND is_active = true
    """
    db = get_db()
    
    # Query accounts with type cash or bank
    accounts = await db.chart_of_accounts.find({
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
    
    # If no accounts found from COA, return default ones
    if not accounts:
        accounts = [
            {"id": "kas-default", "code": "1-1100", "name": "Kas", "type": "cash", "balance": 0},
            {"id": "bank-default", "code": "1-1200", "name": "Bank", "type": "bank", "balance": 0},
            {"id": "kas-kecil", "code": "1-1101", "name": "Kas Kecil", "type": "cash", "balance": 0},
        ]
    else:
        # Ensure each account has an id
        for acc in accounts:
            if not acc.get("id"):
                acc["id"] = acc.get("code", str(uuid.uuid4()))
    
    return {
        "accounts": accounts,
        "total": len(accounts)
    }


@router.get("/by-type/{account_type}")
async def get_accounts_by_type(
    account_type: str,
    user: dict = Depends(get_current_user)
):
    """Get accounts by type (cash, bank, ar, ap, etc)"""
    db = get_db()
    
    accounts = await db.chart_of_accounts.find({
        "$or": [
            {"type": account_type},
            {"account_type": account_type},
            {"category": account_type}
        ]
    }, {"_id": 0}).sort("code", 1).to_list(100)
    
    return {
        "accounts": accounts,
        "account_type": account_type,
        "total": len(accounts)
    }
