# OCB GROUP SUPER AI - AI Marketing Routes
# Automated marketing campaigns and customer segmentation

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import uuid

from database import get_db

router = APIRouter(prefix="/api/ai-marketing", tags=["AI Marketing"])

def gen_id() -> str:
    return str(uuid.uuid4())

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

# ==================== REQUEST MODELS ====================

class CreateCampaignRequest(BaseModel):
    name: str
    description: str = ""
    campaign_type: str = "broadcast"  # broadcast, promo, reminder, followup
    target_segments: List[str] = []
    target_activity: List[str] = []
    target_branches: List[str] = []
    message_template: str = ""
    image_url: str = ""
    promo_code: str = ""
    channels: List[str] = ["internal_chat"]
    scheduled_at: Optional[str] = None
    budget: float = 0

class BroadcastMessageRequest(BaseModel):
    campaign_id: Optional[str] = None
    message: str
    target_segment: str = "all"
    target_activity: str = "all"
    channel: str = "internal_chat"

# ==================== AI MARKETING ENDPOINTS ====================

@router.get("/customers/segments")
async def get_customer_segments():
    """Get customer segmentation overview"""
    db = get_db()
    
    # Get all customers
    customers = await db['customers'].find({}, {"_id": 0}).to_list(None)
    
    # Segment by type
    segments = {
        "regular": [],
        "member": [],
        "vip": [],
        "reseller": [],
        "wholesale": []
    }
    
    # Activity status
    activity = {
        "active": [],      # Transaksi dalam 30 hari
        "passive": [],     # Tidak transaksi 30-90 hari
        "dormant": [],     # Tidak transaksi > 90 hari
        "new": []          # Baru bergabung
    }
    
    now = datetime.now(timezone.utc)
    
    for customer in customers:
        # By segment
        segment = customer.get("segment", "regular")
        if segment in segments:
            segments[segment].append(customer)
        
        # By activity
        last_purchase = customer.get("last_purchase_date")
        created_at = customer.get("created_at", "")
        
        if last_purchase:
            try:
                last_date = datetime.fromisoformat(last_purchase.replace("Z", "+00:00"))
                days_ago = (now - last_date).days
                
                if days_ago <= 30:
                    activity["active"].append(customer)
                elif days_ago <= 90:
                    activity["passive"].append(customer)
                else:
                    activity["dormant"].append(customer)
            except:
                activity["dormant"].append(customer)
        elif created_at:
            try:
                created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                if (now - created).days <= 30:
                    activity["new"].append(customer)
                else:
                    activity["dormant"].append(customer)
            except:
                activity["dormant"].append(customer)
    
    # Calculate stats
    segment_stats = {}
    for seg, custs in segments.items():
        segment_stats[seg] = {
            "count": len(custs),
            "total_value": sum(c.get("lifetime_value", 0) for c in custs),
            "avg_value": sum(c.get("lifetime_value", 0) for c in custs) / len(custs) if custs else 0
        }
    
    activity_stats = {}
    for act, custs in activity.items():
        activity_stats[act] = {
            "count": len(custs),
            "total_value": sum(c.get("lifetime_value", 0) for c in custs)
        }
    
    return {
        "total_customers": len(customers),
        "by_segment": segment_stats,
        "by_activity": activity_stats,
        "segment_list": list(segments.keys()),
        "activity_list": list(activity.keys())
    }

@router.post("/campaign/create")
async def create_campaign(data: CreateCampaignRequest):
    """Create a new marketing campaign"""
    db = get_db()
    
    # Count target customers
    filter_query = {}
    if data.target_segments:
        filter_query["segment"] = {"$in": data.target_segments}
    if data.target_activity:
        filter_query["activity_status"] = {"$in": data.target_activity}
    
    target_count = await db['customers'].count_documents(filter_query) if filter_query else await db['customers'].count_documents({})
    
    campaign = {
        "id": gen_id(),
        "name": data.name,
        "description": data.description,
        "campaign_type": data.campaign_type,
        "target_segments": data.target_segments,
        "target_activity": data.target_activity,
        "target_branches": data.target_branches,
        "target_customer_ids": [],
        "message_template": data.message_template,
        "image_url": data.image_url,
        "promo_code": data.promo_code,
        "product_ids": [],
        "channels": data.channels,
        "scheduled_at": data.scheduled_at,
        "started_at": None,
        "completed_at": None,
        "status": "draft" if data.scheduled_at else "draft",
        "total_targets": target_count,
        "sent_count": 0,
        "delivered_count": 0,
        "read_count": 0,
        "clicked_count": 0,
        "converted_count": 0,
        "budget": data.budget,
        "spent": 0,
        "created_by": "",
        "created_at": now_iso(),
        "updated_at": now_iso()
    }
    
    await db['marketing_campaigns'].insert_one(campaign)
    
    return {
        "message": "Campaign created successfully",
        "campaign": campaign
    }

@router.get("/campaigns")
async def list_campaigns(status: Optional[str] = None):
    """List all marketing campaigns"""
    db = get_db()
    
    filter_query = {}
    if status:
        filter_query["status"] = status
    
    campaigns = await db['marketing_campaigns'].find(
        filter_query,
        {"_id": 0}
    ).sort("created_at", -1).to_list(None)
    
    return {
        "campaigns": campaigns,
        "total": len(campaigns)
    }

@router.get("/campaign/{campaign_id}")
async def get_campaign(campaign_id: str):
    """Get campaign details"""
    db = get_db()
    
    campaign = await db['marketing_campaigns'].find_one(
        {"id": campaign_id},
        {"_id": 0}
    )
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    return campaign

@router.post("/campaign/{campaign_id}/start")
async def start_campaign(campaign_id: str):
    """Start a campaign"""
    db = get_db()
    
    campaign = await db['marketing_campaigns'].find_one({"id": campaign_id}, {"_id": 0})
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if campaign["status"] == "running":
        raise HTTPException(status_code=400, detail="Campaign already running")
    
    # Get target customers
    filter_query = {}
    if campaign.get("target_segments"):
        filter_query["segment"] = {"$in": campaign["target_segments"]}
    if campaign.get("target_activity"):
        filter_query["activity_status"] = {"$in": campaign["target_activity"]}
    
    customers = await db['customers'].find(filter_query, {"_id": 0, "id": 1, "phone": 1, "whatsapp": 1, "name": 1}).to_list(None)
    
    # Update campaign
    await db['marketing_campaigns'].update_one(
        {"id": campaign_id},
        {"$set": {
            "status": "running",
            "started_at": now_iso(),
            "total_targets": len(customers),
            "target_customer_ids": [c["id"] for c in customers],
            "updated_at": now_iso()
        }}
    )
    
    # In production: Send actual messages via WhatsApp API
    # For now, log the broadcast
    sent_count = 0
    for customer in customers:
        # Create broadcast log
        broadcast_log = {
            "id": gen_id(),
            "campaign_id": campaign_id,
            "customer_id": customer["id"],
            "customer_name": customer.get("name", ""),
            "customer_phone": customer.get("phone", ""),
            "message": campaign["message_template"],
            "channel": campaign["channels"][0] if campaign["channels"] else "internal_chat",
            "status": "sent",  # In production: track actual delivery
            "sent_at": now_iso()
        }
        await db['broadcast_logs'].insert_one(broadcast_log)
        sent_count += 1
    
    # Update sent count
    await db['marketing_campaigns'].update_one(
        {"id": campaign_id},
        {"$set": {"sent_count": sent_count, "delivered_count": sent_count}}
    )
    
    return {
        "message": f"Campaign started. Sent to {sent_count} customers.",
        "sent_count": sent_count
    }

@router.post("/campaign/{campaign_id}/stop")
async def stop_campaign(campaign_id: str):
    """Stop a running campaign"""
    db = get_db()
    
    result = await db['marketing_campaigns'].update_one(
        {"id": campaign_id},
        {"$set": {
            "status": "completed",
            "completed_at": now_iso(),
            "updated_at": now_iso()
        }}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    return {"message": "Campaign stopped"}

@router.post("/broadcast")
async def send_broadcast(data: BroadcastMessageRequest):
    """Send a quick broadcast message"""
    db = get_db()
    
    # Get target customers
    filter_query = {"opt_in_marketing": True}
    if data.target_segment != "all":
        filter_query["segment"] = data.target_segment
    if data.target_activity != "all":
        filter_query["activity_status"] = data.target_activity
    
    customers = await db['customers'].find(filter_query, {"_id": 0, "id": 1, "phone": 1, "name": 1}).to_list(None)
    
    sent_count = 0
    for customer in customers:
        broadcast_log = {
            "id": gen_id(),
            "campaign_id": data.campaign_id,
            "customer_id": customer["id"],
            "customer_name": customer.get("name", ""),
            "customer_phone": customer.get("phone", ""),
            "message": data.message,
            "channel": data.channel,
            "status": "sent",
            "sent_at": now_iso()
        }
        await db['broadcast_logs'].insert_one(broadcast_log)
        sent_count += 1
    
    return {
        "message": f"Broadcast sent to {sent_count} customers",
        "sent_count": sent_count
    }

@router.get("/broadcast/logs")
async def get_broadcast_logs(campaign_id: Optional[str] = None, limit: int = 100):
    """Get broadcast logs"""
    db = get_db()
    
    filter_query = {}
    if campaign_id:
        filter_query["campaign_id"] = campaign_id
    
    logs = await db['broadcast_logs'].find(
        filter_query,
        {"_id": 0}
    ).sort("sent_at", -1).limit(limit).to_list(None)
    
    return {"logs": logs, "total": len(logs)}

@router.get("/customers/recommendations")
async def get_customer_recommendations():
    """Get AI recommendations for customer engagement"""
    db = get_db()
    
    recommendations = []
    
    # Get customer stats
    segments = await get_customer_segments()
    
    # Dormant customers
    dormant_count = segments["by_activity"].get("dormant", {}).get("count", 0)
    if dormant_count > 0:
        recommendations.append({
            "type": "reactivation",
            "priority": "high",
            "title": f"{dormant_count} Pelanggan Dormant",
            "description": "Pelanggan yang tidak bertransaksi > 90 hari.",
            "action": "Kirim promo reactivation dengan diskon khusus.",
            "target_count": dormant_count
        })
    
    # Passive customers
    passive_count = segments["by_activity"].get("passive", {}).get("count", 0)
    if passive_count > 0:
        recommendations.append({
            "type": "engagement",
            "priority": "medium",
            "title": f"{passive_count} Pelanggan Passive",
            "description": "Pelanggan yang tidak bertransaksi 30-90 hari.",
            "action": "Kirim reminder produk favorit atau promo.",
            "target_count": passive_count
        })
    
    # VIP appreciation
    vip_count = segments["by_segment"].get("vip", {}).get("count", 0)
    if vip_count > 0:
        recommendations.append({
            "type": "loyalty",
            "priority": "medium",
            "title": f"{vip_count} Pelanggan VIP",
            "description": "Pelanggan dengan nilai tinggi.",
            "action": "Kirim exclusive offer atau early access promo.",
            "target_count": vip_count
        })
    
    # New customers
    new_count = segments["by_activity"].get("new", {}).get("count", 0)
    if new_count > 0:
        recommendations.append({
            "type": "onboarding",
            "priority": "medium",
            "title": f"{new_count} Pelanggan Baru",
            "description": "Pelanggan yang baru bergabung.",
            "action": "Kirim welcome message dan pengenalan produk unggulan.",
            "target_count": new_count
        })
    
    return {
        "recommendations": recommendations,
        "total_recommendations": len(recommendations)
    }

@router.get("/analytics")
async def get_marketing_analytics():
    """Get marketing campaign analytics"""
    db = get_db()
    
    # Get all campaigns
    campaigns = await db['marketing_campaigns'].find({}, {"_id": 0}).to_list(None)
    
    # Calculate totals
    total_sent = sum(c.get("sent_count", 0) for c in campaigns)
    total_delivered = sum(c.get("delivered_count", 0) for c in campaigns)
    total_read = sum(c.get("read_count", 0) for c in campaigns)
    total_clicked = sum(c.get("clicked_count", 0) for c in campaigns)
    total_converted = sum(c.get("converted_count", 0) for c in campaigns)
    total_budget = sum(c.get("budget", 0) for c in campaigns)
    total_spent = sum(c.get("spent", 0) for c in campaigns)
    
    # Calculate rates
    delivery_rate = (total_delivered / total_sent * 100) if total_sent > 0 else 0
    read_rate = (total_read / total_delivered * 100) if total_delivered > 0 else 0
    click_rate = (total_clicked / total_read * 100) if total_read > 0 else 0
    conversion_rate = (total_converted / total_clicked * 100) if total_clicked > 0 else 0
    
    return {
        "total_campaigns": len(campaigns),
        "active_campaigns": len([c for c in campaigns if c.get("status") == "running"]),
        "completed_campaigns": len([c for c in campaigns if c.get("status") == "completed"]),
        
        "total_messages_sent": total_sent,
        "total_delivered": total_delivered,
        "total_read": total_read,
        "total_clicked": total_clicked,
        "total_converted": total_converted,
        
        "delivery_rate": round(delivery_rate, 2),
        "read_rate": round(read_rate, 2),
        "click_rate": round(click_rate, 2),
        "conversion_rate": round(conversion_rate, 2),
        
        "total_budget": total_budget,
        "total_spent": total_spent,
        "roi": ((total_converted * 100000 - total_spent) / total_spent * 100) if total_spent > 0 else 0  # Assume 100k per conversion
    }
