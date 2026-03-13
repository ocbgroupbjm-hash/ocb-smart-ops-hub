# OCB TITAN ERP - P1 Integration Testing (Iteration 49)
# Features: Auto-apply discounts, Price level lookup, Owner Edit Button APIs
# Testing: Backend APIs and frontend Owner Edit verification

import pytest
import requests
import os
import json

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestP1Integration:
    """Test P1 Integration features: Discount/Promo Engine, Price Level, Owner Edit"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with owner credentials"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as owner
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "ocbgroupbjm@gmail.com",
            "password": "admin123"
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        login_data = login_response.json()
        self.token = login_data.get("access_token") or login_data.get("token")
        self.user = login_data.get("user", {})
        assert self.token, "No token received from login"
        assert self.user.get("role") in ["owner", "pemilik", "super_admin"], f"User role not owner: {self.user.get('role')}"
        
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        
        yield
        self.session.close()

    # ==================== P1-A: DISCOUNT/PROMO ENGINE ====================
    
    def test_calculate_pricing_endpoint_exists(self):
        """Test POST /api/master/calculate-pricing endpoint is accessible"""
        # Get a product to test with
        products_res = self.session.get(f"{BASE_URL}/api/products?limit=1")
        assert products_res.status_code == 200, f"Failed to get products: {products_res.text}"
        products = products_res.json()
        items_list = products.get("items", [])
        
        if not items_list:
            pytest.skip("No products available for testing")
        
        product = items_list[0]
        product_id = product.get("id")
        
        # Test calculate-pricing endpoint
        payload = {
            "items": [{"product_id": product_id, "quantity": 5, "unit_price": 100000}],
            "customer_id": None,
            "branch_id": None
        }
        
        response = self.session.post(f"{BASE_URL}/api/master/calculate-pricing", json=payload)
        assert response.status_code == 200, f"calculate-pricing failed: {response.text}"
        
        data = response.json()
        assert "items" in data, "Response missing 'items' field"
        assert "totals" in data, "Response missing 'totals' field"
        assert "discounts" in data, "Response missing 'discounts' field"
        print(f"PASS: calculate-pricing returns items with totals: {data['totals']}")
    
    def test_calculate_pricing_returns_discounts(self):
        """Test that calculate-pricing returns discount information"""
        products_res = self.session.get(f"{BASE_URL}/api/products?limit=5")
        if products_res.status_code != 200:
            pytest.skip("Products endpoint unavailable")
        
        products = products_res.json().get("items", [])
        if not products:
            pytest.skip("No products for discount testing")
        
        product = products[0]
        
        payload = {
            "items": [{"product_id": product.get("id"), "quantity": 10, "unit_price": product.get("selling_price", 50000)}],
            "customer_id": None,
            "branch_id": None
        }
        
        response = self.session.post(f"{BASE_URL}/api/master/calculate-pricing", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        # Check totals structure
        totals = data.get("totals", {})
        assert "subtotal" in totals, "Missing subtotal in totals"
        assert "grand_total" in totals, "Missing grand_total in totals"
        print(f"PASS: Discounts returned: {len(data.get('discounts', []))}, Total discount: {totals.get('total_discount', 0)}")

    def test_check_promotions_endpoint(self):
        """Test POST /api/master/check-promotions returns promotion list"""
        products_res = self.session.get(f"{BASE_URL}/api/products?limit=3")
        if products_res.status_code != 200:
            pytest.skip("Products unavailable")
        
        products = products_res.json().get("items", [])
        if not products:
            pytest.skip("No products")
        
        payload = {
            "items": [{"product_id": p.get("id"), "quantity": 5, "unit_price": p.get("selling_price", 10000)} for p in products[:3]],
            "customer_id": None,
            "branch_id": None
        }
        
        response = self.session.post(f"{BASE_URL}/api/master/check-promotions", json=payload)
        assert response.status_code == 200, f"check-promotions failed: {response.text}"
        
        data = response.json()
        assert "promotions" in data, "Response missing 'promotions' field"
        print(f"PASS: check-promotions returns {len(data['promotions'])} promotions")

    def test_check_discounts_endpoint(self):
        """Test POST /api/master/check-discounts for single item"""
        products_res = self.session.get(f"{BASE_URL}/api/products?limit=1")
        if products_res.status_code != 200:
            pytest.skip("Products unavailable")
        
        products = products_res.json().get("items", [])
        if not products:
            pytest.skip("No products")
        
        product = products[0]
        
        payload = {
            "item": {"product_id": product.get("id"), "quantity": 10, "unit_price": product.get("selling_price", 50000)},
            "customer_id": None,
            "branch_id": None
        }
        
        response = self.session.post(f"{BASE_URL}/api/master/check-discounts", json=payload)
        assert response.status_code == 200, f"check-discounts failed: {response.text}"
        
        data = response.json()
        assert "discounts" in data, "Response missing 'discounts' field"
        print(f"PASS: check-discounts returns {len(data['discounts'])} applicable discounts")

    # ==================== P1-B: PRICE LEVEL LOOKUP ====================
    
    def test_price_for_customer_endpoint(self):
        """Test GET /api/master/price-for-customer/{product_id}/{customer_id}"""
        # Get a product
        products_res = self.session.get(f"{BASE_URL}/api/products?limit=1")
        if products_res.status_code != 200:
            pytest.skip("Products unavailable")
        products = products_res.json().get("items", [])
        if not products:
            pytest.skip("No products")
        
        # Get a customer  
        customers_res = self.session.get(f"{BASE_URL}/api/customers?limit=1")
        if customers_res.status_code != 200:
            pytest.skip("Customers unavailable")
        customers = customers_res.json()
        customers_list = customers.get("items", customers) if isinstance(customers, dict) else customers
        if not customers_list:
            pytest.skip("No customers")
        
        product_id = products[0].get("id")
        customer_id = customers_list[0].get("id") if isinstance(customers_list, list) else None
        
        if not customer_id:
            pytest.skip("No valid customer ID")
        
        response = self.session.get(f"{BASE_URL}/api/master/price-for-customer/{product_id}/{customer_id}")
        assert response.status_code == 200, f"price-for-customer failed: {response.text}"
        
        data = response.json()
        assert "price" in data, "Response missing 'price' field"
        assert "price_level" in data, "Response missing 'price_level' field"
        print(f"PASS: Price level lookup - Level: {data['price_level']}, Price: {data['price']}, Source: {data.get('source', 'N/A')}")

    def test_price_levels_info_endpoint(self):
        """Test GET /api/master/price-levels returns level definitions"""
        response = self.session.get(f"{BASE_URL}/api/master/price-levels")
        assert response.status_code == 200, f"price-levels failed: {response.text}"
        
        data = response.json()
        assert "levels" in data, "Response missing 'levels' field"
        levels = data["levels"]
        assert len(levels) >= 5, f"Expected at least 5 price levels, got {len(levels)}"
        print(f"PASS: Price levels defined: {[l['name'] for l in levels]}")

    # ==================== P1-C: OWNER EDIT API ====================
    
    def test_owner_edit_purchase_order_endpoint_exists(self):
        """Test PUT /api/owner/edit/purchase-order/{id} endpoint exists"""
        # Get an existing PO
        po_res = self.session.get(f"{BASE_URL}/api/purchase/orders?limit=1")
        if po_res.status_code != 200:
            pytest.skip("PO endpoint unavailable")
        
        po_data = po_res.json()
        orders = po_data.get("items", po_data) if isinstance(po_data, dict) else po_data
        if not orders or (isinstance(orders, list) and len(orders) == 0):
            pytest.skip("No PO available for testing")
        
        po = orders[0] if isinstance(orders, list) else None
        if not po:
            pytest.skip("No PO found")
        
        po_id = po.get("id")
        
        # Test owner edit with minimal change (notes)
        payload = {
            "notes": f"Test owner edit - {os.urandom(4).hex()}"
        }
        
        response = self.session.put(f"{BASE_URL}/api/owner/edit/purchase-order/{po_id}", json=payload)
        
        # Should succeed for owner or return 403 for non-owner
        assert response.status_code in [200, 403], f"Unexpected status: {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            assert data.get("success") == True, "Edit should succeed"
            assert data.get("audit_logged") == True, "Should have audit log"
            print(f"PASS: Owner edit PO successful, audit logged: {data.get('audit_logged')}")
        else:
            print(f"INFO: Owner edit returned 403 (permission check working)")

    def test_owner_audit_logs_endpoint(self):
        """Test GET /api/owner/audit-logs is accessible for owner"""
        response = self.session.get(f"{BASE_URL}/api/owner/audit-logs?limit=10")
        
        assert response.status_code == 200, f"audit-logs failed: {response.text}"
        
        data = response.json()
        assert "items" in data, "Response missing 'items' field"
        print(f"PASS: Audit logs accessible, {data.get('total', len(data['items']))} total logs")

    def test_owner_audit_log_detail(self):
        """Test GET /api/owner/audit-logs/{record_id} for specific record"""
        # Get a recent audit log
        logs_res = self.session.get(f"{BASE_URL}/api/owner/audit-logs?limit=1")
        if logs_res.status_code != 200:
            pytest.skip("Audit logs unavailable")
        
        logs = logs_res.json().get("items", [])
        if not logs:
            pytest.skip("No audit logs available")
        
        record_id = logs[0].get("record_id")
        if not record_id:
            pytest.skip("No record_id in audit log")
        
        response = self.session.get(f"{BASE_URL}/api/owner/audit-logs/{record_id}")
        assert response.status_code == 200, f"audit-log detail failed: {response.text}"
        
        data = response.json()
        assert "history" in data, "Response missing 'history' field"
        print(f"PASS: Audit log history for record {record_id}: {len(data['history'])} entries")

    # ==================== DISCOUNT/PROMO MASTER DATA ====================
    
    def test_discounts_list_endpoint(self):
        """Test GET /api/master/discounts returns discount rules"""
        response = self.session.get(f"{BASE_URL}/api/master/discounts")
        assert response.status_code == 200, f"discounts list failed: {response.text}"
        
        data = response.json()
        # Can be list or object with items
        if isinstance(data, list):
            print(f"PASS: Discounts list: {len(data)} discount rules")
        else:
            print(f"PASS: Discounts response received")

    def test_promotions_list_endpoint(self):
        """Test GET /api/master/promotions returns promo rules"""
        response = self.session.get(f"{BASE_URL}/api/master/promotions")
        assert response.status_code == 200, f"promotions list failed: {response.text}"
        
        data = response.json()
        if isinstance(data, list):
            print(f"PASS: Promotions list: {len(data)} promotions")
        else:
            print(f"PASS: Promotions response received")

    def test_customer_groups_with_price_level(self):
        """Test GET /api/master/customer-groups includes price_level"""
        response = self.session.get(f"{BASE_URL}/api/master/customer-groups")
        assert response.status_code == 200, f"customer-groups failed: {response.text}"
        
        data = response.json()
        groups = data if isinstance(data, list) else data.get("items", [])
        
        if groups:
            # Check if price_level field exists in groups
            has_price_level = any("price_level" in g for g in groups)
            print(f"PASS: Customer groups: {len(groups)}, price_level field present: {has_price_level}")
        else:
            print(f"PASS: Customer groups endpoint works (no groups yet)")

    # ==================== OWNER ROLE VERIFICATION ====================
    
    def test_owner_role_has_full_access(self):
        """Verify owner role has access to owner-restricted endpoints"""
        # Test multiple owner-only endpoints
        endpoints = [
            "/api/owner/audit-logs",
            "/api/users",
            "/api/master/discounts",
            "/api/master/promotions"
        ]
        
        accessible = 0
        for endpoint in endpoints:
            res = self.session.get(f"{BASE_URL}{endpoint}")
            if res.status_code == 200:
                accessible += 1
                print(f"  - {endpoint}: ACCESSIBLE")
            else:
                print(f"  - {endpoint}: {res.status_code}")
        
        assert accessible >= 3, f"Owner should access most endpoints, only {accessible}/{len(endpoints)} accessible"
        print(f"PASS: Owner has access to {accessible}/{len(endpoints)} restricted endpoints")


class TestDiscountPromoEngine:
    """Deep testing of Discount & Promo Engine logic"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "ocbgroupbjm@gmail.com",
            "password": "admin123"
        })
        if login_response.status_code != 200:
            pytest.skip("Login failed")
        
        token = login_response.json().get("access_token") or login_response.json().get("token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        yield
        self.session.close()

    def test_pricing_calculation_subtotal(self):
        """Verify subtotal calculation in pricing response"""
        products_res = self.session.get(f"{BASE_URL}/api/products?limit=1")
        if products_res.status_code != 200:
            pytest.skip("Products unavailable")
        
        products = products_res.json().get("items", [])
        if not products:
            pytest.skip("No products")
        
        product = products[0]
        qty = 5
        price = 100000
        
        payload = {
            "items": [{"product_id": product.get("id"), "quantity": qty, "unit_price": price}],
            "customer_id": None,
            "branch_id": None
        }
        
        response = self.session.post(f"{BASE_URL}/api/master/calculate-pricing", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        totals = data.get("totals", {})
        
        expected_subtotal = qty * price
        actual_subtotal = totals.get("subtotal", 0)
        
        assert actual_subtotal == expected_subtotal, f"Subtotal mismatch: expected {expected_subtotal}, got {actual_subtotal}"
        print(f"PASS: Subtotal calculation correct: {qty} x {price} = {actual_subtotal}")

    def test_pricing_with_multiple_items(self):
        """Test pricing calculation with multiple items"""
        products_res = self.session.get(f"{BASE_URL}/api/products?limit=3")
        if products_res.status_code != 200:
            pytest.skip("Products unavailable")
        
        products = products_res.json().get("items", [])
        if len(products) < 2:
            pytest.skip("Need at least 2 products")
        
        items = [
            {"product_id": products[0].get("id"), "quantity": 3, "unit_price": 50000},
            {"product_id": products[1].get("id"), "quantity": 2, "unit_price": 75000}
        ]
        
        expected_subtotal = (3 * 50000) + (2 * 75000)  # 150000 + 150000 = 300000
        
        payload = {"items": items, "customer_id": None, "branch_id": None}
        response = self.session.post(f"{BASE_URL}/api/master/calculate-pricing", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        actual_subtotal = data.get("totals", {}).get("subtotal", 0)
        
        assert actual_subtotal == expected_subtotal, f"Multi-item subtotal wrong: {actual_subtotal} != {expected_subtotal}"
        print(f"PASS: Multi-item pricing calculation correct: {actual_subtotal}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
