# Rollback Plan - Purchase Module Consolidation

## Date: 2026-03-17
## Blueprint Version: v2.4.3

---

## CURRENT STATE

### Duplicate Modules Identified
1. **Pesanan Pembelian** (menu group)
   - Daftar Pesanan → PurchaseOrders.jsx
   - Tambah Pesanan Pembelian → PurchaseEnterprise.jsx

2. **Daftar Pembelian** (menu group)
   - Daftar Pembelian → PurchaseList.jsx
   - Tambah Pembelian → PurchaseEnterprise.jsx

### Evidence Files
All test evidence stored in `/app/test_reports/`:
- `real_test_po_*.json`
- `real_test_purchase_*.json`
- `purchase_vs_po_*.json`
- `menu_duplicate_audit.md`
- `frontend_route_mapping.json`
- `backend_endpoint_mapping.json`

---

## ROLLBACK OPTIONS

### Option A: Consolidate to Single Menu
**Recommended** - Merge into one "Pembelian" menu

Changes required:
1. Update Sidebar.jsx - remove duplicate menu group
2. Keep PurchaseOrders.jsx as main list
3. Delete or redirect PurchaseList.jsx
4. Single "Tambah Pembelian" entry

### Option B: Keep Both with Different Functions
Create truly different modules:

1. **Purchase Order Flow** (existing)
   - Create PO → Submit → Receive → Complete
   - Stock changes only on receiving
   - AP created on full receipt

2. **Direct Purchase Flow** (NEW - to be created)
   - Create → Post → Done
   - Stock and Journal created immediately on post
   - No receiving step required

---

## ROLLBACK PROCEDURE

If consolidation causes issues:

1. Use Emergent Platform "Rollback" feature
2. Target checkpoint: Before menu consolidation
3. Restore Sidebar.jsx to previous state
4. Verify both menu groups exist

---

## TENANT SYNC RULES

After consolidation PASS on ocb_titan:
- **SYNC**: code, logic, schema, blueprint_version
- **DO NOT SYNC**: transactions, items, journals, stock data

Tenants to sync:
- ocb_unit_4
- ocb_unt_1
- erp_db

