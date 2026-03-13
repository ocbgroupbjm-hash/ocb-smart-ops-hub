# ENDPOINT AUTH AUDIT

**Generated:** 2026-03-13T21:53:41.710665+00:00

## Protected Endpoints

| Endpoint | Method | Required Role | Status |
|----------|--------|---------------|--------|
| /api/audit/logs | GET | admin | ✅ Protected |
| /api/users | GET | admin | ✅ Protected |
| /api/ar/list | GET | authenticated | ✅ Protected |
| /api/ap/list | GET | authenticated | ✅ Protected |
| /api/sales | GET | authenticated | ✅ Protected |

## Summary

All sensitive endpoints require authentication.
Admin endpoints additionally require admin/owner role.
