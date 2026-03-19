# iPOS 5 Staging Service
# Manages staging collections for iPOS data before import to OCB TITAN
# TENANT-AWARE + AUDIT-READY

import uuid
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from database import get_db
import logging

logger = logging.getLogger(__name__)


class StagingService:
    """
    Staging layer for iPOS 5 data migration
    
    All data from iPOS goes through staging before import to OCB TITAN final collections.
    
    RULES:
    - Staging is separate from final collections
    - All records have source_record_id, source_system, import_batch_id
    - All records are tenant-aware
    - All records have timestamps and checksums for idempotency
    """
    
    # Staging collection names
    COLLECTIONS = {
        "items": "ipos_items_staging",
        "categories": "ipos_categories_staging",
        "brands": "ipos_brands_staging",
        "units": "ipos_units_staging",
        "suppliers": "ipos_suppliers_staging",
        "customers": "ipos_customers_staging",
        "warehouses": "ipos_warehouses_staging",
        "stock_positions": "ipos_stock_staging",
        "chart_of_accounts": "ipos_accounts_staging",
        "journals": "ipos_journal_staging",
        "sales_headers": "ipos_sales_hd_staging",
        "sales_details": "ipos_sales_dt_staging",
        "purchase_headers": "ipos_purchase_hd_staging",
        "purchase_details": "ipos_purchase_dt_staging",
        "ar_balances": "ipos_ar_staging",
        "ap_balances": "ipos_ap_staging",
        "ap_payment_headers": "ipos_ap_payment_hd_staging",
        "ap_payment_details": "ipos_ap_payment_dt_staging",
        "ar_payment_headers": "ipos_ar_payment_hd_staging",
        "ar_payment_details": "ipos_ar_payment_dt_staging",
        "batches": "ipos_import_batches",
        "reconciliation": "ipos_reconciliation_results",
        "audit": "ipos_audit_logs"
    }
    
    def __init__(self, tenant_id: str = "ocb_titan"):
        self.tenant_id = tenant_id
        self.db = get_db()
    
    def _get_collection(self, name: str):
        """Get staging collection by name"""
        if name not in self.COLLECTIONS:
            raise ValueError(f"Unknown staging collection: {name}")
        return self.db[self.COLLECTIONS[name]]
    
    def _compute_checksum(self, data: Dict) -> str:
        """Compute checksum for idempotency"""
        # Remove volatile fields for checksum
        clean_data = {k: v for k, v in data.items() 
                      if k not in ['_id', 'imported_at', 'batch_id', 'staging_id', 'raw_data']}
        data_str = str(sorted(clean_data.items()))
        return hashlib.md5(data_str.encode()).hexdigest()
    
    async def create_batch(self, source_file: str, description: str = "", user_id: str = "") -> Dict:
        """Create a new import batch"""
        batch_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        batch = {
            "batch_id": batch_id,
            "tenant_id": self.tenant_id,
            "source_file": source_file,
            "source_system": "IPOS5_ULTIMATE",
            "description": description,
            "status": "created",
            "created_at": now,
            "created_by": user_id,
            "stats": {},
            "errors": [],
            "completed_at": None
        }
        
        await self._get_collection("batches").insert_one(batch)
        
        await self._log_audit(
            batch_id=batch_id,
            action="batch_created",
            details=f"Import batch created from {source_file}",
            user_id=user_id
        )
        
        return batch
    
    async def update_batch_status(self, batch_id: str, status: str, stats: Dict = None, errors: List = None):
        """Update batch status and stats"""
        update_data = {
            "status": status,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        if stats:
            update_data["stats"] = stats
        if errors:
            update_data["errors"] = errors
        if status in ["completed", "failed"]:
            update_data["completed_at"] = datetime.now(timezone.utc).isoformat()
        
        await self._get_collection("batches").update_one(
            {"batch_id": batch_id},
            {"$set": update_data}
        )
    
    async def stage_records_bulk(self, collection_name: str, records: List[Dict], batch_id: str) -> Dict:
        """
        Stage records in bulk (faster than one-by-one)
        
        Uses upsert to prevent duplicates based on source_record_id
        """
        if not records:
            return {"inserted": 0, "updated": 0, "skipped": 0, "errors": []}
        
        collection = self._get_collection(collection_name)
        now = datetime.now(timezone.utc).isoformat()
        
        # Ensure index exists for duplicate prevention
        try:
            await collection.create_index(
                [("tenant_id", 1), ("source_record_id", 1)],
                unique=True,
                background=True
            )
        except Exception:
            pass  # Index may already exist
        
        inserted = 0
        skipped = 0
        errors = []
        
        # Use bulk upsert operations
        from pymongo import UpdateOne
        operations = []
        
        for record in records:
            source_id = record.get("source_id") or record.get("code") or str(uuid.uuid4())
            checksum = self._compute_checksum(record)
            
            doc = {
                "staging_id": str(uuid.uuid4()),
                "tenant_id": self.tenant_id,
                "batch_id": batch_id,
                "source_system": "IPOS5",
                "source_record_id": source_id,
                "checksum": checksum,
                "imported_at": now,
                "mapped": False,
                "validated": False,
                "imported_to_final": False,
                "data": record
            }
            
            # Upsert - only insert if not exists
            operations.append(UpdateOne(
                {"tenant_id": self.tenant_id, "source_record_id": source_id},
                {"$setOnInsert": doc},
                upsert=True
            ))
        
        # Execute bulk operations in batches
        batch_size = 5000
        for i in range(0, len(operations), batch_size):
            batch_ops = operations[i:i+batch_size]
            try:
                result = await collection.bulk_write(batch_ops, ordered=False)
                inserted += result.upserted_count
                skipped += (len(batch_ops) - result.upserted_count)
            except Exception as e:
                errors.append({"batch": i // batch_size, "error": str(e)})
        
        return {
            "inserted": inserted,
            "updated": 0,
            "skipped": skipped,
            "errors": errors
        }

    async def stage_records(self, collection_name: str, records: List[Dict], batch_id: str) -> Dict:
        """
        Stage records from iPOS to staging collection
        
        Returns:
            {
                "inserted": int,
                "updated": int,
                "skipped": int,
                "errors": List
            }
        """
        if not records:
            return {"inserted": 0, "updated": 0, "skipped": 0, "errors": []}
        
        collection = self._get_collection(collection_name)
        now = datetime.now(timezone.utc).isoformat()
        
        inserted = 0
        updated = 0
        skipped = 0
        errors = []
        
        for record in records:
            try:
                source_id = record.get("source_id") or record.get("code") or str(uuid.uuid4())
                checksum = self._compute_checksum(record)
                
                staging_record = {
                    "staging_id": str(uuid.uuid4()),
                    "tenant_id": self.tenant_id,
                    "batch_id": batch_id,
                    "source_system": "IPOS5",
                    "source_record_id": source_id,
                    "checksum": checksum,
                    "imported_at": now,
                    "mapped": False,
                    "validated": False,
                    "imported_to_final": False,
                    "data": record
                }
                
                # Check if record already exists (idempotency)
                existing = await collection.find_one({
                    "tenant_id": self.tenant_id,
                    "source_record_id": source_id
                })
                
                if existing:
                    if existing.get("checksum") == checksum:
                        # Same data, skip
                        skipped += 1
                    else:
                        # Data changed, update
                        await collection.update_one(
                            {"_id": existing["_id"]},
                            {"$set": {
                                "batch_id": batch_id,
                                "checksum": checksum,
                                "imported_at": now,
                                "data": record,
                                "mapped": False,
                                "validated": False
                            }}
                        )
                        updated += 1
                else:
                    # New record
                    await collection.insert_one(staging_record)
                    inserted += 1
                    
            except Exception as e:
                errors.append({
                    "source_id": source_id,
                    "error": str(e)
                })
        
        return {
            "inserted": inserted,
            "updated": updated,
            "skipped": skipped,
            "errors": errors
        }
    
    async def stage_all_from_parser(self, parser_data: Dict, batch_id: str) -> Dict:
        """
        Stage all data from parser extraction
        
        Args:
            parser_data: Output from IPOSBackupParser.extract_all()
            batch_id: Import batch ID
            
        Returns:
            Stats per collection
        """
        stats = {}
        all_errors = []
        
        # Map parser output to staging collections
        mappings = [
            ("items", parser_data.get("items", [])),
            ("categories", parser_data.get("categories", [])),
            ("brands", parser_data.get("brands", [])),
            ("units", parser_data.get("units", [])),
            ("suppliers", parser_data.get("suppliers", [])),
            ("customers", parser_data.get("customers", [])),
            ("warehouses", parser_data.get("warehouses", [])),
            ("stock_positions", parser_data.get("stock_positions", [])),
            ("chart_of_accounts", parser_data.get("chart_of_accounts", [])),
            ("journals", parser_data.get("journals", [])),
            ("sales_headers", parser_data.get("sales_headers", [])),
            ("sales_details", parser_data.get("sales_details", [])),
            ("purchase_headers", parser_data.get("purchase_headers", [])),
            ("purchase_details", parser_data.get("purchase_details", [])),
            ("ar_balances", parser_data.get("ar_balances", [])),
            ("ap_balances", parser_data.get("ap_balances", [])),
            ("ap_payment_headers", parser_data.get("ap_payment_headers", [])),
            ("ap_payment_details", parser_data.get("ap_payment_details", [])),
            ("ar_payment_headers", parser_data.get("ar_payment_headers", [])),
            ("ar_payment_details", parser_data.get("ar_payment_details", [])),
        ]
        
        for collection_name, records in mappings:
            result = await self.stage_records(collection_name, records, batch_id)
            stats[collection_name] = {
                "total": len(records),
                "inserted": result["inserted"],
                "updated": result["updated"],
                "skipped": result["skipped"],
                "error_count": len(result["errors"])
            }
            all_errors.extend(result["errors"])
        
        # Update batch with stats
        await self.update_batch_status(
            batch_id, 
            "staged",
            stats=stats,
            errors=all_errors[:100]  # Limit errors stored
        )
        
        await self._log_audit(
            batch_id=batch_id,
            action="staging_completed",
            details=f"Staged {sum(s['total'] for s in stats.values())} total records",
            user_id=""
        )
        
        return stats
    
    async def get_staging_summary(self, batch_id: str = None) -> Dict:
        """Get summary of staging data"""
        summary = {}
        
        for name, coll_name in self.COLLECTIONS.items():
            if name in ["batches", "reconciliation", "audit"]:
                continue
            
            query = {"tenant_id": self.tenant_id}
            if batch_id:
                query["batch_id"] = batch_id
            
            collection = self.db[coll_name]
            count = await collection.count_documents(query)
            summary[name] = count
        
        return summary
    
    async def get_staged_records(self, collection_name: str, batch_id: str = None, 
                                  skip: int = 0, limit: int = 100) -> List[Dict]:
        """Get staged records from a collection"""
        collection = self._get_collection(collection_name)
        
        query = {"tenant_id": self.tenant_id}
        if batch_id:
            query["batch_id"] = batch_id
        
        cursor = collection.find(query, {"_id": 0}).skip(skip).limit(limit)
        return await cursor.to_list(limit)
    
    async def clear_staging(self, collection_name: str = None, batch_id: str = None):
        """Clear staging data"""
        if collection_name:
            collections = [collection_name]
        else:
            collections = [n for n in self.COLLECTIONS.keys() 
                          if n not in ["batches", "reconciliation", "audit"]]
        
        for name in collections:
            collection = self._get_collection(name)
            query = {"tenant_id": self.tenant_id}
            if batch_id:
                query["batch_id"] = batch_id
            
            await collection.delete_many(query)
        
        await self._log_audit(
            batch_id=batch_id or "all",
            action="staging_cleared",
            details=f"Cleared staging: {collections}",
            user_id=""
        )
    
    async def _log_audit(self, batch_id: str, action: str, details: str, user_id: str):
        """Log audit entry"""
        audit = {
            "id": str(uuid.uuid4()),
            "tenant_id": self.tenant_id,
            "batch_id": batch_id,
            "action": action,
            "details": details,
            "user_id": user_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        await self._get_collection("audit").insert_one(audit)
    
    async def get_audit_logs(self, batch_id: str = None, limit: int = 100) -> List[Dict]:
        """Get audit logs"""
        query = {"tenant_id": self.tenant_id}
        if batch_id:
            query["batch_id"] = batch_id
        
        cursor = self._get_collection("audit").find(
            query, {"_id": 0}
        ).sort("timestamp", -1).limit(limit)
        
        return await cursor.to_list(limit)
