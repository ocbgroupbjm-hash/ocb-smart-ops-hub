"""
OCB TITAN ERP - RBAC System Backend Tests
Tests: Permission Matrix, Role Assignment, Audit Log APIs
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "ocbgroupbjm@gmail.com"
TEST_PASSWORD = "admin123"

class TestRBACSystem:
    """RBAC System API Tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Login and get auth token"""
        # First get businesses to find OCB GROUP
        login_payload = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
        
        # Login
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_payload)
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token") or data.get("token")
            self.user = data.get("user", {})
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip(f"Login failed: {response.status_code}")
    
    # =============== RBAC INIT TEST ===============
    def test_01_rbac_init(self):
        """Test RBAC system initialization"""
        response = requests.post(f"{BASE_URL}/api/rbac/init", headers=self.headers)
        assert response.status_code == 200, f"Init failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "message" in data
        assert "total_modules" in data
        assert "total_actions" in data
        
        # Verify counts (95 modules, 11 actions as per code)
        assert data["total_modules"] == 95, f"Expected 95 modules, got {data['total_modules']}"
        assert data["total_actions"] == 11, f"Expected 11 actions, got {data['total_actions']}"
        print(f"RBAC Init: {data['message']} - {data['total_modules']} modules, {data['total_actions']} actions")
    
    # =============== ROLES TESTS ===============
    def test_02_get_roles(self):
        """Test GET /api/rbac/roles - List all roles"""
        response = requests.get(f"{BASE_URL}/api/rbac/roles", headers=self.headers)
        assert response.status_code == 200, f"Get roles failed: {response.text}"
        data = response.json()
        
        assert "roles" in data
        assert "total" in data
        assert isinstance(data["roles"], list)
        
        # Verify default roles exist
        role_codes = [r.get("code") for r in data["roles"]]
        expected_roles = ["super_admin", "owner", "director", "manager", "cashier", "viewer"]
        for expected in expected_roles:
            assert expected in role_codes, f"Missing role: {expected}"
        
        print(f"Roles found: {len(data['roles'])} - {role_codes}")
        return data["roles"]
    
    def test_03_get_single_role(self):
        """Test GET /api/rbac/roles/{role_id} - Get single role with permissions"""
        # First get roles list
        roles_resp = requests.get(f"{BASE_URL}/api/rbac/roles", headers=self.headers)
        roles = roles_resp.json().get("roles", [])
        
        if not roles:
            pytest.skip("No roles available")
        
        role = roles[0]  # Get first role
        response = requests.get(f"{BASE_URL}/api/rbac/roles/{role['id']}", headers=self.headers)
        assert response.status_code == 200, f"Get role failed: {response.text}"
        data = response.json()
        
        assert "id" in data
        assert "name" in data
        assert "permissions" in data
        print(f"Role: {data['name']} - {len(data.get('permissions', []))} permissions")
    
    # =============== PERMISSION MODULES TEST ===============
    def test_04_get_permission_modules(self):
        """Test GET /api/rbac/permissions/modules - Get all available modules"""
        response = requests.get(f"{BASE_URL}/api/rbac/permissions/modules", headers=self.headers)
        assert response.status_code == 200, f"Get modules failed: {response.text}"
        data = response.json()
        
        assert "modules" in data
        assert "categories" in data
        assert "actions" in data
        
        # Verify module count
        assert len(data["modules"]) == 95, f"Expected 95 modules, got {len(data['modules'])}"
        
        # Verify actions
        expected_actions = ["view", "create", "edit", "delete", "approve", "export", "print"]
        for action in expected_actions:
            assert action in data["actions"], f"Missing action: {action}"
        
        # Verify categories
        expected_categories = ["master_data", "pembelian", "penjualan", "persediaan", "akuntansi", "laporan", "pengaturan"]
        for cat in expected_categories:
            assert cat in data["categories"], f"Missing category: {cat}"
        
        print(f"Modules: {len(data['modules'])} - Categories: {list(data['categories'].keys())}")
        print(f"Actions: {data['actions']}")
    
    # =============== PERMISSION MATRIX TEST ===============
    def test_05_get_permission_matrix(self):
        """Test GET /api/rbac/permissions/matrix/{role_id} - Get permission matrix"""
        # Get super_admin role
        roles_resp = requests.get(f"{BASE_URL}/api/rbac/roles", headers=self.headers)
        roles = roles_resp.json().get("roles", [])
        super_admin = next((r for r in roles if r.get("code") == "super_admin"), None)
        
        if not super_admin:
            pytest.skip("Super admin role not found")
        
        response = requests.get(
            f"{BASE_URL}/api/rbac/permissions/matrix/{super_admin['id']}", 
            headers=self.headers
        )
        assert response.status_code == 200, f"Get matrix failed: {response.text}"
        data = response.json()
        
        assert "role" in data
        assert "matrix" in data
        assert "actions" in data
        
        # Verify matrix structure
        assert len(data["matrix"]) == 95, f"Expected 95 modules in matrix, got {len(data['matrix'])}"
        
        # Verify each matrix item has correct structure
        for item in data["matrix"]:
            assert "module" in item
            assert "name" in item
            assert "category" in item
            assert "permissions" in item
        
        print(f"Matrix for {data['role']['name']}: {len(data['matrix'])} modules")
    
    # =============== UPDATE PERMISSIONS TEST ===============
    def test_06_update_permissions(self):
        """Test POST /api/rbac/permissions/{role_id} - Update permissions"""
        # Get viewer role (good for testing as it's restricted)
        roles_resp = requests.get(f"{BASE_URL}/api/rbac/roles", headers=self.headers)
        roles = roles_resp.json().get("roles", [])
        viewer = next((r for r in roles if r.get("code") == "viewer"), None)
        
        if not viewer:
            pytest.skip("Viewer role not found")
        
        # Update some permissions
        permissions_update = {
            "permissions": [
                {"module": "master_item", "action": "view", "allowed": True},
                {"module": "master_item", "action": "export", "allowed": True},
                {"module": "sales", "action": "view", "allowed": True}
            ]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/rbac/permissions/{viewer['id']}", 
            json=permissions_update,
            headers=self.headers
        )
        assert response.status_code == 200, f"Update permissions failed: {response.text}"
        data = response.json()
        
        assert "message" in data
        assert "count" in data
        assert data["count"] == 3
        print(f"Permissions updated: {data['message']} - count: {data['count']}")
    
    # =============== USER PERMISSIONS TEST ===============
    def test_07_get_my_permissions(self):
        """Test GET /api/rbac/user/permissions - Get current user permissions"""
        response = requests.get(f"{BASE_URL}/api/rbac/user/permissions", headers=self.headers)
        assert response.status_code == 200, f"Get my permissions failed: {response.text}"
        data = response.json()
        
        assert "user_id" in data
        assert "role_id" in data or data.get("all_permissions") is not None
        
        # If user has super_admin role
        if data.get("all_permissions"):
            print("User has all_permissions (super_admin)")
        else:
            print(f"User permissions: role_id={data.get('role_id')}, permissions count={len(data.get('permissions', {}))}")
    
    # =============== PERMISSION CHECK TEST ===============
    def test_08_check_permission(self):
        """Test GET /api/rbac/check - Check specific permission"""
        # Check for master_item view permission
        response = requests.get(
            f"{BASE_URL}/api/rbac/check",
            params={"module": "master_item", "action": "view"},
            headers=self.headers
        )
        assert response.status_code == 200, f"Check permission failed: {response.text}"
        data = response.json()
        
        assert "module" in data
        assert "action" in data
        assert "allowed" in data
        assert data["module"] == "master_item"
        assert data["action"] == "view"
        
        print(f"Permission check: {data['module']}.{data['action']} = {data['allowed']}")
    
    def test_09_check_permission_sales_create(self):
        """Test permission check for sales create"""
        response = requests.get(
            f"{BASE_URL}/api/rbac/check",
            params={"module": "sales", "action": "create"},
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        print(f"Permission check: {data['module']}.{data['action']} = {data['allowed']}")
    
    # =============== USER ROLE ASSIGNMENT TEST ===============
    def test_10_get_users_for_role_assignment(self):
        """Test GET /api/users - Get users list for role assignment"""
        response = requests.get(f"{BASE_URL}/api/users", headers=self.headers)
        assert response.status_code == 200, f"Get users failed: {response.text}"
        data = response.json()
        
        # API returns {items: [], total: n} format
        users = data.get("items") or data.get("users") or data
        if isinstance(users, dict):
            users = users.get("items", [])
        assert isinstance(users, list), f"Users should be a list, got {type(users)}"
        
        print(f"Users available for role assignment: {len(users)}")
        if users:
            print(f"First user: {users[0].get('name', users[0].get('email', 'N/A'))}")
    
    def test_11_assign_role_to_user(self):
        """Test PUT /api/rbac/user/{user_id}/role - Assign role to user"""
        # Get users
        users_resp = requests.get(f"{BASE_URL}/api/users", headers=self.headers)
        users_data = users_resp.json()
        users = users_data.get("items") or users_data.get("users") or users_data
        
        # Get roles
        roles_resp = requests.get(f"{BASE_URL}/api/rbac/roles", headers=self.headers)
        roles = roles_resp.json().get("roles", [])
        
        if not users or not roles:
            pytest.skip("No users or roles available")
        
        # Find super_admin role
        super_admin = next((r for r in roles if r.get("code") == "super_admin"), None)
        if not super_admin:
            pytest.skip("Super admin role not found")
        
        # Assign role to first user
        user = users[0]
        role_update = {
            "role_id": super_admin["id"],
            "branch_access": []
        }
        
        response = requests.put(
            f"{BASE_URL}/api/rbac/user/{user['id']}/role",
            json=role_update,
            headers=self.headers
        )
        assert response.status_code == 200, f"Assign role failed: {response.text}"
        data = response.json()
        
        assert "message" in data
        print(f"Role assignment: {data['message']}")
    
    # =============== AUDIT LOG TEST ===============
    def test_12_get_audit_logs(self):
        """Test GET /api/rbac/audit-logs - Get audit logs"""
        response = requests.get(f"{BASE_URL}/api/rbac/audit-logs", headers=self.headers)
        assert response.status_code == 200, f"Get audit logs failed: {response.text}"
        data = response.json()
        
        assert "logs" in data
        assert "total" in data
        
        print(f"Audit logs: {len(data['logs'])} entries (total: {data['total']})")
        
        if data["logs"]:
            log = data["logs"][0]
            print(f"Latest log: {log.get('action')} - {log.get('module')} - {log.get('description')}")
    
    def test_13_get_audit_logs_with_filters(self):
        """Test audit logs with filters"""
        # Filter by action
        response = requests.get(
            f"{BASE_URL}/api/rbac/audit-logs",
            params={"action": "edit", "limit": 10},
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        print(f"Filtered logs (action=edit): {len(data['logs'])} entries")
    
    # =============== BULK PERMISSIONS TEST ===============
    def test_14_bulk_update_permissions(self):
        """Test POST /api/rbac/permissions/{role_id}/bulk - Bulk update permissions"""
        # Get viewer role
        roles_resp = requests.get(f"{BASE_URL}/api/rbac/roles", headers=self.headers)
        roles = roles_resp.json().get("roles", [])
        viewer = next((r for r in roles if r.get("code") == "viewer"), None)
        
        if not viewer:
            pytest.skip("Viewer role not found")
        
        # Test set_all for specific category
        response = requests.post(
            f"{BASE_URL}/api/rbac/permissions/{viewer['id']}/bulk",
            params={"action": "set_all", "category": "laporan"},
            headers=self.headers
        )
        assert response.status_code == 200, f"Bulk update failed: {response.text}"
        data = response.json()
        
        assert "message" in data
        print(f"Bulk update: {data['message']}")
    
    # =============== ROLE CRUD TEST ===============
    def test_15_create_role(self):
        """Test POST /api/rbac/roles - Create new role"""
        role_data = {
            "code": "TEST_ROLE_RBAC",
            "name": "Test RBAC Role",
            "description": "Test role for RBAC testing",
            "level": 99,
            "all_permissions": False,
            "all_branches": False,
            "direct_cashier": False,
            "view_only": False,
            "branch_access": [],
            "account_access": []
        }
        
        response = requests.post(
            f"{BASE_URL}/api/rbac/roles",
            json=role_data,
            headers=self.headers
        )
        
        # May fail if role already exists
        if response.status_code == 400:
            print("Test role already exists, skipping create")
            return
        
        assert response.status_code == 200, f"Create role failed: {response.text}"
        data = response.json()
        assert "id" in data
        print(f"Created role: {data['id']}")
        
        self.__class__.test_role_id = data["id"]
    
    def test_16_delete_test_role(self):
        """Test DELETE /api/rbac/roles/{role_id} - Delete test role"""
        # Get the test role
        roles_resp = requests.get(f"{BASE_URL}/api/rbac/roles", headers=self.headers)
        roles = roles_resp.json().get("roles", [])
        test_role = next((r for r in roles if r.get("code") == "TEST_ROLE_RBAC"), None)
        
        if not test_role:
            print("Test role not found, skipping delete")
            return
        
        response = requests.delete(
            f"{BASE_URL}/api/rbac/roles/{test_role['id']}",
            headers=self.headers
        )
        assert response.status_code == 200, f"Delete role failed: {response.text}"
        data = response.json()
        print(f"Deleted role: {data['message']}")
    
    # =============== BRANCH ACCESS CHECK ===============
    def test_17_check_branch_access(self):
        """Test GET /api/rbac/check-branch - Check branch access"""
        # Get branches first
        branches_resp = requests.get(f"{BASE_URL}/api/global-map/branches", headers=self.headers)
        if branches_resp.status_code != 200:
            pytest.skip("Cannot get branches")
        
        branches = branches_resp.json().get("branches", [])
        if not branches:
            pytest.skip("No branches available")
        
        branch_id = branches[0].get("id")
        
        response = requests.get(
            f"{BASE_URL}/api/rbac/check-branch",
            params={"branch_id": branch_id},
            headers=self.headers
        )
        assert response.status_code == 200, f"Check branch access failed: {response.text}"
        data = response.json()
        
        assert "branch_id" in data
        assert "allowed" in data
        print(f"Branch access check: branch={branch_id}, allowed={data['allowed']}")
    
    # =============== GET USER PERMISSIONS BY ID ===============
    def test_18_get_user_permissions_by_id(self):
        """Test GET /api/rbac/user/{user_id}/permissions - Get specific user permissions"""
        # Get current user id
        user_id = self.user.get("id")
        if not user_id:
            # Try to get from users list
            users_resp = requests.get(f"{BASE_URL}/api/users", headers=self.headers)
            users = users_resp.json().get("users") or users_resp.json()
            if users:
                user_id = users[0].get("id")
        
        if not user_id:
            pytest.skip("No user id available")
        
        response = requests.get(
            f"{BASE_URL}/api/rbac/user/{user_id}/permissions",
            headers=self.headers
        )
        assert response.status_code == 200, f"Get user permissions failed: {response.text}"
        data = response.json()
        
        assert "user_id" in data
        print(f"User {user_id} permissions: role={data.get('role_name')}, all_permissions={data.get('all_permissions')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
