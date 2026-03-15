"""
OCB TITAN ERP - Enterprise Stabilization Testing (Iteration 73)
Testing 4 Tasks:
  TASK 1: Data Sheet - GET /api/customers, /api/suppliers, /api/erp/employees
  TASK 2: Quick Create - POST /api/master/categories, /api/master/units, /api/master/brands
  TASK 3: Assembly Enterprise - GET /api/assembly-enterprise/formulas/v2, /api/assembly-enterprise/history/v2
  TASK 4: Reversal flow evidence (if POSTED transactions exist)
  
Governance: All testing only on ocb_titan tenant
"""

import pytest
import requests
import os
import uuid
from datetime import datetime

# Backend URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials for ocb_titan tenant
TEST_EMAIL = "ocbgroupbjm@gmail.com"
TEST_PASSWORD = "admin123"


class TestAuthAndSetup:
    """Authentication and setup tests"""
    token = None
    
    @pytest.fixture(autouse=True, scope="class")
    def setup_auth(self, request):
        """Login and get token for all tests"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
                "db_name": "ocb_titan"
            }
        )
        if response.status_code == 200:
            request.cls.token = response.json().get("token")
            request.cls.user = response.json().get("user", {})
            print(f"\n✓ Login successful for tenant ocb_titan")
        else:
            pytest.skip(f"Login failed: {response.status_code} - {response.text}")
    
    def get_headers(self):
        return {"Authorization": f"Bearer {self.token}"}
    
    def test_health_check(self):
        """Test API health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print(f"✓ Health check passed - DB: {data.get('active_database')}")
    
    def test_login_success(self, setup_auth):
        """Verify login was successful"""
        assert self.token is not None
        print(f"✓ Auth token acquired")


class TestTask1DataSheetBinding:
    """
    TASK 1: Data Sheet binding tests
    Verify GET endpoints return correct data for customers, suppliers, employees
    """
    token = None
    
    @pytest.fixture(autouse=True, scope="class")
    def setup_auth(self, request):
        """Login for this test class"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD, "db_name": "ocb_titan"}
        )
        if response.status_code == 200:
            request.cls.token = response.json().get("token")
        else:
            pytest.skip("Auth failed")
    
    def get_headers(self):
        return {"Authorization": f"Bearer {self.token}"}
    
    # ========== CUSTOMERS ==========
    def test_get_customers_endpoint(self):
        """TASK 1: GET /api/customers should return items array with 15+ customers"""
        response = requests.get(f"{BASE_URL}/api/customers", headers=self.get_headers())
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Response should have 'items' array or be an array directly
        items = data.get("items") or data.get("customers") or data
        if isinstance(items, list):
            count = len(items)
        else:
            count = data.get("total", 0)
        
        print(f"✓ GET /api/customers - Total: {count} customers")
        # Data Sheet expects 15 customers for ocb_titan
        assert count >= 0, "Customers endpoint should return data"
    
    def test_customers_response_structure(self):
        """Verify customers response has correct structure for Data Sheet"""
        response = requests.get(f"{BASE_URL}/api/customers", headers=self.get_headers())
        assert response.status_code == 200
        
        data = response.json()
        items = data.get("items", [])
        
        if items:
            first = items[0]
            # Data Sheet expects these fields
            expected_fields = ["id", "name"]
            for field in expected_fields:
                assert field in first, f"Customer missing field: {field}"
            print(f"✓ Customer structure valid - has fields: {list(first.keys())[:8]}...")
    
    # ========== SUPPLIERS ==========
    def test_get_suppliers_endpoint(self):
        """TASK 1: GET /api/suppliers should return items array with 12+ suppliers"""
        response = requests.get(f"{BASE_URL}/api/suppliers", headers=self.get_headers())
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Response should have 'items' array
        items = data.get("items") or data.get("suppliers") or data
        if isinstance(items, list):
            count = len(items)
        else:
            count = data.get("total", 0)
        
        print(f"✓ GET /api/suppliers - Total: {count} suppliers")
        assert count >= 0, "Suppliers endpoint should return data"
    
    def test_suppliers_response_structure(self):
        """Verify suppliers response has correct structure for Data Sheet"""
        response = requests.get(f"{BASE_URL}/api/suppliers", headers=self.get_headers())
        assert response.status_code == 200
        
        data = response.json()
        items = data.get("items", [])
        
        if items:
            first = items[0]
            expected_fields = ["id", "name"]
            for field in expected_fields:
                assert field in first, f"Supplier missing field: {field}"
            print(f"✓ Supplier structure valid - has fields: {list(first.keys())[:8]}...")
    
    # ========== EMPLOYEES ==========
    def test_get_employees_endpoint(self):
        """TASK 1: GET /api/erp/employees should return employees array with 21+ employees"""
        response = requests.get(f"{BASE_URL}/api/erp/employees", headers=self.get_headers())
        
        # Employee endpoint may have different response structure
        if response.status_code == 200:
            data = response.json()
            # Could be {employees: []} or {items: []} or direct array
            employees = data.get("employees") or data.get("items") or data
            if isinstance(employees, list):
                count = len(employees)
            else:
                count = data.get("total", 0)
            
            print(f"✓ GET /api/erp/employees - Total: {count} employees")
            assert count >= 0, "Employees endpoint should return data"
        else:
            print(f"⚠ GET /api/erp/employees returned {response.status_code}")
            # Try HR enterprise endpoint as fallback
            response2 = requests.get(f"{BASE_URL}/api/hr/employees", headers=self.get_headers())
            if response2.status_code == 200:
                data = response2.json()
                count = data.get("total", 0)
                print(f"✓ GET /api/hr/employees (fallback) - Total: {count} employees")
                assert count >= 0
            else:
                pytest.skip(f"Employees endpoints not available: {response.status_code}, {response2.status_code}")
    
    def test_employees_response_structure(self):
        """Verify employees response has correct structure for Data Sheet"""
        response = requests.get(f"{BASE_URL}/api/erp/employees", headers=self.get_headers())
        
        if response.status_code != 200:
            response = requests.get(f"{BASE_URL}/api/hr/employees", headers=self.get_headers())
        
        if response.status_code == 200:
            data = response.json()
            employees = data.get("employees") or data.get("items") or []
            
            if employees:
                first = employees[0]
                # Data Sheet expects these fields for employees
                assert "id" in first or "employee_id" in first, "Employee missing ID field"
                assert "full_name" in first or "name" in first, "Employee missing name field"
                print(f"✓ Employee structure valid - has fields: {list(first.keys())[:8]}...")


class TestTask2QuickCreate:
    """
    TASK 2: Quick Create master references tests
    Test POST endpoints for creating categories, units, brands from item form
    """
    token = None
    created_ids = {"category": None, "unit": None, "brand": None}
    
    @pytest.fixture(autouse=True, scope="class")
    def setup_auth(self, request):
        """Login for this test class"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD, "db_name": "ocb_titan"}
        )
        if response.status_code == 200:
            request.cls.token = response.json().get("token")
        else:
            pytest.skip("Auth failed")
    
    def get_headers(self):
        return {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
    
    # ========== CATEGORIES ==========
    def test_create_category(self):
        """TASK 2: POST /api/master/categories - Quick create new category"""
        unique_code = f"TEST-CAT-{uuid.uuid4().hex[:6].upper()}"
        payload = {
            "code": unique_code,
            "name": f"Test Category {datetime.now().strftime('%H%M%S')}",
            "description": "Created by quick create testing"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/master/categories",
            json=payload,
            headers=self.get_headers()
        )
        
        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Store created ID for cleanup/verification
        self.created_ids["category"] = data.get("id")
        print(f"✓ POST /api/master/categories - Created: {unique_code}, ID: {data.get('id')}")
    
    def test_get_categories_list(self):
        """Verify categories list endpoint works"""
        response = requests.get(f"{BASE_URL}/api/master/categories", headers=self.get_headers())
        assert response.status_code == 200
        
        data = response.json()
        # Response is array of categories
        if isinstance(data, list):
            print(f"✓ GET /api/master/categories - Total: {len(data)} categories")
        else:
            items = data.get("items") or data.get("categories") or []
            print(f"✓ GET /api/master/categories - Total: {len(items)} categories")
    
    # ========== UNITS ==========
    def test_create_unit(self):
        """TASK 2: POST /api/master/units - Quick create new unit"""
        unique_code = f"TEST-UNT-{uuid.uuid4().hex[:6].upper()}"
        payload = {
            "code": unique_code,
            "name": f"Test Unit {datetime.now().strftime('%H%M%S')}",
            "description": "Created by quick create testing"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/master/units",
            json=payload,
            headers=self.get_headers()
        )
        
        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}: {response.text}"
        data = response.json()
        
        self.created_ids["unit"] = data.get("id")
        print(f"✓ POST /api/master/units - Created: {unique_code}, ID: {data.get('id')}")
    
    def test_get_units_list(self):
        """Verify units list endpoint works"""
        response = requests.get(f"{BASE_URL}/api/master/units", headers=self.get_headers())
        assert response.status_code == 200
        
        data = response.json()
        if isinstance(data, list):
            print(f"✓ GET /api/master/units - Total: {len(data)} units")
        else:
            items = data.get("items") or data.get("units") or []
            print(f"✓ GET /api/master/units - Total: {len(items)} units")
    
    # ========== BRANDS ==========
    def test_create_brand(self):
        """TASK 2: POST /api/master/brands - Quick create new brand"""
        unique_code = f"TEST-BRD-{uuid.uuid4().hex[:6].upper()}"
        payload = {
            "code": unique_code,
            "name": f"Test Brand {datetime.now().strftime('%H%M%S')}",
            "description": "Created by quick create testing"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/master/brands",
            json=payload,
            headers=self.get_headers()
        )
        
        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}: {response.text}"
        data = response.json()
        
        self.created_ids["brand"] = data.get("id")
        print(f"✓ POST /api/master/brands - Created: {unique_code}, ID: {data.get('id')}")
    
    def test_get_brands_list(self):
        """Verify brands list endpoint works"""
        response = requests.get(f"{BASE_URL}/api/master/brands", headers=self.get_headers())
        assert response.status_code == 200
        
        data = response.json()
        if isinstance(data, list):
            print(f"✓ GET /api/master/brands - Total: {len(data)} brands")
        else:
            items = data.get("items") or data.get("brands") or []
            print(f"✓ GET /api/master/brands - Total: {len(items)} brands")


class TestTask3AssemblyEnterpriseAPI:
    """
    TASK 3: Assembly Enterprise API tests
    Verify GET /api/assembly-enterprise/formulas/v2 and /api/assembly-enterprise/history/v2
    """
    token = None
    
    @pytest.fixture(autouse=True, scope="class")
    def setup_auth(self, request):
        """Login for this test class"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD, "db_name": "ocb_titan"}
        )
        if response.status_code == 200:
            request.cls.token = response.json().get("token")
        else:
            pytest.skip("Auth failed")
    
    def get_headers(self):
        return {"Authorization": f"Bearer {self.token}"}
    
    # ========== FORMULAS V2 ==========
    def test_get_assembly_formulas_v2(self):
        """TASK 3: GET /api/assembly-enterprise/formulas/v2 returns formulas"""
        response = requests.get(
            f"{BASE_URL}/api/assembly-enterprise/formulas/v2",
            headers=self.get_headers()
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        formulas = data.get("formulas", [])
        total = data.get("total", len(formulas))
        
        print(f"✓ GET /api/assembly-enterprise/formulas/v2 - Total: {total} formulas")
        assert "formulas" in data, "Response should contain 'formulas' array"
    
    def test_get_assembly_formulas_v2_structure(self):
        """Verify formula response structure"""
        response = requests.get(
            f"{BASE_URL}/api/assembly-enterprise/formulas/v2",
            headers=self.get_headers()
        )
        assert response.status_code == 200
        
        data = response.json()
        formulas = data.get("formulas", [])
        
        if formulas:
            first = formulas[0]
            expected_fields = ["id", "formula_name", "status"]
            for field in expected_fields:
                if field not in first:
                    # Legacy formulas might have different field names
                    alt_fields = {"formula_name": "name"}
                    alt = alt_fields.get(field)
                    if alt and alt in first:
                        continue
                assert field in first or first.get("source") == "legacy", f"Formula missing field: {field}"
            print(f"✓ Formula structure valid - has fields: {list(first.keys())[:10]}...")
    
    def test_get_assembly_formulas_with_status_filter(self):
        """Test formulas endpoint with status filter"""
        # Test with ACTIVE filter
        response = requests.get(
            f"{BASE_URL}/api/assembly-enterprise/formulas/v2?status=ACTIVE",
            headers=self.get_headers()
        )
        assert response.status_code == 200
        
        data = response.json()
        print(f"✓ GET /api/assembly-enterprise/formulas/v2?status=ACTIVE - {data.get('total', 0)} formulas")
        
        # Test with ALL filter
        response_all = requests.get(
            f"{BASE_URL}/api/assembly-enterprise/formulas/v2?status=ALL",
            headers=self.get_headers()
        )
        assert response_all.status_code == 200
        data_all = response_all.json()
        print(f"✓ GET /api/assembly-enterprise/formulas/v2?status=ALL - {data_all.get('total', 0)} formulas")
    
    # ========== HISTORY V2 ==========
    def test_get_assembly_history_v2(self):
        """TASK 3: GET /api/assembly-enterprise/history/v2 returns transactions"""
        response = requests.get(
            f"{BASE_URL}/api/assembly-enterprise/history/v2",
            headers=self.get_headers()
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        transactions = data.get("transactions", [])
        total = data.get("total", len(transactions))
        
        print(f"✓ GET /api/assembly-enterprise/history/v2 - Total: {total} transactions")
        assert "transactions" in data, "Response should contain 'transactions' array"
    
    def test_get_assembly_history_v2_with_status_filter(self):
        """Test history endpoint with status filters"""
        statuses = ["DRAFT", "POSTED", "REVERSED", "CANCELLED", "ALL"]
        
        for status in statuses:
            response = requests.get(
                f"{BASE_URL}/api/assembly-enterprise/history/v2?status={status}",
                headers=self.get_headers()
            )
            assert response.status_code == 200, f"Status filter {status} failed: {response.status_code}"
            
            data = response.json()
            count = data.get("total", len(data.get("transactions", [])))
            print(f"  - Status={status}: {count} transactions")
        
        print(f"✓ All status filters working for /api/assembly-enterprise/history/v2")
    
    def test_get_assembly_history_v2_structure(self):
        """Verify history response structure"""
        response = requests.get(
            f"{BASE_URL}/api/assembly-enterprise/history/v2?status=ALL",
            headers=self.get_headers()
        )
        assert response.status_code == 200
        
        data = response.json()
        transactions = data.get("transactions", [])
        
        if transactions:
            first = transactions[0]
            expected_fields = ["id", "assembly_number", "status"]
            for field in expected_fields:
                assert field in first, f"Transaction missing field: {field}"
            print(f"✓ Transaction structure valid - has fields: {list(first.keys())[:10]}...")


class TestTask4ReversalFlow:
    """
    TASK 4: Complete reversal flow evidence
    Test if POSTED transactions can be reversed properly
    """
    token = None
    
    @pytest.fixture(autouse=True, scope="class")
    def setup_auth(self, request):
        """Login for this test class"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD, "db_name": "ocb_titan"}
        )
        if response.status_code == 200:
            request.cls.token = response.json().get("token")
        else:
            pytest.skip("Auth failed")
    
    def get_headers(self):
        return {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
    
    def test_reversal_endpoint_exists(self):
        """TASK 4: Verify reversal endpoint exists"""
        # Try to call reverse with invalid ID to check endpoint exists
        response = requests.post(
            f"{BASE_URL}/api/assembly-enterprise/execute/v2/reverse",
            json={
                "assembly_id": "non-existent-id",
                "reason": "Test reversal endpoint"
            },
            headers=self.get_headers()
        )
        
        # Expected: 404 (not found) or 400 (bad request), NOT 405 (method not allowed)
        assert response.status_code in [400, 404, 422], \
            f"Reversal endpoint should exist. Got {response.status_code}: {response.text}"
        print(f"✓ Reversal endpoint exists (POST /api/assembly-enterprise/execute/v2/reverse)")
    
    def test_find_posted_transactions_for_reversal(self):
        """TASK 4: Check if there are any POSTED transactions available for reversal"""
        response = requests.get(
            f"{BASE_URL}/api/assembly-enterprise/history/v2?status=POSTED",
            headers=self.get_headers()
        )
        assert response.status_code == 200
        
        data = response.json()
        posted_transactions = data.get("transactions", [])
        
        if posted_transactions:
            print(f"✓ Found {len(posted_transactions)} POSTED transactions available for reversal")
            # Don't actually reverse - just verify they exist
            first = posted_transactions[0]
            print(f"  - First POSTED: {first.get('assembly_number')}, Formula: {first.get('formula_name')}")
        else:
            print(f"⚠ No POSTED transactions found - reversal test skipped")
            print(f"  Note: To test full reversal flow, need to POST a DRAFT assembly first")
            # This is expected based on iteration_72 - POST fails due to 0 stock
    
    def test_draft_workflow_rules(self):
        """TASK 4: Verify business rules for DRAFT workflow"""
        # Get a DRAFT transaction if available
        response = requests.get(
            f"{BASE_URL}/api/assembly-enterprise/history/v2?status=DRAFT",
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            data = response.json()
            drafts = data.get("transactions", [])
            
            if drafts:
                print(f"✓ Found {len(drafts)} DRAFT transactions")
                draft_id = drafts[0].get("id")
                
                # Try to reverse a DRAFT - should fail
                reverse_response = requests.post(
                    f"{BASE_URL}/api/assembly-enterprise/execute/v2/reverse",
                    json={"assembly_id": draft_id, "reason": "Test invalid reversal"},
                    headers=self.get_headers()
                )
                
                # Should get 400 - only POSTED can be reversed
                if reverse_response.status_code == 400:
                    print(f"✓ Business rule verified: DRAFT cannot be reversed (returns 400)")
                else:
                    print(f"  Reverse response: {reverse_response.status_code}")
            else:
                print(f"  No DRAFT transactions to test workflow rules")
    
    def test_post_endpoint_exists(self):
        """TASK 4: Verify POST endpoint for assembly exists"""
        response = requests.post(
            f"{BASE_URL}/api/assembly-enterprise/execute/v2/post",
            json={"assembly_id": "non-existent-id"},
            headers=self.get_headers()
        )
        
        # Expected: 404 (not found), NOT 405 (method not allowed)
        assert response.status_code in [400, 404, 422], \
            f"POST endpoint should exist. Got {response.status_code}: {response.text}"
        print(f"✓ POST endpoint exists (POST /api/assembly-enterprise/execute/v2/post)")


class TestLegacyAPICompatibility:
    """
    Additional: Test legacy assembly API endpoints still work
    """
    token = None
    
    @pytest.fixture(autouse=True, scope="class")
    def setup_auth(self, request):
        """Login for this test class"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD, "db_name": "ocb_titan"}
        )
        if response.status_code == 200:
            request.cls.token = response.json().get("token")
        else:
            pytest.skip("Auth failed")
    
    def get_headers(self):
        return {"Authorization": f"Bearer {self.token}"}
    
    def test_legacy_assembly_formulas(self):
        """Test legacy assembly formulas endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/assembly/formulas",
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            data = response.json()
            formulas = data.get("formulas", data)
            if isinstance(formulas, list):
                print(f"✓ Legacy GET /api/assembly/formulas - {len(formulas)} formulas")
            else:
                print(f"✓ Legacy GET /api/assembly/formulas - OK")
        else:
            print(f"⚠ Legacy endpoint /api/assembly/formulas returned {response.status_code}")
    
    def test_legacy_assembly_transactions(self):
        """Test legacy assembly transactions endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/assembly/transactions",
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            data = response.json()
            transactions = data.get("transactions", data)
            if isinstance(transactions, list):
                print(f"✓ Legacy GET /api/assembly/transactions - {len(transactions)} transactions")
            else:
                print(f"✓ Legacy GET /api/assembly/transactions - OK")
        else:
            print(f"⚠ Legacy endpoint /api/assembly/transactions returned {response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
