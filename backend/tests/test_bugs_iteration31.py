"""
OCB TITAN ERP - Bug Testing Iteration 31
Tests for reported bugs:
1. RBAC Security - Kasir tidak boleh void/delete transaksi (harus 403)
2. Employee Update - tunjangan dan bonus fields harus tersimpan
3. Payroll Rules - PUT dan DELETE harus berfungsi

Test Credentials:
- Owner: ocbgroupbjm@gmail.com / admin123
- Kasir: kasir_test@ocb.com / password123
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAuthentication:
    """Authentication tests - get tokens for both roles"""
    
    @pytest.fixture(scope="class")
    def owner_token(self):
        """Get Owner/Admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "ocbgroupbjm@gmail.com",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Owner login failed: {response.text}"
        data = response.json()
        token = data.get("access_token") or data.get("token")
        assert token, "No token in owner login response"
        print(f"✓ Owner login successful")
        return token
    
    @pytest.fixture(scope="class")
    def kasir_token(self):
        """Get Kasir token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "kasir_test@ocb.com",
            "password": "password123"
        })
        assert response.status_code == 200, f"Kasir login failed: {response.text}"
        data = response.json()
        token = data.get("access_token") or data.get("token")
        assert token, "No token in kasir login response"
        print(f"✓ Kasir login successful")
        return token


class TestRBACKasirSecurity(TestAuthentication):
    """
    RBAC Security Tests - Kasir should NOT be able to void/delete
    Expected: 403 Forbidden
    """
    
    def test_kasir_cannot_void_transaction(self, kasir_token):
        """Kasir should NOT be able to void transaction - expect 403"""
        headers = {"Authorization": f"Bearer {kasir_token}"}
        
        # Try to void a fake transaction
        response = requests.post(
            f"{BASE_URL}/api/pos/void/fake-transaction-id",
            headers=headers,
            params={"reason": "test void"}
        )
        
        # MUST get 403 Forbidden, not 404
        assert response.status_code == 403, f"Expected 403 but got {response.status_code}: {response.text}"
        assert "AKSES DITOLAK" in response.text or "tidak memiliki izin" in response.text.lower()
        print(f"✓ Kasir blocked from voiding transaction (403)")
    
    def test_kasir_cannot_delete_held_transaction(self, kasir_token):
        """Kasir should NOT be able to delete held transaction - expect 403"""
        headers = {"Authorization": f"Bearer {kasir_token}"}
        
        response = requests.delete(
            f"{BASE_URL}/api/pos/held/fake-held-id",
            headers=headers
        )
        
        assert response.status_code == 403, f"Expected 403 but got {response.status_code}: {response.text}"
        print(f"✓ Kasir blocked from deleting held transaction (403)")
    
    def test_kasir_cannot_delete_product(self, kasir_token):
        """Kasir should NOT be able to delete product - expect 403"""
        headers = {"Authorization": f"Bearer {kasir_token}"}
        
        response = requests.delete(
            f"{BASE_URL}/api/products/fake-product-id",
            headers=headers
        )
        
        assert response.status_code == 403, f"Expected 403 but got {response.status_code}: {response.text}"
        print(f"✓ Kasir blocked from deleting product (403)")


class TestOwnerAccess(TestAuthentication):
    """Owner should have full access to all operations"""
    
    def test_owner_can_access_void(self, owner_token):
        """Owner should have permission to void (may get 404 if transaction not found, but NOT 403)"""
        headers = {"Authorization": f"Bearer {owner_token}"}
        
        response = requests.post(
            f"{BASE_URL}/api/pos/void/fake-transaction-id",
            headers=headers,
            params={"reason": "test void"}
        )
        
        # Should NOT be 403 - either 404 (not found) or 400 (bad request)
        assert response.status_code != 403, f"Owner got 403 - RBAC broken! Response: {response.text}"
        print(f"✓ Owner has access to void endpoint (got {response.status_code}, not 403)")
    
    def test_owner_can_access_delete(self, owner_token):
        """Owner should have permission to delete products (may get 404 but NOT 403)"""
        headers = {"Authorization": f"Bearer {owner_token}"}
        
        response = requests.delete(
            f"{BASE_URL}/api/products/fake-product-id",
            headers=headers
        )
        
        assert response.status_code != 403, f"Owner got 403 - RBAC broken! Response: {response.text}"
        print(f"✓ Owner has access to delete endpoint (got {response.status_code}, not 403)")


class TestEmployeeUpdate(TestAuthentication):
    """
    Employee Update - tunjangan dan bonus fields harus tersimpan
    """
    
    def test_create_and_update_employee_with_tunjangan(self, owner_token):
        """Create employee, update with tunjangan fields, verify persistence"""
        headers = {"Authorization": f"Bearer {owner_token}"}
        
        # Step 1: Create test employee
        unique_nik = f"TEST_{uuid.uuid4().hex[:8]}"
        create_payload = {
            "nik": unique_nik,
            "name": "Test Employee Tunjangan",
            "email": f"test_{unique_nik}@example.com",
            "gaji_pokok": 5000000
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/erp/employees",
            headers=headers,
            json=create_payload
        )
        assert create_response.status_code == 200, f"Create failed: {create_response.text}"
        created = create_response.json()
        employee_id = created.get("employee", {}).get("id")
        assert employee_id, f"No employee ID in response: {created}"
        print(f"✓ Created test employee: {employee_id}")
        
        # Step 2: Update with tunjangan fields
        update_payload = {
            "tunjangan_jabatan": 500000,
            "tunjangan_transport": 300000,
            "tunjangan_makan": 200000,
            "tunjangan_keluarga": 400000,
            "tunjangan_lainnya": 100000,
            "bonus_kehadiran": 250000,
            "bonus_performance": 500000,
            "bonus_target": 750000,
            "bonus_lainnya": 100000,
            "potongan_bpjs_kes": 50000,
            "potongan_bpjs_tk": 75000
        }
        
        update_response = requests.put(
            f"{BASE_URL}/api/erp/employees/{employee_id}",
            headers=headers,
            json=update_payload
        )
        assert update_response.status_code == 200, f"Update failed: {update_response.text}"
        print(f"✓ Updated employee with tunjangan fields")
        
        # Step 3: GET to verify data persisted
        get_response = requests.get(
            f"{BASE_URL}/api/erp/employees/{employee_id}",
            headers=headers
        )
        assert get_response.status_code == 200, f"GET failed: {get_response.text}"
        
        emp_data = get_response.json()
        
        # Verify all tunjangan fields
        assert emp_data.get("tunjangan_jabatan") == 500000, f"tunjangan_jabatan not saved: {emp_data.get('tunjangan_jabatan')}"
        assert emp_data.get("tunjangan_transport") == 300000, f"tunjangan_transport not saved"
        assert emp_data.get("tunjangan_makan") == 200000, f"tunjangan_makan not saved"
        assert emp_data.get("tunjangan_keluarga") == 400000, f"tunjangan_keluarga not saved"
        assert emp_data.get("bonus_kehadiran") == 250000, f"bonus_kehadiran not saved"
        assert emp_data.get("bonus_performance") == 500000, f"bonus_performance not saved"
        assert emp_data.get("bonus_target") == 750000, f"bonus_target not saved"
        assert emp_data.get("potongan_bpjs_kes") == 50000, f"potongan_bpjs_kes not saved"
        assert emp_data.get("potongan_bpjs_tk") == 75000, f"potongan_bpjs_tk not saved"
        
        print(f"✓ All tunjangan and bonus fields correctly persisted!")
        
        # Cleanup - delete test employee
        requests.delete(f"{BASE_URL}/api/erp/employees/{employee_id}", headers=headers)


class TestPayrollRules(TestAuthentication):
    """
    Payroll Rules CRUD - PUT and DELETE endpoints
    """
    
    def test_payroll_rules_crud(self, owner_token):
        """Test full CRUD for payroll rules"""
        headers = {"Authorization": f"Bearer {owner_token}"}
        
        # Step 1: Create payroll rule
        unique_jabatan_id = f"jabatan_test_{uuid.uuid4().hex[:8]}"
        create_payload = {
            "jabatan_id": unique_jabatan_id,
            "jabatan_name": "Test Jabatan Payroll",
            "gaji_pokok": 5000000,
            "tunjangan_jabatan": 500000,
            "tunjangan_transport": 300000,
            "tunjangan_makan": 200000,
            "bonus_kehadiran_full": 250000,
            "potongan_telat_per_menit": 5000,
            "potongan_alpha_per_hari": 200000
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/erp/master/payroll-rules",
            headers=headers,
            json=create_payload
        )
        assert create_response.status_code == 200, f"Create payroll rule failed: {create_response.text}"
        created = create_response.json()
        print(f"✓ Created payroll rule: {created}")
        
        # Get the rule ID from list
        list_response = requests.get(
            f"{BASE_URL}/api/erp/master/payroll-rules",
            headers=headers
        )
        assert list_response.status_code == 200
        rules = list_response.json().get("rules", [])
        rule_id = None
        for rule in rules:
            if rule.get("jabatan_id") == unique_jabatan_id:
                rule_id = rule.get("id")
                break
        
        assert rule_id, f"Could not find created rule in list"
        print(f"✓ Found rule ID: {rule_id}")
        
        # Step 2: PUT - Update payroll rule
        update_payload = {
            "jabatan_id": unique_jabatan_id,
            "jabatan_name": "Test Jabatan UPDATED",
            "gaji_pokok": 6000000,
            "tunjangan_jabatan": 600000,
            "tunjangan_transport": 400000,
            "tunjangan_makan": 250000,
            "bonus_kehadiran_full": 300000,
            "potongan_telat_per_menit": 6000,
            "potongan_alpha_per_hari": 250000
        }
        
        update_response = requests.put(
            f"{BASE_URL}/api/erp/master/payroll-rules/{rule_id}",
            headers=headers,
            json=update_payload
        )
        assert update_response.status_code == 200, f"PUT payroll rule failed: {update_response.status_code} - {update_response.text}"
        print(f"✓ PUT payroll-rules/{rule_id} works - Response: {update_response.text}")
        
        # Verify update persisted
        list_response2 = requests.get(
            f"{BASE_URL}/api/erp/master/payroll-rules",
            headers=headers
        )
        rules2 = list_response2.json().get("rules", [])
        updated_rule = None
        for rule in rules2:
            if rule.get("id") == rule_id:
                updated_rule = rule
                break
        
        if updated_rule:
            assert updated_rule.get("gaji_pokok") == 6000000, f"PUT did not persist gaji_pokok"
            assert updated_rule.get("tunjangan_jabatan") == 600000, f"PUT did not persist tunjangan_jabatan"
            print(f"✓ PUT updates persisted correctly")
        
        # Step 3: DELETE - Delete payroll rule
        delete_response = requests.delete(
            f"{BASE_URL}/api/erp/master/payroll-rules/{rule_id}",
            headers=headers
        )
        assert delete_response.status_code == 200, f"DELETE payroll rule failed: {delete_response.status_code} - {delete_response.text}"
        print(f"✓ DELETE payroll-rules/{rule_id} works - Response: {delete_response.text}")
        
        # Verify deletion (soft delete - is_active=False)
        list_response3 = requests.get(
            f"{BASE_URL}/api/erp/master/payroll-rules",
            headers=headers
        )
        rules3 = list_response3.json().get("rules", [])
        found = any(r.get("id") == rule_id for r in rules3)
        assert not found, "Rule still visible after DELETE (soft delete should set is_active=False)"
        print(f"✓ DELETE soft-delete verified - rule no longer in active list")


class TestHealthCheck:
    """Basic API health check"""
    
    def test_api_health(self):
        """Check API is accessible"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Health check failed: {response.status_code}"
        print(f"✓ API health check passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
