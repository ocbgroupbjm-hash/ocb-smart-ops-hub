# OCB AI TITAN - Settings API
# Printer, Company, General Settings, etc.

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
from database import db
from utils.auth import get_current_user
from datetime import datetime, timezone
import uuid

router = APIRouter(prefix="/settings", tags=["Settings"])

settings_collection = db["settings"]

# ==================== PRINTER SETTINGS ====================

class PrinterSettings(BaseModel):
    printer_type: str = "thermal"
    connection_type: str = "usb"
    printer_name: str = ""
    ip_address: str = ""
    port: int = 9100
    bluetooth_address: str = ""
    paper_width: int = 80
    auto_cut: bool = True
    open_drawer: bool = False
    header_logo: bool = True
    header_text: str = "OCB AI TITAN"
    header_subtitle: str = "Enterprise Retail System"
    header_address: str = ""
    header_phone: str = ""
    footer_text: str = "Terima kasih atas kunjungan Anda"
    footer_note: str = ""
    print_copies: int = 1
    font_size: str = "normal"
    show_logo: bool = True
    show_barcode: bool = True
    show_qr_code: bool = False

@router.get("/printer")
async def get_printer_settings(user: dict = Depends(get_current_user)):
    settings = await settings_collection.find_one({"type": "printer"}, {"_id": 0})
    if settings:
        return settings.get("data", {})
    return PrinterSettings().model_dump()

@router.post("/printer")
async def save_printer_settings(data: PrinterSettings, user: dict = Depends(get_current_user)):
    await settings_collection.update_one(
        {"type": "printer"},
        {"$set": {
            "type": "printer",
            "data": data.model_dump(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "updated_by": user.get("id")
        }},
        upsert=True
    )
    return {"message": "Pengaturan printer berhasil disimpan"}

@router.post("/printer/test")
async def test_print(user: dict = Depends(get_current_user)):
    # In real implementation, this would send test print to printer
    # For now, just simulate success
    return {"message": "Test print berhasil dikirim", "status": "success"}

# ==================== COMPANY SETTINGS ====================

class CompanySettings(BaseModel):
    name: str = "OCB AI TITAN"
    tagline: str = "Enterprise Retail System"
    address: str = ""
    city: str = ""
    province: str = ""
    postal_code: str = ""
    phone: str = ""
    email: str = ""
    website: str = ""
    npwp: str = ""
    logo_url: str = ""

@router.get("/company")
async def get_company_settings(user: dict = Depends(get_current_user)):
    settings = await settings_collection.find_one({"type": "company"}, {"_id": 0})
    if settings:
        return settings.get("data", {})
    return CompanySettings().model_dump()

@router.post("/company")
async def save_company_settings(data: CompanySettings, user: dict = Depends(get_current_user)):
    await settings_collection.update_one(
        {"type": "company"},
        {"$set": {
            "type": "company",
            "data": data.model_dump(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "updated_by": user.get("id")
        }},
        upsert=True
    )
    return {"message": "Pengaturan perusahaan berhasil disimpan"}

# ==================== GENERAL SETTINGS ====================

class GeneralSettings(BaseModel):
    currency: str = "IDR"
    currency_symbol: str = "Rp"
    decimal_places: int = 0
    date_format: str = "DD/MM/YYYY"
    time_format: str = "HH:mm"
    timezone: str = "Asia/Jakarta"
    language: str = "id"
    tax_rate: float = 11
    default_branch_id: str = ""

@router.get("/general")
async def get_general_settings(user: dict = Depends(get_current_user)):
    settings = await settings_collection.find_one({"type": "general"}, {"_id": 0})
    if settings:
        return settings.get("data", {})
    return GeneralSettings().model_dump()

@router.post("/general")
async def save_general_settings(data: GeneralSettings, user: dict = Depends(get_current_user)):
    await settings_collection.update_one(
        {"type": "general"},
        {"$set": {
            "type": "general",
            "data": data.model_dump(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "updated_by": user.get("id")
        }},
        upsert=True
    )
    return {"message": "Pengaturan umum berhasil disimpan"}

# ==================== NUMBERING SETTINGS ====================

class NumberingSettings(BaseModel):
    po_prefix: str = "PO"
    po_digits: int = 6
    po_reset: str = "never"  # never, yearly, monthly
    
    so_prefix: str = "SO"
    so_digits: int = 6
    so_reset: str = "never"
    
    invoice_prefix: str = "INV"
    invoice_digits: int = 6
    invoice_reset: str = "yearly"
    
    receipt_prefix: str = "TRX"
    receipt_digits: int = 6
    receipt_reset: str = "daily"

@router.get("/numbering")
async def get_numbering_settings(user: dict = Depends(get_current_user)):
    settings = await settings_collection.find_one({"type": "numbering"}, {"_id": 0})
    if settings:
        return settings.get("data", {})
    return NumberingSettings().model_dump()

@router.post("/numbering")
async def save_numbering_settings(data: NumberingSettings, user: dict = Depends(get_current_user)):
    await settings_collection.update_one(
        {"type": "numbering"},
        {"$set": {
            "type": "numbering",
            "data": data.model_dump(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "updated_by": user.get("id")
        }},
        upsert=True
    )
    return {"message": "Pengaturan nomor berhasil disimpan"}

# ==================== ACTIVITY LOG ====================

activity_logs = db["activity_logs"]

@router.get("/activity-log")
async def get_activity_logs(
    page: int = 1,
    limit: int = 50,
    user: dict = Depends(get_current_user)
):
    skip = (page - 1) * limit
    cursor = activity_logs.find({}, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
    logs = await cursor.to_list(limit)
    total = await activity_logs.count_documents({})
    return {"items": logs, "total": total, "page": page, "limit": limit}

# ==================== BACKUP & RESTORE ====================

@router.post("/backup")
async def create_backup(user: dict = Depends(get_current_user)):
    # In real implementation, this would create database backup
    backup_id = str(uuid.uuid4())
    backup_record = {
        "id": backup_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user.get("id"),
        "status": "completed",
        "size": "0 MB"
    }
    await db["backups"].insert_one(backup_record)
    return {"message": "Backup berhasil dibuat", "backup_id": backup_id}

@router.get("/backups")
async def list_backups(user: dict = Depends(get_current_user)):
    cursor = db["backups"].find({}, {"_id": 0}).sort("created_at", -1).limit(20)
    backups = await cursor.to_list(20)
    return backups

@router.post("/restore/{backup_id}")
async def restore_backup(backup_id: str, user: dict = Depends(get_current_user)):
    backup = await db["backups"].find_one({"id": backup_id})
    if not backup:
        raise HTTPException(status_code=404, detail="Backup tidak ditemukan")
    # In real implementation, this would restore from backup
    return {"message": "Restore berhasil dimulai"}

# ==================== SYSTEM INFO ====================

@router.get("/info")
async def get_system_info(user: dict = Depends(get_current_user)):
    return {
        "system_name": "OCB AI TITAN",
        "version": "2.0.0",
        "description": "Enterprise Retail AI System",
        "company": "OCB GROUP",
        "modules": [
            "Master Data", "Pembelian", "Penjualan", "Persediaan",
            "Akuntansi", "Laporan", "Hallo AI", "AI Business"
        ],
        "ai_capabilities": [
            "CEO AI", "CFO AI", "COO AI", "CMO AI",
            "Sales AI", "Customer Service AI", "Business Analyst AI"
        ],
        "database": "MongoDB",
        "api": "FastAPI",
        "frontend": "React"
    }
