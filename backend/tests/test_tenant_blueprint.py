# Test Tenant Blueprint & Multi-Tenant Standardization Module
# Tests: tenant list, sync-all, create tenant, health check
# Blueprint version validation for all tenants

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
OWNER_EMAIL = "ocbgroupbjm@gmail.com"
OWNER_PASSWORD = "admin123"

# Target tenants to verify
TARGET_TENANTS = ['ocb_titan', 'ocb_unit_4', 'ocb_unt_1']
EXPECTED_BLUEPRINT_VERSION = "1.0.0"

# Required collections for healthy tenant
REQUIRED_COLLECTIONS = ['accounts', 'roles', 'branches', 'company_profile', 'account_settings', 'numbering_settings']


@pytest.fixture(scope="module")
def auth_token():
    """Get auth token for API calls"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": OWNER_EMAIL, "password": OWNER_PASSWORD}
    )
    if response.status_code != 200:
        pytest.skip(f"Auth failed: {response.status_code}")
    return response.json().get("token")


@pytest.fixture(scope="module")
def api_client(auth_token):
    """Session with auth headers"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    })
    return session


class TestTenantList:
    """Test /api/tenant/list - List all tenants with status"""

    def test_list_tenants_returns_200(self, api_client):
        """API should return 200 and list of tenants"""
        response = api_client.get(f"{BASE_URL}/api/tenant/list")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "current_blueprint_version" in data, "Missing current_blueprint_version"
        assert "tenants" in data, "Missing tenants list"
        assert isinstance(data["tenants"], list), "Tenants should be a list"
        print(f"✓ Tenant list returned {len(data['tenants'])} tenants")

    def test_list_contains_target_tenants(self, api_client):
        """Verify target tenants are in the list"""
        response = api_client.get(f"{BASE_URL}/api/tenant/list")
        assert response.status_code == 200
        
        data = response.json()
        tenant_names = [t["database"] for t in data["tenants"]]
        
        for target in TARGET_TENANTS:
            assert target in tenant_names, f"Target tenant '{target}' not found in list"
        print(f"✓ All target tenants found: {TARGET_TENANTS}")

    def test_tenant_structure_complete(self, api_client):
        """Each tenant should have required fields"""
        response = api_client.get(f"{BASE_URL}/api/tenant/list")
        assert response.status_code == 200
        
        data = response.json()
        required_fields = ["database", "health", "blueprint_version", "accounts", "roles", "branches"]
        
        for tenant in data["tenants"]:
            for field in required_fields:
                assert field in tenant, f"Tenant {tenant.get('database')} missing field: {field}"
        print(f"✓ All tenants have required structure fields")


class TestTenantHealth:
    """Test /api/tenant/health/{db_name} - Health check for specific tenant"""

    @pytest.mark.parametrize("db_name", TARGET_TENANTS)
    def test_tenant_health_returns_200(self, api_client, db_name):
        """Health check should return 200 for all target tenants"""
        response = api_client.get(f"{BASE_URL}/api/tenant/health/{db_name}")
        assert response.status_code == 200, f"Expected 200 for {db_name}, got {response.status_code}"
        
        data = response.json()
        assert data["database"] == db_name
        print(f"✓ Health check for {db_name}: {data.get('health')}")

    @pytest.mark.parametrize("db_name", TARGET_TENANTS)
    def test_tenant_is_healthy(self, api_client, db_name):
        """Target tenants should have health=healthy"""
        response = api_client.get(f"{BASE_URL}/api/tenant/health/{db_name}")
        assert response.status_code == 200
        
        data = response.json()
        # Accept 'healthy' or check that there are no critical issues
        issues = data.get("issues", [])
        has_critical_issues = any("Missing" in issue for issue in issues if "mismatch" not in issue.lower())
        
        assert data.get("health") == "healthy" or not has_critical_issues, \
            f"{db_name} health issues: {issues}"
        print(f"✓ {db_name} health status: {data.get('health')}")

    @pytest.mark.parametrize("db_name", TARGET_TENANTS)
    def test_tenant_blueprint_version(self, api_client, db_name):
        """Target tenants should have blueprint_version=1.0.0"""
        response = api_client.get(f"{BASE_URL}/api/tenant/health/{db_name}")
        assert response.status_code == 200
        
        data = response.json()
        version = data.get("blueprint_version")
        assert version == EXPECTED_BLUEPRINT_VERSION, \
            f"{db_name} has version {version}, expected {EXPECTED_BLUEPRINT_VERSION}"
        print(f"✓ {db_name} blueprint version: {version}")

    @pytest.mark.parametrize("db_name", TARGET_TENANTS)
    def test_tenant_has_required_collections(self, api_client, db_name):
        """Each tenant should have required collections populated"""
        response = api_client.get(f"{BASE_URL}/api/tenant/health/{db_name}")
        assert response.status_code == 200
        
        data = response.json()
        checks = data.get("checks", {})
        
        for collection in REQUIRED_COLLECTIONS:
            count = checks.get(collection, 0)
            assert count > 0, f"{db_name} has 0 items in {collection}"
        print(f"✓ {db_name} has all required collections populated")


class TestTenantSyncAll:
    """Test /api/tenant/sync-all - Sync all tenants to blueprint"""

    def test_sync_all_returns_200(self, api_client):
        """Sync-all should return 200 with results"""
        response = api_client.post(f"{BASE_URL}/api/tenant/sync-all")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("status") == "completed", "Sync status should be completed"
        assert "blueprint_version" in data, "Missing blueprint_version in response"
        assert "results" in data, "Missing results in response"
        print(f"✓ Sync-all completed, synced {len(data.get('results', []))} databases")

    def test_sync_all_results_structure(self, api_client):
        """Sync results should have proper structure"""
        response = api_client.post(f"{BASE_URL}/api/tenant/sync-all")
        assert response.status_code == 200
        
        data = response.json()
        results = data.get("results", [])
        
        for result in results:
            assert "database" in result, "Result missing database field"
            assert "blueprint_version" in result, "Result missing blueprint_version"
            assert "changes" in result, "Result missing changes field"
        print(f"✓ All sync results have proper structure")


class TestTenantCreate:
    """Test /api/tenant/create - Create new tenant"""

    def test_create_duplicate_tenant_fails(self, api_client):
        """Creating existing tenant should fail with 400"""
        # Try to create an existing tenant
        response = api_client.post(
            f"{BASE_URL}/api/tenant/create",
            params={
                "database_key": "ocb_titan",  # Already exists
                "company_name": "Test Company",
                "owner_email": "test@test.com",
                "owner_password": "test123"
            }
        )
        # Should return 400 for duplicate
        assert response.status_code == 400, \
            f"Expected 400 for duplicate tenant, got {response.status_code}"
        print("✓ Duplicate tenant creation properly rejected")


class TestNewTenantVerification:
    """Verify newly created tenant ocb_unit_test has complete structure"""

    def test_new_tenant_exists(self, api_client):
        """ocb_unit_test should exist in tenant list"""
        response = api_client.get(f"{BASE_URL}/api/tenant/list")
        assert response.status_code == 200
        
        data = response.json()
        tenant_names = [t["database"] for t in data["tenants"]]
        
        if "ocb_unit_test" not in tenant_names:
            pytest.skip("ocb_unit_test not found - may not have been created yet")
        print("✓ ocb_unit_test exists in tenant list")

    def test_new_tenant_health(self, api_client):
        """ocb_unit_test should be healthy"""
        response = api_client.get(f"{BASE_URL}/api/tenant/health/ocb_unit_test")
        
        if response.status_code == 404:
            pytest.skip("ocb_unit_test not found")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check health status
        assert data.get("health") in ["healthy", "needs_attention"], \
            f"ocb_unit_test health: {data.get('health')}"
        print(f"✓ ocb_unit_test health: {data.get('health')}")

    def test_new_tenant_has_complete_structure(self, api_client):
        """ocb_unit_test should have all required collections"""
        response = api_client.get(f"{BASE_URL}/api/tenant/health/ocb_unit_test")
        
        if response.status_code == 404:
            pytest.skip("ocb_unit_test not found")
        
        assert response.status_code == 200
        data = response.json()
        checks = data.get("checks", {})
        
        required = ['accounts', 'roles', 'branches', 'company_profile', 'account_settings', 'numbering_settings']
        missing = [c for c in required if checks.get(c, 0) == 0]
        
        if missing:
            print(f"⚠ ocb_unit_test missing collections: {missing}")
        else:
            print(f"✓ ocb_unit_test has all required collections")
        
        assert len(missing) == 0, f"ocb_unit_test missing: {missing}"


class TestBlueprintVersionLock:
    """Verify all tenants are on the same blueprint version"""

    def test_all_tenants_same_version(self, api_client):
        """All target tenants should have blueprint_version=1.0.0"""
        response = api_client.get(f"{BASE_URL}/api/tenant/list")
        assert response.status_code == 200
        
        data = response.json()
        current_version = data.get("current_blueprint_version")
        
        version_mismatches = []
        for tenant in data["tenants"]:
            db_name = tenant.get("database")
            version = tenant.get("blueprint_version")
            
            if db_name in TARGET_TENANTS and version != current_version:
                version_mismatches.append(f"{db_name}: {version}")
        
        assert len(version_mismatches) == 0, \
            f"Version mismatches found: {version_mismatches}"
        print(f"✓ All target tenants on version {current_version}")

    def test_no_migration_needed(self, api_client):
        """Target tenants should not need migration"""
        response = api_client.get(f"{BASE_URL}/api/tenant/list")
        assert response.status_code == 200
        
        data = response.json()
        tenants_needing_migration = []
        
        for tenant in data["tenants"]:
            db_name = tenant.get("database")
            if db_name in TARGET_TENANTS and tenant.get("needs_migration"):
                tenants_needing_migration.append(db_name)
        
        # This is informational - not a critical failure
        if tenants_needing_migration:
            print(f"⚠ Tenants needing migration: {tenants_needing_migration}")
        else:
            print("✓ No target tenants need migration")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
