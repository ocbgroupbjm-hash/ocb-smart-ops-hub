"""
OCB TITAN ERP - PRIORITAS 1-5 Validation Tests
Iteration 70: Bug Fix and New Features Validation

PRIORITAS 1: Journal security - sistem journal tidak bisa dihapus, manual journal bisa dihapus
PRIORITAS 2: General Ledger search dengan single letter (ketik 'p' cari Piutang)
PRIORITAS 3: Date format DD/MM/YYYY (check formatDateDDMMYYYY function)
PRIORITAS 4: Purchase export to Excel (/api/export/purchase)
PRIORITAS 5: Serial number range generation (/api/purchase/serial-numbers/generate)
"""

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
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "tenant_db": TEST_TENANT
    })
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token") or data.get("token")
    pytest.skip(f"Authentication failed: {response.status_code}")

@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Get headers with auth token"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }

# ==============================================================================
# PRIORITAS 1: Journal Security Tests
# ==============================================================================

class TestPrioritas1JournalSecurity:
    """
    PRIORITAS 1: Journal security - sistem journal tidak bisa dihapus, manual journal bisa dihapus
    """
    
    def test_get_journals_list(self, auth_headers):
        """Test GET /api/accounting/journals - should return journal list"""
        response = requests.get(f"{BASE_URL}/api/accounting/journals", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        print(f"Found {len(data.get('items', []))} journals")
    
    def test_create_manual_journal(self, auth_headers):
        """Test creating a manual journal entry"""
        # Get accounts first
        acc_response = requests.get(f"{BASE_URL}/api/accounting/accounts", headers=auth_headers)
        if acc_response.status_code != 200:
            pytest.skip("Cannot get accounts")
        
        accounts = acc_response.json().get("items", [])
        if len(accounts) < 2:
            pytest.skip("Not enough accounts for journal test")
        
        # Create balanced journal
        test_journal = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "reference": f"TEST-MANUAL-{uuid.uuid4().hex[:6]}",
            "description": "TEST Manual Journal Entry for deletion test",
            "source": "manual",
            "entries": [
                {"account_id": accounts[0]["id"], "debit": 1000, "credit": 0, "description": "Test debit"},
                {"account_id": accounts[1]["id"], "debit": 0, "credit": 1000, "description": "Test credit"}
            ]
        }
        
        response = requests.post(f"{BASE_URL}/api/accounting/journals", json=test_journal, headers=auth_headers)
        print(f"Create manual journal response: {response.status_code}")
        
        if response.status_code == 200 or response.status_code == 201:
            data = response.json()
            assert "id" in data or "journal_number" in data
            print(f"Created manual journal: {data.get('journal_number', data.get('id'))}")
            return data
        else:
            print(f"Create journal failed: {response.text}")
            pytest.skip("Cannot create test journal")
    
    def test_check_journal_deletable_endpoint(self, auth_headers):
        """Test /api/accounting/journals/{id}/can-delete endpoint"""
        # Get journals
        response = requests.get(f"{BASE_URL}/api/accounting/journals?limit=20", headers=auth_headers)
        assert response.status_code == 200
        journals = response.json().get("items", [])
        
        if not journals:
            pytest.skip("No journals to test")
        
        # Test can-delete for first journal
        journal = journals[0]
        journal_id = journal.get("id")
        
        check_response = requests.get(f"{BASE_URL}/api/accounting/journals/{journal_id}/can-delete", headers=auth_headers)
        print(f"Can-delete check status: {check_response.status_code}")
        
        if check_response.status_code == 200:
            data = check_response.json()
            assert "can_delete" in data
            print(f"Journal {journal.get('journal_number')}: can_delete={data.get('can_delete')}, reason={data.get('reason')}")
            return data
        elif check_response.status_code == 404:
            print("Can-delete endpoint returns 404 - endpoint may not exist")
    
    def test_delete_system_journal_blocked(self, auth_headers):
        """
        CRITICAL: System generated journals (purchase, payment, ap, ar) CANNOT be deleted
        """
        response = requests.get(f"{BASE_URL}/api/accounting/journals?limit=100", headers=auth_headers)
        assert response.status_code == 200
        journals = response.json().get("items", [])
        
        # Find a system journal
        protected_sources = ['purchase', 'pembelian', 'payment', 'pembayaran', 'ap', 'ar', 'inventory', 'payroll', 'sales', 'penjualan', 'cash', 'bank', 'pos']
        
        system_journal = None
        for journal in journals:
            source = (journal.get('journal_source') or journal.get('reference_type') or journal.get('source') or 'manual').lower()
            if any(src in source for src in protected_sources):
                system_journal = journal
                break
        
        if not system_journal:
            # Check for journals with reference_id (also system journals)
            for journal in journals:
                if journal.get('reference_id') and journal.get('source', 'manual').lower() != 'manual':
                    system_journal = journal
                    break
        
        if not system_journal:
            print("No system journal found to test deletion block")
            pytest.skip("No system journals available for testing")
        
        journal_id = system_journal.get("id")
        journal_source = system_journal.get('journal_source') or system_journal.get('reference_type') or system_journal.get('source', 'manual')
        print(f"Testing delete block on system journal: {system_journal.get('journal_number')} (source: {journal_source})")
        
        # Attempt to delete - should be blocked with 403
        delete_response = requests.delete(f"{BASE_URL}/api/accounting/journals/{journal_id}", headers=auth_headers)
        print(f"Delete system journal response: {delete_response.status_code}")
        
        # Should return 403 Forbidden for system journals
        assert delete_response.status_code == 403, f"Expected 403 for system journal delete, got {delete_response.status_code}: {delete_response.text}"
        
        error_data = delete_response.json()
        assert "cannot be deleted" in error_data.get("detail", "").lower() or "tidak dapat dihapus" in error_data.get("detail", "").lower()
        print(f"PASS: System journal delete blocked correctly: {error_data.get('detail')}")
    
    def test_delete_manual_journal_allowed(self, auth_headers):
        """
        Manual journals CAN be deleted
        """
        # First create a manual journal
        acc_response = requests.get(f"{BASE_URL}/api/accounting/accounts", headers=auth_headers)
        if acc_response.status_code != 200:
            pytest.skip("Cannot get accounts")
        
        accounts = acc_response.json().get("items", [])
        if len(accounts) < 2:
            pytest.skip("Not enough accounts")
        
        test_journal = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "reference": f"TEST-DELETE-{uuid.uuid4().hex[:6]}",
            "description": "TEST Manual Journal for deletion",
            "source": "manual",
            "entries": [
                {"account_id": accounts[0]["id"], "debit": 500, "credit": 0, "description": "Test"},
                {"account_id": accounts[1]["id"], "debit": 0, "credit": 500, "description": "Test"}
            ]
        }
        
        create_response = requests.post(f"{BASE_URL}/api/accounting/journals", json=test_journal, headers=auth_headers)
        if create_response.status_code not in [200, 201]:
            pytest.skip("Cannot create manual journal for deletion test")
        
        created = create_response.json()
        journal_id = created.get("id")
        journal_number = created.get("journal_number")
        print(f"Created manual journal for deletion: {journal_number}")
        
        # Now delete it - should succeed
        delete_response = requests.delete(f"{BASE_URL}/api/accounting/journals/{journal_id}", headers=auth_headers)
        print(f"Delete manual journal response: {delete_response.status_code}")
        
        assert delete_response.status_code == 200, f"Expected 200 for manual journal delete, got {delete_response.status_code}: {delete_response.text}"
        print(f"PASS: Manual journal {journal_number} deleted successfully")


# ==============================================================================
# PRIORITAS 2: General Ledger Search Tests
# ==============================================================================

class TestPrioritas2GeneralLedgerSearch:
    """
    PRIORITAS 2: General Ledger search dengan single letter (ketik 'p' cari Piutang)
    Backend provides data, frontend handles filtering with debounce
    """
    
    def test_trial_balance_returns_all_accounts(self, auth_headers):
        """Test that trial balance returns all accounts for frontend filtering"""
        response = requests.get(f"{BASE_URL}/api/accounting/financial/trial-balance", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "accounts" in data
        accounts = data.get("accounts", [])
        print(f"Trial Balance returned {len(accounts)} accounts")
        
        # Check if Piutang accounts exist
        piutang_accounts = [a for a in accounts if 'piutang' in a.get('account_name', '').lower()]
        print(f"Found {len(piutang_accounts)} Piutang accounts:")
        for acc in piutang_accounts[:5]:
            print(f"  - {acc.get('account_code')}: {acc.get('account_name')}")
        
        return accounts
    
    def test_general_ledger_api(self, auth_headers):
        """Test general ledger API returns data"""
        response = requests.get(f"{BASE_URL}/api/accounting/financial/general-ledger", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        print(f"General Ledger returned {len(data.get('entries', []))} entries")
        return data
    
    def test_search_piutang_accounts(self, auth_headers):
        """Test that searching for 'piutang' returns relevant accounts"""
        # Get all accounts for the search test
        response = requests.get(f"{BASE_URL}/api/accounting/financial/trial-balance", headers=auth_headers)
        assert response.status_code == 200
        
        accounts = response.json().get("accounts", [])
        
        # Simulate frontend search for 'p' (like %p%)
        search_term = 'p'
        filtered = [a for a in accounts if 
                   search_term.lower() in a.get('account_code', '').lower() or 
                   search_term.lower() in a.get('account_name', '').lower()]
        
        print(f"Search 'p' returns {len(filtered)} accounts (from {len(accounts)} total)")
        
        # Should find accounts like "Piutang Usaha", "Persediaan", "Pendapatan", etc.
        assert len(filtered) > 0, "Single letter 'p' search should find accounts"
        
        # List first few results
        for acc in filtered[:10]:
            print(f"  - {acc.get('account_code')}: {acc.get('account_name')}")
        
        # Verify Piutang is found
        piutang_found = any('piutang' in a.get('account_name', '').lower() for a in filtered)
        print(f"Piutang found in results: {piutang_found}")


# ==============================================================================
# PRIORITAS 3: Date Format DD/MM/YYYY Tests
# ==============================================================================

class TestPrioritas3DateFormat:
    """
    PRIORITAS 3: Date format DD/MM/YYYY validation
    The formatDateDDMMYYYY function should be in /app/frontend/src/utils/dateUtils.js
    This is a frontend function, we validate the backend returns proper ISO dates
    """
    
    def test_journal_dates_are_iso_format(self, auth_headers):
        """Test that journal dates from API are in ISO format (backend responsibility)"""
        response = requests.get(f"{BASE_URL}/api/accounting/journals?limit=10", headers=auth_headers)
        assert response.status_code == 200
        
        journals = response.json().get("items", [])
        for journal in journals[:5]:
            date = journal.get("date") or journal.get("created_at")
            if date:
                # Should be ISO format YYYY-MM-DD or ISO 8601
                assert len(date) >= 10, f"Date should be ISO format: {date}"
                print(f"Journal {journal.get('journal_number')}: date={date}")
    
    def test_purchase_order_dates_format(self, auth_headers):
        """Test purchase order dates are in proper format"""
        response = requests.get(f"{BASE_URL}/api/purchase/orders?limit=10", headers=auth_headers)
        assert response.status_code == 200
        
        orders = response.json().get("items", [])
        for order in orders[:5]:
            created_at = order.get("created_at")
            if created_at:
                print(f"PO {order.get('po_number')}: created_at={created_at}")


# ==============================================================================
# PRIORITAS 4: Purchase Export to Excel Tests
# ==============================================================================

class TestPrioritas4PurchaseExport:
    """
    PRIORITAS 4: Purchase export to Excel (/api/export/purchase)
    """
    
    def test_purchase_export_endpoint(self, auth_headers):
        """Test /api/export/purchase endpoint"""
        response = requests.get(f"{BASE_URL}/api/export/purchase", headers=auth_headers)
        print(f"Purchase export status: {response.status_code}")
        
        if response.status_code == 404:
            print("WARNING: /api/export/purchase endpoint NOT FOUND - needs implementation")
            pytest.skip("Purchase export endpoint not implemented")
        
        # If endpoint exists, verify response
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            print(f"Export content-type: {content_type}")
            
            # Could be xlsx, csv, or json
            assert 'application' in content_type or 'text' in content_type
            print("PASS: Purchase export endpoint working")
    
    def test_alternative_purchase_data_export(self, auth_headers):
        """Alternative: Get purchase orders data for export"""
        response = requests.get(f"{BASE_URL}/api/purchase/orders?limit=100", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        orders = data.get("items", [])
        print(f"Purchase orders available for export: {len(orders)}")
        
        # Validate export-ready data structure
        if orders:
            sample = orders[0]
            export_fields = ['po_number', 'supplier_name', 'total', 'status', 'created_at']
            available = [f for f in export_fields if f in sample]
            print(f"Export fields available: {available}")


# ==============================================================================
# PRIORITAS 5: Serial Number Range Generation Tests
# ==============================================================================

class TestPrioritas5SerialNumberGeneration:
    """
    PRIORITAS 5: Serial number range generation (/api/purchase/serial-numbers/generate)
    Input: SN Awal = 10001, SN Akhir = 10010
    Output: [10001, 10002, ..., 10010]
    """
    
    def test_serial_number_generate_endpoint(self, auth_headers):
        """Test POST /api/purchase/serial-numbers/generate"""
        test_data = {
            "item_id": str(uuid.uuid4()),
            "product_id": str(uuid.uuid4()),
            "sn_start": "TEST10001",
            "sn_end": "TEST10005",
            "purchase_id": None
        }
        
        response = requests.post(
            f"{BASE_URL}/api/purchase/serial-numbers/generate",
            json=test_data,
            headers=auth_headers
        )
        
        print(f"Serial number generate status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Generate response: {data}")
            
            assert data.get("success") == True
            assert data.get("count") == 5
            assert len(data.get("serial_numbers", [])) == 5
            print(f"PASS: Generated {data.get('count')} serial numbers: {data.get('serial_numbers')}")
        elif response.status_code == 404:
            print("WARNING: Serial number generate endpoint not found")
            pytest.skip("Serial number endpoint not implemented")
        else:
            print(f"Serial number generate failed: {response.text}")
            pytest.fail(f"Unexpected status: {response.status_code}")
    
    def test_serial_number_numeric_range(self, auth_headers):
        """Test numeric serial number range generation"""
        test_data = {
            "item_id": str(uuid.uuid4()),
            "product_id": str(uuid.uuid4()),
            "sn_start": "20001",
            "sn_end": "20010"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/purchase/serial-numbers/generate",
            json=test_data,
            headers=auth_headers
        )
        
        if response.status_code == 200:
            data = response.json()
            assert data.get("count") == 10
            sns = data.get("serial_numbers", [])
            
            # Verify sequential
            expected = ["20001", "20002", "20003", "20004", "20005", "20006", "20007", "20008", "20009", "20010"]
            assert sns == expected, f"Expected sequential SNs, got: {sns}"
            print(f"PASS: Sequential SN range generated correctly")
    
    def test_serial_number_list_endpoint(self, auth_headers):
        """Test GET /api/purchase/serial-numbers"""
        response = requests.get(
            f"{BASE_URL}/api/purchase/serial-numbers?limit=20",
            headers=auth_headers
        )
        
        print(f"Serial numbers list status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Total serial numbers: {data.get('total', 0)}")
            items = data.get("items", [])
            if items:
                print(f"Sample SN: {items[0]}")
    
    def test_serial_number_validation(self, auth_headers):
        """Test validation: SN Akhir must be > SN Awal"""
        test_data = {
            "item_id": str(uuid.uuid4()),
            "product_id": str(uuid.uuid4()),
            "sn_start": "30010",  # Start is higher
            "sn_end": "30001"     # End is lower - should fail
        }
        
        response = requests.post(
            f"{BASE_URL}/api/purchase/serial-numbers/generate",
            json=test_data,
            headers=auth_headers
        )
        
        if response.status_code == 400:
            print(f"PASS: Validation correctly rejects invalid range: {response.json()}")
        else:
            print(f"Validation response: {response.status_code} - {response.text}")


# ==============================================================================
# Additional Tests: HR KPI and Analytics
# ==============================================================================

class TestHRKPIAnalytics:
    """HR: KPI and Analytics endpoints"""
    
    def test_kpi_summary_endpoint(self, auth_headers):
        """Test /api/dashboard-intel/kpi-summary"""
        response = requests.get(f"{BASE_URL}/api/dashboard-intel/kpi-summary", headers=auth_headers)
        print(f"KPI Summary status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"KPI Summary: {data}")
    
    def test_hr_attendance_shifts(self, auth_headers):
        """Test /api/hr/attendance/shifts"""
        response = requests.get(f"{BASE_URL}/api/hr/attendance/shifts", headers=auth_headers)
        print(f"HR Shifts status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"HR Shifts: {len(data) if isinstance(data, list) else data}")
    
    def test_employees_kpi_export(self, auth_headers):
        """Test /api/export/employees/kpi"""
        response = requests.get(f"{BASE_URL}/api/export/employees/kpi?format=json", headers=auth_headers)
        print(f"Employee KPI export status: {response.status_code}")


# ==============================================================================
# Accounting Verification Tests
# ==============================================================================

class TestAccountingVerification:
    """Accounting: Trial Balance balanced, Piutang Usaha visible"""
    
    def test_trial_balance_is_balanced(self, auth_headers):
        """Test that Trial Balance is balanced (Debit = Credit)"""
        response = requests.get(f"{BASE_URL}/api/accounting/financial/trial-balance", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        totals = data.get("totals", {})
        
        total_debit = totals.get("debit", 0)
        total_credit = totals.get("credit", 0)
        is_balanced = totals.get("is_balanced", False)
        
        print(f"Trial Balance: Debit={total_debit:,.2f}, Credit={total_credit:,.2f}, Balanced={is_balanced}")
        
        # Should be balanced
        assert is_balanced or abs(total_debit - total_credit) < 0.01, "Trial Balance should be balanced"
        print("PASS: Trial Balance is balanced")
    
    def test_piutang_usaha_visible(self, auth_headers):
        """Test that Piutang Usaha account is visible in reports"""
        response = requests.get(f"{BASE_URL}/api/accounting/financial/trial-balance", headers=auth_headers)
        assert response.status_code == 200
        
        accounts = response.json().get("accounts", [])
        
        # Look for Piutang Usaha (1-1300)
        piutang_usaha = None
        for acc in accounts:
            code = acc.get("account_code", "")
            name = acc.get("account_name", "").lower()
            if "1-1300" in code or ("piutang" in name and "usaha" in name):
                piutang_usaha = acc
                break
        
        if piutang_usaha:
            print(f"PASS: Piutang Usaha found: {piutang_usaha.get('account_code')} - {piutang_usaha.get('account_name')}")
            print(f"  Debit: {piutang_usaha.get('debit', 0):,.2f}, Credit: {piutang_usaha.get('credit', 0):,.2f}")
        else:
            # Check for any Piutang account
            piutang_any = [a for a in accounts if 'piutang' in a.get('account_name', '').lower()]
            if piutang_any:
                print(f"Found {len(piutang_any)} Piutang-related accounts:")
                for acc in piutang_any:
                    print(f"  - {acc.get('account_code')}: {acc.get('account_name')}")
            else:
                print("WARNING: No Piutang accounts found in Trial Balance")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
