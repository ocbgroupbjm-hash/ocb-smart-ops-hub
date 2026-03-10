"""
OCB TITAN AI - Phase 1-15 Comprehensive Test Suite
Tests all Master ERP CRUD operations, CRM AI, HR, Export/Import, WhatsApp Alerts, War Room
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

def gen_test_id():
    return f"TEST_{uuid.uuid4().hex[:8]}"

@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


# ==================== MASTER SHIFT CRUD ====================
class TestMasterShiftCRUD:
    """Test Master Shift CRUD - Save button must work"""
    
    created_shift_id = None
    
    def test_01_list_shifts(self, api_client):
        """GET /api/erp/master/shifts - List all shifts"""
        response = api_client.get(f"{BASE_URL}/api/erp/master/shifts")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "shifts" in data, "Response should contain 'shifts' field"
        print(f"PASS: List shifts - found {len(data['shifts'])} shifts")
    
    def test_02_create_shift(self, api_client):
        """POST /api/erp/master/shifts - Create new shift (SIMPAN)"""
        payload = {
            "code": gen_test_id(),
            "name": "Test Shift Morning",
            "start_time": "07:00",
            "end_time": "15:00",
            "break_minutes": 60
        }
        response = api_client.post(f"{BASE_URL}/api/erp/master/shifts", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "shift" in data, "Response should contain 'shift' field"
        assert data["shift"]["code"] == payload["code"]
        assert data["shift"]["name"] == payload["name"]
        TestMasterShiftCRUD.created_shift_id = data["shift"]["id"]
        print(f"PASS: Create shift - ID: {TestMasterShiftCRUD.created_shift_id}")
    
    def test_03_update_shift(self, api_client):
        """PUT /api/erp/master/shifts/{id} - Update shift"""
        if not TestMasterShiftCRUD.created_shift_id:
            pytest.skip("No shift created to update")
        
        payload = {
            "code": gen_test_id(),
            "name": "Updated Test Shift",
            "start_time": "08:00",
            "end_time": "16:00",
            "break_minutes": 45
        }
        response = api_client.put(
            f"{BASE_URL}/api/erp/master/shifts/{TestMasterShiftCRUD.created_shift_id}",
            json=payload
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"PASS: Update shift - {TestMasterShiftCRUD.created_shift_id}")
    
    def test_04_delete_shift(self, api_client):
        """DELETE /api/erp/master/shifts/{id} - Soft delete shift"""
        if not TestMasterShiftCRUD.created_shift_id:
            pytest.skip("No shift created to delete")
        
        response = api_client.delete(
            f"{BASE_URL}/api/erp/master/shifts/{TestMasterShiftCRUD.created_shift_id}"
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"PASS: Delete shift - {TestMasterShiftCRUD.created_shift_id}")


# ==================== MASTER JABATAN CRUD ====================
class TestMasterJabatanCRUD:
    """Test Master Jabatan CRUD - Save button must work"""
    
    created_jabatan_id = None
    
    def test_01_list_jabatan(self, api_client):
        """GET /api/erp/master/jabatan - List all jabatan"""
        response = api_client.get(f"{BASE_URL}/api/erp/master/jabatan")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "jabatan" in data, "Response should contain 'jabatan' field"
        print(f"PASS: List jabatan - found {len(data['jabatan'])} positions")
    
    def test_02_create_jabatan(self, api_client):
        """POST /api/erp/master/jabatan - Create new jabatan (SIMPAN)"""
        payload = {
            "code": gen_test_id(),
            "name": "Test Supervisor",
            "level": 3,
            "department": "Operations"
        }
        response = api_client.post(f"{BASE_URL}/api/erp/master/jabatan", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "jabatan" in data, "Response should contain 'jabatan' field"
        assert data["jabatan"]["code"] == payload["code"]
        assert data["jabatan"]["name"] == payload["name"]
        TestMasterJabatanCRUD.created_jabatan_id = data["jabatan"]["id"]
        print(f"PASS: Create jabatan - ID: {TestMasterJabatanCRUD.created_jabatan_id}")
    
    def test_03_update_jabatan(self, api_client):
        """PUT /api/erp/master/jabatan/{id} - Update jabatan"""
        if not TestMasterJabatanCRUD.created_jabatan_id:
            pytest.skip("No jabatan created to update")
        
        payload = {
            "code": gen_test_id(),
            "name": "Updated Manager Position",
            "level": 4,
            "department": "HR"
        }
        response = api_client.put(
            f"{BASE_URL}/api/erp/master/jabatan/{TestMasterJabatanCRUD.created_jabatan_id}",
            json=payload
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"PASS: Update jabatan - {TestMasterJabatanCRUD.created_jabatan_id}")
    
    def test_04_delete_jabatan(self, api_client):
        """DELETE /api/erp/master/jabatan/{id} - Soft delete jabatan"""
        if not TestMasterJabatanCRUD.created_jabatan_id:
            pytest.skip("No jabatan created to delete")
        
        response = api_client.delete(
            f"{BASE_URL}/api/erp/master/jabatan/{TestMasterJabatanCRUD.created_jabatan_id}"
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"PASS: Delete jabatan - {TestMasterJabatanCRUD.created_jabatan_id}")


# ==================== MASTER LOKASI ABSENSI CRUD ====================
class TestMasterLokasiAbsensiCRUD:
    """Test Master Lokasi Absensi CRUD - Save button must work"""
    
    created_lokasi_id = None
    
    def test_01_list_lokasi_absensi(self, api_client):
        """GET /api/erp/master/lokasi-absensi - List all attendance locations"""
        response = api_client.get(f"{BASE_URL}/api/erp/master/lokasi-absensi")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "lokasi" in data, "Response should contain 'lokasi' field"
        print(f"PASS: List lokasi absensi - found {len(data['lokasi'])} locations")
    
    def test_02_create_lokasi_absensi(self, api_client):
        """POST /api/erp/master/lokasi-absensi - Create new lokasi absensi (SIMPAN)"""
        payload = {
            "branch_id": gen_test_id(),
            "branch_name": "Test Branch Office",
            "latitude": -3.3194,
            "longitude": 114.5908,
            "radius_meters": 100,
            "address": "Jl. Test Address No. 123, Banjarmasin"
        }
        response = api_client.post(f"{BASE_URL}/api/erp/master/lokasi-absensi", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "lokasi" in data, "Response should contain 'lokasi' field"
        assert data["lokasi"]["branch_name"] == payload["branch_name"]
        assert data["lokasi"]["latitude"] == payload["latitude"]
        TestMasterLokasiAbsensiCRUD.created_lokasi_id = data["lokasi"]["id"]
        print(f"PASS: Create lokasi absensi - ID: {TestMasterLokasiAbsensiCRUD.created_lokasi_id}")
    
    def test_03_update_lokasi_absensi(self, api_client):
        """PUT /api/erp/master/lokasi-absensi/{id} - Update lokasi absensi"""
        if not TestMasterLokasiAbsensiCRUD.created_lokasi_id:
            pytest.skip("No lokasi created to update")
        
        payload = {
            "branch_id": gen_test_id(),
            "branch_name": "Updated Branch",
            "latitude": -3.3200,
            "longitude": 114.5900,
            "radius_meters": 150,
            "address": "Updated Address"
        }
        response = api_client.put(
            f"{BASE_URL}/api/erp/master/lokasi-absensi/{TestMasterLokasiAbsensiCRUD.created_lokasi_id}",
            json=payload
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"PASS: Update lokasi absensi - {TestMasterLokasiAbsensiCRUD.created_lokasi_id}")
    
    def test_04_delete_lokasi_absensi(self, api_client):
        """DELETE /api/erp/master/lokasi-absensi/{id} - Soft delete lokasi"""
        if not TestMasterLokasiAbsensiCRUD.created_lokasi_id:
            pytest.skip("No lokasi created to delete")
        
        response = api_client.delete(
            f"{BASE_URL}/api/erp/master/lokasi-absensi/{TestMasterLokasiAbsensiCRUD.created_lokasi_id}"
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"PASS: Delete lokasi absensi - {TestMasterLokasiAbsensiCRUD.created_lokasi_id}")


# ==================== MASTER PAYROLL RULES CRUD ====================
class TestMasterPayrollRulesCRUD:
    """Test Master Payroll Rules CRUD - Save button must work"""
    
    created_rule_id = None
    test_jabatan_id = None
    
    def test_01_list_payroll_rules(self, api_client):
        """GET /api/erp/master/payroll-rules - List all payroll rules"""
        response = api_client.get(f"{BASE_URL}/api/erp/master/payroll-rules")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "rules" in data, "Response should contain 'rules' field"
        print(f"PASS: List payroll rules - found {len(data['rules'])} rules")
    
    def test_02_create_payroll_rule(self, api_client):
        """POST /api/erp/master/payroll-rules - Create new payroll rule (SIMPAN)"""
        TestMasterPayrollRulesCRUD.test_jabatan_id = gen_test_id()
        payload = {
            "jabatan_id": TestMasterPayrollRulesCRUD.test_jabatan_id,
            "jabatan_name": "Test Manager",
            "gaji_pokok": 5000000,
            "tunjangan_jabatan": 1000000,
            "tunjangan_transport": 500000,
            "tunjangan_makan": 400000,
            "bonus_kehadiran_full": 300000,
            "potongan_telat_per_menit": 1000,
            "potongan_alpha_per_hari": 200000
        }
        response = api_client.post(f"{BASE_URL}/api/erp/master/payroll-rules", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        # API returns message on create/upsert
        assert "message" in data
        assert "payroll" in data["message"].lower() or "rule" in data.get("rule", {})
        print(f"PASS: Create payroll rule for jabatan: {TestMasterPayrollRulesCRUD.test_jabatan_id}")
    
    def test_03_update_payroll_rule_upsert(self, api_client):
        """POST /api/erp/master/payroll-rules - Update via upsert"""
        if not TestMasterPayrollRulesCRUD.test_jabatan_id:
            pytest.skip("No payroll rule created")
        
        payload = {
            "jabatan_id": TestMasterPayrollRulesCRUD.test_jabatan_id,
            "jabatan_name": "Test Manager Updated",
            "gaji_pokok": 6000000,
            "tunjangan_jabatan": 1200000,
            "tunjangan_transport": 600000,
            "tunjangan_makan": 450000,
            "bonus_kehadiran_full": 350000,
            "potongan_telat_per_menit": 1500,
            "potongan_alpha_per_hari": 250000
        }
        response = api_client.post(f"{BASE_URL}/api/erp/master/payroll-rules", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "diupdate" in data.get("message", "").lower() or "message" in data
        print(f"PASS: Update payroll rule for jabatan: {TestMasterPayrollRulesCRUD.test_jabatan_id}")


# ==================== EMPLOYEE CRUD ====================
class TestEmployeeCRUD:
    """Test Employee Create/List API"""
    
    created_employee_id = None
    test_nik = None
    
    def test_01_list_employees(self, api_client):
        """GET /api/erp/employees - List all employees"""
        response = api_client.get(f"{BASE_URL}/api/erp/employees")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "employees" in data, "Response should contain 'employees' field"
        print(f"PASS: List employees - found {len(data['employees'])} employees")
    
    def test_02_create_employee(self, api_client):
        """POST /api/erp/employees - Create new employee"""
        TestEmployeeCRUD.test_nik = gen_test_id()
        payload = {
            "nik": TestEmployeeCRUD.test_nik,
            "name": "Test Employee OCB",
            "email": "test.employee@ocbgroup.com",
            "phone": "081234567890",
            "whatsapp": "081234567890",
            "jabatan_name": "Staff",
            "department": "Operations",
            "branch_name": "Cabang Utama",
            "gender": "Laki-laki",
            "join_date": "2025-01-01",
            "contract_type": "tetap",
            "gaji_pokok": 4000000
        }
        response = api_client.post(f"{BASE_URL}/api/erp/employees", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "employee" in data, "Response should contain 'employee' field"
        assert data["employee"]["nik"] == payload["nik"]
        assert data["employee"]["name"] == payload["name"]
        TestEmployeeCRUD.created_employee_id = data["employee"]["id"]
        print(f"PASS: Create employee - ID: {TestEmployeeCRUD.created_employee_id}")
    
    def test_03_get_employee_detail(self, api_client):
        """GET /api/erp/employees/{id} - Get employee detail"""
        if not TestEmployeeCRUD.created_employee_id:
            pytest.skip("No employee created")
        
        response = api_client.get(f"{BASE_URL}/api/erp/employees/{TestEmployeeCRUD.created_employee_id}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("nik") == TestEmployeeCRUD.test_nik
        print(f"PASS: Get employee detail - {TestEmployeeCRUD.created_employee_id}")
    
    def test_04_update_employee(self, api_client):
        """PUT /api/erp/employees/{id} - Update employee"""
        if not TestEmployeeCRUD.created_employee_id:
            pytest.skip("No employee created")
        
        payload = {
            "name": "Updated Test Employee",
            "jabatan_name": "Senior Staff",
            "gaji_pokok": 5000000
        }
        response = api_client.put(
            f"{BASE_URL}/api/erp/employees/{TestEmployeeCRUD.created_employee_id}",
            json=payload
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"PASS: Update employee - {TestEmployeeCRUD.created_employee_id}")
    
    def test_05_search_employees(self, api_client):
        """GET /api/erp/employees?search= - Search employees"""
        response = api_client.get(f"{BASE_URL}/api/erp/employees?search=Test")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "employees" in data
        print(f"PASS: Search employees - found {len(data['employees'])} matching")
    
    def test_06_delete_employee(self, api_client):
        """DELETE /api/erp/employees/{id} - Delete employee"""
        if not TestEmployeeCRUD.created_employee_id:
            pytest.skip("No employee created")
        
        response = api_client.delete(f"{BASE_URL}/api/erp/employees/{TestEmployeeCRUD.created_employee_id}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"PASS: Delete employee - {TestEmployeeCRUD.created_employee_id}")


# ==================== CRM AI CUSTOMER CRUD ====================
class TestCRMCustomerCRUD:
    """Test CRM AI Customer CRUD - simpan data pelanggan"""
    
    created_customer_id = None
    
    def test_01_list_customers(self, api_client):
        """GET /api/crm-ai/customers - List all customers"""
        response = api_client.get(f"{BASE_URL}/api/crm-ai/customers")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "customers" in data, "Response should contain 'customers' field"
        print(f"PASS: List CRM customers - found {len(data['customers'])} customers")
    
    def test_02_create_customer(self, api_client):
        """POST /api/crm-ai/customers - Create new customer (SIMPAN)"""
        payload = {
            "name": "Test Customer OCB",
            "phone": f"08{uuid.uuid4().hex[:10]}",
            "email": "test.customer@example.com",
            "address": "Jl. Test No. 123",
            "birth_date": "1990-01-15",
            "gender": "Laki-laki",
            "notes": "Test customer from automated test",
            "tags": ["vip", "test"],
            "source": "online"
        }
        response = api_client.post(f"{BASE_URL}/api/crm-ai/customers", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "customer" in data, "Response should contain 'customer' field"
        assert data["customer"]["name"] == payload["name"]
        TestCRMCustomerCRUD.created_customer_id = data["customer"]["id"]
        print(f"PASS: Create CRM customer - ID: {TestCRMCustomerCRUD.created_customer_id}")
    
    def test_03_get_customer_detail(self, api_client):
        """GET /api/crm-ai/customers/{id} - Get customer detail"""
        if not TestCRMCustomerCRUD.created_customer_id:
            pytest.skip("No customer created")
        
        response = api_client.get(f"{BASE_URL}/api/crm-ai/customers/{TestCRMCustomerCRUD.created_customer_id}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "customer" in data
        print(f"PASS: Get CRM customer detail - {TestCRMCustomerCRUD.created_customer_id}")
    
    def test_04_update_customer(self, api_client):
        """PUT /api/crm-ai/customers/{id} - Update customer"""
        if not TestCRMCustomerCRUD.created_customer_id:
            pytest.skip("No customer created")
        
        payload = {
            "name": "Updated Test Customer",
            "phone": f"08{uuid.uuid4().hex[:10]}",
            "email": "updated.test@example.com",
            "address": "Jl. Updated No. 456",
            "tags": ["vip", "updated"],
            "notes": "Updated notes"
        }
        response = api_client.put(
            f"{BASE_URL}/api/crm-ai/customers/{TestCRMCustomerCRUD.created_customer_id}",
            json=payload
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"PASS: Update CRM customer - {TestCRMCustomerCRUD.created_customer_id}")


# ==================== CRM AI CHARACTER ANALYSIS ====================
class TestCRMCustomerCharacter:
    """Test CRM AI Customer Character Analysis"""
    
    def test_01_get_customer_character(self, api_client):
        """GET /api/crm-ai/customers/{id}/character - Get character analysis"""
        if not TestCRMCustomerCRUD.created_customer_id:
            pytest.skip("No customer to analyze")
        
        response = api_client.get(
            f"{BASE_URL}/api/crm-ai/customers/{TestCRMCustomerCRUD.created_customer_id}/character"
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "character" in data, "Response should contain 'character' field"
        print(f"PASS: Get customer character - buying_frequency: {data['character'].get('buying_frequency')}")
    
    def test_02_save_customer_character(self, api_client):
        """POST /api/crm-ai/customers/{id}/character - Save character profile"""
        if not TestCRMCustomerCRUD.created_customer_id:
            pytest.skip("No customer created")
        
        payload = {
            "customer_id": TestCRMCustomerCRUD.created_customer_id,
            "buying_frequency": "frequent",
            "price_sensitivity": "normal",
            "communication_style": "casual",
            "preferred_channel": "whatsapp",
            "interests": ["electronics", "fashion"],
            "special_notes": "VIP customer, respond quickly"
        }
        response = api_client.post(
            f"{BASE_URL}/api/crm-ai/customers/{TestCRMCustomerCRUD.created_customer_id}/character",
            json=payload
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "character" in data
        print(f"PASS: Save customer character profile")
    
    def test_03_analyze_customer_ai(self, api_client):
        """POST /api/crm-ai/customers/{id}/analyze - AI analysis of customer"""
        if not TestCRMCustomerCRUD.created_customer_id:
            pytest.skip("No customer to analyze")
        
        response = api_client.post(
            f"{BASE_URL}/api/crm-ai/customers/{TestCRMCustomerCRUD.created_customer_id}/analyze"
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "analysis" in data, "Response should contain 'analysis' field"
        analysis = data["analysis"]
        assert "buying_frequency" in analysis
        assert "price_sensitivity" in analysis
        assert "recommendations" in analysis
        print(f"PASS: AI customer analysis - category: {analysis.get('buying_frequency')}")


# ==================== CRM AI AUTO RESPONSE ====================
class TestCRMAutoResponse:
    """Test CRM AI Generate Auto Response"""
    
    def test_01_generate_auto_response_greeting(self, api_client):
        """POST /api/crm-ai/generate-response - Generate response for greeting"""
        if not TestCRMCustomerCRUD.created_customer_id:
            pytest.skip("No customer created")
        
        response = api_client.post(
            f"{BASE_URL}/api/crm-ai/generate-response",
            params={
                "customer_id": TestCRMCustomerCRUD.created_customer_id,
                "incoming_message": "Halo, selamat pagi!"
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "generated_response" in data
        assert "detected_intent" in data
        assert data["detected_intent"] == "greeting"
        print(f"PASS: Auto response for greeting - Intent: {data['detected_intent']}")
    
    def test_02_generate_auto_response_price_inquiry(self, api_client):
        """POST /api/crm-ai/generate-response - Generate response for price inquiry"""
        if not TestCRMCustomerCRUD.created_customer_id:
            pytest.skip("No customer created")
        
        response = api_client.post(
            f"{BASE_URL}/api/crm-ai/generate-response",
            params={
                "customer_id": TestCRMCustomerCRUD.created_customer_id,
                "incoming_message": "Berapa harga produk ini?"
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "generated_response" in data
        assert data["detected_intent"] == "price_inquiry"
        print(f"PASS: Auto response for price inquiry - Intent: {data['detected_intent']}")
    
    def test_03_generate_auto_response_complaint(self, api_client):
        """POST /api/crm-ai/generate-response - Generate response for complaint"""
        if not TestCRMCustomerCRUD.created_customer_id:
            pytest.skip("No customer created")
        
        response = api_client.post(
            f"{BASE_URL}/api/crm-ai/generate-response",
            params={
                "customer_id": TestCRMCustomerCRUD.created_customer_id,
                "incoming_message": "Produknya rusak, saya kecewa sekali!"
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "generated_response" in data
        assert data["detected_intent"] == "complaint"
        assert data.get("needs_review") is True
        print(f"PASS: Auto response for complaint - needs_review: {data.get('needs_review')}")
    
    def test_04_analyze_complaint(self, api_client):
        """POST /api/crm-ai/complaint/analyze - Analyze complaint text"""
        response = api_client.post(
            f"{BASE_URL}/api/crm-ai/complaint/analyze",
            params={
                "complaint_text": "Barang yang saya pesan rusak dan pengiriman sangat lambat!",
                "customer_id": TestCRMCustomerCRUD.created_customer_id or ""
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "detected_category" in data
        assert "suggested_response" in data
        assert "priority" in data
        print(f"PASS: Complaint analysis - category: {data['detected_category']}, priority: {data['priority']}")


# ==================== HR TRAINING MANAGEMENT ====================
class TestHRTraining:
    """Test HR Training Management"""
    
    created_training_id = None
    test_employee_id = None
    
    def test_01_list_trainings(self, api_client):
        """GET /api/hr/trainings - List all trainings"""
        response = api_client.get(f"{BASE_URL}/api/hr/trainings")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "trainings" in data, "Response should contain 'trainings' field"
        print(f"PASS: List trainings - found {len(data['trainings'])} trainings")
    
    def test_02_create_training(self, api_client):
        """POST /api/hr/trainings - Create new training"""
        payload = {
            "title": "Test Training Program",
            "description": "Training for automated testing",
            "trainer": "Test Trainer",
            "training_type": "internal",
            "start_date": "2026-02-01",
            "end_date": "2026-02-02",
            "location": "Training Room A",
            "max_participants": 20,
            "department_ids": [],
            "position_ids": [],
            "is_mandatory": False
        }
        response = api_client.post(f"{BASE_URL}/api/hr/trainings", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "training" in data
        TestHRTraining.created_training_id = data["training"]["id"]
        print(f"PASS: Create training - ID: {TestHRTraining.created_training_id}")
    
    def test_03_update_training(self, api_client):
        """PUT /api/hr/trainings/{id} - Update training"""
        if not TestHRTraining.created_training_id:
            pytest.skip("No training created")
        
        payload = {
            "title": "Updated Test Training",
            "description": "Updated description",
            "trainer": "Updated Trainer",
            "training_type": "external",
            "start_date": "2026-03-01",
            "end_date": "2026-03-02",
            "location": "Conference Room",
            "max_participants": 30,
            "is_mandatory": True
        }
        response = api_client.put(
            f"{BASE_URL}/api/hr/trainings/{TestHRTraining.created_training_id}",
            json=payload
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"PASS: Update training - {TestHRTraining.created_training_id}")


# ==================== HR DEPARTMENT & ORG STRUCTURE ====================
class TestHRDepartmentOrg:
    """Test HR Department & Organization Structure"""
    
    created_department_id = None
    
    def test_01_list_departments(self, api_client):
        """GET /api/hr/departments - List all departments"""
        response = api_client.get(f"{BASE_URL}/api/hr/departments")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "departments" in data, "Response should contain 'departments' field"
        print(f"PASS: List departments - found {len(data['departments'])} departments")
    
    def test_02_create_department(self, api_client):
        """POST /api/hr/departments - Create new department"""
        payload = {
            "code": gen_test_id(),
            "name": "Test Department",
            "parent_id": "",
            "head_employee_id": "",
            "description": "Test department from automated test"
        }
        response = api_client.post(f"{BASE_URL}/api/hr/departments", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "department" in data
        TestHRDepartmentOrg.created_department_id = data["department"]["id"]
        print(f"PASS: Create department - ID: {TestHRDepartmentOrg.created_department_id}")
    
    def test_03_update_department(self, api_client):
        """PUT /api/hr/departments/{id} - Update department"""
        if not TestHRDepartmentOrg.created_department_id:
            pytest.skip("No department created")
        
        payload = {
            "code": gen_test_id(),
            "name": "Updated Test Department",
            "parent_id": "",
            "description": "Updated description"
        }
        response = api_client.put(
            f"{BASE_URL}/api/hr/departments/{TestHRDepartmentOrg.created_department_id}",
            json=payload
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"PASS: Update department - {TestHRDepartmentOrg.created_department_id}")
    
    def test_04_get_org_structure(self, api_client):
        """GET /api/hr/organization/structure - Get organization structure"""
        response = api_client.get(f"{BASE_URL}/api/hr/organization/structure")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "structure" in data
        print(f"PASS: Get org structure - {len(data['structure'])} departments in structure")
    
    def test_05_get_org_chart(self, api_client):
        """GET /api/hr/organization/chart - Get organization chart"""
        response = api_client.get(f"{BASE_URL}/api/hr/organization/chart")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "chart" in data
        print(f"PASS: Get org chart - {len(data['chart'])} nodes in chart")
    
    def test_06_seed_departments(self, api_client):
        """POST /api/hr/seed-departments - Seed default departments"""
        response = api_client.post(f"{BASE_URL}/api/hr/seed-departments")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "message" in data
        print(f"PASS: Seed departments - {data['message']}")


# ==================== EXPORT SYSTEM ====================
class TestExportSystem:
    """Test Export System (Excel, PDF)"""
    
    def test_01_export_employees_xlsx(self, api_client):
        """GET /api/export-v2/hr/employees?format=xlsx - Export employees to Excel"""
        response = api_client.get(f"{BASE_URL}/api/export-v2/hr/employees?format=xlsx")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        assert "spreadsheet" in response.headers.get("Content-Type", "") or "octet-stream" in response.headers.get("Content-Type", "")
        print(f"PASS: Export employees to XLSX - Size: {len(response.content)} bytes")
    
    def test_02_export_employees_pdf(self, api_client):
        """GET /api/export-v2/hr/employees?format=pdf - Export employees to PDF"""
        response = api_client.get(f"{BASE_URL}/api/export-v2/hr/employees?format=pdf")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        assert "pdf" in response.headers.get("Content-Type", "").lower()
        print(f"PASS: Export employees to PDF - Size: {len(response.content)} bytes")
    
    def test_03_export_products_json(self, api_client):
        """GET /api/export-v2/master/products?format=json - Export products to JSON"""
        response = api_client.get(f"{BASE_URL}/api/export-v2/master/products?format=json")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"PASS: Export products to JSON - Size: {len(response.content)} bytes")
    
    def test_04_export_ranking_employees(self, api_client):
        """GET /api/export-v2/ranking/employees - Export employee ranking"""
        response = api_client.get(f"{BASE_URL}/api/export-v2/ranking/employees?format=json")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "rankings" in data
        print(f"PASS: Export employee ranking - {len(data['rankings'])} employees")
    
    def test_05_export_ranking_branches(self, api_client):
        """GET /api/export-v2/ranking/branches - Export branch ranking"""
        response = api_client.get(f"{BASE_URL}/api/export-v2/ranking/branches?format=json")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "rankings" in data
        print(f"PASS: Export branch ranking - {len(data['rankings'])} branches")
    
    def test_06_export_dashboard_summary(self, api_client):
        """GET /api/export-v2/dashboard/summary - Export dashboard summary"""
        response = api_client.get(f"{BASE_URL}/api/export-v2/dashboard/summary?format=pdf")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        assert "pdf" in response.headers.get("Content-Type", "").lower()
        print(f"PASS: Export dashboard summary PDF - Size: {len(response.content)} bytes")


# ==================== IMPORT SYSTEM ====================
class TestImportSystem:
    """Test Import System - download template & preview"""
    
    def test_01_get_import_templates(self, api_client):
        """GET /api/import/templates - List available import templates"""
        response = api_client.get(f"{BASE_URL}/api/import/templates")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "templates" in data
        assert len(data["templates"]) > 0, "Should have at least one template"
        print(f"PASS: Get import templates - {len(data['templates'])} templates available")
    
    def test_02_download_products_template(self, api_client):
        """GET /api/import/templates/products/download - Download products template"""
        response = api_client.get(f"{BASE_URL}/api/import/templates/products/download")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        assert "spreadsheet" in response.headers.get("Content-Type", "") or len(response.content) > 0
        print(f"PASS: Download products template - Size: {len(response.content)} bytes")
    
    def test_03_download_employees_template(self, api_client):
        """GET /api/import/templates/employees/download - Download employees template"""
        response = api_client.get(f"{BASE_URL}/api/import/templates/employees/download")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"PASS: Download employees template - Size: {len(response.content)} bytes")
    
    def test_04_download_suppliers_template(self, api_client):
        """GET /api/import/templates/suppliers/download - Download suppliers template"""
        response = api_client.get(f"{BASE_URL}/api/import/templates/suppliers/download")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"PASS: Download suppliers template - Size: {len(response.content)} bytes")
    
    def test_05_get_import_history(self, api_client):
        """GET /api/import/history - Get import history"""
        response = api_client.get(f"{BASE_URL}/api/import/history")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "imports" in data
        print(f"PASS: Get import history - {len(data['imports'])} imports")
    
    def test_06_invalid_template_404(self, api_client):
        """GET /api/import/templates/invalid/download - Should return 404"""
        response = api_client.get(f"{BASE_URL}/api/import/templates/invalid_template/download")
        assert response.status_code == 404, f"Expected 404 for invalid template, got {response.status_code}"
        print(f"PASS: Invalid template returns 404")


# ==================== WHATSAPP ALERTS ====================
class TestWhatsAppAlerts:
    """Test WhatsApp Alert templates & recipients"""
    
    created_recipient_id = None
    
    def test_01_get_alert_triggers(self, api_client):
        """GET /api/whatsapp-alerts/triggers - Get available triggers"""
        response = api_client.get(f"{BASE_URL}/api/whatsapp-alerts/triggers")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "triggers" in data
        assert len(data["triggers"]) > 0
        print(f"PASS: Get alert triggers - {len(data['triggers'])} trigger types")
    
    def test_02_get_alert_templates(self, api_client):
        """GET /api/whatsapp-alerts/templates - Get alert templates"""
        response = api_client.get(f"{BASE_URL}/api/whatsapp-alerts/templates")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "templates" in data
        print(f"PASS: Get alert templates - {len(data['templates'])} templates")
    
    def test_03_get_alert_config(self, api_client):
        """GET /api/whatsapp-alerts/config - Get config"""
        response = api_client.get(f"{BASE_URL}/api/whatsapp-alerts/config")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "is_enabled" in data or "type" in data
        print(f"PASS: Get alert config - enabled: {data.get('is_enabled', False)}")
    
    def test_04_get_recipients(self, api_client):
        """GET /api/whatsapp-alerts/recipients - Get recipients"""
        response = api_client.get(f"{BASE_URL}/api/whatsapp-alerts/recipients")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "recipients" in data
        print(f"PASS: Get alert recipients - {len(data['recipients'])} recipients")
    
    def test_05_add_recipient(self, api_client):
        """POST /api/whatsapp-alerts/recipients - Add recipient"""
        payload = {
            "name": "Test Recipient",
            "phone": f"628{uuid.uuid4().hex[:10]}",
            "role": "admin",
            "is_active": True,
            "alert_types": ["minus_kas", "stok_kosong"]
        }
        response = api_client.post(f"{BASE_URL}/api/whatsapp-alerts/recipients", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "recipient" in data
        TestWhatsAppAlerts.created_recipient_id = data["recipient"]["id"]
        print(f"PASS: Add recipient - ID: {TestWhatsAppAlerts.created_recipient_id}")
    
    def test_06_update_recipient(self, api_client):
        """PUT /api/whatsapp-alerts/recipients/{id} - Update recipient"""
        if not TestWhatsAppAlerts.created_recipient_id:
            pytest.skip("No recipient created")
        
        payload = {
            "name": "Updated Test Recipient",
            "phone": f"628{uuid.uuid4().hex[:10]}",
            "role": "spv",
            "is_active": True,
            "alert_types": ["minus_kas", "stok_kosong", "audit_minus"]
        }
        response = api_client.put(
            f"{BASE_URL}/api/whatsapp-alerts/recipients/{TestWhatsAppAlerts.created_recipient_id}",
            json=payload
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"PASS: Update recipient - {TestWhatsAppAlerts.created_recipient_id}")
    
    def test_07_get_alert_logs(self, api_client):
        """GET /api/whatsapp-alerts/logs - Get alert logs"""
        response = api_client.get(f"{BASE_URL}/api/whatsapp-alerts/logs")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "logs" in data
        print(f"PASS: Get alert logs - {len(data['logs'])} logs")
    
    def test_08_test_alert(self, api_client):
        """POST /api/whatsapp-alerts/test - Test alert (MOCKED)"""
        response = api_client.post(
            f"{BASE_URL}/api/whatsapp-alerts/test",
            params={"phone": "628123456789", "message": "Test from automated test"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        # WhatsApp is mocked, so it returns success/queued
        assert "success" in data or "message" in data
        print(f"PASS: Test alert - {data.get('message', data.get('note', 'queued'))}")
    
    def test_09_delete_recipient(self, api_client):
        """DELETE /api/whatsapp-alerts/recipients/{id} - Delete recipient"""
        if not TestWhatsAppAlerts.created_recipient_id:
            pytest.skip("No recipient created")
        
        response = api_client.delete(
            f"{BASE_URL}/api/whatsapp-alerts/recipients/{TestWhatsAppAlerts.created_recipient_id}"
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"PASS: Delete recipient - {TestWhatsAppAlerts.created_recipient_id}")


# ==================== WAR ROOM ALERTS ====================
class TestWarRoomAlerts:
    """Test War Room Alert System"""
    
    created_alert_id = None
    
    def test_01_get_active_alerts(self, api_client):
        """GET /api/warroom-alerts/active - Get active alerts"""
        response = api_client.get(f"{BASE_URL}/api/warroom-alerts/active")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "alerts" in data
        assert "summary" in data
        print(f"PASS: Get active alerts - {data['total']} active, critical: {data['summary']['critical']}")
    
    def test_02_create_alert(self, api_client):
        """POST /api/warroom-alerts/create - Create war room alert"""
        payload = {
            "alert_type": "minus_kas",
            "priority": "high",
            "title": "Test Alert - Minus Kas",
            "message": "Test alert from automated testing",
            "branch_id": gen_test_id(),
            "branch_name": "Test Branch",
            "related_entity_id": gen_test_id(),
            "related_entity_type": "setoran",
            "data": {"amount": -150000, "penjaga": "Test Penjaga"}
        }
        response = api_client.post(f"{BASE_URL}/api/warroom-alerts/create", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "alert" in data
        TestWarRoomAlerts.created_alert_id = data["alert"]["id"]
        print(f"PASS: Create war room alert - ID: {TestWarRoomAlerts.created_alert_id}")
    
    def test_03_get_alert_detail(self, api_client):
        """GET /api/warroom-alerts/{id} - Get alert detail"""
        if not TestWarRoomAlerts.created_alert_id:
            pytest.skip("No alert created")
        
        response = api_client.get(f"{BASE_URL}/api/warroom-alerts/{TestWarRoomAlerts.created_alert_id}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("id") == TestWarRoomAlerts.created_alert_id
        print(f"PASS: Get alert detail - status: {data.get('status')}")
    
    def test_04_acknowledge_alert(self, api_client):
        """POST /api/warroom-alerts/{id}/acknowledge - Acknowledge alert"""
        if not TestWarRoomAlerts.created_alert_id:
            pytest.skip("No alert created")
        
        response = api_client.post(
            f"{BASE_URL}/api/warroom-alerts/{TestWarRoomAlerts.created_alert_id}/acknowledge",
            params={"user_name": "Test User"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"PASS: Acknowledge alert - {TestWarRoomAlerts.created_alert_id}")
    
    def test_05_resolve_alert(self, api_client):
        """POST /api/warroom-alerts/{id}/resolve - Resolve alert"""
        if not TestWarRoomAlerts.created_alert_id:
            pytest.skip("No alert created")
        
        response = api_client.post(
            f"{BASE_URL}/api/warroom-alerts/{TestWarRoomAlerts.created_alert_id}/resolve",
            params={"user_name": "Test User", "notes": "Resolved by automated test"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"PASS: Resolve alert - {TestWarRoomAlerts.created_alert_id}")
    
    def test_06_get_alert_stats(self, api_client):
        """GET /api/warroom-alerts/stats/summary - Get alert statistics"""
        response = api_client.get(f"{BASE_URL}/api/warroom-alerts/stats/summary")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "total_active" in data
        assert "by_priority" in data
        assert "by_status" in data
        print(f"PASS: Get alert stats - active: {data['total_active']}, today: {data.get('today_count', 0)}")
    
    def test_07_get_all_alerts(self, api_client):
        """GET /api/warroom-alerts/all - Get all alerts"""
        response = api_client.get(f"{BASE_URL}/api/warroom-alerts/all")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "alerts" in data
        print(f"PASS: Get all alerts - {len(data['alerts'])} alerts")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
