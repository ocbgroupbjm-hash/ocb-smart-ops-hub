# Purchase Consolidation - Final Rollback Plan

## Blueprint: v2.4.4
## Date: 2026-03-17

---

## Rollback Trigger Conditions
- Critical bug in purchase flow
- Menu navigation broken
- Stock movements incorrect
- AP creation failing

---

## Rollback Procedure

### Option 1: Emergent Platform Rollback (Recommended)
1. Go to Emergent Platform
2. Click "Rollback" 
3. Select checkpoint before v2.4.4
4. Verify all tenants working

### Option 2: Manual Rollback
1. Restore Sidebar.jsx from git (restore duplicate menu items)
2. Restore App.js from git (remove redirects)
3. Restart frontend
4. Verify both routes work

---

## Post-Rollback Verification
1. Login to each tenant
2. Verify "Daftar Pembelian" menu exists
3. Verify "Tambah Pembelian" menu exists
4. Test /purchase/list route
5. Test /purchase/add route

---

## Contacts
- Evidence files: /app/test_reports/
- PRD: /app/memory/PRD.md

