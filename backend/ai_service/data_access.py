# OCB TITAN ERP - AI Business Engine
# =====================================
# AI Data Access Layer (READ-ONLY)
# Version: 1.0.0

"""
AI DATA ACCESS LAYER

Arsitektur:
    Core DB → Read-only Access → AI Data Access Layer → Feature Builder → AI Insights

Rules:
- SELECT ONLY - NO INSERT/UPDATE/DELETE
- Tenant Isolated
- RBAC Protected
- Kill Switch Enabled
"""

from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
import os

# AI Engine Configuration
AI_ENGINE_CONFIG = {
    "enabled": os.environ.get("AI_ENGINE_ENABLED", "true").lower() == "true",
    "version": "1.0.0",
    "model_version": "ocb-titan-ai-v1",
    "read_only": True,
    "allowed_operations": ["SELECT", "AGGREGATE", "COUNT", "DISTINCT"],
    "forbidden_operations": ["INSERT", "UPDATE", "DELETE", "DROP"]
}

class AIKillSwitch:
    """
    AI Kill Switch - Emergency disable untuk AI Engine
    
    Two levels:
    1. GLOBAL: Set AI_ENGINE_ENABLED=false di environment
    2. TENANT: Set ai_enabled=false di _tenant_metadata
    """
    
    @staticmethod
    def is_enabled() -> bool:
        return AI_ENGINE_CONFIG["enabled"]
    
    @staticmethod
    def check_or_raise():
        if not AIKillSwitch.is_enabled():
            raise AIEngineDisabledException("AI Engine is disabled via GLOBAL kill switch (AI_ENGINE_ENABLED=false)")
    
    @staticmethod
    async def check_tenant_enabled(db) -> bool:
        """Check if AI is enabled for current tenant"""
        metadata = await db["_tenant_metadata"].find_one({}, {"_id": 0, "ai_enabled": 1})
        if metadata and metadata.get("ai_enabled") == False:
            return False
        return True
    
    @staticmethod
    async def check_tenant_or_raise(db):
        """Check tenant-level kill switch"""
        if not await AIKillSwitch.check_tenant_enabled(db):
            raise AIEngineDisabledException("AI Engine is disabled for this tenant (ai_enabled=false)")
    
    @staticmethod
    async def set_tenant_enabled(db, enabled: bool):
        """Set tenant-level AI enabled status"""
        await db["_tenant_metadata"].update_one(
            {},
            {"$set": {"ai_enabled": enabled, "ai_updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        return enabled


class AIEngineDisabledException(Exception):
    """Exception raised when AI Engine is disabled"""
    pass


class AIReadOnlyViolationException(Exception):
    """Exception raised when write operation is attempted"""
    pass


class AIDataAccessLayer:
    """
    AI Data Access Layer - READ-ONLY access to database
    
    Fitur:
    - SELECT only
    - Tenant isolation
    - Query logging
    - Performance monitoring
    """
    
    def __init__(self, db):
        self.db = db
        self.query_count = 0
        self.last_query_time = None
    
    async def read_collection(
        self,
        collection: str,
        query: Dict = None,
        projection: Dict = None,
        limit: int = 1000,
        sort: List = None
    ) -> List[Dict]:
        """
        READ-ONLY query to collection
        """
        AIKillSwitch.check_or_raise()
        
        query = query or {}
        projection = projection or {"_id": 0}
        
        # Ensure _id is excluded
        projection["_id"] = 0
        
        cursor = self.db[collection].find(query, projection)
        
        if sort:
            cursor = cursor.sort(sort)
        
        cursor = cursor.limit(limit)
        
        self.query_count += 1
        self.last_query_time = datetime.now(timezone.utc)
        
        return await cursor.to_list(limit)
    
    async def aggregate(
        self,
        collection: str,
        pipeline: List[Dict],
        limit: int = 1000
    ) -> List[Dict]:
        """
        READ-ONLY aggregation
        """
        AIKillSwitch.check_or_raise()
        
        # Add $limit if not present
        has_limit = any("$limit" in stage for stage in pipeline)
        if not has_limit:
            pipeline.append({"$limit": limit})
        
        self.query_count += 1
        self.last_query_time = datetime.now(timezone.utc)
        
        return await self.db[collection].aggregate(pipeline).to_list(limit)
    
    async def count(self, collection: str, query: Dict = None) -> int:
        """Count documents (READ-ONLY)"""
        AIKillSwitch.check_or_raise()
        
        query = query or {}
        self.query_count += 1
        
        return await self.db[collection].count_documents(query)
    
    async def distinct(self, collection: str, field: str, query: Dict = None) -> List:
        """Get distinct values (READ-ONLY)"""
        AIKillSwitch.check_or_raise()
        
        query = query or {}
        self.query_count += 1
        
        return await self.db[collection].distinct(field, query)
    
    # WRITE OPERATIONS ARE BLOCKED
    async def insert(self, *args, **kwargs):
        raise AIReadOnlyViolationException("INSERT operation is forbidden in AI Engine")
    
    async def update(self, *args, **kwargs):
        raise AIReadOnlyViolationException("UPDATE operation is forbidden in AI Engine")
    
    async def delete(self, *args, **kwargs):
        raise AIReadOnlyViolationException("DELETE operation is forbidden in AI Engine")


class AIFeatureBuilder:
    """
    AI Feature Builder - Build features from raw data
    """
    
    def __init__(self, data_layer: AIDataAccessLayer):
        self.data = data_layer
    
    async def build_sales_features(self, days: int = 30) -> Dict:
        """Build sales features for analysis"""
        AIKillSwitch.check_or_raise()
        
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        
        # Get sales data
        sales = await self.data.read_collection(
            "sales_invoices",
            {"created_at": {"$gte": since}},
            limit=5000
        )
        
        # Get products for enrichment
        products = await self.data.read_collection("products", limit=1000)
        product_map = {p.get("id"): p for p in products}
        
        return {
            "sales_data": sales,
            "products": product_map,
            "period_days": days,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    
    async def build_inventory_features(self) -> Dict:
        """Build inventory features for analysis"""
        AIKillSwitch.check_or_raise()
        
        # Get stock movements
        movements = await self.data.read_collection(
            "stock_movements",
            limit=5000
        )
        
        # Get current stock
        stock = await self.data.read_collection("stock", limit=1000)
        
        # Get products
        products = await self.data.read_collection("products", limit=1000)
        
        return {
            "movements": movements,
            "current_stock": stock,
            "products": products,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    
    async def build_finance_features(self, days: int = 30) -> Dict:
        """Build finance features for analysis"""
        AIKillSwitch.check_or_raise()
        
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        
        # Get journal entries
        journals = await self.data.read_collection(
            "journal_entries",
            {"status": "posted"},
            limit=5000
        )
        
        # Get chart of accounts
        coa = await self.data.read_collection("chart_of_accounts", limit=500)
        
        # Get cash transactions
        cash = await self.data.read_collection("cash_transactions", limit=2000)
        
        return {
            "journals": journals,
            "chart_of_accounts": coa,
            "cash_transactions": cash,
            "period_days": days,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }


# Export configuration
def get_ai_config() -> Dict:
    return AI_ENGINE_CONFIG.copy()


def is_ai_enabled() -> bool:
    return AIKillSwitch.is_enabled()
