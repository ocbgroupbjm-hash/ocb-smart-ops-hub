import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Search, Eye, Printer, Loader2, Download, Filter, ShoppingBag } from 'lucide-react';
import { toast } from 'sonner';

const SalesList = () => {
  const { api } = useAuth();
  const [sales, setSales] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [selectedSale, setSelectedSale] = useState(null);
  const [showDetail, setShowDetail] = useState(false);

  const loadSales = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        ...(searchTerm && { search: searchTerm }),
        ...(statusFilter && { status: statusFilter }),
        ...(dateFrom && { date_from: dateFrom }),
        ...(dateTo && { date_to: dateTo })
      });
      const res = await api(`/api/pos/transactions?${params}`);
      if (res.ok) {
        const data = await res.json();
        setSales(data.items || data || []);
      }
    } catch (err) {
      toast.error('Gagal memuat data');
    } finally {
      setLoading(false);
    }
  }, [api, searchTerm, statusFilter, dateFrom, dateTo]);

  useEffect(() => {
    loadSales();
  }, [loadSales]);

  const getStatusBadge = (status) => {
    const badges = {
      completed: 'bg-green-600/20 text-green-400',
      pending: 'bg-yellow-600/20 text-yellow-400',
      cancelled: 'bg-red-600/20 text-red-400',
      refunded: 'bg-purple-600/20 text-purple-400'
    };
    const labels = {
      completed: 'Selesai',
      pending: 'Pending',
      cancelled: 'Dibatalkan',
      refunded: 'Refund'
    };
    return (
      <span className={`px-2 py-1 rounded-full text-xs ${badges[status] || badges.completed}`}>
        {labels[status] || status}
      </span>
    );
  };

  const handleViewDetail = (sale) => {
    setSelectedSale(sale);
    setShowDetail(true);
  };

  const exportToExcel = async () => {
    toast.info('Fitur export akan segera tersedia');
  };

  return (
    <div className="space-y-4" data-testid="sales-list-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Daftar Penjualan</h1>
          <p className="text-gray-400 text-sm">Riwayat semua transaksi penjualan</p>
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
              placeholder="Cari no. faktur, pelanggan..."
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
            <option value="completed">Selesai</option>
            <option value="pending">Pending</option>
            <option value="cancelled">Dibatalkan</option>
            <option value="refunded">Refund</option>
          </select>
          <input
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
            className="px-4 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200"
          />
          <input
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
            className="px-4 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200"
          />
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
          <p className="text-gray-400 text-sm">Total Transaksi</p>
          <p className="text-2xl font-bold text-amber-200">{sales.length}</p>
        </div>
        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
          <p className="text-gray-400 text-sm">Selesai</p>
          <p className="text-2xl font-bold text-green-400">{sales.filter(s => s.status === 'completed').length}</p>
        </div>
        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
          <p className="text-gray-400 text-sm">Pending</p>
          <p className="text-2xl font-bold text-yellow-400">{sales.filter(s => s.status === 'pending').length}</p>
        </div>
        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
          <p className="text-gray-400 text-sm">Total Nilai</p>
          <p className="text-xl font-bold text-green-400">
            Rp {sales.reduce((sum, s) => sum + (s.total || 0), 0).toLocaleString('id-ID')}
          </p>
        </div>
      </div>

      {/* Table */}
      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-red-900/20">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">NO. FAKTUR</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">TANGGAL</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">PELANGGAN</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-amber-200">ITEMS</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-amber-200">TOTAL</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">PEMBAYARAN</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">STATUS</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">AKSI</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-red-900/20">
              {loading ? (
                <tr><td colSpan={8} className="px-4 py-8 text-center"><Loader2 className="h-8 w-8 animate-spin mx-auto text-amber-400" /></td></tr>
              ) : sales.length === 0 ? (
                <tr><td colSpan={8} className="px-4 py-8 text-center text-gray-400">Belum ada data penjualan</td></tr>
              ) : sales.map(sale => (
                <tr key={sale.id} className="hover:bg-red-900/10">
                  <td className="px-4 py-3">
                    <div className="font-medium text-amber-300 font-mono">{sale.invoice_number || sale.transaction_number}</div>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-400">
                    {new Date(sale.created_at).toLocaleDateString('id-ID')}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-200">{sale.customer_name || 'Umum'}</td>
                  <td className="px-4 py-3 text-sm text-right text-gray-300">{sale.items?.length || 0} item</td>
                  <td className="px-4 py-3 text-sm text-right text-green-400 font-medium">
                    Rp {(sale.total || 0).toLocaleString('id-ID')}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className="text-xs text-gray-400">{sale.payment_method || 'Tunai'}</span>
                  </td>
                  <td className="px-4 py-3 text-center">{getStatusBadge(sale.status)}</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-center gap-1">
                      <button 
                        onClick={() => handleViewDetail(sale)}
                        className="p-1.5 hover:bg-blue-600/20 rounded text-blue-400"
                      >
                        <Eye className="h-4 w-4" />
                      </button>
                      <button className="p-1.5 hover:bg-gray-600/20 rounded text-gray-400">
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
      {showDetail && selectedSale && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
            <div className="p-4 border-b border-red-900/30 flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold text-amber-100">Detail Penjualan</h2>
                <p className="text-sm text-gray-400">{selectedSale.invoice_number || selectedSale.transaction_number}</p>
              </div>
              <button onClick={() => setShowDetail(false)} className="p-2 hover:bg-red-900/20 rounded text-gray-400">✕</button>
            </div>
            <div className="p-4 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-400">Pelanggan</p>
                  <p className="text-gray-200">{selectedSale.customer_name || 'Umum'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-400">Tanggal</p>
                  <p className="text-gray-200">{new Date(selectedSale.created_at).toLocaleDateString('id-ID')}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-400">Status</p>
                  {getStatusBadge(selectedSale.status)}
                </div>
                <div>
                  <p className="text-sm text-gray-400">Total</p>
                  <p className="text-green-400 font-bold">Rp {(selectedSale.total || 0).toLocaleString('id-ID')}</p>
                </div>
              </div>
              
              <div className="border-t border-red-900/30 pt-4">
                <h3 className="text-sm font-semibold text-amber-200 mb-2">Item Penjualan</h3>
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
                    {selectedSale.items?.map((item, idx) => (
                      <tr key={idx}>
                        <td className="px-3 py-2 text-gray-200">{item.product_name}</td>
                        <td className="px-3 py-2 text-center text-gray-400">{item.quantity}</td>
                        <td className="px-3 py-2 text-right text-gray-400">Rp {(item.price || 0).toLocaleString('id-ID')}</td>
                        <td className="px-3 py-2 text-right text-green-400">Rp {(item.subtotal || 0).toLocaleString('id-ID')}</td>
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

export default SalesList;
