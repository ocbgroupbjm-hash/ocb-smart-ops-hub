"""
OCB TITAN AI - Multi-Database Login & Feature Tests
Tests multi-database switching, login flows, and key features:
- Login for OCB GROUP (ocb_titan), OCB UNIT 4 (ocb_unit_4), OCB UNIT 1 RITAIL (ocb_unt_1)
- Product photo upload
- Mass employee upload template download
- CRM AI customer save and character analysis  
- HR Training
- Attendance approval workflow
- Export/Import system
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = "https://smart-ops-hub-6.preview.emergentagent.com"

TEST_EMAIL = "ocbgroupbjm@gmail.com"
TEST_PASSWORD = "admin123"

DATABASES = [
    {"db_name": "ocb_titan", "business_name": "OCB GROUP"},
    {"db_name": "ocb_unit_4", "business_name": "OCB UNIT 4 MPC & MP3"},
    {"db_name": "ocb_unt_1", "business_name": "OCB UNIT 1 RITAIL"},
]


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


# ==================== MULTI-DATABASE LOGIN TESTS ====================

class TestMultiDatabaseLogin:
    """Test multi-database switching and login flows"""
    
    def test_list_businesses(self, api_client):
        """Test listing all available businesses/databases"""
        response = api_client.get(f"{BASE_URL}/api/business/list")
        assert response.status_code == 200, f"Failed to list businesses: {response.text}"
        
        data = response.json()
        assert "businesses" in data
        assert len(data["businesses"]) >= 3, "Expected at least 3 businesses"
        
        # Verify all expected databases exist
        db_names = [b["db_name"] for b in data["businesses"]]
        for db in DATABASES:
            assert db["db_name"] in db_names, f"Missing database: {db['db_name']}"
        print(f"✓ Found {len(data['businesses'])} businesses")
    
    @pytest.mark.parametrize("db_info", DATABASES)
    def test_switch_database(self, api_client, db_info):
        """Test switching to each database"""
        response = api_client.post(f"{BASE_URL}/api/business/switch/{db_info['db_name']}")
        assert response.status_code == 200, f"Failed to switch to {db_info['db_name']}: {response.text}"
        
        data = response.json()
        assert data.get("db_name") == db_info["db_name"]
        print(f"✓ Switched to {db_info['business_name']} ({db_info['db_name']})")
    
    @pytest.mark.parametrize("db_info", DATABASES)
    def test_ensure_admin_user(self, api_client, db_info):
        """Test ensure admin user exists in each database"""
        response = api_client.post(
            f"{BASE_URL}/api/business/ensure-admin/{db_info['db_name']}",
            params={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200, f"Failed ensure admin in {db_info['db_name']}: {response.text}"
        
        data = response.json()
        assert "message" in data
        print(f"✓ Admin ensured in {db_info['business_name']}")
    
    @pytest.mark.parametrize("db_info", DATABASES)
    def test_login_to_database(self, api_client, db_info):
        """Test login to each database after switching"""
        # Switch to database first
        switch_response = api_client.post(f"{BASE_URL}/api/business/switch/{db_info['db_name']}")
        assert switch_response.status_code == 200, f"Failed to switch: {switch_response.text}"
        
        # Ensure admin exists
        ensure_response = api_client.post(
            f"{BASE_URL}/api/business/ensure-admin/{db_info['db_name']}",
            params={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert ensure_response.status_code == 200
        
        # Now login
        login_response = api_client.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert login_response.status_code == 200, f"Login failed for {db_info['db_name']}: {login_response.text}"
        
        data = login_response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == TEST_EMAIL
        print(f"✓ Login successful to {db_info['business_name']}")


# ==================== MASTER ERP CRUD TESTS ====================

class TestMasterERP:
    """Test Master ERP CRUD operations"""
    
    @pytest.fixture(autouse=True)
    def setup(self, api_client):
        """Switch to main database and login"""
        api_client.post(f"{BASE_URL}/api/business/switch/ocb_titan")
        api_client.post(f"{BASE_URL}/api/business/ensure-admin/ocb_titan", 
                       params={"email": TEST_EMAIL, "password": TEST_PASSWORD})
        login = api_client.post(f"{BASE_URL}/api/auth/login",
                               json={"email": TEST_EMAIL, "password": TEST_PASSWORD})
        if login.status_code == 200:
            token = login.json().get("token")
            api_client.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_create_shift(self, api_client):
        """Test creating a new shift"""
        shift_data = {
            "code": "TEST_SHIFT",
            "name": "TEST Shift Pagi",
            "start_time": "07:00",
            "end_time": "15:00",
            "break_minutes": 60
        }
        response = api_client.post(f"{BASE_URL}/api/erp/master/shifts", json=shift_data)
        assert response.status_code == 200, f"Failed to create shift: {response.text}"
        
        data = response.json()
        assert "message" in data
        assert "shift" in data
        print(f"✓ Created shift: {shift_data['name']}")
        return data.get("shift", {}).get("id")
    
    def test_create_jabatan(self, api_client):
        """Test creating a new jabatan/position"""
        jabatan_data = {
            "code": "TEST_JAB",
            "name": "TEST Supervisor",
            "level": 2,
            "department": "Operasional"
        }
        response = api_client.post(f"{BASE_URL}/api/erp/master/jabatan", json=jabatan_data)
        assert response.status_code == 200, f"Failed to create jabatan: {response.text}"
        print(f"✓ Created jabatan: {jabatan_data['name']}")
    
    def test_create_lokasi_absensi(self, api_client):
        """Test creating attendance location"""
        lokasi_data = {
            "branch_id": "test-branch-123",
            "branch_name": "TEST Branch",
            "latitude": -3.3164,
            "longitude": 114.5908,
            "radius_meters": 100,
            "address": "Jl. Test No. 1, Banjarmasin"
        }
        response = api_client.post(f"{BASE_URL}/api/erp/master/lokasi-absensi", json=lokasi_data)
        assert response.status_code == 200, f"Failed to create lokasi: {response.text}"
        print(f"✓ Created lokasi absensi: {lokasi_data['branch_name']}")
    
    def test_create_payroll_rule(self, api_client):
        """Test creating payroll rule"""
        rule_data = {
            "jabatan_id": "test-jabatan-123",
            "jabatan_name": "TEST Kasir",
            "gaji_pokok": 3500000,
            "tunjangan_jabatan": 500000,
            "tunjangan_transport": 300000,
            "tunjangan_makan": 400000,
            "bonus_kehadiran_full": 200000,
            "potongan_telat_per_menit": 1000,
            "potongan_alpha_per_hari": 150000
        }
        response = api_client.post(f"{BASE_URL}/api/erp/master/payroll-rules", json=rule_data)
        assert response.status_code == 200, f"Failed to create payroll rule: {response.text}"
        print(f"✓ Created payroll rule for: {rule_data['jabatan_name']}")


# ==================== EMPLOYEE TESTS ====================

class TestEmployeeAPI:
    """Test Employee CRUD operations"""
    
    @pytest.fixture(autouse=True)
    def setup(self, api_client):
        api_client.post(f"{BASE_URL}/api/business/switch/ocb_titan")
        api_client.post(f"{BASE_URL}/api/business/ensure-admin/ocb_titan",
                       params={"email": TEST_EMAIL, "password": TEST_PASSWORD})
        login = api_client.post(f"{BASE_URL}/api/auth/login",
                               json={"email": TEST_EMAIL, "password": TEST_PASSWORD})
        if login.status_code == 200:
            token = login.json().get("token")
            api_client.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_create_employee(self, api_client):
        """Test creating new employee"""
        import uuid
        emp_data = {
            "nik": f"TEST-{uuid.uuid4().hex[:8]}",
            "name": "TEST Budi Santoso",
            "email": "testbudi@test.com",
            "phone": "081234567890",
            "jabatan_name": "Kasir",
            "department": "Operasional",
            "branch_name": "Test Branch",
            "join_date": "2024-01-15",
            "contract_type": "tetap",
            "gaji_pokok": 3500000
        }
        response = api_client.post(f"{BASE_URL}/api/erp/employees", json=emp_data)
        assert response.status_code == 200, f"Failed to create employee: {response.text}"
        
        data = response.json()
        assert "employee" in data
        print(f"✓ Created employee: {emp_data['name']}")
        return data["employee"]["id"]
    
    def test_list_employees(self, api_client):
        """Test listing employees"""
        response = api_client.get(f"{BASE_URL}/api/erp/employees")
        assert response.status_code == 200, f"Failed to list employees: {response.text}"
        
        data = response.json()
        assert "employees" in data
        print(f"✓ Listed {len(data['employees'])} employees")


# ==================== PRODUCT PHOTO UPLOAD TESTS ====================

class TestProductPhotoUpload:
    """Test product photo upload API"""
    
    @pytest.fixture(autouse=True)
    def setup(self, api_client):
        api_client.post(f"{BASE_URL}/api/business/switch/ocb_titan")
    
    def test_get_product_for_upload(self, api_client):
        """First ensure a product exists"""
        response = api_client.get(f"{BASE_URL}/api/products?limit=1")
        if response.status_code == 200:
            data = response.json()
            if data.get("products"):
                return data["products"][0].get("id")
        return None
    
    def test_product_photo_upload_endpoint_exists(self, api_client):
        """Test that product photo upload endpoint exists"""
        # Test with minimal data - endpoint should reject missing file, not 404
        response = api_client.post(f"{BASE_URL}/api/files/products/photo", data={})
        # 422 (validation error) or 400 is expected - not 404
        assert response.status_code != 404, "Product photo upload endpoint not found"
        print(f"✓ Product photo upload endpoint exists (status: {response.status_code})")


# ==================== CRM AI TESTS ====================

class TestCRMAI:
    """Test CRM AI customer management"""
    
    @pytest.fixture(autouse=True)
    def setup(self, api_client):
        api_client.post(f"{BASE_URL}/api/business/switch/ocb_titan")
        api_client.post(f"{BASE_URL}/api/business/ensure-admin/ocb_titan",
                       params={"email": TEST_EMAIL, "password": TEST_PASSWORD})
        login = api_client.post(f"{BASE_URL}/api/auth/login",
                               json={"email": TEST_EMAIL, "password": TEST_PASSWORD})
        if login.status_code == 200:
            token = login.json().get("token")
            api_client.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_create_customer(self, api_client):
        """Test creating new CRM customer"""
        import uuid
        customer_data = {
            "name": f"TEST Customer {uuid.uuid4().hex[:6]}",
            "phone": f"0812{uuid.uuid4().hex[:8]}",
            "email": "testcustomer@test.com",
            "address": "Jl. Test No. 1",
            "source": "walk-in",
            "tags": ["vip", "regular"]
        }
        response = api_client.post(f"{BASE_URL}/api/crm-ai/customers", json=customer_data)
        assert response.status_code == 200, f"Failed to create customer: {response.text}"
        
        data = response.json()
        assert "customer" in data
        customer_id = data["customer"]["id"]
        print(f"✓ Created CRM customer: {customer_data['name']}")
        return customer_id
    
    def test_analyze_customer_character(self, api_client):
        """Test customer character analysis"""
        # First create a customer
        import uuid
        customer_data = {
            "name": f"TEST Analyze {uuid.uuid4().hex[:6]}",
            "phone": f"0813{uuid.uuid4().hex[:8]}"
        }
        create_response = api_client.post(f"{BASE_URL}/api/crm-ai/customers", json=customer_data)
        assert create_response.status_code == 200
        
        customer_id = create_response.json()["customer"]["id"]
        
        # Now analyze character
        response = api_client.post(f"{BASE_URL}/api/crm-ai/customers/{customer_id}/analyze")
        assert response.status_code == 200, f"Failed to analyze customer: {response.text}"
        
        data = response.json()
        assert "analysis" in data
        assert "buying_frequency" in data["analysis"]
        print(f"✓ Customer character analyzed: buying_frequency={data['analysis']['buying_frequency']}")


# ==================== HR TRAINING TESTS ====================

class TestHRTraining:
    """Test HR Training management"""
    
    @pytest.fixture(autouse=True)
    def setup(self, api_client):
        api_client.post(f"{BASE_URL}/api/business/switch/ocb_titan")
        api_client.post(f"{BASE_URL}/api/business/ensure-admin/ocb_titan",
                       params={"email": TEST_EMAIL, "password": TEST_PASSWORD})
        login = api_client.post(f"{BASE_URL}/api/auth/login",
                               json={"email": TEST_EMAIL, "password": TEST_PASSWORD})
        if login.status_code == 200:
            token = login.json().get("token")
            api_client.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_create_training(self, api_client):
        """Test creating new training"""
        import uuid
        training_data = {
            "title": f"TEST Training {uuid.uuid4().hex[:6]}",
            "description": "Test training description",
            "trainer": "John Doe",
            "training_type": "internal",
            "start_date": "2026-02-01",
            "end_date": "2026-02-03",
            "location": "Meeting Room A",
            "max_participants": 30,
            "is_mandatory": False
        }
        response = api_client.post(f"{BASE_URL}/api/hr/trainings", json=training_data)
        assert response.status_code == 200, f"Failed to create training: {response.text}"
        
        data = response.json()
        assert "training" in data
        print(f"✓ Created training: {training_data['title']}")
    
    def test_list_trainings(self, api_client):
        """Test listing trainings"""
        response = api_client.get(f"{BASE_URL}/api/hr/trainings")
        assert response.status_code == 200, f"Failed to list trainings: {response.text}"
        
        data = response.json()
        assert "trainings" in data
        print(f"✓ Listed {len(data['trainings'])} trainings")


# ==================== ATTENDANCE APPROVAL TESTS ====================

class TestAttendanceApproval:
    """Test attendance approval workflow"""
    
    @pytest.fixture(autouse=True)
    def setup(self, api_client):
        api_client.post(f"{BASE_URL}/api/business/switch/ocb_titan")
        api_client.post(f"{BASE_URL}/api/business/ensure-admin/ocb_titan",
                       params={"email": TEST_EMAIL, "password": TEST_PASSWORD})
        login = api_client.post(f"{BASE_URL}/api/auth/login",
                               json={"email": TEST_EMAIL, "password": TEST_PASSWORD})
        if login.status_code == 200:
            token = login.json().get("token")
            api_client.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_list_pending_approvals(self, api_client):
        """Test listing pending attendance approvals"""
        response = api_client.get(f"{BASE_URL}/api/attendance/approvals/pending")
        assert response.status_code == 200, f"Failed to list pending approvals: {response.text}"
        
        data = response.json()
        assert "pending" in data
        assert "total" in data
        print(f"✓ Found {data['total']} pending attendance approvals")
    
    def test_list_attendance(self, api_client):
        """Test listing attendance records"""
        response = api_client.get(f"{BASE_URL}/api/attendance/list")
        assert response.status_code == 200, f"Failed to list attendance: {response.text}"
        
        data = response.json()
        assert "attendance" in data
        print(f"✓ Listed {len(data['attendance'])} attendance records")


# ==================== MASS UPLOAD TEMPLATE TESTS ====================

class TestMassUploadTemplate:
    """Test mass upload template download"""
    
    @pytest.fixture(autouse=True)
    def setup(self, api_client):
        api_client.post(f"{BASE_URL}/api/business/switch/ocb_titan")
    
    def test_employee_upload_template_download(self, api_client):
        """Test downloading employee mass upload template"""
        response = api_client.get(f"{BASE_URL}/api/hr/employees/upload-template")
        assert response.status_code == 200, f"Failed to download template: {response.text}"
        
        # Check content type - should be Excel
        content_type = response.headers.get("content-type", "")
        assert "spreadsheet" in content_type or "octet-stream" in content_type, \
            f"Expected Excel file, got: {content_type}"
        
        # Check we got actual content
        assert len(response.content) > 0, "Template file is empty"
        print(f"✓ Downloaded employee template ({len(response.content)} bytes)")


# ==================== EXPORT SYSTEM TESTS ====================

class TestExportSystem:
    """Test export system"""
    
    @pytest.fixture(autouse=True)
    def setup(self, api_client):
        api_client.post(f"{BASE_URL}/api/business/switch/ocb_titan")
        api_client.post(f"{BASE_URL}/api/business/ensure-admin/ocb_titan",
                       params={"email": TEST_EMAIL, "password": TEST_PASSWORD})
        login = api_client.post(f"{BASE_URL}/api/auth/login",
                               json={"email": TEST_EMAIL, "password": TEST_PASSWORD})
        if login.status_code == 200:
            token = login.json().get("token")
            api_client.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_export_employees_excel(self, api_client):
        """Test exporting employees to Excel"""
        response = api_client.get(f"{BASE_URL}/api/export-v2/hr/employees?format=xlsx")
        assert response.status_code == 200, f"Failed to export employees: {response.text}"
        
        content_type = response.headers.get("content-type", "")
        assert "spreadsheet" in content_type or "octet-stream" in content_type
        print(f"✓ Exported employees Excel ({len(response.content)} bytes)")


# ==================== IMPORT SYSTEM TESTS ====================

class TestImportSystem:
    """Test import system"""
    
    @pytest.fixture(autouse=True)
    def setup(self, api_client):
        api_client.post(f"{BASE_URL}/api/business/switch/ocb_titan")
    
    def test_list_import_templates(self, api_client):
        """Test listing available import templates"""
        response = api_client.get(f"{BASE_URL}/api/import/templates")
        assert response.status_code == 200, f"Failed to list templates: {response.text}"
        
        data = response.json()
        assert "templates" in data
        print(f"✓ Found {len(data['templates'])} import templates")
    
    def test_download_employees_template(self, api_client):
        """Test downloading employees import template"""
        response = api_client.get(f"{BASE_URL}/api/import/templates/employees/download")
        assert response.status_code == 200, f"Failed to download template: {response.text}"
        
        assert len(response.content) > 0, "Template file is empty"
        print(f"✓ Downloaded employees template ({len(response.content)} bytes)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
