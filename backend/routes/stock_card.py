# OCB TITAN AI - Kartu Stok (Stock Card)
# Classic ERP-style stock movement card with running balance

from fastapi import APIRouter, HTTPException, Depends, Query
from datetime import datetime, timezone
from typing import Optional
import uuid

router = APIRouter(prefix="/api/inventory", tags=["Stock Card"])

def get_db():
    from database import get_db as db_get
    return db_get()

from routes.auth import get_current_user


@router.get("/stock-card")
async def get_stock_card(
    item_id: str = Query(..., description="Item ID"),
    branch_id: str = Query("", description="Branch ID (optional, empty for all)"),
    month: int = Query(..., description="Month (1-12)"),
    year: int = Query(..., description="Year"),
    user: dict = Depends(get_current_user)
):
    """
    Get stock card (kartu stok) for an item showing all movements with running balance.
    
    Returns movements sorted by date ASC, transaction_no ASC for accurate running balance.
    """
    db = get_db()
    
    # Verify item exists
    item = await db["products"].find_one({"id": item_id}, {"_id": 0, "code": 1, "name": 1})
    if not item:
        raise HTTPException(status_code=404, detail="Item tidak ditemukan")
    
    # Build date range for the period
    start_date = f"{year}-{month:02d}-01T00:00:00"
    if month == 12:
        end_date = f"{year + 1}-01-01T00:00:00"
    else:
        end_date = f"{year}-{month + 1:02d}-01T00:00:00"
    
    # Query for movements in the period
    query = {
        "item_id": item_id,
        "created_at": {"$gte": start_date, "$lt": end_date}
    }
    
    if branch_id:
        query["branch_id"] = branch_id
    
    # Get all movements sorted by date and reference
    movements = await db["stock_movements"].find(
        query,
        {"_id": 0}
    ).sort([("created_at", 1), ("reference_id", 1)]).to_list(1000)
    
    # Calculate opening balance (saldo awal) - sum of all movements before this period
    opening_query = {
        "item_id": item_id,
        "created_at": {"$lt": start_date}
    }
    if branch_id:
        opening_query["branch_id"] = branch_id
    
    opening_movements = await db["stock_movements"].find(
        opening_query,
        {"_id": 0, "quantity": 1}
    ).to_list(10000)
    
    opening_balance = sum(m.get("quantity", 0) for m in opening_movements)
    
    # Get branch names
    branches_cursor = await db["branches"].find({}, {"_id": 0, "id": 1, "name": 1}).to_list(500)
    branch_map = {b["id"]: b["name"] for b in branches_cursor}
    
    # Build stock card with running balance
    stock_card = []
    running_balance = opening_balance
    
    # Add opening balance row
    stock_card.append({
        "no_transaksi": "-",
        "cabang": "Semua Cabang" if not branch_id else branch_map.get(branch_id, "-"),
        "tanggal": f"{year}-{month:02d}-01",
        "tipe": "Saldo Awal",
        "baris": "-",
        "keterangan": f"Saldo Awal Periode {month:02d}/{year}",
        "masuk": 0,
        "keluar": 0,
        "saldo": running_balance,
        "supplier_pelanggan": "-"
    })
    
    # Transaction type mapping
    type_labels = {
        "purchase": "Pembelian",
        "sale": "Penjualan",
        "stock_in": "Stok Masuk",
        "stock_out": "Stok Keluar",
        "transfer_in": "Transfer Masuk",
        "transfer_out": "Transfer Keluar",
        "opname": "Stok Opname",
        "retur_sale": "Retur Penjualan",
        "retur_purchase": "Retur Pembelian",
        "assembly": "Rakitan Produk",
        "receive": "Penerimaan Barang"
    }
    
    # Process each movement
    for idx, mov in enumerate(movements, 1):
        qty = mov.get("quantity", 0)
        masuk = qty if qty > 0 else 0
        keluar = abs(qty) if qty < 0 else 0
        running_balance += qty
        
        # Format date
        created_at = mov.get("created_at", "")
        if created_at:
            try:
                dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                tanggal = dt.strftime("%Y-%m-%d %H:%M")
            except:
                tanggal = created_at[:16]
        else:
            tanggal = "-"
        
        stock_card.append({
            "no_transaksi": mov.get("reference_id", "-") or f"TRX-{idx:04d}",
            "cabang": branch_map.get(mov.get("branch_id", ""), "-"),
            "tanggal": tanggal,
            "tipe": type_labels.get(mov.get("transaction_type", ""), mov.get("transaction_type", "-")),
            "baris": str(idx),
            "keterangan": mov.get("notes", "-") or "-",
            "masuk": masuk,
            "keluar": keluar,
            "saldo": running_balance,
            "supplier_pelanggan": mov.get("supplier_name", "") or mov.get("customer_name", "") or "-"
        })
    
    # Calculate totals
    total_masuk = sum(row["masuk"] for row in stock_card[1:])  # Skip opening balance
    total_keluar = sum(row["keluar"] for row in stock_card[1:])
    
    return {
        "item": item,
        "period": f"{month:02d}/{year}",
        "branch_id": branch_id,
        "branch_name": branch_map.get(branch_id, "Semua Cabang") if branch_id else "Semua Cabang",
        "opening_balance": opening_balance,
        "closing_balance": running_balance,
        "total_masuk": total_masuk,
        "total_keluar": total_keluar,
        "movements": stock_card,
        "count": len(stock_card)
    }


@router.get("/stock-card/items-search")
async def search_items_for_stock_card(
    q: str = Query("", description="Search query"),
    user: dict = Depends(get_current_user)
):
    """Search items for stock card selection"""
    db = get_db()
    
    query = {}
    if q:
        query["$or"] = [
            {"code": {"$regex": q, "$options": "i"}},
            {"name": {"$regex": q, "$options": "i"}},
            {"barcode": {"$regex": q, "$options": "i"}}
        ]
    
    items = await db["products"].find(
        query,
        {"_id": 0, "id": 1, "code": 1, "name": 1, "barcode": 1}
    ).limit(20).to_list(20)
    
    return {"items": items}


@router.post("/stock-card/create-test-data")
async def create_test_stock_movements(
    item_id: str,
    branch_id: str,
    user: dict = Depends(get_current_user)
):
    """Create test stock movements for testing stock card"""
    db = get_db()
    
    # Verify item exists
    item = await db["products"].find_one({"id": item_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Item tidak ditemukan")
    
    # Get branch name
    branch = await db["branches"].find_one({"id": branch_id}, {"_id": 0, "name": 1})
    branch_name = branch.get("name", "") if branch else ""
    
    # Current date
    now = datetime.now(timezone.utc)
    base_date = now.replace(day=1)
    
    # Create test movements
    test_movements = [
        {
            "id": str(uuid.uuid4()),
            "item_id": item_id,
            "branch_id": branch_id,
            "transaction_type": "purchase",
            "quantity": 50,
            "stock_before": 0,
            "stock_after": 50,
            "reference_id": "PO-TEST-001",
            "notes": "Pembelian awal bulan",
            "supplier_name": "PT Supplier Test",
            "created_at": base_date.replace(day=2).isoformat(),
            "created_by": user.get("id")
        },
        {
            "id": str(uuid.uuid4()),
            "item_id": item_id,
            "branch_id": branch_id,
            "transaction_type": "sale",
            "quantity": -10,
            "stock_before": 50,
            "stock_after": 40,
            "reference_id": "SO-TEST-001",
            "notes": "Penjualan ke customer",
            "customer_name": "Toko ABC",
            "created_at": base_date.replace(day=5).isoformat(),
            "created_by": user.get("id")
        },
        {
            "id": str(uuid.uuid4()),
            "item_id": item_id,
            "branch_id": branch_id,
            "transaction_type": "transfer_out",
            "quantity": -5,
            "stock_before": 40,
            "stock_after": 35,
            "reference_id": "TRF-TEST-001",
            "notes": "Transfer ke cabang lain",
            "created_at": base_date.replace(day=10).isoformat(),
            "created_by": user.get("id")
        },
        {
            "id": str(uuid.uuid4()),
            "item_id": item_id,
            "branch_id": branch_id,
            "transaction_type": "stock_in",
            "quantity": 20,
            "stock_before": 35,
            "stock_after": 55,
            "reference_id": "SI-TEST-001",
            "notes": "Stok masuk tambahan",
            "created_at": base_date.replace(day=15).isoformat(),
            "created_by": user.get("id")
        },
        {
            "id": str(uuid.uuid4()),
            "item_id": item_id,
            "branch_id": branch_id,
            "transaction_type": "sale",
            "quantity": -8,
            "stock_before": 55,
            "stock_after": 47,
            "reference_id": "SO-TEST-002",
            "notes": "Penjualan kedua",
            "customer_name": "Toko XYZ",
            "created_at": base_date.replace(day=18).isoformat(),
            "created_by": user.get("id")
        },
        {
            "id": str(uuid.uuid4()),
            "item_id": item_id,
            "branch_id": branch_id,
            "transaction_type": "retur_sale",
            "quantity": 3,
            "stock_before": 47,
            "stock_after": 50,
            "reference_id": "RT-TEST-001",
            "notes": "Retur dari Toko XYZ",
            "customer_name": "Toko XYZ",
            "created_at": base_date.replace(day=20).isoformat(),
            "created_by": user.get("id")
        }
    ]
    
    # Insert movements
    await db["stock_movements"].insert_many(test_movements)
    
    # Update branch stock
    await db["item_branch_stock"].update_one(
        {"item_id": item_id, "branch_id": branch_id},
        {"$set": {"stock_current": 50, "updated_at": now.isoformat()}},
        upsert=True
    )
    
    return {
        "message": "Test data created successfully",
        "movements_created": len(test_movements),
        "final_stock": 50
    }
