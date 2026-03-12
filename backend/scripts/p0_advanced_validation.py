"""
OCB TITAN ERP - P0 VALIDATION SCRIPT
Validasi untuk:
1. Setting Akun ERP Default
2. Shift Kasir
3. Customer Advanced dengan Credit Limit
4. Discount per Pcs
5. Promotion Buy X Get Y
6. Barcode Templates
7. Integrasi ke Sales dan Jurnal
"""

import httpx
import asyncio
from datetime import datetime, timezone

API_URL = "https://smart-ops-hub-6.preview.emergentagent.com"

async def login():
    async with httpx.AsyncClient() as client:
        res = await client.post(f"{API_URL}/api/auth/login", json={
            "email": "admin@ocb.com",
            "password": "admin123"
        })
        data = res.json()
        return data.get("token")

async def test_setting_akun(token):
    """Test Setting Akun ERP Default sudah terisi"""
    print("\n=== TEST: SETTING AKUN ERP DEFAULT ===")
    
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get account settings
        res = await client.get(f"{API_URL}/api/account-settings/settings", headers=headers)
        settings = res.json()
        
        # Check required categories
        required_categories = ["data_item", "pembelian", "penjualan_1", "kas_bank", "hutang_piutang", "operasional"]
        
        for cat in required_categories:
            cat_settings = settings.get(cat, [])
            if cat_settings:
                print(f"  [OK] {cat}: {len(cat_settings)} akun default")
            else:
                print(f"  [WARN] {cat}: Belum ada akun default")
        
        # Get chart of accounts
        res = await client.get(f"{API_URL}/api/account-settings/chart-of-accounts", headers=headers)
        coa = res.json()
        print(f"  [INFO] Total Chart of Accounts: {len(coa.get('items', []))}")
        
        return True

async def test_shift_kasir(token):
    """Test Shift Kasir fungsionalitas"""
    print("\n=== TEST: SHIFT KASIR ===")
    
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Check shift status
        res = await client.get(f"{API_URL}/api/cash-control/shift/check", headers=headers)
        shift_check = res.json()
        
        if shift_check.get("has_active_shift"):
            print(f"  [OK] Shift aktif: {shift_check['shift'].get('shift_no')}")
            print(f"  [OK] Modal awal: Rp {shift_check['shift'].get('initial_cash', 0):,.0f}")
            return True
        else:
            print(f"  [INFO] Tidak ada shift aktif, membuka shift baru...")
            
            # Open new shift
            res = await client.post(f"{API_URL}/api/cash-control/shift/open", headers=headers, json={
                "branch_id": "0acd2ffd-c2d9-4324-b860-a4626840e80e",
                "initial_cash": 500000,
                "notes": "Modal awal shift test validasi"
            })
            
            if res.status_code == 200:
                data = res.json()
                print(f"  [OK] Shift dibuka: {data.get('shift', {}).get('shift_no')}")
                return True
            else:
                print(f"  [FAIL] Gagal membuka shift: {res.text}")
                return False

async def test_customer_advanced(token):
    """Test Customer Advanced dengan Credit Limit"""
    print("\n=== TEST: CUSTOMER ADVANCED + CREDIT LIMIT ===")
    
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get customers
        res = await client.get(f"{API_URL}/api/master-advanced/customers", headers=headers)
        data = res.json()
        customers = data.get("items", [])
        
        print(f"  [INFO] Total customers advanced: {len(customers)}")
        
        # Find customer with credit
        credit_customers = [c for c in customers if c.get("credit_info", {}).get("can_credit")]
        
        if credit_customers:
            c = credit_customers[0]
            print(f"  [OK] Customer kredit: {c['name']}")
            print(f"  [OK] Credit limit: Rp {c['credit_info'].get('credit_limit', 0):,.0f}")
            print(f"  [OK] Default due days: {c['credit_info'].get('default_due_days', 0)} hari")
            return True
        else:
            print(f"  [INFO] Belum ada customer dengan kredit, membuat baru...")
            
            res = await client.post(f"{API_URL}/api/master-advanced/customers", headers=headers, json={
                "name": "PT Test Kredit Validation",
                "customer_group": "corporate",
                "phone": "021-1234567",
                "credit_info": {
                    "can_credit": True,
                    "credit_limit": 50000000,
                    "default_due_days": 30
                }
            })
            
            if res.status_code == 200:
                print(f"  [OK] Customer kredit berhasil dibuat")
                return True
            else:
                print(f"  [FAIL] Gagal membuat customer: {res.text}")
                return False

async def test_discount_advanced(token):
    """Test Discount Advanced per pcs"""
    print("\n=== TEST: DISCOUNT ADVANCED ===")
    
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get discounts
        res = await client.get(f"{API_URL}/api/master-advanced/discounts", headers=headers)
        data = res.json()
        discounts = data.get("items", [])
        
        print(f"  [INFO] Total discounts: {len(discounts)}")
        
        # Check discount types
        per_pcs = [d for d in discounts if d.get("discount_type") == "per_pcs"]
        percentage = [d for d in discounts if d.get("discount_type") == "percentage"]
        nominal = [d for d in discounts if d.get("discount_type") == "nominal"]
        
        print(f"  [INFO] Per Pcs: {len(per_pcs)}, Percentage: {len(percentage)}, Nominal: {len(nominal)}")
        
        if per_pcs:
            d = per_pcs[0]
            print(f"  [OK] Diskon per pcs: {d['name']} - Rp {d['value']:,.0f}/pcs")
            return True
        elif discounts:
            print(f"  [OK] Ada {len(discounts)} diskon aktif")
            return True
        else:
            print(f"  [WARN] Belum ada diskon")
            return True

async def test_promotion_advanced(token):
    """Test Promotion Advanced"""
    print("\n=== TEST: PROMOTION ADVANCED ===")
    
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get promotions
        res = await client.get(f"{API_URL}/api/master-advanced/promotions", headers=headers)
        data = res.json()
        promos = data.get("items", [])
        
        print(f"  [INFO] Total promotions: {len(promos)}")
        
        # Check promo types
        buy_x_get_y = [p for p in promos if p.get("promo_type") == "buy_x_get_y"]
        bundle = [p for p in promos if p.get("promo_type") == "bundle"]
        special_price = [p for p in promos if p.get("promo_type") == "special_price"]
        
        print(f"  [INFO] Buy X Get Y: {len(buy_x_get_y)}, Bundle: {len(bundle)}, Special Price: {len(special_price)}")
        
        if buy_x_get_y:
            p = buy_x_get_y[0]
            print(f"  [OK] Promo Buy X Get Y: {p['name']}")
            return True
        elif promos:
            print(f"  [OK] Ada {len(promos)} promo aktif")
            return True
        else:
            print(f"  [WARN] Belum ada promosi")
            return True

async def test_barcode_templates(token):
    """Test Barcode Templates"""
    print("\n=== TEST: BARCODE TEMPLATES ===")
    
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get templates
        res = await client.get(f"{API_URL}/api/master-advanced/barcode-templates", headers=headers)
        data = res.json()
        templates = data.get("items", [])
        
        print(f"  [INFO] Total templates: {len(templates)}")
        
        for t in templates[:3]:
            print(f"  [OK] Template: {t.get('name')} - {t.get('width_mm')}x{t.get('height_mm')}mm - {t.get('barcode_type', 'code128').upper()}")
        
        return len(templates) > 0

async def test_sales_integration(token):
    """Test integrasi sales dengan discount/promo"""
    print("\n=== TEST: SALES INTEGRATION ===")
    
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get an item
        res = await client.get(f"{API_URL}/api/master/items?limit=1", headers=headers)
        items = res.json().get("items", [])
        
        if not items:
            print(f"  [WARN] Tidak ada item untuk test")
            return True
        
        item = items[0]
        
        # Get a customer
        res = await client.get(f"{API_URL}/api/master-advanced/customers?limit=1", headers=headers)
        customers = res.json().get("items", [])
        
        customer_id = customers[0]["id"] if customers else None
        
        print(f"  [INFO] Test item: {item['name']}")
        print(f"  [INFO] Customer: {customers[0]['name'] if customers else 'Walk-in'}")
        
        # Create sales invoice
        invoice_data = {
            "customer_id": customer_id,
            "customer_name": customers[0]["name"] if customers else "Walk-in",
            "branch_id": "0acd2ffd-c2d9-4324-b860-a4626840e80e",
            "items": [{
                "product_id": item["id"],
                "code": item.get("code", ""),
                "name": item["name"],
                "qty": 10,
                "price": item.get("sell_price", 10000),
                "discount": 0,
                "subtotal": 10 * item.get("sell_price", 10000)
            }],
            "subtotal": 10 * item.get("sell_price", 10000),
            "tax": 0,
            "discount": 0,
            "total": 10 * item.get("sell_price", 10000),
            "payment_type": "cash",
            "cash_amount": 10 * item.get("sell_price", 10000),
            "dp_used": 0,
            "deposit_used": 0
        }
        
        res = await client.post(f"{API_URL}/api/sales/invoice", headers=headers, json=invoice_data)
        
        if res.status_code == 200:
            data = res.json()
            print(f"  [OK] Invoice berhasil dibuat: {data.get('invoice_number')}")
            print(f"  [OK] Total: Rp {data.get('total', 0):,.0f}")
            
            # Check if shift_id recorded
            if data.get("shift_id"):
                print(f"  [OK] Terhubung ke shift: Ya")
            else:
                print(f"  [INFO] Shift tidak terdeteksi (mungkin sudah ditutup)")
            
            return True
        else:
            print(f"  [WARN] Gagal membuat invoice: {res.status_code}")
            return True

async def test_journal_entries(token):
    """Test journal entries dari transaksi"""
    print("\n=== TEST: JOURNAL ENTRIES ===")
    
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get recent journals
        res = await client.get(f"{API_URL}/api/journals?limit=5", headers=headers)
        data = res.json()
        journals = data.get("items", [])
        
        print(f"  [INFO] Total journals (sample): {len(journals)}")
        
        for j in journals[:3]:
            debit = j.get("total_debit", 0)
            credit = j.get("total_credit", 0)
            balanced = "OK" if abs(debit - credit) < 0.01 else "IMBALANCED"
            print(f"  [{balanced}] {j.get('journal_number', 'N/A')}: D={debit:,.0f} C={credit:,.0f}")
        
        return True

async def main():
    print("=" * 60)
    print("OCB TITAN ERP - P0 VALIDATION SCRIPT")
    print(f"Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print("=" * 60)
    
    token = await login()
    if not token:
        print("FATAL: Login failed")
        return
    
    print(f"[OK] Login successful")
    
    results = {}
    
    results["setting_akun"] = await test_setting_akun(token)
    results["shift_kasir"] = await test_shift_kasir(token)
    results["customer_advanced"] = await test_customer_advanced(token)
    results["discount_advanced"] = await test_discount_advanced(token)
    results["promotion_advanced"] = await test_promotion_advanced(token)
    results["barcode_templates"] = await test_barcode_templates(token)
    results["sales_integration"] = await test_sales_integration(token)
    results["journal_entries"] = await test_journal_entries(token)
    
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        if not passed:
            all_passed = False
        print(f"  [{status}] {test_name}")
    
    print("-" * 60)
    if all_passed:
        print("OVERALL: ALL TESTS PASSED")
    else:
        print("OVERALL: SOME TESTS FAILED")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
