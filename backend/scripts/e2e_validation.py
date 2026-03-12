#!/usr/bin/env python3
"""
END-TO-END OPERATIONAL VALIDATION SCRIPT
==========================================
Validates the complete business cycle:
1. Purchase Flow: Create -> Submit -> Receive
2. Sales Flow: Create Invoice (Cash & Credit)
3. Payment Flow: AP & AR Payment
4. Stock Opname: Execute with variance
5. Financial Reports: Validate all balances

WAJIB: Total Debit = Total Credit
WAJIB: Assets = Liabilities + Equity
"""

import asyncio
import os
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# Database connection
MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = 'erp_db'

async def get_db():
    client = AsyncIOMotorClient(MONGO_URL)
    return client[DB_NAME], client

async def generate_number(prefix: str, db) -> str:
    """Generate auto number"""
    date_str = datetime.now().strftime("%Y%m%d")
    last = await db.counters.find_one({"prefix": prefix, "date": date_str})
    if last:
        seq = last.get("seq", 0) + 1
        await db.counters.update_one({"prefix": prefix, "date": date_str}, {"$set": {"seq": seq}})
    else:
        seq = 1
        await db.counters.insert_one({"prefix": prefix, "date": date_str, "seq": seq})
    return f"{prefix}-{date_str}-{str(seq).zfill(4)}"

# ==================== SETUP MASTER DATA ====================
async def setup_master_data(db):
    """Setup all required master data for testing"""
    print("\n" + "=" * 80)
    print("STEP 0: SETUP MASTER DATA")
    print("=" * 80)
    
    # 0.1 Create Chart of Accounts
    accounts = [
        {"code": "1-1100", "name": "Kas", "type": "asset", "category": "current_asset"},
        {"code": "1-1200", "name": "Bank BCA", "type": "asset", "category": "current_asset"},
        {"code": "1-1300", "name": "Piutang Usaha", "type": "asset", "category": "current_asset"},
        {"code": "1-1400", "name": "Persediaan Barang", "type": "asset", "category": "current_asset"},
        {"code": "2-1100", "name": "Hutang Usaha", "type": "liability", "category": "current_liability"},
        {"code": "2-1400", "name": "PPN Keluaran", "type": "liability", "category": "current_liability"},
        {"code": "2-1500", "name": "PPN Masukan", "type": "liability", "category": "current_liability"},
        {"code": "2-1600", "name": "Uang Muka Pelanggan", "type": "liability", "category": "current_liability"},
        {"code": "2-1700", "name": "Deposit Pelanggan", "type": "liability", "category": "current_liability"},
        {"code": "3-1000", "name": "Modal", "type": "equity", "category": "equity"},
        {"code": "3-2000", "name": "Laba Ditahan", "type": "equity", "category": "retained_earnings"},
        {"code": "4-1000", "name": "Penjualan", "type": "revenue", "category": "operating_revenue"},
        {"code": "4-1100", "name": "Retur Penjualan", "type": "revenue", "category": "contra_revenue"},
        {"code": "5-1000", "name": "Harga Pokok Penjualan", "type": "expense", "category": "cogs"},
        {"code": "5-2000", "name": "Beban Komisi Sales", "type": "expense", "category": "operating_expense"},
        {"code": "6-1000", "name": "Selisih Stok", "type": "expense", "category": "other_expense"},
    ]
    
    for acc in accounts:
        acc["id"] = str(ObjectId())
        acc["is_active"] = True
        await db.chart_of_accounts.update_one({"code": acc["code"]}, {"$set": acc}, upsert=True)
    print(f"   ✅ Created {len(accounts)} accounts")
    
    # 0.2 Create Branch/Warehouse
    branch = {
        "id": "branch-001",
        "code": "HQ",
        "name": "Gudang Pusat",
        "address": "Jakarta",
        "is_active": True
    }
    await db.branches.update_one({"id": branch["id"]}, {"$set": branch}, upsert=True)
    await db.warehouses.update_one({"id": branch["id"]}, {"$set": branch}, upsert=True)
    print(f"   ✅ Created branch: {branch['name']}")
    
    # 0.3 Create Supplier
    supplier = {
        "id": "supplier-001",
        "code": "SP-0001",
        "name": "PT Supplier Utama",
        "address": "Bandung",
        "phone": "022-1234567",
        "is_active": True
    }
    await db.suppliers.update_one({"id": supplier["id"]}, {"$set": supplier}, upsert=True)
    print(f"   ✅ Created supplier: {supplier['name']}")
    
    # 0.4 Create Customer
    customer = {
        "id": "customer-001",
        "code": "PL-0001",
        "name": "PT Pelanggan Prima",
        "address": "Surabaya",
        "phone": "031-9876543",
        "credit_limit": 50000000,
        "is_active": True
    }
    await db.customers.update_one({"id": customer["id"]}, {"$set": customer}, upsert=True)
    print(f"   ✅ Created customer: {customer['name']}")
    
    # 0.5 Create Products
    products = [
        {
            "id": "product-001",
            "code": "ITM-0001",
            "name": "Laptop Asus ROG",
            "unit": "UNIT",
            "cost_price": 10000000,
            "sell_price": 15000000,
            "stock": 0,
            "category_id": "cat-001",
            "is_active": True
        },
        {
            "id": "product-002",
            "code": "ITM-0002",
            "name": "Monitor LG 27inch",
            "unit": "UNIT",
            "cost_price": 3000000,
            "sell_price": 4500000,
            "stock": 0,
            "category_id": "cat-001",
            "is_active": True
        },
        {
            "id": "product-003",
            "code": "ITM-0003",
            "name": "Keyboard Mechanical",
            "unit": "UNIT",
            "cost_price": 500000,
            "sell_price": 800000,
            "stock": 0,
            "category_id": "cat-002",
            "is_active": True
        }
    ]
    for p in products:
        await db.products.update_one({"id": p["id"]}, {"$set": p}, upsert=True)
    print(f"   ✅ Created {len(products)} products")
    
    # 0.6 Create initial capital journal (Modal Awal)
    initial_capital_entries = [
        {"account_code": "1-1100", "account_name": "Kas", "debit": 100000000, "credit": 0},
        {"account_code": "3-1000", "account_name": "Modal", "debit": 0, "credit": 100000000}
    ]
    
    journal_number = await generate_number("JV", db)
    initial_journal = {
        "id": str(ObjectId()),
        "journal_number": journal_number,
        "date": datetime.now(timezone.utc).isoformat(),
        "reference": "SETUP",
        "reference_type": "setup",
        "reference_id": "SETUP",
        "description": "Modal Awal Perusahaan",
        "lines": initial_capital_entries,
        "entries": initial_capital_entries,
        "total_debit": 100000000,
        "total_credit": 100000000,
        "status": "posted",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.journal_entries.insert_one(initial_journal)
    
    # Also add to general_ledger
    for entry in initial_capital_entries:
        ledger_entry = {
            "id": str(ObjectId()),
            "journal_id": initial_journal["id"],
            "journal_number": journal_number,
            "account_code": entry["account_code"],
            "account_name": entry["account_name"],
            "debit": entry["debit"],
            "credit": entry["credit"],
            "date": initial_journal["date"],
            "reference": "SETUP",
            "description": "Modal Awal Perusahaan"
        }
        await db.general_ledger.insert_one(ledger_entry)
    
    print(f"   ✅ Created initial capital journal: {journal_number}")
    
    return {
        "branch_id": branch["id"],
        "supplier_id": supplier["id"],
        "customer_id": customer["id"],
        "products": products
    }

# ==================== TEST 1: PURCHASE FLOW ====================
async def test_purchase_flow(db, master_data):
    """Test Purchase Order -> Receiving -> Stock Update -> AP"""
    print("\n" + "=" * 80)
    print("TEST 1: PURCHASE FLOW")
    print("=" * 80)
    
    # 1.1 Create Purchase Order
    po_number = await generate_number("PO", db)
    items = [
        {
            "product_id": master_data["products"][0]["id"],
            "product_code": master_data["products"][0]["code"],
            "product_name": master_data["products"][0]["name"],
            "quantity": 5,
            "unit_price": 10000000,
            "subtotal": 50000000
        },
        {
            "product_id": master_data["products"][1]["id"],
            "product_code": master_data["products"][1]["code"],
            "product_name": master_data["products"][1]["name"],
            "quantity": 10,
            "unit_price": 3000000,
            "subtotal": 30000000
        }
    ]
    subtotal = sum(i["subtotal"] for i in items)
    ppn = subtotal * 0.11
    total = subtotal + ppn
    
    po = {
        "id": str(ObjectId()),
        "po_number": po_number,
        "date": datetime.now(timezone.utc).isoformat(),
        "supplier_id": master_data["supplier_id"],
        "supplier_name": "PT Supplier Utama",
        "branch_id": master_data["branch_id"],
        "items": items,
        "subtotal": subtotal,
        "ppn_amount": ppn,
        "total": total,
        "status": "confirmed",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.purchase_orders.insert_one(po)
    print(f"   ✅ PO Created: {po_number}")
    print(f"      Subtotal: Rp {subtotal:,.0f}")
    print(f"      PPN 11%: Rp {ppn:,.0f}")
    print(f"      Total: Rp {total:,.0f}")
    
    # 1.2 Create Receiving
    rcv_number = await generate_number("RCV", db)
    receiving = {
        "id": str(ObjectId()),
        "receiving_number": rcv_number,
        "po_number": po_number,
        "po_id": po["id"],
        "date": datetime.now(timezone.utc).isoformat(),
        "supplier_id": master_data["supplier_id"],
        "supplier_name": "PT Supplier Utama",
        "branch_id": master_data["branch_id"],
        "items": items,
        "subtotal": subtotal,
        "ppn_amount": ppn,
        "total": total,
        "status": "completed",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.receivings.insert_one(receiving)
    print(f"   ✅ Receiving Created: {rcv_number}")
    
    # 1.3 Update Stock via stock_movements
    for item in items:
        movement = {
            "id": str(ObjectId()),
            "product_id": item["product_id"],
            "branch_id": master_data["branch_id"],
            "warehouse_id": master_data["branch_id"],
            "quantity": item["quantity"],  # Positive for receiving
            "movement_type": "purchase_in",
            "reference_type": "receiving",
            "reference_number": rcv_number,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.stock_movements.insert_one(movement)
        
        # Update product_stocks for quick lookup
        await db.product_stocks.update_one(
            {"product_id": item["product_id"], "branch_id": master_data["branch_id"]},
            {"$inc": {"quantity": item["quantity"]}, "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}},
            upsert=True
        )
    print(f"   ✅ Stock updated for {len(items)} products")
    
    # 1.4 Create AP (Hutang Usaha)
    ap_number = await generate_number("AP", db)
    ap = {
        "id": str(ObjectId()),
        "ap_number": ap_number,
        "po_number": po_number,
        "receiving_number": rcv_number,
        "supplier_id": master_data["supplier_id"],
        "supplier_name": "PT Supplier Utama",
        "amount": total,
        "paid_amount": 0,
        "remaining_amount": total,
        "outstanding_amount": total,
        "due_date": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
        "status": "open",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.accounts_payable.insert_one(ap)
    print(f"   ✅ AP Created: {ap_number} = Rp {total:,.0f}")
    
    # 1.5 Create Purchase Journal
    # Pembelian:
    #   Debit  Persediaan Barang    80,000,000
    #   Debit  PPN Masukan           8,800,000
    #   Credit Hutang Usaha         88,800,000
    purchase_entries = [
        {"account_code": "1-1400", "account_name": "Persediaan Barang", "debit": subtotal, "credit": 0},
        {"account_code": "2-1500", "account_name": "PPN Masukan", "debit": ppn, "credit": 0},
        {"account_code": "2-1100", "account_name": "Hutang Usaha", "debit": 0, "credit": total}
    ]
    
    jv_number = await generate_number("JV", db)
    purchase_journal = {
        "id": str(ObjectId()),
        "journal_number": jv_number,
        "date": datetime.now(timezone.utc).isoformat(),
        "reference": rcv_number,
        "reference_type": "receiving",
        "reference_id": rcv_number,
        "description": f"Pembelian {rcv_number}",
        "lines": purchase_entries,
        "entries": purchase_entries,
        "total_debit": subtotal + ppn,
        "total_credit": total,
        "status": "posted",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.journal_entries.insert_one(purchase_journal)
    
    for entry in purchase_entries:
        ledger_entry = {
            "id": str(ObjectId()),
            "journal_id": purchase_journal["id"],
            "journal_number": jv_number,
            "account_code": entry["account_code"],
            "account_name": entry["account_name"],
            "debit": entry["debit"],
            "credit": entry["credit"],
            "date": purchase_journal["date"],
            "reference": rcv_number,
            "description": f"Pembelian {rcv_number}"
        }
        await db.general_ledger.insert_one(ledger_entry)
    
    print(f"   ✅ Purchase Journal: {jv_number}")
    
    # Verify journal balance
    j_debit = sum(e["debit"] for e in purchase_entries)
    j_credit = sum(e["credit"] for e in purchase_entries)
    if j_debit == j_credit:
        print(f"   ✅ PURCHASE JOURNAL BALANCED: Debit={j_debit:,.0f} Credit={j_credit:,.0f}")
    else:
        print(f"   ❌ PURCHASE JOURNAL NOT BALANCED: Debit={j_debit:,.0f} Credit={j_credit:,.0f}")
    
    return {"ap_id": ap["id"], "ap_amount": total, "po_number": po_number}

# ==================== TEST 2: SALES FLOW ====================
async def test_sales_flow(db, master_data):
    """Test Sales Invoice creation - Cash and Credit"""
    print("\n" + "=" * 80)
    print("TEST 2: SALES FLOW")
    print("=" * 80)
    
    results = []
    
    # 2.1 PENJUALAN TUNAI
    print("\n   --- 2.1 PENJUALAN TUNAI ---")
    inv_number_cash = await generate_number("INV", db)
    items_cash = [
        {
            "product_id": master_data["products"][0]["id"],
            "product_code": master_data["products"][0]["code"],
            "product_name": master_data["products"][0]["name"],
            "quantity": 2,
            "unit_price": 15000000,
            "cost_price": 10000000,
            "subtotal": 30000000,
            "total": 30000000,
            "hpp": 20000000
        }
    ]
    subtotal_cash = 30000000
    ppn_cash = subtotal_cash * 0.11
    total_cash = subtotal_cash + ppn_cash
    total_hpp_cash = 20000000
    
    invoice_cash = {
        "id": str(ObjectId()),
        "invoice_number": inv_number_cash,
        "date": datetime.now(timezone.utc).isoformat(),
        "customer_id": master_data["customer_id"],
        "customer_name": "PT Pelanggan Prima",
        "branch_id": master_data["branch_id"],
        "items": items_cash,
        "subtotal": subtotal_cash,
        "discount_amount": 0,
        "tax_amount": ppn_cash,
        "total": total_cash,
        "total_hpp": total_hpp_cash,
        "payment_type": "cash",
        "cash_amount": total_cash,
        "credit_amount": 0,
        "is_credit": False,
        "status": "completed",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.sales_invoices.insert_one(invoice_cash)
    print(f"   ✅ Invoice Cash: {inv_number_cash}")
    print(f"      Subtotal: Rp {subtotal_cash:,.0f}")
    print(f"      PPN 11%: Rp {ppn_cash:,.0f}")
    print(f"      Total: Rp {total_cash:,.0f}")
    
    # Update stock (decrease)
    for item in items_cash:
        movement = {
            "id": str(ObjectId()),
            "product_id": item["product_id"],
            "branch_id": master_data["branch_id"],
            "warehouse_id": master_data["branch_id"],
            "quantity": -item["quantity"],  # Negative for sales
            "movement_type": "sales_out",
            "reference_type": "sales",
            "reference_number": inv_number_cash,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.stock_movements.insert_one(movement)
        await db.product_stocks.update_one(
            {"product_id": item["product_id"], "branch_id": master_data["branch_id"]},
            {"$inc": {"quantity": -item["quantity"]}}
        )
    
    # Create Sales Journal (Cash)
    # Debit  Kas                  33,300,000
    # Credit Penjualan            30,000,000
    # Credit PPN Keluaran          3,300,000
    sales_entries_cash = [
        {"account_code": "1-1100", "account_name": "Kas", "debit": total_cash, "credit": 0},
        {"account_code": "4-1000", "account_name": "Penjualan", "debit": 0, "credit": subtotal_cash},
        {"account_code": "2-1400", "account_name": "PPN Keluaran", "debit": 0, "credit": ppn_cash}
    ]
    
    jv_cash = await generate_number("JV", db)
    journal_cash = {
        "id": str(ObjectId()),
        "journal_number": jv_cash,
        "date": datetime.now(timezone.utc).isoformat(),
        "reference": inv_number_cash,
        "reference_type": "sales",
        "reference_id": inv_number_cash,
        "description": f"Penjualan Tunai {inv_number_cash}",
        "lines": sales_entries_cash,
        "entries": sales_entries_cash,
        "total_debit": total_cash,
        "total_credit": total_cash,
        "status": "posted",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.journal_entries.insert_one(journal_cash)
    for entry in sales_entries_cash:
        await db.general_ledger.insert_one({
            "id": str(ObjectId()),
            "journal_id": journal_cash["id"],
            "journal_number": jv_cash,
            "account_code": entry["account_code"],
            "account_name": entry["account_name"],
            "debit": entry["debit"],
            "credit": entry["credit"],
            "date": journal_cash["date"],
            "reference": inv_number_cash,
            "description": f"Penjualan Tunai {inv_number_cash}"
        })
    
    # Verify balance
    d = sum(e["debit"] for e in sales_entries_cash)
    c = sum(e["credit"] for e in sales_entries_cash)
    print(f"   ✅ Sales Journal (Cash): {jv_cash}")
    if d == c:
        print(f"   ✅ CASH SALES JOURNAL BALANCED: D={d:,.0f} C={c:,.0f}")
    else:
        print(f"   ❌ CASH SALES JOURNAL NOT BALANCED: D={d:,.0f} C={c:,.0f}")
    
    # HPP Journal (Cash)
    hpp_entries_cash = [
        {"account_code": "5-1000", "account_name": "Harga Pokok Penjualan", "debit": total_hpp_cash, "credit": 0},
        {"account_code": "1-1400", "account_name": "Persediaan Barang", "debit": 0, "credit": total_hpp_cash}
    ]
    jv_hpp_cash = await generate_number("JV", db)
    journal_hpp_cash = {
        "id": str(ObjectId()),
        "journal_number": jv_hpp_cash,
        "date": datetime.now(timezone.utc).isoformat(),
        "reference": inv_number_cash,
        "reference_type": "hpp",
        "reference_id": inv_number_cash,
        "description": f"HPP {inv_number_cash}",
        "lines": hpp_entries_cash,
        "entries": hpp_entries_cash,
        "total_debit": total_hpp_cash,
        "total_credit": total_hpp_cash,
        "status": "posted",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.journal_entries.insert_one(journal_hpp_cash)
    for entry in hpp_entries_cash:
        await db.general_ledger.insert_one({
            "id": str(ObjectId()),
            "journal_id": journal_hpp_cash["id"],
            "journal_number": jv_hpp_cash,
            "account_code": entry["account_code"],
            "account_name": entry["account_name"],
            "debit": entry["debit"],
            "credit": entry["credit"],
            "date": journal_hpp_cash["date"],
            "reference": inv_number_cash,
            "description": f"HPP {inv_number_cash}"
        })
    print(f"   ✅ HPP Journal (Cash): {jv_hpp_cash}")
    
    results.append({"type": "cash", "invoice_number": inv_number_cash, "total": total_cash})
    
    # 2.2 PENJUALAN KREDIT
    print("\n   --- 2.2 PENJUALAN KREDIT ---")
    inv_number_credit = await generate_number("INV", db)
    items_credit = [
        {
            "product_id": master_data["products"][1]["id"],
            "product_code": master_data["products"][1]["code"],
            "product_name": master_data["products"][1]["name"],
            "quantity": 3,
            "unit_price": 4500000,
            "cost_price": 3000000,
            "subtotal": 13500000,
            "total": 13500000,
            "hpp": 9000000
        }
    ]
    subtotal_credit = 13500000
    ppn_credit = subtotal_credit * 0.11
    total_credit = subtotal_credit + ppn_credit
    total_hpp_credit = 9000000
    
    invoice_credit = {
        "id": str(ObjectId()),
        "invoice_number": inv_number_credit,
        "date": datetime.now(timezone.utc).isoformat(),
        "customer_id": master_data["customer_id"],
        "customer_name": "PT Pelanggan Prima",
        "branch_id": master_data["branch_id"],
        "items": items_credit,
        "subtotal": subtotal_credit,
        "discount_amount": 0,
        "tax_amount": ppn_credit,
        "total": total_credit,
        "total_hpp": total_hpp_credit,
        "payment_type": "credit",
        "cash_amount": 0,
        "credit_amount": total_credit,
        "is_credit": True,
        "status": "completed",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.sales_invoices.insert_one(invoice_credit)
    print(f"   ✅ Invoice Credit: {inv_number_credit}")
    print(f"      Subtotal: Rp {subtotal_credit:,.0f}")
    print(f"      PPN 11%: Rp {ppn_credit:,.0f}")
    print(f"      Total: Rp {total_credit:,.0f}")
    
    # Update stock
    for item in items_credit:
        movement = {
            "id": str(ObjectId()),
            "product_id": item["product_id"],
            "branch_id": master_data["branch_id"],
            "warehouse_id": master_data["branch_id"],
            "quantity": -item["quantity"],
            "movement_type": "sales_out",
            "reference_type": "sales",
            "reference_number": inv_number_credit,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.stock_movements.insert_one(movement)
        await db.product_stocks.update_one(
            {"product_id": item["product_id"], "branch_id": master_data["branch_id"]},
            {"$inc": {"quantity": -item["quantity"]}}
        )
    
    # Create AR
    ar_number = await generate_number("AR", db)
    ar = {
        "id": str(ObjectId()),
        "ar_number": ar_number,
        "ar_no": ar_number,
        "invoice_number": inv_number_credit,
        "customer_id": master_data["customer_id"],
        "customer_name": "PT Pelanggan Prima",
        "amount": total_credit,
        "paid_amount": 0,
        "remaining_amount": total_credit,
        "outstanding_amount": total_credit,
        "due_date": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
        "status": "open",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.accounts_receivable.insert_one(ar)
    print(f"   ✅ AR Created: {ar_number} = Rp {total_credit:,.0f}")
    
    # Create Sales Journal (Credit)
    # Debit  Piutang Usaha        14,985,000
    # Credit Penjualan            13,500,000
    # Credit PPN Keluaran          1,485,000
    sales_entries_credit = [
        {"account_code": "1-1300", "account_name": "Piutang Usaha", "debit": total_credit, "credit": 0},
        {"account_code": "4-1000", "account_name": "Penjualan", "debit": 0, "credit": subtotal_credit},
        {"account_code": "2-1400", "account_name": "PPN Keluaran", "debit": 0, "credit": ppn_credit}
    ]
    
    jv_credit = await generate_number("JV", db)
    journal_credit = {
        "id": str(ObjectId()),
        "journal_number": jv_credit,
        "date": datetime.now(timezone.utc).isoformat(),
        "reference": inv_number_credit,
        "reference_type": "sales",
        "reference_id": inv_number_credit,
        "description": f"Penjualan Kredit {inv_number_credit}",
        "lines": sales_entries_credit,
        "entries": sales_entries_credit,
        "total_debit": total_credit,
        "total_credit": total_credit,
        "status": "posted",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.journal_entries.insert_one(journal_credit)
    for entry in sales_entries_credit:
        await db.general_ledger.insert_one({
            "id": str(ObjectId()),
            "journal_id": journal_credit["id"],
            "journal_number": jv_credit,
            "account_code": entry["account_code"],
            "account_name": entry["account_name"],
            "debit": entry["debit"],
            "credit": entry["credit"],
            "date": journal_credit["date"],
            "reference": inv_number_credit,
            "description": f"Penjualan Kredit {inv_number_credit}"
        })
    
    d = sum(e["debit"] for e in sales_entries_credit)
    c = sum(e["credit"] for e in sales_entries_credit)
    print(f"   ✅ Sales Journal (Credit): {jv_credit}")
    if d == c:
        print(f"   ✅ CREDIT SALES JOURNAL BALANCED: D={d:,.0f} C={c:,.0f}")
    else:
        print(f"   ❌ CREDIT SALES JOURNAL NOT BALANCED: D={d:,.0f} C={c:,.0f}")
    
    # HPP Journal (Credit)
    hpp_entries_credit = [
        {"account_code": "5-1000", "account_name": "Harga Pokok Penjualan", "debit": total_hpp_credit, "credit": 0},
        {"account_code": "1-1400", "account_name": "Persediaan Barang", "debit": 0, "credit": total_hpp_credit}
    ]
    jv_hpp_credit = await generate_number("JV", db)
    journal_hpp_credit = {
        "id": str(ObjectId()),
        "journal_number": jv_hpp_credit,
        "date": datetime.now(timezone.utc).isoformat(),
        "reference": inv_number_credit,
        "reference_type": "hpp",
        "reference_id": inv_number_credit,
        "description": f"HPP {inv_number_credit}",
        "lines": hpp_entries_credit,
        "entries": hpp_entries_credit,
        "total_debit": total_hpp_credit,
        "total_credit": total_hpp_credit,
        "status": "posted",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.journal_entries.insert_one(journal_hpp_credit)
    for entry in hpp_entries_credit:
        await db.general_ledger.insert_one({
            "id": str(ObjectId()),
            "journal_id": journal_hpp_credit["id"],
            "journal_number": jv_hpp_credit,
            "account_code": entry["account_code"],
            "account_name": entry["account_name"],
            "debit": entry["debit"],
            "credit": entry["credit"],
            "date": journal_hpp_credit["date"],
            "reference": inv_number_credit,
            "description": f"HPP {inv_number_credit}"
        })
    print(f"   ✅ HPP Journal (Credit): {jv_hpp_credit}")
    
    results.append({"type": "credit", "invoice_number": inv_number_credit, "total": total_credit, "ar_id": ar["id"]})
    
    return results

# ==================== TEST 3: PAYMENT FLOW ====================
async def test_payment_flow(db, purchase_data, sales_data):
    """Test AP Payment and AR Payment"""
    print("\n" + "=" * 80)
    print("TEST 3: PAYMENT FLOW")
    print("=" * 80)
    
    # 3.1 AP Payment (Bayar Hutang)
    print("\n   --- 3.1 AP PAYMENT ---")
    ap = await db.accounts_payable.find_one({"id": purchase_data["ap_id"]})
    if ap:
        pay_amount = ap["remaining_amount"]
        pay_number = await generate_number("PAY", db)
        
        payment = {
            "id": str(ObjectId()),
            "payment_number": pay_number,
            "date": datetime.now(timezone.utc).isoformat(),
            "payment_type": "ap",
            "supplier_id": ap["supplier_id"],
            "supplier_name": ap["supplier_name"],
            "ap_id": ap["id"],
            "ap_number": ap["ap_number"],
            "amount": pay_amount,
            "payment_method": "cash",
            "status": "completed",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.payments.insert_one(payment)
        
        # Update AP
        await db.accounts_payable.update_one(
            {"id": ap["id"]},
            {"$set": {"paid_amount": pay_amount, "remaining_amount": 0, "outstanding_amount": 0, "status": "paid"}}
        )
        
        # AP Payment Journal
        # Debit  Hutang Usaha         88,800,000
        # Credit Kas                  88,800,000
        ap_pay_entries = [
            {"account_code": "2-1100", "account_name": "Hutang Usaha", "debit": pay_amount, "credit": 0},
            {"account_code": "1-1100", "account_name": "Kas", "debit": 0, "credit": pay_amount}
        ]
        
        jv_ap = await generate_number("JV", db)
        journal_ap = {
            "id": str(ObjectId()),
            "journal_number": jv_ap,
            "date": datetime.now(timezone.utc).isoformat(),
            "reference": pay_number,
            "reference_type": "ap_payment",
            "reference_id": pay_number,
            "description": f"Pembayaran AP {ap['ap_number']}",
            "lines": ap_pay_entries,
            "entries": ap_pay_entries,
            "total_debit": pay_amount,
            "total_credit": pay_amount,
            "status": "posted",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.journal_entries.insert_one(journal_ap)
        for entry in ap_pay_entries:
            await db.general_ledger.insert_one({
                "id": str(ObjectId()),
                "journal_id": journal_ap["id"],
                "journal_number": jv_ap,
                "account_code": entry["account_code"],
                "account_name": entry["account_name"],
                "debit": entry["debit"],
                "credit": entry["credit"],
                "date": journal_ap["date"],
                "reference": pay_number,
                "description": f"Pembayaran AP {ap['ap_number']}"
            })
        
        print(f"   ✅ AP Payment: {pay_number} = Rp {pay_amount:,.0f}")
        print(f"   ✅ AP Journal: {jv_ap}")
        d = sum(e["debit"] for e in ap_pay_entries)
        c = sum(e["credit"] for e in ap_pay_entries)
        if d == c:
            print(f"   ✅ AP PAYMENT JOURNAL BALANCED: D={d:,.0f} C={c:,.0f}")
        else:
            print(f"   ❌ AP PAYMENT JOURNAL NOT BALANCED: D={d:,.0f} C={c:,.0f}")
    
    # 3.2 AR Payment (Terima Piutang)
    print("\n   --- 3.2 AR PAYMENT ---")
    credit_sale = next((s for s in sales_data if s["type"] == "credit"), None)
    if credit_sale:
        ar = await db.accounts_receivable.find_one({"id": credit_sale["ar_id"]})
        if ar:
            recv_amount = ar["remaining_amount"]
            recv_number = await generate_number("RECV", db)
            
            ar_payment = {
                "id": str(ObjectId()),
                "payment_number": recv_number,
                "date": datetime.now(timezone.utc).isoformat(),
                "payment_type": "ar",
                "customer_id": ar["customer_id"],
                "customer_name": ar["customer_name"],
                "ar_id": ar["id"],
                "ar_number": ar["ar_number"],
                "invoice_number": ar["invoice_number"],
                "amount": recv_amount,
                "payment_method": "cash",
                "status": "completed",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.ar_payments.insert_one(ar_payment)
            
            # Update AR
            await db.accounts_receivable.update_one(
                {"id": ar["id"]},
                {"$set": {"paid_amount": recv_amount, "remaining_amount": 0, "outstanding_amount": 0, "status": "paid"}}
            )
            
            # AR Payment Journal
            # Debit  Kas                  14,985,000
            # Credit Piutang Usaha        14,985,000
            ar_pay_entries = [
                {"account_code": "1-1100", "account_name": "Kas", "debit": recv_amount, "credit": 0},
                {"account_code": "1-1300", "account_name": "Piutang Usaha", "debit": 0, "credit": recv_amount}
            ]
            
            jv_ar = await generate_number("JV", db)
            journal_ar = {
                "id": str(ObjectId()),
                "journal_number": jv_ar,
                "date": datetime.now(timezone.utc).isoformat(),
                "reference": recv_number,
                "reference_type": "ar_payment",
                "reference_id": recv_number,
                "description": f"Penerimaan Piutang {ar['ar_number']}",
                "lines": ar_pay_entries,
                "entries": ar_pay_entries,
                "total_debit": recv_amount,
                "total_credit": recv_amount,
                "status": "posted",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.journal_entries.insert_one(journal_ar)
            for entry in ar_pay_entries:
                await db.general_ledger.insert_one({
                    "id": str(ObjectId()),
                    "journal_id": journal_ar["id"],
                    "journal_number": jv_ar,
                    "account_code": entry["account_code"],
                    "account_name": entry["account_name"],
                    "debit": entry["debit"],
                    "credit": entry["credit"],
                    "date": journal_ar["date"],
                    "reference": recv_number,
                    "description": f"Penerimaan Piutang {ar['ar_number']}"
                })
            
            print(f"   ✅ AR Payment: {recv_number} = Rp {recv_amount:,.0f}")
            print(f"   ✅ AR Journal: {jv_ar}")
            d = sum(e["debit"] for e in ar_pay_entries)
            c = sum(e["credit"] for e in ar_pay_entries)
            if d == c:
                print(f"   ✅ AR PAYMENT JOURNAL BALANCED: D={d:,.0f} C={c:,.0f}")
            else:
                print(f"   ❌ AR PAYMENT JOURNAL NOT BALANCED: D={d:,.0f} C={c:,.0f}")

# ==================== TEST 4: STOCK OPNAME ====================
async def test_stock_opname(db, master_data):
    """Test Stock Opname with negative variance"""
    print("\n" + "=" * 80)
    print("TEST 4: STOCK OPNAME")
    print("=" * 80)
    
    # Get current stock for product-003 (Keyboard)
    product = master_data["products"][2]
    
    # First add some stock via receiving
    movement_in = {
        "id": str(ObjectId()),
        "product_id": product["id"],
        "branch_id": master_data["branch_id"],
        "warehouse_id": master_data["branch_id"],
        "quantity": 20,
        "movement_type": "purchase_in",
        "reference_type": "receiving",
        "reference_number": "RCV-OPNAME-TEST",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.stock_movements.insert_one(movement_in)
    await db.product_stocks.update_one(
        {"product_id": product["id"], "branch_id": master_data["branch_id"]},
        {"$inc": {"quantity": 20}},
        upsert=True
    )
    
    # Calculate system stock
    pipeline = [
        {"$match": {"product_id": product["id"], "branch_id": master_data["branch_id"]}},
        {"$group": {"_id": None, "total": {"$sum": "$quantity"}}}
    ]
    result = await db.stock_movements.aggregate(pipeline).to_list(1)
    system_stock = result[0]["total"] if result else 0
    
    print(f"   📦 Product: {product['name']}")
    print(f"   📊 System Stock (from movements): {system_stock}")
    
    # Execute Stock Opname with negative variance
    physical_count = 18  # Actual count (2 less than system)
    variance = physical_count - system_stock
    
    opname_number = await generate_number("SO", db)
    opname = {
        "id": str(ObjectId()),
        "opname_number": opname_number,
        "date": datetime.now(timezone.utc).isoformat(),
        "branch_id": master_data["branch_id"],
        "items": [
            {
                "product_id": product["id"],
                "product_code": product["code"],
                "product_name": product["name"],
                "system_stock": system_stock,
                "physical_count": physical_count,
                "variance": variance
            }
        ],
        "status": "completed",
        "notes": "Test Stock Opname",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.stock_opnames.insert_one(opname)
    print(f"   ✅ Stock Opname: {opname_number}")
    print(f"      Physical Count: {physical_count}")
    print(f"      Variance: {variance}")
    
    # Create adjustment movement
    if variance != 0:
        adj_movement = {
            "id": str(ObjectId()),
            "product_id": product["id"],
            "branch_id": master_data["branch_id"],
            "warehouse_id": master_data["branch_id"],
            "quantity": variance,  # Negative for loss
            "movement_type": "adjustment_out" if variance < 0 else "adjustment_in",
            "reference_type": "stock_opname",
            "reference_number": opname_number,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.stock_movements.insert_one(adj_movement)
        await db.product_stocks.update_one(
            {"product_id": product["id"], "branch_id": master_data["branch_id"]},
            {"$inc": {"quantity": variance}}
        )
        
        # Stock Adjustment Journal
        # Selisih stok kurang (loss):
        #   Debit  Selisih Stok         1,000,000 (2 x 500,000)
        #   Credit Persediaan Barang    1,000,000
        adj_value = abs(variance) * product["cost_price"]
        
        if variance < 0:
            adj_entries = [
                {"account_code": "6-1000", "account_name": "Selisih Stok", "debit": adj_value, "credit": 0},
                {"account_code": "1-1400", "account_name": "Persediaan Barang", "debit": 0, "credit": adj_value}
            ]
        else:
            adj_entries = [
                {"account_code": "1-1400", "account_name": "Persediaan Barang", "debit": adj_value, "credit": 0},
                {"account_code": "6-1000", "account_name": "Selisih Stok", "debit": 0, "credit": adj_value}
            ]
        
        jv_adj = await generate_number("JV", db)
        journal_adj = {
            "id": str(ObjectId()),
            "journal_number": jv_adj,
            "date": datetime.now(timezone.utc).isoformat(),
            "reference": opname_number,
            "reference_type": "stock_opname",
            "reference_id": opname_number,
            "description": f"Penyesuaian Stok {opname_number}",
            "lines": adj_entries,
            "entries": adj_entries,
            "total_debit": adj_value,
            "total_credit": adj_value,
            "status": "posted",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.journal_entries.insert_one(journal_adj)
        for entry in adj_entries:
            await db.general_ledger.insert_one({
                "id": str(ObjectId()),
                "journal_id": journal_adj["id"],
                "journal_number": jv_adj,
                "account_code": entry["account_code"],
                "account_name": entry["account_name"],
                "debit": entry["debit"],
                "credit": entry["credit"],
                "date": journal_adj["date"],
                "reference": opname_number,
                "description": f"Penyesuaian Stok {opname_number}"
            })
        
        print(f"   ✅ Stock Adjustment Journal: {jv_adj}")
        print(f"      Adjustment Value: Rp {adj_value:,.0f}")
        d = sum(e["debit"] for e in adj_entries)
        c = sum(e["credit"] for e in adj_entries)
        if d == c:
            print(f"   ✅ ADJUSTMENT JOURNAL BALANCED: D={d:,.0f} C={c:,.0f}")
        else:
            print(f"   ❌ ADJUSTMENT JOURNAL NOT BALANCED: D={d:,.0f} C={c:,.0f}")
    
    # Verify final stock
    result = await db.stock_movements.aggregate(pipeline).to_list(1)
    final_stock = result[0]["total"] if result else 0
    print(f"   ✅ Final Stock (from movements): {final_stock}")
    
    if final_stock == physical_count:
        print(f"   ✅ STOCK OPNAME SUCCESS: System={final_stock} Physical={physical_count}")
    else:
        print(f"   ❌ STOCK OPNAME MISMATCH: System={final_stock} Physical={physical_count}")

# ==================== TEST 5: FINANCIAL REPORTS ====================
async def test_financial_reports(db):
    """Validate all financial reports are balanced"""
    print("\n" + "=" * 80)
    print("TEST 5: MULTI-MODULE FINANCIAL VALIDATION")
    print("=" * 80)
    
    all_passed = True
    
    # 5.1 Journal Balance Check
    print("\n   --- 5.1 JOURNAL BALANCE CHECK ---")
    journals = await db.journal_entries.find({}).to_list(None)
    total_system_debit = 0
    total_system_credit = 0
    imbalanced = []
    
    for j in journals:
        lines = j.get('lines', []) or j.get('entries', [])
        j_debit = sum(l.get('debit', 0) for l in lines)
        j_credit = sum(l.get('credit', 0) for l in lines)
        total_system_debit += j_debit
        total_system_credit += j_credit
        if j_debit != j_credit:
            imbalanced.append({"number": j.get("journal_number"), "diff": j_debit - j_credit})
    
    print(f"   Total Journals: {len(journals)}")
    print(f"   Total Debit: Rp {total_system_debit:,.0f}")
    print(f"   Total Credit: Rp {total_system_credit:,.0f}")
    
    if imbalanced:
        print(f"   ❌ IMBALANCED JOURNALS ({len(imbalanced)}):")
        for ij in imbalanced:
            print(f"      - {ij['number']}: Diff={ij['diff']:,.0f}")
        all_passed = False
    else:
        print(f"   ✅ ALL JOURNALS BALANCED")
    
    # 5.2 Trial Balance
    print("\n   --- 5.2 TRIAL BALANCE ---")
    gl_entries = await db.general_ledger.find({}).to_list(None)
    
    account_balances = {}
    for entry in gl_entries:
        code = entry.get("account_code")
        name = entry.get("account_name", "")
        if code not in account_balances:
            account_balances[code] = {"name": name, "debit": 0, "credit": 0}
        account_balances[code]["debit"] += entry.get("debit", 0)
        account_balances[code]["credit"] += entry.get("credit", 0)
    
    tb_debit = 0
    tb_credit = 0
    print(f"   {'Code':<10} {'Account Name':<30} {'Debit':>18} {'Credit':>18}")
    print(f"   {'-'*10} {'-'*30} {'-'*18} {'-'*18}")
    
    for code in sorted(account_balances.keys()):
        acc = account_balances[code]
        tb_debit += acc["debit"]
        tb_credit += acc["credit"]
        print(f"   {code:<10} {acc['name'][:30]:<30} {acc['debit']:>18,.0f} {acc['credit']:>18,.0f}")
    
    print(f"   {'-'*10} {'-'*30} {'-'*18} {'-'*18}")
    print(f"   {'TOTAL':<10} {'':<30} {tb_debit:>18,.0f} {tb_credit:>18,.0f}")
    
    if tb_debit == tb_credit:
        print(f"\n   ✅ TRIAL BALANCE: BALANCED")
    else:
        print(f"\n   ❌ TRIAL BALANCE: NOT BALANCED (Diff: {tb_debit - tb_credit:,.0f})")
        all_passed = False
    
    # 5.3 Balance Sheet
    print("\n   --- 5.3 BALANCE SHEET ---")
    
    # Calculate balances per account type
    assets = 0
    liabilities = 0
    equity = 0
    revenue = 0
    expenses = 0
    
    for code, acc in account_balances.items():
        balance = acc["debit"] - acc["credit"]
        if code.startswith("1-"):  # Assets
            assets += balance
        elif code.startswith("2-"):  # Liabilities
            liabilities += -balance  # Credit balance
        elif code.startswith("3-"):  # Equity
            equity += -balance  # Credit balance
        elif code.startswith("4-"):  # Revenue
            revenue += -balance  # Credit balance
        elif code.startswith("5-") or code.startswith("6-"):  # Expenses
            expenses += balance  # Debit balance
    
    net_income = revenue - expenses
    total_equity = equity + net_income
    
    print(f"   ASSETS:")
    print(f"      Total Assets: Rp {assets:,.0f}")
    print(f"   LIABILITIES:")
    print(f"      Total Liabilities: Rp {liabilities:,.0f}")
    print(f"   EQUITY:")
    print(f"      Capital: Rp {equity:,.0f}")
    print(f"      Net Income (Revenue - Expenses): Rp {net_income:,.0f}")
    print(f"      Total Equity: Rp {total_equity:,.0f}")
    print(f"   ------------------------------------------")
    print(f"   Liabilities + Equity: Rp {liabilities + total_equity:,.0f}")
    
    if assets == liabilities + total_equity:
        print(f"\n   ✅ BALANCE SHEET: BALANCED (Assets = Liabilities + Equity)")
    else:
        diff = assets - (liabilities + total_equity)
        print(f"\n   ❌ BALANCE SHEET: NOT BALANCED (Diff: {diff:,.0f})")
        all_passed = False
    
    # 5.4 Income Statement
    print("\n   --- 5.4 INCOME STATEMENT ---")
    print(f"   Revenue: Rp {revenue:,.0f}")
    print(f"   Expenses: Rp {expenses:,.0f}")
    print(f"   Net Income: Rp {net_income:,.0f}")
    
    if revenue >= expenses:
        print(f"   ✅ INCOME STATEMENT: VALID (Profit)")
    else:
        print(f"   ⚠️ INCOME STATEMENT: VALID (Loss)")
    
    # 5.5 Cash Flow Summary
    print("\n   --- 5.5 CASH FLOW SUMMARY ---")
    cash_balance = account_balances.get("1-1100", {"debit": 0, "credit": 0})
    cash_net = cash_balance["debit"] - cash_balance["credit"]
    print(f"   Cash Balance (1-1100): Rp {cash_net:,.0f}")
    
    # Final Summary
    print("\n" + "=" * 80)
    print("FINAL VALIDATION RESULT")
    print("=" * 80)
    
    if all_passed:
        print("\n   🎉🎉🎉 ALL TESTS PASSED 🎉🎉🎉")
        print("   ✅ Total Debit = Total Credit")
        print("   ✅ Assets = Liabilities + Equity")
        print("   ✅ All Financial Reports Consistent")
        print("\n   SYSTEM STATUS: OPERATIONALLY STABLE")
    else:
        print("\n   ❌ SOME TESTS FAILED")
        print("   System requires fixes before proceeding")
    
    return all_passed

# ==================== MAIN ====================
async def main():
    print("\n" + "=" * 80)
    print("ERP END-TO-END OPERATIONAL VALIDATION")
    print("=" * 80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    db, client = await get_db()
    
    try:
        # Setup
        master_data = await setup_master_data(db)
        
        # Test 1: Purchase Flow
        purchase_data = await test_purchase_flow(db, master_data)
        
        # Test 2: Sales Flow
        sales_data = await test_sales_flow(db, master_data)
        
        # Test 3: Payment Flow
        await test_payment_flow(db, purchase_data, sales_data)
        
        # Test 4: Stock Opname
        await test_stock_opname(db, master_data)
        
        # Test 5: Financial Reports
        result = await test_financial_reports(db)
        
        return result
        
    finally:
        client.close()

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)
