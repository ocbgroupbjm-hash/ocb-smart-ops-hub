"""
OCB TITAN ERP - Phase 3 Testing
Stock Reorder Engine & Warehouse Control Module Tests
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# ==================== FIXTURES ====================

@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for Owner/Admin"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "ocbgroupbjm@gmail.com",
        "password": "admin123"
    })
    if response.status_code == 200:
        return response.json().get("token")
    pytest.fail(f"Authentication failed: {response.status_code}")

@pytest.fixture(scope="module")
def api_client(auth_token):
    """Authenticated requests session"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    })
    return session

@pytest.fixture(scope="module")
def test_product_id(api_client):
    """Get first product ID for testing"""
    response = api_client.get(f"{BASE_URL}/api/products?limit=1")
    if response.status_code == 200:
        items = response.json().get("items", [])
        if items:
            return items[0].get("id")
    return None

@pytest.fixture(scope="module")
def test_warehouse_ids(api_client):
    """Get or create warehouse IDs for testing"""
    # Get existing warehouses
    response = api_client.get(f"{BASE_URL}/api/warehouse")
    if response.status_code == 200:
        warehouses = response.json().get("items", [])
        if len(warehouses) >= 2:
            return warehouses[0]["id"], warehouses[1]["id"]
    return None, None


# ==================== STOCK REORDER ENGINE TESTS ====================

class TestStockReorderPolicy:
    """Stock Reorder Policy API Tests"""
    
    def test_get_reorder_policy(self, api_client):
        """GET /api/stock-reorder/policy - Get reorder policy config"""
        response = api_client.get(f"{BASE_URL}/api/stock-reorder/policy")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        # Validate policy structure
        assert "safety_stock_days" in data
        assert "lead_time_days" in data
        assert "velocity_days" in data
        assert "auto_generate_po" in data
        assert "min_reorder_qty" in data
        assert "rounding_multiple" in data
        
        # Validate default values
        assert data["safety_stock_days"] >= 0
        assert data["lead_time_days"] >= 0
        assert data["velocity_days"] > 0
        print(f"PASS: Reorder policy retrieved - {data}")


class TestStockReorderDashboard:
    """Stock Reorder Dashboard API Tests"""
    
    def test_get_reorder_dashboard(self, api_client):
        """GET /api/stock-reorder/dashboard - Get dashboard summary"""
        response = api_client.get(f"{BASE_URL}/api/stock-reorder/dashboard")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        # Validate dashboard structure
        assert "summary" in data
        summary = data["summary"]
        
        assert "total_products" in summary
        assert "with_stock_settings" in summary
        assert "needs_reorder" in summary
        assert "critical_count" in summary
        assert "high_count" in summary
        assert "medium_count" in summary
        assert "out_of_stock" in summary
        
        # Validate counts are non-negative
        assert summary["total_products"] >= 0
        assert summary["critical_count"] >= 0
        print(f"PASS: Dashboard retrieved - {summary}")
    
    def test_dashboard_contains_critical_items(self, api_client):
        """Verify dashboard shows critical items list"""
        response = api_client.get(f"{BASE_URL}/api/stock-reorder/dashboard")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "critical_items" in data
        assert isinstance(data["critical_items"], list)
        
        # If there are critical items, verify structure
        if data["critical_items"]:
            item = data["critical_items"][0]
            assert "product_id" in item
            assert "product_name" in item
            assert "current_stock" in item
            assert "urgency" in item
            print(f"PASS: Critical items found - {len(data['critical_items'])} items")
        else:
            print("PASS: No critical items (stock is healthy)")


class TestStockReorderSuggestions:
    """Stock Reorder Suggestions API Tests"""
    
    def test_get_reorder_suggestions(self, api_client):
        """GET /api/stock-reorder/suggestions - Get reorder suggestions"""
        response = api_client.get(f"{BASE_URL}/api/stock-reorder/suggestions")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "items" in data
        assert "summary" in data
        
        summary = data["summary"]
        assert "total_items" in summary
        assert "critical" in summary
        assert "high" in summary
        assert "medium" in summary
        assert "low" in summary
        
        print(f"PASS: Suggestions retrieved - {summary['total_items']} items needing reorder")
    
    def test_filter_suggestions_by_urgency(self, api_client):
        """GET /api/stock-reorder/suggestions?urgency=critical"""
        response = api_client.get(f"{BASE_URL}/api/stock-reorder/suggestions?urgency=critical")
        
        assert response.status_code == 200
        data = response.json()
        
        # All items should be critical
        for item in data.get("items", []):
            assert item["urgency"] == "critical", f"Expected critical urgency, got {item['urgency']}"
        
        print(f"PASS: Critical urgency filter works - {len(data.get('items', []))} critical items")
    
    def test_suggestions_item_structure(self, api_client):
        """Verify suggestion item has correct structure"""
        response = api_client.get(f"{BASE_URL}/api/stock-reorder/suggestions")
        
        assert response.status_code == 200
        data = response.json()
        
        if data.get("items"):
            item = data["items"][0]
            # Required fields
            required_fields = [
                "product_id", "product_code", "product_name", "unit",
                "current_stock", "minimum_stock", "maximum_stock",
                "reorder_point", "sales_velocity", "suggested_qty",
                "urgency", "needs_reorder", "days_remaining"
            ]
            for field in required_fields:
                assert field in item, f"Missing field: {field}"
            
            assert item["needs_reorder"] == True
            print(f"PASS: Suggestion structure valid - {item['product_name']}")
        else:
            print("PASS: No suggestions (all stock healthy)")


class TestStockReorderSettings:
    """Stock Reorder Settings API Tests"""
    
    def test_update_stock_settings(self, api_client, test_product_id):
        """PUT /api/stock-reorder/settings - Update product stock settings"""
        if not test_product_id:
            pytest.skip("No product available for testing")
        
        # Update settings
        payload = {
            "product_id": test_product_id,
            "minimum_stock": 15,
            "maximum_stock": 150,
            "lead_time_days": 5
        }
        
        response = api_client.put(f"{BASE_URL}/api/stock-reorder/settings", json=payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("success") == True
        print(f"PASS: Stock settings updated for product {test_product_id}")
        
        # Verify settings were saved
        get_response = api_client.get(f"{BASE_URL}/api/stock-reorder/settings/{test_product_id}")
        assert get_response.status_code == 200
        settings_data = get_response.json()
        
        assert settings_data["settings"]["minimum_stock"] == 15
        assert settings_data["settings"]["maximum_stock"] == 150
        print(f"PASS: Settings persisted - Min: {settings_data['settings']['minimum_stock']}, Max: {settings_data['settings']['maximum_stock']}")


class TestProductVelocity:
    """Product Sales Velocity API Tests"""
    
    def test_get_product_velocity(self, api_client, test_product_id):
        """GET /api/stock-reorder/velocity/{product_id} - Get sales velocity"""
        if not test_product_id:
            pytest.skip("No product available for testing")
        
        response = api_client.get(f"{BASE_URL}/api/stock-reorder/velocity/{test_product_id}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert "product_id" in data
        assert "period_days" in data
        assert "total_sold" in data
        assert "average_daily_velocity" in data
        assert "daily_breakdown" in data
        
        assert data["product_id"] == test_product_id
        assert data["period_days"] == 30  # Default
        print(f"PASS: Velocity retrieved - Avg daily: {data['average_daily_velocity']}")


class TestGeneratePODraft:
    """Generate PO Draft API Tests"""
    
    def test_generate_po_draft(self, api_client):
        """POST /api/stock-reorder/generate-po-draft - Generate PO draft"""
        # API uses query params, not body
        response = api_client.post(f"{BASE_URL}/api/stock-reorder/generate-po-draft?urgency_filter=critical")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "success" in data
        
        if data["success"]:
            assert "drafts" in data
            assert "total_drafts" in data
            assert "total_items" in data
            print(f"PASS: PO draft generated - {data['total_drafts']} drafts with {data['total_items']} items")
        else:
            # No items to reorder is also valid
            assert "message" in data
            print(f"PASS: No items to reorder - {data.get('message')}")


# ==================== WAREHOUSE CONTROL TESTS ====================

class TestWarehouseList:
    """Warehouse List API Tests"""
    
    def test_list_warehouses(self, api_client):
        """GET /api/warehouse - List all warehouses"""
        response = api_client.get(f"{BASE_URL}/api/warehouse")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)
        
        print(f"PASS: {data['total']} warehouses retrieved")
    
    def test_warehouse_item_structure(self, api_client):
        """Verify warehouse item has correct structure"""
        response = api_client.get(f"{BASE_URL}/api/warehouse")
        
        assert response.status_code == 200
        data = response.json()
        
        if data.get("items"):
            wh = data["items"][0]
            required_fields = ["id", "code", "name", "is_active"]
            for field in required_fields:
                assert field in wh, f"Missing field: {field}"
            print(f"PASS: Warehouse structure valid - {wh['name']}")


class TestWarehouseCreate:
    """Warehouse Create API Tests"""
    
    def test_create_warehouse(self, api_client):
        """POST /api/warehouse - Create new warehouse"""
        unique_code = f"WH-TEST-{uuid.uuid4().hex[:6].upper()}"
        
        payload = {
            "name": f"Test Warehouse {unique_code}",
            "code": unique_code,
            "branch_id": "main",
            "address": "Test Address",
            "type": "storage",
            "is_default": False
        }
        
        response = api_client.post(f"{BASE_URL}/api/warehouse", json=payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert data.get("success") == True
        assert "warehouse_id" in data
        print(f"PASS: Warehouse created - ID: {data['warehouse_id']}")
        
        # Store for cleanup
        return data["warehouse_id"]
    
    def test_duplicate_code_rejected(self, api_client):
        """POST /api/warehouse - Duplicate code in same branch should fail"""
        # Get first warehouse that has a branch_id set
        response = api_client.get(f"{BASE_URL}/api/warehouse")
        if response.status_code != 200 or not response.json().get("items"):
            pytest.skip("No warehouses available for testing")
        
        # Find a warehouse with a branch_id
        existing_wh = None
        for wh in response.json()["items"]:
            if wh.get("branch_id"):
                existing_wh = wh
                break
        
        # If no warehouse has branch_id, create one first
        if not existing_wh:
            # Create a warehouse with specific branch_id for testing
            test_code = f"WH-DUP-{uuid.uuid4().hex[:4].upper()}"
            create_resp = api_client.post(f"{BASE_URL}/api/warehouse", json={
                "name": "Dup Test Base",
                "code": test_code,
                "branch_id": "test-branch-dup",
                "type": "storage"
            })
            assert create_resp.status_code == 200
            
            # Now try to create duplicate
            payload = {
                "name": "Duplicate Test",
                "code": test_code,  # Same code
                "branch_id": "test-branch-dup",  # Same branch
                "type": "storage"
            }
        else:
            payload = {
                "name": "Duplicate Test",
                "code": existing_wh["code"],  # Use existing code
                "branch_id": existing_wh["branch_id"],  # Same branch
                "type": "storage"
            }
        
        response = api_client.post(f"{BASE_URL}/api/warehouse", json=payload)
        
        # Should fail due to duplicate code in same branch
        assert response.status_code == 400, f"Expected 400 for duplicate, got {response.status_code}: {response.text}"
        assert "sudah digunakan" in response.json().get("detail", "").lower()
        print("PASS: Duplicate warehouse code rejected")


class TestWarehouseStock:
    """Warehouse Stock API Tests"""
    
    def test_get_warehouse_stock(self, api_client, test_warehouse_ids):
        """GET /api/warehouse/{id}/stock - Get warehouse stock list"""
        source_id, dest_id = test_warehouse_ids
        if not source_id:
            pytest.skip("No warehouse available for testing")
        
        response = api_client.get(f"{BASE_URL}/api/warehouse/{source_id}/stock")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert "warehouse" in data
        assert "items" in data
        assert "total" in data
        assert "low_stock_count" in data
        
        print(f"PASS: Warehouse stock retrieved - {data['total']} products, {data['low_stock_count']} low stock")


class TestWarehouseDashboard:
    """Warehouse Dashboard API Tests"""
    
    def test_get_warehouse_dashboard(self, api_client):
        """GET /api/warehouse/dashboard/summary - Get dashboard summary"""
        response = api_client.get(f"{BASE_URL}/api/warehouse/dashboard/summary")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert "warehouses" in data
        assert "total_warehouses" in data
        assert "pending_transfers" in data
        assert "in_transit_transfers" in data
        assert "recent_transfers" in data
        
        print(f"PASS: Dashboard - {data['total_warehouses']} warehouses, {data['pending_transfers']} pending transfers")


class TestStockTransfer:
    """Stock Transfer API Tests"""
    
    def test_list_transfers(self, api_client):
        """GET /api/warehouse/transfers - List all transfers"""
        response = api_client.get(f"{BASE_URL}/api/warehouse/transfers")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert "items" in data
        assert "total" in data
        
        print(f"PASS: {data['total']} transfers retrieved")
    
    def test_filter_transfers_by_status(self, api_client):
        """GET /api/warehouse/transfers?status=pending"""
        response = api_client.get(f"{BASE_URL}/api/warehouse/transfers?status=pending")
        
        assert response.status_code == 200
        data = response.json()
        
        # All items should have pending status
        for item in data.get("items", []):
            assert item["status"] == "pending", f"Expected pending status, got {item['status']}"
        
        print(f"PASS: Status filter works - {data['total']} pending transfers")
    
    def test_create_transfer_validation_same_warehouse(self, api_client, test_warehouse_ids):
        """POST /api/warehouse/transfer - Same source/dest should fail"""
        source_id, dest_id = test_warehouse_ids
        if not source_id:
            pytest.skip("No warehouse available for testing")
        
        payload = {
            "source_warehouse_id": source_id,
            "destination_warehouse_id": source_id,  # Same warehouse
            "items": [{"product_id": "test", "quantity": 1}],
            "transfer_reason": "Test transfer"
        }
        
        response = api_client.post(f"{BASE_URL}/api/warehouse/transfer", json=payload)
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        assert "sama" in response.json().get("detail", "").lower()
        print("PASS: Same warehouse transfer rejected")
    
    def test_create_transfer_validation_insufficient_stock(self, api_client, test_warehouse_ids, test_product_id):
        """POST /api/warehouse/transfer - Insufficient stock should fail"""
        source_id, dest_id = test_warehouse_ids
        if not source_id or not dest_id or not test_product_id:
            pytest.skip("Required test data not available")
        
        payload = {
            "source_warehouse_id": source_id,
            "destination_warehouse_id": dest_id,
            "items": [{"product_id": test_product_id, "quantity": 999999}],  # Excessive qty
            "transfer_reason": "Test transfer - insufficient stock"
        }
        
        response = api_client.post(f"{BASE_URL}/api/warehouse/transfer", json=payload)
        
        # Should fail due to insufficient stock
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        assert "tidak cukup" in response.json().get("detail", "").lower() or "stok" in response.json().get("detail", "").lower()
        print("PASS: Insufficient stock transfer rejected")


class TestTransferActions:
    """Transfer Action (Approve/Reject/Complete) API Tests"""
    
    def test_invalid_action_rejected(self, api_client):
        """POST /api/warehouse/transfer/{id}/action - Invalid action should fail"""
        # First get a transfer or create one
        transfers_response = api_client.get(f"{BASE_URL}/api/warehouse/transfers?status=pending")
        
        if transfers_response.status_code != 200 or not transfers_response.json().get("items"):
            pytest.skip("No pending transfers available for testing")
        
        transfer_id = transfers_response.json()["items"][0]["id"]
        
        response = api_client.post(f"{BASE_URL}/api/warehouse/transfer/{transfer_id}/action", json={
            "action": "invalid_action",
            "notes": "Test"
        })
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("PASS: Invalid action rejected")


class TestLowStockAlerts:
    """Low Stock Alerts API Tests"""
    
    def test_get_low_stock_alerts(self, api_client):
        """GET /api/stock-reorder/low-stock-alerts"""
        response = api_client.get(f"{BASE_URL}/api/stock-reorder/low-stock-alerts")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert "alerts" in data
        assert "total" in data
        
        # Verify alert structure if alerts exist
        if data["alerts"]:
            alert = data["alerts"][0]
            assert "product_id" in alert
            assert "product_name" in alert
            assert "current_stock" in alert
            assert "urgency" in alert
            assert "message" in alert
            print(f"PASS: {data['total']} low stock alerts - First: {alert['message']}")
        else:
            print("PASS: No low stock alerts (stock healthy)")


# ==================== INTEGRATION TESTS ====================

class TestStockReorderWarehouseIntegration:
    """Integration tests between Stock Reorder and Warehouse modules"""
    
    def test_dashboard_consistency(self, api_client):
        """Verify reorder dashboard and suggestions are consistent"""
        dashboard_response = api_client.get(f"{BASE_URL}/api/stock-reorder/dashboard")
        suggestions_response = api_client.get(f"{BASE_URL}/api/stock-reorder/suggestions")
        
        assert dashboard_response.status_code == 200
        assert suggestions_response.status_code == 200
        
        dashboard = dashboard_response.json()
        suggestions = suggestions_response.json()
        
        # Needs reorder count should match
        assert dashboard["summary"]["needs_reorder"] == suggestions["summary"]["total_items"]
        print(f"PASS: Dashboard and suggestions counts consistent - {dashboard['summary']['needs_reorder']} items")
    
    def test_warehouse_stock_available(self, api_client):
        """Verify warehouse stock endpoint works for all warehouses"""
        warehouses_response = api_client.get(f"{BASE_URL}/api/warehouse")
        
        assert warehouses_response.status_code == 200
        warehouses = warehouses_response.json().get("items", [])
        
        for wh in warehouses[:3]:  # Test first 3 warehouses
            stock_response = api_client.get(f"{BASE_URL}/api/warehouse/{wh['id']}/stock")
            assert stock_response.status_code == 200, f"Failed for warehouse {wh['name']}"
        
        print(f"PASS: Stock endpoint works for {min(3, len(warehouses))} warehouses")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
