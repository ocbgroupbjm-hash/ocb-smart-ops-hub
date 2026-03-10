# OCB TITAN AI - Real-time War Room Alerts
# Alert panel for War Room dashboard

from fastapi import APIRouter, HTTPException
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel
import uuid

from database import get_db

router = APIRouter(prefix="/api/warroom-alerts", tags=["War Room Alerts"])

def gen_id():
    return str(uuid.uuid4())

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def get_wib_now():
    return datetime.now(timezone.utc) + timedelta(hours=7)

# Collections
def alerts_col():
    return get_db()['warroom_alerts']

def notifications_col():
    return get_db()['alert_notifications']

# ==================== MODELS ====================

class Alert(BaseModel):
    alert_type: str  # minus_kas, stok_kosong, cabang_bermasalah, etc.
    priority: str  # critical, high, medium, low
    title: str
    message: str
    branch_id: str = ""
    branch_name: str = ""
    related_entity_id: str = ""
    related_entity_type: str = ""
    data: dict = {}

class AlertAction(BaseModel):
    action: str  # acknowledge, resolve, escalate, snooze
    notes: str = ""
    user_id: str
    user_name: str

# ==================== CREATE ALERTS ====================

@router.post("/create")
async def create_alert(alert: Alert):
    """Create new war room alert"""
    doc = {
        "id": gen_id(),
        **alert.dict(),
        "status": "new",  # new, acknowledged, in_progress, resolved, escalated
        "created_at": now_iso(),
        "acknowledged_at": None,
        "resolved_at": None,
        "acknowledged_by": None,
        "resolved_by": None,
        "action_history": [],
        "notifications_sent": []
    }
    
    await alerts_col().insert_one(doc)
    
    # Create notification records for relevant recipients
    recipients = get_alert_recipients(alert.alert_type, alert.priority)
    for recipient in recipients:
        notification = {
            "id": gen_id(),
            "alert_id": doc["id"],
            "recipient_role": recipient,
            "status": "pending",
            "created_at": now_iso()
        }
        await notifications_col().insert_one(notification)
        doc["notifications_sent"].append(recipient)
    
    await alerts_col().update_one({"id": doc["id"]}, {"$set": {"notifications_sent": doc["notifications_sent"]}})
    
    doc.pop("_id", None)
    return {"message": "Alert berhasil dibuat", "alert": doc}

def get_alert_recipients(alert_type: str, priority: str) -> List[str]:
    """Get recipients based on alert type and priority"""
    recipients = {
        "minus_kas": ["owner", "hrd", "spv"],
        "stok_kosong": ["owner", "gudang", "spv"],
        "stok_minimum": ["gudang", "spv"],
        "cabang_belum_setor": ["owner", "spv"],
        "spv_leave_store": ["owner", "hrd"],
        "kpi_terlambat": ["hrd", "spv"],
        "performance_rendah": ["owner", "hrd"],
        "audit_minus": ["owner", "hrd"],
        "cabang_bermasalah": ["owner"]
    }
    
    base_recipients = recipients.get(alert_type, ["admin"])
    
    # Add owner for critical/high priority
    if priority in ["critical", "high"] and "owner" not in base_recipients:
        base_recipients.append("owner")
    
    return base_recipients

# ==================== GET ALERTS ====================

@router.get("/active")
async def get_active_alerts(
    priority: Optional[str] = None,
    branch_id: Optional[str] = None,
    alert_type: Optional[str] = None,
    limit: int = 50
):
    """Get active (unresolved) alerts"""
    query = {"status": {"$nin": ["resolved"]}}
    
    if priority:
        query["priority"] = priority
    if branch_id:
        query["branch_id"] = branch_id
    if alert_type:
        query["alert_type"] = alert_type
    
    alerts = await alerts_col().find(query, {"_id": 0}).sort("created_at", -1).to_list(length=limit)
    
    # Count by priority
    all_active = await alerts_col().find({"status": {"$nin": ["resolved"]}}, {"priority": 1, "_id": 0}).to_list(length=1000)
    
    summary = {
        "critical": len([a for a in all_active if a.get("priority") == "critical"]),
        "high": len([a for a in all_active if a.get("priority") == "high"]),
        "medium": len([a for a in all_active if a.get("priority") == "medium"]),
        "low": len([a for a in all_active if a.get("priority") == "low"])
    }
    
    return {
        "total": len(alerts),
        "summary": summary,
        "alerts": alerts
    }

@router.get("/all")
async def get_all_alerts(
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100
):
    """Get all alerts with filters"""
    query = {}
    
    if status:
        query["status"] = status
    if start_date and end_date:
        query["created_at"] = {"$gte": start_date, "$lte": end_date}
    
    alerts = await alerts_col().find(query, {"_id": 0}).sort("created_at", -1).to_list(length=limit)
    return {"alerts": alerts}

@router.get("/{alert_id}")
async def get_alert_detail(alert_id: str):
    """Get alert detail"""
    alert = await alerts_col().find_one({"id": alert_id}, {"_id": 0})
    if not alert:
        raise HTTPException(status_code=404, detail="Alert tidak ditemukan")
    return alert

# ==================== ALERT ACTIONS ====================

@router.post("/{alert_id}/action")
async def perform_alert_action(alert_id: str, action: AlertAction):
    """Perform action on alert"""
    alert = await alerts_col().find_one({"id": alert_id}, {"_id": 0})
    if not alert:
        raise HTTPException(status_code=404, detail="Alert tidak ditemukan")
    
    action_record = {
        "action": action.action,
        "notes": action.notes,
        "user_id": action.user_id,
        "user_name": action.user_name,
        "timestamp": now_iso()
    }
    
    update = {
        "$push": {"action_history": action_record}
    }
    
    if action.action == "acknowledge":
        update["$set"] = {
            "status": "acknowledged",
            "acknowledged_at": now_iso(),
            "acknowledged_by": action.user_name
        }
    elif action.action == "resolve":
        update["$set"] = {
            "status": "resolved",
            "resolved_at": now_iso(),
            "resolved_by": action.user_name
        }
    elif action.action == "escalate":
        update["$set"] = {
            "status": "escalated",
            "escalated_at": now_iso(),
            "escalated_by": action.user_name
        }
    elif action.action == "in_progress":
        update["$set"] = {"status": "in_progress"}
    
    await alerts_col().update_one({"id": alert_id}, update)
    
    return {"message": f"Alert berhasil di-{action.action}"}

@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, user_name: str):
    """Quick acknowledge alert"""
    return await perform_alert_action(alert_id, AlertAction(
        action="acknowledge",
        user_id="",
        user_name=user_name
    ))

@router.post("/{alert_id}/resolve")
async def resolve_alert(alert_id: str, user_name: str, notes: str = ""):
    """Quick resolve alert"""
    return await perform_alert_action(alert_id, AlertAction(
        action="resolve",
        notes=notes,
        user_id="",
        user_name=user_name
    ))

# ==================== DASHBOARD STATS ====================

@router.get("/stats/summary")
async def get_alert_stats():
    """Get alert statistics for dashboard"""
    today = get_wib_now().strftime("%Y-%m-%d")
    
    # All active
    active = await alerts_col().find({"status": {"$nin": ["resolved"]}}, {"_id": 0}).to_list(length=1000)
    
    # Today's alerts
    today_alerts = await alerts_col().find({
        "created_at": {"$gte": f"{today}T00:00:00"}
    }, {"_id": 0}).to_list(length=1000)
    
    # By branch
    branch_alerts = {}
    for a in active:
        bid = a.get("branch_name") or "Unknown"
        if bid not in branch_alerts:
            branch_alerts[bid] = 0
        branch_alerts[bid] += 1
    
    # Top affected branches
    top_branches = sorted(branch_alerts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return {
        "total_active": len(active),
        "by_priority": {
            "critical": len([a for a in active if a.get("priority") == "critical"]),
            "high": len([a for a in active if a.get("priority") == "high"]),
            "medium": len([a for a in active if a.get("priority") == "medium"]),
            "low": len([a for a in active if a.get("priority") == "low"])
        },
        "by_status": {
            "new": len([a for a in active if a.get("status") == "new"]),
            "acknowledged": len([a for a in active if a.get("status") == "acknowledged"]),
            "in_progress": len([a for a in active if a.get("status") == "in_progress"]),
            "escalated": len([a for a in active if a.get("status") == "escalated"])
        },
        "today_count": len(today_alerts),
        "top_affected_branches": [{"branch": b, "count": c} for b, c in top_branches],
        "generated_at": now_iso()
    }

# ==================== AUTO-GENERATE ALERTS ====================

@router.post("/auto/check-minus")
async def auto_check_minus_kas():
    """Auto-check for minus kas and create alerts"""
    today = get_wib_now().strftime("%Y-%m-%d")
    
    setoran_col = get_db()['setoran_harian']
    setoran = await setoran_col.find({
        "tanggal": today,
        "selisih": {"$lt": -50000}  # Minus more than 50k
    }, {"_id": 0}).to_list(length=100)
    
    alerts_created = 0
    for s in setoran:
        # Check if alert already exists
        existing = await alerts_col().find_one({
            "alert_type": "minus_kas",
            "related_entity_id": s.get("id"),
            "status": {"$nin": ["resolved"]}
        })
        
        if existing:
            continue
        
        await create_alert(Alert(
            alert_type="minus_kas",
            priority="high" if s.get("selisih", 0) < -100000 else "medium",
            title=f"Minus Kas: {s.get('branch_name')}",
            message=f"Selisih kas Rp {abs(s.get('selisih', 0)):,.0f} pada {s.get('tanggal')}",
            branch_id=s.get("branch_id", ""),
            branch_name=s.get("branch_name", ""),
            related_entity_id=s.get("id", ""),
            related_entity_type="setoran",
            data={"amount": s.get("selisih"), "penjaga": s.get("penjaga_name")}
        ))
        alerts_created += 1
    
    return {"message": f"{alerts_created} alert minus kas dibuat"}

@router.post("/auto/check-stock")
async def auto_check_stock():
    """Auto-check for empty/low stock and create alerts"""
    products_col = get_db()['products']
    
    # Empty stock
    empty_stock = await products_col.find({
        "stock": 0,
        "is_active": True
    }, {"_id": 0}).to_list(length=500)
    
    # Low stock
    low_stock = await products_col.find({
        "$expr": {"$and": [
            {"$lt": ["$stock", "$min_stock"]},
            {"$gt": ["$stock", 0]}
        ]},
        "is_active": True
    }, {"_id": 0}).to_list(length=500)
    
    alerts_created = 0
    
    for p in empty_stock:
        existing = await alerts_col().find_one({
            "alert_type": "stok_kosong",
            "related_entity_id": p.get("id"),
            "status": {"$nin": ["resolved"]}
        })
        
        if existing:
            continue
        
        await create_alert(Alert(
            alert_type="stok_kosong",
            priority="high",
            title=f"Stok Kosong: {p.get('name')}",
            message=f"Produk {p.get('code')} - {p.get('name')} sudah habis",
            related_entity_id=p.get("id", ""),
            related_entity_type="product",
            data={"product_code": p.get("code"), "product_name": p.get("name")}
        ))
        alerts_created += 1
    
    for p in low_stock:
        existing = await alerts_col().find_one({
            "alert_type": "stok_minimum",
            "related_entity_id": p.get("id"),
            "status": {"$nin": ["resolved"]}
        })
        
        if existing:
            continue
        
        await create_alert(Alert(
            alert_type="stok_minimum",
            priority="medium",
            title=f"Stok Rendah: {p.get('name')}",
            message=f"Stok {p.get('stock')} di bawah minimum {p.get('min_stock', 10)}",
            related_entity_id=p.get("id", ""),
            related_entity_type="product",
            data={"stock": p.get("stock"), "min_stock": p.get("min_stock")}
        ))
        alerts_created += 1
    
    return {"message": f"{alerts_created} alert stok dibuat"}

@router.post("/auto/check-unreported")
async def auto_check_unreported_branches():
    """Auto-check for branches that haven't reported setoran"""
    today = get_wib_now().strftime("%Y-%m-%d")
    current_hour = get_wib_now().hour
    
    # Only check after 15:00 WIB
    if current_hour < 15:
        return {"message": "Pengecekan dilakukan setelah jam 15:00 WIB"}
    
    branches_col = get_db()['branches']
    setoran_col = get_db()['setoran_harian']
    
    all_branches = await branches_col.find({"is_active": True}, {"_id": 0}).to_list(length=100)
    setoran_today = await setoran_col.find({"tanggal": today}, {"_id": 0}).to_list(length=100)
    
    reported_branch_ids = set(s.get("branch_id") for s in setoran_today)
    
    alerts_created = 0
    for branch in all_branches:
        if branch.get("id") in reported_branch_ids:
            continue
        
        existing = await alerts_col().find_one({
            "alert_type": "cabang_belum_setor",
            "branch_id": branch.get("id"),
            "created_at": {"$gte": f"{today}T00:00:00"},
            "status": {"$nin": ["resolved"]}
        })
        
        if existing:
            continue
        
        await create_alert(Alert(
            alert_type="cabang_belum_setor",
            priority="medium",
            title=f"Belum Setoran: {branch.get('name')}",
            message=f"Cabang {branch.get('code')} belum melaporkan setoran hari ini",
            branch_id=branch.get("id", ""),
            branch_name=branch.get("name", ""),
            related_entity_id=branch.get("id", ""),
            related_entity_type="branch"
        ))
        alerts_created += 1
    
    return {"message": f"{alerts_created} alert cabang belum setor dibuat"}
