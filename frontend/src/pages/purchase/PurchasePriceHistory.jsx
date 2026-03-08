import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Search, TrendingUp, TrendingDown, Loader2, Calendar, Package } from 'lucide-react';
import { toast } from 'sonner';

const PurchasePriceHistory = () => {
  const { api } = useAuth();
  const [priceHistory, setPriceHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [products, setProducts] = useState([]);
  const [selectedProduct, setSelectedProduct] = useState('');

  const loadPriceHistory = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        ...(searchTerm && { search: searchTerm }),
        ...(selectedProduct && { product_id: selectedProduct })
      });
      const res = await api(`/api/purchase/price-history?${params}`);
      if (res.ok) {
        const data = await res.json();
        setPriceHistory(data.items || data || []);
      }
    } catch (err) {
      toast.error('Gagal memuat data');
    } finally {
      setLoading(false);
    }
  }, [api, searchTerm, selectedProduct]);

  const loadProducts = useCallback(async () => {
    try {
      const res = await api('/api/products');
      if (res.ok) {
        const data = await res.json();
        setProducts(data.items || data || []);
      }
    } catch (err) {
      console.error('Error loading products');
    }
  }, [api]);

  useEffect(() => {
    loadPriceHistory();
    loadProducts();
  }, [loadPriceHistory, loadProducts]);

  const getPriceChange = (current, previous) => {
    if (!previous || previous === 0) return null;
    const change = ((current - previous) / previous) * 100;
    return change;
  };

  return (
    <div className="space-y-4" data-testid="price-history-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">History Harga Beli</h1>
          <p className="text-gray-400 text-sm">Riwayat perubahan harga beli dari supplier</p>
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
            value={selectedProduct}
            onChange={(e) => setSelectedProduct(e.target.value)}
            className="px-4 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200"
          >
            <option value="">Semua Produk</option>
            {products.map(p => (
              <option key={p.id} value={p.id}>{p.name}</option>
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
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">PRODUK</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">SUPPLIER</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-amber-200">HARGA LAMA</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-amber-200">HARGA BARU</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">PERUBAHAN</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">TANGGAL</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">NO. PO</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-red-900/20">
              {loading ? (
                <tr><td colSpan={7} className="px-4 py-8 text-center"><Loader2 className="h-8 w-8 animate-spin mx-auto text-amber-400" /></td></tr>
              ) : priceHistory.length === 0 ? (
                <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-400">Belum ada riwayat harga</td></tr>
              ) : priceHistory.map((item, idx) => {
                const change = getPriceChange(item.new_price, item.old_price);
                return (
                  <tr key={idx} className="hover:bg-red-900/10">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <Package className="h-4 w-4 text-gray-500" />
                        <span className="font-medium text-gray-200">{item.product_name}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-400">{item.supplier_name}</td>
                    <td className="px-4 py-3 text-sm text-right text-gray-400">
                      Rp {(item.old_price || 0).toLocaleString('id-ID')}
                    </td>
                    <td className="px-4 py-3 text-sm text-right font-medium text-green-400">
                      Rp {(item.new_price || 0).toLocaleString('id-ID')}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {change !== null ? (
                        <span className={`flex items-center justify-center gap-1 text-sm ${
                          change > 0 ? 'text-red-400' : change < 0 ? 'text-green-400' : 'text-gray-400'
                        }`}>
                          {change > 0 ? <TrendingUp className="h-4 w-4" /> : change < 0 ? <TrendingDown className="h-4 w-4" /> : null}
                          {change > 0 ? '+' : ''}{change.toFixed(1)}%
                        </span>
                      ) : (
                        <span className="text-gray-500">-</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-400">
                      {new Date(item.created_at).toLocaleDateString('id-ID')}
                    </td>
                    <td className="px-4 py-3 text-sm font-mono text-amber-300">{item.po_number}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default PurchasePriceHistory;
