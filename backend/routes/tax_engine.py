"""
OCB TITAN ERP - PHASE 2 FINANCIAL CONTROL SYSTEM
Module: Multi Tax Engine & Accounting Period Closing Enhancement
Following OCB TITAN AI MASTER LAW - NON-DESTRUCTIVE Development

This module provides:
1. Multi Tax Engine - PPN, PPh 21, PPh 22, PPh 23
2. Accounting Period Closing Enhancement
3. Auto Journal for Tax Transactions
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from database import get_db as get_database
from routes.auth import get_current_user
from routes.rbac_middleware import require_permission
import uuid

router = APIRouter(prefix="/api/tax-engine", tags=["Multi Tax Engine"])

# ==================== TAX TYPE CONSTANTS ====================

TAX_TYPES = {
    "PPN": {
        "code": "PPN",
        "name": "Pajak Pertambahan Nilai",
        "default_rate": 11.0,
        "account_key_input": "ppn_masukan",
        "account_key_output": "ppn_keluaran",
        "description": "PPN 11% untuk barang dan jasa",
        "category": "value_added_tax"
    },
    "PPNBM": {
        "code": "PPNBM",
        "name": "Pajak Penjualan Barang Mewah",
        "default_rate": 10.0,
        "account_key_input": "ppnbm_masukan",
        "account_key_output": "ppnbm_keluaran",
        "description": "PPnBM untuk barang mewah",
        "category": "luxury_tax"
    },
    "PPH21": {
        "code": "PPH21",
        "name": "Pajak Penghasilan Pasal 21",
        "default_rate": 5.0,
        "account_key_payable": "pph21_hutang",
        "account_key_expense": "beban_pph21",
        "description": "PPh 21 atas penghasilan karyawan",
        "category": "income_tax",
        "brackets": [
            {"min": 0, "max": 60000000, "rate": 5},
            {"min": 60000000, "max": 250000000, "rate": 15},
            {"min": 250000000, "max": 500000000, "rate": 25},
            {"min": 500000000, "max": 5000000000, "rate": 30},
            {"min": 5000000000, "max": None, "rate": 35}
        ]
    },
    "PPH22": {
        "code": "PPH22",
        "name": "Pajak Penghasilan Pasal 22",
        "default_rate": 1.5,
        "account_key_prepaid": "pph22_dibayar_dimuka",
        "account_key_payable": "pph22_hutang",
        "description": "PPh 22 atas impor/pembelian tertentu",
        "category": "income_tax"
    },
    "PPH23": {
        "code": "PPH23",
        "name": "Pajak Penghasilan Pasal 23",
        "default_rate": 2.0,
        "account_key_prepaid": "pph23_dibayar_dimuka",
        "account_key_payable": "pph23_hutang",
        "description": "PPh 23 atas dividen, royalti, jasa",
        "category": "income_tax",
        "service_rates": {
            "general": 2.0,
            "no_npwp": 4.0,
            "construction": 2.0,
            "rental": 2.0
        }
    },
    "PPH4_2": {
        "code": "PPH4_2",
        "name": "Pajak Penghasilan Pasal 4 ayat 2",
        "default_rate": 0.5,
        "account_key_prepaid": "pph4_2_dibayar_dimuka",
        "account_key_payable": "pph4_2_hutang",
        "description": "PPh Final UMKM",
        "category": "final_tax"
    }
}

# Default account mapping for taxes
DEFAULT_TAX_ACCOUNTS = {
    # PPN
    "ppn_masukan": {"code": "1-1500", "name": "PPN Masukan", "type": "asset"},
    "ppn_keluaran": {"code": "2-1400", "name": "PPN Keluaran", "type": "liability"},
    "ppnbm_masukan": {"code": "1-1510", "name": "PPnBM Masukan", "type": "asset"},
    "ppnbm_keluaran": {"code": "2-1410", "name": "PPnBM Keluaran", "type": "liability"},
    
    # PPh 21
    "pph21_hutang": {"code": "2-1510", "name": "Hutang PPh 21", "type": "liability"},
    "beban_pph21": {"code": "5-3100", "name": "Beban PPh 21", "type": "expense"},
    
    # PPh 22
    "pph22_dibayar_dimuka": {"code": "1-1520", "name": "PPh 22 Dibayar Dimuka", "type": "asset"},
    "pph22_hutang": {"code": "2-1520", "name": "Hutang PPh 22", "type": "liability"},
    
    # PPh 23
    "pph23_dibayar_dimuka": {"code": "1-1530", "name": "PPh 23 Dibayar Dimuka", "type": "asset"},
    "pph23_hutang": {"code": "2-1530", "name": "Hutang PPh 23", "type": "liability"},
    
    # PPh 4(2)
    "pph4_2_dibayar_dimuka": {"code": "1-1540", "name": "PPh 4(2) Dibayar Dimuka", "type": "asset"},
    "pph4_2_hutang": {"code": "2-1540", "name": "Hutang PPh 4(2)", "type": "liability"}
}

# ==================== PYDANTIC MODELS ====================

class TaxConfigCreate(BaseModel):
    tax_code: str
    tax_name: str
    tax_rate: float
    account_debit: str
    account_credit: str
    is_active: bool = True
    notes: str = ""

class TaxConfigUpdate(BaseModel):
    tax_name: Optional[str] = None
    tax_rate: Optional[float] = None
    account_debit: Optional[str] = None
    account_credit: Optional[str] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None

class TaxCalculationRequest(BaseModel):
    tax_code: str
    base_amount: float
    is_inclusive: bool = False
    branch_id: Optional[str] = None

class TaxJournalRequest(BaseModel):
    tax_code: str
    amount: float
    transaction_type: str  # "sales", "purchase", "payroll", "service"
    reference_id: str
    reference_no: str
    branch_id: Optional[str] = None
    description: str = ""

class PeriodClosingRequest(BaseModel):
    period_id: str
    closing_notes: str = ""
    
class PeriodReopenRequest(BaseModel):
    period_id: str
    reason: str
    approval_code: Optional[str] = None

# ==================== TAX ACCOUNT DERIVATION ====================

async def derive_tax_account(db, account_key: str, branch_id: str = None) -> Dict[str, str]:
    """
    Derive tax account from settings with branch override support
    Priority: Branch Mapping > Global Setting > Default
    """
    # Priority 1: Branch-specific mapping
    if branch_id:
        mapping = await db.account_mapping_branch.find_one({
            "branch_id": branch_id, "account_key": account_key
        }, {"_id": 0})
        if mapping:
            return {"code": mapping["account_code"], "name": mapping["account_name"]}
    
    # Priority 2: Global tax setting
    tax_setting = await db.tax_configurations.find_one({
        "account_key": account_key, "is_active": True
    }, {"_id": 0})
    if tax_setting:
        return {"code": tax_setting["account_code"], "name": tax_setting["account_name"]}
    
    # Priority 3: Default
    default = DEFAULT_TAX_ACCOUNTS.get(account_key)
    if default:
        return {"code": default["code"], "name": default["name"]}
    
    return {"code": "9-9999", "name": f"Unknown Tax Account ({account_key})"}

# ==================== TAX CALCULATION ENGINE ====================

async def calculate_tax(tax_code: str, base_amount: float, is_inclusive: bool = False, 
                        custom_rate: float = None) -> Dict[str, Any]:
    """
    Calculate tax amount based on tax code and base amount
    
    Args:
        tax_code: Tax type code (PPN, PPH21, etc.)
        base_amount: Amount before/including tax
        is_inclusive: If True, base_amount includes tax
        custom_rate: Override default rate
    
    Returns:
        Dict with tax_amount, net_amount, gross_amount, rate
    """
    tax_config = TAX_TYPES.get(tax_code)
    if not tax_config:
        raise HTTPException(status_code=400, detail=f"Tax code {tax_code} tidak valid")
    
    rate = custom_rate if custom_rate is not None else tax_config["default_rate"]
    
    if is_inclusive:
        # Tax is included in base_amount
        net_amount = base_amount / (1 + rate / 100)
        tax_amount = base_amount - net_amount
        gross_amount = base_amount
    else:
        # Tax is on top of base_amount
        net_amount = base_amount
        tax_amount = base_amount * (rate / 100)
        gross_amount = base_amount + tax_amount
    
    return {
        "tax_code": tax_code,
        "tax_name": tax_config["name"],
        "rate": rate,
        "net_amount": round(net_amount, 2),
        "tax_amount": round(tax_amount, 2),
        "gross_amount": round(gross_amount, 2),
        "is_inclusive": is_inclusive
    }

async def calculate_pph21(gross_salary: float, ptkp: str = "TK/0") -> Dict[str, Any]:
    """
    Calculate PPh 21 for payroll using progressive rate
    
    Args:
        gross_salary: Annual gross salary
        ptkp: PTKP status (TK/0, K/0, K/1, K/2, K/3)
    
    Returns:
        Dict with tax details
    """
    # PTKP 2024 (Penghasilan Tidak Kena Pajak)
    ptkp_values = {
        "TK/0": 54000000,  # Tidak Kawin, 0 tanggungan
        "TK/1": 58500000,
        "TK/2": 63000000,
        "TK/3": 67500000,
        "K/0": 58500000,   # Kawin, 0 tanggungan
        "K/1": 63000000,
        "K/2": 67500000,
        "K/3": 72000000,
        "K/I/0": 112500000,  # Kawin + Istri bekerja
        "K/I/1": 117000000,
        "K/I/2": 121500000,
        "K/I/3": 126000000
    }
    
    ptkp_amount = ptkp_values.get(ptkp, 54000000)
    pkp = max(0, gross_salary - ptkp_amount)  # Penghasilan Kena Pajak
    
    # Progressive tax calculation
    brackets = TAX_TYPES["PPH21"]["brackets"]
    total_tax = 0
    remaining_pkp = pkp
    tax_breakdown = []
    
    for bracket in brackets:
        if remaining_pkp <= 0:
            break
        
        bracket_min = bracket["min"]
        bracket_max = bracket["max"] if bracket["max"] else float('inf')
        rate = bracket["rate"]
        
        taxable_in_bracket = min(remaining_pkp, bracket_max - bracket_min)
        tax_in_bracket = taxable_in_bracket * (rate / 100)
        
        if taxable_in_bracket > 0:
            tax_breakdown.append({
                "bracket": f"{bracket_min:,} - {bracket_max:,}" if bracket["max"] else f"> {bracket_min:,}",
                "rate": rate,
                "taxable_amount": taxable_in_bracket,
                "tax_amount": tax_in_bracket
            })
        
        total_tax += tax_in_bracket
        remaining_pkp -= taxable_in_bracket
    
    return {
        "tax_code": "PPH21",
        "gross_salary": gross_salary,
        "ptkp_status": ptkp,
        "ptkp_amount": ptkp_amount,
        "pkp": pkp,
        "annual_tax": round(total_tax, 0),
        "monthly_tax": round(total_tax / 12, 0),
        "effective_rate": round((total_tax / gross_salary) * 100, 2) if gross_salary > 0 else 0,
        "breakdown": tax_breakdown
    }

# ==================== TAX JOURNAL GENERATOR ====================

async def create_tax_journal(
    db,
    tax_code: str,
    amount: float,
    transaction_type: str,
    reference_id: str,
    reference_no: str,
    branch_id: str = None,
    user: dict = None,
    description: str = ""
) -> Dict[str, Any]:
    """
    Create automatic journal entry for tax transaction
    
    Args:
        db: Database connection
        tax_code: Tax type code
        amount: Tax amount
        transaction_type: "sales", "purchase", "payroll", "service"
        reference_id: Source transaction ID
        reference_no: Source transaction number
        branch_id: Branch ID
        user: Current user
        description: Journal description
    """
    tax_config = TAX_TYPES.get(tax_code)
    if not tax_config:
        raise HTTPException(status_code=400, detail=f"Tax code {tax_code} tidak valid")
    
    journal_id = str(uuid.uuid4())
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    journal_no = f"JV-TAX-{tax_code}-{today}-{uuid.uuid4().hex[:6].upper()}"
    
    # Determine debit/credit accounts based on transaction type
    if transaction_type == "sales":
        # Sales tax: Debit nothing, Credit PPN Keluaran (liability)
        debit_account = await derive_tax_account(db, "ppn_masukan", branch_id)  # Clearing
        credit_account = await derive_tax_account(db, tax_config.get("account_key_output", "ppn_keluaran"), branch_id)
    elif transaction_type == "purchase":
        # Purchase tax: Debit PPN Masukan (asset), Credit nothing
        debit_account = await derive_tax_account(db, tax_config.get("account_key_input", "ppn_masukan"), branch_id)
        credit_account = await derive_tax_account(db, "ppn_keluaran", branch_id)  # Clearing
    elif transaction_type == "payroll":
        # Payroll tax: Debit Expense, Credit Hutang PPh
        debit_account = await derive_tax_account(db, tax_config.get("account_key_expense", "beban_pph21"), branch_id)
        credit_account = await derive_tax_account(db, tax_config.get("account_key_payable", "pph21_hutang"), branch_id)
    elif transaction_type == "service":
        # Service tax withheld: Debit Prepaid, Credit Payable
        debit_account = await derive_tax_account(db, tax_config.get("account_key_prepaid", "pph23_dibayar_dimuka"), branch_id)
        credit_account = await derive_tax_account(db, tax_config.get("account_key_payable", "pph23_hutang"), branch_id)
    else:
        raise HTTPException(status_code=400, detail=f"Transaction type {transaction_type} tidak valid")
    
    user_id = user.get("user_id") or user.get("id") if user else "system"
    user_name = user.get("name", "System") if user else "System"
    
    journal_entry = {
        "id": journal_id,
        "journal_no": journal_no,
        "journal_date": datetime.now(timezone.utc).isoformat(),
        "source_type": f"tax_{transaction_type}",
        "source_id": reference_id,
        "reference_no": reference_no,
        "tax_code": tax_code,
        "description": description or f"Jurnal pajak {tax_config['name']} untuk {reference_no}",
        "entries": [
            {
                "account_code": debit_account["code"],
                "account_name": debit_account["name"],
                "debit": amount,
                "credit": 0,
                "description": f"{tax_config['name']} - {reference_no}"
            },
            {
                "account_code": credit_account["code"],
                "account_name": credit_account["name"],
                "debit": 0,
                "credit": amount,
                "description": f"{tax_config['name']} - {reference_no}"
            }
        ],
        "total_debit": amount,
        "total_credit": amount,
        "is_balanced": True,
        "status": "posted",
        "branch_id": branch_id,
        "created_by": user_id,
        "created_by_name": user_name,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.journal_entries.insert_one(journal_entry)
    
    return {
        "journal_id": journal_id,
        "journal_no": journal_no,
        "tax_code": tax_code,
        "amount": amount,
        "status": "posted"
    }

# ==================== API ENDPOINTS ====================

@router.get("/tax-types")
async def list_tax_types(user: dict = Depends(get_current_user)):
    """Get all available tax types with configuration"""
    return {
        "items": list(TAX_TYPES.values()),
        "total": len(TAX_TYPES)
    }

@router.get("/tax-accounts")
async def list_tax_accounts(user: dict = Depends(get_current_user)):
    """Get default tax account mapping"""
    return {
        "items": [
            {"account_key": k, **v} for k, v in DEFAULT_TAX_ACCOUNTS.items()
        ],
        "total": len(DEFAULT_TAX_ACCOUNTS)
    }

@router.get("/configurations")
async def list_tax_configurations(user: dict = Depends(get_current_user)):
    """Get custom tax configurations"""
    db = get_database()
    configs = await db.tax_configurations.find({"is_active": True}, {"_id": 0}).to_list(100)
    
    if not configs:
        # Return defaults if no custom configs
        configs = [
            {
                "id": f"default-{code}",
                "tax_code": code,
                "tax_name": config["name"],
                "tax_rate": config["default_rate"],
                "category": config["category"],
                "is_default": True
            }
            for code, config in TAX_TYPES.items()
        ]
    
    return {"items": configs, "total": len(configs)}

@router.post("/configurations")
async def create_tax_configuration(
    data: TaxConfigCreate,
    user: dict = Depends(require_permission("settings", "create"))
):
    """Create custom tax configuration"""
    db = get_database()
    
    # Check if already exists
    existing = await db.tax_configurations.find_one({"tax_code": data.tax_code})
    if existing:
        raise HTTPException(status_code=400, detail=f"Konfigurasi pajak {data.tax_code} sudah ada")
    
    config = {
        "id": str(uuid.uuid4()),
        "tax_code": data.tax_code,
        "tax_name": data.tax_name,
        "tax_rate": data.tax_rate,
        "account_debit": data.account_debit,
        "account_credit": data.account_credit,
        "is_active": data.is_active,
        "notes": data.notes,
        "created_by": user.get("user_id") or user.get("id"),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.tax_configurations.insert_one(config)
    config.pop("_id", None)
    
    return config

@router.put("/configurations/{config_id}")
async def update_tax_configuration(
    config_id: str,
    data: TaxConfigUpdate,
    user: dict = Depends(require_permission("settings", "edit"))
):
    """Update tax configuration"""
    db = get_database()
    
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    update_data["updated_by"] = user.get("user_id") or user.get("id")
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.tax_configurations.update_one(
        {"id": config_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Konfigurasi pajak tidak ditemukan")
    
    return {"success": True, "message": "Konfigurasi pajak berhasil diperbarui"}

@router.post("/calculate")
async def calculate_tax_endpoint(
    data: TaxCalculationRequest,
    user: dict = Depends(get_current_user)
):
    """Calculate tax for given amount"""
    result = await calculate_tax(
        data.tax_code,
        data.base_amount,
        data.is_inclusive
    )
    return result

@router.post("/calculate-pph21")
async def calculate_pph21_endpoint(
    gross_salary: float,
    ptkp: str = "TK/0",
    user: dict = Depends(get_current_user)
):
    """Calculate PPh 21 with progressive rate"""
    result = await calculate_pph21(gross_salary, ptkp)
    return result

@router.post("/create-journal")
async def create_tax_journal_endpoint(
    data: TaxJournalRequest,
    user: dict = Depends(require_permission("accounting", "create"))
):
    """Create tax journal entry"""
    db = get_database()
    
    result = await create_tax_journal(
        db,
        data.tax_code,
        data.amount,
        data.transaction_type,
        data.reference_id,
        data.reference_no,
        data.branch_id,
        user,
        data.description
    )
    
    return result

# ==================== ACCOUNTING PERIOD CLOSING ENHANCEMENT ====================

PERIOD_CLOSING_PERMISSIONS = {
    "close": ["owner", "admin", "finance_manager"],
    "reopen": ["owner"],  # Only owner can reopen
    "lock": ["owner"]     # Only owner can lock permanently
}

@router.get("/period-status/{period_id}")
async def get_period_status(
    period_id: str,
    user: dict = Depends(get_current_user)
):
    """Get period status with closing eligibility check"""
    db = get_database()
    
    period = await db.fiscal_periods.find_one({"id": period_id}, {"_id": 0})
    if not period:
        raise HTTPException(status_code=404, detail="Periode tidak ditemukan")
    
    # Check if there are unposted journals
    unposted_journals = await db.journal_entries.count_documents({
        "journal_date": {"$gte": period["start_date"], "$lte": period["end_date"]},
        "status": {"$ne": "posted"}
    })
    
    # Check journal balance
    balance_check = await db.journal_entries.aggregate([
        {
            "$match": {
                "journal_date": {"$gte": period["start_date"], "$lte": period["end_date"]}
            }
        },
        {
            "$group": {
                "_id": None,
                "total_debit": {"$sum": "$total_debit"},
                "total_credit": {"$sum": "$total_credit"}
            }
        }
    ]).to_list(1)
    
    is_balanced = True
    total_debit = 0
    total_credit = 0
    
    if balance_check:
        total_debit = balance_check[0].get("total_debit", 0)
        total_credit = balance_check[0].get("total_credit", 0)
        is_balanced = abs(total_debit - total_credit) < 0.01
    
    # Check user permission
    user_role = user.get("role", "")
    can_close = user_role in PERIOD_CLOSING_PERMISSIONS["close"]
    can_reopen = user_role in PERIOD_CLOSING_PERMISSIONS["reopen"]
    can_lock = user_role in PERIOD_CLOSING_PERMISSIONS["lock"]
    
    return {
        "period": period,
        "closing_eligibility": {
            "can_close": can_close and unposted_journals == 0 and is_balanced,
            "can_reopen": can_reopen and period["status"] == "closed",
            "can_lock": can_lock and period["status"] == "closed",
            "unposted_journals": unposted_journals,
            "is_balanced": is_balanced,
            "total_debit": total_debit,
            "total_credit": total_credit,
            "balance_difference": abs(total_debit - total_credit)
        },
        "user_permissions": {
            "can_close": can_close,
            "can_reopen": can_reopen,
            "can_lock": can_lock
        }
    }

@router.post("/period-close")
async def close_accounting_period(
    data: PeriodClosingRequest,
    user: dict = Depends(get_current_user)
):
    """Close accounting period with validation"""
    db = get_database()
    
    # Check permission
    user_role = user.get("role", "")
    if user_role not in PERIOD_CLOSING_PERMISSIONS["close"]:
        raise HTTPException(
            status_code=403, 
            detail="Anda tidak memiliki izin untuk menutup periode. Diperlukan: Owner, Admin, atau Finance Manager"
        )
    
    period = await db.fiscal_periods.find_one({"id": data.period_id}, {"_id": 0})
    if not period:
        raise HTTPException(status_code=404, detail="Periode tidak ditemukan")
    
    if period["status"] != "open":
        raise HTTPException(status_code=400, detail=f"Periode sudah {period['status']}, tidak dapat ditutup")
    
    # Validation checks
    unposted = await db.journal_entries.count_documents({
        "journal_date": {"$gte": period["start_date"], "$lte": period["end_date"]},
        "status": {"$ne": "posted"}
    })
    
    if unposted > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"Masih ada {unposted} jurnal yang belum diposting. Posting semua jurnal terlebih dahulu."
        )
    
    # Close period
    await db.fiscal_periods.update_one(
        {"id": data.period_id},
        {"$set": {
            "status": "closed",
            "closed_at": datetime.now(timezone.utc).isoformat(),
            "closed_by": user.get("user_id") or user.get("id"),
            "closed_by_name": user.get("name"),
            "closing_notes": data.closing_notes,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Log activity
    await db.audit_logs.insert_one({
        "id": str(uuid.uuid4()),
        "action": "period_close",
        "module": "accounting",
        "target_id": data.period_id,
        "description": f"Menutup periode {period['period_name']}",
        "user_id": user.get("user_id") or user.get("id"),
        "user_name": user.get("name"),
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    return {
        "success": True,
        "message": f"Periode {period['period_name']} berhasil ditutup",
        "new_status": "closed"
    }

@router.post("/period-reopen")
async def reopen_accounting_period(
    data: PeriodReopenRequest,
    user: dict = Depends(get_current_user)
):
    """Reopen closed period (Owner only)"""
    db = get_database()
    
    # Check permission - Only owner can reopen
    user_role = user.get("role", "")
    if user_role not in PERIOD_CLOSING_PERMISSIONS["reopen"]:
        raise HTTPException(
            status_code=403, 
            detail="Hanya Owner yang dapat membuka kembali periode yang sudah ditutup"
        )
    
    period = await db.fiscal_periods.find_one({"id": data.period_id}, {"_id": 0})
    if not period:
        raise HTTPException(status_code=404, detail="Periode tidak ditemukan")
    
    if period["status"] == "locked":
        raise HTTPException(status_code=400, detail="Periode sudah LOCKED dan tidak dapat dibuka kembali")
    
    if period["status"] == "open":
        raise HTTPException(status_code=400, detail="Periode sudah dalam status OPEN")
    
    # Reopen period
    await db.fiscal_periods.update_one(
        {"id": data.period_id},
        {"$set": {
            "status": "open",
            "reopened_at": datetime.now(timezone.utc).isoformat(),
            "reopened_by": user.get("user_id") or user.get("id"),
            "reopened_by_name": user.get("name"),
            "reopen_reason": data.reason,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Log activity
    await db.audit_logs.insert_one({
        "id": str(uuid.uuid4()),
        "action": "period_reopen",
        "module": "accounting",
        "target_id": data.period_id,
        "description": f"Membuka kembali periode {period['period_name']}. Alasan: {data.reason}",
        "user_id": user.get("user_id") or user.get("id"),
        "user_name": user.get("name"),
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    return {
        "success": True,
        "message": f"Periode {period['period_name']} berhasil dibuka kembali",
        "new_status": "open"
    }

# ==================== INITIALIZE DEFAULT TAX ACCOUNTS ====================

@router.post("/initialize-defaults")
async def initialize_default_tax_accounts(user: dict = Depends(require_permission("settings", "create"))):
    """Initialize default tax accounts in chart of accounts"""
    db = get_database()
    
    count = 0
    for key, account in DEFAULT_TAX_ACCOUNTS.items():
        existing = await db.chart_of_accounts.find_one({"code": account["code"]})
        if not existing:
            coa_entry = {
                "id": str(uuid.uuid4()),
                "code": account["code"],
                "name": account["name"],
                "type": account["type"],
                "category": "tax",
                "is_active": True,
                "created_by": user.get("user_id") or user.get("id"),
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.chart_of_accounts.insert_one(coa_entry)
            count += 1
    
    return {"success": True, "initialized": count, "message": f"{count} akun pajak berhasil diinisialisasi"}
