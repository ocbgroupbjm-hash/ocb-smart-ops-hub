"""
Iteration 35 - Master Data ERP Module Testing
Tests all Master Data APIs from master_erp.py and master_data.py
- Items (Products), Categories, Brands, Units, Warehouses
- Suppliers, Customers, Sales Persons, Customer Groups
- Item Types, Regions, Banks, E-Money, Discounts, Promotions
"""

import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestMasterDataERPAuth:
    """Test authentication for Master Data APIs"""
    
    token = None
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get token"""
        if TestMasterDataERPAuth.token:
            return
        
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "ocbgroupbjm@gmail.com",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        TestMasterDataERPAuth.token = data.get("token")
        assert TestMasterDataERPAuth.token, "No token in response"
    
    def get_headers(self):
        return {"Authorization": f"Bearer {TestMasterDataERPAuth.token}"}


class TestItemsAPI(TestMasterDataERPAuth):
    """Test Items (Products) CRUD - /api/master/items"""
    
    def test_list_items(self):
        """GET /api/master/items - List items with pagination"""
        response = requests.get(f"{BASE_URL}/api/master/items", headers=self.get_headers())
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "items" in data, "Response should have 'items' key"
        assert "total" in data, "Response should have 'total' key"
        assert "page" in data, "Response should have 'page' key"
        print(f"Items count: {data['total']}")
    
    def test_list_items_with_search(self):
        """GET /api/master/items with search filter"""
        response = requests.get(f"{BASE_URL}/api/master/items?search=test", headers=self.get_headers())
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "items" in data
    
    def test_list_items_with_filters(self):
        """GET /api/master/items with multiple filters"""
        params = {
            "page": 1,
            "limit": 10,
            "sort_by": "code",
            "sort_order": "asc",
            "item_type": "barang",
            "is_active": "true"
        }
        response = requests.get(f"{BASE_URL}/api/master/items", params=params, headers=self.get_headers())
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "items" in data
        print(f"Filtered items: {len(data['items'])}")
    
    def test_create_item(self):
        """POST /api/master/items - Create new item"""
        unique_code = f"TEST-{uuid.uuid4().hex[:8].upper()}"
        item_data = {
            "code": unique_code,
            "barcode": f"BAR{uuid.uuid4().hex[:12].upper()}",
            "name": f"Test Item {datetime.now().strftime('%H%M%S')}",
            "category_id": "",
            "unit_id": "",
            "brand_id": "",
            "branch_id": "",
            "rack": "A1",
            "item_type": "barang",
            "cost_price": 10000,
            "selling_price": 15000,
            "min_stock": 5,
            "max_stock": 100,
            "description": "Test item created by iteration 35",
            "is_active": True,
            "track_stock": True,
            "discontinued": False
        }
        response = requests.post(f"{BASE_URL}/api/master/items", json=item_data, headers=self.get_headers())
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "id" in data, "Response should have 'id'"
        assert "message" in data, "Response should have 'message'"
        print(f"Created item: {unique_code} - {data['id']}")
        return data["id"]


class TestCategoriesAPI(TestMasterDataERPAuth):
    """Test Categories CRUD - /api/master/categories"""
    
    def test_list_categories(self):
        """GET /api/master/categories"""
        response = requests.get(f"{BASE_URL}/api/master/categories", headers=self.get_headers())
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"Categories count: {len(data)}")
    
    def test_create_category(self):
        """POST /api/master/categories"""
        unique_code = f"CAT-{uuid.uuid4().hex[:6].upper()}"
        cat_data = {
            "code": unique_code,
            "name": f"Test Category {datetime.now().strftime('%H%M%S')}",
            "description": "Test category"
        }
        response = requests.post(f"{BASE_URL}/api/master/categories", json=cat_data, headers=self.get_headers())
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "id" in data
        print(f"Created category: {unique_code}")


class TestBrandsAPI(TestMasterDataERPAuth):
    """Test Brands CRUD - /api/master/brands"""
    
    def test_list_brands(self):
        """GET /api/master/brands"""
        response = requests.get(f"{BASE_URL}/api/master/brands", headers=self.get_headers())
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"Brands count: {len(data)}")
    
    def test_create_brand(self):
        """POST /api/master/brands"""
        unique_code = f"BRD-{uuid.uuid4().hex[:6].upper()}"
        brand_data = {
            "code": unique_code,
            "name": f"Test Brand {datetime.now().strftime('%H%M%S')}",
            "description": "Test brand"
        }
        response = requests.post(f"{BASE_URL}/api/master/brands", json=brand_data, headers=self.get_headers())
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "id" in data
        print(f"Created brand: {unique_code}")


class TestUnitsAPI(TestMasterDataERPAuth):
    """Test Units CRUD - /api/master/units"""
    
    def test_list_units(self):
        """GET /api/master/units"""
        response = requests.get(f"{BASE_URL}/api/master/units", headers=self.get_headers())
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"Units count: {len(data)}")
    
    def test_create_unit(self):
        """POST /api/master/units"""
        unique_code = f"UNT-{uuid.uuid4().hex[:6].upper()}"
        unit_data = {
            "code": unique_code,
            "name": f"Test Unit {datetime.now().strftime('%H%M%S')}",
            "description": "Test unit"
        }
        response = requests.post(f"{BASE_URL}/api/master/units", json=unit_data, headers=self.get_headers())
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "id" in data
        print(f"Created unit: {unique_code}")


class TestWarehousesAPI(TestMasterDataERPAuth):
    """Test Warehouses CRUD - /api/master/warehouses"""
    
    def test_list_warehouses(self):
        """GET /api/master/warehouses"""
        response = requests.get(f"{BASE_URL}/api/master/warehouses", headers=self.get_headers())
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"Warehouses count: {len(data)}")
    
    def test_create_warehouse(self):
        """POST /api/master/warehouses"""
        unique_code = f"WH-{uuid.uuid4().hex[:6].upper()}"
        wh_data = {
            "code": unique_code,
            "name": f"Test Warehouse {datetime.now().strftime('%H%M%S')}",
            "branch_id": "",
            "address": "Test address",
            "is_active": True
        }
        response = requests.post(f"{BASE_URL}/api/master/warehouses", json=wh_data, headers=self.get_headers())
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "id" in data
        print(f"Created warehouse: {unique_code}")


class TestSuppliersAPI(TestMasterDataERPAuth):
    """Test Suppliers CRUD - /api/suppliers"""
    
    def test_list_suppliers(self):
        """GET /api/suppliers"""
        response = requests.get(f"{BASE_URL}/api/suppliers", headers=self.get_headers())
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        # Response could be {items: [], total: x} or just []
        if isinstance(data, dict):
            assert "items" in data or "total" in data
            print(f"Suppliers count: {data.get('total', len(data.get('items', [])))}")
        else:
            assert isinstance(data, list)
            print(f"Suppliers count: {len(data)}")


class TestCustomersAPI(TestMasterDataERPAuth):
    """Test Customers CRUD - /api/customers"""
    
    def test_list_customers(self):
        """GET /api/customers"""
        response = requests.get(f"{BASE_URL}/api/customers", headers=self.get_headers())
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        if isinstance(data, dict):
            assert "items" in data
            print(f"Customers count: {data.get('total', len(data.get('items', [])))}")
        else:
            assert isinstance(data, list)
            print(f"Customers count: {len(data)}")


class TestSalesPersonsAPI(TestMasterDataERPAuth):
    """Test Sales Persons CRUD - /api/master/sales-persons"""
    
    def test_list_sales_persons(self):
        """GET /api/master/sales-persons"""
        response = requests.get(f"{BASE_URL}/api/master/sales-persons", headers=self.get_headers())
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"Sales persons count: {len(data)}")
    
    def test_create_sales_person(self):
        """POST /api/master/sales-persons"""
        unique_code = f"SP-{uuid.uuid4().hex[:6].upper()}"
        sp_data = {
            "code": unique_code,
            "name": f"Test Sales {datetime.now().strftime('%H%M%S')}",
            "phone": "081234567890",
            "email": "testsales@test.com",
            "branch_id": "",
            "commission_percent": 5.0,
            "target_monthly": 10000000,
            "is_active": True
        }
        response = requests.post(f"{BASE_URL}/api/master/sales-persons", json=sp_data, headers=self.get_headers())
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "id" in data
        print(f"Created sales person: {unique_code}")


class TestCustomerGroupsAPI(TestMasterDataERPAuth):
    """Test Customer Groups CRUD - /api/master/customer-groups"""
    
    def test_list_customer_groups(self):
        """GET /api/master/customer-groups"""
        response = requests.get(f"{BASE_URL}/api/master/customer-groups", headers=self.get_headers())
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"Customer groups count: {len(data)}")
    
    def test_create_customer_group(self):
        """POST /api/master/customer-groups"""
        unique_code = f"GRP-{uuid.uuid4().hex[:6].upper()}"
        group_data = {
            "code": unique_code,
            "name": f"Test Group {datetime.now().strftime('%H%M%S')}",
            "discount_percent": 5.0,
            "description": "Test customer group"
        }
        response = requests.post(f"{BASE_URL}/api/master/customer-groups", json=group_data, headers=self.get_headers())
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "id" in data
        print(f"Created customer group: {unique_code}")


class TestItemTypesAPI(TestMasterDataERPAuth):
    """Test Item Types CRUD - /api/master/item-types"""
    
    def test_list_item_types(self):
        """GET /api/master/item-types"""
        response = requests.get(f"{BASE_URL}/api/master/item-types", headers=self.get_headers())
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        # Response could be {items: [], total: x} or just []
        if isinstance(data, dict):
            assert "items" in data or "total" in data
            items = data.get("items", [])
            print(f"Item types count: {len(items)}")
        else:
            assert isinstance(data, list)
            print(f"Item types count: {len(data)}")
    
    def test_create_item_type(self):
        """POST /api/master/item-types"""
        unique_code = f"IT-{uuid.uuid4().hex[:6].upper()}"
        type_data = {
            "code": unique_code,
            "name": f"Test Item Type {datetime.now().strftime('%H%M%S')}",
            "description": "Test item type"
        }
        response = requests.post(f"{BASE_URL}/api/master/item-types", json=type_data, headers=self.get_headers())
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "id" in data
        print(f"Created item type: {unique_code}")


class TestRegionsAPI(TestMasterDataERPAuth):
    """Test Regions CRUD - /api/master/regions"""
    
    def test_list_regions(self):
        """GET /api/master/regions"""
        response = requests.get(f"{BASE_URL}/api/master/regions", headers=self.get_headers())
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"Regions count: {len(data)}")
    
    def test_create_region(self):
        """POST /api/master/regions"""
        unique_code = f"REG-{uuid.uuid4().hex[:6].upper()}"
        region_data = {
            "code": unique_code,
            "name": f"Test Region {datetime.now().strftime('%H%M%S')}",
            "parent_id": "",
            "type": "province"
        }
        response = requests.post(f"{BASE_URL}/api/master/regions", json=region_data, headers=self.get_headers())
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "id" in data
        print(f"Created region: {unique_code}")


class TestBanksAPI(TestMasterDataERPAuth):
    """Test Banks CRUD - /api/master/banks"""
    
    def test_list_banks(self):
        """GET /api/master/banks"""
        response = requests.get(f"{BASE_URL}/api/master/banks", headers=self.get_headers())
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"Banks count: {len(data)}")
    
    def test_create_bank(self):
        """POST /api/master/banks"""
        unique_code = f"BNK-{uuid.uuid4().hex[:6].upper()}"
        bank_data = {
            "code": unique_code,
            "name": f"Test Bank {datetime.now().strftime('%H%M%S')}",
            "account_number": "1234567890",
            "account_name": "Test Account",
            "branch": "Test Branch",
            "is_active": True
        }
        response = requests.post(f"{BASE_URL}/api/master/banks", json=bank_data, headers=self.get_headers())
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "id" in data
        print(f"Created bank: {unique_code}")


class TestEmoneyAPI(TestMasterDataERPAuth):
    """Test E-Money CRUD - /api/master/emoney"""
    
    def test_list_emoney(self):
        """GET /api/master/emoney"""
        response = requests.get(f"{BASE_URL}/api/master/emoney", headers=self.get_headers())
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"E-Money count: {len(data)}")
    
    def test_create_emoney(self):
        """POST /api/master/emoney"""
        unique_code = f"EM-{uuid.uuid4().hex[:6].upper()}"
        emoney_data = {
            "code": unique_code,
            "name": f"Test E-Money {datetime.now().strftime('%H%M%S')}",
            "provider": "Test Provider",
            "fee_percent": 1.5,
            "fee_fixed": 500,
            "is_active": True
        }
        response = requests.post(f"{BASE_URL}/api/master/emoney", json=emoney_data, headers=self.get_headers())
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "id" in data
        print(f"Created e-money: {unique_code}")


class TestDiscountsAPI(TestMasterDataERPAuth):
    """Test Discounts CRUD - /api/master/discounts"""
    
    def test_list_discounts(self):
        """GET /api/master/discounts"""
        response = requests.get(f"{BASE_URL}/api/master/discounts", headers=self.get_headers())
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"Discounts count: {len(data)}")
    
    def test_create_discount(self):
        """POST /api/master/discounts"""
        unique_code = f"DSC-{uuid.uuid4().hex[:6].upper()}"
        discount_data = {
            "code": unique_code,
            "name": f"Test Discount {datetime.now().strftime('%H%M%S')}",
            "discount_type": "percent",
            "discount_value": 10.0,
            "min_purchase": 50000,
            "start_date": "2026-01-01",
            "end_date": "2026-12-31",
            "is_active": True
        }
        response = requests.post(f"{BASE_URL}/api/master/discounts", json=discount_data, headers=self.get_headers())
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "id" in data
        print(f"Created discount: {unique_code}")


class TestPromotionsAPI(TestMasterDataERPAuth):
    """Test Promotions CRUD - /api/master/promotions"""
    
    def test_list_promotions(self):
        """GET /api/master/promotions"""
        response = requests.get(f"{BASE_URL}/api/master/promotions", headers=self.get_headers())
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"Promotions count: {len(data)}")
    
    def test_create_promotion(self):
        """POST /api/master/promotions"""
        unique_code = f"PRM-{uuid.uuid4().hex[:6].upper()}"
        promo_data = {
            "code": unique_code,
            "name": f"Test Promo {datetime.now().strftime('%H%M%S')}",
            "promo_type": "buy_get",
            "description": "Test promotion",
            "start_date": "2026-01-01",
            "end_date": "2026-12-31",
            "is_active": True
        }
        response = requests.post(f"{BASE_URL}/api/master/promotions", json=promo_data, headers=self.get_headers())
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "id" in data
        print(f"Created promotion: {unique_code}")


class TestOwnerDashboard(TestMasterDataERPAuth):
    """Test Owner Dashboard - /api/owner-dashboard/summary"""
    
    def test_owner_dashboard_summary(self):
        """GET /api/owner-dashboard/summary - Verify dashboard working"""
        response = requests.get(f"{BASE_URL}/api/owner-dashboard/summary", headers=self.get_headers())
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        # Just verify it returns data
        print(f"Owner dashboard returned data: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")


class TestFinanceDashboard(TestMasterDataERPAuth):
    """Test Finance Dashboard - /api/finance-dashboard/summary"""
    
    def test_finance_dashboard_summary(self):
        """GET /api/finance-dashboard/summary - Verify dashboard working"""
        response = requests.get(f"{BASE_URL}/api/finance-dashboard/summary", headers=self.get_headers())
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        print(f"Finance dashboard returned data: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")


class TestShippingCostsAPI(TestMasterDataERPAuth):
    """Test Shipping Costs (Ongkir) CRUD - /api/master/shipping-costs"""
    
    def test_list_shipping_costs(self):
        """GET /api/master/shipping-costs"""
        response = requests.get(f"{BASE_URL}/api/master/shipping-costs", headers=self.get_headers())
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"Shipping costs count: {len(data)}")
    
    def test_create_shipping_cost(self):
        """POST /api/master/shipping-costs"""
        unique_code = f"SC-{uuid.uuid4().hex[:6].upper()}"
        sc_data = {
            "code": unique_code,
            "name": f"Test Ongkir {datetime.now().strftime('%H%M%S')}",
            "destination": "Jakarta",
            "cost": 15000,
            "min_weight": 0,
            "max_weight": 10,
            "is_active": True
        }
        response = requests.post(f"{BASE_URL}/api/master/shipping-costs", json=sc_data, headers=self.get_headers())
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "id" in data
        print(f"Created shipping cost: {unique_code}")


class TestCustomerPointsAPI(TestMasterDataERPAuth):
    """Test Customer Points - /api/master/customer-points"""
    
    def test_list_customer_points(self):
        """GET /api/master/customer-points"""
        response = requests.get(f"{BASE_URL}/api/master/customer-points", headers=self.get_headers())
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"Customer points count: {len(data)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
