"""
Test Purchase Reversal System - Iteration 96
Testing P0 Purchase Reversal Flow

Test PO IDs from main agent:
- Draft PO: 2a39626e-a381-44c7-b0c9-40b2c6b2e896 (PO000043)
- Received PO: b72e55cb-a217-40ea-a6e6-7c8d6fd8900a (PO000040)
"""
import pytest
import requests
import os
import json

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "ocbgroupbjm@gmail.com"
TEST_PASSWORD = "admin123"
TEST_TENANT = "ocb_titan"

# Test PO IDs - Updated to use valid current POs
DRAFT_PO_ID = "1d4a712d-9e96-440e-8e1f-70826c4d5274"
DRAFT_PO_NUMBER = "PO000042"
RECEIVED_PO_ID = "b72e55cb-a217-40ea-a6e6-7c8d6fd8900a"
RECEIVED_PO_NUMBER = "PO000040"


@pytest.fixture(scope="module")
def auth_token():
    """Get auth token for testing"""
    # First get tenant list
    login_payload = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "tenant_id": TEST_TENANT
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_payload)
    if response.status_code == 200:
        data = response.json()
        return data.get("token") or data.get("access_token")
    
    pytest.skip(f"Login failed: {response.status_code} - {response.text}")


@pytest.fixture
def api_client(auth_token):
    """Shared requests session with auth"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    })
    return session


class TestReversalPreviewForDraftPO:
    """Test reversal preview endpoint for DRAFT PO"""
    
    def test_reversal_preview_draft_returns_can_delete_true(self, api_client):
        """
        GET /api/purchase/orders/{id}/reversal-preview for DRAFT PO
        Expected: can_delete=true, can_reverse=false
        """
        response = api_client.get(f"{BASE_URL}/api/purchase/orders/{DRAFT_PO_ID}/reversal-preview")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        print(f"Draft PO reversal preview: {json.dumps(data, indent=2)}")
        
        # Validate draft PO specific flags
        assert data.get("can_delete") == True, "Draft PO should have can_delete=true"
        assert data.get("can_reverse") == False, "Draft PO should have can_reverse=false"
        assert data.get("action_recommended") == "DELETE", f"Expected DELETE, got {data.get('action_recommended')}"
        assert data.get("current_status") == "draft", f"Expected draft status, got {data.get('current_status')}"
        
        print("✅ PASS: Draft PO reversal preview returns correct flags")


class TestReversalPreviewForReceivedPO:
    """Test reversal preview endpoint for RECEIVED PO"""
    
    def test_reversal_preview_received_returns_can_reverse_true(self, api_client):
        """
        GET /api/purchase/orders/{id}/reversal-preview for RECEIVED PO
        Expected: can_delete=false, can_reverse=true
        """
        response = api_client.get(f"{BASE_URL}/api/purchase/orders/{RECEIVED_PO_ID}/reversal-preview")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        print(f"Received PO reversal preview: {json.dumps(data, indent=2)}")
        
        # Validate non-draft PO flags
        assert data.get("can_delete") == False, "Received PO should have can_delete=false"
        # can_reverse depends on whether there are active payments
        assert "can_reverse" in data, "Response should contain can_reverse flag"
        
        # If no active payments, can_reverse should be true
        if not data.get("has_active_payments", False):
            assert data.get("can_reverse") == True, "PO without active payments should have can_reverse=true"
            assert data.get("action_recommended") == "REVERSE", f"Expected REVERSE, got {data.get('action_recommended')}"
        else:
            assert data.get("action_recommended") == "REVERSE_PAYMENTS_FIRST"
        
        print("✅ PASS: Received PO reversal preview returns correct flags")
    
    def test_reversal_preview_shows_impacts(self, api_client):
        """
        Verify reversal preview shows stock_movements, ap_records, journals in impacts
        """
        response = api_client.get(f"{BASE_URL}/api/purchase/orders/{RECEIVED_PO_ID}/reversal-preview")
        
        assert response.status_code == 200
        
        data = response.json()
        
        # Check impacts structure exists
        assert "impacts" in data, "Response should contain impacts section"
        impacts = data.get("impacts", {})
        
        # Verify impact categories exist
        assert "stock_movements" in impacts, "Impacts should show stock_movements"
        assert "ap_records" in impacts, "Impacts should show ap_records"
        assert "journals" in impacts, "Impacts should show journals"
        assert "payments" in impacts, "Impacts should show payments"
        
        # Check summary
        assert "summary" in data, "Response should contain summary"
        summary = data.get("summary", {})
        assert "total_stock_movements" in summary
        assert "total_ap_records" in summary
        assert "total_journals" in summary
        
        print(f"✅ PASS: Impacts summary - Stock: {summary.get('total_stock_movements')}, AP: {summary.get('total_ap_records')}, Journals: {summary.get('total_journals')}")


class TestReverseEndpoint:
    """Test POST /api/purchase/orders/{id}/reverse endpoint"""
    
    def test_reverse_endpoint_exists(self, api_client):
        """
        POST /api/purchase/orders/{id}/reverse endpoint exists
        """
        # Try with empty body - should fail validation but endpoint exists
        response = api_client.post(f"{BASE_URL}/api/purchase/orders/{RECEIVED_PO_ID}/reverse", json={})
        
        # 422 = validation error (reason required) - endpoint exists
        # 400 = business rule error - endpoint exists  
        # 404 = endpoint doesn't exist
        assert response.status_code != 404, "Reverse endpoint should exist"
        
        print(f"Reverse endpoint response: {response.status_code} - {response.text[:200]}")
        print("✅ PASS: Reverse endpoint exists")
    
    def test_reverse_requires_reason(self, api_client):
        """
        POST /api/purchase/orders/{id}/reverse requires 'reason' field
        """
        # Try without reason - should fail
        response = api_client.post(
            f"{BASE_URL}/api/purchase/orders/{RECEIVED_PO_ID}/reverse", 
            json={}
        )
        
        # Should return 422 (validation error) for missing required field
        # Or 400 if empty reason is checked in business logic
        assert response.status_code in [400, 422], f"Expected 400 or 422, got {response.status_code}"
        
        print(f"Without reason: {response.status_code}")
        print("✅ PASS: Reverse endpoint validates reason is required")
    
    def test_reverse_draft_po_should_fail(self, api_client):
        """
        Cannot reverse a DRAFT PO - should use DELETE instead
        """
        response = api_client.post(
            f"{BASE_URL}/api/purchase/orders/{DRAFT_PO_ID}/reverse",
            json={"reason": "Test reversal"}
        )
        
        # Should return 400 - draft POs should be deleted not reversed
        assert response.status_code == 400, f"Expected 400 for draft PO, got {response.status_code}"
        
        # Check error message mentions draft
        data = response.json()
        assert "draft" in str(data.get("detail", "")).lower() or "DELETE" in str(data.get("detail", "")), \
            "Error should mention draft status or DELETE alternative"
        
        print(f"Draft reverse error: {data.get('detail')}")
        print("✅ PASS: Cannot reverse DRAFT PO (must use DELETE)")


class TestPODetails:
    """Verify PO details and status"""
    
    def test_draft_po_exists(self, api_client):
        """Verify draft PO exists and has correct status"""
        response = api_client.get(f"{BASE_URL}/api/purchase/orders/{DRAFT_PO_ID}")
        
        assert response.status_code == 200, f"Draft PO not found: {response.status_code}"
        
        data = response.json()
        print(f"Draft PO: {data.get('po_number')} - Status: {data.get('status')}")
        
        assert data.get("status") == "draft", f"Expected draft status, got {data.get('status')}"
    
    def test_received_po_exists(self, api_client):
        """Verify received PO exists and has received/posted status"""
        response = api_client.get(f"{BASE_URL}/api/purchase/orders/{RECEIVED_PO_ID}")
        
        assert response.status_code == 200, f"Received PO not found: {response.status_code}"
        
        data = response.json()
        print(f"Received PO: {data.get('po_number')} - Status: {data.get('status')}")
        
        # Status should be received, posted, or similar non-draft status
        assert data.get("status") != "draft", f"PO should not be draft, got {data.get('status')}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
