# OCB TITAN ERP - Observability System
# =====================================
# OpenTelemetry-style observability with tracing, metrics, and logging
#
# Features:
# - Request tracing (trace_id, request_id, tenant_id)
# - API latency monitoring
# - Error rate tracking
# - System metrics collection
# - Query performance monitoring

from fastapi import APIRouter, Request, Response, HTTPException, Depends
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from functools import wraps
import uuid
import time
import os
import psutil
import asyncio

router = APIRouter(prefix="/api/observability", tags=["Observability"])

# Import dependencies
from utils.auth import get_current_user
from database import get_db, get_active_db_name


# ==================== TRACING CONTEXT ====================

class TraceContext:
    """Thread-local-like trace context for request tracing"""
    _context = {}
    
    @classmethod
    def set(cls, trace_id: str, request_id: str, tenant_id: str, user_id: str = None):
        cls._context = {
            "trace_id": trace_id,
            "request_id": request_id,
            "tenant_id": tenant_id,
            "user_id": user_id,
            "started_at": datetime.now(timezone.utc).isoformat()
        }
    
    @classmethod
    def get(cls):
        return cls._context.copy()
    
    @classmethod
    def clear(cls):
        cls._context = {}


# ==================== METRICS STORAGE ====================

# In-memory metrics storage (for demo - production would use Prometheus/InfluxDB)
class MetricsStore:
    """In-memory metrics storage"""
    
    def __init__(self):
        self.api_latencies: List[Dict] = []
        self.error_counts: Dict[str, int] = {}
        self.request_counts: Dict[str, int] = {}
        self.active_requests: int = 0
        self.max_latencies = 10000  # Keep last 10000 records
    
    def record_latency(self, endpoint: str, method: str, latency_ms: float, 
                       status_code: int, tenant_id: str = None, trace_id: str = None):
        """Record API latency"""
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "endpoint": endpoint,
            "method": method,
            "latency_ms": latency_ms,
            "status_code": status_code,
            "tenant_id": tenant_id,
            "trace_id": trace_id
        }
        self.api_latencies.append(record)
        
        # Trim old records
        if len(self.api_latencies) > self.max_latencies:
            self.api_latencies = self.api_latencies[-self.max_latencies:]
        
        # Update counts
        key = f"{method}:{endpoint}"
        self.request_counts[key] = self.request_counts.get(key, 0) + 1
        
        # Track errors
        if status_code >= 400:
            error_key = f"{status_code}:{endpoint}"
            self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
    
    def get_stats(self, minutes: int = 60):
        """Get statistics for last N minutes"""
        since = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        since_str = since.isoformat()
        
        recent = [r for r in self.api_latencies if r["timestamp"] >= since_str]
        
        if not recent:
            return {
                "period_minutes": minutes,
                "total_requests": 0,
                "avg_latency_ms": 0,
                "p50_latency_ms": 0,
                "p95_latency_ms": 0,
                "p99_latency_ms": 0,
                "error_rate": 0,
                "requests_per_minute": 0
            }
        
        latencies = [r["latency_ms"] for r in recent]
        latencies.sort()
        
        errors = sum(1 for r in recent if r["status_code"] >= 400)
        
        def percentile(data, p):
            idx = int(len(data) * p / 100)
            return data[min(idx, len(data) - 1)]
        
        return {
            "period_minutes": minutes,
            "total_requests": len(recent),
            "avg_latency_ms": round(sum(latencies) / len(latencies), 2),
            "p50_latency_ms": round(percentile(latencies, 50), 2),
            "p95_latency_ms": round(percentile(latencies, 95), 2),
            "p99_latency_ms": round(percentile(latencies, 99), 2),
            "error_rate": round(errors / len(recent) * 100, 2),
            "requests_per_minute": round(len(recent) / minutes, 2)
        }


# Global metrics store
metrics_store = MetricsStore()


# ==================== MIDDLEWARE HELPER ====================

async def trace_request(request: Request, call_next):
    """Middleware to trace all requests"""
    trace_id = str(uuid.uuid4())
    request_id = str(uuid.uuid4())
    tenant_id = get_active_db_name()
    
    # Set trace context
    TraceContext.set(trace_id, request_id, tenant_id)
    
    # Add trace headers to response
    start_time = time.time()
    metrics_store.active_requests += 1
    
    try:
        response = await call_next(request)
        
        latency_ms = (time.time() - start_time) * 1000
        
        # Record metrics
        metrics_store.record_latency(
            endpoint=request.url.path,
            method=request.method,
            latency_ms=latency_ms,
            status_code=response.status_code,
            tenant_id=tenant_id,
            trace_id=trace_id
        )
        
        # Add trace headers
        response.headers["X-Trace-ID"] = trace_id
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{latency_ms:.2f}ms"
        
        return response
    finally:
        metrics_store.active_requests -= 1
        TraceContext.clear()


# ==================== API ENDPOINTS ====================

def require_admin(user: dict = Depends(get_current_user)):
    """Require admin or super_admin role"""
    role = user.get("role_code") or user.get("role") or ""
    if role.lower() not in ["super_admin", "owner", "admin"]:
        raise HTTPException(status_code=403, detail="Observability hanya dapat diakses oleh Admin atau Super Admin")
    return user


@router.get("/health")
async def get_observability_health():
    """Get observability system health"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metrics_store_size": len(metrics_store.api_latencies),
        "active_requests": metrics_store.active_requests
    }


@router.get("/metrics")
async def get_metrics(
    minutes: int = 60,
    user: dict = Depends(require_admin)
):
    """Get API metrics for last N minutes"""
    stats = metrics_store.get_stats(minutes)
    
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "tenant_id": get_active_db_name(),
        "stats": stats,
        "error_counts": dict(list(metrics_store.error_counts.items())[:20]),
        "top_endpoints": dict(sorted(
            metrics_store.request_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:20])
    }


@router.get("/system")
async def get_system_metrics(user: dict = Depends(require_admin)):
    """Get system-level metrics (CPU, memory, disk)"""
    
    cpu_percent = psutil.cpu_percent(interval=0.5)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Network I/O
    net_io = psutil.net_io_counters()
    
    # Load average (Linux only)
    try:
        load_avg = os.getloadavg()
    except:
        load_avg = [0, 0, 0]
    
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cpu": {
            "percent": cpu_percent,
            "count": psutil.cpu_count(),
            "load_avg_1m": load_avg[0],
            "load_avg_5m": load_avg[1],
            "load_avg_15m": load_avg[2]
        },
        "memory": {
            "total_gb": round(memory.total / (1024**3), 2),
            "used_gb": round(memory.used / (1024**3), 2),
            "available_gb": round(memory.available / (1024**3), 2),
            "percent": memory.percent
        },
        "disk": {
            "total_gb": round(disk.total / (1024**3), 2),
            "used_gb": round(disk.used / (1024**3), 2),
            "free_gb": round(disk.free / (1024**3), 2),
            "percent": disk.percent
        },
        "network": {
            "bytes_sent": net_io.bytes_sent,
            "bytes_recv": net_io.bytes_recv,
            "packets_sent": net_io.packets_sent,
            "packets_recv": net_io.packets_recv
        }
    }


@router.get("/traces/recent")
async def get_recent_traces(
    limit: int = 100,
    user: dict = Depends(require_admin)
):
    """Get recent trace records"""
    recent = metrics_store.api_latencies[-limit:]
    recent.reverse()  # Most recent first
    
    return {
        "total": len(recent),
        "traces": recent
    }


@router.get("/traces/{trace_id}")
async def get_trace(trace_id: str, user: dict = Depends(require_admin)):
    """Get specific trace by ID"""
    for record in metrics_store.api_latencies:
        if record.get("trace_id") == trace_id:
            return record
    
    raise HTTPException(status_code=404, detail=f"Trace '{trace_id}' not found")


@router.get("/errors")
async def get_error_summary(
    minutes: int = 60,
    user: dict = Depends(require_admin)
):
    """Get error summary for last N minutes"""
    since = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    since_str = since.isoformat()
    
    recent_errors = [
        r for r in metrics_store.api_latencies 
        if r["timestamp"] >= since_str and r["status_code"] >= 400
    ]
    
    # Group by status code
    by_status = {}
    for e in recent_errors:
        code = e["status_code"]
        if code not in by_status:
            by_status[code] = []
        by_status[code].append(e)
    
    return {
        "period_minutes": minutes,
        "total_errors": len(recent_errors),
        "by_status_code": {k: len(v) for k, v in by_status.items()},
        "recent_errors": recent_errors[:50]
    }


@router.get("/tenant-activity")
async def get_tenant_activity(
    minutes: int = 60,
    user: dict = Depends(require_admin)
):
    """Get activity by tenant"""
    since = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    since_str = since.isoformat()
    
    recent = [r for r in metrics_store.api_latencies if r["timestamp"] >= since_str]
    
    # Group by tenant
    by_tenant = {}
    for r in recent:
        tenant = r.get("tenant_id") or "unknown"
        if tenant not in by_tenant:
            by_tenant[tenant] = {"count": 0, "total_latency": 0, "errors": 0}
        by_tenant[tenant]["count"] += 1
        by_tenant[tenant]["total_latency"] += r["latency_ms"]
        if r["status_code"] >= 400:
            by_tenant[tenant]["errors"] += 1
    
    # Calculate averages
    for tenant, data in by_tenant.items():
        data["avg_latency_ms"] = round(data["total_latency"] / data["count"], 2) if data["count"] > 0 else 0
        data["error_rate"] = round(data["errors"] / data["count"] * 100, 2) if data["count"] > 0 else 0
        del data["total_latency"]
    
    return {
        "period_minutes": minutes,
        "tenants": by_tenant
    }


@router.get("/query-performance")
async def get_query_performance(user: dict = Depends(require_admin)):
    """Get database query performance metrics"""
    db = get_db()
    
    # Get MongoDB server status
    try:
        server_status = await db.command("serverStatus")
        opcounters = server_status.get("opcounters", {})
        connections = server_status.get("connections", {})
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "database": get_active_db_name(),
            "operations": {
                "insert": opcounters.get("insert", 0),
                "query": opcounters.get("query", 0),
                "update": opcounters.get("update", 0),
                "delete": opcounters.get("delete", 0)
            },
            "connections": {
                "current": connections.get("current", 0),
                "available": connections.get("available", 0),
                "total_created": connections.get("totalCreated", 0)
            }
        }
    except Exception as e:
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "database": get_active_db_name(),
            "error": str(e)
        }


@router.get("/dashboard")
async def get_observability_dashboard(user: dict = Depends(require_admin)):
    """Get complete observability dashboard"""
    
    # Get all metrics
    stats_1h = metrics_store.get_stats(60)
    stats_24h = metrics_store.get_stats(1440)
    
    cpu_percent = psutil.cpu_percent(interval=0.5)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "tenant_id": get_active_db_name(),
        "api_metrics": {
            "last_1h": stats_1h,
            "last_24h": stats_24h
        },
        "system_health": {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "disk_percent": disk.percent,
            "status": "healthy" if cpu_percent < 80 and memory.percent < 80 else "warning"
        },
        "active_requests": metrics_store.active_requests,
        "top_errors": dict(sorted(
            metrics_store.error_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10])
    }
