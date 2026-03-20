"""
Quick Purchase Module - Backend API Tests
Tests for the iPOS-style Quick Purchase feature at /purchase/quick
Iteration 91 - Testing backend APIs for purchase orders
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://smart-ops-hub-6.preview.emergentagent.com')

@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for OCB GROUP tenant"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={
            "email": "ocbgroupbjm@gmail.com",
            "password": "admin123",
            "tenant_id": "ocb_titan"
        }
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    assert "token" in data, "No token in response"
    return data["token"]


@pytest.fixture(scope="module")
def api_client(auth_token):
    """Create authenticated session"""
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    })
    return session


class TestProductSearch:
    """Test product search for Quick Purchase"""
    
    def test_get_products_list(self, api_client):
        """GET /api/products - should return products for search"""
        response = api_client.get(f"{BASE_URL}/api/products?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) > 0
        
        # Verify product structure
        product = data["items"][0]
        assert "id" in product
        assert "name" in product or "code" in product
        print(f"Found {len(data['items'])} products")
    
    def test_search_products_by_name(self, api_client):
        """GET /api/products?search=charger - should return matching products"""
        response = api_client.get(f"{BASE_URL}/api/products?search=charger&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        # May have 0 results if no charger products
        print(f"Found {len(data['items'])} products matching 'charger'")
    
    def test_search_products_by_code(self, api_client):
        """GET /api/products?search=PRD - should return products with PRD code"""
        response = api_client.get(f"{BASE_URL}/api/products?search=PRD&limit=10")
        assert response.status_code == 200
        data = response.json()
        print(f"Found {len(data['items'])} products matching 'PRD'")


class TestSupplierSelection:
    """Test supplier dropdown data"""
    
    def test_get_suppliers_list(self, api_client):
        """GET /api/suppliers - should return suppliers for dropdown"""
        response = api_client.get(f"{BASE_URL}/api/suppliers")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) > 0
        
        # Verify supplier structure
        supplier = data["items"][0]
        assert "id" in supplier
        assert "name" in supplier
        print(f"Found {len(data['items'])} suppliers")
        return data["items"][0]["id"]  # Return first supplier ID for PO test


class TestWarehouseSelection:
    """Test warehouse dropdown data"""
    
    def test_get_warehouses_list(self, api_client):
        """GET /api/master/warehouses - should return warehouses for dropdown"""
        response = api_client.get(f"{BASE_URL}/api/master/warehouses")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "items" in data
        
        warehouses = data if isinstance(data, list) else data.get("items", [])
        assert len(warehouses) > 0
        
        # Verify warehouse structure
        warehouse = warehouses[0]
        assert "id" in warehouse
        assert "name" in warehouse
        print(f"Found {len(warehouses)} warehouses")


class TestPurchaseOrderCRUD:
    """Test Purchase Order creation from Quick Purchase"""
    
    @pytest.fixture
    def test_supplier_id(self, api_client):
        """Get a valid supplier ID for testing"""
        response = api_client.get(f"{BASE_URL}/api/suppliers")
        assert response.status_code == 200
        suppliers = response.json()["items"]
        assert len(suppliers) > 0
        return suppliers[0]["id"]
    
    @pytest.fixture
    def test_product(self, api_client):
        """Get a valid product for testing"""
        response = api_client.get(f"{BASE_URL}/api/products?limit=1")
        assert response.status_code == 200
        products = response.json()["items"]
        assert len(products) > 0
        return products[0]
    
    def test_create_po_from_quick_purchase(self, api_client, test_supplier_id, test_product):
        """POST /api/purchase/orders - Create PO with draft status"""
        payload = {
            "supplier_id": test_supplier_id,
            "items": [
                {
                    "product_id": test_product["id"],
                    "product_name": test_product.get("name", "Test Product"),
                    "quantity": 2,
                    "unit_cost": 50000,
                    "discount_percent": 0,
                    "purchase_unit": test_product.get("unit", "pcs"),
                    "conversion_ratio": 1
                }
            ],
            "notes": "TEST_Quick Purchase - Iteration 91 Test",
            "total_amount": 100000
        }
        
        response = api_client.post(f"{BASE_URL}/api/purchase/orders", json=payload)
        assert response.status_code == 200, f"Create PO failed: {response.text}"
        
        data = response.json()
        assert "id" in data or "po_number" in data
        
        po_number = data.get("po_number")
        po_id = data.get("id")
        print(f"Created PO: {po_number} (ID: {po_id})")
        
        # Verify the PO was created with draft status
        if po_id:
            verify_response = api_client.get(f"{BASE_URL}/api/purchase/orders/{po_id}")
            if verify_response.status_code == 200:
                po_data = verify_response.json()
                assert po_data.get("status") == "draft", "PO should be created with draft status"
                print(f"Verified PO status: {po_data.get('status')}")
        
        return data
    
    def test_create_po_requires_supplier(self, api_client, test_product):
        """POST /api/purchase/orders - Should fail without supplier"""
        payload = {
            "supplier_id": "",  # Empty supplier
            "items": [
                {
                    "product_id": test_product["id"],
                    "quantity": 1,
                    "unit_cost": 10000
                }
            ]
        }
        
        response = api_client.post(f"{BASE_URL}/api/purchase/orders", json=payload)
        # Should fail with 400 Bad Request
        assert response.status_code in [400, 422], f"Should reject empty supplier: {response.status_code}"
        print("Correctly rejected PO without supplier")
    
    def test_create_po_requires_items(self, api_client, test_supplier_id):
        """POST /api/purchase/orders - Should fail without items"""
        payload = {
            "supplier_id": test_supplier_id,
            "items": []  # Empty items
        }
        
        response = api_client.post(f"{BASE_URL}/api/purchase/orders", json=payload)
        # Should fail with 400 Bad Request
        assert response.status_code in [400, 422], f"Should reject empty items: {response.status_code}"
        print("Correctly rejected PO without items")
    
    def test_list_purchase_orders(self, api_client):
        """GET /api/purchase/orders - Should list POs"""
        response = api_client.get(f"{BASE_URL}/api/purchase/orders?limit=5")
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert "total" in data
        
        print(f"Found {data['total']} total POs, showing {len(data['items'])}")
        
        # Verify PO structure
        if len(data["items"]) > 0:
            po = data["items"][0]
            assert "po_number" in po
            assert "status" in po


class TestPurchaseOrderListFilters:
    """Test PO list filtering for Quick Purchase workflow"""
    
    def test_filter_by_status_draft(self, api_client):
        """GET /api/purchase/orders?status=draft - Filter by draft status"""
        response = api_client.get(f"{BASE_URL}/api/purchase/orders?status=draft&limit=10")
        assert response.status_code == 200
        
        data = response.json()
        for po in data["items"]:
            assert po["status"] == "draft", f"Expected draft status, got {po['status']}"
        
        print(f"Found {len(data['items'])} draft POs")
    
    def test_search_by_po_number(self, api_client):
        """GET /api/purchase/orders?search=PO000 - Search by PO number"""
        response = api_client.get(f"{BASE_URL}/api/purchase/orders?search=PO000&limit=10")
        assert response.status_code == 200
        
        data = response.json()
        print(f"Found {len(data['items'])} POs matching 'PO000'")


class TestPriceHistoryTracking:
    """Test purchase price history (for price tracking feature)"""
    
    def test_get_price_history(self, api_client):
        """GET /api/purchase/price-history - Should return price history"""
        response = api_client.get(f"{BASE_URL}/api/purchase/price-history?limit=10")
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        print(f"Found {len(data['items'])} price history records")


# Cleanup fixture to delete test POs
@pytest.fixture(scope="module", autouse=True)
def cleanup_test_data(api_client):
    """Cleanup TEST_ prefixed POs after tests"""
    yield
    # Note: In production, implement proper cleanup
    # For now, test POs with notes containing "TEST_" can be identified
    print("Test cleanup: Manual cleanup may be needed for TEST_ prefixed records")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
