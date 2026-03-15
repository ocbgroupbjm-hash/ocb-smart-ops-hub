# ROLLBACK PLAN - MODUL PERAKITAN VOUCHER
## OCB TITAN ERP × AI - Blueprint v2.4.3
## Date: 2026-03-15

---

## 1. PERUBAHAN YANG DILAKUKAN

### Frontend Changes
| File | Change | Reversible |
|------|--------|------------|
| `/app/frontend/src/App.js` | Removed route `/inventory/assemblies` | YES |
| `/app/frontend/src/pages/inventory/ProductAssembly.jsx` | Removed legacy API fallbacks, updated UI labels | YES |
| `/app/frontend/src/components/layout/Sidebar.jsx` | Menu label changed to "Perakitan Voucher" | YES |

### Backend Changes
| File | Change | Reversible |
|------|--------|------------|
| `/app/backend/routes/assembly_enterprise.py` | Added hard delete endpoint with validation and audit logging | YES |

### Database Changes
| Collection | Change | Reversible |
|------------|--------|------------|
| `assembly_formulas` | Some test formulas deleted via hard delete | NO (data loss) |
| `assembly_components` | Related components deleted | NO (data loss) |
| `audit_logs` | New audit entries for HARD_DELETE_FORMULA | YES (can remove) |

---

## 2. ROLLBACK STEPS

### Step 1: Restore Frontend Route (if needed)
```bash
# Add back the legacy route in App.js
# Line ~391: <Route path="inventory/assemblies" element={<ProductAssembly />} />
```

### Step 2: Restore Legacy API Fallbacks (if needed)
```javascript
// In ProductAssembly.jsx, restore:
const API_LEGACY = '/api/assembly'; // Legacy fallback

// In loadFormulas, restore fallback logic
```

### Step 3: Restore UI Labels (if needed)
```bash
# In Sidebar.jsx line 210:
# Change "Perakitan Voucher" back to "Perakitan"
```

### Step 4: Remove Hard Delete Endpoint (if critical)
```bash
# Comment out or remove the DELETE endpoint in assembly_enterprise.py
# Lines 559-635
```

---

## 3. DATA RECOVERY

### Deleted Formulas (Cannot be automatically recovered)
| Formula ID | Name | Status |
|------------|------|--------|
| 0165b3cf-7cc8-43c6-93c2-bc3e85fd9dfc | TEST-VOUCHER-230630 | Deleted |
| 071b2b45-5c61-4173-b806-464ac9816f32 | TEST-VOUCHER-230717 | Deleted |
| 77ae3566-b675-4613-a9b8-562530bee896 | TEST-AUDIT-DELETE-231559 | Deleted |

### Recovery Option
- Check MongoDB backups if available
- Recreate formulas manually if data is critical

---

## 4. VERIFICATION AFTER ROLLBACK

1. Check frontend loads at `/inventory/assemblies`
2. Check legacy API endpoints respond
3. Verify CRUD operations work
4. Check no 404/500 errors in logs

---

## 5. CONTACTS

- System Architect: [Contact Info]
- Database Admin: [Contact Info]
- DevOps: [Contact Info]

---

## 6. NOTES

- Hard delete is intentional per System Architect requirement
- Deleted formulas were test data, not production data
- All changes are code-level and can be reverted via git
