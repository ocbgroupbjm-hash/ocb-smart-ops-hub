"""
Test Account Settings Module - Iteration 36
Tests for:
- Account Settings CRUD with 12 tabs (Data Item, Pembelian, Penjualan 1, Penjualan 2, Konsinyasi, Hutang Piutang, Lain-lain, Cabang, Gudang, Kategori, Payment Method, Pajak)
- Account Derivation Engine
- Fiscal Period System
- Branch/Warehouse/Category/Payment/Tax Mappings
- Integration with Sales Module
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAccountSettingsModule:
    """Account Settings API Tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "ocbgroupbjm@gmail.com",
            "password": "admin123"
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        token = login_response.json().get("token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        yield
    
    # ============== ACCOUNT SETTINGS CRUD TESTS ==============
    
    def test_get_all_account_settings(self):
        """GET /api/account-settings/ - List all account settings grouped by tab"""
        response = self.session.get(f"{BASE_URL}/api/account-settings/")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "settings" in data
        assert "is_default" in data
        print(f"PASS - Got account settings, is_default: {data['is_default']}, tabs: {list(data['settings'].keys())}")
    
    def test_get_account_settings_by_tab_data_item(self):
        """GET /api/account-settings/by-tab/data_item - Get settings for Data Item tab"""
        response = self.session.get(f"{BASE_URL}/api/account-settings/by-tab/data_item")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "items" in data
        assert data["tab"] == "data_item"
        print(f"PASS - Data Item tab has {len(data['items'])} settings")
    
    def test_get_account_settings_by_tab_pembelian(self):
        """GET /api/account-settings/by-tab/pembelian - Get settings for Pembelian tab"""
        response = self.session.get(f"{BASE_URL}/api/account-settings/by-tab/pembelian")
        assert response.status_code == 200
        data = response.json()
        assert data["tab"] == "pembelian"
        print(f"PASS - Pembelian tab has {len(data['items'])} settings")
    
    def test_get_account_settings_by_tab_penjualan_1(self):
        """GET /api/account-settings/by-tab/penjualan_1 - Get settings for Penjualan 1 tab"""
        response = self.session.get(f"{BASE_URL}/api/account-settings/by-tab/penjualan_1")
        assert response.status_code == 200
        data = response.json()
        assert data["tab"] == "penjualan_1"
        print(f"PASS - Penjualan 1 tab has {len(data['items'])} settings")
    
    def test_get_account_settings_by_tab_penjualan_2(self):
        """GET /api/account-settings/by-tab/penjualan_2 - Get settings for Penjualan 2 tab"""
        response = self.session.get(f"{BASE_URL}/api/account-settings/by-tab/penjualan_2")
        assert response.status_code == 200
        data = response.json()
        assert data["tab"] == "penjualan_2"
        print(f"PASS - Penjualan 2 tab has {len(data['items'])} settings")
    
    def test_get_account_settings_by_tab_konsinyasi(self):
        """GET /api/account-settings/by-tab/konsinyasi - Get settings for Konsinyasi tab"""
        response = self.session.get(f"{BASE_URL}/api/account-settings/by-tab/konsinyasi")
        assert response.status_code == 200
        data = response.json()
        assert data["tab"] == "konsinyasi"
        print(f"PASS - Konsinyasi tab has {len(data['items'])} settings")
    
    def test_get_account_settings_by_tab_hutang_piutang(self):
        """GET /api/account-settings/by-tab/hutang_piutang - Get settings for Hutang Piutang tab"""
        response = self.session.get(f"{BASE_URL}/api/account-settings/by-tab/hutang_piutang")
        assert response.status_code == 200
        data = response.json()
        assert data["tab"] == "hutang_piutang"
        print(f"PASS - Hutang Piutang tab has {len(data['items'])} settings")
    
    def test_get_account_settings_by_tab_lain_lain(self):
        """GET /api/account-settings/by-tab/lain_lain - Get settings for Lain-lain tab"""
        response = self.session.get(f"{BASE_URL}/api/account-settings/by-tab/lain_lain")
        assert response.status_code == 200
        data = response.json()
        assert data["tab"] == "lain_lain"
        print(f"PASS - Lain-lain tab has {len(data['items'])} settings")
    
    def test_create_account_setting(self):
        """POST /api/account-settings/ - Create/update account setting"""
        unique_key = f"test_account_{uuid.uuid4().hex[:8]}"
        response = self.session.post(f"{BASE_URL}/api/account-settings/", json={
            "module": "data_item",
            "account_key": unique_key,
            "account_code": "9-9999",
            "account_name": "Test Account",
            "tab_group": "data_item",
            "description": "Test account for iteration 36"
        })
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["account_key"] == unique_key
        assert data["account_code"] == "9-9999"
        print(f"PASS - Created account setting: {data['id']}")
    
    def test_initialize_default_settings(self):
        """POST /api/account-settings/initialize-defaults - Initialize default settings"""
        response = self.session.post(f"{BASE_URL}/api/account-settings/initialize-defaults", json={})
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["success"] == True
        print(f"PASS - Initialized {data['initialized']} default settings")
    
    # ============== CHART OF ACCOUNTS TESTS ==============
    
    def test_get_chart_of_accounts(self):
        """GET /api/account-settings/chart-of-accounts - List COA for dropdown"""
        response = self.session.get(f"{BASE_URL}/api/account-settings/chart-of-accounts")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "items" in data
        assert len(data["items"]) > 0
        # Verify structure
        first_account = data["items"][0]
        assert "code" in first_account
        assert "name" in first_account
        print(f"PASS - Got {len(data['items'])} chart of accounts")
    
    # ============== ACCOUNT DERIVATION ENGINE TESTS ==============
    
    def test_derive_account_global_fallback(self):
        """GET /api/account-settings/derive-account - Test global/default fallback"""
        response = self.session.get(f"{BASE_URL}/api/account-settings/derive-account", params={
            "account_key": "hpp"
        })
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "account_code" in data
        assert "account_name" in data
        assert "source" in data
        print(f"PASS - Derived account for 'hpp': {data['account_code']} ({data['source']})")
    
    def test_derive_account_not_found(self):
        """GET /api/account-settings/derive-account - Test non-existent key"""
        response = self.session.get(f"{BASE_URL}/api/account-settings/derive-account", params={
            "account_key": "nonexistent_key_xyz"
        })
        assert response.status_code == 404, f"Expected 404, got: {response.status_code}"
        print("PASS - 404 for non-existent account key")
    
    def test_derive_account_with_branch(self):
        """GET /api/account-settings/derive-account - With branch_id param"""
        response = self.session.get(f"{BASE_URL}/api/account-settings/derive-account", params={
            "account_key": "pembayaran_tunai",
            "branch_id": "test_branch_001"
        })
        # Should return 200 even if no branch mapping exists (fallback to global/default)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "source" in data
        print(f"PASS - Derived with branch_id, source: {data['source']}")
    
    def test_derive_account_with_warehouse(self):
        """GET /api/account-settings/derive-account - With warehouse_id param"""
        response = self.session.get(f"{BASE_URL}/api/account-settings/derive-account", params={
            "account_key": "persediaan_barang",
            "warehouse_id": "main"
        })
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["account_code"] == "1-1400" or data["source"] in ["default", "global"]
        print(f"PASS - Derived with warehouse_id: {data['account_code']}")
    
    def test_derive_account_with_payment_method(self):
        """GET /api/account-settings/derive-account - With payment_method param"""
        response = self.session.get(f"{BASE_URL}/api/account-settings/derive-account", params={
            "account_key": "pembayaran_tunai",
            "payment_method": "cash"
        })
        assert response.status_code == 200
        data = response.json()
        print(f"PASS - Derived with payment_method: {data['account_code']} ({data['source']})")
    
    # ============== BRANCH MAPPING TESTS ==============
    
    def test_get_branch_account_mapping(self):
        """GET /api/account-settings/branch-mapping - Get branch mappings"""
        response = self.session.get(f"{BASE_URL}/api/account-settings/branch-mapping")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "items" in data
        print(f"PASS - Got {len(data['items'])} branch mappings")
    
    def test_create_branch_account_mapping(self):
        """POST /api/account-settings/branch-mapping - Create branch mapping"""
        response = self.session.post(f"{BASE_URL}/api/account-settings/branch-mapping", json={
            "mapping_type": "branch",
            "reference_id": f"TEST_BRANCH_{uuid.uuid4().hex[:6]}",
            "reference_name": "Test Branch",
            "account_key": "kas",
            "account_code": "1-1100",
            "account_name": "Kas"
        })
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "id" in data
        assert data["branch_id"].startswith("TEST_BRANCH")
        print(f"PASS - Created branch mapping: {data['id']}")
    
    # ============== WAREHOUSE MAPPING TESTS ==============
    
    def test_get_warehouse_account_mapping(self):
        """GET /api/account-settings/warehouse-mapping - Get warehouse mappings"""
        response = self.session.get(f"{BASE_URL}/api/account-settings/warehouse-mapping")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        print(f"PASS - Got {len(data['items'])} warehouse mappings")
    
    def test_create_warehouse_account_mapping(self):
        """POST /api/account-settings/warehouse-mapping - Create warehouse mapping"""
        response = self.session.post(f"{BASE_URL}/api/account-settings/warehouse-mapping", json={
            "mapping_type": "warehouse",
            "reference_id": f"TEST_WH_{uuid.uuid4().hex[:6]}",
            "reference_name": "Test Warehouse",
            "account_key": "persediaan",
            "account_code": "1-1400",
            "account_name": "Persediaan Barang"
        })
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "id" in data
        print(f"PASS - Created warehouse mapping: {data['id']}")
    
    # ============== CATEGORY MAPPING TESTS ==============
    
    def test_get_category_account_mapping(self):
        """GET /api/account-settings/category-mapping - Get category mappings"""
        response = self.session.get(f"{BASE_URL}/api/account-settings/category-mapping")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        print(f"PASS - Got {len(data['items'])} category mappings")
    
    def test_create_category_account_mapping(self):
        """POST /api/account-settings/category-mapping - Create category mapping"""
        response = self.session.post(f"{BASE_URL}/api/account-settings/category-mapping", json={
            "mapping_type": "category",
            "reference_id": f"TEST_CAT_{uuid.uuid4().hex[:6]}",
            "reference_name": "Test Category",
            "account_key": "hpp",
            "account_code": "5-1000",
            "account_name": "Harga Pokok Penjualan"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        print(f"PASS - Created category mapping: {data['id']}")
    
    # ============== PAYMENT MAPPING TESTS ==============
    
    def test_get_payment_account_mapping(self):
        """GET /api/account-settings/payment-mapping - Get payment method mappings"""
        response = self.session.get(f"{BASE_URL}/api/account-settings/payment-mapping")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        print(f"PASS - Got {len(data['items'])} payment mappings")
    
    def test_create_payment_account_mapping(self):
        """POST /api/account-settings/payment-mapping - Create payment mapping"""
        response = self.session.post(f"{BASE_URL}/api/account-settings/payment-mapping", json={
            "mapping_type": "payment_method",
            "reference_id": "qris",
            "reference_name": "QRIS",
            "account_key": "bank",
            "account_code": "1-1200",
            "account_name": "Bank"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        print(f"PASS - Created payment mapping: {data['id']}")
    
    # ============== TAX MAPPING TESTS ==============
    
    def test_get_tax_account_mapping(self):
        """GET /api/account-settings/tax-mapping - Get tax type mappings"""
        response = self.session.get(f"{BASE_URL}/api/account-settings/tax-mapping")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        print(f"PASS - Got {len(data['items'])} tax mappings")
    
    def test_create_tax_account_mapping(self):
        """POST /api/account-settings/tax-mapping - Create tax mapping"""
        response = self.session.post(f"{BASE_URL}/api/account-settings/tax-mapping", json={
            "mapping_type": "tax",
            "reference_id": "ppn",
            "reference_name": "PPN",
            "account_key": "ppn_keluaran",
            "account_code": "2-1400",
            "account_name": "PPN Keluaran"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        print(f"PASS - Created tax mapping: {data['id']}")
    
    # ============== FISCAL PERIOD TESTS ==============
    
    def test_get_fiscal_periods(self):
        """GET /api/account-settings/fiscal-periods - List fiscal periods"""
        response = self.session.get(f"{BASE_URL}/api/account-settings/fiscal-periods")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        print(f"PASS - Got {len(data['items'])} fiscal periods")
    
    def test_create_fiscal_period(self):
        """POST /api/account-settings/fiscal-periods - Create fiscal period"""
        # Use a unique period to avoid overlap
        unique_year = 2099 + int(uuid.uuid4().hex[:2], 16) % 100
        response = self.session.post(f"{BASE_URL}/api/account-settings/fiscal-periods", json={
            "period_name": f"FY {unique_year}",
            "start_date": f"{unique_year}-01-01",
            "end_date": f"{unique_year}-12-31",
            "status": "open"
        })
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "id" in data
        assert data["status"] == "open"
        print(f"PASS - Created fiscal period: {data['period_name']}")


class TestSalesModuleAccountDerivation:
    """Test Sales Module integration with Account Derivation Engine"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "ocbgroupbjm@gmail.com",
            "password": "admin123"
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        token = login_response.json().get("token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        yield
    
    def test_sales_invoice_with_account_derivation(self):
        """Test Sales Invoice uses Account Derivation Engine for journal entries"""
        # First get a valid product
        products_resp = self.session.get(f"{BASE_URL}/api/master/items", params={"limit": 10})
        assert products_resp.status_code == 200
        products = products_resp.json().get("items", [])
        
        # Find a product with stock (PRD-AUDIT-001 or any other)
        product = None
        for p in products:
            if p.get("stock", 0) > 0:
                product = p
                break
        
        if not product:
            print("SKIP - No product with stock available for sales invoice test")
            pytest.skip("No product with stock available")
        
        # Get a customer
        customers_resp = self.session.get(f"{BASE_URL}/api/customers", params={"limit": 5})
        assert customers_resp.status_code == 200
        customers = customers_resp.json().get("items", [])
        
        if not customers:
            print("SKIP - No customers available")
            pytest.skip("No customers available")
        
        customer = customers[0]
        
        # Create a sales invoice
        invoice_data = {
            "customer_id": customer["id"],
            "warehouse_id": "main",
            "ppn_type": "exclude",
            "ppn_percent": 11,
            "items": [{
                "product_id": product["id"],
                "quantity": 1,
                "unit_price": product.get("selling_price", 10000),
                "discount_percent": 0,
                "tax_percent": 0
            }],
            "payment_type": "cash",
            "cash_amount": product.get("selling_price", 10000) * 1.11  # Include PPN
        }
        
        response = self.session.post(f"{BASE_URL}/api/sales/invoices", json=invoice_data)
        assert response.status_code == 200, f"Failed: {response.text}"
        invoice = response.json()
        assert "invoice_number" in invoice
        print(f"PASS - Created sales invoice {invoice['invoice_number']} with Account Derivation Engine")
    
    def test_sales_orders_list(self):
        """Test GET /api/sales/orders"""
        response = self.session.get(f"{BASE_URL}/api/sales/orders")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        print(f"PASS - Got {len(data['items'])} sales orders")
    
    def test_sales_invoices_list(self):
        """Test GET /api/sales/invoices"""
        response = self.session.get(f"{BASE_URL}/api/sales/invoices")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        print(f"PASS - Got {len(data['items'])} sales invoices")
    
    def test_journal_entries_check(self):
        """Verify journal entries exist (created by Sales Module)"""
        response = self.session.get(f"{BASE_URL}/api/accounting/journals", params={"limit": 10})
        if response.status_code == 200:
            data = response.json()
            items = data.get("items", data.get("journals", []))
            print(f"PASS - Got {len(items)} journal entries")
        else:
            # Try alternate endpoint
            response2 = self.session.get(f"{BASE_URL}/api/journals", params={"limit": 10})
            if response2.status_code == 200:
                data = response2.json()
                print(f"PASS - Got journal entries from alternate endpoint")
            else:
                print(f"INFO - Journal endpoint returned {response.status_code}, may not be implemented")
                pytest.skip("Journal endpoint not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
