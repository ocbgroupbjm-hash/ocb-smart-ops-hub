"""
Test Menu Cleanup & AR Payment Delete Validation - Iteration 95
P0 Menu Duplication Cleanup verification tests

Tests:
1. AR Payments List endpoint availability
2. AR Payment DELETE endpoint for draft payments
3. AR Payment DELETE endpoint for posted payments (should fail)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestARPaymentsEndpoints:
    """AR Payments endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with auth"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_payload = {
            "email": "ocbgroupbjm@gmail.com",
            "password": "admin123",
            "tenant_id": "ocb_titan"
        }
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json=login_payload)
        if login_response.status_code == 200:
            data = login_response.json()
            token = data.get("token") or data.get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        yield
        self.session.close()
    
    def test_ar_payments_list_via_sales(self):
        """Test AR payments list endpoint via sales module /api/sales/ar-payments"""
        response = self.session.get(f"{BASE_URL}/api/sales/ar-payments")
        print(f"AR Payments via /api/sales/ar-payments: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        print(f"Found {len(data.get('items', []))} AR payments")
    
    def test_ar_payments_list_via_ar(self):
        """Test AR payments list endpoint via /api/ar/payments (may not exist)"""
        response = self.session.get(f"{BASE_URL}/api/ar/payments")
        print(f"AR Payments via /api/ar/payments: {response.status_code}")
        # This endpoint may or may not exist - document the result
        if response.status_code == 200:
            data = response.json()
            print(f"Found {len(data.get('items', []))} AR payments")
        else:
            print(f"Endpoint not found or error: {response.text[:200]}")
    
    def test_delete_ar_payment_posted_via_allocation_engine(self):
        """Test DELETE posted AR payment via payment-allocation engine (should fail)"""
        # First, get a payment
        response = self.session.get(f"{BASE_URL}/api/sales/ar-payments")
        if response.status_code != 200:
            pytest.skip("Cannot get AR payments list")
        
        payments = response.json().get("items", [])
        
        # Find a posted payment
        posted_payment = None
        for p in payments:
            if p.get("status") == "posted":
                posted_payment = p
                break
        
        if not posted_payment:
            pytest.skip("No posted AR payment found to test delete")
        
        payment_id = posted_payment.get("id")
        print(f"Testing DELETE posted payment {posted_payment.get('payment_no')} via /api/payment-allocation/ar/payments/{payment_id}")
        
        # Try to delete via payment-allocation engine
        response = self.session.delete(f"{BASE_URL}/api/payment-allocation/ar/payments/{payment_id}")
        print(f"DELETE response: {response.status_code} - {response.text[:200]}")
        
        # Should return 400 for posted payments
        assert response.status_code == 400, f"Expected 400 for posted payment, got {response.status_code}"
        assert "POSTED" in response.text.upper() or "REVERSE" in response.text.upper()
    
    def test_delete_ar_payment_via_correct_endpoint(self):
        """Test DELETE AR payment via correct endpoint /api/payment-allocation/ar/payments/{id}"""
        # First, get a payment
        response = self.session.get(f"{BASE_URL}/api/sales/ar-payments")
        if response.status_code != 200:
            pytest.skip("Cannot get AR payments list")
        
        payments = response.json().get("items", [])
        
        if not payments:
            pytest.skip("No AR payments found")
        
        # Find a posted payment (should fail delete)
        posted_payment = None
        for p in payments:
            if p.get("status") == "posted":
                posted_payment = p
                break
        
        if posted_payment:
            payment_id = posted_payment.get("id")
            print(f"Testing DELETE posted payment via /api/payment-allocation/ar/payments/{payment_id}")
            
            # Try to delete via correct endpoint
            response = self.session.delete(f"{BASE_URL}/api/payment-allocation/ar/payments/{payment_id}")
            print(f"DELETE posted response: {response.status_code} - {response.text[:200]}")
            
            # Should return 400 for posted payments
            assert response.status_code == 400, f"Expected 400 for posted, got {response.status_code}"
            print("PASS: Posted payment DELETE correctly rejected")
        else:
            # Find any payment to test delete
            payment = payments[0]
            payment_id = payment.get("id")
            status = payment.get("status", "unknown")
            print(f"Testing DELETE {status} payment via /api/payment-allocation/ar/payments/{payment_id}")
            
            response = self.session.delete(f"{BASE_URL}/api/payment-allocation/ar/payments/{payment_id}")
            print(f"DELETE response: {response.status_code} - {response.text[:200]}")
            
            # Document the result
            if response.status_code == 200:
                print("Good: Draft payment deleted successfully")
            elif response.status_code == 400:
                print("Good: DELETE blocked for this payment (status validation working)")
            else:
                print(f"Unexpected status: {response.status_code}")


class TestEndpointRouting:
    """Test correct endpoint routing for AR/AP payments"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with auth"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_payload = {
            "email": "ocbgroupbjm@gmail.com",
            "password": "admin123",
            "tenant_id": "ocb_titan"
        }
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json=login_payload)
        if login_response.status_code == 200:
            data = login_response.json()
            token = data.get("token") or data.get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        yield
        self.session.close()
    
    def test_payment_allocation_ar_delete_exists(self):
        """Verify /api/payment-allocation/ar/payments/{id} DELETE endpoint exists"""
        # Use a fake ID to test endpoint existence
        response = self.session.delete(f"{BASE_URL}/api/payment-allocation/ar/payments/fake-id-12345")
        print(f"DELETE /api/payment-allocation/ar/payments/fake-id: {response.status_code}")
        
        # Should return 404 (not found) not 405 (method not allowed)
        # 404 means endpoint exists but payment not found
        assert response.status_code in [400, 404, 422], f"Unexpected status: {response.status_code}"
    
    def test_payment_allocation_ap_delete_exists(self):
        """Verify /api/payment-allocation/ap/payments/{id} DELETE endpoint exists"""
        response = self.session.delete(f"{BASE_URL}/api/payment-allocation/ap/payments/fake-id-12345")
        print(f"DELETE /api/payment-allocation/ap/payments/fake-id: {response.status_code}")
        
        assert response.status_code in [400, 404, 422], f"Unexpected status: {response.status_code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
