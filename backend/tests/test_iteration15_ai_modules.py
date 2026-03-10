# OCB TITAN AI - Iteration 15 Test Suite
# Testing: AI Store Prediction, AI Fraud Detection, AI CFO, Payroll Files

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://smart-ops-hub-6.preview.emergentagent.com')

class TestLoginFlow:
    """Test multi-database login flow - OCB GROUP"""
    
    def test_business_list(self):
        """GET /api/business/list - Lists all databases"""
        response = requests.get(f"{BASE_URL}/api/business/list")
        assert response.status_code == 200
        data = response.json()
        assert "databases" in data or "businesses" in data or isinstance(data, list)
        print(f"Business list response: {data}")
    
    def test_switch_to_ocb_titan(self):
        """POST /api/business/switch/ocb_titan - Switch to OCB GROUP database"""
        response = requests.post(f"{BASE_URL}/api/business/switch/ocb_titan")
        assert response.status_code == 200
        print(f"Switch response: {response.json()}")
    
    def test_ensure_admin(self):
        """POST /api/business/ensure-admin/ocb_titan - Ensure admin exists"""
        response = requests.post(f"{BASE_URL}/api/business/ensure-admin/ocb_titan")
        assert response.status_code == 200
        print(f"Ensure admin response: {response.json()}")
    
    def test_login_with_credentials(self):
        """POST /api/auth/login - Login with ocbgroupbjm@gmail.com"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "ocbgroupbjm@gmail.com",
            "password": "admin123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data or "access_token" in data
        print(f"Login successful, token received")


class TestAIStoreEndpoints:
    """Test AI Store Prediction endpoints"""
    
    def test_branch_viability_3months(self):
        """GET /api/ai-store/branch-viability - Branch viability analysis"""
        response = requests.get(f"{BASE_URL}/api/ai-store/branch-viability?period=3months")
        assert response.status_code == 200
        data = response.json()
        assert "branches" in data
        assert "status_summary" in data
        assert "total_branches_analyzed" in data
        print(f"Branch viability: {data['total_branches_analyzed']} branches analyzed")
    
    def test_branch_viability_6months(self):
        """GET /api/ai-store/branch-viability with 6months period"""
        response = requests.get(f"{BASE_URL}/api/ai-store/branch-viability?period=6months")
        assert response.status_code == 200
        data = response.json()
        assert "branches" in data
        print(f"Branch viability (6 months): {data['total_branches_analyzed']} branches")
    
    def test_new_branch_recommendation(self):
        """GET /api/ai-store/new-branch-recommendation - Location recommendations"""
        response = requests.get(f"{BASE_URL}/api/ai-store/new-branch-recommendation")
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data
        print(f"New branch recommendations: {len(data['recommendations'])} regions")


class TestAIFraudDetection:
    """Test AI Fraud Detection endpoints"""
    
    def test_cashier_risk_30days(self):
        """GET /api/ai-fraud/cashier-risk - Cashier fraud risk analysis"""
        response = requests.get(f"{BASE_URL}/api/ai-fraud/cashier-risk?period=30days")
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "employees" in data
        print(f"Cashier risk: {data['summary']['total_analyzed']} employees analyzed")
    
    def test_cashier_risk_7days(self):
        """GET /api/ai-fraud/cashier-risk with 7days period"""
        response = requests.get(f"{BASE_URL}/api/ai-fraud/cashier-risk?period=7days")
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
    
    def test_cashier_risk_90days(self):
        """GET /api/ai-fraud/cashier-risk with 90days period"""
        response = requests.get(f"{BASE_URL}/api/ai-fraud/cashier-risk?period=90days")
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
    
    def test_missing_stock_30days(self):
        """GET /api/ai-fraud/missing-stock - Missing stock detection"""
        response = requests.get(f"{BASE_URL}/api/ai-fraud/missing-stock?period=30days")
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "items" in data
        print(f"Missing stock: {data['summary']['total_items_analyzed']} items analyzed")
    
    def test_missing_stock_7days(self):
        """GET /api/ai-fraud/missing-stock with 7days period"""
        response = requests.get(f"{BASE_URL}/api/ai-fraud/missing-stock?period=7days")
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
    
    def test_fraud_dashboard(self):
        """GET /api/ai-fraud/dashboard - Fraud detection dashboard"""
        response = requests.get(f"{BASE_URL}/api/ai-fraud/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert "top_risk_cashiers" in data
        assert "top_risk_items" in data
        assert "cashier_summary" in data
        print(f"Fraud dashboard: loaded successfully")
    
    def test_get_fraud_alerts(self):
        """GET /api/ai-fraud/alerts - List fraud alerts"""
        response = requests.get(f"{BASE_URL}/api/ai-fraud/alerts")
        assert response.status_code == 200
        data = response.json()
        assert "alerts" in data
        print(f"Fraud alerts: {len(data['alerts'])} alerts")


class TestAICFOEndpoints:
    """Test AI CFO Module endpoints"""
    
    def test_cfo_dashboard(self):
        """GET /api/ai-cfo/dashboard - CFO dashboard with financial analytics"""
        response = requests.get(f"{BASE_URL}/api/ai-cfo/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "branch_profitability" in data
        # Validate summary fields
        summary = data["summary"]
        assert "revenue_today" in summary
        assert "revenue_month" in summary
        assert "total_payroll" in summary
        assert "payroll_ratio" in summary
        print(f"CFO Dashboard: Revenue month = {summary['revenue_month']}")
    
    def test_profit_loss_month(self):
        """GET /api/ai-cfo/profit-loss - Profit & Loss statement (month)"""
        response = requests.get(f"{BASE_URL}/api/ai-cfo/profit-loss?period=month")
        assert response.status_code == 200
        data = response.json()
        assert "revenue" in data
        assert "gross_profit" in data
        assert "net_profit" in data
        assert "expenses" in data
        print(f"P&L Month: Net profit = {data['net_profit']}")
    
    def test_profit_loss_day(self):
        """GET /api/ai-cfo/profit-loss with day period"""
        response = requests.get(f"{BASE_URL}/api/ai-cfo/profit-loss?period=day")
        assert response.status_code == 200
        data = response.json()
        assert "revenue" in data
    
    def test_profit_loss_week(self):
        """GET /api/ai-cfo/profit-loss with week period"""
        response = requests.get(f"{BASE_URL}/api/ai-cfo/profit-loss?period=week")
        assert response.status_code == 200
        data = response.json()
        assert "revenue" in data
    
    def test_cash_flow_month(self):
        """GET /api/ai-cfo/cash-flow - Cash flow analysis (month)"""
        response = requests.get(f"{BASE_URL}/api/ai-cfo/cash-flow?period=month")
        assert response.status_code == 200
        data = response.json()
        assert "inflows" in data
        assert "outflows" in data
        assert "net_cash_flow" in data
        assert "predictions" in data
        print(f"Cash Flow: Net = {data['net_cash_flow']}")
    
    def test_cash_flow_week(self):
        """GET /api/ai-cfo/cash-flow with week period"""
        response = requests.get(f"{BASE_URL}/api/ai-cfo/cash-flow?period=week")
        assert response.status_code == 200
        data = response.json()
        assert "net_cash_flow" in data
    
    def test_branch_loss_analysis(self):
        """GET /api/ai-cfo/branch-loss-analysis - Branches losing money"""
        response = requests.get(f"{BASE_URL}/api/ai-cfo/branch-loss-analysis")
        assert response.status_code == 200
        data = response.json()
        assert "total_branches" in data
        assert "branches" in data
        print(f"Branch Loss Analysis: {data['loss_branches_count']} loss branches")
    
    def test_employee_efficiency_3months(self):
        """GET /api/ai-cfo/employee-efficiency - Employee efficiency analysis"""
        response = requests.get(f"{BASE_URL}/api/ai-cfo/employee-efficiency?analysis_period=3months")
        assert response.status_code == 200
        data = response.json()
        assert "branches" in data
        assert "summary" in data
        print(f"Employee Efficiency: {data['summary']['total_current_employees']} employees")
    
    def test_employee_efficiency_6months(self):
        """GET /api/ai-cfo/employee-efficiency with 6months period"""
        response = requests.get(f"{BASE_URL}/api/ai-cfo/employee-efficiency?analysis_period=6months")
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
    
    def test_trend_analysis(self):
        """GET /api/ai-cfo/trend-analysis - Trend analysis over time"""
        response = requests.get(f"{BASE_URL}/api/ai-cfo/trend-analysis?period=3months")
        assert response.status_code == 200
        data = response.json()
        assert "trend_data" in data
        assert "summary" in data
        print(f"Trend Analysis: {len(data['trend_data'])} periods")


class TestPayrollFilesEndpoints:
    """Test Payroll File Generation endpoints"""
    
    def test_payroll_dashboard_summary(self):
        """GET /api/payroll-files/dashboard-summary - Payroll HR summary"""
        response = requests.get(f"{BASE_URL}/api/payroll-files/dashboard-summary")
        assert response.status_code == 200
        data = response.json()
        assert "total_employees" in data
        assert "monthly_employees" in data
        assert "daily_employees" in data
        assert "estimated_monthly_payroll" in data
        # Validate payroll details
        payroll = data["estimated_monthly_payroll"]
        assert "total_gross" in payroll
        assert "total_take_home_pay" in payroll
        print(f"Payroll Summary: {data['total_employees']} employees, THP = {payroll['total_take_home_pay']}")
    
    def test_company_payroll_report_json(self):
        """GET /api/payroll-files/report/company - Company-wide payroll report (JSON)"""
        response = requests.get(f"{BASE_URL}/api/payroll-files/report/company?period_month=3&period_year=2026&format=json")
        assert response.status_code == 200
        data = response.json()
        assert "branches" in data
        assert "grand_total" in data
        print(f"Company Report: {data['branch_count']} branches")


class TestAIWarroomEndpoints:
    """Test AI Warroom dashboard endpoint"""
    
    def test_warroom_dashboard(self):
        """GET /api/ai-warroom/dashboard - AI War Room dashboard"""
        response = requests.get(f"{BASE_URL}/api/ai-warroom/dashboard")
        assert response.status_code == 200
        data = response.json()
        print(f"War Room Dashboard: loaded successfully")


class TestHealthAndRoot:
    """Test basic health endpoints"""
    
    def test_health_check(self):
        """GET /api/health - Health check"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print(f"Health check: {data['status']}")
    
    def test_root_api(self):
        """GET /api - Root endpoint"""
        response = requests.get(f"{BASE_URL}/api")
        assert response.status_code == 200
        data = response.json()
        assert "system" in data
        print(f"API Root: {data['system']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
