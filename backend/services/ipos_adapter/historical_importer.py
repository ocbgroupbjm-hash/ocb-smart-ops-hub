# iPOS Historical Transaction Importer
# Imports sales and purchase transactions from staging to OCB TITAN
# 
# RULES:
# 1. PILOT TENANT ONLY: ocb_titan
# 2. DRY-RUN FIRST - validate before commit
# 3. BATCH COMMITS with import_batch_id
# 4. ROLLBACK SUPPORT - can undo entire batch
# 5. AUDIT LOGGED - every action tracked

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class HistoricalTransactionImporter:
    """
    Import historical sales and purchase transactions from iPOS staging
    
    IMPORT FLOW:
    1. DRY-RUN: Validate all data, calculate effects, report issues
    2. COMMIT: Execute import with batch tracking
    3. VALIDATE: Reconcile totals after import
    4. ROLLBACK: Undo batch if needed
    
    EFFECTS TRACKED:
    - Stock movements (out for sales, in for purchases)
    - AR/AP creation
    - Journal entries
    - HPP/COGS
    """
    
    PILOT_TENANT = "ocb_titan"
    
    def __init__(self, db, tenant_id: str = None):
        if tenant_id and tenant_id != self.PILOT_TENANT:
            raise ValueError(f"Historical import only allowed on pilot tenant: {self.PILOT_TENANT}")
        
        self.db = db
        self.tenant_id = self.PILOT_TENANT
        self.current_batch_id = None
        self.dry_run_results = None
        self.import_stats = {}
    
    # ============================================================
    # DRY-RUN METHODS
    # ============================================================
    
    async def dry_run_sales_import(self) -> Dict:
        """
        DRY-RUN: Validate sales import without committing
        
        Checks:
        - Product existence
        - Stock availability (if enforcing)
        - Customer mapping
        - Warehouse mapping
        - Calculate expected effects
        """
        logger.info("=== DRY-RUN: Sales Import Validation ===")
        
        result = {
            "type": "SALES_DRY_RUN",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tenant_id": self.tenant_id,
            "status": "VALIDATING",
            "summary": {},
            "validation_errors": [],
            "warnings": [],
            "expected_effects": {}
        }
        
        # Get product mapping (code -> id)
        product_map = {}
        async for p in self.db.products.find({"tenant_id": self.tenant_id}):
            product_map[p.get("code")] = {
                "id": p.get("id"),
                "name": p.get("name"),
                "cost_price": p.get("cost_price", 0)
            }
        
        # Get branch mapping (code -> id)
        branch_map = {}
        async for b in self.db.branches.find({"tenant_id": self.tenant_id}):
            branch_map[b.get("code")] = b.get("id")
        
        # Get staged sales
        sales_headers = []
        async for doc in self.db.ipos_sales_hd_staging.find({"tenant_id": self.tenant_id}):
            sales_headers.append(doc.get("data", {}))
        
        sales_details = []
        async for doc in self.db.ipos_sales_dt_staging.find({"tenant_id": self.tenant_id}):
            sales_details.append(doc.get("data", {}))
        
        # Group details by transaction
        details_by_trx = {}
        for d in sales_details:
            trx = d.get("transaction_no")
            if trx not in details_by_trx:
                details_by_trx[trx] = []
            details_by_trx[trx].append(d)
        
        result["summary"]["total_transactions"] = len(sales_headers)
        result["summary"]["total_line_items"] = len(sales_details)
        result["summary"]["total_value"] = sum(float(h.get("total", 0) or 0) for h in sales_headers)
        
        # Validate each transaction
        valid_count = 0
        invalid_count = 0
        missing_products = set()
        missing_branches = set()
        
        expected_stock_out = {}  # item_code -> qty
        expected_revenue = Decimal('0')
        expected_cogs = Decimal('0')
        expected_ar = Decimal('0')
        
        for header in sales_headers:
            trx_no = header.get("transaction_no")
            branch_code = header.get("warehouse_code")
            details = details_by_trx.get(trx_no, [])
            
            is_valid = True
            
            # Check branch
            if branch_code and branch_code not in branch_map:
                missing_branches.add(branch_code)
                # Auto-assign default branch
            
            # Check products in details
            for detail in details:
                item_code = detail.get("item_code")
                qty = float(detail.get("quantity", 0) or 0)
                
                if item_code not in product_map:
                    missing_products.add(item_code)
                    is_valid = False
                else:
                    # Track expected stock out
                    expected_stock_out[item_code] = expected_stock_out.get(item_code, 0) + qty
            
            if is_valid:
                valid_count += 1
                total = Decimal(str(header.get("total", 0) or 0))
                expected_revenue += total
                
                # AR if credit sale
                if header.get("payment_method") == "KREDIT" or float(header.get("paid_credit", 0) or 0) > 0:
                    expected_ar += total
            else:
                invalid_count += 1
        
        # Calculate expected COGS
        for item_code, qty in expected_stock_out.items():
            if item_code in product_map:
                cost = product_map[item_code].get("cost_price", 0)
                expected_cogs += Decimal(str(qty)) * Decimal(str(cost))
        
        result["summary"]["valid_transactions"] = valid_count
        result["summary"]["invalid_transactions"] = invalid_count
        
        if missing_products:
            result["validation_errors"].append({
                "type": "MISSING_PRODUCTS",
                "count": len(missing_products),
                "items": list(missing_products)[:20],
                "action": "These transactions will be skipped"
            })
        
        if missing_branches:
            result["warnings"].append({
                "type": "MISSING_BRANCHES",
                "count": len(missing_branches),
                "items": list(missing_branches)[:10],
                "action": "Will use default branch"
            })
        
        result["expected_effects"] = {
            "stock_out_items": len(expected_stock_out),
            "stock_out_total_qty": sum(expected_stock_out.values()),
            "revenue": float(expected_revenue),
            "cogs": float(expected_cogs),
            "gross_profit": float(expected_revenue - expected_cogs),
            "ar_created": float(expected_ar),
            "journal_entries": valid_count * 4  # 4 lines per sales
        }
        
        result["status"] = "READY" if invalid_count == 0 else "HAS_ISSUES"
        result["can_proceed"] = valid_count > 0
        
        self.dry_run_results = result
        return result
    
    async def dry_run_purchase_import(self) -> Dict:
        """DRY-RUN: Validate purchase import without committing"""
        logger.info("=== DRY-RUN: Purchase Import Validation ===")
        
        result = {
            "type": "PURCHASE_DRY_RUN",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tenant_id": self.tenant_id,
            "status": "VALIDATING",
            "summary": {},
            "validation_errors": [],
            "warnings": [],
            "expected_effects": {}
        }
        
        # Get product mapping
        product_map = {}
        async for p in self.db.products.find({"tenant_id": self.tenant_id}):
            product_map[p.get("code")] = {
                "id": p.get("id"),
                "name": p.get("name")
            }
        
        # Get staged purchases
        purchase_headers = []
        async for doc in self.db.ipos_purchase_hd_staging.find({"tenant_id": self.tenant_id}):
            purchase_headers.append(doc.get("data", {}))
        
        purchase_details = []
        async for doc in self.db.ipos_purchase_dt_staging.find({"tenant_id": self.tenant_id}):
            purchase_details.append(doc.get("data", {}))
        
        # Group details by transaction
        details_by_trx = {}
        for d in purchase_details:
            trx = d.get("transaction_no")
            if trx not in details_by_trx:
                details_by_trx[trx] = []
            details_by_trx[trx].append(d)
        
        result["summary"]["total_transactions"] = len(purchase_headers)
        result["summary"]["total_line_items"] = len(purchase_details)
        result["summary"]["total_value"] = sum(float(h.get("total", 0) or 0) for h in purchase_headers)
        
        valid_count = 0
        invalid_count = 0
        missing_products = set()
        
        expected_stock_in = {}
        expected_inventory_value = Decimal('0')
        expected_ap = Decimal('0')
        
        for header in purchase_headers:
            trx_no = header.get("transaction_no")
            details = details_by_trx.get(trx_no, [])
            
            is_valid = True
            
            for detail in details:
                item_code = detail.get("item_code")
                qty = float(detail.get("quantity", 0) or 0)
                price = float(detail.get("price", 0) or 0)
                
                if item_code not in product_map:
                    missing_products.add(item_code)
                    is_valid = False
                else:
                    expected_stock_in[item_code] = expected_stock_in.get(item_code, 0) + qty
                    expected_inventory_value += Decimal(str(qty)) * Decimal(str(price))
            
            if is_valid:
                valid_count += 1
                total = Decimal(str(header.get("total", 0) or 0))
                
                # AP if credit purchase
                if header.get("payment_method") == "KREDIT" or float(header.get("paid_credit", 0) or 0) > 0:
                    expected_ap += total
            else:
                invalid_count += 1
        
        result["summary"]["valid_transactions"] = valid_count
        result["summary"]["invalid_transactions"] = invalid_count
        
        if missing_products:
            result["validation_errors"].append({
                "type": "MISSING_PRODUCTS",
                "count": len(missing_products),
                "items": list(missing_products)[:20]
            })
        
        result["expected_effects"] = {
            "stock_in_items": len(expected_stock_in),
            "stock_in_total_qty": sum(expected_stock_in.values()),
            "inventory_value_increase": float(expected_inventory_value),
            "ap_created": float(expected_ap),
            "journal_entries": valid_count * 2  # 2 lines per purchase
        }
        
        result["status"] = "READY" if invalid_count == 0 else "HAS_ISSUES"
        result["can_proceed"] = valid_count > 0
        
        return result
    
    # ============================================================
    # IMPORT METHODS (COMMIT)
    # ============================================================
    
    async def import_sales(self, skip_stock_update: bool = True, skip_journal: bool = True) -> Dict:
        """
        COMMIT: Import sales transactions
        
        Args:
            skip_stock_update: If True, don't update stock (already imported from iPOS)
            skip_journal: If True, don't create journals (already in staging)
        """
        logger.info("=== COMMIT: Sales Import ===")
        
        # Create batch
        self.current_batch_id = str(uuid.uuid4())
        batch_start = datetime.now(timezone.utc)
        
        batch_record = {
            "id": self.current_batch_id,
            "type": "SALES_IMPORT",
            "tenant_id": self.tenant_id,
            "status": "IN_PROGRESS",
            "started_at": batch_start.isoformat(),
            "source": "IPOS5_STAGING",
            "config": {
                "skip_stock_update": skip_stock_update,
                "skip_journal": skip_journal
            },
            "stats": {},
            "errors": []
        }
        
        await self.db.import_batches.insert_one(batch_record)
        
        result = {
            "batch_id": self.current_batch_id,
            "type": "SALES_IMPORT",
            "started_at": batch_start.isoformat(),
            "status": "IN_PROGRESS",
            "imported": 0,
            "skipped": 0,
            "errors": []
        }
        
        try:
            # Get mappings
            product_map = {}
            async for p in self.db.products.find({"tenant_id": self.tenant_id}):
                product_map[p.get("code")] = p
            
            branch_map = {}
            async for b in self.db.branches.find({"tenant_id": self.tenant_id}):
                branch_map[b.get("code")] = b.get("id")
            
            default_branch = list(branch_map.values())[0] if branch_map else "default"
            
            # Get staged data
            sales_headers = []
            async for doc in self.db.ipos_sales_hd_staging.find({"tenant_id": self.tenant_id}):
                sales_headers.append(doc.get("data", {}))
            
            details_by_trx = {}
            async for doc in self.db.ipos_sales_dt_staging.find({"tenant_id": self.tenant_id}):
                d = doc.get("data", {})
                trx = d.get("transaction_no")
                if trx not in details_by_trx:
                    details_by_trx[trx] = []
                details_by_trx[trx].append(d)
            
            # Process in batches
            batch_size = 500
            for i in range(0, len(sales_headers), batch_size):
                batch_headers = sales_headers[i:i+batch_size]
                
                for header in batch_headers:
                    trx_no = header.get("transaction_no")
                    details = details_by_trx.get(trx_no, [])
                    
                    # Validate products exist
                    valid = True
                    for detail in details:
                        if detail.get("item_code") not in product_map:
                            valid = False
                            break
                    
                    if not valid:
                        result["skipped"] += 1
                        continue
                    
                    try:
                        # Create sales invoice
                        branch_id = branch_map.get(header.get("warehouse_code"), default_branch)
                        
                        invoice_items = []
                        total_hpp = 0
                        
                        for detail in details:
                            product = product_map.get(detail.get("item_code"), {})
                            qty = float(detail.get("quantity", 0) or 0)
                            price = float(detail.get("price", 0) or 0)
                            hpp = float(detail.get("cost", 0) or product.get("cost_price", 0) or 0)
                            
                            invoice_items.append({
                                "product_id": product.get("id"),
                                "product_code": detail.get("item_code"),
                                "product_name": product.get("name", ""),
                                "quantity": qty,
                                "unit_price": price,
                                "cost_price": hpp,
                                "discount_percent": float(detail.get("discount1", 0) or 0),
                                "total": float(detail.get("total", 0) or qty * price),
                                "hpp": qty * hpp
                            })
                            total_hpp += qty * hpp
                        
                        invoice = {
                            "id": str(uuid.uuid4()),
                            "tenant_id": self.tenant_id,
                            "invoice_number": trx_no,
                            "branch_id": branch_id,
                            "date": header.get("date"),
                            "customer_code": header.get("customer_code"),
                            "sales_type": header.get("type", "JL"),
                            "subtotal": float(header.get("subtotal", 0) or 0),
                            "discount": float(header.get("discount", 0) or 0),
                            "tax": float(header.get("tax", 0) or 0),
                            "grand_total": float(header.get("total", 0) or 0),
                            "paid_amount": float(header.get("paid", 0) or 0),
                            "payment_method": header.get("payment_method", "TUNAI"),
                            "status": "COMPLETED",
                            "items": invoice_items,
                            "total_hpp": total_hpp,
                            "gross_profit": float(header.get("total", 0) or 0) - total_hpp,
                            "source_system": "IPOS5",
                            "import_batch_id": self.current_batch_id,
                            "created_at": datetime.now(timezone.utc).isoformat()
                        }
                        
                        await self.db.sales_invoices.insert_one(invoice)
                        result["imported"] += 1
                        
                        # Create audit log
                        await self._log_action("SALES_IMPORT", trx_no, invoice)
                        
                    except Exception as e:
                        result["errors"].append({
                            "transaction_no": trx_no,
                            "error": str(e)
                        })
                
                # Progress log
                logger.info(f"Processed {min(i + batch_size, len(sales_headers))}/{len(sales_headers)} sales")
            
            # Update batch record
            result["status"] = "COMPLETED"
            result["completed_at"] = datetime.now(timezone.utc).isoformat()
            
            await self.db.import_batches.update_one(
                {"id": self.current_batch_id},
                {"$set": {
                    "status": "COMPLETED",
                    "completed_at": result["completed_at"],
                    "stats": {
                        "imported": result["imported"],
                        "skipped": result["skipped"],
                        "errors": len(result["errors"])
                    }
                }}
            )
            
        except Exception as e:
            result["status"] = "FAILED"
            result["error"] = str(e)
            
            await self.db.import_batches.update_one(
                {"id": self.current_batch_id},
                {"$set": {"status": "FAILED", "error": str(e)}}
            )
        
        return result
    
    async def import_purchases(self, skip_stock_update: bool = True, skip_journal: bool = True) -> Dict:
        """COMMIT: Import purchase transactions"""
        logger.info("=== COMMIT: Purchase Import ===")
        
        self.current_batch_id = str(uuid.uuid4())
        batch_start = datetime.now(timezone.utc)
        
        batch_record = {
            "id": self.current_batch_id,
            "type": "PURCHASE_IMPORT",
            "tenant_id": self.tenant_id,
            "status": "IN_PROGRESS",
            "started_at": batch_start.isoformat(),
            "source": "IPOS5_STAGING"
        }
        
        await self.db.import_batches.insert_one(batch_record)
        
        result = {
            "batch_id": self.current_batch_id,
            "type": "PURCHASE_IMPORT",
            "started_at": batch_start.isoformat(),
            "status": "IN_PROGRESS",
            "imported": 0,
            "skipped": 0,
            "errors": []
        }
        
        try:
            # Get mappings
            product_map = {}
            async for p in self.db.products.find({"tenant_id": self.tenant_id}):
                product_map[p.get("code")] = p
            
            branch_map = {}
            async for b in self.db.branches.find({"tenant_id": self.tenant_id}):
                branch_map[b.get("code")] = b.get("id")
            
            default_branch = list(branch_map.values())[0] if branch_map else "default"
            
            # Get staged data
            purchase_headers = []
            async for doc in self.db.ipos_purchase_hd_staging.find({"tenant_id": self.tenant_id}):
                purchase_headers.append(doc.get("data", {}))
            
            details_by_trx = {}
            async for doc in self.db.ipos_purchase_dt_staging.find({"tenant_id": self.tenant_id}):
                d = doc.get("data", {})
                trx = d.get("transaction_no")
                if trx not in details_by_trx:
                    details_by_trx[trx] = []
                details_by_trx[trx].append(d)
            
            for header in purchase_headers:
                trx_no = header.get("transaction_no")
                details = details_by_trx.get(trx_no, [])
                
                # Validate
                valid = True
                for detail in details:
                    if detail.get("item_code") not in product_map:
                        valid = False
                        break
                
                if not valid:
                    result["skipped"] += 1
                    continue
                
                try:
                    branch_id = branch_map.get(header.get("warehouse_code"), default_branch)
                    
                    po_items = []
                    for detail in details:
                        product = product_map.get(detail.get("item_code"), {})
                        qty = float(detail.get("quantity", 0) or 0)
                        price = float(detail.get("price", 0) or 0)
                        
                        po_items.append({
                            "product_id": product.get("id"),
                            "product_code": detail.get("item_code"),
                            "product_name": product.get("name", ""),
                            "quantity": qty,
                            "unit_cost": price,
                            "total": float(detail.get("total", 0) or qty * price)
                        })
                    
                    po = {
                        "id": str(uuid.uuid4()),
                        "tenant_id": self.tenant_id,
                        "po_number": trx_no,
                        "branch_id": branch_id,
                        "date": header.get("date"),
                        "supplier_code": header.get("supplier_code"),
                        "purchase_type": header.get("type", "BL"),
                        "subtotal": float(header.get("subtotal", 0) or 0),
                        "discount": float(header.get("discount", 0) or 0),
                        "tax": float(header.get("tax", 0) or 0),
                        "total_amount": float(header.get("total", 0) or 0),
                        "payment_method": header.get("payment_method", "KREDIT"),
                        "status": "COMPLETED",
                        "receive_status": "RECEIVED",
                        "items": po_items,
                        "source_system": "IPOS5",
                        "import_batch_id": self.current_batch_id,
                        "created_at": datetime.now(timezone.utc).isoformat()
                    }
                    
                    await self.db.purchase_orders.insert_one(po)
                    result["imported"] += 1
                    
                    await self._log_action("PURCHASE_IMPORT", trx_no, po)
                    
                except Exception as e:
                    result["errors"].append({
                        "transaction_no": trx_no,
                        "error": str(e)
                    })
            
            result["status"] = "COMPLETED"
            result["completed_at"] = datetime.now(timezone.utc).isoformat()
            
            await self.db.import_batches.update_one(
                {"id": self.current_batch_id},
                {"$set": {
                    "status": "COMPLETED",
                    "completed_at": result["completed_at"],
                    "stats": {
                        "imported": result["imported"],
                        "skipped": result["skipped"]
                    }
                }}
            )
            
        except Exception as e:
            result["status"] = "FAILED"
            result["error"] = str(e)
        
        return result
    
    # ============================================================
    # ROLLBACK METHODS
    # ============================================================
    
    async def rollback_batch(self, batch_id: str) -> Dict:
        """
        ROLLBACK: Undo entire import batch
        
        Deletes all records with matching import_batch_id
        """
        logger.info(f"=== ROLLBACK: Batch {batch_id} ===")
        
        result = {
            "batch_id": batch_id,
            "status": "ROLLING_BACK",
            "deleted": {}
        }
        
        try:
            # Get batch info
            batch = await self.db.import_batches.find_one({"id": batch_id})
            if not batch:
                return {"status": "ERROR", "error": "Batch not found"}
            
            batch_type = batch.get("type")
            
            if batch_type == "SALES_IMPORT":
                # Delete sales invoices
                del_result = await self.db.sales_invoices.delete_many({
                    "import_batch_id": batch_id
                })
                result["deleted"]["sales_invoices"] = del_result.deleted_count
            
            elif batch_type == "PURCHASE_IMPORT":
                # Delete purchase orders
                del_result = await self.db.purchase_orders.delete_many({
                    "import_batch_id": batch_id
                })
                result["deleted"]["purchase_orders"] = del_result.deleted_count
            
            # Update batch status
            await self.db.import_batches.update_one(
                {"id": batch_id},
                {"$set": {
                    "status": "ROLLED_BACK",
                    "rolled_back_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            
            # Log rollback
            await self._log_action("ROLLBACK", batch_id, result["deleted"])
            
            result["status"] = "ROLLED_BACK"
            
        except Exception as e:
            result["status"] = "ROLLBACK_FAILED"
            result["error"] = str(e)
        
        return result
    
    # ============================================================
    # VALIDATION METHODS
    # ============================================================
    
    async def validate_import(self) -> Dict:
        """Validate import results against staging data"""
        logger.info("=== VALIDATING IMPORT ===")
        
        result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tenant_id": self.tenant_id,
            "validations": {}
        }
        
        # Sales validation
        staging_sales_count = await self.db.ipos_sales_hd_staging.count_documents({"tenant_id": self.tenant_id})
        imported_sales_count = await self.db.sales_invoices.count_documents({
            "tenant_id": self.tenant_id,
            "source_system": "IPOS5"
        })
        
        staging_sales_total = 0
        async for doc in self.db.ipos_sales_hd_staging.find({"tenant_id": self.tenant_id}):
            staging_sales_total += float(doc.get("data", {}).get("total", 0) or 0)
        
        imported_sales_total = 0
        async for doc in self.db.sales_invoices.find({"tenant_id": self.tenant_id, "source_system": "IPOS5"}):
            imported_sales_total += float(doc.get("grand_total", 0) or 0)
        
        result["validations"]["sales"] = {
            "staging_count": staging_sales_count,
            "imported_count": imported_sales_count,
            "staging_total": staging_sales_total,
            "imported_total": imported_sales_total,
            "count_match": staging_sales_count == imported_sales_count,
            "total_match": abs(staging_sales_total - imported_sales_total) < 1
        }
        
        # Purchase validation
        staging_purchase_count = await self.db.ipos_purchase_hd_staging.count_documents({"tenant_id": self.tenant_id})
        imported_purchase_count = await self.db.purchase_orders.count_documents({
            "tenant_id": self.tenant_id,
            "source_system": "IPOS5"
        })
        
        staging_purchase_total = 0
        async for doc in self.db.ipos_purchase_hd_staging.find({"tenant_id": self.tenant_id}):
            staging_purchase_total += float(doc.get("data", {}).get("total", 0) or 0)
        
        imported_purchase_total = 0
        async for doc in self.db.purchase_orders.find({"tenant_id": self.tenant_id, "source_system": "IPOS5"}):
            imported_purchase_total += float(doc.get("total_amount", 0) or 0)
        
        result["validations"]["purchases"] = {
            "staging_count": staging_purchase_count,
            "imported_count": imported_purchase_count,
            "staging_total": staging_purchase_total,
            "imported_total": imported_purchase_total,
            "count_match": staging_purchase_count == imported_purchase_count,
            "total_match": abs(staging_purchase_total - imported_purchase_total) < 1
        }
        
        # Overall status
        sales_ok = result["validations"]["sales"]["count_match"] and result["validations"]["sales"]["total_match"]
        purchase_ok = result["validations"]["purchases"]["count_match"] and result["validations"]["purchases"]["total_match"]
        
        result["overall_status"] = "PASS" if (sales_ok and purchase_ok) else "FAIL"
        
        return result
    
    # ============================================================
    # HELPER METHODS
    # ============================================================
    
    async def _log_action(self, action: str, reference: str, data: Any):
        """Log action to audit trail"""
        log = {
            "id": str(uuid.uuid4()),
            "tenant_id": self.tenant_id,
            "batch_id": self.current_batch_id,
            "action": action,
            "reference": reference,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data_summary": str(data)[:500] if data else None
        }
        
        await self.db.ipos_audit_logs.insert_one(log)
    
    async def get_import_batches(self, limit: int = 20) -> List[Dict]:
        """Get list of import batches"""
        cursor = self.db.import_batches.find(
            {"tenant_id": self.tenant_id},
            {"_id": 0}
        ).sort("started_at", -1).limit(limit)
        
        return await cursor.to_list(limit)
    
    async def get_batch_details(self, batch_id: str) -> Optional[Dict]:
        """Get details of specific batch"""
        batch = await self.db.import_batches.find_one(
            {"id": batch_id},
            {"_id": 0}
        )
        return batch
