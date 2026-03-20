/**
 * POS Screen - iPOS Style
 * 
 * Shortcut Keyboard:
 * - Enter = Tambah item / Konfirmasi input
 * - F1 = Bayar Tunai
 * - F2 = Bayar Non-Tunai (Transfer/E-Money)
 * - Delete = Hapus item aktif
 * - Esc = Batal transaksi / Tutup modal
 * - Arrow Up/Down = Navigasi item di cart
 * - Ctrl+S = Simpan transaksi
 * 
 * Flow: Single screen, minim klik, keyboard-driven
 */

import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { 
  Search, ShoppingCart, Trash2, Plus, Minus, CreditCard, 
  Banknote, Package, Loader2, X, Check, Keyboard, ArrowUp, 
  ArrowDown, AlertCircle, Wallet
} from 'lucide-react';
import { toast } from 'sonner';

const formatRupiah = (num) => `Rp ${(num || 0).toLocaleString('id-ID')}`;

const POSScreen = () => {
  const { api, user } = useAuth();
  const navigate = useNavigate();
  const searchInputRef = useRef(null);
  const paymentInputRef = useRef(null);
  
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  
  // Master data
  const [products, setProducts] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  
  // Search state
  const [searchText, setSearchText] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [showResults, setShowResults] = useState(false);
  const [selectedResultIndex, setSelectedResultIndex] = useState(0);
  
  // Cart state
  const [cart, setCart] = useState([]);
  const [selectedCartIndex, setSelectedCartIndex] = useState(-1);
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [selectedWarehouse, setSelectedWarehouse] = useState(null);
  
  // Payment state
  const [showPayment, setShowPayment] = useState(false);
  const [paymentType, setPaymentType] = useState('cash'); // cash, transfer
  const [paymentAmount, setPaymentAmount] = useState(0);
  
  // Load master data
  useEffect(() => {
    const loadData = async () => {
      try {
        const [prodRes, custRes, whRes] = await Promise.all([
          api('/api/products?limit=5000'),
          api('/api/customers'),
          api('/api/master/warehouses')
        ]);
        
        if (prodRes.ok) setProducts((await prodRes.json()).items || []);
        if (custRes.ok) setCustomers((await custRes.json()).items || []);
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
  
  // Focus search on load and after payment
  useEffect(() => {
    if (!loading && !showPayment && searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, [loading, showPayment]);
  
  // Search products by code, barcode, or name
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
      // Auto-add if exact barcode match
      addToCart(exactBarcode);
      setSearchText('');
      setShowResults(false);
      return;
    }
    
    const exactCode = products.find(p => p.code?.toLowerCase() === lowerText);
    if (exactCode) {
      // Auto-add if exact code match
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
            ? { ...item, qty: item.qty + 1, subtotal: (item.qty + 1) * item.price }
            : item
        );
      }
      // Get price from selling_price (backend field name)
      const itemPrice = product.selling_price || product.sell_price || 0;
      
      // Warning if no valid price
      if (itemPrice <= 0) {
        toast.warning(`Peringatan: ${product.name} tidak memiliki harga jual!`, { duration: 3000 });
      }
      
      return [...prev, {
        product_id: product.id,
        product_code: product.code || '-',
        product_name: product.name,
        price: itemPrice,
        qty: 1,
        subtotal: itemPrice
      }];
    });
    
    toast.success(`+ ${product.name}`, { duration: 1000 });
    
    // Clear search and refocus
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
        return { ...item, qty: newQty, subtotal: newQty * item.price };
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
    setSelectedCustomer(null);
    setPaymentAmount(0);
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
      tax: 0,
      total: subtotal,
      itemCount: cart.reduce((sum, item) => sum + item.qty, 0)
    };
  }, [cart]);
  
  // Open payment modal
  const openPayment = useCallback((type) => {
    if (cart.length === 0) {
      toast.error('Cart kosong!');
      return;
    }
    setPaymentType(type);
    setPaymentAmount(totals.total);
    setShowPayment(true);
    setTimeout(() => {
      if (paymentInputRef.current) {
        paymentInputRef.current.focus();
        paymentInputRef.current.select();
      }
    }, 100);
  }, [cart.length, totals.total]);
  
  // Process payment
  const processPayment = async () => {
    if (cart.length === 0) {
      toast.error('Cart kosong');
      return;
    }
    
    if (!selectedCustomer) {
      toast.error('Pilih pelanggan terlebih dahulu!');
      return;
    }
    
    if (paymentAmount < totals.total && paymentType === 'cash') {
      toast.error('Uang tidak cukup!');
      return;
    }
    
    setSaving(true);
    try {
      const payload = {
        customer_id: selectedCustomer?.id || '',
        warehouse_id: selectedWarehouse?.id || '',
        ppn_type: 'exclude',
        ppn_percent: 0,
        notes: `POS - ${paymentType === 'cash' ? 'Tunai' : 'Transfer'}`,
        items: cart.map(item => ({
          product_id: item.product_id,
          quantity: item.qty,
          unit_price: item.price,
          discount_percent: 0,
          tax_percent: 0,
        })),
        subtotal: totals.subtotal,
        discount_amount: 0,
        tax_amount: 0,
        other_cost: 0,
        total: totals.total,
        payment_type: paymentType === 'cash' ? 'cash' : 'credit',
        // Send actual total as cash_amount (kembalian only for display)
        cash_amount: paymentType === 'cash' ? totals.total : 0,
        credit_amount: paymentType === 'cash' ? 0 : totals.total,
      };
      
      const res = await api('/api/sales/invoices', {
        method: 'POST',
        body: JSON.stringify(payload)
      });
      
      const data = await res.json();
      
      if (res.ok) {
        const change = paymentType === 'cash' ? paymentAmount - totals.total : 0;
        
        toast.success(
          <div>
            <div className="font-bold">Transaksi Berhasil!</div>
            <div className="text-sm">{data.invoice_number}</div>
            {change > 0 && <div className="text-yellow-300">Kembalian: {formatRupiah(change)}</div>}
          </div>,
          { duration: 3000 }
        );
        
        // Reset for next transaction
        setCart([]);
        setPaymentAmount(0);
        setShowPayment(false);
        setSelectedCustomer(null);
        setSelectedCartIndex(-1);
        
        // Focus back to search
        setTimeout(() => {
          if (searchInputRef.current) {
            searchInputRef.current.focus();
          }
        }, 100);
      } else {
        toast.error(data.detail || 'Gagal menyimpan');
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
  
  // Handle payment input keydown
  const handlePaymentKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      processPayment();
    } else if (e.key === 'Escape') {
      setShowPayment(false);
    }
  };
  
  // Global keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Don't trigger shortcuts when typing in inputs (except designated shortcuts)
      const isInput = e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA';
      
      if (e.key === 'F1') {
        e.preventDefault();
        if (!showPayment && cart.length > 0) {
          openPayment('cash');
        }
      } else if (e.key === 'F2') {
        e.preventDefault();
        if (!showPayment && cart.length > 0) {
          openPayment('transfer');
        }
      } else if (e.key === 'Escape') {
        if (showPayment) {
          setShowPayment(false);
        } else if (showResults) {
          setShowResults(false);
        } else if (cart.length > 0) {
          // Confirm before clearing
          if (window.confirm('Batalkan transaksi ini?')) {
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
      } else if (e.ctrlKey && e.key === 's') {
        e.preventDefault();
        if (cart.length > 0) {
          openPayment('cash');
        }
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [cart, selectedCartIndex, showPayment, showResults, openPayment, clearCart, removeFromCart]);
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-900">
        <Loader2 className="h-12 w-12 animate-spin text-blue-500" />
      </div>
    );
  }
  
  return (
    <div className="h-screen flex bg-gray-900" data-testid="pos-screen">
      {/* Left Panel - Product Search & Cart */}
      <div className="flex-1 flex flex-col p-4">
        {/* Header with shortcuts info */}
        <div className="flex items-center justify-between mb-3">
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <ShoppingCart className="h-6 w-6 text-green-400" />
            POS Kasir
          </h1>
          <div className="flex items-center gap-4 text-xs text-gray-400">
            <span className="flex items-center gap-1">
              <Keyboard className="h-3 w-3" />
              <kbd className="px-1.5 py-0.5 bg-gray-700 rounded">F1</kbd> Tunai
            </span>
            <span className="flex items-center gap-1">
              <kbd className="px-1.5 py-0.5 bg-gray-700 rounded">F2</kbd> Transfer
            </span>
            <span className="flex items-center gap-1">
              <kbd className="px-1.5 py-0.5 bg-gray-700 rounded">Esc</kbd> Batal
            </span>
          </div>
        </div>
        
        {/* Search Bar - Auto Focus */}
        <div className="relative mb-4">
          <div className="flex items-center bg-gray-800 border-2 border-green-500 rounded-lg overflow-hidden shadow-lg shadow-green-500/10">
            <Search className="h-6 w-6 text-green-400 ml-4" />
            <input
              ref={searchInputRef}
              type="text"
              value={searchText}
              onChange={(e) => handleSearch(e.target.value)}
              onKeyDown={handleSearchKeyDown}
              onFocus={() => searchText && setShowResults(true)}
              placeholder="Scan barcode / ketik kode / nama barang lalu ENTER..."
              className="flex-1 px-4 py-4 bg-transparent text-white text-lg focus:outline-none placeholder-gray-500"
              data-testid="pos-search-input"
              autoComplete="off"
            />
            {searchText && (
              <button 
                onClick={() => { setSearchText(''); setShowResults(false); }}
                className="p-2 mr-2 hover:bg-gray-700 rounded"
                tabIndex={-1}
              >
                <X className="h-5 w-5 text-gray-400" />
              </button>
            )}
          </div>
          
          {/* Search Results Dropdown */}
          {showResults && searchResults.length > 0 && (
            <div className="absolute top-full left-0 right-0 mt-1 bg-gray-800 border border-gray-600 rounded-lg shadow-2xl z-50 max-h-80 overflow-y-auto">
              {searchResults.map((product, idx) => (
                <button
                  key={product.id}
                  onClick={() => selectSearchResult(idx)}
                  className={`w-full px-4 py-3 flex items-center justify-between text-left border-b border-gray-700 last:border-0 transition-colors ${
                    idx === selectedResultIndex ? 'bg-green-600/20 border-l-4 border-l-green-500' : 'hover:bg-gray-700'
                  }`}
                  data-testid={`product-result-${product.id}`}
                >
                  <div className="flex-1">
                    <div className="text-white font-medium">{product.name}</div>
                    <div className="text-gray-400 text-sm flex gap-3">
                      <span className="font-mono">{product.code || '-'}</span>
                      {product.barcode && <span>BC: {product.barcode}</span>}
                      <span>Stok: {product.stock || 0}</span>
                    </div>
                  </div>
                  <div className="text-green-400 font-bold text-lg">{formatRupiah(product.selling_price || product.sell_price)}</div>
                </button>
              ))}
              <div className="px-4 py-2 bg-gray-900 text-xs text-gray-500 flex items-center gap-2">
                <ArrowUp className="h-3 w-3" /><ArrowDown className="h-3 w-3" /> Navigasi
                <span className="ml-2">Enter = Pilih</span>
              </div>
            </div>
          )}
          
          {/* No results message */}
          {showResults && searchText && searchResults.length === 0 && (
            <div className="absolute top-full left-0 right-0 mt-1 bg-gray-800 border border-gray-600 rounded-lg shadow-xl p-4 text-center">
              <AlertCircle className="h-8 w-8 text-yellow-500 mx-auto mb-2" />
              <p className="text-gray-400">Item tidak ditemukan: "{searchText}"</p>
            </div>
          )}
        </div>
        
        {/* Cart Items */}
        <div className="flex-1 bg-gray-800/50 rounded-lg border border-gray-700 overflow-hidden flex flex-col">
          <div className="p-3 bg-gray-800 border-b border-gray-700 flex items-center justify-between">
            <div className="flex items-center gap-2 text-gray-300">
              <ShoppingCart className="h-5 w-5" />
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
                <p className="text-sm mt-2">Scan barcode atau ketik nama barang</p>
              </div>
            ) : (
              <table className="w-full">
                <thead className="bg-gray-800/80 sticky top-0">
                  <tr className="text-gray-400 text-xs">
                    <th className="p-2 text-left w-8">#</th>
                    <th className="p-2 text-left">Item</th>
                    <th className="p-2 text-right w-28">Harga</th>
                    <th className="p-2 text-center w-36">Qty</th>
                    <th className="p-2 text-right w-32">Subtotal</th>
                    <th className="p-2 w-12"></th>
                  </tr>
                </thead>
                <tbody>
                  {cart.map((item, idx) => (
                    <tr 
                      key={item.product_id} 
                      className={`border-b border-gray-700/50 transition-colors cursor-pointer ${
                        idx === selectedCartIndex ? 'bg-blue-600/20 border-l-4 border-l-blue-500' : 'hover:bg-gray-800/30'
                      }`}
                      onClick={() => setSelectedCartIndex(idx)}
                      data-testid={`cart-item-${item.product_id}`}
                    >
                      <td className="p-2 text-gray-500 text-sm">{idx + 1}</td>
                      <td className="p-2">
                        <div className="font-medium text-white">{item.product_name}</div>
                        <div className="text-gray-500 text-xs font-mono">{item.product_code}</div>
                      </td>
                      <td className="p-2 text-right text-gray-300">{formatRupiah(item.price)}</td>
                      <td className="p-2">
                        <div className="flex items-center justify-center gap-1">
                          <button
                            onClick={(e) => { e.stopPropagation(); updateQty(item.product_id, item.qty - 1); }}
                            className="p-1.5 bg-gray-700 hover:bg-red-600 rounded transition-colors"
                            data-testid={`qty-minus-${item.product_id}`}
                          >
                            <Minus className="h-4 w-4" />
                          </button>
                          <input
                            type="number"
                            value={item.qty}
                            onChange={(e) => {
                              e.stopPropagation();
                              const newQty = parseInt(e.target.value) || 1;
                              updateQty(item.product_id, newQty);
                            }}
                            onClick={(e) => e.stopPropagation()}
                            className="w-14 px-2 py-1 bg-gray-800 border border-gray-600 rounded text-center text-white font-bold"
                            min="1"
                            data-testid={`qty-input-${item.product_id}`}
                          />
                          <button
                            onClick={(e) => { e.stopPropagation(); updateQty(item.product_id, item.qty + 1); }}
                            className="p-1.5 bg-gray-700 hover:bg-green-600 rounded transition-colors"
                            data-testid={`qty-plus-${item.product_id}`}
                          >
                            <Plus className="h-4 w-4" />
                          </button>
                        </div>
                      </td>
                      <td className="p-2 text-right font-bold text-white">{formatRupiah(item.subtotal)}</td>
                      <td className="p-2">
                        <button
                          onClick={(e) => { e.stopPropagation(); removeFromCart(item.product_id); }}
                          className="p-1.5 hover:bg-red-600 rounded text-red-400 hover:text-white transition-colors"
                          data-testid={`remove-item-${item.product_id}`}
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
            <div className="px-3 py-2 bg-gray-900 border-t border-gray-700 text-xs text-gray-500 flex items-center gap-4">
              <span><ArrowUp className="h-3 w-3 inline" /><ArrowDown className="h-3 w-3 inline" /> Pilih item</span>
              <span><kbd className="px-1 bg-gray-700 rounded">Del</kbd> Hapus item terpilih</span>
            </div>
          )}
        </div>
      </div>
      
      {/* Right Panel - Summary & Payment */}
      <div className="w-96 bg-gray-800 border-l border-gray-700 flex flex-col">
        {/* Customer Selection */}
        <div className="p-4 border-b border-gray-700">
          <label className="block text-xs text-gray-400 mb-1">Pelanggan</label>
          <select
            value={selectedCustomer?.id || ''}
            onChange={(e) => {
              const cust = customers.find(c => c.id === e.target.value);
              setSelectedCustomer(cust || null);
            }}
            className="w-full px-3 py-2.5 bg-gray-900 border border-gray-600 rounded-lg text-white"
            data-testid="customer-select"
          >
            <option value="">Walk-in / Umum</option>
            {customers.map(c => (
              <option key={c.id} value={c.id}>{c.code} - {c.name}</option>
            ))}
          </select>
        </div>
        
        {/* Warehouse Selection */}
        <div className="p-4 border-b border-gray-700">
          <label className="block text-xs text-gray-400 mb-1">Gudang</label>
          <select
            value={selectedWarehouse?.id || ''}
            onChange={(e) => {
              const wh = warehouses.find(w => w.id === e.target.value);
              setSelectedWarehouse(wh || null);
            }}
            className="w-full px-3 py-2.5 bg-gray-900 border border-gray-600 rounded-lg text-white"
            data-testid="warehouse-select"
          >
            {warehouses.map(w => (
              <option key={w.id} value={w.id}>{w.name}</option>
            ))}
          </select>
        </div>
        
        {/* Totals Summary */}
        <div className="flex-1 p-4 flex flex-col justify-center">
          <div className="space-y-4">
            <div className="flex justify-between text-gray-400">
              <span>Subtotal ({totals.itemCount} item)</span>
              <span className="text-white">{formatRupiah(totals.subtotal)}</span>
            </div>
            <div className="flex justify-between text-gray-400">
              <span>Pajak</span>
              <span className="text-white">{formatRupiah(totals.tax)}</span>
            </div>
            <div className="h-px bg-gray-600"></div>
            <div className="flex justify-between items-center">
              <span className="text-xl font-medium text-gray-300">TOTAL</span>
              <span className="text-3xl font-bold text-green-400" data-testid="total-amount">
                {formatRupiah(totals.total)}
              </span>
            </div>
          </div>
        </div>
        
        {/* Payment Buttons */}
        <div className="p-4 border-t border-gray-700 space-y-3">
          <button
            onClick={() => openPayment('cash')}
            disabled={cart.length === 0 || saving}
            className={`w-full py-4 rounded-lg font-bold text-lg flex items-center justify-center gap-3 transition-all ${
              cart.length === 0 
                ? 'bg-gray-700 text-gray-500 cursor-not-allowed' 
                : 'bg-green-600 hover:bg-green-500 text-white shadow-lg shadow-green-600/30 hover:shadow-green-500/40'
            }`}
            data-testid="pay-cash-btn"
          >
            <Banknote className="h-6 w-6" />
            BAYAR TUNAI
            <kbd className="ml-2 px-2 py-0.5 bg-green-700 rounded text-sm">F1</kbd>
          </button>
          
          <button
            onClick={() => openPayment('transfer')}
            disabled={cart.length === 0 || saving}
            className={`w-full py-4 rounded-lg font-bold text-lg flex items-center justify-center gap-3 transition-all ${
              cart.length === 0 
                ? 'bg-gray-700 text-gray-500 cursor-not-allowed' 
                : 'bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-600/30 hover:shadow-blue-500/40'
            }`}
            data-testid="pay-transfer-btn"
          >
            <Wallet className="h-6 w-6" />
            TRANSFER / E-MONEY
            <kbd className="ml-2 px-2 py-0.5 bg-blue-700 rounded text-sm">F2</kbd>
          </button>
        </div>
      </div>
      
      {/* Payment Modal */}
      {showPayment && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50" data-testid="payment-modal">
          <div className="bg-gray-800 rounded-2xl p-6 w-[420px] border border-gray-600 shadow-2xl">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-bold text-white flex items-center gap-2">
                {paymentType === 'cash' ? (
                  <>
                    <Banknote className="h-6 w-6 text-green-400" />
                    Pembayaran Tunai
                  </>
                ) : (
                  <>
                    <Wallet className="h-6 w-6 text-blue-400" />
                    Transfer / E-Money
                  </>
                )}
              </h3>
              <button 
                onClick={() => setShowPayment(false)}
                className="p-1 hover:bg-gray-700 rounded"
              >
                <X className="h-5 w-5 text-gray-400" />
              </button>
            </div>
            
            <div className="space-y-5">
              {/* Total */}
              <div className="bg-gray-900 rounded-xl p-5 text-center">
                <div className="text-gray-400 text-sm mb-1">Total Bayar</div>
                <div className="text-4xl font-bold text-green-400">{formatRupiah(totals.total)}</div>
              </div>
              
              {/* Payment input */}
              {paymentType === 'cash' && (
                <div>
                  <label className="block text-sm text-gray-400 mb-2">Uang Diterima</label>
                  <input
                    ref={paymentInputRef}
                    type="number"
                    value={paymentAmount || ''}
                    onChange={(e) => setPaymentAmount(parseFloat(e.target.value) || 0)}
                    onKeyDown={handlePaymentKeyDown}
                    className="w-full px-4 py-4 bg-gray-900 border-2 border-green-500 rounded-xl text-white text-2xl font-bold text-center focus:outline-none focus:border-green-400"
                    data-testid="payment-amount-input"
                  />
                </div>
              )}
              
              {/* Quick amounts for cash */}
              {paymentType === 'cash' && (
                <div className="grid grid-cols-3 gap-2">
                  {[
                    totals.total,
                    Math.ceil(totals.total / 10000) * 10000,
                    Math.ceil(totals.total / 50000) * 50000,
                    Math.ceil(totals.total / 100000) * 100000,
                    200000,
                    500000
                  ].filter((v, i, a) => a.indexOf(v) === i).slice(0, 6).map(amt => (
                    <button
                      key={amt}
                      onClick={() => setPaymentAmount(amt)}
                      className={`px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                        paymentAmount === amt 
                          ? 'bg-green-600 text-white' 
                          : 'bg-gray-700 hover:bg-gray-600 text-white'
                      }`}
                    >
                      {formatRupiah(amt)}
                    </button>
                  ))}
                </div>
              )}
              
              {/* Change calculation */}
              {paymentType === 'cash' && paymentAmount >= totals.total && (
                <div className="bg-blue-900/30 rounded-xl p-4 border border-blue-500/30">
                  <div className="text-gray-400 text-sm">Kembalian</div>
                  <div className="text-3xl font-bold text-blue-400">
                    {formatRupiah(paymentAmount - totals.total)}
                  </div>
                </div>
              )}
              
              {/* Insufficient warning */}
              {paymentType === 'cash' && paymentAmount > 0 && paymentAmount < totals.total && (
                <div className="bg-red-900/30 rounded-xl p-4 border border-red-500/30 flex items-center gap-3">
                  <AlertCircle className="h-6 w-6 text-red-400" />
                  <div>
                    <div className="text-red-400 font-medium">Uang Kurang!</div>
                    <div className="text-sm text-gray-400">
                      Kurang {formatRupiah(totals.total - paymentAmount)}
                    </div>
                  </div>
                </div>
              )}
              
              {/* Transfer note */}
              {paymentType === 'transfer' && (
                <div className="bg-blue-900/20 rounded-xl p-4 border border-blue-500/30">
                  <p className="text-blue-300 text-sm">
                    Pastikan transfer sudah diterima sebelum menekan tombol Simpan.
                  </p>
                </div>
              )}
              
              {/* Action buttons */}
              <div className="flex gap-3 pt-2">
                <button
                  onClick={() => setShowPayment(false)}
                  className="flex-1 py-3.5 bg-gray-700 hover:bg-gray-600 rounded-xl text-white font-medium transition-colors"
                  data-testid="cancel-payment-btn"
                >
                  Batal
                </button>
                <button
                  onClick={processPayment}
                  disabled={saving || (paymentType === 'cash' && paymentAmount < totals.total)}
                  className="flex-1 py-3.5 bg-green-600 hover:bg-green-500 rounded-xl text-white font-bold flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  data-testid="confirm-payment-btn"
                >
                  {saving ? (
                    <Loader2 className="h-5 w-5 animate-spin" />
                  ) : (
                    <>
                      <Check className="h-5 w-5" />
                      SIMPAN
                    </>
                  )}
                </button>
              </div>
              
              {/* Keyboard hint */}
              <div className="text-center text-xs text-gray-500">
                <kbd className="px-1.5 py-0.5 bg-gray-700 rounded">Enter</kbd> = Simpan
                <span className="mx-2">|</span>
                <kbd className="px-1.5 py-0.5 bg-gray-700 rounded">Esc</kbd> = Batal
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default POSScreen;
