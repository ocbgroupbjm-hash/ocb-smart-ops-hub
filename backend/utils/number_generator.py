"""
Central Number Generator - SINGLE SOURCE OF TRUTH
==================================================
Semua modul WAJIB menggunakan fungsi ini untuk generate nomor.
DILARANG membuat format nomor hardcode di modul lain.
"""

from datetime import datetime, timezone
from bson import ObjectId

# Default settings for each module
DEFAULT_TRANSACTION_SETTINGS = {
    "PO": {"prefix": "PO", "digit_count": 4, "reset_type": "monthly"},
    "RCV": {"prefix": "RCV", "digit_count": 4, "reset_type": "monthly"},
    "PR": {"prefix": "PR", "digit_count": 4, "reset_type": "monthly"},
    "INV": {"prefix": "INV", "digit_count": 4, "reset_type": "monthly"},
    "SO": {"prefix": "SO", "digit_count": 4, "reset_type": "monthly"},
    "SRT": {"prefix": "SRT", "digit_count": 4, "reset_type": "monthly"},
    "DO": {"prefix": "DO", "digit_count": 4, "reset_type": "monthly"},
    "PAY": {"prefix": "PAY", "digit_count": 4, "reset_type": "monthly"},
    "RECV": {"prefix": "RECV", "digit_count": 4, "reset_type": "monthly"},
    "JV": {"prefix": "JV", "digit_count": 4, "reset_type": "monthly"},
    "AP": {"prefix": "AP", "digit_count": 4, "reset_type": "monthly"},
    "AR": {"prefix": "AR", "digit_count": 4, "reset_type": "monthly"},
    "STK": {"prefix": "STK", "digit_count": 4, "reset_type": "monthly"},
    "TRF": {"prefix": "TRF", "digit_count": 4, "reset_type": "monthly"},
    "ASM": {"prefix": "ASM", "digit_count": 4, "reset_type": "monthly"},
    "EXP": {"prefix": "EXP", "digit_count": 4, "reset_type": "monthly"},
    "DEP": {"prefix": "DEP", "digit_count": 4, "reset_type": "monthly"},
    "COM": {"prefix": "COM", "digit_count": 4, "reset_type": "monthly"},
    "TI": {"prefix": "TI", "digit_count": 4, "reset_type": "monthly"},
}

DEFAULT_MASTER_SETTINGS = {
    "supplier": {"prefix": "SP", "digit_count": 4},
    "customer": {"prefix": "PL", "digit_count": 4},
    "salesperson": {"prefix": "SL", "digit_count": 4},
    "item": {"prefix": "ITM", "digit_count": 4},
    "category": {"prefix": "CAT", "digit_count": 4},
    "brand": {"prefix": "BRD", "digit_count": 4},
    "warehouse": {"prefix": "WH", "digit_count": 4},
    "branch": {"prefix": "BR", "digit_count": 4},
}


def get_reset_key(reset_type: str) -> str:
    """Get reset key based on reset type"""
    now = datetime.now(timezone.utc)
    if reset_type == "monthly":
        return now.strftime("%Y%m")
    elif reset_type == "yearly":
        return now.strftime("%Y")
    else:
        return "ALL"


async def generate_transaction_number(db, module_code: str, branch_id: str = None) -> str:
    """
    CENTRAL ENGINE: Generate nomor transaksi
    Semua modul WAJIB menggunakan fungsi ini.
    
    Args:
        db: Database connection
        module_code: Kode modul (PO, INV, JV, AR, AP, etc)
        branch_id: Optional branch ID for multi-branch numbering
    
    Returns:
        Generated number string (e.g., "INV-20260312-0001")
    """
    module_code = module_code.upper()
    
    # Get setting from database or use default
    setting = await db.transaction_number_settings.find_one(
        {"module_code": module_code}, {"_id": 0}
    )
    
    if not setting:
        # Use default and create setting
        default = DEFAULT_TRANSACTION_SETTINGS.get(module_code, {
            "prefix": module_code,
            "digit_count": 4,
            "reset_type": "monthly"
        })
        setting = {
            "id": str(ObjectId()),
            "module_code": module_code,
            "module_name": module_code,
            "prefix_1": default["prefix"],
            "prefix_2": "",
            "prefix_3": "",
            "separator": "-",
            "include_date": True,
            "date_format": "YYYYMMDD",
            "digit_count": default["digit_count"],
            "last_number": 0,
            "reset_type": default["reset_type"],
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.transaction_number_settings.insert_one(setting)
    
    # Get reset key
    reset_type = setting.get("reset_type", "monthly")
    reset_key = get_reset_key(reset_type)
    
    # Build counter key
    counter_key = f"{module_code}_{reset_key}"
    if branch_id:
        counter_key += f"_{branch_id}"
    
    # Atomic increment counter
    counter = await db.number_counters.find_one_and_update(
        {"key": counter_key},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True
    )
    
    next_number = counter.get("seq", 1)
    
    # Build number string
    parts = []
    
    # Add prefix(es)
    if setting.get("prefix_1"):
        parts.append(setting["prefix_1"])
    if setting.get("prefix_2"):
        parts.append(setting["prefix_2"])
    if setting.get("prefix_3"):
        parts.append(setting["prefix_3"])
    
    # Add date if enabled
    if setting.get("include_date", True):
        date_format = setting.get("date_format", "YYYYMMDD")
        if date_format == "YYYYMMDD":
            parts.append(datetime.now(timezone.utc).strftime("%Y%m%d"))
        elif date_format == "YYYYMM":
            parts.append(datetime.now(timezone.utc).strftime("%Y%m"))
        elif date_format == "YYYY":
            parts.append(datetime.now(timezone.utc).strftime("%Y"))
        else:
            parts.append(datetime.now(timezone.utc).strftime("%Y%m%d"))
    
    # Add sequence number
    digit_count = setting.get("digit_count", 4)
    parts.append(str(next_number).zfill(digit_count))
    
    # Join with separator
    separator = setting.get("separator", "-")
    generated_number = separator.join(parts)
    
    # Update last_number in setting
    await db.transaction_number_settings.update_one(
        {"module_code": module_code},
        {"$set": {"last_number": next_number}}
    )
    
    return generated_number


async def generate_master_code(db, entity_type: str) -> str:
    """
    CENTRAL ENGINE: Generate kode master
    Semua master creation WAJIB menggunakan fungsi ini.
    
    Args:
        db: Database connection
        entity_type: Tipe entity (supplier, customer, salesperson, item, etc)
    
    Returns:
        Generated code string (e.g., "SP-0001")
    """
    entity_type = entity_type.lower()
    
    # Get setting from database or use default
    setting = await db.master_number_settings.find_one(
        {"entity_type": entity_type}, {"_id": 0}
    )
    
    if not setting:
        # Use default and create setting
        default = DEFAULT_MASTER_SETTINGS.get(entity_type, {
            "prefix": entity_type.upper()[:3],
            "digit_count": 4
        })
        setting = {
            "id": str(ObjectId()),
            "entity_type": entity_type,
            "entity_name": entity_type.title(),
            "prefix": default["prefix"],
            "separator": "-",
            "digit_count": default["digit_count"],
            "last_number": 0,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.master_number_settings.insert_one(setting)
    
    # Build counter key
    counter_key = f"MASTER_{entity_type.upper()}"
    
    # Atomic increment counter
    counter = await db.number_counters.find_one_and_update(
        {"key": counter_key},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True
    )
    
    next_number = counter.get("seq", 1)
    
    # Build code string
    prefix = setting.get("prefix", entity_type.upper()[:3])
    separator = setting.get("separator", "-")
    digit_count = setting.get("digit_count", 4)
    
    generated_code = f"{prefix}{separator}{str(next_number).zfill(digit_count)}"
    
    # Update last_number in setting
    await db.master_number_settings.update_one(
        {"entity_type": entity_type},
        {"$set": {"last_number": next_number}}
    )
    
    return generated_code


async def check_duplicate_code(db, collection: str, code_field: str, code_value: str, exclude_id: str = None) -> bool:
    """
    Check if code already exists in collection
    
    Returns:
        True if duplicate exists, False if unique
    """
    query = {code_field: code_value}
    if exclude_id:
        query["id"] = {"$ne": exclude_id}
    
    existing = await db[collection].find_one(query)
    return existing is not None
