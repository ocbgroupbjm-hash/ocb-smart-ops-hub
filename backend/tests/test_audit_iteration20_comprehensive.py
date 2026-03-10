"""
OCB TITAN AI - AUDIT RONDE 4 - ITERATION 20
Comprehensive testing of all modules:
- PENGATURAN (Users, Roles, Branches)
- AKUNTANSI (COA, Cash, Journals, Ledger, Financial Reports)
- PERSEDIAAN (Stock, Movements, Transfers, Opname)
- LAPORAN (Sales, Inventory, Cash, Receivables, Payables)
"""
import pytest
import requests
import os
from datetime import datetime, timedelta
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAuditAuthentication:
    """Authentication tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.email = "ocbgroupbjm@gmail.com"
        self.password = "admin123"
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def test_01_login_success(self):
        """Test login with valid credentials"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": self.email,
            "password": self.password
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == self.email
        assert data["user"]["role"] == "owner"
        print(f"✓ Login successful - User: {data['user']['name']}, Role: {data['user']['role']}")


class TestPengaturanUsers:
    """PENGATURAN - User Management CRUD Tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        # Login to get token
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "ocbgroupbjm@gmail.com",
            "password": "admin123"
        })
        token = response.json().get("token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_01_list_users(self):
        """List all users"""
        response = self.session.get(f"{BASE_URL}/api/users")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 1
        print(f"✓ Found {data['total']} users")
    
    def test_02_create_audit_user(self):
        """Create test user with AUDIT- prefix"""
        user_data = {
            "email": f"AUDIT-user-{uuid.uuid4().hex[:8]}@test.com",
            "password": "test123456",
            "name": "AUDIT Test User",
            "phone": "08123456789",
            "role": "cashier"
        }
        response = self.session.post(f"{BASE_URL}/api/users", json=user_data)
        assert response.status_code == 200, f"Create user failed: {response.text}"
        data = response.json()
        assert "id" in data
        print(f"✓ Created audit user: {user_data['email']}")
        
        # Verify user exists
        get_response = self.session.get(f"{BASE_URL}/api/users/{data['id']}")
        assert get_response.status_code == 200
        assert get_response.json()["name"] == "AUDIT Test User"
        
        # Store for cleanup
        self.__class__.created_user_id = data["id"]
    
    def test_03_update_audit_user(self):
        """Update test user"""
        if not hasattr(self.__class__, 'created_user_id'):
            pytest.skip("No user created in previous test")
        
        update_data = {"name": "AUDIT Updated User", "phone": "08987654321"}
        response = self.session.put(
            f"{BASE_URL}/api/users/{self.__class__.created_user_id}",
            json=update_data
        )
        assert response.status_code == 200
        print(f"✓ Updated user: {self.__class__.created_user_id}")
        
        # Verify update
        get_response = self.session.get(f"{BASE_URL}/api/users/{self.__class__.created_user_id}")
        assert get_response.json()["name"] == "AUDIT Updated User"
    
    def test_04_delete_audit_user(self):
        """Delete test user"""
        if not hasattr(self.__class__, 'created_user_id'):
            pytest.skip("No user created in previous test")
        
        response = self.session.delete(f"{BASE_URL}/api/users/{self.__class__.created_user_id}")
        assert response.status_code == 200
        print(f"✓ Deleted user: {self.__class__.created_user_id}")


class TestPengaturanRoles:
    """PENGATURAN - Roles/Hak Akses Tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "ocbgroupbjm@gmail.com",
            "password": "admin123"
        })
        token = response.json().get("token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_01_list_roles(self):
        """List all roles"""
        response = self.session.get(f"{BASE_URL}/api/roles")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 5  # owner, admin, supervisor, cashier, finance, inventory
        role_codes = [r["code"] for r in data]
        assert "owner" in role_codes
        assert "admin" in role_codes
        assert "cashier" in role_codes
        print(f"✓ Found {len(data)} roles: {role_codes}")
    
    def test_02_get_role_detail(self):
        """Get specific role details"""
        response = self.session.get(f"{BASE_URL}/api/roles/owner")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "owner"
        assert "permissions" in data
        assert data["permissions"]["dashboard"]["lihat"] == True
        print(f"✓ Owner role has full permissions")


class TestPengaturanBranches:
    """PENGATURAN - Branch Management Tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "ocbgroupbjm@gmail.com",
            "password": "admin123"
        })
        token = response.json().get("token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_01_list_branches(self):
        """List all branches"""
        response = self.session.get(f"{BASE_URL}/api/branches")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 40  # Should have 40+ branches
        print(f"✓ Found {len(data)} branches")
    
    def test_02_get_branch_detail(self):
        """Get branch details"""
        # First get list
        response = self.session.get(f"{BASE_URL}/api/branches")
        branches = response.json()
        if branches:
            branch_id = branches[0]["id"]
            detail_response = self.session.get(f"{BASE_URL}/api/branches/{branch_id}")
            assert detail_response.status_code == 200
            print(f"✓ Got branch detail: {detail_response.json()['name']}")


class TestAkuntansiCOA:
    """AKUNTANSI - Daftar Perkiraan (Chart of Accounts) CRUD"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "ocbgroupbjm@gmail.com",
            "password": "admin123"
        })
        token = response.json().get("token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_01_list_accounts(self):
        """List all accounts"""
        response = self.session.get(f"{BASE_URL}/api/accounting/accounts")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert data["total"] >= 10
        print(f"✓ Found {data['total']} accounts (COA)")
    
    def test_02_create_audit_account(self):
        """Create test account"""
        account_data = {
            "code": f"9-AUDIT-{uuid.uuid4().hex[:4].upper()}",
            "name": "AUDIT Test Account",
            "category": "expense",
            "account_type": "detail",
            "is_cash": False,
            "is_active": True,
            "normal_balance": "debit"
        }
        response = self.session.post(f"{BASE_URL}/api/accounting/accounts", json=account_data)
        assert response.status_code == 200, f"Create account failed: {response.text}"
        data = response.json()
        assert "id" in data
        print(f"✓ Created audit account: {account_data['code']}")
        self.__class__.created_account_id = data["id"]
    
    def test_03_update_audit_account(self):
        """Update test account"""
        if not hasattr(self.__class__, 'created_account_id'):
            pytest.skip("No account created")
        
        update_data = {
            "code": f"9-AUDIT-UPD",
            "name": "AUDIT Updated Account",
            "category": "expense",
            "account_type": "detail",
            "is_cash": False,
            "is_active": True,
            "normal_balance": "debit"
        }
        response = self.session.put(
            f"{BASE_URL}/api/accounting/accounts/{self.__class__.created_account_id}",
            json=update_data
        )
        assert response.status_code == 200
        print(f"✓ Updated account")
    
    def test_04_delete_audit_account(self):
        """Delete test account"""
        if not hasattr(self.__class__, 'created_account_id'):
            pytest.skip("No account created")
        
        response = self.session.delete(
            f"{BASE_URL}/api/accounting/accounts/{self.__class__.created_account_id}"
        )
        assert response.status_code == 200
        print(f"✓ Deleted account")


class TestAkuntansiCash:
    """AKUNTANSI - Kas Masuk/Keluar Tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "ocbgroupbjm@gmail.com",
            "password": "admin123"
        })
        token = response.json().get("token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_01_list_cash_transactions(self):
        """List cash transactions"""
        response = self.session.get(f"{BASE_URL}/api/accounting/cash")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        print(f"✓ Found {data['total']} cash transactions")
    
    def test_02_get_cash_in_transactions(self):
        """Filter cash in transactions"""
        response = self.session.get(f"{BASE_URL}/api/accounting/cash?transaction_type=cash_in")
        assert response.status_code == 200
        print(f"✓ Cash In filter works")
    
    def test_03_get_cash_out_transactions(self):
        """Filter cash out transactions"""
        response = self.session.get(f"{BASE_URL}/api/accounting/cash?transaction_type=cash_out")
        assert response.status_code == 200
        print(f"✓ Cash Out filter works")


class TestAkuntansiJournals:
    """AKUNTANSI - Jurnal Tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "ocbgroupbjm@gmail.com",
            "password": "admin123"
        })
        token = response.json().get("token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_01_list_journals(self):
        """List all journals"""
        response = self.session.get(f"{BASE_URL}/api/accounting/journals")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total_debit" in data
        assert "total_credit" in data
        print(f"✓ Found {data['total']} journals, Total Debit: {data['total_debit']}, Total Credit: {data['total_credit']}")
    
    def test_02_get_unbalanced_journals(self):
        """Check for unbalanced journals"""
        response = self.session.get(f"{BASE_URL}/api/accounting/journals/unbalanced")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        print(f"✓ Unbalanced journals check: {data['total']} found")


class TestAkuntansiLedger:
    """AKUNTANSI - Buku Besar Tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "ocbgroupbjm@gmail.com",
            "password": "admin123"
        })
        token = response.json().get("token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_01_get_general_ledger(self):
        """Get general ledger"""
        response = self.session.get(f"{BASE_URL}/api/accounting/ledger")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        print(f"✓ General ledger: {data['total']} accounts with transactions")


class TestAkuntansiFinancialReports:
    """AKUNTANSI - Neraca, Laba Rugi, Trial Balance"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "ocbgroupbjm@gmail.com",
            "password": "admin123"
        })
        token = response.json().get("token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_01_trial_balance(self):
        """Neraca Saldo"""
        response = self.session.get(f"{BASE_URL}/api/accounting/trial-balance")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total_debit" in data
        assert "total_credit" in data
        assert "is_balanced" in data
        print(f"✓ Trial Balance - Debit: {data['total_debit']}, Credit: {data['total_credit']}, Balanced: {data['is_balanced']}")
    
    def test_02_balance_sheet(self):
        """Neraca"""
        response = self.session.get(f"{BASE_URL}/api/accounting/financial/balance-sheet")
        assert response.status_code == 200
        data = response.json()
        assert "assets" in data
        assert "liabilities" in data
        assert "equity" in data
        assert "total_assets" in data
        assert "is_balanced" in data
        print(f"✓ Balance Sheet - Assets: {data['total_assets']}, Equity: {data['total_equity']}, Balanced: {data['is_balanced']}")
    
    def test_03_income_statement(self):
        """Laba Rugi"""
        response = self.session.get(f"{BASE_URL}/api/accounting/financial/income-statement")
        assert response.status_code == 200
        data = response.json()
        assert "revenues" in data
        assert "expenses" in data
        assert "total_revenue" in data
        assert "total_expense" in data
        assert "net_income" in data
        print(f"✓ Income Statement - Revenue: {data['total_revenue']}, Expense: {data['total_expense']}, Net Income: {data['net_income']}")


class TestPersediaanStock:
    """PERSEDIAAN - Stock Tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "ocbgroupbjm@gmail.com",
            "password": "admin123"
        })
        token = response.json().get("token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_01_list_stock(self):
        """List stock"""
        response = self.session.get(f"{BASE_URL}/api/inventory/stock")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        print(f"✓ Found {data['total']} stock items")
    
    def test_02_low_stock_alerts(self):
        """Get low stock alerts"""
        response = self.session.get(f"{BASE_URL}/api/inventory/stock/low")
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Low stock alerts: {len(data)} items")


class TestPersediaanMovements:
    """PERSEDIAAN - Stock Movements"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "ocbgroupbjm@gmail.com",
            "password": "admin123"
        })
        token = response.json().get("token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_01_list_movements(self):
        """List stock movements"""
        response = self.session.get(f"{BASE_URL}/api/inventory/movements")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        print(f"✓ Found {data['total']} stock movements")


class TestPersediaanTransfers:
    """PERSEDIAAN - Transfer Stok"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "ocbgroupbjm@gmail.com",
            "password": "admin123"
        })
        token = response.json().get("token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_01_list_transfers(self):
        """List stock transfers"""
        response = self.session.get(f"{BASE_URL}/api/inventory/transfers")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        print(f"✓ Found {data['total']} transfers")


class TestLaporanSales:
    """LAPORAN - Penjualan"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "ocbgroupbjm@gmail.com",
            "password": "admin123"
        })
        token = response.json().get("token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_01_sales_report_daily(self):
        """Daily sales report"""
        response = self.session.get(
            f"{BASE_URL}/api/reports/sales?date_from=2026-01-01&date_to=2026-03-31&group_by=day"
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "totals" in data
        print(f"✓ Sales Report - Net Sales: {data['totals']['net_sales']}, Transactions: {data['totals']['transactions']}")
    
    def test_02_best_sellers(self):
        """Best sellers report"""
        response = self.session.get(
            f"{BASE_URL}/api/reports/best-sellers?date_from=2026-01-01&date_to=2026-03-31"
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        print(f"✓ Best Sellers: {data['total_items']} products")


class TestLaporanInventory:
    """LAPORAN - Persediaan"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "ocbgroupbjm@gmail.com",
            "password": "admin123"
        })
        token = response.json().get("token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_01_inventory_report(self):
        """Inventory report"""
        response = self.session.get(f"{BASE_URL}/api/reports/inventory")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "summary" in data
        print(f"✓ Inventory Report - Products: {data['summary']['total_products']}, Value: {data['summary']['total_stock_value']}")


class TestLaporanCash:
    """LAPORAN - Kas"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "ocbgroupbjm@gmail.com",
            "password": "admin123"
        })
        token = response.json().get("token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_01_cash_report(self):
        """Cash flow report"""
        response = self.session.get(
            f"{BASE_URL}/api/reports/cash?date_from=2026-01-01&date_to=2026-03-31"
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total_in" in data
        assert "total_out" in data
        print(f"✓ Cash Report - In: {data['total_in']}, Out: {data['total_out']}, Net: {data['net_flow']}")


class TestLaporanPiutangHutang:
    """LAPORAN - Piutang & Hutang"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "ocbgroupbjm@gmail.com",
            "password": "admin123"
        })
        token = response.json().get("token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_01_receivables_report(self):
        """Accounts receivable report"""
        response = self.session.get(f"{BASE_URL}/api/reports/receivables")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total_receivable" in data
        print(f"✓ Receivables Report - Total: {data['total_receivable']}")
    
    def test_02_payables_report(self):
        """Accounts payable report"""
        response = self.session.get(f"{BASE_URL}/api/reports/payables")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total_payable" in data
        print(f"✓ Payables Report - Total: {data['total_payable']}")


class TestMasterData:
    """Master Data CRUD - Categories, Units, Products"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "ocbgroupbjm@gmail.com",
            "password": "admin123"
        })
        token = response.json().get("token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_01_list_categories(self):
        """List categories"""
        response = self.session.get(f"{BASE_URL}/api/categories")
        assert response.status_code == 200
        print(f"✓ Categories API works")
    
    def test_02_list_units(self):
        """List units"""
        response = self.session.get(f"{BASE_URL}/api/units")
        assert response.status_code == 200
        print(f"✓ Units API works")
    
    def test_03_list_products(self):
        """List products"""
        response = self.session.get(f"{BASE_URL}/api/products")
        assert response.status_code == 200
        print(f"✓ Products API works")


class TestDashboard:
    """Dashboard API Tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "ocbgroupbjm@gmail.com",
            "password": "admin123"
        })
        token = response.json().get("token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_01_dashboard_summary(self):
        """Dashboard summary"""
        response = self.session.get(f"{BASE_URL}/api/dashboard/summary")
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Dashboard Summary works")
    
    def test_02_health_check(self):
        """Health check"""
        response = self.session.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print(f"✓ Health Check: {data['status']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
