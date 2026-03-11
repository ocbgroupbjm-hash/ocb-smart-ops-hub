"""
OCB TITAN ERP - Phase 3 Test Suite
Module: Purchase Planning Engine & Sales Target System
Testing:
- Purchase Planning - Generate, List, Dashboard, Status, Create PO
- Sales Target - CRUD, Dashboard, Leaderboard
"""

import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    BASE_URL = "https://smart-ops-hub-6.preview.emergentagent.com"

# Test credentials
TEST_EMAIL = "ocbgroupbjm@gmail.com"
TEST_PASSWORD = "admin123"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for owner account"""
    # First select the OCB business
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    
    # Switch to OCB TITAN database
    switch_res = session.post(f"{BASE_URL}/api/business/switch/ocb_titan")
    print(f"Business switch status: {switch_res.status_code}")
    
    # Login
    login_res = session.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    
    if login_res.status_code != 200:
        pytest.skip(f"Authentication failed: {login_res.text}")
    
    data = login_res.json()
    token = data.get("token") or data.get("access_token")
    print(f"Login successful for: {data.get('user', {}).get('name', 'Unknown')}")
    return token


@pytest.fixture(scope="module")
def api_client(auth_token):
    """Authenticated API client"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    })
    return session


# ==================== PURCHASE PLANNING TESTS ====================

class TestPurchasePlanningGenerate:
    """Purchase Planning - Generate endpoint tests"""
    
    def test_generate_planning(self, api_client):
        """Test POST /api/purchase-planning/generate"""
        response = api_client.post(f"{BASE_URL}/api/purchase-planning/generate", json={
            "include_all_low_stock": True
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True
        assert "generated" in data
        assert "skipped" in data
        assert "items" in data
        print(f"Generated: {data['generated']}, Skipped: {data['skipped']}")


class TestPurchasePlanningList:
    """Purchase Planning - List endpoint tests"""
    
    def test_list_planning_items(self, api_client):
        """Test GET /api/purchase-planning/list"""
        response = api_client.get(f"{BASE_URL}/api/purchase-planning/list")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "items" in data
        assert "summary" in data
        
        # Check summary structure
        summary = data["summary"]
        assert "total" in summary
        assert "draft" in summary
        print(f"Total items: {summary.get('total', 0)}, Draft: {summary.get('draft', 0)}")
    
    def test_list_with_status_filter(self, api_client):
        """Test filtering by status"""
        response = api_client.get(f"{BASE_URL}/api/purchase-planning/list?status=draft")
        
        assert response.status_code == 200
        data = response.json()
        
        # All items should be draft
        for item in data.get("items", []):
            if "status" in item:
                assert item["status"] == "draft", f"Expected draft status, got {item['status']}"
    
    def test_list_with_urgency_filter(self, api_client):
        """Test filtering by urgency"""
        response = api_client.get(f"{BASE_URL}/api/purchase-planning/list?urgency=critical")
        
        assert response.status_code == 200


class TestPurchasePlanningDashboard:
    """Purchase Planning - Dashboard endpoint tests"""
    
    def test_get_dashboard_summary(self, api_client):
        """Test GET /api/purchase-planning/dashboard/summary"""
        response = api_client.get(f"{BASE_URL}/api/purchase-planning/dashboard/summary")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Dashboard should have status and urgency breakdowns
        assert "by_status" in data or "total_pending" in data
        print(f"Dashboard data: {data}")


class TestPurchasePlanningStatus:
    """Purchase Planning - Status update tests"""
    
    def test_status_workflow(self, api_client):
        """Test status transitions: draft -> reviewed -> approved"""
        # First get a draft item
        list_res = api_client.get(f"{BASE_URL}/api/purchase-planning/list?status=draft&limit=1")
        assert list_res.status_code == 200
        
        items = list_res.json().get("items", [])
        if not items:
            pytest.skip("No draft planning items to test status workflow")
        
        planning_id = items[0]["id"]
        
        # Update to reviewed
        review_res = api_client.post(f"{BASE_URL}/api/purchase-planning/{planning_id}/status", json={
            "status": "reviewed",
            "notes": "Test review"
        })
        
        assert review_res.status_code == 200, f"Review failed: {review_res.text}"
        review_data = review_res.json()
        assert review_data.get("success") == True
        assert review_data.get("new_status") == "reviewed"
        
        # Update to approved
        approve_res = api_client.post(f"{BASE_URL}/api/purchase-planning/{planning_id}/status", json={
            "status": "approved",
            "notes": "Test approve"
        })
        
        assert approve_res.status_code == 200, f"Approve failed: {approve_res.text}"
        approve_data = approve_res.json()
        assert approve_data.get("success") == True
        assert approve_data.get("new_status") == "approved"
        
        print(f"Successfully transitioned planning {planning_id} from draft -> reviewed -> approved")
    
    def test_invalid_status_transition(self, api_client):
        """Test that invalid status transitions are rejected"""
        # Get a draft item
        list_res = api_client.get(f"{BASE_URL}/api/purchase-planning/list?status=draft&limit=1")
        items = list_res.json().get("items", [])
        
        if not items:
            pytest.skip("No draft items for invalid transition test")
        
        planning_id = items[0]["id"]
        
        # Try to go directly from draft to approved (invalid)
        response = api_client.post(f"{BASE_URL}/api/purchase-planning/{planning_id}/status", json={
            "status": "approved",
            "notes": "Direct to approved"
        })
        
        # Should be rejected with 400
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"


class TestPurchasePlanningCreatePO:
    """Purchase Planning - Create PO from approved items"""
    
    def test_create_po_from_approved(self, api_client):
        """Test POST /api/purchase-planning/create-po"""
        # Get approved items
        list_res = api_client.get(f"{BASE_URL}/api/purchase-planning/list?status=approved")
        assert list_res.status_code == 200
        
        items = list_res.json().get("items", [])
        if not items:
            pytest.skip("No approved planning items to create PO")
        
        # Get IDs of approved items
        planning_ids = [item["id"] for item in items[:3]]  # Max 3 items
        
        response = api_client.post(f"{BASE_URL}/api/purchase-planning/create-po", json={
            "planning_ids": planning_ids
        })
        
        assert response.status_code == 200, f"Create PO failed: {response.text}"
        
        data = response.json()
        assert data.get("success") == True
        assert "created_pos" in data
        print(f"Created {data.get('created_pos', 0)} PO drafts")
    
    def test_create_po_empty_ids(self, api_client):
        """Test that empty planning IDs returns error"""
        response = api_client.post(f"{BASE_URL}/api/purchase-planning/create-po", json={
            "planning_ids": []
        })
        
        # Should fail with 400 or return success with 0 POs
        data = response.json()
        if response.status_code == 400:
            assert "detail" in data
        else:
            # If 200, should have created 0 POs
            assert data.get("created_pos", 0) == 0 or "tidak ada" in data.get("message", "").lower()


# ==================== SALES TARGET TESTS ====================

class TestSalesTargetDashboard:
    """Sales Target - Dashboard endpoint tests (MUST work after route fix)"""
    
    def test_get_dashboard_summary(self, api_client):
        """Test GET /api/sales-target/dashboard/summary"""
        response = api_client.get(f"{BASE_URL}/api/sales-target/dashboard/summary?period_type=monthly")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "period_type" in data
        assert "total_target" in data
        assert "total_actual" in data
        assert "overall_achievement" in data
        print(f"Dashboard: Target={data.get('total_target', 0)}, Actual={data.get('total_actual', 0)}, Achievement={data.get('overall_achievement', 0)}%")


class TestSalesTargetLeaderboard:
    """Sales Target - Leaderboard endpoint tests (CRITICAL - was 404 before fix)"""
    
    def test_get_leaderboard(self, api_client):
        """Test GET /api/sales-target/leaderboard - This was returning 404 before fix"""
        response = api_client.get(f"{BASE_URL}/api/sales-target/leaderboard?period_type=monthly")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "items" in data
        assert "total" in data
        print(f"Leaderboard: {data.get('total', 0)} salesmen")
        
        # Check item structure if there are items
        for item in data.get("items", [])[:1]:
            assert "rank" in item
            assert "salesman_name" in item
            assert "achievement_percent" in item


class TestSalesTargetList:
    """Sales Target - List endpoint tests"""
    
    def test_list_targets(self, api_client):
        """Test GET /api/sales-target/list"""
        response = api_client.get(f"{BASE_URL}/api/sales-target/list")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "items" in data
        assert "summary" in data
        
        print(f"Total targets: {data['summary'].get('total', 0)}")
    
    def test_list_with_filters(self, api_client):
        """Test list with type and period filters"""
        response = api_client.get(f"{BASE_URL}/api/sales-target/list?target_type=branch&period_type=monthly")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check all items match filter
        for item in data.get("items", []):
            if "target_type" in item:
                assert item["target_type"] == "branch"


class TestSalesTargetCreate:
    """Sales Target - Create endpoint tests"""
    
    def test_create_target(self, api_client):
        """Test POST /api/sales-target"""
        # Get a branch to create target for
        branch_res = api_client.get(f"{BASE_URL}/api/branches")
        branches = branch_res.json() if branch_res.status_code == 200 else []
        if isinstance(branches, dict):
            branches = branches.get("items", [])
        
        if not branches:
            pytest.skip("No branches available to create target")
        
        branch = branches[0]
        
        # Calculate period dates
        today = datetime.now()
        period_start = today.replace(day=1).strftime("%Y-%m-%d")
        # End of month
        next_month = today.replace(day=28) + timedelta(days=4)
        period_end = (next_month - timedelta(days=next_month.day)).strftime("%Y-%m-%d")
        
        response = api_client.post(f"{BASE_URL}/api/sales-target", json={
            "target_type": "branch",
            "target_ref_id": branch["id"],
            "target_ref_name": branch.get("name", "Test Branch"),
            "period_type": "monthly",
            "period_start": period_start,
            "period_end": period_end,
            "target_value": 100000000,  # 100jt
            "notes": "Test target from pytest"
        })
        
        # Could be 200 or 400 if duplicate exists
        if response.status_code == 200:
            data = response.json()
            assert data.get("success") == True
            assert "target_id" in data
            print(f"Created target: {data.get('target_id')}")
            return data.get("target_id")
        elif response.status_code == 400:
            # Duplicate - this is OK
            print("Target already exists for this period")
        else:
            pytest.fail(f"Unexpected status: {response.status_code}: {response.text}")
    
    def test_create_target_validation(self, api_client):
        """Test validation - target_value must be > 0"""
        response = api_client.post(f"{BASE_URL}/api/sales-target", json={
            "target_type": "branch",
            "target_ref_id": "test-123",
            "period_type": "monthly",
            "period_start": "2026-01-01",
            "period_end": "2026-01-31",
            "target_value": 0  # Invalid - must be > 0
        })
        
        # Should fail validation
        assert response.status_code == 422, f"Expected 422 for invalid target_value, got {response.status_code}"


class TestSalesTargetDelete:
    """Sales Target - Delete endpoint tests"""
    
    def test_delete_target(self, api_client):
        """Test DELETE /api/sales-target/{id}"""
        # First get list of targets
        list_res = api_client.get(f"{BASE_URL}/api/sales-target/list")
        targets = list_res.json().get("items", [])
        
        if not targets:
            pytest.skip("No targets to delete")
        
        # Find a target that we can delete (test one)
        target_to_delete = None
        for t in targets:
            if "pytest" in t.get("notes", "").lower() or "test" in t.get("notes", "").lower():
                target_to_delete = t
                break
        
        if not target_to_delete:
            # Use the first one but skip if we shouldn't delete it
            pytest.skip("No test targets to delete")
        
        target_id = target_to_delete["id"]
        
        response = api_client.delete(f"{BASE_URL}/api/sales-target/{target_id}")
        
        assert response.status_code == 200, f"Delete failed: {response.text}"
        data = response.json()
        assert data.get("success") == True
        print(f"Deleted target: {target_id}")


class TestSalesTargetGetById:
    """Sales Target - Get by ID tests"""
    
    def test_get_target_by_id(self, api_client):
        """Test GET /api/sales-target/{id}"""
        # First get list
        list_res = api_client.get(f"{BASE_URL}/api/sales-target/list?limit=1")
        targets = list_res.json().get("items", [])
        
        if not targets:
            pytest.skip("No targets to get by ID")
        
        target_id = targets[0]["id"]
        
        response = api_client.get(f"{BASE_URL}/api/sales-target/{target_id}")
        
        assert response.status_code == 200, f"Get by ID failed: {response.text}"
        
        data = response.json()
        assert data.get("id") == target_id
        assert "target_value" in data
        assert "actual_value" in data  # Should be enriched
        assert "achievement_percent" in data
    
    def test_get_nonexistent_target(self, api_client):
        """Test 404 for nonexistent target"""
        response = api_client.get(f"{BASE_URL}/api/sales-target/nonexistent-id-12345")
        
        assert response.status_code == 404


# ==================== INTEGRATION TESTS ====================

class TestIntegration:
    """Integration tests for both modules"""
    
    def test_purchase_planning_full_flow(self, api_client):
        """Test full flow: generate -> list -> check item"""
        # Generate
        gen_res = api_client.post(f"{BASE_URL}/api/purchase-planning/generate", json={
            "include_all_low_stock": True
        })
        assert gen_res.status_code == 200
        
        # List
        list_res = api_client.get(f"{BASE_URL}/api/purchase-planning/list")
        assert list_res.status_code == 200
        
        items = list_res.json().get("items", [])
        if items:
            # Get detail
            item_id = items[0]["id"]
            detail_res = api_client.get(f"{BASE_URL}/api/purchase-planning/{item_id}")
            assert detail_res.status_code == 200
            
            detail = detail_res.json()
            assert detail.get("id") == item_id
            assert "product_name" in detail
    
    def test_sales_target_endpoints_after_fix(self, api_client):
        """Verify all sales target endpoints work after route ordering fix"""
        # List should work
        list_res = api_client.get(f"{BASE_URL}/api/sales-target/list")
        assert list_res.status_code == 200, "List endpoint failed"
        
        # Dashboard should work (was 404 before fix)
        dash_res = api_client.get(f"{BASE_URL}/api/sales-target/dashboard/summary")
        assert dash_res.status_code == 200, "Dashboard endpoint failed (was 404 before fix)"
        
        # Leaderboard should work (was 404 before fix)
        leader_res = api_client.get(f"{BASE_URL}/api/sales-target/leaderboard")
        assert leader_res.status_code == 200, "Leaderboard endpoint failed (was 404 before fix)"
        
        print("All sales target endpoints working correctly after route ordering fix!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
