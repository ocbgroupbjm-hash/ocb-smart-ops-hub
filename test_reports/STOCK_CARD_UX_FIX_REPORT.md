# Stock Card UX Fix Report - 2026-03-20

## Issue Reported
User melaporkan bahwa item `001002` menunjukkan stok 18 di "Daftar Item" tapi 0 di "Kartu Stok" untuk Maret 2026.

## Root Cause Analysis
1. **Backend API sudah benar** - API `/api/inventory/stock-card-modal` mengembalikan data yang benar (stok 18)
2. **Masalah adalah UX/Logic di Frontend** - Default behavior tidak jelas apakah menampilkan "stok saat ini" atau "stok berdasarkan periode"

## Fix Applied

### 1. StockCardModal.jsx - Mode Toggle "Semua Periode" vs "Berdasarkan Periode"
- Ditambahkan state `viewMode` dengan opsi 'all' (Semua Periode) dan 'period' (Berdasarkan Periode)
- Default mode = 'all' yang menampilkan SEMUA transaksi = STOK SAAT INI
- Mode 'period' hanya aktif ketika user memilih tanggal tertentu
- UI toggle button yang jelas dengan warna hijau (Semua Periode) vs amber (Berdasarkan Periode)

### 2. Date Filter Logic Fix
- Sebelum: date filter selalu dikirim ke API meskipun kosong
- Sesudah: date filter HANYA dikirim jika `viewMode === 'period'` DAN tanggal diisi
- Ini memastikan default view selalu menampilkan stok saat ini (semua periode)

### 3. UX Label Updates
- Header kolom di MasterItems.jsx: "STOK" → "STOK SAAT INI" dengan tooltip
- Summary card di StockCardModal: "Saldo Akhir" → "STOK SAAT INI" (mode all) atau "Saldo Periode" (mode period)
- Warna visual: Hijau untuk stok saat ini, Amber untuk stok berdasarkan periode
- Info text yang jelas di footer menunjukkan mode yang sedang aktif

### 4. Files Modified
- `/app/frontend/src/components/StockCardModal.jsx`
  - Line 3: Added Clock, History icons
  - Line 24: Added viewMode state
  - Line 32-44: Modified loadStockMovements to only send date filter in 'period' mode  
  - Line 180-260: New mode toggle UI with clear labels
  - Line 262-290: Updated summary cards with mode-aware labels and colors
  - Line 355-365: Updated footer with mode indicator

- `/app/frontend/src/pages/master/MasterItems.jsx`
  - Line 749: Updated column header from "STOK" to "STOK SAAT INI" with tooltip

## Verification

### API Test Results
```
=== TEST 1: Semua Periode (Stok Saat Ini) ===
Total In: 18
Total Out: 0
Balance (STOK SAAT INI): 18
Total Movements: 1

=== TEST 2: Berdasarkan Periode (Mar 2026) ===
Total In: 18
Total Out: 0
Balance (Periode Mar 2026): 18
Total Movements: 1

=== TEST 3: Item 001000 - Periode Jan 2025 (seharusnya 0) ===
Total In: 0
Total Out: 0
Balance (Periode): 0
Total Movements: 0
```

### Expected UX Flow
1. User buka Kartu Stok → Default mode "Semua Periode" → Tampil STOK SAAT INI (18)
2. User pilih "Berdasarkan Periode" → Filter tanggal aktif → Tampil stok sesuai periode
3. User klik "Semua Periode" lagi → Reset filter → Kembali ke STOK SAAT INI

## Status: ✅ DONE
- Backend: VERIFIED via curl
- Frontend: MODIFIED (await user validation via UI)
- UX Labels: UPDATED untuk membedakan "Stok Saat Ini" vs "Berdasarkan Periode"

## Evidence
- `/app/test_reports/STOCK_CARD_UX_FIX_REPORT.md` (this file)
- API verification via bash
