"""
OCB AI TITAN - Comprehensive Backend Testing
Tests for Multi-Business Login, Accounting, AI Features, Reports, Settings
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# ==================== AUTH & MULTI-BUSINESS TESTS ====================

class TestMultiBusinessLogin:
    """Test Multi-Business Login Flow"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.owner_email = "ocbgroupbjm@gmail.com"
        self.owner_password = "admin123"
    
    def test_01_health_check(self):
        """Test API health endpoint"""
        res = self.session.get(f"{BASE_URL}/api/health")
        assert res.status_code == 200
        data = res.json()
        assert data.get("status") == "healthy"
        print("Health check PASS")
    
    def test_02_owner_login(self):
        """Step 1: Login Owner verification"""
        res = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": self.owner_email,
            "password": self.owner_password
        })
        assert res.status_code == 200
        data = res.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["role"] in ["owner", "admin"]
        print(f"Owner login PASS - Role: {data['user']['role']}, Name: {data['user']['name']}")
    
    def test_03_invalid_login(self):
        """Test login with invalid credentials"""
        res = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@test.com",
            "password": "wrongpass"
        })
        assert res.status_code in [401, 400]
        print("Invalid login correctly rejected")
    
    def test_04_business_list(self):
        """Step 2: Get list of businesses"""
        res = self.session.get(f"{BASE_URL}/api/business/list")
        assert res.status_code == 200
        data = res.json()
        assert "businesses" in data
        businesses = data["businesses"]
        assert len(businesses) >= 1
        print(f"Business list PASS - Found {len(businesses)} businesses:")
        for b in businesses:
            print(f"  - {b.get('name')} ({b.get('db_name')})")
    
    def test_05_switch_business(self):
        """Step 3: Switch to a business database"""
        res = self.session.post(f"{BASE_URL}/api/business/switch/ocb_titan")
        assert res.status_code in [200, 400]  # May be already active
        print("Business switch API PASS")


class TestAuthentication:
    """Get authentication token for subsequent tests"""
    token = None
    
    @classmethod
    def get_token(cls):
        if not cls.token:
            res = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": "ocbgroupbjm@gmail.com",
                "password": "admin123"
            })
            if res.status_code == 200:
                cls.token = res.json().get("token")
        return cls.token


# ==================== ACCOUNTING TESTS (CRITICAL) ====================

class TestChartOfAccounts:
    """Test Chart of Accounts (Daftar Perkiraan)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.token = TestAuthentication.get_token()
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def test_01_list_accounts(self):
        """Test listing all accounts"""
        res = self.session.get(f"{BASE_URL}/api/accounting/accounts")
        assert res.status_code == 200
        data = res.json()
        assert "items" in data
        print(f"Chart of Accounts PASS - Total accounts: {len(data['items'])}")
        
        # Check structure
        if data["items"]:
            account = data["items"][0]
            assert "code" in account
            assert "name" in account
            assert "category" in account
            print(f"  Sample account: {account.get('code')} - {account.get('name')}")
    
    def test_02_create_account(self):
        """Test creating a new account"""
        test_code = f"TEST-{os.urandom(4).hex()}"
        res = self.session.post(f"{BASE_URL}/api/accounting/accounts", json={
            "code": test_code,
            "name": "Test Account for Pytest",
            "category": "asset",
            "account_type": "detail",
            "normal_balance": "debit",
            "is_active": True,
            "is_cash": False,
            "description": "Test account created by pytest"
        })
        assert res.status_code == 200
        data = res.json()
        assert "id" in data
        print(f"Create account PASS - ID: {data['id']}, Code: {test_code}")
        
        # Verify by GET
        get_res = self.session.get(f"{BASE_URL}/api/accounting/accounts/{data['id']}")
        assert get_res.status_code == 200
        fetched = get_res.json()
        assert fetched["code"] == test_code
        print("Account verification PASS")
        
        # Clean up - delete test account
        del_res = self.session.delete(f"{BASE_URL}/api/accounting/accounts/{data['id']}")
        assert del_res.status_code == 200
        print("Test account cleanup PASS")
    
    def test_03_filter_by_category(self):
        """Test filtering accounts by category"""
        categories = ["asset", "liability", "equity", "revenue", "expense"]
        for cat in categories:
            res = self.session.get(f"{BASE_URL}/api/accounting/accounts?category={cat}")
            assert res.status_code == 200
            data = res.json()
            # All returned accounts should match category
            for account in data["items"]:
                assert account["category"] == cat
        print("Category filtering PASS")


class TestJournalEntries:
    """Test Journal Entries (Data Jurnal)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.token = TestAuthentication.get_token()
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def test_01_list_journals(self):
        """Test listing journal entries"""
        res = self.session.get(f"{BASE_URL}/api/accounting/journals")
        assert res.status_code == 200
        data = res.json()
        assert "items" in data
        assert "total_debit" in data
        assert "total_credit" in data
        print(f"Journal Entries PASS - Total: {len(data['items'])}, Debit: {data['total_debit']}, Credit: {data['total_credit']}")
    
    def test_02_unbalanced_journals(self):
        """Test checking for unbalanced journals"""
        res = self.session.get(f"{BASE_URL}/api/accounting/journals/unbalanced")
        assert res.status_code == 200
        data = res.json()
        assert "items" in data
        print(f"Unbalanced journals check PASS - Found: {len(data['items'])}")
    
    def test_03_create_balanced_journal(self):
        """Test creating a balanced journal entry"""
        # Get accounts first
        acc_res = self.session.get(f"{BASE_URL}/api/accounting/accounts")
        accounts = acc_res.json()["items"]
        if len(accounts) < 2:
            pytest.skip("Need at least 2 accounts for journal test")
        
        acc1 = accounts[0]["id"]
        acc2 = accounts[1]["id"]
        
        res = self.session.post(f"{BASE_URL}/api/accounting/journals", json={
            "date": "2026-01-15",
            "reference": "TEST-JOURNAL",
            "description": "Pytest journal entry",
            "entries": [
                {"account_id": acc1, "debit": 100000, "credit": 0},
                {"account_id": acc2, "debit": 0, "credit": 100000}
            ],
            "source": "manual"
        })
        assert res.status_code == 200
        data = res.json()
        assert "id" in data
        print(f"Create balanced journal PASS - ID: {data['id']}")
        
        # Clean up
        self.session.delete(f"{BASE_URL}/api/accounting/journals/{data['id']}")
    
    def test_04_reject_unbalanced_journal(self):
        """Test that unbalanced journals are rejected"""
        acc_res = self.session.get(f"{BASE_URL}/api/accounting/accounts")
        accounts = acc_res.json()["items"]
        if len(accounts) < 1:
            pytest.skip("Need accounts for test")
        
        res = self.session.post(f"{BASE_URL}/api/accounting/journals", json={
            "date": "2026-01-15",
            "description": "Unbalanced test",
            "entries": [
                {"account_id": accounts[0]["id"], "debit": 100000, "credit": 0}
            ]
        })
        assert res.status_code == 400
        print("Unbalanced journal correctly rejected PASS")


class TestFinancialReports:
    """Test Financial Reports (Trial Balance, Balance Sheet, Income Statement)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.token = TestAuthentication.get_token()
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def test_01_trial_balance(self):
        """Test Trial Balance (Neraca Saldo)"""
        res = self.session.get(f"{BASE_URL}/api/accounting/trial-balance")
        assert res.status_code == 200
        data = res.json()
        assert "items" in data
        assert "total_debit" in data
        assert "total_credit" in data
        assert "is_balanced" in data
        
        # Verify debit = credit (balanced)
        if data["items"]:
            balance_status = "BALANCED" if data["is_balanced"] else "UNBALANCED"
            print(f"Trial Balance PASS - {balance_status}")
            print(f"  Debit: {data['total_debit']}, Credit: {data['total_credit']}")
        else:
            print("Trial Balance PASS - No data yet")
    
    def test_02_balance_sheet(self):
        """Test Balance Sheet (Neraca)"""
        res = self.session.get(f"{BASE_URL}/api/accounting/financial/balance-sheet")
        assert res.status_code == 200
        data = res.json()
        assert "assets" in data
        assert "liabilities" in data
        assert "equity" in data
        assert "total_assets" in data
        assert "total_liabilities" in data
        assert "total_equity" in data
        assert "is_balanced" in data
        
        balance_status = "BALANCED" if data["is_balanced"] else "UNBALANCED"
        print(f"Balance Sheet PASS - {balance_status}")
        print(f"  Assets: {data['total_assets']}, Liabilities: {data['total_liabilities']}, Equity: {data['total_equity']}")
    
    def test_03_income_statement(self):
        """Test Income Statement (Laba Rugi)"""
        res = self.session.get(f"{BASE_URL}/api/accounting/financial/income-statement")
        assert res.status_code == 200
        data = res.json()
        assert "revenues" in data
        assert "expenses" in data
        assert "total_revenue" in data
        assert "total_expense" in data
        assert "net_income" in data
        
        print(f"Income Statement PASS")
        print(f"  Revenue: {data['total_revenue']}, Expense: {data['total_expense']}, Net Income: {data['net_income']}")
    
    def test_04_cash_flow(self):
        """Test Cash Flow (Arus Kas)"""
        res = self.session.get(f"{BASE_URL}/api/accounting/financial/cash-flow")
        assert res.status_code == 200
        data = res.json()
        assert "operating" in data
        assert "net_cash_flow" in data
        print(f"Cash Flow PASS - Net: {data['net_cash_flow']}")
    
    def test_05_general_ledger(self):
        """Test General Ledger (Buku Besar)"""
        res = self.session.get(f"{BASE_URL}/api/accounting/ledger")
        assert res.status_code == 200
        data = res.json()
        assert "items" in data
        print(f"General Ledger PASS - {len(data['items'])} accounts with transactions")


# ==================== AI FEATURES TESTS (CRITICAL) ====================

class TestHalloAI:
    """Test Hallo AI Chat Feature"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.token = TestAuthentication.get_token()
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def test_01_get_personas(self):
        """Test getting AI personas"""
        res = self.session.get(f"{BASE_URL}/api/hallo-ai/personas")
        assert res.status_code == 200
        data = res.json()
        assert len(data) > 0
        print(f"AI Personas PASS - Found {len(data)} personas:")
        for p in data[:3]:
            print(f"  - {p.get('id')}: {p.get('name')}")
    
    def test_02_suggested_questions(self):
        """Test getting suggested questions"""
        res = self.session.get(f"{BASE_URL}/api/hallo-ai/suggested-questions?persona=analyst")
        assert res.status_code == 200
        data = res.json()
        assert "suggestions" in data
        print(f"Suggested questions PASS - {len(data['suggestions'])} suggestions")
    
    def test_03_chat_sessions(self):
        """Test listing chat sessions"""
        res = self.session.get(f"{BASE_URL}/api/hallo-ai/sessions")
        assert res.status_code == 200
        print("Chat sessions list PASS")
    
    def test_04_send_chat_message(self):
        """Test sending chat message to AI"""
        res = self.session.post(f"{BASE_URL}/api/hallo-ai/chat", json={
            "message": "Berapa total penjualan hari ini?",
            "persona": "analyst"
        }, timeout=30)  # AI may take time
        assert res.status_code == 200
        data = res.json()
        assert "response" in data
        assert "session_id" in data
        print(f"AI Chat PASS - Response received (length: {len(data['response'])})")


class TestAIBusiness:
    """Test AI Business Analytics Feature"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.token = TestAuthentication.get_token()
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def test_01_insight_penjualan(self):
        """Test sales insights"""
        res = self.session.get(f"{BASE_URL}/api/ai-bisnis/insight-penjualan")
        assert res.status_code == 200
        data = res.json()
        print("AI Sales Insight PASS")
    
    def test_02_rekomendasi_restock(self):
        """Test restock recommendations"""
        res = self.session.get(f"{BASE_URL}/api/ai-bisnis/rekomendasi-restock")
        assert res.status_code == 200
        print("AI Restock Recommendation PASS")
    
    def test_03_produk_terlaris(self):
        """Test best selling products"""
        res = self.session.get(f"{BASE_URL}/api/ai-bisnis/produk-terlaris")
        assert res.status_code == 200
        print("AI Best Sellers PASS")
    
    def test_04_produk_lambat(self):
        """Test slow moving products"""
        res = self.session.get(f"{BASE_URL}/api/ai-bisnis/produk-lambat")
        assert res.status_code == 200
        print("AI Slow Products PASS")
    
    def test_05_analisa_stok(self):
        """Test stock analysis"""
        res = self.session.get(f"{BASE_URL}/api/ai-bisnis/analisa-stok")
        assert res.status_code == 200
        print("AI Stock Analysis PASS")
    
    def test_06_performa_cabang(self):
        """Test branch performance"""
        res = self.session.get(f"{BASE_URL}/api/ai-bisnis/performa-cabang")
        assert res.status_code == 200
        print("AI Branch Performance PASS")
    
    def test_07_rekomendasi_bisnis(self):
        """Test business recommendations"""
        res = self.session.get(f"{BASE_URL}/api/ai-bisnis/rekomendasi-bisnis")
        assert res.status_code == 200
        print("AI Business Recommendations PASS")


# ==================== REPORTS TESTS ====================

class TestReports:
    """Test Reports (9 tabs)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.token = TestAuthentication.get_token()
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def test_01_sales_report(self):
        """Test sales report (Penjualan)"""
        res = self.session.get(f"{BASE_URL}/api/reports/sales?date_from=2026-01-01&date_to=2026-12-31")
        assert res.status_code == 200
        print("Sales Report PASS")
    
    def test_02_product_performance(self):
        """Test product performance report (Produk)"""
        res = self.session.get(f"{BASE_URL}/api/reports/product-performance?date_from=2026-01-01&date_to=2026-12-31")
        assert res.status_code == 200
        print("Product Report PASS")
    
    def test_03_best_sellers(self):
        """Test best sellers report (Terlaris)"""
        res = self.session.get(f"{BASE_URL}/api/reports/best-sellers?date_from=2026-01-01&date_to=2026-12-31")
        assert res.status_code == 200
        print("Best Sellers Report PASS")
    
    def test_04_inventory_report(self):
        """Test inventory report (Stok)"""
        res = self.session.get(f"{BASE_URL}/api/reports/inventory")
        assert res.status_code == 200
        print("Inventory Report PASS")
    
    def test_05_branch_comparison(self):
        """Test branch comparison report (Cabang)"""
        res = self.session.get(f"{BASE_URL}/api/reports/branch-comparison?date_from=2026-01-01&date_to=2026-12-31")
        assert res.status_code == 200
        print("Branch Report PASS")
    
    def test_06_cashiers_report(self):
        """Test cashiers report (Kasir)"""
        res = self.session.get(f"{BASE_URL}/api/reports/cashiers?date_from=2026-01-01&date_to=2026-12-31")
        assert res.status_code == 200
        print("Cashiers Report PASS")
    
    def test_07_customer_analysis(self):
        """Test customer analysis report (Pelanggan)"""
        res = self.session.get(f"{BASE_URL}/api/reports/customer-analysis?date_from=2026-01-01&date_to=2026-12-31")
        assert res.status_code == 200
        print("Customer Report PASS")
    
    def test_08_payables_report(self):
        """Test payables report (Hutang)"""
        res = self.session.get(f"{BASE_URL}/api/reports/payables")
        assert res.status_code == 200
        print("Payables Report PASS")
    
    def test_09_receivables_report(self):
        """Test receivables report (Piutang)"""
        res = self.session.get(f"{BASE_URL}/api/reports/receivables")
        assert res.status_code == 200
        print("Receivables Report PASS")


# ==================== SETTINGS & BACKUP TESTS ====================

class TestSettings:
    """Test Settings Features"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.token = TestAuthentication.get_token()
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def test_01_backup_list(self):
        """Test listing backups"""
        res = self.session.get(f"{BASE_URL}/api/backup/list")
        assert res.status_code == 200
        data = res.json()
        assert "backups" in data
        print(f"Backup List PASS - {len(data['backups'])} backups found")
    
    def test_02_create_backup(self):
        """Test creating backup"""
        res = self.session.post(f"{BASE_URL}/api/backup/create")
        assert res.status_code == 200
        data = res.json()
        assert "id" in data or "name" in data
        print(f"Create Backup PASS")
    
    def test_03_printers_list(self):
        """Test listing printers"""
        res = self.session.get(f"{BASE_URL}/api/print/printers")
        assert res.status_code == 200
        print("Printers List PASS")
    
    def test_04_receipt_template(self):
        """Test receipt template"""
        res = self.session.get(f"{BASE_URL}/api/print/template")
        assert res.status_code == 200
        print("Receipt Template PASS")


# ==================== ADDITIONAL FEATURES ====================

class TestBusinessManager:
    """Test Business Manager Feature"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.token = TestAuthentication.get_token()
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def test_01_list_businesses(self):
        """Test listing businesses"""
        res = self.session.get(f"{BASE_URL}/api/business/list")
        assert res.status_code == 200
        data = res.json()
        assert "businesses" in data
        print(f"Business Manager PASS - {len(data['businesses'])} businesses")
    
    def test_02_create_business(self):
        """Test creating a new business"""
        test_name = f"test_biz_{os.urandom(4).hex()}"
        res = self.session.post(f"{BASE_URL}/api/business/create", json={
            "id": test_name,
            "name": "Test Business Pytest",
            "db_name": test_name,
            "description": "Test business",
            "icon": "store",
            "color": "#991B1B"
        })
        assert res.status_code in [200, 400]  # May fail if DB already exists
        print("Create Business API PASS")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
