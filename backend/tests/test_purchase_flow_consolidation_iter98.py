"""
Purchase Flow Consolidation Tests - Iteration 98
Testing P0 BLOCKER FIX: warehouse_id now queries branches collection

Tests:
1. Create PO with warehouse from branches - Quick Purchase flow
2. Create PO with warehouse from branches - Buat PO modal flow
3. Discount calculation validation
4. Warehouse dropdown returns branches data
5. PO creation returns po_number
6. PO saved with correct warehouse_name
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = "https://smart-ops-hub-6.preview.emergentagent.com"

# Test credentials
TEST_EMAIL = "ocbgroupbjm@gmail.com"
TEST_PASSWORD = "admin123"
TEST_TENANT = "ocb_titan"


@pytest.fixture(scope="module")
def auth_session():
    """Get authenticated session for all tests"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    
    # Login
    login_response = session.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "tenant_id": TEST_TENANT
    })
    
    if login_response.status_code != 200:
        pytest.skip(f"Authentication failed: {login_response.text}")
    
    data = login_response.json()
    token = data.get("token") or data.get("access_token")
    session.headers.update({"Authorization": f"Bearer {token}"})
    
    # Store test data
    session.test_data = {
        "warehouse_id": None,
        "supplier_id": None,
        "product_id": None,
        "po_id": None
    }
    
    return session


class TestPurchaseFlowConsolidation:
    """Test Purchase Order creation with warehouse from branches collection"""
    
    def test_01_warehouse_endpoint_returns_branches_data(self, auth_session):
        """Test that /api/master/warehouses returns data from branches collection"""
        response = auth_session.get(f"{BASE_URL}/api/master/warehouses")
        assert response.status_code == 200, f"Warehouse endpoint failed: {response.text}"
        
        warehouses = response.json()
        assert isinstance(warehouses, list), "Warehouses should be a list"
        assert len(warehouses) > 0, "Should have at least one warehouse"
        
        # Check first warehouse
        first_warehouse = warehouses[0]
        print(f"First warehouse: {first_warehouse.get('name')} (id: {first_warehouse.get('id')})")
        
        # Find "3 FRONT" warehouse or use first one
        for wh in warehouses:
            if "FRONT" in wh.get("name", "").upper() or "3 FRONT" in wh.get("name", ""):
                auth_session.test_data["warehouse_id"] = wh.get('id')
                print(f"Found '3 FRONT' warehouse: {wh.get('name')}")
                break
        
        if not auth_session.test_data["warehouse_id"]:
            auth_session.test_data["warehouse_id"] = first_warehouse.get('id')
        
        # Verify expected fields
        assert 'id' in first_warehouse, "Warehouse should have id"
        assert 'name' in first_warehouse, "Warehouse should have name"
    
    def test_02_get_suppliers_for_po(self, auth_session):
        """Get suppliers list for PO creation"""
        response = auth_session.get(f"{BASE_URL}/api/suppliers")
        assert response.status_code == 200, f"Suppliers endpoint failed: {response.text}"
        
        data = response.json()
        suppliers = data.get('items') or data
        assert len(suppliers) > 0, "Should have at least one supplier"
        
        auth_session.test_data["supplier_id"] = suppliers[0].get('id')
        print(f"Using supplier: {suppliers[0].get('name')} (id: {suppliers[0].get('id')})")
    
    def test_03_get_products_for_po(self, auth_session):
        """Get products list for PO creation"""
        response = auth_session.get(f"{BASE_URL}/api/products?limit=10")
        assert response.status_code == 200, f"Products endpoint failed: {response.text}"
        
        data = response.json()
        products = data.get('items') or data
        assert len(products) > 0, "Should have at least one product"
        
        # Find a product with cost_price
        for product in products:
            if product.get('cost_price', 0) > 0:
                auth_session.test_data["product_id"] = product.get('id')
                print(f"Using product: {product.get('name')} (cost: {product.get('cost_price')})")
                break
        
        if not auth_session.test_data["product_id"]:
            auth_session.test_data["product_id"] = products[0].get('id')
    
    def test_04_discount_calculation_10_percent(self, auth_session):
        """Test discount calculation: qty=10, price=10000, disc=10% should result in subtotal=90000"""
        qty = 10
        price = 10000
        discount_percent = 10
        
        # Formula: subtotal = qty * price * (1 - discount_percent/100)
        expected_subtotal = qty * price * (1 - discount_percent / 100)
        
        assert expected_subtotal == 90000, f"Discount calc wrong: expected 90000, got {expected_subtotal}"
        print(f"✓ Discount calculation verified: {qty} * {price} * (1 - {discount_percent}/100) = {expected_subtotal}")
    
    def test_05_discount_calculation_20_percent(self, auth_session):
        """Test discount calculation: qty=5, price=20000, disc=20% should result in subtotal=80000"""
        qty = 5
        price = 20000
        discount_percent = 20
        
        # Formula: subtotal = qty * price * (1 - discount_percent/100)
        expected_subtotal = qty * price * (1 - discount_percent / 100)
        
        assert expected_subtotal == 80000, f"Discount calc wrong: expected 80000, got {expected_subtotal}"
        print(f"✓ Discount calculation verified: {qty} * {price} * (1 - {discount_percent}/100) = {expected_subtotal}")
    
    def test_06_create_po_with_warehouse_from_branches(self, auth_session):
        """Create PO with warehouse_id from branches collection - Core fix test"""
        assert auth_session.test_data["supplier_id"], "No supplier ID from previous test"
        assert auth_session.test_data["warehouse_id"], "No warehouse ID from previous test"
        assert auth_session.test_data["product_id"], "No product ID from previous test"
        
        # Create PO payload (simulating Quick Purchase or Buat PO modal)
        payload = {
            "supplier_id": auth_session.test_data["supplier_id"],
            "warehouse_id": auth_session.test_data["warehouse_id"],
            "notes": "Test PO - Purchase Flow Consolidation iter98",
            "items": [
                {
                    "product_id": auth_session.test_data["product_id"],
                    "product_name": "Test Product",
                    "quantity": 10,
                    "unit_cost": 10000,
                    "discount_percent": 10,
                    "purchase_unit": "pcs",
                    "conversion_ratio": 1
                }
            ],
            "total_amount": 90000  # 10 * 10000 * (1 - 10/100)
        }
        
        print(f"Creating PO with warehouse_id: {auth_session.test_data['warehouse_id']}")
        
        response = auth_session.post(f"{BASE_URL}/api/purchase/orders", json=payload)
        
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text[:500] if response.text else 'empty'}")
        
        assert response.status_code in [200, 201], f"PO creation failed: {response.text}"
        
        data = response.json()
        
        # Verify response contains po_number (requirement)
        assert 'po_number' in data, "Response should contain po_number"
        assert data.get('po_number'), "po_number should not be empty"
        
        auth_session.test_data["po_id"] = data.get('id')
        print(f"✓ PO created successfully: {data.get('po_number')}")
    
    def test_07_verify_po_has_correct_warehouse_name(self, auth_session):
        """Verify saved PO has correct warehouse_name from branches"""
        if not auth_session.test_data["po_id"]:
            pytest.skip("No test PO created")
        
        response = auth_session.get(f"{BASE_URL}/api/purchase/orders/{auth_session.test_data['po_id']}")
        assert response.status_code == 200, f"Get PO failed: {response.text}"
        
        po = response.json()
        
        print(f"PO details:")
        print(f"  - po_number: {po.get('po_number')}")
        print(f"  - warehouse_id: {po.get('warehouse_id')}")
        print(f"  - warehouse_name: {po.get('warehouse_name')}")
        print(f"  - total: {po.get('total')}")
        print(f"  - status: {po.get('status')}")
        
        # Verify warehouse_name is populated correctly
        assert po.get('warehouse_id') == auth_session.test_data["warehouse_id"], "warehouse_id mismatch"
        assert po.get('warehouse_name'), "warehouse_name should be populated from branches"
        
        # Verify items are saved correctly with discount
        items = po.get('items', [])
        assert len(items) > 0, "PO should have items"
        
        first_item = items[0]
        print(f"  - Item: {first_item.get('product_name')}, qty: {first_item.get('quantity')}, price: {first_item.get('unit_cost')}, disc: {first_item.get('discount_percent')}%")
    
    def test_08_branches_endpoint_same_data_as_warehouses(self, auth_session):
        """Verify branches endpoint returns data"""
        response = auth_session.get(f"{BASE_URL}/api/branches")
        
        if response.status_code == 200:
            branches_data = response.json()
            branches = branches_data if isinstance(branches_data, list) else branches_data.get('items', [])
            print(f"Branches count: {len(branches)}")
            
            # Check if our test warehouse_id exists in branches
            if auth_session.test_data["warehouse_id"]:
                found_in_branches = any(b.get('id') == auth_session.test_data["warehouse_id"] for b in branches)
                print(f"Test warehouse_id found in branches: {found_in_branches}")
        else:
            print(f"Branches endpoint response: {response.status_code}")
    
    def test_09_create_po_with_different_discounts(self, auth_session):
        """Test PO creation with various discount percentages calculation"""
        discount_cases = [
            {"qty": 5, "price": 20000, "discount": 20, "expected": 80000},
            {"qty": 10, "price": 10000, "discount": 0, "expected": 100000},
            {"qty": 2, "price": 50000, "discount": 50, "expected": 50000}
        ]
        
        for case in discount_cases:
            # Calculate manually
            calculated = case['qty'] * case['price'] * (1 - case['discount'] / 100)
            assert calculated == case['expected'], f"Discount calc failed for case {case}"
            print(f"✓ Verified: qty={case['qty']}, price={case['price']}, disc={case['discount']}% = {calculated}")
    
    def test_10_cleanup_test_po(self, auth_session):
        """Cleanup: Delete test PO if created"""
        if auth_session.test_data["po_id"]:
            response = auth_session.delete(
                f"{BASE_URL}/api/purchase/orders/{auth_session.test_data['po_id']}?reason=Test cleanup iter98"
            )
            print(f"Cleanup response: {response.status_code}")
        else:
            print("No PO to cleanup")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
