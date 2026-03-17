# Purchase vs Purchase Order - Perbandingan Nyata

## Date: 2026-03-17
## Tested on: ocb_titan

---

## TABEL PERBANDINGAN

| Aspek | Tambah Pesanan Pembelian | Tambah Pembelian |
|-------|--------------------------|-------------------|
| **Menu Path** | Pesanan Pembelian > Tambah | Daftar Pembelian > Tambah |
| **Route** | /purchase/orders/add | /purchase/add |
| **Component** | PurchaseEnterprise.jsx | PurchaseEnterprise.jsx |
| **API Create** | POST /api/purchase/orders | POST /api/purchase/orders |
| **API List** | GET /api/purchase/orders | GET /api/purchase/orders |
| **Payload** | IDENTIK | IDENTIK |
| **Status Awal** | draft | draft |
| **Status Setelah Submit** | ordered | ordered |
| **Stock Movement Saat Create** | TIDAK | TIDAK |
| **Stock Movement Saat Submit** | TIDAK | TIDAK |
| **Stock Movement Saat Receive** | YA | YA |
| **Journal Saat Create** | TIDAK | TIDAK |
| **Journal Saat Submit** | TIDAK | TIDAK |
| **AP Saat Full Receive** | YA | YA |
| **Receiving Dependency** | YA, wajib lewat receive | YA, wajib lewat receive |

---

## HASIL UJI NYATA

### Test 1: Tambah Pesanan Pembelian (via /purchase/orders/add)
```
1. Create PO: POST /api/purchase/orders
   - Response: {id: "xxx", po_number: "PO000030"}
   - Status: draft
   - Stock: TIDAK BERUBAH

2. Submit PO: POST /api/purchase/orders/{id}/submit
   - Status: ordered
   - Stock: TIDAK BERUBAH
   - Journal: TIDAK TERBENTUK

3. Partial Receive (3/10): POST /api/purchase/orders/{id}/receive
   - Status: partial
   - received_qty: 3
   - Stock Movement: +3 (stock_in)

4. Final Receive (7/10): POST /api/purchase/orders/{id}/receive
   - Status: received
   - received_qty: 10
   - Stock Movement: +7 (stock_in)
   - AP Created: YA
```

### Test 2: Tambah Pembelian (via /purchase/add)
- IDENTIK dengan Test 1
- Menggunakan component dan endpoint yang sama
- Flow dan hasil sama persis

---

## KESIMPULAN

**KEPUTUSAN: DUPLICATE MODULE**

Dua menu ini adalah **DUPLIKAT FUNGSIONAL**:
- Sama component: `PurchaseEnterprise.jsx`
- Sama endpoint: `POST /api/purchase/orders`
- Sama flow: create → submit → receive
- Sama hasil: stok berubah hanya saat receiving

**Tidak ada "Pembelian Langsung" yang terpisah dari PO flow.**

---

## REKOMENDASI

Konsolidasi diperlukan untuk menghindari:
1. Kebingungan user
2. Duplicate data entry
3. Maintenance burden
4. Inconsistent UX

