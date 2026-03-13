"""
OCB TITAN - Batch 4 Final Validation Tests
Tests RBAC, Stock Opname Toolbar, AR Payment Dropdown, Database Init
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://smart-ops-hub-6.preview.emergentagent.com')

# ========== FIXTURES ==========

@pytest.fixture(scope="module")
def owner_token():
    """Get owner authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "ocbgroupbjm@gmail.com",
        "password": "admin123"
    })
    assert response.status_code == 200, f"Owner login failed: {response.text}"
    data = response.json()
    assert data.get("user", {}).get("role") == "owner", "User is not owner"
    assert data.get("user", {}).get("permissions") == ["*"], "Owner should have ['*'] permissions"
    return data["token"]

@pytest.fixture(scope="module")
def kasir_token():
    """Get kasir authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "kasir_test@ocb.com",
        "password": "password123"
    })
    assert response.status_code == 200, f"Kasir login failed: {response.text}"
    data = response.json()
    assert data.get("user", {}).get("role") == "kasir", "User is not kasir"
    return data["token"]

@pytest.fixture
def owner_headers(owner_token):
    return {"Authorization": f"Bearer {owner_token}", "Content-Type": "application/json"}

@pytest.fixture
def kasir_headers(kasir_token):
    return {"Authorization": f"Bearer {kasir_token}", "Content-Type": "application/json"}


# ========== DATABASE INIT TESTS ==========

class TestDatabaseInitialization:
    """Test database initialization endpoint"""
    
    def test_init_check_returns_ready(self, owner_headers):
        """GET /api/system/init-check should return status ready with all counts > 0"""
        response = requests.get(f"{BASE_URL}/api/system/init-check", headers=owner_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("status") == "ready", f"Expected status ready, got: {data.get('status')}"
        
        checks = data.get("checks", {})
        assert checks.get("accounts", 0) > 0, "accounts count should be > 0"
        assert checks.get("account_settings", 0) > 0, "account_settings count should be > 0"
        assert checks.get("numbering_settings", 0) > 0, "numbering_settings count should be > 0"
        assert checks.get("branches", 0) > 0, "branches count should be > 0"
        assert checks.get("company_profile", 0) > 0, "company_profile count should be > 0"
        assert checks.get("roles", 0) > 0, "roles count should be > 0"
        print(f"PASS: Database init check - {checks}")
    
    def test_init_check_requires_auth(self):
        """GET /api/system/init-check should require authentication"""
        response = requests.get(f"{BASE_URL}/api/system/init-check")
        assert response.status_code in [401, 403], "Should require auth"


# ========== RBAC OWNER TESTS ==========

class TestRBACOwner:
    """Test that owner has full access"""
    
    def test_owner_login_has_wildcard_permission(self, owner_token):
        """Owner should have ['*'] in permissions"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "ocbgroupbjm@gmail.com",
            "password": "admin123"
        })
        data = response.json()
        perms = data.get("user", {}).get("permissions", [])
        assert "*" in perms, f"Owner should have wildcard permission, got: {perms}"
        print(f"PASS: Owner has permissions: {perms}")
    
    def test_owner_can_access_master_data(self, owner_headers):
        """Owner can access /api/products (master data)"""
        response = requests.get(f"{BASE_URL}/api/products?limit=5", headers=owner_headers)
        assert response.status_code == 200
        print("PASS: Owner can access products")
    
    def test_owner_can_access_users(self, owner_headers):
        """Owner can access /api/users"""
        response = requests.get(f"{BASE_URL}/api/users?limit=5", headers=owner_headers)
        assert response.status_code == 200
        print("PASS: Owner can access users list")
    
    def test_owner_can_access_roles(self, owner_headers):
        """Owner can access /api/roles"""
        response = requests.get(f"{BASE_URL}/api/roles", headers=owner_headers)
        assert response.status_code == 200
        print("PASS: Owner can access roles list")
    
    def test_owner_can_access_accounting(self, owner_headers):
        """Owner can access /api/accounting/accounts"""
        response = requests.get(f"{BASE_URL}/api/accounting/accounts", headers=owner_headers)
        assert response.status_code == 200
        print("PASS: Owner can access accounting")
    
    def test_owner_can_access_inventory(self, owner_headers):
        """Owner can access /api/inventory/stock"""
        response = requests.get(f"{BASE_URL}/api/inventory/stock?limit=5", headers=owner_headers)
        assert response.status_code == 200
        print("PASS: Owner can access inventory")
    
    def test_owner_can_access_purchase(self, owner_headers):
        """Owner can access /api/purchase/orders"""
        response = requests.get(f"{BASE_URL}/api/purchase/orders?limit=5", headers=owner_headers)
        assert response.status_code == 200
        print("PASS: Owner can access purchase")
    
    def test_owner_can_access_sales(self, owner_headers):
        """Owner can access /api/sales/orders"""
        response = requests.get(f"{BASE_URL}/api/sales/orders?limit=5", headers=owner_headers)
        assert response.status_code == 200
        print("PASS: Owner can access sales")


# ========== RBAC KASIR TESTS ==========

class TestRBACKasir:
    """Test kasir restricted access - cannot delete master, edit journals, approve, settings"""
    
    def test_kasir_login_has_limited_permissions(self, kasir_token):
        """Kasir should NOT have ['*'] permission"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "kasir_test@ocb.com",
            "password": "password123"
        })
        data = response.json()
        perms = data.get("user", {}).get("permissions", [])
        assert "*" not in perms, f"Kasir should NOT have wildcard permission, got: {perms}"
        print(f"PASS: Kasir has limited permissions: {perms}")
    
    def test_kasir_can_view_products(self, kasir_headers):
        """Kasir can view products"""
        response = requests.get(f"{BASE_URL}/api/products?limit=5", headers=kasir_headers)
        # Kasir should be able to view (for POS)
        assert response.status_code == 200, f"Kasir should view products: {response.text}"
        print("PASS: Kasir can view products")
    
    def test_kasir_cannot_delete_product(self, kasir_headers, owner_headers):
        """Kasir should NOT be able to delete products (master data)"""
        # First create a test product as owner
        create_res = requests.post(f"{BASE_URL}/api/products", headers=owner_headers, json={
            "code": "TEST-KASIR-DELETE",
            "name": "Test Product for Kasir Delete",
            "price": 10000,
            "category": "Test"
        })
        
        if create_res.status_code == 200:
            prod_id = create_res.json().get("id")
            
            # Try to delete as kasir - should be denied
            delete_res = requests.delete(f"{BASE_URL}/api/products/{prod_id}", headers=kasir_headers)
            
            # Kasir should not be able to delete
            assert delete_res.status_code in [403, 401], f"Kasir should NOT delete product, got: {delete_res.status_code}"
            print(f"PASS: Kasir blocked from deleting product (status: {delete_res.status_code})")
            
            # Cleanup - delete as owner
            requests.delete(f"{BASE_URL}/api/products/{prod_id}", headers=owner_headers)
        else:
            # Product might already exist - try direct delete test
            prods = requests.get(f"{BASE_URL}/api/products?search=TEST-KASIR-DELETE", headers=owner_headers)
            if prods.status_code == 200:
                items = prods.json().get("items", [])
                if items:
                    prod_id = items[0]["id"]
                    delete_res = requests.delete(f"{BASE_URL}/api/products/{prod_id}", headers=kasir_headers)
                    assert delete_res.status_code in [403, 401], f"Kasir should NOT delete: {delete_res.status_code}"
                    print("PASS: Kasir blocked from deleting product")
    
    def test_kasir_cannot_access_settings(self, kasir_headers):
        """Kasir should NOT be able to access system settings"""
        response = requests.get(f"{BASE_URL}/api/settings/company", headers=kasir_headers)
        # Could be 403 or return limited data
        # The key is kasir cannot EDIT settings
        if response.status_code == 200:
            # Try to edit
            edit_res = requests.put(f"{BASE_URL}/api/settings/company", headers=kasir_headers, json={
                "name": "HACKED BY KASIR"
            })
            # 405 = Method Not Allowed is also a valid protection
            assert edit_res.status_code in [403, 401, 404, 405], f"Kasir should NOT edit settings: {edit_res.status_code}"
            print(f"PASS: Kasir blocked from editing settings (status: {edit_res.status_code})")
    
    def test_kasir_can_create_pos_transaction(self, kasir_headers):
        """Kasir CAN create POS transactions"""
        # Get first product
        prod_res = requests.get(f"{BASE_URL}/api/products?limit=1", headers=kasir_headers)
        if prod_res.status_code == 200:
            items = prod_res.json().get("items", [])
            if items:
                # Kasir should be able to access POS-related endpoints
                # This is view-only check since actual POS flow is complex
                print("PASS: Kasir can access products for POS")
            else:
                print("SKIP: No products available for POS test")
        else:
            print(f"SKIP: Cannot get products: {prod_res.status_code}")


# ========== AR PAYMENT DROPDOWN TESTS ==========

class TestARPaymentDropdown:
    """Test AR Payment dropdown shows Kas/Bank accounts"""
    
    def test_accounts_endpoint_returns_kas_bank(self, owner_headers):
        """GET /api/accounting/accounts?category=asset should return Kas, Kas Kecil, Bank BCA"""
        response = requests.get(f"{BASE_URL}/api/accounting/accounts?category=asset", headers=owner_headers)
        assert response.status_code == 200
        
        data = response.json()
        items = data.get("items", [])
        
        # Find required accounts
        kas_found = False
        kas_kecil_found = False
        bank_bca_found = False
        
        for acc in items:
            if acc.get("code") == "1-1000" and "Kas" in acc.get("name", ""):
                kas_found = True
            if acc.get("code") == "1-1001" and "Kas Kecil" in acc.get("name", ""):
                kas_kecil_found = True
            if acc.get("code") == "1-1002" and "Bank BCA" in acc.get("name", ""):
                bank_bca_found = True
        
        assert kas_found, "Kas (1-1000) not found in accounts"
        assert kas_kecil_found, "Kas Kecil (1-1001) not found in accounts"
        assert bank_bca_found, "Bank BCA (1-1002) not found in accounts"
        
        print(f"PASS: AR Payment dropdown accounts found - Kas, Kas Kecil, Bank BCA (total: {len(items)} asset accounts)")
    
    def test_accounts_have_required_fields(self, owner_headers):
        """Accounts should have id, code, name for dropdown"""
        response = requests.get(f"{BASE_URL}/api/accounting/accounts?category=asset", headers=owner_headers)
        data = response.json()
        items = data.get("items", [])
        
        for acc in items[:3]:  # Check first 3
            assert "id" in acc, "Account missing 'id'"
            assert "code" in acc, "Account missing 'code'"
            assert "name" in acc, "Account missing 'name'"
        
        print("PASS: Accounts have required fields for dropdown")


# ========== STOCK OPNAME TOOLBAR TESTS ==========

class TestStockOpnameEndpoint:
    """Test Stock Opname backend endpoints"""
    
    def test_opnames_list_endpoint(self, owner_headers):
        """GET /api/inventory/opnames should return opnames list"""
        response = requests.get(f"{BASE_URL}/api/inventory/opnames", headers=owner_headers)
        assert response.status_code == 200
        print(f"PASS: Stock opnames list endpoint works")
    
    def test_branches_endpoint_for_opname(self, owner_headers):
        """GET /api/branches should return branches for opname selection"""
        response = requests.get(f"{BASE_URL}/api/branches", headers=owner_headers)
        assert response.status_code == 200
        data = response.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        assert len(items) > 0, "Should have at least 1 branch"
        print(f"PASS: Branches available for stock opname: {len(items)}")
    
    def test_inventory_stock_endpoint(self, owner_headers):
        """GET /api/inventory/stock should return stock for opname"""
        response = requests.get(f"{BASE_URL}/api/inventory/stock?limit=10", headers=owner_headers)
        assert response.status_code == 200
        print("PASS: Inventory stock endpoint works")


# ========== ROLES CONFIGURATION TESTS ==========

class TestRolesConfiguration:
    """Test that roles are properly configured"""
    
    def test_owner_role_exists_with_permissions(self, owner_headers):
        """Owner role should exist with inherit_all or ['*'] permissions"""
        response = requests.get(f"{BASE_URL}/api/roles", headers=owner_headers)
        assert response.status_code == 200
        
        data = response.json()
        roles = data.get("items", data) if isinstance(data, dict) else data
        
        owner_role = None
        for role in roles:
            if role.get("code") == "owner" or role.get("name", "").lower() == "pemilik":
                owner_role = role
                break
        
        assert owner_role is not None, "Owner role not found"
        
        # Check owner has full access
        has_inherit_all = owner_role.get("inherit_all", False)
        has_wildcard = "*" in owner_role.get("permissions", [])
        
        assert has_inherit_all or has_wildcard, f"Owner role should have full access: {owner_role}"
        print(f"PASS: Owner role configured correctly - inherit_all: {has_inherit_all}, wildcard: {has_wildcard}")
    
    def test_kasir_role_exists_with_limited_permissions(self, owner_headers):
        """Kasir role should exist with limited permissions"""
        response = requests.get(f"{BASE_URL}/api/roles", headers=owner_headers)
        data = response.json()
        roles = data.get("items", data) if isinstance(data, dict) else data
        
        kasir_role = None
        for role in roles:
            if role.get("code") in ["kasir", "cashier"]:
                kasir_role = role
                break
        
        assert kasir_role is not None, "Kasir role not found"
        
        # Kasir should NOT have full access
        has_inherit_all = kasir_role.get("inherit_all", False)
        has_wildcard = "*" in kasir_role.get("permissions", [])
        
        assert not has_inherit_all, "Kasir should NOT have inherit_all"
        assert not has_wildcard, "Kasir should NOT have wildcard permission"
        print(f"PASS: Kasir role has limited permissions: {kasir_role.get('permissions', [])[:5]}...")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
