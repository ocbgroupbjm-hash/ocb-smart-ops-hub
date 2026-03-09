# OCB TITAN AI - Module Tests
# Tests for Global Map, AI Command Center, KPI Performance, CRM AI, and Data Export APIs

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestGlobalMapAPI:
    """Global Map Monitoring System API Tests"""
    
    def test_get_all_branch_locations(self):
        """Test /api/global-map/branches endpoint"""
        response = requests.get(f"{BASE_URL}/api/global-map/branches")
        print(f"GET /api/global-map/branches: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "total_branches" in data
        assert "status_summary" in data
        assert "branches" in data
        assert "green" in data["status_summary"]
        assert "yellow" in data["status_summary"]
        assert "red" in data["status_summary"]
        print(f"Total branches: {data['total_branches']}, Status summary: {data['status_summary']}")
    
    def test_get_realtime_gps(self):
        """Test /api/global-map/gps/realtime endpoint"""
        response = requests.get(f"{BASE_URL}/api/global-map/gps/realtime")
        print(f"GET /api/global-map/gps/realtime: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "tanggal" in data
        assert "total_tracked" in data
        assert "active_count" in data
        assert "locations" in data
        print(f"Total tracked: {data['total_tracked']}, Active: {data['active_count']}")
    
    def test_get_stock_map(self):
        """Test /api/global-map/stock/map endpoint"""
        response = requests.get(f"{BASE_URL}/api/global-map/stock/map")
        print(f"GET /api/global-map/stock/map: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_branches" in data
        assert "status_summary" in data
        assert "branches" in data
        print(f"Stock map - Total branches: {data['total_branches']}")
    
    def test_get_stock_alerts(self):
        """Test /api/global-map/stock/alerts endpoint"""
        response = requests.get(f"{BASE_URL}/api/global-map/stock/alerts")
        print(f"GET /api/global-map/stock/alerts: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total" in data
        assert "alerts" in data
        print(f"Stock alerts: {data['total']}")
    
    def test_get_spv_alerts(self):
        """Test /api/global-map/spv/alerts endpoint"""
        response = requests.get(f"{BASE_URL}/api/global-map/spv/alerts")
        print(f"GET /api/global-map/spv/alerts: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "tanggal" in data
        assert "total" in data
        assert "alerts" in data
        print(f"SPV alerts: {data['total']}")


class TestAICommandCenterAPI:
    """AI Command Center API Tests"""
    
    def test_get_ai_dashboard(self):
        """Test /api/ai-command/dashboard endpoint"""
        response = requests.get(f"{BASE_URL}/api/ai-command/dashboard")
        print(f"GET /api/ai-command/dashboard: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "generated_at" in data
        assert "summary" in data
        assert "financials" in data
        assert "inventory" in data
        assert "insights" in data
        assert "insights_count" in data
        
        # Validate summary structure
        summary = data["summary"]
        assert "total_branches" in summary
        assert "total_employees" in summary
        assert "attendance_rate" in summary
        
        # Validate financials
        financials = data["financials"]
        assert "sales_today" in financials
        assert "sales_month" in financials
        print(f"AI Dashboard - Branches: {summary['total_branches']}, Employees: {summary['total_employees']}")
        print(f"Insights count: {data['insights_count']}")
    
    def test_get_ai_recommendations(self):
        """Test /api/ai-command/recommendations endpoint"""
        response = requests.get(f"{BASE_URL}/api/ai-command/recommendations")
        print(f"GET /api/ai-command/recommendations: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "generated_at" in data
        assert "total_recommendations" in data
        assert "by_priority" in data
        assert "recommendations" in data
        print(f"Total recommendations: {data['total_recommendations']}, By priority: {data['by_priority']}")
    
    def test_get_trend_analysis(self):
        """Test /api/ai-command/trends endpoint"""
        response = requests.get(f"{BASE_URL}/api/ai-command/trends?days=30")
        print(f"GET /api/ai-command/trends: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "period" in data
        assert "data_points" in data
        assert "trend_direction" in data
        assert "sales_trend_percentage" in data
        assert "daily_data" in data
        assert "summary" in data
        print(f"Trend: {data['trend_direction']}, Change: {data['sales_trend_percentage']}%")
    
    def test_get_anomalies(self):
        """Test /api/ai-command/anomalies endpoint"""
        response = requests.get(f"{BASE_URL}/api/ai-command/anomalies")
        print(f"GET /api/ai-command/anomalies: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "generated_at" in data
        assert "total_anomalies" in data
        assert "by_severity" in data
        assert "anomalies" in data
        print(f"Total anomalies: {data['total_anomalies']}, By severity: {data['by_severity']}")


class TestKPIPerformanceAPI:
    """KPI & AI Performance System API Tests"""
    
    def test_get_kpi_templates(self):
        """Test /api/kpi/templates endpoint"""
        response = requests.get(f"{BASE_URL}/api/kpi/templates")
        print(f"GET /api/kpi/templates: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "templates" in data
        print(f"KPI Templates count: {len(data['templates'])}")
    
    def test_seed_kpi_templates(self):
        """Test /api/kpi/seed-templates endpoint"""
        response = requests.post(f"{BASE_URL}/api/kpi/seed-templates")
        print(f"POST /api/kpi/seed-templates: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        print(f"Seed templates result: {data['message']}")
    
    def test_get_ai_employee_ranking(self):
        """Test /api/kpi/ai-ranking/employees endpoint"""
        response = requests.get(f"{BASE_URL}/api/kpi/ai-ranking/employees")
        print(f"GET /api/kpi/ai-ranking/employees: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "period" in data
        assert "total_employees" in data
        assert "summary" in data
        assert "rankings" in data
        print(f"Employee ranking - Total: {data['total_employees']}, Summary: {data.get('summary', {})}")
    
    def test_get_ai_branch_ranking(self):
        """Test /api/kpi/ai-ranking/branches endpoint"""
        response = requests.get(f"{BASE_URL}/api/kpi/ai-ranking/branches")
        print(f"GET /api/kpi/ai-ranking/branches: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "period" in data
        assert "total_branches" in data
        assert "rankings" in data
        print(f"Branch ranking - Total: {data['total_branches']}")
    
    def test_get_kpi_targets(self):
        """Test /api/kpi/targets endpoint"""
        response = requests.get(f"{BASE_URL}/api/kpi/targets")
        print(f"GET /api/kpi/targets: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "targets" in data
        print(f"KPI Targets count: {len(data['targets'])}")


class TestCRMAIPromptAPI:
    """CRM AI Prompt Builder API Tests"""
    
    def test_get_prompts(self):
        """Test /api/crm-ai/prompts endpoint"""
        response = requests.get(f"{BASE_URL}/api/crm-ai/prompts")
        print(f"GET /api/crm-ai/prompts: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "prompts" in data
        print(f"CRM AI Prompts count: {len(data['prompts'])}")
    
    def test_seed_prompts(self):
        """Test /api/crm-ai/seed-prompts endpoint"""
        response = requests.post(f"{BASE_URL}/api/crm-ai/seed-prompts")
        print(f"POST /api/crm-ai/seed-prompts: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        print(f"Seed prompts result: {data['message']}")
    
    def test_analyze_complaint(self):
        """Test /api/crm-ai/complaint/analyze endpoint"""
        complaint_text = "Produk saya rusak dan pengiriman terlambat"
        response = requests.post(
            f"{BASE_URL}/api/crm-ai/complaint/analyze",
            params={"complaint_text": complaint_text, "customer_id": "test-customer"}
        )
        print(f"POST /api/crm-ai/complaint/analyze: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "complaint_text" in data
        assert "detected_category" in data
        assert "sentiment" in data
        assert "suggested_response" in data
        assert "priority" in data
        print(f"Complaint analysis - Category: {data['detected_category']}, Priority: {data['priority']}")
    
    def test_get_marketing_scripts(self):
        """Test /api/crm-ai/marketing-scripts endpoint"""
        response = requests.get(f"{BASE_URL}/api/crm-ai/marketing-scripts")
        print(f"GET /api/crm-ai/marketing-scripts: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "scripts" in data
        print(f"Marketing scripts count: {len(data['scripts'])}")
    
    def test_get_product_recommendations(self):
        """Test /api/crm-ai/recommend-products endpoint"""
        response = requests.get(f"{BASE_URL}/api/crm-ai/recommend-products/test-customer-id")
        print(f"GET /api/crm-ai/recommend-products: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "customer_id" in data
        assert "total_recommendations" in data
        assert "recommendations" in data
        print(f"Recommendations: {data['total_recommendations']}")


class TestDataExportAPI:
    """Global Data Export System API Tests"""
    
    def test_export_products_json(self):
        """Test /api/export/master/products endpoint"""
        response = requests.get(f"{BASE_URL}/api/export/master/products?format=json")
        print(f"GET /api/export/master/products: {response.status_code}")
        
        assert response.status_code == 200
        # Check content type
        content_type = response.headers.get('content-type', '')
        assert 'application/json' in content_type
        print(f"Export products - Content-Type: {content_type}")
    
    def test_export_branches_json(self):
        """Test /api/export/master/branches endpoint"""
        response = requests.get(f"{BASE_URL}/api/export/master/branches?format=json")
        print(f"GET /api/export/master/branches: {response.status_code}")
        
        assert response.status_code == 200
        print("Export branches - OK")
    
    def test_export_employees(self):
        """Test /api/export/employees/all endpoint"""
        response = requests.get(f"{BASE_URL}/api/export/employees/all?format=json")
        print(f"GET /api/export/employees/all: {response.status_code}")
        
        assert response.status_code == 200
        print("Export employees - OK")
    
    def test_export_inventory_stock(self):
        """Test /api/export/inventory/stock endpoint"""
        response = requests.get(f"{BASE_URL}/api/export/inventory/stock?format=json")
        print(f"GET /api/export/inventory/stock: {response.status_code}")
        
        assert response.status_code == 200
        print("Export inventory stock - OK")
    
    def test_export_customers(self):
        """Test /api/export/master/customers endpoint"""
        response = requests.get(f"{BASE_URL}/api/export/master/customers?format=json")
        print(f"GET /api/export/master/customers: {response.status_code}")
        
        assert response.status_code == 200
        print("Export customers - OK")
    
    def test_export_products_csv(self):
        """Test /api/export/master/products CSV format"""
        response = requests.get(f"{BASE_URL}/api/export/master/products?format=csv")
        print(f"GET /api/export/master/products (CSV): {response.status_code}")
        
        assert response.status_code == 200
        content_type = response.headers.get('content-type', '')
        assert 'text/csv' in content_type
        print(f"Export products CSV - Content-Type: {content_type}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
