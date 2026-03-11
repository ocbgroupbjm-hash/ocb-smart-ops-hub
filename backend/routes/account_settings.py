"""
OCB TITAN - ERP Account Settings Module
Enterprise Account Mapping System like iPOS Ultimate
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from bson import ObjectId
import uuid
from database import get_db as get_database
from routes.auth import get_current_user

router = APIRouter(prefix="/api/account-settings", tags=["Account Settings"])

# ==================== MODELS ====================

class AccountSettingCreate(BaseModel):
    module: str
    account_key: str
    account_code: str
    account_name: str
    tab_group: str = "global"
    description: str = ""

class AccountMappingCreate(BaseModel):
    mapping_type: str  # branch, warehouse, category, payment_method, tax
    reference_id: str  # ID of branch/warehouse/category/etc
    reference_name: str = ""
    account_key: str
    account_code: str
    account_name: str

class FiscalPeriodCreate(BaseModel):
    period_name: str
    start_date: str
    end_date: str
    status: str = "open"

# ==================== DEFAULT ACCOUNT SETTINGS ====================

DEFAULT_ACCOUNT_SETTINGS = {
    "data_item": [
        {"account_key": "hpp", "account_code": "5-1000", "account_name": "Harga Pokok Penjualan", "description": "Akun HPP untuk item baru"},
        {"account_key": "pendapatan_jual", "account_code": "4-1000", "account_name": "Pendapatan Penjualan", "description": "Akun pendapatan penjualan"},
        {"account_key": "pendapatan_jasa", "account_code": "4-1100", "account_name": "Pendapatan Jasa", "description": "Akun pendapatan jasa"},
        {"account_key": "biaya_non_inventory", "account_code": "5-2000", "account_name": "Biaya Non Inventory", "description": "Akun biaya non-inventory"},
        {"account_key": "persediaan_barang", "account_code": "1-1400", "account_name": "Persediaan Barang", "description": "Akun persediaan barang dagang"},
        {"account_key": "persediaan_dalam_proses", "account_code": "1-1410", "account_name": "Persediaan Dalam Proses", "description": "Akun WIP"},
        {"account_key": "biaya_tenaga_kerja", "account_code": "5-2100", "account_name": "Biaya Tenaga Kerja", "description": "Akun biaya TK langsung"},
        {"account_key": "biaya_overhead", "account_code": "5-2200", "account_name": "Biaya Overhead", "description": "Akun overhead pabrik"},
        {"account_key": "item_masuk", "account_code": "1-1400", "account_name": "Persediaan Barang", "description": "Akun item masuk"},
        {"account_key": "item_keluar", "account_code": "1-1400", "account_name": "Persediaan Barang", "description": "Akun item keluar"},
        {"account_key": "item_opname", "account_code": "5-9100", "account_name": "Selisih Persediaan", "description": "Akun selisih opname"},
        {"account_key": "saldo_awal_item", "account_code": "3-9000", "account_name": "Historical Balancing", "description": "Akun saldo awal persediaan"},
    ],
    "pembelian": [
        {"account_key": "potongan_pembelian", "account_code": "5-1100", "account_name": "Potongan Pembelian", "description": "Diskon dari supplier"},
        {"account_key": "ppn_masukan", "account_code": "1-1500", "account_name": "PPN Masukan", "description": "Pajak pembelian"},
        {"account_key": "biaya_lain_pembelian", "account_code": "5-1200", "account_name": "Biaya Lain Pembelian", "description": "Ongkir, handling"},
        {"account_key": "pembayaran_tunai_pembelian", "account_code": "1-1100", "account_name": "Kas", "description": "Kas untuk pembelian tunai"},
        {"account_key": "pembayaran_kredit_pembelian", "account_code": "2-1100", "account_name": "Hutang Dagang", "description": "Hutang pembelian kredit"},
        {"account_key": "uang_muka_po", "account_code": "1-1600", "account_name": "Uang Muka Pembelian", "description": "DP pembelian"},
        {"account_key": "deposit_supplier", "account_code": "2-1200", "account_name": "Deposit Supplier", "description": "Dana titipan ke supplier"},
        {"account_key": "retur_potongan_pembelian", "account_code": "5-1100", "account_name": "Potongan Pembelian", "description": "Diskon retur"},
        {"account_key": "retur_ppn_pembelian", "account_code": "1-1500", "account_name": "PPN Masukan", "description": "PPN retur"},
        {"account_key": "titip_uang_muka_po", "account_code": "2-1300", "account_name": "Titipan Uang Muka PO", "description": "Uang muka PO diterima"},
        {"account_key": "kas_uang_muka_po", "account_code": "1-1100", "account_name": "Kas", "description": "Kas uang muka PO"},
    ],
    "penjualan_1": [
        {"account_key": "potongan_penjualan", "account_code": "4-2000", "account_name": "Potongan Penjualan", "description": "Diskon ke customer"},
        {"account_key": "ppn_keluaran", "account_code": "2-1400", "account_name": "PPN Keluaran", "description": "Pajak penjualan"},
        {"account_key": "biaya_lain_penjualan", "account_code": "5-3000", "account_name": "Biaya Lain Penjualan", "description": "Biaya penjualan lainnya"},
        {"account_key": "pembayaran_tunai", "account_code": "1-1100", "account_name": "Kas", "description": "Kas penjualan tunai"},
        {"account_key": "pembayaran_debit", "account_code": "1-1200", "account_name": "Bank", "description": "Bank penjualan debit"},
        {"account_key": "pembayaran_kartu_kredit", "account_code": "1-1210", "account_name": "Piutang Kartu Kredit", "description": "Piutang CC"},
        {"account_key": "pembayaran_emoney", "account_code": "1-1220", "account_name": "Piutang E-Money", "description": "Piutang e-money"},
        {"account_key": "pembayaran_kredit", "account_code": "1-1300", "account_name": "Piutang Usaha", "description": "Piutang penjualan kredit"},
        {"account_key": "komisi_sales", "account_code": "5-4000", "account_name": "Beban Komisi Sales", "description": "Biaya komisi"},
        {"account_key": "hutang_ongkir", "account_code": "2-1500", "account_name": "Hutang Ongkir Titipan", "description": "Ongkir titipan"},
        {"account_key": "uang_muka_so", "account_code": "2-1600", "account_name": "Uang Muka Penjualan", "description": "DP penjualan"},
        {"account_key": "deposit_pelanggan", "account_code": "2-1700", "account_name": "Deposit Pelanggan", "description": "Deposit customer"},
        {"account_key": "hutang_komisi_sales", "account_code": "2-1800", "account_name": "Hutang Komisi Sales", "description": "Hutang komisi"},
        {"account_key": "pembulatan", "account_code": "4-9000", "account_name": "Pendapatan Pembulatan", "description": "Pembulatan"},
        {"account_key": "ppnbm", "account_code": "2-1410", "account_name": "PPnBM", "description": "PPnBM keluaran"},
        {"account_key": "pph23", "account_code": "1-1510", "account_name": "PPh 23 Dibayar Dimuka", "description": "PPh 23"},
        {"account_key": "titip_uang_muka_so", "account_code": "2-1600", "account_name": "Titipan Uang Muka SO", "description": "DP SO diterima"},
        {"account_key": "kas_uang_muka_so", "account_code": "1-1100", "account_name": "Kas", "description": "Kas DP SO"},
    ],
    "penjualan_2": [
        {"account_key": "retur_potongan_penjualan", "account_code": "4-2000", "account_name": "Potongan Penjualan", "description": "Diskon retur"},
        {"account_key": "retur_ppn_penjualan", "account_code": "2-1400", "account_name": "PPN Keluaran", "description": "PPN retur"},
        {"account_key": "retur_biaya_lain", "account_code": "5-3000", "account_name": "Biaya Lain Penjualan", "description": "Biaya retur"},
        {"account_key": "retur_pembayaran_tunai", "account_code": "1-1100", "account_name": "Kas", "description": "Kas retur tunai"},
        {"account_key": "retur_pembayaran_kredit", "account_code": "1-1300", "account_name": "Piutang Usaha", "description": "Piutang retur"},
        {"account_key": "retur_komisi_sales", "account_code": "5-4000", "account_name": "Beban Komisi Sales", "description": "Reverse komisi"},
        {"account_key": "retur_deposit_pelanggan", "account_code": "2-1700", "account_name": "Deposit Pelanggan", "description": "Deposit retur"},
        {"account_key": "retur_hutang_komisi", "account_code": "2-1800", "account_name": "Hutang Komisi Sales", "description": "Hutang komisi retur"},
        {"account_key": "retur_ppnbm", "account_code": "2-1410", "account_name": "PPnBM", "description": "PPnBM retur"},
        {"account_key": "donasi", "account_code": "5-5000", "account_name": "Beban Donasi", "description": "Akun donasi"},
    ],
    "konsinyasi": [
        {"account_key": "konsinyasi_masuk_pajak", "account_code": "1-1500", "account_name": "PPN Masukan", "description": "PPN konsinyasi masuk"},
        {"account_key": "hutang_konsinyasi", "account_code": "2-2000", "account_name": "Hutang Konsinyasi", "description": "Hutang barang konsinyasi"},
        {"account_key": "barang_konsinyasi_masuk", "account_code": "1-1420", "account_name": "Barang Konsinyasi Masuk", "description": "Persediaan konsinyasi"},
        {"account_key": "konsinyasi_keluar_pajak", "account_code": "2-1400", "account_name": "PPN Keluaran", "description": "PPN konsinyasi keluar"},
        {"account_key": "konsinyasi_keluar_biaya", "account_code": "5-3100", "account_name": "Biaya Konsinyasi", "description": "Biaya konsinyasi"},
        {"account_key": "piutang_konsinyasi", "account_code": "1-1310", "account_name": "Piutang Konsinyasi", "description": "Piutang konsinyasi"},
        {"account_key": "piutang_pajak_konsinyasi", "account_code": "1-1320", "account_name": "Piutang Pajak Konsinyasi", "description": "Piutang pajak"},
        {"account_key": "barang_konsinyasi_keluar", "account_code": "1-1430", "account_name": "Barang Konsinyasi Keluar", "description": "Konsinyasi keluar"},
    ],
    "hutang_piutang": [
        {"account_key": "potongan_hutang", "account_code": "4-3000", "account_name": "Potongan Hutang", "description": "Diskon pelunasan hutang"},
        {"account_key": "potongan_piutang", "account_code": "5-6000", "account_name": "Potongan Piutang", "description": "Diskon pelunasan piutang"},
        {"account_key": "laba_selisih_kurs", "account_code": "4-4000", "account_name": "Laba Selisih Kurs", "description": "Keuntungan kurs"},
        {"account_key": "rugi_selisih_kurs", "account_code": "5-7000", "account_name": "Rugi Selisih Kurs", "description": "Kerugian kurs"},
    ],
    "lain_lain": [
        {"account_key": "prive", "account_code": "3-2000", "account_name": "Prive", "description": "Pengambilan pemilik"},
        {"account_key": "laba_ditahan", "account_code": "3-3000", "account_name": "Laba Ditahan", "description": "Retained earnings"},
        {"account_key": "laba_tahun_berjalan", "account_code": "3-4000", "account_name": "Laba Tahun Berjalan", "description": "Current year profit"},
        {"account_key": "historical_balancing", "account_code": "3-9000", "account_name": "Historical Balancing", "description": "Saldo penyeimbang"},
        {"account_key": "biaya_lain_diambil_dari", "account_code": "5-9000", "account_name": "Biaya Lain-lain", "description": "Biaya umum"},
    ],
}

# ==================== GLOBAL ACCOUNT SETTINGS ENDPOINTS ====================

@router.get("/")
async def get_all_account_settings(user: dict = Depends(get_current_user)):
    """Get all account settings grouped by tab"""
    db = get_database()
    
    settings = await db.account_settings.find({}, {"_id": 0}).to_list(1000)
    
    # If no settings, return defaults
    if not settings:
        result = {}
        for tab, accounts in DEFAULT_ACCOUNT_SETTINGS.items():
            result[tab] = []
            for acc in accounts:
                result[tab].append({
                    "id": str(uuid.uuid4()),
                    "module": tab,
                    "tab_group": tab,
                    **acc
                })
        return {"settings": result, "is_default": True}
    
    # Group by tab
    result = {}
    for s in settings:
        tab = s.get("tab_group", "global")
        if tab not in result:
            result[tab] = []
        result[tab].append(s)
    
    return {"settings": result, "is_default": False}

@router.get("/by-tab/{tab}")
async def get_account_settings_by_tab(tab: str, user: dict = Depends(get_current_user)):
    """Get account settings for specific tab"""
    db = get_database()
    
    settings = await db.account_settings.find({"tab_group": tab}, {"_id": 0}).to_list(100)
    
    if not settings and tab in DEFAULT_ACCOUNT_SETTINGS:
        settings = []
        for acc in DEFAULT_ACCOUNT_SETTINGS[tab]:
            settings.append({
                "id": str(uuid.uuid4()),
                "module": tab,
                "tab_group": tab,
                **acc
            })
    
    return {"items": settings, "tab": tab}

@router.post("/")
async def create_account_setting(data: AccountSettingCreate, user: dict = Depends(get_current_user)):
    """Create new account setting"""
    db = get_database()
    
    setting = {
        "id": str(uuid.uuid4()),
        "module": data.module,
        "account_key": data.account_key,
        "account_code": data.account_code,
        "account_name": data.account_name,
        "tab_group": data.tab_group,
        "description": data.description,
        "updated_by": user.get("id"),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.account_settings.insert_one(setting)
    setting.pop("_id", None)
    return setting

@router.put("/{setting_id}")
async def update_account_setting(setting_id: str, data: AccountSettingCreate, user: dict = Depends(get_current_user)):
    """Update account setting"""
    db = get_database()
    
    result = await db.account_settings.update_one(
        {"id": setting_id},
        {"$set": {
            "account_code": data.account_code,
            "account_name": data.account_name,
            "description": data.description,
            "updated_by": user.get("id"),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Setting tidak ditemukan")
    
    return {"success": True}

@router.post("/initialize-defaults")
async def initialize_default_settings(user: dict = Depends(get_current_user)):
    """Initialize default account settings"""
    db = get_database()
    
    count = 0
    for tab, accounts in DEFAULT_ACCOUNT_SETTINGS.items():
        for acc in accounts:
            existing = await db.account_settings.find_one({
                "tab_group": tab,
                "account_key": acc["account_key"]
            })
            if not existing:
                setting = {
                    "id": str(uuid.uuid4()),
                    "module": tab,
                    "tab_group": tab,
                    **acc,
                    "updated_by": user.get("id"),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
                await db.account_settings.insert_one(setting)
                count += 1
    
    return {"success": True, "initialized": count}

# ==================== ACCOUNT MAPPING PER BRANCH ====================

@router.get("/branch-mapping")
async def get_branch_account_mapping(user: dict = Depends(get_current_user)):
    """Get account mappings per branch"""
    db = get_database()
    mappings = await db.account_mapping_branch.find({}, {"_id": 0}).to_list(500)
    return {"items": mappings}

@router.post("/branch-mapping")
async def create_branch_account_mapping(data: AccountMappingCreate, user: dict = Depends(get_current_user)):
    """Create account mapping for branch"""
    db = get_database()
    
    mapping = {
        "id": str(uuid.uuid4()),
        "mapping_type": "branch",
        "branch_id": data.reference_id,
        "branch_name": data.reference_name,
        "account_key": data.account_key,
        "account_code": data.account_code,
        "account_name": data.account_name,
        "updated_by": user.get("id"),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.account_mapping_branch.insert_one(mapping)
    mapping.pop("_id", None)
    return mapping

# ==================== ACCOUNT MAPPING PER WAREHOUSE ====================

@router.get("/warehouse-mapping")
async def get_warehouse_account_mapping(user: dict = Depends(get_current_user)):
    """Get account mappings per warehouse"""
    db = get_database()
    mappings = await db.account_mapping_warehouse.find({}, {"_id": 0}).to_list(500)
    return {"items": mappings}

@router.post("/warehouse-mapping")
async def create_warehouse_account_mapping(data: AccountMappingCreate, user: dict = Depends(get_current_user)):
    """Create account mapping for warehouse"""
    db = get_database()
    
    mapping = {
        "id": str(uuid.uuid4()),
        "mapping_type": "warehouse",
        "warehouse_id": data.reference_id,
        "warehouse_name": data.reference_name,
        "account_key": data.account_key,
        "account_code": data.account_code,
        "account_name": data.account_name,
        "updated_by": user.get("id"),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.account_mapping_warehouse.insert_one(mapping)
    mapping.pop("_id", None)
    return mapping

# ==================== ACCOUNT MAPPING PER CATEGORY ====================

@router.get("/category-mapping")
async def get_category_account_mapping(user: dict = Depends(get_current_user)):
    """Get account mappings per category"""
    db = get_database()
    mappings = await db.account_mapping_category.find({}, {"_id": 0}).to_list(500)
    return {"items": mappings}

@router.post("/category-mapping")
async def create_category_account_mapping(data: AccountMappingCreate, user: dict = Depends(get_current_user)):
    """Create account mapping for category"""
    db = get_database()
    
    mapping = {
        "id": str(uuid.uuid4()),
        "mapping_type": "category",
        "category_id": data.reference_id,
        "category_name": data.reference_name,
        "account_key": data.account_key,
        "account_code": data.account_code,
        "account_name": data.account_name,
        "updated_by": user.get("id"),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.account_mapping_category.insert_one(mapping)
    mapping.pop("_id", None)
    return mapping

# ==================== ACCOUNT MAPPING PER PAYMENT METHOD ====================

@router.get("/payment-mapping")
async def get_payment_account_mapping(user: dict = Depends(get_current_user)):
    """Get account mappings per payment method"""
    db = get_database()
    mappings = await db.account_mapping_payment.find({}, {"_id": 0}).to_list(500)
    return {"items": mappings}

@router.post("/payment-mapping")
async def create_payment_account_mapping(data: AccountMappingCreate, user: dict = Depends(get_current_user)):
    """Create account mapping for payment method"""
    db = get_database()
    
    mapping = {
        "id": str(uuid.uuid4()),
        "mapping_type": "payment_method",
        "payment_method_id": data.reference_id,
        "payment_method_name": data.reference_name,
        "account_key": data.account_key,
        "account_code": data.account_code,
        "account_name": data.account_name,
        "updated_by": user.get("id"),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.account_mapping_payment.insert_one(mapping)
    mapping.pop("_id", None)
    return mapping

# ==================== ACCOUNT MAPPING PER TAX ====================

@router.get("/tax-mapping")
async def get_tax_account_mapping(user: dict = Depends(get_current_user)):
    """Get account mappings per tax type"""
    db = get_database()
    mappings = await db.account_mapping_tax.find({}, {"_id": 0}).to_list(500)
    return {"items": mappings}

@router.post("/tax-mapping")
async def create_tax_account_mapping(data: AccountMappingCreate, user: dict = Depends(get_current_user)):
    """Create account mapping for tax type"""
    db = get_database()
    
    mapping = {
        "id": str(uuid.uuid4()),
        "mapping_type": "tax",
        "tax_type_id": data.reference_id,
        "tax_type_name": data.reference_name,
        "account_key": data.account_key,
        "account_code": data.account_code,
        "account_name": data.account_name,
        "updated_by": user.get("id"),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.account_mapping_tax.insert_one(mapping)
    mapping.pop("_id", None)
    return mapping

# ==================== ACCOUNT DERIVATION ENGINE ====================

@router.get("/derive-account")
async def derive_account(
    account_key: str,
    branch_id: str = None,
    warehouse_id: str = None,
    category_id: str = None,
    payment_method: str = None,
    tax_type: str = None,
    user: dict = Depends(get_current_user)
):
    """
    ACCOUNT DERIVATION ENGINE
    Priority: Branch > Warehouse > Category > Payment > Tax > Global
    """
    db = get_database()
    
    # Priority 1: Check branch mapping
    if branch_id:
        mapping = await db.account_mapping_branch.find_one({
            "branch_id": branch_id,
            "account_key": account_key
        }, {"_id": 0})
        if mapping:
            return {"account_code": mapping["account_code"], "account_name": mapping["account_name"], "source": "branch"}
    
    # Priority 2: Check warehouse mapping
    if warehouse_id:
        mapping = await db.account_mapping_warehouse.find_one({
            "warehouse_id": warehouse_id,
            "account_key": account_key
        }, {"_id": 0})
        if mapping:
            return {"account_code": mapping["account_code"], "account_name": mapping["account_name"], "source": "warehouse"}
    
    # Priority 3: Check category mapping
    if category_id:
        mapping = await db.account_mapping_category.find_one({
            "category_id": category_id,
            "account_key": account_key
        }, {"_id": 0})
        if mapping:
            return {"account_code": mapping["account_code"], "account_name": mapping["account_name"], "source": "category"}
    
    # Priority 4: Check payment method mapping
    if payment_method:
        mapping = await db.account_mapping_payment.find_one({
            "payment_method_id": payment_method,
            "account_key": account_key
        }, {"_id": 0})
        if mapping:
            return {"account_code": mapping["account_code"], "account_name": mapping["account_name"], "source": "payment"}
    
    # Priority 5: Check tax mapping
    if tax_type:
        mapping = await db.account_mapping_tax.find_one({
            "tax_type_id": tax_type,
            "account_key": account_key
        }, {"_id": 0})
        if mapping:
            return {"account_code": mapping["account_code"], "account_name": mapping["account_name"], "source": "tax"}
    
    # Priority 6: Fall back to global setting
    global_setting = await db.account_settings.find_one({
        "account_key": account_key
    }, {"_id": 0})
    
    if global_setting:
        return {"account_code": global_setting["account_code"], "account_name": global_setting["account_name"], "source": "global"}
    
    # Check defaults
    for tab, accounts in DEFAULT_ACCOUNT_SETTINGS.items():
        for acc in accounts:
            if acc["account_key"] == account_key:
                return {"account_code": acc["account_code"], "account_name": acc["account_name"], "source": "default"}
    
    raise HTTPException(status_code=404, detail=f"Account key '{account_key}' tidak ditemukan")

# ==================== FISCAL PERIOD SYSTEM ====================

@router.get("/fiscal-periods")
async def get_fiscal_periods(user: dict = Depends(get_current_user)):
    """Get all fiscal periods"""
    db = get_database()
    periods = await db.fiscal_periods.find({}, {"_id": 0}).sort("start_date", -1).to_list(100)
    return {"items": periods}

@router.post("/fiscal-periods")
async def create_fiscal_period(data: FiscalPeriodCreate, user: dict = Depends(get_current_user)):
    """Create fiscal period"""
    db = get_database()
    
    # Check overlap
    existing = await db.fiscal_periods.find_one({
        "$or": [
            {"start_date": {"$lte": data.end_date}, "end_date": {"$gte": data.start_date}},
        ]
    })
    if existing:
        raise HTTPException(status_code=400, detail="Periode fiscal overlap dengan periode yang sudah ada")
    
    period = {
        "id": str(uuid.uuid4()),
        "period_name": data.period_name,
        "start_date": data.start_date,
        "end_date": data.end_date,
        "status": data.status,
        "created_by": user.get("id"),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.fiscal_periods.insert_one(period)
    period.pop("_id", None)
    return period

@router.put("/fiscal-periods/{period_id}/status")
async def update_fiscal_period_status(period_id: str, status: str, user: dict = Depends(get_current_user)):
    """Update fiscal period status (open/closed/locked)"""
    db = get_database()
    
    if status not in ["open", "closed", "locked"]:
        raise HTTPException(status_code=400, detail="Status harus: open, closed, atau locked")
    
    result = await db.fiscal_periods.update_one(
        {"id": period_id},
        {"$set": {
            "status": status,
            "updated_by": user.get("id"),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Periode tidak ditemukan")
    
    return {"success": True, "new_status": status}

# ==================== CHART OF ACCOUNTS (For dropdown) ====================

@router.get("/chart-of-accounts")
async def get_chart_of_accounts(user: dict = Depends(get_current_user)):
    """Get chart of accounts for dropdown"""
    db = get_database()
    
    accounts = await db.chart_of_accounts.find({}, {"_id": 0}).sort("code", 1).to_list(500)
    
    # If no COA, return default structure
    if not accounts:
        accounts = [
            {"code": "1-1100", "name": "Kas", "type": "asset"},
            {"code": "1-1200", "name": "Bank", "type": "asset"},
            {"code": "1-1210", "name": "Piutang Kartu Kredit", "type": "asset"},
            {"code": "1-1220", "name": "Piutang E-Money", "type": "asset"},
            {"code": "1-1300", "name": "Piutang Usaha", "type": "asset"},
            {"code": "1-1400", "name": "Persediaan Barang", "type": "asset"},
            {"code": "1-1500", "name": "PPN Masukan", "type": "asset"},
            {"code": "1-1510", "name": "PPh 23 Dibayar Dimuka", "type": "asset"},
            {"code": "1-1600", "name": "Uang Muka Pembelian", "type": "asset"},
            {"code": "2-1100", "name": "Hutang Dagang", "type": "liability"},
            {"code": "2-1400", "name": "PPN Keluaran", "type": "liability"},
            {"code": "2-1700", "name": "Deposit Pelanggan", "type": "liability"},
            {"code": "2-1800", "name": "Hutang Komisi Sales", "type": "liability"},
            {"code": "3-1000", "name": "Modal", "type": "equity"},
            {"code": "3-3000", "name": "Laba Ditahan", "type": "equity"},
            {"code": "3-9000", "name": "Historical Balancing", "type": "equity"},
            {"code": "4-1000", "name": "Pendapatan Penjualan", "type": "revenue"},
            {"code": "4-1100", "name": "Pendapatan Jasa", "type": "revenue"},
            {"code": "4-2000", "name": "Potongan Penjualan", "type": "contra_revenue"},
            {"code": "5-1000", "name": "Harga Pokok Penjualan", "type": "expense"},
            {"code": "5-2000", "name": "Biaya Non Inventory", "type": "expense"},
            {"code": "5-4000", "name": "Beban Komisi Sales", "type": "expense"},
        ]
    
    return {"items": accounts}
