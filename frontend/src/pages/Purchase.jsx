import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Plus, Search, Edit, Trash2, Truck, X, Save, Loader2, Check, Package, FileText, ReceiptText } from 'lucide-react';
import { toast } from 'sonner';

const Purchase = () => {
  const { api, user } = useAuth();
  const [orders, setOrders] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [showReceiveModal, setShowReceiveModal] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [saving, setSaving] = useState(false);
  const [statusFilter, setStatusFilter] = useState('');
  const [form, setForm] = useState({ supplier_id: '', expected_date: '', notes: '', items: [] });
  const [receiveItems, setReceiveItems] = useState([]);

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
    if (form.items.find(i => i.product_id === product.id)) {
      toast.error('Produk sudah ada dalam daftar');
      return;
    }
    setForm({ ...form, items: [...form.items, { 
      product_id: product.id, 
      product_name: product.name, 
      product_code: product.code,
      quantity: 1, 
      unit_cost: product.cost_price || 0, 
      discount_percent: 0 
    }]});
  };

  const updateItem = (index, field, value) => {
    const newItems = [...form.items];
    newItems[index][field] = value;
    setForm({ ...form, items: newItems });
  };

  const removeItem = (index) => {
    setForm({ ...form, items: form.items.filter((_, i) => i !== index) });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.supplier_id || form.items.length === 0) { 
      toast.error('Pilih supplier dan tambahkan minimal 1 item'); 
      return; 
    }
    setSaving(true);
    try {
      const res = await api('/api/purchase/orders', {
        method: 'POST',
        body: JSON.stringify(form)
      });
      if (res.ok) { 
        toast.success('Purchase Order dibuat'); 
        setShowModal(false); 
        loadOrders(); 
      } else { 
        const error = await res.json(); 
        toast.error(error.detail || 'Gagal menyimpan'); 
      }
    } catch (err) { toast.error('Gagal menyimpan'); }
    finally { setSaving(false); }
  };

  const submitOrder = async (orderId) => {
    try {
      const res = await api(`/api/purchase/orders/${orderId}/submit`, { method: 'POST' });
      if (res.ok) { toast.success('PO dikirim ke supplier'); loadOrders(); }
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

  return (
    <div className="space-y-6">
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
                    <div className="font-medium">{order.po_number}</div>
                    <div className="text-sm text-gray-400">{new Date(order.created_at).toLocaleDateString('id-ID')}</div>
                  </td>
                  <td className="px-4 py-3 text-gray-300">{order.supplier_name}</td>
                  <td className="px-4 py-3 text-center">{order.items?.length || 0}</td>
                  <td className="px-4 py-3 text-right text-amber-400 font-semibold">{formatRupiah(order.total)}</td>
                  <td className="px-4 py-3 text-center">
                    <span className={`px-2 py-1 rounded text-xs font-semibold ${statusColors[order.status]}`}>
                      {statusLabels[order.status] || order.status}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex justify-center gap-1">
                      {order.status === 'draft' && (
                        <>
                          <button onClick={() => submitOrder(order.id)} className="px-2 py-1 text-xs bg-blue-600/20 text-blue-400 rounded hover:bg-blue-600/30">Kirim</button>
                          <button onClick={() => cancelOrder(order.id)} className="px-2 py-1 text-xs bg-red-600/20 text-red-400 rounded hover:bg-red-600/30">Batal</button>
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
                      <div className="text-xs text-gray-400">{product.code}</div>
                    </button>
                  ))}
                </div>
              </div>

              {form.items.length > 0 && (
                <div>
                  <label className="block text-sm text-gray-400 mb-2">Daftar Item ({form.items.length})</label>
                  <div className="bg-[#0a0608] rounded-lg overflow-hidden">
                    <table className="w-full text-sm">
                      <thead className="bg-red-900/20">
                        <tr>
                          <th className="px-3 py-2 text-left">Produk</th>
                          <th className="px-3 py-2 text-center w-24">Qty</th>
                          <th className="px-3 py-2 text-right w-32">Harga</th>
                          <th className="px-3 py-2 text-center w-20">Disc %</th>
                          <th className="px-3 py-2 text-right w-32">Subtotal</th>
                          <th className="px-3 py-2 w-10"></th>
                        </tr>
                      </thead>
                      <tbody>
                        {form.items.map((item, idx) => {
                          const subtotal = item.quantity * item.unit_cost * (1 - item.discount_percent / 100);
                          return (
                            <tr key={idx} className="border-t border-red-900/10">
                              <td className="px-3 py-2">{item.product_name}</td>
                              <td className="px-3 py-2"><input type="number" min="1" value={item.quantity} onChange={(e) => updateItem(idx, 'quantity', Number(e.target.value))} className="w-full px-2 py-1 bg-[#1a1214] border border-red-900/30 rounded text-center" /></td>
                              <td className="px-3 py-2"><input type="number" value={item.unit_cost} onChange={(e) => updateItem(idx, 'unit_cost', Number(e.target.value))} className="w-full px-2 py-1 bg-[#1a1214] border border-red-900/30 rounded text-right" /></td>
                              <td className="px-3 py-2"><input type="number" min="0" max="100" value={item.discount_percent} onChange={(e) => updateItem(idx, 'discount_percent', Number(e.target.value))} className="w-full px-2 py-1 bg-[#1a1214] border border-red-900/30 rounded text-center" /></td>
                              <td className="px-3 py-2 text-right text-amber-400">{formatRupiah(subtotal)}</td>
                              <td className="px-3 py-2"><button type="button" onClick={() => removeItem(idx)} className="text-red-400 hover:text-red-300"><X className="h-4 w-4" /></button></td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                  <div className="text-right mt-3 text-lg font-bold text-amber-400">Total: {formatRupiah(totalForm)}</div>
                </div>
              )}

              <div>
                <label className="block text-sm text-gray-400 mb-1">Catatan</label>
                <textarea value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" rows={2} />
              </div>

              <div className="flex gap-3 pt-4">
                <button type="button" onClick={() => setShowModal(false)} className="flex-1 py-2 border border-red-900/30 rounded-lg hover:bg-red-900/20">Batal</button>
                <button type="submit" disabled={saving || form.items.length === 0} className="flex-1 py-2 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg disabled:opacity-50 flex items-center justify-center gap-2">
                  {saving ? <Loader2 className="h-5 w-5 animate-spin" /> : <Save className="h-5 w-5" />}
                  {saving ? 'Menyimpan...' : 'Simpan PO'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal Terima Barang */}
      {showReceiveModal && selectedOrder && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-2xl">
            <div className="p-6 border-b border-red-900/30 flex justify-between items-center">
              <div>
                <h2 className="text-xl font-bold">Terima Barang</h2>
                <p className="text-gray-400 text-sm">PO: {selectedOrder.po_number}</p>
              </div>
              <button onClick={() => setShowReceiveModal(false)} className="text-gray-400 hover:text-white"><X className="h-6 w-6" /></button>
            </div>
            
            <div className="p-6">
              <div className="space-y-3 max-h-80 overflow-y-auto">
                {receiveItems.map((item, idx) => {
                  const remaining = item.ordered_qty - item.received_qty;
                  return (
                    <div key={idx} className="p-3 bg-[#0a0608] rounded-lg">
                      <div className="flex justify-between items-center mb-2">
                        <div>
                          <div className="font-medium">{item.product_name}</div>
                          <div className="text-sm text-gray-400">Dipesan: {item.ordered_qty} | Diterima: {item.received_qty} | Sisa: {remaining}</div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <label className="text-sm text-gray-400">Terima:</label>
                        <input type="number" min="0" max={remaining} value={item.quantity} onChange={(e) => {
                          const newItems = [...receiveItems];
                          newItems[idx].quantity = Math.min(remaining, Math.max(0, Number(e.target.value)));
                          setReceiveItems(newItems);
                        }} className="w-24 px-2 py-1 bg-[#1a1214] border border-red-900/30 rounded text-center" />
                        <button type="button" onClick={() => {
                          const newItems = [...receiveItems];
                          newItems[idx].quantity = remaining;
                          setReceiveItems(newItems);
                        }} className="px-2 py-1 text-xs bg-blue-600/20 text-blue-400 rounded">Semua</button>
                      </div>
                    </div>
                  );
                })}
              </div>

              <div className="flex gap-3 mt-6">
                <button onClick={() => setShowReceiveModal(false)} className="flex-1 py-2 border border-red-900/30 rounded-lg hover:bg-red-900/20">Batal</button>
                <button onClick={handleReceive} className="flex-1 py-2 bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-lg flex items-center justify-center gap-2">
                  <Check className="h-5 w-5" /> Konfirmasi Terima
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
