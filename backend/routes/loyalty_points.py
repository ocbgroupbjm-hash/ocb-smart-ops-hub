# Customer Loyalty Points System
# OCB AI TITAN - Retail Points Engine

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from database import db
from utils.auth import get_current_user
from datetime import datetime, timezone
import uuid

router = APIRouter(prefix="/loyalty", tags=["Customer Loyalty Points"])

customer_points = db["customer_points"]
point_transactions = db["point_transactions"]
point_rules = db["point_rules"]

# ==================== PYDANTIC MODELS ====================

class PointRuleCreate(BaseModel):
    name: str
    rule_type: str = "earn"  # earn, redeem
    # Earn rules
    points_per_amount: float = 0  # Rp per point (e.g., 10000 = 1 point)
    min_transaction: float = 0  # Min transaction untuk dapat point
    multiplier: float = 1  # Point multiplier
    # Redeem rules
    point_value: float = 0  # Nilai Rp per point saat redeem (e.g., 100 point = 10000)
    min_redeem: int = 0  # Min point untuk redeem
    max_redeem_percent: float = 100  # Max % dari total transaksi
    is_active: bool = True
    description: str = ""

class PointTransactionCreate(BaseModel):
    customer_id: str
    transaction_type: str  # earn, redeem, adjustment, expired
    points: int
    reference_type: str = ""  # invoice, manual, promo
    reference_id: str = ""
    description: str = ""

class PointRedeemRequest(BaseModel):
    customer_id: str
    points_to_redeem: int
    invoice_id: str = ""

# ==================== POINT RULES ====================

@router.get("/rules")
async def list_point_rules(user: dict = Depends(get_current_user)):
    """Get all point rules"""
    result = await point_rules.find({}, {"_id": 0}).sort("rule_type", 1).to_list(100)
    
    # Return defaults if empty
    if not result:
        return [
            {
                "id": "default-earn",
                "name": "Default Earn Rule",
                "rule_type": "earn",
                "points_per_amount": 10000,  # Rp 10.000 = 1 point
                "min_transaction": 50000,
                "multiplier": 1,
                "is_active": True,
                "is_default": True
            },
            {
                "id": "default-redeem",
                "name": "Default Redeem Rule",
                "rule_type": "redeem",
                "point_value": 100,  # 100 point = Rp 10.000
                "min_redeem": 100,
                "max_redeem_percent": 50,
                "is_active": True,
                "is_default": True
            }
        ]
    return result

@router.post("/rules")
async def create_point_rule(data: PointRuleCreate, user: dict = Depends(get_current_user)):
    """Create new point rule"""
    rule = {
        "id": str(uuid.uuid4()),
        **data.model_dump(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user.get("id")
    }
    await point_rules.insert_one(rule)
    return {"id": rule["id"], "message": "Rule berhasil ditambahkan"}

@router.put("/rules/{rule_id}")
async def update_point_rule(rule_id: str, data: PointRuleCreate, user: dict = Depends(get_current_user)):
    """Update point rule"""
    update_data = data.model_dump()
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await point_rules.update_one({"id": rule_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Rule tidak ditemukan")
    return {"message": "Rule berhasil diupdate"}

@router.delete("/rules/{rule_id}")
async def delete_point_rule(rule_id: str, user: dict = Depends(get_current_user)):
    """Delete point rule"""
    result = await point_rules.delete_one({"id": rule_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Rule tidak ditemukan")
    return {"message": "Rule berhasil dihapus"}

# ==================== CUSTOMER POINTS ====================

@router.get("/customers")
async def list_customer_points(search: str = "", user: dict = Depends(get_current_user)):
    """Get all customers with their points"""
    pipeline = [
        {"$lookup": {
            "from": "customers",
            "localField": "customer_id",
            "foreignField": "id",
            "as": "customer"
        }},
        {"$unwind": {"path": "$customer", "preserveNullAndEmptyArrays": True}},
        {"$project": {
            "_id": 0,
            "id": 1,
            "customer_id": 1,
            "customer_code": "$customer.code",
            "customer_name": "$customer.name",
            "customer_phone": "$customer.phone",
            "current_points": 1,
            "total_earned": 1,
            "total_redeemed": 1,
            "last_earn_date": 1,
            "last_redeem_date": 1
        }}
    ]
    
    if search:
        pipeline.insert(0, {"$lookup": {
            "from": "customers",
            "localField": "customer_id",
            "foreignField": "id",
            "as": "cust_search"
        }})
        pipeline.insert(1, {"$unwind": {"path": "$cust_search", "preserveNullAndEmptyArrays": True}})
        pipeline.insert(2, {"$match": {"$or": [
            {"cust_search.name": {"$regex": search, "$options": "i"}},
            {"cust_search.code": {"$regex": search, "$options": "i"}}
        ]}})
    
    result = await customer_points.aggregate(pipeline).to_list(500)
    return result

@router.get("/customers/{customer_id}")
async def get_customer_points(customer_id: str, user: dict = Depends(get_current_user)):
    """Get specific customer points and history"""
    # Get customer point balance
    point_record = await customer_points.find_one({"customer_id": customer_id}, {"_id": 0})
    
    if not point_record:
        # Initialize if not exists
        point_record = {
            "id": str(uuid.uuid4()),
            "customer_id": customer_id,
            "current_points": 0,
            "total_earned": 0,
            "total_redeemed": 0,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await customer_points.insert_one(point_record)
        point_record.pop("_id", None)
    
    # Get customer info
    customer = await db["customers"].find_one({"id": customer_id}, {"_id": 0, "name": 1, "code": 1, "phone": 1})
    
    # Get recent transactions
    transactions = await point_transactions.find(
        {"customer_id": customer_id}, 
        {"_id": 0}
    ).sort("created_at", -1).limit(20).to_list(20)
    
    return {
        **point_record,
        "customer": customer,
        "recent_transactions": transactions
    }

# ==================== POINT TRANSACTIONS ====================

@router.post("/earn")
async def earn_points(
    customer_id: str,
    transaction_amount: float,
    invoice_id: str = "",
    user: dict = Depends(get_current_user)
):
    """
    Calculate and award points for a transaction.
    Called after successful sales invoice/POS.
    """
    # Get active earn rule
    earn_rule = await point_rules.find_one({"rule_type": "earn", "is_active": True}, {"_id": 0})
    
    if not earn_rule:
        # Use default
        earn_rule = {
            "points_per_amount": 10000,
            "min_transaction": 50000,
            "multiplier": 1
        }
    
    # Check minimum transaction
    if transaction_amount < earn_rule.get("min_transaction", 0):
        return {"points_earned": 0, "message": "Transaksi di bawah minimum untuk dapat point"}
    
    # Calculate points
    points_per_amount = earn_rule.get("points_per_amount", 10000)
    multiplier = earn_rule.get("multiplier", 1)
    
    if points_per_amount <= 0:
        return {"points_earned": 0, "message": "Point rule tidak valid"}
    
    points_earned = int((transaction_amount / points_per_amount) * multiplier)
    
    if points_earned <= 0:
        return {"points_earned": 0, "message": "Transaksi belum cukup untuk dapat point"}
    
    # Get or create customer point record
    point_record = await customer_points.find_one({"customer_id": customer_id})
    
    if not point_record:
        point_record = {
            "id": str(uuid.uuid4()),
            "customer_id": customer_id,
            "current_points": 0,
            "total_earned": 0,
            "total_redeemed": 0,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await customer_points.insert_one(point_record)
    
    # Update points
    await customer_points.update_one(
        {"customer_id": customer_id},
        {
            "$inc": {
                "current_points": points_earned,
                "total_earned": points_earned
            },
            "$set": {
                "last_earn_date": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    # Record transaction
    trans = {
        "id": str(uuid.uuid4()),
        "customer_id": customer_id,
        "transaction_type": "earn",
        "points": points_earned,
        "reference_type": "invoice",
        "reference_id": invoice_id,
        "transaction_amount": transaction_amount,
        "description": f"Earn {points_earned} points dari transaksi Rp {transaction_amount:,.0f}",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user.get("id")
    }
    await point_transactions.insert_one(trans)
    
    return {
        "points_earned": points_earned,
        "new_balance": (point_record.get("current_points", 0) + points_earned),
        "message": f"Berhasil mendapatkan {points_earned} points"
    }

@router.post("/redeem")
async def redeem_points(data: PointRedeemRequest, user: dict = Depends(get_current_user)):
    """
    Redeem points for discount.
    Returns discount amount to apply to transaction.
    """
    # Get customer point balance
    point_record = await customer_points.find_one({"customer_id": data.customer_id}, {"_id": 0})
    
    if not point_record:
        raise HTTPException(status_code=404, detail="Customer belum memiliki point")
    
    current_points = point_record.get("current_points", 0)
    
    if current_points < data.points_to_redeem:
        raise HTTPException(status_code=400, detail=f"Point tidak cukup. Saldo: {current_points}")
    
    # Get redeem rule
    redeem_rule = await point_rules.find_one({"rule_type": "redeem", "is_active": True}, {"_id": 0})
    
    if not redeem_rule:
        # Use default: 100 point = Rp 10.000
        redeem_rule = {
            "point_value": 100,  # 100 point = 10000
            "min_redeem": 100
        }
    
    min_redeem = redeem_rule.get("min_redeem", 100)
    if data.points_to_redeem < min_redeem:
        raise HTTPException(status_code=400, detail=f"Minimal redeem {min_redeem} points")
    
    # Calculate discount value
    point_value = redeem_rule.get("point_value", 100)
    discount_amount = (data.points_to_redeem / point_value) * 10000  # Base: 100 point = 10000
    
    # Deduct points
    await customer_points.update_one(
        {"customer_id": data.customer_id},
        {
            "$inc": {
                "current_points": -data.points_to_redeem,
                "total_redeemed": data.points_to_redeem
            },
            "$set": {
                "last_redeem_date": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    # Record transaction
    trans = {
        "id": str(uuid.uuid4()),
        "customer_id": data.customer_id,
        "transaction_type": "redeem",
        "points": -data.points_to_redeem,
        "reference_type": "invoice",
        "reference_id": data.invoice_id,
        "discount_amount": discount_amount,
        "description": f"Redeem {data.points_to_redeem} points untuk diskon Rp {discount_amount:,.0f}",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user.get("id")
    }
    await point_transactions.insert_one(trans)
    
    return {
        "points_redeemed": data.points_to_redeem,
        "discount_amount": discount_amount,
        "new_balance": current_points - data.points_to_redeem,
        "message": f"Berhasil redeem {data.points_to_redeem} points"
    }

@router.post("/adjust")
async def adjust_points(data: PointTransactionCreate, user: dict = Depends(get_current_user)):
    """Manual point adjustment (admin only)"""
    # Get or create customer point record
    point_record = await customer_points.find_one({"customer_id": data.customer_id})
    
    if not point_record:
        point_record = {
            "id": str(uuid.uuid4()),
            "customer_id": data.customer_id,
            "current_points": 0,
            "total_earned": 0,
            "total_redeemed": 0,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await customer_points.insert_one(point_record)
    
    # Update points
    update_fields = {"$inc": {"current_points": data.points}}
    if data.points > 0:
        update_fields["$inc"]["total_earned"] = data.points
    else:
        update_fields["$inc"]["total_redeemed"] = abs(data.points)
    
    await customer_points.update_one({"customer_id": data.customer_id}, update_fields)
    
    # Record transaction
    trans = {
        "id": str(uuid.uuid4()),
        **data.model_dump(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user.get("id")
    }
    await point_transactions.insert_one(trans)
    
    return {
        "message": f"Point adjustment: {data.points}",
        "new_balance": point_record.get("current_points", 0) + data.points
    }

@router.get("/transactions/{customer_id}")
async def get_point_transactions(
    customer_id: str, 
    limit: int = 50,
    user: dict = Depends(get_current_user)
):
    """Get point transaction history for a customer"""
    result = await point_transactions.find(
        {"customer_id": customer_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    return result
