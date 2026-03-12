"""
OCB TITAN ERP - Phase 3 Commission Engine & Cash Control Tests
Tests for:
1. Commission Engine - Policy, Calculate, Simulate, Approve, Pay
2. Cash Control - Shift management, Discrepancies, Deposits
"""

import pytest
import requests
import os
from datetime import datetime, timedelta
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
TEST_PREFIX = "TEST_COMM_CASH_"

# Test Credentials
ADMIN_EMAIL = "ocbgroupbjm@gmail.com"
ADMIN_PASSWORD = "admin123"


class TestSetup:
    """Setup: Get auth token and branch for testing"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        # First select business
        select_res = requests.post(f"{BASE_URL}/api/auth/select-business", json={
            "db_name": "ocb_titan"
        })
        
        # Then login
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token") or data.get("token")
        
        pytest.skip(f"Authentication failed: {response.status_code}")
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        """Headers with auth token"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    @pytest.fixture(scope="class")
    def branch_id(self, headers):
        """Get a branch ID for testing"""
        response = requests.get(f"{BASE_URL}/api/branches", headers=headers)
        if response.status_code == 200:
            data = response.json()
            # Handle both list and dict with "items" key
            if isinstance(data, list):
                items = data
            else:
                items = data.get("items") or []
            if items and len(items) > 0:
                return items[0].get("id")
        return "test-branch-001"


# ==================== COMMISSION ENGINE TESTS ====================

class TestCommissionPolicy(TestSetup):
    """Commission Policy Tests"""
    
    def test_get_commission_policy(self, headers):
        """Test GET /api/commission/policy"""
        response = requests.get(f"{BASE_URL}/api/commission/policy", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        # Verify policy structure
        assert "base_rate" in data, "Policy missing base_rate"
        assert "achievement_multiplier" in data, "Policy missing achievement_multiplier"
        assert "super_bonus_threshold" in data, "Policy missing super_bonus_threshold"
        assert "super_bonus_rate" in data, "Policy missing super_bonus_rate"
        assert "min_achievement_for_commission" in data, "Policy missing min_achievement_for_commission"
        
        # Validate policy values
        assert 0 <= data["base_rate"] <= 1, "base_rate should be 0-1"
        assert data["super_bonus_threshold"] >= 100, "super_bonus_threshold should be >= 100"
        
        print(f"PASS: Commission policy retrieved - base_rate={data['base_rate']}, super_threshold={data['super_bonus_threshold']}")
    
    def test_update_commission_policy(self, headers):
        """Test PUT /api/commission/policy"""
        update_data = {
            "base_rate": 0.025,  # 2.5%
            "min_achievement_for_commission": 60
        }
        
        response = requests.put(
            f"{BASE_URL}/api/commission/policy",
            headers=headers,
            json=update_data
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True, "Update should return success"
        assert "policy" in data, "Should return updated policy"
        assert data["policy"]["base_rate"] == 0.025, "base_rate not updated correctly"
        
        print("PASS: Commission policy updated successfully")
        
        # Revert to original
        revert_data = {
            "base_rate": 0.02,
            "min_achievement_for_commission": 50
        }
        requests.put(f"{BASE_URL}/api/commission/policy", headers=headers, json=revert_data)


class TestCommissionSimulate(TestSetup):
    """Commission Simulation Tests"""
    
    def test_simulate_commission_eligible(self, headers):
        """Test POST /api/commission/simulate - eligible scenario"""
        response = requests.post(
            f"{BASE_URL}/api/commission/simulate?sales_value=10000000&achievement=100",
            headers=headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data.get("eligible") == True, "Should be eligible at 100% achievement"
        assert "base_commission" in data, "Missing base_commission"
        assert "total_commission" in data, "Missing total_commission"
        assert data["total_commission"] > 0, "Total commission should be > 0"
        
        print(f"PASS: Simulation at 100% - Base: {data['base_commission']}, Total: {data['total_commission']}")
    
    def test_simulate_commission_with_super_bonus(self, headers):
        """Test simulation with achievement > 110% (super bonus)"""
        response = requests.post(
            f"{BASE_URL}/api/commission/simulate?sales_value=10000000&achievement=120",
            headers=headers
        )
        
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("eligible") == True
        assert data.get("super_bonus", 0) > 0, "Should have super_bonus at 120%"
        assert data.get("achievement_bonus", 0) > 0, "Should have achievement_bonus at 120%"
        
        print(f"PASS: Simulation at 120% - Super Bonus: {data['super_bonus']}, Achievement Bonus: {data['achievement_bonus']}")
    
    def test_simulate_commission_below_minimum(self, headers):
        """Test simulation below minimum achievement"""
        response = requests.post(
            f"{BASE_URL}/api/commission/simulate?sales_value=10000000&achievement=40",
            headers=headers
        )
        
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("eligible") == False, "Should not be eligible at 40%"
        assert "reason" in data, "Should have reason for ineligibility"
        assert data.get("total_commission") == 0, "Total commission should be 0"
        
        print(f"PASS: Below minimum correctly returns ineligible - reason: {data.get('reason')}")


class TestCommissionCalculate(TestSetup):
    """Commission Calculation Tests"""
    
    def test_calculate_commissions_all(self, headers):
        """Test POST /api/commission/calculate for all"""
        today = datetime.now()
        period_start = today.replace(day=1).strftime("%Y-%m-%d")
        if today.month == 12:
            period_end = today.replace(year=today.year+1, month=1, day=1) - timedelta(days=1)
        else:
            period_end = today.replace(month=today.month+1, day=1) - timedelta(days=1)
        period_end = period_end.strftime("%Y-%m-%d")
        
        payload = {
            "period_type": "monthly",
            "period_start": period_start,
            "period_end": period_end,
            "calculate_for": "all"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/commission/calculate",
            headers=headers,
            json=payload
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True
        assert "calculated" in data, "Missing calculated count"
        assert "skipped" in data, "Missing skipped count"
        
        print(f"PASS: Commission calculation - Calculated: {data['calculated']}, Skipped: {data['skipped']}")


class TestCommissionList(TestSetup):
    """Commission List Tests"""
    
    def test_list_commissions(self, headers):
        """Test GET /api/commission/list"""
        response = requests.get(f"{BASE_URL}/api/commission/list", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "items" in data, "Missing items"
        assert "summary" in data, "Missing summary"
        
        # Validate summary structure
        summary = data["summary"]
        assert "total" in summary
        assert "calculated" in summary
        assert "approved" in summary
        assert "paid" in summary
        assert "total_amount" in summary
        
        print(f"PASS: Commission list - Total: {summary['total']}, Total Amount: {summary['total_amount']}")
    
    def test_list_commissions_with_status_filter(self, headers):
        """Test list with status filter"""
        response = requests.get(
            f"{BASE_URL}/api/commission/list?status=calculated",
            headers=headers
        )
        
        assert response.status_code == 200
        
        data = response.json()
        items = data.get("items", [])
        
        # All items should have calculated status
        for item in items:
            assert item.get("status") == "calculated", f"Expected status 'calculated', got {item.get('status')}"
        
        print(f"PASS: Filtered list - Found {len(items)} calculated commissions")


class TestCommissionDashboard(TestSetup):
    """Commission Dashboard Tests"""
    
    def test_get_dashboard_summary(self, headers):
        """Test GET /api/commission/dashboard/summary"""
        response = requests.get(
            f"{BASE_URL}/api/commission/dashboard/summary?period_type=monthly",
            headers=headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "period_type" in data
        assert "period_start" in data
        assert "period_end" in data
        assert "by_status" in data
        assert "total_commissions" in data
        assert "total_amount" in data
        assert "total_sales" in data
        assert "policy" in data
        
        print(f"PASS: Dashboard summary - Period: {data['period_start']} to {data['period_end']}, Total: {data['total_commissions']}")


class TestCommissionApproveAndPay(TestSetup):
    """Commission Approve and Pay Tests"""
    
    def test_approve_commissions(self, headers):
        """Test POST /api/commission/approve"""
        # First get calculated commissions
        list_res = requests.get(
            f"{BASE_URL}/api/commission/list?status=calculated",
            headers=headers
        )
        
        if list_res.status_code != 200:
            pytest.skip("Could not get commission list")
        
        items = list_res.json().get("items", [])
        if not items:
            pytest.skip("No calculated commissions to approve")
        
        commission_ids = [items[0]["id"]]
        
        response = requests.post(
            f"{BASE_URL}/api/commission/approve",
            headers=headers,
            json={"commission_ids": commission_ids, "notes": "Test approval"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True
        assert data.get("approved") >= 0
        
        print(f"PASS: Approve commissions - Approved: {data.get('approved')}")
    
    def test_pay_commissions(self, headers):
        """Test POST /api/commission/pay"""
        # First get approved commissions
        list_res = requests.get(
            f"{BASE_URL}/api/commission/list?status=approved",
            headers=headers
        )
        
        if list_res.status_code != 200:
            pytest.skip("Could not get commission list")
        
        items = list_res.json().get("items", [])
        if not items:
            pytest.skip("No approved commissions to pay")
        
        commission_ids = [items[0]["id"]]
        
        response = requests.post(
            f"{BASE_URL}/api/commission/pay",
            headers=headers,
            json={
                "commission_ids": commission_ids,
                "payment_method": "bank_transfer",
                "payment_reference": f"TEST-PAY-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True
        assert "paid" in data
        assert "total_amount" in data
        
        print(f"PASS: Pay commissions - Paid: {data.get('paid')}, Amount: {data.get('total_amount')}")


# ==================== CASH CONTROL TESTS ====================

class TestCashControlShift(TestSetup):
    """Cash Control Shift Tests"""
    
    @pytest.fixture(scope="class")
    def test_shift_id(self, headers, branch_id):
        """Create a test shift and return its ID"""
        # First check if there's already an open shift
        current_res = requests.get(
            f"{BASE_URL}/api/cash-control/shift/current",
            headers=headers
        )
        
        if current_res.status_code == 200:
            data = current_res.json()
            if data.get("has_open_shift"):
                return data["shift"]["id"]
        
        # Open new shift
        response = requests.post(
            f"{BASE_URL}/api/cash-control/shift/open",
            headers=headers,
            json={
                "branch_id": branch_id,
                "initial_cash": 500000,
                "notes": f"{TEST_PREFIX}shift"
            }
        )
        
        if response.status_code == 200:
            return response.json().get("shift", {}).get("id")
        
        return None
    
    def test_open_shift(self, headers, branch_id):
        """Test POST /api/cash-control/shift/open"""
        # First check if there's already an open shift
        current_res = requests.get(
            f"{BASE_URL}/api/cash-control/shift/current",
            headers=headers
        )
        
        if current_res.status_code == 200 and current_res.json().get("has_open_shift"):
            print("SKIP: User already has open shift")
            return
        
        response = requests.post(
            f"{BASE_URL}/api/cash-control/shift/open",
            headers=headers,
            json={
                "branch_id": branch_id,
                "initial_cash": 500000,
                "notes": f"{TEST_PREFIX}shift"
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True
        assert "shift" in data
        assert data["shift"].get("status") == "open"
        assert data["shift"].get("initial_cash") == 500000
        
        print(f"PASS: Shift opened - {data['shift'].get('shift_no')}")
    
    def test_get_current_shift(self, headers):
        """Test GET /api/cash-control/shift/current"""
        response = requests.get(
            f"{BASE_URL}/api/cash-control/shift/current",
            headers=headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "has_open_shift" in data
        
        if data["has_open_shift"]:
            assert "shift" in data
            assert "expected_cash" in data["shift"]
            print(f"PASS: Current shift - {data['shift'].get('shift_no')}, Expected: Rp {data['shift'].get('expected_cash')}")
        else:
            print("PASS: No open shift for current user")
    
    def test_list_shifts(self, headers):
        """Test GET /api/cash-control/shifts"""
        response = requests.get(
            f"{BASE_URL}/api/cash-control/shifts",
            headers=headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "items" in data
        assert "summary" in data
        
        summary = data["summary"]
        assert "total" in summary
        assert "open" in summary
        assert "closed" in summary
        
        print(f"PASS: Shifts list - Total: {summary['total']}, Open: {summary['open']}")
    
    def test_list_shifts_with_filter(self, headers):
        """Test shifts list with status filter"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        response = requests.get(
            f"{BASE_URL}/api/cash-control/shifts?date_from={today}&date_to={today}",
            headers=headers
        )
        
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        
        print(f"PASS: Today's shifts - Count: {len(data['items'])}")


class TestCashControlCloseShift(TestSetup):
    """Test closing shift with discrepancy calculation"""
    
    def test_close_shift_with_discrepancy(self, headers):
        """Test POST /api/cash-control/shift/{id}/close"""
        # First get current open shift
        current_res = requests.get(
            f"{BASE_URL}/api/cash-control/shift/current",
            headers=headers
        )
        
        if current_res.status_code != 200 or not current_res.json().get("has_open_shift"):
            pytest.skip("No open shift to close")
        
        shift = current_res.json()["shift"]
        shift_id = shift["id"]
        expected_cash = shift.get("expected_cash", 500000)
        
        # Close with slight discrepancy (overage)
        actual_cash = expected_cash + 5000  # Rp 5000 overage
        
        response = requests.post(
            f"{BASE_URL}/api/cash-control/shift/{shift_id}/close",
            headers=headers,
            json={
                "actual_cash": actual_cash,
                "notes": f"{TEST_PREFIX}close with overage"
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True
        assert "expected_cash" in data
        assert "actual_cash" in data
        assert "discrepancy" in data
        assert "discrepancy_type" in data
        
        print(f"PASS: Shift closed - Expected: {data['expected_cash']}, Actual: {data['actual_cash']}, Discrepancy: {data['discrepancy']} ({data['discrepancy_type']})")


class TestCashControlDashboard(TestSetup):
    """Cash Control Dashboard Tests"""
    
    def test_get_dashboard_summary(self, headers):
        """Test GET /api/cash-control/dashboard/summary"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        response = requests.get(
            f"{BASE_URL}/api/cash-control/dashboard/summary?date={today}",
            headers=headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "date" in data
        assert "shifts" in data
        assert "sales" in data
        assert "discrepancies" in data
        assert "deposits" in data
        
        # Validate shifts structure
        assert "total" in data["shifts"]
        assert "open" in data["shifts"]
        assert "closed" in data["shifts"]
        
        # Validate discrepancies structure
        assert "pending_count" in data["discrepancies"]
        
        print(f"PASS: Cash Control Dashboard - Shifts: {data['shifts']['total']}, Discrepancies: {data['discrepancies']['pending_count']}")


class TestCashControlDiscrepancies(TestSetup):
    """Cash Control Discrepancies Tests"""
    
    def test_list_discrepancies(self, headers):
        """Test GET /api/cash-control/discrepancies"""
        response = requests.get(
            f"{BASE_URL}/api/cash-control/discrepancies",
            headers=headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "items" in data
        assert "summary" in data
        
        summary = data["summary"]
        assert "total" in summary
        assert "pending" in summary
        assert "resolved" in summary
        assert "shortages" in summary
        assert "overages" in summary
        
        print(f"PASS: Discrepancies list - Pending: {summary['pending']}, Shortages: {summary['shortages']}, Overages: {summary['overages']}")
    
    def test_resolve_discrepancy(self, headers):
        """Test POST /api/cash-control/discrepancy/{id}/resolve"""
        # First get pending discrepancies
        list_res = requests.get(
            f"{BASE_URL}/api/cash-control/discrepancies?status=pending",
            headers=headers
        )
        
        if list_res.status_code != 200:
            pytest.skip("Could not get discrepancies")
        
        items = list_res.json().get("items", [])
        if not items:
            pytest.skip("No pending discrepancies to resolve")
        
        discrepancy_id = items[0]["id"]
        
        response = requests.post(
            f"{BASE_URL}/api/cash-control/discrepancy/{discrepancy_id}/resolve",
            headers=headers,
            json={
                "resolution_type": "explained",
                "resolution_notes": f"{TEST_PREFIX}Test resolution - counting error"
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True
        
        print("PASS: Discrepancy resolved successfully")


class TestCashControlDeposits(TestSetup):
    """Cash Control Deposit Tests"""
    
    def test_record_deposit(self, headers):
        """Test POST /api/cash-control/deposit"""
        # First get a shift ID (open or closed)
        shifts_res = requests.get(
            f"{BASE_URL}/api/cash-control/shifts?limit=1",
            headers=headers
        )
        
        if shifts_res.status_code != 200:
            pytest.skip("Could not get shifts")
        
        shifts = shifts_res.json().get("items", [])
        if not shifts:
            pytest.skip("No shifts available for deposit")
        
        shift_id = shifts[0]["id"]
        
        response = requests.post(
            f"{BASE_URL}/api/cash-control/deposit",
            headers=headers,
            json={
                "shift_id": shift_id,
                "deposit_amount": 500000,
                "deposit_method": "cash",
                "notes": f"{TEST_PREFIX}test deposit"
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True
        assert "deposit" in data
        assert data["deposit"].get("deposit_amount") == 500000
        
        print(f"PASS: Deposit recorded - {data['deposit'].get('deposit_no')}, Amount: Rp 500,000")
    
    def test_list_deposits(self, headers):
        """Test GET /api/cash-control/deposits"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        response = requests.get(
            f"{BASE_URL}/api/cash-control/deposits?date_from={today}&date_to={today}",
            headers=headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "items" in data
        assert "summary" in data
        
        summary = data["summary"]
        assert "total" in summary
        assert "total_amount" in summary
        
        print(f"PASS: Deposits list - Count: {summary['total']}, Total: Rp {summary['total_amount']}")


# ==================== INTEGRATION TESTS ====================

class TestIntegration(TestSetup):
    """Integration Tests"""
    
    def test_commission_workflow(self, headers):
        """Test full commission workflow: Policy -> Simulate -> Calculate"""
        # 1. Get policy
        policy_res = requests.get(f"{BASE_URL}/api/commission/policy", headers=headers)
        assert policy_res.status_code == 200
        policy = policy_res.json()
        
        # 2. Simulate with policy values
        sim_res = requests.post(
            f"{BASE_URL}/api/commission/simulate?sales_value=10000000&achievement=105",
            headers=headers
        )
        assert sim_res.status_code == 200
        sim = sim_res.json()
        
        # Verify simulation uses policy
        expected_base = 10000000 * policy["base_rate"]
        assert abs(sim["base_commission"] - expected_base) < 1, "Base commission should match policy"
        
        # 3. Dashboard should reflect policy
        dash_res = requests.get(
            f"{BASE_URL}/api/commission/dashboard/summary",
            headers=headers
        )
        assert dash_res.status_code == 200
        dash = dash_res.json()
        assert dash["policy"]["base_rate"] == policy["base_rate"]
        
        print("PASS: Commission workflow integration verified")
    
    def test_cash_control_workflow(self, headers, branch_id):
        """Test cash control workflow: Dashboard -> Shifts -> Discrepancies"""
        # 1. Get dashboard
        today = datetime.now().strftime("%Y-%m-%d")
        dash_res = requests.get(
            f"{BASE_URL}/api/cash-control/dashboard/summary?date={today}",
            headers=headers
        )
        assert dash_res.status_code == 200
        dash = dash_res.json()
        
        # 2. List shifts
        shifts_res = requests.get(f"{BASE_URL}/api/cash-control/shifts", headers=headers)
        assert shifts_res.status_code == 200
        
        # 3. List discrepancies
        disc_res = requests.get(f"{BASE_URL}/api/cash-control/discrepancies", headers=headers)
        assert disc_res.status_code == 200
        
        # 4. List deposits
        dep_res = requests.get(f"{BASE_URL}/api/cash-control/deposits", headers=headers)
        assert dep_res.status_code == 200
        
        print("PASS: Cash control workflow integration verified")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
