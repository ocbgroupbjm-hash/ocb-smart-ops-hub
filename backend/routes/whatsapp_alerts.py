# OCB TITAN AI - WhatsApp Alert System
# Automated alerts via WhatsApp

from fastapi import APIRouter, HTTPException
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel
import uuid
import json

from database import get_db

router = APIRouter(prefix="/api/whatsapp-alerts", tags=["WhatsApp Alerts"])

def gen_id():
    return str(uuid.uuid4())

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def get_wib_now():
    return datetime.now(timezone.utc) + timedelta(hours=7)

# Collections
def alert_config_col():
    return get_db()['whatsapp_alert_config']

def alert_log_col():
    return get_db()['whatsapp_alert_logs']

def alert_templates_col():
    return get_db()['whatsapp_alert_templates']

# ==================== MODELS ====================

class AlertRecipient(BaseModel):
    name: str
    phone: str
    role: str  # owner, hrd, spv, gudang, admin
    is_active: bool = True
    alert_types: List[str] = []  # Which alerts to receive

class AlertTemplate(BaseModel):
    trigger_type: str
    template_name: str
    message_template: str
    priority: str = "medium"  # low, medium, high, critical
    is_active: bool = True

class AlertConfig(BaseModel):
    is_enabled: bool = True
    api_provider: str = ""  # whatsapp provider (fonnte, wablas, etc)
    api_key: str = ""
    api_url: str = ""
    sender_number: str = ""

# ==================== ALERT TRIGGERS ====================

ALERT_TRIGGERS = {
    "minus_kas": {
        "name": "Minus Kas Cabang",
        "description": "Alert ketika cabang memiliki selisih kas minus",
        "default_template": "⚠️ ALERT MINUS KAS\n\nCabang: {branch_name}\nTanggal: {date}\nSelisih: Rp {amount}\nPenjaga: {penjaga_name}\n\nSegera lakukan investigasi!",
        "priority": "high",
        "recipients": ["owner", "hrd", "spv"]
    },
    "stok_kosong": {
        "name": "Stok Kosong",
        "description": "Alert ketika produk stok habis",
        "default_template": "📦 ALERT STOK KOSONG\n\nCabang: {branch_name}\nProduk: {product_name}\nKategori: {category}\n\nSegera lakukan restok!",
        "priority": "high",
        "recipients": ["owner", "gudang", "spv"]
    },
    "stok_minimum": {
        "name": "Stok di Bawah Minimum",
        "description": "Alert ketika stok di bawah minimum",
        "default_template": "📉 ALERT STOK MINIMUM\n\nCabang: {branch_name}\nProduk: {product_name}\nStok: {current_stock}\nMinimum: {min_stock}\n\nPertimbangkan untuk restok.",
        "priority": "medium",
        "recipients": ["gudang", "spv"]
    },
    "cabang_belum_setor": {
        "name": "Cabang Belum Setoran",
        "description": "Alert ketika cabang belum lapor setoran",
        "default_template": "⏰ ALERT BELUM SETOR\n\nCabang: {branch_name}\nTanggal: {date}\nStatus: Belum ada laporan setoran\n\nSegera follow up!",
        "priority": "medium",
        "recipients": ["owner", "spv"]
    },
    "spv_leave_store": {
        "name": "SPV Meninggalkan Toko",
        "description": "Alert ketika SPV terdeteksi meninggalkan lokasi toko",
        "default_template": "🚨 ALERT SPV MOVEMENT\n\nSPV: {spv_name}\nCabang: {branch_name}\nWaktu: {time}\nLokasi terakhir: {location}\n\nVerifikasi keberadaan SPV.",
        "priority": "high",
        "recipients": ["owner", "hrd"]
    },
    "kpi_terlambat": {
        "name": "KPI Terlambat",
        "description": "Alert ketika karyawan belum submit KPI",
        "default_template": "📋 ALERT KPI TERLAMBAT\n\nKaryawan: {employee_name}\nKPI: {kpi_name}\nDeadline: {deadline}\n\nSegera ingatkan karyawan.",
        "priority": "medium",
        "recipients": ["hrd", "spv"]
    },
    "performance_rendah": {
        "name": "Karyawan Performance Rendah",
        "description": "Alert ketika karyawan memiliki performa rendah",
        "default_template": "⚠️ ALERT PERFORMA RENDAH\n\nKaryawan: {employee_name}\nCabang: {branch_name}\nSkor: {score}%\nKategori: {category}\n\nLakukan evaluasi segera.",
        "priority": "high",
        "recipients": ["owner", "hrd"]
    },
    "audit_minus": {
        "name": "Audit Minus Besar",
        "description": "Alert ketika audit mendeteksi minus besar",
        "default_template": "🔴 ALERT AUDIT MINUS\n\nCabang: {branch_name}\nTipe: {audit_type}\nSelisih: Rp {amount}\nTanggal: {date}\n\nSEGERA investigasi!",
        "priority": "critical",
        "recipients": ["owner", "hrd"]
    },
    "cabang_bermasalah": {
        "name": "Cabang Bermasalah",
        "description": "Alert ketika cabang memiliki multiple issues",
        "default_template": "🚨 ALERT CABANG BERMASALAH\n\nCabang: {branch_name}\nMasalah:\n{issues}\n\nStatus: PERLU PERHATIAN SEGERA",
        "priority": "critical",
        "recipients": ["owner"]
    }
}

# ==================== CONFIGURATION ====================

@router.get("/config")
async def get_alert_config():
    """Get WhatsApp alert configuration"""
    config = await alert_config_col().find_one({"type": "main_config"}, {"_id": 0})
    if not config:
        config = {
            "type": "main_config",
            "is_enabled": False,
            "api_provider": "",
            "api_key": "",
            "api_url": "",
            "sender_number": "",
            "note": "Konfigurasi WhatsApp API belum diatur"
        }
    return config

@router.put("/config")
async def update_alert_config(config: AlertConfig):
    """Update WhatsApp alert configuration"""
    await alert_config_col().update_one(
        {"type": "main_config"},
        {"$set": {
            "type": "main_config",
            **config.dict(),
            "updated_at": now_iso()
        }},
        upsert=True
    )
    return {"message": "Konfigurasi berhasil disimpan"}

# ==================== RECIPIENTS ====================

@router.get("/recipients")
async def get_recipients():
    """Get all alert recipients"""
    recipients = await alert_config_col().find({"type": "recipient"}, {"_id": 0}).to_list(length=100)
    return {"recipients": recipients}

@router.post("/recipients")
async def add_recipient(recipient: AlertRecipient):
    """Add alert recipient"""
    doc = {
        "id": gen_id(),
        "type": "recipient",
        **recipient.dict(),
        "created_at": now_iso()
    }
    await alert_config_col().insert_one(doc)
    # Remove MongoDB _id before returning
    doc.pop("_id", None)
    return {"message": "Recipient berhasil ditambahkan", "recipient": doc}

@router.put("/recipients/{recipient_id}")
async def update_recipient(recipient_id: str, recipient: AlertRecipient):
    """Update alert recipient"""
    await alert_config_col().update_one(
        {"id": recipient_id, "type": "recipient"},
        {"$set": {**recipient.dict(), "updated_at": now_iso()}}
    )
    return {"message": "Recipient berhasil diupdate"}

@router.delete("/recipients/{recipient_id}")
async def delete_recipient(recipient_id: str):
    """Delete alert recipient"""
    await alert_config_col().delete_one({"id": recipient_id, "type": "recipient"})
    return {"message": "Recipient berhasil dihapus"}

# ==================== TEMPLATES ====================

@router.get("/triggers")
async def get_alert_triggers():
    """Get all available alert triggers"""
    return {"triggers": ALERT_TRIGGERS}

@router.get("/templates")
async def get_alert_templates():
    """Get all alert templates"""
    templates = await alert_templates_col().find({}, {"_id": 0}).to_list(length=100)
    
    # If no templates, create from defaults
    if not templates:
        for key, trigger in ALERT_TRIGGERS.items():
            template = {
                "id": gen_id(),
                "trigger_type": key,
                "template_name": trigger["name"],
                "message_template": trigger["default_template"],
                "priority": trigger["priority"],
                "default_recipients": trigger["recipients"],
                "is_active": True,
                "created_at": now_iso()
            }
            await alert_templates_col().insert_one(template)
            templates.append(template)
    
    return {"templates": templates}

@router.put("/templates/{template_id}")
async def update_template(template_id: str, template: AlertTemplate):
    """Update alert template"""
    await alert_templates_col().update_one(
        {"id": template_id},
        {"$set": {**template.dict(), "updated_at": now_iso()}}
    )
    return {"message": "Template berhasil diupdate"}

# ==================== SEND ALERTS ====================

@router.post("/send")
async def send_alert(
    trigger_type: str,
    data: dict,
    recipient_roles: List[str] = None
):
    """Send WhatsApp alert"""
    # Get config
    config = await alert_config_col().find_one({"type": "main_config"}, {"_id": 0})
    if not config or not config.get("is_enabled"):
        return {
            "sent": False,
            "reason": "WhatsApp alerts tidak aktif",
            "queued": True
        }
    
    # Get template
    template = await alert_templates_col().find_one({"trigger_type": trigger_type}, {"_id": 0})
    if not template or not template.get("is_active"):
        return {"sent": False, "reason": "Template tidak aktif"}
    
    # Get recipients
    roles = recipient_roles or ALERT_TRIGGERS.get(trigger_type, {}).get("recipients", [])
    recipients = await alert_config_col().find({
        "type": "recipient",
        "is_active": True,
        "role": {"$in": roles}
    }, {"_id": 0}).to_list(length=50)
    
    if not recipients:
        return {"sent": False, "reason": "Tidak ada recipient aktif"}
    
    # Format message
    message = template["message_template"]
    for key, value in data.items():
        message = message.replace(f"{{{key}}}", str(value))
    
    # Log alerts
    sent_count = 0
    for recipient in recipients:
        log = {
            "id": gen_id(),
            "trigger_type": trigger_type,
            "recipient_id": recipient["id"],
            "recipient_name": recipient["name"],
            "recipient_phone": recipient["phone"],
            "message": message,
            "priority": template.get("priority", "medium"),
            "status": "queued",  # Will be "sent" after actual API call
            "created_at": now_iso()
        }
        await alert_log_col().insert_one(log)
        sent_count += 1
    
    # In production, this would call WhatsApp API
    # For now, just log and return
    return {
        "sent": False,
        "queued": True,
        "recipients_count": sent_count,
        "message_preview": message[:200],
        "note": "Pesan di-queue. Konfigurasi WhatsApp API diperlukan untuk pengiriman aktual."
    }

@router.post("/test")
async def test_alert(phone: str, message: str = "Test alert dari OCB TITAN AI"):
    """Test WhatsApp alert"""
    config = await alert_config_col().find_one({"type": "main_config"}, {"_id": 0})
    
    if not config or not config.get("api_key"):
        return {
            "success": False,
            "message": "WhatsApp API belum dikonfigurasi",
            "config_status": "not_configured"
        }
    
    # In production, this would send actual test message
    log = {
        "id": gen_id(),
        "trigger_type": "test",
        "recipient_phone": phone,
        "message": message,
        "status": "test_queued",
        "created_at": now_iso()
    }
    await alert_log_col().insert_one(log)
    
    return {
        "success": True,
        "message": "Test alert queued",
        "note": "Konfigurasi WhatsApp API untuk pengiriman aktual"
    }

# ==================== ALERT LOGS ====================

@router.get("/logs")
async def get_alert_logs(limit: int = 100, status: Optional[str] = None):
    """Get alert logs"""
    query = {}
    if status:
        query["status"] = status
    
    logs = await alert_log_col().find(query, {"_id": 0}).sort("created_at", -1).to_list(length=limit)
    return {"logs": logs}

# ==================== AUTO-TRIGGER ENDPOINTS ====================

@router.post("/trigger/minus-kas")
async def trigger_minus_kas_alert(
    branch_name: str,
    date: str,
    amount: float,
    penjaga_name: str
):
    """Trigger minus kas alert"""
    return await send_alert("minus_kas", {
        "branch_name": branch_name,
        "date": date,
        "amount": f"{abs(amount):,.0f}",
        "penjaga_name": penjaga_name
    })

@router.post("/trigger/stok-kosong")
async def trigger_stok_kosong_alert(
    branch_name: str,
    product_name: str,
    category: str
):
    """Trigger stok kosong alert"""
    return await send_alert("stok_kosong", {
        "branch_name": branch_name,
        "product_name": product_name,
        "category": category
    })

@router.post("/trigger/cabang-bermasalah")
async def trigger_cabang_bermasalah_alert(
    branch_name: str,
    issues: List[str]
):
    """Trigger cabang bermasalah alert"""
    return await send_alert("cabang_bermasalah", {
        "branch_name": branch_name,
        "issues": "\n".join([f"• {i}" for i in issues])
    })

# ==================== INITIALIZE DEFAULT TEMPLATES ====================

@router.post("/init-templates")
async def initialize_templates():
    """Initialize default alert templates"""
    created = 0
    for key, trigger in ALERT_TRIGGERS.items():
        existing = await alert_templates_col().find_one({"trigger_type": key})
        if not existing:
            template = {
                "id": gen_id(),
                "trigger_type": key,
                "template_name": trigger["name"],
                "message_template": trigger["default_template"],
                "priority": trigger["priority"],
                "default_recipients": trigger["recipients"],
                "is_active": True,
                "created_at": now_iso()
            }
            await alert_templates_col().insert_one(template)
            created += 1
    
    return {"message": f"{created} template berhasil dibuat"}
