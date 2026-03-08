from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import uuid

class AnalyticsEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str
    branch_id: Optional[str] = None
    event_type: str  # sale, customer_interaction, inventory_update, ai_query
    event_data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DashboardStats(BaseModel):
    total_customers: int = 0
    total_conversations: int = 0
    total_sales: float = 0.0
    active_branches: int = 0
    ai_queries_today: int = 0
    avg_sentiment: Optional[str] = None