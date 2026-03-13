"""
OCB TITAN - Multi-Tenant ERP Blueprint Testing (Iteration 61)

Tests for:
1. Login as owner to ocb_titan
2. Switch to tenant ocb_unit_4 via API /api/business/switch/{db_name}
3. Create user in active tenant with role_id and role_code
4. API /api/tenant/blueprint-status shows all tenants with blueprint 2.0.0
5. API /api/tenant/list shows all tenant databases
6. New user login to tenant

Credentials:
- Owner: ocbgroupbjm@gmail.com / admin123
- Test user: test_unit4_user@ocb.com / password123 (in ocb_unit_4)
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
OWNER_EMAIL = "ocbgroupbjm@gmail.com"
OWNER_PASSWORD = "admin123"
TEST_USER_EMAIL = "test_unit4_user@ocb.com"
TEST_USER_PASSWORD = "password123"


class TestHealthAndSetup:
    """Basic health check and setup tests"""
    
    def test_health_endpoint(self):
        """API health check"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "active_database" in data
        print(f"Active database: {data['active_database']}")


class TestOwnerLoginToOcbTitan:
    """Test 1: Login as owner to ocb_titan"""
    
    def test_switch_to_ocb_titan(self):
        """Switch to ocb_titan database"""
        response = requests.post(f"{BASE_URL}/api/business/switch/ocb_titan")
        assert response.status_code == 200
        data = response.json()
        assert data["db_name"] == "ocb_titan"
        print(f"Switched to: {data['db_name']}")
    
    def test_owner_login_ocb_titan(self):
        """Login as owner to ocb_titan"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": OWNER_EMAIL, "password": OWNER_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["user"]["email"] == OWNER_EMAIL
        assert data["user"]["role"] == "owner"
        print(f"Logged in as: {data['user']['name']} (role: {data['user']['role']})")


class TestSwitchTenant:
    """Test 2: Switch to tenant ocb_unit_4 via API"""
    
    def test_switch_to_ocb_unit_4(self):
        """Switch to ocb_unit_4 database"""
        response = requests.post(f"{BASE_URL}/api/business/switch/ocb_unit_4")
        assert response.status_code == 200
        data = response.json()
        assert data["db_name"] == "ocb_unit_4"
        assert data["restart_required"] == False
        print(f"Switched to: {data['business']['name']} ({data['db_name']})")
    
    def test_verify_current_business(self):
        """Verify current business is ocb_unit_4"""
        response = requests.get(f"{BASE_URL}/api/business/current")
        assert response.status_code == 200
        data = response.json()
        assert data["current_db"] == "ocb_unit_4"
        print(f"Current DB verified: {data['current_db']}")
    
    def test_health_shows_ocb_unit_4(self):
        """Health endpoint shows ocb_unit_4 as active"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["active_database"] == "ocb_unit_4"
        print(f"Health shows active: {data['active_database']}")


class TestCreateUserWithRoleId:
    """Test 3: Create user in active tenant with role_id and role_code"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - ensure we're on ocb_unit_4 and get token"""
        # Switch to ocb_unit_4
        requests.post(f"{BASE_URL}/api/business/switch/ocb_unit_4")
        
        # Login to get token for ocb_unit_4
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": OWNER_EMAIL, "password": OWNER_PASSWORD}
        )
        assert login_response.status_code == 200
        self.token = login_response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_create_user_with_role_id(self):
        """Create new user and verify role_id and role_code are set"""
        timestamp = int(time.time())
        test_email = f"TEST_iter61_{timestamp}@ocb.com"
        
        # Create user
        create_response = requests.post(
            f"{BASE_URL}/api/users",
            headers=self.headers,
            json={
                "email": test_email,
                "password": "password123",
                "name": f"Test User {timestamp}",
                "phone": "08123456789",
                "role": "cashier"
            }
        )
        assert create_response.status_code == 200
        create_data = create_response.json()
        assert "id" in create_data
        user_id = create_data["id"]
        print(f"Created user: {user_id}")
        
        # Get user details to verify role_id and role_code
        get_response = requests.get(
            f"{BASE_URL}/api/users/{user_id}",
            headers=self.headers
        )
        assert get_response.status_code == 200
        user_data = get_response.json()
        
        # Verify role_id and role_code are present
        assert "role_id" in user_data, "User must have role_id"
        assert user_data["role_id"] is not None, "role_id must not be null"
        assert "role_code" in user_data, "User must have role_code"
        assert user_data["role_code"] == "cashier", f"role_code should be cashier, got {user_data['role_code']}"
        
        print(f"User has role_id: {user_data['role_id']}")
        print(f"User has role_code: {user_data['role_code']}")


class TestBlueprintStatusAPI:
    """Test 4: API /api/tenant/blueprint-status shows all tenants with blueprint 2.0.0"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get token for tenant management"""
        # Switch to ocb_titan for admin operations
        requests.post(f"{BASE_URL}/api/business/switch/ocb_titan")
        
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": OWNER_EMAIL, "password": OWNER_PASSWORD}
        )
        assert login_response.status_code == 200
        self.token = login_response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_blueprint_status_endpoint(self):
        """Test blueprint status shows all tenants"""
        response = requests.get(
            f"{BASE_URL}/api/tenant/blueprint-status",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check current blueprint version
        assert data["current_blueprint_version"] == "2.0.0"
        print(f"Current blueprint version: {data['current_blueprint_version']}")
        
        # Check tenants exist
        assert "tenants" in data
        assert len(data["tenants"]) > 0
        print(f"Total tenants: {len(data['tenants'])}")
    
    def test_all_tenants_have_blueprint_2_0_0(self):
        """All ocb_* tenants should have blueprint 2.0.0"""
        response = requests.get(
            f"{BASE_URL}/api/tenant/blueprint-status",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        ocb_tenants = [t for t in data["tenants"] if t["database"].startswith("ocb_")]
        
        for tenant in ocb_tenants:
            assert tenant["blueprint_version"] == "2.0.0", \
                f"Tenant {tenant['database']} has version {tenant['blueprint_version']}, expected 2.0.0"
            print(f"{tenant['database']}: blueprint={tenant['blueprint_version']}")
    
    def test_all_tenants_have_all_required_collections(self):
        """All tenants should have has_all_required=true"""
        response = requests.get(
            f"{BASE_URL}/api/tenant/blueprint-status",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        ocb_tenants = [t for t in data["tenants"] if t["database"].startswith("ocb_")]
        
        for tenant in ocb_tenants:
            assert tenant["has_all_required"] == True, \
                f"Tenant {tenant['database']} missing collections: {tenant.get('missing_collections', [])}"
            print(f"{tenant['database']}: has_all_required={tenant['has_all_required']}")
    
    def test_all_tenants_no_sync_needed(self):
        """All tenants should have needs_sync=false"""
        response = requests.get(
            f"{BASE_URL}/api/tenant/blueprint-status",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        ocb_tenants = [t for t in data["tenants"] if t["database"].startswith("ocb_")]
        
        for tenant in ocb_tenants:
            assert tenant["needs_sync"] == False, \
                f"Tenant {tenant['database']} needs sync"
            print(f"{tenant['database']}: needs_sync={tenant['needs_sync']}")


class TestTenantListAPI:
    """Test 5: API /api/tenant/list shows all tenant databases"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get token"""
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": OWNER_EMAIL, "password": OWNER_PASSWORD}
        )
        assert login_response.status_code == 200
        self.token = login_response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_tenant_list_endpoint(self):
        """Test tenant list API returns all tenants"""
        response = requests.get(
            f"{BASE_URL}/api/tenant/list",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "tenants" in data
        assert "current_blueprint_version" in data
        assert "current_migration_version" in data
        
        print(f"Blueprint: {data['current_blueprint_version']}")
        print(f"Migration: {data['current_migration_version']}")
        print(f"Total tenants: {len(data['tenants'])}")
    
    def test_tenant_list_has_required_fields(self):
        """Each tenant should have required fields"""
        response = requests.get(
            f"{BASE_URL}/api/tenant/list",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        required_fields = ["database", "accounts", "roles", "users", "branches", 
                          "blueprint_version", "health"]
        
        for tenant in data["tenants"]:
            for field in required_fields:
                assert field in tenant, f"Tenant {tenant.get('database')} missing field: {field}"
            print(f"{tenant['database']}: health={tenant['health']}")
    
    def test_ocb_unit_4_in_tenant_list(self):
        """ocb_unit_4 should be in tenant list"""
        response = requests.get(
            f"{BASE_URL}/api/tenant/list",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        ocb_unit_4 = next((t for t in data["tenants"] if t["database"] == "ocb_unit_4"), None)
        assert ocb_unit_4 is not None, "ocb_unit_4 not found in tenant list"
        assert ocb_unit_4["health"] == "healthy"
        print(f"ocb_unit_4 found: health={ocb_unit_4['health']}, users={ocb_unit_4['users']}")


class TestNewUserLogin:
    """Test 6: New user can login to the tenant"""
    
    def test_switch_to_ocb_unit_4_for_login(self):
        """Switch to ocb_unit_4 before login test"""
        response = requests.post(f"{BASE_URL}/api/business/switch/ocb_unit_4")
        assert response.status_code == 200
        assert response.json()["db_name"] == "ocb_unit_4"
    
    def test_existing_test_user_login(self):
        """Test existing test user can login"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["user"]["email"] == TEST_USER_EMAIL
        print(f"Test user logged in: {data['user']['name']} (role: {data['user']['role']})")
    
    def test_create_and_login_new_user(self):
        """Create new user and verify login works"""
        # First login as owner to create user
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": OWNER_EMAIL, "password": OWNER_PASSWORD}
        )
        assert login_response.status_code == 200
        token = login_response.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create new user
        timestamp = int(time.time())
        new_email = f"TEST_login_iter61_{timestamp}@ocb.com"
        new_password = "testpass123"
        
        create_response = requests.post(
            f"{BASE_URL}/api/users",
            headers=headers,
            json={
                "email": new_email,
                "password": new_password,
                "name": "Login Test User",
                "role": "cashier"
            }
        )
        assert create_response.status_code == 200
        print(f"Created user: {new_email}")
        
        # Login with new user
        new_login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": new_email, "password": new_password}
        )
        assert new_login_response.status_code == 200
        new_user_data = new_login_response.json()
        assert new_user_data["user"]["email"] == new_email
        print(f"New user logged in successfully: {new_user_data['user']['email']}")


class TestCleanup:
    """Cleanup after tests - switch back to default database"""
    
    def test_switch_back_to_ocb_titan(self):
        """Switch back to ocb_titan as default"""
        response = requests.post(f"{BASE_URL}/api/business/switch/ocb_titan")
        assert response.status_code == 200
        assert response.json()["db_name"] == "ocb_titan"
        print("Switched back to ocb_titan")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
