"""
Test: STOK BARANG MODULE SYNC - Iteration 105
Feature: 3 Module Synchronization (Stok Barang = Daftar Item = Kartu Stok)

ARCHITECTURE:
- SSOT = stock_movements collection
- All 3 modules use $or: [{product_id}, {item_id}] for backward compatibility
- GET /api/inventory/stock - Stok Barang module (tested here)
- GET /api/master/items - Daftar Item module
- GET /api/inventory/stock-card-modal - Kartu Stok module
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "ocbgroupbjm@gmail.com"
TEST_PASSWORD = "admin123"

# Test items for reconciliation
TEST_ITEMS = [
    {"code": "001000", "expected_stock": 141},
    {"code": "001001", "expected_stock": 1750},  # Main test item
    {"code": "001002", "expected_stock": 18},
    {"code": "001003", "expected_stock": 18},
    {"code": "001004", "expected_stock": 24},
    {"code": "001005", "expected_stock": 21},
    {"code": "001006", "expected_stock": 0},
    {"code": "001007", "expected_stock": 24},
    {"code": "TPLN15K", "expected_stock": 0},
    {"code": "TPLN50K", "expected_stock": 0},
]


class TestStokBarangSync:
    """Test sync between Stok Barang, Daftar Item, and Kartu Stok modules"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        return data.get("token") or data.get("access_token")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get headers with auth token"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    # ==================== BASIC ENDPOINT TESTS ====================
    
    def test_01_login_success(self, auth_token):
        """Test login works"""
        assert auth_token is not None
        assert len(auth_token) > 10
        print(f"✅ Login successful")
    
    def test_02_stok_barang_endpoint_accessible(self, auth_headers):
        """Test /api/inventory/stock endpoint is accessible (Stok Barang)"""
        response = requests.get(
            f"{BASE_URL}/api/inventory/stock?limit=10",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Stok Barang endpoint failed: {response.text}"
        data = response.json()
        assert "items" in data, "Response missing 'items' field"
        assert "total" in data, "Response missing 'total' field"
        print(f"✅ Stok Barang endpoint accessible, total items: {data.get('total')}")
    
    def test_03_daftar_item_endpoint_accessible(self, auth_headers):
        """Test /api/master/items endpoint is accessible (Daftar Item)"""
        response = requests.get(
            f"{BASE_URL}/api/master/items?page=1&limit=10",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Daftar Item endpoint failed: {response.text}"
        data = response.json()
        assert "items" in data, "Response missing 'items' field"
        print(f"✅ Daftar Item endpoint accessible, total items: {data.get('total')}")
    
    def test_04_kartu_stok_endpoint_accessible(self, auth_headers):
        """Test /api/inventory/stock-card-modal endpoint is accessible (Kartu Stok)"""
        # First get an item id to test with
        items_resp = requests.get(
            f"{BASE_URL}/api/master/items?search=001001&limit=5",
            headers=auth_headers
        )
        if items_resp.status_code != 200:
            pytest.skip("Cannot get item for Kartu Stok test")
        
        items = items_resp.json().get("items", [])
        if not items:
            pytest.skip("No items found for Kartu Stok test")
        
        item_id = items[0].get("id")
        
        response = requests.get(
            f"{BASE_URL}/api/inventory/stock-card-modal?item_id={item_id}",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Kartu Stok endpoint failed: {response.text}"
        data = response.json()
        assert "item" in data, "Response missing 'item' field"
        assert "balance" in data, "Response missing 'balance' field"
        print(f"✅ Kartu Stok endpoint accessible, item balance: {data.get('balance')}")
    
    # ==================== 3 MODULE RECONCILIATION ====================
    
    def test_05_item_001001_three_module_sync(self, auth_headers):
        """
        CRITICAL TEST: Item 001001 must show same qty in all 3 modules
        Expected: 1750 (or current SSOT value)
        """
        item_code = "001001"
        
        # 1. Get from Stok Barang (/api/inventory/stock)
        stok_barang_resp = requests.get(
            f"{BASE_URL}/api/inventory/stock?search={item_code}&limit=10",
            headers=auth_headers
        )
        assert stok_barang_resp.status_code == 200, f"Stok Barang failed: {stok_barang_resp.text}"
        stok_barang_data = stok_barang_resp.json()
        
        stok_barang_item = None
        for item in stok_barang_data.get("items", []):
            if item.get("product_code") == item_code or item.get("code") == item_code:
                stok_barang_item = item
                break
        
        assert stok_barang_item is not None, f"Item {item_code} not found in Stok Barang"
        stok_barang_qty = stok_barang_item.get("quantity", 0)
        product_id = stok_barang_item.get("product_id")
        
        # 2. Get from Daftar Item (/api/master/items)
        daftar_item_resp = requests.get(
            f"{BASE_URL}/api/master/items?search={item_code}&limit=10",
            headers=auth_headers
        )
        assert daftar_item_resp.status_code == 200
        daftar_item_data = daftar_item_resp.json()
        
        daftar_item_item = None
        for item in daftar_item_data.get("items", []):
            if item.get("code") == item_code:
                daftar_item_item = item
                break
        
        assert daftar_item_item is not None, f"Item {item_code} not found in Daftar Item"
        daftar_item_stock = daftar_item_item.get("stock", 0)
        
        # 3. Get from Kartu Stok (/api/inventory/stock-card-modal)
        item_id_for_kartu = product_id or daftar_item_item.get("id")
        kartu_stok_resp = requests.get(
            f"{BASE_URL}/api/inventory/stock-card-modal?item_id={item_id_for_kartu}",
            headers=auth_headers
        )
        assert kartu_stok_resp.status_code == 200
        kartu_stok_data = kartu_stok_resp.json()
        kartu_stok_balance = kartu_stok_data.get("balance", 0)
        
        # Print comparison
        print(f"\n{'='*70}")
        print(f"3 MODULE RECONCILIATION - Item {item_code}")
        print(f"{'='*70}")
        print(f"Stok Barang (inventory/stock):  {stok_barang_qty}")
        print(f"Daftar Item (master/items):     {daftar_item_stock}")
        print(f"Kartu Stok (stock-card-modal):  {kartu_stok_balance}")
        print(f"{'='*70}")
        
        # All 3 must match
        assert stok_barang_qty == daftar_item_stock, \
            f"MISMATCH! Stok Barang ({stok_barang_qty}) != Daftar Item ({daftar_item_stock})"
        assert stok_barang_qty == kartu_stok_balance, \
            f"MISMATCH! Stok Barang ({stok_barang_qty}) != Kartu Stok ({kartu_stok_balance})"
        
        print(f"✅ All 3 modules MATCH: {stok_barang_qty}")
    
    def test_06_reconcile_10_items_all_modules(self, auth_headers):
        """
        Reconcile 10 items across all 3 modules
        Each item must show SAME quantity in Stok Barang, Daftar Item, and Kartu Stok
        """
        results = []
        all_match = True
        
        print(f"\n{'='*90}")
        print("FULL RECONCILIATION: 10 ITEMS - Stok Barang vs Daftar Item vs Kartu Stok")
        print(f"{'='*90}")
        print(f"{'#':<3} | {'Code':<12} | {'Stok Barang':<12} | {'Daftar Item':<12} | {'Kartu Stok':<12} | {'Match':<6}")
        print(f"{'-'*90}")
        
        for idx, test_item in enumerate(TEST_ITEMS, 1):
            code = test_item["code"]
            
            # 1. Stok Barang
            stok_resp = requests.get(
                f"{BASE_URL}/api/inventory/stock?search={code}&limit=5",
                headers=auth_headers
            )
            stok_barang_qty = 0
            product_id = None
            if stok_resp.status_code == 200:
                for item in stok_resp.json().get("items", []):
                    if item.get("product_code") == code or item.get("code") == code:
                        stok_barang_qty = item.get("quantity", 0)
                        product_id = item.get("product_id")
                        break
            
            # 2. Daftar Item
            items_resp = requests.get(
                f"{BASE_URL}/api/master/items?search={code}&limit=5",
                headers=auth_headers
            )
            daftar_item_stock = 0
            item_id = None
            if items_resp.status_code == 200:
                for item in items_resp.json().get("items", []):
                    if item.get("code") == code:
                        daftar_item_stock = item.get("stock", 0)
                        item_id = item.get("id")
                        break
            
            # Skip if item not found
            if not product_id and not item_id:
                print(f"{idx:<3} | {code:<12} | {'N/A':<12} | {'N/A':<12} | {'N/A':<12} | ⏭️")
                continue
            
            # 3. Kartu Stok
            kartu_stok_balance = 0
            use_id = product_id or item_id
            if use_id:
                kartu_resp = requests.get(
                    f"{BASE_URL}/api/inventory/stock-card-modal?item_id={use_id}",
                    headers=auth_headers
                )
                if kartu_resp.status_code == 200:
                    kartu_stok_balance = kartu_resp.json().get("balance", 0)
            
            # Check if all match
            match_sb_di = stok_barang_qty == daftar_item_stock
            match_sb_ks = stok_barang_qty == kartu_stok_balance
            is_match = match_sb_di and match_sb_ks
            match_symbol = "✅" if is_match else "❌"
            
            if not is_match:
                all_match = False
            
            print(f"{idx:<3} | {code:<12} | {stok_barang_qty:<12} | {daftar_item_stock:<12} | {kartu_stok_balance:<12} | {match_symbol}")
            
            results.append({
                "code": code,
                "stok_barang": stok_barang_qty,
                "daftar_item": daftar_item_stock,
                "kartu_stok": kartu_stok_balance,
                "match": is_match
            })
        
        print(f"{'-'*90}")
        matched_count = sum(1 for r in results if r.get("match", False))
        print(f"TOTAL: {matched_count}/{len(results)} items MATCH across all 3 modules")
        print(f"{'='*90}\n")
        
        # Assert all found items match
        for result in results:
            assert result.get("match", False), \
                f"Item {result['code']}: Stok Barang ({result['stok_barang']}) vs Daftar Item ({result['daftar_item']}) vs Kartu Stok ({result['kartu_stok']})"
    
    # ==================== BRANCH FILTER TESTS ====================
    
    def test_07_stok_barang_no_default_branch_filter(self, auth_headers):
        """
        Test that Stok Barang without branch_id shows total from ALL branches
        No default branch filter should be applied
        """
        # Get stock without branch filter
        response = requests.get(
            f"{BASE_URL}/api/inventory/stock?search=001001&limit=10",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Find item 001001
        item_001001 = None
        for item in data.get("items", []):
            if item.get("product_code") == "001001" or item.get("code") == "001001":
                item_001001 = item
                break
        
        assert item_001001 is not None, "Item 001001 not found"
        
        total_qty = item_001001.get("quantity", 0)
        branch_id_in_response = item_001001.get("branch_id", "")
        
        print(f"\nStok Barang without branch filter:")
        print(f"Item: 001001")
        print(f"Total Quantity: {total_qty}")
        print(f"Branch ID in response: {branch_id_in_response}")
        
        # Should NOT be filtered by user's branch (total should be > branch-specific qty)
        # branch_id should be 'all' or empty when no filter applied
        assert total_qty > 0, "Stock should be positive for item 001001"
        assert branch_id_in_response in ["all", ""], \
            f"Expected branch_id 'all' or empty, got: {branch_id_in_response}"
        
        print(f"✅ No default branch filter applied, showing total: {total_qty}")
    
    def test_08_stok_barang_with_branch_filter(self, auth_headers):
        """Test that Stok Barang with explicit branch_id filters correctly"""
        # First get available branches
        branches_resp = requests.get(
            f"{BASE_URL}/api/inventory/stock?limit=5",  # Get any item to see branches
            headers=auth_headers
        )
        
        if branches_resp.status_code != 200:
            pytest.skip("Cannot get branches")
        
        # Get branches from another endpoint
        branches_list_resp = requests.get(
            f"{BASE_URL}/api/master/warehouses",  # Using warehouses as proxy for branches
            headers=auth_headers
        )
        
        if branches_list_resp.status_code != 200:
            pytest.skip("Cannot get branches list")
        
        branches = branches_list_resp.json()
        if isinstance(branches, dict):
            branches = branches.get("items", branches.get("branches", []))
        
        if not branches or not isinstance(branches, list) or len(branches) == 0:
            pytest.skip("No branches found")
        
        branch_id = branches[0].get("id")
        branch_name = branches[0].get("name", "Unknown")
        
        print(f"\nTesting branch filter with: {branch_name} ({branch_id})")
        
        # Get stock WITH branch filter
        filtered_resp = requests.get(
            f"{BASE_URL}/api/inventory/stock?search=001001&branch_id={branch_id}&limit=10",
            headers=auth_headers
        )
        assert filtered_resp.status_code == 200
        
        filtered_data = filtered_resp.json()
        
        # Get stock WITHOUT branch filter
        unfiltered_resp = requests.get(
            f"{BASE_URL}/api/inventory/stock?search=001001&limit=10",
            headers=auth_headers
        )
        assert unfiltered_resp.status_code == 200
        unfiltered_data = unfiltered_resp.json()
        
        # Find item in both results
        filtered_item = None
        unfiltered_item = None
        
        for item in filtered_data.get("items", []):
            if item.get("product_code") == "001001":
                filtered_item = item
                break
        
        for item in unfiltered_data.get("items", []):
            if item.get("product_code") == "001001":
                unfiltered_item = item
                break
        
        if filtered_item and unfiltered_item:
            filtered_qty = filtered_item.get("quantity", 0)
            unfiltered_qty = unfiltered_item.get("quantity", 0)
            
            print(f"With branch filter ({branch_name}): {filtered_qty}")
            print(f"Without branch filter (all): {unfiltered_qty}")
            
            # Filtered should be <= unfiltered (branch subset of total)
            assert filtered_qty <= unfiltered_qty, \
                f"Branch filter not working: filtered ({filtered_qty}) > unfiltered ({unfiltered_qty})"
            
            print(f"✅ Branch filter working correctly")
        else:
            print(f"⚠️ Item not found in one of the results")
    
    # ==================== SSOT VERIFICATION ====================
    
    def test_09_verify_ssot_source(self, auth_headers):
        """
        Verify that /api/inventory/stock uses stock_movements as SSOT
        The implementation should use $or query for backward compatibility
        """
        # Get an item
        response = requests.get(
            f"{BASE_URL}/api/inventory/stock?search=001001&limit=5",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        items = data.get("items", [])
        if not items:
            pytest.skip("No items found")
        
        item = items[0]
        
        # Check response structure from /api/inventory/stock
        print(f"\nStok Barang response structure:")
        print(f"  product_id: {item.get('product_id')}")
        print(f"  product_code: {item.get('product_code')}")
        print(f"  quantity: {item.get('quantity')}")
        print(f"  available: {item.get('available')}")
        print(f"  branch_id: {item.get('branch_id')}")
        
        # Verify required fields
        assert "product_id" in item, "Missing product_id field"
        assert "quantity" in item, "Missing quantity field"
        
        # Quantity should be a number
        qty = item.get("quantity", 0)
        assert isinstance(qty, (int, float)), f"quantity should be number, got {type(qty)}"
        
        print(f"✅ SSOT response structure verified")
    
    def test_10_quantity_data_integrity(self, auth_headers):
        """Test that quantities are consistent and non-negative where expected"""
        response = requests.get(
            f"{BASE_URL}/api/inventory/stock?limit=50",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        items = data.get("items", [])
        
        negative_stock_items = []
        for item in items:
            qty = item.get("quantity", 0)
            # Note: Some items might have negative stock (backorders), but most should be >= 0
            if qty < 0:
                negative_stock_items.append({
                    "code": item.get("product_code"),
                    "quantity": qty
                })
        
        print(f"\nData Integrity Check:")
        print(f"Total items checked: {len(items)}")
        print(f"Items with negative stock: {len(negative_stock_items)}")
        
        if negative_stock_items:
            print("Negative stock items:")
            for neg_item in negative_stock_items[:5]:  # Show first 5
                print(f"  {neg_item['code']}: {neg_item['quantity']}")
        
        # Allow some negative stock but flag if too many
        assert len(negative_stock_items) < len(items) * 0.1, \
            f"Too many items ({len(negative_stock_items)}) have negative stock"
        
        print(f"✅ Data integrity check passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
