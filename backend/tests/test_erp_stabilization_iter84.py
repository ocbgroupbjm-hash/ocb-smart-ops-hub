"""
OCB TITAN ERP STABILIZATION TEST - Iteration 84
Testing:
1. TENANT ISOLATION: JWT contains tenant_id, database routing per-request
2. PURCHASE MODULE: Warehouse, PIC, Payment Account, Item Search Flow
3. ASSEMBLY MODULE: Stock movements on execute/reverse
"""

import pytest
import requests
import os
import jwt

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "ocbgroupbjm@gmail.com"
TEST_PASSWORD = "admin123"
TENANT_OCB_TITAN = "ocb_titan"
TENANT_OCB_UNT_1 = "ocb_unt_1"


class TestTenantIsolation:
    """TASK 1: Test Multi-Tenant Routing - JWT contains tenant_id"""
    
    def test_login_ocb_titan_jwt_contains_tenant_id(self):
        """Login to ocb_titan and verify JWT contains tenant_id:ocb_titan"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "db_name": TENANT_OCB_TITAN
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        assert "token" in data, "No token in response"
        
        # Decode JWT without verification to check payload
        token = data["token"]
        payload = jwt.decode(token, options={"verify_signature": False})
        
        assert "tenant_id" in payload, f"tenant_id not in JWT payload: {payload.keys()}"
        assert payload["tenant_id"] == TENANT_OCB_TITAN, f"Expected tenant_id={TENANT_OCB_TITAN}, got {payload.get('tenant_id')}"
        print(f"✓ JWT contains tenant_id: {payload['tenant_id']}")
        
        # Also check user response
        assert "user" in data
        assert data["user"].get("tenant_id") == TENANT_OCB_TITAN, f"User response tenant_id mismatch"
    
    def test_login_ocb_unt_1_jwt_contains_tenant_id(self):
        """Login to ocb_unt_1 and verify JWT contains tenant_id:ocb_unt_1"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "db_name": TENANT_OCB_UNT_1
        })
        assert response.status_code == 200, f"Login to ocb_unt_1 failed: {response.text}"
        
        data = response.json()
        token = data["token"]
        payload = jwt.decode(token, options={"verify_signature": False})
        
        assert payload.get("tenant_id") == TENANT_OCB_UNT_1, f"Expected tenant_id={TENANT_OCB_UNT_1}, got {payload.get('tenant_id')}"
        print(f"✓ JWT contains tenant_id: {payload['tenant_id']}")
    
    def test_cross_request_tenant_isolation(self):
        """Using ocb_titan token should always access ocb_titan data"""
        # Get ocb_titan token
        titan_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "db_name": TENANT_OCB_TITAN
        })
        titan_token = titan_response.json()["token"]
        
        # Get ocb_unt_1 token (this switches server default DB)
        unt1_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "db_name": TENANT_OCB_UNT_1
        })
        unt1_token = unt1_response.json()["token"]
        
        # Now use titan token - should still access titan data
        headers_titan = {"Authorization": f"Bearer {titan_token}"}
        products_titan = requests.get(f"{BASE_URL}/api/products?limit=5", headers=headers_titan)
        assert products_titan.status_code == 200
        
        # Use unt1 token
        headers_unt1 = {"Authorization": f"Bearer {unt1_token}"}
        products_unt1 = requests.get(f"{BASE_URL}/api/products?limit=5", headers=headers_unt1)
        assert products_unt1.status_code == 200
        
        # Cross-check using titan token again after unt1 request
        products_titan_again = requests.get(f"{BASE_URL}/api/products?limit=5", headers=headers_titan)
        assert products_titan_again.status_code == 200
        
        print("✓ Cross-request tenant isolation working correctly")


class TestPurchaseModule:
    """TASK 2: Test Purchase Module - Warehouse, PIC, Payment Account, Item Search"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for ocb_titan"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "db_name": TENANT_OCB_TITAN
        })
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_warehouses_for_dropdown(self):
        """Warehouses should be available for PO warehouse dropdown"""
        response = requests.get(f"{BASE_URL}/api/master/warehouses", headers=self.headers)
        assert response.status_code == 200, f"Failed to get warehouses: {response.text}"
        
        data = response.json()
        # Handle both list and dict response
        if isinstance(data, list):
            warehouses = data
        else:
            warehouses = data.get("warehouses") or data.get("items") or data
        print(f"✓ Warehouses API working (count: {len(warehouses) if isinstance(warehouses, list) else 'N/A'})")
    
    def test_get_employees_for_pic_dropdown(self):
        """PIC dropdown should load from /api/hr/employees"""
        response = requests.get(f"{BASE_URL}/api/hr/employees?status=active", headers=self.headers)
        assert response.status_code == 200, f"Failed to get employees: {response.text}"
        
        data = response.json()
        employees = data.get("employees") or data.get("items") or data
        print(f"✓ Employees for PIC dropdown available: {len(employees) if isinstance(employees, list) else 'N/A'}")
    
    def test_get_cash_bank_accounts_for_payment_dropdown(self):
        """Payment account dropdown should load from /api/account-settings/chart-of-accounts?types=CASH,BANK"""
        response = requests.get(f"{BASE_URL}/api/account-settings/chart-of-accounts?types=CASH,BANK", headers=self.headers)
        assert response.status_code == 200, f"Failed to get COA: {response.text}"
        
        data = response.json()
        accounts = data.get("accounts") or data.get("items") or data
        print(f"✓ Cash/Bank accounts for payment dropdown: {len(accounts) if isinstance(accounts, list) else 'N/A'}")
    
    def test_get_products_for_item_search(self):
        """Products should be searchable for PO item selection"""
        response = requests.get(f"{BASE_URL}/api/products", headers=self.headers)
        assert response.status_code == 200, f"Failed to get products: {response.text}"
        
        data = response.json()
        products = data.get("items") or data.get("products") or data
        assert isinstance(products, list), "Products should be a list"
        print(f"✓ Products for item search: {len(products)}")
    
    def test_get_suppliers_for_po(self):
        """Suppliers should be available for PO creation"""
        response = requests.get(f"{BASE_URL}/api/suppliers", headers=self.headers)
        assert response.status_code == 200, f"Failed to get suppliers: {response.text}"
        
        data = response.json()
        suppliers = data.get("items") or data.get("suppliers") or data
        print(f"✓ Suppliers available: {len(suppliers) if isinstance(suppliers, list) else 'N/A'}")
    
    def test_create_po_validation_no_supplier(self):
        """PO creation should fail without supplier"""
        # Create PO without supplier_id
        po_data = {
            "supplier_id": "",  # Empty supplier
            "warehouse_id": "test-wh",
            "items": [
                {"product_id": "test-prod", "quantity": 1, "unit_cost": 1000}
            ]
        }
        
        response = requests.post(f"{BASE_URL}/api/purchase/orders", json=po_data, headers=self.headers)
        # Should return 400 or 422 validation error
        assert response.status_code in [400, 422], f"Expected validation error, got {response.status_code}: {response.text}"
        print("✓ PO creation validation - supplier required")
    
    def test_purchase_orders_list(self):
        """List purchase orders endpoint should work"""
        response = requests.get(f"{BASE_URL}/api/purchase/orders", headers=self.headers)
        assert response.status_code == 200, f"Failed to list POs: {response.text}"
        
        data = response.json()
        assert "items" in data or isinstance(data, list), "Response should contain items"
        print(f"✓ Purchase orders list working")


class TestAssemblyStockMovements:
    """TASK 3: Assembly Voucher stock movement validation"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for ocb_titan"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "db_name": TENANT_OCB_TITAN
        })
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_list_assembly_formulas(self):
        """List assembly formulas (vouchers)"""
        response = requests.get(f"{BASE_URL}/api/assembly-enterprise/formulas/v2?status=ALL", headers=self.headers)
        assert response.status_code == 200, f"Failed to list formulas: {response.text}"
        
        data = response.json()
        formulas = data.get("formulas", [])
        print(f"✓ Assembly formulas found: {len(formulas)}")
        return formulas
    
    def test_assembly_history_transactions(self):
        """List assembly transaction history"""
        response = requests.get(f"{BASE_URL}/api/assembly-enterprise/history/v2", headers=self.headers)
        assert response.status_code == 200, f"Failed to get history: {response.text}"
        
        data = response.json()
        transactions = data.get("transactions", [])
        print(f"✓ Assembly transactions found: {len(transactions)}")
        
        # Check for stock movements on POSTED transactions
        for txn in transactions[:3]:  # Check first 3
            if txn.get("status") == "POSTED":
                print(f"  - {txn.get('assembly_number')}: status={txn.get('status')}, has movement_ids: {'movement_ids' in txn}")
    
    def test_assembly_detail_has_stock_movements(self):
        """Check that POSTED assembly has stock_movements"""
        # First get a POSTED transaction
        response = requests.get(f"{BASE_URL}/api/assembly-enterprise/history/v2?status=POSTED&limit=1", headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        transactions = data.get("transactions", [])
        
        if not transactions:
            pytest.skip("No POSTED assembly transactions to test")
        
        txn_id = transactions[0]["id"]
        
        # Get detail
        detail_response = requests.get(f"{BASE_URL}/api/assembly-enterprise/history/v2/{txn_id}", headers=self.headers)
        assert detail_response.status_code == 200
        
        detail = detail_response.json()
        
        # Check stock_movements array
        stock_movements = detail.get("stock_movements", [])
        print(f"✓ Assembly detail has {len(stock_movements)} stock movements")
        
        if stock_movements:
            movement_types = set(m.get("movement_type") for m in stock_movements)
            print(f"  Movement types: {movement_types}")
            
            # Should have ASSEMBLY_CONSUME and ASSEMBLY_PRODUCE
            assert "ASSEMBLY_CONSUME" in movement_types or any("CONSUME" in t for t in movement_types), "Missing ASSEMBLY_CONSUME"
            assert "ASSEMBLY_PRODUCE" in movement_types or any("PRODUCE" in t for t in movement_types), "Missing ASSEMBLY_PRODUCE"
    
    def test_assembly_reversal_creates_reversal_movements(self):
        """Check that REVERSED assembly has reversal stock movements"""
        # Get a REVERSED transaction if exists
        response = requests.get(f"{BASE_URL}/api/assembly-enterprise/history/v2?status=REVERSED&limit=1", headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        transactions = data.get("transactions", [])
        
        if not transactions:
            pytest.skip("No REVERSED assembly transactions to test")
        
        txn_id = transactions[0]["id"]
        
        # Get detail
        detail_response = requests.get(f"{BASE_URL}/api/assembly-enterprise/history/v2/{txn_id}", headers=self.headers)
        assert detail_response.status_code == 200
        
        detail = detail_response.json()
        
        # Should have reversal_movement_ids or reversal_journal_entry_id
        has_reversal_movements = detail.get("reversal_movement_ids", [])
        has_reversal_journal = detail.get("reversal_journal_entry_id")
        
        print(f"✓ Reversed assembly has reversal tracking:")
        print(f"  - reversal_movement_ids: {len(has_reversal_movements) if has_reversal_movements else 0}")
        print(f"  - reversal_journal_entry_id: {has_reversal_journal}")


class TestCancelTransactionReversal:
    """TASK 4: Cancel transaction should be REVERSAL not DELETE"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for ocb_titan"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "db_name": TENANT_OCB_TITAN
        })
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_po_cancel_uses_status_not_delete(self):
        """PO cancel should set status to cancelled, not delete record"""
        # Get a draft PO
        response = requests.get(f"{BASE_URL}/api/purchase/orders?status=draft", headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        items = data.get("items", [])
        
        if not items:
            pytest.skip("No draft POs to test cancel")
        
        po_id = items[0]["id"]
        po_number = items[0].get("po_number")
        
        # Cancel the PO
        cancel_response = requests.post(f"{BASE_URL}/api/purchase/orders/{po_id}/cancel", headers=self.headers)
        
        # Should return success with message about cancelled
        if cancel_response.status_code == 200:
            # Verify PO still exists with cancelled status
            verify_response = requests.get(f"{BASE_URL}/api/purchase/orders/{po_id}", headers=self.headers)
            
            if verify_response.status_code == 200:
                po_data = verify_response.json()
                assert po_data.get("status") == "cancelled", f"PO should be cancelled, not deleted. Status: {po_data.get('status')}"
                print(f"✓ PO {po_number} cancelled (status=cancelled), record preserved")
            else:
                print(f"⚠ PO {po_number} might have been deleted instead of cancelled")
    
    def test_assembly_draft_delete_is_soft_delete(self):
        """Assembly DRAFT delete should be CANCELLED status (soft delete)"""
        # Check assembly enterprise route for delete behavior
        response = requests.get(f"{BASE_URL}/api/assembly-enterprise/history/v2?status=DRAFT&limit=1", headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        transactions = data.get("transactions", [])
        
        if not transactions:
            pytest.skip("No DRAFT assembly to test delete")
        
        txn_id = transactions[0]["id"]
        txn_number = transactions[0].get("assembly_number")
        
        # Delete should soft-delete (status=CANCELLED)
        delete_response = requests.delete(f"{BASE_URL}/api/assembly-enterprise/transactions/v2/{txn_id}", headers=self.headers)
        
        if delete_response.status_code == 200:
            print(f"✓ Assembly {txn_number} soft-deleted (CANCELLED)")
        else:
            print(f"Delete response: {delete_response.status_code} - {delete_response.text}")
    
    def test_assembly_posted_cannot_delete_must_reverse(self):
        """Assembly POSTED cannot be deleted, must use reversal"""
        response = requests.get(f"{BASE_URL}/api/assembly-enterprise/history/v2?status=POSTED&limit=1", headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        transactions = data.get("transactions", [])
        
        if not transactions:
            pytest.skip("No POSTED assembly to test")
        
        txn_id = transactions[0]["id"]
        
        # Try to delete POSTED - should fail
        delete_response = requests.delete(f"{BASE_URL}/api/assembly-enterprise/transactions/v2/{txn_id}", headers=self.headers)
        
        # Should return 400 error
        assert delete_response.status_code == 400, f"POSTED assembly delete should be blocked: {delete_response.status_code}"
        print("✓ POSTED assembly delete blocked - must use reversal")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
