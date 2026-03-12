"""
Number Settings API - Pengaturan Nomor Transaksi & Master
=========================================================
Engine terpusat untuk generate nomor otomatis untuk:
- Transaksi: PO, RCV, INV, PAY, SO, JV, dll
- Master: Supplier, Pelanggan, Sales, Item

SINGLE SOURCE OF TRUTH untuk semua nomor di sistem ERP
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone
from bson import ObjectId
from database import get_db as get_database

router = APIRouter(prefix="/api/number-settings", tags=["Number Settings"])

# ==================== MODELS ====================

class TransactionNumberSetting(BaseModel):
    """Setting nomor untuk transaksi"""
    module_code: str  # PO, RCV, INV, PAY, SO, JV, AR, AP, etc
    module_name: str  # Nama lengkap modul
    branch_id: Optional[str] = None  # Opsional: per cabang
    warehouse_id: Optional[str] = None  # Opsional: per gudang
    prefix_1: str = ""  # Prefix utama, e.g., "INV"
    prefix_2: str = ""  # Prefix tambahan, e.g., branch code
    prefix_3: str = ""  # Prefix tambahan lain
    separator: str = "-"  # Pemisah antar bagian
    include_date: bool = True  # Apakah include tanggal YYYYMMDD
    date_format: str = "YYYYMMDD"  # Format tanggal
    digit_count: int = 4  # Jumlah digit angka
    last_number: int = 0  # Nomor terakhir
    reset_type: str = "monthly"  # none, monthly, yearly
    is_active: bool = True

class MasterNumberSetting(BaseModel):
    """Setting nomor untuk master data"""
    entity_type: str  # supplier, customer, salesperson, item
    entity_name: str  # Nama lengkap entity
    prefix: str  # Prefix, e.g., "SP", "PL", "SL", "ITM"
    separator: str = "-"  # Pemisah
    digit_count: int = 4  # Jumlah digit
    last_number: int = 0  # Nomor terakhir
    is_active: bool = True

class GenerateNumberRequest(BaseModel):
    """Request untuk generate nomor"""
    module_code: str  # Kode modul
    branch_id: Optional[str] = None
    warehouse_id: Optional[str] = None

# ==================== DEFAULT SETTINGS ====================

DEFAULT_TRANSACTION_SETTINGS = [
    {"module_code": "PO", "module_name": "Purchase Order", "prefix_1": "PO", "digit_count": 4, "reset_type": "monthly"},
    {"module_code": "RCV", "module_name": "Receiving / Penerimaan Barang", "prefix_1": "RCV", "digit_count": 4, "reset_type": "monthly"},
    {"module_code": "PR", "module_name": "Purchase Return", "prefix_1": "PR", "digit_count": 4, "reset_type": "monthly"},
    {"module_code": "INV", "module_name": "Sales Invoice / Penjualan", "prefix_1": "INV", "digit_count": 4, "reset_type": "monthly"},
    {"module_code": "SO", "module_name": "Sales Order / Pesanan Penjualan", "prefix_1": "SO", "digit_count": 4, "reset_type": "monthly"},
    {"module_code": "SRT", "module_name": "Sales Return / Retur Penjualan", "prefix_1": "SRT", "digit_count": 4, "reset_type": "monthly"},
    {"module_code": "DO", "module_name": "Delivery Order / Surat Jalan", "prefix_1": "DO", "digit_count": 4, "reset_type": "monthly"},
    {"module_code": "PAY", "module_name": "Payment Out / Pembayaran Hutang", "prefix_1": "PAY", "digit_count": 4, "reset_type": "monthly"},
    {"module_code": "RECV", "module_name": "Payment In / Penerimaan Piutang", "prefix_1": "RECV", "digit_count": 4, "reset_type": "monthly"},
    {"module_code": "JV", "module_name": "Journal Voucher", "prefix_1": "JV", "digit_count": 4, "reset_type": "monthly"},
    {"module_code": "AP", "module_name": "Accounts Payable", "prefix_1": "AP", "digit_count": 4, "reset_type": "monthly"},
    {"module_code": "AR", "module_name": "Accounts Receivable", "prefix_1": "AR", "digit_count": 4, "reset_type": "monthly"},
    {"module_code": "STK", "module_name": "Stock Opname", "prefix_1": "STK", "digit_count": 4, "reset_type": "monthly"},
    {"module_code": "TRF", "module_name": "Stock Transfer", "prefix_1": "TRF", "digit_count": 4, "reset_type": "monthly"},
    {"module_code": "ASM", "module_name": "Assembly / Produksi", "prefix_1": "ASM", "digit_count": 4, "reset_type": "monthly"},
    {"module_code": "EXP", "module_name": "Expense / Pengeluaran", "prefix_1": "EXP", "digit_count": 4, "reset_type": "monthly"},
    {"module_code": "DEP", "module_name": "Cash Deposit / Setoran", "prefix_1": "DEP", "digit_count": 4, "reset_type": "monthly"},
    {"module_code": "COM", "module_name": "Commission / Komisi", "prefix_1": "COM", "digit_count": 4, "reset_type": "monthly"},
    {"module_code": "TI", "module_name": "Trade In / Tukar Tambah", "prefix_1": "TI", "digit_count": 4, "reset_type": "monthly"},
]

DEFAULT_MASTER_SETTINGS = [
    {"entity_type": "supplier", "entity_name": "Supplier", "prefix": "SP", "digit_count": 4},
    {"entity_type": "customer", "entity_name": "Pelanggan", "prefix": "PL", "digit_count": 4},
    {"entity_type": "salesperson", "entity_name": "Sales / Salesman", "prefix": "SL", "digit_count": 4},
    {"entity_type": "item", "entity_name": "Item / Barang", "prefix": "ITM", "digit_count": 4},
    {"entity_type": "category", "entity_name": "Kategori", "prefix": "CAT", "digit_count": 4},
    {"entity_type": "brand", "entity_name": "Merk / Brand", "prefix": "BRD", "digit_count": 4},
    {"entity_type": "warehouse", "entity_name": "Gudang", "prefix": "WH", "digit_count": 4},
    {"entity_type": "branch", "entity_name": "Cabang", "prefix": "BR", "digit_count": 4},
]

# ==================== HELPER FUNCTIONS ====================

def get_date_string(date_format: str) -> str:
    """Generate date string based on format"""
    now = datetime.now(timezone.utc)
    if date_format == "YYYYMMDD":
        return now.strftime("%Y%m%d")
    elif date_format == "YYYYMM":
        return now.strftime("%Y%m")
    elif date_format == "YYYY":
        return now.strftime("%Y")
    elif date_format == "MMDD":
        return now.strftime("%m%d")
    elif date_format == "DDMMYYYY":
        return now.strftime("%d%m%Y")
    else:
        return now.strftime("%Y%m%d")

def get_reset_key(reset_type: str) -> str:
    """Get reset key based on reset type"""
    now = datetime.now(timezone.utc)
    if reset_type == "monthly":
        return now.strftime("%Y%m")
    elif reset_type == "yearly":
        return now.strftime("%Y")
    else:
        return "ALL"  # No reset

def preview_number(setting: dict, next_number: int = None) -> str:
    """Generate preview of number format"""
    parts = []
    
    # Add prefixes
    if setting.get("prefix_1"):
        parts.append(setting["prefix_1"])
    if setting.get("prefix_2"):
        parts.append(setting["prefix_2"])
    if setting.get("prefix_3"):
        parts.append(setting["prefix_3"])
    
    # Add date if enabled
    if setting.get("include_date", True):
        date_format = setting.get("date_format", "YYYYMMDD")
        parts.append(get_date_string(date_format))
    
    # Add number
    digit_count = setting.get("digit_count", 4)
    num = next_number if next_number is not None else (setting.get("last_number", 0) + 1)
    parts.append(str(num).zfill(digit_count))
    
    separator = setting.get("separator", "-")
    return separator.join(parts)

def preview_master_number(setting: dict, next_number: int = None) -> str:
    """Generate preview of master number format"""
    prefix = setting.get("prefix", "")
    separator = setting.get("separator", "-")
    digit_count = setting.get("digit_count", 4)
    num = next_number if next_number is not None else (setting.get("last_number", 0) + 1)
    
    return f"{prefix}{separator}{str(num).zfill(digit_count)}"

# ==================== TRANSACTION NUMBER ENDPOINTS ====================

@router.get("/transactions")
async def get_transaction_settings():
    """Get all transaction number settings"""
    db = get_database()
    settings = await db.transaction_number_settings.find({}, {"_id": 0}).to_list(100)
    
    # If empty, seed with defaults
    if not settings:
        for default in DEFAULT_TRANSACTION_SETTINGS:
            default["id"] = str(ObjectId())
            default["include_date"] = True
            default["date_format"] = "YYYYMMDD"
            default["separator"] = "-"
            default["prefix_2"] = ""
            default["prefix_3"] = ""
            default["last_number"] = 0
            default["is_active"] = True
            default["created_at"] = datetime.now(timezone.utc).isoformat()
            await db.transaction_number_settings.insert_one(default)
        settings = await db.transaction_number_settings.find({}, {"_id": 0}).to_list(100)
    
    # Add preview to each setting
    for setting in settings:
        setting["preview"] = preview_number(setting)
    
    return {"items": settings, "total": len(settings)}

@router.get("/transactions/{module_code}")
async def get_transaction_setting(module_code: str):
    """Get specific transaction number setting"""
    db = get_database()
    setting = await db.transaction_number_settings.find_one(
        {"module_code": module_code.upper()}, {"_id": 0}
    )
    if not setting:
        raise HTTPException(status_code=404, detail=f"Setting untuk {module_code} tidak ditemukan")
    
    setting["preview"] = preview_number(setting)
    return setting

@router.post("/transactions")
async def create_transaction_setting(data: TransactionNumberSetting):
    """Create new transaction number setting"""
    db = get_database()
    
    # Check if exists
    existing = await db.transaction_number_settings.find_one({"module_code": data.module_code.upper()})
    if existing:
        raise HTTPException(status_code=400, detail=f"Setting untuk {data.module_code} sudah ada")
    
    setting = data.dict()
    setting["id"] = str(ObjectId())
    setting["module_code"] = data.module_code.upper()
    setting["created_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.transaction_number_settings.insert_one(setting)
    setting.pop("_id", None)
    setting["preview"] = preview_number(setting)
    
    return setting

@router.put("/transactions/{module_code}")
async def update_transaction_setting(module_code: str, data: dict):
    """Update transaction number setting"""
    db = get_database()
    
    # Only allow certain fields to be updated
    allowed_fields = [
        "module_name", "prefix_1", "prefix_2", "prefix_3", "separator",
        "include_date", "date_format", "digit_count", "reset_type", "is_active"
    ]
    
    update_data = {k: v for k, v in data.items() if k in allowed_fields}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.transaction_number_settings.update_one(
        {"module_code": module_code.upper()},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail=f"Setting untuk {module_code} tidak ditemukan")
    
    setting = await db.transaction_number_settings.find_one(
        {"module_code": module_code.upper()}, {"_id": 0}
    )
    setting["preview"] = preview_number(setting)
    
    return setting

@router.post("/transactions/{module_code}/reset")
async def reset_transaction_counter(module_code: str):
    """Reset counter untuk modul tertentu"""
    db = get_database()
    
    result = await db.transaction_number_settings.update_one(
        {"module_code": module_code.upper()},
        {"$set": {"last_number": 0, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail=f"Setting untuk {module_code} tidak ditemukan")
    
    # Also reset in counters collection
    reset_key = get_reset_key("monthly")  # Default to monthly
    await db.counters.delete_many({"prefix": module_code.upper()})
    
    return {"success": True, "message": f"Counter {module_code} telah direset"}

# ==================== MASTER NUMBER ENDPOINTS ====================

@router.get("/masters")
async def get_master_settings():
    """Get all master number settings"""
    db = get_database()
    settings = await db.master_number_settings.find({}, {"_id": 0}).to_list(100)
    
    # If empty, seed with defaults
    if not settings:
        for default in DEFAULT_MASTER_SETTINGS:
            default["id"] = str(ObjectId())
            default["separator"] = "-"
            default["last_number"] = 0
            default["is_active"] = True
            default["created_at"] = datetime.now(timezone.utc).isoformat()
            await db.master_number_settings.insert_one(default)
        settings = await db.master_number_settings.find({}, {"_id": 0}).to_list(100)
    
    # Add preview to each setting
    for setting in settings:
        setting["preview"] = preview_master_number(setting)
    
    return {"items": settings, "total": len(settings)}

@router.get("/masters/{entity_type}")
async def get_master_setting(entity_type: str):
    """Get specific master number setting"""
    db = get_database()
    setting = await db.master_number_settings.find_one(
        {"entity_type": entity_type.lower()}, {"_id": 0}
    )
    if not setting:
        raise HTTPException(status_code=404, detail=f"Setting untuk {entity_type} tidak ditemukan")
    
    setting["preview"] = preview_master_number(setting)
    return setting

@router.put("/masters/{entity_type}")
async def update_master_setting(entity_type: str, data: dict):
    """Update master number setting"""
    db = get_database()
    
    # Only allow certain fields to be updated
    allowed_fields = ["entity_name", "prefix", "separator", "digit_count", "is_active"]
    
    update_data = {k: v for k, v in data.items() if k in allowed_fields}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.master_number_settings.update_one(
        {"entity_type": entity_type.lower()},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail=f"Setting untuk {entity_type} tidak ditemukan")
    
    setting = await db.master_number_settings.find_one(
        {"entity_type": entity_type.lower()}, {"_id": 0}
    )
    setting["preview"] = preview_master_number(setting)
    
    return setting

# ==================== NUMBER GENERATOR ENGINE ====================

@router.post("/generate/transaction")
async def generate_transaction_number(request: GenerateNumberRequest):
    """
    CENTRAL ENGINE: Generate nomor transaksi
    Semua modul WAJIB menggunakan endpoint ini untuk generate nomor
    """
    db = get_database()
    
    # Get setting
    setting = await db.transaction_number_settings.find_one(
        {"module_code": request.module_code.upper()}, {"_id": 0}
    )
    
    if not setting:
        # Create default if not exists
        setting = {
            "id": str(ObjectId()),
            "module_code": request.module_code.upper(),
            "module_name": request.module_code.upper(),
            "prefix_1": request.module_code.upper(),
            "prefix_2": "",
            "prefix_3": "",
            "separator": "-",
            "include_date": True,
            "date_format": "YYYYMMDD",
            "digit_count": 4,
            "last_number": 0,
            "reset_type": "monthly",
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.transaction_number_settings.insert_one(setting)
    
    # Get reset key
    reset_key = get_reset_key(setting.get("reset_type", "monthly"))
    
    # Get and increment counter
    counter_key = f"{request.module_code.upper()}_{reset_key}"
    if request.branch_id:
        counter_key += f"_{request.branch_id}"
    if request.warehouse_id:
        counter_key += f"_{request.warehouse_id}"
    
    counter = await db.number_counters.find_one_and_update(
        {"key": counter_key},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True
    )
    
    next_number = counter.get("seq", 1)
    
    # Build number
    parts = []
    
    if setting.get("prefix_1"):
        parts.append(setting["prefix_1"])
    if setting.get("prefix_2"):
        parts.append(setting["prefix_2"])
    if setting.get("prefix_3"):
        parts.append(setting["prefix_3"])
    
    if setting.get("include_date", True):
        date_format = setting.get("date_format", "YYYYMMDD")
        parts.append(get_date_string(date_format))
    
    digit_count = setting.get("digit_count", 4)
    parts.append(str(next_number).zfill(digit_count))
    
    separator = setting.get("separator", "-")
    generated_number = separator.join(parts)
    
    # Update last_number in setting
    await db.transaction_number_settings.update_one(
        {"module_code": request.module_code.upper()},
        {"$set": {"last_number": next_number}}
    )
    
    return {
        "number": generated_number,
        "module_code": request.module_code.upper(),
        "sequence": next_number,
        "reset_key": reset_key
    }

@router.post("/generate/master")
async def generate_master_number(entity_type: str):
    """
    CENTRAL ENGINE: Generate nomor master
    Semua master WAJIB menggunakan endpoint ini untuk generate kode otomatis
    """
    db = get_database()
    
    # Get setting
    setting = await db.master_number_settings.find_one(
        {"entity_type": entity_type.lower()}, {"_id": 0}
    )
    
    if not setting:
        # Create default if not exists
        prefix_map = {
            "supplier": "SP",
            "customer": "PL",
            "salesperson": "SL",
            "item": "ITM",
            "category": "CAT",
            "brand": "BRD",
            "warehouse": "WH",
            "branch": "BR"
        }
        setting = {
            "id": str(ObjectId()),
            "entity_type": entity_type.lower(),
            "entity_name": entity_type.title(),
            "prefix": prefix_map.get(entity_type.lower(), entity_type.upper()[:3]),
            "separator": "-",
            "digit_count": 4,
            "last_number": 0,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.master_number_settings.insert_one(setting)
    
    # Get and increment counter
    counter_key = f"MASTER_{entity_type.upper()}"
    
    counter = await db.number_counters.find_one_and_update(
        {"key": counter_key},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True
    )
    
    next_number = counter.get("seq", 1)
    
    # Build number
    prefix = setting.get("prefix", entity_type.upper()[:3])
    separator = setting.get("separator", "-")
    digit_count = setting.get("digit_count", 4)
    
    generated_code = f"{prefix}{separator}{str(next_number).zfill(digit_count)}"
    
    # Update last_number in setting
    await db.master_number_settings.update_one(
        {"entity_type": entity_type.lower()},
        {"$set": {"last_number": next_number}}
    )
    
    return {
        "code": generated_code,
        "entity_type": entity_type.lower(),
        "sequence": next_number
    }

@router.get("/preview/transaction/{module_code}")
async def preview_transaction_number(module_code: str):
    """Preview nomor transaksi berikutnya"""
    db = get_database()
    
    setting = await db.transaction_number_settings.find_one(
        {"module_code": module_code.upper()}, {"_id": 0}
    )
    
    if not setting:
        raise HTTPException(status_code=404, detail=f"Setting untuk {module_code} tidak ditemukan")
    
    # Get current counter
    reset_key = get_reset_key(setting.get("reset_type", "monthly"))
    counter_key = f"{module_code.upper()}_{reset_key}"
    
    counter = await db.number_counters.find_one({"key": counter_key})
    next_number = (counter.get("seq", 0) if counter else 0) + 1
    
    return {
        "preview": preview_number(setting, next_number),
        "next_sequence": next_number,
        "setting": setting
    }

@router.get("/preview/master/{entity_type}")
async def preview_master_number_endpoint(entity_type: str):
    """Preview kode master berikutnya"""
    db = get_database()
    
    setting = await db.master_number_settings.find_one(
        {"entity_type": entity_type.lower()}, {"_id": 0}
    )
    
    if not setting:
        raise HTTPException(status_code=404, detail=f"Setting untuk {entity_type} tidak ditemukan")
    
    # Get current counter
    counter_key = f"MASTER_{entity_type.upper()}"
    counter = await db.number_counters.find_one({"key": counter_key})
    next_number = (counter.get("seq", 0) if counter else 0) + 1
    
    return {
        "preview": preview_master_number(setting, next_number),
        "next_sequence": next_number,
        "setting": setting
    }
