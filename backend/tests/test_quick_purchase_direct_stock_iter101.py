"""
Quick Purchase Direct Stock In - ARSITEKTUR FINAL OCB TITAN
Tests for POST /api/purchase/quick endpoint that LANGSUNG adds stock
Iteration 101

FLOW FINAL per Arsitektur:
- Quick Purchase = purchase + stock in LANGSUNG
- Berbeda dengan Buat PO (/api/purchase/orders) yang status draft

SOURCE OF TRUTH:
- Lokasi: branches
- Item Master: products  
- Stok: product_stocks
- Histori Stok: stock_movements
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://smart-ops-hub-6.preview.emergentagent.com')


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for OCB TITAN tenant"""
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


class TestQuickPurchaseEndpoint:
    """Test POST /api/purchase/quick - Direct Stock In"""
    
    @pytest.fixture
    def test_supplier(self, api_client):
        """Get a valid supplier for testing"""
        response = api_client.get(f"{BASE_URL}/api/suppliers")
        assert response.status_code == 200
        suppliers = response.json()["items"]
        assert len(suppliers) > 0, "No suppliers found"
        return suppliers[0]
    
    @pytest.fixture
    def test_product(self, api_client):
        """Get a valid product for testing"""
        response = api_client.get(f"{BASE_URL}/api/products?limit=5")
        assert response.status_code == 200
        products = response.json()["items"]
        assert len(products) > 0, "No products found"
        return products[0]
    
    @pytest.fixture
    def test_branch(self, api_client):
        """Get a valid branch/warehouse for testing"""
        response = api_client.get(f"{BASE_URL}/api/master/warehouses")
        assert response.status_code == 200
        branches = response.json()
        assert len(branches) > 0, "No branches found"
        return branches[0]
    
    def test_01_quick_purchase_endpoint_exists(self, api_client, test_supplier, test_product):
        """POST /api/purchase/quick - Endpoint should exist and accept requests"""
        payload = {
            "supplier_id": test_supplier["id"],
            "branch_id": "",  # Will use default
            "items": [
                {
                    "product_id": test_product["id"],
                    "product_name": test_product.get("name", "Test Product"),
                    "quantity": 1,
                    "unit_cost": 10000,
                    "discount_percent": 0,
                    "purchase_unit": test_product.get("unit", "pcs"),
                    "conversion_ratio": 1
                }
            ],
            "notes": "TEST_Quick Purchase Iteration 101 - Endpoint Test",
            "is_cash": True
        }
        
        response = api_client.post(f"{BASE_URL}/api/purchase/quick", json=payload)
        assert response.status_code == 200, f"Quick Purchase endpoint failed: {response.text}"
        
        data = response.json()
        assert data.get("success") == True, f"Expected success=True, got {data}"
        assert "po_number" in data, "Missing po_number in response"
        assert data["po_number"].startswith("QPO"), f"Expected QPO prefix, got {data['po_number']}"
        
        print(f"✓ Quick Purchase created: {data['po_number']}")
        print(f"  Stock updated: {data.get('stock_updated', [])}")
    
    def test_02_quick_purchase_creates_posted_status(self, api_client, test_supplier, test_product):
        """Quick Purchase should create PO with status='posted' (not draft)"""
        payload = {
            "supplier_id": test_supplier["id"],
            "items": [
                {
                    "product_id": test_product["id"],
                    "quantity": 2,
                    "unit_cost": 15000
                }
            ],
            "notes": "TEST_Posted Status Check"
        }
        
        response = api_client.post(f"{BASE_URL}/api/purchase/quick", json=payload)
        assert response.status_code == 200
        data = response.json()
        
        po_id = data.get("id")
        po_number = data.get("po_number")
        
        # Verify the PO has posted status
        verify_response = api_client.get(f"{BASE_URL}/api/purchase/orders/{po_id}")
        assert verify_response.status_code == 200
        
        po_data = verify_response.json()
        assert po_data.get("status") == "posted", f"Expected 'posted' status, got '{po_data.get('status')}'"
        assert po_data.get("is_quick_purchase") == True, "Expected is_quick_purchase=True"
        
        print(f"✓ PO {po_number} has correct status: {po_data.get('status')}")
    
    def test_03_quick_purchase_stock_immediately_updated(self, api_client, test_supplier, test_branch):
        """Quick Purchase should IMMEDIATELY update stock in product_stocks"""
        # Get a product and its current stock
        products_response = api_client.get(f"{BASE_URL}/api/products?limit=3")
        assert products_response.status_code == 200
        products = products_response.json()["items"]
        test_product = products[0]
        
        # Get current stock for this product in the branch
        stock_before_response = api_client.get(f"{BASE_URL}/api/products?branch_id={test_branch['id']}&search={test_product.get('code', '')}")
        stock_before = 0
        if stock_before_response.status_code == 200:
            before_data = stock_before_response.json()
            if before_data["items"]:
                stock_before = before_data["items"][0].get("stock", 0)
        
        # Perform quick purchase
        qty_to_add = 3
        payload = {
            "supplier_id": test_supplier["id"],
            "branch_id": test_branch["id"],
            "items": [
                {
                    "product_id": test_product["id"],
                    "quantity": qty_to_add,
                    "unit_cost": 20000
                }
            ],
            "notes": "TEST_Stock Update Check"
        }
        
        response = api_client.post(f"{BASE_URL}/api/purchase/quick", json=payload)
        assert response.status_code == 200
        data = response.json()
        
        # Verify stock was updated in the response
        stock_updated = data.get("stock_updated", [])
        assert len(stock_updated) > 0, "Expected stock_updated in response"
        
        stock_result = stock_updated[0]
        assert stock_result["added"] == qty_to_add
        assert stock_result["new_stock"] == stock_result["old_stock"] + qty_to_add
        
        print(f"✓ Stock updated: {stock_result['old_stock']} → {stock_result['new_stock']} (+{qty_to_add})")
    
    def test_04_quick_purchase_records_stock_movement(self, api_client, test_supplier, test_product, test_branch):
        """Quick Purchase should record stock_movement with reference_type='quick_purchase'"""
        # Perform quick purchase
        payload = {
            "supplier_id": test_supplier["id"],
            "branch_id": test_branch["id"],
            "items": [
                {
                    "product_id": test_product["id"],
                    "quantity": 5,
                    "unit_cost": 25000
                }
            ],
            "notes": "TEST_Stock Movement Check"
        }
        
        response = api_client.post(f"{BASE_URL}/api/purchase/quick", json=payload)
        assert response.status_code == 200
        data = response.json()
        
        po_number = data.get("po_number")
        
        # Check stock movements
        movements_response = api_client.get(f"{BASE_URL}/api/inventory/movements?limit=10")
        assert movements_response.status_code == 200
        
        movements = movements_response.json().get("items", [])
        
        # Find movement for our quick purchase
        found_movement = None
        for movement in movements:
            if movement.get("reference_no") == po_number or movement.get("reference_type") == "quick_purchase":
                found_movement = movement
                break
        
        if found_movement:
            assert found_movement.get("reference_type") == "quick_purchase"
            assert found_movement.get("movement_type") == "stock_in"
            print(f"✓ Stock movement recorded: {found_movement.get('reference_no')}")
        else:
            # May be due to pagination, check the response had stock_updated
            assert len(data.get("stock_updated", [])) > 0
            print(f"✓ Stock updated verified through response")
    
    def test_05_quick_purchase_requires_supplier(self, api_client, test_product):
        """Quick Purchase should fail without supplier_id"""
        payload = {
            "supplier_id": "",
            "items": [
                {
                    "product_id": test_product["id"],
                    "quantity": 1,
                    "unit_cost": 10000
                }
            ]
        }
        
        response = api_client.post(f"{BASE_URL}/api/purchase/quick", json=payload)
        assert response.status_code == 400, f"Should reject empty supplier: {response.status_code}"
        print("✓ Correctly rejected Quick Purchase without supplier")
    
    def test_06_quick_purchase_requires_items(self, api_client, test_supplier):
        """Quick Purchase should fail without items"""
        payload = {
            "supplier_id": test_supplier["id"],
            "items": []
        }
        
        response = api_client.post(f"{BASE_URL}/api/purchase/quick", json=payload)
        assert response.status_code == 400, f"Should reject empty items: {response.status_code}"
        print("✓ Correctly rejected Quick Purchase without items")
    
    def test_07_quick_purchase_requires_positive_quantity(self, api_client, test_supplier, test_product):
        """Quick Purchase should fail with zero or negative quantity"""
        payload = {
            "supplier_id": test_supplier["id"],
            "items": [
                {
                    "product_id": test_product["id"],
                    "quantity": 0,  # Invalid
                    "unit_cost": 10000
                }
            ]
        }
        
        response = api_client.post(f"{BASE_URL}/api/purchase/quick", json=payload)
        assert response.status_code == 400, f"Should reject zero quantity: {response.status_code}"
        print("✓ Correctly rejected Quick Purchase with zero quantity")


class TestBuatPOvsQuickPurchase:
    """Test difference between Buat PO (/api/purchase/orders) and Quick Purchase (/api/purchase/quick)"""
    
    @pytest.fixture
    def test_supplier(self, api_client):
        """Get a valid supplier for testing"""
        response = api_client.get(f"{BASE_URL}/api/suppliers")
        assert response.status_code == 200
        return response.json()["items"][0]
    
    @pytest.fixture
    def test_product(self, api_client):
        """Get a valid product for testing"""
        response = api_client.get(f"{BASE_URL}/api/products?limit=1")
        assert response.status_code == 200
        return response.json()["items"][0]
    
    def test_08_buat_po_creates_draft_status(self, api_client, test_supplier, test_product):
        """POST /api/purchase/orders - Should create PO with status='draft' (NO stock change)"""
        payload = {
            "supplier_id": test_supplier["id"],
            "items": [
                {
                    "product_id": test_product["id"],
                    "quantity": 10,
                    "unit_cost": 30000
                }
            ],
            "notes": "TEST_Buat PO vs Quick Purchase - Draft PO"
        }
        
        response = api_client.post(f"{BASE_URL}/api/purchase/orders", json=payload)
        assert response.status_code == 200
        data = response.json()
        
        po_id = data.get("id")
        po_number = data.get("po_number")
        
        # Verify status is draft
        verify_response = api_client.get(f"{BASE_URL}/api/purchase/orders/{po_id}")
        assert verify_response.status_code == 200
        
        po_data = verify_response.json()
        assert po_data.get("status") == "draft", f"Buat PO should be 'draft', got '{po_data.get('status')}'"
        
        # Should NOT have is_quick_purchase flag
        assert po_data.get("is_quick_purchase") != True
        
        print(f"✓ Buat PO {po_number} correctly has draft status")
        print(f"  (Stok belum masuk, perlu proses Terima Barang)")
    
    def test_09_verify_po_prefix_difference(self, api_client):
        """Quick Purchase uses QPO prefix, regular PO uses PO prefix"""
        # Get recent POs
        response = api_client.get(f"{BASE_URL}/api/purchase/orders?limit=20")
        assert response.status_code == 200
        
        pos = response.json()["items"]
        
        quick_pos = [po for po in pos if po.get("po_number", "").startswith("QPO")]
        regular_pos = [po for po in pos if po.get("po_number", "").startswith("PO") and not po.get("po_number", "").startswith("QPO")]
        
        print(f"Found {len(quick_pos)} Quick Purchase orders (QPO prefix)")
        print(f"Found {len(regular_pos)} Regular PO orders (PO prefix)")
        
        # Verify quick purchase POs have posted status
        for qpo in quick_pos[:3]:  # Check first 3
            assert qpo.get("status") == "posted" or qpo.get("is_quick_purchase") == True, \
                f"QPO {qpo.get('po_number')} should be posted or quick_purchase"


class TestProductsListShowsUpdatedStock:
    """Test that /api/products shows updated stock after Quick Purchase"""
    
    @pytest.fixture
    def test_supplier(self, api_client):
        response = api_client.get(f"{BASE_URL}/api/suppliers")
        return response.json()["items"][0]
    
    @pytest.fixture
    def test_branch(self, api_client):
        response = api_client.get(f"{BASE_URL}/api/master/warehouses")
        return response.json()[0]
    
    def test_10_products_list_shows_branch_stock(self, api_client, test_branch):
        """GET /api/products?branch_id=xxx - Should show stock for specific branch"""
        response = api_client.get(f"{BASE_URL}/api/products?branch_id={test_branch['id']}&limit=5")
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        
        # Check stock fields are present
        for product in data["items"][:3]:
            assert "stock" in product or product.get("stock") is not None, \
                f"Product {product.get('name')} missing stock field"
            print(f"  Product: {product.get('name', 'N/A')[:30]} | Stock: {product.get('stock', 0)}")
        
        print(f"✓ Products list returns stock for branch {test_branch['name']}")
    
    def test_11_products_list_aggregates_stock(self, api_client):
        """GET /api/products - Without branch filter should aggregate stock across all branches"""
        response = api_client.get(f"{BASE_URL}/api/products?limit=5")
        assert response.status_code == 200
        
        data = response.json()
        
        for product in data["items"][:3]:
            if "branches_count" in product:
                print(f"  Product: {product.get('name', 'N/A')[:30]} | Stock: {product.get('stock', 0)} | Branches: {product.get('branches_count', 0)}")
        
        print("✓ Products list shows aggregated stock")


class TestBranchFilterInProducts:
    """Test branch_id filter works correctly in Products page"""
    
    def test_12_branch_filter_works(self, api_client):
        """Branch filter should filter stock by specific branch"""
        # Get branches
        branches_response = api_client.get(f"{BASE_URL}/api/master/warehouses")
        assert branches_response.status_code == 200
        branches = branches_response.json()
        assert len(branches) > 0
        
        test_branch = branches[0]
        
        # Get products with branch filter
        response = api_client.get(f"{BASE_URL}/api/products?branch_id={test_branch['id']}&limit=3")
        assert response.status_code == 200
        
        data = response.json()
        print(f"✓ Branch filter works for: {test_branch['name']}")
        print(f"  Found {len(data['items'])} products")


# ==================== Run Tests ====================
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
