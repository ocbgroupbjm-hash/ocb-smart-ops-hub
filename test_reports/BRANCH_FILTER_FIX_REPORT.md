# LAPORAN FIX: BRANCH FILTER DAFTAR ITEM
# P0 BUG: Items hilang saat filter cabang tertentu

================================================================
## ROOT CAUSE PASTI
================================================================

**Masalah di:** `/app/backend/routes/master_erp.py` function `list_items()`

**Query SEBELUM (SALAH):**
```python
# Line 94-96 (SEBELUM)
# Branch filter (CABANG sebagai lokasi utama)
if branch_id:
    query["branch_id"] = branch_id  # <-- FILTER ITEMS by branch_id field
```

**Efek:**
- Saat user pilih Headquarters, query mencari `items WHERE branch_id == "HQ_ID"`
- Sebagian besar items tidak punya `branch_id` atau punya nilai berbeda
- Hasilnya: **0 items** (daftar kosong)

================================================================
## QUERY SEBELUM vs SESUDAH
================================================================

### SEBELUM (SALAH)
```python
@router.get("/items")
async def list_items(branch_id: str = ""):
    query = {}
    
    # SALAH: branch_id filter items, bukan stok
    if branch_id:
        query["branch_id"] = branch_id
    
    result = await items.find(query).to_list()
    
    # TIDAK ADA stock lookup dari product_stocks
    return {"items": result}
```

### SESUDAH (BENAR)
```python
@router.get("/items")
async def list_items(branch_id: str = ""):
    query = {}
    
    # BENAR: branch_id TIDAK memfilter items
    # branch_id hanya untuk lookup stok
    
    result = await items.find(query).to_list()
    
    # STOCK LOOKUP dari product_stocks
    for item in result:
        if branch_id:
            # Cabang tertentu: stok cabang itu saja
            stock_rec = await product_stocks.find_one(
                {"product_id": item["id"], "branch_id": branch_id}
            )
            item["stock"] = stock_rec.get("quantity", 0) if stock_rec else 0
        else:
            # Semua Cabang: agregat semua
            agg = await product_stocks.aggregate([
                {"$match": {"product_id": item["id"]}},
                {"$group": {"_id": None, "total": {"$sum": "$quantity"}}}
            ]).to_list()
            item["stock"] = agg[0]["total"] if agg else 0
    
    return {"items": result}
```

================================================================
## TEST RESULTS
================================================================

### TEST 1: Tanpa filter branch (Cabang = Semua)
```
GET /api/master/items?limit=5
Response:
  Total items: 176
  TPLN15K | TOKEN PLN 15K | stock=0
  TPLN50K | TOKEN PLN 50K | stock=0
  001000 | VOUCER ISAT ZERO | stock=28508
  001001 | VOUCER ORI ISAT 1GB/2H | stock=5
  001002 | VOUCER ORI ISAT 2,5GB/5H | stock=5570
```
✅ 176 items ditampilkan dengan stok agregat

### TEST 2: Filter branch = Headquarters
```
GET /api/master/items?limit=5&branch_id=0acd2ffd-c2d9-4324-b860-a4626840e80e
Response:
  Total items: 176
  TPLN15K | TOKEN PLN 15K | stock=0
  TPLN50K | TOKEN PLN 50K | stock=0
  001000 | VOUCER ISAT ZERO | stock=0
  001001 | VOUCER ORI ISAT 1GB/2H | stock=0
  001002 | VOUCER ORI ISAT 2,5GB/5H | stock=0
```
✅ 176 items TETAP ditampilkan, stok sesuai cabang HQ (banyak 0)

### TEST 3: Validasi stok PULSA INDOSAT 5K (dari Quick Purchase)
```
Cabang = Semua:      stock=200 ✅
Cabang = HQ:         stock=0   ✅ (tidak ada stok di HQ)
Cabang = 3 FRONT:    stock=200 ✅ (Quick Purchase masuk ke sini)
```

================================================================
## SCREENSHOT
================================================================

| File | Deskripsi |
|------|-----------|
| `/app/test_reports/branch_filter_fix_1_semua.png` | Cabang = Semua, 176 items, stok agregat |

================================================================
## BUKTI VALIDASI
================================================================

| Requirement | Status |
|-------------|--------|
| Item tetap tampil di semua filter cabang | ✅ PASS (176 items) |
| Cabang = Semua → total stok semua cabang | ✅ PASS |
| Cabang tertentu → stok hanya cabang itu | ✅ PASS |
| Stok 0 jika tidak ada di cabang tersebut | ✅ PASS |
| Daftar TIDAK kosong palsu | ✅ PASS |

================================================================
## FILE TERDAMPAK
================================================================

| File | Perubahan |
|------|-----------|
| `/app/backend/routes/master_erp.py` | Function `list_items()` - Hapus branch_id dari query filter, tambah stock lookup dari product_stocks |

================================================================
## STATUS FINAL
================================================================

# ✅ FIX BERHASIL

Daftar item sekarang:
1. SELALU menampilkan semua master items (dari collection `items`)
2. Filter cabang hanya mempengaruhi NILAI STOK (dari `product_stocks`)
3. Item dengan stok 0 di cabang tertentu TETAP ditampilkan
4. Stok agregat untuk "Semua Cabang" benar
5. Stok per cabang untuk filter cabang tertentu benar

================================================================
## ARSITEKTUR YANG DITEGAKKAN
================================================================

| Rule | Implementasi |
|------|--------------|
| Master source = items (products) | ✅ Query dari collection `items` |
| Stok source = product_stocks | ✅ Stock lookup dari `product_stocks` |
| branch_id filter stok, bukan items | ✅ branch_id hanya untuk stock lookup |
| Left join semantic | ✅ Item tetap tampil, stok 0 jika tidak ada |
