# OCB TITAN - Stock Validation Module
# P0: NO NEGATIVE STOCK + STOCK CHAIN DELETE PROTECTION
#
# ATURAN:
# 1. Stok TIDAK BOLEH minus
# 2. Transaksi stok TIDAK BOLEH dihapus jika sudah ada transaksi setelahnya
# 3. Delete/Reverse HARUS dari transaksi paling belakang dulu

from datetime import datetime, timezone
from typing import Optional, List, Dict, Tuple
from fastapi import HTTPException
import uuid


class StockValidationError(Exception):
    """Custom exception for stock validation errors"""
    def __init__(self, message: str, error_code: str, details: dict = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


# ==================== NO NEGATIVE STOCK VALIDATION ====================

async def validate_stock_available(
    db,
    product_id: str,
    branch_id: str,
    required_qty: float,
    product_name: str = "",
    transaction_type: str = "unknown"
) -> dict:
    """
    Validasi apakah stok mencukupi untuk transaksi keluar.
    
    BLOK transaksi jika saldo tidak mencukupi:
    - sales
    - transfer keluar
    - adjustment minus
    - stock usage
    - reversal yang mengurangi stok
    
    Args:
        db: Database instance
        product_id: ID produk
        branch_id: ID cabang
        required_qty: Jumlah yang dibutuhkan (harus positif)
        product_name: Nama produk untuk pesan error
        transaction_type: Tipe transaksi untuk audit
    
    Returns:
        dict dengan available_stock dan validation result
    
    Raises:
        StockValidationError jika stok tidak mencukupi
    """
    # Get current stock from stock_movements (SSOT)
    pipeline = [
        {"$match": {
            "$or": [
                {"product_id": product_id},
                {"item_id": product_id}
            ],
            "branch_id": branch_id
        }},
        {"$group": {
            "_id": None,
            "total_qty": {"$sum": "$quantity"}
        }}
    ]
    
    result = await db["stock_movements"].aggregate(pipeline).to_list(1)
    available_stock = result[0]["total_qty"] if result else 0
    
    # Validasi
    if required_qty > available_stock:
        raise StockValidationError(
            message=f"Stok tidak mencukupi. Saldo tersedia: {available_stock}, diminta: {required_qty}",
            error_code="INSUFFICIENT_STOCK",
            details={
                "product_id": product_id,
                "product_name": product_name,
                "branch_id": branch_id,
                "available_stock": available_stock,
                "required_qty": required_qty,
                "shortage": required_qty - available_stock,
                "transaction_type": transaction_type
            }
        )
    
    return {
        "valid": True,
        "available_stock": available_stock,
        "required_qty": required_qty,
        "remaining_after": available_stock - required_qty
    }


async def validate_stock_for_items(
    db,
    branch_id: str,
    items: List[dict],
    transaction_type: str = "unknown"
) -> dict:
    """
    Validasi stok untuk multiple items sekaligus.
    
    Args:
        db: Database instance
        branch_id: ID cabang
        items: List of {product_id, product_name, quantity}
        transaction_type: Tipe transaksi
    
    Returns:
        dict dengan validation results
    
    Raises:
        StockValidationError jika ada item dengan stok tidak mencukupi
    """
    errors = []
    valid_items = []
    
    for item in items:
        product_id = item.get("product_id")
        product_name = item.get("product_name", "")
        required_qty = abs(item.get("quantity", 0))  # Ambil nilai absolut
        
        try:
            result = await validate_stock_available(
                db, product_id, branch_id, required_qty,
                product_name, transaction_type
            )
            valid_items.append({
                **item,
                "validation": result
            })
        except StockValidationError as e:
            errors.append({
                "product_id": product_id,
                "product_name": product_name,
                "error": e.message,
                "details": e.details
            })
    
    if errors:
        # Buat pesan error gabungan
        error_messages = []
        for err in errors:
            pname = err.get("product_name") or err.get("product_id")
            details = err.get("details", {})
            error_messages.append(
                f"{pname}: Tersedia {details.get('available_stock', 0)}, diminta {details.get('required_qty', 0)}"
            )
        
        raise StockValidationError(
            message=f"Stok tidak mencukupi untuk {len(errors)} item: " + "; ".join(error_messages),
            error_code="INSUFFICIENT_STOCK_MULTIPLE",
            details={
                "errors": errors,
                "error_count": len(errors),
                "transaction_type": transaction_type
            }
        )
    
    return {
        "valid": True,
        "items_validated": len(valid_items),
        "items": valid_items
    }


# ==================== STOCK CHAIN DEPENDENCY CHECK ====================

async def check_stock_chain_dependency(
    db,
    reference_id: str,
    product_id: str,
    branch_id: str,
    movement_created_at: str = None
) -> dict:
    """
    Cek apakah ada transaksi setelah movement ini yang bergantung padanya.
    
    RULE:
    - Sebelum delete/reverse, cek apakah ada movement setelah transaksi ini
    - Pada product yang sama
    - Pada branch yang sama
    - Yang membuat saldo setelahnya bergantung pada transaksi ini
    
    Args:
        db: Database instance
        reference_id: ID transaksi yang akan di-reverse
        product_id: ID produk
        branch_id: ID cabang
        movement_created_at: Waktu movement (untuk cari yang setelahnya)
    
    Returns:
        dict dengan dependency info
    
    Raises:
        StockValidationError jika ada dependency
    """
    # Cari movement asli jika created_at tidak diberikan
    if not movement_created_at:
        original_movement = await db["stock_movements"].find_one({
            "reference_id": reference_id,
            "$or": [
                {"product_id": product_id},
                {"item_id": product_id}
            ],
            "branch_id": branch_id,
            "is_reversed": {"$ne": True}
        })
        
        if not original_movement:
            return {
                "has_dependency": False,
                "message": "No original movement found",
                "can_reverse": True
            }
        
        movement_created_at = original_movement.get("created_at")
    
    # Cari movements SETELAH transaksi ini
    subsequent_movements = await db["stock_movements"].find({
        "$or": [
            {"product_id": product_id},
            {"item_id": product_id}
        ],
        "branch_id": branch_id,
        "created_at": {"$gt": movement_created_at},
        "is_reversed": {"$ne": True},
        "reference_type": {"$nin": ["reversal", "duplicate_reversal", "purchase_reversal"]}  # Exclude reversals
    }).sort("created_at", 1).to_list(100)
    
    if subsequent_movements:
        # Ada transaksi setelahnya - BLOCK!
        blocking_transactions = []
        for mov in subsequent_movements[:5]:  # Tampilkan 5 pertama
            blocking_transactions.append({
                "reference_id": mov.get("reference_id"),
                "reference_number": mov.get("reference_number", mov.get("reference_no", "-")),
                "reference_type": mov.get("reference_type"),
                "quantity": mov.get("quantity", 0),
                "created_at": str(mov.get("created_at", ""))
            })
        
        raise StockValidationError(
            message=f"Transaksi tidak bisa dihapus/reverse karena sudah ada {len(subsequent_movements)} transaksi setelahnya. Reverse transaksi terbaru terlebih dahulu.",
            error_code="STOCK_CHAIN_DEPENDENCY",
            details={
                "product_id": product_id,
                "branch_id": branch_id,
                "reference_id": reference_id,
                "subsequent_count": len(subsequent_movements),
                "blocking_transactions": blocking_transactions
            }
        )
    
    return {
        "has_dependency": False,
        "message": "No subsequent movements found",
        "can_reverse": True
    }


async def check_reversal_chain_for_transaction(
    db,
    reference_id: str,
    reference_types: List[str]
) -> dict:
    """
    Cek chain dependency untuk SEMUA movements dari transaksi.
    
    Args:
        db: Database instance
        reference_id: ID transaksi
        reference_types: List of reference_type
    
    Returns:
        dict dengan dependency info untuk semua products/branches
    
    Raises:
        StockValidationError jika ada dependency
    """
    # Get all movements for this transaction
    movements = await db["stock_movements"].find({
        "reference_id": reference_id,
        "reference_type": {"$in": reference_types},
        "is_reversed": {"$ne": True}
    }).to_list(1000)
    
    if not movements:
        return {
            "has_dependency": False,
            "message": "No movements to check",
            "can_reverse": True
        }
    
    all_dependencies = []
    
    for mov in movements:
        product_id = mov.get("product_id") or mov.get("item_id")
        branch_id = mov.get("branch_id")
        created_at = mov.get("created_at")
        
        try:
            await check_stock_chain_dependency(
                db, reference_id, product_id, branch_id, 
                str(created_at) if created_at else None
            )
        except StockValidationError as e:
            all_dependencies.append({
                "product_id": product_id,
                "branch_id": branch_id,
                "error": e.message,
                "details": e.details
            })
    
    if all_dependencies:
        raise StockValidationError(
            message=f"Transaksi tidak bisa dihapus/reverse karena ada {len(all_dependencies)} product/branch dengan transaksi setelahnya. Reverse transaksi terbaru terlebih dahulu.",
            error_code="STOCK_CHAIN_DEPENDENCY_MULTIPLE",
            details={
                "reference_id": reference_id,
                "dependencies": all_dependencies,
                "dependency_count": len(all_dependencies)
            }
        )
    
    return {
        "has_dependency": False,
        "message": "All movements can be reversed",
        "can_reverse": True,
        "movements_checked": len(movements)
    }


# ==================== REVERSAL VALIDATION (NO NEGATIVE AFTER REVERSAL) ====================

async def validate_reversal_wont_cause_negative(
    db,
    reference_id: str,
    reference_types: List[str]
) -> dict:
    """
    Validasi bahwa reversal tidak akan menyebabkan stok minus.
    
    RULE: Jika reversal akan mengurangi stok (dari transaksi IN),
    cek apakah stok saat ini cukup untuk dikurangi.
    
    Args:
        db: Database instance
        reference_id: ID transaksi
        reference_types: List of reference_type
    
    Returns:
        dict dengan validation result
    
    Raises:
        StockValidationError jika reversal akan menyebabkan stok minus
    """
    movements = await db["stock_movements"].find({
        "reference_id": reference_id,
        "reference_type": {"$in": reference_types},
        "is_reversed": {"$ne": True}
    }).to_list(1000)
    
    errors = []
    
    for mov in movements:
        original_qty = mov.get("quantity", 0)
        
        # Hanya cek jika reversal akan MENGURANGI stok (original qty positif)
        if original_qty > 0:
            product_id = mov.get("product_id") or mov.get("item_id")
            branch_id = mov.get("branch_id")
            product_name = mov.get("product_name", "")
            
            try:
                await validate_stock_available(
                    db, product_id, branch_id, original_qty,
                    product_name, "reversal_validation"
                )
            except StockValidationError as e:
                errors.append({
                    "product_id": product_id,
                    "product_name": product_name,
                    "branch_id": branch_id,
                    "reversal_qty": -original_qty,
                    "error": e.message,
                    "details": e.details
                })
    
    if errors:
        error_messages = []
        for err in errors:
            pname = err.get("product_name") or err.get("product_id")
            details = err.get("details", {})
            error_messages.append(
                f"{pname}: Saldo {details.get('available_stock', 0)}, akan dikurangi {abs(err.get('reversal_qty', 0))}"
            )
        
        raise StockValidationError(
            message=f"Reversal akan menyebabkan stok minus untuk {len(errors)} item: " + "; ".join(error_messages),
            error_code="REVERSAL_WOULD_CAUSE_NEGATIVE",
            details={
                "errors": errors,
                "error_count": len(errors)
            }
        )
    
    return {
        "valid": True,
        "message": "Reversal will not cause negative stock",
        "movements_checked": len(movements)
    }


# ==================== COMPREHENSIVE REVERSAL VALIDATION ====================

async def validate_can_reverse_transaction(
    db,
    reference_id: str,
    reference_types: List[str]
) -> dict:
    """
    Validasi komprehensif sebelum reversal:
    1. Cek chain dependency
    2. Cek apakah reversal akan menyebabkan stok minus
    
    Args:
        db: Database instance
        reference_id: ID transaksi
        reference_types: List of reference_type
    
    Returns:
        dict dengan validation result
    
    Raises:
        StockValidationError jika validasi gagal
    """
    # Step 1: Check chain dependency
    chain_result = await check_reversal_chain_for_transaction(db, reference_id, reference_types)
    
    # Step 2: Check negative stock
    negative_result = await validate_reversal_wont_cause_negative(db, reference_id, reference_types)
    
    return {
        "valid": True,
        "can_reverse": True,
        "chain_check": chain_result,
        "negative_check": negative_result
    }


# ==================== AUDIT LOGGING ====================

async def log_stock_validation_event(
    db,
    user_id: str,
    user_name: str,
    event_type: str,
    success: bool,
    details: dict,
    ip_address: str = ""
):
    """
    Log semua blocked action dan reversal untuk audit trail.
    """
    event = {
        "id": str(uuid.uuid4()),
        "event_type": f"STOCK_VALIDATION_{event_type}",
        "user_id": user_id,
        "user_name": user_name,
        "success": success,
        "details": details,
        "ip_address": ip_address,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db["stock_validation_logs"].insert_one(event)
    return event
