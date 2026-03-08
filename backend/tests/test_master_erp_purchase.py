# OCB AI TITAN - Master Data ERP & Purchase API Tests
# Tests for Banks, E-Money, Purchase Orders, Purchase Payments, Sales, Stock Cards

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = "https://smart-ops-hub-6.preview.emergentagent.com"

class TestAuthentication:
    """Test user authentication"""
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@ocb.com",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data, "Response should contain token"
        assert "user" in data, "Response should contain user"
        return data["token"]


@pytest.fixture
def auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "admin@ocb.com",
        "password": "admin123"
    })
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip("Authentication failed - skipping authenticated tests")


@pytest.fixture
def auth_headers(auth_token):
    """Get headers with auth token"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


# ==================== BANKS CRUD TESTS ====================

class TestBanksCRUD:
    """Test Master Data - Banks CRUD operations"""
    
    def test_list_banks(self, auth_headers):
        """Test GET /api/master/banks - List all banks"""
        response = requests.get(f"{BASE_URL}/api/master/banks", headers=auth_headers)
        assert response.status_code == 200, f"Failed to list banks: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Banks response should be a list"
        print(f"Found {len(data)} banks")
    
    def test_create_bank(self, auth_headers):
        """Test POST /api/master/banks - Create new bank"""
        unique_id = str(uuid.uuid4())[:8]
        bank_data = {
            "code": f"TEST_{unique_id}",
            "name": f"Test Bank {unique_id}",
            "account_number": "1234567890",
            "account_name": "Test Account",
            "branch": "Test Branch",
            "is_active": True
        }
        response = requests.post(f"{BASE_URL}/api/master/banks", 
                                headers=auth_headers, json=bank_data)
        assert response.status_code == 200, f"Failed to create bank: {response.text}"
        data = response.json()
        assert "id" in data, "Response should contain id"
        print(f"Created bank with id: {data['id']}")
        return data["id"]
    
    def test_create_update_delete_bank(self, auth_headers):
        """Test full CRUD cycle for bank"""
        # CREATE
        unique_id = str(uuid.uuid4())[:8]
        bank_data = {
            "code": f"CRUD_{unique_id}",
            "name": f"CRUD Test Bank {unique_id}",
            "account_number": "9876543210",
            "account_name": "CRUD Account",
            "branch": "CRUD Branch",
            "is_active": True
        }
        create_response = requests.post(f"{BASE_URL}/api/master/banks", 
                                       headers=auth_headers, json=bank_data)
        assert create_response.status_code == 200, f"Create failed: {create_response.text}"
        bank_id = create_response.json()["id"]
        print(f"Created bank: {bank_id}")
        
        # UPDATE
        update_data = {
            "code": f"CRUD_{unique_id}",
            "name": f"Updated Bank {unique_id}",
            "account_number": "1111111111",
            "account_name": "Updated Account",
            "branch": "Updated Branch",
            "is_active": False
        }
        update_response = requests.put(f"{BASE_URL}/api/master/banks/{bank_id}", 
                                      headers=auth_headers, json=update_data)
        assert update_response.status_code == 200, f"Update failed: {update_response.text}"
        print(f"Updated bank: {bank_id}")
        
        # VERIFY UPDATE - list and check
        list_response = requests.get(f"{BASE_URL}/api/master/banks?search={unique_id}", 
                                    headers=auth_headers)
        assert list_response.status_code == 200
        banks = list_response.json()
        updated_bank = next((b for b in banks if b.get("id") == bank_id), None)
        if updated_bank:
            assert updated_bank["name"] == f"Updated Bank {unique_id}", "Bank name not updated"
            assert updated_bank["is_active"] == False, "Bank status not updated"
            print("Bank update verified")
        
        # DELETE
        delete_response = requests.delete(f"{BASE_URL}/api/master/banks/{bank_id}", 
                                         headers=auth_headers)
        assert delete_response.status_code == 200, f"Delete failed: {delete_response.text}"
        print(f"Deleted bank: {bank_id}")
        
        # VERIFY DELETE
        verify_response = requests.get(f"{BASE_URL}/api/master/banks?search={unique_id}", 
                                      headers=auth_headers)
        banks_after = verify_response.json()
        deleted_bank = next((b for b in banks_after if b.get("id") == bank_id), None)
        assert deleted_bank is None, "Bank should be deleted"
        print("Bank deletion verified")


# ==================== E-MONEY CRUD TESTS ====================

class TestEmoneyCRUD:
    """Test Master Data - E-Money CRUD operations"""
    
    def test_list_emoney(self, auth_headers):
        """Test GET /api/master/emoney - List all e-money"""
        response = requests.get(f"{BASE_URL}/api/master/emoney", headers=auth_headers)
        assert response.status_code == 200, f"Failed to list e-money: {response.text}"
        data = response.json()
        assert isinstance(data, list), "E-Money response should be a list"
        print(f"Found {len(data)} e-money records")
    
    def test_create_emoney(self, auth_headers):
        """Test POST /api/master/emoney - Create new e-money"""
        unique_id = str(uuid.uuid4())[:8]
        emoney_data = {
            "code": f"EM_{unique_id}",
            "name": f"Test E-Money {unique_id}",
            "provider": "Test Provider",
            "fee_percent": 1.5,
            "fee_fixed": 500,
            "is_active": True
        }
        response = requests.post(f"{BASE_URL}/api/master/emoney", 
                                headers=auth_headers, json=emoney_data)
        assert response.status_code == 200, f"Failed to create e-money: {response.text}"
        data = response.json()
        assert "id" in data, "Response should contain id"
        print(f"Created e-money with id: {data['id']}")
        return data["id"]
    
    def test_create_update_delete_emoney(self, auth_headers):
        """Test full CRUD cycle for e-money"""
        # CREATE
        unique_id = str(uuid.uuid4())[:8]
        emoney_data = {
            "code": f"EMCRUD_{unique_id}",
            "name": f"CRUD E-Money {unique_id}",
            "provider": "GoPay",
            "fee_percent": 2.0,
            "fee_fixed": 1000,
            "is_active": True
        }
        create_response = requests.post(f"{BASE_URL}/api/master/emoney", 
                                       headers=auth_headers, json=emoney_data)
        assert create_response.status_code == 200, f"Create failed: {create_response.text}"
        emoney_id = create_response.json()["id"]
        print(f"Created e-money: {emoney_id}")
        
        # UPDATE
        update_data = {
            "code": f"EMCRUD_{unique_id}",
            "name": f"Updated E-Money {unique_id}",
            "provider": "OVO",
            "fee_percent": 1.0,
            "fee_fixed": 0,
            "is_active": False
        }
        update_response = requests.put(f"{BASE_URL}/api/master/emoney/{emoney_id}", 
                                      headers=auth_headers, json=update_data)
        assert update_response.status_code == 200, f"Update failed: {update_response.text}"
        print(f"Updated e-money: {emoney_id}")
        
        # VERIFY UPDATE
        list_response = requests.get(f"{BASE_URL}/api/master/emoney?search={unique_id}", 
                                    headers=auth_headers)
        assert list_response.status_code == 200
        emoneys = list_response.json()
        updated = next((e for e in emoneys if e.get("id") == emoney_id), None)
        if updated:
            assert updated["provider"] == "OVO", "E-Money provider not updated"
            print("E-Money update verified")
        
        # DELETE
        delete_response = requests.delete(f"{BASE_URL}/api/master/emoney/{emoney_id}", 
                                         headers=auth_headers)
        assert delete_response.status_code == 200, f"Delete failed: {delete_response.text}"
        print(f"Deleted e-money: {emoney_id}")


# ==================== PURCHASE ORDERS TESTS ====================

class TestPurchaseOrders:
    """Test Purchase Orders - view list"""
    
    def test_list_purchase_orders(self, auth_headers):
        """Test GET /api/purchase/orders - List all purchase orders"""
        response = requests.get(f"{BASE_URL}/api/purchase/orders", headers=auth_headers)
        assert response.status_code == 200, f"Failed to list purchase orders: {response.text}"
        data = response.json()
        assert "items" in data, "Response should contain items"
        assert "total" in data, "Response should contain total"
        print(f"Found {len(data['items'])} purchase orders, total: {data['total']}")
        
        # Verify data structure of items
        if len(data['items']) > 0:
            po = data['items'][0]
            assert "id" in po or "po_number" in po, "PO should have id or po_number"
            print(f"First PO: {po.get('po_number', 'N/A')}")
    
    def test_filter_purchase_orders_by_status(self, auth_headers):
        """Test GET /api/purchase/orders with status filter"""
        # Test filtering by various statuses
        for status in ['draft', 'ordered', 'received', 'cancelled']:
            response = requests.get(f"{BASE_URL}/api/purchase/orders?status={status}", 
                                   headers=auth_headers)
            assert response.status_code == 200, f"Failed to filter by {status}: {response.text}"
            data = response.json()
            print(f"POs with status '{status}': {len(data['items'])}")


# ==================== PURCHASE PAYMENTS TESTS ====================

class TestPurchasePayments:
    """Test Purchase Payments - view list"""
    
    def test_list_purchase_payments(self, auth_headers):
        """Test GET /api/purchase/payments - List all purchase payments"""
        response = requests.get(f"{BASE_URL}/api/purchase/payments", headers=auth_headers)
        assert response.status_code == 200, f"Failed to list payments: {response.text}"
        data = response.json()
        assert "items" in data, "Response should contain items"
        print(f"Found {len(data['items'])} purchase payments")
        
        # Verify data structure
        if len(data['items']) > 0:
            payment = data['items'][0]
            print(f"First payment: {payment.get('payment_number', 'N/A')}")


# ==================== SALES LIST TESTS ====================

class TestSalesList:
    """Test Sales List - view all sales transactions"""
    
    def test_list_sales_transactions(self, auth_headers):
        """Test GET /api/pos/transactions - List all sales"""
        response = requests.get(f"{BASE_URL}/api/pos/transactions", headers=auth_headers)
        assert response.status_code == 200, f"Failed to list sales: {response.text}"
        data = response.json()
        
        # Response could be list or object with items
        if isinstance(data, list):
            print(f"Found {len(data)} sales transactions")
        elif isinstance(data, dict):
            items = data.get('items', data.get('transactions', []))
            print(f"Found {len(items)} sales transactions")
        
        # Verify structure
        if isinstance(data, list) and len(data) > 0:
            sale = data[0]
            print(f"First sale: {sale.get('invoice_number', sale.get('transaction_number', 'N/A'))}")
        elif isinstance(data, dict) and len(data.get('items', [])) > 0:
            sale = data['items'][0]
            print(f"First sale: {sale.get('invoice_number', sale.get('transaction_number', 'N/A'))}")


# ==================== STOCK CARDS TESTS ====================

class TestStockCards:
    """Test Stock Cards - view stock levels"""
    
    def test_list_stock(self, auth_headers):
        """Test GET /api/inventory/stock - List branch stock"""
        response = requests.get(f"{BASE_URL}/api/inventory/stock", headers=auth_headers)
        assert response.status_code == 200, f"Failed to list stock: {response.text}"
        data = response.json()
        
        if isinstance(data, dict):
            items = data.get('items', [])
            total = data.get('total', 0)
            print(f"Found {len(items)} stock items, total: {total}")
    
    def test_list_low_stock(self, auth_headers):
        """Test GET /api/inventory/stock/low - Get low stock alerts"""
        response = requests.get(f"{BASE_URL}/api/inventory/stock/low", headers=auth_headers)
        assert response.status_code == 200, f"Failed to get low stock: {response.text}"
        data = response.json()
        
        if isinstance(data, list):
            print(f"Found {len(data)} low stock items")
    
    def test_list_products_for_stock(self, auth_headers):
        """Test GET /api/products - List products (alternative stock view)"""
        response = requests.get(f"{BASE_URL}/api/products", headers=auth_headers)
        assert response.status_code == 200, f"Failed to list products: {response.text}"
        data = response.json()
        
        if isinstance(data, list):
            print(f"Found {len(data)} products")
        elif isinstance(data, dict):
            items = data.get('items', data.get('products', []))
            print(f"Found {len(items)} products")
    
    def test_list_stock_movements(self, auth_headers):
        """Test GET /api/inventory/movements - List stock movements"""
        response = requests.get(f"{BASE_URL}/api/inventory/movements", headers=auth_headers)
        assert response.status_code == 200, f"Failed to list movements: {response.text}"
        data = response.json()
        
        if isinstance(data, dict):
            items = data.get('items', [])
            print(f"Found {len(items)} stock movements")


# ==================== ADDITIONAL MASTER DATA TESTS ====================

class TestMasterDataEndpoints:
    """Test additional master data endpoints"""
    
    def test_list_regions(self, auth_headers):
        """Test GET /api/master/regions"""
        response = requests.get(f"{BASE_URL}/api/master/regions", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        print(f"Regions endpoint working")
    
    def test_list_shipping_costs(self, auth_headers):
        """Test GET /api/master/shipping-costs"""
        response = requests.get(f"{BASE_URL}/api/master/shipping-costs", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        print(f"Shipping costs endpoint working")
    
    def test_list_categories(self, auth_headers):
        """Test GET /api/master/categories"""
        response = requests.get(f"{BASE_URL}/api/master/categories", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        print(f"Categories endpoint working")
    
    def test_list_units(self, auth_headers):
        """Test GET /api/master/units"""
        response = requests.get(f"{BASE_URL}/api/master/units", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        print(f"Units endpoint working")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
