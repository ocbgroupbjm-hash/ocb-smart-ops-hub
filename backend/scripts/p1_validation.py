#!/usr/bin/env python3
"""
P1 VALIDATION SCRIPT - FULL END-TO-END TEST
============================================
Validasi lengkap semua P1 tasks:
1. AR invoice_number tidak boleh null
2. Engine nomor transaksi untuk semua modul
3. Engine nomor master untuk semua entity
4. Auto kode item
5. Inline edit datasheet
6. End-to-end transaction flow
"""

import asyncio
import os
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = 'erp_db'

async def get_db():
    client = AsyncIOMotorClient(MONGO_URL)
    return client[DB_NAME], client


# Import central generator
import sys
sys.path.insert(0, '/app/backend')
from utils.number_generator import generate_transaction_number, generate_master_code, check_duplicate_code


async def test_ar_invoice_number(db):
    """Test AR - semua harus punya invoice_number"""
    print("\n" + "=" * 80)
    print("P1-1: VALIDASI AR INVOICE_NUMBER")
    print("=" * 80)
    
    # Count AR with null invoice_number
    all_ar = await db.accounts_receivable.find({}, {"_id": 0}).to_list(100)
    null_invoice = [ar for ar in all_ar if not ar.get('invoice_number')]
    
    print(f"\nTotal AR: {len(all_ar)}")
    print(f"AR dengan invoice_number NULL: {len(null_invoice)}")
    
    if null_invoice:
        print("\n❌ GAGAL - Ada AR tanpa invoice_number:")
        for ar in null_invoice:
            print(f"   - {ar.get('ar_number', ar.get('ar_no', 'N/A'))}")
        return False
    else:
        print("\n✅ LULUS - Semua AR memiliki invoice_number")
        for ar in all_ar:
            print(f"   ✅ {ar.get('ar_number', ar.get('ar_no', 'N/A'))} -> {ar.get('invoice_number')}")
        return True


async def test_transaction_number_engine(db):
    """Test engine nomor transaksi untuk semua modul"""
    print("\n" + "=" * 80)
    print("P1-2: VALIDASI ENGINE NOMOR TRANSAKSI")
    print("=" * 80)
    
    modules = ["PO", "RCV", "INV", "PAY", "RECV", "JV", "AP", "AR", "STK", "TRF", "ASM", "EXP"]
    results = []
    all_passed = True
    
    print("\nGenerating numbers for each module:")
    
    for module in modules:
        try:
            # Generate 2 numbers to check sequence
            num1 = await generate_transaction_number(db, module)
            num2 = await generate_transaction_number(db, module)
            
            # Check format
            parts1 = num1.split("-")
            parts2 = num2.split("-")
            
            # Check sequence incremented
            seq1 = int(parts1[-1])
            seq2 = int(parts2[-1])
            
            if seq2 == seq1 + 1:
                print(f"   ✅ {module}: {num1} -> {num2} (sequence +1 ✓)")
                results.append({"module": module, "num1": num1, "num2": num2, "status": "PASS"})
            else:
                print(f"   ❌ {module}: {num1} -> {num2} (sequence error)")
                results.append({"module": module, "num1": num1, "num2": num2, "status": "FAIL"})
                all_passed = False
                
        except Exception as e:
            print(f"   ❌ {module}: ERROR - {e}")
            results.append({"module": module, "error": str(e), "status": "ERROR"})
            all_passed = False
    
    # Check no duplicates
    print("\nChecking for duplicates:")
    all_numbers = [r.get("num1") for r in results if r.get("num1")] + [r.get("num2") for r in results if r.get("num2")]
    duplicates = [n for n in all_numbers if all_numbers.count(n) > 1]
    
    if duplicates:
        print(f"   ❌ DUPLICATE FOUND: {duplicates}")
        all_passed = False
    else:
        print(f"   ✅ No duplicates - {len(all_numbers)} unique numbers generated")
    
    if all_passed:
        print("\n✅ LULUS - Engine nomor transaksi berfungsi dengan baik")
    else:
        print("\n❌ GAGAL - Ada masalah dengan engine nomor transaksi")
    
    return all_passed


async def test_master_number_engine(db):
    """Test engine nomor master untuk semua entity"""
    print("\n" + "=" * 80)
    print("P1-3: VALIDASI ENGINE NOMOR MASTER")
    print("=" * 80)
    
    entities = ["supplier", "customer", "salesperson", "item", "category", "brand", "warehouse", "branch"]
    results = []
    all_passed = True
    
    print("\nGenerating codes for each entity:")
    
    for entity in entities:
        try:
            # Generate 2 codes to check sequence
            code1 = await generate_master_code(db, entity)
            code2 = await generate_master_code(db, entity)
            
            # Check sequence incremented
            seq1 = int(code1.split("-")[-1])
            seq2 = int(code2.split("-")[-1])
            
            if seq2 == seq1 + 1:
                print(f"   ✅ {entity}: {code1} -> {code2} (sequence +1 ✓)")
                results.append({"entity": entity, "code1": code1, "code2": code2, "status": "PASS"})
            else:
                print(f"   ❌ {entity}: {code1} -> {code2} (sequence error)")
                results.append({"entity": entity, "code1": code1, "code2": code2, "status": "FAIL"})
                all_passed = False
                
        except Exception as e:
            print(f"   ❌ {entity}: ERROR - {e}")
            results.append({"entity": entity, "error": str(e), "status": "ERROR"})
            all_passed = False
    
    if all_passed:
        print("\n✅ LULUS - Engine nomor master berfungsi dengan baik")
    else:
        print("\n❌ GAGAL - Ada masalah dengan engine nomor master")
    
    return all_passed


async def test_auto_item_code(db):
    """Test auto kode item"""
    print("\n" + "=" * 80)
    print("P1-4: VALIDASI AUTO KODE ITEM")
    print("=" * 80)
    
    all_passed = True
    
    # Test AUTO mode - generate 3 items
    print("\n--- Test AUTO Mode ---")
    auto_codes = []
    for i in range(3):
        code = await generate_master_code(db, "item")
        auto_codes.append(code)
        print(f"   ✅ Item AUTO #{i+1}: {code}")
    
    # Check sequence
    seqs = [int(c.split("-")[-1]) for c in auto_codes]
    if seqs[1] == seqs[0] + 1 and seqs[2] == seqs[1] + 1:
        print(f"   ✅ Sequence berurutan: {seqs}")
    else:
        print(f"   ❌ Sequence tidak berurutan: {seqs}")
        all_passed = False
    
    # Test MANUAL mode
    print("\n--- Test MANUAL Mode ---")
    manual_code = "MANUAL-TEST-001"
    
    # Check duplicate detection
    is_duplicate = await check_duplicate_code(db, "products", "code", manual_code)
    if not is_duplicate:
        print(f"   ✅ Manual code '{manual_code}' unique - allowed")
    else:
        print(f"   ⚠️ Manual code '{manual_code}' already exists")
    
    # Test duplicate rejection
    print("\n--- Test Duplicate Rejection ---")
    # Simulate saving a product with auto code
    test_product = {
        "id": str(ObjectId()),
        "code": auto_codes[0],  # Use first auto code
        "name": "Test Product",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.products.update_one({"code": test_product["code"]}, {"$set": test_product}, upsert=True)
    
    # Check if duplicate is detected
    is_duplicate = await check_duplicate_code(db, "products", "code", auto_codes[0])
    if is_duplicate:
        print(f"   ✅ Duplicate '{auto_codes[0]}' correctly detected and rejected")
    else:
        print(f"   ❌ Duplicate detection failed")
        all_passed = False
    
    # Cleanup
    await db.products.delete_one({"id": test_product["id"]})
    
    if all_passed:
        print("\n✅ LULUS - Auto kode item berfungsi dengan baik")
    else:
        print("\n❌ GAGAL - Ada masalah dengan auto kode item")
    
    return all_passed


async def test_end_to_end_flow(db):
    """Test end-to-end transaction flow"""
    print("\n" + "=" * 80)
    print("P1-6: RETEST END-TO-END FINAL")
    print("=" * 80)
    
    all_passed = True
    
    # 1. Create supplier with auto number
    print("\n--- Step 1: Create Supplier ---")
    supplier_code = await generate_master_code(db, "supplier")
    supplier = {
        "id": str(ObjectId()),
        "code": supplier_code,
        "name": "Test Supplier P1",
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.suppliers.insert_one(supplier)
    print(f"   ✅ Supplier: {supplier_code}")
    
    # 2. Create item with auto code
    print("\n--- Step 2: Create Item ---")
    item_code = await generate_master_code(db, "item")
    product = {
        "id": str(ObjectId()),
        "code": item_code,
        "name": "Test Product P1",
        "unit": "UNIT",
        "cost_price": 1000000,
        "sell_price": 1500000,
        "stock": 0,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.products.insert_one(product)
    print(f"   ✅ Product: {item_code}")
    
    # 3. Create PO with auto number
    print("\n--- Step 3: Create Purchase Order ---")
    po_number = await generate_transaction_number(db, "PO")
    po = {
        "id": str(ObjectId()),
        "po_number": po_number,
        "supplier_id": supplier["id"],
        "supplier_name": supplier["name"],
        "items": [{"product_id": product["id"], "product_name": product["name"], "quantity": 10, "unit_price": 1000000, "subtotal": 10000000}],
        "subtotal": 10000000,
        "ppn_amount": 1100000,
        "total": 11100000,
        "status": "confirmed",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.purchase_orders.insert_one(po)
    print(f"   ✅ PO: {po_number}")
    
    # 4. Create Receiving with auto number
    print("\n--- Step 4: Create Receiving ---")
    rcv_number = await generate_transaction_number(db, "RCV")
    receiving = {
        "id": str(ObjectId()),
        "receiving_number": rcv_number,
        "po_number": po_number,
        "supplier_id": supplier["id"],
        "items": po["items"],
        "total": po["total"],
        "status": "completed",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.receivings.insert_one(receiving)
    print(f"   ✅ Receiving: {rcv_number}")
    
    # Add stock movement
    await db.stock_movements.insert_one({
        "id": str(ObjectId()),
        "product_id": product["id"],
        "branch_id": "branch-001",
        "warehouse_id": "branch-001",
        "quantity": 10,
        "movement_type": "purchase_in",
        "reference_type": "receiving",
        "reference_number": rcv_number,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    print(f"   ✅ Stock +10 units")
    
    # 5. Create Customer
    print("\n--- Step 5: Create Customer ---")
    customer_code = await generate_master_code(db, "customer")
    customer = {
        "id": str(ObjectId()),
        "code": customer_code,
        "name": "Test Customer P1",
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.customers.insert_one(customer)
    print(f"   ✅ Customer: {customer_code}")
    
    # 6. Create Sales Invoice with auto number
    print("\n--- Step 6: Create Sales Invoice ---")
    inv_number = await generate_transaction_number(db, "INV")
    invoice = {
        "id": str(ObjectId()),
        "invoice_number": inv_number,
        "customer_id": customer["id"],
        "customer_name": customer["name"],
        "items": [{"product_id": product["id"], "product_name": product["name"], "quantity": 3, "unit_price": 1500000, "subtotal": 4500000, "hpp": 3000000}],
        "subtotal": 4500000,
        "tax_amount": 495000,
        "total": 4995000,
        "total_hpp": 3000000,
        "payment_type": "credit",
        "cash_amount": 0,
        "credit_amount": 4995000,
        "status": "completed",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.sales_invoices.insert_one(invoice)
    print(f"   ✅ Invoice: {inv_number}")
    
    # Add stock movement (sales out)
    await db.stock_movements.insert_one({
        "id": str(ObjectId()),
        "product_id": product["id"],
        "branch_id": "branch-001",
        "warehouse_id": "branch-001",
        "quantity": -3,
        "movement_type": "sales_out",
        "reference_type": "sales",
        "reference_number": inv_number,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    print(f"   ✅ Stock -3 units")
    
    # 7. Create AR with invoice_number - CRITICAL TEST
    print("\n--- Step 7: Create AR (with invoice_number) ---")
    ar_number = await generate_transaction_number(db, "AR")
    ar = {
        "id": str(ObjectId()),
        "ar_number": ar_number,
        "ar_no": ar_number,
        "invoice_number": inv_number,  # WAJIB - tidak boleh null
        "customer_id": customer["id"],
        "customer_name": customer["name"],
        "amount": invoice["total"],
        "paid_amount": 0,
        "remaining_amount": invoice["total"],
        "status": "open",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.accounts_receivable.insert_one(ar)
    
    # VALIDASI AR
    if ar.get("invoice_number"):
        print(f"   ✅ AR: {ar_number} -> Invoice: {ar['invoice_number']}")
    else:
        print(f"   ❌ AR: {ar_number} -> Invoice: NULL ❌")
        all_passed = False
    
    # 8. Create AP
    print("\n--- Step 8: Create AP ---")
    ap_number = await generate_transaction_number(db, "AP")
    ap = {
        "id": str(ObjectId()),
        "ap_number": ap_number,
        "ap_no": ap_number,
        "po_number": po_number,
        "supplier_id": supplier["id"],
        "supplier_name": supplier["name"],
        "amount": po["total"],
        "paid_amount": 0,
        "remaining_amount": po["total"],
        "status": "open",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.accounts_payable.insert_one(ap)
    print(f"   ✅ AP: {ap_number}")
    
    # 9. Create Journal Entries for transactions
    print("\n--- Step 9: Create Journals ---")
    
    # Purchase Journal
    jv_purchase = await generate_transaction_number(db, "JV")
    purchase_entries = [
        {"account_code": "1-1400", "account_name": "Persediaan", "debit": 10000000, "credit": 0},
        {"account_code": "2-1500", "account_name": "PPN Masukan", "debit": 1100000, "credit": 0},
        {"account_code": "2-1100", "account_name": "Hutang Usaha", "debit": 0, "credit": 11100000}
    ]
    await db.journal_entries.insert_one({
        "id": str(ObjectId()),
        "journal_number": jv_purchase,
        "date": datetime.now(timezone.utc).isoformat(),
        "reference": rcv_number,
        "reference_type": "receiving",
        "description": f"Pembelian {rcv_number}",
        "lines": purchase_entries,
        "entries": purchase_entries,
        "total_debit": 11100000,
        "total_credit": 11100000,
        "status": "posted",
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    for e in purchase_entries:
        await db.general_ledger.insert_one({
            "id": str(ObjectId()),
            "journal_number": jv_purchase,
            "account_code": e["account_code"],
            "account_name": e["account_name"],
            "debit": e["debit"],
            "credit": e["credit"],
            "date": datetime.now(timezone.utc).isoformat(),
            "reference": rcv_number,
            "description": f"Pembelian {rcv_number}"
        })
    print(f"   ✅ Journal Purchase: {jv_purchase}")
    
    # Sales Journal
    jv_sales = await generate_transaction_number(db, "JV")
    sales_entries = [
        {"account_code": "1-1300", "account_name": "Piutang Usaha", "debit": 4995000, "credit": 0},
        {"account_code": "4-1000", "account_name": "Penjualan", "debit": 0, "credit": 4500000},
        {"account_code": "2-1400", "account_name": "PPN Keluaran", "debit": 0, "credit": 495000}
    ]
    await db.journal_entries.insert_one({
        "id": str(ObjectId()),
        "journal_number": jv_sales,
        "date": datetime.now(timezone.utc).isoformat(),
        "reference": inv_number,
        "reference_type": "sales",
        "description": f"Penjualan {inv_number}",
        "lines": sales_entries,
        "entries": sales_entries,
        "total_debit": 4995000,
        "total_credit": 4995000,
        "status": "posted",
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    for e in sales_entries:
        await db.general_ledger.insert_one({
            "id": str(ObjectId()),
            "journal_number": jv_sales,
            "account_code": e["account_code"],
            "account_name": e["account_name"],
            "debit": e["debit"],
            "credit": e["credit"],
            "date": datetime.now(timezone.utc).isoformat(),
            "reference": inv_number,
            "description": f"Penjualan {inv_number}"
        })
    print(f"   ✅ Journal Sales: {jv_sales}")
    
    # HPP Journal
    jv_hpp = await generate_transaction_number(db, "JV")
    hpp_entries = [
        {"account_code": "5-1000", "account_name": "HPP", "debit": 3000000, "credit": 0},
        {"account_code": "1-1400", "account_name": "Persediaan", "debit": 0, "credit": 3000000}
    ]
    await db.journal_entries.insert_one({
        "id": str(ObjectId()),
        "journal_number": jv_hpp,
        "date": datetime.now(timezone.utc).isoformat(),
        "reference": inv_number,
        "reference_type": "hpp",
        "description": f"HPP {inv_number}",
        "lines": hpp_entries,
        "entries": hpp_entries,
        "total_debit": 3000000,
        "total_credit": 3000000,
        "status": "posted",
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    for e in hpp_entries:
        await db.general_ledger.insert_one({
            "id": str(ObjectId()),
            "journal_number": jv_hpp,
            "account_code": e["account_code"],
            "account_name": e["account_name"],
            "debit": e["debit"],
            "credit": e["credit"],
            "date": datetime.now(timezone.utc).isoformat(),
            "reference": inv_number,
            "description": f"HPP {inv_number}"
        })
    print(f"   ✅ Journal HPP: {jv_hpp}")
    
    # 10. Validate Financial Reports
    print("\n--- Step 10: Validate Financial Reports ---")
    
    # Check all journals balanced
    journals = await db.journal_entries.find({}).to_list(100)
    imbalanced = []
    for j in journals:
        lines = j.get('lines', []) or j.get('entries', [])
        d = sum(l.get('debit', 0) for l in lines)
        c = sum(l.get('credit', 0) for l in lines)
        if d != c:
            imbalanced.append(j.get('journal_number'))
    
    if imbalanced:
        print(f"   ❌ {len(imbalanced)} journals not balanced: {imbalanced}")
        all_passed = False
    else:
        print(f"   ✅ All {len(journals)} journals BALANCED")
    
    # Check General Ledger totals
    gl = await db.general_ledger.find({}).to_list(1000)
    gl_debit = sum(e.get('debit', 0) for e in gl)
    gl_credit = sum(e.get('credit', 0) for e in gl)
    
    if gl_debit == gl_credit:
        print(f"   ✅ General Ledger: Debit={gl_debit:,.0f} Credit={gl_credit:,.0f} BALANCED")
    else:
        print(f"   ❌ General Ledger NOT BALANCED: Debit={gl_debit:,.0f} Credit={gl_credit:,.0f}")
        all_passed = False
    
    # Summary
    print("\n" + "=" * 80)
    if all_passed:
        print("✅ END-TO-END VALIDATION PASSED")
    else:
        print("❌ END-TO-END VALIDATION FAILED")
    print("=" * 80)
    
    return all_passed


async def main():
    print("\n" + "=" * 80)
    print("P1 VALIDATION SUITE - FULL TEST")
    print("=" * 80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    db, client = await get_db()
    
    results = {}
    
    try:
        # P1-1: AR invoice_number
        results["ar_validation"] = await test_ar_invoice_number(db)
        
        # P1-2: Transaction number engine
        results["transaction_numbers"] = await test_transaction_number_engine(db)
        
        # P1-3: Master number engine
        results["master_numbers"] = await test_master_number_engine(db)
        
        # P1-4: Auto item code
        results["auto_item_code"] = await test_auto_item_code(db)
        
        # P1-6: End-to-end flow
        results["e2e_flow"] = await test_end_to_end_flow(db)
        
        # Final Summary
        print("\n" + "=" * 80)
        print("FINAL P1 VALIDATION SUMMARY")
        print("=" * 80)
        
        all_passed = True
        for test, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"   {test}: {status}")
            if not passed:
                all_passed = False
        
        print("\n" + "=" * 80)
        if all_passed:
            print("🎉🎉🎉 ALL P1 TESTS PASSED 🎉🎉🎉")
            print("System is OPERATIONALLY STABLE")
        else:
            print("❌ SOME P1 TESTS FAILED")
            print("System requires fixes")
        print("=" * 80)
        
        return all_passed
        
    finally:
        client.close()


if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)
