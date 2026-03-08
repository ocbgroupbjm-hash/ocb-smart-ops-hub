# OCB AI TITAN - Accounting, Backup, Serial, Assembly Test Suite
# Tests: Chart of Accounts CRUD, Journals, Financial Reports, Backup, Serial Numbers, Assembly Formulas

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAuth:
    """Authentication tests"""
    
    def test_login_with_owner_credentials(self):
        """Test login with owner credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "ocbgroupbjm@gmail.com",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        assert "token" in data, "No token in response"
        assert "user" in data, "No user data in response"
        assert data["user"]["role"] == "owner", f"Expected owner role, got {data['user']['role']}"


class TestChartOfAccounts:
    """Chart of Accounts CRUD tests"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "ocbgroupbjm@gmail.com",
            "password": "admin123"
        })
        return response.json().get("token")
    
    def test_list_accounts(self, auth_token):
        """List all chart of accounts"""
        response = requests.get(
            f"{BASE_URL}/api/accounting/accounts",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 0
        print(f"Total accounts: {data['total']}")
    
    def test_create_account(self, auth_token):
        """Create a new account"""
        test_code = f"TEST-{uuid.uuid4().hex[:6]}"
        payload = {
            "code": test_code,
            "name": f"TEST Account {test_code}",
            "category": "asset",
            "parent_id": "",
            "account_type": "detail",
            "is_cash": False,
            "is_active": True,
            "description": "Test account for pytest",
            "normal_balance": "debit"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/accounting/accounts",
            headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
            json=payload
        )
        assert response.status_code == 200, f"Create failed: {response.text}"
        
        data = response.json()
        assert "id" in data
        assert "message" in data
        
        # Cleanup - delete the test account
        requests.delete(
            f"{BASE_URL}/api/accounting/accounts/{data['id']}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        print(f"Created and deleted test account: {test_code}")
    
    def test_filter_accounts_by_category(self, auth_token):
        """Filter accounts by category"""
        response = requests.get(
            f"{BASE_URL}/api/accounting/accounts?category=asset",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        # Verify all returned items are assets
        for item in data.get("items", []):
            assert item.get("category") == "asset"


class TestJournalEntries:
    """Journal Entries tests"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "ocbgroupbjm@gmail.com",
            "password": "admin123"
        })
        return response.json().get("token")
    
    def test_list_journals(self, auth_token):
        """List all journal entries"""
        response = requests.get(
            f"{BASE_URL}/api/accounting/journals",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "total_debit" in data
        assert "total_credit" in data
        print(f"Total journals: {data['total']}, Debit: {data['total_debit']}, Credit: {data['total_credit']}")


class TestFinancialReports:
    """Financial Reports tests - Trial Balance, Balance Sheet, Income Statement"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "ocbgroupbjm@gmail.com",
            "password": "admin123"
        })
        return response.json().get("token")
    
    def test_trial_balance(self, auth_token):
        """Get Trial Balance report"""
        response = requests.get(
            f"{BASE_URL}/api/accounting/trial-balance",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert "total_debit" in data
        assert "total_credit" in data
        assert "is_balanced" in data
        print(f"Trial Balance: {len(data['items'])} items, Balanced: {data['is_balanced']}")
    
    def test_balance_sheet(self, auth_token):
        """Get Balance Sheet (Neraca) report"""
        response = requests.get(
            f"{BASE_URL}/api/accounting/financial/balance-sheet",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "assets" in data
        assert "liabilities" in data
        assert "equity" in data
        assert "total_assets" in data
        assert "is_balanced" in data
        print(f"Balance Sheet: Assets={len(data['assets'])}, Liabilities={len(data['liabilities'])}, Equity={len(data['equity'])}")
    
    def test_income_statement(self, auth_token):
        """Get Income Statement (Laba Rugi) report"""
        response = requests.get(
            f"{BASE_URL}/api/accounting/financial/income-statement",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "revenues" in data
        assert "expenses" in data
        assert "total_revenue" in data
        assert "total_expense" in data
        assert "net_income" in data
        print(f"Income Statement: Net Income = {data['net_income']}")


class TestReportsModule:
    """Reports page API tests - 9 report types"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "ocbgroupbjm@gmail.com",
            "password": "admin123"
        })
        return response.json().get("token")
    
    def test_sales_report(self, auth_token):
        """Test sales report (Penjualan)"""
        response = requests.get(
            f"{BASE_URL}/api/reports/sales?date_from=2025-01-01&date_to=2026-01-31&group_by=day",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "data" in data
        assert "totals" in data
        print(f"Sales Report: {len(data['data'])} records")
    
    def test_product_performance_report(self, auth_token):
        """Test product performance report (Produk)"""
        response = requests.get(
            f"{BASE_URL}/api/reports/product-performance?date_from=2025-01-01&date_to=2026-01-31",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "data" in data
        assert "totals" in data
        print(f"Product Performance: {len(data['data'])} products")
    
    def test_best_sellers_report(self, auth_token):
        """Test best sellers report (Terlaris)"""
        response = requests.get(
            f"{BASE_URL}/api/reports/best-sellers?date_from=2025-01-01&date_to=2026-01-31",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        print(f"Best Sellers: {len(data['items'])} items")
    
    def test_inventory_report(self, auth_token):
        """Test inventory report (Stok)"""
        response = requests.get(
            f"{BASE_URL}/api/reports/inventory",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "data" in data
        assert "summary" in data
        print(f"Inventory Report: {len(data['data'])} products")
    
    def test_branch_comparison_report(self, auth_token):
        """Test branch comparison report (Cabang)"""
        response = requests.get(
            f"{BASE_URL}/api/reports/branch-comparison?date_from=2025-01-01&date_to=2026-01-31",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "branches" in data
        assert "totals" in data
        print(f"Branch Comparison: {len(data['branches'])} branches")
    
    def test_cashier_report(self, auth_token):
        """Test cashier report (Kasir)"""
        response = requests.get(
            f"{BASE_URL}/api/reports/cashiers?date_from=2025-01-01&date_to=2026-01-31",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        print(f"Cashier Report: {len(data['items'])} cashiers")
    
    def test_customer_analysis_report(self, auth_token):
        """Test customer analysis report (Pelanggan)"""
        response = requests.get(
            f"{BASE_URL}/api/reports/customer-analysis",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "total_customers" in data
        assert "segments" in data
        print(f"Customer Analysis: {data['total_customers']} total customers")
    
    def test_payables_report(self, auth_token):
        """Test payables report (Hutang)"""
        response = requests.get(
            f"{BASE_URL}/api/reports/payables",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert "total_payable" in data
        print(f"Payables Report: {len(data['items'])} items, Total: {data['total_payable']}")
    
    def test_receivables_report(self, auth_token):
        """Test receivables report (Piutang)"""
        response = requests.get(
            f"{BASE_URL}/api/reports/receivables",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert "total_receivable" in data
        print(f"Receivables Report: {len(data['items'])} items, Total: {data['total_receivable']}")


class TestBackupModule:
    """Backup & Restore tests"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "ocbgroupbjm@gmail.com",
            "password": "admin123"
        })
        return response.json().get("token")
    
    def test_list_backups(self, auth_token):
        """List all backups"""
        response = requests.get(
            f"{BASE_URL}/api/backup/list",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "backups" in data
        print(f"Backups found: {len(data['backups'])}")
    
    def test_create_backup(self, auth_token):
        """Create a new backup"""
        response = requests.post(
            f"{BASE_URL}/api/backup/create",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "id" in data
        assert "name" in data
        assert "message" in data
        print(f"Backup created: {data['name']}, Records: {data.get('total_records', 0)}")
        
        # Note: Not deleting the backup to preserve data integrity


class TestSerialNumberModule:
    """Serial Number tracking tests"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "ocbgroupbjm@gmail.com",
            "password": "admin123"
        })
        return response.json().get("token")
    
    def test_list_serial_numbers(self, auth_token):
        """List all serial numbers"""
        response = requests.get(
            f"{BASE_URL}/api/serial/list",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert "total" in data
        print(f"Serial numbers found: {data['total']}")
        
        # Verify serial structure if any exist
        if data['items']:
            serial = data['items'][0]
            assert "serial" in serial
            assert "status" in serial


class TestProductAssemblyModule:
    """Product Assembly (Rakitan Produk) tests"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "ocbgroupbjm@gmail.com",
            "password": "admin123"
        })
        return response.json().get("token")
    
    def test_list_assembly_formulas(self, auth_token):
        """List all assembly formulas"""
        response = requests.get(
            f"{BASE_URL}/api/assembly/formulas",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "formulas" in data
        assert "total" in data
        print(f"Assembly formulas found: {data['total']}")
        
        # Verify formula structure if any exist
        if data['formulas']:
            formula = data['formulas'][0]
            assert "name" in formula
            assert "result_product_id" in formula
            assert "components" in formula
    
    def test_list_assembly_transactions(self, auth_token):
        """List assembly transactions history"""
        response = requests.get(
            f"{BASE_URL}/api/assembly/transactions",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "transactions" in data
        assert "total" in data
        print(f"Assembly transactions: {data['total']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
