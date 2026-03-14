# AP Payment Module - Actions Test Report

## Test Date: 2026-03-14

## Overview
Pengujian modul pembayaran hutang (Accounts Payable) sesuai dengan requirement P0.

## Tested Features

### 1. Dropdown Bank/Kas ✅ FIXED
- **Sebelum:** Dropdown kosong, menampilkan "Tidak ditemukan"
- **Sesudah:** Dropdown menampilkan 9 akun Kas/Bank aktif
- **Akun yang tersedia:**
  - 1-1001 - Kas (cash)
  - 1-1002 - Bank BCA (bank)
  - 1-1003 - Bank BRI (bank)
  - 1101 - Kas (cash)
  - 1102 - Bank (bank)
  - 1103 - Kas Kecil Pusat (cash)
  - 1104 - Kas Cabang (cash)
  - 1105 - Kas Kasir (cash)
  - 1106 - Kas Dalam Perjalanan (cash)

### 2. Tombol Aksi di Daftar Hutang ✅ IMPLEMENTED
| Tombol | Status | Kondisi Tampil |
|--------|--------|----------------|
| Tambah | ✅ | Selalu |
| Detail (Eye) | ✅ | Selalu |
| Edit | ✅ | Hanya jika belum ada pembayaran |
| Bayar | ✅ | Hanya jika status != paid |
| Cetak | ✅ | Selalu |
| Hapus (soft) | ✅ | Hanya jika belum ada pembayaran |
| Export CSV | ✅ | Selalu |

### 3. Pembayaran Hutang ✅ TESTED
- Endpoint: POST /api/ap/{ap_id}/payment
- Hasil test:
  - Payment No: PAY-20260314-0002
  - Journal No: JV-20260314-0005
  - New Outstanding: 5,400,000 (berkurang 100,000)
- Jurnal otomatis:
  - Dr. Hutang Dagang (2-1100): Rp 100,000
  - Cr. Bank (1-1200): Rp 100,000
  - Balanced: TRUE
  - Status: POSTED

### 4. Soft Delete ✅ IMPLEMENTED
- Endpoint: PUT /api/ap/{ap_id}/soft-delete
- Validasi:
  - Tidak bisa hapus jika sudah ada pembayaran
  - Tidak bisa hapus jika status = paid
  - Tidak bisa hapus jika sudah ada jurnal terkait

### 5. Cetak ✅ IMPLEMENTED
- Format: HTML dengan print dialog
- Informasi yang ditampilkan:
  - No. Hutang, Tanggal, Jatuh Tempo
  - Supplier, Invoice
  - Total, Terbayar, Outstanding
  - Area tanda tangan

## Evidence Files
- cash_bank_ledger_test.json - Response API accounts cash-bank
- ap_payment_journal_test.json - Response API pembayaran
- bank_kas_dropdown_test.png - Screenshot modal dengan dropdown

## Compliance Check
- [x] Tenant-aware
- [x] Hanya akun aktif
- [x] Filter CASH/BANK type
- [x] Prioritas berdasar metode pembayaran
- [x] Audit trail (log_activity)
- [x] Journal balanced
- [x] Soft delete only

## Status: PASSED ✅
