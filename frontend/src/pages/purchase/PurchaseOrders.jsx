import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { 
  Plus, Search, Eye, Printer, Truck, Check, X, RotateCcw, 
  Loader2, FileText, Calendar, Package, ChevronDown
} from 'lucide-react';
import { toast } from 'sonner';

const PurchaseOrders = () => {
  const { api } = useAuth();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [showReceiveModal, setShowReceiveModal] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [suppliers, setSuppliers] = useState([]);
  const [products, setProducts] = useState([]);
  
  const [formData, setFormData] = useState({
    supplier_id: '',
    notes: '',
    items: [{ product_id: '', quantity: 1, unit_cost: 0, discount_percent: 0 }]
  });

  const loadOrders = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        ...(searchTerm && { search: searchTerm }),
        ...(statusFilter && { status: statusFilter })
      });
      const res = await api(`/api/purchase/orders?${params}`);
      if (res.ok) {
        const data = await res.json();
        setOrders(data.items || data || []);
      }
    } catch (err) {
      toast.error('Gagal memuat data');
    } finally {
      setLoading(false);
    }
  }, [api, searchTerm, statusFilter]);

  const loadMasterData = useCallback(async () => {
    try {
      const [supRes, prodRes] = await Promise.all([
        api('/api/suppliers'),
        api('/api/products')
      ]);
      if (supRes.ok) {
        const data = await supRes.json();
        setSuppliers(data.items || data || []);
      }
      if (prodRes.ok) {
        const data = await prodRes.json();
        setProducts(data.items || data || []);
      }
    } catch (err) {
      console.error('Error loading master data');
    }
  }, [api]);

  useEffect(() => {
    loadOrders();
    loadMasterData();
  }, [loadOrders, loadMasterData]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.supplier_id) {
      toast.error('Pilih supplier terlebih dahulu');
      return;
    }
    if (formData.items.some(i => !i.product_id || i.quantity <= 0)) {
      toast.error('Lengkapi data item');
      return;
    }

    try {
      const res = await api('/api/purchase/orders', {
        method: 'POST',
        body: JSON.stringify(formData)
      });
      if (res.ok) {
        toast.success('Purchase Order berhasil dibuat');
        setShowModal(false);
        resetForm();
        loadOrders();
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Gagal membuat PO');
      }
    } catch (err) {
      toast.error('Terjadi kesalahan');
    }
  };

  const handleSubmitPO = async (order) => {
    if (!confirm(`Submit PO ${order.po_number} ke supplier?`)) return;
    try {
      const res = await api(`/api/purchase/orders/${order.id}/submit`, { method: 'POST' });
      if (res.ok) {
        toast.success('PO berhasil disubmit');
        loadOrders();
      }
    } catch (err) {
      toast.error('Gagal submit PO');
    }
  };

  const handleReceive = async () => {
    if (!selectedOrder) return;
    try {
      const receiveItems = selectedOrder.items.map(item => ({
        product_id: item.product_id,
        quantity: item.quantity - (item.received_quantity || 0)
      }));

      const res = await api(`/api/purchase/orders/${selectedOrder.id}/receive`, {
        method: 'POST',
        body: JSON.stringify({ items: receiveItems, notes: 'Penerimaan barang' })
      });
      if (res.ok) {
        toast.success('Barang berhasil diterima, stok diupdate');
        setShowReceiveModal(false);
        setSelectedOrder(null);
        loadOrders();
      }
    } catch (err) {
      toast.error('Gagal menerima barang');
    }
  };

  const handleCancel = async (order) => {
    if (!confirm(`Batalkan PO ${order.po_number}?`)) return;
    try {
      const res = await api(`/api/purchase/orders/${order.id}/cancel`, { method: 'POST' });
      if (res.ok) {
        toast.success('PO dibatalkan');
        loadOrders();
      }
    } catch (err) {
      toast.error('Gagal membatalkan PO');
    }
  };

  const resetForm = () => {
    setFormData({
      supplier_id: '',
      notes: '',
      items: [{ product_id: '', quantity: 1, unit_cost: 0, discount_percent: 0 }]
    });
  };

  const addItem = () => {
    setFormData(prev => ({
      ...prev,
      items: [...prev.items, { product_id: '', quantity: 1, unit_cost: 0, discount_percent: 0 }]
    }));
  };

  const removeItem = (index) => {
    if (formData.items.length === 1) return;
    setFormData(prev => ({
      ...prev,
      items: prev.items.filter((_, i) => i !== index)
    }));
  };

  const updateItem = (index, field, value) => {
    const newItems = [...formData.items];
    newItems[index][field] = value;
    
    // Auto-fill price when product selected
    if (field === 'product_id') {
      const product = products.find(p => p.id === value);
      if (product) {
        newItems[index].unit_cost = product.cost_price || 0;
      }
    }
    
    setFormData(prev => ({ ...prev, items: newItems }));
  };

  const getStatusBadge = (status) => {
    const badges = {
      draft: 'bg-gray-600/20 text-gray-400',
      submitted: 'bg-blue-600/20 text-blue-400',
      partial: 'bg-yellow-600/20 text-yellow-400',
      received: 'bg-green-600/20 text-green-400',
      cancelled: 'bg-red-600/20 text-red-400'
    };
    const labels = {
      draft: 'Draft',
      submitted: 'Disubmit',
      partial: 'Sebagian',
      received: 'Diterima',
      cancelled: 'Dibatalkan'
    };
    return (
      <span className={`px-2 py-1 rounded-full text-xs ${badges[status] || badges.draft}`}>
        {labels[status] || status}
      </span>
    );
  };

  const calculateTotal = () => {
    return formData.items.reduce((sum, item) => {
      const subtotal = item.quantity * item.unit_cost;
      const discount = subtotal * (item.discount_percent / 100);
      return sum + subtotal - discount;
    }, 0);
  };

  return (
    <div className="space-y-4" data-testid="purchase-orders-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Pesanan Pembelian</h1>
          <p className="text-gray-400 text-sm">Kelola purchase order ke supplier</p>
        </div>
        <button 
          onClick={() => { resetForm(); setShowModal(true); }}
          className="px-4 py-2 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg flex items-center gap-2"
        >
          <Plus className="h-4 w-4" /> Buat PO Baru
        </button>
      </div>

      {/* Filters */}
      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Cari no. PO, supplier..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200"
            />
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-4 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200"
          >
            <option value="">Semua Status</option>
            <option value="draft">Draft</option>
            <option value="submitted">Disubmit</option>
            <option value="partial">Sebagian Diterima</option>
            <option value="received">Diterima</option>
            <option value="cancelled">Dibatalkan</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-red-900/20">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">NO. PO</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">TANGGAL</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">SUPPLIER</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-amber-200">ITEMS</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-amber-200">TOTAL</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">STATUS</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">AKSI</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-red-900/20">
              {loading ? (
                <tr><td colSpan={7} className="px-4 py-8 text-center"><Loader2 className="h-8 w-8 animate-spin mx-auto text-amber-400" /></td></tr>
              ) : orders.length === 0 ? (
                <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-400">Belum ada purchase order</td></tr>
              ) : orders.map(order => (
                <tr key={order.id} className="hover:bg-red-900/10">
                  <td className="px-4 py-3">
                    <div className="font-medium text-amber-300 font-mono">{order.po_number}</div>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-400">
                    {new Date(order.created_at).toLocaleDateString('id-ID')}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-200">{order.supplier_name}</td>
                  <td className="px-4 py-3 text-sm text-right text-gray-300">{order.items?.length || 0} item</td>
                  <td className="px-4 py-3 text-sm text-right text-green-400 font-medium">
                    Rp {(order.total || 0).toLocaleString('id-ID')}
                  </td>
                  <td className="px-4 py-3 text-center">{getStatusBadge(order.status)}</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-center gap-1">
                      {order.status === 'draft' && (
                        <button 
                          onClick={() => handleSubmitPO(order)}
                          className="p-1.5 hover:bg-blue-600/20 rounded text-blue-400"
                          title="Submit ke Supplier"
                        >
                          <Truck className="h-4 w-4" />
                        </button>
                      )}
                      {(order.status === 'submitted' || order.status === 'partial') && (
                        <button 
                          onClick={() => { setSelectedOrder(order); setShowReceiveModal(true); }}
                          className="p-1.5 hover:bg-green-600/20 rounded text-green-400"
                          title="Terima Barang"
                        >
                          <Check className="h-4 w-4" />
                        </button>
                      )}
                      {order.status !== 'received' && order.status !== 'cancelled' && (
                        <button 
                          onClick={() => handleCancel(order)}
                          className="p-1.5 hover:bg-red-600/20 rounded text-red-400"
                          title="Batalkan"
                        >
                          <X className="h-4 w-4" />
                        </button>
                      )}
                      <button className="p-1.5 hover:bg-gray-600/20 rounded text-gray-400" title="Print">
                        <Printer className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Create PO Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <div className="p-4 border-b border-red-900/30 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-amber-100">Buat Purchase Order Baru</h2>
              <button onClick={() => setShowModal(false)} className="p-1 hover:bg-red-900/20 rounded">
                <X className="h-5 w-5" />
              </button>
            </div>
            <form onSubmit={handleSubmit} className="p-4 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Supplier *</label>
                  <select
                    value={formData.supplier_id}
                    onChange={(e) => setFormData({ ...formData, supplier_id: e.target.value })}
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg"
                    required
                  >
                    <option value="">Pilih Supplier</option>
                    {suppliers.map(s => (
                      <option key={s.id} value={s.id}>{s.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Catatan</label>
                  <input
                    type="text"
                    value={formData.notes}
                    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg"
                    placeholder="Catatan tambahan..."
                  />
                </div>
              </div>

              {/* Items */}
              <div className="border border-red-900/30 rounded-lg overflow-hidden">
                <div className="bg-red-900/20 px-4 py-2 flex items-center justify-between">
                  <span className="font-medium text-amber-200">Item Pembelian</span>
                  <button type="button" onClick={addItem} className="text-sm text-amber-400 hover:text-amber-300">
                    + Tambah Item
                  </button>
                </div>
                <table className="w-full">
                  <thead className="bg-red-900/10">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs text-gray-400">PRODUK</th>
                      <th className="px-4 py-2 text-center text-xs text-gray-400 w-24">QTY</th>
                      <th className="px-4 py-2 text-right text-xs text-gray-400 w-32">HARGA</th>
                      <th className="px-4 py-2 text-center text-xs text-gray-400 w-20">DISK %</th>
                      <th className="px-4 py-2 text-right text-xs text-gray-400 w-36">SUBTOTAL</th>
                      <th className="px-4 py-2 w-12"></th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-red-900/20">
                    {formData.items.map((item, idx) => {
                      const subtotal = item.quantity * item.unit_cost * (1 - item.discount_percent/100);
                      return (
                        <tr key={idx}>
                          <td className="px-4 py-2">
                            <select
                              value={item.product_id}
                              onChange={(e) => updateItem(idx, 'product_id', e.target.value)}
                              className="w-full px-2 py-1 bg-[#0a0608] border border-red-900/30 rounded text-sm"
                            >
                              <option value="">Pilih Produk</option>
                              {products.map(p => (
                                <option key={p.id} value={p.id}>{p.name}</option>
                              ))}
                            </select>
                          </td>
                          <td className="px-4 py-2">
                            <input
                              type="number"
                              min="1"
                              value={item.quantity}
                              onChange={(e) => updateItem(idx, 'quantity', Number(e.target.value))}
                              className="w-full px-2 py-1 bg-[#0a0608] border border-red-900/30 rounded text-sm text-center"
                            />
                          </td>
                          <td className="px-4 py-2">
                            <input
                              type="number"
                              min="0"
                              value={item.unit_cost}
                              onChange={(e) => updateItem(idx, 'unit_cost', Number(e.target.value))}
                              className="w-full px-2 py-1 bg-[#0a0608] border border-red-900/30 rounded text-sm text-right"
                            />
                          </td>
                          <td className="px-4 py-2">
                            <input
                              type="number"
                              min="0"
                              max="100"
                              value={item.discount_percent}
                              onChange={(e) => updateItem(idx, 'discount_percent', Number(e.target.value))}
                              className="w-full px-2 py-1 bg-[#0a0608] border border-red-900/30 rounded text-sm text-center"
                            />
                          </td>
                          <td className="px-4 py-2 text-right text-sm text-green-400">
                            Rp {subtotal.toLocaleString('id-ID')}
                          </td>
                          <td className="px-4 py-2">
                            {formData.items.length > 1 && (
                              <button 
                                type="button" 
                                onClick={() => removeItem(idx)}
                                className="p-1 hover:bg-red-600/20 rounded text-red-400"
                              >
                                <X className="h-4 w-4" />
                              </button>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                  <tfoot className="bg-red-900/10">
                    <tr>
                      <td colSpan={4} className="px-4 py-3 text-right font-semibold text-amber-200">TOTAL:</td>
                      <td className="px-4 py-3 text-right font-bold text-green-400">
                        Rp {calculateTotal().toLocaleString('id-ID')}
                      </td>
                      <td></td>
                    </tr>
                  </tfoot>
                </table>
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-red-900/30">
                <button type="button" onClick={() => setShowModal(false)} className="px-4 py-2 border border-red-900/30 rounded-lg">
                  Batal
                </button>
                <button type="submit" className="px-4 py-2 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg">
                  Simpan PO
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Receive Modal */}
      {showReceiveModal && selectedOrder && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-2xl">
            <div className="p-4 border-b border-red-900/30 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-amber-100">
                Terima Barang - {selectedOrder.po_number}
              </h2>
              <button onClick={() => setShowReceiveModal(false)} className="p-1 hover:bg-red-900/20 rounded">
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="p-4">
              <p className="text-gray-400 mb-4">Barang yang akan diterima:</p>
              <table className="w-full mb-4">
                <thead className="bg-red-900/20">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs text-amber-200">PRODUK</th>
                    <th className="px-4 py-2 text-center text-xs text-amber-200">DIPESAN</th>
                    <th className="px-4 py-2 text-center text-xs text-amber-200">DITERIMA</th>
                    <th className="px-4 py-2 text-center text-xs text-amber-200">SISA</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-red-900/20">
                  {selectedOrder.items?.map((item, idx) => (
                    <tr key={idx}>
                      <td className="px-4 py-2 text-gray-200">{item.product_name}</td>
                      <td className="px-4 py-2 text-center text-gray-400">{item.quantity}</td>
                      <td className="px-4 py-2 text-center text-green-400">{item.received_quantity || 0}</td>
                      <td className="px-4 py-2 text-center text-amber-400">
                        {item.quantity - (item.received_quantity || 0)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div className="flex justify-end gap-3">
                <button 
                  onClick={() => setShowReceiveModal(false)} 
                  className="px-4 py-2 border border-red-900/30 rounded-lg"
                >
                  Batal
                </button>
                <button 
                  onClick={handleReceive}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg flex items-center gap-2"
                >
                  <Check className="h-4 w-4" /> Terima Semua Sisa
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PurchaseOrders;
