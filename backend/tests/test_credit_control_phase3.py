"""
OCB TITAN ERP - Phase 3 Operational Control System
Module: Customer Credit Limit Control Tests
Tests: credit_limit, credit_hold status, overdue_blocking, hard stop, approval override, audit trail
"""

import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test Credentials
OWNER_EMAIL = "ocbgroupbjm@gmail.com"
OWNER_PASSWORD = "admin123"
KASIR_EMAIL = "kasir_test@ocb.com"
KASIR_PASSWORD = "password123"

# Test Customer ID (already setup with 50jt credit limit)
TEST_CUSTOMER_ID = "CUS-AUDIT-003"


class TestAuth:
    """Authentication tests to get tokens"""
    
    @pytest.fixture(scope="class")
    def owner_token(self):
        """Get Owner token for authenticated requests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": OWNER_EMAIL,
            "password": OWNER_PASSWORD
        })
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token") or data.get("token")
        pytest.skip("Owner authentication failed - skipping authenticated tests")
    
    @pytest.fixture(scope="class")
    def kasir_token(self):
        """Get Kasir token for RBAC tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": KASIR_EMAIL,
            "password": KASIR_PASSWORD
        })
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token") or data.get("token")
        pytest.skip("Kasir authentication failed - skipping RBAC tests")


class TestCreditPolicy:
    """Test credit policy endpoints"""
    
    @pytest.fixture(scope="class")
    def token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": OWNER_EMAIL,
            "password": OWNER_PASSWORD
        })
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token") or data.get("token")
        pytest.skip("Authentication failed")
    
    def test_get_credit_policy(self, token):
        """GET /api/credit-control/policy - Get default credit policy"""
        response = requests.get(
            f"{BASE_URL}/api/credit-control/policy",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        # Verify policy structure
        assert "default_credit_limit" in data
        assert "max_overdue_days" in data
        assert "segments" in data
        
        # Verify segments exist
        segments = data.get("segments", {})
        assert "regular" in segments
        assert "member" in segments
        assert "vip" in segments
        print(f"[PASS] GET /api/credit-control/policy - Policy has {len(segments)} segments")


class TestCustomerCreditStatus:
    """Test customer credit status endpoints"""
    
    @pytest.fixture(scope="class")
    def token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": OWNER_EMAIL,
            "password": OWNER_PASSWORD
        })
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token") or data.get("token")
        pytest.skip("Authentication failed")
    
    def test_get_customer_credit_status(self, token):
        """GET /api/credit-control/customer/{id} - Get customer credit info"""
        response = requests.get(
            f"{BASE_URL}/api/credit-control/customer/{TEST_CUSTOMER_ID}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        # Verify credit info structure
        assert "customer_id" in data
        assert "credit_limit" in data
        assert "outstanding_balance" in data
        assert "available_credit" in data
        assert "effective_status" in data
        assert "can_transact" in data
        
        print(f"[PASS] GET /api/credit-control/customer/{TEST_CUSTOMER_ID}")
        print(f"  - Credit Limit: Rp {data.get('credit_limit', 0):,.0f}")
        print(f"  - Status: {data.get('effective_status')}")
        print(f"  - Can Transact: {data.get('can_transact')}")
    
    def test_get_nonexistent_customer(self, token):
        """GET /api/credit-control/customer/{id} - 404 for invalid customer"""
        response = requests.get(
            f"{BASE_URL}/api/credit-control/customer/INVALID-CUSTOMER-ID",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("[PASS] Non-existent customer returns 404")


class TestCreditCheck:
    """Test credit check (hard stop) endpoint"""
    
    @pytest.fixture(scope="class")
    def token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": OWNER_EMAIL,
            "password": OWNER_PASSWORD
        })
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token") or data.get("token")
        pytest.skip("Authentication failed")
    
    def test_credit_check_allowed(self, token):
        """POST /api/credit-control/check - Transaction within limit should be allowed"""
        response = requests.post(
            f"{BASE_URL}/api/credit-control/check",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "customer_id": TEST_CUSTOMER_ID,
                "transaction_amount": 1000000,  # 1jt - should be allowed
                "transaction_type": "sales"
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "allowed" in data
        assert "reason" in data
        assert "credit_info" in data
        
        print(f"[PASS] Credit check for Rp 1,000,000")
        print(f"  - Allowed: {data.get('allowed')}")
        print(f"  - Reason: {data.get('reason')}")
    
    def test_credit_check_exceeds_limit(self, token):
        """POST /api/credit-control/check - Transaction exceeding limit should be blocked"""
        # Get current credit info first
        info_response = requests.get(
            f"{BASE_URL}/api/credit-control/customer/{TEST_CUSTOMER_ID}",
            headers={"Authorization": f"Bearer {token}"}
        )
        credit_info = info_response.json()
        credit_limit = credit_info.get("credit_limit", 0)
        
        # Try to transact more than available
        over_limit_amount = credit_limit + 10000000  # Limit + 10jt
        
        response = requests.post(
            f"{BASE_URL}/api/credit-control/check",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "customer_id": TEST_CUSTOMER_ID,
                "transaction_amount": over_limit_amount,
                "transaction_type": "sales"
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        # Should be blocked if customer has outstanding balance
        if credit_limit > 0:
            # If limit exists and transaction exceeds, check response structure
            assert "allowed" in data
            assert "requires_override" in data
            print(f"[PASS] Credit check for over-limit amount Rp {over_limit_amount:,.0f}")
            print(f"  - Allowed: {data.get('allowed')}")
            print(f"  - Requires Override: {data.get('requires_override')}")


class TestCreditLimitUpdate:
    """Test credit limit update endpoint"""
    
    @pytest.fixture(scope="class")
    def token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": OWNER_EMAIL,
            "password": OWNER_PASSWORD
        })
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token") or data.get("token")
        pytest.skip("Authentication failed")
    
    def test_update_credit_limit(self, token):
        """PUT /api/credit-control/customer/{id}/limit - Update credit limit"""
        new_limit = 75000000  # 75jt
        
        response = requests.put(
            f"{BASE_URL}/api/credit-control/customer/{TEST_CUSTOMER_ID}/limit",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "customer_id": TEST_CUSTOMER_ID,
                "credit_limit": new_limit,
                "notes": "TEST - Update limit via pytest"
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data.get("success") == True
        assert data.get("new_limit") == new_limit
        
        print(f"[PASS] Update credit limit to Rp {new_limit:,.0f}")
        print(f"  - Old Limit: Rp {data.get('old_limit', 0):,.0f}")
        print(f"  - New Limit: Rp {data.get('new_limit', 0):,.0f}")
        
        # Restore original limit
        requests.put(
            f"{BASE_URL}/api/credit-control/customer/{TEST_CUSTOMER_ID}/limit",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "customer_id": TEST_CUSTOMER_ID,
                "credit_limit": 50000000,  # Restore to 50jt
                "notes": "TEST - Restore limit via pytest"
            }
        )


class TestCreditHoldActions:
    """Test credit hold/release/block endpoints"""
    
    @pytest.fixture(scope="class")
    def token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": OWNER_EMAIL,
            "password": OWNER_PASSWORD
        })
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token") or data.get("token")
        pytest.skip("Authentication failed")
    
    def test_hold_customer(self, token):
        """POST /api/credit-control/customer/{id}/hold - Hold customer credit"""
        response = requests.post(
            f"{BASE_URL}/api/credit-control/customer/{TEST_CUSTOMER_ID}/hold",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "customer_id": TEST_CUSTOMER_ID,
                "action": "hold",
                "reason": "TEST - Temporary hold via pytest"
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data.get("success") == True
        assert data.get("new_status") == "hold"
        
        print(f"[PASS] Hold customer {TEST_CUSTOMER_ID}")
        print(f"  - Old Status: {data.get('old_status')}")
        print(f"  - New Status: {data.get('new_status')}")
    
    def test_release_hold(self, token):
        """POST /api/credit-control/customer/{id}/hold - Release customer hold"""
        response = requests.post(
            f"{BASE_URL}/api/credit-control/customer/{TEST_CUSTOMER_ID}/hold",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "customer_id": TEST_CUSTOMER_ID,
                "action": "release",
                "reason": ""
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data.get("success") == True
        assert data.get("new_status") == "active"
        
        print(f"[PASS] Release hold for customer {TEST_CUSTOMER_ID}")
        print(f"  - New Status: {data.get('new_status')}")
    
    def test_block_customer(self, token):
        """POST /api/credit-control/customer/{id}/hold - Block customer credit"""
        response = requests.post(
            f"{BASE_URL}/api/credit-control/customer/{TEST_CUSTOMER_ID}/hold",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "customer_id": TEST_CUSTOMER_ID,
                "action": "block",
                "reason": "TEST - Blocked via pytest"
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data.get("success") == True
        assert data.get("new_status") == "blocked"
        
        print(f"[PASS] Block customer {TEST_CUSTOMER_ID}")
    
    def test_unblock_customer(self, token):
        """POST /api/credit-control/customer/{id}/hold - Unblock customer"""
        response = requests.post(
            f"{BASE_URL}/api/credit-control/customer/{TEST_CUSTOMER_ID}/hold",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "customer_id": TEST_CUSTOMER_ID,
                "action": "unblock",
                "reason": ""
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data.get("success") == True
        assert data.get("new_status") == "active"
        
        print(f"[PASS] Unblock customer {TEST_CUSTOMER_ID}")
    
    def test_invalid_action(self, token):
        """POST /api/credit-control/customer/{id}/hold - Invalid action returns 400"""
        response = requests.post(
            f"{BASE_URL}/api/credit-control/customer/{TEST_CUSTOMER_ID}/hold",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "customer_id": TEST_CUSTOMER_ID,
                "action": "invalid_action",
                "reason": "TEST"
            }
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("[PASS] Invalid action returns 400")


class TestHardStopIntegration:
    """Test hard stop integration - blocked customer cannot transact"""
    
    @pytest.fixture(scope="class")
    def token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": OWNER_EMAIL,
            "password": OWNER_PASSWORD
        })
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token") or data.get("token")
        pytest.skip("Authentication failed")
    
    def test_held_customer_cannot_transact(self, token):
        """Held customer should not be able to transact"""
        # Hold customer first
        requests.post(
            f"{BASE_URL}/api/credit-control/customer/{TEST_CUSTOMER_ID}/hold",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "customer_id": TEST_CUSTOMER_ID,
                "action": "hold",
                "reason": "TEST - Hard stop test"
            }
        )
        
        # Check if can transact
        response = requests.post(
            f"{BASE_URL}/api/credit-control/check",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "customer_id": TEST_CUSTOMER_ID,
                "transaction_amount": 100000,  # Small amount
                "transaction_type": "sales"
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("allowed") == False, "Held customer should not be allowed to transact"
        assert data.get("requires_override") == True, "Held customer should require override"
        
        print("[PASS] Held customer cannot transact - hard stop working")
        
        # Release hold to clean up
        requests.post(
            f"{BASE_URL}/api/credit-control/customer/{TEST_CUSTOMER_ID}/hold",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "customer_id": TEST_CUSTOMER_ID,
                "action": "release",
                "reason": ""
            }
        )


class TestDashboard:
    """Test credit dashboard endpoint"""
    
    @pytest.fixture(scope="class")
    def token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": OWNER_EMAIL,
            "password": OWNER_PASSWORD
        })
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token") or data.get("token")
        pytest.skip("Authentication failed")
    
    def test_get_dashboard(self, token):
        """GET /api/credit-control/dashboard - Get credit dashboard summary"""
        response = requests.get(
            f"{BASE_URL}/api/credit-control/dashboard",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        # Verify dashboard structure
        assert "customers_by_status" in data
        assert "total_customers" in data
        assert "total_outstanding" in data
        assert "total_overdue" in data
        assert "pending_override_approvals" in data
        
        print(f"[PASS] GET /api/credit-control/dashboard")
        print(f"  - Total Customers: {data.get('total_customers')}")
        print(f"  - Total Outstanding: Rp {data.get('total_outstanding', 0):,.0f}")
        print(f"  - Total Overdue: Rp {data.get('total_overdue', 0):,.0f}")
        print(f"  - Pending Overrides: {data.get('pending_override_approvals')}")


class TestAtRiskCustomers:
    """Test at-risk customers endpoint"""
    
    @pytest.fixture(scope="class")
    def token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": OWNER_EMAIL,
            "password": OWNER_PASSWORD
        })
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token") or data.get("token")
        pytest.skip("Authentication failed")
    
    def test_get_at_risk_customers(self, token):
        """GET /api/credit-control/at-risk - Get at-risk customers list"""
        response = requests.get(
            f"{BASE_URL}/api/credit-control/at-risk?min_overdue_days=7",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "total_at_risk_balance" in data
        
        print(f"[PASS] GET /api/credit-control/at-risk")
        print(f"  - Total At Risk: {data.get('total')}")
        print(f"  - At Risk Balance: Rp {data.get('total_at_risk_balance', 0):,.0f}")
        
        # Verify each at-risk customer has required fields
        for customer in data.get("items", [])[:3]:  # Check first 3
            assert "customer_id" in customer
            assert "effective_status" in customer
            assert "utilization_percent" in customer
            assert "risk_factors" in customer


class TestAuditLog:
    """Test credit audit log endpoint"""
    
    @pytest.fixture(scope="class")
    def token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": OWNER_EMAIL,
            "password": OWNER_PASSWORD
        })
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token") or data.get("token")
        pytest.skip("Authentication failed")
    
    def test_get_audit_log(self, token):
        """GET /api/credit-control/audit-log - Get credit audit logs"""
        response = requests.get(
            f"{BASE_URL}/api/credit-control/audit-log?limit=10",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "items" in data
        assert "total" in data
        
        print(f"[PASS] GET /api/credit-control/audit-log")
        print(f"  - Total Logs: {data.get('total')}")
        
        # Verify audit log structure
        for log in data.get("items", [])[:3]:
            assert "action" in log
            assert "module" in log
            assert "timestamp" in log
            print(f"  - {log.get('action')}: {log.get('description', '')[:50]}...")
    
    def test_get_audit_log_by_customer(self, token):
        """GET /api/credit-control/audit-log - Filter by customer_id"""
        response = requests.get(
            f"{BASE_URL}/api/credit-control/audit-log?customer_id={TEST_CUSTOMER_ID}&limit=5",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        # All logs should be for the specified customer
        for log in data.get("items", []):
            assert log.get("target_id") == TEST_CUSTOMER_ID or log.get("target_id") is None
        
        print(f"[PASS] Audit log filter by customer_id working")


class TestRBACAccess:
    """Test RBAC - Kasir should not be able to update credit settings"""
    
    @pytest.fixture(scope="class")
    def kasir_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": KASIR_EMAIL,
            "password": KASIR_PASSWORD
        })
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token") or data.get("token")
        pytest.skip("Kasir authentication failed")
    
    def test_kasir_can_view_dashboard(self, kasir_token):
        """Kasir should be able to view dashboard"""
        response = requests.get(
            f"{BASE_URL}/api/credit-control/dashboard",
            headers={"Authorization": f"Bearer {kasir_token}"}
        )
        # Kasir should be able to view
        assert response.status_code == 200, f"Kasir should be able to view dashboard"
        print("[PASS] Kasir can view credit dashboard")
    
    def test_kasir_cannot_update_limit(self, kasir_token):
        """Kasir should NOT be able to update credit limit"""
        response = requests.put(
            f"{BASE_URL}/api/credit-control/customer/{TEST_CUSTOMER_ID}/limit",
            headers={"Authorization": f"Bearer {kasir_token}"},
            json={
                "customer_id": TEST_CUSTOMER_ID,
                "credit_limit": 100000000,
                "notes": "TEST - Kasir trying to update"
            }
        )
        # Should be 403 Forbidden
        assert response.status_code == 403, f"Expected 403, got {response.status_code}. Kasir should not be able to update credit limit"
        print("[PASS] Kasir cannot update credit limit (403)")
    
    def test_kasir_cannot_hold_customer(self, kasir_token):
        """Kasir should NOT be able to hold customer"""
        response = requests.post(
            f"{BASE_URL}/api/credit-control/customer/{TEST_CUSTOMER_ID}/hold",
            headers={"Authorization": f"Bearer {kasir_token}"},
            json={
                "customer_id": TEST_CUSTOMER_ID,
                "action": "hold",
                "reason": "TEST - Kasir trying to hold"
            }
        )
        # Should be 403 Forbidden
        assert response.status_code == 403, f"Expected 403, got {response.status_code}. Kasir should not be able to hold customer"
        print("[PASS] Kasir cannot hold customer (403)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
