"""
OCB TITAN ERP - IDEMPOTENCY PROTECTION SYSTEM
MASTER BLUEPRINT: Enterprise Hardening Phase - Guard System 4

Mencegah duplicate transactions dari API retries.

Header: Idempotency-Key
Table: idempotency_keys

Flow:
1. Request masuk dengan Idempotency-Key header
2. Cek apakah key sudah pernah digunakan
3. Jika sudah → return response sebelumnya
4. Jika belum → process request, simpan response
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Response
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any, Callable
from datetime import datetime, timezone, timedelta
from database import get_db
from utils.auth import get_current_user
import uuid
import json
import hashlib
import functools

router = APIRouter(prefix="/idempotency", tags=["Idempotency Protection"])

# Configuration
IDEMPOTENCY_KEY_HEADER = "Idempotency-Key"
KEY_TTL_HOURS = 24  # Keys expire after 24 hours
PROTECTED_ENDPOINTS = [
    "/api/sales",
    "/api/pos",
    "/api/purchase",
    "/api/journal",
    "/api/payment",
    "/api/transfer",
    "/api/adjustment"
]


class IdempotencyStore:
    """Manages idempotency keys in MongoDB"""
    
    def __init__(self, db):
        self.db = db
        self.collection = db["idempotency_keys"]
    
    async def get_key(self, key: str) -> Optional[Dict]:
        """Get existing idempotency key record"""
        record = await self.collection.find_one(
            {"key": key},
            {"_id": 0}
        )
        return record
    
    async def store_key(
        self,
        key: str,
        endpoint: str,
        request_hash: str,
        response_code: int,
        response_body: Dict,
        user_id: str
    ) -> Dict:
        """Store new idempotency key with response"""
        record = {
            "id": str(uuid.uuid4()),
            "key": key,
            "endpoint": endpoint,
            "request_hash": request_hash,
            "response_code": response_code,
            "response_body": response_body,
            "user_id": user_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=KEY_TTL_HOURS)).isoformat()
        }
        
        await self.collection.insert_one(record)
        return record
    
    async def cleanup_expired(self) -> int:
        """Remove expired keys"""
        now = datetime.now(timezone.utc).isoformat()
        result = await self.collection.delete_many({
            "expires_at": {"$lt": now}
        })
        return result.deleted_count


def compute_request_hash(endpoint: str, body: Dict) -> str:
    """Compute hash of request for matching"""
    content = json.dumps({
        "endpoint": endpoint,
        "body": body
    }, sort_keys=True, default=str)
    return hashlib.sha256(content.encode()).hexdigest()


async def check_idempotency(
    request: Request,
    endpoint: str,
    body: Dict,
    user_id: str
) -> Optional[JSONResponse]:
    """
    Check if request is duplicate based on Idempotency-Key.
    Returns cached response if duplicate, None if new request.
    """
    idempotency_key = request.headers.get(IDEMPOTENCY_KEY_HEADER)
    
    if not idempotency_key:
        return None  # No idempotency key, proceed normally
    
    db = get_db()
    store = IdempotencyStore(db)
    
    # Check for existing key
    existing = await store.get_key(idempotency_key)
    
    if existing:
        # Check if request matches
        request_hash = compute_request_hash(endpoint, body)
        
        if existing.get("request_hash") == request_hash:
            # Same request, return cached response
            return JSONResponse(
                status_code=existing.get("response_code", 200),
                content=existing.get("response_body", {}),
                headers={"X-Idempotent-Replayed": "true"}
            )
        else:
            # Different request with same key - error
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "IDEMPOTENCY_KEY_MISMATCH",
                    "message": f"Idempotency key '{idempotency_key}' sudah digunakan untuk request berbeda",
                    "original_endpoint": existing.get("endpoint")
                }
            )
    
    return None


async def save_idempotent_response(
    request: Request,
    endpoint: str,
    body: Dict,
    response_code: int,
    response_body: Dict,
    user_id: str
):
    """Save response for idempotency key"""
    idempotency_key = request.headers.get(IDEMPOTENCY_KEY_HEADER)
    
    if not idempotency_key:
        return
    
    db = get_db()
    store = IdempotencyStore(db)
    request_hash = compute_request_hash(endpoint, body)
    
    await store.store_key(
        key=idempotency_key,
        endpoint=endpoint,
        request_hash=request_hash,
        response_code=response_code,
        response_body=response_body,
        user_id=user_id
    )


# ==================== API ENDPOINTS ====================

@router.get("/keys")
async def list_idempotency_keys(
    limit: int = 100,
    user: dict = Depends(get_current_user)
):
    """List recent idempotency keys (admin only)"""
    user_role = (user.get("role", "") or user.get("role_code", "")).lower()
    if user_role not in ["owner", "admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="AKSES DITOLAK")
    
    db = get_db()
    keys = await db["idempotency_keys"].find(
        {},
        {"_id": 0, "response_body": 0}  # Exclude large response body
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    return {
        "keys": keys,
        "total": len(keys)
    }


@router.get("/keys/{key}")
async def get_idempotency_key(
    key: str,
    user: dict = Depends(get_current_user)
):
    """Get specific idempotency key details"""
    db = get_db()
    store = IdempotencyStore(db)
    
    record = await store.get_key(key)
    if not record:
        raise HTTPException(status_code=404, detail="Key tidak ditemukan")
    
    return record


@router.post("/cleanup")
async def cleanup_expired_keys(
    user: dict = Depends(get_current_user)
):
    """Cleanup expired idempotency keys (admin only)"""
    user_role = (user.get("role", "") or user.get("role_code", "")).lower()
    if user_role not in ["owner", "admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="AKSES DITOLAK")
    
    db = get_db()
    store = IdempotencyStore(db)
    
    deleted_count = await store.cleanup_expired()
    
    return {
        "success": True,
        "deleted_count": deleted_count,
        "message": f"Removed {deleted_count} expired keys"
    }


@router.get("/stats")
async def get_idempotency_stats(
    user: dict = Depends(get_current_user)
):
    """Get idempotency statistics"""
    db = get_db()
    
    now = datetime.now(timezone.utc).isoformat()
    
    total = await db["idempotency_keys"].count_documents({})
    active = await db["idempotency_keys"].count_documents({
        "expires_at": {"$gt": now}
    })
    expired = total - active
    
    # Get by endpoint
    pipeline = [
        {"$group": {
            "_id": "$endpoint",
            "count": {"$sum": 1}
        }},
        {"$sort": {"count": -1}}
    ]
    by_endpoint = await db["idempotency_keys"].aggregate(pipeline).to_list(20)
    
    return {
        "total_keys": total,
        "active_keys": active,
        "expired_keys": expired,
        "by_endpoint": by_endpoint,
        "ttl_hours": KEY_TTL_HOURS
    }


@router.post("/test")
async def test_idempotency(
    request: Request,
    test_data: Dict[str, Any] = None,
    user: dict = Depends(get_current_user)
):
    """
    Test endpoint for idempotency
    Send request with Idempotency-Key header to test
    """
    idempotency_key = request.headers.get(IDEMPOTENCY_KEY_HEADER)
    
    if not idempotency_key:
        return {
            "message": "No Idempotency-Key header provided",
            "instruction": "Add 'Idempotency-Key: <unique-key>' header to test"
        }
    
    body = test_data or {"test": True, "timestamp": datetime.now(timezone.utc).isoformat()}
    
    # Check for duplicate
    cached = await check_idempotency(
        request=request,
        endpoint="/api/idempotency/test",
        body=body,
        user_id=user.get("user_id", "")
    )
    
    if cached:
        return cached
    
    # Generate new response
    response_body = {
        "success": True,
        "idempotency_key": idempotency_key,
        "message": "Request baru berhasil diproses",
        "data": body,
        "processed_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Save for future replay
    await save_idempotent_response(
        request=request,
        endpoint="/api/idempotency/test",
        body=body,
        response_code=200,
        response_body=response_body,
        user_id=user.get("user_id", "")
    )
    
    return response_body


# ==================== HELPER FOR OTHER MODULES ====================

async def idempotent_transaction(
    request: Request,
    endpoint: str,
    body: Dict,
    user_id: str,
    transaction_func: Callable
) -> Dict:
    """
    Wrapper for transactional operations with idempotency protection.
    
    Usage:
        result = await idempotent_transaction(
            request=request,
            endpoint="/api/sales",
            body=sale_data,
            user_id=user["user_id"],
            transaction_func=create_sale
        )
    """
    # Check for duplicate
    cached = await check_idempotency(request, endpoint, body, user_id)
    if cached:
        return cached
    
    # Execute transaction
    result = await transaction_func()
    
    # Save response
    await save_idempotent_response(
        request=request,
        endpoint=endpoint,
        body=body,
        response_code=200,
        response_body=result,
        user_id=user_id
    )
    
    return result
