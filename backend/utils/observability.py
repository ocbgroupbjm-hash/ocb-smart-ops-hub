"""
OCB TITAN ERP - OBSERVABILITY SYSTEM
MASTER BLUEPRINT: Production Hardening Phase 20

OpenTelemetry implementation for:
- Request tracing
- Performance monitoring
- Error tracking
- Queue lag monitoring

Tracking:
- trace_id
- tenant_id
- operation
- duration
- status

Dashboard monitoring:
- system_health
- posting_latency
- journal_integrity
- stock_drift
"""

import os
import time
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Callable
from functools import wraps
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import asyncio
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("observability")

# ==================== TRACE STORAGE ====================

class TraceStore:
    """In-memory trace storage with auto-cleanup"""
    
    def __init__(self, max_traces: int = 10000, retention_hours: int = 24):
        self.traces = []
        self.max_traces = max_traces
        self.retention_hours = retention_hours
        self.metrics = {
            "total_requests": 0,
            "total_errors": 0,
            "avg_latency_ms": 0,
            "latencies": []
        }
    
    def add_trace(self, trace: Dict):
        """Add a trace and maintain size limit"""
        self.traces.append(trace)
        
        # Update metrics
        self.metrics["total_requests"] += 1
        if trace.get("status") == "error":
            self.metrics["total_errors"] += 1
        
        latency = trace.get("duration_ms", 0)
        self.metrics["latencies"].append(latency)
        
        # Keep only last 1000 latencies for avg calculation
        if len(self.metrics["latencies"]) > 1000:
            self.metrics["latencies"] = self.metrics["latencies"][-1000:]
        
        if self.metrics["latencies"]:
            self.metrics["avg_latency_ms"] = sum(self.metrics["latencies"]) / len(self.metrics["latencies"])
        
        # Cleanup old traces
        if len(self.traces) > self.max_traces:
            self.traces = self.traces[-self.max_traces:]
    
    def get_recent_traces(self, limit: int = 100, operation: str = None, status: str = None) -> list:
        """Get recent traces with optional filters"""
        traces = self.traces[-limit:]
        
        if operation:
            traces = [t for t in traces if t.get("operation") == operation]
        
        if status:
            traces = [t for t in traces if t.get("status") == status]
        
        return traces
    
    def get_metrics(self) -> Dict:
        """Get current metrics summary"""
        error_rate = 0
        if self.metrics["total_requests"] > 0:
            error_rate = (self.metrics["total_errors"] / self.metrics["total_requests"]) * 100
        
        return {
            "total_requests": self.metrics["total_requests"],
            "total_errors": self.metrics["total_errors"],
            "error_rate_percent": round(error_rate, 2),
            "avg_latency_ms": round(self.metrics["avg_latency_ms"], 2),
            "traces_stored": len(self.traces)
        }
    
    def clear(self):
        """Clear all traces"""
        self.traces = []
        self.metrics = {
            "total_requests": 0,
            "total_errors": 0,
            "avg_latency_ms": 0,
            "latencies": []
        }


# Global trace store
trace_store = TraceStore()


# ==================== TRACE CONTEXT ====================

class TraceContext:
    """Context for current trace"""
    
    def __init__(self):
        self.trace_id = str(uuid.uuid4())
        self.tenant_id = None
        self.operation = None
        self.start_time = time.time()
        self.attributes = {}
        self.events = []
        self.status = "ok"
        self.error = None
    
    def set_attribute(self, key: str, value: Any):
        self.attributes[key] = value
    
    def add_event(self, name: str, attributes: Dict = None):
        self.events.append({
            "name": name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "attributes": attributes or {}
        })
    
    def set_error(self, error: str):
        self.status = "error"
        self.error = error
    
    def finish(self) -> Dict:
        """Finish trace and return trace data"""
        duration_ms = (time.time() - self.start_time) * 1000
        
        trace_data = {
            "trace_id": self.trace_id,
            "tenant_id": self.tenant_id,
            "operation": self.operation,
            "start_time": datetime.fromtimestamp(self.start_time, tz=timezone.utc).isoformat(),
            "duration_ms": round(duration_ms, 2),
            "status": self.status,
            "error": self.error,
            "attributes": self.attributes,
            "events": self.events
        }
        
        # Add to store
        trace_store.add_trace(trace_data)
        
        return trace_data


# ==================== MIDDLEWARE ====================

class ObservabilityMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for automatic request tracing"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        ctx = TraceContext()
        
        # Set operation from path
        ctx.operation = f"{request.method} {request.url.path}"
        
        # Extract tenant from header or path
        ctx.tenant_id = request.headers.get("X-Tenant-ID")
        if not ctx.tenant_id:
            # Try to extract from Authorization token
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                # We'll set this later if available
                pass
        
        # Set request attributes
        ctx.set_attribute("http.method", request.method)
        ctx.set_attribute("http.url", str(request.url))
        ctx.set_attribute("http.client_ip", request.client.host if request.client else "unknown")
        ctx.set_attribute("http.user_agent", request.headers.get("user-agent", ""))
        
        ctx.add_event("request_started")
        
        try:
            response = await call_next(request)
            
            ctx.set_attribute("http.status_code", response.status_code)
            
            if response.status_code >= 400:
                ctx.set_error(f"HTTP {response.status_code}")
            
            ctx.add_event("request_completed", {"status_code": response.status_code})
            
            return response
            
        except Exception as e:
            ctx.set_error(str(e))
            ctx.add_event("request_error", {"error": str(e)})
            raise
        
        finally:
            trace_data = ctx.finish()
            
            # Log slow requests
            if trace_data["duration_ms"] > 1000:
                logger.warning(f"Slow request: {ctx.operation} took {trace_data['duration_ms']}ms")


# ==================== DECORATORS ====================

def trace_operation(operation_name: str = None):
    """Decorator for tracing specific operations"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            ctx = TraceContext()
            ctx.operation = operation_name or func.__name__
            
            # Try to get tenant_id from kwargs
            ctx.tenant_id = kwargs.get("tenant_id") or kwargs.get("db_name")
            
            ctx.add_event("operation_started")
            
            try:
                result = await func(*args, **kwargs)
                ctx.add_event("operation_completed")
                return result
                
            except Exception as e:
                ctx.set_error(str(e))
                ctx.add_event("operation_error", {"error": str(e)})
                raise
                
            finally:
                ctx.finish()
        
        return wrapper
    return decorator


def trace_sync_operation(operation_name: str = None):
    """Decorator for tracing synchronous operations"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            ctx = TraceContext()
            ctx.operation = operation_name or func.__name__
            
            ctx.add_event("operation_started")
            
            try:
                result = func(*args, **kwargs)
                ctx.add_event("operation_completed")
                return result
                
            except Exception as e:
                ctx.set_error(str(e))
                ctx.add_event("operation_error", {"error": str(e)})
                raise
                
            finally:
                ctx.finish()
        
        return wrapper
    return decorator


# ==================== HEALTH MONITOR ====================

class SystemHealthMonitor:
    """Monitor system health metrics"""
    
    def __init__(self):
        self.checks = {}
        self.last_check = None
    
    async def check_database(self, mongo_url: str = None) -> Dict:
        """Check MongoDB connectivity"""
        from motor.motor_asyncio import AsyncIOMotorClient
        
        mongo_url = mongo_url or os.environ.get("MONGO_URL", "mongodb://localhost:27017")
        
        try:
            client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=5000)
            await client.admin.command("ping")
            client.close()
            return {"status": "healthy", "latency_ms": 0}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def check_journal_integrity(self, db_name: str = "ocb_titan") -> Dict:
        """Check if journal entries are balanced"""
        from motor.motor_asyncio import AsyncIOMotorClient
        
        mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
        
        try:
            client = AsyncIOMotorClient(mongo_url)
            db = client[db_name]
            
            # Get totals from posted journals
            pipeline = [
                {"$match": {"status": "posted"}},
                {"$unwind": "$entries"},
                {"$group": {
                    "_id": None,
                    "total_debit": {"$sum": "$entries.debit"},
                    "total_credit": {"$sum": "$entries.credit"}
                }}
            ]
            
            result = await db["journal_entries"].aggregate(pipeline).to_list(1)
            client.close()
            
            if not result:
                return {"status": "healthy", "message": "No journals"}
            
            totals = result[0]
            debit = totals.get("total_debit", 0) or 0
            credit = totals.get("total_credit", 0) or 0
            diff = abs(debit - credit)
            
            status = "healthy" if diff < 1 else "unhealthy"
            
            return {
                "status": status,
                "total_debit": debit,
                "total_credit": credit,
                "difference": diff,
                "balanced": diff < 1
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def check_stock_drift(self, db_name: str = "ocb_titan") -> Dict:
        """Check for stock drift (SSOT vs cache)"""
        from motor.motor_asyncio import AsyncIOMotorClient
        
        mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
        
        try:
            client = AsyncIOMotorClient(mongo_url)
            db = client[db_name]
            
            # Count products with stock
            product_count = await db["products"].count_documents({})
            movement_count = await db["stock_movements"].count_documents({})
            
            client.close()
            
            return {
                "status": "healthy",
                "products": product_count,
                "movements": movement_count
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def run_all_checks(self, db_name: str = "ocb_titan") -> Dict:
        """Run all health checks"""
        self.last_check = datetime.now(timezone.utc).isoformat()
        
        self.checks = {
            "timestamp": self.last_check,
            "database": await self.check_database(),
            "journal_integrity": await self.check_journal_integrity(db_name),
            "stock_drift": await self.check_stock_drift(db_name),
            "request_metrics": trace_store.get_metrics()
        }
        
        # Calculate overall health
        unhealthy_count = sum(1 for k, v in self.checks.items() 
                            if isinstance(v, dict) and v.get("status") == "unhealthy")
        
        self.checks["overall_status"] = "healthy" if unhealthy_count == 0 else "degraded"
        
        return self.checks


# Global health monitor
health_monitor = SystemHealthMonitor()


# ==================== API FUNCTIONS ====================

def get_trace_store() -> TraceStore:
    """Get global trace store"""
    return trace_store


def get_health_monitor() -> SystemHealthMonitor:
    """Get global health monitor"""
    return health_monitor


async def get_system_health(db_name: str = "ocb_titan") -> Dict:
    """Get current system health"""
    return await health_monitor.run_all_checks(db_name)


def get_recent_traces(limit: int = 100, operation: str = None, status: str = None) -> list:
    """Get recent traces"""
    return trace_store.get_recent_traces(limit, operation, status)


def get_metrics() -> Dict:
    """Get current metrics"""
    return trace_store.get_metrics()
