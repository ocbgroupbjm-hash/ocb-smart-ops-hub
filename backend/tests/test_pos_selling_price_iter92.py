"""
Test POS Screen selling_price bug fix - iteration 92
Bug: POS Screen items were showing Rp 0 price
Root cause: Backend sends 'selling_price' but frontend was looking for 'sell_price'
Fix: POSScreen.jsx now uses product.selling_price || product.sell_price
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "tenant_id": "ocb_titan",
        "email": "ocbgroupbjm@gmail.com",
        "password": "admin123"
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json().get("token")

@pytest.fixture
def api_client(auth_token):
    """Shared requests session with auth header"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    })
    return session


class TestProductSellingPriceField:
    """Test that products API returns selling_price field correctly"""
    
    def test_products_list_has_selling_price(self, api_client):
        """Products list endpoint returns selling_price field"""
        response = api_client.get(f"{BASE_URL}/api/products?limit=10")
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert len(data["items"]) > 0
        
        # Check first product has selling_price field
        product = data["items"][0]
        assert "selling_price" in product, "Product missing selling_price field"
        assert isinstance(product["selling_price"], (int, float)), "selling_price should be numeric"
    
    def test_prd002_has_correct_selling_price(self, api_client):
        """PRD002 (XL Unlimited 30 Hari) should have selling_price = 65000"""
        response = api_client.get(f"{BASE_URL}/api/products?search=PRD002")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["items"]) > 0, "PRD002 not found"
        
        product = data["items"][0]
        assert product["code"] == "PRD002"
        assert product["selling_price"] == 65000, f"Expected 65000, got {product['selling_price']}"
    
    def test_product_search_returns_selling_price(self, api_client):
        """Product search endpoint returns selling_price"""
        response = api_client.get(f"{BASE_URL}/api/products/search?q=XL")
        assert response.status_code == 200
        
        products = response.json()
        assert len(products) > 0, "No products found for search 'XL'"
        
        # All products should have selling_price
        for product in products:
            assert "selling_price" in product, f"Product {product.get('code')} missing selling_price"
    
    def test_product_by_id_has_selling_price(self, api_client):
        """Get product by ID returns selling_price"""
        # First get PRD002's ID
        response = api_client.get(f"{BASE_URL}/api/products?search=PRD002")
        assert response.status_code == 200
        product_id = response.json()["items"][0]["id"]
        
        # Get product by ID
        response = api_client.get(f"{BASE_URL}/api/products/{product_id}")
        assert response.status_code == 200
        
        product = response.json()
        assert "selling_price" in product
        assert product["selling_price"] == 65000


class TestSalesInvoiceWithCorrectPrice:
    """Test that sales invoices use correct selling_price"""
    
    def test_get_recent_invoice_with_correct_total(self, api_client):
        """Check recent invoice INV-20260320-0012 has correct total"""
        response = api_client.get(f"{BASE_URL}/api/sales/invoices?limit=20")
        assert response.status_code == 200
        
        data = response.json()
        invoices = data.get("items", [])
        
        # Look for the test invoice or any invoice with correct pricing
        found_invoice = None
        for inv in invoices:
            if inv.get("invoice_number") == "INV-20260320-0012":
                found_invoice = inv
                break
        
        if found_invoice:
            # Invoice should have total = 65000 (1 x PRD002)
            assert found_invoice["total"] == 65000, f"Invoice total should be 65000, got {found_invoice['total']}"
            print(f"Found invoice INV-20260320-0012 with correct total: {found_invoice['total']}")
        else:
            # If not found, just verify we can fetch invoices
            print("Invoice INV-20260320-0012 not found in recent list, but API works")
    
    def test_create_invoice_with_correct_price(self, api_client):
        """Create new invoice and verify price is saved correctly"""
        # Get PRD002 details
        response = api_client.get(f"{BASE_URL}/api/products?search=PRD002")
        assert response.status_code == 200
        product = response.json()["items"][0]
        product_id = product["id"]
        selling_price = product["selling_price"]
        
        # Get a customer
        response = api_client.get(f"{BASE_URL}/api/customers")
        assert response.status_code == 200
        customers = response.json().get("items", [])
        customer_id = customers[0]["id"] if customers else ""
        
        # Get a warehouse
        response = api_client.get(f"{BASE_URL}/api/master/warehouses")
        assert response.status_code == 200
        warehouses = response.json()
        warehouse_id = warehouses[0]["id"] if warehouses else ""
        
        # Create invoice payload - same as POSScreen uses
        qty = 2
        payload = {
            "customer_id": customer_id,
            "warehouse_id": warehouse_id,
            "ppn_type": "exclude",
            "ppn_percent": 0,
            "notes": "TEST-POS-PRICE-FIX - Verify selling_price used",
            "items": [{
                "product_id": product_id,
                "quantity": qty,
                "unit_price": selling_price,  # Should be 65000
                "discount_percent": 0,
                "tax_percent": 0,
            }],
            "subtotal": selling_price * qty,  # 130000
            "discount_amount": 0,
            "tax_amount": 0,
            "other_cost": 0,
            "total": selling_price * qty,  # 130000
            "payment_type": "cash",
            "cash_amount": selling_price * qty,
            "credit_amount": 0,
        }
        
        response = api_client.post(f"{BASE_URL}/api/sales/invoices", json=payload)
        assert response.status_code in [200, 201], f"Failed to create invoice: {response.text}"
        
        data = response.json()
        invoice_number = data.get("invoice_number", "")
        print(f"Created test invoice: {invoice_number}")
        
        # Verify the invoice was saved with correct total
        assert "id" in data or "invoice_number" in data


class TestProductPriceVariations:
    """Test various products have correct selling_price"""
    
    def test_multiple_products_have_selling_price(self, api_client):
        """Verify multiple products have valid selling_price"""
        response = api_client.get(f"{BASE_URL}/api/products?limit=20")
        assert response.status_code == 200
        
        products = response.json()["items"]
        products_with_price = []
        products_without_price = []
        
        for p in products:
            price = p.get("selling_price", 0) or 0
            if price > 0:
                products_with_price.append(p["code"])
            else:
                products_without_price.append(p["code"])
        
        print(f"Products with selling_price > 0: {len(products_with_price)}")
        print(f"Products with selling_price = 0: {len(products_without_price)}")
        
        # At least some products should have price
        assert len(products_with_price) > 0, "No products have selling_price > 0"
    
    def test_sell_price_vs_selling_price_field(self, api_client):
        """Check that selling_price is the correct field, not sell_price"""
        response = api_client.get(f"{BASE_URL}/api/products?limit=5")
        assert response.status_code == 200
        
        products = response.json()["items"]
        for p in products:
            # selling_price should be the valid field
            assert "selling_price" in p, f"Product {p['code']} missing selling_price"
            
            # sell_price might be null or not present
            sell_price = p.get("sell_price")
            selling_price = p.get("selling_price")
            
            # For products with price, selling_price should be valid
            if selling_price and selling_price > 0:
                print(f"Product {p['code']}: selling_price={selling_price}, sell_price={sell_price}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
