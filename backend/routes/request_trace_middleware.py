# OCB TITAN ERP - Request Trace Middleware
# Adds trace_id to all requests for end-to-end observability

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime, timezone
import uuid
import time
import logging
import json

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger("ocb_trace")

def generate_trace_id():
    """Generate unique trace ID: TRACE-YYYYMMDD-XXXXXX"""
    date_part = datetime.now(timezone.utc).strftime("%Y%m%d")
    random_part = str(uuid.uuid4())[:6].upper()
    return f"TRACE-{date_part}-{random_part}"


class RequestTraceMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add trace_id to all requests.
    
    Flow: UI → API → Worker → Database
    
    Each request gets:
    - trace_id: TRACE-YYYYMMDD-XXXXXX
    - user_id: from auth token
    - tenant_id: from active database
    - endpoint: request path
    - execution_time: milliseconds
    """
    
    async def dispatch(self, request: Request, call_next):
        # Generate or use existing trace_id from header
        trace_id = request.headers.get("X-Trace-ID")
        if not trace_id:
            trace_id = generate_trace_id()
        
        # Store trace_id in request state
        request.state.trace_id = trace_id
        
        # Extract user info if available
        user_id = "anonymous"
        tenant_id = "unknown"
        
        # Try to get from auth header
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            try:
                import jwt
                token = auth_header.replace("Bearer ", "")
                # Just decode without verification for logging
                payload = jwt.decode(token, options={"verify_signature": False})
                user_id = payload.get("user_id") or payload.get("id") or "unknown"
                tenant_id = payload.get("tenant_id") or payload.get("db_name") or "unknown"
            except Exception:
                pass
        
        # Track start time
        start_time = time.time()
        
        # Process request
        response = None
        error_message = None
        status_code = 500
        
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            error_message = str(e)
            raise
        finally:
            # Calculate execution time
            execution_time_ms = round((time.time() - start_time) * 1000, 2)
            
            # Create structured log entry
            log_entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "trace_id": trace_id,
                "user_id": user_id,
                "tenant_id": tenant_id,
                "method": request.method,
                "endpoint": str(request.url.path),
                "query_params": str(request.query_params) if request.query_params else None,
                "status_code": status_code,
                "execution_time_ms": execution_time_ms,
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("User-Agent", "")[:100],
                "error": error_message
            }
            
            # Log based on status
            if status_code >= 500:
                logger.error(json.dumps(log_entry))
            elif status_code >= 400:
                logger.warning(json.dumps(log_entry))
            elif execution_time_ms > 5000:  # Slow query > 5s
                logger.warning(json.dumps({**log_entry, "slow_query": True}))
            else:
                logger.info(json.dumps(log_entry))
        
        # Add trace_id to response headers
        if response:
            response.headers["X-Trace-ID"] = trace_id
        
        return response


# Metrics storage (in-memory for simplicity)
_metrics_store = {
    "request_count": 0,
    "error_count": 0,
    "total_latency_ms": 0,
    "slow_queries": 0,
    "endpoints": {},
    "last_reset": datetime.now(timezone.utc).isoformat()
}


def record_metric(endpoint: str, status_code: int, latency_ms: float):
    """Record request metrics"""
    _metrics_store["request_count"] += 1
    _metrics_store["total_latency_ms"] += latency_ms
    
    if status_code >= 500:
        _metrics_store["error_count"] += 1
    
    if latency_ms > 5000:
        _metrics_store["slow_queries"] += 1
    
    # Per-endpoint tracking
    if endpoint not in _metrics_store["endpoints"]:
        _metrics_store["endpoints"][endpoint] = {
            "count": 0,
            "errors": 0,
            "total_latency": 0
        }
    
    _metrics_store["endpoints"][endpoint]["count"] += 1
    _metrics_store["endpoints"][endpoint]["total_latency"] += latency_ms
    if status_code >= 500:
        _metrics_store["endpoints"][endpoint]["errors"] += 1


def get_metrics():
    """Get current metrics"""
    metrics = _metrics_store.copy()
    
    # Calculate averages
    if metrics["request_count"] > 0:
        metrics["avg_latency_ms"] = round(
            metrics["total_latency_ms"] / metrics["request_count"], 2
        )
        metrics["error_rate"] = round(
            (metrics["error_count"] / metrics["request_count"]) * 100, 2
        )
    else:
        metrics["avg_latency_ms"] = 0
        metrics["error_rate"] = 0
    
    # Add endpoint stats
    endpoint_stats = []
    for ep, data in metrics["endpoints"].items():
        if data["count"] > 0:
            endpoint_stats.append({
                "endpoint": ep,
                "count": data["count"],
                "avg_latency_ms": round(data["total_latency"] / data["count"], 2),
                "error_rate": round((data["errors"] / data["count"]) * 100, 2)
            })
    
    metrics["top_endpoints"] = sorted(
        endpoint_stats, 
        key=lambda x: x["count"], 
        reverse=True
    )[:10]
    
    return metrics


def reset_metrics():
    """Reset metrics"""
    global _metrics_store
    _metrics_store = {
        "request_count": 0,
        "error_count": 0,
        "total_latency_ms": 0,
        "slow_queries": 0,
        "endpoints": {},
        "last_reset": datetime.now(timezone.utc).isoformat()
    }
