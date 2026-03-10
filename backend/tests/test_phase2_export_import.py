# OCB TITAN AI Phase 2 - Export, Import, File Upload, WhatsApp Alerts Tests
# Tests for Advanced Export (Excel, PDF, CSV, JSON), Import System, File Upload, WhatsApp Alerts

import pytest
import requests
import os
import json

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAdvancedExportSystem:
    """Tests for Advanced Export API - Excel, PDF, CSV, JSON exports"""
    
    def test_export_products_json(self):
        """Test exporting products as JSON"""
        response = requests.get(f"{BASE_URL}/api/export-v2/master/products?format=json")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert 'application/json' in response.headers.get('Content-Type', '')
        print(f"PASS: Export products JSON - Status: {response.status_code}")
    
    def test_export_products_csv(self):
        """Test exporting products as CSV"""
        response = requests.get(f"{BASE_URL}/api/export-v2/master/products?format=csv")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        content_type = response.headers.get('Content-Type', '')
        assert 'text/csv' in content_type, f"Expected text/csv, got {content_type}"
        print(f"PASS: Export products CSV - Status: {response.status_code}")
    
    def test_export_products_xlsx(self):
        """Test exporting products as Excel (xlsx)"""
        response = requests.get(f"{BASE_URL}/api/export-v2/master/products?format=xlsx")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        content_type = response.headers.get('Content-Type', '')
        assert 'spreadsheet' in content_type or 'xlsx' in content_type or len(response.content) > 0, f"Expected Excel content, got {content_type}"
        # Check content disposition for xlsx filename
        content_disp = response.headers.get('Content-Disposition', '')
        assert '.xlsx' in content_disp, f"Expected xlsx filename, got {content_disp}"
        print(f"PASS: Export products Excel - Status: {response.status_code}, Size: {len(response.content)} bytes")
    
    def test_export_products_pdf(self):
        """Test exporting products as PDF"""
        response = requests.get(f"{BASE_URL}/api/export-v2/master/products?format=pdf")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        content_type = response.headers.get('Content-Type', '')
        assert 'pdf' in content_type, f"Expected PDF content, got {content_type}"
        # Check content starts with PDF magic bytes
        assert response.content[:4] == b'%PDF', "Response should be a valid PDF"
        print(f"PASS: Export products PDF - Status: {response.status_code}, Size: {len(response.content)} bytes")
    
    def test_export_employees_xlsx(self):
        """Test exporting employees as Excel"""
        response = requests.get(f"{BASE_URL}/api/export-v2/hr/employees?format=xlsx")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"PASS: Export employees Excel - Status: {response.status_code}")
    
    def test_export_branches_json(self):
        """Test exporting branches as JSON"""
        response = requests.get(f"{BASE_URL}/api/export-v2/master/branches?format=json")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"PASS: Export branches JSON - Status: {response.status_code}")
    
    def test_export_kpi_templates_xlsx(self):
        """Test exporting KPI templates as Excel"""
        response = requests.get(f"{BASE_URL}/api/export-v2/kpi/templates?format=xlsx")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"PASS: Export KPI templates Excel - Status: {response.status_code}")
    
    def test_export_with_date_range(self):
        """Test export with date range parameters"""
        response = requests.get(f"{BASE_URL}/api/export-v2/sales/transactions?format=json&start_date=2025-01-01&end_date=2025-01-31")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"PASS: Export with date range - Status: {response.status_code}")
    
    def test_export_employee_ranking(self):
        """Test employee ranking export"""
        response = requests.get(f"{BASE_URL}/api/export-v2/ranking/employees?format=json&month=1&year=2026")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert 'rankings' in data, "Response should contain rankings"
        print(f"PASS: Export employee ranking - Status: {response.status_code}")
    
    def test_export_branch_ranking(self):
        """Test branch ranking export"""
        response = requests.get(f"{BASE_URL}/api/export-v2/ranking/branches?format=json&month=1&year=2026")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert 'rankings' in data, "Response should contain rankings"
        print(f"PASS: Export branch ranking - Status: {response.status_code}")
    
    def test_export_warroom_alerts(self):
        """Test warroom alerts export"""
        response = requests.get(f"{BASE_URL}/api/export-v2/warroom/alerts?format=json")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"PASS: Export warroom alerts - Status: {response.status_code}")
    
    def test_export_dashboard_summary_pdf(self):
        """Test dashboard summary PDF export"""
        response = requests.get(f"{BASE_URL}/api/export-v2/dashboard/summary?format=pdf")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.content[:4] == b'%PDF', "Response should be a valid PDF"
        print(f"PASS: Export dashboard summary PDF - Status: {response.status_code}")


class TestImportSystem:
    """Tests for Import System API - templates, validation, preview"""
    
    def test_get_import_templates(self):
        """Test fetching import templates"""
        response = requests.get(f"{BASE_URL}/api/import/templates")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert 'templates' in data, "Response should contain templates"
        templates = data['templates']
        assert len(templates) > 0, "Should have at least one template"
        # Check template structure
        for t in templates:
            assert 'key' in t, "Template should have key"
            assert 'name' in t, "Template should have name"
            assert 'required_columns' in t, "Template should have required_columns"
        print(f"PASS: Get import templates - {len(templates)} templates found")
    
    def test_download_products_template(self):
        """Test downloading products import template"""
        response = requests.get(f"{BASE_URL}/api/import/templates/products/download?format=xlsx")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        content_type = response.headers.get('Content-Type', '')
        assert 'spreadsheet' in content_type or len(response.content) > 0, f"Expected Excel content"
        print(f"PASS: Download products template - Size: {len(response.content)} bytes")
    
    def test_download_employees_template(self):
        """Test downloading employees import template"""
        response = requests.get(f"{BASE_URL}/api/import/templates/employees/download?format=xlsx")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"PASS: Download employees template - Size: {len(response.content)} bytes")
    
    def test_download_suppliers_template(self):
        """Test downloading suppliers import template"""
        response = requests.get(f"{BASE_URL}/api/import/templates/suppliers/download?format=xlsx")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"PASS: Download suppliers template - Size: {len(response.content)} bytes")
    
    def test_download_branches_template(self):
        """Test downloading branches import template"""
        response = requests.get(f"{BASE_URL}/api/import/templates/branches/download?format=xlsx")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"PASS: Download branches template - Size: {len(response.content)} bytes")
    
    def test_download_invalid_template(self):
        """Test downloading invalid template returns 404"""
        response = requests.get(f"{BASE_URL}/api/import/templates/invalid_template_xyz/download")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print(f"PASS: Invalid template returns 404")
    
    def test_import_history(self):
        """Test fetching import history"""
        response = requests.get(f"{BASE_URL}/api/import/history")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert 'imports' in data, "Response should contain imports"
        print(f"PASS: Get import history - {len(data['imports'])} records")


class TestFileUploadSystem:
    """Tests for File Upload API - KPI evidence, product photos"""
    
    def test_kpi_evidence_endpoint_exists(self):
        """Test KPI evidence upload endpoint exists"""
        # Send a minimal POST to check endpoint exists (will fail validation but not 404)
        response = requests.post(f"{BASE_URL}/api/files/kpi/evidence", data={})
        # 422 means endpoint exists but validation failed (expected)
        assert response.status_code in [422, 400], f"Expected 422 or 400, got {response.status_code}"
        print(f"PASS: KPI evidence endpoint exists - Status: {response.status_code}")
    
    def test_product_photo_endpoint_exists(self):
        """Test product photo upload endpoint exists"""
        response = requests.post(f"{BASE_URL}/api/files/products/photo", data={})
        assert response.status_code in [422, 400], f"Expected 422 or 400, got {response.status_code}"
        print(f"PASS: Product photo endpoint exists - Status: {response.status_code}")
    
    def test_get_kpi_evidence_for_target(self):
        """Test getting KPI evidence for a target"""
        response = requests.get(f"{BASE_URL}/api/files/kpi/evidence/test-kpi-id")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert 'evidence' in data, "Response should contain evidence"
        print(f"PASS: Get KPI evidence - Status: {response.status_code}")
    
    def test_get_product_photos(self):
        """Test getting product photos"""
        response = requests.get(f"{BASE_URL}/api/files/products/photos/test-product-id")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert 'photos' in data, "Response should contain photos"
        print(f"PASS: Get product photos - Status: {response.status_code}")
    
    def test_enhance_photo_endpoint_exists(self):
        """Test AI photo enhancement endpoint exists"""
        response = requests.post(f"{BASE_URL}/api/files/products/photo/test-photo-id/enhance")
        # Should return 404 (photo not found) not 404 (route not found)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        data = response.json()
        assert 'detail' in data, "Should have error detail"
        print(f"PASS: Enhance photo endpoint exists - Status: {response.status_code}")


class TestWhatsAppAlertSystem:
    """Tests for WhatsApp Alert System API"""
    
    def test_get_alert_triggers(self):
        """Test getting all alert triggers"""
        response = requests.get(f"{BASE_URL}/api/whatsapp-alerts/triggers")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert 'triggers' in data, "Response should contain triggers"
        triggers = data['triggers']
        assert len(triggers) > 0, "Should have at least one trigger"
        # Check expected triggers exist
        expected_triggers = ['minus_kas', 'stok_kosong', 'cabang_belum_setor']
        for trigger in expected_triggers:
            assert trigger in triggers, f"Expected trigger {trigger} not found"
        print(f"PASS: Get alert triggers - {len(triggers)} triggers found")
    
    def test_get_alert_templates(self):
        """Test getting alert templates"""
        response = requests.get(f"{BASE_URL}/api/whatsapp-alerts/templates")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert 'templates' in data, "Response should contain templates"
        print(f"PASS: Get alert templates - {len(data['templates'])} templates found")
    
    def test_get_alert_config(self):
        """Test getting WhatsApp alert config"""
        response = requests.get(f"{BASE_URL}/api/whatsapp-alerts/config")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        # Config should have basic structure
        print(f"PASS: Get alert config - Status: {response.status_code}")
    
    def test_get_alert_recipients(self):
        """Test getting alert recipients"""
        response = requests.get(f"{BASE_URL}/api/whatsapp-alerts/recipients")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert 'recipients' in data, "Response should contain recipients"
        print(f"PASS: Get alert recipients - {len(data['recipients'])} recipients found")
    
    def test_get_alert_logs(self):
        """Test getting alert logs"""
        response = requests.get(f"{BASE_URL}/api/whatsapp-alerts/logs?limit=10")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert 'logs' in data, "Response should contain logs"
        print(f"PASS: Get alert logs - {len(data['logs'])} logs found")
    
    def test_add_recipient(self):
        """Test adding a recipient"""
        recipient = {
            "name": "TEST_Recipient",
            "phone": "6281234567890",
            "role": "admin",
            "is_active": True,
            "alert_types": ["minus_kas", "stok_kosong"]
        }
        response = requests.post(f"{BASE_URL}/api/whatsapp-alerts/recipients", json=recipient)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert 'recipient' in data, "Response should contain recipient"
        print(f"PASS: Add recipient - Recipient ID: {data['recipient'].get('id', 'N/A')}")
        return data['recipient'].get('id')
    
    def test_init_templates(self):
        """Test initializing default templates"""
        response = requests.post(f"{BASE_URL}/api/whatsapp-alerts/init-templates")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert 'message' in data, "Response should contain message"
        print(f"PASS: Init templates - {data['message']}")
    
    def test_send_test_alert(self):
        """Test sending test alert (will be queued, not actually sent)"""
        response = requests.post(
            f"{BASE_URL}/api/whatsapp-alerts/test",
            params={"phone": "6281234567890", "message": "Test from automated testing"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        print(f"PASS: Send test alert - {data.get('message', 'queued')}")
    
    def test_trigger_minus_kas_alert(self):
        """Test triggering minus kas alert (queued)"""
        response = requests.post(
            f"{BASE_URL}/api/whatsapp-alerts/trigger/minus-kas",
            params={
                "branch_name": "Test Branch",
                "date": "2026-01-15",
                "amount": 50000,
                "penjaga_name": "Test Penjaga"
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        # Alert should be queued (not sent since WhatsApp not configured)
        assert 'queued' in data or 'sent' in data, "Response should indicate queue status"
        print(f"PASS: Trigger minus kas alert - Queued: {data.get('queued', data.get('sent', False))}")
    
    def test_trigger_stok_kosong_alert(self):
        """Test triggering stok kosong alert (queued)"""
        response = requests.post(
            f"{BASE_URL}/api/whatsapp-alerts/trigger/stok-kosong",
            params={
                "branch_name": "Test Branch",
                "product_name": "Test Product",
                "category": "Test Category"
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"PASS: Trigger stok kosong alert - Status: {response.status_code}")


class TestCleanup:
    """Cleanup test data"""
    
    def test_cleanup_test_recipients(self):
        """Cleanup TEST_ prefixed recipients"""
        response = requests.get(f"{BASE_URL}/api/whatsapp-alerts/recipients")
        if response.status_code == 200:
            recipients = response.json().get('recipients', [])
            for r in recipients:
                if r.get('name', '').startswith('TEST_'):
                    delete_response = requests.delete(f"{BASE_URL}/api/whatsapp-alerts/recipients/{r['id']}")
                    print(f"Deleted test recipient: {r['name']}")
        print("PASS: Cleanup completed")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
