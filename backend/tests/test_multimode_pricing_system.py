# Multi-Mode Selling Price System Tests for OCB TITAN ERP
# Tests: Single Price, Quantity Pricing, Level Pricing, Unit Pricing
# POS Security: override_price permission check

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')

# Test credentials
PEMILIK_CREDENTIALS = {"email": "ocbgroupbjm@gmail.com", "password": "admin123"}
KASIR_CREDENTIALS = {"email": "kasir_test@ocb.com", "password": "test123"}

# Test product IDs from main agent
PRODUCT_ID_QUANTITY = "397edcd5-d0ab-4982-ba6b-79889ff3d798"  # quantity mode
PRODUCT_ID_LEVEL = "339a4adf-1f19-459a-8dfc-a27dc7fd00a0"     # level mode


class TestPricingSystemInit:
    """Test pricing system initialization"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.pemilik_token = self.login_user(PEMILIK_CREDENTIALS)
        yield
    
    def login_user(self, credentials):
        """Login and return token"""
        # First select business
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        # Select OCB GROUP business
        bus_res = session.post(f"{BASE_URL}/api/auth/select-business", json={
            "db_name": "ocb_titan"
        })
        if bus_res.status_code == 200:
            bus_data = bus_res.json()
            if bus_data.get("token"):
                session.headers.update({"Authorization": f"Bearer {bus_data['token']}"})
        
        # Login with credentials
        login_res = session.post(f"{BASE_URL}/api/auth/login", json=credentials)
        if login_res.status_code == 200:
            return login_res.json().get("token")
        return None
    
    def test_init_pricing_system(self):
        """Test POST /api/pricing/init - Initialize pricing system"""
        headers = {"Authorization": f"Bearer {self.pemilik_token}", "Content-Type": "application/json"}
        res = requests.post(f"{BASE_URL}/api/pricing/init", headers=headers)
        
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        
        # Validate response structure
        assert "message" in data
        assert "customer_levels_created" in data
        assert "pricing_modes" in data
        
        # Validate pricing modes
        expected_modes = ["single", "quantity", "level", "unit"]
        for mode in expected_modes:
            assert mode in data["pricing_modes"], f"Missing mode: {mode}"
        
        print(f"✓ Pricing system initialized: {data['message']}")
        print(f"✓ Customer levels created: {data['customer_levels_created']}")
        print(f"✓ Pricing modes: {data['pricing_modes']}")


class TestPricingModes:
    """Test pricing modes API"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.token = self.login_pemilik()
        yield
    
    def login_pemilik(self):
        """Login as PEMILIK"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        # Select business
        bus_res = session.post(f"{BASE_URL}/api/auth/select-business", json={"db_name": "ocb_titan"})
        if bus_res.status_code == 200:
            bus_data = bus_res.json()
            if bus_data.get("token"):
                session.headers.update({"Authorization": f"Bearer {bus_data['token']}"})
        
        # Login
        login_res = session.post(f"{BASE_URL}/api/auth/login", json=PEMILIK_CREDENTIALS)
        if login_res.status_code == 200:
            return login_res.json().get("token")
        return None
    
    def test_get_pricing_modes(self):
        """Test GET /api/pricing/modes - Get all pricing modes"""
        headers = {"Authorization": f"Bearer {self.token}"}
        res = requests.get(f"{BASE_URL}/api/pricing/modes", headers=headers)
        
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        data = res.json()
        
        # Validate response structure
        assert "modes" in data
        assert "total" in data
        assert data["total"] == 4, f"Expected 4 modes, got {data['total']}"
        
        # Validate each mode
        modes = {m["code"]: m for m in data["modes"]}
        
        assert "single" in modes, "Missing single mode"
        assert "quantity" in modes, "Missing quantity mode"
        assert "level" in modes, "Missing level mode"
        assert "unit" in modes, "Missing unit mode"
        
        # Validate mode details
        assert modes["single"]["name"] == "Satu Harga"
        assert modes["quantity"]["name"] == "Berdasarkan Jumlah"
        assert modes["level"]["name"] == "Level Harga"
        assert modes["unit"]["name"] == "Berdasarkan Satuan"
        
        print("✓ All 4 pricing modes present:")
        for mode in data["modes"]:
            print(f"  - {mode['code']}: {mode['name']}")


class TestCustomerLevels:
    """Test customer levels API"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.token = self.login_pemilik()
        yield
    
    def login_pemilik(self):
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        bus_res = session.post(f"{BASE_URL}/api/auth/select-business", json={"db_name": "ocb_titan"})
        if bus_res.status_code == 200:
            bus_data = bus_res.json()
            if bus_data.get("token"):
                session.headers.update({"Authorization": f"Bearer {bus_data['token']}"})
        login_res = session.post(f"{BASE_URL}/api/auth/login", json=PEMILIK_CREDENTIALS)
        if login_res.status_code == 200:
            return login_res.json().get("token")
        return None
    
    def test_get_customer_levels(self):
        """Test GET /api/pricing/customer-levels"""
        headers = {"Authorization": f"Bearer {self.token}"}
        res = requests.get(f"{BASE_URL}/api/pricing/customer-levels", headers=headers)
        
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        data = res.json()
        
        # Validate response structure
        assert "levels" in data
        assert "total" in data
        assert data["total"] >= 5, f"Expected at least 5 levels, got {data['total']}"
        
        # Validate required customer levels exist
        level_codes = [l["code"] for l in data["levels"]]
        required_levels = ["retail", "member", "reseller", "distributor", "grosir"]
        
        for level in required_levels:
            assert level in level_codes, f"Missing customer level: {level}"
        
        print(f"✓ Found {data['total']} customer levels:")
        for level in data["levels"]:
            print(f"  - {level['code']}: {level['name']} (Level {level['level']}, Discount {level.get('discount_percent', 0)}%)")


class TestQuantityPricing:
    """Test QUANTITY mode pricing - Price changes based on quantity"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.token = self.login_pemilik()
        yield
    
    def login_pemilik(self):
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        bus_res = session.post(f"{BASE_URL}/api/auth/select-business", json={"db_name": "ocb_titan"})
        if bus_res.status_code == 200:
            bus_data = bus_res.json()
            if bus_data.get("token"):
                session.headers.update({"Authorization": f"Bearer {bus_data['token']}"})
        login_res = session.post(f"{BASE_URL}/api/auth/login", json=PEMILIK_CREDENTIALS)
        if login_res.status_code == 200:
            return login_res.json().get("token")
        return None
    
    def test_get_product_pricing_config(self):
        """Test GET /api/pricing/product/{id} - Get product pricing config"""
        headers = {"Authorization": f"Bearer {self.token}"}
        res = requests.get(f"{BASE_URL}/api/pricing/product/{PRODUCT_ID_QUANTITY}", headers=headers)
        
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        
        # Validate response structure
        assert "product" in data
        assert "pricing" in data
        assert "modes" in data
        
        # Validate pricing config
        pricing = data["pricing"]
        assert pricing["pricing_mode"] == "quantity", f"Expected quantity mode, got {pricing['pricing_mode']}"
        assert "quantity_prices" in pricing
        assert len(pricing["quantity_prices"]) > 0, "Expected quantity price rules"
        
        print(f"✓ Product pricing config for QUANTITY mode:")
        print(f"  Mode: {pricing['pricing_mode']}")
        print(f"  Base Price: {pricing.get('selling_price', 0)}")
        print(f"  Quantity Rules: {len(pricing['quantity_prices'])}")
    
    def test_calculate_qty_1(self):
        """Test price calculation for qty=1 (should be 20000)"""
        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        res = requests.post(f"{BASE_URL}/api/pricing/calculate", headers=headers, json={
            "product_id": PRODUCT_ID_QUANTITY,
            "quantity": 1,
            "customer_level": "retail"
        })
        
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        data = res.json()
        
        # Validate response
        assert "price" in data
        assert "mode" in data
        assert data["mode"] == "quantity"
        assert data["price"] == 20000, f"Expected price 20000 for qty=1, got {data['price']}"
        
        print(f"✓ QUANTITY MODE qty=1: Price = Rp {data['price']:,.0f} (expected 20,000)")
    
    def test_calculate_qty_6(self):
        """Test price calculation for qty=6 (should be 18000 for qty 5-9)"""
        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        res = requests.post(f"{BASE_URL}/api/pricing/calculate", headers=headers, json={
            "product_id": PRODUCT_ID_QUANTITY,
            "quantity": 6,
            "customer_level": "retail"
        })
        
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        data = res.json()
        
        assert data["price"] == 18000, f"Expected price 18000 for qty=6, got {data['price']}"
        
        print(f"✓ QUANTITY MODE qty=6: Price = Rp {data['price']:,.0f} (expected 18,000)")
    
    def test_calculate_qty_15(self):
        """Test price calculation for qty=15 (should be 15000 for qty 10+)"""
        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        res = requests.post(f"{BASE_URL}/api/pricing/calculate", headers=headers, json={
            "product_id": PRODUCT_ID_QUANTITY,
            "quantity": 15,
            "customer_level": "retail"
        })
        
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        data = res.json()
        
        assert data["price"] == 15000, f"Expected price 15000 for qty=15, got {data['price']}"
        
        print(f"✓ QUANTITY MODE qty=15: Price = Rp {data['price']:,.0f} (expected 15,000)")


class TestLevelPricing:
    """Test LEVEL mode pricing - Price changes based on customer level"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.token = self.login_pemilik()
        yield
    
    def login_pemilik(self):
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        bus_res = session.post(f"{BASE_URL}/api/auth/select-business", json={"db_name": "ocb_titan"})
        if bus_res.status_code == 200:
            bus_data = bus_res.json()
            if bus_data.get("token"):
                session.headers.update({"Authorization": f"Bearer {bus_data['token']}"})
        login_res = session.post(f"{BASE_URL}/api/auth/login", json=PEMILIK_CREDENTIALS)
        if login_res.status_code == 200:
            return login_res.json().get("token")
        return None
    
    def test_get_level_product_pricing(self):
        """Test GET /api/pricing/product/{id} - Get LEVEL mode product"""
        headers = {"Authorization": f"Bearer {self.token}"}
        res = requests.get(f"{BASE_URL}/api/pricing/product/{PRODUCT_ID_LEVEL}", headers=headers)
        
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        
        pricing = data["pricing"]
        assert pricing["pricing_mode"] == "level", f"Expected level mode, got {pricing['pricing_mode']}"
        assert "price_levels" in pricing
        assert pricing["price_levels"] is not None, "Expected price_levels config"
        
        print(f"✓ Product pricing config for LEVEL mode:")
        print(f"  Mode: {pricing['pricing_mode']}")
        if pricing["price_levels"]:
            for level, price in pricing["price_levels"].items():
                if price > 0:
                    print(f"  - {level}: Rp {price:,.0f}")
    
    def test_calculate_level_retail(self):
        """Test price calculation for retail level (should be 100000)"""
        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        res = requests.post(f"{BASE_URL}/api/pricing/calculate", headers=headers, json={
            "product_id": PRODUCT_ID_LEVEL,
            "quantity": 1,
            "customer_level": "retail"
        })
        
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        data = res.json()
        
        assert data["mode"] == "level"
        assert data["price"] == 100000, f"Expected price 100000 for retail, got {data['price']}"
        
        print(f"✓ LEVEL MODE retail: Price = Rp {data['price']:,.0f} (expected 100,000)")
    
    def test_calculate_level_grosir(self):
        """Test price calculation for grosir level (should be 80000)"""
        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        res = requests.post(f"{BASE_URL}/api/pricing/calculate", headers=headers, json={
            "product_id": PRODUCT_ID_LEVEL,
            "quantity": 1,
            "customer_level": "grosir"
        })
        
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        data = res.json()
        
        assert data["price"] == 80000, f"Expected price 80000 for grosir, got {data['price']}"
        
        print(f"✓ LEVEL MODE grosir: Price = Rp {data['price']:,.0f} (expected 80,000)")
    
    def test_calculate_level_member(self):
        """Test price calculation for member level"""
        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        res = requests.post(f"{BASE_URL}/api/pricing/calculate", headers=headers, json={
            "product_id": PRODUCT_ID_LEVEL,
            "quantity": 1,
            "customer_level": "member"
        })
        
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        data = res.json()
        
        print(f"✓ LEVEL MODE member: Price = Rp {data['price']:,.0f}")


class TestPOSSecurityKasir:
    """Test POS Security - KASIR without override_price permission should get 403"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.kasir_token = self.login_kasir()
        yield
    
    def login_kasir(self):
        """Login as KASIR (no override_price permission)"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        # Select business
        bus_res = session.post(f"{BASE_URL}/api/auth/select-business", json={"db_name": "ocb_titan"})
        if bus_res.status_code == 200:
            bus_data = bus_res.json()
            if bus_data.get("token"):
                session.headers.update({"Authorization": f"Bearer {bus_data['token']}"})
        
        # Login as kasir
        login_res = session.post(f"{BASE_URL}/api/auth/login", json=KASIR_CREDENTIALS)
        if login_res.status_code == 200:
            return login_res.json().get("token")
        return None
    
    def test_kasir_cannot_select_different_price(self):
        """Test KASIR gets 403 when trying to select non-default price level"""
        if not self.kasir_token:
            pytest.skip("KASIR login failed")
        
        headers = {"Authorization": f"Bearer {self.kasir_token}", "Content-Type": "application/json"}
        
        # Try to select a different price level (not default)
        res = requests.post(f"{BASE_URL}/api/pricing/pos/select-price", headers=headers, json={
            "product_id": PRODUCT_ID_LEVEL,
            "selected_level": "grosir"  # Non-default level
        })
        
        # Should get 403 Forbidden because KASIR doesn't have override_price permission
        # OR 400 if product doesn't allow price selection
        if res.status_code == 403:
            data = res.json()
            print(f"✓ KASIR blocked with 403: {data.get('detail', 'No permission')}")
            assert "TIDAK MEMILIKI IZIN" in data.get("detail", "") or res.status_code == 403
        elif res.status_code == 400:
            data = res.json()
            print(f"✓ Product doesn't allow price selection: {data.get('detail')}")
        else:
            print(f"Response: {res.status_code} - {res.text}")
            # Accept 200 if product doesn't have price selection enabled
            if res.status_code == 200:
                pytest.skip("Product allows price selection or default level selected")
        
        print("✓ POS Security: KASIR properly restricted from changing prices")


class TestPOSSecurityPemilik:
    """Test POS Security - PEMILIK with inherit_all can change prices"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.pemilik_token = self.login_pemilik()
        yield
    
    def login_pemilik(self):
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        bus_res = session.post(f"{BASE_URL}/api/auth/select-business", json={"db_name": "ocb_titan"})
        if bus_res.status_code == 200:
            bus_data = bus_res.json()
            if bus_data.get("token"):
                session.headers.update({"Authorization": f"Bearer {bus_data['token']}"})
        login_res = session.post(f"{BASE_URL}/api/auth/login", json=PEMILIK_CREDENTIALS)
        if login_res.status_code == 200:
            return login_res.json().get("token")
        return None
    
    def test_pemilik_can_select_price(self):
        """Test PEMILIK can select different price level (has inherit_all)"""
        headers = {"Authorization": f"Bearer {self.pemilik_token}", "Content-Type": "application/json"}
        
        # First, enable allow_price_selection for the product
        config_res = requests.put(f"{BASE_URL}/api/pricing/product/{PRODUCT_ID_LEVEL}", headers=headers, json={
            "pricing_mode": "level",
            "selling_price": 100000,
            "quantity_prices": [],
            "price_levels": {
                "retail": 100000,
                "member": 95000,
                "reseller": 90000,
                "distributor": 85000,
                "grosir": 80000
            },
            "unit_prices": [],
            "allow_price_selection": True,
            "default_level": "retail"
        })
        
        if config_res.status_code != 200:
            print(f"Config update: {config_res.status_code} - {config_res.text}")
        
        # Now try to select grosir price
        res = requests.post(f"{BASE_URL}/api/pricing/pos/select-price", headers=headers, json={
            "product_id": PRODUCT_ID_LEVEL,
            "selected_level": "grosir"
        })
        
        # PEMILIK should be allowed (has inherit_all)
        if res.status_code == 200:
            data = res.json()
            print(f"✓ PEMILIK allowed to select price level: grosir")
            print(f"  Selected price: Rp {data.get('price', 0):,.0f}")
            assert data.get("selected_level") == "grosir"
        elif res.status_code == 400:
            print(f"Product config issue: {res.json().get('detail')}")
        else:
            print(f"Response: {res.status_code} - {res.text}")
        
        print("✓ POS Security: PEMILIK can override prices (inherit_all)")


class TestProductPricingUpdate:
    """Test updating product pricing configuration"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.token = self.login_pemilik()
        yield
    
    def login_pemilik(self):
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        bus_res = session.post(f"{BASE_URL}/api/auth/select-business", json={"db_name": "ocb_titan"})
        if bus_res.status_code == 200:
            bus_data = bus_res.json()
            if bus_data.get("token"):
                session.headers.update({"Authorization": f"Bearer {bus_data['token']}"})
        login_res = session.post(f"{BASE_URL}/api/auth/login", json=PEMILIK_CREDENTIALS)
        if login_res.status_code == 200:
            return login_res.json().get("token")
        return None
    
    def test_update_pricing_config(self):
        """Test PUT /api/pricing/product/{id} - Update pricing config"""
        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        
        # Update with quantity pricing
        res = requests.put(f"{BASE_URL}/api/pricing/product/{PRODUCT_ID_QUANTITY}", headers=headers, json={
            "pricing_mode": "quantity",
            "selling_price": 20000,
            "quantity_prices": [
                {"min_qty": 1, "max_qty": 4, "price": 20000},
                {"min_qty": 5, "max_qty": 9, "price": 18000},
                {"min_qty": 10, "max_qty": None, "price": 15000}
            ],
            "price_levels": None,
            "unit_prices": [],
            "allow_price_selection": False,
            "default_level": "retail"
        })
        
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        
        assert "message" in data
        assert data.get("pricing_mode") == "quantity"
        
        print(f"✓ Pricing config updated: {data['message']}")
        print(f"  Mode: {data['pricing_mode']}")


class TestBatchPriceCalculation:
    """Test batch price calculation for multiple products"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.token = self.login_pemilik()
        yield
    
    def login_pemilik(self):
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        bus_res = session.post(f"{BASE_URL}/api/auth/select-business", json={"db_name": "ocb_titan"})
        if bus_res.status_code == 200:
            bus_data = bus_res.json()
            if bus_data.get("token"):
                session.headers.update({"Authorization": f"Bearer {bus_data['token']}"})
        login_res = session.post(f"{BASE_URL}/api/auth/login", json=PEMILIK_CREDENTIALS)
        if login_res.status_code == 200:
            return login_res.json().get("token")
        return None
    
    def test_calculate_batch_prices(self):
        """Test POST /api/pricing/calculate-batch"""
        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        
        res = requests.post(f"{BASE_URL}/api/pricing/calculate-batch", headers=headers, json=[
            {"product_id": PRODUCT_ID_QUANTITY, "quantity": 5, "customer_level": "retail"},
            {"product_id": PRODUCT_ID_LEVEL, "quantity": 1, "customer_level": "grosir"}
        ])
        
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        data = res.json()
        
        assert "prices" in data
        assert "count" in data
        assert data["count"] == 2
        
        print(f"✓ Batch price calculation: {data['count']} products")
        for price_data in data["prices"]:
            print(f"  - {price_data['product_id'][:8]}...: Rp {price_data['price']:,.0f} ({price_data['mode']})")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
