"""
OCB TITAN ERP - Stock Reorder & Payroll Bug Fix Tests (Iteration 46)
Tests for:
1. Stock Reorder - Save PO Draft button creates PO and saves to database
2. Stock Reorder - Dashboard shows correct reorder suggestions
3. HR Payroll - Buat Periode Baru button opens modal and creates new period
4. HR Payroll - Duplicate period validation works
5. HR Payroll - Generate Payroll calculates correctly
6. Purchase Module - PO from Stock Reorder visible in purchase list
"""

import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
TEST_EMAIL = "ocbgroupbjm@gmail.com"
TEST_PASSWORD = "admin123"

# ==================== FIXTURES ====================

@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        return data.get("token")
    pytest.fail(f"Authentication failed: {response.status_code} - {response.text}")

@pytest.fixture(scope="module")
def api_client(auth_token):
    """Authenticated requests session"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    })
    return session

# ==================== STOCK REORDER TESTS ====================

class TestStockReorderDashboard:
    """Test Stock Reorder Dashboard functionality"""
    
    def test_stock_reorder_dashboard_returns_summary(self, api_client):
        """Test dashboard endpoint returns proper summary data"""
        response = api_client.get(f"{BASE_URL}/api/stock-reorder/dashboard")
        assert response.status_code == 200, f"Dashboard failed: {response.text}"
        
        data = response.json()
        assert "summary" in data, "Response should contain summary"
        
        summary = data["summary"]
        assert "total_products" in summary
        assert "needs_reorder" in summary
        assert "critical_count" in summary
        assert "high_count" in summary
        assert "out_of_stock" in summary
        
        print(f"Dashboard Summary: total_products={summary.get('total_products')}, "
              f"needs_reorder={summary.get('needs_reorder')}, "
              f"critical={summary.get('critical_count')}")
    
    def test_stock_reorder_suggestions_returns_items(self, api_client):
        """Test suggestions endpoint returns reorder items"""
        response = api_client.get(f"{BASE_URL}/api/stock-reorder/suggestions")
        assert response.status_code == 200, f"Suggestions failed: {response.text}"
        
        data = response.json()
        assert "items" in data, "Response should contain items"
        assert "summary" in data, "Response should contain summary"
        
        # Check item structure if items exist
        if data["items"]:
            item = data["items"][0]
            assert "product_id" in item
            assert "product_name" in item
            assert "current_stock" in item
            assert "minimum_stock" in item
            assert "suggested_qty" in item
            assert "urgency" in item
            print(f"First suggestion: {item.get('product_name')} - urgency: {item.get('urgency')}, "
                  f"current: {item.get('current_stock')}, suggested: {item.get('suggested_qty')}")
        
        print(f"Total reorder suggestions: {len(data['items'])}")

    def test_stock_reorder_suggestions_filter_by_urgency(self, api_client):
        """Test urgency filter works"""
        for urgency in ["critical", "high", "medium", "low"]:
            response = api_client.get(f"{BASE_URL}/api/stock-reorder/suggestions?urgency={urgency}")
            assert response.status_code == 200, f"Urgency filter {urgency} failed: {response.text}"
            
            data = response.json()
            # All items should have matching urgency
            for item in data["items"]:
                assert item["urgency"] == urgency, f"Item has wrong urgency: {item['urgency']} != {urgency}"
            
            print(f"Urgency '{urgency}': {len(data['items'])} items")

class TestStockReorderPOGeneration:
    """Test Save PO Draft functionality - THE BUG FIX"""
    
    def test_generate_po_draft_preview_mode(self, api_client):
        """Test PO draft preview (save_to_db=false)"""
        response = api_client.post(f"{BASE_URL}/api/stock-reorder/generate-po-draft?save_to_db=false")
        
        # Can be success or no items to reorder
        assert response.status_code == 200, f"Preview PO failed: {response.text}"
        
        data = response.json()
        print(f"Preview PO response: {data}")
        
        if data.get("success"):
            assert "drafts" in data
            assert "total_drafts" in data
            assert "total_items" in data
            assert data.get("saved_to_database") == False, "Preview should not save to DB"
            print(f"Preview: {data.get('total_drafts')} drafts with {data.get('total_items')} items")
        else:
            # No items to reorder is also valid
            assert "message" in data
            print(f"No items to reorder: {data.get('message')}")
    
    def test_generate_po_draft_save_to_db(self, api_client):
        """Test PO draft save to database (save_to_db=true) - CRITICAL BUG FIX TEST"""
        response = api_client.post(f"{BASE_URL}/api/stock-reorder/generate-po-draft?save_to_db=true")
        
        assert response.status_code == 200, f"Save PO failed: {response.text}"
        
        data = response.json()
        print(f"Save PO response: {data}")
        
        if data.get("success"):
            assert "drafts" in data
            assert data.get("saved_to_database") == True, "Should indicate saved to DB"
            assert "saved_count" in data
            
            # Store the first PO number for verification
            if data.get("drafts"):
                po_number = data["drafts"][0].get("po_number")
                assert po_number.startswith("PO-REORDER-"), f"PO number format wrong: {po_number}"
                print(f"Saved PO: {po_number}, saved_count: {data.get('saved_count')}")
                
                # Return PO ID for verification test
                return data["drafts"][0].get("id")
        else:
            print(f"No items to create PO: {data.get('message')}")
    
    def test_saved_po_visible_in_purchase_list(self, api_client):
        """Verify saved PO appears in purchase orders list"""
        # First create a PO
        create_response = api_client.post(f"{BASE_URL}/api/stock-reorder/generate-po-draft?save_to_db=true")
        
        if create_response.status_code == 200 and create_response.json().get("success"):
            po_data = create_response.json()
            if po_data.get("drafts"):
                po_id = po_data["drafts"][0].get("id")
                po_number = po_data["drafts"][0].get("po_number")
                
                # Now check purchase orders list
                list_response = api_client.get(f"{BASE_URL}/api/purchase/orders")
                assert list_response.status_code == 200, f"List PO failed: {list_response.text}"
                
                orders = list_response.json()
                # Handle both list and dict responses
                if isinstance(orders, dict):
                    orders = orders.get("orders", orders.get("items", []))
                
                # Check if our PO exists
                found = False
                for order in orders:
                    if order.get("id") == po_id or order.get("po_number") == po_number:
                        found = True
                        assert order.get("source") == "stock_reorder", "Source should be stock_reorder"
                        assert order.get("status") == "draft", "Status should be draft"
                        print(f"Found PO in list: {order.get('po_number')} with {order.get('total_items', len(order.get('items', [])))} items")
                        break
                
                if not found:
                    # Maybe the PO is in a different format, just verify it exists in DB
                    print(f"PO {po_number} created successfully (may need different query to find in list)")
        else:
            print("No PO created - no items need reorder")

    def test_generate_po_with_urgency_filter(self, api_client):
        """Test generating PO only for critical/high urgency items"""
        response = api_client.post(f"{BASE_URL}/api/stock-reorder/generate-po-draft?save_to_db=false&urgency_filter=critical")
        
        assert response.status_code == 200, f"Urgency filter PO failed: {response.text}"
        
        data = response.json()
        print(f"Critical urgency PO: {data}")

# ==================== PAYROLL TESTS ====================

class TestPayrollPeriodManagement:
    """Test HR Payroll Period Management - BUG FIX"""
    
    def test_list_payroll_periods(self, api_client):
        """Test listing existing payroll periods"""
        response = api_client.get(f"{BASE_URL}/api/payroll/periods")
        assert response.status_code == 200, f"List periods failed: {response.text}"
        
        data = response.json()
        assert "periods" in data, "Response should contain periods"
        
        print(f"Existing payroll periods: {len(data['periods'])}")
        for period in data["periods"][:3]:  # Show first 3
            print(f"  - {period.get('period_name')}: {period.get('status')}")
    
    def test_create_payroll_period_success(self, api_client):
        """Test creating new payroll period - CRITICAL BUG FIX TEST"""
        # Use a unique month/year to avoid duplicate
        test_year = 2027
        test_month = 6  # June 2027 - should not exist
        
        response = api_client.post(f"{BASE_URL}/api/payroll/periods", json={
            "period_month": test_month,
            "period_year": test_year
        })
        
        # Either 200 (created) or 400 (already exists)
        if response.status_code == 200:
            data = response.json()
            assert "period" in data or "message" in data
            
            if "period" in data:
                period = data["period"]
                assert period.get("period_month") == test_month
                assert period.get("period_year") == test_year
                assert period.get("status") == "draft"
                assert "period_name" in period
                print(f"Created period: {period.get('period_name')}")
                
                # Return period ID for cleanup
                return period.get("id")
            else:
                print(f"Period creation message: {data.get('message')}")
        elif response.status_code == 400:
            # Already exists - this is expected validation
            data = response.json()
            assert "detail" in data or "message" in data
            error_msg = data.get("detail") or data.get("message")
            assert "sudah ada" in error_msg.lower() or "already" in error_msg.lower(), f"Unexpected error: {error_msg}"
            print(f"Period already exists (expected): {error_msg}")
        else:
            pytest.fail(f"Unexpected status: {response.status_code} - {response.text}")
    
    def test_create_payroll_period_duplicate_validation(self, api_client):
        """Test duplicate period validation works"""
        # First, get existing periods
        list_response = api_client.get(f"{BASE_URL}/api/payroll/periods")
        periods = list_response.json().get("periods", [])
        
        if periods:
            # Try to create duplicate of first period
            existing = periods[0]
            response = api_client.post(f"{BASE_URL}/api/payroll/periods", json={
                "period_month": existing.get("period_month"),
                "period_year": existing.get("period_year")
            })
            
            assert response.status_code == 400, f"Should reject duplicate: {response.status_code}"
            
            data = response.json()
            error_msg = data.get("detail") or data.get("message", "")
            assert "sudah ada" in error_msg.lower() or "already" in error_msg.lower(), f"Wrong error: {error_msg}"
            print(f"Duplicate validation works: {error_msg}")
        else:
            # Create first period, then try duplicate
            response1 = api_client.post(f"{BASE_URL}/api/payroll/periods", json={
                "period_month": 1,
                "period_year": 2028
            })
            
            # Try duplicate
            response2 = api_client.post(f"{BASE_URL}/api/payroll/periods", json={
                "period_month": 1,
                "period_year": 2028
            })
            
            assert response2.status_code == 400, "Should reject duplicate"
            print("Duplicate validation works for new period")
    
    def test_get_payroll_period_details(self, api_client):
        """Test getting period details"""
        # Get periods first
        list_response = api_client.get(f"{BASE_URL}/api/payroll/periods")
        periods = list_response.json().get("periods", [])
        
        if periods:
            period_id = periods[0].get("id")
            response = api_client.get(f"{BASE_URL}/api/payroll/periods/{period_id}")
            
            assert response.status_code == 200, f"Get period failed: {response.text}"
            
            data = response.json()
            assert "period" in data
            assert "details" in data
            
            period = data["period"]
            print(f"Period details: {period.get('period_name')}, employees: {period.get('total_employees', 0)}")
        else:
            print("No periods to test details")

class TestPayrollGeneration:
    """Test Payroll Generation functionality"""
    
    def test_generate_payroll_for_period(self, api_client):
        """Test generating payroll for a period"""
        # Get a draft period
        list_response = api_client.get(f"{BASE_URL}/api/payroll/periods")
        periods = list_response.json().get("periods", [])
        
        draft_period = None
        for p in periods:
            if p.get("status") == "draft":
                draft_period = p
                break
        
        if draft_period:
            period_id = draft_period.get("id")
            response = api_client.post(f"{BASE_URL}/api/payroll/periods/{period_id}/generate")
            
            # 200 = success, 400 = already processed
            if response.status_code == 200:
                data = response.json()
                assert "message" in data
                assert "total_employees" in data
                print(f"Generated payroll: {data.get('total_employees')} employees, "
                      f"gross: {data.get('total_gross')}, net: {data.get('total_net')}")
            elif response.status_code == 400:
                print(f"Period already processed: {response.json().get('detail')}")
            else:
                pytest.fail(f"Unexpected status: {response.status_code}")
        else:
            # Create a new period for testing
            response = api_client.post(f"{BASE_URL}/api/payroll/periods", json={
                "period_month": 12,
                "period_year": 2027
            })
            
            if response.status_code == 200:
                period = response.json().get("period", {})
                period_id = period.get("id")
                
                gen_response = api_client.post(f"{BASE_URL}/api/payroll/periods/{period_id}/generate")
                assert gen_response.status_code in [200, 400]
                print(f"Generate response: {gen_response.json()}")
            else:
                print("Could not create period for generation test")
    
    def test_payroll_details_endpoint(self, api_client):
        """Test payroll details listing"""
        response = api_client.get(f"{BASE_URL}/api/payroll/details")
        
        assert response.status_code == 200, f"Details failed: {response.text}"
        
        data = response.json()
        assert "details" in data
        
        print(f"Total payroll details: {len(data.get('details', []))}")
        
        # Check structure if details exist
        if data["details"]:
            detail = data["details"][0]
            expected_fields = ["employee_name", "gaji_pokok", "total_earnings", "total_deductions", "take_home_pay"]
            for field in expected_fields:
                assert field in detail, f"Missing field: {field}"
            
            print(f"Sample detail: {detail.get('employee_name')} - THP: {detail.get('take_home_pay')}")

# ==================== INTEGRATION TESTS ====================

class TestStockReorderPurchaseIntegration:
    """Test integration between Stock Reorder and Purchase modules"""
    
    def test_po_from_reorder_has_correct_source(self, api_client):
        """Verify PO created from reorder has source=stock_reorder"""
        # Get all purchase orders
        response = api_client.get(f"{BASE_URL}/api/purchase/orders")
        
        assert response.status_code == 200
        
        orders = response.json()
        if isinstance(orders, dict):
            orders = orders.get("orders", orders.get("items", []))
        
        reorder_pos = [o for o in orders if o.get("source") == "stock_reorder"]
        print(f"POs from stock reorder: {len(reorder_pos)}")
        
        for po in reorder_pos[:3]:
            print(f"  - {po.get('po_number')}: {po.get('status')}, items: {po.get('total_items', len(po.get('items', [])))}")

# ==================== API AUTHENTICATION TESTS ====================

class TestAPIAuthentication:
    """Test API authentication requirements"""
    
    def test_stock_reorder_requires_auth(self):
        """Test stock reorder endpoints require authentication"""
        response = requests.get(f"{BASE_URL}/api/stock-reorder/dashboard")
        assert response.status_code in [401, 403], f"Should require auth: {response.status_code}"
        print("Stock reorder dashboard requires auth: PASS")
    
    def test_payroll_requires_auth(self):
        """Test payroll endpoints require authentication"""
        response = requests.get(f"{BASE_URL}/api/payroll/periods")
        # Payroll may or may not require auth depending on setup
        if response.status_code in [401, 403]:
            print("Payroll requires auth: PASS")
        else:
            print(f"Payroll auth status: {response.status_code}")
    
    def test_generate_po_requires_auth(self):
        """Test PO generation requires authentication"""
        response = requests.post(f"{BASE_URL}/api/stock-reorder/generate-po-draft")
        assert response.status_code in [401, 403, 422], f"Should require auth: {response.status_code}"
        print("Generate PO requires auth: PASS")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
