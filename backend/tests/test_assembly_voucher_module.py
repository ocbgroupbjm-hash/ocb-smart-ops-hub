"""
TEST FILE: Assembly Voucher Module - Perakitan Voucher
OCB TITAN ERP - Assembly Enterprise API Tests

Features tested:
1. List formulas via GET /api/assembly-enterprise/formulas/v2?status=ALL
2. CREATE formula via POST /api/assembly-enterprise/formulas/v2
3. EDIT formula via PUT /api/assembly-enterprise/formulas/v2/{id}
4. HARD DELETE unused voucher - should SUCCEED
5. HARD DELETE used voucher - should FAIL with error "Voucher sudah digunakan..."
6. Execute assembly to mark formula as used

Date: 2026-03-15
"""

import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = 'https://smart-ops-hub-6.preview.emergentagent.com'

# Test credentials
TEST_EMAIL = "ocbgroupbjm@gmail.com"
TEST_PASSWORD = "admin123"


class TestAuthSetup:
    """Authentication tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data, "No token in response"
        return data["token"]
    
    def test_login_success(self, auth_token):
        """Verify login returns valid token"""
        assert auth_token is not None
        assert len(auth_token) > 50


class TestAssemblyFormulaList:
    """Test GET /api/assembly-enterprise/formulas/v2"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        return response.json()["token"]
    
    def test_list_formulas_returns_array(self, auth_token):
        """List formulas should return array"""
        response = requests.get(
            f"{BASE_URL}/api/assembly-enterprise/formulas/v2?status=ALL",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "formulas" in data
        assert isinstance(data["formulas"], list)
    
    def test_list_formulas_has_pagination(self, auth_token):
        """List should include pagination fields"""
        response = requests.get(
            f"{BASE_URL}/api/assembly-enterprise/formulas/v2?status=ALL",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        data = response.json()
        assert "total" in data
        assert "skip" in data
        assert "limit" in data
    
    def test_formula_has_required_fields(self, auth_token):
        """Each formula should have required fields"""
        response = requests.get(
            f"{BASE_URL}/api/assembly-enterprise/formulas/v2?status=ALL",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        data = response.json()
        if data["formulas"]:
            formula = data["formulas"][0]
            required_fields = ["id", "formula_name", "product_result_id", "result_quantity", "status", "components"]
            for field in required_fields:
                assert field in formula, f"Missing field: {field}"


class TestAssemblyFormulaCRUD:
    """Test CREATE, EDIT operations for formulas"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def products(self, auth_token):
        """Get products for testing"""
        response = requests.get(
            f"{BASE_URL}/api/products?limit=5",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        return response.json().get("items", [])
    
    def test_create_formula_success(self, auth_token, products):
        """Create new formula voucher"""
        if len(products) < 2:
            pytest.skip("Need at least 2 products for testing")
        
        unique_name = f"TEST-VOUCHER-{datetime.now().strftime('%H%M%S')}"
        payload = {
            "formula_name": unique_name,
            "product_result_id": products[0]["id"],
            "result_quantity": 1,
            "uom": "pcs",
            "components": [
                {
                    "item_id": products[1]["id"],
                    "quantity_required": 2,
                    "uom": "pcs",
                    "sequence_no": 1
                }
            ],
            "notes": "Test formula created by pytest"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/assembly-enterprise/formulas/v2",
            headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
            json=payload
        )
        
        assert response.status_code == 200, f"Create failed: {response.text}"
        data = response.json()
        assert "id" in data
        assert "message" in data
        assert unique_name in data.get("formula_name", "") or unique_name in data.get("message", "")
    
    def test_create_formula_requires_components(self, auth_token, products):
        """Creating formula without components should fail"""
        if not products:
            pytest.skip("No products available")
        
        payload = {
            "formula_name": f"TEST-NO-COMP-{datetime.now().strftime('%H%M%S')}",
            "product_result_id": products[0]["id"],
            "result_quantity": 1,
            "uom": "pcs",
            "components": [],
            "notes": "Test - should fail"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/assembly-enterprise/formulas/v2",
            headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
            json=payload
        )
        
        # Should fail validation
        assert response.status_code in [400, 422], f"Expected 400/422, got {response.status_code}"
    
    def test_edit_formula_success(self, auth_token):
        """Edit existing formula - update notes"""
        # Get existing formulas
        response = requests.get(
            f"{BASE_URL}/api/assembly-enterprise/formulas/v2?status=ALL",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        formulas = response.json().get("formulas", [])
        
        if not formulas:
            pytest.skip("No formulas to edit")
        
        formula = formulas[0]
        updated_notes = f"Updated by pytest at {datetime.now().isoformat()}"
        
        response = requests.put(
            f"{BASE_URL}/api/assembly-enterprise/formulas/v2/{formula['id']}",
            headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
            json={"notes": updated_notes}
        )
        
        assert response.status_code == 200, f"Edit failed: {response.text}"
        assert "message" in response.json()


class TestAssemblyHardDelete:
    """Test HARD DELETE functionality - critical for this task"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def products(self, auth_token):
        """Get products for testing"""
        response = requests.get(
            f"{BASE_URL}/api/products?limit=5",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        return response.json().get("items", [])
    
    def test_hard_delete_unused_voucher_success(self, auth_token, products):
        """
        CRITICAL TEST: Hard delete an unused voucher should SUCCEED
        1. Create new voucher
        2. Try to hard delete
        3. Should succeed (no transactions linked)
        """
        if len(products) < 2:
            pytest.skip("Need at least 2 products for testing")
        
        # Step 1: Create new formula
        unique_name = f"TEST-DELETE-ME-{datetime.now().strftime('%H%M%S')}"
        create_payload = {
            "formula_name": unique_name,
            "product_result_id": products[0]["id"],
            "result_quantity": 1,
            "uom": "pcs",
            "components": [
                {
                    "item_id": products[1]["id"],
                    "quantity_required": 1,
                    "uom": "pcs",
                    "sequence_no": 1
                }
            ],
            "notes": "Test formula for hard delete - UNUSED"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/assembly-enterprise/formulas/v2",
            headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
            json=create_payload
        )
        
        assert create_response.status_code == 200, f"Create failed: {create_response.text}"
        formula_id = create_response.json()["id"]
        
        # Step 2: Hard delete - should succeed
        delete_response = requests.delete(
            f"{BASE_URL}/api/assembly-enterprise/formulas/v2/{formula_id}/hard-delete",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert delete_response.status_code == 200, f"Hard delete failed: {delete_response.text}"
        data = delete_response.json()
        assert "berhasil dihapus permanen" in data.get("message", "").lower() or "deleted" in data.get("message", "").lower()
        
        # Step 3: Verify formula no longer exists
        get_response = requests.get(
            f"{BASE_URL}/api/assembly-enterprise/formulas/v2/{formula_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert get_response.status_code == 404, "Formula should not exist after hard delete"
    
    def test_hard_delete_used_voucher_fails(self, auth_token, products):
        """
        CRITICAL TEST: Hard delete a USED voucher should FAIL
        1. Create new voucher
        2. Execute assembly (creates transaction)
        3. Try to hard delete
        4. Should FAIL with message "Voucher sudah digunakan pada X transaksi"
        """
        if len(products) < 3:
            pytest.skip("Need at least 3 products for testing")
        
        # Step 1: Create new formula
        unique_name = f"TEST-USED-{datetime.now().strftime('%H%M%S')}"
        create_payload = {
            "formula_name": unique_name,
            "product_result_id": products[0]["id"],
            "result_quantity": 1,
            "uom": "pcs",
            "components": [
                {
                    "item_id": products[2]["id"],
                    "quantity_required": 1,
                    "uom": "pcs",
                    "sequence_no": 1
                }
            ],
            "notes": "Test formula for used voucher delete test"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/assembly-enterprise/formulas/v2",
            headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
            json=create_payload
        )
        
        assert create_response.status_code == 200, f"Create failed: {create_response.text}"
        formula_id = create_response.json()["id"]
        
        # Step 2: Execute assembly to create transaction
        # Note: This may fail due to stock, but transaction record should still be created
        execute_payload = {
            "formula_id": formula_id,
            "planned_qty": 1,
            "notes": "Test execution for delete validation",
            "save_as_draft": True  # Save as draft to avoid stock validation
        }
        
        execute_response = requests.post(
            f"{BASE_URL}/api/assembly-enterprise/execute/v2",
            headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
            json=execute_payload
        )
        
        # Even if execution fails due to stock, check if transaction was created
        if execute_response.status_code != 200:
            # Skip this test if we can't create transaction
            # But first, clean up the formula we created
            requests.delete(
                f"{BASE_URL}/api/assembly-enterprise/formulas/v2/{formula_id}/hard-delete",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            pytest.skip("Could not create assembly transaction for testing")
        
        # Step 3: Try to hard delete - should FAIL
        delete_response = requests.delete(
            f"{BASE_URL}/api/assembly-enterprise/formulas/v2/{formula_id}/hard-delete",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Should return 400 with error message
        assert delete_response.status_code == 400, f"Expected 400, got {delete_response.status_code}"
        
        error_data = delete_response.json()
        error_detail = error_data.get("detail", "")
        
        # Verify error message contains transaction count
        assert "sudah digunakan" in error_detail.lower() or "transaksi" in error_detail.lower(), \
            f"Expected error about being used in transactions, got: {error_detail}"
        assert "tidak dapat dihapus" in error_detail.lower() or "cannot" in error_detail.lower(), \
            f"Expected message about cannot delete, got: {error_detail}"


class TestAssemblyTransactionHistory:
    """Test transaction history endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        return response.json()["token"]
    
    def test_get_history_returns_transactions(self, auth_token):
        """Get assembly transaction history"""
        response = requests.get(
            f"{BASE_URL}/api/assembly-enterprise/history/v2?status=ALL",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "transactions" in data
        assert isinstance(data["transactions"], list)
        assert "total" in data


class TestAssemblyEndpointSecurity:
    """Test endpoint security - unauthorized access"""
    
    def test_list_formulas_requires_auth(self):
        """List formulas without auth should fail"""
        response = requests.get(f"{BASE_URL}/api/assembly-enterprise/formulas/v2?status=ALL")
        assert response.status_code in [401, 403]
    
    def test_hard_delete_requires_auth(self):
        """Hard delete without auth should fail"""
        response = requests.delete(f"{BASE_URL}/api/assembly-enterprise/formulas/v2/fake-id/hard-delete")
        assert response.status_code in [401, 403]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
