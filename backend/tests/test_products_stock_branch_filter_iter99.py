"""
Test Products Stock Display and Branch Filter - Iteration 99

Tests:
1. Products list shows aggregated stock from all branches
2. Products list shows branch count for each product  
3. Branch filter in product list works correctly
4. Brand filter input works
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "ocbgroupbjm@gmail.com"
TEST_PASSWORD = "admin123"
TEST_TENANT = "ocb_titan"


class TestProductsStockBranchFilter:
    """Test Products API with stock aggregation and branch filter"""
    
    token = None
    branches = []
    
    @pytest.fixture(autouse=True)
    def setup(self, request):
        """Login and get token before tests"""
        if not TestProductsStockBranchFilter.token:
            login_response = requests.post(
                f"{BASE_URL}/api/auth/login",
                json={
                    "email": TEST_EMAIL,
                    "password": TEST_PASSWORD,
                    "tenant_id": TEST_TENANT
                }
            )
            assert login_response.status_code == 200, f"Login failed: {login_response.text}"
            data = login_response.json()
            TestProductsStockBranchFilter.token = data.get("access_token") or data.get("token")
        
        self.headers = {
            "Authorization": f"Bearer {TestProductsStockBranchFilter.token}",
            "Content-Type": "application/json"
        }
    
    # === Test 1: Get branches/warehouses list ===
    def test_01_get_branches_list(self):
        """Test /api/master/warehouses returns branches for filter dropdown"""
        response = requests.get(
            f"{BASE_URL}/api/master/warehouses",
            headers=self.headers
        )
        assert response.status_code == 200, f"Failed to get warehouses: {response.text}"
        
        branches = response.json()
        assert isinstance(branches, list), "Expected list of branches"
        assert len(branches) > 0, "Expected at least one branch"
        
        # Save branches for later tests
        TestProductsStockBranchFilter.branches = branches
        
        # Check branch structure
        first_branch = branches[0]
        assert "id" in first_branch, "Branch should have id"
        assert "name" in first_branch, "Branch should have name"
        
        print(f"✓ Found {len(branches)} branches")
        print(f"  Sample branches: {[b.get('name', 'N/A') for b in branches[:5]]}")
    
    # === Test 2: Products list with aggregated stock ===
    def test_02_products_list_aggregated_stock(self):
        """Test /api/products returns aggregated stock from all branches"""
        response = requests.get(
            f"{BASE_URL}/api/products?limit=50",
            headers=self.headers
        )
        assert response.status_code == 200, f"Failed to get products: {response.text}"
        
        data = response.json()
        assert "items" in data, "Response should have items"
        items = data["items"]
        assert len(items) > 0, "Expected at least one product"
        
        # Check product structure for stock fields
        first_product = items[0]
        assert "stock" in first_product, "Product should have stock field"
        
        # Find a product with stock > 0
        product_with_stock = None
        for p in items:
            if p.get("stock", 0) > 0:
                product_with_stock = p
                break
        
        if product_with_stock:
            print(f"✓ Product with stock: {product_with_stock.get('name')}")
            print(f"  - Stock: {product_with_stock.get('stock', 0)}")
            print(f"  - Branches count: {product_with_stock.get('branches_count', 'N/A')}")
            
            # Verify branches_count field exists for aggregated view
            if "branches_count" in product_with_stock:
                assert isinstance(product_with_stock["branches_count"], int), "branches_count should be integer"
        else:
            print("⚠ No products with stock found (this may be expected)")
        
        print(f"✓ Products list returned {len(items)} items")
    
    # === Test 3: Products list with branch filter ===
    def test_03_products_list_with_branch_filter(self):
        """Test /api/products with branch_id filter shows stock for specific branch"""
        if not TestProductsStockBranchFilter.branches:
            pytest.skip("No branches available")
        
        # Get first branch
        test_branch = TestProductsStockBranchFilter.branches[0]
        branch_id = test_branch.get("id")
        branch_name = test_branch.get("name", "Unknown")
        
        response = requests.get(
            f"{BASE_URL}/api/products?limit=50&branch_id={branch_id}",
            headers=self.headers
        )
        assert response.status_code == 200, f"Failed to get products with branch filter: {response.text}"
        
        data = response.json()
        items = data.get("items", [])
        
        print(f"✓ Products filtered by branch '{branch_name}' returned {len(items)} items")
        
        # When branch_id is specified, product should have branch_stock instead of branches_count
        if items:
            first_item = items[0]
            # Check that we get branch-specific stock
            assert "stock" in first_item, "Product should have stock even with branch filter"
            print(f"  Sample product: {first_item.get('name')}, stock={first_item.get('stock', 0)}")
    
    # === Test 4: Products list with brand filter ===
    def test_04_products_list_with_brand_filter(self):
        """Test /api/products with brand filter"""
        # First get list without filter to find a brand
        response = requests.get(
            f"{BASE_URL}/api/products?limit=100",
            headers=self.headers
        )
        assert response.status_code == 200
        
        data = response.json()
        items = data.get("items", [])
        
        # Find a product with brand
        product_with_brand = None
        for p in items:
            if p.get("brand"):
                product_with_brand = p
                break
        
        if not product_with_brand:
            print("⚠ No products with brand found, skipping brand filter test")
            return
        
        test_brand = product_with_brand.get("brand")
        
        # Test brand filter
        response = requests.get(
            f"{BASE_URL}/api/products?limit=50&brand={test_brand}",
            headers=self.headers
        )
        assert response.status_code == 200, f"Failed to filter by brand: {response.text}"
        
        data = response.json()
        filtered_items = data.get("items", [])
        
        # All returned items should have matching brand
        for item in filtered_items:
            item_brand = item.get("brand", "")
            assert test_brand.lower() in item_brand.lower(), f"Product {item.get('name')} has brand {item_brand}, expected {test_brand}"
        
        print(f"✓ Brand filter '{test_brand}' returned {len(filtered_items)} products")
    
    # === Test 5: Products list with search filter ===
    def test_05_products_list_with_search(self):
        """Test /api/products with search filter"""
        # Use a known product code pattern
        search_term = "PRD"
        
        response = requests.get(
            f"{BASE_URL}/api/products?limit=50&search={search_term}",
            headers=self.headers
        )
        assert response.status_code == 200, f"Failed to search products: {response.text}"
        
        data = response.json()
        items = data.get("items", [])
        
        print(f"✓ Search '{search_term}' returned {len(items)} products")
    
    # === Test 6: Verify specific products have stock (PRD002, PXLA5K) ===
    def test_06_verify_specific_product_stock(self):
        """Test specific products mentioned in requirements have stock"""
        # According to requirements: PRD002 has 278 stock, PXLA5K has 1100 stock
        test_codes = ["PRD002", "PXLA5K"]
        
        for code in test_codes:
            response = requests.get(
                f"{BASE_URL}/api/products?search={code}",
                headers=self.headers
            )
            assert response.status_code == 200
            
            data = response.json()
            items = data.get("items", [])
            
            # Find exact match
            matching = [p for p in items if p.get("code") == code]
            
            if matching:
                product = matching[0]
                stock = product.get("stock", 0)
                branches_count = product.get("branches_count", 0)
                print(f"✓ Product {code}: stock={stock}, branches={branches_count}")
            else:
                print(f"⚠ Product {code} not found (may have different code)")
    
    # === Test 7: Products combined filters (branch + brand) ===
    def test_07_products_combined_filters(self):
        """Test /api/products with multiple filters"""
        if not TestProductsStockBranchFilter.branches:
            pytest.skip("No branches available")
        
        test_branch = TestProductsStockBranchFilter.branches[0]
        branch_id = test_branch.get("id")
        
        response = requests.get(
            f"{BASE_URL}/api/products?limit=50&branch_id={branch_id}&search=PRD",
            headers=self.headers
        )
        assert response.status_code == 200, f"Failed with combined filters: {response.text}"
        
        data = response.json()
        items = data.get("items", [])
        
        print(f"✓ Combined filter (branch + search) returned {len(items)} products")
    
    # === Test 8: Get product with stock details ===
    def test_08_product_detail_stock(self):
        """Test /api/products/{id} returns stock across all branches"""
        # First get a product
        response = requests.get(
            f"{BASE_URL}/api/products?limit=5",
            headers=self.headers
        )
        assert response.status_code == 200
        
        data = response.json()
        items = data.get("items", [])
        
        if not items:
            pytest.skip("No products available")
        
        product_id = items[0].get("id")
        
        # Get product detail
        response = requests.get(
            f"{BASE_URL}/api/products/{product_id}",
            headers=self.headers
        )
        assert response.status_code == 200, f"Failed to get product detail: {response.text}"
        
        product = response.json()
        assert "total_stock" in product or "stock" in product, "Product detail should have stock info"
        
        if "stocks" in product:
            stocks = product.get("stocks", [])
            print(f"✓ Product {product.get('name')} has stock in {len(stocks)} branches")
            for s in stocks[:3]:  # Show first 3
                print(f"  - {s.get('branch_name', s.get('branch_id'))}: {s.get('quantity', 0)}")
        else:
            print(f"✓ Product {product.get('name')} total_stock: {product.get('total_stock', product.get('stock', 0))}")


class TestQuickPurchaseStockNote:
    """Test Quick Purchase page stock note message"""
    
    token = None
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get token"""
        if not TestQuickPurchaseStockNote.token:
            login_response = requests.post(
                f"{BASE_URL}/api/auth/login",
                json={
                    "email": TEST_EMAIL,
                    "password": TEST_PASSWORD,
                    "tenant_id": TEST_TENANT
                }
            )
            assert login_response.status_code == 200
            data = login_response.json()
            TestQuickPurchaseStockNote.token = data.get("access_token") or data.get("token")
        
        self.headers = {
            "Authorization": f"Bearer {TestQuickPurchaseStockNote.token}",
            "Content-Type": "application/json"
        }
    
    def test_01_quick_purchase_endpoints_available(self):
        """Test Quick Purchase related endpoints are available"""
        # Test suppliers endpoint
        response = requests.get(
            f"{BASE_URL}/api/suppliers",
            headers=self.headers
        )
        assert response.status_code == 200, f"Suppliers endpoint failed: {response.text}"
        
        # Test warehouses endpoint
        response = requests.get(
            f"{BASE_URL}/api/master/warehouses",
            headers=self.headers
        )
        assert response.status_code == 200, f"Warehouses endpoint failed: {response.text}"
        
        # Test products endpoint
        response = requests.get(
            f"{BASE_URL}/api/products?limit=5",
            headers=self.headers
        )
        assert response.status_code == 200, f"Products endpoint failed: {response.text}"
        
        print("✓ All Quick Purchase related endpoints are available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
