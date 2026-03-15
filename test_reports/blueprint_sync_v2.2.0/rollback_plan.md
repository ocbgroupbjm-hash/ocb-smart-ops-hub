# ROLLBACK PLAN - Blueprint v2.2.0 Multi-Tenant Sync

## Overview
This document outlines the rollback procedure for the Blueprint v2.2.0 multi-tenant synchronization.

---

## 1. What Was Synced

| Tenant | Database | Previous Version | New Version |
|--------|----------|------------------|-------------|
| OCB GROUP | ocb_titan | 2.1.0 | 2.2.0 |
| OCB UNIT 4 MPC & MP3 | ocb_unit_4 | 2.1.0 | 2.2.0 |
| OCB UNIT 1 RETAIL | ocb_unt_1 | 2.1.0 | 2.2.0 |

---

## 2. Collections Created/Verified

The following collections were ensured to exist in all tenants:
- `journal_entries`, `journal_lines`, `accounts`, `journals`
- `ap_invoices`, `ap_payments`, `ap_payment_allocations`
- `ar_invoices`, `ar_payments`, `ar_payment_allocations`
- `employees`, `attendance_logs`, `payroll`, `leave_requests`
- `kpi_targets`, `kpi_results`
- `inventory_serial_numbers`, `stock_movements`, `products`

---

## 3. Rollback Procedure

### Step 1: Revert Blueprint Version in Metadata

```python
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

async def rollback_blueprint():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    
    tenants = ["ocb_titan", "ocb_unit_4", "ocb_unt_1"]
    
    for db_name in tenants:
        db = client[db_name]
        await db["_tenant_metadata"].update_one(
            {},
            {"$set": {
                "blueprint_version": "2.1.0",
                "rollback_from": "2.2.0",
                "rollback_at": "2026-03-15T00:00:00Z"
            }}
        )
        print(f"Reverted {db_name} to v2.1.0")
    
    client.close()

asyncio.run(rollback_blueprint())
```

### Step 2: Remove v2.2.0 Lock Record (Optional)

```python
async def remove_version_lock():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["erp_db"]
    
    await db["blueprint_versions"].delete_one({"version": "2.2.0"})
    
    client.close()
```

### Step 3: Verify Rollback

After rollback, verify:
1. All tenants show `blueprint_version: "2.1.0"`
2. Application continues to function normally
3. No data loss has occurred

---

## 4. Features That Would Be Unavailable After Rollback

If rollback is performed, the following features would need code revert:
- PRIORITAS 7: AP/AR Payment Allocation improvements

Note: The core payment allocation code would still exist, only the version marker changes.

---

## 5. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Data loss | Very Low | High | No data modified, only metadata |
| Feature regression | Low | Medium | Code still deployed |
| Version mismatch | Low | Low | Sync can be re-run |

---

## 6. Decision Matrix

| Scenario | Action |
|----------|--------|
| Minor bug found | Fix forward, no rollback |
| Critical bug in payment allocation | Disable feature flag, fix, re-sync |
| Data corruption | Restore from backup, then rollback |
| Performance degradation | Investigate first, rollback only if necessary |

---

**Document Version:** 1.0
**Created:** 2026-03-15
**Blueprint Version:** v2.2.0
