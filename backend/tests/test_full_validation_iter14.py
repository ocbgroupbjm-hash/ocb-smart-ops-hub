"""
OCB TITAN AI - Full System Validation Test Suite
Iteration 14 - Testing:
- Multi-database login (ocb_titan, ocb_unit_4, ocb_unt_1)
- Master ERP CRUD (Shift, Jabatan, Lokasi Absensi, Payroll Rules)
- Employee CRUD
- Product Photo Upload API
- CRM AI Customer (create, list, analyze, auto response)
- HR Training
- Mass Upload Template Download
- Export v2 Employees Excel
- Import Templates
- Attendance Approval
- WhatsApp Alerts
- War Room
"""
import pytest
import requests
import os
import json
from datetime import datetime
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "ocbgroupbjm@gmail.com"
TEST_PASSWORD = "admin123"

# Database names
DATABASES = ["ocb_titan", "ocb_unit_4", "ocb_unt_1"]


class TestMultiDatabaseLogin:
    """Test login across multiple databases"""
    
    def test_business_list(self):
        """List all available businesses"""
        resp = requests.get(f"{BASE_URL}/api/business/list")
        assert resp.status_code == 200
        data = resp.json()
        assert "businesses" in data
        assert len(data["businesses"]) >= 3
        print(f"SUCCESS: Found {len(data['businesses'])} businesses")
    
    @pytest.mark.parametrize("db_name", DATABASES)
    def test_switch_database(self, db_name):
        """Switch to each database"""
        resp = requests.post(f"{BASE_URL}/api/business/switch/{db_name}")
        assert resp.status_code == 200
        data = resp.json()
        assert "message" in data
        print(f"SUCCESS: Switched to {db_name}")
    
    @pytest.mark.parametrize("db_name", DATABASES)
    def test_ensure_admin(self, db_name):
        """Ensure admin user exists in each database"""
        resp = requests.post(
            f"{BASE_URL}/api/business/ensure-admin/{db_name}",
            params={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "message" in data
        print(f"SUCCESS: Admin ensured in {db_name}")
    
    @pytest.mark.parametrize("db_name", DATABASES)
    def test_login_to_database(self, db_name):
        """Login to each database"""
        # First switch to the database
        requests.post(f"{BASE_URL}/api/business/switch/{db_name}")
        
        # Then login
        resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == TEST_EMAIL
        print(f"SUCCESS: Logged into {db_name} - User: {data['user']['name']}")


class TestMasterShiftCRUD:
    """Master Shift CRUD tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Ensure we're on the main database and logged in"""
        requests.post(f"{BASE_URL}/api/business/switch/ocb_titan")
    
    def test_create_shift(self):
        """Create a new shift"""
        test_shift = {
            "code": f"TEST_SHIFT_{uuid.uuid4().hex[:6]}",
            "name": "Test Shift Pagi",
            "start_time": "07:00",
            "end_time": "15:00",
            "break_minutes": 60
        }
        resp = requests.post(f"{BASE_URL}/api/erp/master/shifts", json=test_shift)
        assert resp.status_code == 200
        data = resp.json()
        assert "message" in data
        assert "shift" in data
        print(f"SUCCESS: Created shift - {data['shift']['name']}")
    
    def test_list_shifts(self):
        """List all shifts"""
        resp = requests.get(f"{BASE_URL}/api/erp/master/shifts")
        assert resp.status_code == 200
        data = resp.json()
        assert "shifts" in data
        print(f"SUCCESS: Found {len(data['shifts'])} shifts")
    
    def test_update_shift(self):
        """Create and update a shift"""
        # First create
        test_shift = {
            "code": f"UPD_SHIFT_{uuid.uuid4().hex[:6]}",
            "name": "Shift To Update",
            "start_time": "08:00",
            "end_time": "16:00",
            "break_minutes": 60
        }
        create_resp = requests.post(f"{BASE_URL}/api/erp/master/shifts", json=test_shift)
        assert create_resp.status_code == 200
        shift_id = create_resp.json()["shift"]["id"]
        
        # Then update
        update_data = {
            "code": test_shift["code"],
            "name": "Updated Shift Name",
            "start_time": "09:00",
            "end_time": "17:00",
            "break_minutes": 45
        }
        update_resp = requests.put(f"{BASE_URL}/api/erp/master/shifts/{shift_id}", json=update_data)
        assert update_resp.status_code == 200
        print(f"SUCCESS: Updated shift {shift_id}")


class TestMasterJabatanCRUD:
    """Master Jabatan CRUD tests"""
    
    def test_create_jabatan(self):
        """Create a new jabatan"""
        test_jabatan = {
            "code": f"TEST_JAB_{uuid.uuid4().hex[:6]}",
            "name": "Test Jabatan Manager",
            "level": 2,
            "department": "Operasional"
        }
        resp = requests.post(f"{BASE_URL}/api/erp/master/jabatan", json=test_jabatan)
        assert resp.status_code == 200
        data = resp.json()
        assert "message" in data
        print(f"SUCCESS: Created jabatan - {data['jabatan']['name']}")
    
    def test_list_jabatan(self):
        """List all jabatan"""
        resp = requests.get(f"{BASE_URL}/api/erp/master/jabatan")
        assert resp.status_code == 200
        data = resp.json()
        assert "jabatan" in data
        print(f"SUCCESS: Found {len(data['jabatan'])} jabatan")


class TestMasterLokasiAbsensi:
    """Master Lokasi Absensi CRUD tests"""
    
    def test_create_lokasi_absensi(self):
        """Create lokasi absensi"""
        test_lokasi = {
            "branch_id": f"TEST_BRANCH_{uuid.uuid4().hex[:6]}",
            "branch_name": "Test Branch",
            "latitude": -3.316694,
            "longitude": 114.590111,
            "radius_meters": 100,
            "address": "Test Address, Banjarmasin"
        }
        resp = requests.post(f"{BASE_URL}/api/erp/master/lokasi-absensi", json=test_lokasi)
        assert resp.status_code == 200
        data = resp.json()
        assert "lokasi" in data
        print(f"SUCCESS: Created lokasi absensi at {test_lokasi['address']}")
    
    def test_list_lokasi_absensi(self):
        """List all lokasi absensi"""
        resp = requests.get(f"{BASE_URL}/api/erp/master/lokasi-absensi")
        assert resp.status_code == 200
        data = resp.json()
        assert "lokasi" in data
        print(f"SUCCESS: Found {len(data['lokasi'])} lokasi absensi")


class TestMasterPayrollRules:
    """Master Payroll Rules CRUD tests"""
    
    def test_create_payroll_rule(self):
        """Create payroll rule"""
        test_rule = {
            "jabatan_id": f"TEST_JAB_ID_{uuid.uuid4().hex[:6]}",
            "jabatan_name": "Test Jabatan",
            "gaji_pokok": 5000000,
            "tunjangan_jabatan": 500000,
            "tunjangan_transport": 300000,
            "tunjangan_makan": 200000,
            "bonus_kehadiran_full": 250000,
            "potongan_telat_per_menit": 5000,
            "potongan_alpha_per_hari": 200000
        }
        resp = requests.post(f"{BASE_URL}/api/erp/master/payroll-rules", json=test_rule)
        assert resp.status_code == 200
        data = resp.json()
        assert "message" in data
        print(f"SUCCESS: Created payroll rule for {test_rule['jabatan_name']}")
    
    def test_list_payroll_rules(self):
        """List all payroll rules"""
        resp = requests.get(f"{BASE_URL}/api/erp/master/payroll-rules")
        assert resp.status_code == 200
        data = resp.json()
        assert "rules" in data
        print(f"SUCCESS: Found {len(data['rules'])} payroll rules")


class TestEmployeeCRUD:
    """Employee CRUD tests"""
    
    def test_create_employee(self):
        """Create employee"""
        test_emp = {
            "nik": f"TEST_EMP_{uuid.uuid4().hex[:6]}",
            "name": "Test Employee",
            "email": f"test_{uuid.uuid4().hex[:6]}@test.com",
            "phone": "081234567890",
            "jabatan_name": "Staff",
            "department": "Operasional",
            "branch_name": "HQ",
            "join_date": "2024-01-15",
            "contract_type": "tetap",
            "gaji_pokok": 4500000
        }
        resp = requests.post(f"{BASE_URL}/api/erp/employees", json=test_emp)
        assert resp.status_code == 200
        data = resp.json()
        assert "employee" in data
        print(f"SUCCESS: Created employee - {data['employee']['name']}")
        return data["employee"]["id"]
    
    def test_list_employees(self):
        """List employees"""
        resp = requests.get(f"{BASE_URL}/api/erp/employees")
        assert resp.status_code == 200
        data = resp.json()
        assert "employees" in data
        print(f"SUCCESS: Found {len(data['employees'])} employees")
    
    def test_get_employee_detail(self):
        """Get employee detail"""
        # First create an employee
        test_emp = {
            "nik": f"TEST_DET_{uuid.uuid4().hex[:6]}",
            "name": "Employee Detail Test",
            "email": f"detail_{uuid.uuid4().hex[:6]}@test.com"
        }
        create_resp = requests.post(f"{BASE_URL}/api/erp/employees", json=test_emp)
        assert create_resp.status_code == 200
        emp_id = create_resp.json()["employee"]["id"]
        
        # Get detail
        detail_resp = requests.get(f"{BASE_URL}/api/erp/employees/{emp_id}")
        assert detail_resp.status_code == 200
        data = detail_resp.json()
        assert data["id"] == emp_id
        print(f"SUCCESS: Got employee detail - {data['name']}")


class TestProductPhotoUpload:
    """Product Photo Upload API tests"""
    
    def test_product_photo_endpoint_exists(self):
        """Test that product photo upload endpoint exists"""
        # Create a minimal test image (1x1 white pixel PNG)
        import base64
        # 1x1 white PNG in base64
        white_pixel = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
        )
        
        files = {"file": ("test.png", white_pixel, "image/png")}
        data = {"product_id": "test_product_123", "is_primary": "false"}
        
        # This should return 404 if product doesn't exist, but endpoint exists
        resp = requests.post(f"{BASE_URL}/api/files/products/photo", files=files, data=data)
        # Either 200 (success) or 404 (product not found) means endpoint exists
        assert resp.status_code in [200, 404]
        print(f"SUCCESS: Product photo upload endpoint exists - Status: {resp.status_code}")


class TestCRMAICustomer:
    """CRM AI Customer tests"""
    
    def test_create_customer(self):
        """Create CRM customer"""
        test_customer = {
            "name": f"TEST_Customer_{uuid.uuid4().hex[:6]}",
            "phone": f"0812{uuid.uuid4().hex[:8]}",
            "email": f"customer_{uuid.uuid4().hex[:6]}@test.com",
            "address": "Test Address",
            "source": "online",
            "tags": ["test", "vip"]
        }
        resp = requests.post(f"{BASE_URL}/api/crm-ai/customers", json=test_customer)
        assert resp.status_code == 200
        data = resp.json()
        assert "customer" in data
        print(f"SUCCESS: Created customer - {data['customer']['name']}")
        return data["customer"]["id"]
    
    def test_list_customers(self):
        """List CRM customers"""
        resp = requests.get(f"{BASE_URL}/api/crm-ai/customers")
        assert resp.status_code == 200
        data = resp.json()
        assert "customers" in data
        print(f"SUCCESS: Found {len(data['customers'])} customers")
    
    def test_analyze_customer_character(self):
        """Test AI character analysis"""
        # First create a customer
        test_customer = {
            "name": f"Analyze_Customer_{uuid.uuid4().hex[:6]}",
            "phone": f"0813{uuid.uuid4().hex[:8]}"
        }
        create_resp = requests.post(f"{BASE_URL}/api/crm-ai/customers", json=test_customer)
        assert create_resp.status_code == 200
        customer_id = create_resp.json()["customer"]["id"]
        
        # Analyze character
        analyze_resp = requests.post(f"{BASE_URL}/api/crm-ai/customers/{customer_id}/analyze")
        assert analyze_resp.status_code == 200
        data = analyze_resp.json()
        assert "analysis" in data
        print(f"SUCCESS: Analyzed customer character - Buying frequency: {data['analysis']['buying_frequency']}")
    
    def test_auto_response_generation(self):
        """Test auto response generation"""
        # Create customer first
        test_customer = {
            "name": f"AutoResp_Customer_{uuid.uuid4().hex[:6]}",
            "phone": f"0814{uuid.uuid4().hex[:8]}"
        }
        create_resp = requests.post(f"{BASE_URL}/api/crm-ai/customers", json=test_customer)
        assert create_resp.status_code == 200
        customer_id = create_resp.json()["customer"]["id"]
        
        # Generate auto response
        resp = requests.post(
            f"{BASE_URL}/api/crm-ai/generate-response",
            params={"customer_id": customer_id, "incoming_message": "Halo, berapa harga produk ini?"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "generated_response" in data
        assert "detected_intent" in data
        print(f"SUCCESS: Generated auto response - Intent: {data['detected_intent']}")


class TestHRTraining:
    """HR Training CRUD tests"""
    
    def test_create_training(self):
        """Create training"""
        test_training = {
            "title": f"TEST_Training_{uuid.uuid4().hex[:6]}",
            "description": "Test Training Description",
            "trainer": "Test Trainer",
            "training_type": "internal",
            "start_date": "2024-02-01",
            "end_date": "2024-02-03",
            "location": "Training Room",
            "max_participants": 30,
            "is_mandatory": False
        }
        resp = requests.post(f"{BASE_URL}/api/hr/trainings", json=test_training)
        assert resp.status_code == 200
        data = resp.json()
        assert "training" in data
        print(f"SUCCESS: Created training - {data['training']['title']}")
    
    def test_list_trainings(self):
        """List trainings"""
        resp = requests.get(f"{BASE_URL}/api/hr/trainings")
        assert resp.status_code == 200
        data = resp.json()
        assert "trainings" in data
        print(f"SUCCESS: Found {len(data['trainings'])} trainings")


class TestHRMassUploadTemplate:
    """HR Mass Upload Template tests"""
    
    def test_download_employee_template(self):
        """Download employee upload template"""
        resp = requests.get(f"{BASE_URL}/api/hr/employees/upload-template")
        assert resp.status_code == 200
        assert "spreadsheet" in resp.headers.get("content-type", "") or len(resp.content) > 0
        print(f"SUCCESS: Downloaded employee template - Size: {len(resp.content)} bytes")


class TestExportV2:
    """Export v2 tests"""
    
    def test_export_employees_excel(self):
        """Export employees to Excel"""
        resp = requests.get(f"{BASE_URL}/api/export-v2/hr/employees?format=xlsx")
        assert resp.status_code == 200
        content_type = resp.headers.get("content-type", "")
        assert "spreadsheet" in content_type or "xlsx" in content_type or len(resp.content) > 0
        print(f"SUCCESS: Exported employees to Excel - Size: {len(resp.content)} bytes")
    
    def test_export_employees_csv(self):
        """Export employees to CSV"""
        resp = requests.get(f"{BASE_URL}/api/export-v2/hr/employees?format=csv")
        assert resp.status_code == 200
        print(f"SUCCESS: Exported employees to CSV - Size: {len(resp.content)} bytes")
    
    def test_export_employees_pdf(self):
        """Export employees to PDF"""
        resp = requests.get(f"{BASE_URL}/api/export-v2/hr/employees?format=pdf")
        assert resp.status_code == 200
        print(f"SUCCESS: Exported employees to PDF - Size: {len(resp.content)} bytes")


class TestImportSystem:
    """Import System tests"""
    
    def test_list_import_templates(self):
        """List all import templates"""
        resp = requests.get(f"{BASE_URL}/api/import/templates")
        assert resp.status_code == 200
        data = resp.json()
        assert "templates" in data
        # Should have at least these templates: products, suppliers, customers, branches, employees, stock_awal, saldo_awal, kpi_targets
        template_keys = [t["key"] for t in data["templates"]]
        assert "employees" in template_keys
        assert "products" in template_keys
        print(f"SUCCESS: Found {len(data['templates'])} import templates: {', '.join(template_keys)}")
    
    def test_download_employee_import_template(self):
        """Download employee import template"""
        resp = requests.get(f"{BASE_URL}/api/import/templates/employees/download")
        assert resp.status_code == 200
        assert len(resp.content) > 0
        print(f"SUCCESS: Downloaded employee import template - Size: {len(resp.content)} bytes")
    
    def test_download_products_import_template(self):
        """Download products import template"""
        resp = requests.get(f"{BASE_URL}/api/import/templates/products/download")
        assert resp.status_code == 200
        print(f"SUCCESS: Downloaded products import template - Size: {len(resp.content)} bytes")


class TestAttendanceApproval:
    """Attendance Approval tests"""
    
    def test_list_pending_approvals(self):
        """List pending attendance approvals"""
        resp = requests.get(f"{BASE_URL}/api/attendance/approvals/pending")
        assert resp.status_code == 200
        data = resp.json()
        assert "pending" in data
        assert "total" in data
        print(f"SUCCESS: Found {data['total']} pending approvals")
    
    def test_list_attendance(self):
        """List attendance records"""
        resp = requests.get(f"{BASE_URL}/api/attendance/list")
        assert resp.status_code == 200
        data = resp.json()
        assert "attendance" in data
        print(f"SUCCESS: Found {len(data['attendance'])} attendance records")
    
    def test_create_izin_and_approval_flow(self):
        """Test izin creation and approval flow"""
        # Create izin request
        test_izin = {
            "employee_id": f"TEST_EMP_{uuid.uuid4().hex[:6]}",
            "employee_nik": f"NIK_{uuid.uuid4().hex[:6]}",
            "employee_name": "Test Employee Izin",
            "jabatan": "Staff",
            "branch_id": "test_branch",
            "branch_name": "Test Branch",
            "tanggal": "2024-03-01",
            "status": "izin",
            "keterangan": "Test izin untuk testing"
        }
        create_resp = requests.post(f"{BASE_URL}/api/attendance/izin", json=test_izin)
        assert create_resp.status_code == 200
        data = create_resp.json()
        assert "attendance_id" in data
        attendance_id = data["attendance_id"]
        print(f"SUCCESS: Created izin request - ID: {attendance_id}")
        
        # Approve the izin
        approve_resp = requests.put(
            f"{BASE_URL}/api/attendance/approvals/{attendance_id}/approve",
            params={"approver_id": "test_approver", "approver_name": "Test Approver", "notes": "Approved for testing"}
        )
        assert approve_resp.status_code == 200
        print(f"SUCCESS: Approved izin request - ID: {attendance_id}")
    
    def test_get_approval_history(self):
        """Get approval history"""
        resp = requests.get(f"{BASE_URL}/api/attendance/approvals/history")
        assert resp.status_code == 200
        data = resp.json()
        assert "history" in data
        print(f"SUCCESS: Found {len(data['history'])} approval history records")


class TestWarRoom:
    """War Room / Alert System tests"""
    
    def test_list_alerts(self):
        """List system alerts"""
        resp = requests.get(f"{BASE_URL}/api/erp/alerts")
        assert resp.status_code == 200
        data = resp.json()
        assert "alerts" in data
        print(f"SUCCESS: Found {len(data['alerts'])} alerts")
    
    def test_list_alerts_by_severity(self):
        """List alerts filtered by severity"""
        resp = requests.get(f"{BASE_URL}/api/erp/alerts", params={"is_resolved": False})
        assert resp.status_code == 200
        data = resp.json()
        assert "by_severity" in data
        print(f"SUCCESS: Alerts by severity - Critical: {data['by_severity'].get('critical', 0)}, Warning: {data['by_severity'].get('warning', 0)}")


class TestWhatsAppAlerts:
    """WhatsApp Alerts tests - Note: Sending is mocked"""
    
    def test_alerts_endpoint_exists(self):
        """Verify alerts endpoint exists for WhatsApp triggers"""
        resp = requests.get(f"{BASE_URL}/api/erp/alerts")
        assert resp.status_code == 200
        print("SUCCESS: Alerts endpoint exists for WhatsApp triggers (sending is MOCKED)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
