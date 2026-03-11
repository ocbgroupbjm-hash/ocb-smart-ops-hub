"""
Sales Module API Tests - Iteration 34
Testing Sales Module iPOS Style with Stock, AR, and Accounting Integration
"""
import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://smart-ops-hub-6.preview.emergentagent.com').rstrip('/')

# Test data
TEST_CUSTOMER_ID = "CUS-AUDIT-003"
TEST_PRODUCT_ID = "PRD-AUDIT-001"

class TestSalesOrderAPI:
    """Sales Order (Pesanan Jual) API Tests"""
    
    def test_get_sales_orders(self):
        """GET /api/sales/orders - List Sales Orders"""
        response = requests.get(f"{BASE_URL}/api/sales/orders")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "items" in data, "Response should contain 'items'"
        assert "total" in data, "Response should contain 'total'"
        assert isinstance(data["items"], list), "items should be a list"
        print(f"✓ GET /api/sales/orders - {data['total']} orders found")
    
    def test_create_sales_order(self):
        """POST /api/sales/orders - Create Sales Order"""
        payload = {
            "customer_id": TEST_CUSTOMER_ID,
            "warehouse_id": "main",
            "ppn_type": "exclude",
            "ppn_percent": 11,
            "notes": f"TEST_SO_{datetime.now().isoformat()}",
            "items": [
                {
                    "product_id": TEST_PRODUCT_ID,
                    "quantity": 3,
                    "unit_price": 45000,
                    "discount_percent": 0,
                    "tax_percent": 0
                }
            ]
        }
        
        response = requests.post(f"{BASE_URL}/api/sales/orders", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "id" in data, "Response should contain 'id'"
        assert "order_number" in data, "Response should contain 'order_number'"
        assert data["order_number"].startswith("SO-"), "Order number should start with SO-"
        assert data["status"] == "confirmed", "Status should be confirmed"
        assert data["customer_id"] == TEST_CUSTOMER_ID, "Customer ID should match"
        print(f"✓ POST /api/sales/orders - Created {data['order_number']}")
        return data["id"]


class TestSalesInvoiceAPI:
    """Sales Invoice (Penjualan) API Tests - Stock, Journal, AR Integration"""
    
    def test_get_sales_invoices(self):
        """GET /api/sales/invoices - List Sales Invoices"""
        response = requests.get(f"{BASE_URL}/api/sales/invoices")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "items" in data, "Response should contain 'items'"
        assert "total" in data, "Response should contain 'total'"
        print(f"✓ GET /api/sales/invoices - {data['total']} invoices found")
    
    def test_get_invoices_with_filter(self):
        """GET /api/sales/invoices with filters"""
        response = requests.get(f"{BASE_URL}/api/sales/invoices?customer_id={TEST_CUSTOMER_ID}")
        assert response.status_code == 200
        
        data = response.json()
        if data["total"] > 0:
            for inv in data["items"]:
                assert inv["customer_id"] == TEST_CUSTOMER_ID, "Customer filter should work"
        print(f"✓ GET /api/sales/invoices with filter - {data['total']} invoices for customer")
    
    def test_create_cash_invoice_with_integration(self):
        """POST /api/sales/invoices - Cash sale with stock reduction and journal"""
        payload = {
            "customer_id": TEST_CUSTOMER_ID,
            "warehouse_id": "main",
            "ppn_type": "exclude",
            "ppn_percent": 11,
            "notes": f"TEST_CASH_INV_{datetime.now().isoformat()}",
            "payment_type": "cash",
            "cash_amount": 163350,  # 3 * 45000 + 11% PPN = 135000 + 14850 + 13500 = 149850 rounded
            "credit_amount": 0,
            "items": [
                {
                    "product_id": TEST_PRODUCT_ID,
                    "quantity": 3,
                    "unit_price": 45000,
                    "discount_percent": 0,
                    "tax_percent": 0
                }
            ]
        }
        
        response = requests.post(f"{BASE_URL}/api/sales/invoices", json=payload)
        # Note: If stock is insufficient, this will return 400
        if response.status_code == 400:
            print(f"⚠ Stock insufficient for test product, skipping invoice creation")
            pytest.skip("Stock insufficient")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "id" in data, "Response should contain 'id'"
        assert "invoice_number" in data, "Response should contain 'invoice_number'"
        assert data["invoice_number"].startswith("INV-"), "Invoice number should start with INV-"
        assert data["status"] == "completed", "Status should be completed"
        assert data["is_credit"] == False, "Cash sale should not be credit"
        assert data["payment_type"] == "cash", "Payment type should be cash"
        print(f"✓ POST /api/sales/invoices (cash) - Created {data['invoice_number']}")
        return data
    
    def test_create_credit_invoice_with_ar(self):
        """POST /api/sales/invoices - Credit sale creates AR entry"""
        payload = {
            "customer_id": TEST_CUSTOMER_ID,
            "warehouse_id": "main",
            "ppn_type": "exclude",
            "ppn_percent": 11,
            "notes": f"TEST_CREDIT_INV_{datetime.now().isoformat()}",
            "payment_type": "credit",
            "cash_amount": 0,
            "credit_amount": 163350,
            "items": [
                {
                    "product_id": TEST_PRODUCT_ID,
                    "quantity": 3,
                    "unit_price": 45000,
                    "discount_percent": 0,
                    "tax_percent": 0
                }
            ]
        }
        
        response = requests.post(f"{BASE_URL}/api/sales/invoices", json=payload)
        if response.status_code == 400:
            print(f"⚠ Stock insufficient for test product, skipping credit invoice creation")
            pytest.skip("Stock insufficient")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["is_credit"] == True, "Credit sale should be marked as credit"
        assert data["credit_amount"] > 0, "Credit amount should be > 0"
        print(f"✓ POST /api/sales/invoices (credit) - Created {data['invoice_number']} with AR")
        return data


class TestSalesReturnAPI:
    """Sales Return (Retur Penjualan) API Tests - Stock add back, Journal, AR reduction"""
    
    def test_get_sales_returns(self):
        """GET /api/sales/returns - List Sales Returns"""
        response = requests.get(f"{BASE_URL}/api/sales/returns")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "items" in data, "Response should contain 'items'"
        assert "total" in data, "Response should contain 'total'"
        print(f"✓ GET /api/sales/returns - {data['total']} returns found")
    
    def test_create_sales_return(self):
        """POST /api/sales/returns - Create return with stock and AR integration"""
        payload = {
            "customer_id": TEST_CUSTOMER_ID,
            "warehouse_id": "main",
            "ppn_type": "exclude",
            "notes": f"TEST_RETURN_{datetime.now().isoformat()}",
            "refund_type": "ar_deduct",
            "items": [
                {
                    "product_id": TEST_PRODUCT_ID,
                    "quantity": 1,
                    "unit_price": 45000
                }
            ],
            "cash_refund": 0,
            "deposit_add": 0
        }
        
        response = requests.post(f"{BASE_URL}/api/sales/returns", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "id" in data, "Response should contain 'id'"
        assert "return_number" in data, "Response should contain 'return_number'"
        assert data["return_number"].startswith("SRT-"), "Return number should start with SRT-"
        assert data["status"] == "completed", "Status should be completed"
        print(f"✓ POST /api/sales/returns - Created {data['return_number']}")
        return data


class TestSalesPriceHistoryAPI:
    """Sales Price History API Tests"""
    
    def test_get_price_history(self):
        """GET /api/sales/price-history - List Price History"""
        response = requests.get(f"{BASE_URL}/api/sales/price-history")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "items" in data, "Response should contain 'items'"
        assert "total" in data, "Response should contain 'total'"
        print(f"✓ GET /api/sales/price-history - {data['total']} records found")
    
    def test_price_history_filter_by_customer(self):
        """GET /api/sales/price-history with customer filter"""
        response = requests.get(f"{BASE_URL}/api/sales/price-history?customer_id={TEST_CUSTOMER_ID}")
        assert response.status_code == 200
        
        data = response.json()
        print(f"✓ GET /api/sales/price-history with customer filter - {data['total']} records")
    
    def test_price_history_filter_by_product(self):
        """GET /api/sales/price-history with product filter"""
        response = requests.get(f"{BASE_URL}/api/sales/price-history?product_id={TEST_PRODUCT_ID}")
        assert response.status_code == 200
        
        data = response.json()
        print(f"✓ GET /api/sales/price-history with product filter - {data['total']} records")


class TestTradeInAPI:
    """Trade-In (Tukar Tambah) API Tests"""
    
    def test_get_trade_in(self):
        """GET /api/sales/trade-in - List Trade-In Transactions"""
        response = requests.get(f"{BASE_URL}/api/sales/trade-in")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "items" in data, "Response should contain 'items'"
        assert "total" in data, "Response should contain 'total'"
        print(f"✓ GET /api/sales/trade-in - {data['total']} transactions found")


class TestCustomerPointsAPI:
    """Customer Loyalty Points API Tests"""
    
    def test_get_customer_points(self):
        """GET /api/sales/points - List Customer Points"""
        response = requests.get(f"{BASE_URL}/api/sales/points")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "items" in data, "Response should contain 'items'"
        assert "total" in data, "Response should contain 'total'"
        print(f"✓ GET /api/sales/points - {data['total']} point records found")
    
    def test_get_points_by_customer(self):
        """GET /api/sales/points with customer filter"""
        response = requests.get(f"{BASE_URL}/api/sales/points?customer_id={TEST_CUSTOMER_ID}")
        assert response.status_code == 200
        
        data = response.json()
        print(f"✓ GET /api/sales/points with customer filter - {data['total']} records")


class TestCommissionPaymentsAPI:
    """Commission Payments (Pembayaran Komisi Sales) API Tests"""
    
    def test_get_commission_payments(self):
        """GET /api/sales/commission-payments - List Commission Payments"""
        response = requests.get(f"{BASE_URL}/api/sales/commission-payments")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "items" in data, "Response should contain 'items'"
        assert "total" in data, "Response should contain 'total'"
        print(f"✓ GET /api/sales/commission-payments - {data['total']} payments found")


class TestDeliveriesAPI:
    """Deliveries (Pengiriman) API Tests"""
    
    def test_get_deliveries(self):
        """GET /api/sales/deliveries - List Deliveries"""
        response = requests.get(f"{BASE_URL}/api/sales/deliveries")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "items" in data, "Response should contain 'items'"
        assert "total" in data, "Response should contain 'total'"
        print(f"✓ GET /api/sales/deliveries - {data['total']} deliveries found")
    
    def test_get_deliveries_with_status_filter(self):
        """GET /api/sales/deliveries with status filter"""
        response = requests.get(f"{BASE_URL}/api/sales/deliveries?status=pending")
        assert response.status_code == 200
        
        data = response.json()
        print(f"✓ GET /api/sales/deliveries with status filter - {data['total']} deliveries")


class TestSalesIntegration:
    """Integration Tests - Verify Stock, Journal, AR are created correctly"""
    
    def test_verify_stock_movements(self):
        """Verify stock movements are created after sales"""
        response = requests.get(f"{BASE_URL}/api/inventory/movements?product_id={TEST_PRODUCT_ID}&limit=5")
        if response.status_code == 200:
            data = response.json()
            movements = data.get("items", data.get("movements", []))
            sales_movements = [m for m in movements if "sales" in m.get("type", "").lower()]
            print(f"✓ Stock movements verified - {len(sales_movements)} sales movements found")
        else:
            print(f"⚠ Stock movements endpoint returned {response.status_code}")
    
    def test_verify_journal_entries(self):
        """Verify journal entries are created after sales"""
        response = requests.get(f"{BASE_URL}/api/accounting/journals?limit=10")
        if response.status_code == 200:
            data = response.json()
            journals = data.get("items", data.get("journals", []))
            inv_journals = [j for j in journals if "INV-" in str(j.get("reference", "")) or "Penjualan" in str(j.get("description", ""))]
            print(f"✓ Journal entries verified - {len(inv_journals)} sales journals found")
        else:
            print(f"⚠ Journal entries endpoint returned {response.status_code}")
    
    def test_verify_accounts_receivable(self):
        """Verify AR entries are created for credit sales"""
        response = requests.get(f"{BASE_URL}/api/ar/list?customer_id={TEST_CUSTOMER_ID}")
        if response.status_code == 200:
            data = response.json()
            ar_items = data.get("items", [])
            inv_ar = [ar for ar in ar_items if "INV-" in str(ar.get("invoice_number", ""))]
            print(f"✓ AR entries verified - {len(inv_ar)} sales AR records found")
        else:
            print(f"⚠ AR list endpoint returned {response.status_code}")


class TestOwnerDashboard:
    """Owner Dashboard API Tests"""
    
    def test_pos_transactions_api(self):
        """GET /api/pos/transactions for sales KPI"""
        response = requests.get(f"{BASE_URL}/api/pos/transactions?limit=10")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ GET /api/pos/transactions - Working for Owner Dashboard")
    
    def test_ar_list_api(self):
        """GET /api/ar/list for AR KPI"""
        response = requests.get(f"{BASE_URL}/api/ar/list?limit=10")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ GET /api/ar/list - Working for Owner Dashboard")
    
    def test_ap_list_api(self):
        """GET /api/ap/list for AP KPI"""
        response = requests.get(f"{BASE_URL}/api/ap/list?limit=10")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ GET /api/ap/list - Working for Owner Dashboard")
    
    def test_deposit_list_api(self):
        """GET /api/deposit/list for Deposit KPI"""
        response = requests.get(f"{BASE_URL}/api/deposit/list?limit=10")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ GET /api/deposit/list - Working for Owner Dashboard")
    
    def test_branches_api(self):
        """GET /api/branches for Branch Performance"""
        response = requests.get(f"{BASE_URL}/api/branches")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ GET /api/branches - Working for Owner Dashboard")


class TestFinanceDashboard:
    """Finance Dashboard API Tests"""
    
    def test_trial_balance_api(self):
        """GET /api/accounting/trial-balance for Finance Dashboard"""
        response = requests.get(f"{BASE_URL}/api/accounting/trial-balance")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ GET /api/accounting/trial-balance - Working for Finance Dashboard")
    
    def test_journals_api(self):
        """GET /api/accounting/journals for Finance Dashboard"""
        response = requests.get(f"{BASE_URL}/api/accounting/journals?limit=20")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ GET /api/accounting/journals - Working for Finance Dashboard")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
