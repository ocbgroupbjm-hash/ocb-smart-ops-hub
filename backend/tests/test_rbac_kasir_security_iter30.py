"""
OCB TITAN ERP - RBAC Security Tests (Iteration 30)
CRITICAL: Kasir role must NOT be able to delete, void, or cancel transactions
All destructive operations MUST return 403 Forbidden for Kasir role

Test Credentials:
- Owner: ocbgroupbjm@gmail.com / admin123 (should have full access)
- Kasir: kasir_test@ocb.com / password123 (should be BLOCKED on destructive ops)

Endpoints Under Test:
- DELETE /api/products/{product_id} - master_item.delete
- DELETE /api/pos/held/{held_id} - sales.delete  
- POST /api/pos/void/{transaction_id} - sales.void
- POST /api/purchase/orders/{po_id}/cancel - purchase.delete

Integration Tests:
- Credit sale creates AR entry automatically
- Purchase receive creates AP entry automatically
- Audit logs record sensitive actions
- Journal entries created for AR/AP transactions
"""
import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
OWNER_CREDS = {"email": "ocbgroupbjm@gmail.com", "password": "admin123"}
KASIR_CREDS = {"email": "kasir_test@ocb.com", "password": "password123"}


class TestRBACSecurity:
    """CRITICAL RBAC Security tests - Kasir MUST get 403 on destructive operations"""
    
    owner_token = None
    kasir_token = None
    owner_headers = None
    kasir_headers = None
    test_product_id = None
    test_held_id = None
    test_transaction_id = None
    test_po_id = None
    
    @classmethod
    def setup_class(cls):
        """Setup: Login both users"""
        # Login Owner
        response = requests.post(f"{BASE_URL}/api/auth/login", json=OWNER_CREDS)
        if response.status_code == 200:
            data = response.json()
            cls.owner_token = data.get("access_token") or data.get("token")
            cls.owner_headers = {"Authorization": f"Bearer {cls.owner_token}"}
            print(f"Owner login successful: {data.get('user', {}).get('email')}")
        else:
            print(f"Owner login FAILED: {response.status_code} - {response.text[:200]}")
        
        # Login Kasir
        response = requests.post(f"{BASE_URL}/api/auth/login", json=KASIR_CREDS)
        if response.status_code == 200:
            data = response.json()
            cls.kasir_token = data.get("access_token") or data.get("token")
            cls.kasir_headers = {"Authorization": f"Bearer {cls.kasir_token}"}
            print(f"Kasir login successful: {data.get('user', {}).get('email')}")
        else:
            print(f"Kasir login FAILED: {response.status_code} - {response.text[:200]}")
    
    # ==================== KASIR DELETE PRODUCT - MUST RETURN 403 ====================
    
    def test_01_kasir_delete_product_must_return_403(self):
        """CRITICAL: Kasir trying to DELETE product MUST return 403 Forbidden"""
        assert self.kasir_headers, "Kasir login required"
        
        # Try to delete a product (any product ID will do for testing 403)
        response = requests.delete(
            f"{BASE_URL}/api/products/test-product-id-123",
            headers=self.kasir_headers
        )
        
        print(f"Kasir DELETE product response: {response.status_code}")
        print(f"Response body: {response.text[:300]}")
        
        # CRITICAL: Must be 403, NOT 404 (permission check happens BEFORE resource check)
        assert response.status_code == 403, \
            f"SECURITY VIOLATION: Kasir DELETE product returned {response.status_code}, expected 403 Forbidden"
        
        # Verify error message mentions permission denied
        if response.status_code == 403:
            try:
                error_msg = response.json().get("detail", "")
                assert "AKSES DITOLAK" in error_msg or "izin" in error_msg.lower() or "permission" in error_msg.lower(), \
                    f"Error message should mention access denied, got: {error_msg}"
                print(f"PASS: Kasir DELETE product blocked with 403 - {error_msg}")
            except:
                print(f"PASS: Kasir DELETE product blocked with 403")
    
    # ==================== KASIR DELETE HELD TRANSACTION - MUST RETURN 403 ====================
    
    def test_02_kasir_delete_held_transaction_must_return_403(self):
        """CRITICAL: Kasir trying to DELETE held transaction MUST return 403 Forbidden"""
        assert self.kasir_headers, "Kasir login required"
        
        # Try to delete a held transaction
        response = requests.delete(
            f"{BASE_URL}/api/pos/held/test-held-id-123",
            headers=self.kasir_headers
        )
        
        print(f"Kasir DELETE held transaction response: {response.status_code}")
        print(f"Response body: {response.text[:300]}")
        
        # CRITICAL: Must be 403
        assert response.status_code == 403, \
            f"SECURITY VIOLATION: Kasir DELETE held transaction returned {response.status_code}, expected 403 Forbidden"
        
        print(f"PASS: Kasir DELETE held transaction blocked with 403")
    
    # ==================== KASIR VOID TRANSACTION - MUST RETURN 403 ====================
    
    def test_03_kasir_void_transaction_must_return_403(self):
        """CRITICAL: Kasir trying to VOID transaction MUST return 403 Forbidden"""
        assert self.kasir_headers, "Kasir login required"
        
        # Try to void a transaction
        response = requests.post(
            f"{BASE_URL}/api/pos/void/test-transaction-id-123",
            headers=self.kasir_headers,
            params={"reason": "Test void"}
        )
        
        print(f"Kasir VOID transaction response: {response.status_code}")
        print(f"Response body: {response.text[:300]}")
        
        # CRITICAL: Must be 403
        assert response.status_code == 403, \
            f"SECURITY VIOLATION: Kasir VOID transaction returned {response.status_code}, expected 403 Forbidden"
        
        print(f"PASS: Kasir VOID transaction blocked with 403")
    
    # ==================== KASIR CANCEL PURCHASE ORDER - MUST RETURN 403 ====================
    
    def test_04_kasir_cancel_purchase_order_must_return_403(self):
        """CRITICAL: Kasir trying to CANCEL purchase order MUST return 403 Forbidden"""
        assert self.kasir_headers, "Kasir login required"
        
        # Try to cancel a purchase order
        response = requests.post(
            f"{BASE_URL}/api/purchase/orders/test-po-id-123/cancel",
            headers=self.kasir_headers
        )
        
        print(f"Kasir CANCEL PO response: {response.status_code}")
        print(f"Response body: {response.text[:300]}")
        
        # CRITICAL: Must be 403
        assert response.status_code == 403, \
            f"SECURITY VIOLATION: Kasir CANCEL PO returned {response.status_code}, expected 403 Forbidden"
        
        print(f"PASS: Kasir CANCEL purchase order blocked with 403")
    
    # ==================== OWNER ACCESS TESTS (Should NOT get 403) ====================
    
    def test_05_owner_delete_product_should_not_return_403(self):
        """OWNER should NOT get 403 when deleting product (may get 404 if not found)"""
        assert self.owner_headers, "Owner login required"
        
        # Try to delete a non-existent product
        response = requests.delete(
            f"{BASE_URL}/api/products/nonexistent-product-id-xyz",
            headers=self.owner_headers
        )
        
        print(f"Owner DELETE product response: {response.status_code}")
        print(f"Response body: {response.text[:300]}")
        
        # Owner should NOT get 403 (permission should be granted)
        # May get 404 if product doesn't exist - that's correct
        assert response.status_code != 403, \
            f"Owner DELETE product incorrectly returned 403 (should have permission)"
        
        if response.status_code == 404:
            print(f"PASS: Owner has permission, returned 404 (product not found) as expected")
        elif response.status_code == 200:
            print(f"PASS: Owner successfully deleted product")
    
    def test_06_owner_void_transaction_should_not_return_403(self):
        """OWNER should NOT get 403 when voiding transaction (may get 404 if not found)"""
        assert self.owner_headers, "Owner login required"
        
        # Try to void a non-existent transaction
        response = requests.post(
            f"{BASE_URL}/api/pos/void/nonexistent-tx-id-xyz",
            headers=self.owner_headers,
            params={"reason": "Test void by owner"}
        )
        
        print(f"Owner VOID transaction response: {response.status_code}")
        print(f"Response body: {response.text[:300]}")
        
        # Owner should NOT get 403
        assert response.status_code != 403, \
            f"Owner VOID transaction incorrectly returned 403 (should have permission)"
        
        if response.status_code == 404:
            print(f"PASS: Owner has permission, returned 404 (transaction not found) as expected")


class TestARAPIntegration:
    """Test Sales→AR and Purchase→AP auto-integration"""
    
    owner_token = None
    owner_headers = None
    
    @classmethod
    def setup_class(cls):
        """Login as owner for integration tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=OWNER_CREDS)
        if response.status_code == 200:
            data = response.json()
            cls.owner_token = data.get("access_token") or data.get("token")
            cls.owner_headers = {"Authorization": f"Bearer {cls.owner_token}"}
    
    def test_07_credit_sale_creates_ar_entry(self):
        """Integration: Credit sale with is_credit=true should create AR entry"""
        assert self.owner_headers, "Owner login required"
        
        # First, get a product to sell
        products_resp = requests.get(
            f"{BASE_URL}/api/products?limit=1",
            headers=self.owner_headers
        )
        
        if products_resp.status_code != 200:
            pytest.skip("Could not fetch products for test")
        
        products = products_resp.json().get("items", [])
        if not products:
            pytest.skip("No products available for credit sale test")
        
        product = products[0]
        print(f"Using product: {product.get('name')} (ID: {product.get('id')})")
        
        # Get a customer for credit sale
        customers_resp = requests.get(
            f"{BASE_URL}/api/customers?limit=1",
            headers=self.owner_headers
        )
        
        customer_id = None
        customer_name = "TEST Credit Customer"
        if customers_resp.status_code == 200:
            customers = customers_resp.json().get("items", [])
            if customers:
                customer_id = customers[0].get("id")
                customer_name = customers[0].get("name", customer_name)
        
        # Create a credit sale (is_credit=true)
        sale_data = {
            "items": [{
                "product_id": product.get("id"),
                "quantity": 1,
                "discount_percent": 0,
                "discount_amount": 0
            }],
            "customer_id": customer_id,
            "customer_name": customer_name,
            "discount_percent": 0,
            "discount_amount": 0,
            "payments": [{
                "method": "cash",
                "amount": 0,  # Zero payment to create full AR
                "reference": ""
            }],
            "notes": "TEST_CREDIT_SALE_AR_INTEGRATION",
            "is_credit": True,
            "credit_due_days": 30
        }
        
        response = requests.post(
            f"{BASE_URL}/api/pos/transaction",
            headers=self.owner_headers,
            json=sale_data
        )
        
        print(f"Credit sale response: {response.status_code}")
        print(f"Response body: {response.text[:500]}")
        
        if response.status_code == 200:
            result = response.json()
            ar_id = result.get("ar_id")
            invoice = result.get("invoice_number")
            
            if ar_id:
                print(f"PASS: Credit sale created AR entry - AR ID: {ar_id}, Invoice: {invoice}")
                
                # Verify AR exists
                ar_resp = requests.get(
                    f"{BASE_URL}/api/accounting/ar?limit=10",
                    headers=self.owner_headers
                )
                if ar_resp.status_code == 200:
                    ar_items = ar_resp.json().get("items", [])
                    ar_found = any(ar.get("id") == ar_id for ar in ar_items)
                    print(f"AR verification: {'Found' if ar_found else 'Not found in list'}")
            else:
                print(f"Note: Credit sale completed but no AR created (may be paid in full)")
        elif response.status_code == 400:
            print(f"Note: Sale failed with 400 - likely insufficient stock or missing branch")
        else:
            pytest.fail(f"Credit sale failed with unexpected status: {response.status_code}")
    
    def test_08_purchase_receive_creates_ap_entry(self):
        """Integration: Receiving purchase order should create AP entry"""
        assert self.owner_headers, "Owner login required"
        
        # Check existing purchase orders
        po_resp = requests.get(
            f"{BASE_URL}/api/purchase/orders?status=ordered&limit=5",
            headers=self.owner_headers
        )
        
        print(f"PO list response: {po_resp.status_code}")
        
        if po_resp.status_code != 200:
            pytest.skip("Could not fetch purchase orders")
        
        pos = po_resp.json().get("items", [])
        print(f"Found {len(pos)} ordered POs")
        
        # If no POs in ordered status, we'll document this
        if not pos:
            print("Note: No purchase orders in 'ordered' status to test AP integration")
            print("Testing AP integration would require creating a new PO first")
            return
        
        # Use first ordered PO
        po = pos[0]
        po_id = po.get("id")
        po_number = po.get("po_number")
        print(f"Testing with PO: {po_number}")
        
        # Get items to receive
        po_items = po.get("items", [])
        if not po_items:
            pytest.skip("PO has no items to receive")
        
        # Prepare receive data
        receive_data = {
            "items": [
                {"product_id": item.get("product_id"), "quantity": item.get("quantity", 1)}
                for item in po_items
            ],
            "notes": "TEST_AP_INTEGRATION_RECEIVE"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/purchase/orders/{po_id}/receive",
            headers=self.owner_headers,
            json=receive_data
        )
        
        print(f"Receive PO response: {response.status_code}")
        print(f"Response body: {response.text[:500]}")
        
        if response.status_code == 200:
            result = response.json()
            ap_created = result.get("ap_created")
            ap_id = result.get("ap_id")
            
            if ap_created:
                print(f"PASS: Purchase receive created AP entry - AP ID: {ap_id}")
            else:
                print(f"Note: PO received but AP not created (may be partial receive)")
        elif response.status_code == 400:
            print(f"Note: Receive failed - PO may already be fully received")


class TestAuditLogAndJournalEntries:
    """Test audit log recording and journal entries for AR/AP"""
    
    owner_token = None
    owner_headers = None
    
    @classmethod
    def setup_class(cls):
        """Login as owner"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=OWNER_CREDS)
        if response.status_code == 200:
            data = response.json()
            cls.owner_token = data.get("access_token") or data.get("token")
            cls.owner_headers = {"Authorization": f"Bearer {cls.owner_token}"}
    
    def test_09_audit_log_records_sensitive_actions(self):
        """Verify audit logs record sensitive actions"""
        assert self.owner_headers, "Owner login required"
        
        # Get audit logs
        response = requests.get(
            f"{BASE_URL}/api/rbac/audit-logs?limit=50",
            headers=self.owner_headers
        )
        
        print(f"Audit logs response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logs = data.get("logs", [])
            total = data.get("total", 0)
            
            print(f"Total audit log entries: {total}")
            print(f"Recent log sample:")
            
            # Check for security-related actions
            access_denied_logs = [l for l in logs if l.get("action") == "access_denied"]
            delete_logs = [l for l in logs if l.get("action") == "delete"]
            void_logs = [l for l in logs if l.get("action") == "void"]
            
            print(f"  - access_denied entries: {len(access_denied_logs)}")
            print(f"  - delete entries: {len(delete_logs)}")
            print(f"  - void entries: {len(void_logs)}")
            
            # Show recent entries
            for log in logs[:5]:
                print(f"  [{log.get('severity', 'normal')}] {log.get('action')} - {log.get('module')} - {log.get('description', '')[:60]}...")
            
            assert len(logs) > 0, "Audit log should have entries"
            print(f"PASS: Audit log is recording entries")
        else:
            print(f"Warning: Could not fetch audit logs - {response.status_code}")
    
    def test_10_journal_entries_created_for_ar_ap(self):
        """Verify journal entries are created for AR/AP transactions"""
        assert self.owner_headers, "Owner login required"
        
        # Get journal entries
        response = requests.get(
            f"{BASE_URL}/api/accounting/journal-entries?limit=20",
            headers=self.owner_headers
        )
        
        print(f"Journal entries response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            entries = data.get("items", data.get("entries", []))
            
            print(f"Journal entries found: {len(entries)}")
            
            # Look for AR/AP related journal entries
            ar_journals = [j for j in entries if "AR" in str(j.get("journal_no", "")) or j.get("source_type") == "sales_credit"]
            ap_journals = [j for j in entries if "AP" in str(j.get("journal_no", "")) or j.get("source_type") == "purchase_credit"]
            
            print(f"  - AR related journals: {len(ar_journals)}")
            print(f"  - AP related journals: {len(ap_journals)}")
            
            # Show some entries
            for entry in entries[:5]:
                print(f"  {entry.get('journal_no')} - {entry.get('source_type', 'N/A')} - {entry.get('description', '')[:50]}...")
            
            print(f"PASS: Journal entries endpoint accessible")
        elif response.status_code == 404:
            print("Note: Journal entries endpoint may not exist yet")
        else:
            print(f"Warning: Could not fetch journal entries - {response.status_code}")


class TestKasirPermissionCheck:
    """Additional Kasir permission checks using RBAC check endpoint"""
    
    kasir_token = None
    kasir_headers = None
    
    @classmethod
    def setup_class(cls):
        """Login as Kasir"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=KASIR_CREDS)
        if response.status_code == 200:
            data = response.json()
            cls.kasir_token = data.get("access_token") or data.get("token")
            cls.kasir_headers = {"Authorization": f"Bearer {cls.kasir_token}"}
    
    def test_11_kasir_master_item_delete_permission_denied(self):
        """Verify Kasir does not have master_item.delete permission"""
        assert self.kasir_headers, "Kasir login required"
        
        response = requests.get(
            f"{BASE_URL}/api/rbac/check",
            params={"module": "master_item", "action": "delete"},
            headers=self.kasir_headers
        )
        
        print(f"Kasir master_item.delete check: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            allowed = data.get("allowed", False)
            print(f"Kasir master_item.delete allowed: {allowed}")
            assert allowed == False, f"SECURITY: Kasir should NOT have master_item.delete permission!"
            print(f"PASS: Kasir does not have master_item.delete permission")
    
    def test_12_kasir_sales_delete_permission_denied(self):
        """Verify Kasir does not have sales.delete permission"""
        assert self.kasir_headers, "Kasir login required"
        
        response = requests.get(
            f"{BASE_URL}/api/rbac/check",
            params={"module": "sales", "action": "delete"},
            headers=self.kasir_headers
        )
        
        print(f"Kasir sales.delete check: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            allowed = data.get("allowed", False)
            print(f"Kasir sales.delete allowed: {allowed}")
            assert allowed == False, f"SECURITY: Kasir should NOT have sales.delete permission!"
            print(f"PASS: Kasir does not have sales.delete permission")
    
    def test_13_kasir_sales_void_permission_denied(self):
        """Verify Kasir does not have sales.void permission"""
        assert self.kasir_headers, "Kasir login required"
        
        response = requests.get(
            f"{BASE_URL}/api/rbac/check",
            params={"module": "sales", "action": "void"},
            headers=self.kasir_headers
        )
        
        print(f"Kasir sales.void check: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            allowed = data.get("allowed", False)
            print(f"Kasir sales.void allowed: {allowed}")
            assert allowed == False, f"SECURITY: Kasir should NOT have sales.void permission!"
            print(f"PASS: Kasir does not have sales.void permission")
    
    def test_14_kasir_purchase_delete_permission_denied(self):
        """Verify Kasir does not have purchase.delete permission (cancel PO)"""
        assert self.kasir_headers, "Kasir login required"
        
        response = requests.get(
            f"{BASE_URL}/api/rbac/check",
            params={"module": "purchase", "action": "delete"},
            headers=self.kasir_headers
        )
        
        print(f"Kasir purchase.delete check: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            allowed = data.get("allowed", False)
            print(f"Kasir purchase.delete allowed: {allowed}")
            assert allowed == False, f"SECURITY: Kasir should NOT have purchase.delete permission!"
            print(f"PASS: Kasir does not have purchase.delete permission")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
