# iPOS Data Importer - Import master data from iPOS to OCB TITAN
# IDEMPOTENT - Safe to run multiple times

import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Any
import uuid
import logging

logger = logging.getLogger(__name__)


class IPOSDataImporter:
    """
    Import iPOS data from staging to OCB TITAN production
    
    IMPORT ORDER (due to dependencies):
    1. Chart of Accounts
    2. Categories, Brands, Units
    3. Warehouses (to branches)
    4. Items (products)
    5. Suppliers
    6. Customers
    7. Stock positions
    
    RULES:
    - All imports are idempotent (check for existing by source_id)
    - Maintain source_id mapping for reference
    - All imports to tenant: ocb_titan
    """
    
    # iPOS to OCB TITAN field mappings
    ACCOUNT_MAPPING = {
        "1-2010": {"name": "PERSEDIAAN BARANG", "group": "1", "type": "D"},
        "2-1101": {"name": "HUTANG DAGANG", "group": "2", "type": "K"},
        "4-1100": {"name": "PENDAPATAN PENJUALAN", "group": "4", "type": "K"},
        "5-1300": {"name": "HARGA POKOK PENJUALAN", "group": "5", "type": "D"},
        "1-1210": {"name": "PIUTANG DAGANG", "group": "1", "type": "D"},
        "1-1100": {"name": "KAS & BANK", "group": "1", "type": "D"},
        "1-1110": {"name": "KAS KECIL", "group": "1", "type": "D"},
        "1-1121": {"name": "BANK MANDIRI", "group": "1", "type": "D"},
        "1-1122": {"name": "BANK BCA", "group": "1", "type": "D"},
    }
    
    def __init__(self, db, tenant_id: str = "ocb_titan"):
        self.db = db
        self.tenant_id = tenant_id
        self.import_stats = {}
        self.mapping_cache = {}  # Source ID -> OCB TITAN ID
    
    async def import_chart_of_accounts(self, staged_accounts: List[Dict]) -> Dict:
        """Import chart of accounts from staging"""
        stats = {"imported": 0, "skipped": 0, "errors": []}
        
        for acc in staged_accounts:
            data = acc.get("data", acc)
            source_code = data.get("code")
            
            # Check existing
            existing = await self.db.chart_of_accounts.find_one({
                "code": source_code, "tenant_id": self.tenant_id
            })
            
            if existing:
                self.mapping_cache[f"acc_{source_code}"] = existing.get("id")
                stats["skipped"] += 1
                continue
            
            # Create new account
            new_id = str(uuid.uuid4())
            account = {
                "id": new_id,
                "tenant_id": self.tenant_id,
                "code": source_code,
                "name": data.get("name", ""),
                "group": data.get("group", "1"),
                "type": data.get("type", "D"),
                "level": data.get("level", 1),
                "parent_code": data.get("parent_code"),
                "is_active": True,
                "source_system": "IPOS5",
                "source_id": source_code,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            try:
                await self.db.chart_of_accounts.insert_one(account)
                self.mapping_cache[f"acc_{source_code}"] = new_id
                stats["imported"] += 1
            except Exception as e:
                stats["errors"].append({"code": source_code, "error": str(e)})
        
        logger.info(f"Accounts import: {stats['imported']} imported, {stats['skipped']} skipped")
        return stats
    
    async def import_categories(self, staged_categories: List[Dict]) -> Dict:
        """Import categories"""
        stats = {"imported": 0, "skipped": 0, "errors": []}
        
        for cat in staged_categories:
            data = cat.get("data", cat)
            source_id = data.get("source_id") or data.get("code")
            
            existing = await self.db.categories.find_one({
                "code": source_id, "tenant_id": self.tenant_id
            })
            
            if existing:
                self.mapping_cache[f"cat_{source_id}"] = existing.get("id")
                stats["skipped"] += 1
                continue
            
            new_id = str(uuid.uuid4())
            category = {
                "id": new_id,
                "tenant_id": self.tenant_id,
                "code": source_id,
                "name": data.get("name", source_id),
                "description": data.get("description", ""),
                "is_active": True,
                "source_system": "IPOS5",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            try:
                await self.db.categories.insert_one(category)
                self.mapping_cache[f"cat_{source_id}"] = new_id
                stats["imported"] += 1
            except Exception as e:
                stats["errors"].append({"id": source_id, "error": str(e)})
        
        return stats
    
    async def import_warehouses(self, staged_warehouses: List[Dict]) -> Dict:
        """Import warehouses to branches"""
        stats = {"imported": 0, "skipped": 0, "errors": []}
        
        for wh in staged_warehouses:
            data = wh.get("data", wh)
            source_code = data.get("code")
            
            existing = await self.db.branches.find_one({
                "code": source_code, "tenant_id": self.tenant_id
            })
            
            if existing:
                self.mapping_cache[f"branch_{source_code}"] = existing.get("id")
                stats["skipped"] += 1
                continue
            
            new_id = str(uuid.uuid4())
            branch = {
                "id": new_id,
                "tenant_id": self.tenant_id,
                "code": source_code,
                "name": data.get("name", source_code),
                "address": data.get("address", ""),
                "city": data.get("city", ""),
                "phone": data.get("phone", ""),
                "function": data.get("function", "Utama"),
                "is_active": True,
                "source_system": "IPOS5",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            try:
                await self.db.branches.insert_one(branch)
                self.mapping_cache[f"branch_{source_code}"] = new_id
                stats["imported"] += 1
            except Exception as e:
                stats["errors"].append({"code": source_code, "error": str(e)})
        
        return stats
    
    async def import_products(self, staged_items: List[Dict]) -> Dict:
        """Import products from staged items"""
        stats = {"imported": 0, "skipped": 0, "updated": 0, "errors": []}
        
        for item in staged_items:
            data = item.get("data", item)
            source_code = data.get("code")
            
            existing = await self.db.products.find_one({
                "code": source_code, "tenant_id": self.tenant_id
            })
            
            if existing:
                # Update existing product with iPOS data
                update_data = {
                    "name": data.get("name", existing.get("name")),
                    "cost_price": float(data.get("cost_price", 0) or 0),
                    "selling_price": float(data.get("sell_price_1", 0) or 0),
                    "wholesale_price": float(data.get("sell_price_2", 0) or 0),
                    "member_price": float(data.get("sell_price_3", 0) or 0),
                    "unit": data.get("unit", existing.get("unit", "PCS")),
                    "brand": data.get("brand", existing.get("brand", "")),
                    "min_stock": int(data.get("min_stock", 0) or 0),
                    "source_system": "IPOS5",
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
                
                await self.db.products.update_one(
                    {"id": existing.get("id")},
                    {"$set": update_data}
                )
                self.mapping_cache[f"prod_{source_code}"] = existing.get("id")
                stats["updated"] += 1
                continue
            
            # Create new product
            new_id = str(uuid.uuid4())
            
            # Lookup category
            category_code = data.get("category")
            category_id = self.mapping_cache.get(f"cat_{category_code}")
            
            product = {
                "id": new_id,
                "tenant_id": self.tenant_id,
                "code": source_code,
                "barcode": data.get("barcode", ""),
                "name": data.get("name", source_code),
                "description": "",
                "category_id": category_id,
                "brand": data.get("brand", ""),
                "unit": data.get("unit", "PCS"),
                "item_type": data.get("type", "barang"),
                "cost_price": float(data.get("cost_price", 0) or 0),
                "selling_price": float(data.get("sell_price_1", 0) or 0),
                "wholesale_price": float(data.get("sell_price_2", 0) or 0),
                "member_price": float(data.get("sell_price_3", 0) or 0),
                "reseller_price": float(data.get("sell_price_3", 0) or 0),
                "min_stock": int(data.get("min_stock", 0) or 0),
                "track_stock": True,
                "tax_rate": 0,
                "is_active": True,
                "is_bundle": False,
                "source_system": "IPOS5",
                "source_id": source_code,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            try:
                await self.db.products.insert_one(product)
                self.mapping_cache[f"prod_{source_code}"] = new_id
                stats["imported"] += 1
            except Exception as e:
                stats["errors"].append({"code": source_code, "error": str(e)})
        
        return stats
    
    async def import_stock_positions(self, staged_stocks: List[Dict]) -> Dict:
        """Import stock positions with HPP"""
        stats = {"imported": 0, "skipped": 0, "updated": 0, "errors": []}
        
        for stock in staged_stocks:
            data = stock.get("data", stock)
            item_code = data.get("item_code")
            warehouse_code = data.get("warehouse_code")
            
            # Lookup product and branch IDs
            product_id = self.mapping_cache.get(f"prod_{item_code}")
            branch_id = self.mapping_cache.get(f"branch_{warehouse_code}")
            
            if not product_id:
                # Try direct lookup
                product = await self.db.products.find_one({"code": item_code, "tenant_id": self.tenant_id})
                if product:
                    product_id = product.get("id")
                else:
                    stats["errors"].append({"item": item_code, "error": "Product not found"})
                    continue
            
            if not branch_id:
                branch = await self.db.branches.find_one({"code": warehouse_code, "tenant_id": self.tenant_id})
                if branch:
                    branch_id = branch.get("id")
                else:
                    # Use default branch
                    branch_id = "0acd2ffd-c2d9-4324-b860-a4626840e80e"
            
            quantity = int(float(data.get("quantity", 0) or 0))
            unit_cost = float(data.get("hpp_base", 0) or 0)
            
            existing = await self.db.product_stocks.find_one({
                "product_id": product_id, "branch_id": branch_id
            })
            
            if existing:
                # Update with iPOS values
                await self.db.product_stocks.update_one(
                    {"product_id": product_id, "branch_id": branch_id},
                    {"$set": {
                        "quantity": quantity,
                        "available": quantity,
                        "unit_cost": unit_cost,
                        "total_value": quantity * unit_cost,
                        "source_system": "IPOS5",
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }}
                )
                stats["updated"] += 1
            else:
                new_stock = {
                    "id": str(uuid.uuid4()),
                    "product_id": product_id,
                    "branch_id": branch_id,
                    "quantity": quantity,
                    "reserved": 0,
                    "available": quantity,
                    "unit_cost": unit_cost,
                    "total_value": quantity * unit_cost,
                    "source_system": "IPOS5",
                    "last_restock": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
                
                try:
                    await self.db.product_stocks.insert_one(new_stock)
                    stats["imported"] += 1
                except Exception as e:
                    stats["errors"].append({"item": item_code, "warehouse": warehouse_code, "error": str(e)})
        
        return stats
    
    async def configure_account_settings(self) -> Dict:
        """Configure default account settings to match iPOS"""
        settings = [
            # Purchase accounts
            {"account_key": "persediaan_barang", "account_code": "1-2010", "account_name": "PERSEDIAAN BARANG", "module": "purchase"},
            {"account_key": "pembayaran_kredit_pembelian", "account_code": "2-1101", "account_name": "HUTANG DAGANG", "module": "purchase"},
            {"account_key": "pembayaran_tunai_pembelian", "account_code": "1-1100", "account_name": "KAS & BANK", "module": "purchase"},
            {"account_key": "potongan_pembelian", "account_code": "5-199X01", "account_name": "POTONGAN PEMBELIAN", "module": "purchase"},
            
            # Sales accounts  
            {"account_key": "piutang_dagang", "account_code": "1-1210", "account_name": "PIUTANG DAGANG", "module": "sales"},
            {"account_key": "pendapatan_penjualan", "account_code": "4-1100", "account_name": "PENDAPATAN PENJUALAN", "module": "sales"},
            {"account_key": "hpp", "account_code": "5-1300", "account_name": "HARGA POKOK PENJUALAN", "module": "sales"},
            {"account_key": "pembayaran_tunai", "account_code": "1-1100", "account_name": "KAS & BANK", "module": "sales"},
            
            # AR/AP accounts
            {"account_key": "hutang_dagang", "account_code": "2-1101", "account_name": "HUTANG DAGANG", "module": "ap"},
            {"account_key": "piutang_dagang", "account_code": "1-1210", "account_name": "PIUTANG DAGANG", "module": "ar"},
        ]
        
        stats = {"configured": 0, "skipped": 0}
        
        for setting in settings:
            existing = await self.db.account_settings.find_one({
                "account_key": setting["account_key"],
                "tenant_id": self.tenant_id
            })
            
            if existing:
                stats["skipped"] += 1
                continue
            
            setting["id"] = str(uuid.uuid4())
            setting["tenant_id"] = self.tenant_id
            setting["created_at"] = datetime.now(timezone.utc).isoformat()
            
            await self.db.account_settings.insert_one(setting)
            stats["configured"] += 1
        
        logger.info(f"Account settings: {stats['configured']} configured, {stats['skipped']} skipped")
        return stats
    
    async def run_full_import(self, staged_data: Dict) -> Dict:
        """Run full import in correct order"""
        logger.info("=== STARTING FULL iPOS DATA IMPORT ===")
        
        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tenant_id": self.tenant_id,
            "steps": {}
        }
        
        # Step 1: Configure account settings
        logger.info("Step 1: Configuring account settings...")
        results["steps"]["account_settings"] = await self.configure_account_settings()
        
        # Step 2: Import Chart of Accounts
        if staged_data.get("chart_of_accounts"):
            logger.info("Step 2: Importing Chart of Accounts...")
            results["steps"]["accounts"] = await self.import_chart_of_accounts(staged_data["chart_of_accounts"])
        
        # Step 3: Import Categories
        if staged_data.get("categories"):
            logger.info("Step 3: Importing Categories...")
            results["steps"]["categories"] = await self.import_categories(staged_data["categories"])
        
        # Step 4: Import Warehouses
        if staged_data.get("warehouses"):
            logger.info("Step 4: Importing Warehouses...")
            results["steps"]["warehouses"] = await self.import_warehouses(staged_data["warehouses"])
        
        # Step 5: Import Products
        if staged_data.get("items"):
            logger.info("Step 5: Importing Products...")
            results["steps"]["products"] = await self.import_products(staged_data["items"])
        
        # Step 6: Import Stock Positions
        if staged_data.get("stock_positions"):
            logger.info("Step 6: Importing Stock Positions...")
            results["steps"]["stock"] = await self.import_stock_positions(staged_data["stock_positions"])
        
        logger.info("=== IMPORT COMPLETE ===")
        return results
