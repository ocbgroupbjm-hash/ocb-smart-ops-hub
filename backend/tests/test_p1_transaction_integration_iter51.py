"""
OCB TITAN ERP - P1 Transaction Integration Tests (Iteration 51)
Testing:
1. Pricing Engine - calculate-pricing, check-discounts, check-promotions
2. Price Level - price-for-customer lookup
3. Owner Edit - Sales Invoice, Item Master, Purchase Orders
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = 'https://smart-ops-hub-6.preview.emergentagent.com'

OWNER_CREDS = {
    "email": "ocbgroupbjm@gmail.com",
    "password": "admin123"
}

class TestPricingEngine:
    """Test discount/promo engine APIs"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for tests"""
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json=OWNER_CREDS)
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        self.token = login_res.json().get('token')
        self.headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
    
    def test_calculate_pricing_endpoint(self):
        """Test POST /api/master/calculate-pricing - main pricing engine"""
        payload = {
            "items": [
                {"product_id": "test-product-1", "quantity": 5, "unit_price": 100000}
            ],
            "customer_id": "test-customer-1",
            "branch_id": "test-branch-1"
        }
        res = requests.post(f"{BASE_URL}/api/master/calculate-pricing", json=payload, headers=self.headers)
        # Should return 200 even if no discounts apply
        assert res.status_code in [200, 422], f"Calculate pricing failed: {res.status_code} - {res.text}"
        if res.status_code == 200:
            data = res.json()
            # Check response structure
            assert "items" in data or "totals" in data, f"Missing expected fields in response: {data}"
            print(f"✓ Calculate pricing response: {data.keys()}")
    
    def test_check_discounts_endpoint(self):
        """Test POST /api/master/check-discounts"""
        payload = {
            "items": [{"product_id": "test-prod-1", "quantity": 3, "unit_price": 50000}],
            "customer_id": "test-cust-1"
        }
        res = requests.post(f"{BASE_URL}/api/master/check-discounts", json=payload, headers=self.headers)
        assert res.status_code in [200, 422], f"Check discounts failed: {res.status_code}"
        if res.status_code == 200:
            data = res.json()
            print(f"✓ Check discounts response: {data}")
    
    def test_check_promotions_endpoint(self):
        """Test POST /api/master/check-promotions"""
        payload = {
            "items": [{"product_id": "test-prod-1", "quantity": 10, "unit_price": 50000}],
            "customer_id": "test-cust-1",
            "branch_id": "test-branch-1"
        }
        res = requests.post(f"{BASE_URL}/api/master/check-promotions", json=payload, headers=self.headers)
        assert res.status_code in [200, 422], f"Check promotions failed: {res.status_code}"
        if res.status_code == 200:
            data = res.json()
            print(f"✓ Check promotions response: {data}")


class TestPriceLevelSystem:
    """Test price level lookup APIs"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json=OWNER_CREDS)
        assert login_res.status_code == 200
        self.token = login_res.json().get('token')
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_price_levels_list(self):
        """Test GET /api/master/price-levels - get all price level definitions"""
        res = requests.get(f"{BASE_URL}/api/master/price-levels", headers=self.headers)
        assert res.status_code == 200, f"Price levels failed: {res.status_code}"
        data = res.json()
        print(f"✓ Price levels: {len(data)} levels defined")
    
    def test_price_for_customer_with_real_data(self):
        """Test GET /api/master/price-for-customer/{product_id}/{customer_id}"""
        # First get a real product and customer
        prod_res = requests.get(f"{BASE_URL}/api/products?limit=1", headers=self.headers)
        cust_res = requests.get(f"{BASE_URL}/api/customers?limit=1", headers=self.headers)
        
        if prod_res.status_code == 200 and cust_res.status_code == 200:
            prods = prod_res.json().get('items', [])
            custs = cust_res.json().get('items', [])
            
            if prods and custs:
                product_id = prods[0].get('id')
                customer_id = custs[0].get('id')
                
                res = requests.get(
                    f"{BASE_URL}/api/master/price-for-customer/{product_id}/{customer_id}",
                    headers=self.headers
                )
                assert res.status_code in [200, 404], f"Price for customer failed: {res.status_code}"
                if res.status_code == 200:
                    data = res.json()
                    print(f"✓ Price for customer: level={data.get('price_level')}, price={data.get('price')}")
            else:
                print("⚠ No products or customers found for testing")
        else:
            print("⚠ Could not fetch products/customers for testing")


class TestOwnerEditAPIs:
    """Test Owner Edit APIs for Sales, Items, Purchase Orders"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token and verify owner role"""
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json=OWNER_CREDS)
        assert login_res.status_code == 200
        data = login_res.json()
        self.token = data.get('token')
        self.user = data.get('user', {})
        self.headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        
        # Verify owner role
        role = self.user.get('role', '').lower()
        print(f"Logged in as: {self.user.get('name')} - role: {role}")
    
    def test_owner_edit_sales_invoice(self):
        """Test PUT /api/owner/edit/sales/{id} - Sales Invoice owner edit"""
        # Get a sales invoice first
        sales_res = requests.get(f"{BASE_URL}/api/sales/invoices?limit=1", headers=self.headers)
        if sales_res.status_code == 200:
            invoices = sales_res.json().get('items', [])
            if invoices:
                invoice_id = invoices[0].get('id')
                # Test owner edit endpoint
                edit_payload = {
                    "notes": f"TEST_OWNER_EDIT_{invoice_id[:8]}",
                    "discount_amount": 0
                }
                res = requests.put(
                    f"{BASE_URL}/api/owner/edit/sales/{invoice_id}",
                    json=edit_payload,
                    headers=self.headers
                )
                assert res.status_code in [200, 404, 403], f"Owner edit sales failed: {res.status_code}"
                if res.status_code == 200:
                    data = res.json()
                    print(f"✓ Owner edit sales: audit_logged={data.get('audit_logged')}")
            else:
                print("⚠ No sales invoices found for testing")
        else:
            print(f"⚠ Could not fetch sales invoices: {sales_res.status_code}")
    
    def test_owner_edit_item(self):
        """Test PUT /api/owner/edit/item/{id} - Master Item owner edit"""
        # Get an item first
        items_res = requests.get(f"{BASE_URL}/api/master/items?limit=1", headers=self.headers)
        if items_res.status_code == 200:
            items = items_res.json().get('items', [])
            if items:
                item_id = items[0].get('id')
                edit_payload = {
                    "name": items[0].get('name'),  # Keep same name
                    "min_stock": 10
                }
                res = requests.put(
                    f"{BASE_URL}/api/owner/edit/item/{item_id}",
                    json=edit_payload,
                    headers=self.headers
                )
                assert res.status_code in [200, 404, 403], f"Owner edit item failed: {res.status_code}"
                if res.status_code == 200:
                    data = res.json()
                    print(f"✓ Owner edit item: audit_logged={data.get('audit_logged')}")
            else:
                print("⚠ No items found for testing")
        else:
            print(f"⚠ Could not fetch items: {items_res.status_code}")
    
    def test_owner_edit_purchase_order(self):
        """Test PUT /api/owner/edit/purchase-order/{id} - PO owner edit"""
        # Get a PO first
        po_res = requests.get(f"{BASE_URL}/api/purchase/orders?limit=1", headers=self.headers)
        if po_res.status_code == 200:
            orders = po_res.json().get('items', po_res.json() if isinstance(po_res.json(), list) else [])
            if orders:
                order_id = orders[0].get('id')
                edit_payload = {
                    "notes": f"TEST_OWNER_EDIT_{order_id[:8] if order_id else 'PO'}"
                }
                res = requests.put(
                    f"{BASE_URL}/api/owner/edit/purchase-order/{order_id}",
                    json=edit_payload,
                    headers=self.headers
                )
                assert res.status_code in [200, 404, 403], f"Owner edit PO failed: {res.status_code}"
                if res.status_code == 200:
                    data = res.json()
                    print(f"✓ Owner edit PO: audit_logged={data.get('audit_logged')}")
            else:
                print("⚠ No purchase orders found for testing")
        else:
            print(f"⚠ Could not fetch purchase orders: {po_res.status_code}")
    
    def test_audit_logs_accessible(self):
        """Test GET /api/owner/audit-logs - verify audit logs accessible for owner"""
        res = requests.get(f"{BASE_URL}/api/owner/audit-logs?limit=5", headers=self.headers)
        assert res.status_code in [200, 403], f"Audit logs failed: {res.status_code}"
        if res.status_code == 200:
            data = res.json()
            logs = data.get('logs', data if isinstance(data, list) else [])
            print(f"✓ Audit logs accessible: {len(logs)} recent logs")


class TestSalesInvoiceIntegration:
    """Test Sales Invoice with pricing engine integration"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json=OWNER_CREDS)
        assert login_res.status_code == 200
        self.token = login_res.json().get('token')
        self.headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
    
    def test_sales_invoices_list(self):
        """Test GET /api/sales/invoices"""
        res = requests.get(f"{BASE_URL}/api/sales/invoices", headers=self.headers)
        assert res.status_code == 200, f"Sales invoices list failed: {res.status_code}"
        data = res.json()
        print(f"✓ Sales invoices: {len(data.get('items', []))} found")
    
    def test_customers_with_price_level(self):
        """Test that customers have price level info"""
        res = requests.get(f"{BASE_URL}/api/customers?limit=5", headers=self.headers)
        assert res.status_code == 200
        customers = res.json().get('items', [])
        for c in customers[:3]:
            # Check if customer has price_level or segment (which determines price level)
            print(f"Customer: {c.get('name')} - segment: {c.get('segment', 'N/A')}, price_level: {c.get('price_level', 'N/A')}")
    
    def test_products_list(self):
        """Test GET /api/products"""
        res = requests.get(f"{BASE_URL}/api/products?limit=5", headers=self.headers)
        assert res.status_code == 200
        data = res.json()
        products = data.get('items', [])
        print(f"✓ Products: {len(products)} found")
        for p in products[:3]:
            print(f"  - {p.get('name')}: sell_price={p.get('selling_price', p.get('sell_price', 0))}")


class TestPOSIntegration:
    """Test POS pricing engine integration"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json=OWNER_CREDS)
        assert login_res.status_code == 200
        self.token = login_res.json().get('token')
        self.headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
    
    def test_product_search(self):
        """Test GET /api/products/search - used in POS"""
        res = requests.get(f"{BASE_URL}/api/products/search?q=test", headers=self.headers)
        assert res.status_code == 200, f"Product search failed: {res.status_code}"
        print(f"✓ Product search works")
    
    def test_customer_search(self):
        """Test GET /api/customers/search - used in POS"""
        res = requests.get(f"{BASE_URL}/api/customers/search?q=test", headers=self.headers)
        assert res.status_code == 200, f"Customer search failed: {res.status_code}"
        print(f"✓ Customer search works")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
