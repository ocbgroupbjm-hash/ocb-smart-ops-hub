/**
 * Quick Stock View - iPOS Style
 * 
 * Tampilan stok yang sederhana dan cepat:
 * - Search produk di kiri
 * - Detail stok + movements di kanan
 * - No popup, no modal, single screen
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { 
  Search, Package, Loader2, TrendingUp, TrendingDown, 
  AlertTriangle, CheckCircle, XCircle, Box, ArrowRight,
  Keyboard
} from 'lucide-react';
import { toast } from 'sonner';

const formatNumber = (num) => (num || 0).toLocaleString('id-ID');

const QuickStock = () => {
  const { api } = useAuth();
  const searchRef = useRef(null);
  
  const [loading, setLoading] = useState(true);
  const [products, setProducts] = useState([]);
  const [searchText, setSearchText] = useState('');
  const [filteredProducts, setFilteredProducts] = useState([]);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [movements, setMovements] = useState([]);
  const [loadingMovements, setLoadingMovements] = useState(false);
  
  // Load all products with stock
  useEffect(() => {
    const loadProducts = async () => {
      try {
        const res = await api('/api/inventory/stock?limit=1000');
        if (res.ok) {
          const data = await res.json();
          const items = data.items || data || [];
          setProducts(items);
          setFilteredProducts(items.slice(0, 20));
        }
      } catch (err) {
        toast.error('Gagal memuat data stok');
      } finally {
        setLoading(false);
      }
    };
    loadProducts();
  }, [api]);
  
  // Focus search on load
  useEffect(() => {
    if (!loading && searchRef.current) {
      searchRef.current.focus();
    }
  }, [loading]);
  
  // Filter products
  useEffect(() => {
    if (!searchText) {
      setFilteredProducts(products.slice(0, 20));
      setSelectedIndex(0);
      return;
    }
    
    const lower = searchText.toLowerCase();
    const filtered = products.filter(p => 
      p.product_name?.toLowerCase().includes(lower) ||
      p.product_code?.toLowerCase().includes(lower)
    ).slice(0, 20);
    
    setFilteredProducts(filtered);
    setSelectedIndex(0);
  }, [searchText, products]);
  
  // Load movements when product selected
  const loadMovements = useCallback(async (product) => {
    if (!product) return;
    
    setLoadingMovements(true);
    try {
      const res = await api(`/api/inventory/movements?product_id=${product.product_id}&limit=50`);
      if (res.ok) {
        const data = await res.json();
        setMovements(data.items || data || []);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingMovements(false);
    }
  }, [api]);
  
  // Select product
  const selectProduct = useCallback((product) => {
    setSelectedProduct(product);
    loadMovements(product);
  }, [loadMovements]);
  
  // Keyboard navigation
  const handleKeyDown = (e) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex(prev => Math.min(prev + 1, filteredProducts.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex(prev => Math.max(prev - 1, 0));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (filteredProducts[selectedIndex]) {
        selectProduct(filteredProducts[selectedIndex]);
      }
    } else if (e.key === 'Escape') {
      setSearchText('');
      setSelectedProduct(null);
      setMovements([]);
    }
  };
  
  // Auto-select when navigating
  useEffect(() => {
    if (filteredProducts[selectedIndex]) {
      selectProduct(filteredProducts[selectedIndex]);
    }
  }, [selectedIndex, filteredProducts, selectProduct]);
  
  // Get stock status
  const getStatus = (qty, min = 10) => {
    if (qty <= 0) return { icon: XCircle, text: 'Habis', color: 'text-red-400', bg: 'bg-red-900/30' };
    if (qty <= min) return { icon: AlertTriangle, text: 'Kritis', color: 'text-yellow-400', bg: 'bg-yellow-900/30' };
    return { icon: CheckCircle, text: 'Aman', color: 'text-green-400', bg: 'bg-green-900/30' };
  };
  
  // Calculate stats
  const stats = {
    total: products.length,
    safe: products.filter(p => (p.quantity || 0) > (p.min_stock || 10)).length,
    critical: products.filter(p => (p.quantity || 0) > 0 && (p.quantity || 0) <= (p.min_stock || 10)).length,
    empty: products.filter(p => (p.quantity || 0) <= 0).length
  };
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-4rem)] bg-[#0a0608]">
        <Loader2 className="h-12 w-12 animate-spin text-amber-500" />
      </div>
    );
  }
  
  return (
    <div className="h-[calc(100vh-4rem)] flex bg-[#0a0608]" data-testid="quick-stock-screen">
      {/* Left Panel - Product List */}
      <div className="w-96 border-r border-red-900/30 flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-red-900/30">
          <h1 className="text-xl font-bold text-amber-100 flex items-center gap-2">
            <Box className="h-6 w-6 text-amber-400" />
            Quick Stock
          </h1>
          <div className="flex items-center gap-2 mt-1 text-xs text-gray-500">
            <Keyboard className="h-3 w-3" />
            <span>Arrow = Navigasi | Enter = Pilih | Esc = Reset</span>
          </div>
        </div>
        
        {/* Search */}
        <div className="p-3 border-b border-red-900/30">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
            <input
              ref={searchRef}
              type="text"
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Cari kode / nama barang..."
              className="w-full pl-10 pr-4 py-2.5 bg-[#1a1214] border border-red-900/30 rounded-lg text-white placeholder-gray-500 focus:border-amber-500 focus:outline-none"
              data-testid="stock-search-input"
            />
          </div>
        </div>
        
        {/* Stats Bar */}
        <div className="grid grid-cols-4 gap-1 p-2 bg-[#1a1214]/50 border-b border-red-900/30 text-xs">
          <div className="text-center py-1">
            <div className="text-gray-400">Total</div>
            <div className="font-bold text-white">{stats.total}</div>
          </div>
          <div className="text-center py-1">
            <div className="text-green-400">Aman</div>
            <div className="font-bold text-green-400">{stats.safe}</div>
          </div>
          <div className="text-center py-1">
            <div className="text-yellow-400">Kritis</div>
            <div className="font-bold text-yellow-400">{stats.critical}</div>
          </div>
          <div className="text-center py-1">
            <div className="text-red-400">Habis</div>
            <div className="font-bold text-red-400">{stats.empty}</div>
          </div>
        </div>
        
        {/* Product List */}
        <div className="flex-1 overflow-y-auto">
          {filteredProducts.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <Package className="h-12 w-12 mx-auto mb-2 opacity-30" />
              <p>Tidak ada produk ditemukan</p>
            </div>
          ) : (
            filteredProducts.map((product, idx) => {
              const status = getStatus(product.quantity, product.min_stock);
              const isSelected = selectedProduct?.product_id === product.product_id;
              const isHighlighted = idx === selectedIndex;
              
              return (
                <button
                  key={product.product_id || idx}
                  onClick={() => {
                    setSelectedIndex(idx);
                    selectProduct(product);
                  }}
                  className={`w-full p-3 text-left border-b border-red-900/20 transition-colors ${
                    isSelected ? 'bg-amber-600/20 border-l-4 border-l-amber-500' : 
                    isHighlighted ? 'bg-red-900/20' : 'hover:bg-red-900/10'
                  }`}
                  data-testid={`product-item-${product.product_id}`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-white truncate">{product.product_name}</div>
                      <div className="text-xs text-gray-500 font-mono">{product.product_code}</div>
                    </div>
                    <div className="text-right ml-2">
                      <div className={`text-lg font-bold ${status.color}`}>
                        {formatNumber(product.quantity)}
                      </div>
                      <div className={`text-xs px-1.5 py-0.5 rounded ${status.bg} ${status.color}`}>
                        {status.text}
                      </div>
                    </div>
                  </div>
                </button>
              );
            })
          )}
        </div>
      </div>
      
      {/* Right Panel - Stock Detail */}
      <div className="flex-1 flex flex-col">
        {!selectedProduct ? (
          <div className="flex-1 flex items-center justify-center text-gray-500">
            <div className="text-center">
              <ArrowRight className="h-16 w-16 mx-auto mb-4 opacity-20" />
              <p className="text-lg">Pilih produk di sebelah kiri</p>
              <p className="text-sm mt-2">atau ketik untuk mencari</p>
            </div>
          </div>
        ) : (
          <>
            {/* Product Header */}
            <div className="p-6 bg-[#1a1214] border-b border-red-900/30">
              <div className="flex items-start justify-between">
                <div>
                  <div className="text-sm text-amber-400 font-mono">{selectedProduct.product_code}</div>
                  <h2 className="text-2xl font-bold text-white mt-1">{selectedProduct.product_name}</h2>
                  <div className="text-sm text-gray-400 mt-1">
                    {selectedProduct.branch_name || 'Semua Cabang'} | Min. Stok: {selectedProduct.min_stock || 10}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm text-gray-400">Stok Saat Ini</div>
                  <div className={`text-4xl font-bold ${getStatus(selectedProduct.quantity).color}`}>
                    {formatNumber(selectedProduct.quantity)}
                  </div>
                  <div className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm mt-2 ${getStatus(selectedProduct.quantity).bg} ${getStatus(selectedProduct.quantity).color}`}>
                    {React.createElement(getStatus(selectedProduct.quantity).icon, { className: "h-4 w-4" })}
                    {getStatus(selectedProduct.quantity).text}
                  </div>
                </div>
              </div>
            </div>
            
            {/* Movement History */}
            <div className="flex-1 overflow-hidden flex flex-col">
              <div className="p-4 bg-[#0a0608] border-b border-red-900/30">
                <h3 className="font-semibold text-amber-200">Riwayat Pergerakan Stok</h3>
              </div>
              
              <div className="flex-1 overflow-y-auto">
                {loadingMovements ? (
                  <div className="p-8 text-center">
                    <Loader2 className="h-8 w-8 animate-spin mx-auto text-amber-400" />
                  </div>
                ) : movements.length === 0 ? (
                  <div className="p-8 text-center text-gray-500">
                    <TrendingUp className="h-12 w-12 mx-auto mb-2 opacity-30" />
                    <p>Belum ada riwayat pergerakan</p>
                  </div>
                ) : (
                  <table className="w-full">
                    <thead className="bg-red-900/20 sticky top-0">
                      <tr className="text-xs text-gray-400">
                        <th className="px-4 py-2 text-left">Tanggal</th>
                        <th className="px-4 py-2 text-center">Tipe</th>
                        <th className="px-4 py-2 text-center">Masuk</th>
                        <th className="px-4 py-2 text-center">Keluar</th>
                        <th className="px-4 py-2 text-left">Referensi</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-red-900/20">
                      {movements.map((m, idx) => {
                        const isIn = m.movement_type === 'stock_in' || m.quantity > 0 && m.movement_type?.includes('in');
                        const qty = Math.abs(m.quantity || 0);
                        
                        return (
                          <tr key={idx} className="hover:bg-red-900/10">
                            <td className="px-4 py-2 text-sm text-gray-400">
                              {new Date(m.created_at).toLocaleDateString('id-ID', {
                                day: '2-digit',
                                month: 'short',
                                year: 'numeric'
                              })}
                            </td>
                            <td className="px-4 py-2 text-center">
                              <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs ${
                                isIn ? 'bg-green-900/30 text-green-400' : 'bg-red-900/30 text-red-400'
                              }`}>
                                {isIn ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                                {isIn ? 'Masuk' : 'Keluar'}
                              </span>
                            </td>
                            <td className="px-4 py-2 text-center font-mono">
                              {isIn ? (
                                <span className="text-green-400">+{formatNumber(qty)}</span>
                              ) : (
                                <span className="text-gray-600">-</span>
                              )}
                            </td>
                            <td className="px-4 py-2 text-center font-mono">
                              {!isIn ? (
                                <span className="text-red-400">-{formatNumber(qty)}</span>
                              ) : (
                                <span className="text-gray-600">-</span>
                              )}
                            </td>
                            <td className="px-4 py-2 text-sm text-gray-400 truncate max-w-xs">
                              {m.reference_number || m.notes || m.reference_type || '-'}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default QuickStock;
