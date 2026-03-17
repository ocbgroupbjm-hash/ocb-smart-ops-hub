# Rollback Plan - Purchase Consolidation

## Date: 2026-03-17
## Blueprint Version: v2.4.4

---

## Changes Made

### 1. Menu Consolidation (Sidebar.jsx)
- Removed "Daftar Pembelian" menu
- Removed "Tambah Pembelian" menu
- Renamed "Pesanan Pembelian" → "Daftar PO Pembelian"
- Renamed "Tambah Pesanan Pembelian" → "Buat PO Pembelian"
- Added "Terima Barang" direct link

### 2. Route Consolidation (App.js)
- Added redirect: /purchase/list → /purchase/orders
- Added redirect: /purchase/add → /purchase/orders/add

### 3. Business Rules (LOCKED)
- Stock changes ONLY on receiving
- AP created ONLY on full receipt

---

## Rollback Procedure

If issues occur after sync:

1. **Use Emergent Rollback Feature**
   - Go to Emergent Platform
   - Click "Rollback" option
   - Select checkpoint before v2.4.4

2. **Manual Rollback** (if needed)
   - Restore Sidebar.jsx from git
   - Restore App.js from git
   - Restart frontend

---

## Verification After Rollback

1. Login to each tenant
2. Check menu structure restored
3. Check both routes work:
   - /purchase/orders
   - /purchase/list
4. Check both add routes work:
   - /purchase/orders/add
   - /purchase/add

---

## Contact

For issues, check:
- `/app/test_reports/` for all evidence files
- PRD.md for architecture decisions

