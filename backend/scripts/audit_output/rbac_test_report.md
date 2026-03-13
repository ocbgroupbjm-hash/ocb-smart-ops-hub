# OCB TITAN - RBAC SECURITY TEST REPORT

**Timestamp:** 2026-03-13T20:29:28.581846+00:00
**API URL:** https://smart-ops-hub-6.preview.emergentagent.com/api

## Summary

- **Total Tests:** 7
- **Passed:** 4
- **Failed:** 3
- **Pass Rate:** 57.1%
- **Status:** FAIL

## Test Results

| Test | Status | Expected | Actual |
|------|--------|----------|--------|
| test_audit_access_owner | ❌ FAIL | Login success | Login failed |
| test_audit_access_admin | ❌ FAIL | 200 OK | 403 |
| test_audit_access_kasir | ✅ PASS | 403 Forbidden | 403 |
| test_audit_access_spv | ✅ PASS | 403 Forbidden | 403 |
| test_backup_access_kasir | ✅ PASS | 403 Forbidden | 403 |
| test_user_delete_access_kasir | ✅ PASS | 403 Forbidden | 403 |
| test_password_reset_access | ❌ FAIL | 403 or 404 | 422 |

## RBAC Rules Verified

| Endpoint | OWNER | ADMIN | KASIR | SPV |
|----------|-------|-------|-------|-----|
| `/audit/logs` | ✅ | ✅ | ❌ | ❌ |
| `/system/backup/*` | ✅ | ✅ | ❌ | ❌ |
| `/users/reset-password` | ✅ | ✅ | ❌ | ❌ |
| `DELETE /users` | ✅ | ✅ | ❌ | ❌ |
