"""
OCB TITAN ERP - PHASE 2 FINANCIAL CONTROL SYSTEM
Module: Auto Journal Engine (Formalized)
Following OCB TITAN AI MASTER LAW - NON-DESTRUCTIVE Development

This module provides:
1. Standardized journal generator for all modules
2. Journal templates for each transaction type
3. Automatic journal creation with validation
4. Integration with Account Derivation Engine
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from database import get_db as get_database
from routes.auth import get_current_user
from routes.rbac_middleware import require_permission
import uuid

router = APIRouter(prefix="/api/auto-journal", tags=["Auto Journal Engine"])

# ==================== JOURNAL TEMPLATES ====================

JOURNAL_TEMPLATES = {
    # SALES TEMPLATES
    "sales_cash": {
        "name": "Penjualan Tunai",
        "debit_accounts": ["kas"],
        "credit_accounts": ["pendapatan_jual", "ppn_keluaran"],
        "description_template": "Penjualan tunai {reference_no}"
    },
    "sales_credit": {
        "name": "Penjualan Kredit",
        "debit_accounts": ["piutang_usaha"],
        "credit_accounts": ["pendapatan_jual", "ppn_keluaran"],
        "description_template": "Penjualan kredit {reference_no} ke {customer_name}"
    },
    "sales_cogs": {
        "name": "HPP Penjualan",
        "debit_accounts": ["hpp"],
        "credit_accounts": ["persediaan_barang"],
        "description_template": "HPP untuk {reference_no}"
    },
    "sales_return": {
        "name": "Retur Penjualan",
        "debit_accounts": ["retur_penjualan", "ppn_keluaran"],
        "credit_accounts": ["kas", "piutang_usaha"],
        "description_template": "Retur penjualan {reference_no}"
    },
    
    # PURCHASE TEMPLATES
    "purchase_cash": {
        "name": "Pembelian Tunai",
        "debit_accounts": ["persediaan_barang", "ppn_masukan"],
        "credit_accounts": ["kas"],
        "description_template": "Pembelian tunai {reference_no}"
    },
    "purchase_credit": {
        "name": "Pembelian Kredit",
        "debit_accounts": ["persediaan_barang", "ppn_masukan"],
        "credit_accounts": ["hutang_dagang"],
        "description_template": "Pembelian kredit {reference_no} dari {supplier_name}"
    },
    "purchase_return": {
        "name": "Retur Pembelian",
        "debit_accounts": ["kas", "hutang_dagang"],
        "credit_accounts": ["retur_pembelian", "ppn_masukan"],
        "description_template": "Retur pembelian {reference_no}"
    },
    
    # AR/AP TEMPLATES
    "ar_payment_cash": {
        "name": "Pelunasan Piutang Kas",
        "debit_accounts": ["kas"],
        "credit_accounts": ["piutang_usaha"],
        "description_template": "Pelunasan piutang {reference_no} dari {customer_name}"
    },
    "ar_payment_bank": {
        "name": "Pelunasan Piutang Bank",
        "debit_accounts": ["bank"],
        "credit_accounts": ["piutang_usaha"],
        "description_template": "Pelunasan piutang {reference_no} via transfer"
    },
    "ap_payment_cash": {
        "name": "Pembayaran Hutang Kas",
        "debit_accounts": ["hutang_dagang"],
        "credit_accounts": ["kas"],
        "description_template": "Pembayaran hutang {reference_no} ke {supplier_name}"
    },
    "ap_payment_bank": {
        "name": "Pembayaran Hutang Bank",
        "debit_accounts": ["hutang_dagang"],
        "credit_accounts": ["bank"],
        "description_template": "Pembayaran hutang {reference_no} via transfer"
    },
    
    # INVENTORY TEMPLATES
    "stock_adjustment_in": {
        "name": "Penyesuaian Stok Masuk",
        "debit_accounts": ["persediaan_barang"],
        "credit_accounts": ["selisih_persediaan"],
        "description_template": "Penyesuaian stok masuk {reference_no}"
    },
    "stock_adjustment_out": {
        "name": "Penyesuaian Stok Keluar",
        "debit_accounts": ["selisih_persediaan"],
        "credit_accounts": ["persediaan_barang"],
        "description_template": "Penyesuaian stok keluar {reference_no}"
    },
    "stock_transfer": {
        "name": "Transfer Stok Antar Gudang",
        "debit_accounts": ["persediaan_barang_tujuan"],
        "credit_accounts": ["persediaan_barang_asal"],
        "description_template": "Transfer stok {reference_no}"
    },
    
    # CASH/BANK TEMPLATES
    "cash_receipt": {
        "name": "Penerimaan Kas",
        "debit_accounts": ["kas"],
        "credit_accounts": ["pendapatan_lain"],
        "description_template": "Penerimaan kas {reference_no}"
    },
    "cash_disbursement": {
        "name": "Pengeluaran Kas",
        "debit_accounts": ["biaya_operasional"],
        "credit_accounts": ["kas"],
        "description_template": "Pengeluaran kas {reference_no}"
    },
    "bank_transfer_in": {
        "name": "Transfer Masuk Bank",
        "debit_accounts": ["bank"],
        "credit_accounts": ["kas"],
        "description_template": "Transfer ke bank {reference_no}"
    },
    "bank_transfer_out": {
        "name": "Transfer Keluar Bank",
        "debit_accounts": ["kas"],
        "credit_accounts": ["bank"],
        "description_template": "Tarik dari bank {reference_no}"
    },
    
    # PAYROLL TEMPLATES
    "payroll_salary": {
        "name": "Gaji Karyawan",
        "debit_accounts": ["beban_gaji"],
        "credit_accounts": ["kas", "pph21_hutang"],
        "description_template": "Gaji karyawan {reference_no}"
    },
    
    # DEPOSIT TEMPLATES
    "deposit_cashier": {
        "name": "Setoran Kasir",
        "debit_accounts": ["kas_dalam_perjalanan"],
        "credit_accounts": ["kas_kasir"],
        "description_template": "Setoran kasir {reference_no}"
    },
    "deposit_confirm": {
        "name": "Konfirmasi Setoran",
        "debit_accounts": ["kas_pusat"],
        "credit_accounts": ["kas_dalam_perjalanan"],
        "description_template": "Konfirmasi setoran {reference_no}"
    }
}

# Account key mapping to derive accounts
ACCOUNT_KEY_MAPPING = {
    "kas": "pembayaran_tunai",
    "bank": "pembayaran_debit",
    "piutang_usaha": "pembayaran_kredit",
    "hutang_dagang": "pembayaran_kredit_pembelian",
    "persediaan_barang": "persediaan_barang",
    "pendapatan_jual": "pendapatan_jual",
    "hpp": "hpp",
    "ppn_masukan": "ppn_masukan",
    "ppn_keluaran": "ppn_keluaran",
    "retur_penjualan": "retur_potongan_penjualan",
    "retur_pembelian": "retur_potongan_pembelian",
    "selisih_persediaan": "selisih_persediaan",
    "beban_gaji": "beban_gaji",
    "pph21_hutang": "pph21_hutang",
    "kas_kasir": "kas_kasir",
    "kas_pusat": "kas_kecil_pusat",
    "kas_dalam_perjalanan": "kas_dalam_perjalanan",
    "pendapatan_lain": "pendapatan_lain",
    "biaya_operasional": "biaya_operasional"
}

# Default accounts fallback
DEFAULT_ACCOUNTS = {
    "kas": {"code": "1-1100", "name": "Kas"},
    "bank": {"code": "1-1200", "name": "Bank"},
    "piutang_usaha": {"code": "1-1300", "name": "Piutang Usaha"},
    "hutang_dagang": {"code": "2-1100", "name": "Hutang Dagang"},
    "persediaan_barang": {"code": "1-1400", "name": "Persediaan Barang"},
    "pendapatan_jual": {"code": "4-1000", "name": "Pendapatan Penjualan"},
    "hpp": {"code": "5-1000", "name": "Harga Pokok Penjualan"},
    "ppn_masukan": {"code": "1-1500", "name": "PPN Masukan"},
    "ppn_keluaran": {"code": "2-1400", "name": "PPN Keluaran"},
    "retur_penjualan": {"code": "4-2000", "name": "Retur Penjualan"},
    "retur_pembelian": {"code": "5-1100", "name": "Retur Pembelian"},
    "selisih_persediaan": {"code": "5-9100", "name": "Selisih Persediaan"},
    "beban_gaji": {"code": "5-2000", "name": "Beban Gaji"},
    "pph21_hutang": {"code": "2-1510", "name": "Hutang PPh 21"},
    "kas_kasir": {"code": "1-1100", "name": "Kas"},
    "kas_pusat": {"code": "1-1100", "name": "Kas"},
    "kas_dalam_perjalanan": {"code": "1-1110", "name": "Kas Dalam Perjalanan"},
    "pendapatan_lain": {"code": "4-9000", "name": "Pendapatan Lain-lain"},
    "biaya_operasional": {"code": "5-5000", "name": "Biaya Operasional"}
}

# ==================== PYDANTIC MODELS ====================

class JournalEntry(BaseModel):
    account_key: str
    account_code: Optional[str] = None
    account_name: Optional[str] = None
    debit: float = 0
    credit: float = 0
    description: str = ""

class AutoJournalRequest(BaseModel):
    template_code: str
    reference_type: str  # "sales", "purchase", "payment", etc.
    reference_id: str
    reference_no: str
    branch_id: Optional[str] = None
    warehouse_id: Optional[str] = None
    entries: List[JournalEntry]
    additional_info: Optional[Dict[str, Any]] = None

class JournalGenerateRequest(BaseModel):
    template_code: str
    amount: float
    tax_amount: float = 0
    reference_type: str
    reference_id: str
    reference_no: str
    branch_id: Optional[str] = None
    customer_name: Optional[str] = None
    supplier_name: Optional[str] = None
    description: Optional[str] = None

# ==================== ACCOUNT DERIVATION ====================

async def derive_account(db, account_key: str, branch_id: str = None, 
                         warehouse_id: str = None) -> Dict[str, str]:
    """
    Derive account from Account Derivation Engine
    Priority: Branch > Warehouse > Global > Default
    """
    # Map to derivation key
    derivation_key = ACCOUNT_KEY_MAPPING.get(account_key, account_key)
    
    # Priority 1: Branch mapping
    if branch_id:
        mapping = await db.account_mapping_branch.find_one({
            "branch_id": branch_id, "account_key": derivation_key
        }, {"_id": 0})
        if mapping:
            return {"code": mapping["account_code"], "name": mapping["account_name"]}
    
    # Priority 2: Warehouse mapping
    if warehouse_id:
        mapping = await db.account_mapping_warehouse.find_one({
            "warehouse_id": warehouse_id, "account_key": derivation_key
        }, {"_id": 0})
        if mapping:
            return {"code": mapping["account_code"], "name": mapping["account_name"]}
    
    # Priority 3: Global setting
    global_setting = await db.account_settings.find_one({
        "account_key": derivation_key
    }, {"_id": 0})
    if global_setting:
        return {"code": global_setting["account_code"], "name": global_setting["account_name"]}
    
    # Priority 4: Default fallback
    default = DEFAULT_ACCOUNTS.get(account_key)
    if default:
        return default
    
    return {"code": "9-9999", "name": f"Unknown ({account_key})"}

# ==================== JOURNAL GENERATOR ====================

async def generate_journal(
    db,
    template_code: str,
    entries: List[Dict[str, Any]],
    reference_type: str,
    reference_id: str,
    reference_no: str,
    branch_id: str = None,
    warehouse_id: str = None,
    user: dict = None,
    description: str = None
) -> Dict[str, Any]:
    """
    Generate journal entry using template
    
    Args:
        db: Database connection
        template_code: Template code from JOURNAL_TEMPLATES
        entries: List of journal entries with account_key, debit, credit
        reference_type: Source type (sales, purchase, etc.)
        reference_id: Source document ID
        reference_no: Source document number
        branch_id: Branch ID for account derivation
        warehouse_id: Warehouse ID for account derivation
        user: Current user
        description: Custom description
    
    Returns:
        Created journal entry
    """
    template = JOURNAL_TEMPLATES.get(template_code)
    if not template:
        raise HTTPException(status_code=400, detail=f"Template {template_code} tidak valid")
    
    journal_id = str(uuid.uuid4())
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    journal_no = f"JV-{reference_type.upper()[:3]}-{today}-{uuid.uuid4().hex[:6].upper()}"
    
    # Build journal entries with derived accounts
    journal_entries = []
    total_debit = 0
    total_credit = 0
    
    for entry in entries:
        account_key = entry.get("account_key")
        account = await derive_account(db, account_key, branch_id, warehouse_id)
        
        # Override with specific account if provided
        if entry.get("account_code"):
            account["code"] = entry["account_code"]
        if entry.get("account_name"):
            account["name"] = entry["account_name"]
        
        debit = entry.get("debit", 0)
        credit = entry.get("credit", 0)
        
        journal_entries.append({
            "account_code": account["code"],
            "account_name": account["name"],
            "debit": debit,
            "credit": credit,
            "description": entry.get("description", "")
        })
        
        total_debit += debit
        total_credit += credit
    
    # Validate balance
    if abs(total_debit - total_credit) > 0.01:
        raise HTTPException(
            status_code=400, 
            detail=f"Jurnal tidak seimbang. Debit: {total_debit}, Credit: {total_credit}"
        )
    
    user_id = user.get("user_id") or user.get("id") if user else "system"
    user_name = user.get("name", "System") if user else "System"
    
    # Generate description from template
    if not description:
        description = template["description_template"].format(
            reference_no=reference_no,
            customer_name=entries[0].get("customer_name", ""),
            supplier_name=entries[0].get("supplier_name", "")
        )
    
    journal = {
        "id": journal_id,
        "journal_no": journal_no,
        "journal_date": datetime.now(timezone.utc).isoformat(),
        "template_code": template_code,
        "template_name": template["name"],
        "source_type": reference_type,
        "source_id": reference_id,
        "reference_no": reference_no,
        "description": description,
        "entries": journal_entries,
        "total_debit": total_debit,
        "total_credit": total_credit,
        "is_balanced": True,
        "status": "posted",
        "branch_id": branch_id,
        "created_by": user_id,
        "created_by_name": user_name,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.journal_entries.insert_one(journal)
    
    return {
        "journal_id": journal_id,
        "journal_no": journal_no,
        "template_code": template_code,
        "total_debit": total_debit,
        "total_credit": total_credit,
        "status": "posted"
    }

async def generate_standard_journal(
    db,
    template_code: str,
    amount: float,
    tax_amount: float,
    reference_type: str,
    reference_id: str,
    reference_no: str,
    branch_id: str = None,
    customer_name: str = None,
    supplier_name: str = None,
    user: dict = None
) -> Dict[str, Any]:
    """
    Generate standard journal from template with automatic entry creation
    """
    template = JOURNAL_TEMPLATES.get(template_code)
    if not template:
        raise HTTPException(status_code=400, detail=f"Template {template_code} tidak valid")
    
    entries = []
    
    # Build debit entries
    for account_key in template["debit_accounts"]:
        if account_key == "ppn_masukan" or account_key == "ppn_keluaran":
            entry_amount = tax_amount
        else:
            entry_amount = amount
        
        if entry_amount > 0:
            entries.append({
                "account_key": account_key,
                "debit": entry_amount,
                "credit": 0,
                "description": f"{template['name']} - {reference_no}",
                "customer_name": customer_name,
                "supplier_name": supplier_name
            })
    
    # Build credit entries
    for account_key in template["credit_accounts"]:
        if account_key == "ppn_masukan" or account_key == "ppn_keluaran":
            entry_amount = tax_amount
        else:
            entry_amount = amount
        
        if entry_amount > 0:
            entries.append({
                "account_key": account_key,
                "debit": 0,
                "credit": entry_amount,
                "description": f"{template['name']} - {reference_no}",
                "customer_name": customer_name,
                "supplier_name": supplier_name
            })
    
    return await generate_journal(
        db, template_code, entries, reference_type, 
        reference_id, reference_no, branch_id, None, user
    )

# ==================== API ENDPOINTS ====================

@router.get("/templates")
async def list_journal_templates(user: dict = Depends(get_current_user)):
    """Get all available journal templates"""
    templates = [
        {
            "code": code,
            "name": template["name"],
            "debit_accounts": template["debit_accounts"],
            "credit_accounts": template["credit_accounts"],
            "description_template": template["description_template"]
        }
        for code, template in JOURNAL_TEMPLATES.items()
    ]
    
    return {
        "items": templates,
        "total": len(templates),
        "categories": {
            "sales": [t for t in templates if t["code"].startswith("sales")],
            "purchase": [t for t in templates if t["code"].startswith("purchase")],
            "ar_ap": [t for t in templates if t["code"].startswith("ar_") or t["code"].startswith("ap_")],
            "inventory": [t for t in templates if t["code"].startswith("stock")],
            "cash_bank": [t for t in templates if t["code"].startswith("cash") or t["code"].startswith("bank")],
            "payroll": [t for t in templates if t["code"].startswith("payroll")],
            "deposit": [t for t in templates if t["code"].startswith("deposit")]
        }
    }

@router.get("/templates/{template_code}")
async def get_journal_template(
    template_code: str,
    user: dict = Depends(get_current_user)
):
    """Get specific journal template with account details"""
    template = JOURNAL_TEMPLATES.get(template_code)
    if not template:
        raise HTTPException(status_code=404, detail=f"Template {template_code} tidak ditemukan")
    
    db = get_database()
    
    # Get account details
    debit_accounts = []
    for key in template["debit_accounts"]:
        account = await derive_account(db, key)
        debit_accounts.append({"key": key, **account})
    
    credit_accounts = []
    for key in template["credit_accounts"]:
        account = await derive_account(db, key)
        credit_accounts.append({"key": key, **account})
    
    return {
        "code": template_code,
        "name": template["name"],
        "description_template": template["description_template"],
        "debit_accounts": debit_accounts,
        "credit_accounts": credit_accounts
    }

@router.post("/generate")
async def generate_journal_endpoint(
    data: JournalGenerateRequest,
    user: dict = Depends(require_permission("accounting", "create"))
):
    """Generate journal entry using template"""
    db = get_database()
    
    result = await generate_standard_journal(
        db,
        data.template_code,
        data.amount,
        data.tax_amount,
        data.reference_type,
        data.reference_id,
        data.reference_no,
        data.branch_id,
        data.customer_name,
        data.supplier_name,
        user
    )
    
    return result

@router.post("/generate-custom")
async def generate_custom_journal(
    data: AutoJournalRequest,
    user: dict = Depends(require_permission("accounting", "create"))
):
    """Generate journal with custom entries"""
    db = get_database()
    
    entries = [e.model_dump() for e in data.entries]
    
    result = await generate_journal(
        db,
        data.template_code,
        entries,
        data.reference_type,
        data.reference_id,
        data.reference_no,
        data.branch_id,
        data.warehouse_id,
        user
    )
    
    return result

@router.get("/preview/{template_code}")
async def preview_journal(
    template_code: str,
    amount: float,
    tax_amount: float = 0,
    branch_id: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Preview journal entries without creating"""
    template = JOURNAL_TEMPLATES.get(template_code)
    if not template:
        raise HTTPException(status_code=404, detail=f"Template {template_code} tidak ditemukan")
    
    db = get_database()
    
    entries = []
    total_debit = 0
    total_credit = 0
    
    # For sales_cash: Kas (debit) = amount + tax, Pendapatan (credit) = amount, PPN (credit) = tax
    # For purchase_cash: Persediaan (debit) = amount, PPN (debit) = tax, Kas (credit) = amount + tax
    
    is_sales_cash = template_code in ["sales_cash"]
    is_purchase_cash = template_code in ["purchase_cash"]
    
    # Build debit entries
    for account_key in template["debit_accounts"]:
        account = await derive_account(db, account_key, branch_id)
        
        if "ppn" in account_key:
            entry_amount = tax_amount
        elif is_sales_cash and account_key == "kas":
            entry_amount = amount + tax_amount  # Kas terima total termasuk pajak
        else:
            entry_amount = amount
        
        if entry_amount > 0:
            entries.append({
                "account_code": account["code"],
                "account_name": account["name"],
                "debit": entry_amount,
                "credit": 0
            })
            total_debit += entry_amount
    
    # Build credit entries
    for account_key in template["credit_accounts"]:
        account = await derive_account(db, account_key, branch_id)
        
        if "ppn" in account_key:
            entry_amount = tax_amount
        elif is_purchase_cash and account_key == "kas":
            entry_amount = amount + tax_amount  # Kas bayar total termasuk pajak
        else:
            entry_amount = amount
        
        if entry_amount > 0:
            entries.append({
                "account_code": account["code"],
                "account_name": account["name"],
                "debit": 0,
                "credit": entry_amount
            })
            total_credit += entry_amount
    
    return {
        "template_code": template_code,
        "template_name": template["name"],
        "entries": entries,
        "total_debit": total_debit,
        "total_credit": total_credit,
        "is_balanced": abs(total_debit - total_credit) < 0.01
    }

@router.get("/account-mapping")
async def get_account_mapping(user: dict = Depends(get_current_user)):
    """Get account key to derivation key mapping"""
    return {
        "mapping": ACCOUNT_KEY_MAPPING,
        "defaults": DEFAULT_ACCOUNTS
    }
