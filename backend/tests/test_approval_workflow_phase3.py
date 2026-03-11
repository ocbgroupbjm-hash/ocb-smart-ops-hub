"""
Test Suite for OCB TITAN ERP - Phase 3 Operational Control System
Module: Approval Workflow Engine
Tests:
- GET /api/approval-workflow/types - Approval types list
- POST /api/approval-workflow/check - Check if approval needed
- POST /api/approval-workflow/request - Create approval request
- GET /api/approval-workflow/pending - Pending approvals
- GET /api/approval-workflow/my-requests - User's own requests
- GET /api/approval-workflow/{id} - Approval detail
- POST /api/approval-workflow/{id}/action - Approve/Reject
- GET /api/approval-workflow/dashboard/summary - Dashboard summary
- Role-based access control (kasir cannot approve)
"""

import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')

# Test credentials
OWNER_EMAIL = "ocbgroupbjm@gmail.com"
OWNER_PASSWORD = "admin123"
KASIR_EMAIL = "kasir_test@ocb.com"
KASIR_PASSWORD = "password123"


class TestApprovalWorkflowAuth:
    """Test authentication and token retrieval"""
    
    @pytest.fixture(scope="class")
    def owner_token(self):
        """Get owner/admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": OWNER_EMAIL,
            "password": OWNER_PASSWORD
        })
        assert response.status_code == 200, f"Owner login failed: {response.text}"
        data = response.json()
        return data.get("token") or data.get("access_token")
    
    @pytest.fixture(scope="class")
    def kasir_token(self):
        """Get kasir token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": KASIR_EMAIL,
            "password": KASIR_PASSWORD
        })
        # Kasir may not exist, skip if not
        if response.status_code != 200:
            pytest.skip(f"Kasir login failed: {response.text}")
        data = response.json()
        return data.get("token") or data.get("access_token")
    
    def test_owner_login(self, owner_token):
        """Verify owner can login"""
        assert owner_token is not None
        assert len(owner_token) > 0
        print(f"Owner token obtained: {owner_token[:20]}...")


class TestApprovalTypes:
    """Test GET /api/approval-workflow/types"""
    
    @pytest.fixture(scope="class")
    def owner_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": OWNER_EMAIL,
            "password": OWNER_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        return data.get("token") or data.get("access_token")
    
    def test_get_approval_types(self, owner_token):
        """Test fetching all approval types"""
        response = requests.get(
            f"{BASE_URL}/api/approval-workflow/types",
            headers={"Authorization": f"Bearer {owner_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        print(f"Total approval types: {data['total']}")
    
    def test_approval_types_content(self, owner_token):
        """Test approval types have required fields and correct codes"""
        response = requests.get(
            f"{BASE_URL}/api/approval-workflow/types",
            headers={"Authorization": f"Bearer {owner_token}"}
        )
        data = response.json()
        items = data.get("items", [])
        
        expected_codes = ["purchase_order", "discount", "void_transaction", "price_override", "credit_override"]
        actual_codes = [item["code"] for item in items]
        
        for code in expected_codes:
            assert code in actual_codes, f"Missing approval type: {code}"
        
        # Check each type has required fields
        for item in items:
            assert "code" in item
            assert "name" in item
            assert "description" in item
            assert "levels" in item
            assert "approvers" in item
            print(f"Approval type: {item['code']} - {item['name']}")


class TestApprovalCheck:
    """Test POST /api/approval-workflow/check"""
    
    @pytest.fixture(scope="class")
    def owner_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": OWNER_EMAIL,
            "password": OWNER_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        return data.get("token") or data.get("access_token")
    
    def test_check_purchase_auto_approve(self, owner_token):
        """Test checking if small purchase auto-approves"""
        response = requests.post(
            f"{BASE_URL}/api/approval-workflow/check",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={
                "approval_type": "purchase_order",
                "reference_type": "purchase_order",
                "reference_id": "test-po-123",
                "reference_no": "PO-TEST-001",
                "amount": 5000000,  # 5 juta - below 10 juta limit
                "variance_percent": 0
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["requires_approval"] == False  # Auto-approve
        assert data["required_level"] == 0
        print(f"5M purchase: requires_approval={data['requires_approval']}, level={data['required_level']}")
    
    def test_check_purchase_needs_approval(self, owner_token):
        """Test checking if large purchase needs approval"""
        response = requests.post(
            f"{BASE_URL}/api/approval-workflow/check",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={
                "approval_type": "purchase_order",
                "reference_type": "purchase_order",
                "reference_id": "test-po-456",
                "reference_no": "PO-TEST-002",
                "amount": 25000000,  # 25 juta - needs level 1 approval
                "variance_percent": 0
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["requires_approval"] == True
        assert data["required_level"] == 1
        print(f"25M purchase: requires_approval={data['requires_approval']}, level={data['required_level']}")
    
    def test_check_discount_auto_approve(self, owner_token):
        """Test checking if small discount auto-approves"""
        response = requests.post(
            f"{BASE_URL}/api/approval-workflow/check",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={
                "approval_type": "discount",
                "reference_type": "sales_invoice",
                "reference_id": "test-inv-123",
                "reference_no": "INV-TEST-001",
                "amount": 0,
                "variance_percent": 5  # 5% discount - below 10% limit
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["requires_approval"] == False
        print(f"5% discount: requires_approval={data['requires_approval']}")
    
    def test_check_discount_needs_approval(self, owner_token):
        """Test checking if large discount needs approval"""
        response = requests.post(
            f"{BASE_URL}/api/approval-workflow/check",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={
                "approval_type": "discount",
                "reference_type": "sales_invoice",
                "reference_id": "test-inv-456",
                "reference_no": "INV-TEST-002",
                "amount": 0,
                "variance_percent": 25  # 25% discount - needs level 2 approval
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["requires_approval"] == True
        assert data["required_level"] == 2
        print(f"25% discount: requires_approval={data['requires_approval']}, level={data['required_level']}")
    
    def test_check_void_transaction(self, owner_token):
        """Test void transaction always requires approval"""
        response = requests.post(
            f"{BASE_URL}/api/approval-workflow/check",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={
                "approval_type": "void_transaction",
                "reference_type": "transaction",
                "reference_id": "test-trx-123",
                "reference_no": "TRX-TEST-001",
                "amount": 100000,  # Small amount but still needs approval
                "variance_percent": 0
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["requires_approval"] == True
        print(f"Void transaction: requires_approval={data['requires_approval']}, level={data['required_level']}")


class TestApprovalRequestCreate:
    """Test POST /api/approval-workflow/request"""
    
    @pytest.fixture(scope="class")
    def owner_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": OWNER_EMAIL,
            "password": OWNER_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        return data.get("token") or data.get("access_token")
    
    def test_create_approval_request_auto_approve(self, owner_token):
        """Test creating request that auto-approves"""
        response = requests.post(
            f"{BASE_URL}/api/approval-workflow/request",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={
                "approval_type": "purchase_order",
                "reference_type": "purchase_order",
                "reference_id": f"test-po-auto-{uuid.uuid4().hex[:8]}",
                "reference_no": "PO-AUTO-001",
                "amount": 5000000,  # Below limit
                "variance_percent": 0,
                "requester_notes": "Test auto approve"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "auto_approved"
        assert data["approval_id"] is None
        print(f"Auto-approved: {data['message']}")
    
    def test_create_approval_request_pending(self, owner_token):
        """Test creating request that needs approval"""
        ref_id = f"TEST_po-pending-{uuid.uuid4().hex[:8]}"
        response = requests.post(
            f"{BASE_URL}/api/approval-workflow/request",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={
                "approval_type": "purchase_order",
                "reference_type": "purchase_order",
                "reference_id": ref_id,
                "reference_no": "PO-PENDING-001",
                "amount": 25000000,  # 25 juta - needs approval
                "variance_percent": 0,
                "requester_notes": "Test pending approval"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"
        assert data["approval_id"] is not None
        assert data["approval_no"] is not None
        print(f"Pending approval created: {data['approval_no']} (ID: {data['approval_id']})")
        return data["approval_id"]
    
    def test_create_void_approval_request(self, owner_token):
        """Test creating void transaction approval"""
        ref_id = f"TEST_trx-void-{uuid.uuid4().hex[:8]}"
        response = requests.post(
            f"{BASE_URL}/api/approval-workflow/request",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={
                "approval_type": "void_transaction",
                "reference_type": "transaction",
                "reference_id": ref_id,
                "reference_no": "TRX-VOID-001",
                "amount": 500000,
                "variance_percent": 0,
                "requester_notes": "Customer complaint - void requested"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"
        print(f"Void approval created: {data['approval_no']}")
    
    def test_create_invalid_approval_type(self, owner_token):
        """Test creating request with invalid type"""
        response = requests.post(
            f"{BASE_URL}/api/approval-workflow/request",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={
                "approval_type": "invalid_type",
                "reference_type": "test",
                "reference_id": "test-123",
                "reference_no": "TEST-001",
                "amount": 1000000
            }
        )
        assert response.status_code == 400
        print(f"Invalid type rejected: {response.json()['detail']}")


class TestPendingApprovals:
    """Test GET /api/approval-workflow/pending"""
    
    @pytest.fixture(scope="class")
    def owner_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": OWNER_EMAIL,
            "password": OWNER_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        return data.get("token") or data.get("access_token")
    
    def test_get_pending_approvals(self, owner_token):
        """Test fetching pending approvals"""
        response = requests.get(
            f"{BASE_URL}/api/approval-workflow/pending",
            headers={"Authorization": f"Bearer {owner_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        print(f"Pending approvals: {data['total']}")
        
        # Print first few items
        for item in data["items"][:3]:
            print(f"  - {item['approval_no']}: {item['approval_type']} - {item['status']}")
    
    def test_filter_pending_by_type(self, owner_token):
        """Test filtering pending by approval type"""
        response = requests.get(
            f"{BASE_URL}/api/approval-workflow/pending?approval_type=purchase_order",
            headers={"Authorization": f"Bearer {owner_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # All items should be purchase_order type
        for item in data["items"]:
            assert item["approval_type"] == "purchase_order"
        print(f"Pending purchase orders: {data['total']}")


class TestMyRequests:
    """Test GET /api/approval-workflow/my-requests"""
    
    @pytest.fixture(scope="class")
    def owner_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": OWNER_EMAIL,
            "password": OWNER_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        return data.get("token") or data.get("access_token")
    
    def test_get_my_requests(self, owner_token):
        """Test fetching user's own requests"""
        response = requests.get(
            f"{BASE_URL}/api/approval-workflow/my-requests",
            headers={"Authorization": f"Bearer {owner_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        print(f"My requests: {data['total']}")
    
    def test_filter_my_requests_by_status(self, owner_token):
        """Test filtering my requests by status"""
        response = requests.get(
            f"{BASE_URL}/api/approval-workflow/my-requests?status=pending",
            headers={"Authorization": f"Bearer {owner_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # All items should have pending status
        for item in data["items"]:
            assert item["status"] == "pending"
        print(f"My pending requests: {data['total']}")


class TestApprovalDetail:
    """Test GET /api/approval-workflow/{id}"""
    
    @pytest.fixture(scope="class")
    def owner_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": OWNER_EMAIL,
            "password": OWNER_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        return data.get("token") or data.get("access_token")
    
    @pytest.fixture(scope="class")
    def approval_id(self, owner_token):
        """Create an approval request to test detail"""
        ref_id = f"TEST_detail-{uuid.uuid4().hex[:8]}"
        response = requests.post(
            f"{BASE_URL}/api/approval-workflow/request",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={
                "approval_type": "discount",
                "reference_type": "sales_invoice",
                "reference_id": ref_id,
                "reference_no": "INV-DETAIL-001",
                "amount": 0,
                "variance_percent": 15,  # 15% discount
                "requester_notes": "VIP customer request"
            }
        )
        assert response.status_code == 200
        data = response.json()
        return data["approval_id"]
    
    def test_get_approval_detail(self, owner_token, approval_id):
        """Test fetching approval detail"""
        response = requests.get(
            f"{BASE_URL}/api/approval-workflow/{approval_id}",
            headers={"Authorization": f"Bearer {owner_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == approval_id
        assert "approval_no" in data
        assert "approval_type" in data
        assert "status" in data
        assert "requester_name" in data
        assert "required_level" in data
        assert "required_approvers" in data
        print(f"Approval detail: {data['approval_no']} - Level {data['required_level']}")
    
    def test_get_invalid_approval(self, owner_token):
        """Test fetching non-existent approval"""
        response = requests.get(
            f"{BASE_URL}/api/approval-workflow/non-existent-id",
            headers={"Authorization": f"Bearer {owner_token}"}
        )
        assert response.status_code == 404
        print(f"Invalid ID rejected: {response.json()['detail']}")


class TestApprovalAction:
    """Test POST /api/approval-workflow/{id}/action"""
    
    @pytest.fixture(scope="class")
    def owner_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": OWNER_EMAIL,
            "password": OWNER_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        return data.get("token") or data.get("access_token")
    
    def test_approve_request(self, owner_token):
        """Test approving a request"""
        # Create a new request to approve
        ref_id = f"TEST_approve-{uuid.uuid4().hex[:8]}"
        create_response = requests.post(
            f"{BASE_URL}/api/approval-workflow/request",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={
                "approval_type": "price_override",
                "reference_type": "sales_invoice",
                "reference_id": ref_id,
                "reference_no": "INV-APPROVE-001",
                "amount": 0,
                "variance_percent": 10,  # 10% price override
                "requester_notes": "Special pricing for bulk order"
            }
        )
        assert create_response.status_code == 200
        approval_id = create_response.json()["approval_id"]
        
        # Approve the request
        response = requests.post(
            f"{BASE_URL}/api/approval-workflow/{approval_id}/action",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={
                "action": "approve",
                "notes": "Approved for bulk discount"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["status"] == "approved"
        print(f"Approval successful: {data['message']}")
        
        # Verify status changed
        detail_response = requests.get(
            f"{BASE_URL}/api/approval-workflow/{approval_id}",
            headers={"Authorization": f"Bearer {owner_token}"}
        )
        assert detail_response.status_code == 200
        detail = detail_response.json()
        assert detail["status"] == "approved"
        assert detail["approved_by_name"] is not None
    
    def test_reject_request(self, owner_token):
        """Test rejecting a request"""
        # Create a new request to reject
        ref_id = f"TEST_reject-{uuid.uuid4().hex[:8]}"
        create_response = requests.post(
            f"{BASE_URL}/api/approval-workflow/request",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={
                "approval_type": "credit_override",
                "reference_type": "sales_invoice",
                "reference_id": ref_id,
                "reference_no": "INV-REJECT-001",
                "amount": 5000000,  # 5 juta credit override
                "variance_percent": 0,
                "requester_notes": "Customer exceeds credit limit"
            }
        )
        assert create_response.status_code == 200
        approval_id = create_response.json()["approval_id"]
        
        # Reject the request
        response = requests.post(
            f"{BASE_URL}/api/approval-workflow/{approval_id}/action",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={
                "action": "reject",
                "notes": "Customer has outstanding payment"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["status"] == "rejected"
        print(f"Rejection successful: {data['message']}")
        
        # Verify status changed
        detail_response = requests.get(
            f"{BASE_URL}/api/approval-workflow/{approval_id}",
            headers={"Authorization": f"Bearer {owner_token}"}
        )
        assert detail_response.status_code == 200
        detail = detail_response.json()
        assert detail["status"] == "rejected"
        assert detail["rejected_by_name"] is not None
    
    def test_invalid_action(self, owner_token):
        """Test invalid action type"""
        # Create a request
        ref_id = f"TEST_invalid-{uuid.uuid4().hex[:8]}"
        create_response = requests.post(
            f"{BASE_URL}/api/approval-workflow/request",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={
                "approval_type": "void_transaction",
                "reference_type": "transaction",
                "reference_id": ref_id,
                "reference_no": "TRX-INVALID-001",
                "amount": 100000
            }
        )
        approval_id = create_response.json()["approval_id"]
        
        # Try invalid action
        response = requests.post(
            f"{BASE_URL}/api/approval-workflow/{approval_id}/action",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={
                "action": "invalid_action",
                "notes": ""
            }
        )
        assert response.status_code == 400
        print(f"Invalid action rejected: {response.json()['detail']}")
    
    def test_cannot_act_on_processed_request(self, owner_token):
        """Test cannot approve/reject already processed request"""
        # Create and approve a request
        ref_id = f"TEST_processed-{uuid.uuid4().hex[:8]}"
        create_response = requests.post(
            f"{BASE_URL}/api/approval-workflow/request",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={
                "approval_type": "discount",
                "reference_type": "sales_invoice",
                "reference_id": ref_id,
                "reference_no": "INV-PROCESSED-001",
                "amount": 0,
                "variance_percent": 15
            }
        )
        approval_id = create_response.json()["approval_id"]
        
        # Approve first
        requests.post(
            f"{BASE_URL}/api/approval-workflow/{approval_id}/action",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={"action": "approve", "notes": ""}
        )
        
        # Try to reject already approved
        response = requests.post(
            f"{BASE_URL}/api/approval-workflow/{approval_id}/action",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={"action": "reject", "notes": "Changed my mind"}
        )
        assert response.status_code == 400
        print(f"Double action rejected: {response.json()['detail']}")


class TestRoleBasedAccess:
    """Test role-based access control for approvals"""
    
    @pytest.fixture(scope="class")
    def owner_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": OWNER_EMAIL,
            "password": OWNER_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        return data.get("token") or data.get("access_token")
    
    @pytest.fixture(scope="class")
    def kasir_token(self):
        """Get kasir token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": KASIR_EMAIL,
            "password": KASIR_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Kasir user not available: {response.text}")
        data = response.json()
        return data.get("token") or data.get("access_token")
    
    def test_kasir_cannot_approve(self, owner_token, kasir_token):
        """Test kasir role cannot approve requests"""
        # Create a request as owner
        ref_id = f"TEST_kasir-{uuid.uuid4().hex[:8]}"
        create_response = requests.post(
            f"{BASE_URL}/api/approval-workflow/request",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={
                "approval_type": "void_transaction",
                "reference_type": "transaction",
                "reference_id": ref_id,
                "reference_no": "TRX-KASIR-001",
                "amount": 250000,
                "requester_notes": "Test kasir cannot approve"
            }
        )
        assert create_response.status_code == 200
        approval_id = create_response.json()["approval_id"]
        
        # Try to approve as kasir - should fail with 403
        response = requests.post(
            f"{BASE_URL}/api/approval-workflow/{approval_id}/action",
            headers={"Authorization": f"Bearer {kasir_token}"},
            json={"action": "approve", "notes": "Kasir trying to approve"}
        )
        assert response.status_code == 403
        print(f"Kasir approval blocked: {response.json()['detail']}")
    
    def test_kasir_can_view_pending(self, kasir_token):
        """Test kasir can view pending approvals (but list might be empty)"""
        response = requests.get(
            f"{BASE_URL}/api/approval-workflow/pending",
            headers={"Authorization": f"Bearer {kasir_token}"}
        )
        # Kasir may get empty list or 200 with filtered results
        assert response.status_code == 200
        data = response.json()
        print(f"Kasir sees {data['total']} pending approvals")
    
    def test_owner_can_approve_all(self, owner_token):
        """Test owner can approve all levels"""
        # Create high-level approval (100M+ purchase order)
        ref_id = f"TEST_owner-{uuid.uuid4().hex[:8]}"
        create_response = requests.post(
            f"{BASE_URL}/api/approval-workflow/request",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={
                "approval_type": "purchase_order",
                "reference_type": "purchase_order",
                "reference_id": ref_id,
                "reference_no": "PO-OWNER-001",
                "amount": 150000000,  # 150 juta - level 3 (owner only)
                "requester_notes": "Large purchase needs owner approval"
            }
        )
        assert create_response.status_code == 200
        data = create_response.json()
        approval_id = data["approval_id"]
        assert data["required_level"] == 3
        
        # Owner should be able to approve
        response = requests.post(
            f"{BASE_URL}/api/approval-workflow/{approval_id}/action",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={"action": "approve", "notes": "Owner approved large PO"}
        )
        assert response.status_code == 200
        assert response.json()["status"] == "approved"
        print(f"Owner approved level 3 request successfully")


class TestDashboardSummary:
    """Test GET /api/approval-workflow/dashboard/summary"""
    
    @pytest.fixture(scope="class")
    def owner_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": OWNER_EMAIL,
            "password": OWNER_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        return data.get("token") or data.get("access_token")
    
    def test_get_dashboard_summary(self, owner_token):
        """Test fetching dashboard summary"""
        response = requests.get(
            f"{BASE_URL}/api/approval-workflow/dashboard/summary",
            headers={"Authorization": f"Bearer {owner_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check expected fields
        assert "pending_by_type" in data
        assert "today_stats" in data
        assert "my_pending_requests" in data
        assert "pending_for_my_approval" in data
        assert "total_pending" in data
        
        print(f"Dashboard summary:")
        print(f"  - Total pending: {data['total_pending']}")
        print(f"  - My pending requests: {data['my_pending_requests']}")
        print(f"  - Pending for my approval: {data['pending_for_my_approval']}")
        print(f"  - Pending by type: {data['pending_by_type']}")
        print(f"  - Today stats: {data['today_stats']}")


class TestAuditTrail:
    """Test audit trail for approval actions"""
    
    @pytest.fixture(scope="class")
    def owner_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": OWNER_EMAIL,
            "password": OWNER_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        return data.get("token") or data.get("access_token")
    
    def test_approval_action_creates_audit(self, owner_token):
        """Test that approval/reject creates audit log"""
        # Create and approve a request
        ref_id = f"TEST_audit-{uuid.uuid4().hex[:8]}"
        ref_no = f"INV-AUDIT-{uuid.uuid4().hex[:4].upper()}"
        
        create_response = requests.post(
            f"{BASE_URL}/api/approval-workflow/request",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={
                "approval_type": "discount",
                "reference_type": "sales_invoice",
                "reference_id": ref_id,
                "reference_no": ref_no,
                "amount": 0,
                "variance_percent": 15,
                "requester_notes": "Audit test"
            }
        )
        approval_id = create_response.json()["approval_id"]
        
        # Approve
        action_response = requests.post(
            f"{BASE_URL}/api/approval-workflow/{approval_id}/action",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={"action": "approve", "notes": "Audit trail test"}
        )
        assert action_response.status_code == 200
        
        # Check approval detail has action history
        detail_response = requests.get(
            f"{BASE_URL}/api/approval-workflow/{approval_id}",
            headers={"Authorization": f"Bearer {owner_token}"}
        )
        detail = detail_response.json()
        assert detail["approved_by_name"] is not None
        assert detail["action_at"] is not None
        print(f"Audit trail recorded: Approved by {detail['approved_by_name']} at {detail['action_at']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
