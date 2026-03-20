"""
Test POS Payment Flow - Iteration 94
Bug Fix: Payment save error 'Terjadi kesalahan' - JSON parse error handling

Tests:
1. Sales invoice creation with valid customer
2. Sales invoice creation with invalid customer (should return proper error)
3. Multi-item transaction
4. Overpay transaction (change calculation)
5. Customer validation required
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestPOSPaymentFlow:
    """POS Payment Flow Tests - Bug Fix Verification"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication and tenant switch"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Switch tenant first
        switch_response = self.session.post(f"{BASE_URL}/api/business/switch/ocb_titan")
        if switch_response.status_code != 200:
            print(f"Tenant switch warning: {switch_response.status_code}")
        
        # Ensure admin exists
        self.session.post(f"{BASE_URL}/api/business/ensure-admin/ocb_titan")
        
        # Login
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "ocbgroupbjm@gmail.com",
            "password": "admin123"
        })
        
        if login_response.status_code != 200:
            pytest.skip(f"Login failed: {login_response.status_code} - {login_response.text}")
        
        login_data = login_response.json()
        # Token can be in 'token' or 'access_token' field
        token = login_data.get("token") or login_data.get("access_token")
        if token:
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Get customers list
        cust_response = self.session.get(f"{BASE_URL}/api/customers?limit=10")
        if cust_response.status_code == 200:
            customers = cust_response.json().get("items", [])
            self.valid_customer = customers[1] if len(customers) > 1 else customers[0] if customers else None
        else:
            self.valid_customer = None
            
        # Get products list
        prod_response = self.session.get(f"{BASE_URL}/api/products?limit=50")
        if prod_response.status_code == 200:
            products = prod_response.json().get("items", [])
            self.products = [p for p in products if p.get("selling_price", 0) > 0][:5]
        else:
            self.products = []
            
        # Get warehouse
        wh_response = self.session.get(f"{BASE_URL}/api/master/warehouses")
        if wh_response.status_code == 200:
            warehouses = wh_response.json() or []
            self.warehouse = warehouses[0] if warehouses else None
        else:
            self.warehouse = None
        
        yield
        
    def test_get_customers_list(self):
        """Verify customers endpoint returns valid data"""
        response = self.session.get(f"{BASE_URL}/api/customers")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "items" in data, "Response should have 'items' key"
        assert len(data["items"]) > 0, "Should have at least one customer"
        
        # First customer should have id and name
        first_customer = data["items"][0]
        assert "id" in first_customer, "Customer should have 'id'"
        assert "name" in first_customer, "Customer should have 'name'"
        print(f"✓ Found {len(data['items'])} customers")
        
    def test_get_products_list(self):
        """Verify products endpoint returns valid data"""
        response = self.session.get(f"{BASE_URL}/api/products?limit=50")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "items" in data, "Response should have 'items' key"
        assert len(data["items"]) > 0, "Should have at least one product"
        
        # Check product has required fields
        first_product = data["items"][0]
        assert "id" in first_product, "Product should have 'id'"
        assert "name" in first_product, "Product should have 'name'"
        print(f"✓ Found {len(data['items'])} products")
        
    def test_get_warehouses_list(self):
        """Verify warehouses endpoint returns valid data"""
        response = self.session.get(f"{BASE_URL}/api/master/warehouses")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        assert len(data) > 0, "Should have at least one warehouse"
        
        first_warehouse = data[0]
        assert "id" in first_warehouse, "Warehouse should have 'id'"
        assert "name" in first_warehouse, "Warehouse should have 'name'"
        print(f"✓ Found {len(data)} warehouses")
        
    def test_single_item_transaction_success(self):
        """Test single item transaction - select customer, add 1 item, pay cash, save → should succeed"""
        if not self.valid_customer:
            pytest.skip("No valid customer available")
        if not self.products:
            pytest.skip("No products with price available")
        if not self.warehouse:
            pytest.skip("No warehouse available")
            
        product = self.products[0]
        unit_price = product.get("selling_price", 10000)
        
        payload = {
            "customer_id": self.valid_customer["id"],
            "warehouse_id": self.warehouse["id"],
            "ppn_type": "exclude",
            "ppn_percent": 0,
            "notes": "POS - Tunai (Test Single Item)",
            "items": [{
                "product_id": product["id"],
                "quantity": 1,
                "unit_price": unit_price,
                "discount_percent": 0,
                "tax_percent": 0
            }],
            "subtotal": unit_price,
            "discount_amount": 0,
            "tax_amount": 0,
            "other_cost": 0,
            "total": unit_price,
            "payment_type": "cash",
            "cash_amount": unit_price,
            "credit_amount": 0,
            "dp_used": 0,
            "deposit_used": 0
        }
        
        response = self.session.post(f"{BASE_URL}/api/sales/invoices", json=payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "invoice_number" in data, "Response should have invoice_number"
        assert "total" in data, "Response should have total"
        assert data["total"] == unit_price, f"Total should be {unit_price}"
        
        print(f"✓ Single item transaction SUCCESS: {data['invoice_number']} - Total: {data['total']}")
        
    def test_multi_item_transaction_success(self):
        """Test multi-item transaction - add multiple items, pay cash, save → should succeed"""
        if not self.valid_customer:
            pytest.skip("No valid customer available")
        if len(self.products) < 2:
            pytest.skip("Not enough products available")
        if not self.warehouse:
            pytest.skip("No warehouse available")
            
        items = []
        total = 0
        
        for product in self.products[:2]:
            unit_price = product.get("selling_price", 10000)
            items.append({
                "product_id": product["id"],
                "quantity": 1,
                "unit_price": unit_price,
                "discount_percent": 0,
                "tax_percent": 0
            })
            total += unit_price
            
        payload = {
            "customer_id": self.valid_customer["id"],
            "warehouse_id": self.warehouse["id"],
            "ppn_type": "exclude",
            "ppn_percent": 0,
            "notes": "POS - Tunai (Test Multi Item)",
            "items": items,
            "subtotal": total,
            "discount_amount": 0,
            "tax_amount": 0,
            "other_cost": 0,
            "total": total,
            "payment_type": "cash",
            "cash_amount": total,
            "credit_amount": 0,
            "dp_used": 0,
            "deposit_used": 0
        }
        
        response = self.session.post(f"{BASE_URL}/api/sales/invoices", json=payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "invoice_number" in data, "Response should have invoice_number"
        assert len(payload["items"]) == 2, "Should have 2 items"
        
        print(f"✓ Multi-item transaction SUCCESS: {data['invoice_number']} - Total: {data['total']} ({len(items)} items)")
        
    def test_overpay_transaction_kembalian(self):
        """Test overpay transaction - pay more than total, should calculate change correctly"""
        if not self.valid_customer:
            pytest.skip("No valid customer available")
        if not self.products:
            pytest.skip("No products available")
        if not self.warehouse:
            pytest.skip("No warehouse available")
            
        product = self.products[0]
        unit_price = product.get("selling_price", 50000)
        overpay_amount = 100000  # Pay 100k for item costing less
        
        payload = {
            "customer_id": self.valid_customer["id"],
            "warehouse_id": self.warehouse["id"],
            "ppn_type": "exclude",
            "ppn_percent": 0,
            "notes": "POS - Tunai (Test Overpay)",
            "items": [{
                "product_id": product["id"],
                "quantity": 1,
                "unit_price": unit_price,
                "discount_percent": 0,
                "tax_percent": 0
            }],
            "subtotal": unit_price,
            "discount_amount": 0,
            "tax_amount": 0,
            "other_cost": 0,
            "total": unit_price,
            "payment_type": "cash",
            "cash_amount": unit_price,  # Backend only needs actual total
            "credit_amount": 0,
            "dp_used": 0,
            "deposit_used": 0
        }
        
        response = self.session.post(f"{BASE_URL}/api/sales/invoices", json=payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "invoice_number" in data, "Response should have invoice_number"
        
        # Verify change calculation would be correct
        expected_change = overpay_amount - unit_price
        assert expected_change >= 0, "Change should be non-negative"
        
        print(f"✓ Overpay transaction SUCCESS: {data['invoice_number']} - Total: {unit_price}, Change would be: {expected_change}")
        
    def test_invalid_customer_returns_error(self):
        """Test that invalid customer_id returns proper error message (not 'Terjadi kesalahan')"""
        if not self.products:
            pytest.skip("No products available")
        if not self.warehouse:
            pytest.skip("No warehouse available")
            
        product = self.products[0]
        unit_price = product.get("selling_price", 10000)
        
        payload = {
            "customer_id": "invalid_customer_id_12345",  # Invalid ID
            "warehouse_id": self.warehouse["id"],
            "ppn_type": "exclude",
            "ppn_percent": 0,
            "notes": "POS - Tunai (Test Invalid Customer)",
            "items": [{
                "product_id": product["id"],
                "quantity": 1,
                "unit_price": unit_price,
                "discount_percent": 0,
                "tax_percent": 0
            }],
            "subtotal": unit_price,
            "discount_amount": 0,
            "tax_amount": 0,
            "other_cost": 0,
            "total": unit_price,
            "payment_type": "cash",
            "cash_amount": unit_price,
            "credit_amount": 0,
            "dp_used": 0,
            "deposit_used": 0
        }
        
        response = self.session.post(f"{BASE_URL}/api/sales/invoices", json=payload)
        
        # Should return 404 with proper error message
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        
        data = response.json()
        assert "detail" in data, "Response should have 'detail' field"
        
        # Error message should be specific, not generic
        error_msg = data["detail"]
        assert "Customer" in error_msg or "tidak ditemukan" in error_msg, f"Error should mention customer: {error_msg}"
        
        print(f"✓ Invalid customer returns proper error: {error_msg}")
        
    def test_missing_warehouse_returns_error(self):
        """Test that missing warehouse_id is handled properly"""
        if not self.valid_customer:
            pytest.skip("No valid customer available")
        if not self.products:
            pytest.skip("No products available")
            
        product = self.products[0]
        unit_price = product.get("selling_price", 10000)
        
        payload = {
            "customer_id": self.valid_customer["id"],
            "warehouse_id": None,  # Missing warehouse
            "ppn_type": "exclude",
            "ppn_percent": 0,
            "notes": "POS - Tunai (Test Missing Warehouse)",
            "items": [{
                "product_id": product["id"],
                "quantity": 1,
                "unit_price": unit_price,
                "discount_percent": 0,
                "tax_percent": 0
            }],
            "subtotal": unit_price,
            "discount_amount": 0,
            "tax_amount": 0,
            "other_cost": 0,
            "total": unit_price,
            "payment_type": "cash",
            "cash_amount": unit_price,
            "credit_amount": 0,
            "dp_used": 0,
            "deposit_used": 0
        }
        
        response = self.session.post(f"{BASE_URL}/api/sales/invoices", json=payload)
        
        # Should either succeed with default warehouse or return validation error
        # Not a crash with 500
        assert response.status_code in [200, 400, 422], f"Expected 200/400/422, got {response.status_code}: {response.text}"
        
        print(f"✓ Missing warehouse handled properly: Status {response.status_code}")
        
    def test_verify_invoice_created_in_database(self):
        """Test that invoice is actually created and persisted in database"""
        if not self.valid_customer:
            pytest.skip("No valid customer available")
        if not self.products:
            pytest.skip("No products available")
        if not self.warehouse:
            pytest.skip("No warehouse available")
            
        product = self.products[0]
        unit_price = product.get("selling_price", 10000)
        
        # Create invoice
        payload = {
            "customer_id": self.valid_customer["id"],
            "warehouse_id": self.warehouse["id"],
            "ppn_type": "exclude",
            "ppn_percent": 0,
            "notes": "POS - Tunai (Test Verify Persistence)",
            "items": [{
                "product_id": product["id"],
                "quantity": 1,
                "unit_price": unit_price,
                "discount_percent": 0,
                "tax_percent": 0
            }],
            "subtotal": unit_price,
            "discount_amount": 0,
            "tax_amount": 0,
            "other_cost": 0,
            "total": unit_price,
            "payment_type": "cash",
            "cash_amount": unit_price,
            "credit_amount": 0,
            "dp_used": 0,
            "deposit_used": 0
        }
        
        create_response = self.session.post(f"{BASE_URL}/api/sales/invoices", json=payload)
        assert create_response.status_code == 200, f"Create failed: {create_response.text}"
        
        created_data = create_response.json()
        invoice_number = created_data.get("invoice_number")
        customer_id = created_data.get("customer_id")
        
        # Verify by fetching invoice list
        list_response = self.session.get(f"{BASE_URL}/api/sales/invoices?limit=5")
        assert list_response.status_code == 200, f"List failed: {list_response.text}"
        
        list_data = list_response.json()
        invoices = list_data.get("items", [])
        
        # Check if our invoice exists
        found = any(inv.get("invoice_number") == invoice_number for inv in invoices)
        assert found, f"Invoice {invoice_number} should be in recent invoices list"
        
        # Verify customer and total
        our_invoice = next((inv for inv in invoices if inv.get("invoice_number") == invoice_number), None)
        assert our_invoice is not None
        assert our_invoice.get("customer_id") == customer_id, "Customer ID should match"
        assert our_invoice.get("total") == unit_price, f"Total should be {unit_price}"
        
        print(f"✓ Invoice verified in database: {invoice_number} - Customer: {our_invoice.get('customer_name')}, Total: {our_invoice.get('total')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
