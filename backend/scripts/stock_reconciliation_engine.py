#!/usr/bin/env python3
"""
OCB TITAN ERP - STOCK RECONCILIATION ENGINE
MASTER BLUEPRINT: Production Hardening Phase 20

Engine yang setiap hari memeriksa:
- stock_balance vs SUM(stock_movements)

Jika ada selisih:
- Buat alert
- Buat laporan
- Buat audit log

Scheduler: daily 02:00
Output: /app/reports/stock_reconciliation_report.json
"""

import asyncio
import os
import json
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Dict, List, Any
import uuid

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
REPORTS_DIR = "/app/reports"
ALERT_THRESHOLD = 0  # Any discrepancy should trigger alert


class StockReconciliationEngine:
    def __init__(self, mongo_url: str = MONGO_URL):
        self.mongo_url = mongo_url
        self.client = None
        self.discrepancies = []
        self.alerts = []
        
    async def connect(self):
        self.client = AsyncIOMotorClient(self.mongo_url)
        
    async def disconnect(self):
        if self.client:
            self.client.close()
    
    async def get_stock_from_movements(self, db, product_id: str = None, branch_id: str = None) -> Dict[str, float]:
        """
        Calculate stock balance from stock_movements (SSOT)
        Returns: {product_id: total_quantity}
        """
        # Handle both product_id and item_id fields
        pipeline = [
            {"$addFields": {
                "effective_product_id": {
                    "$ifNull": ["$product_id", "$item_id"]
                }
            }},
            {"$match": {"effective_product_id": {"$ne": None}}},
            {"$group": {
                "_id": {
                    "product_id": "$effective_product_id",
                    "branch_id": "$branch_id"
                },
                "total_qty": {"$sum": "$quantity"},
                "product_name": {"$first": "$product_name"},
                "branch_name": {"$first": "$branch_name"}
            }}
        ]
        
        if product_id:
            pipeline.insert(2, {"$match": {"effective_product_id": product_id}})
        if branch_id:
            pipeline.insert(2, {"$match": {"branch_id": branch_id}})
        
        results = await db["stock_movements"].aggregate(pipeline).to_list(100000)
        
        stock_map = {}
        for r in results:
            pid = r['_id'].get('product_id', '')
            bid = r['_id'].get('branch_id', 'ALL')
            if not pid:
                continue
            key = f"{pid}|{bid}"
            stock_map[key] = {
                "product_id": pid,
                "branch_id": r["_id"].get("branch_id"),
                "product_name": r.get("product_name", ""),
                "branch_name": r.get("branch_name", ""),
                "movement_qty": r["total_qty"]
            }
        
        return stock_map
    
    async def get_stock_from_cache(self, db, product_id: str = None, branch_id: str = None) -> Dict[str, float]:
        """
        Get stock balance from product_stocks cache (if exists)
        Returns: {product_id: cached_quantity}
        """
        match_stage = {}
        if product_id:
            match_stage["product_id"] = product_id
        if branch_id:
            match_stage["branch_id"] = branch_id
        
        # Try product_stocks collection first
        stocks = await db["product_stocks"].find(match_stage, {"_id": 0}).to_list(100000)
        
        if not stocks:
            # Try products collection with stock field
            products = await db["products"].find({}, {"_id": 0, "id": 1, "name": 1, "stock": 1, "sku": 1}).to_list(100000)
            stock_map = {}
            for p in products:
                key = f"{p.get('id', '')}|ALL"
                stock_map[key] = {
                    "product_id": p.get("id", ""),
                    "branch_id": None,
                    "product_name": p.get("name", ""),
                    "cached_qty": p.get("stock", 0) or 0
                }
            return stock_map
        
        stock_map = {}
        for s in stocks:
            key = f"{s.get('product_id', '')}|{s.get('branch_id', 'ALL')}"
            stock_map[key] = {
                "product_id": s.get("product_id", ""),
                "branch_id": s.get("branch_id"),
                "product_name": s.get("product_name", ""),
                "cached_qty": s.get("quantity", 0) or s.get("stock", 0) or 0
            }
        
        return stock_map
    
    async def reconcile_stock(self, db_name: str) -> Dict[str, Any]:
        """
        Main reconciliation function for a single tenant
        Compares stock_movements SSOT with cached stock values
        """
        db = self.client[db_name]
        
        print(f"\n[RECONCILE] Processing tenant: {db_name}")
        
        # Get stock from SSOT (stock_movements)
        movement_stock = await self.get_stock_from_movements(db)
        print(f"  → Found {len(movement_stock)} product/branch combinations in movements")
        
        # Get stock from cache
        cached_stock = await self.get_stock_from_cache(db)
        print(f"  → Found {len(cached_stock)} product/branch combinations in cache")
        
        # Compare and find discrepancies
        discrepancies = []
        all_keys = set(movement_stock.keys()) | set(cached_stock.keys())
        
        for key in all_keys:
            movement_data = movement_stock.get(key, {"movement_qty": 0, "product_name": "", "product_id": key.split("|")[0], "branch_id": None})
            cache_data = cached_stock.get(key, {"cached_qty": 0, "product_id": key.split("|")[0]})
            
            movement_qty = movement_data.get("movement_qty", 0) or 0
            cached_qty = cache_data.get("cached_qty", 0) or 0
            
            difference = movement_qty - cached_qty
            
            product_id = movement_data.get("product_id") or cache_data.get("product_id") or key.split("|")[0]
            
            if abs(difference) > ALERT_THRESHOLD:
                discrepancy = {
                    "product_id": product_id,
                    "product_name": movement_data.get("product_name") or cache_data.get("product_name", ""),
                    "branch_id": movement_data.get("branch_id") or cache_data.get("branch_id"),
                    "branch_name": movement_data.get("branch_name", ""),
                    "movement_qty": movement_qty,
                    "cached_qty": cached_qty,
                    "difference": difference,
                    "status": "DISCREPANCY" if difference != 0 else "OK"
                }
                discrepancies.append(discrepancy)
        
        return {
            "tenant": db_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_products_checked": len(all_keys),
            "discrepancies_found": len(discrepancies),
            "discrepancies": discrepancies,
            "status": "ALERT" if discrepancies else "OK"
        }
    
    async def create_alert(self, db, discrepancy: Dict, tenant: str):
        """Create alert for stock discrepancy"""
        alert = {
            "id": str(uuid.uuid4()),
            "type": "stock_discrepancy",
            "severity": "high" if abs(discrepancy["difference"]) > 10 else "medium",
            "tenant_id": tenant,
            "product_id": discrepancy["product_id"],
            "product_name": discrepancy["product_name"],
            "branch_id": discrepancy.get("branch_id"),
            "message": f"Stock discrepancy detected: {discrepancy['product_name']} - Movement: {discrepancy['movement_qty']}, Cache: {discrepancy['cached_qty']}, Diff: {discrepancy['difference']}",
            "data": discrepancy,
            "acknowledged": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db["system_alerts"].insert_one(alert)
        self.alerts.append(alert)
        
        return alert
    
    async def create_audit_log(self, db, action: str, details: Dict, tenant: str):
        """Create audit log entry for reconciliation"""
        log_entry = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant,
            "user_id": "SYSTEM",
            "user_name": "Stock Reconciliation Engine",
            "action": action,
            "module": "stock_reconciliation",
            "entity_type": "inventory",
            "entity_id": details.get("product_id", ""),
            "before_data": None,
            "after_data": details,
            "description": f"Stock reconciliation: {action}",
            "ip_address": "localhost",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db["audit_logs"].insert_one(log_entry)
        
        return log_entry
    
    async def run_reconciliation(self, tenants: List[str] = None) -> Dict:
        """
        Run full stock reconciliation for all tenants
        """
        await self.connect()
        
        timestamp = datetime.now(timezone.utc)
        print("="*70)
        print("OCB TITAN - STOCK RECONCILIATION ENGINE")
        print(f"Timestamp: {timestamp.isoformat()}")
        print("="*70)
        
        # Get tenant list
        if not tenants:
            businesses_file = "/app/backend/data/businesses.json"
            if os.path.exists(businesses_file):
                with open(businesses_file, "r") as f:
                    businesses = json.load(f)
                    tenants = [b["db_name"] for b in businesses if b.get("is_active") and not b.get("is_test")]
            else:
                tenants = ["ocb_titan"]
        
        print(f"Tenants to reconcile: {tenants}")
        
        # Run reconciliation for each tenant
        all_results = []
        total_discrepancies = 0
        
        for tenant in tenants:
            try:
                result = await self.reconcile_stock(tenant)
                all_results.append(result)
                
                db = self.client[tenant]
                
                # Create alerts and audit logs for discrepancies
                for disc in result.get("discrepancies", []):
                    await self.create_alert(db, disc, tenant)
                    await self.create_audit_log(db, "STOCK_DISCREPANCY_DETECTED", disc, tenant)
                    total_discrepancies += 1
                
                # Log reconciliation run
                await self.create_audit_log(db, "STOCK_RECONCILIATION_RUN", {
                    "tenant": tenant,
                    "products_checked": result["total_products_checked"],
                    "discrepancies_found": result["discrepancies_found"],
                    "status": result["status"]
                }, tenant)
                
            except Exception as e:
                print(f"  ❌ Error reconciling {tenant}: {e}")
                all_results.append({
                    "tenant": tenant,
                    "status": "ERROR",
                    "error": str(e)
                })
        
        await self.disconnect()
        
        # Build final report
        report = {
            "report_id": f"STOCKREC-{timestamp.strftime('%Y%m%d_%H%M%S')}",
            "timestamp": timestamp.isoformat(),
            "scheduler": "daily_02:00",
            "tenants_processed": len(tenants),
            "total_discrepancies": total_discrepancies,
            "alerts_generated": len(self.alerts),
            "overall_status": "ALERT" if total_discrepancies > 0 else "OK",
            "tenant_results": all_results
        }
        
        # Save report
        os.makedirs(REPORTS_DIR, exist_ok=True)
        report_path = f"{REPORTS_DIR}/stock_reconciliation_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2, default=str)
        
        # Also save timestamped report
        timestamped_path = f"{REPORTS_DIR}/stock_reconciliation_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        with open(timestamped_path, "w") as f:
            json.dump(report, f, indent=2, default=str)
        
        # Print summary
        print("\n" + "="*70)
        print("STOCK RECONCILIATION SUMMARY")
        print("="*70)
        print(f"Tenants Processed: {len(tenants)}")
        print(f"Total Discrepancies: {total_discrepancies}")
        print(f"Alerts Generated: {len(self.alerts)}")
        print(f"Overall Status: {report['overall_status']}")
        print(f"Report saved: {report_path}")
        print("="*70)
        
        return report
    
    async def fix_discrepancies(self, db_name: str, auto_fix: bool = False) -> Dict:
        """
        Fix stock discrepancies by updating cache to match SSOT
        Only runs if auto_fix is True (requires manual approval)
        """
        if not auto_fix:
            return {"status": "SKIPPED", "message": "Auto-fix disabled. Manual approval required."}
        
        await self.connect()
        db = self.client[db_name]
        
        # Get discrepancies
        result = await self.reconcile_stock(db_name)
        
        fixed = []
        for disc in result.get("discrepancies", []):
            # Update product_stocks cache to match SSOT
            await db["product_stocks"].update_one(
                {
                    "product_id": disc["product_id"],
                    "branch_id": disc.get("branch_id")
                },
                {
                    "$set": {
                        "quantity": disc["movement_qty"],
                        "last_reconciled": datetime.now(timezone.utc).isoformat()
                    }
                },
                upsert=True
            )
            
            # Also update products collection if no branch
            if not disc.get("branch_id"):
                await db["products"].update_one(
                    {"id": disc["product_id"]},
                    {"$set": {"stock": disc["movement_qty"]}}
                )
            
            # Log the fix
            await self.create_audit_log(db, "STOCK_DISCREPANCY_FIXED", {
                **disc,
                "action": "cache_updated_to_ssot"
            }, db_name)
            
            fixed.append(disc)
        
        await self.disconnect()
        
        return {
            "status": "FIXED",
            "tenant": db_name,
            "discrepancies_fixed": len(fixed),
            "details": fixed
        }


# ==================== SCHEDULER FUNCTIONS ====================

async def scheduled_reconciliation():
    """Function to be called by scheduler at 02:00 daily"""
    engine = StockReconciliationEngine()
    return await engine.run_reconciliation()


# ==================== CLI ====================

async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="OCB TITAN Stock Reconciliation Engine")
    parser.add_argument("--tenant", type=str, help="Specific tenant to reconcile")
    parser.add_argument("--all", action="store_true", help="Reconcile all tenants")
    parser.add_argument("--fix", action="store_true", help="Auto-fix discrepancies (USE WITH CAUTION)")
    
    args = parser.parse_args()
    
    engine = StockReconciliationEngine()
    
    if args.fix and args.tenant:
        result = await engine.fix_discrepancies(args.tenant, auto_fix=True)
    elif args.tenant:
        result = await engine.run_reconciliation([args.tenant])
    else:
        result = await engine.run_reconciliation()
    
    return result


if __name__ == "__main__":
    asyncio.run(main())
