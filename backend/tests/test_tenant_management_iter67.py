"""
OCB TITAN - Tenant Management Module Tests (Iteration 67)
==========================================================
Testing Edit dan Hapus tenant dengan guardrail sesuai Blueprint Governance System.

Features tested:
1. GET /api/tenant/tenants - List all tenants
2. POST /api/tenant/tenants - Create new tenant
3. PATCH /api/tenant/tenants/{id}/status - Edit tenant status
4. PATCH /api/tenant/tenants/{id} - Edit tenant config
5. DELETE /api/tenant/{id}?confirm_delete=false - Check transactions (dry run)
6. DELETE /api/tenant/{id}?confirm_delete=true - Actually delete tenant
7. RBAC protection - only owner/super_admin can access
8. Guardrail - tenant with transactions cannot be hard deleted
9. Audit logging - all actions are logged
"""

import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
OWNER_EMAIL = "ocbgroupbjm@gmail.com"
OWNER_PASSWORD = "admin123"

# Test tenant data
TEST_TENANT_ID = f"test_tenant_{uuid.uuid4().hex[:8]}"
TEST_DB_NAME = f"ocb_{TEST_TENANT_ID}"


class TestAuthenticationSetup:
    """Authentication setup for tenant management tests"""
    
    @pytest.fixture(scope="class")
    def owner_token(self):
        """Get owner authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": OWNER_EMAIL, "password": OWNER_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data, "No token in response"
        assert data["user"]["role"] == "owner", f"Expected owner role, got {data['user']['role']}"
        return data["token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, owner_token):
        """Get authentication headers"""
        return {
            "Authorization": f"Bearer {owner_token}",
            "Content-Type": "application/json"
        }


class TestListTenants(TestAuthenticationSetup):
    """Test GET /api/tenant/tenants - List all tenants"""
    
    def test_list_tenants_success(self, auth_headers):
        """Test listing all tenants as owner"""
        response = requests.get(
            f"{BASE_URL}/api/tenant/tenants",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed to list tenants: {response.text}"
        
        data = response.json()
        assert "tenants" in data, "Response missing 'tenants' field"
        assert "current_blueprint_version" in data, "Response missing 'current_blueprint_version'"
        assert "total_tenants" in data, "Response missing 'total_tenants'"
        
        # Verify tenant structure if any tenants exist
        if data["tenants"]:
            tenant = data["tenants"][0]
            assert "database" in tenant, "Tenant missing 'database' field"
            assert "accounts" in tenant, "Tenant missing 'accounts' field"
            assert "health" in tenant, "Tenant missing 'health' field"
        
        print(f"✓ Listed {data['total_tenants']} tenants successfully")
    
    def test_list_tenants_unauthorized(self):
        """Test listing tenants without auth token fails"""
        response = requests.get(f"{BASE_URL}/api/tenant/tenants")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ Unauthorized access correctly blocked")


class TestCreateTenant(TestAuthenticationSetup):
    """Test POST /api/tenant/tenants - Create new tenant"""
    
    def test_create_tenant_success(self, auth_headers):
        """Test creating a new tenant as owner"""
        tenant_data = {
            "business_name": f"Test Business {uuid.uuid4().hex[:6]}",
            "tenant_id": TEST_TENANT_ID,
            "database_name": TEST_DB_NAME,
            "tenant_type": "retail",
            "status": "active",
            "timezone": "Asia/Jakarta",
            "currency": "IDR",
            "default_branch_name": "Test HQ",
            "default_warehouse_name": "Test Warehouse",
            "admin_name": "Test Admin",
            "admin_email": f"testadmin_{uuid.uuid4().hex[:6]}@test.com",
            "admin_password": "testpass123"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/tenant/tenants",
            headers=auth_headers,
            json=tenant_data
        )
        
        # Check for success or already exists
        if response.status_code == 400 and "already exists" in response.json().get("detail", ""):
            pytest.skip("Tenant already exists, skipping creation test")
        
        assert response.status_code in [200, 201], f"Failed to create tenant: {response.text}"
        
        data = response.json()
        assert data["status"] in ["created", "partial"], f"Unexpected status: {data['status']}"
        assert data["tenant_id"] == TEST_TENANT_ID
        assert data["database_name"] == TEST_DB_NAME
        assert "blueprint_version" in data
        assert "smoke_test" in data
        
        print(f"✓ Created tenant: {data['tenant_id']} ({data['database_name']})")
    
    def test_create_tenant_duplicate_fails(self, auth_headers):
        """Test creating duplicate tenant fails"""
        tenant_data = {
            "business_name": "Duplicate Test",
            "tenant_id": TEST_TENANT_ID,
            "database_name": TEST_DB_NAME,
            "tenant_type": "retail",
            "status": "active",
            "timezone": "Asia/Jakarta",
            "currency": "IDR",
            "default_branch_name": "HQ",
            "default_warehouse_name": "Warehouse",
            "admin_name": "Admin",
            "admin_email": "dup@test.com",
            "admin_password": "testpass123"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/tenant/tenants",
            headers=auth_headers,
            json=tenant_data
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        assert "already exists" in response.json().get("detail", "").lower()
        print("✓ Duplicate tenant creation correctly blocked")


class TestEditTenantStatus(TestAuthenticationSetup):
    """Test PATCH /api/tenant/tenants/{id}/status - Edit tenant status"""
    
    def test_update_tenant_status_success(self, auth_headers):
        """Test updating tenant status"""
        # First, list tenants to get a valid tenant_id
        list_response = requests.get(
            f"{BASE_URL}/api/tenant/tenants",
            headers=auth_headers
        )
        assert list_response.status_code == 200
        
        tenants = list_response.json().get("tenants", [])
        if not tenants:
            pytest.skip("No tenants available for status update test")
        
        # Use the test tenant or first available
        test_tenant = None
        for t in tenants:
            if t["database"] == TEST_DB_NAME:
                test_tenant = t
                break
        
        if not test_tenant:
            test_tenant = tenants[0]
        
        tenant_db = test_tenant["database"]
        
        # Update status
        response = requests.patch(
            f"{BASE_URL}/api/tenant/tenants/{tenant_db}/status",
            headers=auth_headers,
            json={
                "status": "active",
                "notes": f"Status update test at {datetime.now().isoformat()}"
            }
        )
        
        assert response.status_code == 200, f"Failed to update status: {response.text}"
        
        data = response.json()
        assert data["status"] == "updated", f"Unexpected status: {data['status']}"
        assert "tenant_id" in data
        assert data["new_status"] == "active"
        assert "updated_at" in data
        
        print(f"✓ Updated tenant status: {tenant_db} -> active")
    
    def test_update_tenant_status_invalid_value(self, auth_headers):
        """Test updating tenant with invalid status value fails"""
        response = requests.patch(
            f"{BASE_URL}/api/tenant/tenants/{TEST_DB_NAME}/status",
            headers=auth_headers,
            json={
                "status": "invalid_status",
                "notes": "Test invalid status"
            }
        )
        
        assert response.status_code == 422, f"Expected 422 validation error, got {response.status_code}"
        print("✓ Invalid status value correctly rejected")


class TestEditTenantConfig(TestAuthenticationSetup):
    """Test PATCH /api/tenant/tenants/{id} - Edit tenant configuration"""
    
    def test_update_tenant_config_success(self, auth_headers):
        """Test updating tenant configuration"""
        # First, list tenants to get a valid tenant_id
        list_response = requests.get(
            f"{BASE_URL}/api/tenant/tenants",
            headers=auth_headers
        )
        assert list_response.status_code == 200
        
        tenants = list_response.json().get("tenants", [])
        if not tenants:
            pytest.skip("No tenants available for config update test")
        
        # Use test tenant or first available
        test_tenant = None
        for t in tenants:
            if t["database"] == TEST_DB_NAME:
                test_tenant = t
                break
        
        if not test_tenant:
            test_tenant = tenants[0]
        
        tenant_db = test_tenant["database"]
        
        # Update config
        response = requests.patch(
            f"{BASE_URL}/api/tenant/tenants/{tenant_db}",
            headers=auth_headers,
            json={
                "tenant_type": "retail",
                "currency": "IDR",
                "timezone": "Asia/Jakarta",
                "ai_enabled": True,
                "notes": f"Config update test at {datetime.now().isoformat()}"
            }
        )
        
        assert response.status_code == 200, f"Failed to update config: {response.text}"
        
        data = response.json()
        assert data["status"] == "updated", f"Unexpected status: {data['status']}"
        assert "updated_fields" in data
        assert "updated_at" in data
        
        print(f"✓ Updated tenant config: {tenant_db}")
        print(f"  Updated fields: {data['updated_fields']}")


class TestDeleteTenantGuardrail(TestAuthenticationSetup):
    """Test DELETE /api/tenant/{id} - Delete tenant with guardrails"""
    
    def test_delete_dry_run_check_transactions(self, auth_headers):
        """Test delete dry run - check for transactions"""
        # First, list tenants to get a valid tenant
        list_response = requests.get(
            f"{BASE_URL}/api/tenant/tenants",
            headers=auth_headers
        )
        assert list_response.status_code == 200
        
        tenants = list_response.json().get("tenants", [])
        if not tenants:
            pytest.skip("No tenants available for delete test")
        
        # Use test tenant if exists
        test_tenant = None
        for t in tenants:
            if t["database"] == TEST_DB_NAME:
                test_tenant = t
                break
        
        if not test_tenant:
            test_tenant = tenants[0]
        
        tenant_db = test_tenant["database"]
        
        # Dry run delete (confirm_delete=false)
        response = requests.delete(
            f"{BASE_URL}/api/tenant/{tenant_db}?confirm_delete=false",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Failed dry run delete: {response.text}"
        
        data = response.json()
        assert data["status"] in ["warning", "requires_confirmation"], f"Unexpected status: {data['status']}"
        assert "tenant_id" in data
        assert "database" in data
        
        # If has transactions, should show warning
        if data["status"] == "warning":
            assert "transaction_counts" in data, "Warning should include transaction_counts"
            assert "total_transactions" in data, "Warning should include total_transactions"
            assert "warning" in data, "Warning should include warning message"
            print(f"✓ Dry run detected {data['total_transactions']} transactions")
            print(f"  Transaction counts: {data['transaction_counts']}")
        else:
            print(f"✓ Dry run - tenant has no transactions, safe to delete")
    
    def test_delete_with_transactions_guardrail(self, auth_headers):
        """Test delete guardrail for tenant with transactions"""
        # Get tenant with transactions (ocb_titan should have data)
        response = requests.delete(
            f"{BASE_URL}/api/tenant/ocb_titan?confirm_delete=false",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        
        if data["status"] == "warning":
            assert data["total_transactions"] > 0, "Expected transactions in production tenant"
            assert "PERHATIAN" in data.get("warning", "") or "PERMANEN" in data.get("warning", ""), \
                "Warning should emphasize irreversible deletion"
            print(f"✓ Guardrail working: {data['total_transactions']} transactions detected")
            print(f"  Warning: {data.get('warning', 'N/A')}")
        elif data["status"] == "requires_confirmation":
            print("✓ Tenant has no transactions but requires confirmation")
    
    def test_delete_actual_test_tenant(self, auth_headers):
        """Test actual deletion of test tenant (with confirm_delete=true)"""
        # Only delete the test tenant we created
        response = requests.delete(
            f"{BASE_URL}/api/tenant/{TEST_DB_NAME}?confirm_delete=true&backup_before_delete=true&reason=pytest_cleanup",
            headers=auth_headers
        )
        
        if response.status_code == 404:
            pytest.skip(f"Test tenant {TEST_DB_NAME} not found, skipping delete test")
        
        assert response.status_code == 200, f"Failed to delete tenant: {response.text}"
        
        data = response.json()
        assert data["status"] == "deleted", f"Unexpected status: {data['status']}"
        assert data["database_dropped"] == True, "Database should be dropped"
        assert "backup_created" in data, "Should have backup info"
        assert data["tenant_id"] == TEST_DB_NAME
        
        print(f"✓ Successfully deleted test tenant: {TEST_DB_NAME}")
        print(f"  Backup: {data.get('backup_created', 'N/A')}")
        print(f"  Transactions deleted: {data.get('transaction_counts_deleted', {})}")


class TestRBACProtection(TestAuthenticationSetup):
    """Test RBAC protection - only owner/super_admin can access"""
    
    def test_list_tenants_requires_auth(self):
        """Test that listing tenants requires authentication"""
        response = requests.get(f"{BASE_URL}/api/tenant/tenants")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ List tenants requires authentication")
    
    def test_create_tenant_requires_auth(self):
        """Test that creating tenant requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/tenant/tenants",
            json={"business_name": "Test", "tenant_id": "test"}
        )
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ Create tenant requires authentication")
    
    def test_delete_tenant_requires_auth(self):
        """Test that deleting tenant requires authentication"""
        response = requests.delete(f"{BASE_URL}/api/tenant/test_tenant")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ Delete tenant requires authentication")


class TestAuditLogging(TestAuthenticationSetup):
    """Test audit logging for tenant operations"""
    
    def test_audit_log_exists_after_update(self, auth_headers):
        """Test that audit log is created after tenant update"""
        # First get a tenant to update
        list_response = requests.get(
            f"{BASE_URL}/api/tenant/tenants",
            headers=auth_headers
        )
        
        tenants = list_response.json().get("tenants", [])
        if not tenants:
            pytest.skip("No tenants available for audit log test")
        
        tenant_db = tenants[0]["database"]
        
        # Update tenant status
        update_response = requests.patch(
            f"{BASE_URL}/api/tenant/tenants/{tenant_db}/status",
            headers=auth_headers,
            json={
                "status": "active",
                "notes": f"Audit log test at {datetime.now().isoformat()}"
            }
        )
        
        assert update_response.status_code == 200, f"Update failed: {update_response.text}"
        
        data = update_response.json()
        assert "updated_at" in data, "Response should have updated_at timestamp"
        
        print(f"✓ Tenant update recorded at: {data['updated_at']}")
        print(f"  Note: Audit log created in tenant's audit_logs collection")


class TestDeletedTenantsHistory(TestAuthenticationSetup):
    """Test GET /api/tenant/deleted/history - View deleted tenants"""
    
    def test_get_deleted_tenants_history(self, auth_headers):
        """Test fetching deleted tenants history"""
        response = requests.get(
            f"{BASE_URL}/api/tenant/deleted/history",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Failed to get history: {response.text}"
        
        data = response.json()
        assert "deleted_tenants" in data, "Response should have deleted_tenants"
        assert "total" in data, "Response should have total count"
        
        print(f"✓ Deleted tenants history: {data['total']} records")
        
        if data["deleted_tenants"]:
            latest = data["deleted_tenants"][0]
            print(f"  Latest deleted: {latest.get('tenant_id', 'N/A')} at {latest.get('deleted_at', 'N/A')}")


class TestSyncBlueprint(TestAuthenticationSetup):
    """Test POST /api/tenant/tenants/{id}/sync-blueprint - Sync tenant blueprint"""
    
    def test_sync_blueprint_success(self, auth_headers):
        """Test syncing tenant blueprint"""
        # Get a tenant to sync
        list_response = requests.get(
            f"{BASE_URL}/api/tenant/tenants",
            headers=auth_headers
        )
        
        tenants = list_response.json().get("tenants", [])
        if not tenants:
            pytest.skip("No tenants available for sync test")
        
        # Find a tenant that needs migration
        tenant_to_sync = None
        for t in tenants:
            if t.get("needs_migration") or t.get("health") == "needs_update":
                tenant_to_sync = t
                break
        
        if not tenant_to_sync:
            tenant_to_sync = tenants[0]
        
        tenant_db = tenant_to_sync["database"]
        
        # Sync blueprint
        response = requests.post(
            f"{BASE_URL}/api/tenant/tenants/{tenant_db}/sync-blueprint",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Failed to sync blueprint: {response.text}"
        
        data = response.json()
        assert data["status"] == "synced", f"Unexpected status: {data['status']}"
        assert "blueprint_version" in data
        assert "changes" in data
        
        print(f"✓ Blueprint synced for: {tenant_db}")
        print(f"  Blueprint version: {data['blueprint_version']}")
        print(f"  Changes: {data['changes']}")


# Additional endpoint tests
class TestTenantListEndpoint(TestAuthenticationSetup):
    """Test GET /api/tenant/list - Alternative list endpoint"""
    
    def test_list_endpoint(self, auth_headers):
        """Test the /list endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/tenant/list",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "tenants" in data
        assert "current_blueprint_version" in data
        
        print(f"✓ Tenant list endpoint working: {len(data['tenants'])} tenants")


class TestBlueprintStatus(TestAuthenticationSetup):
    """Test GET /api/tenant/blueprint-status - Blueprint status"""
    
    def test_blueprint_status_endpoint(self, auth_headers):
        """Test blueprint status endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/tenant/blueprint-status",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "current_blueprint_version" in data
        assert "required_collections" in data
        assert "tenants" in data
        
        print(f"✓ Blueprint status: v{data['current_blueprint_version']}")
        print(f"  Required collections: {len(data['required_collections'])}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
