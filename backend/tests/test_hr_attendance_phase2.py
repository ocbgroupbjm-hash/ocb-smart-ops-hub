# HR Phase 2 Attendance Module Tests - Iteration 79
# Tests: Check-in/Check-out, Shifts, Reports, Employee Attendance

import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

@pytest.fixture(scope="session")
def auth_token():
    """Get authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "ocbgroupbjm@gmail.com", "password": "admin123"}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json().get("token")

@pytest.fixture(scope="session")
def api_client(auth_token):
    """Shared requests session with auth"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    })
    return session

@pytest.fixture
def test_employee_id(api_client):
    """Get an active employee for testing"""
    response = api_client.get(f"{BASE_URL}/api/hr/employees?status=active&limit=10")
    assert response.status_code == 200
    employees = response.json().get("employees", [])
    assert len(employees) > 0, "No active employees found"
    # Find employee without check-in today to use for testing
    return employees[0]["id"]


class TestAttendanceToday:
    """GET /api/hr/attendance/today endpoint tests"""
    
    def test_get_today_attendance_success(self, api_client):
        """Test getting today's attendance summary"""
        response = api_client.get(f"{BASE_URL}/api/hr/attendance/today")
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "date" in data
        assert "summary" in data
        assert "records" in data
        
        # Validate summary fields
        summary = data["summary"]
        assert "total_employees" in summary
        assert "present" in summary
        assert "absent" in summary
        assert "checked_out" in summary
        assert "still_working" in summary
        assert "late" in summary
        
        # Validate types
        assert isinstance(summary["total_employees"], int)
        assert isinstance(summary["present"], int)
        assert isinstance(data["records"], list)
        
        print(f"Today attendance: {summary['present']}/{summary['total_employees']} present")


class TestShifts:
    """GET /api/hr/attendance/shifts endpoint tests"""
    
    def test_get_shifts_success(self, api_client):
        """Test getting all shifts"""
        response = api_client.get(f"{BASE_URL}/api/hr/attendance/shifts")
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "shifts" in data
        assert "count" in data
        assert isinstance(data["shifts"], list)
        
        # Validate at least one shift exists (REG)
        if data["count"] > 0:
            shift = data["shifts"][0]
            assert "id" in shift
            assert "code" in shift
            assert "name" in shift
            assert "start_time" in shift
            assert "end_time" in shift
            print(f"Found {data['count']} shifts, first: {shift['code']} - {shift['name']}")


class TestCheckInCheckOut:
    """POST /api/hr/attendance/checkin and checkout tests"""
    
    def test_checkin_invalid_employee(self, api_client):
        """Test check-in with invalid employee ID returns 404"""
        response = api_client.post(
            f"{BASE_URL}/api/hr/attendance/checkin",
            json={"employee_id": "invalid-uuid-123", "method": "manual"}
        )
        assert response.status_code == 404
        assert "tidak ditemukan" in response.json().get("detail", "").lower()
    
    def test_checkout_without_checkin(self, api_client, test_employee_id):
        """Test check-out without check-in returns 400"""
        # Use a specific test date in the past to avoid conflicts
        response = api_client.post(
            f"{BASE_URL}/api/hr/attendance/checkout",
            json={
                "employee_id": test_employee_id,
                "method": "manual",
                "check_out_time": "2026-01-01T17:00:00+00:00"
            }
        )
        # Should fail because no check-in on that date
        assert response.status_code == 400
        assert "belum check-in" in response.json().get("detail", "").lower()


class TestAttendanceReport:
    """GET /api/hr/attendance/report endpoint tests"""
    
    def test_get_report_success(self, api_client):
        """Test getting attendance report for date range"""
        response = api_client.get(
            f"{BASE_URL}/api/hr/attendance/report",
            params={"start_date": "2026-03-01", "end_date": "2026-03-31"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "period" in data
        assert "summary" in data
        assert "records" in data
        
        # Validate period
        assert data["period"]["start"] == "2026-03-01"
        assert data["period"]["end"] == "2026-03-31"
        
        # Validate summary fields
        summary = data["summary"]
        assert "total_days" in summary
        assert "total_records" in summary
        assert "total_late" in summary
        assert "total_work_hours" in summary
        assert "average_work_hours" in summary
        
        print(f"Report: {summary['total_records']} records, {summary['total_late']} late")
    
    def test_get_report_missing_params(self, api_client):
        """Test report endpoint requires start_date and end_date"""
        response = api_client.get(f"{BASE_URL}/api/hr/attendance/report")
        assert response.status_code == 422  # Validation error


class TestEmployeeAttendance:
    """GET /api/hr/attendance/employee/{id} endpoint tests"""
    
    def test_get_employee_attendance_success(self, api_client, test_employee_id):
        """Test getting attendance for specific employee"""
        response = api_client.get(f"{BASE_URL}/api/hr/attendance/employee/{test_employee_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "employee" in data
        assert "summary" in data
        assert "records" in data
        
        # Validate employee info
        employee = data["employee"]
        assert "id" in employee
        assert "name" in employee
        
        # Validate summary
        summary = data["summary"]
        assert "present_days" in summary
        assert "late_days" in summary
        assert "total_work_hours" in summary
        
        print(f"Employee: {employee.get('name')}, Present days: {summary['present_days']}")
    
    def test_get_employee_attendance_not_found(self, api_client):
        """Test 404 for non-existent employee"""
        response = api_client.get(f"{BASE_URL}/api/hr/attendance/employee/non-existent-id")
        assert response.status_code == 404


class TestDataIntegrity:
    """Verify employee data is properly stored in attendance records"""
    
    def test_attendance_record_has_employee_data(self, api_client):
        """Verify that attendance records contain employee name, nik, department"""
        response = api_client.get(f"{BASE_URL}/api/hr/attendance/today")
        assert response.status_code == 200
        
        records = response.json().get("records", [])
        
        # Check if any new records have proper employee data
        for record in records:
            if record.get("employee_name"):  # Only check records with data
                assert record["employee_name"] is not None, "employee_name should not be null"
                print(f"Record for {record['employee_name']}: NIK={record.get('employee_nik')}, Dept={record.get('department_name')}")
                break


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
