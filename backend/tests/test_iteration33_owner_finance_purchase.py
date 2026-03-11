"""
OCB TITAN - Iteration 33 Tests
Testing:
1. Owner Dashboard APIs (KPI: Sales, Purchases, AR, AP, Deposits)
2. Finance Dashboard APIs (Revenue, COGS, Profit, Assets, Liabilities)
3. Purchase Enterprise Module APIs
"""
import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestOwnerDashboardAPIs:
    """Test APIs used by Owner Dashboard for KPI display"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "ocbgroupbjm@gmail.com",
            "password": "admin123"
        })
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        self.token = login_res.json().get("token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_01_pos_transactions_for_sales_kpi(self):
        """Test POS transactions API - used for Total Penjualan KPI"""
        res = requests.get(f"{BASE_URL}/api/pos/transactions?limit=500", headers=self.headers)
        assert res.status_code == 200, f"POS transactions failed: {res.text}"
        data = res.json()
        assert "items" in data or isinstance(data, list), "Expected items array"
        print(f"SUCCESS: POS transactions API - Found {len(data.get('items', data))} transactions")
    
    def test_02_purchase_orders_for_purchases_kpi(self):
        """Test Purchase orders API - used for Total Pembelian KPI"""
        res = requests.get(f"{BASE_URL}/api/purchase/orders?status=received&limit=200", headers=self.headers)
        assert res.status_code == 200, f"Purchase orders failed: {res.text}"
        data = res.json()
        assert "items" in data or isinstance(data, list), "Expected items array"
        print(f"SUCCESS: Purchase orders API - Found {len(data.get('items', data))} received POs")
    
    def test_03_ar_list_for_receivables_kpi(self):
        """Test AR list API - used for Piutang (AR) KPI"""
        res = requests.get(f"{BASE_URL}/api/ar/list?limit=500", headers=self.headers)
        assert res.status_code == 200, f"AR list failed: {res.text}"
        data = res.json()
        assert "items" in data or isinstance(data, list), "Expected items array"
        print(f"SUCCESS: AR list API - Found {len(data.get('items', data))} receivables")
    
    def test_04_ap_list_for_payables_kpi(self):
        """Test AP list API - used for Hutang (AP) KPI"""
        res = requests.get(f"{BASE_URL}/api/ap/list?limit=500", headers=self.headers)
        assert res.status_code == 200, f"AP list failed: {res.text}"
        data = res.json()
        assert "items" in data or isinstance(data, list), "Expected items array"
        print(f"SUCCESS: AP list API - Found {len(data.get('items', data))} payables")
    
    def test_05_deposits_for_setoran_kpi(self):
        """Test Deposits API - used for Setoran Harian KPI"""
        res = requests.get(f"{BASE_URL}/api/deposits?limit=200", headers=self.headers)
        assert res.status_code == 200, f"Deposits failed: {res.text}"
        data = res.json()
        assert "items" in data or isinstance(data, list), "Expected items array"
        print(f"SUCCESS: Deposits API - Found {len(data.get('items', data))} deposits")
    
    def test_06_inventory_low_stock(self):
        """Test Inventory API for low stock - used for Stok Rendah KPI"""
        res = requests.get(f"{BASE_URL}/api/inventory/stock?low_stock_only=true", headers=self.headers)
        assert res.status_code == 200, f"Inventory low stock failed: {res.text}"
        data = res.json()
        print(f"SUCCESS: Inventory low stock API - Found {len(data.get('items', data))} low stock items")
    
    def test_07_employees_for_stats(self):
        """Test Employees API - used for karyawan statistics"""
        res = requests.get(f"{BASE_URL}/api/erp/employees", headers=self.headers)
        assert res.status_code == 200, f"Employees failed: {res.text}"
        data = res.json()
        print(f"SUCCESS: Employees API working")
    
    def test_08_branches_for_performance(self):
        """Test Branches API - used for cabang performance"""
        res = requests.get(f"{BASE_URL}/api/branches", headers=self.headers)
        assert res.status_code == 200, f"Branches failed: {res.text}"
        data = res.json()
        assert isinstance(data, list), "Expected branches array"
        print(f"SUCCESS: Branches API - Found {len(data)} branches")


class TestFinanceDashboardAPIs:
    """Test APIs used by Finance Dashboard"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "ocbgroupbjm@gmail.com",
            "password": "admin123"
        })
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        self.token = login_res.json().get("token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_01_trial_balance_for_accounts(self):
        """Test Trial Balance API - used for Aset, Kewajiban, Ekuitas"""
        res = requests.get(f"{BASE_URL}/api/accounting/reports/trial-balance", headers=self.headers)
        assert res.status_code == 200, f"Trial balance failed: {res.text}"
        data = res.json()
        print(f"SUCCESS: Trial balance API - Response has {len(data.get('accounts', data))} accounts")
    
    def test_02_journals_for_recent_entries(self):
        """Test Journals API - used for jurnal terbaru"""
        res = requests.get(f"{BASE_URL}/api/accounting/journals?limit=20", headers=self.headers)
        assert res.status_code == 200, f"Journals failed: {res.text}"
        data = res.json()
        print(f"SUCCESS: Journals API - Found {len(data.get('items', data))} journal entries")
    
    def test_03_ar_for_piutang_summary(self):
        """Test AR API for Piutang Usaha summary"""
        res = requests.get(f"{BASE_URL}/api/ar/list?limit=500", headers=self.headers)
        assert res.status_code == 200, f"AR list failed: {res.text}"
        data = res.json()
        items = data.get('items', data)
        # Calculate totals
        total = sum(i.get('outstanding_amount', i.get('amount', 0)) for i in items if isinstance(i, dict))
        print(f"SUCCESS: AR API - Total AR: {total}")
    
    def test_04_ap_for_hutang_summary(self):
        """Test AP API for Hutang Usaha summary"""
        res = requests.get(f"{BASE_URL}/api/ap/list?limit=500", headers=self.headers)
        assert res.status_code == 200, f"AP list failed: {res.text}"
        data = res.json()
        items = data.get('items', data)
        # Calculate totals
        total = sum(i.get('amount', 0) - i.get('paid_amount', 0) for i in items if isinstance(i, dict))
        print(f"SUCCESS: AP API - Total AP: {total}")


class TestPurchaseEnterpriseAPIs:
    """Test Purchase Enterprise Module APIs"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "ocbgroupbjm@gmail.com",
            "password": "admin123"
        })
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        self.token = login_res.json().get("token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_01_list_purchase_orders(self):
        """Test list purchase orders with filters"""
        res = requests.get(f"{BASE_URL}/api/purchase/orders?limit=500", headers=self.headers)
        assert res.status_code == 200, f"List PO failed: {res.text}"
        data = res.json()
        items = data.get('items', data)
        print(f"SUCCESS: List PO - Found {len(items)} purchase orders")
        
        # Verify data structure
        if items and len(items) > 0:
            po = items[0]
            assert 'po_number' in po or 'id' in po, "PO should have po_number or id"
            print(f"  Sample PO: {po.get('po_number', po.get('id'))}")
    
    def test_02_suppliers_for_dropdown(self):
        """Test suppliers API for form dropdown"""
        res = requests.get(f"{BASE_URL}/api/suppliers", headers=self.headers)
        assert res.status_code == 200, f"Suppliers failed: {res.text}"
        data = res.json()
        items = data.get('items', data)
        print(f"SUCCESS: Suppliers API - Found {len(items)} suppliers")
        self.__class__.supplier_id = items[0]['id'] if items else None
    
    def test_03_products_for_item_search(self):
        """Test products API for item search"""
        res = requests.get(f"{BASE_URL}/api/products?limit=2000", headers=self.headers)
        assert res.status_code == 200, f"Products failed: {res.text}"
        data = res.json()
        items = data.get('items', data)
        print(f"SUCCESS: Products API - Found {len(items)} products")
        self.__class__.product_id = items[0]['id'] if items else None
    
    def test_04_warehouses_for_dropdown(self):
        """Test warehouses API for form dropdown"""
        res = requests.get(f"{BASE_URL}/api/master/warehouses", headers=self.headers)
        assert res.status_code == 200, f"Warehouses failed: {res.text}"
        data = res.json()
        print(f"SUCCESS: Warehouses API - Found {len(data)} warehouses")
    
    def test_05_branches_for_dropdown(self):
        """Test branches API for form dropdown"""
        res = requests.get(f"{BASE_URL}/api/branches", headers=self.headers)
        assert res.status_code == 200, f"Branches failed: {res.text}"
        data = res.json()
        print(f"SUCCESS: Branches API - Found {len(data)} branches")
        self.__class__.branch_id = data[0]['id'] if data else None
    
    def test_06_create_purchase_order(self):
        """Test create new purchase order"""
        # Get supplier and product first
        sup_res = requests.get(f"{BASE_URL}/api/suppliers", headers=self.headers)
        suppliers = sup_res.json().get('items', sup_res.json())
        prod_res = requests.get(f"{BASE_URL}/api/products?limit=10", headers=self.headers)
        products = prod_res.json().get('items', prod_res.json())
        
        if not suppliers or not products:
            pytest.skip("No suppliers or products available")
        
        payload = {
            "supplier_id": suppliers[0]['id'],
            "branch_id": None,
            "items": [{
                "product_id": products[0]['id'],
                "quantity": 5,
                "unit_cost": 100000,
                "discount_percent": 0
            }],
            "expected_date": datetime.now().strftime("%Y-%m-%d"),
            "notes": "Test PO from Iteration 33",
            "is_credit": True,
            "credit_due_days": 30
        }
        
        res = requests.post(f"{BASE_URL}/api/purchase/orders", json=payload, headers=self.headers)
        assert res.status_code == 200, f"Create PO failed: {res.text}"
        data = res.json()
        assert 'id' in data or 'po_number' in data, "Response should contain id or po_number"
        self.__class__.test_po_id = data.get('id')
        print(f"SUCCESS: Created PO - {data.get('po_number', data.get('id'))}")
    
    def test_07_get_purchase_order_detail(self):
        """Test get PO detail"""
        if not hasattr(self.__class__, 'test_po_id') or not self.__class__.test_po_id:
            pytest.skip("No test PO created")
        
        res = requests.get(f"{BASE_URL}/api/purchase/orders/{self.__class__.test_po_id}", headers=self.headers)
        assert res.status_code == 200, f"Get PO detail failed: {res.text}"
        data = res.json()
        assert 'items' in data, "PO should have items"
        print(f"SUCCESS: Get PO detail - {data.get('po_number')} with {len(data.get('items', []))} items")
    
    def test_08_price_history_api(self):
        """Test price history API"""
        res = requests.get(f"{BASE_URL}/api/purchase/price-history", headers=self.headers)
        assert res.status_code == 200, f"Price history failed: {res.text}"
        data = res.json()
        items = data.get('items', data)
        print(f"SUCCESS: Price history API - Found {len(items)} records")
    
    def test_09_filter_po_by_status(self):
        """Test filter PO by status"""
        for status in ['draft', 'ordered', 'received', 'cancelled']:
            res = requests.get(f"{BASE_URL}/api/purchase/orders?status={status}&limit=50", headers=self.headers)
            assert res.status_code == 200, f"Filter by {status} failed: {res.text}"
            data = res.json()
            items = data.get('items', data)
            print(f"  Filter by {status}: {len(items)} POs")
        print("SUCCESS: PO filtering by status working")
    
    def test_10_purchase_payments_api(self):
        """Test purchase payments API"""
        res = requests.get(f"{BASE_URL}/api/purchase/payments", headers=self.headers)
        assert res.status_code == 200, f"Payments failed: {res.text}"
        data = res.json()
        print(f"SUCCESS: Payments API - Found {len(data.get('items', data))} payments")
    
    def test_11_purchase_returns_api(self):
        """Test purchase returns API"""
        res = requests.get(f"{BASE_URL}/api/purchase/returns", headers=self.headers)
        assert res.status_code == 200, f"Returns failed: {res.text}"
        data = res.json()
        print(f"SUCCESS: Returns API - Found {len(data.get('items', data))} returns")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
