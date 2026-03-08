"""
OCB TITAN Retail AI System - Comprehensive Backend API Tests
Testing: Auth, Products, POS, Inventory, Finance, Reports, Dashboard
Created for iteration_2 testing
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Admin credentials for OCB TITAN
ADMIN_EMAIL = "admin@ocb.com"
ADMIN_PASSWORD = "admin123"

class TestHealthAndAuth:
    """Health check and Authentication tests"""
    
    def test_health_check(self):
        """Test API health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        assert data.get("system") == "OCB TITAN Retail AI"
        print(f"✓ Health check passed: {data}")
    
    def test_api_root(self):
        """Test API root endpoint"""
        response = requests.get(f"{BASE_URL}/api")
        assert response.status_code == 200
        data = response.json()
        assert data.get("system") == "OCB TITAN Retail AI System"
        assert data.get("company") == "OCB GROUP"
        print(f"✓ API root: {data}")
    
    def test_login_admin(self):
        """Test login with admin credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["role"] == "owner"
        assert data["user"]["email"] == ADMIN_EMAIL
        print(f"✓ Admin login successful: {data['user']['name']}")
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        print("✓ Invalid login correctly rejected")


@pytest.fixture(scope="module")
def auth_headers():
    """Get authentication token for admin user"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code != 200:
        pytest.skip("Authentication failed - cannot proceed with tests")
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


class TestDashboard:
    """Dashboard API tests"""
    
    def test_owner_dashboard(self, auth_headers):
        """Test owner dashboard endpoint"""
        response = requests.get(f"{BASE_URL}/api/dashboard/owner", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Owner dashboard loaded with summary: {data.get('summary', {})}")
    
    def test_branch_dashboard(self, auth_headers):
        """Test branch dashboard endpoint"""
        response = requests.get(f"{BASE_URL}/api/dashboard/branch", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Branch dashboard loaded: {data.get('branch', {}).get('name', 'Unknown')}")
    
    def test_sales_trend(self, auth_headers):
        """Test sales trend endpoint"""
        response = requests.get(f"{BASE_URL}/api/dashboard/sales-trend?days=7", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        print(f"✓ Sales trend loaded: {len(data.get('data', []))} days")


class TestProducts:
    """Products management tests"""
    
    def test_get_categories(self, auth_headers):
        """Test fetching product categories"""
        response = requests.get(f"{BASE_URL}/api/products/categories", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Fetched {len(data)} categories")
    
    def test_get_products(self, auth_headers):
        """Test fetching products list"""
        response = requests.get(f"{BASE_URL}/api/products?limit=50", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        print(f"✓ Fetched {len(data['items'])} products (total: {data['total']})")
    
    def test_search_products(self, auth_headers):
        """Test product search for POS"""
        response = requests.get(f"{BASE_URL}/api/products/search?q=test", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Product search returned {len(data)} results")
    
    def test_create_category(self, auth_headers):
        """Test creating a product category"""
        category = {
            "code": f"TEST_{int(time.time())}",
            "name": f"Test Category {int(time.time())}",
            "description": "Test category for testing"
        }
        response = requests.post(f"{BASE_URL}/api/products/categories", json=category, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        print(f"✓ Created category: {category['name']}")
        return data["id"]
    
    def test_create_product(self, auth_headers):
        """Test creating a product"""
        product = {
            "name": f"TEST_Product_{int(time.time())}",
            "barcode": f"TEST{int(time.time())}",
            "cost_price": 10000,
            "selling_price": 15000,
            "unit": "pcs",
            "min_stock": 5
        }
        response = requests.post(f"{BASE_URL}/api/products", json=product, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "code" in data
        print(f"✓ Created product: {product['name']} with code {data.get('code')}")
        return data["id"]


class TestInventory:
    """Inventory management tests"""
    
    def test_get_stock(self, auth_headers):
        """Test fetching branch stock"""
        response = requests.get(f"{BASE_URL}/api/inventory/stock?limit=50", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        print(f"✓ Fetched {len(data['items'])} stock items")
    
    def test_get_low_stock(self, auth_headers):
        """Test fetching low stock alerts"""
        response = requests.get(f"{BASE_URL}/api/inventory/stock/low", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Fetched {len(data)} low stock alerts")
    
    def test_get_stock_movements(self, auth_headers):
        """Test fetching stock movements"""
        response = requests.get(f"{BASE_URL}/api/inventory/movements?limit=50", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        print(f"✓ Fetched {len(data['items'])} stock movements")
    
    def test_get_transfers(self, auth_headers):
        """Test fetching stock transfers"""
        response = requests.get(f"{BASE_URL}/api/inventory/transfers", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        print(f"✓ Fetched {len(data['items'])} transfers")


class TestPOS:
    """Point of Sale tests"""
    
    def test_get_held_transactions(self, auth_headers):
        """Test fetching held transactions"""
        response = requests.get(f"{BASE_URL}/api/pos/held", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Fetched {len(data)} held transactions")
    
    def test_get_transactions(self, auth_headers):
        """Test fetching transaction history"""
        response = requests.get(f"{BASE_URL}/api/pos/transactions?limit=50", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        print(f"✓ Fetched {len(data['items'])} transactions")
    
    def test_get_today_summary(self, auth_headers):
        """Test fetching today's POS summary"""
        response = requests.get(f"{BASE_URL}/api/pos/summary/today", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_sales" in data
        assert "total_transactions" in data
        print(f"✓ Today's summary: {data.get('total_transactions')} transactions, Rp {data.get('total_sales', 0):,.0f}")


class TestCustomers:
    """Customer management tests"""
    
    def test_get_customers(self, auth_headers):
        """Test fetching customers"""
        response = requests.get(f"{BASE_URL}/api/customers", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        print(f"✓ Fetched {len(data['items'])} customers")
    
    def test_create_customer(self, auth_headers):
        """Test creating a customer"""
        customer = {
            "name": f"TEST_Customer_{int(time.time())}",
            "phone": f"+62812{int(time.time()) % 10000000:07d}",
            "email": f"test_{int(time.time())}@example.com",
            "segment": "regular"
        }
        response = requests.post(f"{BASE_URL}/api/customers", json=customer, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        print(f"✓ Created customer: {customer['name']}")


class TestSuppliers:
    """Supplier management tests"""
    
    def test_get_suppliers(self, auth_headers):
        """Test fetching suppliers"""
        response = requests.get(f"{BASE_URL}/api/suppliers", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        print(f"✓ Fetched {len(data['items'])} suppliers")
    
    def test_create_supplier(self, auth_headers):
        """Test creating a supplier"""
        supplier = {
            "name": f"TEST_Supplier_{int(time.time())}",
            "code": f"SUP{int(time.time()) % 1000000:06d}",
            "phone": "+62812345678",
            "address": "Jakarta, Indonesia",
            "payment_terms": 30
        }
        response = requests.post(f"{BASE_URL}/api/suppliers", json=supplier, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        print(f"✓ Created supplier: {supplier['name']}")


class TestBranches:
    """Branch management tests"""
    
    def test_get_branches(self, auth_headers):
        """Test fetching branches"""
        response = requests.get(f"{BASE_URL}/api/branches", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Fetched {len(data)} branches")


class TestFinance:
    """Finance management tests"""
    
    def test_get_cash_balance(self, auth_headers):
        """Test fetching cash balance"""
        response = requests.get(f"{BASE_URL}/api/finance/cash/balance", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "cash_balance" in data
        assert "branch_name" in data
        print(f"✓ Cash balance: Rp {data.get('cash_balance', 0):,.0f} at {data.get('branch_name')}")
    
    def test_get_cash_movements(self, auth_headers):
        """Test fetching cash movements"""
        response = requests.get(f"{BASE_URL}/api/finance/cash/movements?limit=50", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        print(f"✓ Fetched {len(data['items'])} cash movements")
    
    def test_get_expenses(self, auth_headers):
        """Test fetching expenses"""
        response = requests.get(f"{BASE_URL}/api/finance/expenses?limit=50", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        print(f"✓ Fetched {len(data['items'])} expenses")
    
    def test_daily_report(self, auth_headers):
        """Test fetching daily financial report"""
        today = time.strftime("%Y-%m-%d")
        response = requests.get(f"{BASE_URL}/api/finance/reports/daily?date={today}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "date" in data
        assert "sales" in data
        print(f"✓ Daily report for {data.get('date')}: Sales Rp {data.get('sales', {}).get('total', 0):,.0f}")


class TestReports:
    """Reports API tests"""
    
    def test_sales_report(self, auth_headers):
        """Test sales report"""
        today = time.strftime("%Y-%m-%d")
        month_start = time.strftime("%Y-%m-01")
        response = requests.get(
            f"{BASE_URL}/api/reports/sales?date_from={month_start}&date_to={today}&group_by=day", 
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data or "totals" in data
        print(f"✓ Sales report loaded")
    
    def test_product_performance(self, auth_headers):
        """Test product performance report"""
        today = time.strftime("%Y-%m-%d")
        month_start = time.strftime("%Y-%m-01")
        response = requests.get(
            f"{BASE_URL}/api/reports/product-performance?date_from={month_start}&date_to={today}", 
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Product performance report loaded")
    
    def test_inventory_report(self, auth_headers):
        """Test inventory report"""
        response = requests.get(f"{BASE_URL}/api/reports/inventory", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Inventory report loaded")
    
    def test_branch_comparison(self, auth_headers):
        """Test branch comparison report"""
        today = time.strftime("%Y-%m-%d")
        month_start = time.strftime("%Y-%m-01")
        response = requests.get(
            f"{BASE_URL}/api/reports/branch-comparison?date_from={month_start}&date_to={today}", 
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Branch comparison report loaded")


class TestUsers:
    """User management tests"""
    
    def test_get_current_user(self, auth_headers):
        """Test fetching current user info"""
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert data["email"] == ADMIN_EMAIL
        print(f"✓ Current user: {data.get('name')} ({data.get('role')})")
    
    def test_get_users(self, auth_headers):
        """Test fetching users list"""
        response = requests.get(f"{BASE_URL}/api/users", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Fetched {len(data)} users")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
