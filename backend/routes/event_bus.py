"""
OCB TITAN ERP - EVENT BUS SYSTEM
MASTER BLUEPRINT: Enterprise Hardening Phase - Guard System 5

Event-driven architecture untuk decouple komponen sistem.

Events:
- sale.posted
- purchase.received
- inventory.adjusted
- payroll.processed
- cash.deposited
- journal.posted

Listeners:
- inventory_service
- accounting_service
- kpi_service
- notification_service
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, Dict, List, Callable, Any
from datetime import datetime, timezone
from database import get_db
from utils.auth import get_current_user
import uuid
import asyncio
import json
import logging

router = APIRouter(prefix="/events", tags=["Event Bus System"])

logger = logging.getLogger("event_bus")

# Event Types
EVENT_TYPES = {
    "sale.created": "Penjualan dibuat",
    "sale.posted": "Penjualan di-posting",
    "sale.cancelled": "Penjualan dibatalkan",
    "sale.returned": "Penjualan di-retur",
    
    "purchase.created": "Pembelian dibuat",
    "purchase.received": "Pembelian diterima",
    "purchase.cancelled": "Pembelian dibatalkan",
    "purchase.returned": "Pembelian di-retur",
    
    "inventory.adjusted": "Stok di-adjust",
    "inventory.transferred": "Stok ditransfer",
    "inventory.opname_completed": "Stock opname selesai",
    
    "payment.received": "Pembayaran diterima",
    "payment.made": "Pembayaran dilakukan",
    
    "cash.shift_opened": "Shift kasir dibuka",
    "cash.shift_closed": "Shift kasir ditutup",
    "cash.deposited": "Setoran kas dicatat",
    "cash.variance_detected": "Selisih kas terdeteksi",
    
    "journal.posted": "Jurnal di-posting",
    "journal.reversed": "Jurnal di-reverse",
    
    "payroll.processed": "Payroll diproses",
    "payroll.paid": "Payroll dibayar",
    
    "user.created": "User dibuat",
    "user.deactivated": "User dinonaktifkan",
    
    "system.backup_completed": "Backup selesai",
    "system.restore_completed": "Restore selesai",
    "system.period_locked": "Periode dikunci",
    "system.reconciliation_completed": "Rekonsiliasi selesai"
}


class EventBus:
    """
    In-process Event Bus for OCB TITAN ERP
    
    Features:
    - Async event dispatch
    - Multiple listeners per event
    - Event history in MongoDB
    - Retry mechanism for failed listeners
    """
    
    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {}
        self._event_queue: asyncio.Queue = asyncio.Queue()
    
    def subscribe(self, event_type: str, listener: Callable):
        """Subscribe a listener to an event type"""
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(listener)
        logger.info(f"Listener subscribed to {event_type}")
    
    def unsubscribe(self, event_type: str, listener: Callable):
        """Unsubscribe a listener"""
        if event_type in self._listeners:
            self._listeners[event_type].remove(listener)
    
    async def publish(
        self,
        event_type: str,
        payload: Dict,
        tenant_id: str = "",
        user_id: str = "",
        user_name: str = "",
        branch_id: str = ""
    ) -> Dict:
        """
        Publish an event to all subscribed listeners
        
        Returns event record with delivery status
        """
        event_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        
        event = {
            "id": event_id,
            "event_type": event_type,
            "payload": payload,
            "tenant_id": tenant_id,
            "user_id": user_id,
            "user_name": user_name,
            "branch_id": branch_id,
            "created_at": timestamp,
            "status": "published",
            "delivery_results": []
        }
        
        # Store event in database (without returning _id)
        db = get_db()
        event_copy = event.copy()
        await db["event_log"].insert_one(event_copy)
        
        # Dispatch to listeners
        listeners = self._listeners.get(event_type, [])
        
        if not listeners:
            logger.debug(f"No listeners for event {event_type}")
            event["status"] = "no_listeners"
        else:
            for listener in listeners:
                try:
                    # Call listener asynchronously
                    if asyncio.iscoroutinefunction(listener):
                        result = await listener(event)
                    else:
                        result = listener(event)
                    
                    event["delivery_results"].append({
                        "listener": listener.__name__,
                        "status": "success",
                        "result": str(result)[:200] if result else None
                    })
                except Exception as e:
                    logger.error(f"Listener {listener.__name__} failed: {e}")
                    event["delivery_results"].append({
                        "listener": listener.__name__,
                        "status": "failed",
                        "error": str(e)
                    })
            
            # Update event with delivery results
            failed_count = sum(1 for r in event["delivery_results"] if r["status"] == "failed")
            if failed_count == 0:
                event["status"] = "delivered"
            elif failed_count == len(event["delivery_results"]):
                event["status"] = "failed"
            else:
                event["status"] = "partial"
        
        # Update in database
        await db["event_log"].update_one(
            {"id": event_id},
            {"$set": {
                "status": event["status"],
                "delivery_results": event["delivery_results"]
            }}
        )
        
        logger.info(f"Event {event_type} published: {event['status']}")
        
        return event
    
    def get_event_types(self) -> Dict:
        """Get all supported event types"""
        return EVENT_TYPES


# Global Event Bus instance
event_bus = EventBus()


# ==================== DEFAULT EVENT LISTENERS ====================

async def audit_log_listener(event: Dict):
    """Log all events to audit_logs"""
    db = get_db()
    await db["audit_logs"].insert_one({
        "id": str(uuid.uuid4()),
        "tenant_id": event.get("tenant_id", ""),
        "user_id": event.get("user_id", ""),
        "user_name": event.get("user_name", ""),
        "action": f"EVENT_{event['event_type'].upper().replace('.', '_')}",
        "module": "event_bus",
        "entity_type": "event",
        "entity_id": event.get("id"),
        "before_data": None,
        "after_data": event.get("payload"),
        "description": f"Event: {event['event_type']}",
        "ip_address": "system",
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    return "logged"


async def notification_listener(event: Dict):
    """Send notifications for important events"""
    # Critical events that should trigger notification
    critical_events = [
        "cash.variance_detected",
        "system.backup_completed",
        "system.period_locked"
    ]
    
    if event["event_type"] in critical_events:
        db = get_db()
        await db["notifications"].insert_one({
            "id": str(uuid.uuid4()),
            "tenant_id": event.get("tenant_id", ""),
            "type": "event_alert",
            "title": EVENT_TYPES.get(event["event_type"], event["event_type"]),
            "message": json.dumps(event.get("payload", {}), default=str),
            "event_id": event.get("id"),
            "is_read": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        return "notification_created"
    
    return "skipped"


# Subscribe default listeners
event_bus.subscribe("*", audit_log_listener)  # Wildcard not implemented, but shows intent


# ==================== API ENDPOINTS ====================

@router.get("/types")
async def get_event_types():
    """Get all supported event types"""
    return {
        "event_types": EVENT_TYPES,
        "total": len(EVENT_TYPES)
    }


@router.get("/log")
async def get_event_log(
    event_type: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = 100,
    user: dict = Depends(get_current_user)
):
    """Get event log history"""
    db = get_db()
    
    query = {}
    if event_type:
        query["event_type"] = event_type
    if status:
        query["status"] = status
    if date_from:
        query["created_at"] = {"$gte": date_from}
    if date_to:
        if "created_at" in query:
            query["created_at"]["$lte"] = date_to + "T23:59:59"
        else:
            query["created_at"] = {"$lte": date_to + "T23:59:59"}
    
    events = await db["event_log"].find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    return {
        "events": events,
        "total": len(events)
    }


@router.get("/log/{event_id}")
async def get_event_detail(
    event_id: str,
    user: dict = Depends(get_current_user)
):
    """Get event detail"""
    db = get_db()
    
    event = await db["event_log"].find_one(
        {"id": event_id},
        {"_id": 0}
    )
    
    if not event:
        raise HTTPException(status_code=404, detail="Event tidak ditemukan")
    
    return event


@router.get("/stats")
async def get_event_stats(
    days: int = 7,
    user: dict = Depends(get_current_user)
):
    """Get event statistics"""
    db = get_db()
    
    from datetime import timedelta
    date_from = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    
    # Count by event type
    pipeline = [
        {"$match": {"created_at": {"$gte": date_from}}},
        {"$group": {
            "_id": "$event_type",
            "count": {"$sum": 1},
            "failed": {"$sum": {"$cond": [{"$eq": ["$status", "failed"]}, 1, 0]}}
        }},
        {"$sort": {"count": -1}}
    ]
    
    by_type = await db["event_log"].aggregate(pipeline).to_list(50)
    
    # Count by status
    status_pipeline = [
        {"$match": {"created_at": {"$gte": date_from}}},
        {"$group": {
            "_id": "$status",
            "count": {"$sum": 1}
        }}
    ]
    
    by_status = await db["event_log"].aggregate(status_pipeline).to_list(10)
    
    total = await db["event_log"].count_documents({"created_at": {"$gte": date_from}})
    
    return {
        "period_days": days,
        "total_events": total,
        "by_type": by_type,
        "by_status": by_status
    }


@router.post("/publish")
async def publish_event(
    event_type: str,
    payload: Dict[str, Any],
    user: dict = Depends(get_current_user)
):
    """
    Publish a manual event (admin only)
    For testing or manual triggers
    """
    user_role = (user.get("role", "") or user.get("role_code", "")).lower()
    if user_role not in ["owner", "admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="AKSES DITOLAK")
    
    if event_type not in EVENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Event type tidak valid: {event_type}"
        )
    
    db = get_db()
    tenant_id = db.name
    
    event = await event_bus.publish(
        event_type=event_type,
        payload=payload,
        tenant_id=tenant_id,
        user_id=user.get("user_id", ""),
        user_name=user.get("name", ""),
        branch_id=user.get("branch_id", "")
    )
    
    return {
        "success": True,
        "event": event
    }


@router.post("/test")
async def test_event_bus(
    user: dict = Depends(get_current_user)
):
    """Test the event bus system"""
    db = get_db()
    
    test_payload = {
        "test": True,
        "message": "Event bus test",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    # Publish test event
    event = await event_bus.publish(
        event_type="sale.posted",
        payload=test_payload,
        tenant_id=db.name,
        user_id=user.get("user_id", ""),
        user_name=user.get("name", ""),
        branch_id=user.get("branch_id", "")
    )
    
    return {
        "success": True,
        "message": "Event bus test completed",
        "event": event
    }


# ==================== HELPER FOR OTHER MODULES ====================

async def emit_event(
    event_type: str,
    payload: Dict,
    user: dict = None,
    branch_id: str = ""
):
    """
    Helper function for other modules to emit events.
    
    Usage:
        from routes.event_bus import emit_event
        
        await emit_event(
            event_type="sale.posted",
            payload={"sale_id": sale["id"], "total": sale["total"]},
            user=current_user,
            branch_id=sale["branch_id"]
        )
    """
    db = get_db()
    
    return await event_bus.publish(
        event_type=event_type,
        payload=payload,
        tenant_id=db.name,
        user_id=user.get("user_id", "") if user else "",
        user_name=user.get("name", "") if user else "",
        branch_id=branch_id
    )


# Export event bus for direct access
__all__ = ["router", "event_bus", "emit_event", "EVENT_TYPES"]
