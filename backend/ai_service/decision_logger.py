# OCB TITAN ERP - AI Decision Logger
# =====================================
# Version: 1.0.0

"""
AI DECISION LOGGER

Logs all AI responses for audit and compliance:
- tenant_id
- user_id
- endpoint
- request_id
- model_version
- data_window
- features_used
- output
- timestamp
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional
import uuid
import json


class AIDecisionLogger:
    """
    Logs all AI decisions to ai_decision_log collection
    """
    
    def __init__(self, db):
        self.db = db
        self.collection = "ai_decision_log"
    
    async def log_decision(
        self,
        tenant_id: str,
        user_id: str,
        endpoint: str,
        model_version: str,
        data_window: str,
        features_used: list,
        output: Dict,
        execution_time_ms: float = 0
    ) -> str:
        """
        Log an AI decision
        
        Returns: decision_id
        """
        decision_id = str(uuid.uuid4())
        
        log_entry = {
            "id": decision_id,
            "tenant_id": tenant_id,
            "user_id": user_id,
            "endpoint": endpoint,
            "request_id": str(uuid.uuid4()),
            "model_version": model_version,
            "data_window": data_window,
            "features_used": features_used,
            "output_summary": {
                "insight_type": output.get("insight_type"),
                "recommendations_count": len(output.get("recommendations", [])),
                "has_warnings": any("⚠️" in str(r) for r in output.get("recommendations", []))
            },
            "execution_time_ms": execution_time_ms,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "completed"
        }
        
        await self.db[self.collection].insert_one(log_entry)
        
        return decision_id
    
    async def get_recent_decisions(
        self,
        tenant_id: str = None,
        limit: int = 100
    ) -> list:
        """Get recent AI decisions"""
        query = {}
        if tenant_id:
            query["tenant_id"] = tenant_id
        
        cursor = self.db[self.collection].find(
            query,
            {"_id": 0}
        ).sort("timestamp", -1).limit(limit)
        
        return await cursor.to_list(limit)
    
    async def get_decision_stats(self, tenant_id: str = None) -> Dict:
        """Get AI decision statistics"""
        query = {}
        if tenant_id:
            query["tenant_id"] = tenant_id
        
        total = await self.db[self.collection].count_documents(query)
        
        # Group by endpoint
        pipeline = [
            {"$match": query},
            {"$group": {
                "_id": "$endpoint",
                "count": {"$sum": 1},
                "avg_execution_ms": {"$avg": "$execution_time_ms"}
            }},
            {"$sort": {"count": -1}}
        ]
        
        by_endpoint = await self.db[self.collection].aggregate(pipeline).to_list(20)
        
        return {
            "total_decisions": total,
            "by_endpoint": by_endpoint,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
