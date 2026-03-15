# ROLLBACK PLAN - PRIORITAS 7 PAYMENT ALLOCATION

## Overview
This document outlines the rollback procedure for the Payment Allocation feature in case of critical issues.

---

## 1. Components Affected

| Component | Collection/File | Action |
|-----------|-----------------|--------|
| AP Payments | ap_payments | Delete test records |
| AP Allocations | ap_payment_allocations | Delete test records |
| AR Payments | ar_payments | Delete test records |
| AR Allocations | ar_payment_allocations | Delete test records |
| Journal Entries | journal_entries | Delete payment journals |
| AP Invoices | accounts_payable | Reset test invoice status |
| AR Invoices | accounts_receivable | Reset test invoice status |

---

## 2. Rollback Procedure

### Step 1: Identify Test Data
Test data created during PRIORITAS 7 testing can be identified by:
- Supplier ID: `SUP-TEST-ALLOC-001`
- Customer ID: `CUS-TEST-ALLOC-001`
- Invoice prefixes: `AP-ALLOC-*`, `AR-ALLOC-*`
- Payment prefixes: `PAY-AP-20260315-*`, `PAY-AR-20260315-*`
- Journal references: `reference_type: ap_payment/ar_payment`

### Step 2: Rollback Commands

```python
# MongoDB Rollback Script (Run in Python)
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

async def rollback_priority7():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["ocb_titan"]
    
    # 1. Delete test AP invoices
    await db.accounts_payable.delete_many({
        "supplier_id": "SUP-TEST-ALLOC-001"
    })
    
    # 2. Delete test AR invoices
    await db.accounts_receivable.delete_many({
        "customer_id": "CUS-TEST-ALLOC-001"
    })
    
    # 3. Delete AP payments
    await db.ap_payments.delete_many({
        "supplier_id": "SUP-TEST-ALLOC-001"
    })
    
    # 4. Delete AR payments
    await db.ar_payments.delete_many({
        "customer_id": "CUS-TEST-ALLOC-001"
    })
    
    # 5. Delete AP allocations
    await db.ap_payment_allocations.delete_many({
        "invoice_no": {"$regex": "^AP-ALLOC"}
    })
    
    # 6. Delete AR allocations
    await db.ar_payment_allocations.delete_many({
        "invoice_no": {"$regex": "^AR-ALLOC"}
    })
    
    # 7. Delete test journals (CAUTION: Only if needed)
    # await db.journal_entries.delete_many({
    #     "reference_no": {"$regex": "^PAY-.*-20260315"}
    # })
    
    # 8. Delete test supplier/customer
    await db.suppliers.delete_one({"id": "SUP-TEST-ALLOC-001"})
    await db.customers.delete_one({"id": "CUS-TEST-ALLOC-001"})
    
    print("Rollback completed successfully")

asyncio.run(rollback_priority7())
```

---

## 3. Verification After Rollback

After rollback, verify:
1. No test invoices exist in `accounts_payable` and `accounts_receivable`
2. No test payments exist in `ap_payments` and `ar_payments`
3. Trial Balance is still balanced
4. No orphan allocation records

---

## 4. Production Rollback (If Code Changes Need Revert)

If the payment allocation feature code needs to be reverted:

1. **Backend Route:** `/app/backend/routes/payment_allocation_engine.py`
   - Can be disabled by removing from `server.py` includes
   
2. **Server.py Changes:**
   ```python
   # Comment out these lines in server.py:
   # from routes.payment_allocation_engine import router as payment_allocation_router
   # app.include_router(payment_allocation_router)
   ```

3. **Database Collections:**
   - `ap_payments` - Can be dropped if no production data
   - `ar_payments` - Can be dropped if no production data
   - `ap_payment_allocations` - Can be dropped if no production data
   - `ar_payment_allocations` - Can be dropped if no production data

---

## 5. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Journal corruption | Low | High | Backup before rollback |
| Data loss | Medium | High | Use soft delete first |
| Broken references | Low | Medium | Check foreign keys |
| Balance mismatch | Low | High | Run reconciliation |

---

## 6. Emergency Contact

For production issues:
- Create backup immediately
- Document the issue
- Execute rollback in stages
- Verify after each stage

---

**Document Version:** 1.0
**Created:** 2026-03-15
**Blueprint Version:** v2.1.0
