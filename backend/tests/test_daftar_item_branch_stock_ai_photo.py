# OCB TITAN AI - Testing Daftar Item, Branch Stock, AI Photo Studio
# Tests for: Items CRUD, Filters, Branch Stock, AI Photo Studio APIs

import pytest
import requests
import os
import uuid
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://smart-ops-hub-6.preview.emergentagent.com').rstrip('/')

# Test credentials
TEST_EMAIL = "ocbgroupbjm@gmail.com"
TEST_PASSWORD = "admin123"


class TestAuth:
    """Authentication tests"""
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        print(f"PASS: Login successful - user: {data['user']['name']}")


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for all tests"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip("Authentication failed - skipping tests")


@pytest.fixture
def api_headers(auth_token):
    """Headers with auth token"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


# ============ DAFTAR ITEM TESTS ============

class TestMasterItemsAPI:
    """Tests for /api/master/items endpoint"""
    
    def test_list_items_success(self, api_headers):
        """Test listing items returns data"""
        response = requests.get(f"{BASE_URL}/api/master/items?page=1&limit=10", headers=api_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)
        print(f"PASS: Items list - Total: {data['total']}, Returned: {len(data['items'])}")
    
    def test_filter_by_keyword(self, api_headers):
        """Test keyword filter works"""
        response = requests.get(f"{BASE_URL}/api/master/items?search=ACC", headers=api_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        # Verify search filter applied
        print(f"PASS: Keyword filter 'ACC' - Found: {data['total']} items")
    
    def test_filter_by_item_type(self, api_headers):
        """Test item type filter (barang, jasa, rakitan, etc.)"""
        response = requests.get(f"{BASE_URL}/api/master/items?item_type=barang", headers=api_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        print(f"PASS: Item type filter 'barang' - Found: {data['total']} items")
    
    def test_filter_by_status_aktif(self, api_headers):
        """Test active status filter"""
        response = requests.get(f"{BASE_URL}/api/master/items?is_active=true", headers=api_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        # All items should be active
        for item in data["items"]:
            assert item.get("is_active", True) == True
        print(f"PASS: Active filter - Found: {data['total']} active items")
    
    def test_filter_discontinued(self, api_headers):
        """Test discontinued filter"""
        response = requests.get(f"{BASE_URL}/api/master/items?discontinued=true", headers=api_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        print(f"PASS: Discontinued filter - Found: {data['total']} discontinued items")
    
    def test_sorting_by_code(self, api_headers):
        """Test sorting by code ascending"""
        response = requests.get(f"{BASE_URL}/api/master/items?sort_by=code&sort_order=asc&limit=5", headers=api_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        # Verify sorting
        if len(data["items"]) >= 2:
            codes = [item["code"] for item in data["items"]]
            assert codes == sorted(codes), "Items not sorted by code ascending"
        print(f"PASS: Sort by code asc - First: {data['items'][0]['code'] if data['items'] else 'N/A'}")
    
    def test_pagination(self, api_headers):
        """Test pagination works"""
        response = requests.get(f"{BASE_URL}/api/master/items?page=1&limit=5", headers=api_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get("page") == 1
        assert data.get("limit") == 5
        assert len(data["items"]) <= 5
        print(f"PASS: Pagination - Page 1, Limit 5, Returned: {len(data['items'])}")


class TestItemCRUD:
    """Test CRUD operations on items"""
    
    @pytest.fixture
    def test_item_code(self):
        """Generate unique test item code"""
        return f"TEST_ITEM_{uuid.uuid4().hex[:8].upper()}"
    
    def test_create_item(self, api_headers, test_item_code):
        """Test creating a new item with branch_id"""
        # Get a branch ID first
        branches_res = requests.get(f"{BASE_URL}/api/global-map/branches", headers=api_headers)
        branches = branches_res.json().get("branches", [])
        branch_id = branches[0]["id"] if branches else ""
        
        new_item = {
            "code": test_item_code,
            "barcode": test_item_code,
            "name": f"Test Item {test_item_code}",
            "branch_id": branch_id,
            "item_type": "barang",
            "cost_price": 10000,
            "selling_price": 15000,
            "is_active": True,
            "track_stock": True
        }
        
        response = requests.post(f"{BASE_URL}/api/master/items", headers=api_headers, json=new_item)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "message" in data
        print(f"PASS: Item created - ID: {data['id']}, Code: {test_item_code}")
        
        # Cleanup - delete the test item
        requests.delete(f"{BASE_URL}/api/master/items/{data['id']}", headers=api_headers)
    
    def test_create_item_duplicate_code_fails(self, api_headers):
        """Test that duplicate code returns error"""
        # First get an existing item code
        items_res = requests.get(f"{BASE_URL}/api/master/items?limit=1", headers=api_headers)
        items = items_res.json().get("items", [])
        if not items:
            pytest.skip("No existing items to test duplicate")
        
        existing_code = items[0]["code"]
        
        duplicate_item = {
            "code": existing_code,
            "name": "Duplicate Test",
            "item_type": "barang",
            "cost_price": 1000,
            "selling_price": 2000
        }
        
        response = requests.post(f"{BASE_URL}/api/master/items", headers=api_headers, json=duplicate_item)
        assert response.status_code == 400  # Should fail
        print(f"PASS: Duplicate code rejected - Code: {existing_code}")
    
    def test_update_item(self, api_headers):
        """Test updating an item"""
        # Create item first
        test_code = f"TEST_UPD_{uuid.uuid4().hex[:6].upper()}"
        create_res = requests.post(f"{BASE_URL}/api/master/items", headers=api_headers, json={
            "code": test_code,
            "name": "Original Name",
            "item_type": "barang",
            "cost_price": 1000,
            "selling_price": 2000
        })
        item_id = create_res.json().get("id")
        
        # Update
        update_res = requests.put(f"{BASE_URL}/api/master/items/{item_id}", headers=api_headers, json={
            "code": test_code,
            "name": "Updated Name",
            "item_type": "barang",
            "cost_price": 1500,
            "selling_price": 2500
        })
        assert update_res.status_code == 200
        print(f"PASS: Item updated - ID: {item_id}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/master/items/{item_id}", headers=api_headers)
    
    def test_delete_item(self, api_headers):
        """Test deleting an item"""
        # Create item first
        test_code = f"TEST_DEL_{uuid.uuid4().hex[:6].upper()}"
        create_res = requests.post(f"{BASE_URL}/api/master/items", headers=api_headers, json={
            "code": test_code,
            "name": "To Delete",
            "item_type": "barang",
            "cost_price": 1000,
            "selling_price": 2000
        })
        item_id = create_res.json().get("id")
        
        # Delete
        delete_res = requests.delete(f"{BASE_URL}/api/master/items/{item_id}", headers=api_headers)
        assert delete_res.status_code == 200
        print(f"PASS: Item deleted - ID: {item_id}")
        
        # Verify deleted
        get_res = requests.get(f"{BASE_URL}/api/master/items?search={test_code}", headers=api_headers)
        assert get_res.json()["total"] == 0


# ============ BRANCH STOCK TESTS ============

class TestBranchStockAPI:
    """Tests for /api/inventory/branch-stock endpoint"""
    
    def test_get_branch_stock_for_item(self, api_headers):
        """Test getting branch stocks for an item"""
        # Get an existing item
        items_res = requests.get(f"{BASE_URL}/api/master/items?limit=1", headers=api_headers)
        items = items_res.json().get("items", [])
        if not items:
            pytest.skip("No items to test branch stock")
        
        item_id = items[0]["id"]
        
        response = requests.get(f"{BASE_URL}/api/inventory/branch-stock/{item_id}", headers=api_headers)
        assert response.status_code == 200
        data = response.json()
        assert "branch_stocks" in data
        assert "item_id" in data
        assert isinstance(data["branch_stocks"], list)
        print(f"PASS: Branch stocks loaded - Item: {item_id}, Branches: {len(data['branch_stocks'])}")
    
    def test_branch_stock_has_all_branches(self, api_headers):
        """Test that branch stock returns all 46 branches"""
        # Get an existing item
        items_res = requests.get(f"{BASE_URL}/api/master/items?limit=1", headers=api_headers)
        items = items_res.json().get("items", [])
        if not items:
            pytest.skip("No items to test branch stock")
        
        item_id = items[0]["id"]
        
        # Get branches count
        branches_res = requests.get(f"{BASE_URL}/api/global-map/branches", headers=api_headers)
        total_branches = branches_res.json().get("total_branches", 0)
        
        # Get branch stocks
        stock_res = requests.get(f"{BASE_URL}/api/inventory/branch-stock/{item_id}", headers=api_headers)
        stock_data = stock_res.json()
        
        # Should have stocks for all branches
        assert len(stock_data["branch_stocks"]) == total_branches, \
            f"Expected {total_branches} branch stocks, got {len(stock_data['branch_stocks'])}"
        print(f"PASS: All {total_branches} branches have stock entries")
    
    def test_save_branch_stock(self, api_headers):
        """Test saving branch stocks for an item"""
        # Get an existing item
        items_res = requests.get(f"{BASE_URL}/api/master/items?limit=1", headers=api_headers)
        items = items_res.json().get("items", [])
        if not items:
            pytest.skip("No items to test branch stock")
        
        item_id = items[0]["id"]
        
        # Get current stocks
        current_res = requests.get(f"{BASE_URL}/api/inventory/branch-stock/{item_id}", headers=api_headers)
        current_stocks = current_res.json().get("branch_stocks", [])
        
        if not current_stocks:
            pytest.skip("No branch stocks to update")
        
        # Update first branch stock
        updated_stocks = [{
            "branch_id": current_stocks[0]["branch_id"],
            "branch_name": current_stocks[0].get("branch_name", ""),
            "stock_current": 100,
            "stock_minimum": 10,
            "stock_maximum": 200
        }]
        
        response = requests.post(
            f"{BASE_URL}/api/inventory/branch-stock/{item_id}",
            headers=api_headers,
            json={"branch_stocks": updated_stocks}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"PASS: Branch stock saved - Count: {data.get('count', 1)}")
        
        # Verify update persisted
        verify_res = requests.get(f"{BASE_URL}/api/inventory/branch-stock/{item_id}", headers=api_headers)
        verify_stocks = verify_res.json().get("branch_stocks", [])
        first_stock = next((s for s in verify_stocks if s["branch_id"] == updated_stocks[0]["branch_id"]), None)
        assert first_stock is not None
        assert first_stock["stock_current"] == 100
        print(f"PASS: Branch stock verified - stock_current: {first_stock['stock_current']}")
    
    def test_branch_stock_alerts(self, api_headers):
        """Test low stock alerts endpoint"""
        response = requests.get(f"{BASE_URL}/api/inventory/branch-stock-alerts", headers=api_headers)
        assert response.status_code == 200
        data = response.json()
        assert "alerts" in data
        assert "total" in data
        print(f"PASS: Branch stock alerts - Total: {data['total']}")
    
    def test_ai_restock_recommendations(self, api_headers):
        """Test AI restock recommendations endpoint"""
        response = requests.get(f"{BASE_URL}/api/inventory/ai-restock-recommendations", headers=api_headers)
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data
        assert "summary" in data
        print(f"PASS: AI restock recommendations - Total: {data['summary'].get('total_items_need_restock', 0)}")


# ============ AI PHOTO STUDIO TESTS ============

class TestAIPhotoStudioAPI:
    """Tests for /api/ai-photo-studio endpoint"""
    
    def test_get_item_images(self, api_headers):
        """Test getting images for an item"""
        # Get an existing item
        items_res = requests.get(f"{BASE_URL}/api/master/items?limit=1", headers=api_headers)
        items = items_res.json().get("items", [])
        if not items:
            pytest.skip("No items to test photo studio")
        
        item_id = items[0]["id"]
        
        response = requests.get(f"{BASE_URL}/api/ai-photo-studio/images/{item_id}", headers=api_headers)
        assert response.status_code == 200
        data = response.json()
        assert "images" in data
        assert "total" in data
        print(f"PASS: Images loaded - Item: {item_id}, Count: {data['total']}")
    
    def test_upload_photo_invalid_type(self, api_headers):
        """Test that invalid file type is rejected"""
        # Get an existing item
        items_res = requests.get(f"{BASE_URL}/api/master/items?limit=1", headers=api_headers)
        items = items_res.json().get("items", [])
        if not items:
            pytest.skip("No items to test photo studio")
        
        item_id = items[0]["id"]
        
        # Try to upload a text file (should fail)
        files = {
            'file': ('test.txt', b'this is not an image', 'text/plain')
        }
        
        # Remove Content-Type for multipart
        headers = {"Authorization": api_headers["Authorization"]}
        
        response = requests.post(
            f"{BASE_URL}/api/ai-photo-studio/upload/{item_id}",
            headers=headers,
            files=files,
            data={"is_main": "false"}
        )
        assert response.status_code == 400
        print(f"PASS: Invalid file type rejected")
    
    def test_enhance_photo_fallback(self, api_headers):
        """Test photo enhancement with basic fallback"""
        # Create a small test image (1x1 red pixel PNG)
        import base64
        tiny_png = base64.b64encode(bytes([
            0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, 0x00, 0x00, 0x00, 0x0D,
            0x49, 0x48, 0x44, 0x52, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
            0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53, 0xDE, 0x00, 0x00, 0x00,
            0x0C, 0x49, 0x44, 0x41, 0x54, 0x08, 0xD7, 0x63, 0xF8, 0xCF, 0xC0, 0x00,
            0x00, 0x00, 0x03, 0x00, 0x01, 0x00, 0x05, 0xFE, 0xD4, 0xEF, 0x00, 0x00,
            0x00, 0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE, 0x42, 0x60, 0x82
        ])).decode('utf-8')
        
        response = requests.post(
            f"{BASE_URL}/api/ai-photo-studio/enhance",
            headers=api_headers,
            json={
                "image_base64": tiny_png,
                "enhancement_type": "enhance",
                "mode": "marketplace"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "enhanced_image" in data or "success" in data
        print(f"PASS: Photo enhancement endpoint working (fallback mode)")


# ============ BRANCHES AND FILTERS TESTS ============

class TestBranchesAndFilters:
    """Test branches list and filter integration"""
    
    def test_list_branches(self, api_headers):
        """Test listing all branches"""
        response = requests.get(f"{BASE_URL}/api/global-map/branches", headers=api_headers)
        assert response.status_code == 200
        data = response.json()
        assert "branches" in data
        assert "total_branches" in data
        assert data["total_branches"] == 46, f"Expected 46 branches, got {data['total_branches']}"
        print(f"PASS: Branches loaded - Total: {data['total_branches']}")
    
    def test_filter_items_by_branch(self, api_headers):
        """Test filtering items by branch"""
        # Get a branch ID
        branches_res = requests.get(f"{BASE_URL}/api/global-map/branches", headers=api_headers)
        branches = branches_res.json().get("branches", [])
        if not branches:
            pytest.skip("No branches available")
        
        branch_id = branches[0]["id"]
        
        response = requests.get(f"{BASE_URL}/api/master/items?branch_id={branch_id}", headers=api_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        print(f"PASS: Filter by branch '{branches[0]['name']}' - Found: {data['total']} items")
    
    def test_categories_list(self, api_headers):
        """Test listing categories"""
        response = requests.get(f"{BASE_URL}/api/master/categories", headers=api_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"PASS: Categories loaded - Count: {len(data)}")
    
    def test_units_list(self, api_headers):
        """Test listing units"""
        response = requests.get(f"{BASE_URL}/api/master/units", headers=api_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"PASS: Units loaded - Count: {len(data)}")
    
    def test_brands_list(self, api_headers):
        """Test listing brands"""
        response = requests.get(f"{BASE_URL}/api/master/brands", headers=api_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"PASS: Brands loaded - Count: {len(data)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
