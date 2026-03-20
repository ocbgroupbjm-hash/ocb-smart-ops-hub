"""
Test Kartu Stok MODE FILTER feature - iteration 107
Tests for the new toggle between 'Semua Periode (Stok Saat Ini)' and 'Berdasarkan Periode' modes

Features tested:
1. stock-card-modal endpoint (Semua Periode mode) - all transactions without date filter
2. stock-card endpoint (Berdasarkan Periode mode) - filtered by month/year
3. Both modes should show consistent stock values when viewing same data
4. Backward compatibility with $or pattern for product_id/item_id
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestKartuStokModeFilter:
    """Tests for Kartu Stok MODE FILTER toggle functionality"""
    
    token = None
    item_001002_id = "6ebc4cf3-e344-4491-97bf-5e69a32036b1"  # VOUCER ORI ISAT 2,5GB/5H
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get token before each test"""
        if not TestKartuStokModeFilter.token:
            response = requests.post(
                f"{BASE_URL}/api/auth/login",
                json={
                    "email": "ocbgroupbjm@gmail.com",
                    "password": "admin123",
                    "tenant_id": "ocb_titan"
                }
            )
            assert response.status_code == 200, f"Login failed: {response.text}"
            TestKartuStokModeFilter.token = response.json().get("token")
        
        self.headers = {
            "Authorization": f"Bearer {TestKartuStokModeFilter.token}",
            "Content-Type": "application/json"
        }
    
    # =================================================================
    # TEST: Login and basic auth
    # =================================================================
    def test_01_login_success(self):
        """Verify login works and token is obtained"""
        assert TestKartuStokModeFilter.token is not None
        assert len(TestKartuStokModeFilter.token) > 0
        print("✅ Login successful, token obtained")
    
    # =================================================================
    # TEST: Item search endpoint
    # =================================================================
    def test_02_items_search_accessible(self):
        """Verify item search endpoint works"""
        response = requests.get(
            f"{BASE_URL}/api/inventory/stock-card/items-search?q=001002",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) > 0
        print(f"✅ Item search returned {len(data['items'])} items")
    
    def test_03_item_001002_found(self):
        """Verify item 001002 can be found"""
        response = requests.get(
            f"{BASE_URL}/api/inventory/stock-card/items-search?q=001002",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        items = data.get("items", [])
        item_001002 = next((i for i in items if i.get("code") == "001002"), None)
        assert item_001002 is not None
        assert item_001002.get("name") == "VOUCER ORI ISAT 2,5GB/5H"
        print(f"✅ Item 001002 found: {item_001002['name']}")
    
    # =================================================================
    # TEST: stock-card-modal endpoint (Semua Periode mode)
    # =================================================================
    def test_04_stock_card_modal_accessible(self):
        """Verify stock-card-modal endpoint (Semua Periode) works"""
        response = requests.get(
            f"{BASE_URL}/api/inventory/stock-card-modal?item_id={self.item_001002_id}",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "item" in data
        assert "movements" in data
        assert "balance" in data
        print(f"✅ stock-card-modal endpoint accessible, balance={data['balance']}")
    
    def test_05_semua_periode_item_001002_balance(self):
        """Verify item 001002 shows balance=18 in Semua Periode mode"""
        response = requests.get(
            f"{BASE_URL}/api/inventory/stock-card-modal?item_id={self.item_001002_id}",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify balance is 18
        assert data["balance"] == 18, f"Expected balance=18, got {data['balance']}"
        assert data["total_in"] == 18
        assert data["total_out"] == 0
        assert data["count"] >= 1
        
        print(f"✅ Item 001002 Semua Periode - balance={data['balance']}, total_in={data['total_in']}, movements={data['count']}")
    
    # =================================================================
    # TEST: stock-card endpoint (Berdasarkan Periode mode)
    # =================================================================
    def test_06_stock_card_period_accessible(self):
        """Verify stock-card endpoint (Berdasarkan Periode) works"""
        response = requests.get(
            f"{BASE_URL}/api/inventory/stock-card?item_id={self.item_001002_id}&month=3&year=2026",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "item" in data
        assert "movements" in data
        assert "period" in data
        assert "closing_balance" in data
        print(f"✅ stock-card period endpoint accessible, period={data['period']}")
    
    def test_07_period_march_2026_item_001002_balance(self):
        """Verify item 001002 shows closing_balance=18 in Period March 2026"""
        response = requests.get(
            f"{BASE_URL}/api/inventory/stock-card?item_id={self.item_001002_id}&month=3&year=2026",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify closing balance is 18 (matches Semua Periode)
        assert data["closing_balance"] == 18, f"Expected closing_balance=18, got {data['closing_balance']}"
        assert data["total_masuk"] == 18
        assert data["total_keluar"] == 0
        assert data["period"] == "03/2026"
        
        print(f"✅ Item 001002 Period 03/2026 - closing_balance={data['closing_balance']}, total_masuk={data['total_masuk']}")
    
    def test_08_period_mode_shows_transactions(self):
        """Verify Period mode shows stock opname transaction"""
        response = requests.get(
            f"{BASE_URL}/api/inventory/stock-card?item_id={self.item_001002_id}&month=3&year=2026",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        movements = data.get("movements", [])
        # Should have at least 2 rows: Saldo Awal + the opname transaction
        assert len(movements) >= 2, f"Expected >= 2 movements, got {len(movements)}"
        
        # First row should be Saldo Awal
        assert movements[0]["tipe"] == "Saldo Awal"
        
        # Second row should be the stock opname
        opname_row = next((m for m in movements if "Opname" in m.get("tipe", "")), None)
        assert opname_row is not None, "Stock opname transaction not found in movements"
        assert opname_row["masuk"] == 18
        
        print(f"✅ Period mode shows {len(movements)} movements including stock opname")
    
    # =================================================================
    # TEST: Consistency between modes
    # =================================================================
    def test_09_both_modes_consistent_balance(self):
        """Verify both modes show consistent balance for same item"""
        # Get Semua Periode balance
        response1 = requests.get(
            f"{BASE_URL}/api/inventory/stock-card-modal?item_id={self.item_001002_id}",
            headers=self.headers
        )
        assert response1.status_code == 200
        semua_balance = response1.json()["balance"]
        
        # Get Berdasarkan Periode balance (March 2026)
        response2 = requests.get(
            f"{BASE_URL}/api/inventory/stock-card?item_id={self.item_001002_id}&month=3&year=2026",
            headers=self.headers
        )
        assert response2.status_code == 200
        period_balance = response2.json()["closing_balance"]
        
        # Both should match since all transactions are in March 2026
        assert semua_balance == period_balance, f"Mismatch: Semua={semua_balance}, Period={period_balance}"
        print(f"✅ Both modes consistent: Semua Periode={semua_balance}, Period March 2026={period_balance}")
    
    # =================================================================
    # TEST: Empty period returns 0
    # =================================================================
    def test_10_empty_period_returns_zero(self):
        """Verify period with no transactions returns 0 balance"""
        response = requests.get(
            f"{BASE_URL}/api/inventory/stock-card?item_id={self.item_001002_id}&month=1&year=2026",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # January 2026 should have no transactions, so closing_balance = 0
        assert data["opening_balance"] == 0
        assert data["closing_balance"] == 0
        assert data["total_masuk"] == 0
        assert data["total_keluar"] == 0
        
        print(f"✅ Empty period (Jan 2026) correctly shows 0 balance")
    
    # =================================================================
    # TEST: Verify Daftar Item consistency
    # =================================================================
    def test_11_daftar_item_stock_matches(self):
        """Verify Daftar Item shows same stock as Kartu Stok"""
        response = requests.get(
            f"{BASE_URL}/api/master/items?search=001002",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        items = data.get("items", [])
        item_001002 = next((i for i in items if i.get("code") == "001002"), None)
        
        if item_001002:
            stock = item_001002.get("stock", item_001002.get("stock_total", 0))
            assert stock == 18, f"Daftar Item stock mismatch: expected 18, got {stock}"
            print(f"✅ Daftar Item stock={stock} matches Kartu Stok")
        else:
            pytest.skip("Item 001002 not found in Daftar Item response")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
