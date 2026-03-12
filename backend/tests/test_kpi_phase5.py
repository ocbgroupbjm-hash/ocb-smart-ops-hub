"""
OCB TITAN ERP - Phase 5 KPI System Tests
Testing KPI endpoints for branch, sales, inventory, and finance performance
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = "https://smart-ops-hub-6.preview.emergentagent.com"

# Test credentials
TEST_EMAIL = "ocbgroupbjm@gmail.com"
TEST_PASSWORD = "admin123"


class TestKPIDashboard:
    """KPI Dashboard endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_kpi_dashboard_returns_8_cards(self):
        """Test KPI dashboard returns 8 KPI cards with correct structure"""
        response = requests.get(
            f"{BASE_URL}/api/kpi/dashboard?period=month",
            headers=self.headers
        )
        assert response.status_code == 200, f"Dashboard API failed: {response.text}"
        data = response.json()
        
        # Verify period
        assert "period" in data
        assert data["period"]["type"] == "month"
        assert "start" in data["period"]
        assert "end" in data["period"]
        
        # Verify 8 KPI cards
        assert "kpi_cards" in data
        assert len(data["kpi_cards"]) == 8, f"Expected 8 KPI cards, got {len(data['kpi_cards'])}"
        
        # Verify expected card titles
        card_titles = [card["title"] for card in data["kpi_cards"]]
        expected_titles = [
            "Total Sales", "Target Achievement", "Active Branches", "Active Salesmen",
            "Low Stock Items", "Total AR", "Total AP", "Net Position"
        ]
        for title in expected_titles:
            assert title in card_titles, f"Missing KPI card: {title}"
        
        # Verify each card has required fields
        for card in data["kpi_cards"]:
            assert "title" in card
            assert "value" in card
            assert "format" in card
            assert "category" in card
    
    def test_kpi_dashboard_periods(self):
        """Test KPI dashboard with different period values"""
        periods = ["today", "week", "month", "quarter", "year"]
        
        for period in periods:
            response = requests.get(
                f"{BASE_URL}/api/kpi/dashboard?period={period}",
                headers=self.headers
            )
            assert response.status_code == 200, f"Dashboard API failed for period {period}: {response.text}"
            data = response.json()
            assert data["period"]["type"] == period


class TestKPIBranchPerformance:
    """KPI Branch Performance endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_branch_overview_returns_summary(self):
        """Test branch overview returns summary with all required fields"""
        response = requests.get(
            f"{BASE_URL}/api/kpi/branch/overview?period=month",
            headers=self.headers
        )
        assert response.status_code == 200, f"Branch Overview API failed: {response.text}"
        data = response.json()
        
        # Verify summary fields
        assert "summary" in data
        summary = data["summary"]
        assert "total_branches" in summary
        assert "total_sales" in summary
        assert "total_target" in summary
        assert "overall_achievement" in summary
        assert "achieved_count" in summary
        assert "on_track_count" in summary
        assert "behind_count" in summary
        
        # Verify branches array
        assert "branches" in data
        assert isinstance(data["branches"], list)
    
    def test_branch_overview_returns_branch_kpis(self):
        """Test branch overview returns individual branch KPIs"""
        response = requests.get(
            f"{BASE_URL}/api/kpi/branch/overview?period=month",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        if len(data["branches"]) > 0:
            branch = data["branches"][0]
            # Verify branch KPI structure
            assert "branch_id" in branch
            assert "branch_name" in branch
            assert "sales" in branch
            assert "total" in branch["sales"]
            assert "invoice" in branch["sales"]
            assert "pos" in branch["sales"]
            assert "transaction_count" in branch["sales"]
            
            assert "target" in branch
            assert "value" in branch["target"]
            assert "achievement_percent" in branch["target"]
            assert "gap" in branch["target"]
            
            assert "cash_control" in branch
            assert "status" in branch
            assert branch["status"] in ["achieved", "on_track", "behind"]


class TestKPISalesPerformance:
    """KPI Sales Performance endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_sales_overview_returns_ranking(self):
        """Test sales overview returns salesman ranking"""
        response = requests.get(
            f"{BASE_URL}/api/kpi/sales/overview?period=month",
            headers=self.headers
        )
        assert response.status_code == 200, f"Sales Overview API failed: {response.text}"
        data = response.json()
        
        # Verify summary
        assert "summary" in data
        summary = data["summary"]
        assert "total_salesmen" in summary
        assert "total_sales" in summary
        assert "total_target" in summary
        assert "total_commission" in summary
        assert "achieved_count" in summary
        assert "behind_count" in summary
        
        # Verify ranking
        assert "ranking" in data
        assert isinstance(data["ranking"], list)
    
    def test_sales_ranking_has_correct_fields(self):
        """Test sales ranking items have all required fields"""
        response = requests.get(
            f"{BASE_URL}/api/kpi/sales/overview?period=month",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        if len(data["ranking"]) > 0:
            salesman = data["ranking"][0]
            assert "salesman_id" in salesman
            assert "salesman_name" in salesman
            assert "actual_sales" in salesman
            assert "target_value" in salesman
            assert "achievement_percent" in salesman
            assert "commission_generated" in salesman
            assert "rank" in salesman
            assert "status" in salesman


class TestKPIInventoryPerformance:
    """KPI Inventory Performance endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_inventory_overview_returns_summary(self):
        """Test inventory overview returns correct summary structure"""
        response = requests.get(
            f"{BASE_URL}/api/kpi/inventory/overview",
            headers=self.headers
        )
        assert response.status_code == 200, f"Inventory Overview API failed: {response.text}"
        data = response.json()
        
        # Verify summary
        assert "summary" in data
        summary = data["summary"]
        assert "total_products" in summary
        assert "total_stock_value" in summary
        assert "low_stock_count" in summary
        assert "dead_stock_count" in summary
        assert "slow_moving_count" in summary
        assert "pending_reorder_count" in summary
        assert "dead_stock_value" in summary
        assert "slow_moving_value" in summary
    
    def test_inventory_overview_returns_alerts(self):
        """Test inventory overview returns alert arrays"""
        response = requests.get(
            f"{BASE_URL}/api/kpi/inventory/overview",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify alert arrays exist
        assert "low_stock" in data
        assert "dead_stock" in data
        assert "slow_moving" in data
        assert isinstance(data["low_stock"], list)
        assert isinstance(data["dead_stock"], list)
        assert isinstance(data["slow_moving"], list)
    
    def test_inventory_overview_returns_warehouse_stock(self):
        """Test inventory overview returns warehouse stock breakdown"""
        response = requests.get(
            f"{BASE_URL}/api/kpi/inventory/overview",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "warehouse_stock" in data
        assert isinstance(data["warehouse_stock"], list)
        
        if len(data["warehouse_stock"]) > 0:
            wh = data["warehouse_stock"][0]
            assert "warehouse_id" in wh
            assert "warehouse_name" in wh
            assert "total_items" in wh
            assert "total_value" in wh


class TestKPIFinancePerformance:
    """KPI Finance Performance endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_finance_overview_returns_ar_aging(self):
        """Test finance overview returns AR aging breakdown"""
        response = requests.get(
            f"{BASE_URL}/api/kpi/finance/overview?period=month",
            headers=self.headers
        )
        assert response.status_code == 200, f"Finance Overview API failed: {response.text}"
        data = response.json()
        
        # Verify AR summary
        assert "ar_summary" in data
        ar = data["ar_summary"]
        assert "total" in ar
        assert "aging" in ar
        assert "overdue_percent" in ar
        
        # Verify aging buckets
        aging = ar["aging"]
        assert "current" in aging
        assert "1_30" in aging
        assert "31_60" in aging
        assert "61_90" in aging
        assert "over_90" in aging
    
    def test_finance_overview_returns_ap_aging(self):
        """Test finance overview returns AP aging breakdown"""
        response = requests.get(
            f"{BASE_URL}/api/kpi/finance/overview?period=month",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify AP summary
        assert "ap_summary" in data
        ap = data["ap_summary"]
        assert "total" in ap
        assert "aging" in ap
        assert "overdue_percent" in ap
        
        # Verify aging buckets
        aging = ap["aging"]
        assert "current" in aging
        assert "1_30" in aging
        assert "31_60" in aging
        assert "61_90" in aging
        assert "over_90" in aging
    
    def test_finance_overview_returns_profit_summary(self):
        """Test finance overview returns profit summary"""
        response = requests.get(
            f"{BASE_URL}/api/kpi/finance/overview?period=month",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "profit_summary" in data
        profit = data["profit_summary"]
        assert "revenue" in profit
        assert "cogs" in profit
        assert "gross_profit" in profit
        assert "gross_margin_percent" in profit
    
    def test_finance_overview_returns_branch_profitability(self):
        """Test finance overview returns branch profitability"""
        response = requests.get(
            f"{BASE_URL}/api/kpi/finance/overview?period=month",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "branch_profitability" in data
        assert isinstance(data["branch_profitability"], list)
        
        if len(data["branch_profitability"]) > 0:
            branch = data["branch_profitability"][0]
            assert "branch_id" in branch
            assert "branch_name" in branch
            assert "revenue" in branch
            assert "estimated_profit" in branch


class TestKPIAuthentication:
    """Test KPI endpoints require authentication"""
    
    def test_dashboard_requires_auth(self):
        """Test dashboard endpoint returns 401 without token"""
        response = requests.get(f"{BASE_URL}/api/kpi/dashboard")
        assert response.status_code in [401, 403]
    
    def test_branch_requires_auth(self):
        """Test branch endpoint returns 401 without token"""
        response = requests.get(f"{BASE_URL}/api/kpi/branch/overview")
        assert response.status_code in [401, 403]
    
    def test_sales_requires_auth(self):
        """Test sales endpoint returns 401 without token"""
        response = requests.get(f"{BASE_URL}/api/kpi/sales/overview")
        assert response.status_code in [401, 403]
    
    def test_inventory_requires_auth(self):
        """Test inventory endpoint returns 401 without token"""
        response = requests.get(f"{BASE_URL}/api/kpi/inventory/overview")
        assert response.status_code in [401, 403]
    
    def test_finance_requires_auth(self):
        """Test finance endpoint returns 401 without token"""
        response = requests.get(f"{BASE_URL}/api/kpi/finance/overview")
        assert response.status_code in [401, 403]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
