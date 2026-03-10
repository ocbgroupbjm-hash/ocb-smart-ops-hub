"""
OCB TITAN ERP - Deposit System (Setoran Harian) API Tests
Tests: Init, Seed Sales, My Sales, Create Deposit, Update, Workflow, Journal, Role-based Access
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "ocbgroupbjm@gmail.com"
ADMIN_PASSWORD = "admin123"
KASIR_EMAIL = "kasir_test@ocb.com"
KASIR_PASSWORD = "password123"


class TestDepositSystemSetup:
    """Setup and initialization tests"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if res.status_code == 200:
            return res.json().get("token")
        pytest.skip(f"Admin login failed: {res.status_code} - {res.text}")
    
    def test_api_health(self):
        """Test API health endpoint"""
        res = requests.get(f"{BASE_URL}/api/health")
        assert res.status_code == 200, f"Health check failed: {res.text}"
        data = res.json()
        assert data.get("status") == "healthy"
        print(f"API health: {data}")
    
    def test_admin_login(self, admin_token):
        """Test admin login"""
        assert admin_token is not None, "Admin token should not be None"
        print(f"Admin token acquired: {admin_token[:20]}...")
    
    def test_deposit_init(self, admin_token):
        """Test initialize deposit system: POST /api/deposit/init"""
        res = requests.post(
            f"{BASE_URL}/api/deposit/init",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert res.status_code == 200, f"Init failed: {res.status_code} - {res.text}"
        data = res.json()
        assert "default_accounts" in data
        print(f"Deposit init: {data['message']}, accounts: {data['default_accounts']}")


class TestDepositSeedAndFetch:
    """Tests for seeding sales and fetching for deposit"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if res.status_code == 200:
            return res.json().get("token")
        pytest.skip(f"Admin login failed: {res.status_code}")
    
    def test_seed_sales(self, admin_token):
        """Test seed sample sales: POST /api/deposit/seed-sales"""
        # Seed sales for a future date to ensure we have un-deposited sales
        test_date = "2026-03-12"
        res = requests.post(
            f"{BASE_URL}/api/deposit/seed-sales?count=5&sales_date={test_date}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert res.status_code == 200, f"Seed sales failed: {res.status_code} - {res.text}"
        data = res.json()
        assert "transactions" in data
        assert len(data["transactions"]) == 5
        print(f"Seeded {len(data['transactions'])} transactions for {test_date}")
        print(f"Summary: {data['summary']}")
    
    def test_get_my_sales_for_deposit(self, admin_token):
        """Test get my sales for deposit: GET /api/deposit/my-sales"""
        test_date = "2026-03-12"
        res = requests.get(
            f"{BASE_URL}/api/deposit/my-sales?sales_date={test_date}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert res.status_code == 200, f"Get my sales failed: {res.status_code} - {res.text}"
        data = res.json()
        
        # Verify response structure
        assert "sales_date" in data
        assert "summary" in data
        assert "branch_name" in data
        assert "cashier_name" in data
        
        summary = data["summary"]
        print(f"Sales for {test_date}: {summary['total_transactions']} transactions")
        print(f"Cash should deposit: {summary['cash_should_deposit']}")
    
    def test_get_my_sales_no_data(self, admin_token):
        """Test get my sales for date with no data"""
        future_date = "2030-01-01"
        res = requests.get(
            f"{BASE_URL}/api/deposit/my-sales?sales_date={future_date}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert res.status_code == 200
        data = res.json()
        assert data["summary"]["total_transactions"] == 0
        print(f"Sales for {future_date}: 0 transactions (expected)")


class TestDepositCRUD:
    """Tests for deposit CRUD operations"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if res.status_code == 200:
            return res.json().get("token")
        pytest.skip(f"Admin login failed: {res.status_code}")
    
    @pytest.fixture(scope="class")
    def test_deposit_data(self, admin_token):
        """Create a test deposit and return it for other tests"""
        # First seed some sales for a new date
        test_date = "2026-03-13"
        seed_res = requests.post(
            f"{BASE_URL}/api/deposit/seed-sales?count=3&sales_date={test_date}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        if seed_res.status_code != 200:
            pytest.skip(f"Could not seed sales: {seed_res.text}")
        
        # Create the deposit
        res = requests.post(
            f"{BASE_URL}/api/deposit/create",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json={
                "sales_date": test_date,
                "shift_id": "",
                "notes": "Test deposit from pytest"
            }
        )
        if res.status_code == 200:
            return res.json()
        pytest.skip(f"Could not create deposit: {res.status_code} - {res.text}")
    
    def test_create_deposit(self, admin_token, test_deposit_data):
        """Test create deposit: POST /api/deposit/create"""
        assert test_deposit_data is not None
        assert "id" in test_deposit_data
        assert "deposit_number" in test_deposit_data
        print(f"Created deposit: {test_deposit_data['deposit_number']}")
    
    def test_get_deposit_detail(self, admin_token, test_deposit_data):
        """Test get deposit detail: GET /api/deposit/{id}"""
        deposit_id = test_deposit_data["id"]
        res = requests.get(
            f"{BASE_URL}/api/deposit/{deposit_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert res.status_code == 200, f"Get detail failed: {res.status_code} - {res.text}"
        data = res.json()
        
        # Verify all required fields are present
        assert data["id"] == deposit_id
        assert "deposit_number" in data
        assert "branch_name" in data
        assert "cashier_name" in data
        assert "cash_should_deposit" in data
        assert "status" in data
        assert data["status"] == "draft"
        print(f"Deposit detail: {data['deposit_number']}, status: {data['status']}")
        print(f"Should deposit: {data['cash_should_deposit']}, Transactions: {data.get('total_transactions', 0)}")
    
    def test_update_deposit_with_cash(self, admin_token, test_deposit_data):
        """Test update deposit with cash received: PUT /api/deposit/{id}"""
        deposit_id = test_deposit_data["id"]
        
        # First get the deposit to know the cash_should_deposit
        detail_res = requests.get(
            f"{BASE_URL}/api/deposit/{deposit_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        cash_should = detail_res.json().get("cash_should_deposit", 100000)
        
        # Update with exact match (no difference)
        res = requests.put(
            f"{BASE_URL}/api/deposit/{deposit_id}",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json={
                "cash_received": cash_should,
                "difference_reason": "",
                "admin_fee": 0,
                "notes": "Updated with exact cash match"
            }
        )
        assert res.status_code == 200, f"Update failed: {res.status_code} - {res.text}"
        data = res.json()
        assert data["difference_status"] == "match"
        print(f"Update deposit: {data['message']}, difference: {data['difference_status']}")
    
    def test_update_deposit_with_shortage(self, admin_token):
        """Test update deposit with shortage (requires reason)"""
        # Create a new deposit first
        test_date = "2026-03-14"
        seed_res = requests.post(
            f"{BASE_URL}/api/deposit/seed-sales?count=2&sales_date={test_date}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        if seed_res.status_code != 200:
            pytest.skip("Could not seed sales for shortage test")
        
        create_res = requests.post(
            f"{BASE_URL}/api/deposit/create",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json={"sales_date": test_date, "shift_id": "", "notes": "Test shortage"}
        )
        if create_res.status_code != 200:
            pytest.skip("Could not create deposit for shortage test")
        
        deposit_id = create_res.json()["id"]
        
        # Get cash_should_deposit
        detail_res = requests.get(
            f"{BASE_URL}/api/deposit/{deposit_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        cash_should = detail_res.json().get("cash_should_deposit", 100000)
        
        # Try to update with shortage but NO reason (should fail)
        res = requests.put(
            f"{BASE_URL}/api/deposit/{deposit_id}",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json={
                "cash_received": cash_should - 10000,  # 10k short
                "difference_reason": "",  # Empty reason - should fail
                "admin_fee": 0,
                "notes": ""
            }
        )
        assert res.status_code == 400, "Should fail without difference reason"
        print(f"Correctly rejected shortage without reason: {res.json().get('detail')}")
        
        # Now update with reason (should succeed)
        res2 = requests.put(
            f"{BASE_URL}/api/deposit/{deposit_id}",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json={
                "cash_received": cash_should - 10000,
                "difference_reason": "Kembalian salah hitung",
                "admin_fee": 0,
                "notes": ""
            }
        )
        assert res2.status_code == 200, f"Update with reason failed: {res2.text}"
        assert res2.json()["difference_status"] == "short"
        print(f"Update with shortage + reason: SUCCESS")


class TestDepositWorkflow:
    """Tests for deposit workflow: receive -> verify -> approve -> post"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if res.status_code == 200:
            return res.json().get("token")
        pytest.skip("Admin login failed")
    
    @pytest.fixture(scope="class")
    def workflow_deposit(self, admin_token):
        """Create a deposit for workflow testing"""
        test_date = "2026-03-15"
        
        # Seed sales
        requests.post(
            f"{BASE_URL}/api/deposit/seed-sales?count=4&sales_date={test_date}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        # Create deposit
        create_res = requests.post(
            f"{BASE_URL}/api/deposit/create",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json={"sales_date": test_date, "shift_id": "", "notes": "Workflow test"}
        )
        if create_res.status_code != 200:
            pytest.skip(f"Could not create deposit: {create_res.text}")
        
        deposit = create_res.json()
        
        # Get detail to know cash_should_deposit
        detail_res = requests.get(
            f"{BASE_URL}/api/deposit/{deposit['id']}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        detail = detail_res.json()
        
        # Update with cash received (with small shortage for accounting test)
        requests.put(
            f"{BASE_URL}/api/deposit/{deposit['id']}",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json={
                "cash_received": detail["cash_should_deposit"] - 5000,
                "difference_reason": "Test shortage for journal entry",
                "admin_fee": 0,
                "notes": ""
            }
        )
        
        return {"id": deposit["id"], "deposit_number": deposit["deposit_number"]}
    
    def test_workflow_step1_receive(self, admin_token, workflow_deposit):
        """Test receive deposit: POST /api/deposit/{id}/receive"""
        res = requests.post(
            f"{BASE_URL}/api/deposit/{workflow_deposit['id']}/receive",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            }
        )
        assert res.status_code == 200, f"Receive failed: {res.status_code} - {res.text}"
        print(f"Workflow step 1 - Receive: {res.json()['message']}")
    
    def test_workflow_step2_verify(self, admin_token, workflow_deposit):
        """Test verify deposit: POST /api/deposit/{id}/verify"""
        res = requests.post(
            f"{BASE_URL}/api/deposit/{workflow_deposit['id']}/verify",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json={"verified": True, "notes": "Verified by pytest"}
        )
        assert res.status_code == 200, f"Verify failed: {res.status_code} - {res.text}"
        print(f"Workflow step 2 - Verify: {res.json()['message']}")
    
    def test_workflow_step3_approve(self, admin_token, workflow_deposit):
        """Test approve deposit: POST /api/deposit/{id}/approve"""
        res = requests.post(
            f"{BASE_URL}/api/deposit/{workflow_deposit['id']}/approve",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json={"approved": True, "notes": "Approved by pytest"}
        )
        assert res.status_code == 200, f"Approve failed: {res.status_code} - {res.text}"
        print(f"Workflow step 3 - Approve: {res.json()['message']}")
    
    def test_workflow_step4_post_journal(self, admin_token, workflow_deposit):
        """Test post deposit to journal: POST /api/deposit/{id}/post"""
        res = requests.post(
            f"{BASE_URL}/api/deposit/{workflow_deposit['id']}/post",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            }
        )
        assert res.status_code == 200, f"Post failed: {res.status_code} - {res.text}"
        data = res.json()
        assert "journal_number" in data
        print(f"Workflow step 4 - Post: {data['message']}")
        print(f"Journal created: {data['journal_number']}")
    
    def test_verify_posted_deposit(self, admin_token, workflow_deposit):
        """Verify deposit is posted with journal number"""
        res = requests.get(
            f"{BASE_URL}/api/deposit/{workflow_deposit['id']}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert res.status_code == 200
        data = res.json()
        
        assert data["status"] == "posted"
        assert data["journal_number"] is not None
        print(f"Deposit {data['deposit_number']} posted with journal {data['journal_number']}")
        print(f"Difference: {data['difference_amount']} ({data['difference_status']})")


class TestDepositList:
    """Tests for listing deposits with filters"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if res.status_code == 200:
            return res.json().get("token")
        pytest.skip("Admin login failed")
    
    def test_list_all_deposits(self, admin_token):
        """Test list all deposits: GET /api/deposit/list"""
        res = requests.get(
            f"{BASE_URL}/api/deposit/list",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert res.status_code == 200, f"List failed: {res.status_code} - {res.text}"
        data = res.json()
        
        assert "deposits" in data
        assert "total" in data
        assert "scope" in data
        print(f"Total deposits: {data['total']}")
        print(f"User scope: can_view_all={data['scope'].get('can_view_all')}")
    
    def test_list_deposits_by_status(self, admin_token):
        """Test list deposits filtered by status"""
        res = requests.get(
            f"{BASE_URL}/api/deposit/list?status=posted",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert res.status_code == 200
        data = res.json()
        
        # All returned deposits should have posted status
        for dep in data["deposits"]:
            assert dep["status"] == "posted"
        print(f"Posted deposits: {len(data['deposits'])}")
    
    def test_list_deposits_with_difference(self, admin_token):
        """Test list deposits with difference filter"""
        res = requests.get(
            f"{BASE_URL}/api/deposit/list?has_difference=yes",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert res.status_code == 200
        data = res.json()
        
        # All returned deposits should have non-zero difference
        for dep in data["deposits"]:
            assert dep["difference_amount"] != 0
        print(f"Deposits with difference: {len(data['deposits'])}")


class TestDepositDashboard:
    """Tests for deposit dashboard"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if res.status_code == 200:
            return res.json().get("token")
        pytest.skip("Admin login failed")
    
    def test_dashboard_summary(self, admin_token):
        """Test dashboard summary: GET /api/deposit/dashboard/summary"""
        res = requests.get(
            f"{BASE_URL}/api/deposit/dashboard/summary",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert res.status_code == 200, f"Dashboard failed: {res.status_code} - {res.text}"
        data = res.json()
        
        # Verify all dashboard fields
        assert "pending_deposit" in data
        assert "pending_verification" in data
        assert "pending_approval" in data
        assert "with_difference" in data
        assert "today" in data
        
        print(f"Dashboard: pending={data['pending_deposit']}, verify={data['pending_verification']}, approve={data['pending_approval']}, diff={data['with_difference']}")


class TestRoleBasedAccess:
    """Tests for role-based access control on deposit system"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if res.status_code == 200:
            return res.json().get("token")
        pytest.skip("Admin login failed")
    
    def test_kasir_login(self):
        """Test kasir login"""
        res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": KASIR_EMAIL,
            "password": KASIR_PASSWORD
        })
        # Kasir might not exist - this is expected behavior
        if res.status_code == 200:
            print(f"Kasir login SUCCESS")
            return res.json().get("token")
        else:
            print(f"Kasir login failed (may not exist): {res.status_code}")
            pytest.skip("Kasir test user not available")
    
    def test_admin_full_access(self, admin_token):
        """Test admin has full access to deposit system"""
        res = requests.get(
            f"{BASE_URL}/api/deposit/list",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert res.status_code == 200
        data = res.json()
        
        # Admin should have can_view_all
        scope = data.get("scope", {})
        assert scope.get("can_view_all") == True or scope.get("filter_applied") == False
        print(f"Admin scope: {scope}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
