# LAPORAN FIX: STOK BARANG MODUL SINKRONISASI
# SSOT: stock_movements untuk SEMUA 3 MODUL

================================================================
## QUERY SOURCE STOK BARANG
================================================================

### SEBELUM FIX
```python
# File: /app/backend/routes/inventory.py
# Function: get_branch_stock()

# SEBELUM: Menggunakan product_stocks dengan default branch filter
branch = branch_id or user.get("branch_id")  # <-- Pakai default branch!
pipeline = [
    {"$match": {"branch_id": branch}},
    # ... lookup ke product_stocks
]
items = await product_stocks.aggregate(pipeline).to_list(limit)
```

**Masalah:**
- Menggunakan `product_stocks` (bukan SSOT)
- Default filter `branch_id = user.branch_id` (HQ)
- Hasil: qty=50 (hanya stok di HQ), bukan total 1750

### SESUDAH FIX
```python
# SESUDAH: Menggunakan stock_movements (SSOT) tanpa default branch
branch = branch_id if branch_id else ""  # <-- NO default branch!

stock_query = {
    "$or": [
        {"product_id": product_id},
        {"item_id": product_id}
    ]
}

if branch:  # HANYA filter jika explicitly provided
    stock_query["branch_id"] = branch

agg_result = await db["stock_movements"].aggregate(pipeline).to_list(1)
```

================================================================
## ROOT CAUSE
================================================================

| Issue | Description |
|-------|-------------|
| **Source salah** | Stok Barang pakai `product_stocks`, Daftar Item/Kartu Stok pakai `stock_movements` |
| **Default branch** | Stok Barang default filter = user.branch_id (HQ), padahal stok mayoritas di branch lain |
| **Backward compat** | Legacy data pakai `item_id`, data baru pakai `product_id` |

================================================================
## FILE YANG DIUBAH
================================================================

| File | Function | Perubahan |
|------|----------|-----------|
| `/app/backend/routes/inventory.py` | `get_branch_stock()` | - Source: `product_stocks` → `stock_movements`<br>- Query: `{$or: [product_id, item_id]}`<br>- Hapus default branch filter |

================================================================
## TABEL REKONSILIASI 3 MODUL (10 ITEMS)
================================================================

| # | Code | Name | Daftar Item | Stok Barang | Kartu Stok | Match |
|---|------|------|-------------|-------------|------------|-------|
| 1 | TPLN15K | TOKEN PLN 15K | 0 | 0 | 0 | ✅ |
| 2 | TPLN50K | TOKEN PLN 50K | 0 | 0 | 0 | ✅ |
| 3 | 001000 | VOUCER ISAT ZERO | 141 | 141 | 141 | ✅ |
| 4 | 001001 | VOUCER ORI ISAT 1GB/2H | 1750 | 1750 | 1750 | ✅ |
| 5 | 001002 | VOUCER ORI ISAT 2,5GB/5H | 18 | 18 | 18 | ✅ |
| 6 | 001003 | VOUCER ORI ISAT 3,5GB/5H | 18 | 18 | 18 | ✅ |
| 7 | 001004 | VOUCER ORI ISAT 5GB/5H | 24 | 24 | 24 | ✅ |
| 8 | 001005 | VOUCER ORI ISAT 7GB/7H | 21 | 21 | 21 | ✅ |
| 9 | 001006 | VOUCER ORI ISAT 3GB/30H | 0 | 0 | 0 | ✅ |
| 10 | 001007 | VOUCER ORI ISAT 5GB 3H | 24 | 24 | 24 | ✅ |

**10/10 ITEMS MATCH** ✅

================================================================
## SCREENSHOT EVIDENCE
================================================================

| File | Description |
|------|-------------|
| `/app/test_reports/stok_barang_reconciled.png` | Halaman Stok Barang menampilkan stok dari SSOT |
| `/app/test_reports/inventory_integrity_1_daftar_item.png` | Daftar Item |

================================================================
## ARSITEKTUR FINAL - 3 MODUL SINKRON
================================================================

```
                    ┌──────────────────┐
                    │ stock_movements  │  ← SINGLE SOURCE OF TRUTH
                    │  (Ledger Resmi)  │
                    └────────┬─────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
          ▼                  ▼                  ▼
    ┌───────────┐      ┌───────────┐      ┌───────────┐
    │  Daftar   │      │   Stok    │      │   Kartu   │
    │   Item    │      │  Barang   │      │   Stok    │
    │           │      │           │      │           │
    │ Query:    │      │ Query:    │      │ Query:    │
    │ $or[prod, │      │ $or[prod, │      │ $or[prod, │
    │ item_id]  │      │ item_id]  │      │ item_id]  │
    └─────┬─────┘      └─────┬─────┘      └─────┬─────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │   ANGKA SAMA!    │
                    │  (001001 = 1750) │
                    └──────────────────┘
```

================================================================
## STATUS FINAL
================================================================

# ✅ STOK BARANG MODUL SINKRONISASI SELESAI

| Requirement | Status |
|-------------|--------|
| Query source Stok Barang dijelaskan | ✅ stock_movements |
| Root cause ditemukan | ✅ Source salah + default branch filter |
| 10 items rekonsiliasi match | ✅ 10/10 MATCH |
| Screenshot evidence | ✅ stok_barang_reconciled.png |
| Daftar Item = Stok Barang = Kartu Stok | ✅ SEMUA SINKRON |

================================================================
## CATATAN ARSITEKTUR
================================================================

**SSOT INVENTORY = stock_movements**

Semua modul yang menampilkan stok WAJIB:
1. Query dari `stock_movements` collection
2. Menggunakan pattern `{$or: [{product_id}, {item_id}]}` untuk backward compatibility
3. TIDAK pakai default branch filter (kecuali user explicitly pilih cabang)
4. Agregasi: SUM(quantity) untuk total stok
