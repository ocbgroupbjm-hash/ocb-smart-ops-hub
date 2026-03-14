# OCB TITAN ERP - Phase E System Hardening: Full E2E Regression Testing
# Test file for iteration 65
# Tests: Export/Import, Branch creation, Tenant delete warning, Sales/Purchase/AP/AR flows, Trial Balance, Balance Sheet

import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "ocbgroupbjm@gmail.com"
TEST_PASSWORD = "admin123"
TEST_TENANT = "ocb_titan"

@pytest.fixture(scope="module")
def auth_token():
    """Authenticate and get token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "database": TEST_TENANT
    })
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")

@pytest.fixture(scope="module")
def api_client(auth_token):
    """Create authenticated API client"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    })
    return session


class TestExportEndpoints:
    """Test Export Excel functionality"""
    
    def test_export_products_returns_excel(self, api_client):
        """GET /api/export/products returns valid Excel file"""
        response = api_client.get(f"{BASE_URL}/api/export/products")
        
        # Accept 200 OK or 404 (no products to export)
        assert response.status_code in [200, 404], f"Expected 200 or 404, got {response.status_code}: {response.text}"
        
        if response.status_code == 200:
            # Verify content type is Excel
            content_type = response.headers.get('Content-Type', '')
            assert 'spreadsheet' in content_type or 'excel' in content_type or 'application/octet-stream' in content_type, \
                f"Expected Excel content type, got: {content_type}"
            
            # Verify has content disposition with filename
            content_disp = response.headers.get('Content-Disposition', '')
            assert 'attachment' in content_disp, f"Expected attachment disposition, got: {content_disp}"
            assert '.xlsx' in content_disp, f"Expected .xlsx filename, got: {content_disp}"
            
            print(f"SUCCESS: Export products returned Excel file, size: {len(response.content)} bytes")
        else:
            print(f"INFO: No products to export (404)")
    
    def test_export_customers_returns_excel(self, api_client):
        """GET /api/export/customers returns valid Excel file"""
        response = api_client.get(f"{BASE_URL}/api/export/customers")
        
        assert response.status_code in [200, 404], f"Expected 200 or 404, got {response.status_code}: {response.text}"
        
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '')
            assert 'spreadsheet' in content_type or 'excel' in content_type or 'application/octet-stream' in content_type
            print(f"SUCCESS: Export customers returned Excel file, size: {len(response.content)} bytes")
        else:
            print(f"INFO: No customers to export (404)")
    
    def test_export_suppliers_returns_excel(self, api_client):
        """GET /api/export/suppliers returns valid Excel file"""
        response = api_client.get(f"{BASE_URL}/api/export/suppliers")
        
        assert response.status_code in [200, 404], f"Expected 200 or 404, got {response.status_code}: {response.text}"
        
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '')
            assert 'spreadsheet' in content_type or 'excel' in content_type or 'application/octet-stream' in content_type
            print(f"SUCCESS: Export suppliers returned Excel file, size: {len(response.content)} bytes")
        else:
            print(f"INFO: No suppliers to export (404)")
    
    def test_export_branches_returns_excel(self, api_client):
        """GET /api/export/branches returns valid Excel file"""
        response = api_client.get(f"{BASE_URL}/api/export/branches")
        
        assert response.status_code in [200, 404], f"Expected 200 or 404, got {response.status_code}: {response.text}"
        
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '')
            assert 'spreadsheet' in content_type or 'excel' in content_type or 'application/octet-stream' in content_type
            print(f"SUCCESS: Export branches returned Excel file, size: {len(response.content)} bytes")
        else:
            print(f"INFO: No branches to export (404)")


class TestTemplateEndpoints:
    """Test Template download functionality"""
    
    def test_template_products_returns_xlsx(self, api_client):
        """GET /api/template/products returns template xlsx"""
        response = api_client.get(f"{BASE_URL}/api/template/products")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        content_type = response.headers.get('Content-Type', '')
        assert 'spreadsheet' in content_type or 'excel' in content_type or 'application/octet-stream' in content_type, \
            f"Expected Excel content type, got: {content_type}"
        
        content_disp = response.headers.get('Content-Disposition', '')
        assert 'template_products.xlsx' in content_disp or '.xlsx' in content_disp, \
            f"Expected template_products.xlsx filename, got: {content_disp}"
        
        print(f"SUCCESS: Template products returned xlsx, size: {len(response.content)} bytes")
    
    def test_template_customers_returns_xlsx(self, api_client):
        """GET /api/template/customers returns template xlsx"""
        response = api_client.get(f"{BASE_URL}/api/template/customers")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"SUCCESS: Template customers returned xlsx, size: {len(response.content)} bytes")
    
    def test_template_suppliers_returns_xlsx(self, api_client):
        """GET /api/template/suppliers returns template xlsx"""
        response = api_client.get(f"{BASE_URL}/api/template/suppliers")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"SUCCESS: Template suppliers returned xlsx, size: {len(response.content)} bytes")


class TestBranchCreation:
    """Test Branch CRUD operations"""
    
    def test_create_branch_with_code_field(self, api_client):
        """POST /api/branches creates branch successfully with code field"""
        test_code = f"TST{uuid.uuid4().hex[:4].upper()}"
        branch_data = {
            "code": test_code,
            "name": f"Test Branch {test_code}",
            "address": "Test Address 123",
            "city": "Banjarmasin",
            "phone": "08123456789",
            "email": f"test_{test_code.lower()}@example.com",
            "is_warehouse": False
        }
        
        response = api_client.post(f"{BASE_URL}/api/branches", json=branch_data)
        
        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "id" in data, "Response should contain branch ID"
        
        print(f"SUCCESS: Branch created with ID: {data.get('id')}, code: {test_code}")
        
        # Clean up - try to delete the created branch (if endpoint exists)
        # No cleanup needed as this is just a test branch
        return data.get('id')
    
    def test_list_branches(self, api_client):
        """GET /api/branches returns list of branches"""
        response = api_client.get(f"{BASE_URL}/api/branches")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Should be list or dict with items
        if isinstance(data, list):
            print(f"SUCCESS: Got {len(data)} branches")
            if len(data) > 0:
                assert "id" in data[0], "Branch should have id"
                assert "name" in data[0], "Branch should have name"
        elif isinstance(data, dict) and "items" in data:
            print(f"SUCCESS: Got {len(data['items'])} branches")
        else:
            print(f"SUCCESS: Branches response: {type(data)}")


class TestTenantDeleteWarning:
    """Test Tenant delete endpoint with warning"""
    
    def test_tenant_delete_without_confirm_returns_warning(self, api_client):
        """DELETE /api/tenant/{id}?confirm_delete=false returns warning with transaction counts"""
        # Use the current tenant for testing (ocb_titan)
        tenant_id = TEST_TENANT
        
        response = api_client.delete(
            f"{BASE_URL}/api/tenant/{tenant_id}",
            params={"confirm_delete": False, "backup_before_delete": True}
        )
        
        # Should return 200 with warning status, not actually delete
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Check for warning/confirmation required
        assert data.get("status") in ["warning", "requires_confirmation"], \
            f"Expected warning or requires_confirmation status, got: {data.get('status')}"
        
        # If warning, should include transaction counts
        if data.get("status") == "warning":
            assert "transaction_counts" in data, "Warning response should include transaction_counts"
            tx_counts = data.get("transaction_counts", {})
            print(f"SUCCESS: Tenant delete warning returned with transaction counts:")
            print(f"  - Sales: {tx_counts.get('sales', 0)}")
            print(f"  - Purchases: {tx_counts.get('purchases', 0)}")
            print(f"  - Journals: {tx_counts.get('journals', 0)}")
            print(f"  - AR: {tx_counts.get('ar', 0)}")
            print(f"  - AP: {tx_counts.get('ap', 0)}")
        else:
            print(f"SUCCESS: Tenant delete requires confirmation, status: {data.get('status')}")


class TestSalesFlow:
    """Test Sales invoice list and operations"""
    
    def test_sales_list_page_loads(self, api_client):
        """Sales list API returns data - /api/sales/invoices"""
        response = api_client.get(f"{BASE_URL}/api/sales/invoices")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Check structure
        if isinstance(data, dict):
            items = data.get("items", data.get("invoices", []))
        else:
            items = data
        
        print(f"SUCCESS: Sales list returned {len(items)} invoices")
        
        if len(items) > 0:
            first = items[0]
            assert "id" in first or "invoice_number" in first, "Invoice should have id or invoice_number"
    
    def test_sales_orders_list(self, api_client):
        """Sales orders list API - /api/sales/orders"""
        response = api_client.get(f"{BASE_URL}/api/sales/orders")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        items = data.get("items", data.get("orders", [])) if isinstance(data, dict) else data
        
        print(f"SUCCESS: Sales orders list returned {len(items)} orders")


class TestPurchaseFlow:
    """Test Purchase order list and operations"""
    
    def test_purchase_list_loads(self, api_client):
        """Purchase orders list API returns data"""
        response = api_client.get(f"{BASE_URL}/api/purchase/orders")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        if isinstance(data, dict):
            items = data.get("items", data.get("orders", []))
        else:
            items = data
        
        print(f"SUCCESS: Purchase list returned {len(items)} orders")


class TestAccountsPayable:
    """Test AP (Accounts Payable) functionality"""
    
    def test_ap_list_loads(self, api_client):
        """AP list API returns data - /api/ap/list"""
        response = api_client.get(f"{BASE_URL}/api/ap/list")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        if isinstance(data, dict):
            items = data.get("items", data.get("payables", []))
        else:
            items = data
        
        print(f"SUCCESS: AP list returned {len(items)} payables")
    
    def test_ap_aging_report(self, api_client):
        """AP aging report - /api/ap/aging"""
        response = api_client.get(f"{BASE_URL}/api/ap/aging")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        print(f"SUCCESS: AP aging report returned")
    
    def test_ap_cash_bank_accounts(self, api_client):
        """AP should be able to get cash/bank accounts for payment dropdown"""
        # Try multiple possible endpoints
        endpoints = [
            f"{BASE_URL}/api/account-settings/cash-bank",
            f"{BASE_URL}/api/accounts/cash-bank",
        ]
        
        success = False
        for endpoint in endpoints:
            response = api_client.get(endpoint)
            if response.status_code == 200:
                data = response.json()
                accounts = data.get("accounts", data.get("items", []))
                
                print(f"SUCCESS: Got {len(accounts)} cash/bank accounts from {endpoint}")
                
                if len(accounts) > 0:
                    for acc in accounts[:3]:
                        print(f"  - {acc.get('code')}: {acc.get('name')} ({acc.get('type', 'N/A')})")
                success = True
                break
        
        assert success, f"Could not get cash/bank accounts from any endpoint"


class TestAccountsReceivable:
    """Test AR (Accounts Receivable) functionality"""
    
    def test_ar_list_loads(self, api_client):
        """AR list API returns data - /api/ar/list"""
        response = api_client.get(f"{BASE_URL}/api/ar/list")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        if isinstance(data, dict):
            items = data.get("items", data.get("receivables", []))
        else:
            items = data
        
        print(f"SUCCESS: AR list returned {len(items)} receivables")
    
    def test_ar_aging_report(self, api_client):
        """AR aging report - /api/ar/aging"""
        response = api_client.get(f"{BASE_URL}/api/ar/aging")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        print(f"SUCCESS: AR aging report returned")


class TestFinancialReports:
    """Test Financial Reports - Trial Balance and Balance Sheet"""
    
    def test_trial_balance_api_returns_data(self, api_client):
        """Trial Balance API returns data"""
        # Try the new unified endpoint first
        response = api_client.get(f"{BASE_URL}/api/accounting/financial/trial-balance")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify response structure
        assert "accounts" in data or "items" in data, "Trial balance should have accounts/items"
        assert "totals" in data or ("total_debit" in data and "total_credit" in data), \
            "Trial balance should have totals"
        
        accounts = data.get("accounts", data.get("items", []))
        print(f"SUCCESS: Trial Balance returned {len(accounts)} accounts")
        
        # Check balance
        if "totals" in data:
            totals = data.get("totals", {})
            print(f"  - Total Debit: {totals.get('debit', 0):,.0f}")
            print(f"  - Total Credit: {totals.get('credit', 0):,.0f}")
            print(f"  - Is Balanced: {totals.get('is_balanced', 'N/A')}")
        else:
            print(f"  - Total Debit: {data.get('total_debit', 0):,.0f}")
            print(f"  - Total Credit: {data.get('total_credit', 0):,.0f}")
            print(f"  - Is Balanced: {data.get('is_balanced', 'N/A')}")
    
    def test_balance_sheet_api_returns_data(self, api_client):
        """Balance Sheet API returns data"""
        response = api_client.get(f"{BASE_URL}/api/accounting/financial/balance-sheet")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify response structure
        assert "assets" in data or "total_assets" in data, "Balance sheet should have assets"
        assert "liabilities" in data or "total_liabilities" in data, "Balance sheet should have liabilities"
        assert "equity" in data or "total_equity" in data, "Balance sheet should have equity"
        
        print(f"SUCCESS: Balance Sheet returned data:")
        print(f"  - Total Assets: {data.get('total_assets', 0):,.0f}")
        print(f"  - Total Liabilities: {data.get('total_liabilities', 0):,.0f}")
        print(f"  - Total Equity: {data.get('total_equity', 0):,.0f}")
        print(f"  - Net Income: {data.get('net_income', 0):,.0f}")
        print(f"  - Is Balanced: {data.get('is_balanced', 'N/A')}")
    
    def test_income_statement_api(self, api_client):
        """Income Statement API returns data"""
        response = api_client.get(f"{BASE_URL}/api/accounting/financial/income-statement")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        print(f"SUCCESS: Income Statement returned data:")
        print(f"  - Total Revenue: {data.get('total_revenue', 0):,.0f}")
        print(f"  - Total COGS: {data.get('total_cogs', 0):,.0f}")
        print(f"  - Gross Profit: {data.get('gross_profit', 0):,.0f}")
        print(f"  - Net Income: {data.get('net_income', 0):,.0f}")


class TestGeneralLedger:
    """Test General Ledger functionality"""
    
    def test_general_ledger_api(self, api_client):
        """General Ledger API returns data"""
        response = api_client.get(f"{BASE_URL}/api/accounting/financial/general-ledger")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        entries = data.get("entries", [])
        
        print(f"SUCCESS: General Ledger returned {len(entries)} entries")
        if "summary" in data:
            summary = data.get("summary", {})
            print(f"  - Total Debit: {summary.get('total_debit', 0):,.0f}")
            print(f"  - Total Credit: {summary.get('total_credit', 0):,.0f}")


class TestChartOfAccounts:
    """Test Chart of Accounts API"""
    
    def test_coa_list(self, api_client):
        """Chart of Accounts list API"""
        response = api_client.get(f"{BASE_URL}/api/accounting/accounts")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        items = data.get("items", [])
        
        print(f"SUCCESS: Chart of Accounts returned {len(items)} accounts")
        
        # Check for standard account categories
        categories = set()
        for acc in items:
            cat = acc.get("category", "unknown")
            categories.add(cat)
        
        print(f"  - Categories found: {', '.join(categories)}")


# Run pytest if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
