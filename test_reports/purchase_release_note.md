# Purchase Module Consolidation - Release Note

## Blueprint Version: v2.4.4
## Date: 2026-03-17
## Tenant Tested: ocb_titan

---

## Summary

Consolidated duplicate purchase menus into single official PO flow.

## Changes

### Menu Structure (Sidebar.jsx)
- **Removed**: "Daftar Pembelian" menu item (duplicate)
- **Removed**: "Tambah Pembelian" menu item (duplicate)
- **Renamed**: "Pesanan Pembelian" → "Daftar PO Pembelian"
- **Renamed**: "Tambah Pesanan Pembelian" → "Buat PO Pembelian"
- **Added**: "Terima Barang" direct link for easier access

### Route Changes (App.js)
- `/purchase/list` → Redirects to `/purchase/orders`
- `/purchase/add` → Redirects to `/purchase/orders/add`

### Official Flow
```
Buat PO Pembelian → Submit → Terima Barang → Complete
        ↓              ↓           ↓             ↓
      draft        ordered    partial/received   AP
```

## Business Rules (LOCKED)
1. Stock ONLY changes on receiving
2. AP ONLY created on full receipt
3. No stock/journal changes on PO create/submit

## Testing Evidence
- `purchase_consolidated_flow_regression.json` - Full flow test PASS
- `purchase_partial_receive_proof.json` - Partial receipt verified
- `purchase_final_receive_proof.json` - Final receipt + AP verified

## Sync Instructions
After PASS on ocb_titan, sync to:
- ocb_unit_4
- ocb_unt_1
- erp_db

Sync ONLY: code, logic, schema, blueprint_version
DO NOT sync: database content

