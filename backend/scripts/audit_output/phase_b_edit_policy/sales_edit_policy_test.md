# PHASE B - EDIT POLICY ENFORCEMENT
## Sales Module Edit Policy Test

### Test Date: 2026-03-14
### Rule: POSTED IMMUTABLE

---

## 1. POLICY IMPLEMENTATION

### Rule Matrix:
| Status | Edit Allowed | Action Button |
|--------|--------------|---------------|
| draft | ✅ YES | Edit (purple) |
| pending | ✅ YES | Edit (purple) |
| completed | ❌ NO | Koreksi/Reversal (orange) |
| posted | ❌ NO | Koreksi/Reversal (orange) |
| paid | ❌ NO | Koreksi/Reversal (orange) |
| lunas | ❌ NO | Koreksi/Reversal (orange) |

### Delete Policy:
| Status | Delete Allowed |
|--------|---------------|
| draft | ✅ YES (soft delete) |
| pending | ✅ YES (soft delete) |
| completed/posted | ❌ NO |
| paid/lunas | ❌ NO |

---

## 2. CODE CHANGES

### /app/frontend/src/pages/sales/SalesList.jsx

**handleEdit() function:**
```javascript
const handleEdit = (item) => {
  const isPosted = ['completed', 'posted', 'paid', 'lunas'].includes(item.status?.toLowerCase());
  
  if (isPosted) {
    toast.error(
      'Transaksi yang sudah di-POST tidak bisa diedit langsung. Gunakan fitur Koreksi/Reversal.',
      { duration: 4000 }
    );
    return;
  }
  
  setEditItem(item);
  setShowOwnerEdit(true);
};
```

**UI Button Logic:**
```jsx
{['completed', 'posted', 'paid', 'lunas'].includes(s.status?.toLowerCase()) ? (
  <button onClick={handleReversal} title="Koreksi/Reversal">
    <RotateCcw />
  </button>
) : (
  <button onClick={handleEdit} title="Edit (Draft)">
    <Edit2 />
  </button>
)}
```

---

## 3. BACKEND VALIDATION

Backend juga WAJIB menolak edit untuk transaksi POSTED.
Endpoint yang perlu dipastikan:
- PUT /api/sales/invoices/{id} - reject jika status = posted
- PUT /api/purchases/{id} - reject jika status = posted
- PUT /api/ap/{id} - reject jika status = paid
- PUT /api/ar/{id} - reject jika status = paid

---

## 4. COMPLIANCE

- [x] Frontend menampilkan tombol Koreksi untuk status POSTED
- [x] Frontend block edit untuk status POSTED
- [x] Toast error menjelaskan alasan
- [ ] Backend reject edit untuk POSTED (to be verified)
- [ ] Audit log tercatat untuk attempt edit POSTED (to be implemented)

---

## Status: PARTIAL PASS
Frontend policy enforced, backend validation pending.
