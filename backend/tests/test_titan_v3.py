"""
OCB TITAN Retail AI System - Test Suite v3
Tests for: Role & Permission, AI Business, User Management, Multi-role access control
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
OWNER_CREDS = {"email": "admin@ocb.com", "password": "admin123"}
KASIR_CREDS = {"email": "kasir@ocb.com", "password": "test123"}
SUPERVISOR_CREDS = {"email": "supervisor@ocb.com", "password": "test123"}

class TestAuth:
    """Authentication tests for multiple roles"""
    
    def test_owner_login(self):
        """Test owner/admin login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=OWNER_CREDS)
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["user"]["role"] == "owner"
        assert data["user"]["email"] == "admin@ocb.com"
    
    def test_kasir_login(self):
        """Test cashier login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=KASIR_CREDS)
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["role"] == "cashier"
        assert data["user"]["branch"]["code"] == "CBG1"
        assert "Banjarmasin" in data["user"]["branch"]["name"]
    
    def test_supervisor_login(self):
        """Test supervisor login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=SUPERVISOR_CREDS)
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["role"] == "supervisor"
        assert data["user"]["branch"]["code"] == "CBG1"


class TestRoles:
    """Role & Permission management tests"""
    
    @pytest.fixture
    def owner_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=OWNER_CREDS)
        return response.json()["token"]
    
    def test_get_roles_list(self, owner_token):
        """Test getting all roles - should return 6 default roles"""
        response = requests.get(
            f"{BASE_URL}/api/roles",
            headers={"Authorization": f"Bearer {owner_token}"}
        )
        assert response.status_code == 200
        roles = response.json()
        assert len(roles) >= 6  # 6 default system roles
        
        # Check all default roles exist
        role_codes = [r["code"] for r in roles]
        assert "owner" in role_codes
        assert "admin" in role_codes
        assert "supervisor" in role_codes
        assert "cashier" in role_codes
        assert "finance" in role_codes
        assert "inventory" in role_codes
    
    def test_roles_have_permissions(self, owner_token):
        """Test that roles have permissions defined"""
        response = requests.get(
            f"{BASE_URL}/api/roles",
            headers={"Authorization": f"Bearer {owner_token}"}
        )
        roles = response.json()
        for role in roles:
            assert "permissions" in role
            assert "is_system" in role
            # Check some basic permissions
            perms = role.get("permissions", {})
            assert "dashboard" in perms
            assert "kasir" in perms
    
    def test_get_permissions_template(self, owner_token):
        """Test getting permissions template"""
        response = requests.get(
            f"{BASE_URL}/api/roles/permissions-template",
            headers={"Authorization": f"Bearer {owner_token}"}
        )
        assert response.status_code == 200
        template = response.json()
        assert "dashboard" in template
        assert "kasir" in template
        assert "pelanggan" in template
        assert "ai_bisnis" in template
    
    def test_owner_role_full_access(self, owner_token):
        """Test that owner role has full access to all menus"""
        response = requests.get(
            f"{BASE_URL}/api/roles/owner",
            headers={"Authorization": f"Bearer {owner_token}"}
        )
        assert response.status_code == 200
        role = response.json()
        perms = role["permissions"]
        
        # Owner should have all permissions enabled
        for menu, actions in perms.items():
            for action, enabled in actions.items():
                assert enabled == True, f"Owner should have {action} permission for {menu}"
    
    def test_cashier_limited_permissions(self, owner_token):
        """Test that cashier has limited permissions"""
        response = requests.get(
            f"{BASE_URL}/api/roles/cashier",
            headers={"Authorization": f"Bearer {owner_token}"}
        )
        assert response.status_code == 200
        role = response.json()
        perms = role["permissions"]
        
        # Cashier should have limited access
        assert perms["dashboard"]["lihat"] == True
        assert perms["kasir"]["lihat"] == True
        assert perms["pelanggan"]["lihat"] == True
        # Cashier should NOT have access to these
        assert perms["keuangan"]["lihat"] == False
        assert perms["akuntansi"]["lihat"] == False
        assert perms["cabang"]["lihat"] == False
        assert perms["pengguna"]["lihat"] == False


class TestAIBusiness:
    """AI Business analytics endpoints tests"""
    
    @pytest.fixture
    def owner_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=OWNER_CREDS)
        return response.json()["token"]
    
    @pytest.fixture
    def supervisor_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=SUPERVISOR_CREDS)
        return response.json()["token"]
    
    @pytest.fixture
    def kasir_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=KASIR_CREDS)
        return response.json()["token"]
    
    def test_insight_penjualan(self, owner_token):
        """Test sales insights endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/ai-bisnis/insight-penjualan?days=30",
            headers={"Authorization": f"Bearer {owner_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "periode" in data
        assert "ringkasan" in data
        assert "insights" in data
        assert "total_penjualan" in data["ringkasan"]
        assert "total_laba" in data["ringkasan"]
    
    def test_rekomendasi_restock(self, owner_token):
        """Test restock recommendations endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/ai-bisnis/rekomendasi-restock",
            headers={"Authorization": f"Bearer {owner_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_produk_perlu_restock" in data
        assert "total_estimasi_biaya" in data
        assert "rekomendasi" in data
        assert "insight" in data
    
    def test_produk_terlaris(self, owner_token):
        """Test best sellers endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/ai-bisnis/produk-terlaris?days=30&limit=10",
            headers={"Authorization": f"Bearer {owner_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "periode" in data
        assert "produk_terlaris" in data
        assert "insights" in data
    
    def test_produk_lambat(self, owner_token):
        """Test slow movers endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/ai-bisnis/produk-lambat?days=30",
            headers={"Authorization": f"Bearer {owner_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "periode" in data
        assert "total_nilai_tertahan" in data
        assert "produk_lambat" in data
    
    def test_analisa_stok(self, owner_token):
        """Test stock analysis endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/ai-bisnis/analisa-stok",
            headers={"Authorization": f"Bearer {owner_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "ringkasan" in data
        assert "insights" in data
        assert "total_jenis_produk" in data["ringkasan"]
        assert "nilai_modal" in data["ringkasan"]
    
    def test_performa_cabang_owner_access(self, owner_token):
        """Test branch performance - owner should have access"""
        response = requests.get(
            f"{BASE_URL}/api/ai-bisnis/performa-cabang?days=30",
            headers={"Authorization": f"Bearer {owner_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "periode" in data
        assert "total_cabang" in data
        assert "performa_cabang" in data
        assert "insights" in data
    
    def test_performa_cabang_cashier_denied(self, kasir_token):
        """Test branch performance - cashier should be denied"""
        response = requests.get(
            f"{BASE_URL}/api/ai-bisnis/performa-cabang",
            headers={"Authorization": f"Bearer {kasir_token}"}
        )
        assert response.status_code == 403
        data = response.json()
        assert "Akses ditolak" in data["detail"]
    
    def test_rekomendasi_bisnis(self, owner_token):
        """Test business recommendations endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/ai-bisnis/rekomendasi-bisnis",
            headers={"Authorization": f"Bearer {owner_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "tanggal" in data
        assert "total_rekomendasi" in data
        assert "rekomendasi" in data
    
    def test_dashboard_widget(self, owner_token):
        """Test dashboard AI widget endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/ai-bisnis/dashboard-widget",
            headers={"Authorization": f"Bearer {owner_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "insights" in data


class TestUsers:
    """User management tests"""
    
    @pytest.fixture
    def owner_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=OWNER_CREDS)
        return response.json()["token"]
    
    def test_get_users_list(self, owner_token):
        """Test getting users list"""
        response = requests.get(
            f"{BASE_URL}/api/users",
            headers={"Authorization": f"Bearer {owner_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # Check for users
        users = data.get("items", data) if isinstance(data, dict) else data
        assert len(users) >= 1
    
    def test_filter_users_by_role(self, owner_token):
        """Test filtering users by role"""
        response = requests.get(
            f"{BASE_URL}/api/users?role=cashier",
            headers={"Authorization": f"Bearer {owner_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        users = data.get("items", data) if isinstance(data, dict) else data
        # All users should be cashiers
        for user in users:
            assert user["role"] == "cashier"


class TestBranchRestriction:
    """Tests for branch-based data restriction"""
    
    @pytest.fixture
    def kasir_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=KASIR_CREDS)
        return response.json()["token"]
    
    @pytest.fixture
    def owner_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=OWNER_CREDS)
        return response.json()["token"]
    
    def test_kasir_sees_own_branch(self, kasir_token):
        """Test that kasir sees their branch info"""
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {kasir_token}"}
        )
        assert response.status_code == 200
        user = response.json()
        assert user["branch"]["code"] == "CBG1"
        assert "Banjarmasin" in user["branch"]["name"]
    
    def test_owner_sees_all_branches(self, owner_token):
        """Test that owner can see all branches"""
        response = requests.get(
            f"{BASE_URL}/api/branches",
            headers={"Authorization": f"Bearer {owner_token}"}
        )
        assert response.status_code == 200
        branches = response.json()
        assert len(branches) >= 2  # At least HQ and Cabang 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
