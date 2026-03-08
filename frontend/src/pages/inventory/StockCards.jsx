import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Search, Package, Loader2, TrendingUp, TrendingDown, Download, Filter } from 'lucide-react';
import { toast } from 'sonner';

const StockCards = () => {
  const { api } = useAuth();
  const [stocks, setStocks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [branchFilter, setBranchFilter] = useState('');
  const [branches, setBranches] = useState([]);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [showDetail, setShowDetail] = useState(false);
  const [movements, setMovements] = useState([]);

  const loadStocks = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        ...(searchTerm && { search: searchTerm }),
        ...(branchFilter && { branch_id: branchFilter })
      });
      const res = await api(`/api/inventory/stock?${params}`);
      if (res.ok) {
        const data = await res.json();
        setStocks(data.items || data || []);
      }
    } catch (err) {
      toast.error('Gagal memuat data');
    } finally {
      setLoading(false);
    }
  }, [api, searchTerm, branchFilter]);

  const loadBranches = useCallback(async () => {
    try {
      const res = await api('/api/branches');
      if (res.ok) {
        const data = await res.json();
        setBranches(data.items || data || []);
      }
    } catch (err) { console.error('Error loading branches'); }
  }, [api]);

  useEffect(() => {
    loadStocks();
    loadBranches();
  }, [loadStocks, loadBranches]);

  const viewMovements = async (product) => {
    setSelectedProduct(product);
    try {
      const res = await api(`/api/inventory/movements?product_id=${product.product_id}`);
      if (res.ok) {
        const data = await res.json();
        setMovements(data.items || data || []);
      }
    } catch (err) { toast.error('Gagal memuat history'); }
    setShowDetail(true);
  };

  const getStockStatus = (stock) => {
    const qty = stock.quantity || 0;
    const min = stock.min_stock || 10;
    if (qty <= 0) return { text: 'Habis', color: 'bg-red-600/20 text-red-400' };
    if (qty <= min) return { text: 'Kritis', color: 'bg-yellow-600/20 text-yellow-400' };
    return { text: 'Aman', color: 'bg-green-600/20 text-green-400' };
  };

  return (
    <div className="space-y-4" data-testid="stock-cards-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Kartu Stok</h1>
          <p className="text-gray-400 text-sm">Pantau stok barang dan pergerakan</p>
        </div>
        <button className="px-4 py-2 bg-green-600/20 text-green-400 rounded-lg flex items-center gap-2">
          <Download className="h-4 w-4" /> Export
        </button>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
          <p className="text-gray-400 text-sm">Total Produk</p>
          <p className="text-2xl font-bold text-amber-200">{stocks.length}</p>
        </div>
        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
          <p className="text-gray-400 text-sm">Stok Aman</p>
          <p className="text-2xl font-bold text-green-400">
            {stocks.filter(s => getStockStatus(s).text === 'Aman').length}
          </p>
        </div>
        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
          <p className="text-gray-400 text-sm">Stok Kritis</p>
          <p className="text-2xl font-bold text-yellow-400">
            {stocks.filter(s => getStockStatus(s).text === 'Kritis').length}
          </p>
        </div>
        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
          <p className="text-gray-400 text-sm">Stok Habis</p>
          <p className="text-2xl font-bold text-red-400">
            {stocks.filter(s => getStockStatus(s).text === 'Habis').length}
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Cari produk..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200"
            />
          </div>
          <select
            value={branchFilter}
            onChange={(e) => setBranchFilter(e.target.value)}
            className="px-4 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200"
          >
            <option value="">Semua Cabang</option>
            {branches.map(b => (
              <option key={b.id} value={b.id}>{b.name}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-red-900/20">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">KODE</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">NAMA PRODUK</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">CABANG</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-amber-200">STOK</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-amber-200">MIN. STOK</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">STATUS</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">AKSI</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-red-900/20">
              {loading ? (
                <tr><td colSpan={7} className="px-4 py-8 text-center"><Loader2 className="h-8 w-8 animate-spin mx-auto text-amber-400" /></td></tr>
              ) : stocks.length === 0 ? (
                <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-400">Belum ada data stok</td></tr>
              ) : stocks.map((stock, idx) => {
                const status = getStockStatus(stock);
                return (
                  <tr key={idx} className="hover:bg-red-900/10">
                    <td className="px-4 py-3 text-sm font-mono text-amber-300">{stock.product_code || '-'}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <Package className="h-4 w-4 text-gray-500" />
                        <span className="font-medium text-gray-200">{stock.product_name}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-400">{stock.branch_name || '-'}</td>
                    <td className="px-4 py-3 text-sm text-right font-medium text-gray-200">{stock.quantity || 0}</td>
                    <td className="px-4 py-3 text-sm text-right text-gray-400">{stock.min_stock || 10}</td>
                    <td className="px-4 py-3 text-center">
                      <span className={`px-2 py-1 rounded-full text-xs ${status.color}`}>{status.text}</span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-center">
                        <button 
                          onClick={() => viewMovements(stock)}
                          className="px-3 py-1 bg-blue-600/20 text-blue-400 rounded text-sm hover:bg-blue-600/30"
                        >
                          History
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Movement History Modal */}
      {showDetail && selectedProduct && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-2xl max-h-[80vh] overflow-y-auto">
            <div className="p-4 border-b border-red-900/30 flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold text-amber-100">History Pergerakan Stok</h2>
                <p className="text-sm text-gray-400">{selectedProduct.product_name}</p>
              </div>
              <button onClick={() => setShowDetail(false)} className="p-2 hover:bg-red-900/20 rounded text-gray-400">✕</button>
            </div>
            <div className="p-4">
              <table className="w-full">
                <thead className="bg-red-900/20">
                  <tr>
                    <th className="px-3 py-2 text-left text-xs text-gray-400">TANGGAL</th>
                    <th className="px-3 py-2 text-center text-xs text-gray-400">TIPE</th>
                    <th className="px-3 py-2 text-center text-xs text-gray-400">QTY</th>
                    <th className="px-3 py-2 text-left text-xs text-gray-400">REFERENSI</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-red-900/20">
                  {movements.length === 0 ? (
                    <tr><td colSpan={4} className="px-3 py-4 text-center text-gray-400">Belum ada history</td></tr>
                  ) : movements.map((m, idx) => (
                    <tr key={idx}>
                      <td className="px-3 py-2 text-sm text-gray-400">{new Date(m.created_at).toLocaleDateString('id-ID')}</td>
                      <td className="px-3 py-2 text-center">
                        <span className={`flex items-center justify-center gap-1 text-sm ${
                          m.movement_type === 'stock_in' ? 'text-green-400' : 'text-red-400'
                        }`}>
                          {m.movement_type === 'stock_in' ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                          {m.movement_type === 'stock_in' ? 'Masuk' : 'Keluar'}
                        </span>
                      </td>
                      <td className="px-3 py-2 text-center text-gray-200">{m.quantity}</td>
                      <td className="px-3 py-2 text-sm text-gray-400">{m.notes || m.reference_type || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default StockCards;
