# OCB AI TITAN - Print Settings Routes
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
from database import db
from utils.auth import get_current_user
import uuid

router = APIRouter(prefix="/api/print", tags=["Print Settings"])

print_settings_collection = db["print_settings"]

class PrinterConfig(BaseModel):
    id: Optional[str] = None
    name: str
    type: str  # usb, bluetooth, wifi, network
    connection_string: str  # port/address
    paper_width: int = 80  # mm (58, 80)
    is_default: bool = False
    branch_id: Optional[str] = None

class ReceiptTemplate(BaseModel):
    show_logo: bool = True
    logo_url: Optional[str] = None
    header_text: str = ""
    show_branch_name: bool = True
    show_branch_address: bool = True
    show_branch_phone: bool = True
    show_cashier_name: bool = True
    show_customer_name: bool = True
    show_date_time: bool = True
    show_tax_detail: bool = True
    show_payment_method: bool = True
    footer_text: str = "Terima kasih atas kunjungan Anda!"
    additional_notes: str = ""

class PrintSettings(BaseModel):
    auto_print: bool = False
    print_copies: int = 1
    open_drawer: bool = True
    cut_paper: bool = True
    beep_after_print: bool = False

@router.get("/printers")
async def get_printers(user: dict = Depends(get_current_user)):
    """Get all configured printers"""
    printers = await print_settings_collection.find(
        {"type": "printer"},
        {"_id": 0}
    ).to_list(50)
    return {"printers": printers}

@router.post("/printers")
async def add_printer(config: PrinterConfig, user: dict = Depends(get_current_user)):
    """Add new printer configuration"""
    if user.get("role") not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Hanya owner/admin yang dapat menambah printer")
    
    printer_data = config.dict()
    printer_data["id"] = str(uuid.uuid4())
    printer_data["type"] = "printer"
    printer_data["printer_type"] = config.type
    printer_data["created_at"] = datetime.now(timezone.utc).isoformat()
    
    # If setting as default, unset other defaults
    if config.is_default:
        await print_settings_collection.update_many(
            {"type": "printer"},
            {"$set": {"is_default": False}}
        )
    
    await print_settings_collection.insert_one(printer_data)
    if "_id" in printer_data:
        del printer_data["_id"]
    
    return {"id": printer_data["id"], "message": "Printer berhasil ditambahkan"}

@router.put("/printers/{printer_id}")
async def update_printer(printer_id: str, config: PrinterConfig, user: dict = Depends(get_current_user)):
    """Update printer configuration"""
    if user.get("role") not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Hanya owner/admin yang dapat mengubah printer")
    
    update_data = config.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    if config.is_default:
        await print_settings_collection.update_many(
            {"type": "printer"},
            {"$set": {"is_default": False}}
        )
    
    result = await print_settings_collection.update_one(
        {"id": printer_id, "type": "printer"},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Printer tidak ditemukan")
    
    return {"message": "Printer berhasil diupdate"}

@router.delete("/printers/{printer_id}")
async def delete_printer(printer_id: str, user: dict = Depends(get_current_user)):
    """Delete printer configuration"""
    if user.get("role") not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Hanya owner/admin yang dapat menghapus printer")
    
    result = await print_settings_collection.delete_one({"id": printer_id, "type": "printer"})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Printer tidak ditemukan")
    
    return {"message": "Printer berhasil dihapus"}

@router.get("/template")
async def get_receipt_template(user: dict = Depends(get_current_user)):
    """Get receipt template settings"""
    branch_id = user.get("branch_id")
    template = await print_settings_collection.find_one(
        {"type": "template", "branch_id": branch_id},
        {"_id": 0}
    )
    
    if not template:
        # Return default template
        template = ReceiptTemplate().dict()
        template["branch_id"] = branch_id
    
    return template

@router.put("/template")
async def update_receipt_template(template: ReceiptTemplate, user: dict = Depends(get_current_user)):
    """Update receipt template settings"""
    if user.get("role") not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Hanya owner/admin yang dapat mengubah template")
    
    branch_id = user.get("branch_id")
    template_data = template.dict()
    template_data["type"] = "template"
    template_data["branch_id"] = branch_id
    template_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await print_settings_collection.update_one(
        {"type": "template", "branch_id": branch_id},
        {"$set": template_data},
        upsert=True
    )
    
    return {"message": "Template struk berhasil diupdate"}

@router.get("/settings")
async def get_print_settings(user: dict = Depends(get_current_user)):
    """Get print settings"""
    branch_id = user.get("branch_id")
    settings = await print_settings_collection.find_one(
        {"type": "settings", "branch_id": branch_id},
        {"_id": 0}
    )
    
    if not settings:
        settings = PrintSettings().dict()
        settings["branch_id"] = branch_id
    
    return settings

@router.put("/settings")
async def update_print_settings(settings: PrintSettings, user: dict = Depends(get_current_user)):
    """Update print settings"""
    if user.get("role") not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Hanya owner/admin yang dapat mengubah pengaturan")
    
    branch_id = user.get("branch_id")
    settings_data = settings.dict()
    settings_data["type"] = "settings"
    settings_data["branch_id"] = branch_id
    settings_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await print_settings_collection.update_one(
        {"type": "settings", "branch_id": branch_id},
        {"$set": settings_data},
        upsert=True
    )
    
    return {"message": "Pengaturan print berhasil diupdate"}

@router.post("/test")
async def test_print(printer_id: str = None, user: dict = Depends(get_current_user)):
    """Test print to selected printer"""
    # In a real implementation, this would send a test page to the printer
    # For now, we just simulate the test
    return {
        "success": True,
        "message": "Test print berhasil dikirim",
        "note": "Printer akan mencetak halaman tes jika terhubung dengan benar"
    }
