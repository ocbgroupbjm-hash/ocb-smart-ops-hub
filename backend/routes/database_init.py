# OCB TITAN - Database Initialization Service
# Ensures all required master data exists before user can use the system
# This is called after successful login to verify database readiness

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
from database import get_db as get_database
from utils.auth import get_current_user
import uuid

router = APIRouter(prefix="/api/system", tags=["System Initialization"])

# ==================== DEFAULT DATA TEMPLATES ====================

DEFAULT_COA = [
    # ASSETS
    {"code": "1-1000", "name": "Kas", "category": "asset", "account_type": "detail", "normal_balance": "debit", "is_active": True},
    {"code": "1-1001", "name": "Kas Kecil", "category": "asset", "account_type": "detail", "normal_balance": "debit", "is_active": True},
    {"code": "1-1002", "name": "Bank BCA", "category": "asset", "account_type": "detail", "normal_balance": "debit", "is_active": True},
    {"code": "1-1003", "name": "Bank Mandiri", "category": "asset", "account_type": "detail", "normal_balance": "debit", "is_active": True},
    {"code": "1-1100", "name": "Piutang Usaha", "category": "asset", "account_type": "detail", "normal_balance": "debit", "is_active": True},
    {"code": "1-1200", "name": "Persediaan Barang", "category": "asset", "account_type": "detail", "normal_balance": "debit", "is_active": True},
    {"code": "1-2000", "name": "Aset Tetap", "category": "asset", "account_type": "detail", "normal_balance": "debit", "is_active": True},
    # LIABILITIES
    {"code": "2-1000", "name": "Hutang Usaha", "category": "liability", "account_type": "detail", "normal_balance": "credit", "is_active": True},
    {"code": "2-1100", "name": "Hutang Bank", "category": "liability", "account_type": "detail", "normal_balance": "credit", "is_active": True},
    {"code": "2-1200", "name": "Deposit Pelanggan", "category": "liability", "account_type": "detail", "normal_balance": "credit", "is_active": True},
    # EQUITY
    {"code": "3-1000", "name": "Modal Disetor", "category": "equity", "account_type": "detail", "normal_balance": "credit", "is_active": True},
    {"code": "3-2000", "name": "Laba Ditahan", "category": "equity", "account_type": "detail", "normal_balance": "credit", "is_active": True},
    # REVENUE
    {"code": "4-1000", "name": "Pendapatan Penjualan", "category": "revenue", "account_type": "detail", "normal_balance": "credit", "is_active": True},
    {"code": "4-2000", "name": "Pendapatan Jasa", "category": "revenue", "account_type": "detail", "normal_balance": "credit", "is_active": True},
    {"code": "4-3000", "name": "Pendapatan Lain-lain", "category": "revenue", "account_type": "detail", "normal_balance": "credit", "is_active": True},
    # EXPENSES
    {"code": "5-1000", "name": "Harga Pokok Penjualan", "category": "expense", "account_type": "detail", "normal_balance": "debit", "is_active": True},
    {"code": "5-2000", "name": "Beban Gaji", "category": "expense", "account_type": "detail", "normal_balance": "debit", "is_active": True},
    {"code": "5-3000", "name": "Beban Sewa", "category": "expense", "account_type": "detail", "normal_balance": "debit", "is_active": True},
    {"code": "5-4000", "name": "Beban Listrik & Air", "category": "expense", "account_type": "detail", "normal_balance": "debit", "is_active": True},
    {"code": "5-5000", "name": "Beban Penyusutan", "category": "expense", "account_type": "detail", "normal_balance": "debit", "is_active": True},
    {"code": "5-6000", "name": "Potongan Piutang", "category": "expense", "account_type": "detail", "normal_balance": "debit", "is_active": True},
    {"code": "5-7000", "name": "Beban Adjustment Stok", "category": "expense", "account_type": "detail", "normal_balance": "debit", "is_active": True},
]

DEFAULT_ACCOUNT_SETTINGS = [
    {"account_key": "kas", "account_code": "1-1000", "account_name": "Kas", "description": "Akun kas utama"},
    {"account_key": "bank", "account_code": "1-1002", "account_name": "Bank BCA", "description": "Akun bank utama"},
    {"account_key": "piutang_usaha", "account_code": "1-1100", "account_name": "Piutang Usaha", "description": "Akun piutang dagang"},
    {"account_key": "hutang_usaha", "account_code": "2-1000", "account_name": "Hutang Usaha", "description": "Akun hutang dagang"},
    {"account_key": "persediaan", "account_code": "1-1200", "account_name": "Persediaan Barang", "description": "Akun persediaan"},
    {"account_key": "pendapatan_penjualan", "account_code": "4-1000", "account_name": "Pendapatan Penjualan", "description": "Akun pendapatan utama"},
    {"account_key": "hpp", "account_code": "5-1000", "account_name": "Harga Pokok Penjualan", "description": "Akun HPP"},
    {"account_key": "deposit_pelanggan", "account_code": "2-1200", "account_name": "Deposit Pelanggan", "description": "Akun deposit"},
    {"account_key": "ar_account", "account_code": "1-1100", "account_name": "Piutang Usaha", "description": "Akun piutang AR"},
    {"account_key": "cash_account", "account_code": "1-1000", "account_name": "Kas", "description": "Akun kas untuk pembayaran"},
    {"account_key": "bank_account", "account_code": "1-1002", "account_name": "Bank BCA", "description": "Akun bank untuk pembayaran"},
    {"account_key": "potongan_piutang", "account_code": "5-6000", "account_name": "Potongan Piutang", "description": "Beban potongan AR"},
]

DEFAULT_NUMBERING = [
    {"type": "sales_invoice", "prefix": "INV", "current": 0, "format": "{prefix}-{branch}-{YYYYMMDD}-{seq:04d}"},
    {"type": "purchase_order", "prefix": "PO", "current": 0, "format": "{prefix}-{branch}-{YYYYMMDD}-{seq:04d}"},
    {"type": "purchase_receipt", "prefix": "GR", "current": 0, "format": "{prefix}-{branch}-{YYYYMMDD}-{seq:04d}"},
    {"type": "stock_transfer", "prefix": "TRF", "current": 0, "format": "{prefix}-{YYYYMMDD}-{seq:04d}"},
    {"type": "stock_opname", "prefix": "SO", "current": 0, "format": "{prefix}-{branch}-{YYYYMMDD}-{seq:04d}"},
    {"type": "journal", "prefix": "JV", "current": 0, "format": "{prefix}-{YYYYMMDD}-{seq:04d}"},
    {"type": "ar_payment", "prefix": "ARP", "current": 0, "format": "{prefix}-{YYYYMMDD}-{seq:04d}"},
    {"type": "ap_payment", "prefix": "APP", "current": 0, "format": "{prefix}-{YYYYMMDD}-{seq:04d}"},
    {"type": "cash_in", "prefix": "CI", "current": 0, "format": "{prefix}-{YYYYMMDD}-{seq:04d}"},
    {"type": "cash_out", "prefix": "CO", "current": 0, "format": "{prefix}-{YYYYMMDD}-{seq:04d}"},
]

DEFAULT_ROLES = [
    {
        "name": "Pemilik",
        "code": "owner",
        "level": 1,
        "description": "Pemilik bisnis dengan akses penuh",
        "all_branches": True,
        "inherit_all": True,
        "permissions": ["*"]
    },
    {
        "name": "Admin",
        "code": "admin",
        "level": 2,
        "description": "Administrator sistem",
        "all_branches": True,
        "inherit_all": False,
        "permissions": [
            "dashboard.view", "master.view", "master.create", "master.edit",
            "purchase.view", "purchase.create", "purchase.edit", "purchase.approve",
            "sales.view", "sales.create", "sales.edit",
            "inventory.view", "inventory.create", "inventory.edit",
            "accounting.view", "accounting.create", "accounting.edit",
            "reports.view", "settings.view", "settings.edit"
        ]
    },
    {
        "name": "Keuangan",
        "code": "finance",
        "level": 3,
        "description": "Staff keuangan",
        "all_branches": False,
        "inherit_all": False,
        "permissions": [
            "dashboard.view",
            "accounting.view", "accounting.create", "accounting.edit",
            "ar.view", "ar.create", "ar.payment",
            "ap.view", "ap.create", "ap.payment",
            "reports.view", "reports.finance"
        ]
    },
    {
        "name": "Gudang",
        "code": "warehouse",
        "level": 4,
        "description": "Staff gudang",
        "all_branches": False,
        "inherit_all": False,
        "permissions": [
            "dashboard.view",
            "inventory.view", "inventory.create", "inventory.edit",
            "purchase.view", "purchase.receive",
            "stock_opname.view", "stock_opname.create",
            "stock_transfer.view", "stock_transfer.create"
        ]
    },
    {
        "name": "Kasir",
        "code": "cashier",
        "level": 5,
        "description": "Kasir toko",
        "all_branches": False,
        "inherit_all": False,
        "permissions": [
            "dashboard.view",
            "pos.view", "pos.create", "pos.void",
            "sales.view", "sales.create",
            "inventory.view"
        ]
    }
]


async def ensure_database_initialized():
    """
    Ensure all required master data exists.
    This is called during login to verify database readiness.
    Returns True if database was just initialized, False if already ready.
    """
    db = get_database()
    initialized = False
    now = datetime.now(timezone.utc).isoformat()
    
    # 1. Check and create Chart of Accounts
    accounts_count = await db["accounts"].count_documents({})
    if accounts_count == 0:
        print("[DB_INIT] Creating default Chart of Accounts...")
        for acc in DEFAULT_COA:
            acc["id"] = str(uuid.uuid4())
            acc["balance"] = 0
            acc["created_at"] = now
        await db["accounts"].insert_many([{**a, "id": str(uuid.uuid4())} for a in DEFAULT_COA])
        initialized = True
    
    # 2. Check and create Account Settings
    settings_count = await db["account_settings"].count_documents({})
    if settings_count == 0:
        print("[DB_INIT] Creating default Account Settings...")
        for s in DEFAULT_ACCOUNT_SETTINGS:
            s["id"] = str(uuid.uuid4())
            s["created_at"] = now
        await db["account_settings"].insert_many([{**s, "id": str(uuid.uuid4())} for s in DEFAULT_ACCOUNT_SETTINGS])
        initialized = True
    
    # 3. Check and create Numbering Settings
    numbering_count = await db["numbering_settings"].count_documents({})
    if numbering_count == 0:
        print("[DB_INIT] Creating default Numbering Settings...")
        for n in DEFAULT_NUMBERING:
            n["id"] = str(uuid.uuid4())
            n["created_at"] = now
        await db["numbering_settings"].insert_many([{**n, "id": str(uuid.uuid4())} for n in DEFAULT_NUMBERING])
        initialized = True
    
    # 4. Check and create Default Branch
    branch_count = await db["branches"].count_documents({})
    if branch_count == 0:
        print("[DB_INIT] Creating default Branch (HQ)...")
        await db["branches"].insert_one({
            "id": str(uuid.uuid4()),
            "code": "HQ",
            "name": "Headquarters",
            "address": "Main Office",
            "phone": "",
            "is_warehouse": True,
            "is_active": True,
            "created_at": now
        })
        initialized = True
    
    # 5. Check and create Company Profile
    company = await db["company_profile"].find_one({})
    if not company:
        print("[DB_INIT] Creating default Company Profile...")
        await db["company_profile"].insert_one({
            "id": str(uuid.uuid4()),
            "name": "OCB GROUP",
            "legal_name": "PT OCB GROUP INDONESIA",
            "tax_id": "",
            "address": "",
            "phone": "",
            "email": "",
            "website": "",
            "logo_url": "",
            "base_currency": "IDR",
            "fiscal_year_start": "01",
            "created_at": now
        })
        initialized = True
    
    # 6. Check and update Roles with proper permissions
    for role_template in DEFAULT_ROLES:
        existing = await db["roles"].find_one({"code": role_template["code"]})
        if existing:
            # Update permissions if empty
            if not existing.get("permissions") or len(existing.get("permissions", [])) == 0:
                print(f"[DB_INIT] Updating permissions for role: {role_template['code']}")
                await db["roles"].update_one(
                    {"code": role_template["code"]},
                    {"$set": {
                        "permissions": role_template["permissions"],
                        "level": role_template["level"],
                        "all_branches": role_template["all_branches"],
                        "inherit_all": role_template["inherit_all"],
                        "updated_at": now
                    }}
                )
                initialized = True
        else:
            # Create new role
            print(f"[DB_INIT] Creating role: {role_template['code']}")
            role_template["id"] = str(uuid.uuid4())
            role_template["created_at"] = now
            await db["roles"].insert_one(role_template)
            initialized = True
    
    return initialized


@router.get("/init-check")
async def check_initialization(user: dict = Depends(get_current_user)):
    """
    Check if database is properly initialized.
    Called by frontend after login to verify system readiness.
    """
    db = get_database()
    
    checks = {
        "accounts": await db["accounts"].count_documents({}),
        "account_settings": await db["account_settings"].count_documents({}),
        "numbering_settings": await db["numbering_settings"].count_documents({}),
        "branches": await db["branches"].count_documents({}),
        "company_profile": await db["company_profile"].count_documents({}),
        "roles": await db["roles"].count_documents({})
    }
    
    all_ready = all(v > 0 for v in checks.values())
    
    return {
        "status": "ready" if all_ready else "incomplete",
        "checks": checks,
        "message": "Sistem siap digunakan" if all_ready else "Beberapa data dasar belum tersedia"
    }


@router.post("/initialize")
async def initialize_database(user: dict = Depends(get_current_user)):
    """
    Initialize database with default master data.
    Only runs if data doesn't already exist (safe to call multiple times).
    """
    was_initialized = await ensure_database_initialized()
    
    if was_initialized:
        return {
            "status": "initialized",
            "message": "Database berhasil diinisialisasi dengan data default"
        }
    else:
        return {
            "status": "already_ready",
            "message": "Database sudah siap, tidak ada perubahan"
        }
