import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Search, Eye, Printer, Loader2, Calendar, FileText, Download, Filter } from 'lucide-react';
import { toast } from 'sonner';

const PurchaseList = () => {
  const { api } = useAuth();
  const [purchases, setPurchases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [selectedPurchase, setSelectedPurchase] = useState(null);
  const [showDetail, setShowDetail] = useState(false);

  const loadPurchases = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        ...(searchTerm && { search: searchTerm }),
        ...(statusFilter && { status: statusFilter }),
        ...(dateFrom && { date_from: dateFrom }),
        ...(dateTo && { date_to: dateTo })
      });
      const res = await api(`/api/purchase/orders?${params}`);
      if (res.ok) {
        const data = await res.json();
        setPurchases(data.items || data || []);
      }
    } catch (err) {
      toast.error('Gagal memuat data');
    } finally {
      setLoading(false);
    }
  }, [api, searchTerm, statusFilter, dateFrom, dateTo]);

  useEffect(() => {
    loadPurchases();
  }, [loadPurchases]);

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

  const handleViewDetail = (purchase) => {
    setSelectedPurchase(purchase);
    setShowDetail(true);
  };

  const exportToExcel = async () => {
    toast.info('Fitur export akan segera tersedia');
  };

  return (
    <div className="space-y-4" data-testid="purchase-list-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Daftar Pembelian</h1>
          <p className="text-gray-400 text-sm">Riwayat semua transaksi pembelian</p>
        </div>
        <button onClick={exportToExcel}
          className="px-4 py-2 bg-green-600/20 text-green-400 rounded-lg flex items-center gap-2 hover:bg-green-600/30">
          <Download className="h-4 w-4" /> Export Excel
        </button>
      </div>

      {/* Filters */}
      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="relative">
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
          <input
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
            className="px-4 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200"
            placeholder="Dari Tanggal"
          />
          <input
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
            className="px-4 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200"
            placeholder="Sampai Tanggal"
          />
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
          <p className="text-gray-400 text-sm">Total PO</p>
          <p className="text-2xl font-bold text-amber-200">{purchases.length}</p>
        </div>
        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
          <p className="text-gray-400 text-sm">Menunggu</p>
          <p className="text-2xl font-bold text-blue-400">{purchases.filter(p => p.status === 'submitted').length}</p>
        </div>
        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
          <p className="text-gray-400 text-sm">Diterima</p>
          <p className="text-2xl font-bold text-green-400">{purchases.filter(p => p.status === 'received').length}</p>
        </div>
        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
          <p className="text-gray-400 text-sm">Total Nilai</p>
          <p className="text-xl font-bold text-green-400">
            Rp {purchases.reduce((sum, p) => sum + (p.total || 0), 0).toLocaleString('id-ID')}
          </p>
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
              ) : purchases.length === 0 ? (
                <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-400">Belum ada data pembelian</td></tr>
              ) : purchases.map(purchase => (
                <tr key={purchase.id} className="hover:bg-red-900/10">
                  <td className="px-4 py-3">
                    <div className="font-medium text-amber-300 font-mono">{purchase.po_number}</div>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-400">
                    {new Date(purchase.created_at).toLocaleDateString('id-ID')}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-200">{purchase.supplier_name}</td>
                  <td className="px-4 py-3 text-sm text-right text-gray-300">{purchase.items?.length || 0} item</td>
                  <td className="px-4 py-3 text-sm text-right text-green-400 font-medium">
                    Rp {(purchase.total || 0).toLocaleString('id-ID')}
                  </td>
                  <td className="px-4 py-3 text-center">{getStatusBadge(purchase.status)}</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-center gap-1">
                      <button 
                        onClick={() => handleViewDetail(purchase)}
                        className="p-1.5 hover:bg-blue-600/20 rounded text-blue-400"
                        title="Lihat Detail"
                      >
                        <Eye className="h-4 w-4" />
                      </button>
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

      {/* Detail Modal */}
      {showDetail && selectedPurchase && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
            <div className="p-4 border-b border-red-900/30 flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold text-amber-100">Detail Pembelian</h2>
                <p className="text-sm text-gray-400">{selectedPurchase.po_number}</p>
              </div>
              <button onClick={() => setShowDetail(false)} className="p-2 hover:bg-red-900/20 rounded text-gray-400">✕</button>
            </div>
            <div className="p-4 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-400">Supplier</p>
                  <p className="text-gray-200">{selectedPurchase.supplier_name}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-400">Tanggal</p>
                  <p className="text-gray-200">{new Date(selectedPurchase.created_at).toLocaleDateString('id-ID')}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-400">Status</p>
                  {getStatusBadge(selectedPurchase.status)}
                </div>
                <div>
                  <p className="text-sm text-gray-400">Total</p>
                  <p className="text-green-400 font-bold">Rp {(selectedPurchase.total || 0).toLocaleString('id-ID')}</p>
                </div>
              </div>
              
              <div className="border-t border-red-900/30 pt-4">
                <h3 className="text-sm font-semibold text-amber-200 mb-2">Item Pembelian</h3>
                <table className="w-full">
                  <thead className="bg-red-900/20">
                    <tr>
                      <th className="px-3 py-2 text-left text-xs text-gray-400">PRODUK</th>
                      <th className="px-3 py-2 text-center text-xs text-gray-400">QTY</th>
                      <th className="px-3 py-2 text-right text-xs text-gray-400">HARGA</th>
                      <th className="px-3 py-2 text-right text-xs text-gray-400">SUBTOTAL</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-red-900/20">
                    {selectedPurchase.items?.map((item, idx) => (
                      <tr key={idx}>
                        <td className="px-3 py-2 text-gray-200">{item.product_name}</td>
                        <td className="px-3 py-2 text-center text-gray-400">{item.quantity}</td>
                        <td className="px-3 py-2 text-right text-gray-400">Rp {(item.unit_cost || 0).toLocaleString('id-ID')}</td>
                        <td className="px-3 py-2 text-right text-green-400">Rp {((item.quantity || 0) * (item.unit_cost || 0)).toLocaleString('id-ID')}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PurchaseList;
