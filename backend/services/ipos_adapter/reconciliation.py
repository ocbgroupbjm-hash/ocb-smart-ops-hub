# iPOS 5 Reconciliation Engine
# Compares iPOS staging data against OCB TITAN production data
# Identifies mismatches and generates reconciliation reports

import uuid
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal, ROUND_HALF_UP
from database import get_db
import logging

logger = logging.getLogger(__name__)


class ReconciliationEngine:
    """
    Reconciliation engine for iPOS 5 to OCB TITAN data validation
    
    RECONCILIATION CHECKS:
    1. Stock qty per item
    2. Stock valuation (qty * cost)
    3. Inventory value vs Accounting inventory account
    4. Sales total
    5. Purchase total
    6. AR/AP balance
    7. Journal balance (debit = credit)
    8. Master data consistency
    
    OUTPUT:
    - MATCH: Data matches within tolerance
    - MISMATCH: Data differs beyond tolerance
    - MISSING: Data exists in source but not target (or vice versa)
    """
    
    # Tolerance for numeric comparisons (0.01 = 1 cent)
    TOLERANCE = Decimal("0.01")
    
    # Staging collection names
    STAGING_COLLECTIONS = {
        "items": "ipos_items_staging",
        "stock": "ipos_stock_staging",
        "sales_hd": "ipos_sales_hd_staging",
        "sales_dt": "ipos_sales_dt_staging",
        "purchase_hd": "ipos_purchase_hd_staging",
        "purchase_dt": "ipos_purchase_dt_staging",
        "journals": "ipos_journal_staging",
        "accounts": "ipos_accounts_staging",
        "suppliers": "ipos_suppliers_staging",
        "customers": "ipos_customers_staging",
    }
    
    # OCB TITAN production collection names
    TITAN_COLLECTIONS = {
        "items": "products",
        "stock": "inventory",
        "sales": "sales",
        "purchases": "purchase_orders",
        "journals": "journals",
        "accounts": "chart_of_accounts",
        "suppliers": "suppliers",
        "customers": "customers",
    }
    
    def __init__(self, tenant_id: str = "ocb_titan"):
        self.tenant_id = tenant_id
        self.db = get_db()
        self.results = {}
        self.mismatches = []
        self.summary = {}
    
    # ============================================================
    # MAIN RECONCILIATION METHODS
    # ============================================================
    
    async def run_full_reconciliation(self, batch_id: str = None) -> Dict:
        """
        Run all reconciliation checks
        
        Returns:
            {
                "batch_id": str,
                "timestamp": str,
                "overall_status": "PASS" | "FAIL",
                "checks": {...},
                "mismatches": [...],
                "summary": {...}
            }
        """
        logger.info("=== RUNNING FULL RECONCILIATION ===")
        logger.info(f"Tenant: {self.tenant_id}, Batch: {batch_id}")
        
        start_time = datetime.now(timezone.utc)
        
        results = {
            "batch_id": batch_id,
            "tenant_id": self.tenant_id,
            "timestamp": start_time.isoformat(),
            "overall_status": "PASS",
            "checks": {},
            "mismatches": [],
            "summary": {}
        }
        
        try:
            # 1. Item/Stock count reconciliation
            logger.info("Check 1: Stock Quantities...")
            stock_check = await self.reconcile_stock_quantities(batch_id)
            results["checks"]["stock_quantities"] = stock_check
            
            # 2. Stock valuation reconciliation
            logger.info("Check 2: Stock Valuation...")
            valuation_check = await self.reconcile_stock_valuation(batch_id)
            results["checks"]["stock_valuation"] = valuation_check
            
            # 3. Sales total reconciliation
            logger.info("Check 3: Sales Totals...")
            sales_check = await self.reconcile_sales_totals(batch_id)
            results["checks"]["sales_totals"] = sales_check
            
            # 4. Purchase total reconciliation
            logger.info("Check 4: Purchase Totals...")
            purchase_check = await self.reconcile_purchase_totals(batch_id)
            results["checks"]["purchase_totals"] = purchase_check
            
            # 5. Journal balance check
            logger.info("Check 5: Journal Balance...")
            journal_check = await self.reconcile_journal_balance(batch_id)
            results["checks"]["journal_balance"] = journal_check
            
            # 6. Inventory vs Accounting reconciliation
            logger.info("Check 6: Inventory vs Accounting...")
            inv_acc_check = await self.reconcile_inventory_vs_accounting(batch_id)
            results["checks"]["inventory_vs_accounting"] = inv_acc_check
            
            # 7. Master data count reconciliation
            logger.info("Check 7: Master Data...")
            master_check = await self.reconcile_master_data(batch_id)
            results["checks"]["master_data"] = master_check
            
            # Collect all mismatches
            for check_name, check_result in results["checks"].items():
                if check_result.get("status") == "FAIL":
                    results["overall_status"] = "FAIL"
                
                if check_result.get("mismatches"):
                    for m in check_result["mismatches"]:
                        m["check_type"] = check_name
                    results["mismatches"].extend(check_result["mismatches"])
            
            # Generate summary
            results["summary"] = self._generate_summary(results)
            
            # Save results to database
            await self._save_results(results)
            
        except Exception as e:
            logger.error(f"Reconciliation failed: {e}")
            results["overall_status"] = "ERROR"
            results["error"] = str(e)
        
        results["duration_seconds"] = (datetime.now(timezone.utc) - start_time).total_seconds()
        
        logger.info(f"=== RECONCILIATION COMPLETE: {results['overall_status']} ===")
        
        return results
    
    # ============================================================
    # INDIVIDUAL RECONCILIATION CHECKS
    # ============================================================
    
    async def reconcile_stock_quantities(self, batch_id: str = None) -> Dict:
        """
        Reconcile stock quantities per item
        
        Compares:
        - iPOS: tbl_itemstok (stok column)
        - OCB TITAN: inventory collection (quantity field)
        """
        result = {
            "check_name": "Stock Quantities",
            "status": "PASS",
            "ipos_total": 0,
            "titan_total": 0,
            "difference": 0,
            "item_count": 0,
            "mismatches": []
        }
        
        try:
            # Get iPOS stock data from staging
            staging_coll = self.db[self.STAGING_COLLECTIONS["stock"]]
            query = {"tenant_id": self.tenant_id}
            if batch_id:
                query["batch_id"] = batch_id
            
            ipos_stocks = {}
            async for doc in staging_coll.find(query):
                data = doc.get("data", {})
                item_code = data.get("item_code")
                qty = float(data.get("quantity", 0) or 0)
                if item_code:
                    ipos_stocks[item_code] = ipos_stocks.get(item_code, 0) + qty
            
            result["ipos_total"] = sum(ipos_stocks.values())
            result["item_count"] = len(ipos_stocks)
            
            # Get OCB TITAN stock data
            titan_coll = self.db[self.TITAN_COLLECTIONS["stock"]]
            titan_stocks = {}
            async for doc in titan_coll.find({"tenant_id": self.tenant_id}):
                item_code = doc.get("product_code") or doc.get("item_code")
                qty = float(doc.get("quantity", 0) or 0)
                if item_code:
                    titan_stocks[item_code] = titan_stocks.get(item_code, 0) + qty
            
            result["titan_total"] = sum(titan_stocks.values())
            
            # Compare item by item
            all_items = set(ipos_stocks.keys()) | set(titan_stocks.keys())
            
            for item_code in all_items:
                ipos_qty = ipos_stocks.get(item_code, 0)
                titan_qty = titan_stocks.get(item_code, 0)
                diff = abs(ipos_qty - titan_qty)
                
                if diff > float(self.TOLERANCE):
                    result["mismatches"].append({
                        "item_code": item_code,
                        "ipos_qty": ipos_qty,
                        "titan_qty": titan_qty,
                        "difference": ipos_qty - titan_qty,
                        "status": "MISMATCH"
                    })
            
            result["difference"] = result["ipos_total"] - result["titan_total"]
            
            if result["mismatches"]:
                result["status"] = "FAIL"
                result["mismatch_count"] = len(result["mismatches"])
            
        except Exception as e:
            result["status"] = "ERROR"
            result["error"] = str(e)
        
        return result
    
    async def reconcile_stock_valuation(self, batch_id: str = None) -> Dict:
        """
        Reconcile stock valuation (qty * unit cost)
        
        Compares total inventory value
        """
        result = {
            "check_name": "Stock Valuation",
            "status": "PASS",
            "ipos_value": 0,
            "titan_value": 0,
            "difference": 0,
            "mismatches": []
        }
        
        try:
            # Get iPOS stock with HPP from staging
            staging_coll = self.db[self.STAGING_COLLECTIONS["stock"]]
            query = {"tenant_id": self.tenant_id}
            if batch_id:
                query["batch_id"] = batch_id
            
            ipos_values = {}
            async for doc in staging_coll.find(query):
                data = doc.get("data", {})
                item_code = data.get("item_code")
                qty = float(data.get("quantity", 0) or 0)
                hpp = float(data.get("hpp_base", 0) or 0)
                value = qty * hpp
                if item_code:
                    ipos_values[item_code] = ipos_values.get(item_code, 0) + value
            
            result["ipos_value"] = sum(ipos_values.values())
            
            # Get OCB TITAN inventory values
            titan_coll = self.db[self.TITAN_COLLECTIONS["stock"]]
            titan_values = {}
            async for doc in titan_coll.find({"tenant_id": self.tenant_id}):
                item_code = doc.get("product_code") or doc.get("item_code")
                qty = float(doc.get("quantity", 0) or 0)
                cost = float(doc.get("unit_cost", 0) or doc.get("average_cost", 0) or 0)
                value = qty * cost
                if item_code:
                    titan_values[item_code] = titan_values.get(item_code, 0) + value
            
            result["titan_value"] = sum(titan_values.values())
            result["difference"] = result["ipos_value"] - result["titan_value"]
            
            # Check for significant valuation differences
            all_items = set(ipos_values.keys()) | set(titan_values.keys())
            
            for item_code in all_items:
                ipos_val = ipos_values.get(item_code, 0)
                titan_val = titan_values.get(item_code, 0)
                diff = abs(ipos_val - titan_val)
                
                if diff > 100:  # Flag items with >100 difference
                    result["mismatches"].append({
                        "item_code": item_code,
                        "ipos_value": ipos_val,
                        "titan_value": titan_val,
                        "difference": ipos_val - titan_val,
                        "status": "VALUE_MISMATCH"
                    })
            
            if abs(result["difference"]) > 1000 or result["mismatches"]:
                result["status"] = "FAIL"
                result["mismatch_count"] = len(result["mismatches"])
            
        except Exception as e:
            result["status"] = "ERROR"
            result["error"] = str(e)
        
        return result
    
    async def reconcile_sales_totals(self, batch_id: str = None) -> Dict:
        """Reconcile total sales"""
        result = {
            "check_name": "Sales Totals",
            "status": "PASS",
            "ipos_total": 0,
            "ipos_count": 0,
            "titan_total": 0,
            "titan_count": 0,
            "difference": 0,
            "mismatches": []
        }
        
        try:
            # Get iPOS sales from staging
            staging_coll = self.db[self.STAGING_COLLECTIONS["sales_hd"]]
            query = {"tenant_id": self.tenant_id}
            if batch_id:
                query["batch_id"] = batch_id
            
            ipos_sales = {}
            async for doc in staging_coll.find(query):
                data = doc.get("data", {})
                trx_no = data.get("transaction_no")
                total = float(data.get("total", 0) or 0)
                if trx_no:
                    ipos_sales[trx_no] = total
            
            result["ipos_total"] = sum(ipos_sales.values())
            result["ipos_count"] = len(ipos_sales)
            
            # Get OCB TITAN sales
            titan_coll = self.db[self.TITAN_COLLECTIONS["sales"]]
            titan_sales = {}
            async for doc in titan_coll.find({"tenant_id": self.tenant_id}):
                trx_no = doc.get("transaction_no") or doc.get("invoice_number")
                total = float(doc.get("total", 0) or doc.get("grand_total", 0) or 0)
                if trx_no:
                    titan_sales[trx_no] = total
            
            result["titan_total"] = sum(titan_sales.values())
            result["titan_count"] = len(titan_sales)
            result["difference"] = result["ipos_total"] - result["titan_total"]
            
            # Find missing transactions
            ipos_only = set(ipos_sales.keys()) - set(titan_sales.keys())
            titan_only = set(titan_sales.keys()) - set(ipos_sales.keys())
            
            for trx_no in list(ipos_only)[:50]:
                result["mismatches"].append({
                    "transaction_no": trx_no,
                    "ipos_total": ipos_sales[trx_no],
                    "titan_total": 0,
                    "status": "MISSING_IN_TITAN"
                })
            
            for trx_no in list(titan_only)[:50]:
                result["mismatches"].append({
                    "transaction_no": trx_no,
                    "ipos_total": 0,
                    "titan_total": titan_sales[trx_no],
                    "status": "MISSING_IN_IPOS"
                })
            
            if abs(result["difference"]) > 1000 or result["mismatches"]:
                result["status"] = "FAIL"
                result["mismatch_count"] = len(result["mismatches"])
            
        except Exception as e:
            result["status"] = "ERROR"
            result["error"] = str(e)
        
        return result
    
    async def reconcile_purchase_totals(self, batch_id: str = None) -> Dict:
        """Reconcile total purchases"""
        result = {
            "check_name": "Purchase Totals",
            "status": "PASS",
            "ipos_total": 0,
            "ipos_count": 0,
            "titan_total": 0,
            "titan_count": 0,
            "difference": 0,
            "mismatches": []
        }
        
        try:
            # Get iPOS purchases from staging
            staging_coll = self.db[self.STAGING_COLLECTIONS["purchase_hd"]]
            query = {"tenant_id": self.tenant_id}
            if batch_id:
                query["batch_id"] = batch_id
            
            ipos_purchases = {}
            async for doc in staging_coll.find(query):
                data = doc.get("data", {})
                trx_no = data.get("transaction_no")
                total = float(data.get("total", 0) or 0)
                if trx_no:
                    ipos_purchases[trx_no] = total
            
            result["ipos_total"] = sum(ipos_purchases.values())
            result["ipos_count"] = len(ipos_purchases)
            
            # Get OCB TITAN purchases
            titan_coll = self.db[self.TITAN_COLLECTIONS["purchases"]]
            titan_purchases = {}
            async for doc in titan_coll.find({"tenant_id": self.tenant_id}):
                trx_no = doc.get("po_number") or doc.get("transaction_no")
                total = float(doc.get("total_amount", 0) or doc.get("total", 0) or 0)
                if trx_no:
                    titan_purchases[trx_no] = total
            
            result["titan_total"] = sum(titan_purchases.values())
            result["titan_count"] = len(titan_purchases)
            result["difference"] = result["ipos_total"] - result["titan_total"]
            
            if abs(result["difference"]) > 1000:
                result["status"] = "FAIL"
            
        except Exception as e:
            result["status"] = "ERROR"
            result["error"] = str(e)
        
        return result
    
    async def reconcile_journal_balance(self, batch_id: str = None) -> Dict:
        """
        Check journal balance (total debit = total credit)
        
        CRITICAL: If journal doesn't balance, accounting data is corrupt
        """
        result = {
            "check_name": "Journal Balance",
            "status": "PASS",
            "ipos_debit": 0,
            "ipos_credit": 0,
            "ipos_balance": 0,
            "titan_debit": 0,
            "titan_credit": 0,
            "titan_balance": 0,
            "mismatches": []
        }
        
        try:
            # Get iPOS journals from staging
            staging_coll = self.db[self.STAGING_COLLECTIONS["journals"]]
            query = {"tenant_id": self.tenant_id}
            if batch_id:
                query["batch_id"] = batch_id
            
            ipos_debit = 0
            ipos_credit = 0
            async for doc in staging_coll.find(query):
                data = doc.get("data", {})
                debit = float(data.get("debit", 0) or 0)
                credit = float(data.get("credit", 0) or 0)
                ipos_debit += debit
                ipos_credit += credit
            
            result["ipos_debit"] = ipos_debit
            result["ipos_credit"] = ipos_credit
            result["ipos_balance"] = ipos_debit - ipos_credit
            
            # Get OCB TITAN journals
            titan_coll = self.db[self.TITAN_COLLECTIONS["journals"]]
            titan_debit = 0
            titan_credit = 0
            async for doc in titan_coll.find({"tenant_id": self.tenant_id}):
                # Handle both single journal and journal with lines
                if "lines" in doc:
                    for line in doc["lines"]:
                        titan_debit += float(line.get("debit", 0) or 0)
                        titan_credit += float(line.get("credit", 0) or 0)
                else:
                    titan_debit += float(doc.get("debit", 0) or 0)
                    titan_credit += float(doc.get("credit", 0) or 0)
            
            result["titan_debit"] = titan_debit
            result["titan_credit"] = titan_credit
            result["titan_balance"] = titan_debit - titan_credit
            
            # Check if journals balance
            if abs(result["ipos_balance"]) > float(self.TOLERANCE):
                result["mismatches"].append({
                    "source": "IPOS",
                    "issue": "UNBALANCED_JOURNAL",
                    "debit": ipos_debit,
                    "credit": ipos_credit,
                    "difference": result["ipos_balance"]
                })
                result["status"] = "FAIL"
            
            if abs(result["titan_balance"]) > float(self.TOLERANCE):
                result["mismatches"].append({
                    "source": "TITAN",
                    "issue": "UNBALANCED_JOURNAL",
                    "debit": titan_debit,
                    "credit": titan_credit,
                    "difference": result["titan_balance"]
                })
                result["status"] = "FAIL"
            
        except Exception as e:
            result["status"] = "ERROR"
            result["error"] = str(e)
        
        return result
    
    async def reconcile_inventory_vs_accounting(self, batch_id: str = None) -> Dict:
        """
        CRITICAL CHECK: Inventory value must match Accounting inventory account
        
        Compares:
        - Total stock valuation (qty * cost)
        - Inventory account balance in Chart of Accounts
        """
        result = {
            "check_name": "Inventory vs Accounting",
            "status": "PASS",
            "inventory_value": 0,
            "accounting_balance": 0,
            "difference": 0,
            "inventory_accounts": [],
            "mismatches": []
        }
        
        try:
            # Calculate inventory value from stock
            staging_stock = self.db[self.STAGING_COLLECTIONS["stock"]]
            query = {"tenant_id": self.tenant_id}
            if batch_id:
                query["batch_id"] = batch_id
            
            inventory_value = 0
            async for doc in staging_stock.find(query):
                data = doc.get("data", {})
                qty = float(data.get("quantity", 0) or 0)
                hpp = float(data.get("hpp_base", 0) or 0)
                inventory_value += qty * hpp
            
            result["inventory_value"] = inventory_value
            
            # Find inventory accounts in journals
            # Typically inventory accounts start with '1.1.4' or similar
            staging_journals = self.db[self.STAGING_COLLECTIONS["journals"]]
            
            inventory_balance = 0
            inventory_accounts = set()
            
            async for doc in staging_journals.find(query):
                data = doc.get("data", {})
                account_code = data.get("account_code", "")
                
                # Check if this is an inventory account (starts with common inventory prefixes)
                if account_code and (
                    account_code.startswith("1.1.4") or 
                    account_code.startswith("114") or
                    account_code.startswith("1-1400") or
                    "persediaan" in (data.get("description", "") or "").lower() or
                    "inventory" in (data.get("description", "") or "").lower()
                ):
                    inventory_accounts.add(account_code)
                    debit = float(data.get("debit", 0) or 0)
                    credit = float(data.get("credit", 0) or 0)
                    inventory_balance += (debit - credit)
            
            result["accounting_balance"] = inventory_balance
            result["inventory_accounts"] = list(inventory_accounts)
            result["difference"] = inventory_value - inventory_balance
            
            # Check for significant difference
            if abs(result["difference"]) > 1000:
                result["mismatches"].append({
                    "issue": "INVENTORY_ACCOUNTING_MISMATCH",
                    "inventory_value": inventory_value,
                    "accounting_balance": inventory_balance,
                    "difference": result["difference"],
                    "analysis": "Stock value does not match inventory account balance"
                })
                result["status"] = "FAIL"
            
        except Exception as e:
            result["status"] = "ERROR"
            result["error"] = str(e)
        
        return result
    
    async def reconcile_master_data(self, batch_id: str = None) -> Dict:
        """Reconcile master data counts"""
        result = {
            "check_name": "Master Data",
            "status": "PASS",
            "counts": {},
            "mismatches": []
        }
        
        try:
            # Items
            staging_items = self.db[self.STAGING_COLLECTIONS["items"]]
            query = {"tenant_id": self.tenant_id}
            if batch_id:
                query["batch_id"] = batch_id
            
            ipos_items = await staging_items.count_documents(query)
            
            titan_items = self.db[self.TITAN_COLLECTIONS["items"]]
            titan_item_count = await titan_items.count_documents({"tenant_id": self.tenant_id})
            
            result["counts"]["items"] = {
                "ipos": ipos_items,
                "titan": titan_item_count,
                "difference": ipos_items - titan_item_count
            }
            
            # Suppliers
            staging_suppliers = self.db[self.STAGING_COLLECTIONS["suppliers"]]
            ipos_suppliers = await staging_suppliers.count_documents(query)
            
            titan_suppliers = self.db[self.TITAN_COLLECTIONS["suppliers"]]
            titan_supplier_count = await titan_suppliers.count_documents({"tenant_id": self.tenant_id})
            
            result["counts"]["suppliers"] = {
                "ipos": ipos_suppliers,
                "titan": titan_supplier_count,
                "difference": ipos_suppliers - titan_supplier_count
            }
            
            # Customers
            staging_customers = self.db[self.STAGING_COLLECTIONS["customers"]]
            ipos_customers = await staging_customers.count_documents(query)
            
            titan_customers = self.db[self.TITAN_COLLECTIONS["customers"]]
            titan_customer_count = await titan_customers.count_documents({"tenant_id": self.tenant_id})
            
            result["counts"]["customers"] = {
                "ipos": ipos_customers,
                "titan": titan_customer_count,
                "difference": ipos_customers - titan_customer_count
            }
            
            # Chart of Accounts
            staging_accounts = self.db[self.STAGING_COLLECTIONS["accounts"]]
            ipos_accounts = await staging_accounts.count_documents(query)
            
            titan_accounts = self.db[self.TITAN_COLLECTIONS["accounts"]]
            titan_account_count = await titan_accounts.count_documents({"tenant_id": self.tenant_id})
            
            result["counts"]["accounts"] = {
                "ipos": ipos_accounts,
                "titan": titan_account_count,
                "difference": ipos_accounts - titan_account_count
            }
            
        except Exception as e:
            result["status"] = "ERROR"
            result["error"] = str(e)
        
        return result
    
    # ============================================================
    # HELPER METHODS
    # ============================================================
    
    def _generate_summary(self, results: Dict) -> Dict:
        """Generate human-readable summary"""
        checks = results.get("checks", {})
        
        passed = sum(1 for c in checks.values() if c.get("status") == "PASS")
        failed = sum(1 for c in checks.values() if c.get("status") == "FAIL")
        errors = sum(1 for c in checks.values() if c.get("status") == "ERROR")
        
        summary = {
            "total_checks": len(checks),
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "critical_issues": [],
            "recommendations": []
        }
        
        # Identify critical issues
        if checks.get("journal_balance", {}).get("status") == "FAIL":
            summary["critical_issues"].append("JOURNAL TIDAK BALANCE - Data akuntansi corrupt")
            summary["recommendations"].append("Periksa semua jurnal dan fix entries yang tidak balance")
        
        if checks.get("inventory_vs_accounting", {}).get("status") == "FAIL":
            diff = checks.get("inventory_vs_accounting", {}).get("difference", 0)
            summary["critical_issues"].append(f"INVENTORY vs ACCOUNTING MISMATCH: Selisih Rp {diff:,.2f}")
            summary["recommendations"].append("Lakukan stock opname dan adjustment jurnal persediaan")
        
        stock_check = checks.get("stock_quantities", {})
        if stock_check.get("status") == "FAIL":
            summary["critical_issues"].append(f"STOCK MISMATCH: {stock_check.get('mismatch_count', 0)} item berbeda")
            summary["recommendations"].append("Import ulang data stock dari iPOS ke OCB TITAN")
        
        return summary
    
    async def _save_results(self, results: Dict):
        """Save reconciliation results to database"""
        results_coll = self.db["ipos_reconciliation_results"]
        
        doc = {
            "id": str(uuid.uuid4()),
            "tenant_id": self.tenant_id,
            **results
        }
        
        await results_coll.insert_one(doc)
        logger.info(f"Saved reconciliation results: {doc['id']}")
    
    async def get_latest_results(self) -> Optional[Dict]:
        """Get latest reconciliation results"""
        results_coll = self.db["ipos_reconciliation_results"]
        
        cursor = results_coll.find(
            {"tenant_id": self.tenant_id}
        ).sort("timestamp", -1).limit(1)
        
        results = await cursor.to_list(1)
        if results:
            result = results[0]
            result.pop("_id", None)
            return result
        return None
    
    async def get_all_results(self, limit: int = 10) -> List[Dict]:
        """Get all reconciliation results"""
        results_coll = self.db["ipos_reconciliation_results"]
        
        cursor = results_coll.find(
            {"tenant_id": self.tenant_id},
            {"_id": 0}
        ).sort("timestamp", -1).limit(limit)
        
        return await cursor.to_list(limit)
