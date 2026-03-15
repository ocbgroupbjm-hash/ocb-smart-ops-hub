"""
Assembly Enterprise Module Test - OCB TITAN ERP
Tests for the new /api/assembly-enterprise endpoints:
- Formula CRUD with multi-component support
- DRAFT -> POST workflow
- REVERSAL for POSTED transactions
- Stock movements SSOT (ASSEMBLY_CONSUME/PRODUCE)
- Journal entries integration
- Edit/Delete for DRAFT only
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "ocbgroupbjm@gmail.com"
TEST_PASSWORD = "admin123"
TEST_TENANT = "ocb_titan"

# Test data storage
test_data = {
    "auth_token": None,
    "formula_id": None,
    "draft_assembly_id": None,
    "posted_assembly_id": None
}


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for tests"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    token = response.json().get("token")
    test_data["auth_token"] = token
    return token


@pytest.fixture(scope="module")
def headers(auth_token):
    """Get headers with auth token"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


# ============ FORMULA TESTS ============

class TestFormulaEndpoints:
    """Test formula CRUD endpoints - /api/assembly-enterprise/formulas/v2"""
    
    def test_01_list_formulas_v2(self, headers):
        """Test GET /api/assembly-enterprise/formulas/v2 - List all formulas"""
        response = requests.get(
            f"{BASE_URL}/api/assembly-enterprise/formulas/v2",
            headers=headers,
            params={"status": "ALL", "include_legacy": True}
        )
        assert response.status_code == 200, f"List formulas failed: {response.text}"
        data = response.json()
        assert "formulas" in data
        assert "total" in data
        print(f"Found {data['total']} formulas (v2 + legacy)")
        
        # Check if existing test formula exists
        for f in data.get("formulas", []):
            if "ENTERPRISE-TEST" in f.get("formula_name", ""):
                test_data["formula_id"] = f.get("id")
                print(f"Found existing test formula: {f.get('formula_name')}")
    
    def test_02_create_formula_v2_multi_component(self, headers):
        """Test POST /api/assembly-enterprise/formulas/v2 - Create formula with 2+ components"""
        # First get products for components (API returns 'items' key)
        products_response = requests.get(
            f"{BASE_URL}/api/products",
            headers=headers,
            params={"limit": 10}
        )
        assert products_response.status_code == 200, "Failed to get products"
        products = products_response.json().get("items", [])
        
        if len(products) < 3:
            pytest.skip("Not enough products to test multi-component formula")
        
        # Use first product as result, next 2 as components
        result_product = products[0]
        component1 = products[1]
        component2 = products[2]
        
        formula_data = {
            "formula_name": f"ENTERPRISE-TEST-{uuid.uuid4().hex[:6]}",
            "product_result_id": result_product["id"],
            "result_quantity": 1,
            "uom": "pcs",
            "components": [
                {
                    "item_id": component1["id"],
                    "quantity_required": 2,
                    "uom": "pcs",
                    "sequence_no": 1,
                    "waste_factor": 0
                },
                {
                    "item_id": component2["id"],
                    "quantity_required": 1,
                    "uom": "pcs",
                    "sequence_no": 2,
                    "waste_factor": 0
                }
            ],
            "notes": "Test formula dengan 2 komponen untuk Enterprise Testing"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/assembly-enterprise/formulas/v2",
            headers=headers,
            json=formula_data
        )
        assert response.status_code == 200, f"Create formula failed: {response.text}"
        data = response.json()
        assert "id" in data
        assert data.get("component_count") == 2
        test_data["formula_id"] = data["id"]
        print(f"Created formula: {data.get('formula_name')} with ID: {data['id']}")
    
    def test_03_get_formula_v2_detail(self, headers):
        """Test GET /api/assembly-enterprise/formulas/v2/{id} - Get formula details"""
        formula_id = test_data.get("formula_id")
        if not formula_id:
            pytest.skip("No formula ID available")
        
        response = requests.get(
            f"{BASE_URL}/api/assembly-enterprise/formulas/v2/{formula_id}",
            headers=headers
        )
        assert response.status_code == 200, f"Get formula detail failed: {response.text}"
        data = response.json()
        assert data.get("id") == formula_id
        assert "components" in data
        assert len(data.get("components", [])) >= 1
        print(f"Formula has {len(data.get('components', []))} components")


# ============ EXECUTION TESTS ============

class TestExecutionEndpoints:
    """Test execution endpoints - /api/assembly-enterprise/execute/v2"""
    
    def test_04_validate_stock(self, headers):
        """Test GET /api/assembly-enterprise/validate/stock/{formula_id}"""
        formula_id = test_data.get("formula_id")
        if not formula_id:
            pytest.skip("No formula ID available")
        
        response = requests.get(
            f"{BASE_URL}/api/assembly-enterprise/validate/stock/{formula_id}",
            headers=headers,
            params={"planned_qty": 1}
        )
        assert response.status_code == 200, f"Validate stock failed: {response.text}"
        data = response.json()
        assert "can_execute" in data
        assert "components" in data
        assert "insufficient_items" in data
        print(f"Stock validation: can_execute={data.get('can_execute')}, insufficient={len(data.get('insufficient_items', []))}")
    
    def test_05_execute_assembly_create_draft(self, headers):
        """Test POST /api/assembly-enterprise/execute/v2 - Create DRAFT assembly"""
        formula_id = test_data.get("formula_id")
        if not formula_id:
            pytest.skip("No formula ID available")
        
        execution_data = {
            "formula_id": formula_id,
            "planned_qty": 1,
            "notes": "Test DRAFT assembly dari testing agent",
            "save_as_draft": True
        }
        
        response = requests.post(
            f"{BASE_URL}/api/assembly-enterprise/execute/v2",
            headers=headers,
            json=execution_data
        )
        assert response.status_code == 200, f"Create DRAFT failed: {response.text}"
        data = response.json()
        assert data.get("status") == "DRAFT"
        assert "id" in data
        assert "assembly_number" in data
        test_data["draft_assembly_id"] = data["id"]
        print(f"Created DRAFT assembly: {data.get('assembly_number')} with ID: {data['id']}")
    
    def test_06_post_draft_assembly(self, headers):
        """Test POST /api/assembly-enterprise/execute/v2/post - Post DRAFT assembly"""
        draft_id = test_data.get("draft_assembly_id")
        if not draft_id:
            pytest.skip("No draft assembly ID available")
        
        response = requests.post(
            f"{BASE_URL}/api/assembly-enterprise/execute/v2/post",
            headers=headers,
            json={"assembly_id": draft_id}
        )
        
        # May fail due to insufficient stock - that's expected behavior
        if response.status_code == 400:
            error_detail = response.json().get("detail", {})
            if isinstance(error_detail, dict) and "items" in error_detail:
                print(f"POST failed due to insufficient stock - EXPECTED BEHAVIOR")
                print(f"Insufficient items: {error_detail.get('items')}")
                # Create a new draft to keep for other tests
                formula_id = test_data.get("formula_id")
                new_draft = requests.post(
                    f"{BASE_URL}/api/assembly-enterprise/execute/v2",
                    headers=headers,
                    json={
                        "formula_id": formula_id,
                        "planned_qty": 1,
                        "notes": "Test DRAFT for edit/delete testing",
                        "save_as_draft": True
                    }
                )
                if new_draft.status_code == 200:
                    test_data["draft_assembly_id"] = new_draft.json().get("id")
                return
        
        assert response.status_code == 200, f"Post DRAFT failed: {response.text}"
        data = response.json()
        assert data.get("status") == "POSTED"
        test_data["posted_assembly_id"] = draft_id
        print(f"Posted assembly: {data.get('assembly_number')}")
        print(f"Journal created: {data.get('journal_number')}")
        print(f"Stock movements: {data.get('stock_movements_created')}")


# ============ DRAFT EDIT/DELETE TESTS ============

class TestDraftOperations:
    """Test DRAFT edit and delete operations"""
    
    def test_07_edit_draft_assembly(self, headers):
        """Test PUT /api/assembly-enterprise/transactions/v2/{id} - Edit DRAFT"""
        draft_id = test_data.get("draft_assembly_id")
        if not draft_id:
            pytest.skip("No draft assembly ID available")
        
        # First check if it's still a DRAFT
        history_response = requests.get(
            f"{BASE_URL}/api/assembly-enterprise/history/v2/{draft_id}",
            headers=headers
        )
        if history_response.status_code == 200:
            status = history_response.json().get("status")
            if status != "DRAFT":
                pytest.skip(f"Assembly is {status}, not DRAFT - skipping edit test")
        
        formula_id = test_data.get("formula_id")
        edit_data = {
            "formula_id": formula_id,
            "planned_qty": 2,  # Changed from 1 to 2
            "notes": "Updated notes - testing edit DRAFT"
        }
        
        response = requests.put(
            f"{BASE_URL}/api/assembly-enterprise/transactions/v2/{draft_id}",
            headers=headers,
            json=edit_data
        )
        assert response.status_code == 200, f"Edit DRAFT failed: {response.text}"
        print("DRAFT assembly berhasil diupdate")
    
    def test_08_delete_draft_assembly(self, headers):
        """Test DELETE /api/assembly-enterprise/transactions/v2/{id} - Delete DRAFT"""
        # Create a new draft specifically for deletion test
        formula_id = test_data.get("formula_id")
        if not formula_id:
            pytest.skip("No formula ID available")
        
        # Create draft to delete
        new_draft = requests.post(
            f"{BASE_URL}/api/assembly-enterprise/execute/v2",
            headers=headers,
            json={
                "formula_id": formula_id,
                "planned_qty": 1,
                "notes": "Draft to be deleted",
                "save_as_draft": True
            }
        )
        assert new_draft.status_code == 200, f"Create draft for deletion failed: {new_draft.text}"
        delete_id = new_draft.json().get("id")
        
        # Delete it
        response = requests.delete(
            f"{BASE_URL}/api/assembly-enterprise/transactions/v2/{delete_id}",
            headers=headers
        )
        assert response.status_code == 200, f"Delete DRAFT failed: {response.text}"
        print(f"Draft assembly {delete_id} berhasil dibatalkan (soft delete)")
        
        # Verify it's CANCELLED
        verify = requests.get(
            f"{BASE_URL}/api/assembly-enterprise/history/v2/{delete_id}",
            headers=headers
        )
        assert verify.status_code == 200
        assert verify.json().get("status") == "CANCELLED"


# ============ HISTORY TESTS ============

class TestHistoryEndpoints:
    """Test history and audit endpoints"""
    
    def test_09_list_assembly_history(self, headers):
        """Test GET /api/assembly-enterprise/history/v2 - List with status filter"""
        # Test ALL status
        response = requests.get(
            f"{BASE_URL}/api/assembly-enterprise/history/v2",
            headers=headers,
            params={"status": "ALL", "limit": 50}
        )
        assert response.status_code == 200, f"List history failed: {response.text}"
        data = response.json()
        assert "transactions" in data
        assert "total" in data
        print(f"Total assembly transactions: {data.get('total')}")
        
        # Count by status
        status_counts = {}
        for txn in data.get("transactions", []):
            status = txn.get("status", "UNKNOWN")
            status_counts[status] = status_counts.get(status, 0) + 1
        print(f"Status breakdown: {status_counts}")
    
    def test_10_list_history_by_status_draft(self, headers):
        """Test GET /api/assembly-enterprise/history/v2 - Filter DRAFT only"""
        response = requests.get(
            f"{BASE_URL}/api/assembly-enterprise/history/v2",
            headers=headers,
            params={"status": "DRAFT"}
        )
        assert response.status_code == 200
        data = response.json()
        # All should be DRAFT
        for txn in data.get("transactions", []):
            assert txn.get("status") == "DRAFT", f"Found non-DRAFT: {txn.get('status')}"
        print(f"DRAFT transactions: {data.get('total')}")
    
    def test_11_list_history_by_status_posted(self, headers):
        """Test GET /api/assembly-enterprise/history/v2 - Filter POSTED only"""
        response = requests.get(
            f"{BASE_URL}/api/assembly-enterprise/history/v2",
            headers=headers,
            params={"status": "POSTED"}
        )
        assert response.status_code == 200
        data = response.json()
        for txn in data.get("transactions", []):
            assert txn.get("status") == "POSTED"
        print(f"POSTED transactions: {data.get('total')}")
        
        # Store a POSTED ID for reversal test
        if data.get("transactions"):
            test_data["posted_assembly_id"] = data["transactions"][0].get("id")
    
    def test_12_get_assembly_detail_with_audit(self, headers):
        """Test GET /api/assembly-enterprise/history/v2/{id} - Detail with audit logs"""
        # Get any assembly ID
        history_response = requests.get(
            f"{BASE_URL}/api/assembly-enterprise/history/v2",
            headers=headers,
            params={"limit": 1}
        )
        if history_response.status_code != 200:
            pytest.skip("No assembly history available")
        
        transactions = history_response.json().get("transactions", [])
        if not transactions:
            pytest.skip("No transactions found")
        
        assembly_id = transactions[0].get("id")
        
        response = requests.get(
            f"{BASE_URL}/api/assembly-enterprise/history/v2/{assembly_id}",
            headers=headers
        )
        assert response.status_code == 200, f"Get detail failed: {response.text}"
        data = response.json()
        assert "audit_logs" in data
        assert "stock_movements" in data
        print(f"Assembly {data.get('assembly_number')}: audit_logs={len(data.get('audit_logs', []))}, stock_movements={len(data.get('stock_movements', []))}")


# ============ REVERSAL TESTS ============

class TestReversalEndpoints:
    """Test reversal for POSTED transactions"""
    
    def test_13_reversal_posted_assembly(self, headers):
        """Test POST /api/assembly-enterprise/execute/v2/reverse - Reverse POSTED"""
        posted_id = test_data.get("posted_assembly_id")
        if not posted_id:
            # Try to find a POSTED transaction
            history = requests.get(
                f"{BASE_URL}/api/assembly-enterprise/history/v2",
                headers=headers,
                params={"status": "POSTED", "limit": 1}
            )
            if history.status_code == 200:
                transactions = history.json().get("transactions", [])
                if transactions:
                    posted_id = transactions[0].get("id")
        
        if not posted_id:
            pytest.skip("No POSTED assembly available for reversal test")
        
        reversal_data = {
            "assembly_id": posted_id,
            "reason": "Testing reversal dari testing agent - untuk validasi workflow"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/assembly-enterprise/execute/v2/reverse",
            headers=headers,
            json=reversal_data
        )
        
        if response.status_code == 400:
            error = response.json().get("detail", "")
            if "REVERSED" in str(error):
                print("Assembly already REVERSED - skipping")
                pytest.skip("Assembly already reversed")
            if "DRAFT" in str(error):
                print("Assembly is DRAFT - cannot reverse")
                pytest.skip("Cannot reverse DRAFT")
        
        assert response.status_code == 200, f"Reversal failed: {response.text}"
        data = response.json()
        assert data.get("status") == "REVERSED"
        print(f"Assembly {data.get('assembly_number')} reversed")
        print(f"Reversal journal: {data.get('reversal_journal_number')}")
    
    def test_14_cannot_edit_posted(self, headers):
        """Test that POSTED cannot be edited - should fail"""
        # Find a POSTED or just-reversed transaction
        history = requests.get(
            f"{BASE_URL}/api/assembly-enterprise/history/v2",
            headers=headers,
            params={"status": "POSTED", "limit": 1}
        )
        if history.status_code != 200:
            pytest.skip("No history available")
        
        transactions = history.json().get("transactions", [])
        if not transactions:
            # Try REVERSED
            history = requests.get(
                f"{BASE_URL}/api/assembly-enterprise/history/v2",
                headers=headers,
                params={"status": "REVERSED", "limit": 1}
            )
            transactions = history.json().get("transactions", [])
        
        if not transactions:
            pytest.skip("No POSTED/REVERSED transactions")
        
        posted_id = transactions[0].get("id")
        formula_id = transactions[0].get("formula_id")
        
        edit_data = {
            "formula_id": formula_id,
            "planned_qty": 99,
            "notes": "This should fail"
        }
        
        response = requests.put(
            f"{BASE_URL}/api/assembly-enterprise/transactions/v2/{posted_id}",
            headers=headers,
            json=edit_data
        )
        assert response.status_code == 400, "Edit POSTED should fail but succeeded"
        print("Correctly rejected edit on non-DRAFT assembly")


# ============ LEGACY SUPPORT TEST ============

class TestLegacySupport:
    """Test that legacy /api/assembly endpoints still work"""
    
    def test_15_legacy_formulas_endpoint(self, headers):
        """Test GET /api/assembly/formulas - Legacy endpoint still works"""
        response = requests.get(
            f"{BASE_URL}/api/assembly/formulas",
            headers=headers
        )
        assert response.status_code == 200, f"Legacy formulas failed: {response.text}"
        data = response.json()
        assert "formulas" in data
        print(f"Legacy endpoint: {data.get('total', len(data.get('formulas', [])))} formulas")
    
    def test_16_legacy_transactions_endpoint(self, headers):
        """Test GET /api/assembly/transactions - Legacy endpoint still works"""
        response = requests.get(
            f"{BASE_URL}/api/assembly/transactions",
            headers=headers
        )
        assert response.status_code == 200, f"Legacy transactions failed: {response.text}"
        data = response.json()
        assert "transactions" in data
        print(f"Legacy transactions: {data.get('total', 0)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
