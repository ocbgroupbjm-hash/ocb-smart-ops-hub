# OCB TITAN ERP - STOCK SINGLE SOURCE OF TRUTH SERVICE
# Semua modul WAJIB menggunakan service ini untuk kalkulasi stok
# TIDAK BOLEH baca stok dari products.stock, branch_stock.stock, atau warehouse_stock.stock

from datetime import datetime, timezone
from typing import Optional, Dict, List
import uuid


class StockSSOT:
    """
    SINGLE SOURCE OF TRUTH for all stock calculations.
    Stock is ALWAYS calculated from stock_movements collection.
    """
    
    def __init__(self, db):
        self.db = db
        self.stock_movements = db["stock_movements"]
        self.products = db["products"]
        self.product_stocks = db["product_stocks"]
    
    # ==================== READ STOCK (SINGLE SOURCE) ====================
    
    async def get_stock(self, item_id: str, branch_id: str = None) -> int:
        """
        Calculate current stock from stock_movements.
        This is the ONLY method to get stock quantity.
        
        Args:
            item_id: Product/Item ID
            branch_id: Optional branch ID for branch-specific stock
        
        Returns:
            Current stock quantity (can be negative if oversold)
        """
        match = {"item_id": item_id}
        if branch_id:
            match["branch_id"] = branch_id
        
        # Also try product_id field for backward compatibility
        pipeline = [
            {"$match": {
                "$or": [
                    {"item_id": item_id},
                    {"product_id": item_id}
                ],
                **({"branch_id": branch_id} if branch_id else {})
            }},
            {"$group": {"_id": None, "total": {"$sum": "$quantity"}}}
        ]
        
        result = await self.stock_movements.aggregate(pipeline).to_list(1)
        return result[0]["total"] if result else 0
    
    async def get_stock_bulk(self, item_ids: List[str], branch_id: str = None) -> Dict[str, int]:
        """
        Calculate stock for multiple items at once.
        More efficient than calling get_stock() for each item.
        """
        if not item_ids:
            return {}
        
        match = {
            "$or": [
                {"item_id": {"$in": item_ids}},
                {"product_id": {"$in": item_ids}}
            ]
        }
        if branch_id:
            match["branch_id"] = branch_id
        
        pipeline = [
            {"$match": match},
            {"$group": {
                "_id": {"$ifNull": ["$item_id", "$product_id"]},
                "total": {"$sum": "$quantity"}
            }}
        ]
        
        result = await self.stock_movements.aggregate(pipeline).to_list(len(item_ids))
        return {item["_id"]: item["total"] for item in result}
    
    async def get_stock_by_branch(self, item_id: str) -> List[Dict]:
        """Get stock breakdown by branch for an item"""
        pipeline = [
            {"$match": {
                "$or": [{"item_id": item_id}, {"product_id": item_id}]
            }},
            {"$group": {
                "_id": "$branch_id",
                "total": {"$sum": "$quantity"}
            }}
        ]
        
        result = await self.stock_movements.aggregate(pipeline).to_list(100)
        
        # Get branch names
        branch_stocks = []
        for item in result:
            branch = await self.db["branches"].find_one(
                {"id": item["_id"]}, {"_id": 0, "name": 1}
            )
            branch_stocks.append({
                "branch_id": item["_id"],
                "branch_name": branch.get("name", "Unknown") if branch else "Unknown",
                "stock": item["total"]
            })
        
        return branch_stocks
    
    # ==================== WRITE STOCK (CREATE MOVEMENT) ====================
    
    async def record_movement(
        self,
        item_id: str,
        quantity: int,
        movement_type: str,
        branch_id: str,
        reference_id: str = "",
        reference_no: str = "",
        unit_cost: float = 0,
        notes: str = "",
        user_id: str = "",
        user_name: str = "",
        supplier_name: str = "",
        customer_name: str = ""
    ) -> Dict:
        """
        Record a stock movement. This is the ONLY way to change stock.
        
        Movement types:
        - purchase_receive: Goods receipt from PO (+)
        - sales: Sales to customer (-)
        - adjustment: Stock adjustment (+/-)
        - transfer_in: Transfer received (+)
        - transfer_out: Transfer sent (-)
        - return_purchase: Return to supplier (-)
        - return_sales: Return from customer (+)
        - opname_in: Stock opname increase (+)
        - opname_out: Stock opname decrease (-)
        - production_in: Production output (+)
        - production_out: Production materials (-)
        - initial: Initial stock setup (+)
        
        Args:
            item_id: Product/Item ID
            quantity: Quantity change (positive=in, negative=out)
            movement_type: Type of movement
            branch_id: Branch ID
            reference_id: Reference document ID
            reference_no: Reference document number
            unit_cost: Cost per unit
            notes: Additional notes
            user_id: User who made the change
            user_name: User name
            supplier_name: Supplier name (for purchases)
            customer_name: Customer name (for sales)
        
        Returns:
            Created movement record
        """
        # Get current stock before movement
        stock_before = await self.get_stock(item_id, branch_id)
        stock_after = stock_before + quantity
        
        # Get product info
        product = await self.products.find_one({"id": item_id}, {"_id": 0, "code": 1, "name": 1})
        
        movement = {
            "id": str(uuid.uuid4()),
            "item_id": item_id,
            "product_id": item_id,  # Backward compatibility
            "product_code": product.get("code", "") if product else "",
            "product_name": product.get("name", "") if product else "",
            "branch_id": branch_id,
            "quantity": quantity,
            "movement_type": movement_type,
            "transaction_type": movement_type,  # Backward compatibility
            "stock_before": stock_before,
            "stock_after": stock_after,
            "reference_id": reference_id,
            "reference_no": reference_no,
            "reference_number": reference_no,  # Backward compatibility
            "unit_cost": unit_cost,
            "total_value": abs(quantity) * unit_cost,
            "notes": notes,
            "supplier_name": supplier_name,
            "customer_name": customer_name,
            "created_by": user_id,
            "created_by_name": user_name,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await self.stock_movements.insert_one(movement)
        
        # Sync product_stocks for UI speed (optional cache)
        await self._sync_product_stock(item_id, branch_id)
        
        return {
            "id": movement["id"],
            "stock_before": stock_before,
            "stock_after": stock_after,
            "movement_type": movement_type
        }
    
    async def _sync_product_stock(self, item_id: str, branch_id: str):
        """Sync product_stocks collection (cache) with calculated stock"""
        calculated_qty = await self.get_stock(item_id, branch_id)
        
        existing = await self.product_stocks.find_one({
            "product_id": item_id, "branch_id": branch_id
        })
        
        if existing:
            await self.product_stocks.update_one(
                {"product_id": item_id, "branch_id": branch_id},
                {"$set": {
                    "quantity": calculated_qty,
                    "available": calculated_qty - existing.get("reserved", 0),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
        else:
            await self.product_stocks.insert_one({
                "id": str(uuid.uuid4()),
                "product_id": item_id,
                "branch_id": branch_id,
                "quantity": calculated_qty,
                "available": calculated_qty,
                "reserved": 0,
                "created_at": datetime.now(timezone.utc).isoformat()
            })
    
    # ==================== RECALCULATE (OWNER EDIT) ====================
    
    async def recalculate_from_reference(
        self,
        reference_id: str,
        new_items: List[Dict],
        movement_type: str,
        branch_id: str,
        reference_no: str = "",
        user_id: str = "",
        user_name: str = ""
    ) -> Dict:
        """
        Recalculate stock movements for a reference document (PO, Sales, etc).
        Used when owner edits a transaction.
        
        Steps:
        1. Delete old movements for this reference
        2. Create new movements based on new_items
        3. Return summary of changes
        
        Args:
            reference_id: Document ID (PO ID, Invoice ID, etc)
            new_items: List of new items with {item_id, quantity, unit_cost}
            movement_type: Type of movement
            branch_id: Branch ID
            reference_no: Document number
            user_id: User who made the change
            user_name: User name
        
        Returns:
            Summary of changes made
        """
        # Get old movements for audit
        old_movements = await self.stock_movements.find(
            {"reference_id": reference_id},
            {"_id": 0}
        ).to_list(1000)
        
        old_summary = {}
        for mov in old_movements:
            item_id = mov.get("item_id") or mov.get("product_id")
            old_summary[item_id] = old_summary.get(item_id, 0) + mov.get("quantity", 0)
        
        # Delete old movements
        delete_result = await self.stock_movements.delete_many({
            "reference_id": reference_id
        })
        
        # Create new movements
        new_summary = {}
        for item in new_items:
            item_id = item.get("item_id") or item.get("product_id")
            quantity = item.get("quantity", 0)
            
            # Determine quantity direction based on movement type
            if movement_type in ["sales", "transfer_out", "return_purchase", "production_out"]:
                quantity = -abs(quantity)
            else:
                quantity = abs(quantity)
            
            await self.record_movement(
                item_id=item_id,
                quantity=quantity,
                movement_type=movement_type,
                branch_id=branch_id,
                reference_id=reference_id,
                reference_no=reference_no,
                unit_cost=item.get("unit_cost", 0),
                notes=f"Recalculated by owner: {user_name}",
                user_id=user_id,
                user_name=user_name
            )
            
            new_summary[item_id] = new_summary.get(item_id, 0) + quantity
        
        return {
            "reference_id": reference_id,
            "deleted_movements": delete_result.deleted_count,
            "created_movements": len(new_items),
            "old_summary": old_summary,
            "new_summary": new_summary
        }
    
    # ==================== STOCK CARD (KARTU STOK) ====================
    
    async def get_stock_card(
        self,
        item_id: str,
        branch_id: str = None,
        start_date: str = None,
        end_date: str = None
    ) -> Dict:
        """
        Get complete stock card with running balance.
        This is the definitive stock history.
        """
        # Build query
        match = {"$or": [{"item_id": item_id}, {"product_id": item_id}]}
        if branch_id:
            match["branch_id"] = branch_id
        
        # Calculate opening balance if date filter
        opening_balance = 0
        if start_date:
            opening_query = {
                **match,
                "created_at": {"$lt": start_date}
            }
            opening_pipeline = [
                {"$match": opening_query},
                {"$group": {"_id": None, "total": {"$sum": "$quantity"}}}
            ]
            opening_result = await self.stock_movements.aggregate(opening_pipeline).to_list(1)
            opening_balance = opening_result[0]["total"] if opening_result else 0
            
            # Add date filter
            match["created_at"] = {"$gte": start_date}
            if end_date:
                match["created_at"]["$lt"] = end_date
        
        # Get movements
        movements = await self.stock_movements.find(
            match, {"_id": 0}
        ).sort("created_at", 1).to_list(10000)
        
        # Build stock card with running balance
        running_balance = opening_balance
        stock_card = []
        
        # Add opening balance row
        if start_date:
            stock_card.append({
                "date": start_date,
                "type": "Saldo Awal",
                "reference": "-",
                "in": 0,
                "out": 0,
                "balance": opening_balance,
                "notes": f"Opening balance as of {start_date}"
            })
        
        # Add movements
        for mov in movements:
            qty = mov.get("quantity", 0)
            running_balance += qty
            
            stock_card.append({
                "id": mov.get("id"),
                "date": mov.get("created_at", "")[:19],
                "type": mov.get("movement_type", mov.get("transaction_type", "")),
                "reference": mov.get("reference_no", mov.get("reference_number", "-")),
                "in": qty if qty > 0 else 0,
                "out": abs(qty) if qty < 0 else 0,
                "balance": running_balance,
                "notes": mov.get("notes", ""),
                "partner": mov.get("supplier_name") or mov.get("customer_name") or "-",
                "unit_cost": mov.get("unit_cost", 0)
            })
        
        # Get product info
        product = await self.products.find_one({"id": item_id}, {"_id": 0, "code": 1, "name": 1})
        
        return {
            "item_id": item_id,
            "product_code": product.get("code", "") if product else "",
            "product_name": product.get("name", "") if product else "",
            "branch_id": branch_id,
            "opening_balance": opening_balance,
            "closing_balance": running_balance,
            "total_in": sum(m["in"] for m in stock_card),
            "total_out": sum(m["out"] for m in stock_card),
            "movements": stock_card,
            "count": len(stock_card)
        }


# Global instance getter
def get_stock_ssot(db):
    """Get Stock SSOT service instance"""
    return StockSSOT(db)
