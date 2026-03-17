# Menu Duplicate Audit Report

## Date: 2026-03-17
## Tenant: ocb_titan
## Blueprint: v2.4.3

---

## TEMUAN: DUPLICATE MODULE CONFIRMED ✓

### Analisis Menu Sidebar

| Menu | Path | Component | API Endpoint |
|------|------|-----------|--------------|
| Pesanan Pembelian > Daftar Pesanan | /purchase/orders | PurchaseOrders | GET /api/purchase/orders |
| Pesanan Pembelian > Tambah Pesanan Pembelian | /purchase/orders/add | **PurchaseEnterprise** | POST /api/purchase/orders |
| Daftar Pembelian > Daftar Pembelian | /purchase/list | PurchaseList | GET /api/purchase/orders |
| Daftar Pembelian > Tambah Pembelian | /purchase/add | **PurchaseEnterprise** | POST /api/purchase/orders |

### Bukti Duplikasi

1. **Component Sama**: 
   - `Tambah Pesanan Pembelian` dan `Tambah Pembelian` KEDUANYA menggunakan `PurchaseEnterprise.jsx`
   
2. **API Endpoint Sama**:
   - KEDUANYA memanggil `POST /api/purchase/orders`
   - Tidak ada endpoint terpisah untuk "Pembelian Langsung"

3. **List Component Berbeda Tapi Query Sama**:
   - `PurchaseOrders.jsx` memanggil `/api/purchase/orders`
   - `PurchaseList.jsx` memanggil `/api/purchase/orders`
   - HASIL QUERY IDENTIK

---

## KESIMPULAN

**STATUS: DUPLICATE MODULE**

- Menu "Pesanan Pembelian" dan "Daftar Pembelian" adalah **DUPLIKAT FUNGSIONAL**
- Keduanya mengarah ke modul dan endpoint yang sama
- Tidak ada perbedaan flow, logic, atau hasil antara keduanya
- User dapat bingung dan melakukan input duplikat

---

## REKOMENDASI KONSOLIDASI

### Opsi 1: Pertahankan Satu Menu Saja
- Hapus salah satu menu (disarankan hapus "Daftar Pembelian")
- Rename "Pesanan Pembelian" menjadi "Pembelian"

### Opsi 2: Buat Modul Terpisah (jika memang dibutuhkan)
Jika bisnis memerlukan dua workflow berbeda:
- **Purchase Order (PO)**: Order → Submit → Receive → Receive → Complete
- **Direct Purchase**: Create → Post → Langsung masuk stok + journal

Maka perlu:
- Buat endpoint baru `POST /api/purchase/direct`
- Buat component baru `DirectPurchase.jsx`
- Direct purchase langsung update stok dan create journal tanpa receiving

---

## ACTION ITEMS

1. [ ] Diskusi dengan stakeholder untuk menentukan kebutuhan bisnis sebenarnya
2. [ ] Jika hanya perlu satu flow: Konsolidasi menu dan hapus duplikat
3. [ ] Jika perlu dua flow: Implementasi modul Direct Purchase terpisah
4. [ ] Update documentation

