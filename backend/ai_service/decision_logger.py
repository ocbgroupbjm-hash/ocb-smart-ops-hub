# OCB TITAN ERP - AI Decision Logger
# =====================================
# Version: 1.1.0
#
# WAJIB LOG SETIAP AI RESPONSE (Sesuai PDF Governance):
# - tenant_id
# - user_id
# - request_id
# - endpoint
# - prompt_version
# - model_version
# - features_used
# - output
# - explanation
# - timestamp

"""
AI DECISION LOGGER

Logs all AI responses for audit and compliance.

REQUIRED FIELDS (from PDF governance):
- tenant_id: Tenant identifier
- user_id: User who made the request
- request_id: Unique request identifier (UUID)
- endpoint: API endpoint called
- prompt_version: Version of the prompt used
- model_version: Version of AI model
- features_used: Data features used for analysis
- output: AI output/response
- explanation: AI reasoning/explanation
- timestamp: When the request was made
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional
import uuid
import json


class AIDecisionLogger:
    """
    Logs all AI decisions to ai_decision_log collection
    
    COMPLIANCE: All AI outputs MUST be recorded per governance requirements
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
        explanation: str = "",
        prompt_version: str = "1.0.0",
        execution_time_ms: float = 0
    ) -> str:
        """
        Log an AI decision (MANDATORY per governance)
        
        All fields required by PDF governance:
        - tenant_id
        - user_id  
        - request_id (auto-generated)
        - endpoint
        - prompt_version
        - model_version
        - features_used
        - output
        - explanation
        - timestamp
        
        Returns: decision_id
        """
        decision_id = str(uuid.uuid4())
        request_id = str(uuid.uuid4())
        
        log_entry = {
            # REQUIRED FIELDS (PDF Governance)
            "id": decision_id,
            "tenant_id": tenant_id,
            "user_id": user_id,
            "request_id": request_id,
            "endpoint": endpoint,
            "prompt_version": prompt_version,
            "model_version": model_version,
            "features_used": features_used,
            "output": output,  # Full output stored
            "explanation": explanation or self._generate_explanation(output),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            
            # ADDITIONAL METRICS
            "data_window": data_window,
            "output_summary": {
                "insight_type": output.get("insight_type"),
                "recommendations_count": len(output.get("recommendations", [])),
                "has_warnings": any("⚠️" in str(r) for r in output.get("recommendations", []))
            },
            "execution_time_ms": execution_time_ms,
            "status": "completed"
        }
        
        await self.db[self.collection].insert_one(log_entry)
        
        return decision_id
    
    def _generate_explanation(self, output: Dict) -> str:
        """Generate default explanation from output"""
        insight_type = output.get("insight_type", "unknown")
        recommendations = output.get("recommendations", [])
        
        if not recommendations:
            return f"AI analysis completed for {insight_type}. No specific recommendations generated."
        
        return f"AI analysis for {insight_type} generated {len(recommendations)} recommendations based on historical data patterns."
    
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
    
    async def get_decision_by_request_id(self, request_id: str) -> Optional[Dict]:
        """Get decision by request_id for traceability"""
        return await self.db[self.collection].find_one(
            {"request_id": request_id},
            {"_id": 0}
        )
    
    async def get_decision_stats(self, tenant_id: str = None, days: int = 7) -> Dict:
        """Get AI decision statistics"""
        from datetime import timedelta
        
        query = {}
        if tenant_id:
            query["tenant_id"] = tenant_id
        
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        query["timestamp"] = {"$gte": since}
        
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
        
        # Calculate error rate (decisions without output)
        error_count = await self.db[self.collection].count_documents({
            **query,
            "status": {"$ne": "completed"}
        })
        
        return {
            "period_days": days,
            "total_decisions": total,
            "error_count": error_count,
            "error_rate": round(error_count / total * 100, 2) if total > 0 else 0,
            "by_endpoint": by_endpoint,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
