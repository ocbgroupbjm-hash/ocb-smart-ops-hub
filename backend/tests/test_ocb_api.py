"""
OCB AI Super App - Backend API Tests
Testing: Auth, CRM, Branches, Knowledge, WhatsApp Integration, AI Chat, Analytics
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@ocbai.com"
TEST_PASSWORD = "test123"

class TestHealthAndAuth:
    """Health check and Authentication tests"""
    
    def test_health_check(self):
        """Test API health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print(f"✓ Health check passed: {data}")
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        print(f"✓ Login successful for {TEST_EMAIL}")
        return data["access_token"]
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code in [401, 400]
        print("✓ Invalid login correctly rejected")


class TestCRM:
    """CRM Customer management tests"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Authentication failed")
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_customers(self, auth_headers):
        """Test fetching customers list"""
        response = requests.get(f"{BASE_URL}/api/customers/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Fetched {len(data)} customers")
    
    def test_create_customer(self, auth_headers):
        """Test creating a new customer"""
        test_customer = {
            "name": f"TEST_Customer_{int(time.time())}",
            "phone": "+628123456789",
            "email": f"test_{int(time.time())}@example.com",
            "location": "Jakarta",
            "segment": "regular"
        }
        response = requests.post(f"{BASE_URL}/api/customers/", json=test_customer, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get("name") == test_customer["name"]
        print(f"✓ Created customer: {data.get('name')}")
        return data


class TestBranches:
    """Branch management tests"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Authentication failed")
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_branches(self, auth_headers):
        """Test fetching branches list"""
        response = requests.get(f"{BASE_URL}/api/branches/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Fetched {len(data)} branches")
    
    def test_create_branch(self, auth_headers):
        """Test creating a new branch"""
        test_branch = {
            "name": f"TEST_Branch_{int(time.time())}",
            "location": "Jakarta",  # Required field
            "address": "Test Address, Jakarta",
            "phone": "+628123456789",
            "manager_name": "Test Manager"
        }
        response = requests.post(f"{BASE_URL}/api/branches/", json=test_branch, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get("name") == test_branch["name"]
        print(f"✓ Created branch: {data.get('name')}")


class TestKnowledgeBase:
    """Knowledge Base tests"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Authentication failed")
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_knowledge(self, auth_headers):
        """Test fetching knowledge base"""
        response = requests.get(f"{BASE_URL}/api/knowledge/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Fetched {len(data)} knowledge items")
    
    def test_create_knowledge(self, auth_headers):
        """Test creating knowledge item"""
        test_knowledge = {
            "title": f"TEST_Knowledge_{int(time.time())}",
            "content": "This is test knowledge content for AI training.",
            "category": "general"
        }
        response = requests.post(f"{BASE_URL}/api/knowledge/", json=test_knowledge, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get("title") == test_knowledge["title"]
        print(f"✓ Created knowledge: {data.get('title')}")


class TestWhatsAppIntegration:
    """WhatsApp Integration tests"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Authentication failed")
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_whatsapp_status(self, auth_headers):
        """Test getting WhatsApp integration status"""
        response = requests.get(f"{BASE_URL}/api/whatsapp/status/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "configured" in data
        assert "active" in data
        print(f"✓ WhatsApp status: configured={data.get('configured')}, active={data.get('active')}")
    
    def test_get_whatsapp_config(self, auth_headers):
        """Test getting WhatsApp configuration"""
        response = requests.get(f"{BASE_URL}/api/whatsapp/config/", headers=auth_headers)
        # 200 if exists, 404 if not configured
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert "provider_type" in data
            print(f"✓ WhatsApp config exists: provider={data.get('provider_type')}")
        else:
            print("✓ WhatsApp config not yet configured (404 expected)")
    
    def test_save_whatsapp_config(self, auth_headers):
        """Test saving WhatsApp configuration"""
        config = {
            "provider_type": "meta",
            "business_phone_number": "+628123456789",
            "phone_number_id": "test_phone_id",
            "business_account_id": "test_account_id",
            "default_reply_mode": "customer_service",
            "language": "id",
            "auto_reply_enabled": True,
            "auto_create_crm_customer": True,
            "human_handoff_enabled": False,
            "active_status": False
        }
        response = requests.post(f"{BASE_URL}/api/whatsapp/config/", json=config, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get("provider_type") == "meta"
        print(f"✓ WhatsApp config saved successfully")
    
    def test_get_whatsapp_messages(self, auth_headers):
        """Test fetching WhatsApp messages"""
        response = requests.get(f"{BASE_URL}/api/whatsapp/messages/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Fetched {len(data)} WhatsApp messages")
    
    def test_get_whatsapp_logs(self, auth_headers):
        """Test fetching WhatsApp logs"""
        response = requests.get(f"{BASE_URL}/api/whatsapp/logs/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Fetched {len(data)} WhatsApp logs")
    
    def test_whatsapp_test_message(self, auth_headers):
        """Test WhatsApp test message simulator"""
        test_message = {
            "phone_number": "+628123456789",
            "message_text": "Hello, this is a test message",
            "provider_mode": "test"
        }
        response = requests.post(f"{BASE_URL}/api/whatsapp/test-message/", json=test_message, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert data.get("test_mode") == True
        print(f"✓ WhatsApp test message processed successfully")


class TestAIChat:
    """AI Chat tests"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Authentication failed")
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_ai_chat_message(self, auth_headers):
        """Test sending AI chat message"""
        chat_message = {
            "message": "Hello, what can you help me with?",
            "agent_mode": "customer_service",
            "channel": "webchat",
            "language": "en"
        }
        # AI chat endpoint without trailing slash
        response = requests.post(f"{BASE_URL}/api/ai/chat", json=chat_message, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "conversation_id" in data
        print(f"✓ AI Chat response received: {data.get('response')[:100]}...")


class TestAnalytics:
    """Analytics dashboard tests"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Authentication failed")
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_analytics_dashboard(self, auth_headers):
        """Test fetching analytics dashboard data"""
        response = requests.get(f"{BASE_URL}/api/analytics/dashboard", headers=auth_headers)
        # May redirect with trailing slash
        if response.status_code == 307:
            response = requests.get(f"{BASE_URL}/api/analytics/dashboard/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Analytics dashboard data: {data}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
