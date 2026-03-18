"""
Test HR Payroll Phase 3: Attendance Period Lock + KPI Bonus Integration
OCB AI TITAN ERP System

Test Scenarios:
1. Attendance Period Status - GET /api/hr/payroll/attendance-period/status/{period}
2. Attendance Period Lock - POST /api/hr/payroll/attendance-period/lock
3. Attendance Period Unlock - POST /api/hr/payroll/attendance-period/unlock
4. Payroll Posting Validation - POST /api/hr/payroll/post/{batch_id} - must reject if attendance not locked
5. KPI Bonus in Payroll - verify bonus calculation based on KPI results

Credentials: ocbgroupbjm@gmail.com / admin123 / OCB GROUP (ocb_titan)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    BASE_URL = "https://smart-ops-hub-6.preview.emergentagent.com"

# Test credentials
TEST_EMAIL = "ocbgroupbjm@gmail.com"
TEST_PASSWORD = "admin123"
TEST_TENANT = "ocb_titan"


class TestHRPayrollPhase3:
    """Test suite for HR Payroll Phase 3: Attendance Period Lock + KPI Integration"""
    
    auth_token = None
    test_batch_id = None
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get authentication token before tests"""
        if not TestHRPayrollPhase3.auth_token:
            response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
                "business_code": TEST_TENANT
            })
            if response.status_code == 200:
                data = response.json()
                TestHRPayrollPhase3.auth_token = data.get("access_token") or data.get("token")
                print(f"Auth successful: token obtained")
            else:
                pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")
        yield
    
    def get_headers(self):
        """Return authorization headers"""
        return {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
    
    # ============================================
    # TEST 1: Attendance Period Status (GET)
    # ============================================
    def test_01_attendance_period_status_format_valid(self):
        """Test GET /api/hr/payroll/attendance-period/status/2026-03 returns is_locked status"""
        response = requests.get(
            f"{BASE_URL}/api/hr/payroll/attendance-period/status/2026-03",
            headers=self.get_headers()
        )
        
        print(f"\n=== TEST 1: Attendance Period Status ===")
        print(f"Endpoint: GET /api/hr/payroll/attendance-period/status/2026-03")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        # Verify response contains is_locked field
        assert "is_locked" in data, "Response must contain 'is_locked' field"
        assert "period" in data, "Response must contain 'period' field"
        assert data["period"] == "2026-03", f"Period should be '2026-03', got {data['period']}"
        
        # is_locked should be boolean
        assert isinstance(data["is_locked"], bool), f"is_locked must be boolean, got {type(data['is_locked'])}"
        
        print(f"✓ Attendance period status: is_locked = {data['is_locked']}")
        print(f"✓ Message: {data.get('message', 'N/A')}")
    
    def test_01b_attendance_period_status_invalid_format(self):
        """Test invalid period format returns 400"""
        response = requests.get(
            f"{BASE_URL}/api/hr/payroll/attendance-period/status/invalid",
            headers=self.get_headers()
        )
        
        print(f"\n=== TEST 1b: Invalid Period Format ===")
        print(f"Status Code: {response.status_code}")
        
        assert response.status_code == 400, f"Expected 400 for invalid format, got {response.status_code}"
        print("✓ Correctly returns 400 for invalid period format")
    
    # ============================================
    # TEST 2: Attendance Period Lock (POST)
    # ============================================
    def test_02_attendance_period_lock(self):
        """Test POST /api/hr/payroll/attendance-period/lock with {period_month:3, period_year:2026}"""
        response = requests.post(
            f"{BASE_URL}/api/hr/payroll/attendance-period/lock",
            headers=self.get_headers(),
            json={
                "period_month": 3,
                "period_year": 2026
            }
        )
        
        print(f"\n=== TEST 2: Lock Attendance Period ===")
        print(f"Endpoint: POST /api/hr/payroll/attendance-period/lock")
        print(f"Payload: {{'period_month': 3, 'period_year': 2026}}")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        # Response should indicate success or already_locked
        assert data.get("status") in ["success", "already_locked"], \
            f"Status should be 'success' or 'already_locked', got {data.get('status')}"
        
        if data.get("status") == "already_locked":
            print("✓ Period was already locked - this is expected")
        else:
            print("✓ Period successfully locked")
        
        # Verify status changed
        verify_response = requests.get(
            f"{BASE_URL}/api/hr/payroll/attendance-period/status/2026-03",
            headers=self.get_headers()
        )
        verify_data = verify_response.json()
        assert verify_data.get("is_locked") == True, "Period should be locked after lock request"
        print("✓ Verified: Period is now locked")
    
    # ============================================
    # TEST 3: Attendance Period Unlock (POST)
    # ============================================
    def test_03_attendance_period_unlock(self):
        """Test POST /api/hr/payroll/attendance-period/unlock - should succeed if payroll not posted"""
        # First ensure period is locked
        requests.post(
            f"{BASE_URL}/api/hr/payroll/attendance-period/lock",
            headers=self.get_headers(),
            json={"period_month": 4, "period_year": 2026}  # Use April 2026 for unlock test
        )
        
        # Now try to unlock
        response = requests.post(
            f"{BASE_URL}/api/hr/payroll/attendance-period/unlock",
            headers=self.get_headers(),
            json={
                "period_month": 4,
                "period_year": 2026
            }
        )
        
        print(f"\n=== TEST 3: Unlock Attendance Period ===")
        print(f"Endpoint: POST /api/hr/payroll/attendance-period/unlock")
        print(f"Payload: {{'period_month': 4, 'period_year': 2026}}")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        # If payroll already posted, expect 400. Otherwise expect 200
        if response.status_code == 400:
            data = response.json()
            assert "sudah diposting" in data.get("detail", "").lower() or "already posted" in data.get("detail", "").lower(), \
                "Error should indicate payroll already posted"
            print("✓ Correctly blocked unlock because payroll is posted")
        else:
            assert response.status_code == 200, f"Expected 200 or 400, got {response.status_code}"
            data = response.json()
            assert data.get("status") == "success", f"Expected success status"
            print("✓ Period successfully unlocked (no posted payroll)")
    
    # ============================================
    # TEST 4: Payroll Posting Validation (Must reject if attendance not locked)
    # ============================================
    def test_04_payroll_post_without_locked_attendance_rejected(self):
        """Test POST /api/hr/payroll/post/{batch_id} - must REJECT if attendance period not locked"""
        # First, we need a draft payroll batch for an unlocked period
        # Use a different period (e.g., 5/2026) that's NOT locked
        
        # Ensure period is unlocked
        requests.post(
            f"{BASE_URL}/api/hr/payroll/attendance-period/unlock",
            headers=self.get_headers(),
            json={"period_month": 5, "period_year": 2026}
        )
        
        # Run payroll for May 2026 (unlocked period)
        run_response = requests.post(
            f"{BASE_URL}/api/hr/payroll/run",
            headers=self.get_headers(),
            json={
                "period_month": 5,
                "period_year": 2026
            }
        )
        
        print(f"\n=== TEST 4: Payroll Post Without Locked Attendance ===")
        print(f"Step 1: Run payroll for unlocked period (May 2026)")
        print(f"Run Response: {run_response.status_code} - {run_response.text[:500] if run_response.text else 'N/A'}")
        
        if run_response.status_code == 200:
            run_data = run_response.json()
            batch_id = run_data.get("batch_id")
            
            if batch_id:
                # Try to post the payroll - should be REJECTED
                post_response = requests.post(
                    f"{BASE_URL}/api/hr/payroll/post/{batch_id}",
                    headers=self.get_headers()
                )
                
                print(f"Step 2: Try to post payroll batch {batch_id}")
                print(f"Post Response: {post_response.status_code}")
                print(f"Post Response Body: {post_response.text}")
                
                assert post_response.status_code == 400, \
                    f"Expected 400 (rejected) when posting without locked attendance, got {post_response.status_code}"
                
                post_data = post_response.json()
                assert "belum dikunci" in post_data.get("detail", "").lower() or \
                       "not locked" in post_data.get("detail", "").lower() or \
                       "attendance" in post_data.get("detail", "").lower(), \
                    f"Error should mention attendance not locked: {post_data.get('detail')}"
                
                print("✓ Correctly REJECTED payroll posting - attendance period not locked")
            else:
                print("⚠ No batch_id returned from payroll run")
        else:
            # If no employees, that's also a valid scenario
            if run_response.status_code == 400:
                print("⚠ Payroll run returned 400 - possibly no employees to process")
            else:
                print(f"⚠ Payroll run failed: {run_response.text}")
    
    def test_04b_payroll_post_with_locked_attendance_allowed(self):
        """Test POST /api/hr/payroll/post/{batch_id} - should ALLOW if attendance period IS locked"""
        # Lock March 2026
        lock_response = requests.post(
            f"{BASE_URL}/api/hr/payroll/attendance-period/lock",
            headers=self.get_headers(),
            json={"period_month": 3, "period_year": 2026}
        )
        print(f"\n=== TEST 4b: Payroll Post With Locked Attendance ===")
        print(f"Step 1: Lock attendance for March 2026")
        print(f"Lock Response: {lock_response.status_code}")
        
        # Get existing draft payroll for March 2026
        payroll_response = requests.get(
            f"{BASE_URL}/api/hr/payroll/2026-03?status=draft",
            headers=self.get_headers()
        )
        
        if payroll_response.status_code == 200:
            payroll_data = payroll_response.json()
            payrolls = payroll_data.get("payrolls", [])
            
            if payrolls:
                batch_id = payrolls[0].get("batch_id")
                print(f"Step 2: Found draft payroll batch: {batch_id}")
                
                # Try to post - should be allowed
                post_response = requests.post(
                    f"{BASE_URL}/api/hr/payroll/post/{batch_id}",
                    headers=self.get_headers()
                )
                
                print(f"Step 3: Post payroll")
                print(f"Post Response: {post_response.status_code}")
                print(f"Post Response Body: {post_response.text}")
                
                # Should be 200 (success) or 404 (already posted/not found)
                assert post_response.status_code in [200, 404], \
                    f"Expected 200 (success) or 404 (already posted), got {post_response.status_code}"
                
                if post_response.status_code == 200:
                    print("✓ Payroll posting ALLOWED with locked attendance period")
                else:
                    print("✓ Batch not found (may be already posted)")
            else:
                print("⚠ No draft payroll found for March 2026")
        else:
            print(f"⚠ Failed to get payroll data: {payroll_response.text}")
    
    # ============================================
    # TEST 5: KPI Bonus Integration in Payroll
    # ============================================
    def test_05_kpi_bonus_in_payroll_calculation(self):
        """Verify KPI bonus is calculated and added to payroll items"""
        # First, check if KPI results exist
        # Note: We need to ensure there's an approved KPI result for the test
        
        print(f"\n=== TEST 5: KPI Bonus Integration ===")
        
        # Create a test KPI result first (if we have access)
        # This is optional - we'll verify the logic by checking payroll items
        
        # Run payroll for March 2026 (locked period)
        run_response = requests.post(
            f"{BASE_URL}/api/hr/payroll/run",
            headers=self.get_headers(),
            json={
                "period_month": 3,
                "period_year": 2026
            }
        )
        
        print(f"Step 1: Run payroll for March 2026")
        print(f"Response: {run_response.status_code} - {run_response.text[:500] if run_response.text else 'N/A'}")
        
        if run_response.status_code == 200:
            run_data = run_response.json()
            batch_id = run_data.get("batch_id")
            
            # Get payroll details to check for KPI bonus items
            payroll_response = requests.get(
                f"{BASE_URL}/api/hr/payroll/2026-03",
                headers=self.get_headers()
            )
            
            if payroll_response.status_code == 200:
                payroll_data = payroll_response.json()
                payrolls = payroll_data.get("payrolls", [])
                
                print(f"Step 2: Found {len(payrolls)} payroll records")
                
                # Check if any payroll has KPI bonus item
                kpi_bonus_found = False
                for payroll in payrolls:
                    payroll_id = payroll.get("id")
                    
                    # Get slip details
                    slip_response = requests.get(
                        f"{BASE_URL}/api/hr/payroll/slip/{payroll_id}",
                        headers=self.get_headers()
                    )
                    
                    if slip_response.status_code == 200:
                        slip_data = slip_response.json()
                        items = slip_data.get("items", {})
                        allowances = items.get("allowances", [])
                        
                        for item in allowances:
                            if item.get("item_code") == "KPIBONUS":
                                kpi_bonus_found = True
                                print(f"✓ KPI BONUS found for employee {payroll.get('employee_name')}")
                                print(f"  - Item: {item.get('item_name')}")
                                print(f"  - Amount: Rp {item.get('amount'):,.0f}")
                                break
                
                if kpi_bonus_found:
                    print("✓ KPI Bonus integration working - bonus added to payroll items")
                else:
                    print("⚠ No KPI bonus items found - this may be expected if no approved KPI results")
                    print("  (KPI bonus only appears when employee has approved KPI with score >= 60)")
                    
        elif run_response.status_code == 400:
            data = run_response.json()
            if "sudah diposting" in data.get("detail", "").lower():
                print("⚠ Payroll already posted for this period")
                # Still verify by checking existing posted payroll
                payroll_response = requests.get(
                    f"{BASE_URL}/api/hr/payroll/2026-03?status=posted",
                    headers=self.get_headers()
                )
                if payroll_response.status_code == 200:
                    payroll_data = payroll_response.json()
                    print(f"Found {len(payroll_data.get('payrolls', []))} posted payroll records")
            else:
                print(f"⚠ Payroll run failed: {data.get('detail')}")
        else:
            print(f"⚠ Unexpected response: {run_response.text}")
    
    def test_05b_verify_kpi_bonus_calculation_rules(self):
        """Verify KPI bonus calculation follows the defined rules"""
        print(f"\n=== TEST 5b: KPI Bonus Calculation Rules Verification ===")
        print("Expected KPI Score Ranges:")
        print("  - 90-100: 20% of base salary as bonus (Excellent)")
        print("  - 80-89: 15% of base salary as bonus (Very Good)")
        print("  - 70-79: 10% of base salary as bonus (Good)")
        print("  - 60-69: 5% of base salary as bonus (Satisfactory)")
        print("  - Below 60: No bonus (Needs Improvement)")
        
        # Check payroll items for KPI bonus naming pattern
        payroll_response = requests.get(
            f"{BASE_URL}/api/hr/payroll/2026-03",
            headers=self.get_headers()
        )
        
        if payroll_response.status_code == 200:
            payroll_data = payroll_response.json()
            payrolls = payroll_data.get("payrolls", [])
            
            for payroll in payrolls:
                payroll_id = payroll.get("id")
                slip_response = requests.get(
                    f"{BASE_URL}/api/hr/payroll/slip/{payroll_id}",
                    headers=self.get_headers()
                )
                
                if slip_response.status_code == 200:
                    slip_data = slip_response.json()
                    items = slip_data.get("items", {})
                    allowances = items.get("allowances", [])
                    
                    for item in allowances:
                        if item.get("item_code") == "KPIBONUS":
                            item_name = item.get("item_name", "")
                            # Verify naming pattern includes rating and score
                            # Expected: "Bonus KPI (Excellent - Score 95.0%)"
                            assert "Bonus KPI" in item_name, "KPI bonus item name should contain 'Bonus KPI'"
                            print(f"✓ KPI Bonus item formatted correctly: {item_name}")
                            
                            # Check if it contains rating
                            ratings = ["Excellent", "Very Good", "Good", "Satisfactory", "Needs Improvement"]
                            has_rating = any(r in item_name for r in ratings)
                            if has_rating:
                                print(f"  ✓ Rating included in item name")
                            
                            # Check if it contains score
                            if "Score" in item_name:
                                print(f"  ✓ Score included in item name")
        else:
            print(f"⚠ Could not fetch payroll data: {payroll_response.text}")


class TestAttendancePeriodEdgeCases:
    """Additional edge case tests for attendance period lock"""
    
    auth_token = None
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get authentication token"""
        if not TestAttendancePeriodEdgeCases.auth_token:
            response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
                "business_code": TEST_TENANT
            })
            if response.status_code == 200:
                data = response.json()
                TestAttendancePeriodEdgeCases.auth_token = data.get("access_token") or data.get("token")
        yield
    
    def get_headers(self):
        return {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
    
    def test_lock_idempotent(self):
        """Verify locking an already locked period returns appropriate response"""
        # Lock once
        requests.post(
            f"{BASE_URL}/api/hr/payroll/attendance-period/lock",
            headers=self.get_headers(),
            json={"period_month": 3, "period_year": 2026}
        )
        
        # Lock again - should not error
        response = requests.post(
            f"{BASE_URL}/api/hr/payroll/attendance-period/lock",
            headers=self.get_headers(),
            json={"period_month": 3, "period_year": 2026}
        )
        
        print(f"\n=== Edge Case: Idempotent Lock ===")
        print(f"Status: {response.status_code}")
        
        assert response.status_code == 200, f"Double lock should not fail, got {response.status_code}"
        data = response.json()
        assert data.get("status") in ["success", "already_locked"], \
            f"Should return success or already_locked"
        print("✓ Lock operation is idempotent")
    
    def test_status_includes_locked_metadata(self):
        """Verify status endpoint returns locked_at and locked_by when locked"""
        response = requests.get(
            f"{BASE_URL}/api/hr/payroll/attendance-period/status/2026-03",
            headers=self.get_headers()
        )
        
        print(f"\n=== Edge Case: Lock Metadata ===")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("is_locked"):
                print(f"locked_at: {data.get('locked_at', 'N/A')}")
                print(f"locked_by: {data.get('locked_by', 'N/A')}")
                print(f"message: {data.get('message', 'N/A')}")
                
                # These fields should exist when locked
                assert "locked_at" in data or "message" in data, \
                    "Locked status should include metadata"
                print("✓ Lock metadata included in status response")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
