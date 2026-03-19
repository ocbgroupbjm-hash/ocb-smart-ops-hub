"""
Tenant Rollout Service
======================
Manages rollout of validated blueprint data to other tenants.

IMPORTANT: This service only works AFTER blueprint is locked.
Blueprint ID: BP-20260319004657

Usage:
    rollout = TenantRolloutService(db, source_tenant="ocb_titan")
    
    # Pre-rollout validation
    result = await rollout.validate_source_blueprint("BP-20260319004657")
    
    # Execute rollout to target tenant
    result = await rollout.execute_rollout(target_tenant_id, dry_run=True)
    
    # Validate post-rollout
    result = await rollout.validate_rollout(target_tenant_id)
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class TenantRolloutService:
    """
    Service untuk rollout data dari pilot tenant ke tenant lain.
    
    RULES:
    - Source tenant harus memiliki blueprint yang LOCKED
    - Target tenant harus sudah terdaftar
    - Data rollout mencakup: master data (COA, products, categories, warehouses)
    - Historical transactions TIDAK di-rollout (setiap tenant punya history sendiri)
    """
    
    # Collections yang akan di-rollout (master data only)
    MASTER_COLLECTIONS = [
        "chart_of_accounts",
        "categories", 
        "brands",
        "units",
        "warehouses",
        # Products di-rollout tapi tanpa stock (stock per tenant)
    ]
    
    # Collections yang TIDAK di-rollout (transactional data)
    EXCLUDED_COLLECTIONS = [
        "sales_invoices",
        "purchase_orders", 
        "journals",
        "ap_payments",
        "ar_payments",
        "product_stocks",
        "stock_movements"
    ]
    
    def __init__(self, db, source_tenant: str = "ocb_titan"):
        self.db = db
        self.source_tenant = source_tenant
        self.rollout_id = None
    
    async def validate_source_blueprint(self, blueprint_id: str) -> Dict:
        """
        Validate that source tenant has a locked blueprint.
        """
        logger.info(f"Validating blueprint: {blueprint_id}")
        
        result = {
            "blueprint_id": blueprint_id,
            "status": "VALIDATING",
            "checks": {}
        }
        
        # Check blueprint exists and is locked
        blueprint = await self.db.blueprint_locks.find_one(
            {"blueprint_id": blueprint_id, "tenant_id": self.source_tenant},
            {"_id": 0}
        )
        
        if not blueprint:
            result["status"] = "FAILED"
            result["error"] = f"Blueprint {blueprint_id} not found for tenant {self.source_tenant}"
            return result
        
        if blueprint.get("status") != "LOCKED":
            result["status"] = "FAILED"
            result["error"] = f"Blueprint is not locked. Status: {blueprint.get('status')}"
            return result
        
        result["checks"]["blueprint_exists"] = True
        result["checks"]["blueprint_locked"] = True
        result["checks"]["master_checksum"] = blueprint.get("master_checksum")
        result["checks"]["data_summary"] = blueprint.get("data_summary")
        
        # Verify data integrity by checking counts
        sales_count = await self.db.sales_invoices.count_documents({
            "tenant_id": self.source_tenant, "source_system": "IPOS5"
        })
        expected_sales = blueprint.get("data_summary", {}).get("sales", {}).get("count", 0)
        
        result["checks"]["sales_integrity"] = sales_count == expected_sales
        
        if all(result["checks"].values()):
            result["status"] = "VALID"
        else:
            result["status"] = "INTEGRITY_ERROR"
        
        return result
    
    async def create_target_tenant(self, tenant_id: str, tenant_name: str, admin_email: str) -> Dict:
        """
        Create a new tenant for rollout.
        """
        logger.info(f"Creating target tenant: {tenant_id}")
        
        # Check if tenant already exists
        existing = await self.db.tenants.find_one({"id": tenant_id})
        if existing:
            return {"status": "EXISTS", "tenant_id": tenant_id}
        
        tenant = {
            "id": tenant_id,
            "name": tenant_name,
            "admin_email": admin_email,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "source_blueprint": "BP-20260319004657",
            "status": "PENDING_ROLLOUT"
        }
        
        await self.db.tenants.insert_one(tenant)
        
        return {"status": "CREATED", "tenant_id": tenant_id, "tenant": tenant}
    
    async def execute_rollout(
        self, 
        target_tenant_id: str, 
        dry_run: bool = True,
        include_products: bool = True
    ) -> Dict:
        """
        Execute rollout of master data to target tenant.
        
        Args:
            target_tenant_id: Target tenant ID
            dry_run: If True, only simulate without committing
            include_products: Include product catalog (without stock)
        """
        logger.info(f"{'DRY-RUN' if dry_run else 'EXECUTING'} rollout to {target_tenant_id}")
        
        self.rollout_id = str(uuid.uuid4())
        
        result = {
            "rollout_id": self.rollout_id,
            "source_tenant": self.source_tenant,
            "target_tenant": target_tenant_id,
            "dry_run": dry_run,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "status": "IN_PROGRESS",
            "collections": {},
            "errors": []
        }
        
        try:
            # Rollout each master collection
            for collection_name in self.MASTER_COLLECTIONS:
                coll_result = await self._rollout_collection(
                    collection_name, 
                    target_tenant_id, 
                    dry_run
                )
                result["collections"][collection_name] = coll_result
            
            # Rollout products (special handling - no stock)
            if include_products:
                products_result = await self._rollout_products(target_tenant_id, dry_run)
                result["collections"]["products"] = products_result
            
            result["status"] = "COMPLETED" if not dry_run else "DRY_RUN_COMPLETED"
            result["completed_at"] = datetime.now(timezone.utc).isoformat()
            
            # Save rollout record (only if not dry-run)
            if not dry_run:
                await self.db.tenant_rollouts.insert_one({
                    "rollout_id": self.rollout_id,
                    "source_tenant": self.source_tenant,
                    "target_tenant": target_tenant_id,
                    "blueprint_id": "BP-20260319004657",
                    "status": "COMPLETED",
                    "summary": result["collections"],
                    "created_at": result["started_at"],
                    "completed_at": result["completed_at"]
                })
            
        except Exception as e:
            result["status"] = "FAILED"
            result["error"] = str(e)
            logger.error(f"Rollout failed: {e}")
        
        return result
    
    async def _rollout_collection(
        self, 
        collection_name: str, 
        target_tenant_id: str,
        dry_run: bool
    ) -> Dict:
        """Rollout a single collection."""
        
        source_coll = self.db[collection_name]
        
        # Get source data
        source_docs = await source_coll.find(
            {"tenant_id": self.source_tenant},
            {"_id": 0}
        ).to_list(10000)
        
        if not source_docs:
            return {"count": 0, "status": "NO_DATA"}
        
        # Transform for target tenant
        target_docs = []
        for doc in source_docs:
            new_doc = {**doc}
            new_doc["tenant_id"] = target_tenant_id
            new_doc["id"] = str(uuid.uuid4())  # New ID for target
            new_doc["source_tenant"] = self.source_tenant
            new_doc["rollout_id"] = self.rollout_id
            new_doc["rolled_out_at"] = datetime.now(timezone.utc).isoformat()
            target_docs.append(new_doc)
        
        if dry_run:
            return {
                "count": len(target_docs),
                "status": "DRY_RUN",
                "sample": target_docs[0] if target_docs else None
            }
        
        # Insert to target tenant
        if target_docs:
            await source_coll.insert_many(target_docs)
        
        return {
            "count": len(target_docs),
            "status": "INSERTED"
        }
    
    async def _rollout_products(self, target_tenant_id: str, dry_run: bool) -> Dict:
        """Rollout products without stock data."""
        
        source_products = await self.db.products.find(
            {"tenant_id": self.source_tenant},
            {"_id": 0}
        ).to_list(10000)
        
        if not source_products:
            return {"count": 0, "status": "NO_DATA"}
        
        target_products = []
        for prod in source_products:
            new_prod = {**prod}
            new_prod["tenant_id"] = target_tenant_id
            new_prod["id"] = str(uuid.uuid4())
            new_prod["source_product_id"] = prod.get("id")
            new_prod["source_tenant"] = self.source_tenant
            new_prod["rollout_id"] = self.rollout_id
            new_prod["rolled_out_at"] = datetime.now(timezone.utc).isoformat()
            # Remove stock-related fields
            new_prod.pop("current_stock", None)
            new_prod.pop("stock_value", None)
            target_products.append(new_prod)
        
        if dry_run:
            return {
                "count": len(target_products),
                "status": "DRY_RUN",
                "note": "Products will be created without stock data"
            }
        
        if target_products:
            await self.db.products.insert_many(target_products)
        
        return {
            "count": len(target_products),
            "status": "INSERTED",
            "note": "Stock must be initialized separately for this tenant"
        }
    
    async def validate_rollout(self, target_tenant_id: str) -> Dict:
        """
        Validate rollout to target tenant.
        
        Checks:
        - Master data counts match
        - Data integrity
        - No cross-tenant contamination
        """
        logger.info(f"Validating rollout for tenant: {target_tenant_id}")
        
        result = {
            "target_tenant": target_tenant_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "validations": {},
            "overall_status": "PENDING"
        }
        
        for collection_name in self.MASTER_COLLECTIONS + ["products"]:
            source_count = await self.db[collection_name].count_documents({
                "tenant_id": self.source_tenant
            })
            target_count = await self.db[collection_name].count_documents({
                "tenant_id": target_tenant_id
            })
            
            result["validations"][collection_name] = {
                "source_count": source_count,
                "target_count": target_count,
                "match": source_count == target_count,
                "status": "PASS" if source_count == target_count else "FAIL"
            }
        
        # Check tenant isolation (no IPOS5 transactional data in target)
        for excluded in self.EXCLUDED_COLLECTIONS:
            if excluded in ["product_stocks", "stock_movements"]:
                continue  # These are expected to be different
            
            target_ipos_count = await self.db[excluded].count_documents({
                "tenant_id": target_tenant_id,
                "source_system": "IPOS5"
            })
            
            result["validations"][f"{excluded}_isolation"] = {
                "ipos_records_in_target": target_ipos_count,
                "status": "PASS" if target_ipos_count == 0 else "FAIL"
            }
        
        # Overall status
        all_pass = all(
            v.get("status") == "PASS" 
            for v in result["validations"].values()
        )
        result["overall_status"] = "PASS" if all_pass else "FAIL"
        
        return result
    
    async def get_tenant_isolation_report(self) -> Dict:
        """
        Generate tenant isolation report for current system.
        """
        logger.info("Generating tenant isolation report")
        
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tenants": {},
            "isolation_status": "CHECKING"
        }
        
        # Get all unique tenants
        all_tenants = set()
        
        for coll_name in ["sales_invoices", "purchase_orders", "journals"]:
            tenants = await self.db[coll_name].distinct("tenant_id")
            all_tenants.update(tenants)
        
        # Check each tenant
        for tenant_id in all_tenants:
            if not tenant_id:
                continue
                
            tenant_data = {
                "sales": await self.db.sales_invoices.count_documents({"tenant_id": tenant_id}),
                "purchases": await self.db.purchase_orders.count_documents({"tenant_id": tenant_id}),
                "journals": await self.db.journals.count_documents({"tenant_id": tenant_id}),
                "ap_payments": await self.db.ap_payments.count_documents({"tenant_id": tenant_id}),
                "ar_payments": await self.db.ar_payments.count_documents({"tenant_id": tenant_id}),
                "products": await self.db.products.count_documents({"tenant_id": tenant_id})
            }
            report["tenants"][tenant_id] = tenant_data
        
        # Check for any records without tenant_id (isolation breach)
        orphan_records = {}
        for coll_name in ["sales_invoices", "purchase_orders", "journals"]:
            orphan_count = await self.db[coll_name].count_documents({
                "$or": [{"tenant_id": None}, {"tenant_id": {"$exists": False}}]
            })
            if orphan_count > 0:
                orphan_records[coll_name] = orphan_count
        
        report["orphan_records"] = orphan_records
        report["isolation_status"] = "PASS" if not orphan_records else "BREACH_DETECTED"
        
        return report
