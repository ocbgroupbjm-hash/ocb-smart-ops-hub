/**
 * Quick Purchase Screen - iPOS Style
 * 
 * Shortcut Keyboard:
 * - Enter = Tambah item ke cart
 * - F1 = Simpan PO
 * - Esc = Batal / Hapus cart
 * - Delete = Hapus item aktif
 * - Arrow Up/Down = Navigasi item
 * 
 * Flow: Single screen, minim klik, keyboard-driven
 */

import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { 
  Search, ShoppingCart, Trash2, Plus, Minus, Package, 
  Loader2, X, Check, Keyboard, ArrowUp, ArrowDown, 
  AlertCircle, Truck, Save, Building2
} from 'lucide-react';
import { toast } from 'sonner';

const formatRupiah = (num) => `Rp ${(num || 0).toLocaleString('id-ID')}`;

const QuickPurchase = () => {
  const { api } = useAuth();
  const searchInputRef = useRef(null);
  
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  
  // Master data
  const [products, setProducts] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  
  // Search state
  const [searchText, setSearchText] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [showResults, setShowResults] = useState(false);
  const [selectedResultIndex, setSelectedResultIndex] = useState(0);
  
  // Cart state
  const [cart, setCart] = useState([]);
  const [selectedCartIndex, setSelectedCartIndex] = useState(-1);
  const [selectedSupplier, setSelectedSupplier] = useState(null);
  const [selectedWarehouse, setSelectedWarehouse] = useState(null);
  const [notes, setNotes] = useState('');
  
  // Load master data
  useEffect(() => {
    const loadData = async () => {
      try {
        const [prodRes, supRes, whRes] = await Promise.all([
          api('/api/products?limit=5000'),
          api('/api/suppliers'),
          api('/api/master/warehouses')
        ]);
        
        if (prodRes.ok) setProducts((await prodRes.json()).items || []);
        if (supRes.ok) setSuppliers((await supRes.json()).items || []);
        if (whRes.ok) {
          const whs = await whRes.json() || [];
          setWarehouses(whs);
          if (whs.length > 0) setSelectedWarehouse(whs[0]);
        }
      } catch (err) {
        console.error(err);
        toast.error('Gagal memuat data');
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [api]);
  
  // Focus search on load
  useEffect(() => {
    if (!loading && searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, [loading]);
  
  // Search products
  const handleSearch = useCallback((text) => {
    setSearchText(text);
    setSelectedResultIndex(0);
    
    if (text.length < 1) {
      setSearchResults([]);
      setShowResults(false);
      return;
    }
    
    const lowerText = text.toLowerCase().trim();
    
    // Priority: exact barcode > exact code > partial match
    const exactBarcode = products.find(p => p.barcode?.toLowerCase() === lowerText);
    if (exactBarcode) {
      addToCart(exactBarcode);
      setSearchText('');
      setShowResults(false);
      return;
    }
    
    const exactCode = products.find(p => p.code?.toLowerCase() === lowerText);
    if (exactCode) {
      addToCart(exactCode);
      setSearchText('');
      setShowResults(false);
      return;
    }
    
    // Show dropdown for partial matches
    const results = products.filter(p => 
      p.name?.toLowerCase().includes(lowerText) ||
      p.code?.toLowerCase().includes(lowerText) ||
      p.barcode?.toLowerCase().includes(lowerText)
    ).slice(0, 10);
    
    setSearchResults(results);
    setShowResults(results.length > 0);
  }, [products]);
  
  // Add to cart
  const addToCart = useCallback((product) => {
    setCart(prev => {
      const existing = prev.find(item => item.product_id === product.id);
      if (existing) {
        return prev.map(item => 
          item.product_id === product.id 
            ? { ...item, qty: item.qty + 1, subtotal: (item.qty + 1) * item.unit_cost }
            : item
        );
      }
      return [...prev, {
        product_id: product.id,
        product_code: product.code || '-',
        product_name: product.name,
        unit: product.unit || 'pcs',
        unit_cost: product.cost_price || 0,
        qty: 1,
        discount_percent: 0,
        subtotal: product.cost_price || 0
      }];
    });
    
    toast.success(`+ ${product.name}`, { duration: 1000 });
    
    setSearchText('');
    setShowResults(false);
    setSelectedResultIndex(0);
    if (searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, []);
  
  // Select item from search results
  const selectSearchResult = useCallback((index) => {
    if (searchResults[index]) {
      addToCart(searchResults[index]);
    }
  }, [searchResults, addToCart]);
  
  // Update qty
  const updateQty = useCallback((productId, newQty) => {
    if (newQty < 1) {
      removeFromCart(productId);
      return;
    }
    setCart(prev => prev.map(item => {
      if (item.product_id === productId) {
        return { ...item, qty: newQty, subtotal: newQty * item.unit_cost * (1 - item.discount_percent / 100) };
      }
      return item;
    }));
  }, []);
  
  // Update unit cost
  const updateUnitCost = useCallback((productId, newCost) => {
    setCart(prev => prev.map(item => {
      if (item.product_id === productId) {
        return { ...item, unit_cost: newCost, subtotal: item.qty * newCost * (1 - item.discount_percent / 100) };
      }
      return item;
    }));
  }, []);
  
  // Update discount
  const updateDiscount = useCallback((productId, discount) => {
    setCart(prev => prev.map(item => {
      if (item.product_id === productId) {
        return { ...item, discount_percent: discount, subtotal: item.qty * item.unit_cost * (1 - discount / 100) };
      }
      return item;
    }));
  }, []);
  
  // Remove from cart
  const removeFromCart = useCallback((productId) => {
    setCart(prev => prev.filter(item => item.product_id !== productId));
    setSelectedCartIndex(-1);
    toast.info('Item dihapus');
  }, []);
  
  // Clear cart
  const clearCart = useCallback(() => {
    setCart([]);
    setSelectedCartIndex(-1);
    setNotes('');
    toast.info('Cart dikosongkan');
    if (searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, []);
  
  // Calculate totals
  const totals = useMemo(() => {
    const subtotal = cart.reduce((sum, item) => sum + item.subtotal, 0);
    return {
      subtotal,
      total: subtotal,
      itemCount: cart.reduce((sum, item) => sum + item.qty, 0)
    };
  }, [cart]);
  
  // Save PO
  const savePO = async () => {
    if (cart.length === 0) {
      toast.error('Cart kosong!');
      return;
    }
    
    if (!selectedSupplier) {
      toast.error('Pilih supplier terlebih dahulu!');
      return;
    }
    
    setSaving(true);
    try {
      const payload = {
        supplier_id: selectedSupplier.id,
        warehouse_id: selectedWarehouse?.id || '',
        notes: notes,
        items: cart.map(item => ({
          product_id: item.product_id,
          product_name: item.product_name,
          quantity: item.qty,
          unit_cost: item.unit_cost,
          discount_percent: item.discount_percent,
          purchase_unit: item.unit,
          conversion_ratio: 1
        })),
        total_amount: totals.total
      };
      
      const res = await api('/api/purchase/orders', {
        method: 'POST',
        body: JSON.stringify(payload)
      });
      
      const data = await res.json();
      
      if (res.ok) {
        toast.success(
          <div>
            <div className="font-bold">PO Berhasil Dibuat!</div>
            <div className="text-sm">{data.po_number}</div>
            <div className="text-xs text-gray-400">Total: {formatRupiah(totals.total)}</div>
          </div>,
          { duration: 3000 }
        );
        
        // Reset for next PO
        setCart([]);
        setNotes('');
        setSelectedCartIndex(-1);
        
        // Focus back to search
        setTimeout(() => {
          if (searchInputRef.current) {
            searchInputRef.current.focus();
          }
        }, 100);
      } else {
        toast.error(data.detail || 'Gagal menyimpan PO');
      }
    } catch (err) {
      console.error(err);
      toast.error('Terjadi kesalahan');
    } finally {
      setSaving(false);
    }
  };
  
  // Handle search input keydown
  const handleSearchKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      if (showResults && searchResults.length > 0) {
        selectSearchResult(selectedResultIndex);
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (showResults) {
        setSelectedResultIndex(prev => Math.min(prev + 1, searchResults.length - 1));
      }
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (showResults) {
        setSelectedResultIndex(prev => Math.max(prev - 1, 0));
      }
    } else if (e.key === 'Escape') {
      setShowResults(false);
      setSearchText('');
    }
  };
  
  // Global keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      const isInput = e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA';
      
      if (e.key === 'F1') {
        e.preventDefault();
        if (cart.length > 0 && selectedSupplier) {
          savePO();
        }
      } else if (e.key === 'Escape') {
        if (showResults) {
          setShowResults(false);
        } else if (cart.length > 0) {
          if (window.confirm('Batalkan pembelian ini?')) {
            clearCart();
          }
        }
      } else if (e.key === 'Delete' && !isInput) {
        e.preventDefault();
        if (selectedCartIndex >= 0 && cart[selectedCartIndex]) {
          removeFromCart(cart[selectedCartIndex].product_id);
        }
      } else if ((e.key === 'ArrowUp' || e.key === 'ArrowDown') && !isInput && !showResults) {
        e.preventDefault();
        if (cart.length > 0) {
          if (e.key === 'ArrowUp') {
            setSelectedCartIndex(prev => Math.max(prev - 1, 0));
          } else {
            setSelectedCartIndex(prev => Math.min(prev + 1, cart.length - 1));
          }
        }
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [cart, selectedCartIndex, showResults, selectedSupplier, clearCart, removeFromCart]);
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-[#0a0608]">
        <Loader2 className="h-12 w-12 animate-spin text-amber-500" />
      </div>
    );
  }
  
  return (
    <div className="h-[calc(100vh-4rem)] flex bg-[#0a0608]" data-testid="quick-purchase-screen">
      {/* Left Panel - Product Search & Cart */}
      <div className="flex-1 flex flex-col p-4">
        {/* Header with shortcuts info */}
        <div className="flex items-center justify-between mb-3">
          <h1 className="text-xl font-bold text-amber-100 flex items-center gap-2">
            <Truck className="h-6 w-6 text-amber-400" />
            Quick Purchase
          </h1>
          <div className="flex items-center gap-4 text-xs text-gray-400">
            <span className="flex items-center gap-1">
              <Keyboard className="h-3 w-3" />
              <kbd className="px-1.5 py-0.5 bg-red-900/30 rounded border border-red-800">F1</kbd> Simpan
            </span>
            <span className="flex items-center gap-1">
              <kbd className="px-1.5 py-0.5 bg-red-900/30 rounded border border-red-800">Esc</kbd> Batal
            </span>
          </div>
        </div>
        
        {/* Search Bar */}
        <div className="relative mb-4">
          <div className="flex items-center bg-[#1a1214] border-2 border-amber-600 rounded-lg overflow-hidden shadow-lg shadow-amber-600/10">
            <Search className="h-6 w-6 text-amber-400 ml-4" />
            <input
              ref={searchInputRef}
              type="text"
              value={searchText}
              onChange={(e) => handleSearch(e.target.value)}
              onKeyDown={handleSearchKeyDown}
              onFocus={() => searchText && setShowResults(true)}
              placeholder="Ketik kode / nama barang lalu ENTER..."
              className="flex-1 px-4 py-4 bg-transparent text-white text-lg focus:outline-none placeholder-gray-500"
              data-testid="purchase-search-input"
              autoComplete="off"
            />
            {searchText && (
              <button 
                onClick={() => { setSearchText(''); setShowResults(false); }}
                className="p-2 mr-2 hover:bg-red-900/20 rounded"
                tabIndex={-1}
              >
                <X className="h-5 w-5 text-gray-400" />
              </button>
            )}
          </div>
          
          {/* Search Results Dropdown */}
          {showResults && searchResults.length > 0 && (
            <div className="absolute top-full left-0 right-0 mt-1 bg-[#1a1214] border border-red-900/50 rounded-lg shadow-2xl z-50 max-h-80 overflow-y-auto">
              {searchResults.map((product, idx) => (
                <button
                  key={product.id}
                  onClick={() => selectSearchResult(idx)}
                  className={`w-full px-4 py-3 flex items-center justify-between text-left border-b border-red-900/20 last:border-0 transition-colors ${
                    idx === selectedResultIndex ? 'bg-amber-600/20 border-l-4 border-l-amber-500' : 'hover:bg-red-900/20'
                  }`}
                  data-testid={`product-result-${product.id}`}
                >
                  <div className="flex-1">
                    <div className="text-white font-medium">{product.name}</div>
                    <div className="text-gray-400 text-sm flex gap-3">
                      <span className="font-mono">{product.code || '-'}</span>
                      <span>Stok: {product.stock || 0}</span>
                    </div>
                  </div>
                  <div className="text-amber-400 font-bold text-lg">{formatRupiah(product.cost_price)}</div>
                </button>
              ))}
              <div className="px-4 py-2 bg-[#0a0608] text-xs text-gray-500 flex items-center gap-2">
                <ArrowUp className="h-3 w-3" /><ArrowDown className="h-3 w-3" /> Navigasi
                <span className="ml-2">Enter = Pilih</span>
              </div>
            </div>
          )}
          
          {/* No results */}
          {showResults && searchText && searchResults.length === 0 && (
            <div className="absolute top-full left-0 right-0 mt-1 bg-[#1a1214] border border-red-900/30 rounded-lg shadow-xl p-4 text-center">
              <AlertCircle className="h-8 w-8 text-yellow-500 mx-auto mb-2" />
              <p className="text-gray-400">Item tidak ditemukan: "{searchText}"</p>
            </div>
          )}
        </div>
        
        {/* Cart Items */}
        <div className="flex-1 bg-[#1a1214]/50 rounded-lg border border-red-900/30 overflow-hidden flex flex-col">
          <div className="p-3 bg-[#1a1214] border-b border-red-900/30 flex items-center justify-between">
            <div className="flex items-center gap-2 text-gray-300">
              <ShoppingCart className="h-5 w-5 text-amber-400" />
              <span className="font-medium">Cart ({totals.itemCount} item)</span>
            </div>
            {cart.length > 0 && (
              <button
                onClick={clearCart}
                className="text-red-400 hover:text-red-300 text-sm px-2 py-1 hover:bg-red-900/20 rounded"
                data-testid="clear-cart-btn"
              >
                Hapus Semua
              </button>
            )}
          </div>
          
          <div className="flex-1 overflow-y-auto">
            {cart.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                <Package className="h-16 w-16 mx-auto mb-4 opacity-20" />
                <p className="text-lg">Cart Kosong</p>
                <p className="text-sm mt-2">Ketik kode/nama barang untuk menambah</p>
              </div>
            ) : (
              <table className="w-full">
                <thead className="bg-red-900/20 sticky top-0">
                  <tr className="text-gray-400 text-xs">
                    <th className="p-2 text-left w-8">#</th>
                    <th className="p-2 text-left">Item</th>
                    <th className="p-2 text-center w-24">Qty</th>
                    <th className="p-2 text-right w-28">Harga</th>
                    <th className="p-2 text-center w-16">Disk%</th>
                    <th className="p-2 text-right w-32">Subtotal</th>
                    <th className="p-2 w-10"></th>
                  </tr>
                </thead>
                <tbody>
                  {cart.map((item, idx) => (
                    <tr 
                      key={item.product_id} 
                      className={`border-b border-red-900/20 transition-colors cursor-pointer ${
                        idx === selectedCartIndex ? 'bg-amber-600/20 border-l-4 border-l-amber-500' : 'hover:bg-red-900/10'
                      }`}
                      onClick={() => setSelectedCartIndex(idx)}
                      data-testid={`cart-item-${item.product_id}`}
                    >
                      <td className="p-2 text-gray-500 text-sm">{idx + 1}</td>
                      <td className="p-2">
                        <div className="font-medium text-white">{item.product_name}</div>
                        <div className="text-gray-500 text-xs font-mono">{item.product_code}</div>
                      </td>
                      <td className="p-2">
                        <div className="flex items-center justify-center gap-1">
                          <button
                            onClick={(e) => { e.stopPropagation(); updateQty(item.product_id, item.qty - 1); }}
                            className="p-1 bg-red-900/30 hover:bg-red-600 rounded transition-colors"
                          >
                            <Minus className="h-3 w-3" />
                          </button>
                          <input
                            type="number"
                            value={item.qty}
                            onChange={(e) => {
                              e.stopPropagation();
                              updateQty(item.product_id, parseInt(e.target.value) || 1);
                            }}
                            onClick={(e) => e.stopPropagation()}
                            className="w-12 px-1 py-1 bg-[#0a0608] border border-red-900/30 rounded text-center text-white text-sm"
                            min="1"
                          />
                          <button
                            onClick={(e) => { e.stopPropagation(); updateQty(item.product_id, item.qty + 1); }}
                            className="p-1 bg-red-900/30 hover:bg-green-600 rounded transition-colors"
                          >
                            <Plus className="h-3 w-3" />
                          </button>
                        </div>
                      </td>
                      <td className="p-2">
                        <input
                          type="number"
                          value={item.unit_cost}
                          onChange={(e) => {
                            e.stopPropagation();
                            updateUnitCost(item.product_id, parseFloat(e.target.value) || 0);
                          }}
                          onClick={(e) => e.stopPropagation()}
                          className="w-full px-2 py-1 bg-[#0a0608] border border-red-900/30 rounded text-right text-white text-sm"
                          min="0"
                        />
                      </td>
                      <td className="p-2">
                        <input
                          type="number"
                          value={item.discount_percent}
                          onChange={(e) => {
                            e.stopPropagation();
                            updateDiscount(item.product_id, parseFloat(e.target.value) || 0);
                          }}
                          onClick={(e) => e.stopPropagation()}
                          className="w-full px-1 py-1 bg-[#0a0608] border border-red-900/30 rounded text-center text-white text-sm"
                          min="0"
                          max="100"
                        />
                      </td>
                      <td className="p-2 text-right font-bold text-amber-400">{formatRupiah(item.subtotal)}</td>
                      <td className="p-2">
                        <button
                          onClick={(e) => { e.stopPropagation(); removeFromCart(item.product_id); }}
                          className="p-1 hover:bg-red-600 rounded text-red-400 hover:text-white transition-colors"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
          
          {/* Cart keyboard hint */}
          {cart.length > 0 && (
            <div className="px-3 py-2 bg-[#0a0608] border-t border-red-900/30 text-xs text-gray-500 flex items-center gap-4">
              <span><ArrowUp className="h-3 w-3 inline" /><ArrowDown className="h-3 w-3 inline" /> Pilih item</span>
              <span><kbd className="px-1 bg-red-900/30 rounded">Del</kbd> Hapus item terpilih</span>
            </div>
          )}
        </div>
      </div>
      
      {/* Right Panel - Summary & Save */}
      <div className="w-96 bg-[#1a1214] border-l border-red-900/30 flex flex-col">
        {/* Supplier Selection */}
        <div className="p-4 border-b border-red-900/30">
          <label className="flex items-center gap-2 text-sm text-amber-200 mb-2">
            <Building2 className="h-4 w-4" />
            Supplier <span className="text-red-400">*</span>
          </label>
          <select
            value={selectedSupplier?.id || ''}
            onChange={(e) => {
              const sup = suppliers.find(s => s.id === e.target.value);
              setSelectedSupplier(sup || null);
            }}
            className="w-full px-3 py-3 bg-[#0a0608] border border-red-900/30 rounded-lg text-white focus:border-amber-500 focus:outline-none"
            data-testid="supplier-select"
          >
            <option value="">-- Pilih Supplier --</option>
            {suppliers.map(s => (
              <option key={s.id} value={s.id}>{s.code || ''} - {s.name}</option>
            ))}
          </select>
          {!selectedSupplier && cart.length > 0 && (
            <p className="text-red-400 text-xs mt-1 flex items-center gap-1">
              <AlertCircle className="h-3 w-3" /> Wajib pilih supplier
            </p>
          )}
        </div>
        
        {/* Warehouse Selection */}
        <div className="p-4 border-b border-red-900/30">
          <label className="block text-sm text-gray-400 mb-2">Gudang Tujuan</label>
          <select
            value={selectedWarehouse?.id || ''}
            onChange={(e) => {
              const wh = warehouses.find(w => w.id === e.target.value);
              setSelectedWarehouse(wh || null);
            }}
            className="w-full px-3 py-2.5 bg-[#0a0608] border border-red-900/30 rounded-lg text-white"
            data-testid="warehouse-select"
          >
            {warehouses.map(w => (
              <option key={w.id} value={w.id}>{w.name}</option>
            ))}
          </select>
        </div>
        
        {/* Notes */}
        <div className="p-4 border-b border-red-900/30">
          <label className="block text-sm text-gray-400 mb-2">Catatan (opsional)</label>
          <input
            type="text"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Catatan PO..."
            className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-white text-sm placeholder-gray-600"
          />
        </div>
        
        {/* Totals Summary */}
        <div className="flex-1 p-4 flex flex-col justify-center">
          <div className="space-y-4">
            <div className="flex justify-between text-gray-400">
              <span>Jumlah Item</span>
              <span className="text-white">{totals.itemCount} pcs</span>
            </div>
            <div className="flex justify-between text-gray-400">
              <span>Subtotal</span>
              <span className="text-white">{formatRupiah(totals.subtotal)}</span>
            </div>
            <div className="h-px bg-red-900/30"></div>
            <div className="flex justify-between items-center">
              <span className="text-xl font-medium text-gray-300">TOTAL</span>
              <span className="text-3xl font-bold text-amber-400" data-testid="total-amount">
                {formatRupiah(totals.total)}
              </span>
            </div>
          </div>
        </div>
        
        {/* Save Button */}
        <div className="p-4 border-t border-red-900/30 space-y-3">
          <button
            onClick={savePO}
            disabled={cart.length === 0 || !selectedSupplier || saving}
            className={`w-full py-4 rounded-lg font-bold text-lg flex items-center justify-center gap-3 transition-all ${
              cart.length === 0 || !selectedSupplier
                ? 'bg-gray-800 text-gray-500 cursor-not-allowed' 
                : 'bg-gradient-to-r from-red-600 to-amber-600 hover:from-red-500 hover:to-amber-500 text-white shadow-lg shadow-red-600/30'
            }`}
            data-testid="save-po-btn"
          >
            {saving ? (
              <Loader2 className="h-6 w-6 animate-spin" />
            ) : (
              <>
                <Save className="h-6 w-6" />
                SIMPAN PO
                <kbd className="ml-2 px-2 py-0.5 bg-red-800/50 rounded text-sm">F1</kbd>
              </>
            )}
          </button>
          
          <p className="text-center text-xs text-gray-500">
            PO akan tersimpan dengan status Draft
          </p>
        </div>
      </div>
    </div>
  );
};

export default QuickPurchase;
