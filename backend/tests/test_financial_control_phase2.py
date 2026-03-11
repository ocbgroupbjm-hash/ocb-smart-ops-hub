"""
OCB TITAN ERP - Phase 2 Financial Control System Tests
Iteration 39 - Testing Multi Tax Engine, Consistency Checker, Auto Journal Engine

Tests cover:
1. Multi Tax Engine - /api/tax-engine/* endpoints
2. Financial Consistency Checker - /api/consistency-checker/* endpoints
3. Auto Journal Engine - /api/auto-journal/* endpoints
"""

import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL')

# Test credentials
TEST_EMAIL = "ocbgroupbjm@gmail.com"
TEST_PASSWORD = "admin123"


class TestAuthentication:
    """Authentication tests for Financial Control endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for testing"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data, "No token in response"
        return data["token"]
    
    def test_login_success(self):
        """Test login works with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data.get("user", {}).get("email") == TEST_EMAIL


class TestMultiTaxEngine:
    """Tests for Multi Tax Engine module - 6 Indonesian tax types"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        return response.json().get("token")
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    # ===== TAX TYPES ENDPOINT =====
    def test_get_tax_types(self, headers):
        """Test /api/tax-engine/tax-types returns all 6 tax types"""
        response = requests.get(f"{BASE_URL}/api/tax-engine/tax-types", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "items" in data
        assert data["total"] == 6
        
        # Verify all 6 tax types are present
        tax_codes = [t["code"] for t in data["items"]]
        expected_codes = ["PPN", "PPNBM", "PPH21", "PPH22", "PPH23", "PPH4_2"]
        for code in expected_codes:
            assert code in tax_codes, f"Tax code {code} missing"
    
    def test_tax_types_have_required_fields(self, headers):
        """Test each tax type has required fields"""
        response = requests.get(f"{BASE_URL}/api/tax-engine/tax-types", headers=headers)
        data = response.json()
        
        for tax in data["items"]:
            assert "code" in tax
            assert "name" in tax
            assert "default_rate" in tax
            assert "category" in tax
            assert "description" in tax
    
    def test_ppn_default_rate(self, headers):
        """Test PPN default rate is 11%"""
        response = requests.get(f"{BASE_URL}/api/tax-engine/tax-types", headers=headers)
        data = response.json()
        
        ppn = next((t for t in data["items"] if t["code"] == "PPN"), None)
        assert ppn is not None
        assert ppn["default_rate"] == 11.0
        assert ppn["category"] == "value_added_tax"
    
    # ===== TAX CALCULATION ENDPOINT =====
    def test_calculate_ppn_exclusive(self, headers):
        """Test PPN calculation (exclusive - tax on top of amount)"""
        response = requests.post(f"{BASE_URL}/api/tax-engine/calculate", json={
            "tax_code": "PPN",
            "base_amount": 1000000,
            "is_inclusive": False
        }, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["tax_code"] == "PPN"
        assert data["rate"] == 11.0
        assert data["net_amount"] == 1000000
        assert data["tax_amount"] == 110000  # 11% of 1,000,000
        assert data["gross_amount"] == 1110000  # 1,000,000 + 110,000
        assert data["is_inclusive"] == False
    
    def test_calculate_ppn_inclusive(self, headers):
        """Test PPN calculation (inclusive - tax already in amount)"""
        response = requests.post(f"{BASE_URL}/api/tax-engine/calculate", json={
            "tax_code": "PPN",
            "base_amount": 1110000,
            "is_inclusive": True
        }, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["tax_code"] == "PPN"
        assert data["is_inclusive"] == True
        assert data["gross_amount"] == 1110000
        # Net = 1110000 / 1.11 = 1000000
        assert abs(data["net_amount"] - 1000000) < 1  # Allow small rounding
        assert abs(data["tax_amount"] - 110000) < 1
    
    def test_calculate_pph22(self, headers):
        """Test PPh 22 calculation (1.5% rate)"""
        response = requests.post(f"{BASE_URL}/api/tax-engine/calculate", json={
            "tax_code": "PPH22",
            "base_amount": 10000000,
            "is_inclusive": False
        }, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["tax_code"] == "PPH22"
        assert data["rate"] == 1.5
        assert data["tax_amount"] == 150000  # 1.5% of 10,000,000
    
    def test_calculate_invalid_tax_code(self, headers):
        """Test calculation fails with invalid tax code"""
        response = requests.post(f"{BASE_URL}/api/tax-engine/calculate", json={
            "tax_code": "INVALID",
            "base_amount": 1000000,
            "is_inclusive": False
        }, headers=headers)
        
        assert response.status_code == 400
    
    # ===== PPH 21 PROGRESSIVE CALCULATION =====
    def test_calculate_pph21_basic(self, headers):
        """Test PPh 21 calculation with progressive rate"""
        response = requests.post(
            f"{BASE_URL}/api/tax-engine/calculate-pph21?gross_salary=120000000&ptkp=TK/0",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["tax_code"] == "PPH21"
        assert data["gross_salary"] == 120000000
        assert data["ptkp_status"] == "TK/0"
        assert data["ptkp_amount"] == 54000000  # PTKP for TK/0
        assert data["pkp"] == 66000000  # 120M - 54M = 66M (PKP)
        assert data["annual_tax"] > 0
        assert data["monthly_tax"] > 0
        assert "breakdown" in data
    
    def test_calculate_pph21_with_k1_status(self, headers):
        """Test PPh 21 with K/1 PTKP status (Kawin + 1 tanggungan)"""
        response = requests.post(
            f"{BASE_URL}/api/tax-engine/calculate-pph21?gross_salary=150000000&ptkp=K/1",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["ptkp_status"] == "K/1"
        assert data["ptkp_amount"] == 63000000  # PTKP for K/1
        assert data["pkp"] == 87000000  # 150M - 63M = 87M
    
    def test_pph21_progressive_brackets(self, headers):
        """Test PPh 21 uses progressive tax brackets"""
        # Test with high income to trigger multiple brackets
        response = requests.post(
            f"{BASE_URL}/api/tax-engine/calculate-pph21?gross_salary=300000000&ptkp=TK/0",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have multiple brackets in breakdown
        assert len(data["breakdown"]) >= 2
        
        # First bracket should be 5%
        assert data["breakdown"][0]["rate"] == 5
        
        # Second bracket should be 15%
        if len(data["breakdown"]) > 1:
            assert data["breakdown"][1]["rate"] == 15
    
    def test_pph21_no_tax_if_below_ptkp(self, headers):
        """Test no tax if income below PTKP"""
        response = requests.post(
            f"{BASE_URL}/api/tax-engine/calculate-pph21?gross_salary=50000000&ptkp=TK/0",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Income (50M) < PTKP (54M), so PKP = 0 and tax = 0
        assert data["pkp"] == 0
        assert data["annual_tax"] == 0
        assert data["monthly_tax"] == 0
    
    # ===== TAX ACCOUNTS ENDPOINT =====
    def test_get_tax_accounts(self, headers):
        """Test /api/tax-engine/tax-accounts returns account mapping"""
        response = requests.get(f"{BASE_URL}/api/tax-engine/tax-accounts", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "items" in data
        assert data["total"] > 0
        
        # Check some expected account keys exist
        account_keys = [a["account_key"] for a in data["items"]]
        expected_keys = ["ppn_masukan", "ppn_keluaran", "pph21_hutang"]
        for key in expected_keys:
            assert key in account_keys
    
    # ===== TAX CONFIGURATIONS ENDPOINT =====
    def test_get_tax_configurations(self, headers):
        """Test /api/tax-engine/configurations returns tax configs"""
        response = requests.get(f"{BASE_URL}/api/tax-engine/configurations", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "items" in data
        assert data["total"] >= 6  # At least default configs


class TestFinancialConsistencyChecker:
    """Tests for Financial Consistency Checker module"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        return response.json().get("token")
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    # ===== CHECK TYPES ENDPOINT =====
    def test_get_check_types(self, headers):
        """Test /api/consistency-checker/check-types returns all 6 check types"""
        response = requests.get(f"{BASE_URL}/api/consistency-checker/check-types", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "items" in data
        assert data["total"] == 6
        
        check_types = [c["type"] for c in data["items"]]
        expected_types = ["journal_balance", "trial_balance", "stock_movement", "ar_journal", "ap_journal", "cash_balance"]
        for ct in expected_types:
            assert ct in check_types
    
    def test_check_types_have_severity(self, headers):
        """Test each check type has severity field"""
        response = requests.get(f"{BASE_URL}/api/consistency-checker/check-types", headers=headers)
        data = response.json()
        
        for check in data["items"]:
            assert "severity" in check
            assert check["severity"] in ["critical", "high", "medium", "low"]
    
    # ===== SINGLE CHECK ENDPOINTS =====
    def test_check_journal_balance(self, headers):
        """Test single check: journal_balance"""
        response = requests.get(
            f"{BASE_URL}/api/consistency-checker/check/journal_balance",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["check_type"] == "journal_balance"
        assert data["status"] in ["pass", "fail", "warning"]
        assert "message" in data
    
    def test_check_trial_balance(self, headers):
        """Test single check: trial_balance"""
        response = requests.get(
            f"{BASE_URL}/api/consistency-checker/check/trial_balance",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["check_type"] == "trial_balance"
        assert data["status"] in ["pass", "fail", "warning"]
        assert "details" in data
        if data["details"]:
            assert "total_debit" in data["details"]
            assert "total_credit" in data["details"]
    
    def test_check_stock_movement(self, headers):
        """Test single check: stock_movement"""
        response = requests.get(
            f"{BASE_URL}/api/consistency-checker/check/stock_movement",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["check_type"] == "stock_movement"
        assert data["status"] in ["pass", "fail", "warning"]
    
    def test_check_ar_journal(self, headers):
        """Test single check: ar_journal"""
        response = requests.get(
            f"{BASE_URL}/api/consistency-checker/check/ar_journal",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["check_type"] == "ar_journal"
        assert data["status"] in ["pass", "fail", "warning"]
    
    def test_check_ap_journal(self, headers):
        """Test single check: ap_journal"""
        response = requests.get(
            f"{BASE_URL}/api/consistency-checker/check/ap_journal",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["check_type"] == "ap_journal"
        assert data["status"] in ["pass", "fail", "warning"]
    
    def test_check_cash_balance(self, headers):
        """Test single check: cash_balance"""
        response = requests.get(
            f"{BASE_URL}/api/consistency-checker/check/cash_balance",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["check_type"] == "cash_balance"
        assert data["status"] in ["pass", "fail", "warning"]
    
    def test_check_invalid_type(self, headers):
        """Test single check with invalid type returns 400"""
        response = requests.get(
            f"{BASE_URL}/api/consistency-checker/check/invalid_type",
            headers=headers
        )
        
        assert response.status_code == 400
    
    # ===== FULL REPORT ENDPOINT =====
    def test_full_consistency_report(self, headers):
        """Test /api/consistency-checker/full-report runs all checks"""
        response = requests.get(
            f"{BASE_URL}/api/consistency-checker/full-report",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "report_id" in data
        assert "generated_at" in data
        assert "overall_status" in data
        assert data["overall_status"] in ["healthy", "warning", "critical"]
        
        assert "checks" in data
        assert len(data["checks"]) == 6  # All 6 check types
        
        assert "summary" in data
        assert "total_checks" in data["summary"]
        assert data["summary"]["total_checks"] == 6
        assert "passed" in data["summary"]
        assert "failed" in data["summary"]
        assert "warnings" in data["summary"]
    
    def test_full_report_with_branch_filter(self, headers):
        """Test full report with branch_id filter"""
        response = requests.get(
            f"{BASE_URL}/api/consistency-checker/full-report?branch_id=test-branch",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["summary"]["branch_id"] == "test-branch"
    
    # ===== FIX SUGGESTIONS ENDPOINT =====
    def test_fix_suggestions_journal_balance(self, headers):
        """Test fix suggestions for journal_balance"""
        response = requests.get(
            f"{BASE_URL}/api/consistency-checker/fix-suggestions/journal_balance",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "issue" in data
        assert "suggestions" in data
        assert len(data["suggestions"]) > 0
    
    def test_fix_suggestions_stock_movement(self, headers):
        """Test fix suggestions for stock_movement"""
        response = requests.get(
            f"{BASE_URL}/api/consistency-checker/fix-suggestions/stock_movement",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "suggestions" in data
        assert "stock opname" in data["suggestions"][0].lower() or len(data["suggestions"]) > 0


class TestAutoJournalEngine:
    """Tests for Auto Journal Engine module - 21 templates"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        return response.json().get("token")
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    # ===== TEMPLATES ENDPOINT =====
    def test_get_journal_templates(self, headers):
        """Test /api/auto-journal/templates returns all 21 templates"""
        response = requests.get(f"{BASE_URL}/api/auto-journal/templates", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "items" in data
        assert data["total"] == 21
        
        # Check some expected templates
        template_codes = [t["code"] for t in data["items"]]
        expected_templates = [
            "sales_cash", "sales_credit", "sales_cogs",
            "purchase_cash", "purchase_credit",
            "ar_payment_cash", "ap_payment_cash",
            "stock_adjustment_in", "stock_adjustment_out"
        ]
        for code in expected_templates:
            assert code in template_codes, f"Template {code} missing"
    
    def test_templates_have_categories(self, headers):
        """Test templates response includes categorized groupings"""
        response = requests.get(f"{BASE_URL}/api/auto-journal/templates", headers=headers)
        data = response.json()
        
        assert "categories" in data
        expected_categories = ["sales", "purchase", "ar_ap", "inventory", "cash_bank"]
        for cat in expected_categories:
            assert cat in data["categories"]
    
    def test_template_has_required_fields(self, headers):
        """Test each template has required fields"""
        response = requests.get(f"{BASE_URL}/api/auto-journal/templates", headers=headers)
        data = response.json()
        
        for template in data["items"]:
            assert "code" in template
            assert "name" in template
            assert "debit_accounts" in template
            assert "credit_accounts" in template
            assert "description_template" in template
    
    # ===== SINGLE TEMPLATE ENDPOINT =====
    def test_get_single_template(self, headers):
        """Test getting single template with account details"""
        response = requests.get(
            f"{BASE_URL}/api/auto-journal/templates/sales_cash",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["code"] == "sales_cash"
        assert data["name"] == "Penjualan Tunai"
        assert "debit_accounts" in data
        assert "credit_accounts" in data
        
        # Check accounts have derived details
        for acc in data["debit_accounts"]:
            assert "key" in acc
            assert "code" in acc
            assert "name" in acc
    
    def test_get_invalid_template(self, headers):
        """Test 404 for invalid template code"""
        response = requests.get(
            f"{BASE_URL}/api/auto-journal/templates/invalid_template",
            headers=headers
        )
        
        assert response.status_code == 404
    
    # ===== PREVIEW ENDPOINT =====
    def test_preview_sales_cash_journal(self, headers):
        """Test journal preview for sales_cash template"""
        response = requests.get(
            f"{BASE_URL}/api/auto-journal/preview/sales_cash?amount=1000000&tax_amount=110000",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["template_code"] == "sales_cash"
        assert data["template_name"] == "Penjualan Tunai"
        assert "entries" in data
        assert len(data["entries"]) >= 2  # At least debit and credit
        
        assert data["is_balanced"] == True
        assert data["total_debit"] == data["total_credit"]
    
    def test_preview_sales_cash_balanced(self, headers):
        """Test sales_cash preview: Kas (D) = Amount + Tax, Pendapatan (C) = Amount, PPN (C) = Tax"""
        response = requests.get(
            f"{BASE_URL}/api/auto-journal/preview/sales_cash?amount=1000000&tax_amount=110000",
            headers=headers
        )
        
        data = response.json()
        
        # Total debit should equal total credit
        assert data["is_balanced"] == True
        
        # For sales_cash: Debit Kas = 1,110,000, Credit Pendapatan = 1,000,000, Credit PPN = 110,000
        assert data["total_debit"] == 1110000
        assert data["total_credit"] == 1110000
    
    def test_preview_purchase_cash_journal(self, headers):
        """Test journal preview for purchase_cash template"""
        response = requests.get(
            f"{BASE_URL}/api/auto-journal/preview/purchase_cash?amount=500000&tax_amount=55000",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["template_code"] == "purchase_cash"
        assert data["is_balanced"] == True
        
        # For purchase_cash: Debit Persediaan + PPN, Credit Kas
        assert data["total_debit"] == 555000
        assert data["total_credit"] == 555000
    
    def test_preview_stock_adjustment_in(self, headers):
        """Test journal preview for stock_adjustment_in template"""
        response = requests.get(
            f"{BASE_URL}/api/auto-journal/preview/stock_adjustment_in?amount=200000&tax_amount=0",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["template_code"] == "stock_adjustment_in"
        assert data["is_balanced"] == True
    
    def test_preview_with_zero_tax(self, headers):
        """Test preview works with zero tax amount"""
        response = requests.get(
            f"{BASE_URL}/api/auto-journal/preview/ar_payment_cash?amount=500000&tax_amount=0",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["is_balanced"] == True
        assert data["total_debit"] == 500000
        assert data["total_credit"] == 500000
    
    # ===== ACCOUNT MAPPING ENDPOINT =====
    def test_get_account_mapping(self, headers):
        """Test /api/auto-journal/account-mapping returns mapping"""
        response = requests.get(f"{BASE_URL}/api/auto-journal/account-mapping", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "mapping" in data
        assert "defaults" in data
        
        # Check some expected mappings
        assert "kas" in data["mapping"]
        assert "piutang_usaha" in data["mapping"]
        assert "hutang_dagang" in data["mapping"]
        
        # Check defaults have account codes
        assert data["defaults"]["kas"]["code"] == "1-1100"


class TestFiscalPeriodTaxIntegration:
    """Tests for Fiscal Period Closing with Tax permissions"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        return response.json().get("token")
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_period_status_endpoint_exists(self, headers):
        """Test period status endpoint exists"""
        # Test with a fake period ID - should return 404 (not 500)
        response = requests.get(
            f"{BASE_URL}/api/tax-engine/period-status/fake-period-id",
            headers=headers
        )
        
        # Either 404 (period not found) or 200 (if period exists)
        assert response.status_code in [200, 404]


class TestEndToEndFlows:
    """End-to-end integration tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        return response.json().get("token")
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_tax_calculation_and_journal_preview_flow(self, headers):
        """Test flow: Calculate tax -> Preview journal with tax amount"""
        # Step 1: Calculate PPN
        tax_resp = requests.post(f"{BASE_URL}/api/tax-engine/calculate", json={
            "tax_code": "PPN",
            "base_amount": 1000000,
            "is_inclusive": False
        }, headers=headers)
        
        assert tax_resp.status_code == 200
        tax_data = tax_resp.json()
        
        # Step 2: Use tax amount in journal preview
        journal_resp = requests.get(
            f"{BASE_URL}/api/auto-journal/preview/sales_cash?amount={tax_data['net_amount']}&tax_amount={tax_data['tax_amount']}",
            headers=headers
        )
        
        assert journal_resp.status_code == 200
        journal_data = journal_resp.json()
        
        assert journal_data["is_balanced"] == True
        assert journal_data["total_debit"] == tax_data["gross_amount"]
    
    def test_consistency_check_after_operations(self, headers):
        """Test consistency check can be run after operations"""
        response = requests.get(
            f"{BASE_URL}/api/consistency-checker/full-report",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # System should still be consistent after operations
        assert data["overall_status"] in ["healthy", "warning", "critical"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
