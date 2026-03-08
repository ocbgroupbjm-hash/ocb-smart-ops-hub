import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Search, Plus, Minus, Trash2, ShoppingCart, CreditCard, Banknote, QrCode, Wallet, User, Clock, X, Check, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

const POS = () => {
  const { api, user } = useAuth();
  const [cart, setCart] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [customer, setCustomer] = useState(null);
  const [customerSearch, setCustomerSearch] = useState('');
  const [customerResults, setCustomerResults] = useState([]);
  const [showCustomerModal, setShowCustomerModal] = useState(false);
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [heldTransactions, setHeldTransactions] = useState([]);
  const [showHeldModal, setShowHeldModal] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [payments, setPayments] = useState([]);
  const [discountPercent, setDiscountPercent] = useState(0);
  const searchRef = useRef(null);
  const barcodeBuffer = useRef('');
  const barcodeTimeout = useRef(null);

  // Calculate totals
  const subtotal = cart.reduce((sum, item) => sum + (item.price * item.qty), 0);
  const discountAmount = subtotal * (discountPercent / 100);
  const total = subtotal - discountAmount;

  // Product search
  useEffect(() => {
    const search = async () => {
      if (searchQuery.length < 2) {
        setSearchResults([]);
        return;
      }
      setSearching(true);
      try {
        const res = await api(`/api/products/search?q=${encodeURIComponent(searchQuery)}`);
        if (res.ok) {
          const data = await res.json();
          setSearchResults(data);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setSearching(false);
      }
    };

    const timer = setTimeout(search, 300);
    return () => clearTimeout(timer);
  }, [searchQuery, api]);

  // Barcode scanner handler
  useEffect(() => {
    const handleKeyPress = (e) => {
      // Ignore if focused on input
      if (document.activeElement.tagName === 'INPUT') return;
      
      if (e.key === 'Enter' && barcodeBuffer.current) {
        handleBarcode(barcodeBuffer.current);
        barcodeBuffer.current = '';
        return;
      }
      
      if (e.key.length === 1) {
        barcodeBuffer.current += e.key;
        clearTimeout(barcodeTimeout.current);
        barcodeTimeout.current = setTimeout(() => {
          barcodeBuffer.current = '';
        }, 100);
      }
    };

    window.addEventListener('keypress', handleKeyPress);
    return () => window.removeEventListener('keypress', handleKeyPress);
  }, []);

  const handleBarcode = async (barcode) => {
    try {
      const res = await api(`/api/products/barcode/${barcode}`);
      if (res.ok) {
        const product = await res.json();
        addToCart(product);
        toast.success(`Added: ${product.name}`);
      } else {
        toast.error('Product not found');
      }
    } catch (err) {
      toast.error('Scan error');
    }
  };

  const addToCart = (product) => {
    setCart(prev => {
      const existing = prev.find(item => item.id === product.id);
      if (existing) {
        return prev.map(item =>
          item.id === product.id ? { ...item, qty: item.qty + 1 } : item
        );
      }
      return [...prev, {
        id: product.id,
        code: product.code,
        name: product.name,
        price: product.selling_price,
        cost: product.cost_price,
        stock: product.stock || product.available || 999,
        qty: 1,
        discount: 0
      }];
    });
    setSearchQuery('');
    setSearchResults([]);
  };

  const updateQty = (id, delta) => {
    setCart(prev => prev.map(item => {
      if (item.id === id) {
        const newQty = Math.max(1, item.qty + delta);
        if (newQty > item.stock) {
          toast.error('Insufficient stock');
          return item;
        }
        return { ...item, qty: newQty };
      }
      return item;
    }));
  };

  const removeFromCart = (id) => {
    setCart(prev => prev.filter(item => item.id !== id));
  };

  const clearCart = () => {
    setCart([]);
    setCustomer(null);
    setDiscountPercent(0);
    setPayments([]);
  };

  // Customer search
  const searchCustomers = async (q) => {
    if (q.length < 2) {
      setCustomerResults([]);
      return;
    }
    try {
      const res = await api(`/api/customers/search?q=${encodeURIComponent(q)}`);
      if (res.ok) {
        setCustomerResults(await res.json());
      }
    } catch (err) {
      console.error(err);
    }
  };

  // Hold transaction
  const holdTransaction = async () => {
    if (cart.length === 0) return;
    
    try {
      const res = await api('/api/pos/hold', {
        method: 'POST',
        body: JSON.stringify({
          items: cart.map(item => ({
            product_id: item.id,
            quantity: item.qty,
            discount_percent: item.discount
          })),
          customer_id: customer?.id,
          customer_name: customer?.name || '',
          hold_name: `Hold-${new Date().toLocaleTimeString()}`
        })
      });
      
      if (res.ok) {
        toast.success('Transaction held');
        clearCart();
        loadHeldTransactions();
      }
    } catch (err) {
      toast.error('Failed to hold');
    }
  };

  // Load held transactions
  const loadHeldTransactions = async () => {
    try {
      const res = await api('/api/pos/held');
      if (res.ok) {
        setHeldTransactions(await res.json());
      }
    } catch (err) {
      console.error(err);
    }
  };

  // Recall held transaction
  const recallTransaction = async (held) => {
    try {
      const res = await api(`/api/pos/held/${held.id}`);
      if (res.ok) {
        const data = await res.json();
        
        // Load products into cart
        const items = [];
        for (const item of data.items) {
          const prodRes = await api(`/api/products/${item.product_id}`);
          if (prodRes.ok) {
            const product = await prodRes.json();
            items.push({
              id: product.id,
              code: product.code,
              name: product.name,
              price: product.selling_price,
              cost: product.cost_price,
              stock: product.total_stock || 999,
              qty: item.quantity,
              discount: item.discount_percent || 0
            });
          }
        }
        
        setCart(items);
        if (data.customer_id) {
          setCustomer({ id: data.customer_id, name: data.customer_name });
        }
        
        // Delete held transaction
        await api(`/api/pos/held/${held.id}`, { method: 'DELETE' });
        
        setShowHeldModal(false);
        loadHeldTransactions();
        toast.success('Transaction recalled');
      }
    } catch (err) {
      toast.error('Failed to recall');
    }
  };

  // Process payment
  const processPayment = async () => {
    if (cart.length === 0) return;
    
    const totalPaid = payments.reduce((sum, p) => sum + p.amount, 0);
    if (totalPaid < total) {
      toast.error('Insufficient payment');
      return;
    }
    
    setProcessing(true);
    try {
      const res = await api('/api/pos/transaction', {
        method: 'POST',
        body: JSON.stringify({
          items: cart.map(item => ({
            product_id: item.id,
            quantity: item.qty,
            discount_percent: item.discount
          })),
          customer_id: customer?.id,
          customer_name: customer?.name || '',
          customer_phone: customer?.phone || '',
          discount_percent: discountPercent,
          payments: payments.map(p => ({
            method: p.method,
            amount: p.amount,
            reference: p.reference || ''
          })),
          notes: ''
        })
      });
      
      if (res.ok) {
        const data = await res.json();
        toast.success(`Sale completed! Invoice: ${data.invoice_number}`);
        clearCart();
        setShowPaymentModal(false);
      } else {
        const error = await res.json();
        toast.error(error.detail || 'Transaction failed');
      }
    } catch (err) {
      toast.error('Transaction failed');
    } finally {
      setProcessing(false);
    }
  };

  // Add payment method
  const addPayment = (method) => {
    const remaining = total - payments.reduce((sum, p) => sum + p.amount, 0);
    if (remaining <= 0) return;
    
    setPayments(prev => [...prev, { method, amount: remaining, reference: '' }]);
  };

  useEffect(() => {
    loadHeldTransactions();
  }, []);

  return (
    <div className="h-screen flex bg-[#0a0608] text-gray-100">
      {/* Left Panel - Products */}
      <div className="flex-1 flex flex-col p-4">
        {/* Search Bar */}
        <div className="relative mb-4">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            ref={searchRef}
            type="text"
            placeholder="Search products or scan barcode..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-3 bg-[#1a1214] border border-red-900/30 rounded-lg focus:outline-none focus:border-red-500 text-lg"
            data-testid="pos-search-input"
          />
          
          {/* Search Results Dropdown */}
          {searchResults.length > 0 && (
            <div className="absolute top-full left-0 right-0 mt-1 bg-[#1a1214] border border-red-900/30 rounded-lg shadow-xl z-50 max-h-80 overflow-y-auto">
              {searchResults.map(product => (
                <button
                  key={product.id}
                  onClick={() => addToCart(product)}
                  className="w-full px-4 py-3 flex items-center justify-between hover:bg-red-900/20 border-b border-red-900/10 last:border-0"
                  data-testid={`search-result-${product.code}`}
                >
                  <div>
                    <div className="font-medium">{product.name}</div>
                    <div className="text-sm text-gray-400">{product.code} • Stock: {product.stock || product.available || 0}</div>
                  </div>
                  <div className="text-amber-400 font-bold">
                    Rp {product.selling_price?.toLocaleString()}
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Quick Actions */}
        <div className="flex gap-2 mb-4">
          <button
            onClick={() => setShowHeldModal(true)}
            className="px-4 py-2 bg-amber-600/20 text-amber-400 rounded-lg hover:bg-amber-600/30 flex items-center gap-2"
            data-testid="pos-held-btn"
          >
            <Clock className="h-4 w-4" />
            Held ({heldTransactions.length})
          </button>
          <button
            onClick={() => setShowCustomerModal(true)}
            className="px-4 py-2 bg-blue-600/20 text-blue-400 rounded-lg hover:bg-blue-600/30 flex items-center gap-2"
            data-testid="pos-customer-btn"
          >
            <User className="h-4 w-4" />
            {customer ? customer.name : 'Add Customer'}
          </button>
        </div>

        {/* Cart Items */}
        <div className="flex-1 bg-[#1a1214] border border-red-900/30 rounded-lg overflow-hidden">
          <div className="p-3 bg-red-900/20 border-b border-red-900/30 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ShoppingCart className="h-5 w-5 text-red-400" />
              <span className="font-semibold">Cart ({cart.length} items)</span>
            </div>
            {cart.length > 0 && (
              <button
                onClick={clearCart}
                className="text-red-400 hover:text-red-300 text-sm"
                data-testid="pos-clear-cart"
              >
                Clear All
              </button>
            )}
          </div>
          
          <div className="overflow-y-auto" style={{ height: 'calc(100vh - 400px)' }}>
            {cart.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-gray-500">
                <ShoppingCart className="h-16 w-16 mb-4 opacity-30" />
                <p>Cart is empty</p>
                <p className="text-sm">Search or scan products to add</p>
              </div>
            ) : (
              cart.map(item => (
                <div
                  key={item.id}
                  className="p-3 border-b border-red-900/10 hover:bg-red-900/10"
                  data-testid={`cart-item-${item.id}`}
                >
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <div className="font-medium">{item.name}</div>
                      <div className="text-sm text-gray-400">{item.code}</div>
                    </div>
                    <button
                      onClick={() => removeFromCart(item.id)}
                      className="text-red-400 hover:text-red-300 p-1"
                      data-testid={`remove-item-${item.id}`}
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                  <div className="flex justify-between items-center">
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => updateQty(item.id, -1)}
                        className="w-8 h-8 flex items-center justify-center bg-red-900/30 rounded hover:bg-red-900/50"
                        data-testid={`qty-minus-${item.id}`}
                      >
                        <Minus className="h-4 w-4" />
                      </button>
                      <span className="w-12 text-center font-bold">{item.qty}</span>
                      <button
                        onClick={() => updateQty(item.id, 1)}
                        className="w-8 h-8 flex items-center justify-center bg-red-900/30 rounded hover:bg-red-900/50"
                        data-testid={`qty-plus-${item.id}`}
                      >
                        <Plus className="h-4 w-4" />
                      </button>
                    </div>
                    <div className="text-right">
                      <div className="text-sm text-gray-400">@ Rp {item.price?.toLocaleString()}</div>
                      <div className="font-bold text-amber-400">Rp {(item.price * item.qty).toLocaleString()}</div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Right Panel - Summary & Payment */}
      <div className="w-80 bg-[#12090b] border-l border-red-900/30 flex flex-col">
        {/* User Info */}
        <div className="p-4 border-b border-red-900/30">
          <div className="text-sm text-gray-400">Cashier</div>
          <div className="font-semibold">{user?.name}</div>
          <div className="text-xs text-gray-500">{user?.branch?.name}</div>
        </div>

        {/* Summary */}
        <div className="flex-1 p-4 flex flex-col">
          <div className="space-y-3 mb-6">
            <div className="flex justify-between text-gray-400">
              <span>Subtotal</span>
              <span>Rp {subtotal.toLocaleString()}</span>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Discount</span>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  value={discountPercent}
                  onChange={(e) => setDiscountPercent(Math.max(0, Math.min(100, Number(e.target.value))))}
                  className="w-16 px-2 py-1 bg-[#1a1214] border border-red-900/30 rounded text-right"
                  data-testid="pos-discount-input"
                />
                <span>%</span>
              </div>
            </div>
            
            {discountAmount > 0 && (
              <div className="flex justify-between text-red-400">
                <span>Discount Amount</span>
                <span>-Rp {discountAmount.toLocaleString()}</span>
              </div>
            )}
          </div>

          <div className="mt-auto">
            <div className="flex justify-between text-2xl font-bold mb-6">
              <span>TOTAL</span>
              <span className="text-amber-400">Rp {total.toLocaleString()}</span>
            </div>

            <div className="grid grid-cols-2 gap-2 mb-4">
              <button
                onClick={holdTransaction}
                disabled={cart.length === 0}
                className="py-3 bg-amber-600/20 text-amber-400 rounded-lg hover:bg-amber-600/30 disabled:opacity-50 flex items-center justify-center gap-2"
                data-testid="pos-hold-btn"
              >
                <Clock className="h-5 w-5" />
                Hold
              </button>
              <button
                onClick={clearCart}
                disabled={cart.length === 0}
                className="py-3 bg-red-600/20 text-red-400 rounded-lg hover:bg-red-600/30 disabled:opacity-50 flex items-center justify-center gap-2"
                data-testid="pos-cancel-btn"
              >
                <X className="h-5 w-5" />
                Cancel
              </button>
            </div>

            <button
              onClick={() => {
                if (cart.length === 0) return;
                setPayments([]);
                setShowPaymentModal(true);
              }}
              disabled={cart.length === 0}
              className="w-full py-4 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg font-bold text-lg hover:from-red-500 hover:to-amber-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              data-testid="pos-pay-btn"
            >
              <CreditCard className="h-6 w-6" />
              PAY NOW
            </button>
          </div>
        </div>
      </div>

      {/* Payment Modal */}
      {showPaymentModal && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50" data-testid="payment-modal">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-lg p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-bold">Payment</h2>
              <button onClick={() => setShowPaymentModal(false)} className="text-gray-400 hover:text-white">
                <X className="h-6 w-6" />
              </button>
            </div>

            <div className="text-center mb-6">
              <div className="text-gray-400">Total Amount</div>
              <div className="text-3xl font-bold text-amber-400">Rp {total.toLocaleString()}</div>
            </div>

            {/* Payment Methods */}
            <div className="grid grid-cols-4 gap-2 mb-6">
              <button
                onClick={() => addPayment('cash')}
                className="p-3 bg-green-600/20 text-green-400 rounded-lg hover:bg-green-600/30 flex flex-col items-center gap-1"
                data-testid="pay-cash"
              >
                <Banknote className="h-6 w-6" />
                <span className="text-xs">Cash</span>
              </button>
              <button
                onClick={() => addPayment('qris')}
                className="p-3 bg-purple-600/20 text-purple-400 rounded-lg hover:bg-purple-600/30 flex flex-col items-center gap-1"
                data-testid="pay-qris"
              >
                <QrCode className="h-6 w-6" />
                <span className="text-xs">QRIS</span>
              </button>
              <button
                onClick={() => addPayment('bank_transfer')}
                className="p-3 bg-blue-600/20 text-blue-400 rounded-lg hover:bg-blue-600/30 flex flex-col items-center gap-1"
                data-testid="pay-transfer"
              >
                <CreditCard className="h-6 w-6" />
                <span className="text-xs">Transfer</span>
              </button>
              <button
                onClick={() => addPayment('ewallet')}
                className="p-3 bg-amber-600/20 text-amber-400 rounded-lg hover:bg-amber-600/30 flex flex-col items-center gap-1"
                data-testid="pay-ewallet"
              >
                <Wallet className="h-6 w-6" />
                <span className="text-xs">E-Wallet</span>
              </button>
            </div>

            {/* Payment List */}
            {payments.length > 0 && (
              <div className="space-y-2 mb-6">
                {payments.map((p, idx) => (
                  <div key={idx} className="flex items-center gap-2 bg-[#0a0608] p-3 rounded-lg">
                    <span className="capitalize flex-1">{p.method.replace('_', ' ')}</span>
                    <input
                      type="number"
                      value={p.amount}
                      onChange={(e) => {
                        const newPayments = [...payments];
                        newPayments[idx].amount = Number(e.target.value);
                        setPayments(newPayments);
                      }}
                      className="w-32 px-2 py-1 bg-[#1a1214] border border-red-900/30 rounded text-right"
                    />
                    <button
                      onClick={() => setPayments(payments.filter((_, i) => i !== idx))}
                      className="text-red-400 hover:text-red-300"
                    >
                      <X className="h-5 w-5" />
                    </button>
                  </div>
                ))}
              </div>
            )}

            {/* Summary */}
            <div className="border-t border-red-900/30 pt-4 mb-6">
              <div className="flex justify-between mb-2">
                <span className="text-gray-400">Paid</span>
                <span className="text-green-400">Rp {payments.reduce((s, p) => s + p.amount, 0).toLocaleString()}</span>
              </div>
              <div className="flex justify-between text-lg font-bold">
                <span>Change</span>
                <span className="text-amber-400">
                  Rp {Math.max(0, payments.reduce((s, p) => s + p.amount, 0) - total).toLocaleString()}
                </span>
              </div>
            </div>

            <button
              onClick={processPayment}
              disabled={processing || payments.reduce((s, p) => s + p.amount, 0) < total}
              className="w-full py-4 bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-lg font-bold text-lg hover:from-green-500 hover:to-emerald-500 disabled:opacity-50 flex items-center justify-center gap-2"
              data-testid="confirm-payment-btn"
            >
              {processing ? <Loader2 className="h-6 w-6 animate-spin" /> : <Check className="h-6 w-6" />}
              {processing ? 'Processing...' : 'Complete Sale'}
            </button>
          </div>
        </div>
      )}

      {/* Customer Modal */}
      {showCustomerModal && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50" data-testid="customer-modal">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-md p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">Select Customer</h2>
              <button onClick={() => setShowCustomerModal(false)} className="text-gray-400 hover:text-white">
                <X className="h-6 w-6" />
              </button>
            </div>

            <input
              type="text"
              placeholder="Search by name or phone..."
              value={customerSearch}
              onChange={(e) => {
                setCustomerSearch(e.target.value);
                searchCustomers(e.target.value);
              }}
              className="w-full px-4 py-3 bg-[#0a0608] border border-red-900/30 rounded-lg mb-4"
            />

            <div className="space-y-2 max-h-60 overflow-y-auto">
              {customerResults.map(c => (
                <button
                  key={c.id}
                  onClick={() => {
                    setCustomer(c);
                    setShowCustomerModal(false);
                  }}
                  className="w-full p-3 bg-[#0a0608] rounded-lg hover:bg-red-900/20 text-left"
                >
                  <div className="font-medium">{c.name}</div>
                  <div className="text-sm text-gray-400">{c.phone} • {c.segment}</div>
                </button>
              ))}
            </div>

            {customer && (
              <button
                onClick={() => {
                  setCustomer(null);
                  setShowCustomerModal(false);
                }}
                className="w-full mt-4 py-2 border border-red-900/30 rounded-lg text-red-400 hover:bg-red-900/20"
              >
                Remove Customer
              </button>
            )}
          </div>
        </div>
      )}

      {/* Held Transactions Modal */}
      {showHeldModal && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50" data-testid="held-modal">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-md p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">Held Transactions</h2>
              <button onClick={() => setShowHeldModal(false)} className="text-gray-400 hover:text-white">
                <X className="h-6 w-6" />
              </button>
            </div>

            {heldTransactions.length === 0 ? (
              <div className="text-center text-gray-400 py-8">No held transactions</div>
            ) : (
              <div className="space-y-2 max-h-80 overflow-y-auto">
                {heldTransactions.map(held => (
                  <button
                    key={held.id}
                    onClick={() => recallTransaction(held)}
                    className="w-full p-3 bg-[#0a0608] rounded-lg hover:bg-amber-900/20 text-left"
                  >
                    <div className="font-medium">{held.hold_name}</div>
                    <div className="text-sm text-gray-400">
                      {held.items?.length || 0} items • {new Date(held.created_at).toLocaleTimeString()}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default POS;
