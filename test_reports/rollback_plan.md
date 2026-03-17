# Rollback Plan - PO Delete Policy

## Date: 2026-03-17
## Blueprint Version: v2.4.5

---

## Changes Made

### 1. Backend (purchase.py)
- Added DELETE endpoint `/api/purchase/orders/{po_id}`
- Added delete preview endpoint `/api/purchase/orders/{po_id}/delete-preview`
- Added delete filter params to list endpoint (include_deleted, only_deleted)
- Added DeleteMode constants (SOFT_DELETE, CANCEL_HIDE)

### 2. Frontend (PurchaseOrders.jsx)
- Added delete filter dropdown (Aktif Saja, Dihapus Saja, Semua)
- Added delete confirmation modal with preview
- Updated status badge to show "🗑️ Dihapus" with strikethrough
- Added tombol Hapus for all PO statuses

### 3. Database Schema
New fields on PO documents:
- is_deleted (boolean)
- deleted_at (datetime)
- deleted_by (user_id)
- deleted_by_name (string)
- delete_reason (string)
- delete_mode (SOFT_DELETE | CANCEL_HIDE)

---

## Rollback Procedure

### Option 1: Emergent Platform Rollback
1. Go to Emergent Platform
2. Click "Rollback"
3. Select checkpoint before v2.4.5

### Option 2: Manual Rollback
1. Revert purchase.py to remove DELETE endpoint
2. Revert PurchaseOrders.jsx to remove delete filter and modal
3. Note: Deleted PO documents will remain with is_deleted=true

---

## Post-Rollback Notes
- POs with is_deleted=true will appear in list again (no filter)
- Stock movements and AP records are never affected
- Audit logs are preserved

