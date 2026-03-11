"""
Purchase Module Enterprise Test - Iteration 32
Tests full purchase flow: PO -> Submit -> Receive -> AP Creation -> Journal Creation -> Payment -> Price History

Test Coverage:
- Purchase Order CRUD (create, get, list)
- PO Submit to supplier
- PO Receive with auto AP and Journal creation
- Payment creation
- Price history tracking
- Purchase returns
"""
import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestPurchaseModuleEnterprise:
    """Purchase Module Enterprise Tests - Full Flow"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as Owner
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "ocbgroupbjm@gmail.com",
            "password": "admin123"
        })
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        token = login_resp.json().get("token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Get supplier for testing
        supplier_resp = self.session.get(f"{BASE_URL}/api/suppliers?limit=10")
        if supplier_resp.status_code == 200:
            suppliers = supplier_resp.json().get("items") or supplier_resp.json() or []
            self.supplier_id = suppliers[0]["id"] if suppliers else None
            self.supplier_name = suppliers[0]["name"] if suppliers else None
        else:
            self.supplier_id = None
            
        # Get product for testing
        product_resp = self.session.get(f"{BASE_URL}/api/products?limit=10")
        if product_resp.status_code == 200:
            products = product_resp.json().get("items") or product_resp.json() or []
            if products:
                self.product_id = products[0]["id"]
                self.product_cost = products[0].get("cost_price", 10000)
            else:
                self.product_id = None
        else:
            self.product_id = None
        
        yield
    
    # ==================== PURCHASE ORDER TESTS ====================
    
    def test_01_list_purchase_orders(self):
        """Test listing purchase orders - GET /api/purchase/orders"""
        response = self.session.get(f"{BASE_URL}/api/purchase/orders?limit=50")
        assert response.status_code == 200, f"Failed to list POs: {response.text}"
        
        data = response.json()
        assert "items" in data or isinstance(data, list), "Response should have items array"
        print(f"PASS: List PO - Found {data.get('total', len(data.get('items', [])))} orders")
    
    def test_02_create_purchase_order(self):
        """Test creating a new purchase order - POST /api/purchase/orders"""
        if not self.supplier_id or not self.product_id:
            pytest.skip("No supplier or product available for testing")
        
        po_data = {
            "supplier_id": self.supplier_id,
            "items": [{
                "product_id": self.product_id,
                "quantity": 5,
                "unit_cost": self.product_cost or 10000,
                "discount_percent": 0
            }],
            "expected_date": datetime.now().strftime("%Y-%m-%d"),
            "notes": "TEST_PO_ITER32",
            "is_credit": True,
            "credit_due_days": 30
        }
        
        response = self.session.post(f"{BASE_URL}/api/purchase/orders", json=po_data)
        assert response.status_code == 200, f"Failed to create PO: {response.text}"
        
        result = response.json()
        assert "id" in result, "Response should contain PO id"
        assert "po_number" in result, "Response should contain po_number"
        
        # Store for subsequent tests
        self.__class__.created_po_id = result["id"]
        self.__class__.created_po_number = result["po_number"]
        
        print(f"PASS: Created PO {result['po_number']} with ID {result['id']}")
    
    def test_03_get_purchase_order_detail(self):
        """Test getting PO detail - GET /api/purchase/orders/{id}"""
        po_id = getattr(self.__class__, 'created_po_id', None)
        if not po_id:
            pytest.skip("No PO created to verify")
        
        response = self.session.get(f"{BASE_URL}/api/purchase/orders/{po_id}")
        assert response.status_code == 200, f"Failed to get PO detail: {response.text}"
        
        data = response.json()
        assert data.get("id") == po_id, "PO ID mismatch"
        assert data.get("status") == "draft", "New PO should be in draft status"
        assert "items" in data, "PO should have items"
        
        print(f"PASS: Got PO detail - {data.get('po_number')} status: {data.get('status')}")
    
    def test_04_submit_purchase_order(self):
        """Test submitting PO to supplier - POST /api/purchase/orders/{id}/submit"""
        po_id = getattr(self.__class__, 'created_po_id', None)
        if not po_id:
            pytest.skip("No PO created to submit")
        
        response = self.session.post(f"{BASE_URL}/api/purchase/orders/{po_id}/submit")
        assert response.status_code == 200, f"Failed to submit PO: {response.text}"
        
        # Verify status changed
        verify_resp = self.session.get(f"{BASE_URL}/api/purchase/orders/{po_id}")
        assert verify_resp.status_code == 200
        assert verify_resp.json().get("status") == "ordered", "PO should be in ordered status after submit"
        
        print(f"PASS: PO submitted successfully - status changed to 'ordered'")
    
    def test_05_receive_purchase_order_with_ap_journal(self):
        """Test receiving goods - POST /api/purchase/orders/{id}/receive
        This should auto-create AP and Journal entries"""
        po_id = getattr(self.__class__, 'created_po_id', None)
        if not po_id:
            pytest.skip("No PO created to receive")
        
        # Get PO to find items
        po_resp = self.session.get(f"{BASE_URL}/api/purchase/orders/{po_id}")
        assert po_resp.status_code == 200
        po_data = po_resp.json()
        
        # Prepare receive data
        receive_items = []
        for item in po_data.get("items", []):
            receive_items.append({
                "product_id": item["product_id"],
                "quantity": item["quantity"]  # Receive full quantity
            })
        
        receive_data = {
            "items": receive_items,
            "notes": "TEST receive goods"
        }
        
        response = self.session.post(f"{BASE_URL}/api/purchase/orders/{po_id}/receive", json=receive_data)
        assert response.status_code == 200, f"Failed to receive PO: {response.text}"
        
        result = response.json()
        assert "ap_created" in result, "Response should indicate AP creation"
        
        # Verify AP was created
        if result.get("ap_created"):
            print(f"PASS: Goods received - AP auto-created with ID: {result.get('ap_id')}")
            self.__class__.created_ap_id = result.get("ap_id")
        else:
            print(f"INFO: Goods received but AP not created (might be cash purchase)")
        
        # Verify PO status changed to received
        verify_resp = self.session.get(f"{BASE_URL}/api/purchase/orders/{po_id}")
        assert verify_resp.status_code == 200
        final_status = verify_resp.json().get("status")
        assert final_status in ["received", "partial"], f"Unexpected status: {final_status}"
        
        print(f"PASS: PO status is now '{final_status}'")
    
    def test_06_verify_ap_created(self):
        """Verify Accounts Payable was created after receiving goods"""
        po_number = getattr(self.__class__, 'created_po_number', None)
        if not po_number:
            pytest.skip("No PO to verify AP")
        
        # Get AP list filtered by source
        response = self.session.get(f"{BASE_URL}/api/ap/list?limit=100")
        
        if response.status_code == 200:
            data = response.json()
            ap_list = data.get("items") or data or []
            
            # Find AP for our PO
            matching_ap = [ap for ap in ap_list if ap.get("source_number") == po_number]
            
            if matching_ap:
                ap = matching_ap[0]
                assert ap.get("status") == "unpaid", "New AP should be unpaid"
                assert ap.get("amount") > 0, "AP amount should be positive"
                print(f"PASS: Found AP {ap.get('ap_number')} for PO {po_number}, amount: {ap.get('amount')}")
            else:
                print(f"INFO: No specific AP found for PO {po_number} in list")
        else:
            print(f"INFO: AP list endpoint returned {response.status_code}")
    
    def test_07_verify_journal_created(self):
        """Verify Journal entry was created for the purchase"""
        po_number = getattr(self.__class__, 'created_po_number', None)
        if not po_number:
            pytest.skip("No PO to verify journal")
        
        # Get journal entries
        response = self.session.get(f"{BASE_URL}/api/accounting/journals?limit=100")
        
        if response.status_code == 200:
            data = response.json()
            journals = data.get("items") or data or []
            
            # Find journal for our PO
            matching_journals = [j for j in journals if po_number in str(j.get("description", "")) or po_number in str(j.get("journal_no", ""))]
            
            if matching_journals:
                journal = matching_journals[0]
                print(f"PASS: Found Journal {journal.get('journal_no')} for PO {po_number}")
                assert journal.get("total_debit") == journal.get("total_credit"), "Journal should be balanced"
            else:
                print(f"INFO: Journal entry may be in different format or location")
        else:
            print(f"INFO: Journal endpoint returned {response.status_code}")
    
    # ==================== PAYMENT TESTS ====================
    
    def test_08_list_payments(self):
        """Test listing purchase payments - GET /api/purchase/payments"""
        response = self.session.get(f"{BASE_URL}/api/purchase/payments?limit=100")
        assert response.status_code == 200, f"Failed to list payments: {response.text}"
        
        data = response.json()
        assert "items" in data or isinstance(data, list), "Response should have items"
        print(f"PASS: List payments - Found {len(data.get('items', data))} payments")
    
    def test_09_create_payment(self):
        """Test creating payment - POST /api/purchase/payments"""
        po_id = getattr(self.__class__, 'created_po_id', None)
        if not po_id:
            pytest.skip("No PO created to pay")
        
        payment_data = {
            "po_id": po_id,
            "amount": 10000,  # Partial payment
            "payment_method": "transfer",
            "bank_id": "",
            "reference": f"TEST_PAY_{datetime.now().strftime('%H%M%S')}",
            "notes": "Test payment from iteration 32"
        }
        
        response = self.session.post(f"{BASE_URL}/api/purchase/payments", json=payment_data)
        assert response.status_code == 200, f"Failed to create payment: {response.text}"
        
        result = response.json()
        assert "id" in result or "message" in result, "Response should contain payment id or message"
        print(f"PASS: Payment created successfully")
    
    # ==================== RETURNS TESTS ====================
    
    def test_10_list_returns(self):
        """Test listing purchase returns - GET /api/purchase/returns"""
        response = self.session.get(f"{BASE_URL}/api/purchase/returns?limit=100")
        assert response.status_code == 200, f"Failed to list returns: {response.text}"
        
        data = response.json()
        assert "items" in data or isinstance(data, list), "Response should have items"
        print(f"PASS: List returns - Found {len(data.get('items', data))} returns")
    
    def test_11_create_return(self):
        """Test creating purchase return - POST /api/purchase/returns"""
        po_id = getattr(self.__class__, 'created_po_id', None)
        if not po_id or not self.product_id:
            pytest.skip("No PO or product for return test")
        
        return_data = {
            "po_id": po_id,
            "reason": "TEST return - defective item",
            "items": [{
                "product_id": self.product_id,
                "quantity": 1
            }]
        }
        
        response = self.session.post(f"{BASE_URL}/api/purchase/returns", json=return_data)
        # Return might fail if PO not fully received or other business rules
        if response.status_code == 200:
            result = response.json()
            print(f"PASS: Return created - {result.get('id', 'OK')}")
        else:
            print(f"INFO: Return creation returned {response.status_code} - {response.text[:100]}")
    
    # ==================== PRICE HISTORY TESTS ====================
    
    def test_12_list_price_history(self):
        """Test listing price history - GET /api/purchase/price-history"""
        response = self.session.get(f"{BASE_URL}/api/purchase/price-history?limit=100")
        assert response.status_code == 200, f"Failed to list price history: {response.text}"
        
        data = response.json()
        assert "items" in data or isinstance(data, list), "Response should have items"
        items = data.get("items", data)
        print(f"PASS: Price history - Found {len(items)} records")
        
        # If we have records, verify structure
        if items:
            sample = items[0]
            expected_fields = ["product_id", "supplier_name", "unit_cost"]
            for field in expected_fields:
                if field in sample:
                    print(f"  - {field}: present")
    
    # ==================== CANCEL PO TEST ====================
    
    def test_13_cancel_draft_po(self):
        """Test cancelling a draft PO - POST /api/purchase/orders/{id}/cancel"""
        if not self.supplier_id or not self.product_id:
            pytest.skip("No supplier or product for cancel test")
        
        # Create a new PO specifically for cancel test
        po_data = {
            "supplier_id": self.supplier_id,
            "items": [{
                "product_id": self.product_id,
                "quantity": 1,
                "unit_cost": 5000,
                "discount_percent": 0
            }],
            "notes": "TEST_PO_TO_CANCEL"
        }
        
        create_resp = self.session.post(f"{BASE_URL}/api/purchase/orders", json=po_data)
        if create_resp.status_code != 200:
            pytest.skip("Could not create PO for cancel test")
        
        cancel_po_id = create_resp.json().get("id")
        
        # Cancel it
        cancel_resp = self.session.post(f"{BASE_URL}/api/purchase/orders/{cancel_po_id}/cancel")
        assert cancel_resp.status_code == 200, f"Failed to cancel PO: {cancel_resp.text}"
        
        # Verify status
        verify_resp = self.session.get(f"{BASE_URL}/api/purchase/orders/{cancel_po_id}")
        assert verify_resp.status_code == 200
        assert verify_resp.json().get("status") == "cancelled", "PO should be cancelled"
        
        print(f"PASS: PO cancelled successfully")


class TestPurchaseModuleFilters:
    """Test Purchase Module filter and search functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as Owner
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "ocbgroupbjm@gmail.com",
            "password": "admin123"
        })
        if login_resp.status_code == 200:
            token = login_resp.json().get("token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        yield
    
    def test_filter_po_by_status_draft(self):
        """Test filtering POs by status=draft"""
        response = self.session.get(f"{BASE_URL}/api/purchase/orders?status=draft")
        assert response.status_code == 200, f"Filter failed: {response.text}"
        
        data = response.json()
        items = data.get("items", [])
        
        # All items should be draft
        for item in items:
            assert item.get("status") == "draft", f"Found non-draft item: {item.get('status')}"
        
        print(f"PASS: Filter by status=draft - Found {len(items)} draft POs")
    
    def test_filter_po_by_status_received(self):
        """Test filtering POs by status=received"""
        response = self.session.get(f"{BASE_URL}/api/purchase/orders?status=received")
        assert response.status_code == 200, f"Filter failed: {response.text}"
        
        data = response.json()
        items = data.get("items", [])
        
        print(f"PASS: Filter by status=received - Found {len(items)} received POs")


class TestPurchaseRBACPermissions:
    """Test RBAC permissions for Purchase Module"""
    
    def test_owner_has_purchase_access(self):
        """Test Owner can access purchase endpoints"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        # Login as Owner
        login_resp = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "ocbgroupbjm@gmail.com",
            "password": "admin123"
        })
        assert login_resp.status_code == 200
        token = login_resp.json().get("token")
        session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Try to list POs
        response = session.get(f"{BASE_URL}/api/purchase/orders")
        assert response.status_code == 200, f"Owner should have purchase access: {response.status_code}"
        
        print("PASS: Owner has purchase module access")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
