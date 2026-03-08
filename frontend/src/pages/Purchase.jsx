import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Plus, Search, Truck, Package, FileText, Check, X, Loader2, Eye } from 'lucide-react';
import { toast } from 'sonner';

const Purchase = () => {
  const { api } = useAuth();
  const [activeTab, setActiveTab] = useState('orders');
  const [orders, setOrders] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [showReceiveModal, setShowReceiveModal] = useState(false);
  const [selectedPO, setSelectedPO] = useState(null);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({ supplier_id: '', items: [], notes: '' });

  const formatRupiah = (num) => `Rp ${(num || 0).toLocaleString('id-ID')}`;

  useEffect(() => { loadOrders(); loadSuppliers(); loadProducts(); }, []);

  const loadOrders = async () => {
    setLoading(true);
    try {
      const res = await api('/api/purchase/orders?limit=100');
      if (res.ok) { const data = await res.json(); setOrders(data.items || []); }
    } catch (err) { toast.error('Gagal memuat data'); }
    finally { setLoading(false); }
  };

  const loadSuppliers = async () => {
    try {
      const res = await api('/api/suppliers?limit=100');
      if (res.ok) { const data = await res.json(); setSuppliers(data.items || []); }
    } catch (err) { console.error(err); }
  };

  const loadProducts = async () => {
    try {
      const res = await api('/api/products?limit=500');
      if (res.ok) { const data = await res.json(); setProducts(data.items || []); }
    } catch (err) { console.error(err); }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.supplier_id || form.items.length === 0) { toast.error('Pilih supplier dan tambahkan item'); return; }
    setSaving(true);
    try {
      const res = await api('/api/purchase/orders', { method: 'POST', body: JSON.stringify(form) });
      if (res.ok) { toast.success('PO dibuat'); setShowModal(false); setForm({ supplier_id: '', items: [], notes: '' }); loadOrders(); }
      else { const error = await res.json(); toast.error(error.detail || 'Gagal'); }
    } catch (err) { toast.error('Gagal'); }
    finally { setSaving(false); }
  };

  const handleSubmitPO = async (id) => {
    try {
      const res = await api(`/api/purchase/orders/${id}/submit`, { method: 'POST' });
      if (res.ok) { toast.success('PO dikirim ke supplier'); loadOrders(); }
    } catch (err) { toast.error('Gagal'); }
  };

  const handleReceive = async () => {
    if (!selectedPO) return;
    try {
      const receiveItems = selectedPO.items.map(item => ({
        product_id: item.product_id,
        quantity: item.receive_qty || item.quantity - (item.received_qty || 0)
      })).filter(i => i.quantity > 0);
      
      const res = await api(`/api/purchase/orders/${selectedPO.id}/receive`, {
        method: 'POST',
        body: JSON.stringify({ items: receiveItems, notes: '' })
      });
      if (res.ok) { toast.success('Barang diterima'); setShowReceiveModal(false); loadOrders(); }
    } catch (err) { toast.error('Gagal'); }
  };

  const statusLabels = { draft: 'Draft', ordered: 'Dipesan', partial: 'Sebagian', received: 'Diterima', cancelled: 'Dibatalkan' };
  const statusColors = { draft: 'bg-gray-900/30 text-gray-400', ordered: 'bg-blue-900/30 text-blue-400', partial: 'bg-amber-900/30 text-amber-400', received: 'bg-green-900/30 text-green-400', cancelled: 'bg-red-900/30 text-red-400' };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Pembelian</h1>
          <p className="text-gray-400">Kelola purchase order dan penerimaan barang</p>
        </div>
        <button onClick={() => setShowModal(true)} className="px-4 py-2 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg flex items-center gap-2">
          <Plus className="h-5 w-5" /> Buat PO
        </button>
      </div>

      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
        <table className="w-full">
          <thead className="bg-red-900/20">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-semibold">No. PO</th>
              <th className="px-4 py-3 text-left text-sm font-semibold">Supplier</th>
              <th className="px-4 py-3 text-right text-sm font-semibold">Total</th>
              <th className="px-4 py-3 text-center text-sm font-semibold">Item</th>
              <th className="px-4 py-3 text-center text-sm font-semibold">Status</th>
              <th className="px-4 py-3 text-center text-sm font-semibold">Aksi</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={6} className="px-4 py-8 text-center"><Loader2 className="h-8 w-8 animate-spin mx-auto text-red-400" /></td></tr>
            ) : orders.length === 0 ? (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-400"><Truck className="h-12 w-12 mx-auto mb-2 opacity-30" />Belum ada purchase order</td></tr>
            ) : (
              orders.map(po => (
                <tr key={po.id} className="border-t border-red-900/10 hover:bg-red-900/10">
                  <td className="px-4 py-3 font-medium">{po.po_number}</td>
                  <td className="px-4 py-3 text-gray-400">{po.supplier_name}</td>
                  <td className="px-4 py-3 text-right text-amber-400 font-semibold">{formatRupiah(po.total)}</td>
                  <td className="px-4 py-3 text-center">{po.items?.length || 0}</td>
                  <td className="px-4 py-3 text-center">
                    <span className={`px-2 py-1 rounded text-xs font-semibold ${statusColors[po.status]}`}>
                      {statusLabels[po.status]}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex justify-center gap-2">
                      {po.status === 'draft' && (
                        <button onClick={() => handleSubmitPO(po.id)} className="px-2 py-1 text-xs bg-blue-600/20 text-blue-400 rounded hover:bg-blue-600/30">Kirim</button>
                      )}
                      {(po.status === 'ordered' || po.status === 'partial') && (
                        <button onClick={() => { setSelectedPO(po); setShowReceiveModal(true); }} className="px-2 py-1 text-xs bg-green-600/20 text-green-400 rounded hover:bg-green-600/30">Terima</button>
                      )}
                      <button onClick={() => { setSelectedPO(po); }} className="px-2 py-1 text-xs bg-gray-600/20 text-gray-400 rounded hover:bg-gray-600/30"><Eye className="h-3 w-3" /></button>
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
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-red-900/30 flex justify-between items-center sticky top-0 bg-[#1a1214]">
              <h2 className="text-xl font-bold">Buat Purchase Order</h2>
              <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-white"><X className="h-6 w-6" /></button>
            </div>
            
            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Supplier *</label>
                <select value={form.supplier_id} onChange={(e) => setForm({ ...form, supplier_id: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" required>
                  <option value="">Pilih Supplier</option>
                  {suppliers.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                </select>
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-2">Produk</label>
                <div className="space-y-2 max-h-60 overflow-y-auto">
                  {products.map(p => {
                    const existing = form.items.find(i => i.product_id === p.id);
                    return (
                      <div key={p.id} className="flex items-center justify-between p-2 bg-[#0a0608] rounded">
                        <div>
                          <div className="text-sm font-medium">{p.name}</div>
                          <div className="text-xs text-gray-400">Modal: {formatRupiah(p.cost_price)}</div>
                        </div>
                        {existing ? (
                          <div className="flex items-center gap-2">
                            <input type="number" min="1" value={existing.quantity} onChange={(e) => setForm({ ...form, items: form.items.map(i => i.product_id === p.id ? { ...i, quantity: Number(e.target.value) } : i) })} className="w-16 px-2 py-1 bg-[#1a1214] border border-red-900/30 rounded text-center" />
                            <input type="number" min="0" value={existing.unit_cost} onChange={(e) => setForm({ ...form, items: form.items.map(i => i.product_id === p.id ? { ...i, unit_cost: Number(e.target.value) } : i) })} className="w-24 px-2 py-1 bg-[#1a1214] border border-red-900/30 rounded text-center" placeholder="Harga" />
                            <button type="button" onClick={() => setForm({ ...form, items: form.items.filter(i => i.product_id !== p.id) })} className="text-red-400"><X className="h-4 w-4" /></button>
                          </div>
                        ) : (
                          <button type="button" onClick={() => setForm({ ...form, items: [...form.items, { product_id: p.id, quantity: 1, unit_cost: p.cost_price }] })} className="px-2 py-1 text-xs bg-green-600/20 text-green-400 rounded">Tambah</button>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-1">Catatan</label>
                <textarea value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" rows={2} />
              </div>

              <div className="border-t border-red-900/30 pt-4">
                <div className="flex justify-between text-lg font-bold">
                  <span>Total</span>
                  <span className="text-amber-400">{formatRupiah(form.items.reduce((sum, i) => sum + (i.quantity * i.unit_cost), 0))}</span>
                </div>
              </div>

              <div className="flex gap-3 pt-4">
                <button type="button" onClick={() => setShowModal(false)} className="flex-1 py-2 border border-red-900/30 rounded-lg hover:bg-red-900/20">Batal</button>
                <button type="submit" disabled={saving} className="flex-1 py-2 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg disabled:opacity-50">
                  {saving ? 'Menyimpan...' : 'Buat PO'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal Terima Barang */}
      {showReceiveModal && selectedPO && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-lg p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">Terima Barang - {selectedPO.po_number}</h2>
              <button onClick={() => setShowReceiveModal(false)} className="text-gray-400 hover:text-white"><X className="h-6 w-6" /></button>
            </div>
            
            <div className="space-y-2 max-h-60 overflow-y-auto mb-6">
              {selectedPO.items?.map((item, idx) => {
                const remaining = item.quantity - (item.received_qty || 0);
                return (
                  <div key={idx} className="flex items-center justify-between p-3 bg-[#0a0608] rounded-lg">
                    <div>
                      <div className="font-medium">{item.product_name}</div>
                      <div className="text-sm text-gray-400">Dipesan: {item.quantity} | Diterima: {item.received_qty || 0}</div>
                    </div>
                    <div className="flex items-center gap-2">
                      <input type="number" min="0" max={remaining} defaultValue={remaining} onChange={(e) => { item.receive_qty = Number(e.target.value); }} className="w-20 px-2 py-1 bg-[#1a1214] border border-red-900/30 rounded text-center" />
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="flex gap-3">
              <button onClick={() => setShowReceiveModal(false)} className="flex-1 py-2 border border-red-900/30 rounded-lg hover:bg-red-900/20">Batal</button>
              <button onClick={handleReceive} className="flex-1 py-2 bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-lg flex items-center justify-center gap-2">
                <Check className="h-5 w-5" /> Konfirmasi Terima
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Purchase;
