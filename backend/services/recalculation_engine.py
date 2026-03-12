# OCB TITAN ERP - TRANSACTION RECALCULATION ENGINE
# Setiap perubahan transaksi harus memicu recalculation otomatis
# Engine ini WAJIB dipanggil saat owner mengedit transaksi

from datetime import datetime, timezone
from typing import Optional, Dict, List, Any
import uuid
import json


class RecalculationEngine:
    """
    Transaction Recalculation Engine
    
    When owner edits a transaction, this engine:
    1. Updates the transaction document
    2. Recalculates stock movements
    3. Recalculates accounting journal
    4. Recalculates inventory valuation
    5. Creates audit log
    """
    
    def __init__(self, db):
        self.db = db
        # Collections
        self.audit_logs = db["audit_logs"]
        self.stock_movements = db["stock_movements"]
        self.journal_entries = db["journal_entries"]
        self.journal_entry_lines = db["journal_entry_lines"]
        self.general_ledger = db["general_ledger"]
        self.accounts_payable = db["accounts_payable"]
        self.accounts_receivable = db["accounts_receivable"]
        self.products = db["products"]
        self.item_price_history = db["item_price_history"]
    
    # ==================== AUDIT LOG ====================
    
    async def create_audit_log(
        self,
        user_id: str,
        user_name: str,
        action: str,
        module: str,
        record_id: str,
        old_value: Any,
        new_value: Any,
        description: str = "",
        ip_address: str = ""
    ) -> Dict:
        """Create audit log entry for any data change"""
        log = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "user_name": user_name,
            "action": action,  # create, update, delete
            "module": module,  # purchase_order, purchase, sales, inventory, journal, item, supplier, customer
            "record_id": record_id,
            "old_value": json.dumps(old_value, default=str) if old_value else None,
            "new_value": json.dumps(new_value, default=str) if new_value else None,
            "description": description,
            "ip_address": ip_address,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await self.audit_logs.insert_one(log)
        return log
    
    # ==================== STOCK RECALCULATION ====================
    
    async def recalculate_stock_movements(
        self,
        reference_id: str,
        reference_no: str,
        new_items: List[Dict],
        movement_type: str,
        branch_id: str,
        user_id: str = "",
        user_name: str = "",
        supplier_name: str = "",
        customer_name: str = ""
    ) -> Dict:
        """
        Recalculate stock movements for a reference document.
        
        Steps:
        1. Get old movements
        2. Delete old movements
        3. Create new movements
        4. Sync product_stocks cache
        """
        from services.stock_ssot import get_stock_ssot
        stock_ssot = get_stock_ssot(self.db)
        
        # Get old movements for audit
        old_movements = await self.stock_movements.find(
            {"reference_id": reference_id},
            {"_id": 0}
        ).to_list(1000)
        
        old_summary = []
        affected_items = set()
        
        for mov in old_movements:
            item_id = mov.get("item_id") or mov.get("product_id")
            affected_items.add(item_id)
            old_summary.append({
                "item_id": item_id,
                "quantity": mov.get("quantity", 0),
                "movement_type": mov.get("movement_type", "")
            })
        
        # Delete old movements
        deleted_count = 0
        if old_movements:
            result = await self.stock_movements.delete_many({"reference_id": reference_id})
            deleted_count = result.deleted_count
        
        # Create new movements
        created_count = 0
        for item in new_items:
            item_id = item.get("item_id") or item.get("product_id")
            quantity = item.get("quantity", 0)
            affected_items.add(item_id)
            
            if quantity == 0:
                continue
            
            # Determine quantity direction based on movement type
            if movement_type in ["sales", "transfer_out", "return_purchase", "production_out", "stock_out"]:
                quantity = -abs(quantity)
            else:
                quantity = abs(quantity)
            
            await stock_ssot.record_movement(
                item_id=item_id,
                quantity=quantity,
                movement_type=movement_type,
                branch_id=branch_id,
                reference_id=reference_id,
                reference_no=reference_no,
                unit_cost=item.get("unit_cost", 0),
                notes=f"Recalculated by owner: {user_name}",
                user_id=user_id,
                user_name=user_name,
                supplier_name=supplier_name,
                customer_name=customer_name
            )
            created_count += 1
        
        return {
            "deleted_movements": deleted_count,
            "created_movements": created_count,
            "old_summary": old_summary,
            "affected_items": list(affected_items)
        }
    
    # ==================== JOURNAL RECALCULATION ====================
    
    async def recalculate_journal(
        self,
        reference_id: str,
        reference_no: str,
        reference_type: str,
        new_entries: List[Dict],
        description: str = "",
        branch_id: str = "",
        user_id: str = "",
        user_name: str = ""
    ) -> Dict:
        """
        Recalculate journal entries for a reference document.
        
        Steps:
        1. Get old journal
        2. Delete old journal lines and ledger entries
        3. Update journal with new entries
        4. Create new journal lines and ledger entries
        """
        # Find existing journal
        existing_journal = await self.journal_entries.find_one(
            {"$or": [
                {"reference_id": reference_id},
                {"source_id": reference_id}
            ]},
            {"_id": 0}
        )
        
        old_entries = []
        journal_id = None
        journal_number = None
        
        if existing_journal:
            journal_id = existing_journal.get("id")
            journal_number = existing_journal.get("journal_number", existing_journal.get("journal_no"))
            old_entries = existing_journal.get("entries", existing_journal.get("lines", []))
            
            # Delete old journal lines
            await self.journal_entry_lines.delete_many({"journal_id": journal_id})
            
            # Delete old ledger entries
            await self.general_ledger.delete_many({
                "$or": [
                    {"journal_id": journal_id},
                    {"reference": reference_no}
                ]
            })
        else:
            # Create new journal
            from utils.number_generator import generate_transaction_number
            journal_number = await generate_transaction_number(self.db, "JV")
            journal_id = str(uuid.uuid4())
        
        # Validate balance
        total_debit = sum(e.get("debit", 0) for e in new_entries)
        total_credit = sum(e.get("credit", 0) for e in new_entries)
        
        if abs(total_debit - total_credit) > 0.01:
            raise ValueError(f"Journal not balanced: Debit={total_debit}, Credit={total_credit}")
        
        # Update or create journal
        journal_doc = {
            "id": journal_id,
            "journal_number": journal_number,
            "journal_no": journal_number,
            "journal_date": datetime.now(timezone.utc).isoformat(),
            "reference_type": reference_type,
            "reference_id": reference_id,
            "reference_number": reference_no,
            "description": description or f"Recalculated {reference_type} {reference_no}",
            "branch_id": branch_id,
            "entries": new_entries,
            "lines": new_entries,
            "total_debit": total_debit,
            "total_credit": total_credit,
            "is_balanced": True,
            "status": "posted",
            "updated_by": user_id,
            "updated_by_name": user_name,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        if existing_journal:
            await self.journal_entries.update_one(
                {"id": journal_id},
                {"$set": journal_doc}
            )
        else:
            journal_doc["created_by"] = user_id
            journal_doc["created_by_name"] = user_name
            journal_doc["created_at"] = datetime.now(timezone.utc).isoformat()
            await self.journal_entries.insert_one(journal_doc)
        
        # Create journal lines
        for entry in new_entries:
            line = {
                "id": str(uuid.uuid4()),
                "journal_id": journal_id,
                "account_code": entry.get("account_code"),
                "account_name": entry.get("account_name"),
                "debit": entry.get("debit", 0),
                "credit": entry.get("credit", 0),
                "description": entry.get("description", "")
            }
            await self.journal_entry_lines.insert_one(line)
            
            # Create ledger entry
            ledger = {
                "id": str(uuid.uuid4()),
                "journal_id": journal_id,
                "journal_number": journal_number,
                "account_code": entry.get("account_code"),
                "account_name": entry.get("account_name"),
                "debit": entry.get("debit", 0),
                "credit": entry.get("credit", 0),
                "date": datetime.now(timezone.utc).isoformat(),
                "reference": reference_no,
                "description": description
            }
            await self.general_ledger.insert_one(ledger)
        
        return {
            "journal_id": journal_id,
            "journal_number": journal_number,
            "old_entries_count": len(old_entries),
            "new_entries_count": len(new_entries),
            "total_debit": total_debit,
            "total_credit": total_credit
        }
    
    # ==================== AP/AR RECALCULATION ====================
    
    async def recalculate_payable(
        self,
        reference_id: str,
        supplier_id: str,
        supplier_name: str,
        new_amount: float,
        due_date: str = None,
        user_id: str = ""
    ) -> Dict:
        """Recalculate accounts payable for a purchase"""
        existing_ap = await self.accounts_payable.find_one(
            {"$or": [
                {"reference_id": reference_id},
                {"source_id": reference_id}
            ]},
            {"_id": 0}
        )
        
        old_amount = 0
        if existing_ap:
            old_amount = existing_ap.get("amount", 0)
            paid_amount = existing_ap.get("paid_amount", 0)
            new_balance = new_amount - paid_amount
            
            await self.accounts_payable.update_one(
                {"id": existing_ap["id"]},
                {"$set": {
                    "amount": new_amount,
                    "balance": max(0, new_balance),
                    "status": "paid" if new_balance <= 0 else "unpaid",
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            
            return {
                "ap_id": existing_ap["id"],
                "old_amount": old_amount,
                "new_amount": new_amount,
                "action": "updated"
            }
        
        return {"action": "none", "message": "No AP found for reference"}
    
    async def recalculate_receivable(
        self,
        reference_id: str,
        customer_id: str,
        customer_name: str,
        new_amount: float,
        due_date: str = None,
        user_id: str = ""
    ) -> Dict:
        """Recalculate accounts receivable for a sale"""
        existing_ar = await self.accounts_receivable.find_one(
            {"$or": [
                {"reference_id": reference_id},
                {"source_id": reference_id},
                {"invoice_number": {"$regex": reference_id}}
            ]},
            {"_id": 0}
        )
        
        old_amount = 0
        if existing_ar:
            old_amount = existing_ar.get("amount", 0)
            paid_amount = existing_ar.get("paid_amount", 0)
            new_balance = new_amount - paid_amount
            
            await self.accounts_receivable.update_one(
                {"id": existing_ar["id"]},
                {"$set": {
                    "amount": new_amount,
                    "remaining_amount": max(0, new_balance),
                    "outstanding_amount": max(0, new_balance),
                    "status": "paid" if new_balance <= 0 else "open",
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            
            return {
                "ar_id": existing_ar["id"],
                "old_amount": old_amount,
                "new_amount": new_amount,
                "action": "updated"
            }
        
        return {"action": "none", "message": "No AR found for reference"}
    
    # ==================== INVENTORY VALUATION ====================
    
    async def recalculate_item_valuation(
        self,
        item_id: str,
        new_cost: float = None,
        user_id: str = "",
        user_name: str = ""
    ) -> Dict:
        """
        Recalculate inventory valuation when item cost changes.
        
        Steps:
        1. Update product cost_price
        2. Record price history
        3. Return valuation impact
        """
        # Get current product
        product = await self.products.find_one({"id": item_id}, {"_id": 0})
        if not product:
            return {"error": "Product not found"}
        
        old_cost = product.get("cost_price", 0)
        
        if new_cost is not None and new_cost != old_cost:
            # Update product cost
            await self.products.update_one(
                {"id": item_id},
                {"$set": {
                    "cost_price": new_cost,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            
            # Record price history
            await self.item_price_history.insert_one({
                "id": str(uuid.uuid4()),
                "product_id": item_id,
                "product_code": product.get("code", ""),
                "product_name": product.get("name", ""),
                "old_cost": old_cost,
                "new_cost": new_cost,
                "change_type": "owner_edit",
                "changed_by": user_id,
                "changed_by_name": user_name,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            # Calculate valuation impact
            from services.stock_ssot import get_stock_ssot
            stock_ssot = get_stock_ssot(self.db)
            total_stock = await stock_ssot.get_stock(item_id)
            
            old_valuation = total_stock * old_cost
            new_valuation = total_stock * new_cost
            valuation_change = new_valuation - old_valuation
            
            return {
                "item_id": item_id,
                "old_cost": old_cost,
                "new_cost": new_cost,
                "total_stock": total_stock,
                "old_valuation": old_valuation,
                "new_valuation": new_valuation,
                "valuation_change": valuation_change
            }
        
        return {
            "item_id": item_id,
            "cost_price": old_cost,
            "message": "No cost change required"
        }
    
    # ==================== FULL TRANSACTION RECALCULATION ====================
    
    async def recalculate_purchase_order(
        self,
        po_id: str,
        new_items: List[Dict],
        new_total: float,
        branch_id: str,
        supplier_id: str,
        supplier_name: str,
        user_id: str,
        user_name: str,
        po_number: str = ""
    ) -> Dict:
        """
        Full recalculation when PO is edited by owner.
        """
        results = {
            "po_id": po_id,
            "stock": None,
            "journal": None,
            "ap": None,
            "audit": None
        }
        
        # Check if PO was received
        po = await self.db["purchase_orders"].find_one({"id": po_id}, {"_id": 0})
        if not po:
            return {"error": "PO not found"}
        
        po_number = po_number or po.get("po_number", "")
        
        # Only recalculate stock if PO was received
        if po.get("status") in ["received", "partial"]:
            # Recalculate stock movements
            received_items = [
                {
                    "item_id": item.get("product_id"),
                    "quantity": item.get("received_qty", item.get("quantity", 0)),
                    "unit_cost": item.get("unit_cost", 0)
                }
                for item in new_items
                if item.get("received_qty", item.get("quantity", 0)) > 0
            ]
            
            results["stock"] = await self.recalculate_stock_movements(
                reference_id=po_id,
                reference_no=po_number,
                new_items=received_items,
                movement_type="purchase_receive",
                branch_id=branch_id,
                user_id=user_id,
                user_name=user_name,
                supplier_name=supplier_name
            )
            
            # Recalculate journal (Debit: Inventory, Credit: AP)
            journal_entries = [
                {
                    "account_code": "1-1400",
                    "account_name": "Persediaan Barang",
                    "debit": new_total,
                    "credit": 0,
                    "description": f"Persediaan dari {po_number}"
                },
                {
                    "account_code": "2-1100",
                    "account_name": "Hutang Dagang",
                    "debit": 0,
                    "credit": new_total,
                    "description": f"Hutang ke {supplier_name}"
                }
            ]
            
            results["journal"] = await self.recalculate_journal(
                reference_id=po_id,
                reference_no=po_number,
                reference_type="purchase_credit",
                new_entries=journal_entries,
                description=f"Pembelian {po_number}",
                branch_id=branch_id,
                user_id=user_id,
                user_name=user_name
            )
            
            # Recalculate AP
            results["ap"] = await self.recalculate_payable(
                reference_id=po_id,
                supplier_id=supplier_id,
                supplier_name=supplier_name,
                new_amount=new_total,
                user_id=user_id
            )
        
        # Create audit log
        results["audit"] = await self.create_audit_log(
            user_id=user_id,
            user_name=user_name,
            action="edit_recalculate",
            module="purchase_order",
            record_id=po_id,
            old_value=po,
            new_value={"items": new_items, "total": new_total},
            description=f"Owner edit PO {po_number} - full recalculation"
        )
        
        return results
    
    async def recalculate_sales_invoice(
        self,
        invoice_id: str,
        new_items: List[Dict],
        new_total: float,
        new_hpp: float,
        branch_id: str,
        customer_id: str,
        customer_name: str,
        user_id: str,
        user_name: str,
        invoice_number: str = "",
        is_credit: bool = False
    ) -> Dict:
        """
        Full recalculation when sales invoice is edited by owner.
        """
        results = {
            "invoice_id": invoice_id,
            "stock": None,
            "journal_sales": None,
            "journal_hpp": None,
            "ar": None,
            "audit": None
        }
        
        # Get existing invoice
        invoice = await self.db["sales_invoices"].find_one({"id": invoice_id}, {"_id": 0})
        if not invoice:
            return {"error": "Invoice not found"}
        
        invoice_number = invoice_number or invoice.get("invoice_number", "")
        
        # Recalculate stock movements (negative for sales)
        sales_items = [
            {
                "item_id": item.get("product_id"),
                "quantity": item.get("quantity", 0),
                "unit_cost": item.get("cost_price", 0)
            }
            for item in new_items
            if item.get("quantity", 0) > 0
        ]
        
        results["stock"] = await self.recalculate_stock_movements(
            reference_id=invoice_id,
            reference_no=invoice_number,
            new_items=sales_items,
            movement_type="sales",
            branch_id=branch_id,
            user_id=user_id,
            user_name=user_name,
            customer_name=customer_name
        )
        
        # Recalculate sales journal
        sales_entries = []
        if is_credit:
            sales_entries.append({
                "account_code": "1-1300",
                "account_name": "Piutang Usaha",
                "debit": new_total,
                "credit": 0,
                "description": f"Piutang {customer_name}"
            })
        else:
            sales_entries.append({
                "account_code": "1-1100",
                "account_name": "Kas",
                "debit": new_total,
                "credit": 0,
                "description": f"Penjualan tunai {invoice_number}"
            })
        
        sales_entries.append({
            "account_code": "4-1000",
            "account_name": "Penjualan",
            "debit": 0,
            "credit": new_total,
            "description": f"Penjualan {invoice_number}"
        })
        
        results["journal_sales"] = await self.recalculate_journal(
            reference_id=invoice_id,
            reference_no=invoice_number,
            reference_type="sales",
            new_entries=sales_entries,
            description=f"Penjualan {invoice_number}",
            branch_id=branch_id,
            user_id=user_id,
            user_name=user_name
        )
        
        # Recalculate HPP journal
        if new_hpp > 0:
            hpp_entries = [
                {
                    "account_code": "5-1000",
                    "account_name": "Harga Pokok Penjualan",
                    "debit": new_hpp,
                    "credit": 0,
                    "description": f"HPP {invoice_number}"
                },
                {
                    "account_code": "1-1400",
                    "account_name": "Persediaan Barang",
                    "debit": 0,
                    "credit": new_hpp,
                    "description": f"Pengurangan persediaan {invoice_number}"
                }
            ]
            
            results["journal_hpp"] = await self.recalculate_journal(
                reference_id=f"{invoice_id}_hpp",
                reference_no=f"HPP-{invoice_number}",
                reference_type="hpp",
                new_entries=hpp_entries,
                description=f"HPP {invoice_number}",
                branch_id=branch_id,
                user_id=user_id,
                user_name=user_name
            )
        
        # Recalculate AR if credit sale
        if is_credit and new_total > 0:
            results["ar"] = await self.recalculate_receivable(
                reference_id=invoice_id,
                customer_id=customer_id,
                customer_name=customer_name,
                new_amount=new_total,
                user_id=user_id
            )
        
        # Create audit log
        results["audit"] = await self.create_audit_log(
            user_id=user_id,
            user_name=user_name,
            action="edit_recalculate",
            module="sales_invoice",
            record_id=invoice_id,
            old_value=invoice,
            new_value={"items": new_items, "total": new_total, "hpp": new_hpp},
            description=f"Owner edit Sales {invoice_number} - full recalculation"
        )
        
        return results


# Global instance getter
def get_recalculation_engine(db):
    """Get Recalculation Engine instance"""
    return RecalculationEngine(db)
