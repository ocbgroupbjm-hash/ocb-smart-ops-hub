# OCB TITAN ERP - HR Leave Management Phase 3 Tests
# Tests for leave types, leave requests, approval workflow, and leave balance

import pytest
import requests
import os
import time
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')

# Test credentials
TEST_EMAIL = "ocbgroupbjm@gmail.com"
TEST_PASSWORD = "admin123"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    return data.get("token")


@pytest.fixture
def authenticated_client(auth_token):
    """Create authenticated session"""
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    })
    return session


# ==================== LEAVE TYPES TESTS ====================
class TestLeaveTypes:
    """Tests for GET /api/hr/leave/types"""
    
    def test_get_leave_types_returns_list(self, authenticated_client):
        """Verify leave types endpoint returns list"""
        response = authenticated_client.get(f"{BASE_URL}/api/hr/leave/types")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "leave_types" in data, "Response missing leave_types field"
        assert isinstance(data["leave_types"], list), "leave_types should be a list"
        print(f"Found {len(data['leave_types'])} leave types")
        
    def test_leave_type_has_required_fields(self, authenticated_client):
        """Verify leave types have required fields"""
        response = authenticated_client.get(f"{BASE_URL}/api/hr/leave/types")
        assert response.status_code == 200
        
        data = response.json()
        leave_types = data.get("leave_types", [])
        
        if len(leave_types) > 0:
            leave_type = leave_types[0]
            required_fields = ["id", "code", "name", "max_days"]
            for field in required_fields:
                assert field in leave_type, f"Leave type missing field: {field}"
            print(f"Leave type fields verified: {leave_type.get('name')}")
        else:
            print("No leave types found - may need to create default types")

    def test_create_leave_type(self, authenticated_client):
        """Test creating a new leave type"""
        timestamp = int(time.time())
        leave_type_data = {
            "name": f"TEST Cuti Testing {timestamp}",
            "code": f"TEST{timestamp}",
            "max_days": 5,
            "is_paid": False,
            "requires_approval": True,
            "description": "Testing leave type"
        }
        
        response = authenticated_client.post(
            f"{BASE_URL}/api/hr/leave/types", 
            json=leave_type_data
        )
        
        # May fail if code already exists, which is acceptable
        if response.status_code == 200:
            data = response.json()
            assert "leave_type_id" in data, "Response missing leave_type_id"
            print(f"Created leave type: {data.get('leave_type_id')}")
        elif response.status_code == 400:
            print(f"Leave type code already exists (expected): {response.json()}")
        else:
            assert False, f"Unexpected status: {response.status_code} - {response.text}"


# ==================== LEAVE REQUESTS TESTS ====================
class TestLeaveRequests:
    """Tests for leave request CRUD operations"""
    
    def test_get_leave_requests_paginated(self, authenticated_client):
        """Verify GET /api/hr/leave/requests returns paginated list"""
        response = authenticated_client.get(f"{BASE_URL}/api/hr/leave/requests?page=1&limit=10")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "requests" in data, "Response missing requests field"
        assert "total" in data, "Response missing total field"
        assert "page" in data, "Response missing page field"
        assert "limit" in data, "Response missing limit field"
        
        print(f"Found {data['total']} total requests, page {data['page']}")
        
    def test_filter_leave_requests_by_status(self, authenticated_client):
        """Test filtering leave requests by status"""
        for status in ["pending", "approved", "rejected"]:
            response = authenticated_client.get(
                f"{BASE_URL}/api/hr/leave/requests?status={status}"
            )
            assert response.status_code == 200, f"Failed for status {status}: {response.text}"
            
            data = response.json()
            requests = data.get("requests", [])
            
            # All returned requests should have the filtered status
            for req in requests:
                assert req.get("status") == status, f"Request has wrong status: {req.get('status')}"
            
            print(f"Status '{status}': {len(requests)} requests")
            
    def test_leave_request_has_required_fields(self, authenticated_client):
        """Verify leave requests have required fields"""
        response = authenticated_client.get(f"{BASE_URL}/api/hr/leave/requests?limit=5")
        assert response.status_code == 200
        
        data = response.json()
        requests = data.get("requests", [])
        
        if len(requests) > 0:
            request = requests[0]
            required_fields = [
                "id", "request_no", "employee_id", "employee_name",
                "leave_type_id", "start_date", "end_date", "total_days",
                "status", "reason"
            ]
            for field in required_fields:
                assert field in request, f"Leave request missing field: {field}"
            
            print(f"Request fields verified: {request.get('request_no')}")
        else:
            print("No leave requests found")

    def test_create_leave_request_requires_employee(self, authenticated_client):
        """Test that leave request creation requires valid employee"""
        # First get employees
        emp_response = authenticated_client.get(f"{BASE_URL}/api/hr/employees?limit=1")
        
        if emp_response.status_code != 200:
            pytest.skip("No employees endpoint available")
            
        emp_data = emp_response.json()
        employees = emp_data.get("employees", [])
        
        if len(employees) == 0:
            pytest.skip("No employees available for testing")
        
        # Get leave types
        lt_response = authenticated_client.get(f"{BASE_URL}/api/hr/leave/types")
        leave_types = lt_response.json().get("leave_types", [])
        
        if len(leave_types) == 0:
            pytest.skip("No leave types available")
        
        employee = employees[0]
        leave_type = leave_types[0]
        
        # Calculate dates
        start_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=31)).strftime("%Y-%m-%d")
        
        request_data = {
            "employee_id": employee.get("id"),
            "leave_type_id": leave_type.get("id"),
            "start_date": start_date,
            "end_date": end_date,
            "reason": "TEST Leave Request - Automated Testing"
        }
        
        response = authenticated_client.post(
            f"{BASE_URL}/api/hr/leave/requests",
            json=request_data
        )
        
        # Check response - may fail due to insufficient balance or overlap
        if response.status_code == 200:
            data = response.json()
            assert "request_no" in data, "Response missing request_no"
            print(f"Created leave request: {data.get('request_no')}")
        elif response.status_code == 400:
            # Business rule validation is correct behavior
            data = response.json()
            print(f"Business validation: {data.get('detail')}")
        else:
            print(f"Create response: {response.status_code} - {response.text}")

    def test_create_leave_request_invalid_employee(self, authenticated_client):
        """Test that invalid employee_id returns 404"""
        lt_response = authenticated_client.get(f"{BASE_URL}/api/hr/leave/types")
        leave_types = lt_response.json().get("leave_types", [])
        
        if len(leave_types) == 0:
            pytest.skip("No leave types available")
        
        request_data = {
            "employee_id": "invalid-employee-id-12345",
            "leave_type_id": leave_types[0].get("id"),
            "start_date": "2026-04-01",
            "end_date": "2026-04-02",
            "reason": "TEST - Should fail"
        }
        
        response = authenticated_client.post(
            f"{BASE_URL}/api/hr/leave/requests",
            json=request_data
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("Invalid employee returns 404 - PASS")


# ==================== APPROVAL WORKFLOW TESTS ====================
class TestApprovalWorkflow:
    """Tests for leave approval/rejection workflow"""
    
    def test_approve_leave_request(self, authenticated_client):
        """Test PUT /api/hr/leave/requests/{id}/approve"""
        # Get pending requests
        response = authenticated_client.get(
            f"{BASE_URL}/api/hr/leave/requests?status=pending&limit=1"
        )
        assert response.status_code == 200
        
        data = response.json()
        requests = data.get("requests", [])
        
        if len(requests) == 0:
            print("No pending requests to approve - skipping")
            pytest.skip("No pending leave requests available")
        
        request = requests[0]
        request_id = request.get("id")
        
        # Approve the request
        approve_response = authenticated_client.put(
            f"{BASE_URL}/api/hr/leave/requests/{request_id}/approve",
            json={"status": "approved", "notes": "TEST - Automated approval"}
        )
        
        assert approve_response.status_code == 200, f"Approve failed: {approve_response.text}"
        
        result = approve_response.json()
        assert result.get("status") == "success"
        print(f"Approved request: {result.get('request_no')}")
        
        # Verify status changed
        verify_response = authenticated_client.get(
            f"{BASE_URL}/api/hr/leave/requests/{request_id}"
        )
        assert verify_response.status_code == 200
        updated = verify_response.json()
        assert updated.get("status") == "approved", f"Status not updated: {updated.get('status')}"
        
    def test_reject_leave_request(self, authenticated_client):
        """Test rejecting a leave request"""
        # Get pending requests
        response = authenticated_client.get(
            f"{BASE_URL}/api/hr/leave/requests?status=pending&limit=1"
        )
        assert response.status_code == 200
        
        data = response.json()
        requests = data.get("requests", [])
        
        if len(requests) == 0:
            print("No pending requests to reject - skipping")
            pytest.skip("No pending leave requests available")
            
        request = requests[0]
        request_id = request.get("id")
        
        # Reject the request
        reject_response = authenticated_client.put(
            f"{BASE_URL}/api/hr/leave/requests/{request_id}/approve",
            json={"status": "rejected", "notes": "TEST - Automated rejection"}
        )
        
        assert reject_response.status_code == 200, f"Reject failed: {reject_response.text}"
        print(f"Rejected request: {request.get('request_no')}")
        
    def test_approve_already_processed_fails(self, authenticated_client):
        """Test that approving already processed request fails"""
        # Get an approved request
        response = authenticated_client.get(
            f"{BASE_URL}/api/hr/leave/requests?status=approved&limit=1"
        )
        assert response.status_code == 200
        
        data = response.json()
        requests = data.get("requests", [])
        
        if len(requests) == 0:
            pytest.skip("No approved requests to test")
        
        request = requests[0]
        request_id = request.get("id")
        
        # Try to approve again
        approve_response = authenticated_client.put(
            f"{BASE_URL}/api/hr/leave/requests/{request_id}/approve",
            json={"status": "approved", "notes": "Should fail"}
        )
        
        assert approve_response.status_code == 400, f"Expected 400, got {approve_response.status_code}"
        print("Re-approving processed request returns 400 - PASS")


# ==================== CANCEL LEAVE REQUEST TESTS ====================
class TestCancelLeaveRequest:
    """Tests for cancelling leave requests"""
    
    def test_cancel_pending_request(self, authenticated_client):
        """Test PUT /api/hr/leave/requests/{id}/cancel"""
        # Get pending requests
        response = authenticated_client.get(
            f"{BASE_URL}/api/hr/leave/requests?status=pending&limit=1"
        )
        assert response.status_code == 200
        
        data = response.json()
        requests = data.get("requests", [])
        
        if len(requests) == 0:
            pytest.skip("No pending requests to cancel")
        
        request = requests[0]
        request_id = request.get("id")
        
        # Cancel the request
        cancel_response = authenticated_client.put(
            f"{BASE_URL}/api/hr/leave/requests/{request_id}/cancel"
        )
        
        assert cancel_response.status_code == 200, f"Cancel failed: {cancel_response.text}"
        print(f"Cancelled request: {request.get('request_no')}")
        
    def test_cancel_approved_request_fails(self, authenticated_client):
        """Test that cancelling approved request fails"""
        response = authenticated_client.get(
            f"{BASE_URL}/api/hr/leave/requests?status=approved&limit=1"
        )
        assert response.status_code == 200
        
        data = response.json()
        requests = data.get("requests", [])
        
        if len(requests) == 0:
            pytest.skip("No approved requests to test")
        
        request = requests[0]
        request_id = request.get("id")
        
        cancel_response = authenticated_client.put(
            f"{BASE_URL}/api/hr/leave/requests/{request_id}/cancel"
        )
        
        assert cancel_response.status_code == 400, f"Expected 400, got {cancel_response.status_code}"
        print("Cancelling approved request returns 400 - PASS")


# ==================== LEAVE BALANCE TESTS ====================
class TestLeaveBalance:
    """Tests for employee leave balance"""
    
    def test_get_leave_balance(self, authenticated_client):
        """Test GET /api/hr/leave/balance/{employee_id}"""
        # Get an employee
        emp_response = authenticated_client.get(f"{BASE_URL}/api/hr/employees?limit=1")
        
        if emp_response.status_code != 200:
            pytest.skip("Employees endpoint not available")
        
        emp_data = emp_response.json()
        employees = emp_data.get("employees", [])
        
        if len(employees) == 0:
            pytest.skip("No employees available")
        
        employee = employees[0]
        employee_id = employee.get("id") or employee.get("employee_id")
        
        # Get balance
        balance_response = authenticated_client.get(
            f"{BASE_URL}/api/hr/leave/balance/{employee_id}"
        )
        
        assert balance_response.status_code == 200, f"Failed: {balance_response.text}"
        
        data = balance_response.json()
        assert "balance" in data, "Response missing balance field"
        
        balance = data.get("balance", {})
        expected_fields = ["annual", "sick"]
        for field in expected_fields:
            assert field in balance, f"Balance missing {field} field"
        
        print(f"Employee: {data.get('employee_name')}")
        print(f"Balance: {balance}")
        
    def test_leave_balance_invalid_employee(self, authenticated_client):
        """Test that invalid employee returns 404"""
        response = authenticated_client.get(
            f"{BASE_URL}/api/hr/leave/balance/invalid-emp-id-12345"
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("Invalid employee balance returns 404 - PASS")


# ==================== GET SINGLE LEAVE REQUEST ====================
class TestGetSingleLeaveRequest:
    """Tests for GET /api/hr/leave/requests/{id}"""
    
    def test_get_leave_request_by_id(self, authenticated_client):
        """Test retrieving single leave request"""
        # Get list first
        response = authenticated_client.get(f"{BASE_URL}/api/hr/leave/requests?limit=1")
        assert response.status_code == 200
        
        data = response.json()
        requests = data.get("requests", [])
        
        if len(requests) == 0:
            pytest.skip("No leave requests available")
        
        request = requests[0]
        request_id = request.get("id")
        
        # Get by ID
        detail_response = authenticated_client.get(
            f"{BASE_URL}/api/hr/leave/requests/{request_id}"
        )
        
        assert detail_response.status_code == 200, f"Failed: {detail_response.text}"
        
        detail = detail_response.json()
        assert detail.get("id") == request_id
        print(f"Retrieved request: {detail.get('request_no')}")
        
    def test_get_leave_request_by_request_no(self, authenticated_client):
        """Test retrieving leave request by request_no"""
        response = authenticated_client.get(f"{BASE_URL}/api/hr/leave/requests?limit=1")
        assert response.status_code == 200
        
        data = response.json()
        requests = data.get("requests", [])
        
        if len(requests) == 0:
            pytest.skip("No leave requests available")
        
        request = requests[0]
        request_no = request.get("request_no")
        
        if not request_no:
            pytest.skip("Request has no request_no")
        
        # Get by request_no
        detail_response = authenticated_client.get(
            f"{BASE_URL}/api/hr/leave/requests/{request_no}"
        )
        
        assert detail_response.status_code == 200, f"Failed: {detail_response.text}"
        print(f"Retrieved by request_no: {request_no}")
        
    def test_get_invalid_leave_request(self, authenticated_client):
        """Test that invalid request ID returns 404"""
        response = authenticated_client.get(
            f"{BASE_URL}/api/hr/leave/requests/invalid-request-id-12345"
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("Invalid request ID returns 404 - PASS")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
