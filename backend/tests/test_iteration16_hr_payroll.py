"""
OCB TITAN AI - Iteration 16 Full HR & Payroll System Audit Tests
Testing all modules: Master Jabatan, Master Shift, Lokasi Absensi, Aturan Payroll, 
Data Karyawan, Absensi, Payroll Calculation, Struktur Organisasi, Cuti/Izin, Training.
"""

import pytest
import requests
import os
from datetime import datetime, timedelta
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://smart-ops-hub-6.preview.emergentagent.com').rstrip('/')

# Test credentials from context
TEST_EMAIL = "ocbgroupbjm@gmail.com"
TEST_PASSWORD = "admin123"
TEST_DATABASE = "OCB GROUP"

# Generate unique test identifiers
TEST_PREFIX = f"TEST{datetime.now().strftime('%H%M')}"


class TestHealthAndAuth:
    """Test health check and authentication"""
    
    def test_health_check(self):
        """Verify backend is healthy"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print(f"✓ Health check passed - System: {data.get('system')}")

    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "database": TEST_DATABASE
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data or "access_token" in data
        print(f"✓ Login successful - User: {data.get('user', {}).get('name', 'N/A')}")


class TestMasterJabatan:
    """Test Master Jabatan CRUD - position management"""
    
    def test_list_jabatan(self):
        """Get all jabatan positions"""
        response = requests.get(f"{BASE_URL}/api/erp/master/jabatan")
        assert response.status_code == 200
        data = response.json()
        assert "jabatan" in data
        print(f"✓ List Jabatan - Total: {len(data['jabatan'])}")
        return data['jabatan']
    
    def test_create_jabatan(self):
        """Create new jabatan position"""
        payload = {
            "code": f"{TEST_PREFIX}_JAB",
            "name": f"Test Position {TEST_PREFIX}",
            "level": 3,
            "department": "Testing"
        }
        response = requests.post(f"{BASE_URL}/api/erp/master/jabatan", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "jabatan" in data or "message" in data
        print(f"✓ Create Jabatan - Code: {payload['code']}")
        return data.get("jabatan", {}).get("id")
    
    def test_update_jabatan(self):
        """Update existing jabatan"""
        # First create one
        create_payload = {
            "code": f"{TEST_PREFIX}_JABUPD",
            "name": f"Test Update Position",
            "level": 2,
            "department": "Testing"
        }
        create_res = requests.post(f"{BASE_URL}/api/erp/master/jabatan", json=create_payload)
        assert create_res.status_code == 200
        jab_id = create_res.json().get("jabatan", {}).get("id")
        
        if jab_id:
            update_payload = {"name": "Updated Position Name"}
            update_res = requests.put(f"{BASE_URL}/api/erp/master/jabatan/{jab_id}", json=update_payload)
            assert update_res.status_code == 200
            print(f"✓ Update Jabatan ID: {jab_id}")


class TestMasterShift:
    """Test Master Shift CRUD - shift management"""
    
    def test_list_shifts(self):
        """Get all shifts"""
        response = requests.get(f"{BASE_URL}/api/erp/master/shifts")
        assert response.status_code == 200
        data = response.json()
        assert "shifts" in data
        print(f"✓ List Shifts - Total: {len(data['shifts'])}")
        return data['shifts']
    
    def test_create_shift(self):
        """Create new shift with code field"""
        payload = {
            "code": f"{TEST_PREFIX}_SFT",
            "name": f"Test Shift {TEST_PREFIX}",
            "start_time": "09:00",
            "end_time": "18:00",
            "break_minutes": 60
        }
        response = requests.post(f"{BASE_URL}/api/erp/master/shifts", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "shift" in data or "message" in data
        print(f"✓ Create Shift - Code: {payload['code']}")
    
    def test_update_shift(self):
        """Update existing shift"""
        # First create one
        create_payload = {
            "code": f"{TEST_PREFIX}_SFTUPD",
            "name": f"Shift To Update",
            "start_time": "07:00",
            "end_time": "15:00",
            "break_minutes": 45
        }
        create_res = requests.post(f"{BASE_URL}/api/erp/master/shifts", json=create_payload)
        assert create_res.status_code == 200
        shift_id = create_res.json().get("shift", {}).get("id")
        
        if shift_id:
            update_payload = {"name": "Updated Shift Name", "break_minutes": 30}
            update_res = requests.put(f"{BASE_URL}/api/erp/master/shifts/{shift_id}", json=update_payload)
            assert update_res.status_code == 200
            print(f"✓ Update Shift ID: {shift_id}")


class TestMasterLokasiAbsensi:
    """Test Master Lokasi Absensi CRUD - GPS location for attendance"""
    
    def test_list_lokasi_absensi(self):
        """Get all lokasi absensi"""
        response = requests.get(f"{BASE_URL}/api/erp/master/lokasi-absensi")
        assert response.status_code == 200
        data = response.json()
        assert "lokasi" in data
        print(f"✓ List Lokasi Absensi - Total: {len(data['lokasi'])}")
        return data['lokasi']
    
    def test_create_lokasi_absensi(self):
        """Create lokasi with branch_id and branch_name"""
        payload = {
            "branch_id": f"{TEST_PREFIX}_BR",
            "branch_name": f"Test Branch {TEST_PREFIX}",
            "latitude": -3.316694,
            "longitude": 114.590111,
            "radius_meters": 150,
            "address": "Test Address for GPS Absensi"
        }
        response = requests.post(f"{BASE_URL}/api/erp/master/lokasi-absensi", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "lokasi" in data or "message" in data
        print(f"✓ Create Lokasi Absensi - Branch: {payload['branch_name']}")
    
    def test_update_lokasi_absensi(self):
        """Update existing lokasi absensi"""
        create_payload = {
            "branch_id": f"{TEST_PREFIX}_BRUPD",
            "branch_name": f"Branch To Update",
            "latitude": -3.320000,
            "longitude": 114.600000,
            "radius_meters": 100,
            "address": "Initial Address"
        }
        create_res = requests.post(f"{BASE_URL}/api/erp/master/lokasi-absensi", json=create_payload)
        assert create_res.status_code == 200
        lokasi_id = create_res.json().get("lokasi", {}).get("id")
        
        if lokasi_id:
            update_payload = {"radius_meters": 200, "address": "Updated Address"}
            update_res = requests.put(f"{BASE_URL}/api/erp/master/lokasi-absensi/{lokasi_id}", json=update_payload)
            assert update_res.status_code == 200
            print(f"✓ Update Lokasi ID: {lokasi_id}")


class TestPayrollRules:
    """Test Aturan Payroll CRUD"""
    
    def test_list_payroll_rules(self):
        """Get all payroll rules"""
        response = requests.get(f"{BASE_URL}/api/erp/master/payroll-rules")
        assert response.status_code == 200
        data = response.json()
        assert "rules" in data
        print(f"✓ List Payroll Rules - Total: {len(data['rules'])}")
        return data['rules']
    
    def test_create_payroll_rule(self):
        """Create payroll rule linked to jabatan"""
        payload = {
            "jabatan_id": f"{TEST_PREFIX}_JABPR",
            "jabatan_name": f"Test Position for Payroll {TEST_PREFIX}",
            "gaji_pokok": 5000000,
            "tunjangan_jabatan": 500000,
            "tunjangan_transport": 300000,
            "tunjangan_makan": 200000,
            "bonus_kehadiran_full": 400000,
            "potongan_telat_per_menit": 1000,
            "potongan_alpha_per_hari": 50000
        }
        response = requests.post(f"{BASE_URL}/api/erp/master/payroll-rules", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "rule" in data or "message" in data
        print(f"✓ Create Payroll Rule - Jabatan: {payload['jabatan_name']}, Gaji: Rp{payload['gaji_pokok']:,}")


class TestEmployeeCRUD:
    """Test Data Karyawan CRUD"""
    
    def test_list_employees(self):
        """Get all active employees"""
        response = requests.get(f"{BASE_URL}/api/erp/employees", params={"status": "active"})
        assert response.status_code == 200
        data = response.json()
        assert "employees" in data
        print(f"✓ List Employees - Total: {len(data['employees'])}")
        return data['employees']
    
    def test_create_employee(self):
        """Create new employee"""
        payload = {
            "nik": f"{TEST_PREFIX}001",
            "name": f"Test Karyawan {TEST_PREFIX}",
            "email": f"test_{TEST_PREFIX.lower()}@test.com",
            "phone": "081234567890",
            "jabatan_name": "Staff",
            "department": "Testing",
            "branch_name": "Test Branch",
            "contract_type": "kontrak",
            "gaji_pokok": 4000000
        }
        response = requests.post(f"{BASE_URL}/api/erp/employees", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "employee" in data or "message" in data
        print(f"✓ Create Employee - NIK: {payload['nik']}, Name: {payload['name']}")
        return data.get("employee", {}).get("id")
    
    def test_get_employee_by_id(self):
        """Get employee by ID"""
        # First create an employee
        emp_id = self.test_create_employee()
        if emp_id:
            response = requests.get(f"{BASE_URL}/api/erp/employees/{emp_id}")
            assert response.status_code == 200
            data = response.json()
            assert data.get("nik") or data.get("name")
            print(f"✓ Get Employee by ID: {emp_id}")
    
    def test_update_employee(self):
        """Update employee data"""
        # First create
        create_payload = {
            "nik": f"{TEST_PREFIX}UPD",
            "name": "Employee To Update"
        }
        create_res = requests.post(f"{BASE_URL}/api/erp/employees", json=create_payload)
        assert create_res.status_code == 200
        emp_id = create_res.json().get("employee", {}).get("id")
        
        if emp_id:
            update_payload = {"name": "Updated Employee Name", "gaji_pokok": 5500000}
            update_res = requests.put(f"{BASE_URL}/api/erp/employees/{emp_id}", json=update_payload)
            assert update_res.status_code == 200
            print(f"✓ Update Employee ID: {emp_id}")
    
    def test_delete_employee(self):
        """Delete employee"""
        # First create
        create_payload = {
            "nik": f"{TEST_PREFIX}DEL",
            "name": "Employee To Delete"
        }
        create_res = requests.post(f"{BASE_URL}/api/erp/employees", json=create_payload)
        assert create_res.status_code == 200
        emp_id = create_res.json().get("employee", {}).get("id")
        
        if emp_id:
            delete_res = requests.delete(f"{BASE_URL}/api/erp/employees/{emp_id}")
            assert delete_res.status_code == 200
            print(f"✓ Delete Employee ID: {emp_id}")


class TestAttendance:
    """Test Absensi Check-in/Check-out dengan GPS"""
    
    def test_check_in(self):
        """Test attendance check-in with GPS"""
        # First get an employee
        emp_res = requests.get(f"{BASE_URL}/api/erp/employees", params={"status": "active"})
        employees = emp_res.json().get("employees", [])
        
        if not employees:
            # Create a test employee first
            create_payload = {
                "nik": f"{TEST_PREFIX}CHK",
                "name": f"Checkin Test Employee {TEST_PREFIX}"
            }
            requests.post(f"{BASE_URL}/api/erp/employees", json=create_payload)
            emp_res = requests.get(f"{BASE_URL}/api/erp/employees", params={"status": "active"})
            employees = emp_res.json().get("employees", [])
        
        if employees:
            emp = employees[0]
            payload = {
                "employee_id": emp.get("id"),
                "employee_nik": emp.get("nik"),
                "employee_name": emp.get("name"),
                "jabatan": emp.get("jabatan_name", ""),
                "branch_id": emp.get("branch_id", "TEST_BRANCH"),
                "branch_name": emp.get("branch_name", "Test Branch"),
                "latitude": -3.316694,
                "longitude": 114.590111,
                "address": "Test Check-in Location",
                "device": "Test Device"
            }
            response = requests.post(f"{BASE_URL}/api/attendance/check-in", json=payload)
            # Could be 200 (success) or 400 (already checked in today)
            assert response.status_code in [200, 400]
            print(f"✓ Check-in tested for: {emp.get('name')} - Status: {response.status_code}")
    
    def test_check_out(self):
        """Test attendance check-out"""
        # Get employee who has checked in
        emp_res = requests.get(f"{BASE_URL}/api/erp/employees", params={"status": "active"})
        employees = emp_res.json().get("employees", [])
        
        if employees:
            emp = employees[0]
            payload = {
                "employee_id": emp.get("id"),
                "latitude": -3.316694,
                "longitude": 114.590111,
                "address": "Test Check-out Location",
                "device": "Test Device"
            }
            response = requests.post(f"{BASE_URL}/api/attendance/check-out", json=payload)
            # Could be 200 (success) or 400 (not checked in yet / already checked out)
            assert response.status_code in [200, 400]
            print(f"✓ Check-out tested for: {emp.get('name')} - Status: {response.status_code}")
    
    def test_list_attendance(self):
        """Get attendance list"""
        today = datetime.now().strftime("%Y-%m-%d")
        response = requests.get(f"{BASE_URL}/api/attendance/list", params={"tanggal": today})
        assert response.status_code == 200
        data = response.json()
        assert "attendance" in data
        print(f"✓ List Attendance for {today} - Total: {len(data['attendance'])}")
    
    def test_daily_summary(self):
        """Get daily attendance summary"""
        response = requests.get(f"{BASE_URL}/api/attendance/summary/daily")
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data or "total_karyawan" in data
        print(f"✓ Daily Summary fetched successfully")


class TestIzinCuti:
    """Test Pengajuan Cuti/Izin dan Approval workflow"""
    
    def test_create_izin(self):
        """Create izin/cuti request"""
        # Get employee first
        emp_res = requests.get(f"{BASE_URL}/api/erp/employees", params={"status": "active"})
        employees = emp_res.json().get("employees", [])
        
        if employees:
            emp = employees[0]
            tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            payload = {
                "employee_id": emp.get("id"),
                "employee_nik": emp.get("nik"),
                "employee_name": emp.get("name"),
                "jabatan": emp.get("jabatan_name", ""),
                "branch_id": emp.get("branch_id", ""),
                "branch_name": emp.get("branch_name", ""),
                "tanggal": tomorrow,
                "status": "izin",
                "keterangan": "Test izin request"
            }
            response = requests.post(f"{BASE_URL}/api/attendance/izin", json=payload)
            # Could be 200 (success) or 400 (already exists)
            assert response.status_code in [200, 400]
            print(f"✓ Create Izin tested - Status: {response.status_code}")
            return response.json().get("attendance_id") if response.status_code == 200 else None
    
    def test_get_pending_approvals(self):
        """Get pending approval requests"""
        response = requests.get(f"{BASE_URL}/api/attendance/approvals/pending")
        assert response.status_code == 200
        data = response.json()
        assert "pending" in data
        print(f"✓ Pending Approvals - Total: {len(data['pending'])}")
        return data['pending']
    
    def test_approve_izin(self):
        """Approve izin request"""
        pending = self.test_get_pending_approvals()
        if pending:
            attendance_id = pending[0].get("id")
            response = requests.put(
                f"{BASE_URL}/api/attendance/approvals/{attendance_id}/approve",
                params={"approver_id": "test", "approver_name": "Test Admin"}
            )
            assert response.status_code == 200
            print(f"✓ Approve Izin ID: {attendance_id}")
    
    def test_approval_history(self):
        """Get approval history"""
        response = requests.get(f"{BASE_URL}/api/attendance/approvals/history")
        assert response.status_code == 200
        data = response.json()
        assert "history" in data
        print(f"✓ Approval History - Total: {len(data['history'])}")


class TestPayrollCalculation:
    """Test Payroll Calculation - menghitung Take Home Pay"""
    
    def test_payroll_dashboard_summary(self):
        """Get payroll dashboard summary"""
        response = requests.get(f"{BASE_URL}/api/payroll-files/dashboard-summary")
        assert response.status_code == 200
        data = response.json()
        assert "total_employees" in data or "estimated_monthly_payroll" in data
        print(f"✓ Payroll Dashboard Summary - Employees: {data.get('total_employees', 0)}")
    
    def test_generate_payslip_json(self):
        """Generate payslip in JSON format"""
        # Get employee
        emp_res = requests.get(f"{BASE_URL}/api/erp/employees", params={"status": "active"})
        employees = emp_res.json().get("employees", [])
        
        if employees:
            emp = employees[0]
            response = requests.get(f"{BASE_URL}/api/payroll-files/payslip/{emp['id']}", params={
                "period_month": datetime.now().month,
                "period_year": datetime.now().year,
                "format": "json"
            })
            assert response.status_code == 200
            data = response.json()
            assert "calculation" in data or "take_home_pay" in data or "employee" in data
            print(f"✓ Payslip JSON for {emp.get('name')} generated")
            
            # Verify THP calculation
            if "calculation" in data:
                calc = data["calculation"]
                print(f"  - Gaji Pokok: Rp{calc.get('gaji_pokok', 0):,}")
                print(f"  - Total Tunjangan: Rp{calc.get('tunjangan', {}).get('total', 0):,}")
                print(f"  - Total Potongan: Rp{calc.get('potongan', {}).get('total', 0):,}")
                print(f"  - Take Home Pay: Rp{calc.get('take_home_pay', 0):,}")


class TestStrukturOrganisasi:
    """Test Struktur Organisasi - org chart"""
    
    def test_get_departments(self):
        """Get departments list"""
        response = requests.get(f"{BASE_URL}/api/hr/departments")
        assert response.status_code == 200
        data = response.json()
        assert "departments" in data
        print(f"✓ Departments - Total: {len(data['departments'])}")
    
    def test_get_org_structure(self):
        """Get organization structure"""
        response = requests.get(f"{BASE_URL}/api/hr/organization/structure")
        assert response.status_code == 200
        data = response.json()
        assert "structure" in data
        print(f"✓ Org Structure - Total Departments: {len(data['structure'])}")
    
    def test_get_org_chart(self):
        """Get organization chart data"""
        response = requests.get(f"{BASE_URL}/api/hr/organization/chart")
        assert response.status_code == 200
        data = response.json()
        assert "chart" in data
        print(f"✓ Org Chart - Total nodes: {len(data['chart'])}")
    
    def test_create_department(self):
        """Create new department"""
        payload = {
            "code": f"{TEST_PREFIX}_DPT",
            "name": f"Test Department {TEST_PREFIX}",
            "description": "Test Department for Testing"
        }
        response = requests.post(f"{BASE_URL}/api/hr/departments", json=payload)
        assert response.status_code == 200
        print(f"✓ Create Department - Code: {payload['code']}")


class TestTrainingManagement:
    """Test Training Management"""
    
    def test_list_trainings(self):
        """Get all trainings"""
        response = requests.get(f"{BASE_URL}/api/hr/trainings")
        assert response.status_code == 200
        data = response.json()
        assert "trainings" in data
        print(f"✓ List Trainings - Total: {len(data['trainings'])}")
        return data['trainings']
    
    def test_create_training(self):
        """Create new training"""
        payload = {
            "title": f"Test Training {TEST_PREFIX}",
            "description": "Test training for HR module testing",
            "trainer": "Test Trainer",
            "training_type": "internal",
            "start_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
            "end_date": (datetime.now() + timedelta(days=8)).strftime("%Y-%m-%d"),
            "location": "Test Room",
            "max_participants": 30,
            "is_mandatory": False
        }
        response = requests.post(f"{BASE_URL}/api/hr/trainings", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "training" in data or "message" in data
        print(f"✓ Create Training - Title: {payload['title']}")
        return data.get("training", {}).get("id")
    
    def test_register_for_training(self):
        """Register employee for training"""
        # Get training
        trainings_res = requests.get(f"{BASE_URL}/api/hr/trainings")
        trainings = trainings_res.json().get("trainings", [])
        
        # Get employee
        emp_res = requests.get(f"{BASE_URL}/api/erp/employees", params={"status": "active"})
        employees = emp_res.json().get("employees", [])
        
        if trainings and employees:
            training_id = trainings[0].get("id")
            emp_id = employees[0].get("id")
            
            response = requests.post(f"{BASE_URL}/api/hr/trainings/{training_id}/register/{emp_id}")
            # Could be 200 (success) or 400 (already registered / training full)
            assert response.status_code in [200, 400]
            print(f"✓ Training Registration tested - Status: {response.status_code}")


class TestEmployeeRelations:
    """Test Employee Relations (supervisor, subordinates)"""
    
    def test_get_employee_relations(self):
        """Get employee relations"""
        emp_res = requests.get(f"{BASE_URL}/api/erp/employees", params={"status": "active"})
        employees = emp_res.json().get("employees", [])
        
        if employees:
            emp_id = employees[0].get("id")
            response = requests.get(f"{BASE_URL}/api/hr/employees/{emp_id}/relations")
            assert response.status_code == 200
            data = response.json()
            print(f"✓ Employee Relations for {employees[0].get('name')}")
            if data.get("supervisor"):
                print(f"  - Supervisor: {data['supervisor'].get('name')}")
            print(f"  - Subordinates: {len(data.get('subordinates', []))}")


class TestHRDocuments:
    """Test HR Document Generation"""
    
    def test_generate_sk_pengangkatan(self):
        """Generate SK Pengangkatan document"""
        emp_res = requests.get(f"{BASE_URL}/api/erp/employees", params={"status": "active"})
        employees = emp_res.json().get("employees", [])
        
        if employees:
            emp_id = employees[0].get("id")
            response = requests.get(f"{BASE_URL}/api/hr/documents/generate/sk_pengangkatan/{emp_id}")
            assert response.status_code == 200
            data = response.json()
            assert "content" in data
            print(f"✓ Generated SK Pengangkatan for {employees[0].get('name')}")
    
    def test_generate_surat_referensi(self):
        """Generate Surat Referensi document"""
        emp_res = requests.get(f"{BASE_URL}/api/erp/employees", params={"status": "active"})
        employees = emp_res.json().get("employees", [])
        
        if employees:
            emp_id = employees[0].get("id")
            response = requests.get(f"{BASE_URL}/api/hr/documents/generate/surat_referensi/{emp_id}")
            assert response.status_code == 200
            data = response.json()
            assert "content" in data
            print(f"✓ Generated Surat Referensi for {employees[0].get('name')}")


class TestDropdownJabatanIntegration:
    """Test Dropdown jabatan di form karyawan"""
    
    def test_jabatan_available_for_employee_form(self):
        """Verify jabatan list is available for employee creation form"""
        # This tests the jabatan endpoint that frontend uses for dropdown
        response = requests.get(f"{BASE_URL}/api/erp/master/jabatan")
        assert response.status_code == 200
        data = response.json()
        assert "jabatan" in data
        assert len(data["jabatan"]) >= 0  # Can be empty but should not error
        print(f"✓ Jabatan dropdown data available - Options: {len(data['jabatan'])}")
        
        # Verify structure for dropdown
        if data["jabatan"]:
            jab = data["jabatan"][0]
            assert "id" in jab  # Need id for value
            assert "name" in jab  # Need name for display
            print(f"  - Sample: ID={jab['id'][:8]}..., Name={jab['name']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
