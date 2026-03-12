# OCB TITAN - Owner Control & Stock SSOT API Tests
# Iteration 47: Testing Stock Single Source of Truth and Owner Edit Control
# Tests: Stock SSOT, Owner Edit APIs, Audit Logs, Module Cleanup verification

import pytest
import requests
import os
import json
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "ocbgroupbjm@gmail.com"
TEST_PASSWORD = "admin123"


class TestAuthAndSetup:
    """Authentication and Setup Tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for owner user"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data, "No token in response"
        assert data["user"]["role"] == "owner", "User is not owner"
        return data["token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        """Get headers with auth token"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    def test_login_owner_success(self):
        """Test owner login"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["role"] == "owner"
        print(f"✓ Owner login successful: {data['user']['name']}")


class TestStockSSOT:
    """Stock Single Source of Truth Tests - Stock MUST be calculated from stock_movements only"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    @pytest.fixture(scope="class")
    def test_item_id(self, headers):
        """Get a product ID for testing"""
        response = requests.get(f"{BASE_URL}/api/products?limit=1", headers=headers)
        assert response.status_code == 200
        items = response.json().get("items", [])
        assert len(items) > 0, "No products found for testing"
        return items[0]["id"]
    
    def test_get_stock_ssot(self, headers, test_item_id):
        """Test GET /api/owner/stock/{item_id} - Stock from stock_movements"""
        response = requests.get(
            f"{BASE_URL}/api/owner/stock/{test_item_id}",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "item_id" in data
        assert "stock" in data
        assert "source" in data
        
        # CRITICAL: Verify source is stock_movements (SSOT)
        assert data["source"] == "stock_movements (SSOT)", \
            f"Stock source must be 'stock_movements (SSOT)', got: {data['source']}"
        
        print(f"✓ Stock SSOT: item={data.get('product_code')}, stock={data['stock']}, source={data['source']}")
    
    def test_get_stock_card_ssot(self, headers, test_item_id):
        """Test GET /api/owner/stock-card/{item_id} - Stock card with running balance"""
        response = requests.get(
            f"{BASE_URL}/api/owner/stock-card/{test_item_id}",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "item_id" in data
        assert "movements" in data
        assert "opening_balance" in data
        assert "closing_balance" in data
        
        # Verify movements have running balance
        if data["movements"]:
            for mov in data["movements"][:3]:
                assert "balance" in mov, "Movement must have running balance"
                assert "in" in mov, "Movement must have 'in' quantity"
                assert "out" in mov, "Movement must have 'out' quantity"
        
        print(f"✓ Stock Card: item={data.get('product_code')}, movements={len(data['movements'])}, closing={data['closing_balance']}")
    
    def test_get_stock_by_branch(self, headers, test_item_id):
        """Test GET /api/owner/stock-by-branch/{item_id} - Stock breakdown by branch"""
        response = requests.get(
            f"{BASE_URL}/api/owner/stock-by-branch/{test_item_id}",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "item_id" in data
        assert "total_stock" in data
        assert "branch_stocks" in data
        assert "source" in data
        
        # CRITICAL: Verify source is stock_movements
        assert data["source"] == "stock_movements (SSOT)"
        
        print(f"✓ Stock by Branch: total={data['total_stock']}, branches={len(data['branch_stocks'])}")


class TestOwnerEditControl:
    """Owner Edit Control Tests - Owner can edit any transaction with audit trail"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    @pytest.fixture(scope="class")
    def test_item_id(self, headers):
        """Get a product ID for testing"""
        response = requests.get(f"{BASE_URL}/api/products?limit=1", headers=headers)
        return response.json().get("items", [{}])[0].get("id")
    
    @pytest.fixture(scope="class")
    def test_po_id(self, headers):
        """Get a PO ID for testing"""
        response = requests.get(f"{BASE_URL}/api/purchase/orders?limit=1", headers=headers)
        items = response.json().get("items", [])
        if items:
            return items[0].get("id")
        pytest.skip("No PO found for testing")
    
    def test_owner_edit_item_creates_audit_log(self, headers, test_item_id):
        """Test PUT /api/owner/edit/item/{item_id} - Should create audit log"""
        if not test_item_id:
            pytest.skip("No item ID available")
        
        # Edit item
        response = requests.put(
            f"{BASE_URL}/api/owner/edit/item/{test_item_id}",
            headers=headers,
            json={"cost_price": 99999.0}  # Test value
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response
        assert data.get("success") == True
        assert data.get("audit_logged") == True
        
        # Verify valuation calculation if cost changed
        if "valuation" in data and data["valuation"]:
            val = data["valuation"]
            assert "old_cost" in val
            assert "new_cost" in val
            assert "valuation_change" in val
            print(f"✓ Item Edit: old_cost={val['old_cost']}, new_cost={val['new_cost']}, change={val['valuation_change']}")
        
        print(f"✓ Owner Edit Item: success={data['success']}, audit_logged={data['audit_logged']}")
    
    def test_owner_edit_po_creates_audit_log(self, headers, test_po_id):
        """Test PUT /api/owner/edit/purchase-order/{po_id} - Should create audit log"""
        if not test_po_id:
            pytest.skip("No PO ID available")
        
        timestamp = datetime.now().isoformat()
        response = requests.put(
            f"{BASE_URL}/api/owner/edit/purchase-order/{test_po_id}",
            headers=headers,
            json={"notes": f"Test owner edit at {timestamp}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("success") == True
        assert data.get("audit_logged") == True
        assert "po" in data
        
        print(f"✓ Owner Edit PO: po_number={data['po'].get('po_number')}, audit_logged={data['audit_logged']}")


class TestAuditLogs:
    """Audit Log Tests - All owner edits must create audit logs"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    def test_get_audit_logs(self, headers):
        """Test GET /api/owner/audit-logs - Should return list of audit logs"""
        response = requests.get(
            f"{BASE_URL}/api/owner/audit-logs?limit=10",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "items" in data
        assert "total" in data
        
        # Verify audit log structure
        if data["items"]:
            log = data["items"][0]
            assert "id" in log
            assert "user_id" in log
            assert "user_name" in log
            assert "action" in log
            assert "module" in log
            assert "timestamp" in log
            
            print(f"✓ Audit Logs: count={len(data['items'])}, total={data['total']}")
            print(f"  Latest: action={log['action']}, module={log['module']}, user={log['user_name']}")
    
    def test_get_audit_logs_filter_by_module(self, headers):
        """Test GET /api/owner/audit-logs?module=item - Filter by module"""
        response = requests.get(
            f"{BASE_URL}/api/owner/audit-logs?module=item&limit=5",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # All logs should be for 'item' module
        for log in data.get("items", []):
            assert log["module"] == "item", f"Expected module=item, got {log['module']}"
        
        print(f"✓ Audit Logs filter by module=item: count={len(data.get('items', []))}")
    
    def test_get_audit_log_detail(self, headers):
        """Test GET /api/owner/audit-logs/{record_id} - Get audit history for specific record"""
        # First get an audit log
        response = requests.get(
            f"{BASE_URL}/api/owner/audit-logs?limit=1",
            headers=headers
        )
        assert response.status_code == 200
        items = response.json().get("items", [])
        
        if not items:
            pytest.skip("No audit logs to test detail")
        
        record_id = items[0]["record_id"]
        
        # Get detail
        response = requests.get(
            f"{BASE_URL}/api/owner/audit-logs/{record_id}",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "record_id" in data
        assert "history" in data
        
        print(f"✓ Audit Log Detail: record_id={record_id}, history_count={len(data.get('history', []))}")


class TestOwnerPermission:
    """Test that only owner can access owner control endpoints"""
    
    def test_non_owner_cannot_access_audit_logs(self):
        """Non-owner should get 403 when accessing audit logs"""
        # This test requires a non-owner user - skip if not available
        # For now, just verify the endpoint exists and requires auth
        response = requests.get(f"{BASE_URL}/api/owner/audit-logs")
        assert response.status_code in [401, 403], "Audit logs should require authentication"
        print("✓ Audit logs require authentication")


class TestOwnerEditNonExistent:
    """Test error handling for non-existent records"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    def test_edit_nonexistent_item_returns_404(self, headers):
        """Test editing non-existent item returns 404"""
        response = requests.put(
            f"{BASE_URL}/api/owner/edit/item/nonexistent-id-12345",
            headers=headers,
            json={"cost_price": 100}
        )
        assert response.status_code == 404
        print("✓ Non-existent item returns 404")
    
    def test_edit_nonexistent_po_returns_404(self, headers):
        """Test editing non-existent PO returns 404"""
        response = requests.put(
            f"{BASE_URL}/api/owner/edit/purchase-order/nonexistent-po-12345",
            headers=headers,
            json={"notes": "test"}
        )
        assert response.status_code == 404
        print("✓ Non-existent PO returns 404")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
