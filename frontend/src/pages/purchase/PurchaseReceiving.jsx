import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Search, Check, Loader2, Package, Truck, Eye, X } from 'lucide-react';
import { toast } from 'sonner';

const PurchaseReceiving = () => {
  const { api } = useAuth();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showReceiveModal, setShowReceiveModal] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [receiveItems, setReceiveItems] = useState([]);

  const loadOrders = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api(`/api/purchase/orders?status=submitted,ordered,partial,posted&search=${searchTerm}`);
      if (res.ok) {
        const data = await res.json();
        setOrders(data.items || data || []);
      }
    } catch (err) {
      toast.error('Gagal memuat data');
    } finally {
      setLoading(false);
    }
  }, [api, searchTerm]);

  useEffect(() => {
    loadOrders();
  }, [loadOrders]);

  const handleOpenReceive = (order) => {
    setSelectedOrder(order);
    setReceiveItems(order.items.map(item => ({
      product_id: item.product_id,
      product_name: item.product_name,
      ordered_qty: item.quantity,
      received_qty: item.received_quantity || 0,
      pending_qty: item.quantity - (item.received_quantity || 0),
      receive_now: item.quantity - (item.received_quantity || 0)
    })));
    setShowReceiveModal(true);
  };

  const updateReceiveQty = (index, qty) => {
    const newItems = [...receiveItems];
    newItems[index].receive_now = Math.min(Math.max(0, qty), newItems[index].pending_qty);
    setReceiveItems(newItems);
  };

  const handleReceive = async () => {
    const itemsToReceive = receiveItems.filter(i => i.receive_now > 0);
    if (itemsToReceive.length === 0) {
      toast.error('Pilih minimal 1 item untuk diterima');
      return;
    }
    
    try {
      const res = await api(`/api/purchase/orders/${selectedOrder.id}/receive`, {
        method: 'POST',
        body: JSON.stringify({
          items: itemsToReceive.map(i => ({
            product_id: i.product_id,
            quantity: i.receive_now
          })),
          notes: 'Penerimaan barang'
        })
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

  const getStatusBadge = (status) => {
    const badges = {
      submitted: 'bg-blue-600/20 text-blue-400',
      ordered: 'bg-blue-600/20 text-blue-400',
      posted: 'bg-green-600/20 text-green-400',
      partial: 'bg-yellow-600/20 text-yellow-400',
      received: 'bg-emerald-600/20 text-emerald-400'
    };
    const labels = {
      submitted: 'Menunggu',
      ordered: 'Dipesan',
      posted: 'Posted',
      partial: 'Sebagian',
      received: 'Selesai'
    };
    return (
      <span className={`px-2 py-1 rounded-full text-xs ${badges[status] || 'bg-gray-600/20 text-gray-400'}`}>
        {labels[status] || status}
      </span>
    );
  };

  return (
    <div className="space-y-4" data-testid="purchase-receiving-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Penerimaan Barang</h1>
          <p className="text-gray-400 text-sm">Terima barang dari purchase order</p>
        </div>
      </div>

      {/* Info Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
          <p className="text-gray-400 text-sm">Menunggu Diterima</p>
          <p className="text-2xl font-bold text-blue-400">{orders.filter(o => o.status === 'submitted').length}</p>
        </div>
        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
          <p className="text-gray-400 text-sm">Sebagian Diterima</p>
          <p className="text-2xl font-bold text-yellow-400">{orders.filter(o => o.status === 'partial').length}</p>
        </div>
        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
          <p className="text-gray-400 text-sm">Total PO Pending</p>
          <p className="text-2xl font-bold text-amber-200">{orders.length}</p>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Cari no. PO, supplier..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200"
          />
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
                <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-400">Tidak ada PO yang menunggu penerimaan</td></tr>
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
                    <div className="flex items-center justify-center">
                      <button 
                        onClick={() => handleOpenReceive(order)}
                        className="px-3 py-1.5 bg-green-600/20 text-green-400 rounded-lg flex items-center gap-1 text-sm hover:bg-green-600/30"
                      >
                        <Package className="h-4 w-4" /> Terima
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Receive Modal */}
      {showReceiveModal && selectedOrder && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
            <div className="p-4 border-b border-red-900/30 flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold text-amber-100">Penerimaan Barang</h2>
                <p className="text-sm text-gray-400">{selectedOrder.po_number} - {selectedOrder.supplier_name}</p>
              </div>
              <button onClick={() => setShowReceiveModal(false)} className="p-1 hover:bg-red-900/20 rounded">
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="p-4">
              <div className="border border-red-900/30 rounded-lg overflow-hidden">
                <table className="w-full">
                  <thead className="bg-red-900/20">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs text-amber-200">PRODUK</th>
                      <th className="px-4 py-2 text-center text-xs text-amber-200">DIPESAN</th>
                      <th className="px-4 py-2 text-center text-xs text-amber-200">DITERIMA</th>
                      <th className="px-4 py-2 text-center text-xs text-amber-200">SISA</th>
                      <th className="px-4 py-2 text-center text-xs text-amber-200">TERIMA SEKARANG</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-red-900/20">
                    {receiveItems.map((item, idx) => (
                      <tr key={idx} className={item.pending_qty === 0 ? 'opacity-50' : ''}>
                        <td className="px-4 py-3 text-gray-200">{item.product_name}</td>
                        <td className="px-4 py-3 text-center text-gray-400">{item.ordered_qty}</td>
                        <td className="px-4 py-3 text-center text-green-400">{item.received_qty}</td>
                        <td className="px-4 py-3 text-center text-amber-400">{item.pending_qty}</td>
                        <td className="px-4 py-3">
                          <input
                            type="number"
                            min="0"
                            max={item.pending_qty}
                            value={item.receive_now}
                            onChange={(e) => updateReceiveQty(idx, Number(e.target.value))}
                            disabled={item.pending_qty === 0}
                            className="w-20 px-2 py-1 bg-[#0a0608] border border-red-900/30 rounded text-center text-sm mx-auto block disabled:opacity-50"
                          />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              
              <div className="flex justify-end gap-3 mt-4">
                <button onClick={() => setShowReceiveModal(false)} className="px-4 py-2 border border-red-900/30 rounded-lg">
                  Batal
                </button>
                <button 
                  onClick={handleReceive}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg flex items-center gap-2"
                >
                  <Check className="h-4 w-4" /> Terima & Update Stok
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PurchaseReceiving;
