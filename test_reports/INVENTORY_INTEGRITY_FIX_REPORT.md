# LAPORAN FIX: P0 INVENTORY INTEGRITY BUG
# Item yang sama menunjukkan angka berbeda di Daftar Item vs Kartu Stok

================================================================
## ROOT CAUSE PASTI
================================================================

**MASALAH UTAMA: 2 struktur data berbeda di `stock_movements`:**

1. **Dokumen LAMA (35 records)**: Field `item_id`, tanpa `product_id`
2. **Dokumen BARU (239 records)**: Field `product_id`, tanpa `item_id`

**Dampak:**
- Kartu Stok query dengan `item_id` → hanya menemukan dokumen lama
- Daftar Item pakai `product_stocks` → balance terpisah, tidak sinkron
- Hasil: **ANGKA BERBEDA** untuk item yang sama!

================================================================
## SOURCE MASING-MASING LAYAR (SEBELUM)
================================================================

| Layar | Source Data | Query Field | Issue |
|-------|-------------|-------------|-------|
| Daftar Item | `product_stocks` | product_id | Cached balance tidak sinkron |
| Kartu Stok | `stock_movements` | item_id | Hanya menemukan dokumen lama |

================================================================
## SOURCE OF TRUTH FINAL (SESUDAH FIX)
================================================================

**KEPUTUSAN ARSITEKTUR:**
- **SSOT = stock_movements** (ledger resmi)
- Semua layar harus query dari `stock_movements`
- Query dengan `$or: [{product_id}, {item_id}]` untuk backward compatibility

| Layar | Source Data | Query | Status |
|-------|-------------|-------|--------|
| Daftar Item | `stock_movements` | `{$or: [product_id, item_id]}` | ✅ FIXED |
| Kartu Stok | `stock_movements` | `{$or: [product_id, item_id]}` | ✅ FIXED |

================================================================
## REKONSILIASI ITEM CONTOH: 001001
================================================================

**Item:** 001001 - VOUCER ORI ISAT 1GB/2H
**ID:** 56eab367-a72c-47bd-8931-1f403199220d

### SEBELUM FIX:
| Source | Stok | Issue |
|--------|------|-------|
| product_stocks | 5 | Cached, tidak sinkron |
| stock_movements (by product_id) | 0 | Tidak ada dokumen dengan product_id ini |
| stock_movements (by item_id) | 50 | Dokumen lama pakai item_id |

### SESUDAH FIX:
| Source | Stok | Status |
|--------|------|--------|
| Daftar Item (stock_movements $or query) | **50** | ✅ |
| Kartu Stok (stock_movements $or query) | **50** | ✅ |

**MATCH!** ✅

================================================================
## REKONSILIASI 10 ITEMS (BUKTI)
================================================================

| # | Code | Name | Daftar Item | Kartu Stok | Match |
|---|------|------|-------------|------------|-------|
| 1 | TPLN15K | TOKEN PLN 15K | 0 | 0 | ✅ |
| 2 | TPLN50K | TOKEN PLN 50K | 0 | 0 | ✅ |
| 3 | 001000 | VOUCER ISAT ZERO | 141 | 141 | ✅ |
| 4 | 001001 | VOUCER ORI ISAT 1GB/2H | 50 | 50 | ✅ |
| 5 | 001002 | VOUCER ORI ISAT 2,5GB/5H | 18 | 18 | ✅ |
| 6 | 001003 | VOUCER ORI ISAT 3,5GB/5H | 18 | 18 | ✅ |
| 7 | 001004 | VOUCER ORI ISAT 5GB/5H | 24 | 24 | ✅ |
| 8 | 001005 | VOUCER ORI ISAT 7GB/7H | 21 | 21 | ✅ |
| 9 | 001006 | VOUCER ORI ISAT 3GB/30H | 0 | 0 | ✅ |
| 10 | 001007 | VOUCER ORI ISAT 5GB 3H | 24 | 24 | ✅ |

**10/10 ITEMS MATCH** ✅

================================================================
## FILE YANG DIUBAH
================================================================

### 1. /app/backend/routes/master_erp.py
**Function:** `list_items()`
**Perubahan:**
- SEBELUM: Query stock dari `product_stocks`
- SESUDAH: Query stock dari `stock_movements` dengan `{$or: [product_id, item_id]}`

### 2. /app/backend/routes/stock_card.py
**Function:** `get_stock_card_modal()`
**Perubahan:**
- SEBELUM: Query dengan `{item_id: ...}`
- SESUDAH: Query dengan `{$or: [{product_id: ...}, {item_id: ...}]}`
- Tambah running balance calculation
- Tambah transaction type labels

================================================================
## SCREENSHOT EVIDENCE
================================================================

| File | Deskripsi |
|------|-----------|
| `/app/test_reports/inventory_integrity_1_daftar_item.png` | Daftar Item dengan STOK dari SSOT |
| `/app/test_reports/inventory_integrity_3_kartu_stok_modal.png` | Item 001001, STOK = 50 |

================================================================
## ARSITEKTUR FINAL INVENTORY
================================================================

```
                    ┌──────────────────┐
                    │ stock_movements  │  ← SINGLE SOURCE OF TRUTH
                    │  (Ledger Resmi)  │
                    └────────┬─────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
              ▼                             ▼
    ┌─────────────────┐           ┌─────────────────┐
    │   Daftar Item   │           │   Kartu Stok    │
    │ (Master Items)  │           │ (Stock Card)    │
    │                 │           │                 │
    │ Query: $or      │           │ Query: $or      │
    │ [product_id,    │           │ [product_id,    │
    │  item_id]       │           │  item_id]       │
    │                 │           │                 │
    │ Result: SUM(qty)│           │ Result: running │
    │                 │           │ balance         │
    └─────────────────┘           └─────────────────┘
              │                             │
              └──────────────┬──────────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │   ANGKA SAMA!    │
                    │  Konsisten 100%  │
                    └──────────────────┘
```

================================================================
## STATUS FINAL
================================================================

# ✅ INVENTORY INTEGRITY BUG FIXED

| Requirement | Status |
|-------------|--------|
| Stok Daftar Item = Kartu Stok | ✅ PASS (10/10 items match) |
| Source SSOT dijelaskan | ✅ stock_movements |
| Reconciliation evidence ada | ✅ Tabel 10 items |
| Filter cabang konsisten | ✅ Tested |
| Screenshot bukti | ✅ 2 screenshots |

================================================================
## CATATAN PENTING
================================================================

1. **Data Legacy**: Ada 35 dokumen dengan field `item_id` (legacy)
2. **Data Baru**: Quick Purchase dan transaksi baru pakai `product_id`
3. **Solusi**: Query dengan `$or` untuk backward compatibility
4. **Rekomendasi**: Migrasi data untuk unifikasi field name (optional)
