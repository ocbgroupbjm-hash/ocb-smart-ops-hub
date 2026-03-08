import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Plus, Search, X, Loader2, RotateCcw, Package } from 'lucide-react';
import { toast } from 'sonner';

const SalesReturns = () => {
  const { api } = useAuth();
  const [returns, setReturns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [sales, setSales] = useState([]);
  const [selectedSale, setSelectedSale] = useState(null);
  const [formData, setFormData] = useState({
    transaction_id: '', reason: '', items: []
  });

  const loadReturns = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api(`/api/sales/returns?search=${searchTerm}`);
      if (res.ok) {
        const data = await res.json();
        setReturns(data.items || data || []);
      }
    } catch (err) {
      toast.error('Gagal memuat data');
    } finally {
      setLoading(false);
    }
  }, [api, searchTerm]);

  const loadSales = useCallback(async () => {
    try {
      const res = await api('/api/pos/transactions?status=completed');
      if (res.ok) {
        const data = await res.json();
        setSales(data.items || data || []);
      }
    } catch (err) {
      console.error('Error loading sales');
    }
  }, [api]);

  useEffect(() => {
    loadReturns();
    loadSales();
  }, [loadReturns, loadSales]);

  const handleSelectSale = (saleId) => {
    const sale = sales.find(s => s.id === saleId);
    setSelectedSale(sale);
    if (sale) {
      setFormData({
        ...formData,
        transaction_id: saleId,
        items: sale.items.map(item => ({
          product_id: item.product_id,
          product_name: item.product_name,
          sold_qty: item.quantity,
          return_qty: 0
        }))
      });
    }
  };

  const updateReturnQty = (index, qty) => {
    const newItems = [...formData.items];
    newItems[index].return_qty = Math.min(qty, newItems[index].sold_qty);
    setFormData({ ...formData, items: newItems });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const returnItems = formData.items.filter(i => i.return_qty > 0);
    if (returnItems.length === 0) {
      toast.error('Pilih minimal 1 item untuk diretur');
      return;
    }
    try {
      const res = await api('/api/sales/returns', {
        method: 'POST',
        body: JSON.stringify({
          transaction_id: formData.transaction_id,
          reason: formData.reason,
          items: returnItems.map(i => ({
            product_id: i.product_id,
            quantity: i.return_qty
          }))
        })
      });
      if (res.ok) {
        toast.success('Retur berhasil dicatat');
        setShowModal(false);
        resetForm();
        loadReturns();
      }
    } catch (err) {
      toast.error('Gagal menyimpan retur');
    }
  };

  const resetForm = () => {
    setSelectedSale(null);
    setFormData({ transaction_id: '', reason: '', items: [] });
  };

  const getStatusBadge = (status) => {
    const badges = {
      pending: 'bg-yellow-600/20 text-yellow-400',
      approved: 'bg-green-600/20 text-green-400',
      rejected: 'bg-red-600/20 text-red-400'
    };
    const labels = {
      pending: 'Menunggu',
      approved: 'Disetujui',
      rejected: 'Ditolak'
    };
    return (
      <span className={`px-2 py-1 rounded-full text-xs ${badges[status] || badges.pending}`}>
        {labels[status] || status}
      </span>
    );
  };

  return (
    <div className="space-y-4" data-testid="sales-returns-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Retur Penjualan</h1>
          <p className="text-gray-400 text-sm">Kelola pengembalian barang dari pelanggan</p>
        </div>
        <button onClick={() => { resetForm(); setShowModal(true); }}
          className="px-4 py-2 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg flex items-center gap-2">
          <Plus className="h-4 w-4" /> Buat Retur
        </button>
      </div>

      {/* Filters */}
      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Cari retur..."
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
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">NO. RETUR</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">TANGGAL</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">NO. FAKTUR</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">PELANGGAN</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-amber-200">ITEMS</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-amber-200">NILAI</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">STATUS</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-red-900/20">
              {loading ? (
                <tr><td colSpan={7} className="px-4 py-8 text-center"><Loader2 className="h-8 w-8 animate-spin mx-auto text-amber-400" /></td></tr>
              ) : returns.length === 0 ? (
                <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-400">Belum ada data retur</td></tr>
              ) : returns.map(ret => (
                <tr key={ret.id} className="hover:bg-red-900/10">
                  <td className="px-4 py-3 text-sm font-mono text-amber-300">{ret.return_number || '-'}</td>
                  <td className="px-4 py-3 text-sm text-gray-400">
                    {new Date(ret.created_at).toLocaleDateString('id-ID')}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-300">{ret.invoice_number}</td>
                  <td className="px-4 py-3 text-sm text-gray-200">{ret.customer_name || 'Umum'}</td>
                  <td className="px-4 py-3 text-sm text-right text-gray-300">{ret.items?.length || 0} item</td>
                  <td className="px-4 py-3 text-sm text-right text-red-400 font-medium">
                    Rp {(ret.total || 0).toLocaleString('id-ID')}
                  </td>
                  <td className="px-4 py-3 text-center">{getStatusBadge(ret.status)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Create Return Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="p-4 border-b border-red-900/30 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-amber-100">Buat Retur Penjualan</h2>
              <button onClick={() => setShowModal(false)} className="p-1 hover:bg-red-900/20 rounded"><X className="h-5 w-5" /></button>
            </div>
            <form onSubmit={handleSubmit} className="p-4 space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Pilih Transaksi *</label>
                <select value={formData.transaction_id} onChange={(e) => handleSelectSale(e.target.value)}
                  className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" required>
                  <option value="">Pilih faktur penjualan</option>
                  {sales.map(sale => (
                    <option key={sale.id} value={sale.id}>{sale.invoice_number || sale.transaction_number} - {sale.customer_name || 'Umum'}</option>
                  ))}
                </select>
              </div>

              {selectedSale && (
                <>
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">Alasan Retur *</label>
                    <textarea value={formData.reason} onChange={(e) => setFormData({ ...formData, reason: e.target.value })}
                      className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" rows={2}
                      placeholder="Contoh: Barang rusak, tidak sesuai, dll" required />
                  </div>

                  <div className="border border-red-900/30 rounded-lg overflow-hidden">
                    <div className="bg-red-900/20 px-4 py-2">
                      <span className="font-medium text-amber-200">Item yang Diretur</span>
                    </div>
                    <table className="w-full">
                      <thead className="bg-red-900/10">
                        <tr>
                          <th className="px-4 py-2 text-left text-xs text-gray-400">PRODUK</th>
                          <th className="px-4 py-2 text-center text-xs text-gray-400">DIBELI</th>
                          <th className="px-4 py-2 text-center text-xs text-gray-400">QTY RETUR</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-red-900/20">
                        {formData.items.map((item, idx) => (
                          <tr key={idx}>
                            <td className="px-4 py-2 text-gray-200">{item.product_name}</td>
                            <td className="px-4 py-2 text-center text-gray-400">{item.sold_qty}</td>
                            <td className="px-4 py-2">
                              <input
                                type="number"
                                min="0"
                                max={item.sold_qty}
                                value={item.return_qty}
                                onChange={(e) => updateReturnQty(idx, Number(e.target.value))}
                                className="w-full px-2 py-1 bg-[#0a0608] border border-red-900/30 rounded text-center text-sm"
                              />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </>
              )}

              <div className="flex justify-end gap-3 pt-4 border-t border-red-900/30">
                <button type="button" onClick={() => setShowModal(false)} className="px-4 py-2 border border-red-900/30 rounded-lg">Batal</button>
                <button type="submit" className="px-4 py-2 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg">Simpan Retur</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default SalesReturns;
