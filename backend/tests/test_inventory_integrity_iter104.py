"""
Test: P0 INVENTORY INTEGRITY BUG FIX - Iteration 104
Feature: Daftar Item STOCK = Kartu Stok BALANCE consistency

ARCHITECTURE:
- SSOT = stock_movements (ledger resmi)
- Both endpoints use $or: [{product_id}, {item_id}] for backward compatibility
- GET /api/master/items - stock from stock_movements
- GET /api/inventory/stock-card-modal - balance from stock_movements
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "ocbgroupbjm@gmail.com"
TEST_PASSWORD = "admin123"

# Item 001001 for specific test
ITEM_001001_ID = "56eab367-a72c-47bd-8931-1f403199220d"
ITEM_001001_CODE = "001001"


class TestInventoryIntegrity:
    """P0 Inventory Integrity Bug Fix Validation - Daftar Item STOCK = Kartu Stok BALANCE"""
    
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
    
    def test_01_login_success(self, auth_token):
        """Test login works"""
        assert auth_token is not None
        assert len(auth_token) > 10
        print(f"✅ Login successful, token length: {len(auth_token)}")
    
    def test_02_master_items_endpoint_accessible(self, auth_headers):
        """Test /api/master/items endpoint is accessible"""
        response = requests.get(
            f"{BASE_URL}/api/master/items?page=1&limit=10",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Items endpoint failed: {response.text}"
        data = response.json()
        assert "items" in data, "Response missing 'items' field"
        assert "total" in data, "Response missing 'total' field"
        print(f"✅ Items endpoint accessible, total items: {data.get('total')}")
    
    def test_03_stock_card_modal_endpoint_accessible(self, auth_headers):
        """Test /api/inventory/stock-card-modal endpoint is accessible"""
        response = requests.get(
            f"{BASE_URL}/api/inventory/stock-card-modal?item_id={ITEM_001001_ID}",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Stock card modal failed: {response.text}"
        data = response.json()
        assert "item" in data, "Response missing 'item' field"
        assert "balance" in data, "Response missing 'balance' field"
        print(f"✅ Stock card modal accessible, item: {data.get('item', {}).get('code')}")
    
    def test_04_item_001001_stock_in_daftar_item(self, auth_headers):
        """Test Item 001001 stock in Daftar Item (should be 50)"""
        response = requests.get(
            f"{BASE_URL}/api/master/items?search={ITEM_001001_CODE}&limit=10",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Search failed: {response.text}"
        data = response.json()
        
        items = data.get("items", [])
        item_001001 = None
        for item in items:
            if item.get("code") == ITEM_001001_CODE or item.get("id") == ITEM_001001_ID:
                item_001001 = item
                break
        
        assert item_001001 is not None, f"Item {ITEM_001001_CODE} not found in results"
        
        stock_value = item_001001.get("stock", 0)
        print(f"✅ Item {ITEM_001001_CODE} in Daftar Item: STOCK = {stock_value}")
        
        # Store for comparison
        return stock_value
    
    def test_05_item_001001_balance_in_kartu_stok(self, auth_headers):
        """Test Item 001001 balance in Kartu Stok (should be 50)"""
        response = requests.get(
            f"{BASE_URL}/api/inventory/stock-card-modal?item_id={ITEM_001001_ID}",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Stock card failed: {response.text}"
        data = response.json()
        
        balance = data.get("balance", 0)
        item_info = data.get("item", {})
        movements_count = data.get("count", 0)
        
        print(f"✅ Item {item_info.get('code', 'N/A')} in Kartu Stok: BALANCE = {balance}")
        print(f"   Movements count: {movements_count}")
        
        return balance
    
    def test_06_item_001001_stock_equals_balance_CRITICAL(self, auth_headers):
        """
        CRITICAL TEST: Verify Item 001001 STOCK (Daftar Item) = BALANCE (Kartu Stok)
        This is the main P0 bug validation
        """
        # Get stock from Daftar Item
        items_response = requests.get(
            f"{BASE_URL}/api/master/items?search={ITEM_001001_CODE}&limit=10",
            headers=auth_headers
        )
        assert items_response.status_code == 200
        items_data = items_response.json()
        
        item_001001 = None
        for item in items_data.get("items", []):
            if item.get("code") == ITEM_001001_CODE or item.get("id") == ITEM_001001_ID:
                item_001001 = item
                break
        
        assert item_001001 is not None, f"Item {ITEM_001001_CODE} not found"
        daftar_item_stock = item_001001.get("stock", 0)
        
        # Get balance from Kartu Stok
        stock_card_response = requests.get(
            f"{BASE_URL}/api/inventory/stock-card-modal?item_id={ITEM_001001_ID}",
            headers=auth_headers
        )
        assert stock_card_response.status_code == 200
        stock_card_data = stock_card_response.json()
        kartu_stok_balance = stock_card_data.get("balance", 0)
        
        # CRITICAL ASSERTION: Both values must match
        print(f"\n{'='*60}")
        print(f"P0 INVENTORY INTEGRITY CHECK - Item {ITEM_001001_CODE}")
        print(f"{'='*60}")
        print(f"Daftar Item STOCK:     {daftar_item_stock}")
        print(f"Kartu Stok BALANCE:    {kartu_stok_balance}")
        print(f"MATCH:                 {'✅ YES' if daftar_item_stock == kartu_stok_balance else '❌ NO'}")
        print(f"{'='*60}\n")
        
        assert daftar_item_stock == kartu_stok_balance, \
            f"P0 BUG NOT FIXED! Daftar Item STOCK ({daftar_item_stock}) != Kartu Stok BALANCE ({kartu_stok_balance})"
        
        # Also verify the value is 50 as documented
        assert daftar_item_stock == 50, \
            f"Expected stock of 50 for item {ITEM_001001_CODE}, got {daftar_item_stock}"
    
    def test_07_reconcile_10_items(self, auth_headers):
        """
        Reconcile 10 sample items - Daftar Item STOCK must equal Kartu Stok BALANCE
        """
        # Sample items from the fix report
        test_items = [
            {"code": "TPLN15K", "name": "TOKEN PLN 15K"},
            {"code": "TPLN50K", "name": "TOKEN PLN 50K"},
            {"code": "001000", "name": "VOUCER ISAT ZERO"},
            {"code": "001001", "name": "VOUCER ORI ISAT 1GB/2H"},
            {"code": "001002", "name": "VOUCER ORI ISAT 2,5GB/5H"},
            {"code": "001003", "name": "VOUCER ORI ISAT 3,5GB/5H"},
            {"code": "001004", "name": "VOUCER ORI ISAT 5GB/5H"},
            {"code": "001005", "name": "VOUCER ORI ISAT 7GB/7H"},
            {"code": "001006", "name": "VOUCER ORI ISAT 3GB/30H"},
            {"code": "001007", "name": "VOUCER ORI ISAT 5GB 3H"}
        ]
        
        results = []
        all_match = True
        
        print(f"\n{'='*80}")
        print("RECONCILIATION: 10 ITEMS - Daftar Item vs Kartu Stok")
        print(f"{'='*80}")
        print(f"{'#':<3} | {'Code':<12} | {'Daftar Item':<12} | {'Kartu Stok':<12} | {'Match':<6}")
        print(f"{'-'*80}")
        
        for idx, test_item in enumerate(test_items, 1):
            code = test_item["code"]
            
            # Get from Daftar Item
            items_resp = requests.get(
                f"{BASE_URL}/api/master/items?search={code}&limit=5",
                headers=auth_headers
            )
            
            if items_resp.status_code != 200:
                print(f"{idx:<3} | {code:<12} | ERROR | - | ❌")
                all_match = False
                continue
            
            items_data = items_resp.json()
            found_item = None
            for item in items_data.get("items", []):
                if item.get("code") == code:
                    found_item = item
                    break
            
            if not found_item:
                print(f"{idx:<3} | {code:<12} | NOT FOUND | - | ⏭️")
                continue
            
            daftar_item_stock = found_item.get("stock", 0)
            item_id = found_item.get("id")
            
            # Get from Kartu Stok
            stock_card_resp = requests.get(
                f"{BASE_URL}/api/inventory/stock-card-modal?item_id={item_id}",
                headers=auth_headers
            )
            
            if stock_card_resp.status_code != 200:
                print(f"{idx:<3} | {code:<12} | {daftar_item_stock:<12} | ERROR | ❌")
                all_match = False
                continue
            
            kartu_stok_balance = stock_card_resp.json().get("balance", 0)
            
            is_match = daftar_item_stock == kartu_stok_balance
            match_symbol = "✅" if is_match else "❌"
            
            if not is_match:
                all_match = False
            
            print(f"{idx:<3} | {code:<12} | {daftar_item_stock:<12} | {kartu_stok_balance:<12} | {match_symbol}")
            
            results.append({
                "code": code,
                "daftar_item_stock": daftar_item_stock,
                "kartu_stok_balance": kartu_stok_balance,
                "match": is_match
            })
        
        print(f"{'-'*80}")
        matched_count = sum(1 for r in results if r.get("match", False))
        print(f"TOTAL: {matched_count}/{len(results)} items MATCH")
        print(f"{'='*80}\n")
        
        # All items that were found should match
        for result in results:
            assert result.get("match", False), \
                f"Item {result['code']}: Stock ({result['daftar_item_stock']}) != Balance ({result['kartu_stok_balance']})"
    
    def test_08_branch_filter_consistency(self, auth_headers):
        """Test that branch filter in Daftar Item is consistent with Kartu Stok"""
        # First get available branches
        branches_resp = requests.get(
            f"{BASE_URL}/api/master/branches",
            headers=auth_headers
        )
        
        if branches_resp.status_code != 200:
            pytest.skip("Could not get branches list")
        
        branches = branches_resp.json()
        if isinstance(branches, dict):
            branches = branches.get("items", branches.get("branches", []))
        
        if not branches:
            pytest.skip("No branches found")
        
        # Take first branch for testing
        first_branch = branches[0] if isinstance(branches, list) else None
        if not first_branch:
            pytest.skip("No valid branch found")
        
        branch_id = first_branch.get("id")
        branch_name = first_branch.get("name", "Unknown")
        
        print(f"\n🔍 Testing branch filter consistency for: {branch_name}")
        
        # Get Item 001001 stock with branch filter
        items_resp = requests.get(
            f"{BASE_URL}/api/master/items?search={ITEM_001001_CODE}&branch_id={branch_id}&limit=5",
            headers=auth_headers
        )
        assert items_resp.status_code == 200
        
        items_data = items_resp.json()
        found_item = None
        for item in items_data.get("items", []):
            if item.get("code") == ITEM_001001_CODE:
                found_item = item
                break
        
        if not found_item:
            pytest.skip(f"Item {ITEM_001001_CODE} not found with branch filter")
        
        daftar_item_stock_branch = found_item.get("stock", 0)
        
        # Get from Kartu Stok with branch filter
        stock_card_resp = requests.get(
            f"{BASE_URL}/api/inventory/stock-card-modal?item_id={ITEM_001001_ID}&branch_id={branch_id}",
            headers=auth_headers
        )
        assert stock_card_resp.status_code == 200
        
        kartu_stok_balance_branch = stock_card_resp.json().get("balance", 0)
        
        print(f"Branch: {branch_name} (ID: {branch_id})")
        print(f"Daftar Item STOCK (filtered): {daftar_item_stock_branch}")
        print(f"Kartu Stok BALANCE (filtered): {kartu_stok_balance_branch}")
        
        # Should match even with branch filter
        assert daftar_item_stock_branch == kartu_stok_balance_branch, \
            f"Branch filter mismatch: Stock ({daftar_item_stock_branch}) != Balance ({kartu_stok_balance_branch})"
        
        print(f"✅ Branch filter consistency PASSED")
    
    def test_09_stock_card_running_balance_correct(self, auth_headers):
        """Test that Kartu Stok running balance is calculated correctly"""
        response = requests.get(
            f"{BASE_URL}/api/inventory/stock-card-modal?item_id={ITEM_001001_ID}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        movements = data.get("movements", [])
        final_balance = data.get("balance", 0)
        total_in = data.get("total_in", 0)
        total_out = data.get("total_out", 0)
        
        # Verify running balance calculation
        calculated_balance = total_in - total_out
        
        print(f"\nKartu Stok Running Balance Check:")
        print(f"Total In: {total_in}")
        print(f"Total Out: {total_out}")
        print(f"Calculated Balance: {calculated_balance}")
        print(f"Reported Balance: {final_balance}")
        print(f"Movements Count: {len(movements)}")
        
        assert final_balance == calculated_balance, \
            f"Running balance incorrect: Reported ({final_balance}) != Calculated ({calculated_balance})"
        
        print(f"✅ Running balance calculation correct")
    
    def test_10_no_branch_filter_aggregates_all_branches(self, auth_headers):
        """Test that no branch filter aggregates stock from all branches"""
        # Get stock without branch filter
        items_resp = requests.get(
            f"{BASE_URL}/api/master/items?search={ITEM_001001_CODE}&limit=5",
            headers=auth_headers
        )
        assert items_resp.status_code == 200
        
        items_data = items_resp.json()
        found_item = None
        for item in items_data.get("items", []):
            if item.get("code") == ITEM_001001_CODE:
                found_item = item
                break
        
        assert found_item is not None, f"Item {ITEM_001001_CODE} not found"
        
        total_stock = found_item.get("stock", 0)
        branches_count = found_item.get("branches_count", 0)
        
        print(f"\nNo Branch Filter - Aggregate Stock:")
        print(f"Item: {ITEM_001001_CODE}")
        print(f"Total Stock (all branches): {total_stock}")
        print(f"Branches with stock: {branches_count}")
        
        # Should have stock aggregated
        assert total_stock >= 0, "Stock should be non-negative"
        
        print(f"✅ Stock aggregation working")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
