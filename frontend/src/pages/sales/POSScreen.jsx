/**
 * POS Screen - iPOS Style
 * 
 * Flow mirip iPOS:
 * 1. Scan/ketik kode/nama barang → langsung masuk cart
 * 2. Edit qty langsung di cart
 * 3. Bayar → Selesai
 * 
 * Tanpa form ribet, tanpa popup tidak perlu
 */

import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { 
  Search, ShoppingCart, Trash2, Plus, Minus, CreditCard, 
  Banknote, User, Package, Loader2, X, Check
} from 'lucide-react';
import { toast } from 'sonner';

const formatRupiah = (num) => `Rp ${(num || 0).toLocaleString('id-ID')}`;

const POSScreen = () => {
  const { api, user } = useAuth();
  const navigate = useNavigate();
  const searchInputRef = useRef(null);
  
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
  
  // Cart state
  const [cart, setCart] = useState([]);
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [selectedWarehouse, setSelectedWarehouse] = useState(null);
  const [paymentAmount, setPaymentAmount] = useState(0);
  const [showPayment, setShowPayment] = useState(false);
  
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
  
  // Focus search on load
  useEffect(() => {
    if (!loading && searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, [loading]);
  
  // Search products
  const handleSearch = useCallback((text) => {
    setSearchText(text);
    if (text.length < 1) {
      setSearchResults([]);
      setShowResults(false);
      return;
    }
    
    const lowerText = text.toLowerCase();
    const results = products.filter(p => 
      p.name?.toLowerCase().includes(lowerText) ||
      p.code?.toLowerCase().includes(lowerText) ||
      p.barcode?.toLowerCase() === lowerText
    ).slice(0, 10);
    
    setSearchResults(results);
    setShowResults(true);
    
    // Auto add if exact barcode match
    if (results.length === 1 && results[0].barcode?.toLowerCase() === lowerText) {
      addToCart(results[0]);
      setSearchText('');
      setShowResults(false);
    }
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
      return [...prev, {
        product_id: product.id,
        product_code: product.code || '-',
        product_name: product.name,
        price: product.sell_price || 0,
        qty: 1,
        subtotal: product.sell_price || 0
      }];
    });
    
    // Clear search and refocus
    setSearchText('');
    setShowResults(false);
    if (searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, []);
  
  // Update qty
  const updateQty = useCallback((productId, delta) => {
    setCart(prev => prev.map(item => {
      if (item.product_id === productId) {
        const newQty = Math.max(1, item.qty + delta);
        return { ...item, qty: newQty, subtotal: newQty * item.price };
      }
      return item;
    }));
  }, []);
  
  // Remove from cart
  const removeFromCart = useCallback((productId) => {
    setCart(prev => prev.filter(item => item.product_id !== productId));
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
  
  // Handle payment
  const handlePayment = async () => {
    if (cart.length === 0) {
      toast.error('Cart kosong');
      return;
    }
    
    setSaving(true);
    try {
      const payload = {
        customer_id: selectedCustomer?.id || null,
        warehouse_id: selectedWarehouse?.id || '',
        ppn_type: 'exclude',
        ppn_percent: 0,
        notes: 'POS Transaction',
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
        payment_type: 'cash',
        cash_amount: paymentAmount || totals.total,
        credit_amount: 0,
      };
      
      const res = await api('/api/sales/invoices', {
        method: 'POST',
        body: JSON.stringify(payload)
      });
      
      if (res.ok) {
        const result = await res.json();
        toast.success(`Transaksi ${result.invoice_number} berhasil!`);
        
        // Reset
        setCart([]);
        setPaymentAmount(0);
        setShowPayment(false);
        setSelectedCustomer(null);
        
        // Focus back to search
        if (searchInputRef.current) {
          searchInputRef.current.focus();
        }
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Gagal menyimpan');
      }
    } catch (err) {
      console.error(err);
      toast.error('Terjadi kesalahan');
    } finally {
      setSaving(false);
    }
  };
  
  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'F2') {
        e.preventDefault();
        if (cart.length > 0) setShowPayment(true);
      }
      if (e.key === 'Escape') {
        setShowPayment(false);
        setShowResults(false);
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [cart.length]);
  
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
        {/* Search Bar - iPOS Style */}
        <div className="relative mb-4">
          <div className="flex items-center bg-gray-800 border-2 border-blue-500 rounded-lg overflow-hidden">
            <Search className="h-6 w-6 text-gray-400 ml-4" />
            <input
              ref={searchInputRef}
              type="text"
              value={searchText}
              onChange={(e) => handleSearch(e.target.value)}
              onFocus={() => searchText && setShowResults(true)}
              placeholder="Scan barcode atau ketik nama barang..."
              className="flex-1 px-4 py-4 bg-transparent text-white text-lg focus:outline-none"
              data-testid="pos-search-input"
            />
            {searchText && (
              <button 
                onClick={() => { setSearchText(''); setShowResults(false); }}
                className="p-2 mr-2 hover:bg-gray-700 rounded"
              >
                <X className="h-5 w-5 text-gray-400" />
              </button>
            )}
          </div>
          
          {/* Search Results Dropdown */}
          {showResults && searchResults.length > 0 && (
            <div className="absolute top-full left-0 right-0 mt-1 bg-gray-800 border border-gray-700 rounded-lg shadow-xl z-50 max-h-80 overflow-y-auto">
              {searchResults.map(product => (
                <button
                  key={product.id}
                  onClick={() => addToCart(product)}
                  className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-700 text-left border-b border-gray-700 last:border-0"
                  data-testid={`product-result-${product.id}`}
                >
                  <div>
                    <div className="text-white font-medium">{product.name}</div>
                    <div className="text-gray-400 text-sm">{product.code} | Stok: {product.stock || 0}</div>
                  </div>
                  <div className="text-green-400 font-bold">{formatRupiah(product.sell_price)}</div>
                </button>
              ))}
            </div>
          )}
        </div>
        
        {/* Cart Items */}
        <div className="flex-1 bg-gray-800/50 rounded-lg border border-gray-700 overflow-hidden">
          <div className="p-3 bg-gray-800 border-b border-gray-700 flex items-center justify-between">
            <div className="flex items-center gap-2 text-gray-300">
              <ShoppingCart className="h-5 w-5" />
              <span className="font-medium">Cart ({totals.itemCount} item)</span>
            </div>
            {cart.length > 0 && (
              <button
                onClick={() => setCart([])}
                className="text-red-400 hover:text-red-300 text-sm"
              >
                Hapus Semua
              </button>
            )}
          </div>
          
          <div className="overflow-y-auto" style={{ maxHeight: 'calc(100vh - 350px)' }}>
            {cart.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                <Package className="h-12 w-12 mx-auto mb-2 opacity-30" />
                <p>Scan barcode atau ketik nama barang</p>
                <p className="text-sm mt-1">untuk menambahkan ke cart</p>
              </div>
            ) : (
              <table className="w-full">
                <thead className="bg-gray-800/50 sticky top-0">
                  <tr className="text-gray-400 text-xs">
                    <th className="p-2 text-left">Item</th>
                    <th className="p-2 text-right w-24">Harga</th>
                    <th className="p-2 text-center w-32">Qty</th>
                    <th className="p-2 text-right w-28">Subtotal</th>
                    <th className="p-2 w-10"></th>
                  </tr>
                </thead>
                <tbody>
                  {cart.map(item => (
                    <tr key={item.product_id} className="border-b border-gray-700/50 hover:bg-gray-800/30">
                      <td className="p-2">
                        <div className="font-medium text-white">{item.product_name}</div>
                        <div className="text-gray-500 text-xs">{item.product_code}</div>
                      </td>
                      <td className="p-2 text-right text-gray-300">{formatRupiah(item.price)}</td>
                      <td className="p-2">
                        <div className="flex items-center justify-center gap-1">
                          <button
                            onClick={() => updateQty(item.product_id, -1)}
                            className="p-1 bg-gray-700 hover:bg-gray-600 rounded"
                          >
                            <Minus className="h-4 w-4" />
                          </button>
                          <input
                            type="number"
                            value={item.qty}
                            onChange={(e) => {
                              const newQty = parseInt(e.target.value) || 1;
                              setCart(prev => prev.map(i => 
                                i.product_id === item.product_id 
                                  ? { ...i, qty: newQty, subtotal: newQty * i.price }
                                  : i
                              ));
                            }}
                            className="w-12 px-1 py-1 bg-gray-800 border border-gray-600 rounded text-center text-white"
                          />
                          <button
                            onClick={() => updateQty(item.product_id, 1)}
                            className="p-1 bg-gray-700 hover:bg-gray-600 rounded"
                          >
                            <Plus className="h-4 w-4" />
                          </button>
                        </div>
                      </td>
                      <td className="p-2 text-right font-medium text-white">{formatRupiah(item.subtotal)}</td>
                      <td className="p-2">
                        <button
                          onClick={() => removeFromCart(item.product_id)}
                          className="p-1 hover:bg-red-700 rounded text-red-400"
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
        </div>
      </div>
      
      {/* Right Panel - Payment Summary */}
      <div className="w-80 bg-gray-800 border-l border-gray-700 flex flex-col">
        {/* Customer Selection */}
        <div className="p-4 border-b border-gray-700">
          <label className="block text-xs text-gray-400 mb-1">Pelanggan</label>
          <select
            value={selectedCustomer?.id || ''}
            onChange={(e) => {
              const cust = customers.find(c => c.id === e.target.value);
              setSelectedCustomer(cust || null);
            }}
            className="w-full px-3 py-2 bg-gray-900 border border-gray-600 rounded text-white"
          >
            <option value="">Umum / Walk-in</option>
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
            className="w-full px-3 py-2 bg-gray-900 border border-gray-600 rounded text-white"
          >
            {warehouses.map(w => (
              <option key={w.id} value={w.id}>{w.name}</option>
            ))}
          </select>
        </div>
        
        {/* Totals */}
        <div className="flex-1 p-4">
          <div className="space-y-3">
            <div className="flex justify-between text-gray-400">
              <span>Subtotal</span>
              <span>{formatRupiah(totals.subtotal)}</span>
            </div>
            <div className="flex justify-between text-gray-400">
              <span>Pajak</span>
              <span>{formatRupiah(totals.tax)}</span>
            </div>
            <div className="h-px bg-gray-700 my-2"></div>
            <div className="flex justify-between text-xl font-bold text-white">
              <span>TOTAL</span>
              <span className="text-green-400">{formatRupiah(totals.total)}</span>
            </div>
          </div>
        </div>
        
        {/* Payment Button */}
        <div className="p-4 border-t border-gray-700">
          <button
            onClick={() => cart.length > 0 && setShowPayment(true)}
            disabled={cart.length === 0 || saving}
            className={`w-full py-4 rounded-lg font-bold text-lg flex items-center justify-center gap-2 ${
              cart.length === 0 
                ? 'bg-gray-700 text-gray-500 cursor-not-allowed' 
                : 'bg-green-600 hover:bg-green-500 text-white'
            }`}
            data-testid="pos-pay-btn"
          >
            <CreditCard className="h-6 w-6" />
            BAYAR (F2)
          </button>
        </div>
      </div>
      
      {/* Payment Modal */}
      {showPayment && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-xl p-6 w-96 border border-gray-700">
            <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
              <Banknote className="h-6 w-6 text-green-400" />
              Pembayaran
            </h3>
            
            <div className="space-y-4">
              <div className="bg-gray-900 rounded-lg p-4">
                <div className="text-gray-400 text-sm">Total Bayar</div>
                <div className="text-3xl font-bold text-green-400">{formatRupiah(totals.total)}</div>
              </div>
              
              <div>
                <label className="block text-sm text-gray-400 mb-1">Uang Diterima</label>
                <input
                  type="number"
                  value={paymentAmount || ''}
                  onChange={(e) => setPaymentAmount(parseFloat(e.target.value) || 0)}
                  placeholder={totals.total.toString()}
                  className="w-full px-4 py-3 bg-gray-900 border border-gray-600 rounded-lg text-white text-xl"
                  autoFocus
                />
              </div>
              
              {paymentAmount >= totals.total && (
                <div className="bg-blue-900/30 rounded-lg p-4">
                  <div className="text-gray-400 text-sm">Kembalian</div>
                  <div className="text-2xl font-bold text-blue-400">
                    {formatRupiah(paymentAmount - totals.total)}
                  </div>
                </div>
              )}
              
              {/* Quick amount buttons */}
              <div className="grid grid-cols-3 gap-2">
                {[totals.total, Math.ceil(totals.total / 50000) * 50000, Math.ceil(totals.total / 100000) * 100000].map(amt => (
                  <button
                    key={amt}
                    onClick={() => setPaymentAmount(amt)}
                    className="px-3 py-2 bg-gray-700 hover:bg-gray-600 rounded text-sm text-white"
                  >
                    {formatRupiah(amt)}
                  </button>
                ))}
              </div>
              
              <div className="flex gap-3 mt-6">
                <button
                  onClick={() => setShowPayment(false)}
                  className="flex-1 py-3 bg-gray-700 hover:bg-gray-600 rounded-lg text-white"
                >
                  Batal
                </button>
                <button
                  onClick={handlePayment}
                  disabled={saving || (paymentAmount > 0 && paymentAmount < totals.total)}
                  className="flex-1 py-3 bg-green-600 hover:bg-green-500 rounded-lg text-white font-bold flex items-center justify-center gap-2 disabled:opacity-50"
                  data-testid="pos-confirm-pay"
                >
                  {saving ? <Loader2 className="h-5 w-5 animate-spin" /> : <Check className="h-5 w-5" />}
                  Simpan
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default POSScreen;
