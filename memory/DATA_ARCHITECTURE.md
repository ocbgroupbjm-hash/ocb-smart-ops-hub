# OCB TITAN ERP - DATA ARCHITECTURE
## Single Source of Truth (SSOT) Documentation

### Last Updated: March 10, 2026

---

## PRINSIP UTAMA

Seluruh sistem menggunakan **SINGLE SOURCE OF TRUTH** (SSOT).
- Tidak ada duplikasi data
- Tidak ada duplikasi logic
- Semua modul membaca dari sumber yang sama

---

## SUMBER DATA RESMI

### 1. ITEMS
```
Source: products collection
Used by: Master Data, Persediaan, Penjualan, Pembelian, Laporan, AI
```

### 2. STOK
```
Source: stock_movements collection
Calculation: SUM(quantity) per item per branch
NOT stored in: products.stock (deprecated)
```

### 3. BRANCH CONFIG (Min/Max)
```
Source: item_branch_stock collection
Fields: stock_minimum, stock_maximum
NOTE: stock_current dihilangkan, dihitung dari movements
```

### 4. TRANSAKSI
```
Source: transactions collection
Types: sale, purchase, transfer, opname, stock_in, stock_out
```

### 5. CABANG
```
Source: branches collection
Used by: All modules requiring branch data
```

### 6. JOURNAL
```
Source: journal_entries collection
Auto-created from transactions
```

---

## API ENDPOINTS (SSOT)

| Endpoint | Description |
|----------|-------------|
| GET /api/ssot/items | Get items with calculated stock |
| GET /api/ssot/items/{id}/stock | Get stock per branch (calculated) |
| GET /api/ssot/items/{id}/stock-card | Get stock card with running balance |
| GET /api/ssot/dashboard/summary | Get dashboard summary |
| GET /api/ssot/reports/stock-summary | Get stock summary report |

---

## FLOW DATA

### Pembelian (Purchase)
```
1. Create transaction (type: purchase)
2. → stock_movements IN (+qty)
3. → journal_entries (Debit: Persediaan, Credit: Hutang)
```

### Penjualan (Sale)
```
1. Create transaction (type: sale)
2. → stock_movements OUT (-qty)
3. → journal_entries (Debit: Kas, Credit: Penjualan)
```

### Transfer
```
1. Create transaction (type: transfer)
2. → stock_movements OUT from source branch (-qty)
3. → stock_movements IN to destination branch (+qty)
```

### Stok Opname
```
1. Create transaction (type: opname)
2. → stock_movements ADJUST (+/- difference)
```

---

## PERHITUNGAN STOK

```javascript
// Stok item dihitung dari:
db.stock_movements.aggregate([
  { $match: { item_id: "xxx" } },
  { $group: { _id: null, total: { $sum: "$quantity" } } }
])

// Stok per cabang:
db.stock_movements.aggregate([
  { $match: { item_id: "xxx" } },
  { $group: { _id: "$branch_id", stock: { $sum: "$quantity" } } }
])
```

---

## AUDIT STATUS

| Item | Status |
|------|--------|
| products.stock | ❌ DEPRECATED (tidak dipakai) |
| item_branch_stock.stock_current | ❌ DEPRECATED (dihitung dari movements) |
| stock_movements | ✅ ACTIVE (single source for stock) |
| transactions | ✅ ACTIVE (single source for transactions) |
| journal_entries | ✅ ACTIVE (auto-generated) |

---

## SYNC TEST RESULTS

```
SSOT Service Stock:     100
Branch Stock Service:   100
Stock Card Service:     100
✅ ALL SYNCHRONIZED
```

---

## COLLECTIONS

| Collection | Count | Purpose |
|------------|-------|---------|
| products | 32 | Item master data |
| branches | 46 | Branch/location data |
| stock_movements | 23 | Stock movement ledger |
| item_branch_stock | 230+ | Stock config (min/max only) |
| transactions | 1949 | All transactions |
| journal_entries | Auto | Accounting journal |

---

## FILES

| File | Purpose |
|------|---------|
| /app/backend/routes/ssot_service.py | SSOT Service APIs |
| /app/backend/routes/master_erp.py | Items CRUD |
| /app/backend/routes/branch_stock.py | Branch stock management |
| /app/backend/routes/stock_card.py | Stock card (kartu stok) |

---

## RULES

1. **TIDAK BOLEH** menyimpan stock di products collection
2. **TIDAK BOLEH** update stock_current langsung di item_branch_stock
3. **SEMUA** perubahan stok HARUS melalui stock_movements
4. **SEMUA** transaksi HARUS membuat journal_entries
