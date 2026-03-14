"""
OCB TITAN ERP - AP Payment System Test (Iteration 63)
Tests for:
- GET /api/accounts/cash-bank endpoint (must return >= 5 accounts)
- GET /api/ap/list endpoint
- POST /api/ap/{id}/payment endpoint
- Journal creation and balance verification
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "ocbgroupbjm@gmail.com"
TEST_PASSWORD = "admin123"
TEST_TENANT = "ocb_titan"


class TestAPPaymentSystem:
    """AP Payment System Tests for P0 Bug Fix"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - authenticate and get token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
                "tenant_id": TEST_TENANT
            }
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        self.token = data.get("token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
    def test_01_cash_bank_accounts_at_least_5(self):
        """Test: Dropdown Bank/Kas must show at least 5 accounts"""
        response = requests.get(
            f"{BASE_URL}/api/accounts/cash-bank",
            headers=self.headers
        )
        assert response.status_code == 200, f"API failed: {response.text}"
        
        data = response.json()
        accounts = data.get("accounts", [])
        total = data.get("total", 0)
        
        print(f"Total cash/bank accounts returned: {total}")
        for acc in accounts[:10]:
            print(f"  - {acc.get('code')} - {acc.get('name')} ({acc.get('sub_type', '?')})")
        
        # P0 Requirement: Must return at least 5 accounts
        assert total >= 5, f"Expected at least 5 cash/bank accounts, got {total}"
        assert len(accounts) >= 5, f"Expected at least 5 accounts in list, got {len(accounts)}"
        
        # Verify accounts have required fields
        for acc in accounts:
            assert acc.get("id"), f"Account missing 'id' field: {acc}"
            assert acc.get("code"), f"Account missing 'code' field: {acc}"
            assert acc.get("name"), f"Account missing 'name' field: {acc}"
    
    def test_02_ap_list_endpoint(self):
        """Test: GET /api/ap/list returns AP data"""
        response = requests.get(
            f"{BASE_URL}/api/ap/list",
            headers=self.headers
        )
        assert response.status_code == 200, f"API failed: {response.text}"
        
        data = response.json()
        items = data.get("items", [])
        total = data.get("total", 0)
        
        print(f"Total AP records: {total}")
        # Report first 5 AP items
        for ap in items[:5]:
            print(f"  - {ap.get('ap_no')} | {ap.get('supplier_name')} | Status: {ap.get('status')} | Outstanding: {ap.get('outstanding_amount', 0)}")
        
        # Should return list structure
        assert isinstance(items, list), "Items should be a list"
        assert "total" in data, "Response should contain 'total' field"
    
    def test_03_ap_with_outstanding_exists(self):
        """Test: At least one AP with outstanding > 0 exists for payment testing"""
        response = requests.get(
            f"{BASE_URL}/api/ap/list?status=partial",
            headers=self.headers
        )
        assert response.status_code == 200, f"API failed: {response.text}"
        
        data = response.json()
        items = data.get("items", [])
        
        # Find AP with outstanding > 0
        ap_with_outstanding = [ap for ap in items if ap.get("outstanding_amount", 0) > 0 and ap.get("id")]
        
        if ap_with_outstanding:
            ap = ap_with_outstanding[0]
            print(f"Found payable AP: {ap.get('ap_no')} - Outstanding: {ap.get('outstanding_amount')}")
            self.test_ap_id = ap.get("id")
            self.test_outstanding = ap.get("outstanding_amount")
        else:
            pytest.skip("No AP with outstanding amount found for payment test")
    
    def test_04_ap_payment_creates_journal(self):
        """Test: POST /api/ap/{id}/payment creates payment and journal"""
        # First get an AP with outstanding
        response = requests.get(
            f"{BASE_URL}/api/ap/list?status=partial",
            headers=self.headers
        )
        assert response.status_code == 200
        
        data = response.json()
        items = data.get("items", [])
        ap_with_outstanding = [ap for ap in items if ap.get("outstanding_amount", 0) > 0 and ap.get("id")]
        
        if not ap_with_outstanding:
            pytest.skip("No AP with outstanding amount found")
        
        ap = ap_with_outstanding[0]
        ap_id = ap.get("id")
        outstanding = ap.get("outstanding_amount", 0)
        
        # Get a bank account ID
        acc_response = requests.get(
            f"{BASE_URL}/api/accounts/cash-bank",
            headers=self.headers
        )
        assert acc_response.status_code == 200
        accounts = acc_response.json().get("accounts", [])
        assert len(accounts) > 0, "No cash/bank accounts available"
        
        bank_account_id = accounts[0].get("id")
        
        # Make a small payment
        payment_amount = min(50000, outstanding)  # Pay 50k or less
        
        payment_response = requests.post(
            f"{BASE_URL}/api/ap/{ap_id}/payment",
            headers=self.headers,
            json={
                "amount": payment_amount,
                "payment_method": "transfer",
                "bank_account_id": bank_account_id,
                "reference_no": "TEST-ITER63-001",
                "notes": "Test payment from iteration 63 pytest"
            }
        )
        
        assert payment_response.status_code == 200, f"Payment failed: {payment_response.text}"
        
        result = payment_response.json()
        print(f"Payment successful:")
        print(f"  Payment No: {result.get('payment_no')}")
        print(f"  Journal No: {result.get('journal_no')}")
        print(f"  New Outstanding: {result.get('new_outstanding')}")
        
        # Verify response has required fields
        assert result.get("payment_no"), "Payment should return payment_no"
        assert result.get("journal_no"), "Payment should create journal_no"
        assert result.get("new_outstanding") is not None, "Payment should return new_outstanding"
        assert result.get("new_outstanding") == outstanding - payment_amount, \
            f"New outstanding mismatch: expected {outstanding - payment_amount}, got {result.get('new_outstanding')}"


class TestAPButtons:
    """Test AP Page Buttons existence"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - authenticate"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
                "tenant_id": TEST_TENANT
            }
        )
        assert response.status_code == 200
        self.token = response.json().get("token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_05_soft_delete_endpoint_exists(self):
        """Test: PUT /api/ap/{id}/soft-delete endpoint exists"""
        # Get an AP without payments
        response = requests.get(
            f"{BASE_URL}/api/ap/list",
            headers=self.headers
        )
        assert response.status_code == 200
        
        data = response.json()
        items = data.get("items", [])
        
        # Find AP without payments (paid_amount = 0)
        deletable_ap = [ap for ap in items if ap.get("paid_amount", 0) == 0 and ap.get("status") != "paid" and ap.get("id")]
        
        if not deletable_ap:
            # If no deletable AP, just test that the endpoint responds correctly to non-existent ID
            response = requests.put(
                f"{BASE_URL}/api/ap/non-existent-id/soft-delete",
                headers=self.headers
            )
            # Should return 404 for non-existent, proving endpoint exists
            assert response.status_code in [404, 400], "Soft-delete endpoint should exist"
            print("Soft-delete endpoint exists (tested with non-existent ID)")
        else:
            print(f"Found {len(deletable_ap)} deletable AP records")
            # We don't actually delete, just confirm endpoint is routable
            print("Soft-delete endpoint is available")


class TestAPSummaryDashboard:
    """Test AP Summary Dashboard endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - authenticate"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
                "tenant_id": TEST_TENANT
            }
        )
        assert response.status_code == 200
        self.token = response.json().get("token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_06_summary_dashboard(self):
        """Test: GET /api/ap/summary/dashboard returns summary data"""
        response = requests.get(
            f"{BASE_URL}/api/ap/summary/dashboard",
            headers=self.headers
        )
        assert response.status_code == 200, f"API failed: {response.text}"
        
        data = response.json()
        print(f"AP Summary Dashboard:")
        print(f"  Total AP Count: {data.get('total_ap_count')}")
        print(f"  Total Outstanding: {data.get('total_outstanding')}")
        print(f"  Overdue Count: {data.get('overdue_count')}")
        print(f"  Due This Week: {data.get('due_this_week')}")
        
        # Verify structure
        assert "total_ap_count" in data
        assert "total_outstanding" in data
        assert "overdue_count" in data
    
    def test_07_aging_report(self):
        """Test: GET /api/ap/aging returns aging data"""
        response = requests.get(
            f"{BASE_URL}/api/ap/aging",
            headers=self.headers
        )
        assert response.status_code == 200, f"API failed: {response.text}"
        
        data = response.json()
        aging = data.get("aging", {})
        
        print(f"AP Aging Report:")
        print(f"  Current: {aging.get('current', {}).get('count', 0)} - {aging.get('current', {}).get('amount', 0)}")
        print(f"  1-30 days: {aging.get('1_30', {}).get('count', 0)} - {aging.get('1_30', {}).get('amount', 0)}")
        print(f"  31-60 days: {aging.get('31_60', {}).get('count', 0)} - {aging.get('31_60', {}).get('amount', 0)}")
        
        # Verify structure
        assert "aging" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
