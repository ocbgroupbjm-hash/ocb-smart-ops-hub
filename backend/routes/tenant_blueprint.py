# OCB TITAN - Tenant Blueprint & Migration Engine
# Single Source of Truth for all business databases
# All tenants must follow the same ERP blueprint

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from utils.auth import get_current_user
import uuid
import os

router = APIRouter(prefix="/api/tenant", tags=["Tenant Management"])

# ==================== BLUEPRINT VERSION ====================
CURRENT_BLUEPRINT_VERSION = "2.0.0"  # Updated for full collection sync
CURRENT_MIGRATION_VERSION = 2

# ==================== REQUIRED COLLECTIONS ====================
# All tenant databases MUST have these collections
REQUIRED_COLLECTIONS = [
    "users",
    "roles",
    "branches",
    "company_profile",
    "account_settings",
    "numbering_settings",
    "accounts",
    "products",
    "customers",
    "suppliers",
    "stock_movements",
    "transactions",
    "journal_entries",
    "product_stocks",
    "categories",
    "units",
    "brands",
    "purchase_orders",
    "sales_invoices",
    "accounts_receivable",
    "accounts_payable",
    "ar_payments",
    "ap_payments",
    "cash_movements",
    "audit_logs",
]

# ==================== DEFAULT DATA TEMPLATES ====================

DEFAULT_COA = [
    # ASSETS (1-xxxx)
    {"code": "1-1000", "name": "Kas", "category": "asset", "account_type": "detail", "normal_balance": "debit", "is_active": True, "is_cash": True},
    {"code": "1-1001", "name": "Kas Kecil", "category": "asset", "account_type": "detail", "normal_balance": "debit", "is_active": True, "is_cash": True},
    {"code": "1-1002", "name": "Bank BCA", "category": "asset", "account_type": "detail", "normal_balance": "debit", "is_active": True, "is_bank": True},
    {"code": "1-1003", "name": "Bank Mandiri", "category": "asset", "account_type": "detail", "normal_balance": "debit", "is_active": True, "is_bank": True},
    {"code": "1-1100", "name": "Piutang Usaha", "category": "asset", "account_type": "detail", "normal_balance": "debit", "is_active": True},
    {"code": "1-1200", "name": "Persediaan Barang", "category": "asset", "account_type": "detail", "normal_balance": "debit", "is_active": True},
    {"code": "1-2000", "name": "Aset Tetap", "category": "asset", "account_type": "detail", "normal_balance": "debit", "is_active": True},
    {"code": "1-2100", "name": "Akumulasi Penyusutan", "category": "asset", "account_type": "detail", "normal_balance": "credit", "is_active": True},
    # LIABILITIES (2-xxxx)
    {"code": "2-1000", "name": "Hutang Usaha", "category": "liability", "account_type": "detail", "normal_balance": "credit", "is_active": True},
    {"code": "2-1100", "name": "Hutang Bank", "category": "liability", "account_type": "detail", "normal_balance": "credit", "is_active": True},
    {"code": "2-1200", "name": "Deposit Pelanggan", "category": "liability", "account_type": "detail", "normal_balance": "credit", "is_active": True},
    {"code": "2-1300", "name": "Hutang Pajak", "category": "liability", "account_type": "detail", "normal_balance": "credit", "is_active": True},
    # EQUITY (3-xxxx)
    {"code": "3-1000", "name": "Modal Disetor", "category": "equity", "account_type": "detail", "normal_balance": "credit", "is_active": True},
    {"code": "3-2000", "name": "Laba Ditahan", "category": "equity", "account_type": "detail", "normal_balance": "credit", "is_active": True},
    {"code": "3-3000", "name": "Laba Tahun Berjalan", "category": "equity", "account_type": "detail", "normal_balance": "credit", "is_active": True},
    # REVENUE (4-xxxx)
    {"code": "4-1000", "name": "Pendapatan Penjualan", "category": "revenue", "account_type": "detail", "normal_balance": "credit", "is_active": True},
    {"code": "4-2000", "name": "Pendapatan Jasa", "category": "revenue", "account_type": "detail", "normal_balance": "credit", "is_active": True},
    {"code": "4-3000", "name": "Pendapatan Lain-lain", "category": "revenue", "account_type": "detail", "normal_balance": "credit", "is_active": True},
    {"code": "4-4000", "name": "Diskon Penjualan", "category": "revenue", "account_type": "detail", "normal_balance": "debit", "is_active": True},
    {"code": "4-5000", "name": "Retur Penjualan", "category": "revenue", "account_type": "detail", "normal_balance": "debit", "is_active": True},
    # EXPENSES (5-xxxx)
    {"code": "5-1000", "name": "Harga Pokok Penjualan", "category": "expense", "account_type": "detail", "normal_balance": "debit", "is_active": True},
    {"code": "5-2000", "name": "Beban Gaji", "category": "expense", "account_type": "detail", "normal_balance": "debit", "is_active": True},
    {"code": "5-3000", "name": "Beban Sewa", "category": "expense", "account_type": "detail", "normal_balance": "debit", "is_active": True},
    {"code": "5-4000", "name": "Beban Listrik & Air", "category": "expense", "account_type": "detail", "normal_balance": "debit", "is_active": True},
    {"code": "5-5000", "name": "Beban Penyusutan", "category": "expense", "account_type": "detail", "normal_balance": "debit", "is_active": True},
    {"code": "5-6000", "name": "Potongan Piutang", "category": "expense", "account_type": "detail", "normal_balance": "debit", "is_active": True},
    {"code": "5-7000", "name": "Beban Adjustment Stok", "category": "expense", "account_type": "detail", "normal_balance": "debit", "is_active": True},
    {"code": "5-8000", "name": "Beban Operasional Lain", "category": "expense", "account_type": "detail", "normal_balance": "debit", "is_active": True},
]

DEFAULT_ACCOUNT_SETTINGS = [
    {"account_key": "kas", "account_code": "1-1000", "account_name": "Kas", "description": "Akun kas utama"},
    {"account_key": "kas_kecil", "account_code": "1-1001", "account_name": "Kas Kecil", "description": "Akun kas kecil"},
    {"account_key": "bank", "account_code": "1-1002", "account_name": "Bank BCA", "description": "Akun bank utama"},
    {"account_key": "piutang_usaha", "account_code": "1-1100", "account_name": "Piutang Usaha", "description": "Akun piutang dagang"},
    {"account_key": "hutang_usaha", "account_code": "2-1000", "account_name": "Hutang Usaha", "description": "Akun hutang dagang"},
    {"account_key": "persediaan", "account_code": "1-1200", "account_name": "Persediaan Barang", "description": "Akun persediaan"},
    {"account_key": "pendapatan_penjualan", "account_code": "4-1000", "account_name": "Pendapatan Penjualan", "description": "Akun pendapatan utama"},
    {"account_key": "hpp", "account_code": "5-1000", "account_name": "Harga Pokok Penjualan", "description": "Akun HPP"},
    {"account_key": "deposit_pelanggan", "account_code": "2-1200", "account_name": "Deposit Pelanggan", "description": "Akun deposit"},
    {"account_key": "ar_account", "account_code": "1-1100", "account_name": "Piutang Usaha", "description": "Akun piutang AR"},
    {"account_key": "ap_account", "account_code": "2-1000", "account_name": "Hutang Usaha", "description": "Akun hutang AP"},
    {"account_key": "cash_account", "account_code": "1-1000", "account_name": "Kas", "description": "Akun kas untuk pembayaran"},
    {"account_key": "bank_account", "account_code": "1-1002", "account_name": "Bank BCA", "description": "Akun bank untuk pembayaran"},
    {"account_key": "potongan_piutang", "account_code": "5-6000", "account_name": "Potongan Piutang", "description": "Beban potongan AR"},
    {"account_key": "diskon_penjualan", "account_code": "4-4000", "account_name": "Diskon Penjualan", "description": "Diskon penjualan"},
    {"account_key": "retur_penjualan", "account_code": "4-5000", "account_name": "Retur Penjualan", "description": "Retur penjualan"},
]

DEFAULT_NUMBERING = [
    {"type": "sales_invoice", "prefix": "INV", "current": 0, "format": "{prefix}-{branch}-{YYYYMMDD}-{seq:04d}"},
    {"type": "purchase_order", "prefix": "PO", "current": 0, "format": "{prefix}-{branch}-{YYYYMMDD}-{seq:04d}"},
    {"type": "purchase_receipt", "prefix": "GR", "current": 0, "format": "{prefix}-{branch}-{YYYYMMDD}-{seq:04d}"},
    {"type": "purchase_invoice", "prefix": "PI", "current": 0, "format": "{prefix}-{branch}-{YYYYMMDD}-{seq:04d}"},
    {"type": "purchase_return", "prefix": "PR", "current": 0, "format": "{prefix}-{branch}-{YYYYMMDD}-{seq:04d}"},
    {"type": "sales_return", "prefix": "SR", "current": 0, "format": "{prefix}-{branch}-{YYYYMMDD}-{seq:04d}"},
    {"type": "stock_transfer", "prefix": "TRF", "current": 0, "format": "{prefix}-{YYYYMMDD}-{seq:04d}"},
    {"type": "stock_opname", "prefix": "SO", "current": 0, "format": "{prefix}-{branch}-{YYYYMMDD}-{seq:04d}"},
    {"type": "journal", "prefix": "JV", "current": 0, "format": "{prefix}-{YYYYMMDD}-{seq:04d}"},
    {"type": "ar_payment", "prefix": "ARP", "current": 0, "format": "{prefix}-{YYYYMMDD}-{seq:04d}"},
    {"type": "ap_payment", "prefix": "APP", "current": 0, "format": "{prefix}-{YYYYMMDD}-{seq:04d}"},
    {"type": "cash_in", "prefix": "CI", "current": 0, "format": "{prefix}-{YYYYMMDD}-{seq:04d}"},
    {"type": "cash_out", "prefix": "CO", "current": 0, "format": "{prefix}-{YYYYMMDD}-{seq:04d}"},
    {"type": "item_code", "prefix": "ITM", "current": 0, "format": "{prefix}-{seq:06d}"},
]

DEFAULT_ROLES = [
    {
        "name": "Pemilik",
        "code": "owner",
        "level": 1,
        "description": "Pemilik bisnis dengan akses penuh ke semua fitur",
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
        "permissions": [
            "dashboard.view", "accounting.view", "accounting.create", "accounting.edit",
            "ar.view", "ar.create", "ar.payment", "ap.view", "ap.create", "ap.payment",
            "reports.view", "reports.finance"
        ]
    },
    {
        "name": "Gudang",
        "code": "warehouse",
        "level": 4,
        "description": "Staff gudang",
        "all_branches": False,
        "permissions": [
            "dashboard.view", "inventory.view", "inventory.create", "inventory.edit",
            "purchase.view", "purchase.receive", "stock_opname.view", "stock_opname.create",
            "stock_transfer.view", "stock_transfer.create"
        ]
    },
    {
        "name": "Kasir",
        "code": "cashier",
        "level": 5,
        "description": "Kasir toko",
        "all_branches": False,
        "permissions": [
            "dashboard.view", "pos.view", "pos.create", "pos.void",
            "sales.view", "sales.create", "inventory.view"
        ]
    }
]


def get_mongo_client():
    """Get MongoDB client"""
    return AsyncIOMotorClient(os.environ.get('MONGO_URL'))


async def initialize_tenant_database(db_name: str, company_name: str = ""):
    """
    Initialize a tenant database with full ERP blueprint.
    This ensures all tenants have the same structure.
    """
    client = get_mongo_client()
    db = client[db_name]
    now = datetime.now(timezone.utc).isoformat()
    
    init_log = {
        "database": db_name,
        "blueprint_version": CURRENT_BLUEPRINT_VERSION,
        "migration_version": CURRENT_MIGRATION_VERSION,
        "initialized_at": now,
        "changes": []
    }
    
    # 1. Create/Update tenant metadata
    metadata = await db["_tenant_metadata"].find_one({})
    if not metadata:
        await db["_tenant_metadata"].insert_one({
            "id": str(uuid.uuid4()),
            "database_key": db_name,
            "company_name": company_name or db_name.replace("_", " ").title(),
            "blueprint_version": CURRENT_BLUEPRINT_VERSION,
            "migration_version": CURRENT_MIGRATION_VERSION,
            "initialized_at": now,
            "last_migrated_at": now,
            "status": "active"
        })
        init_log["changes"].append("Created tenant metadata")
    else:
        await db["_tenant_metadata"].update_one({}, {"$set": {
            "blueprint_version": CURRENT_BLUEPRINT_VERSION,
            "migration_version": CURRENT_MIGRATION_VERSION,
            "last_migrated_at": now
        }})
        init_log["changes"].append("Updated tenant metadata version")
    
    # 2. Ensure all required collections exist
    existing_collections = await db.list_collection_names()
    for coll_name in REQUIRED_COLLECTIONS:
        if coll_name not in existing_collections:
            # Create collection with a placeholder document then remove it
            await db.create_collection(coll_name)
            init_log["changes"].append(f"Created collection: {coll_name}")
    
    # 3. Initialize Chart of Accounts
    accounts_count = await db["accounts"].count_documents({})
    if accounts_count == 0:
        for acc in DEFAULT_COA:
            acc_doc = {**acc, "id": str(uuid.uuid4()), "balance": 0, "created_at": now}
            await db["accounts"].insert_one(acc_doc)
        init_log["changes"].append(f"Created {len(DEFAULT_COA)} accounts")
    
    # 4. Initialize Account Settings
    settings_count = await db["account_settings"].count_documents({})
    if settings_count == 0:
        for s in DEFAULT_ACCOUNT_SETTINGS:
            s_doc = {**s, "id": str(uuid.uuid4()), "created_at": now}
            await db["account_settings"].insert_one(s_doc)
        init_log["changes"].append(f"Created {len(DEFAULT_ACCOUNT_SETTINGS)} account settings")
    
    # 5. Initialize Numbering Settings
    numbering_count = await db["numbering_settings"].count_documents({})
    if numbering_count == 0:
        for n in DEFAULT_NUMBERING:
            n_doc = {**n, "id": str(uuid.uuid4()), "created_at": now}
            await db["numbering_settings"].insert_one(n_doc)
        init_log["changes"].append(f"Created {len(DEFAULT_NUMBERING)} numbering settings")
    
    # 6. Initialize Default Branch
    branch_count = await db["branches"].count_documents({})
    if branch_count == 0:
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
        init_log["changes"].append("Created default branch (HQ)")
    
    # 7. Initialize Company Profile
    company = await db["company_profile"].find_one({})
    if not company:
        await db["company_profile"].insert_one({
            "id": str(uuid.uuid4()),
            "name": company_name or db_name.replace("_", " ").upper(),
            "legal_name": "",
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
        init_log["changes"].append("Created company profile")
    
    # 8. Initialize Roles
    for role_template in DEFAULT_ROLES:
        existing = await db["roles"].find_one({"code": role_template["code"]})
        if not existing:
            role_doc = {**role_template, "id": str(uuid.uuid4()), "created_at": now}
            await db["roles"].insert_one(role_doc)
            init_log["changes"].append(f"Created role: {role_template['code']}")
        else:
            # Update permissions if needed
            await db["roles"].update_one(
                {"code": role_template["code"]},
                {"$set": {
                    "permissions": role_template["permissions"],
                    "level": role_template["level"],
                    "all_branches": role_template.get("all_branches", False),
                    "inherit_all": role_template.get("inherit_all", False),
                    "updated_at": now
                }}
            )
    
    # 9. Fix user role_ids
    users = await db["users"].find({}).to_list(100)
    for user in users:
        if not user.get("role_id"):
            role_code = user.get("role_code") or user.get("role", "cashier")
            role = await db["roles"].find_one({"code": role_code})
            if role:
                await db["users"].update_one(
                    {"id": user["id"]},
                    {"$set": {"role_id": role["id"], "role_code": role_code}}
                )
                init_log["changes"].append(f"Fixed role_id for user: {user.get('email')}")
    
    # 10. Initialize default units
    units_count = await db["units"].count_documents({})
    if units_count == 0:
        default_units = [
            {"id": str(uuid.uuid4()), "code": "PCS", "name": "Pieces", "created_at": now},
            {"id": str(uuid.uuid4()), "code": "BOX", "name": "Box", "created_at": now},
            {"id": str(uuid.uuid4()), "code": "KG", "name": "Kilogram", "created_at": now},
            {"id": str(uuid.uuid4()), "code": "LTR", "name": "Liter", "created_at": now},
        ]
        await db["units"].insert_many(default_units)
        init_log["changes"].append(f"Created {len(default_units)} default units")
    
    # 11. Create required indexes (ignore if already exist)
    try:
        await db["products"].create_index("code", unique=True, sparse=True)
    except Exception:
        pass  # Index already exists
    try:
        await db["accounts"].create_index("code", unique=True)
    except Exception:
        pass
    try:
        await db["stock_movements"].create_index([("product_id", 1), ("branch_id", 1)])
    except Exception:
        pass
    try:
        await db["journal_entries"].create_index("journal_number")
    except Exception:
        pass
    try:
        await db["customers"].create_index("code", unique=True, sparse=True)
    except Exception:
        pass
    try:
        await db["suppliers"].create_index("code", unique=True, sparse=True)
    except Exception:
        pass
    
    # 12. Log migration
    await db["_migration_log"].insert_one(init_log)
    
    return init_log


async def get_all_tenant_status():
    """Get status of all business databases"""
    client = get_mongo_client()
    all_dbs = await client.list_database_names()
    
    # Filter business databases (exclude system dbs)
    excluded = ['admin', 'local', 'config', 'test_database']
    business_dbs = [db for db in all_dbs if db not in excluded and not db.startswith('test')]
    
    results = []
    for db_name in business_dbs:
        db = client[db_name]
        
        # Get tenant metadata
        metadata = await db["_tenant_metadata"].find_one({})
        
        # Count key collections
        stats = {
            "database": db_name,
            "accounts": await db["accounts"].count_documents({}),
            "roles": await db["roles"].count_documents({}),
            "users": await db["users"].count_documents({}),
            "branches": await db["branches"].count_documents({}),
            "products": await db["products"].count_documents({}),
            "account_settings": await db["account_settings"].count_documents({}),
            "numbering_settings": await db["numbering_settings"].count_documents({}),
            "company_profile": await db["company_profile"].count_documents({}),
            "blueprint_version": metadata.get("blueprint_version") if metadata else None,
            "migration_version": metadata.get("migration_version") if metadata else None,
            "status": metadata.get("status") if metadata else "unknown",
            "needs_migration": (metadata.get("blueprint_version") != CURRENT_BLUEPRINT_VERSION) if metadata else True
        }
        
        # Determine health
        if stats["accounts"] == 0 or stats["roles"] == 0 or stats["account_settings"] == 0:
            stats["health"] = "incomplete"
        elif stats["needs_migration"]:
            stats["health"] = "needs_update"
        else:
            stats["health"] = "healthy"
        
        results.append(stats)
    
    return results


async def sync_all_tenants():
    """Synchronize all tenant databases to current blueprint"""
    client = get_mongo_client()
    all_dbs = await client.list_database_names()
    
    # Target ALL business databases (ocb_*)
    # Exclude system databases and erp_db (metadata only)
    excluded = ['admin', 'local', 'config', 'test_database', 'erp_db']
    target_dbs = [db for db in all_dbs if db.startswith('ocb_') and db not in excluded]
    
    results = []
    for db_name in target_dbs:
        result = await initialize_tenant_database(db_name)
        # Sanitize result for JSON serialization
        sanitized = {
            "database": result.get("database"),
            "blueprint_version": result.get("blueprint_version"),
            "migration_version": result.get("migration_version"),
            "initialized_at": result.get("initialized_at"),
            "changes": result.get("changes", [])
        }
        results.append(sanitized)
    
    return results


async def cleanup_tenant_collections(db_name: str):
    """Remove unnecessary/test collections from a tenant database"""
    client = get_mongo_client()
    db = client[db_name]
    
    # Collections to delete if found
    garbage_collections = [
        "test", "test_users", "dummy", "backup_old", "sample_data",
        "temp", "dev_logs", "debug", "test_data", "old_", "backup_"
    ]
    
    existing = await db.list_collection_names()
    deleted = []
    
    for coll in existing:
        # Check if collection name matches garbage patterns
        for garbage in garbage_collections:
            if coll.startswith(garbage) or coll == garbage:
                await db.drop_collection(coll)
                deleted.append(coll)
                break
    
    return deleted


async def get_tenant_blueprint_status():
    """Get detailed blueprint status for all tenants"""
    client = get_mongo_client()
    all_dbs = await client.list_database_names()
    
    excluded = ['admin', 'local', 'config', 'test_database', 'erp_db']
    target_dbs = [db for db in all_dbs if db.startswith('ocb_') and db not in excluded]
    
    results = []
    for db_name in target_dbs:
        db = client[db_name]
        existing_collections = set(await db.list_collection_names())
        required_set = set(REQUIRED_COLLECTIONS)
        
        missing = required_set - existing_collections
        metadata = await db["_tenant_metadata"].find_one({})
        
        results.append({
            "database": db_name,
            "blueprint_version": metadata.get("blueprint_version") if metadata else None,
            "total_collections": len(existing_collections),
            "missing_collections": list(missing),
            "has_all_required": len(missing) == 0,
            "needs_sync": metadata.get("blueprint_version") != CURRENT_BLUEPRINT_VERSION if metadata else True
        })
    
    return results


# ==================== API ENDPOINTS ====================

@router.get("/list")
async def list_tenants(user: dict = Depends(get_current_user)):
    """List all tenant databases with their status"""
    tenants = await get_all_tenant_status()
    return {
        "current_blueprint_version": CURRENT_BLUEPRINT_VERSION,
        "current_migration_version": CURRENT_MIGRATION_VERSION,
        "tenants": tenants
    }


@router.post("/sync-all")
async def sync_all_databases(user: dict = Depends(get_current_user)):
    """Synchronize all tenant databases to current blueprint"""
    results = await sync_all_tenants()
    return {
        "status": "completed",
        "blueprint_version": CURRENT_BLUEPRINT_VERSION,
        "total_synced": len(results),
        "results": results
    }


@router.get("/blueprint-status")
async def get_blueprint_status(user: dict = Depends(get_current_user)):
    """Get blueprint status for all tenants"""
    status = await get_tenant_blueprint_status()
    return {
        "current_blueprint_version": CURRENT_BLUEPRINT_VERSION,
        "required_collections": REQUIRED_COLLECTIONS,
        "tenants": status
    }


@router.post("/cleanup/{db_name}")
async def cleanup_database(db_name: str, user: dict = Depends(get_current_user)):
    """Remove garbage/test collections from a tenant database"""
    deleted = await cleanup_tenant_collections(db_name)
    return {
        "database": db_name,
        "deleted_collections": deleted,
        "count": len(deleted)
    }


@router.post("/initialize/{db_name}")
async def initialize_database(db_name: str, company_name: str = "", user: dict = Depends(get_current_user)):
    """Initialize a specific tenant database"""
    result = await initialize_tenant_database(db_name, company_name)
    return {
        "status": "initialized",
        "database": db_name,
        "changes": result["changes"]
    }


@router.post("/create")
async def create_new_tenant(
    database_key: str,
    company_name: str,
    owner_email: str,
    owner_password: str,
    user: dict = Depends(get_current_user)
):
    """Create a new tenant database with full ERP blueprint"""
    from utils.auth import hash_password
    
    client = get_mongo_client()
    
    # Check if database already exists
    existing = await client.list_database_names()
    if database_key in existing:
        raise HTTPException(status_code=400, detail=f"Database {database_key} already exists")
    
    # Initialize the new database
    result = await initialize_tenant_database(database_key, company_name)
    
    # Create owner user
    db = client[database_key]
    owner_role = await db["roles"].find_one({"code": "owner"})
    branch = await db["branches"].find_one({"code": "HQ"})
    
    now = datetime.now(timezone.utc).isoformat()
    owner_user = {
        "id": str(uuid.uuid4()),
        "email": owner_email,
        "password_hash": hash_password(owner_password),
        "name": "Owner",
        "phone": "",
        "role": "owner",
        "role_code": "owner",
        "role_id": owner_role["id"] if owner_role else None,
        "branch_id": branch["id"] if branch else None,
        "branch_ids": [branch["id"]] if branch else [],
        "is_active": True,
        "permissions": ["*"],
        "created_at": now
    }
    await db["users"].insert_one(owner_user)
    
    return {
        "status": "created",
        "database": database_key,
        "company_name": company_name,
        "owner_email": owner_email,
        "blueprint_version": CURRENT_BLUEPRINT_VERSION,
        "changes": result["changes"] + [f"Created owner user: {owner_email}"]
    }


@router.get("/health/{db_name}")
async def check_tenant_health(db_name: str, user: dict = Depends(get_current_user)):
    """Check health of a specific tenant database"""
    client = get_mongo_client()
    db = client[db_name]
    
    checks = {
        "accounts": await db["accounts"].count_documents({}),
        "account_settings": await db["account_settings"].count_documents({}),
        "numbering_settings": await db["numbering_settings"].count_documents({}),
        "roles": await db["roles"].count_documents({}),
        "branches": await db["branches"].count_documents({}),
        "company_profile": await db["company_profile"].count_documents({})
    }
    
    metadata = await db["_tenant_metadata"].find_one({})
    
    issues = []
    if checks["accounts"] == 0:
        issues.append("Missing Chart of Accounts")
    if checks["account_settings"] == 0:
        issues.append("Missing Account Settings")
    if checks["numbering_settings"] == 0:
        issues.append("Missing Numbering Settings")
    if checks["roles"] == 0:
        issues.append("Missing Roles")
    if checks["branches"] == 0:
        issues.append("Missing Branches")
    if checks["company_profile"] == 0:
        issues.append("Missing Company Profile")
    
    needs_migration = not metadata or metadata.get("blueprint_version") != CURRENT_BLUEPRINT_VERSION
    if needs_migration:
        issues.append(f"Blueprint version mismatch (current: {CURRENT_BLUEPRINT_VERSION})")
    
    return {
        "database": db_name,
        "health": "healthy" if not issues else "needs_attention",
        "checks": checks,
        "blueprint_version": metadata.get("blueprint_version") if metadata else None,
        "current_blueprint_version": CURRENT_BLUEPRINT_VERSION,
        "needs_migration": needs_migration,
        "issues": issues
    }
