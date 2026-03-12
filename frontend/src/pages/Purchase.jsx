import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Plus, Search, Edit2, Trash2, Truck, X, Save, Loader2, Check, Package, FileText, Printer, Eye, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';

const Purchase = () => {
  const { api, user } = useAuth();
  const [orders, setOrders] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [showReceiveModal, setShowReceiveModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [saving, setSaving] = useState(false);
  const [statusFilter, setStatusFilter] = useState('');
  const [form, setForm] = useState({ supplier_id: '', expected_date: '', notes: '', items: [] });
  const [editForm, setEditForm] = useState(null);
  const [receiveItems, setReceiveItems] = useState([]);
  const printRef = useRef(null);

  const formatRupiah = (num) => `Rp ${(num || 0).toLocaleString('id-ID')}`;

  useEffect(() => { loadOrders(); loadSuppliers(); loadProducts(); }, [statusFilter]);

  const loadOrders = async () => {
    setLoading(true);
    try {
      let url = `/api/purchase/orders?limit=100`;
      if (statusFilter) url += `&status=${statusFilter}`;
      const res = await api(url);
      if (res.ok) { const data = await res.json(); setOrders(data.items || []); }
    } catch (err) { toast.error('Gagal memuat data pembelian'); }
    finally { setLoading(false); }
  };

  const loadSuppliers = async () => {
    try {
      const res = await api('/api/suppliers');
      if (res.ok) { const data = await res.json(); setSuppliers(data.items || []); }
    } catch (err) { console.error(err); }
  };

  const loadProducts = async () => {
    try {
      const res = await api('/api/products?limit=500');
      if (res.ok) { const data = await res.json(); setProducts(data.items || []); }
    } catch (err) { console.error(err); }
  };

  const openModal = () => {
    setForm({ supplier_id: '', expected_date: '', notes: '', items: [] });
    setShowModal(true);
  };

  const addItem = (product) => {
    const exists = form.items.find(i => i.product_id === product.id);
    if (exists) {
      setForm({
        ...form,
        items: form.items.map(i => i.product_id === product.id ? { ...i, quantity: i.quantity + 1 } : i)
      });
    } else {
      setForm({
        ...form,
        items: [...form.items, {
          product_id: product.id,
          product_code: product.code,
          product_name: product.name,
          unit: product.unit || 'PCS',
          quantity: 1,
          unit_cost: product.cost_price || 0,
          discount_percent: 0
        }]
      });
    }
  };

  const updateItem = (index, field, value) => {
    const newItems = [...form.items];
    newItems[index][field] = field === 'quantity' || field === 'unit_cost' || field === 'discount_percent' ? Number(value) : value;
    setForm({ ...form, items: newItems });
  };

  const removeItem = (index) => {
    setForm({ ...form, items: form.items.filter((_, i) => i !== index) });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (form.items.length === 0) { toast.error('Tambahkan minimal 1 item'); return; }
    
    setSaving(true);
    try {
      const res = await api('/api/purchase/orders', { method: 'POST', body: JSON.stringify(form) });
      if (res.ok) { toast.success('Purchase Order berhasil dibuat'); setShowModal(false); loadOrders(); }
      else { const err = await res.json(); toast.error(err.detail || 'Gagal membuat PO'); }
    } catch (err) { toast.error('Gagal membuat PO'); }
    finally { setSaving(false); }
  };

  const submitOrder = async (orderId) => {
    try {
      const res = await api(`/api/purchase/orders/${orderId}/submit`, { method: 'POST' });
      if (res.ok) { 
        toast.success('PO dikirim ke supplier'); 
        loadOrders(); 
      } else {
        const err = await res.json();
        if (err.detail?.errors) {
          toast.error(
            <div>
              <p className="font-semibold mb-1">{err.detail.message}</p>
              <ul className="text-sm list-disc pl-4">
                {err.detail.errors.map((e, i) => <li key={i}>{e}</li>)}
              </ul>
            </div>
          );
        } else {
          toast.error(err.detail?.message || err.detail || 'Gagal mengirim PO');
        }
      }
    } catch (err) { toast.error('Gagal mengirim PO'); }
  };

  const openReceiveModal = (order) => {
    setSelectedOrder(order);
    setReceiveItems(order.items.map(item => ({
      product_id: item.product_id,
      product_name: item.product_name,
      ordered_qty: item.quantity,
      received_qty: item.received_qty || 0,
      quantity: 0
    })));
    setShowReceiveModal(true);
  };

  const handleReceive = async () => {
    const itemsToReceive = receiveItems.filter(item => item.quantity > 0);
    if (itemsToReceive.length === 0) { toast.error('Masukkan jumlah barang yang diterima'); return; }
    
    try {
      const res = await api(`/api/purchase/orders/${selectedOrder.id}/receive`, {
        method: 'POST',
        body: JSON.stringify({ items: itemsToReceive, notes: '' })
      });
      if (res.ok) { 
        toast.success('Barang diterima'); 
        setShowReceiveModal(false); 
        loadOrders(); 
      }
    } catch (err) { toast.error('Gagal menerima barang'); }
  };

  const cancelOrder = async (orderId) => {
    if (!window.confirm('Batalkan PO ini?')) return;
    try {
      const res = await api(`/api/purchase/orders/${orderId}/cancel`, { method: 'POST' });
      if (res.ok) { toast.success('PO dibatalkan'); loadOrders(); }
    } catch (err) { toast.error('Gagal membatalkan'); }
  };

  // EDIT DRAFT PO
  const openEditModal = async (order) => {
    setSelectedOrder(order);
    setEditForm({
      supplier_id: order.supplier_id || '',
      expected_date: order.expected_date || '',
      notes: order.notes || '',
      discount_amount: order.discount_amount || 0,
      tax_percent: order.tax_percent || 0,
      items: order.items.map(i => ({
        product_id: i.product_id,
        product_code: i.product_code || '',
        product_name: i.product_name || '',
        unit: i.unit || 'PCS',
        quantity: i.quantity || 0,
        unit_cost: i.unit_cost || 0,
        discount_percent: i.discount_percent || 0
      }))
    });
    setShowEditModal(true);
  };

  const updateEditItem = (index, field, value) => {
    const newItems = [...editForm.items];
    newItems[index][field] = field === 'quantity' || field === 'unit_cost' || field === 'discount_percent' ? Number(value) : value;
    setEditForm({ ...editForm, items: newItems });
  };

  const handleEditSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const res = await api(`/api/purchase/orders/${selectedOrder.id}`, { 
        method: 'PUT', 
        body: JSON.stringify(editForm) 
      });
      if (res.ok) { 
        toast.success('PO draft berhasil diupdate'); 
        setShowEditModal(false); 
        loadOrders(); 
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Gagal update PO');
      }
    } catch (err) { toast.error('Gagal update PO'); }
    finally { setSaving(false); }
  };

  // DETAIL & PRINT
  const openDetailModal = async (order) => {
    try {
      const res = await api(`/api/purchase/orders/${order.id}/print`);
      if (res.ok) {
        const data = await res.json();
        setSelectedOrder(data);
        setShowDetailModal(true);
      }
    } catch (err) {
      toast.error('Gagal memuat detail PO');
    }
  };

  const handlePrint = () => {
    if (!selectedOrder) return;
    
    const printWindow = window.open('', '_blank');
    if (!printWindow) {
      toast.error('Popup blocker aktif. Izinkan popup untuk cetak.');
      return;
    }

    const formatDate = (dateStr) => {
      if (!dateStr) return '-';
      return new Date(dateStr).toLocaleDateString('id-ID', { day: '2-digit', month: 'long', year: 'numeric' });
    };

    printWindow.document.write(`
      <!DOCTYPE html>
      <html>
      <head>
        <title>Purchase Order - ${selectedOrder.po_number}</title>
        <style>
          * { margin: 0; padding: 0; box-sizing: border-box; }
          body { font-family: Arial, sans-serif; font-size: 12px; padding: 20px; }
          .header { text-align: center; margin-bottom: 20px; border-bottom: 2px solid #000; padding-bottom: 10px; }
          .header h1 { font-size: 18px; margin-bottom: 5px; }
          .header h2 { font-size: 14px; color: #666; }
          .info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
          .info-box h3 { font-size: 12px; color: #666; margin-bottom: 5px; border-bottom: 1px solid #ccc; padding-bottom: 3px; }
          .info-box p { margin: 3px 0; }
          table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
          th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }
          th { background: #f5f5f5; font-weight: bold; }
          .text-right { text-align: right; }
          .text-center { text-align: center; }
          .total-row { font-weight: bold; background: #f5f5f5; }
          .footer { margin-top: 30px; display: grid; grid-template-columns: 1fr 1fr 1fr; text-align: center; }
          .footer-box { padding: 10px; }
          .footer-box .title { font-size: 11px; color: #666; }
          .footer-box .sign-area { height: 60px; border-bottom: 1px solid #000; margin: 10px 30px; }
          .notes { margin-top: 15px; padding: 10px; background: #f9f9f9; border: 1px solid #ddd; }
          @media print { body { padding: 10px; } }
        </style>
      </head>
      <body>
        <div class="header">
          <h1>PURCHASE ORDER</h1>
          <h2>${selectedOrder.po_number}</h2>
        </div>
        
        <div class="info-grid">
          <div class="info-box">
            <h3>SUPPLIER</h3>
            <p><strong>${selectedOrder.supplier?.name || '-'}</strong></p>
            <p>${selectedOrder.supplier?.address || ''}</p>
            <p>Telp: ${selectedOrder.supplier?.phone || '-'}</p>
            <p>Email: ${selectedOrder.supplier?.email || '-'}</p>
          </div>
          <div class="info-box">
            <h3>INFO PO</h3>
            <p>Tanggal: ${formatDate(selectedOrder.created_at)}</p>
            <p>Status: ${selectedOrder.status}</p>
            <p>Tanggal Kirim: ${formatDate(selectedOrder.expected_date)}</p>
            <p>Cabang: ${selectedOrder.branch?.name || '-'}</p>
          </div>
        </div>

        <table>
          <thead>
            <tr>
              <th class="text-center" style="width:40px">No</th>
              <th>Kode</th>
              <th>Nama Barang</th>
              <th class="text-center">Satuan</th>
              <th class="text-right">Qty</th>
              <th class="text-right">Harga</th>
              <th class="text-right">Disc %</th>
              <th class="text-right">Subtotal</th>
            </tr>
          </thead>
          <tbody>
            ${selectedOrder.items.map((item, idx) => `
              <tr>
                <td class="text-center">${idx + 1}</td>
                <td>${item.product_code}</td>
                <td>${item.product_name}</td>
                <td class="text-center">${item.unit}</td>
                <td class="text-right">${item.quantity}</td>
                <td class="text-right">${formatRupiah(item.unit_cost)}</td>
                <td class="text-right">${item.discount_percent || 0}%</td>
                <td class="text-right">${formatRupiah(item.subtotal)}</td>
              </tr>
            `).join('')}
            <tr class="total-row">
              <td colspan="7" class="text-right">Subtotal</td>
              <td class="text-right">${formatRupiah(selectedOrder.subtotal)}</td>
            </tr>
            ${selectedOrder.discount_amount > 0 ? `
              <tr>
                <td colspan="7" class="text-right">Diskon</td>
                <td class="text-right">-${formatRupiah(selectedOrder.discount_amount)}</td>
              </tr>
            ` : ''}
            ${selectedOrder.tax_amount > 0 ? `
              <tr>
                <td colspan="7" class="text-right">PPN (${selectedOrder.tax_percent}%)</td>
                <td class="text-right">${formatRupiah(selectedOrder.tax_amount)}</td>
              </tr>
            ` : ''}
            <tr class="total-row">
              <td colspan="7" class="text-right">TOTAL</td>
              <td class="text-right">${formatRupiah(selectedOrder.total)}</td>
            </tr>
          </tbody>
        </table>

        ${selectedOrder.notes ? `
          <div class="notes">
            <strong>Catatan:</strong><br/>
            ${selectedOrder.notes}
          </div>
        ` : ''}

        <div class="footer">
          <div class="footer-box">
            <div class="title">Dibuat oleh</div>
            <div class="sign-area"></div>
            <div>${selectedOrder.created_by_name || '-'}</div>
          </div>
          <div class="footer-box">
            <div class="title">Disetujui oleh</div>
            <div class="sign-area"></div>
            <div>________________</div>
          </div>
          <div class="footer-box">
            <div class="title">Diterima oleh</div>
            <div class="sign-area"></div>
            <div>________________</div>
          </div>
        </div>
      </body>
      </html>
    `);
    
    printWindow.document.close();
    setTimeout(() => {
      printWindow.print();
    }, 500);
  };

  const statusLabels = {
    draft: 'Draft', ordered: 'Dipesan', partial: 'Sebagian', received: 'Diterima', cancelled: 'Dibatalkan'
  };

  const statusColors = {
    draft: 'bg-gray-900/30 text-gray-400',
    ordered: 'bg-blue-900/30 text-blue-400',
    partial: 'bg-amber-900/30 text-amber-400',
    received: 'bg-green-900/30 text-green-400',
    cancelled: 'bg-red-900/30 text-red-400'
  };

  const totalForm = form.items.reduce((sum, item) => {
    const subtotal = item.quantity * item.unit_cost;
    const discount = subtotal * (item.discount_percent / 100);
    return sum + subtotal - discount;
  }, 0);

  const editTotalForm = editForm?.items.reduce((sum, item) => {
    const subtotal = item.quantity * item.unit_cost;
    const discount = subtotal * (item.discount_percent / 100);
    return sum + subtotal - discount;
  }, 0) || 0;

  return (
    <div className="space-y-6" data-testid="purchase-page">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Pembelian</h1>
          <p className="text-gray-400">Kelola purchase order dan penerimaan barang</p>
        </div>
        <button onClick={openModal} className="px-4 py-2 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg flex items-center gap-2" data-testid="add-po-btn">
          <Plus className="h-5 w-5" /> Buat PO
        </button>
      </div>

      <div className="flex gap-4">
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="px-4 py-2 bg-[#1a1214] border border-red-900/30 rounded-lg">
          <option value="">Semua Status</option>
          <option value="draft">Draft</option>
          <option value="ordered">Dipesan</option>
          <option value="partial">Sebagian Diterima</option>
          <option value="received">Diterima</option>
          <option value="cancelled">Dibatalkan</option>
        </select>
      </div>

      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
        <table className="w-full">
          <thead className="bg-red-900/20">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-semibold">No. PO</th>
              <th className="px-4 py-3 text-left text-sm font-semibold">Supplier</th>
              <th className="px-4 py-3 text-center text-sm font-semibold">Item</th>
              <th className="px-4 py-3 text-right text-sm font-semibold">Total</th>
              <th className="px-4 py-3 text-center text-sm font-semibold">Status</th>
              <th className="px-4 py-3 text-center text-sm font-semibold">Aksi</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={6} className="px-4 py-8 text-center"><Loader2 className="h-8 w-8 animate-spin mx-auto text-red-400" /></td></tr>
            ) : orders.length === 0 ? (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-400"><FileText className="h-12 w-12 mx-auto mb-2 opacity-30" />Tidak ada purchase order</td></tr>
            ) : (
              orders.map(order => (
                <tr key={order.id} className="border-t border-red-900/10 hover:bg-red-900/10">
                  <td className="px-4 py-3">
                    <div className="font-medium">{order.po_number || order.po_no}</div>
                    <div className="text-sm text-gray-400">{new Date(order.created_at).toLocaleDateString('id-ID')}</div>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`${order.supplier_name === 'Unknown' || !order.supplier_name ? 'text-red-400' : 'text-gray-300'}`}>
                      {order.supplier_name || '(Perlu dipilih)'}
                    </span>
                    {order.needs_completion && (
                      <div className="flex items-center gap-1 text-amber-400 text-xs mt-1">
                        <AlertCircle className="h-3 w-3" /> Perlu dilengkapi
                      </div>
                    )}
                  </td>
                  <td className="px-4 py-3 text-center">{order.items?.length || 0}</td>
                  <td className="px-4 py-3 text-right">
                    <span className={`font-semibold ${order.total > 0 ? 'text-amber-400' : 'text-red-400'}`}>
                      {formatRupiah(order.total)}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className={`px-2 py-1 rounded text-xs font-semibold ${statusColors[order.status]}`}>
                      {statusLabels[order.status] || order.status}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex justify-center gap-1">
                      {/* Detail & Print */}
                      <button onClick={() => openDetailModal(order)} className="p-1.5 text-blue-400 hover:bg-blue-600/20 rounded" title="Lihat Detail">
                        <Eye className="h-4 w-4" />
                      </button>
                      
                      {order.status === 'draft' && (
                        <>
                          <button onClick={() => openEditModal(order)} className="p-1.5 text-amber-400 hover:bg-amber-600/20 rounded" title="Edit">
                            <Edit2 className="h-4 w-4" />
                          </button>
                          <button onClick={() => submitOrder(order.id)} className="px-2 py-1 text-xs bg-blue-600/20 text-blue-400 rounded hover:bg-blue-600/30">Kirim</button>
                          <button onClick={() => cancelOrder(order.id)} className="p-1.5 text-red-400 hover:bg-red-600/20 rounded" title="Batal">
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </>
                      )}
                      {(order.status === 'ordered' || order.status === 'partial') && (
                        <button onClick={() => openReceiveModal(order)} className="px-2 py-1 text-xs bg-green-600/20 text-green-400 rounded hover:bg-green-600/30 flex items-center gap-1">
                          <Package className="h-3 w-3" /> Terima
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Modal Buat PO */}
      {showModal && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-red-900/30 flex justify-between items-center sticky top-0 bg-[#1a1214]">
              <h2 className="text-xl font-bold">Buat Purchase Order</h2>
              <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-white"><X className="h-6 w-6" /></button>
            </div>
            
            <form onSubmit={handleSubmit} className="p-6 space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Supplier *</label>
                  <select value={form.supplier_id} onChange={(e) => setForm({ ...form, supplier_id: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" required>
                    <option value="">Pilih Supplier</option>
                    {suppliers.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Tanggal Diharapkan</label>
                  <input type="date" value={form.expected_date} onChange={(e) => setForm({ ...form, expected_date: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" />
                </div>
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-2">Pilih Produk</label>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2 max-h-40 overflow-y-auto p-2 bg-[#0a0608] rounded-lg">
                  {products.map(product => (
                    <button type="button" key={product.id} onClick={() => addItem(product)} className="p-2 text-left text-sm bg-[#1a1214] rounded hover:bg-red-900/20 border border-red-900/20">
                      <div className="font-medium truncate">{product.name}</div>
                      <div className="text-xs text-gray-400">{product.code} - {formatRupiah(product.cost_price)}</div>
                    </button>
                  ))}
                </div>
              </div>

              {form.items.length > 0 && (
                <div>
                  <label className="block text-sm text-gray-400 mb-2">Daftar Item ({form.items.length})</label>
                  <div className="space-y-2">
                    {form.items.map((item, idx) => (
                      <div key={idx} className="flex items-center gap-2 p-3 bg-[#0a0608] rounded-lg">
                        <div className="flex-1">
                          <div className="font-medium text-sm">{item.product_name}</div>
                          <div className="text-xs text-gray-400">{item.product_code}</div>
                        </div>
                        <input type="number" min="1" value={item.quantity} onChange={(e) => updateItem(idx, 'quantity', e.target.value)} className="w-20 px-2 py-1 bg-[#1a1214] border border-red-900/30 rounded text-center" />
                        <span className="text-xs text-gray-400">×</span>
                        <input type="number" min="0" value={item.unit_cost} onChange={(e) => updateItem(idx, 'unit_cost', e.target.value)} className="w-28 px-2 py-1 bg-[#1a1214] border border-red-900/30 rounded text-right" />
                        <span className="text-amber-400 font-semibold w-32 text-right">{formatRupiah(item.quantity * item.unit_cost)}</span>
                        <button type="button" onClick={() => removeItem(idx)} className="p-1 text-red-400 hover:bg-red-900/20 rounded"><X className="h-4 w-4" /></button>
                      </div>
                    ))}
                  </div>
                  <div className="mt-4 p-3 bg-amber-900/20 rounded-lg flex justify-between items-center">
                    <span className="font-semibold">Total</span>
                    <span className="text-2xl font-bold text-amber-400">{formatRupiah(totalForm)}</span>
                  </div>
                </div>
              )}

              <div>
                <label className="block text-sm text-gray-400 mb-1">Catatan</label>
                <textarea value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" rows={2} />
              </div>

              <div className="flex justify-end gap-3">
                <button type="button" onClick={() => setShowModal(false)} className="px-4 py-2 border border-red-900/30 rounded-lg">Batal</button>
                <button type="submit" disabled={saving} className="px-4 py-2 bg-gradient-to-r from-red-600 to-amber-600 rounded-lg flex items-center gap-2">
                  {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />} Simpan Draft
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal Edit Draft PO */}
      {showEditModal && editForm && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-red-900/30 flex justify-between items-center sticky top-0 bg-[#1a1214]">
              <h2 className="text-xl font-bold">Edit Draft PO - {selectedOrder?.po_number || selectedOrder?.po_no}</h2>
              <button onClick={() => setShowEditModal(false)} className="text-gray-400 hover:text-white"><X className="h-6 w-6" /></button>
            </div>
            
            <form onSubmit={handleEditSubmit} className="p-6 space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Supplier *</label>
                  <select value={editForm.supplier_id} onChange={(e) => setEditForm({ ...editForm, supplier_id: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" required>
                    <option value="">Pilih Supplier</option>
                    {suppliers.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Tanggal Diharapkan</label>
                  <input type="date" value={editForm.expected_date} onChange={(e) => setEditForm({ ...editForm, expected_date: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" />
                </div>
              </div>

              <div>
                <label className="block text-sm text-amber-200 font-semibold mb-2">Daftar Item</label>
                <div className="bg-[#0a0608] rounded-lg overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-red-900/20">
                      <tr>
                        <th className="px-3 py-2 text-left">Produk</th>
                        <th className="px-3 py-2 text-center w-24">Qty</th>
                        <th className="px-3 py-2 text-right w-32">Harga</th>
                        <th className="px-3 py-2 text-right w-24">Disc %</th>
                        <th className="px-3 py-2 text-right w-32">Subtotal</th>
                      </tr>
                    </thead>
                    <tbody>
                      {editForm.items.map((item, idx) => {
                        const subtotal = item.quantity * item.unit_cost * (1 - item.discount_percent / 100);
                        return (
                          <tr key={idx} className="border-t border-red-900/20">
                            <td className="px-3 py-2">
                              <div>{item.product_name}</div>
                              <div className="text-xs text-gray-500">{item.product_code}</div>
                            </td>
                            <td className="px-3 py-2">
                              <input type="number" min="1" value={item.quantity} onChange={(e) => updateEditItem(idx, 'quantity', e.target.value)} 
                                className="w-full px-2 py-1 bg-[#1a1214] border border-red-900/30 rounded text-center" />
                            </td>
                            <td className="px-3 py-2">
                              <input type="number" min="0" value={item.unit_cost} onChange={(e) => updateEditItem(idx, 'unit_cost', e.target.value)} 
                                className={`w-full px-2 py-1 bg-[#1a1214] border rounded text-right ${item.unit_cost <= 0 ? 'border-red-500' : 'border-red-900/30'}`} />
                            </td>
                            <td className="px-3 py-2">
                              <input type="number" min="0" max="100" value={item.discount_percent} onChange={(e) => updateEditItem(idx, 'discount_percent', e.target.value)} 
                                className="w-full px-2 py-1 bg-[#1a1214] border border-red-900/30 rounded text-center" />
                            </td>
                            <td className="px-3 py-2 text-right text-amber-400 font-semibold">{formatRupiah(subtotal)}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="p-4 bg-amber-900/20 rounded-lg">
                <div className="flex justify-between items-center text-lg">
                  <span className="font-semibold">Total</span>
                  <span className={`text-2xl font-bold ${editTotalForm > 0 ? 'text-amber-400' : 'text-red-400'}`}>
                    {formatRupiah(editTotalForm)}
                  </span>
                </div>
                {editTotalForm <= 0 && (
                  <p className="text-red-400 text-sm mt-2 flex items-center gap-1">
                    <AlertCircle className="h-4 w-4" /> Total harus lebih dari 0. Isi harga untuk semua item.
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-1">Catatan</label>
                <textarea value={editForm.notes} onChange={(e) => setEditForm({ ...editForm, notes: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" rows={2} />
              </div>

              <div className="flex justify-end gap-3">
                <button type="button" onClick={() => setShowEditModal(false)} className="px-4 py-2 border border-red-900/30 rounded-lg">Batal</button>
                <button type="submit" disabled={saving} className="px-4 py-2 bg-gradient-to-r from-red-600 to-amber-600 rounded-lg flex items-center gap-2">
                  {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />} Simpan Perubahan
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal Detail & Print */}
      {showDetailModal && selectedOrder && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-red-900/30 flex justify-between items-center sticky top-0 bg-[#1a1214]">
              <h2 className="text-xl font-bold">Detail PO - {selectedOrder.po_number}</h2>
              <div className="flex items-center gap-2">
                <Button onClick={handlePrint} className="bg-blue-600 hover:bg-blue-700">
                  <Printer className="h-4 w-4 mr-2" /> Print
                </Button>
                <button onClick={() => setShowDetailModal(false)} className="text-gray-400 hover:text-white"><X className="h-6 w-6" /></button>
              </div>
            </div>
            
            <div className="p-6 space-y-6" ref={printRef}>
              {/* Info Grid */}
              <div className="grid grid-cols-2 gap-6">
                <div className="bg-[#0a0608] rounded-lg p-4">
                  <h3 className="text-amber-200 font-semibold mb-3 border-b border-red-900/30 pb-2">Supplier</h3>
                  <p className="font-semibold text-lg">{selectedOrder.supplier?.name || '-'}</p>
                  <p className="text-gray-400 text-sm">{selectedOrder.supplier?.address || ''}</p>
                  <p className="text-gray-400 text-sm">Telp: {selectedOrder.supplier?.phone || '-'}</p>
                </div>
                <div className="bg-[#0a0608] rounded-lg p-4">
                  <h3 className="text-amber-200 font-semibold mb-3 border-b border-red-900/30 pb-2">Info PO</h3>
                  <p><span className="text-gray-400">Status:</span> <span className={`px-2 py-0.5 rounded text-xs ${statusColors[selectedOrder.status]}`}>{statusLabels[selectedOrder.status]}</span></p>
                  <p className="text-gray-400 text-sm mt-1">Tanggal: {new Date(selectedOrder.created_at).toLocaleDateString('id-ID')}</p>
                  <p className="text-gray-400 text-sm">Cabang: {selectedOrder.branch?.name || '-'}</p>
                </div>
              </div>

              {/* Items Table */}
              <div className="bg-[#0a0608] rounded-lg overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-red-900/20">
                    <tr>
                      <th className="px-4 py-3 text-left">No</th>
                      <th className="px-4 py-3 text-left">Produk</th>
                      <th className="px-4 py-3 text-center">Qty</th>
                      <th className="px-4 py-3 text-right">Harga</th>
                      <th className="px-4 py-3 text-right">Subtotal</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selectedOrder.items?.map((item, idx) => (
                      <tr key={idx} className="border-t border-red-900/20">
                        <td className="px-4 py-3">{idx + 1}</td>
                        <td className="px-4 py-3">
                          <div>{item.product_name}</div>
                          <div className="text-xs text-gray-500">{item.product_code}</div>
                        </td>
                        <td className="px-4 py-3 text-center">{item.quantity} {item.unit}</td>
                        <td className="px-4 py-3 text-right">{formatRupiah(item.unit_cost)}</td>
                        <td className="px-4 py-3 text-right text-amber-400">{formatRupiah(item.subtotal)}</td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot className="bg-red-900/10">
                    <tr className="border-t border-red-900/30">
                      <td colSpan="4" className="px-4 py-3 text-right font-semibold">Subtotal</td>
                      <td className="px-4 py-3 text-right font-semibold">{formatRupiah(selectedOrder.subtotal)}</td>
                    </tr>
                    {selectedOrder.discount_amount > 0 && (
                      <tr>
                        <td colSpan="4" className="px-4 py-2 text-right">Diskon</td>
                        <td className="px-4 py-2 text-right text-red-400">-{formatRupiah(selectedOrder.discount_amount)}</td>
                      </tr>
                    )}
                    {selectedOrder.tax_amount > 0 && (
                      <tr>
                        <td colSpan="4" className="px-4 py-2 text-right">PPN ({selectedOrder.tax_percent}%)</td>
                        <td className="px-4 py-2 text-right">{formatRupiah(selectedOrder.tax_amount)}</td>
                      </tr>
                    )}
                    <tr className="border-t border-red-900/30">
                      <td colSpan="4" className="px-4 py-3 text-right font-bold text-lg">TOTAL</td>
                      <td className="px-4 py-3 text-right font-bold text-lg text-amber-400">{formatRupiah(selectedOrder.total)}</td>
                    </tr>
                  </tfoot>
                </table>
              </div>

              {selectedOrder.notes && (
                <div className="bg-[#0a0608] rounded-lg p-4">
                  <h3 className="text-amber-200 font-semibold mb-2">Catatan</h3>
                  <p className="text-gray-300">{selectedOrder.notes}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Modal Receive */}
      {showReceiveModal && selectedOrder && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-2xl">
            <div className="p-6 border-b border-red-900/30 flex justify-between items-center">
              <h2 className="text-xl font-bold">Terima Barang - {selectedOrder.po_number || selectedOrder.po_no}</h2>
              <button onClick={() => setShowReceiveModal(false)} className="text-gray-400 hover:text-white"><X className="h-6 w-6" /></button>
            </div>
            
            <div className="p-6 space-y-4">
              {receiveItems.map((item, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 bg-[#0a0608] rounded-lg">
                  <div>
                    <div className="font-medium">{item.product_name}</div>
                    <div className="text-sm text-gray-400">Dipesan: {item.ordered_qty} | Diterima: {item.received_qty}</div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-gray-400">Qty diterima:</span>
                    <input type="number" min="0" max={item.ordered_qty - item.received_qty} value={item.quantity}
                      onChange={(e) => {
                        const newItems = [...receiveItems];
                        newItems[idx].quantity = Math.min(Number(e.target.value), item.ordered_qty - item.received_qty);
                        setReceiveItems(newItems);
                      }}
                      className="w-20 px-3 py-2 bg-[#1a1214] border border-red-900/30 rounded text-center"
                    />
                  </div>
                </div>
              ))}
              
              <div className="flex justify-end gap-3 pt-4">
                <button onClick={() => setShowReceiveModal(false)} className="px-4 py-2 border border-red-900/30 rounded-lg">Batal</button>
                <button onClick={handleReceive} className="px-4 py-2 bg-gradient-to-r from-green-600 to-emerald-600 rounded-lg flex items-center gap-2">
                  <Check className="h-4 w-4" /> Terima Barang
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Purchase;
