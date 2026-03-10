# OCB TITAN ERP - SINGLE SOURCE OF TRUTH (SSOT) SERVICE
# Semua modul WAJIB menggunakan service ini untuk akses data
# Tidak boleh ada query langsung ke collection dari modul lain

from fastapi import APIRouter, HTTPException, Depends, Query
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import uuid

router = APIRouter(prefix="/api/ssot", tags=["Single Source of Truth"])

def get_db():
    from database import get_db as db_get
    return db_get()

from routes.auth import get_current_user

# ==================== DEFINISI SUMBER DATA RESMI ====================

"""
SINGLE SOURCE OF TRUTH ARCHITECTURE
====================================

1. ITEMS
   - Source: products collection
   - Used by: Master Data, Persediaan, Penjualan, Pembelian, Laporan, AI
   
2. STOK
   - Source: stock_movements collection
   - Calculated: SUM(quantity) per item per branch
   - NOT stored in: products.stock, item_branch_stock.stock_current
   
3. TRANSAKSI
   - Source: transactions collection
   - Used by: Penjualan, Pembelian, Laporan, Dashboard, AI
   
4. CABANG
   - Source: branches collection
   - Used by: All modules requiring branch data
   
5. KEUANGAN
   - Source: journal_entries collection
   - Used by: Kas Masuk/Keluar, Buku Besar, Laba Rugi, Neraca
"""


# ==================== ITEM SERVICE ====================

class ItemService:
    """Single source for all item data"""
    
    @staticmethod
    async def get_all(
        search: str = "",
        category_id: str = "",
        brand_id: str = "",
        branch_id: str = "",
        item_type: str = "",
        is_active: bool = None,
        skip: int = 0,
        limit: int = 50
    ) -> Dict[str, Any]:
        db = get_db()
        query = {}
        
        if search:
            query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"code": {"$regex": search, "$options": "i"}},
                {"barcode": {"$regex": search, "$options": "i"}}
            ]
        if category_id:
            query["category_id"] = category_id
        if brand_id:
            query["brand_id"] = brand_id
        if branch_id:
            query["branch_id"] = branch_id
        if item_type:
            query["item_type"] = item_type
        if is_active is not None:
            query["is_active"] = is_active
        
        items = await db["products"].find(query, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
        total = await db["products"].count_documents(query)
        
        # Add calculated stock from stock_movements
        for item in items:
            item["stock"] = await StockService.get_item_total_stock(item["id"])
        
        return {"items": items, "total": total}
    
    @staticmethod
    async def get_by_id(item_id: str) -> Optional[Dict]:
        db = get_db()
        item = await db["products"].find_one({"id": item_id}, {"_id": 0})
        if item:
            item["stock"] = await StockService.get_item_total_stock(item_id)
        return item
    
    @staticmethod
    async def create(data: Dict, user_id: str = None) -> Dict:
        db = get_db()
        
        # Check duplicate code
        existing = await db["products"].find_one({"code": data.get("code")})
        if existing:
            raise HTTPException(status_code=400, detail="Kode item sudah ada")
        
        item = {
            "id": str(uuid.uuid4()),
            **data,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": user_id
        }
        # Remove stock from data - stock is calculated from movements
        item.pop("stock", None)
        
        await db["products"].insert_one(item)
        
        # Initialize stock config for all branches (min/max only, NOT stock_current)
        branches = await db["branches"].find({}, {"_id": 0, "id": 1, "name": 1}).to_list(500)
        stock_configs = []
        for branch in branches:
            stock_configs.append({
                "id": str(uuid.uuid4()),
                "item_id": item["id"],
                "branch_id": branch["id"],
                "branch_name": branch.get("name", ""),
                "stock_minimum": 0,
                "stock_maximum": 0,
                "created_at": datetime.now(timezone.utc).isoformat()
            })
        if stock_configs:
            await db["item_branch_stock"].insert_many(stock_configs)
        
        return {"id": item["id"], "message": "Item berhasil ditambahkan"}
    
    @staticmethod
    async def update(item_id: str, data: Dict) -> Dict:
        db = get_db()
        # Remove stock from update - stock is calculated
        data.pop("stock", None)
        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        result = await db["products"].update_one({"id": item_id}, {"$set": data})
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Item tidak ditemukan")
        return {"message": "Item berhasil diupdate"}
    
    @staticmethod
    async def delete(item_id: str) -> Dict:
        db = get_db()
        result = await db["products"].delete_one({"id": item_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Item tidak ditemukan")
        # Also delete stock configs
        await db["item_branch_stock"].delete_many({"item_id": item_id})
        await db["stock_movements"].delete_many({"item_id": item_id})
        return {"message": "Item berhasil dihapus"}


# ==================== STOCK SERVICE ====================

class StockService:
    """
    Single source for all stock data.
    Stock is ALWAYS calculated from stock_movements collection.
    Never stored directly in items or other collections.
    """
    
    @staticmethod
    async def get_item_total_stock(item_id: str, branch_id: str = None) -> int:
        """Calculate total stock from stock_movements"""
        db = get_db()
        
        match = {"item_id": item_id}
        if branch_id:
            match["branch_id"] = branch_id
        
        pipeline = [
            {"$match": match},
            {"$group": {"_id": None, "total": {"$sum": "$quantity"}}}
        ]
        
        result = await db["stock_movements"].aggregate(pipeline).to_list(1)
        return result[0]["total"] if result else 0
    
    @staticmethod
    async def get_branch_stocks(item_id: str) -> List[Dict]:
        """Get stock per branch for an item"""
        db = get_db()
        
        # Get all branches
        branches = await db["branches"].find({}, {"_id": 0, "id": 1, "name": 1}).to_list(500)
        
        # Get stock config (min/max)
        configs = await db["item_branch_stock"].find(
            {"item_id": item_id},
            {"_id": 0}
        ).to_list(500)
        config_map = {c["branch_id"]: c for c in configs}
        
        # Calculate stock per branch from movements
        pipeline = [
            {"$match": {"item_id": item_id}},
            {"$group": {"_id": "$branch_id", "stock_current": {"$sum": "$quantity"}}}
        ]
        stock_results = await db["stock_movements"].aggregate(pipeline).to_list(500)
        stock_map = {s["_id"]: s["stock_current"] for s in stock_results}
        
        result = []
        for branch in branches:
            config = config_map.get(branch["id"], {})
            result.append({
                "branch_id": branch["id"],
                "branch_name": branch.get("name", ""),
                "stock_current": stock_map.get(branch["id"], 0),  # Calculated from movements
                "stock_minimum": config.get("stock_minimum", 0),
                "stock_maximum": config.get("stock_maximum", 0)
            })
        
        return result
    
    @staticmethod
    async def record_movement(
        item_id: str,
        branch_id: str,
        quantity: int,
        transaction_type: str,
        reference_id: str = "",
        notes: str = "",
        supplier_name: str = "",
        customer_name: str = "",
        user_id: str = None
    ) -> Dict:
        """
        Record a stock movement. This is the ONLY way to change stock.
        
        Transaction types:
        - purchase: Pembelian (+)
        - sale: Penjualan (-)
        - stock_in: Stok Masuk (+)
        - stock_out: Stok Keluar (-)
        - transfer_in: Transfer Masuk (+)
        - transfer_out: Transfer Keluar (-)
        - opname: Stok Opname (adjustment)
        - retur_sale: Retur Penjualan (+)
        - retur_purchase: Retur Pembelian (-)
        - assembly: Rakitan Produk (-)
        """
        db = get_db()
        
        # Get current stock before movement
        stock_before = await StockService.get_item_total_stock(item_id, branch_id)
        stock_after = stock_before + quantity
        
        # Validate - prevent negative stock
        if stock_after < 0:
            raise HTTPException(
                status_code=400,
                detail=f"Stok tidak mencukupi. Stok saat ini: {stock_before}, permintaan: {quantity}"
            )
        
        # Create movement record
        movement = {
            "id": str(uuid.uuid4()),
            "item_id": item_id,
            "branch_id": branch_id,
            "transaction_type": transaction_type,
            "quantity": quantity,
            "stock_before": stock_before,
            "stock_after": stock_after,
            "reference_id": reference_id,
            "notes": notes,
            "supplier_name": supplier_name,
            "customer_name": customer_name,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": user_id
        }
        
        await db["stock_movements"].insert_one(movement)
        
        return {
            "id": movement["id"],
            "stock_before": stock_before,
            "stock_after": stock_after,
            "message": "Stok berhasil diupdate"
        }
    
    @staticmethod
    async def get_stock_card(
        item_id: str,
        branch_id: str = "",
        start_date: str = "",
        end_date: str = ""
    ) -> Dict:
        """Get stock card (kartu stok) with running balance"""
        db = get_db()
        
        # Get item info
        item = await db["products"].find_one({"id": item_id}, {"_id": 0, "code": 1, "name": 1})
        if not item:
            raise HTTPException(status_code=404, detail="Item tidak ditemukan")
        
        # Build query
        query = {"item_id": item_id}
        if branch_id:
            query["branch_id"] = branch_id
        
        date_filter = {}
        if start_date:
            date_filter["$gte"] = start_date
        if end_date:
            date_filter["$lt"] = end_date
        if date_filter:
            query["created_at"] = date_filter
        
        # Get movements
        movements = await db["stock_movements"].find(
            query, {"_id": 0}
        ).sort("created_at", 1).to_list(10000)
        
        # Calculate running balance
        running_balance = 0
        stock_card = []
        
        for mov in movements:
            qty = mov.get("quantity", 0)
            running_balance += qty
            
            stock_card.append({
                "id": mov.get("id"),
                "date": mov.get("created_at", "")[:19],
                "type": mov.get("transaction_type", ""),
                "reference": mov.get("reference_id", "-"),
                "notes": mov.get("notes", ""),
                "in": qty if qty > 0 else 0,
                "out": abs(qty) if qty < 0 else 0,
                "balance": running_balance,
                "partner": mov.get("supplier_name") or mov.get("customer_name") or "-"
            })
        
        return {
            "item": item,
            "movements": stock_card,
            "opening_balance": 0,
            "closing_balance": running_balance,
            "total_in": sum(m["in"] for m in stock_card),
            "total_out": sum(m["out"] for m in stock_card)
        }


# ==================== TRANSACTION SERVICE ====================

class TransactionService:
    """Single source for all transaction data"""
    
    @staticmethod
    async def create(
        transaction_type: str,  # sale, purchase, transfer, opname
        branch_id: str,
        items: List[Dict],
        total: float,
        notes: str = "",
        partner_id: str = "",
        partner_name: str = "",
        user_id: str = None
    ) -> Dict:
        db = get_db()
        
        # Generate transaction number
        prefix = {
            "sale": "SO",
            "purchase": "PO",
            "transfer": "TRF",
            "opname": "OPN",
            "stock_in": "SI",
            "stock_out": "SK"
        }.get(transaction_type, "TRX")
        
        count = await db["transactions"].count_documents({"type": transaction_type})
        trans_no = f"{prefix}-{datetime.now().strftime('%Y%m%d')}-{count + 1:04d}"
        
        # Create transaction
        transaction = {
            "id": str(uuid.uuid4()),
            "transaction_no": trans_no,
            "type": transaction_type,
            "branch_id": branch_id,
            "items": items,
            "total": total,
            "notes": notes,
            "partner_id": partner_id,
            "partner_name": partner_name,
            "status": "completed",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": user_id
        }
        
        await db["transactions"].insert_one(transaction)
        
        # Record stock movements for each item
        for item in items:
            # Determine quantity direction
            if transaction_type in ["purchase", "stock_in", "retur_sale", "transfer_in"]:
                qty = item.get("quantity", 0)
            else:  # sale, stock_out, retur_purchase, transfer_out
                qty = -abs(item.get("quantity", 0))
            
            await StockService.record_movement(
                item_id=item.get("item_id"),
                branch_id=branch_id,
                quantity=qty,
                transaction_type=transaction_type,
                reference_id=trans_no,
                notes=notes,
                supplier_name=partner_name if transaction_type == "purchase" else "",
                customer_name=partner_name if transaction_type == "sale" else "",
                user_id=user_id
            )
        
        # Create journal entry
        await JournalService.create_from_transaction(transaction)
        
        return {
            "id": transaction["id"],
            "transaction_no": trans_no,
            "message": f"Transaksi {trans_no} berhasil dibuat"
        }
    
    @staticmethod
    async def get_list(
        transaction_type: str = "",
        branch_id: str = "",
        start_date: str = "",
        end_date: str = "",
        skip: int = 0,
        limit: int = 50
    ) -> Dict:
        db = get_db()
        
        query = {}
        if transaction_type:
            query["type"] = transaction_type
        if branch_id:
            query["branch_id"] = branch_id
        
        date_filter = {}
        if start_date:
            date_filter["$gte"] = start_date
        if end_date:
            date_filter["$lt"] = end_date
        if date_filter:
            query["created_at"] = date_filter
        
        transactions = await db["transactions"].find(
            query, {"_id": 0}
        ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
        
        total = await db["transactions"].count_documents(query)
        
        return {"transactions": transactions, "total": total}


# ==================== JOURNAL SERVICE ====================

class JournalService:
    """Single source for all accounting/journal data"""
    
    @staticmethod
    async def create_from_transaction(transaction: Dict) -> Dict:
        """Auto-create journal entries from transaction"""
        db = get_db()
        
        entries = []
        trans_type = transaction.get("type")
        total = transaction.get("total", 0)
        
        if trans_type == "sale":
            # Debit: Kas/Piutang, Credit: Penjualan
            entries.append({
                "account_code": "1100",  # Kas
                "account_name": "Kas",
                "debit": total,
                "credit": 0
            })
            entries.append({
                "account_code": "4100",  # Penjualan
                "account_name": "Penjualan",
                "debit": 0,
                "credit": total
            })
        elif trans_type == "purchase":
            # Debit: Persediaan, Credit: Kas/Hutang
            entries.append({
                "account_code": "1300",  # Persediaan
                "account_name": "Persediaan",
                "debit": total,
                "credit": 0
            })
            entries.append({
                "account_code": "2100",  # Hutang Dagang
                "account_name": "Hutang Dagang",
                "debit": 0,
                "credit": total
            })
        
        if entries:
            journal = {
                "id": str(uuid.uuid4()),
                "journal_no": f"JV-{transaction.get('transaction_no', '')}",
                "transaction_id": transaction.get("id"),
                "transaction_no": transaction.get("transaction_no"),
                "transaction_type": trans_type,
                "entries": entries,
                "total_debit": sum(e["debit"] for e in entries),
                "total_credit": sum(e["credit"] for e in entries),
                "notes": transaction.get("notes", ""),
                "branch_id": transaction.get("branch_id"),
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db["journal_entries"].insert_one(journal)
            return journal
        
        return {}


# ==================== API ENDPOINTS ====================

@router.get("/items")
async def get_items(
    search: str = "",
    category_id: str = "",
    brand_id: str = "",
    skip: int = 0,
    limit: int = 50,
    user: dict = Depends(get_current_user)
):
    """Get all items with calculated stock"""
    return await ItemService.get_all(search=search, category_id=category_id, brand_id=brand_id, skip=skip, limit=limit)


@router.get("/items/{item_id}")
async def get_item(item_id: str, user: dict = Depends(get_current_user)):
    """Get single item with calculated stock"""
    item = await ItemService.get_by_id(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item tidak ditemukan")
    return item


@router.get("/items/{item_id}/stock")
async def get_item_stock(item_id: str, user: dict = Depends(get_current_user)):
    """Get stock per branch for an item - calculated from movements"""
    stocks = await StockService.get_branch_stocks(item_id)
    total_stock = await StockService.get_item_total_stock(item_id)
    return {
        "item_id": item_id,
        "total_stock": total_stock,
        "branch_stocks": stocks
    }


@router.get("/items/{item_id}/stock-card")
async def get_item_stock_card(
    item_id: str,
    branch_id: str = "",
    start_date: str = "",
    end_date: str = "",
    user: dict = Depends(get_current_user)
):
    """Get stock card for an item"""
    return await StockService.get_stock_card(item_id, branch_id, start_date, end_date)


@router.get("/dashboard/summary")
async def get_dashboard_summary(
    branch_id: str = "",
    user: dict = Depends(get_current_user)
):
    """Get dashboard summary - all data from single sources"""
    db = get_db()
    
    # Items count
    items_count = await db["products"].count_documents({"is_active": {"$ne": False}})
    
    # Total stock (calculated from movements)
    pipeline = [{"$group": {"_id": None, "total": {"$sum": "$quantity"}}}]
    stock_result = await db["stock_movements"].aggregate(pipeline).to_list(1)
    total_stock = stock_result[0]["total"] if stock_result else 0
    
    # Today's transactions
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    sales_query = {"type": "sale", "created_at": {"$regex": f"^{today}"}}
    if branch_id:
        sales_query["branch_id"] = branch_id
    
    today_sales = await db["transactions"].count_documents(sales_query)
    
    # Revenue from transactions
    revenue_pipeline = [
        {"$match": sales_query},
        {"$group": {"_id": None, "total": {"$sum": "$total"}}}
    ]
    revenue_result = await db["transactions"].aggregate(revenue_pipeline).to_list(1)
    today_revenue = revenue_result[0]["total"] if revenue_result else 0
    
    return {
        "items_count": items_count,
        "total_stock": total_stock,
        "today_sales": today_sales,
        "today_revenue": today_revenue
    }


@router.get("/reports/stock-summary")
async def get_stock_summary(
    branch_id: str = "",
    user: dict = Depends(get_current_user)
):
    """Get stock summary - all calculated from stock_movements"""
    db = get_db()
    
    match = {}
    if branch_id:
        match["branch_id"] = branch_id
    
    pipeline = [
        {"$match": match} if match else {"$match": {}},
        {"$group": {
            "_id": "$item_id",
            "total_in": {"$sum": {"$cond": [{"$gt": ["$quantity", 0]}, "$quantity", 0]}},
            "total_out": {"$sum": {"$cond": [{"$lt": ["$quantity", 0]}, {"$abs": "$quantity"}, 0]}},
            "current_stock": {"$sum": "$quantity"}
        }}
    ]
    
    results = await db["stock_movements"].aggregate(pipeline).to_list(1000)
    
    # Add item details
    for r in results:
        item = await db["products"].find_one({"id": r["_id"]}, {"_id": 0, "code": 1, "name": 1})
        if item:
            r["item_code"] = item.get("code")
            r["item_name"] = item.get("name")
    
    return {
        "summary": results,
        "total_items": len(results),
        "total_stock": sum(r["current_stock"] for r in results)
    }
