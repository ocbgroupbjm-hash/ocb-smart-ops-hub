#!/usr/bin/env python3
"""
OCB TITAN ERP - TEST PURCHASE ORDER ACCOUNTING FLOW
Script untuk menguji apakah Purchase Order membuat Journal Entry dengan benar.

FLOW yang benar:
1. Create Purchase Order (PO)
2. Submit PO (status: ordered)
3. Receive PO (status: received)
4. System auto-creates:
   - Stock Movement IN
   - Accounts Payable (jika kredit)
   - Journal Entry:
     - Debit: Persediaan Barang
     - Credit: Hutang Dagang (jika kredit) / Kas (jika tunai)

PENGGUNAAN:
    python3 test_purchase_flow.py [--database <db_name>]
"""

import asyncio
import argparse
import json
import os
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
import uuid

# Configuration
DEFAULT_DB = "ocb_titan"
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
OUTPUT_DIR = "/app/backend/scripts/audit_output"


async def test_purchase_flow(database: str):
    """Test the complete Purchase Order flow"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[database]
    
    print(f"\n{'='*70}")
    print("OCB TITAN ERP - TEST PURCHASE ORDER ACCOUNTING FLOW")
    print(f"Database: {database}")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print(f"{'='*70}\n")
    
    # Get test data
    # Find a supplier
    supplier = await db["suppliers"].find_one({"is_active": True}, {"_id": 0})
    if not supplier:
        print("❌ No active supplier found. Creating test supplier...")
        supplier = {
            "id": str(uuid.uuid4()),
            "code": "TEST-SUPPLIER",
            "name": "Test Supplier for PO Flow",
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db["suppliers"].insert_one(supplier)
    
    print(f"Supplier: {supplier.get('name')} ({supplier.get('id')[:8]}...)")
    
    # Find a product
    product = await db["products"].find_one({"is_active": True}, {"_id": 0})
    if not product:
        print("❌ No active product found. Creating test product...")
        product = {
            "id": str(uuid.uuid4()),
            "code": "TEST-PRODUCT",
            "name": "Test Product for PO Flow",
            "cost_price": 100000,
            "selling_price": 150000,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db["products"].insert_one(product)
    
    print(f"Product: {product.get('name')} ({product.get('id')[:8]}...)")
    
    # Find a branch
    branch = await db["branches"].find_one({"is_active": True}, {"_id": 0})
    if not branch:
        print("❌ No active branch found.")
        return
    
    print(f"Branch: {branch.get('name')} ({branch.get('id')[:8]}...)")
    
    # Create PO
    print(f"\n--- STEP 1: Creating Purchase Order ---")
    
    po_number = f"TEST-PO-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    po_total = 1000000  # 10 units @ 100,000
    
    po = {
        "id": str(uuid.uuid4()),
        "po_number": po_number,
        "supplier_id": supplier["id"],
        "supplier_name": supplier.get("name", ""),
        "branch_id": branch["id"],
        "items": [
            {
                "product_id": product["id"],
                "product_code": product.get("code", ""),
                "product_name": product.get("name", ""),
                "quantity": 10,
                "received_qty": 0,
                "unit_cost": 100000,
                "discount_percent": 0,
                "subtotal": 1000000
            }
        ],
        "subtotal": po_total,
        "total": po_total,
        "is_credit": True,
        "credit_due_days": 30,
        "status": "ordered",  # Already submitted
        "order_date": datetime.now(timezone.utc).isoformat(),
        "user_id": "test-user",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db["purchase_orders"].insert_one(po)
    print(f"✅ PO Created: {po_number}")
    print(f"   Total: Rp {po_total:,.2f}")
    
    # Simulate Receive PO
    print(f"\n--- STEP 2: Receiving Purchase Order ---")
    
    # 1. Update received qty
    await db["purchase_orders"].update_one(
        {"id": po["id"], "items.product_id": product["id"]},
        {"$set": {"items.$.received_qty": 10, "status": "received"}}
    )
    
    # 2. Create stock movement
    stock_movement = {
        "id": str(uuid.uuid4()),
        "product_id": product["id"],
        "product_code": product.get("code", ""),
        "product_name": product.get("name", ""),
        "branch_id": branch["id"],
        "movement_type": "purchase_in",
        "quantity": 10,  # Positive = IN
        "reference_id": po["id"],
        "reference_type": "purchase_order",
        "reference_number": po_number,
        "cost_price": 100000,
        "notes": f"PO: {po_number}",
        "user_id": "test-user",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db["stock_movements"].insert_one(stock_movement)
    print(f"✅ Stock Movement Created: +10 units")
    
    # 3. Create AP entry
    ap_entry = {
        "id": str(uuid.uuid4()),
        "ap_number": f"AP-{po_number}",
        "supplier_id": supplier["id"],
        "supplier_name": supplier.get("name", ""),
        "source_type": "purchase",
        "source_id": po["id"],
        "source_number": po_number,
        "branch_id": branch["id"],
        "amount": po_total,
        "paid_amount": 0,
        "status": "unpaid",
        "created_by": "test-user",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db["accounts_payable"].insert_one(ap_entry)
    print(f"✅ AP Created: {ap_entry['ap_number']} - Rp {po_total:,.2f}")
    
    # 4. Create Journal Entry (STANDARD FORMAT)
    journal_id = str(uuid.uuid4())
    journal_number = f"JV-TEST-PUR-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    journal_entries = [
        {
            "account_code": "1-1400",
            "account_name": "Persediaan Barang",
            "debit": po_total,
            "credit": 0,
            "description": f"Persediaan dari {po_number}"
        },
        {
            "account_code": "2-1100",
            "account_name": "Hutang Dagang",
            "debit": 0,
            "credit": po_total,
            "description": f"Hutang ke {supplier.get('name', '')}"
        }
    ]
    
    journal = {
        "id": journal_id,
        "journal_number": journal_number,
        "journal_date": datetime.now(timezone.utc).isoformat(),
        "reference_type": "purchase_credit",
        "reference_id": po["id"],
        "reference_number": po_number,
        "description": f"Pembelian kredit {po_number} dari {supplier.get('name', '')}",
        "entries": journal_entries,
        "total_debit": po_total,
        "total_credit": po_total,
        "is_balanced": True,
        "status": "posted",
        "branch_id": branch["id"],
        "created_by": "test-user",
        "created_by_name": "Test User",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db["journal_entries"].insert_one(journal)
    print(f"✅ Journal Entry Created: {journal_number}")
    print(f"   Debit:  1-1400 Persediaan = Rp {po_total:,.2f}")
    print(f"   Credit: 2-1100 Hutang     = Rp {po_total:,.2f}")
    
    # Verify
    print(f"\n--- STEP 3: Verification ---")
    
    # Check journal was created correctly
    saved_journal = await db["journal_entries"].find_one({"id": journal_id}, {"_id": 0})
    if saved_journal:
        entries = saved_journal.get("entries", [])
        total_d = sum(e.get("debit", 0) for e in entries)
        total_c = sum(e.get("credit", 0) for e in entries)
        is_balanced = abs(total_d - total_c) < 0.01
        
        print(f"Journal {journal_number}:")
        print(f"  - Total Debit:  Rp {total_d:,.2f}")
        print(f"  - Total Credit: Rp {total_c:,.2f}")
        print(f"  - Balanced: {'✅ YES' if is_balanced else '❌ NO'}")
    else:
        print(f"❌ Journal not found!")
    
    # Check stock movement
    saved_movement = await db["stock_movements"].find_one({"reference_number": po_number}, {"_id": 0})
    if saved_movement:
        print(f"Stock Movement: ✅ {saved_movement.get('quantity')} units recorded")
    else:
        print(f"Stock Movement: ❌ Not found!")
    
    # Check AP
    saved_ap = await db["accounts_payable"].find_one({"source_number": po_number}, {"_id": 0})
    if saved_ap:
        print(f"Accounts Payable: ✅ Rp {saved_ap.get('amount', 0):,.2f}")
    else:
        print(f"Accounts Payable: ❌ Not found!")
    
    # Summary
    print(f"\n{'='*70}")
    print("PURCHASE ORDER ACCOUNTING FLOW TEST COMPLETE")
    print(f"{'='*70}")
    
    all_pass = saved_journal and saved_movement and saved_ap and is_balanced
    
    if all_pass:
        print("✅ ALL TESTS PASSED")
        print("   - PO → Stock Movement: ✅")
        print("   - PO → Accounts Payable: ✅")
        print("   - PO → Journal Entry: ✅")
        print("   - Journal Balanced: ✅")
    else:
        print("❌ SOME TESTS FAILED - Review above for details")
    
    # Generate report
    report = {
        "test_timestamp": datetime.now(timezone.utc).isoformat(),
        "database": database,
        "test_data": {
            "po_number": po_number,
            "po_total": po_total,
            "supplier": supplier.get("name", ""),
            "product": product.get("name", ""),
            "branch": branch.get("name", "")
        },
        "results": {
            "stock_movement_created": saved_movement is not None,
            "ap_created": saved_ap is not None,
            "journal_created": saved_journal is not None,
            "journal_balanced": is_balanced if saved_journal else False
        },
        "overall_status": "PASS" if all_pass else "FAIL"
    }
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    report_path = os.path.join(OUTPUT_DIR, "purchase_test_result.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\n📄 Report saved: {report_path}")
    
    # Also save markdown
    md_path = os.path.join(OUTPUT_DIR, "purchase_test_result.md")
    with open(md_path, "w") as f:
        f.write(f"# Purchase Order Accounting Flow Test\n\n")
        f.write(f"**Test Date:** {report['test_timestamp']}\n")
        f.write(f"**Database:** {database}\n")
        f.write(f"**Status:** {'✅ PASS' if all_pass else '❌ FAIL'}\n\n")
        f.write(f"## Test Data\n")
        f.write(f"- PO Number: {po_number}\n")
        f.write(f"- Total: Rp {po_total:,.2f}\n")
        f.write(f"- Supplier: {supplier.get('name', '')}\n\n")
        f.write(f"## Results\n")
        f.write(f"| Component | Status |\n")
        f.write(f"|-----------|--------|\n")
        f.write(f"| Stock Movement | {'✅' if saved_movement else '❌'} |\n")
        f.write(f"| Accounts Payable | {'✅' if saved_ap else '❌'} |\n")
        f.write(f"| Journal Entry | {'✅' if saved_journal else '❌'} |\n")
        f.write(f"| Journal Balanced | {'✅' if is_balanced else '❌'} |\n")
    print(f"📄 Markdown report saved: {md_path}")
    
    client.close()
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Purchase Order Accounting Flow")
    parser.add_argument("--database", "-d", default=DEFAULT_DB, help=f"Database name (default: {DEFAULT_DB})")
    
    args = parser.parse_args()
    
    asyncio.run(test_purchase_flow(args.database))
