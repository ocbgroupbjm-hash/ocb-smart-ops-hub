# OCB TITAN - Tenant Isolation Middleware
# Ensures each request uses the correct tenant database based on JWT token
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from database import set_active_db_name, get_default_db_name
from utils.auth import decode_token
import re

# Routes that don't require tenant isolation (public/system routes)
TENANT_EXEMPT_ROUTES = [
    r'^/api/auth/login$',
    r'^/api/auth/register$',
    r'^/api/business/list$',
    r'^/api/business/switch/',
    r'^/api/business/ensure-admin/',
    r'^/api/system/',
    r'^/api/tenant-registry/',
    r'^/api/health$',
    r'^/docs',
    r'^/openapi.json',
    r'^/$',
]

class TenantIsolationMiddleware(BaseHTTPMiddleware):
    """
    Middleware that ensures tenant isolation for each request.
    
    Flow:
    1. Extract tenant_id from JWT token
    2. If no tenant in token, use X-Tenant-ID header
    3. If no header, use default database
    4. Set the database for this request context
    """
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        
        # Check if route is exempt from tenant isolation
        for pattern in TENANT_EXEMPT_ROUTES:
            if re.match(pattern, path):
                # Use default database for exempt routes
                set_active_db_name(get_default_db_name())
                return await call_next(request)
        
        # Try to get tenant_id from JWT token
        tenant_id = None
        
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
            payload = decode_token(token)
            if payload:
                # Priority 1: tenant_id from token
                tenant_id = payload.get('tenant_id') or payload.get('db_name')
        
        # Priority 2: X-Tenant-ID header
        if not tenant_id:
            tenant_id = request.headers.get('X-Tenant-ID')
        
        # Priority 3: Query parameter (for specific cases)
        if not tenant_id:
            tenant_id = request.query_params.get('tenant_id')
        
        # Priority 4: Default database
        if not tenant_id:
            tenant_id = get_default_db_name()
        
        # Set the database for this request context
        set_active_db_name(tenant_id)
        
        # Log tenant routing for debugging
        # print(f"[TENANT] {request.method} {path} -> {tenant_id}")
        
        response = await call_next(request)
        return response
