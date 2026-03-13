"""
Test Tenant Registry Sinkronisasi - Iteration 62
Testing:
1. API /api/business/list returns exactly 5 active tenants
2. Test tenants (ocb_test_clone, ocb_unit_test) NOT returned
3. Internal tenants (erp_db, ocb_ai_database) NOT returned
4. Each tenant has business_type badge
5. Login works on ocb_baju and ocb_counter
6. Create user works on active tenants
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Expected active tenants (5 total)
EXPECTED_ACTIVE_TENANTS = ["ocb_titan", "ocb_unit_4", "ocb_unt_1", "ocb_baju", "ocb_counter"]

# Test/Internal tenants that should NOT appear
EXCLUDED_TENANTS = ["ocb_test_clone", "ocb_unit_test", "erp_db", "ocb_ai_database", "test_database"]

# Business type mapping for validation
EXPECTED_BUSINESS_TYPES = {
    "ocb_titan": "Retail & Distribusi",
    "ocb_unit_4": "Distribusi",
    "ocb_unt_1": "Retail",
    "ocb_baju": "Fashion",
    "ocb_counter": "Counter"
}


class TestBusinessListAPI:
    """Test /api/business/list endpoint"""
    
    def test_business_list_returns_200(self):
        """API should return 200 OK"""
        response = requests.get(f"{BASE_URL}/api/business/list")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"✓ Business list API returns 200")
    
    def test_business_list_returns_exactly_5_tenants(self):
        """Should return exactly 5 active tenants"""
        response = requests.get(f"{BASE_URL}/api/business/list")
        data = response.json()
        businesses = data.get("businesses", [])
        
        assert len(businesses) == 5, f"Expected 5 businesses, got {len(businesses)}: {[b['db_name'] for b in businesses]}"
        print(f"✓ Business list returns exactly 5 tenants")
    
    def test_all_expected_tenants_present(self):
        """All 5 expected tenants should be present"""
        response = requests.get(f"{BASE_URL}/api/business/list")
        data = response.json()
        businesses = data.get("businesses", [])
        db_names = [b['db_name'] for b in businesses]
        
        for tenant in EXPECTED_ACTIVE_TENANTS:
            assert tenant in db_names, f"Expected tenant '{tenant}' not found. Got: {db_names}"
        print(f"✓ All 5 expected tenants present: {db_names}")
    
    def test_excluded_tenants_not_present(self):
        """Test/internal tenants should NOT be present"""
        response = requests.get(f"{BASE_URL}/api/business/list")
        data = response.json()
        businesses = data.get("businesses", [])
        db_names = [b['db_name'] for b in businesses]
        
        for tenant in EXCLUDED_TENANTS:
            assert tenant not in db_names, f"Excluded tenant '{tenant}' should NOT appear in list. Got: {db_names}"
        print(f"✓ Excluded tenants not in list: {EXCLUDED_TENANTS}")
    
    def test_each_tenant_has_business_type(self):
        """Each tenant should have business_type field"""
        response = requests.get(f"{BASE_URL}/api/business/list")
        data = response.json()
        businesses = data.get("businesses", [])
        
        for biz in businesses:
            assert "business_type" in biz, f"Tenant {biz['db_name']} missing business_type"
            assert biz["business_type"], f"Tenant {biz['db_name']} has empty business_type"
            print(f"  - {biz['db_name']}: {biz['business_type']}")
        print(f"✓ All tenants have business_type badge")
    
    def test_business_type_values_correct(self):
        """Business type values should match expected"""
        response = requests.get(f"{BASE_URL}/api/business/list")
        data = response.json()
        businesses = data.get("businesses", [])
        
        for biz in businesses:
            db_name = biz["db_name"]
            expected_type = EXPECTED_BUSINESS_TYPES.get(db_name)
            if expected_type:
                assert biz["business_type"] == expected_type, f"Tenant {db_name}: expected '{expected_type}', got '{biz['business_type']}'"
        print(f"✓ Business type values correct")


class TestTenantSwitchAndLogin:
    """Test switch and login to different tenants"""
    
    @pytest.fixture
    def session(self):
        return requests.Session()
    
    def test_switch_to_ocb_baju(self, session):
        """Switch to ocb_baju tenant"""
        response = session.post(f"{BASE_URL}/api/business/switch/ocb_baju")
        assert response.status_code == 200, f"Switch to ocb_baju failed: {response.text}"
        data = response.json()
        assert data.get("db_name") == "ocb_baju"
        print(f"✓ Switched to ocb_baju: {data.get('message')}")
    
    def test_switch_to_ocb_counter(self, session):
        """Switch to ocb_counter tenant"""
        response = session.post(f"{BASE_URL}/api/business/switch/ocb_counter")
        assert response.status_code == 200, f"Switch to ocb_counter failed: {response.text}"
        data = response.json()
        assert data.get("db_name") == "ocb_counter"
        print(f"✓ Switched to ocb_counter: {data.get('message')}")
    
    def test_login_to_ocb_baju(self, session):
        """Login to ocb_baju as owner"""
        # First switch to ocb_baju
        switch_res = session.post(f"{BASE_URL}/api/business/switch/ocb_baju")
        assert switch_res.status_code == 200
        
        # Ensure admin user exists
        ensure_res = session.post(f"{BASE_URL}/api/business/ensure-admin/ocb_baju")
        print(f"  Ensure admin: {ensure_res.json()}")
        
        # Login
        login_res = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "ocbgroupbjm@gmail.com",
            "password": "admin123"
        })
        assert login_res.status_code == 200, f"Login to ocb_baju failed: {login_res.text}"
        data = login_res.json()
        assert "token" in data, "No token in response"
        assert data.get("user", {}).get("email") == "ocbgroupbjm@gmail.com"
        print(f"✓ Login to ocb_baju successful")
        return data["token"]
    
    def test_login_to_ocb_counter(self, session):
        """Login to ocb_counter as owner"""
        # First switch to ocb_counter
        switch_res = session.post(f"{BASE_URL}/api/business/switch/ocb_counter")
        assert switch_res.status_code == 200
        
        # Ensure admin user exists
        ensure_res = session.post(f"{BASE_URL}/api/business/ensure-admin/ocb_counter")
        print(f"  Ensure admin: {ensure_res.json()}")
        
        # Login
        login_res = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "ocbgroupbjm@gmail.com",
            "password": "admin123"
        })
        assert login_res.status_code == 200, f"Login to ocb_counter failed: {login_res.text}"
        data = login_res.json()
        assert "token" in data, "No token in response"
        print(f"✓ Login to ocb_counter successful")
        return data["token"]


class TestCreateUserInTenants:
    """Test create user in active tenants"""
    
    @pytest.fixture
    def session(self):
        return requests.Session()
    
    def get_auth_token(self, session, db_name):
        """Helper to get auth token for a tenant"""
        # Switch
        session.post(f"{BASE_URL}/api/business/switch/{db_name}")
        # Ensure admin
        session.post(f"{BASE_URL}/api/business/ensure-admin/{db_name}")
        # Login
        login_res = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "ocbgroupbjm@gmail.com",
            "password": "admin123"
        })
        if login_res.status_code == 200:
            return login_res.json().get("token")
        return None
    
    def test_create_user_in_ocb_baju(self, session):
        """Create user in ocb_baju tenant"""
        token = self.get_auth_token(session, "ocb_baju")
        assert token, "Failed to get token for ocb_baju"
        
        test_email = f"test_iter62_baju_{uuid.uuid4().hex[:8]}@ocb.com"
        create_res = session.post(
            f"{BASE_URL}/api/users",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "email": test_email,
                "password": "password123",
                "name": "Test User Baju",
                "role": "kasir"
            }
        )
        assert create_res.status_code in [200, 201], f"Create user failed: {create_res.text}"
        data = create_res.json()
        # API returns {id, message} on success
        assert "id" in data or "user" in data, f"Unexpected response: {data}"
        assert data.get("message") == "User created" or data.get("user", {}).get("email") == test_email
        print(f"✓ Created user in ocb_baju: {test_email}")
    
    def test_create_user_in_ocb_counter(self, session):
        """Create user in ocb_counter tenant"""
        token = self.get_auth_token(session, "ocb_counter")
        assert token, "Failed to get token for ocb_counter"
        
        test_email = f"test_iter62_counter_{uuid.uuid4().hex[:8]}@ocb.com"
        create_res = session.post(
            f"{BASE_URL}/api/users",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "email": test_email,
                "password": "password123",
                "name": "Test User Counter",
                "role": "kasir"
            }
        )
        assert create_res.status_code in [200, 201], f"Create user failed: {create_res.text}"
        print(f"✓ Created user in ocb_counter: {test_email}")
    
    def test_create_user_in_ocb_titan(self, session):
        """Create user in ocb_titan tenant"""
        token = self.get_auth_token(session, "ocb_titan")
        assert token, "Failed to get token for ocb_titan"
        
        test_email = f"test_iter62_titan_{uuid.uuid4().hex[:8]}@ocb.com"
        create_res = session.post(
            f"{BASE_URL}/api/users",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "email": test_email,
                "password": "password123",
                "name": "Test User Titan",
                "role": "kasir"
            }
        )
        assert create_res.status_code in [200, 201], f"Create user failed: {create_res.text}"
        print(f"✓ Created user in ocb_titan: {test_email}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
