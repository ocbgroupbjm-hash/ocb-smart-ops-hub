# OCB AI TITAN - End-to-End API Tests
# Testing all major features: Auth, SUPER AI, Business Manager

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://smart-ops-hub-6.preview.emergentagent.com')

# Test credentials
TEST_EMAIL = "ocbgroupbjm@gmail.com"
TEST_PASSWORD = "admin123"


class TestAuthentication:
    """Test authentication endpoints"""
    
    def test_login_success(self):
        """Test successful login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        assert "token" in data, "Token not in response"
        assert "user" in data, "User not in response"
        assert data["user"]["email"] == TEST_EMAIL
        assert data["user"]["name"] == "Oscar OCB"
        assert data["user"]["role"] == "owner"
        print(f"✅ Login successful for {TEST_EMAIL}")
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@email.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        print("✅ Invalid credentials correctly rejected")
    
    def test_auth_me_with_valid_token(self):
        """Test /auth/me endpoint with valid token"""
        # First login to get token
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        token = login_response.json()["token"]
        
        # Test /auth/me
        response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == TEST_EMAIL
        print("✅ /auth/me endpoint working correctly")


@pytest.fixture(scope="class")
def auth_token():
    """Get authentication token for authenticated tests"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        return response.json()["token"]
    pytest.skip("Authentication failed")


class TestWarroom:
    """Test Warroom Dashboard endpoints"""
    
    def test_warroom_snapshot(self, auth_token):
        """Test warroom snapshot with 41 branches"""
        response = requests.get(f"{BASE_URL}/api/warroom/snapshot", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "total_branches" in data
        assert data["total_branches"] == 41, f"Expected 41 branches, got {data['total_branches']}"
        assert data["active_branches"] == 41
        print(f"✅ Warroom snapshot: {data['total_branches']} branches")
    
    def test_warroom_branches_performance(self, auth_token):
        """Test branch performance endpoint"""
        response = requests.get(f"{BASE_URL}/api/warroom/branches/performance?period=today", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "branches" in data
        assert "total_revenue" in data
        print(f"✅ Branch performance: {len(data['branches'])} branches")
    
    def test_warroom_alerts(self, auth_token):
        """Test alerts endpoint"""
        response = requests.get(f"{BASE_URL}/api/warroom/alerts", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "stock_alerts" in data
        assert "total_alerts" in data
        print(f"✅ Warroom alerts: {data['total_alerts']} total")


class TestAISales:
    """Test AI Sales endpoints"""
    
    def test_list_conversations(self, auth_token):
        """Test listing sales conversations"""
        response = requests.get(f"{BASE_URL}/api/ai-sales/conversations", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "conversations" in data
        assert "total" in data
        print(f"✅ AI Sales conversations: {data['total']} total")
    
    def test_start_conversation(self, auth_token):
        """Test starting a new AI sales conversation"""
        response = requests.post(f"{BASE_URL}/api/ai-sales/conversation/start", 
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "customer_name": "Test Customer",
                "customer_phone": "08123456789",
                "channel": "internal_chat"
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "conversation_id" in data
        assert "messages" in data
        assert len(data["messages"]) > 0, "Welcome message missing"
        print(f"✅ Started conversation: {data['conversation_id'][:8]}...")
        return data["conversation_id"]
    
    def test_send_message_katalog(self, auth_token):
        """Test sending KATALOG message"""
        # First start a conversation
        start_response = requests.post(f"{BASE_URL}/api/ai-sales/conversation/start", 
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"customer_name": "Test", "customer_phone": "08111111111"}
        )
        conv_id = start_response.json()["conversation_id"]
        
        # Send KATALOG message
        response = requests.post(f"{BASE_URL}/api/ai-sales/conversation/{conv_id}/message",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"content": "KATALOG", "message_type": "text"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "ai_response" in data
        assert "Katalog" in data["ai_response"]["content"] or "produk" in data["ai_response"]["content"].lower()
        print("✅ KATALOG command working")
    
    def test_send_message_beli(self, auth_token):
        """Test sending BELI message to add to cart"""
        # Start conversation
        start_response = requests.post(f"{BASE_URL}/api/ai-sales/conversation/start", 
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"customer_name": "Test Beli", "customer_phone": "08222222222"}
        )
        conv_id = start_response.json()["conversation_id"]
        
        # Send BELI message
        response = requests.post(f"{BASE_URL}/api/ai-sales/conversation/{conv_id}/message",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"content": "BELI Telkomsel", "message_type": "text"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "cart_items" in data
        print(f"✅ BELI command working, cart has {len(data['cart_items'])} items")


class TestStockMonitor:
    """Test Stock Monitor endpoints"""
    
    def test_stock_overview(self, auth_token):
        """Test stock overview for all branches"""
        response = requests.get(f"{BASE_URL}/api/stock-monitor/overview", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "total_branches" in data
        assert "total_products" in data
        assert data["total_branches"] == 41
        print(f"✅ Stock overview: {data['total_branches']} branches, {data['total_products']} products")
    
    def test_stock_alerts(self, auth_token):
        """Test stock alerts endpoint"""
        response = requests.get(f"{BASE_URL}/api/stock-monitor/alerts", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "alerts" in data
        assert "total" in data
        print(f"✅ Stock alerts: {data['total']} alerts")


class TestAICFO:
    """Test AI CFO endpoints"""
    
    def test_financial_summary(self, auth_token):
        """Test financial summary endpoint"""
        response = requests.get(f"{BASE_URL}/api/ai-cfo/summary?period=month", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "gross_revenue" in data
        assert "net_profit" in data
        assert "period" in data
        print(f"✅ AI CFO summary: Revenue {data['gross_revenue']}")
    
    def test_profit_analysis(self, auth_token):
        """Test profit analysis endpoint"""
        response = requests.get(f"{BASE_URL}/api/ai-cfo/profit-analysis", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "top_profit_branches" in data
        print("✅ AI CFO profit analysis working")
    
    def test_ai_recommendations(self, auth_token):
        """Test AI CFO recommendations"""
        response = requests.get(f"{BASE_URL}/api/ai-cfo/recommendations", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "recommendations" in data
        print(f"✅ AI CFO recommendations: {len(data['recommendations'])} recommendations")


class TestAIMarketing:
    """Test AI Marketing endpoints"""
    
    def test_campaigns_list(self, auth_token):
        """Test listing marketing campaigns"""
        response = requests.get(f"{BASE_URL}/api/ai-marketing/campaigns", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "campaigns" in data
        assert "total" in data
        print(f"✅ AI Marketing campaigns: {data['total']} total")
    
    def test_customer_segments(self, auth_token):
        """Test customer segmentation"""
        response = requests.get(f"{BASE_URL}/api/ai-marketing/customers/segments", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "total_customers" in data
        assert "by_segment" in data
        print(f"✅ Customer segments: {data['total_customers']} customers")
    
    def test_customer_recommendations(self, auth_token):
        """Test AI marketing recommendations"""
        response = requests.get(f"{BASE_URL}/api/ai-marketing/customers/recommendations", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "recommendations" in data
        print(f"✅ Marketing recommendations: {len(data['recommendations'])} recommendations")


class TestBusinessManager:
    """Test Business Manager endpoints"""
    
    def test_list_businesses(self, auth_token):
        """Test listing available businesses"""
        response = requests.get(f"{BASE_URL}/api/business/list", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "businesses" in data
        assert "current_db" in data
        assert data["current_db"] == "ocb_titan"
        assert len(data["businesses"]) >= 3, f"Expected at least 3 businesses, got {len(data['businesses'])}"
        
        # Verify expected businesses
        business_names = [b["name"] for b in data["businesses"]]
        assert "OCB GROUP" in business_names
        print(f"✅ Business list: {len(data['businesses'])} businesses")
    
    def test_current_business(self, auth_token):
        """Test getting current active business"""
        response = requests.get(f"{BASE_URL}/api/business/current", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "current_db" in data
        assert data["current_db"] == "ocb_titan"
        print(f"✅ Current business: {data['current_db']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
