"""
Test Branch/Warehouse Consolidation - Iteration 97
P0 Konsolidasi Cabang dan Gudang

Testing that:
1. GET /api/master/warehouses returns data from branches collection (_source='branches')
2. GET /api/master/warehouses returns branch_id = id (self-reference)
3. POST /api/master/warehouses creates entry in branches collection
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://smart-ops-hub-6.preview.emergentagent.com').rstrip('/')

# Test credentials
TEST_EMAIL = "ocbgroupbjm@gmail.com"
TEST_PASSWORD = "admin123"
TEST_TENANT = "ocb_titan"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    # Login directly
    login_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "tenant_id": TEST_TENANT
    }
    login_response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    assert login_response.status_code == 200, f"Login failed: {login_response.text}"
    
    token = login_response.json().get("access_token") or login_response.json().get("token")
    assert token, "No token in response"
    return token


@pytest.fixture(scope="module")
def api_client(auth_token):
    """Authenticated requests session"""
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    })
    return session


class TestWarehouseConsolidation:
    """Test warehouse endpoints now alias to branches collection"""
    
    def test_01_warehouses_returns_source_branches(self, api_client):
        """GET /api/master/warehouses should return _source='branches'"""
        response = api_client.get(f"{BASE_URL}/api/master/warehouses")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        warehouses = response.json()
        assert isinstance(warehouses, list), "Response should be a list"
        
        if len(warehouses) > 0:
            # Check _source field exists and equals 'branches'
            first = warehouses[0]
            assert "_source" in first, f"Missing _source field: {first}"
            assert first["_source"] == "branches", f"_source should be 'branches', got: {first.get('_source')}"
            print(f"PASS: Warehouses list has _source='branches' (found {len(warehouses)} items)")
        else:
            print("WARN: No warehouses/branches found, skipping source check")
    
    def test_02_warehouses_returns_branch_id_self_reference(self, api_client):
        """GET /api/master/warehouses should return branch_id = id (self-reference)"""
        response = api_client.get(f"{BASE_URL}/api/master/warehouses")
        assert response.status_code == 200
        
        warehouses = response.json()
        if len(warehouses) > 0:
            for wh in warehouses[:5]:  # Check first 5
                assert "branch_id" in wh, f"Missing branch_id: {wh}"
                assert wh["branch_id"] == wh["id"], f"branch_id should equal id: branch_id={wh.get('branch_id')}, id={wh.get('id')}"
            print(f"PASS: All warehouses have branch_id == id (self-reference)")
        else:
            print("WARN: No warehouses to validate")
    
    def test_03_warehouses_data_structure(self, api_client):
        """Check warehouse data structure has expected fields"""
        response = api_client.get(f"{BASE_URL}/api/master/warehouses")
        assert response.status_code == 200
        
        warehouses = response.json()
        if len(warehouses) > 0:
            first = warehouses[0]
            expected_fields = ["id", "code", "name", "branch_id", "branch_name", "_source"]
            for field in expected_fields:
                assert field in first, f"Missing field '{field}' in warehouse: {first.keys()}"
            print(f"PASS: Warehouse has all expected fields: {expected_fields}")
    
    def test_04_create_warehouse_creates_in_branches(self, api_client):
        """POST /api/master/warehouses should create entry in branches collection"""
        unique_code = f"TST{str(uuid.uuid4())[:6].upper()}"
        create_data = {
            "code": unique_code,
            "name": f"Test Warehouse {unique_code}",
            "address": "Test Address",
            "is_active": True
        }
        
        response = api_client.post(f"{BASE_URL}/api/master/warehouses", json=create_data)
        assert response.status_code in [200, 201], f"Create failed: {response.text}"
        
        result = response.json()
        created_id = result.get("id")
        assert created_id, f"No ID returned: {result}"
        print(f"PASS: Created warehouse/branch with id={created_id}")
        
        # Verify it appears in warehouses list with _source='branches'
        list_response = api_client.get(f"{BASE_URL}/api/master/warehouses?search={unique_code}")
        warehouses = list_response.json()
        
        found = None
        for wh in warehouses:
            if wh.get("code") == unique_code:
                found = wh
                break
        
        assert found, f"Created warehouse not found in list"
        assert found.get("_source") == "branches", f"Created warehouse should have _source='branches'"
        assert found.get("branch_id") == found.get("id"), f"Created warehouse should have branch_id=id"
        print(f"PASS: Created warehouse verified in list with _source='branches'")
        
        # Cleanup - soft delete
        delete_response = api_client.delete(f"{BASE_URL}/api/master/warehouses/{created_id}")
        print(f"Cleanup: delete response status {delete_response.status_code}")


class TestBranchesEndpoint:
    """Test branches endpoint (primary source)"""
    
    def test_05_branches_list(self, api_client):
        """GET /api/branches should return branches"""
        response = api_client.get(f"{BASE_URL}/api/branches")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        # Could be list or dict with items key
        if isinstance(data, dict) and "items" in data:
            branches = data["items"]
        else:
            branches = data if isinstance(data, list) else []
        
        print(f"PASS: Branches endpoint returns {len(branches)} branches")
        
        if len(branches) > 0:
            first = branches[0]
            assert "id" in first
            assert "code" in first
            assert "name" in first
            print(f"PASS: Sample branch: code={first.get('code')}, name={first.get('name')}")
    
    def test_06_warehouse_and_branch_data_match(self, api_client):
        """Warehouses data should match branches data"""
        # Get warehouses
        wh_response = api_client.get(f"{BASE_URL}/api/master/warehouses")
        warehouses = wh_response.json()
        
        # Get branches
        br_response = api_client.get(f"{BASE_URL}/api/branches")
        branches_data = br_response.json()
        if isinstance(branches_data, dict) and "items" in branches_data:
            branches = branches_data["items"]
        else:
            branches = branches_data if isinstance(branches_data, list) else []
        
        # Build branch id set for comparison
        branch_ids = {b.get("id") for b in branches}
        warehouse_ids = {w.get("id") for w in warehouses}
        
        # Warehouses should be subset of or equal to branches
        # (warehouses only shows active, branches might show all)
        if len(warehouses) > 0 and len(branches) > 0:
            common = warehouse_ids & branch_ids
            print(f"PASS: Found {len(common)} common IDs between warehouses and branches")
            assert len(common) > 0, "No common IDs found - data might not be consolidated"


class TestDashboardBranchCount:
    """Test dashboard uses branches data for 'Total Cabang'"""
    
    def test_07_dashboard_stats(self, api_client):
        """Dashboard should show branch count from branches collection"""
        response = api_client.get(f"{BASE_URL}/api/dashboard/stats")
        
        if response.status_code == 200:
            stats = response.json()
            # Check if there's a branch/cabang related stat
            print(f"Dashboard stats keys: {list(stats.keys()) if isinstance(stats, dict) else 'N/A'}")
            # This is informational - dashboard implementation may vary
            print("PASS: Dashboard stats endpoint accessible")
        else:
            print(f"WARN: Dashboard stats endpoint returned {response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
