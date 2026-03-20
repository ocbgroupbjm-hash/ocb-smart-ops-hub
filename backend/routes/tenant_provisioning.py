"""
OCB TITAN ERP - ENTERPRISE TENANT PROVISIONING ENGINE
======================================================
P0: All new tenants MUST be cloned from blueprint (ocb_titan), NOT empty database.

PROVISIONING STATUS:
- provisioning: Tenant sedang dibuat
- ready: Tenant siap digunakan
- error: Tenant gagal dibuat, perlu repair

RULES:
1. Only READY tenants can be selected in UI
2. Clone master data from blueprint, NOT transactions
3. Auto-sync indexes, collections, sequences
4. Repair endpoint for broken tenants
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from datetime import datetime, timezone
from typing import Optional, Dict, List, Any
from pydantic import BaseModel
import uuid
import os

router = APIRouter(prefix="/api/tenant-provisioning", tags=["Tenant Provisioning"])

# Blueprint database - source of truth for all master data
BLUEPRINT_DATABASE = "ocb_titan"

# Collections to COPY (master data)
COLLECTIONS_TO_COPY = [
    "accounts",           # Chart of Accounts
    "account_settings",   # Account configuration
    "categories",         # Product categories
    "units",              # Unit of measure
    "roles",              # User roles
    "permissions",        # Permission settings
    "numbering_settings", # Auto-numbering format
    "company_profile",    # Company info template
    "branches",           # Branch template (HQ)
    "price_types",        # Pricing configuration
    "payment_methods",    # Payment methods
    "tax_settings",       # Tax configuration
    "_sequences",         # Numbering sequences (reset to 0)
]

# Collections to CREATE but NOT copy (transactional)
COLLECTIONS_TO_CREATE_EMPTY = [
    "users",
    "products",
    "suppliers",
    "customers",
    "purchase_orders",
    "purchase_order_items",
    "sales_invoices",
    "sales_invoice_items",
    "stock_movements",
    "product_stocks",
    "journal_entries",
    "transactions",
    "stock_validation_logs",
    "activity_logs",
]

# Indexes that MUST exist in every tenant
REQUIRED_INDEXES = {
    "stock_movements": [
        ("idx_ref_product_branch_type", [
            ("reference_id", 1),
            ("product_id", 1),
            ("branch_id", 1),
            ("reference_type", 1)
        ])
    ],
    "products": [
        ("idx_sku", [("sku", 1)]),
        ("idx_is_active", [("is_active", 1)])
    ],
    "journal_entries": [
        ("idx_reference", [("reference_id", 1), ("reference_type", 1)])
    ],
    "users": [
        ("idx_email", [("email", 1)])
    ]
}


def get_mongo_client():
    from motor.motor_asyncio import AsyncIOMotorClient
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    return AsyncIOMotorClient(mongo_url)


class CreateTenantRequest(BaseModel):
    database_key: str  # e.g. "ocb_unit_5"
    company_name: str
    description: Optional[str] = ""
    owner_email: str
    owner_password: str
    business_type: Optional[str] = "retail"
    icon: Optional[str] = "building"
    color: Optional[str] = "#991B1B"
    copy_products: bool = False  # Default: don't copy products
    copy_suppliers: bool = False
    copy_customers: bool = False


class TenantProvisioningEngine:
    def __init__(self, client, blueprint_db: str = BLUEPRINT_DATABASE):
        self.client = client
        self.blueprint_db = client[blueprint_db]
        self.log = []
    
    def _log(self, message: str, level: str = "info"):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "message": message
        }
        self.log.append(entry)
        print(f"[{level.upper()}] {message}")
    
    async def create_tenant(self, request: CreateTenantRequest) -> Dict:
        """
        Create new tenant with full enterprise provisioning.
        Flow: create → clone structure → clone master → apply config → mark ready
        """
        target_db_name = request.database_key
        target_db = self.client[target_db_name]
        
        self._log(f"Starting provisioning for tenant: {target_db_name}")
        
        try:
            # Step 1: Check if database already exists
            existing = await self.client.list_database_names()
            if target_db_name in existing:
                # Check if it's just empty or has data
                collections = await target_db.list_collection_names()
                if len(collections) > 2:  # More than just system collections
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Database {target_db_name} already exists with data"
                    )
            
            # Step 2: Create metadata with status = provisioning
            now = datetime.now(timezone.utc).isoformat()
            metadata = {
                "id": str(uuid.uuid4()),
                "database_key": target_db_name,
                "company_name": request.company_name,
                "description": request.description,
                "business_type": request.business_type,
                "icon": request.icon,
                "color": request.color,
                "status": "provisioning",  # Will be updated to 'ready' on success
                "blueprint_version": "1.0.2",
                "source_blueprint": BLUEPRINT_DATABASE,
                "timezone": "Asia/Jakarta",
                "currency": "IDR",
                "ai_enabled": False,
                "created_at": now,
                "initialized_at": now,
                "provisioning_started_at": now,
                "provisioning_log": []
            }
            
            await target_db["_tenant_metadata"].delete_many({})
            await target_db["_tenant_metadata"].insert_one(metadata)
            self._log("Created tenant metadata with status: provisioning")
            
            # Step 3: Clone master data collections
            await self._clone_master_data(target_db, request)
            
            # Step 4: Create empty transactional collections
            await self._create_empty_collections(target_db)
            
            # Step 5: Create required indexes
            await self._create_indexes(target_db)
            
            # Step 6: Reset sequences
            await self._reset_sequences(target_db)
            
            # Step 7: Create owner user
            await self._create_owner_user(target_db, request)
            
            # Step 8: Update metadata to READY
            await target_db["_tenant_metadata"].update_one(
                {},
                {"$set": {
                    "status": "ready",
                    "provisioning_completed_at": datetime.now(timezone.utc).isoformat(),
                    "provisioning_log": self.log
                }}
            )
            self._log("Tenant provisioning completed - status: READY")
            
            # Step 9: Register in businesses.json for backward compatibility
            await self._register_in_businesses_json(request)
            
            return {
                "success": True,
                "status": "ready",
                "database": target_db_name,
                "company_name": request.company_name,
                "owner_email": request.owner_email,
                "message": "Tenant berhasil dibuat dan siap digunakan",
                "provisioning_log": self.log
            }
            
        except HTTPException:
            raise
        except Exception as e:
            # Mark as error
            await target_db["_tenant_metadata"].update_one(
                {},
                {"$set": {
                    "status": "error",
                    "error_message": str(e),
                    "provisioning_failed_at": datetime.now(timezone.utc).isoformat(),
                    "provisioning_log": self.log
                }}
            )
            self._log(f"Provisioning failed: {str(e)}", "error")
            raise HTTPException(status_code=500, detail=f"Provisioning failed: {str(e)}")
    
    async def _clone_master_data(self, target_db, request: CreateTenantRequest):
        """Clone master data from blueprint database"""
        self._log("Cloning master data from blueprint...")
        
        for coll_name in COLLECTIONS_TO_COPY:
            try:
                source_coll = self.blueprint_db[coll_name]
                target_coll = target_db[coll_name]
                
                # Clear existing data
                await target_coll.delete_many({})
                
                # Copy all documents
                docs = await source_coll.find({}, {"_id": 0}).to_list(None)
                
                if docs:
                    # For sequences, reset to 0
                    if coll_name == "_sequences":
                        for doc in docs:
                            doc["value"] = 0
                    
                    await target_coll.insert_many(docs)
                    self._log(f"  Copied {len(docs)} docs to {coll_name}")
                else:
                    self._log(f"  {coll_name}: No data to copy (empty in blueprint)")
                    
            except Exception as e:
                self._log(f"  Warning: Failed to copy {coll_name}: {str(e)}", "warning")
        
        # Optionally copy products/suppliers/customers if requested
        if request.copy_products:
            await self._copy_collection("products", target_db)
        
        if request.copy_suppliers:
            await self._copy_collection("suppliers", target_db)
        
        if request.copy_customers:
            await self._copy_collection("customers", target_db)
    
    async def _copy_collection(self, coll_name: str, target_db):
        """Copy a specific collection from blueprint"""
        try:
            source_coll = self.blueprint_db[coll_name]
            target_coll = target_db[coll_name]
            
            docs = await source_coll.find({}, {"_id": 0}).to_list(None)
            if docs:
                await target_coll.delete_many({})
                await target_coll.insert_many(docs)
                self._log(f"  Copied {len(docs)} docs to {coll_name}")
        except Exception as e:
            self._log(f"  Warning: Failed to copy {coll_name}: {str(e)}", "warning")
    
    async def _create_empty_collections(self, target_db):
        """Create empty collections for transactional data"""
        self._log("Creating empty transactional collections...")
        
        existing = await target_db.list_collection_names()
        
        for coll_name in COLLECTIONS_TO_CREATE_EMPTY:
            if coll_name not in existing:
                await target_db.create_collection(coll_name)
                self._log(f"  Created empty collection: {coll_name}")
    
    async def _create_indexes(self, target_db):
        """Create required indexes"""
        self._log("Creating required indexes...")
        
        for coll_name, indexes in REQUIRED_INDEXES.items():
            coll = target_db[coll_name]
            
            for idx_name, idx_spec in indexes:
                try:
                    await coll.create_index(idx_spec, name=idx_name, background=True)
                    self._log(f"  Created index {idx_name} on {coll_name}")
                except Exception as e:
                    if "already exists" not in str(e).lower():
                        self._log(f"  Warning: Index {idx_name}: {str(e)}", "warning")
    
    async def _reset_sequences(self, target_db):
        """Reset all sequences to 0"""
        self._log("Resetting sequences...")
        
        await target_db["_sequences"].update_many(
            {},
            {"$set": {"value": 0}}
        )
        self._log("  All sequences reset to 0")
    
    async def _create_owner_user(self, target_db, request: CreateTenantRequest):
        """Create owner user for the new tenant"""
        from utils.auth import hash_password
        
        self._log(f"Creating owner user: {request.owner_email}")
        
        # Get role and branch
        owner_role = await target_db["roles"].find_one({"code": "owner"})
        branch = await target_db["branches"].find_one({"code": "HQ"})
        
        if not branch:
            # Create default HQ branch
            branch = {
                "id": str(uuid.uuid4()),
                "code": "HQ",
                "name": "Headquarters",
                "address": "",
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await target_db["branches"].insert_one(branch)
        
        user = {
            "id": str(uuid.uuid4()),
            "email": request.owner_email,
            "password_hash": hash_password(request.owner_password),
            "name": "Owner",
            "role": "owner",
            "role_code": "owner",
            "role_id": owner_role["id"] if owner_role else None,
            "branch_id": branch["id"],
            "branch_ids": [branch["id"]],
            "is_active": True,
            "permissions": ["*"],
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await target_db["users"].delete_many({"email": request.owner_email})
        await target_db["users"].insert_one(user)
        self._log(f"  Owner user created: {request.owner_email}")
    
    async def _register_in_businesses_json(self, request: CreateTenantRequest):
        """Register tenant in businesses.json for backward compatibility"""
        import json
        
        business_file = "/app/backend/data/businesses.json"
        
        try:
            if os.path.exists(business_file):
                with open(business_file, 'r') as f:
                    businesses = json.load(f)
            else:
                os.makedirs("/app/backend/data", exist_ok=True)
                businesses = []
            
            # Check if already exists
            if not any(b.get('db_name') == request.database_key for b in businesses):
                businesses.append({
                    "id": request.database_key,
                    "name": request.company_name,
                    "db_name": request.database_key,
                    "description": request.description,
                    "icon": request.icon,
                    "color": request.color,
                    "created_at": datetime.now(timezone.utc).isoformat()
                })
                
                with open(business_file, 'w') as f:
                    json.dump(businesses, f, indent=2)
                
                self._log("  Registered in businesses.json")
        except Exception as e:
            self._log(f"  Warning: Failed to register in businesses.json: {str(e)}", "warning")
    
    async def repair_tenant(self, db_name: str) -> Dict:
        """
        Repair a broken tenant by re-syncing from blueprint.
        Does NOT touch transactional data.
        """
        self._log(f"Starting repair for tenant: {db_name}")
        
        target_db = self.client[db_name]
        
        try:
            # Check if database exists
            existing = await self.client.list_database_names()
            if db_name not in existing:
                raise HTTPException(status_code=404, detail=f"Database {db_name} not found")
            
            # Update status to repairing
            await target_db["_tenant_metadata"].update_one(
                {},
                {"$set": {"status": "repairing"}}
            )
            
            # Re-sync master data (only if missing or different)
            for coll_name in COLLECTIONS_TO_COPY:
                if coll_name == "_sequences":
                    continue  # Don't touch sequences during repair
                
                target_coll = target_db[coll_name]
                source_coll = self.blueprint_db[coll_name]
                
                # Check if collection is empty in target
                target_count = await target_coll.count_documents({})
                source_count = await source_coll.count_documents({})
                
                if target_count == 0 and source_count > 0:
                    docs = await source_coll.find({}, {"_id": 0}).to_list(None)
                    await target_coll.insert_many(docs)
                    self._log(f"  Repaired {coll_name}: copied {len(docs)} docs")
            
            # Ensure all collections exist
            existing_colls = await target_db.list_collection_names()
            for coll_name in COLLECTIONS_TO_CREATE_EMPTY:
                if coll_name not in existing_colls:
                    await target_db.create_collection(coll_name)
                    self._log(f"  Created missing collection: {coll_name}")
            
            # Re-create indexes
            await self._create_indexes(target_db)
            
            # Update status to ready
            await target_db["_tenant_metadata"].update_one(
                {},
                {"$set": {
                    "status": "ready",
                    "last_repaired_at": datetime.now(timezone.utc).isoformat(),
                    "repair_log": self.log
                }}
            )
            
            return {
                "success": True,
                "status": "ready",
                "database": db_name,
                "message": "Tenant berhasil diperbaiki",
                "repair_log": self.log
            }
            
        except HTTPException:
            raise
        except Exception as e:
            await target_db["_tenant_metadata"].update_one(
                {},
                {"$set": {
                    "status": "error",
                    "repair_error": str(e)
                }}
            )
            raise HTTPException(status_code=500, detail=f"Repair failed: {str(e)}")


# ==================== API ENDPOINTS ====================

@router.post("/create")
async def create_new_tenant(request: CreateTenantRequest):
    """
    Create new tenant with enterprise provisioning.
    Clones from blueprint (ocb_titan), creates owner user, marks as READY.
    """
    client = get_mongo_client()
    engine = TenantProvisioningEngine(client)
    
    try:
        result = await engine.create_tenant(request)
        return result
    finally:
        client.close()


@router.post("/{tenant_id}/repair")
async def repair_tenant(tenant_id: str):
    """
    Repair a broken tenant by re-syncing from blueprint.
    Does NOT touch transactional data (purchases, sales, stock_movements, journals).
    """
    client = get_mongo_client()
    engine = TenantProvisioningEngine(client)
    
    try:
        result = await engine.repair_tenant(tenant_id)
        return result
    finally:
        client.close()


@router.get("/{tenant_id}/status")
async def get_tenant_status(tenant_id: str):
    """Get provisioning status of a tenant"""
    client = get_mongo_client()
    
    try:
        db = client[tenant_id]
        metadata = await db["_tenant_metadata"].find_one({}, {"_id": 0})
        
        if not metadata:
            # Check if database exists at all
            existing = await client.list_database_names()
            if tenant_id in existing:
                return {
                    "tenant_id": tenant_id,
                    "status": "uninitialized",
                    "message": "Database exists but no metadata"
                }
            else:
                raise HTTPException(status_code=404, detail="Tenant not found")
        
        return {
            "tenant_id": tenant_id,
            "status": metadata.get("status", "unknown"),
            "company_name": metadata.get("company_name"),
            "blueprint_version": metadata.get("blueprint_version"),
            "created_at": metadata.get("created_at"),
            "provisioning_completed_at": metadata.get("provisioning_completed_at"),
            "last_repaired_at": metadata.get("last_repaired_at"),
            "error_message": metadata.get("error_message"),
            "is_ready": metadata.get("status") == "ready"
        }
    finally:
        client.close()


@router.get("/ready-tenants")
async def list_ready_tenants():
    """List only tenants with status = READY"""
    client = get_mongo_client()
    ready_tenants = []
    
    try:
        all_dbs = await client.list_database_names()
        ocb_dbs = [d for d in all_dbs if d.startswith("ocb_")]
        
        for db_name in ocb_dbs:
            db = client[db_name]
            metadata = await db["_tenant_metadata"].find_one({}, {"_id": 0})
            
            if metadata and metadata.get("status") == "ready":
                ready_tenants.append({
                    "tenant_id": db_name,
                    "name": metadata.get("company_name", db_name),
                    "status": "ready",
                    "blueprint_version": metadata.get("blueprint_version")
                })
        
        return {
            "ready_tenants": ready_tenants,
            "total": len(ready_tenants)
        }
    finally:
        client.close()


@router.post("/sync-all")
async def sync_all_tenants_to_blueprint():
    """
    Sync all tenants to latest blueprint structure.
    Only syncs structure (indexes, collections), NOT data.
    """
    client = get_mongo_client()
    engine = TenantProvisioningEngine(client)
    results = []
    
    try:
        all_dbs = await client.list_database_names()
        ocb_dbs = [d for d in all_dbs if d.startswith("ocb_") and d != BLUEPRINT_DATABASE]
        
        for db_name in ocb_dbs:
            try:
                # Only sync structure
                target_db = client[db_name]
                
                # Create missing collections
                existing_colls = await target_db.list_collection_names()
                for coll_name in COLLECTIONS_TO_CREATE_EMPTY:
                    if coll_name not in existing_colls:
                        await target_db.create_collection(coll_name)
                
                # Create indexes
                await engine._create_indexes(target_db)
                
                results.append({
                    "tenant": db_name,
                    "status": "synced"
                })
            except Exception as e:
                results.append({
                    "tenant": db_name,
                    "status": "error",
                    "error": str(e)
                })
        
        return {
            "message": "Sync completed",
            "results": results
        }
    finally:
        client.close()
