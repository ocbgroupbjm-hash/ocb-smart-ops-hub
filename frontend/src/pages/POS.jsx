import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Search, Plus, Minus, Trash2, ShoppingCart, CreditCard, Banknote, QrCode, Wallet, User, Clock, X, Check, Loader2, Printer, MessageCircle, Tag, Gift, Sparkles } from 'lucide-react';
import { toast } from 'sonner';

const POS = () => {
  const { api, user } = useAuth();
  const [cart, setCart] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
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
  const [lastInvoice, setLastInvoice] = useState(null);
  const [showSuccessModal, setShowSuccessModal] = useState(false);
  const searchRef = useRef(null);
  const barcodeBuffer = useRef('');
  const barcodeTimeout = useRef(null);
  
  // Pricing engine state
  const [appliedDiscounts, setAppliedDiscounts] = useState([]);
  const [appliedPromos, setAppliedPromos] = useState([]);
  const [freeItems, setFreeItems] = useState([]);
  const [engineDiscount, setEngineDiscount] = useState(0);
  const [customerPriceLevel, setCustomerPriceLevel] = useState(1);
  const [calculatingPricing, setCalculatingPricing] = useState(false);

  const subtotal = cart.reduce((sum, item) => sum + (item.price * item.qty), 0);
  const discountAmount = subtotal * (discountPercent / 100) + engineDiscount;
  const total = subtotal - discountAmount;
  const formatRupiah = (num) => `Rp ${(num || 0).toLocaleString('id-ID')}`;

  useEffect(() => {
    const search = async () => {
      if (searchQuery.length < 2) { setSearchResults([]); return; }
      try {
        const res = await api(`/api/products/search?q=${encodeURIComponent(searchQuery)}`);
        if (res.ok) setSearchResults(await res.json());
      } catch (err) { console.error(err); }
    };
    const timer = setTimeout(search, 300);
    return () => clearTimeout(timer);
  }, [searchQuery, api]);

  useEffect(() => {
    const handleKeyPress = (e) => {
      if (document.activeElement.tagName === 'INPUT') return;
      if (e.key === 'Enter' && barcodeBuffer.current) {
        handleBarcode(barcodeBuffer.current);
        barcodeBuffer.current = '';
        return;
      }
      if (e.key.length === 1) {
        barcodeBuffer.current += e.key;
        clearTimeout(barcodeTimeout.current);
        barcodeTimeout.current = setTimeout(() => { barcodeBuffer.current = ''; }, 100);
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
        toast.success(`Ditambahkan: ${product.name}`);
      } else {
        toast.error('Produk tidak ditemukan');
      }
    } catch (err) { toast.error('Error scan barcode'); }
  };

  // ==================== PRICING ENGINE INTEGRATION ====================
  
  // Get price for customer based on price level
  const getPriceForCustomer = async (productId, customerId) => {
    if (!productId || !customerId) return null;
    try {
      const res = await api(`/api/master/price-for-customer/${productId}/${customerId}`);
      if (res.ok) return await res.json();
    } catch (err) { console.error('Error getting price:', err); }
    return null;
  };

  // Calculate pricing with auto-apply discounts & promos
  const calculatePricing = useCallback(async () => {
    if (cart.length === 0) {
      setAppliedDiscounts([]);
      setAppliedPromos([]);
      setFreeItems([]);
      setEngineDiscount(0);
      return;
    }
    
    setCalculatingPricing(true);
    try {
      const res = await api('/api/master/calculate-pricing', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          items: cart.map(item => ({
            product_id: item.id,
            quantity: item.qty,
            unit_price: item.price
          })),
          customer_id: customer?.id,
          branch_id: user?.branch_id
        })
      });
      
      if (res.ok) {
        const data = await res.json();
        setAppliedDiscounts(data.discounts || []);
        setAppliedPromos(data.promotions || []);
        setFreeItems(data.free_items || []);
        setEngineDiscount(data.totals?.total_discount || 0);
        
        if ((data.discounts?.length > 0 || data.promotions?.length > 0) && cart.length > 0) {
          toast.success(`${data.discounts?.length || 0} diskon & ${data.promotions?.length || 0} promo aktif`);
        }
      }
    } catch (err) { console.error('Error calculating pricing:', err); }
    finally { setCalculatingPricing(false); }
  }, [cart, customer, user, api]);

  // Re-calculate pricing when cart or customer changes
  useEffect(() => {
    if (cart.length > 0) {
      const timer = setTimeout(calculatePricing, 500);
      return () => clearTimeout(timer);
    }
  }, [cart, customer, calculatePricing]);

  // Update prices when customer changes
  const handleCustomerSelect = async (selectedCustomer) => {
    setCustomer(selectedCustomer);
    setShowCustomerModal(false);
    
    if (!selectedCustomer || cart.length === 0) return;
    
    // Get price for each item based on customer's price level
    const updatedCart = await Promise.all(cart.map(async (item) => {
      const priceInfo = await getPriceForCustomer(item.id, selectedCustomer.id);
      if (priceInfo && priceInfo.price > 0) {
        setCustomerPriceLevel(priceInfo.price_level || 1);
        return { ...item, price: priceInfo.price, price_level: priceInfo.price_level };
      }
      return item;
    }));
    
    setCart(updatedCart);
    toast.info(`Harga diupdate sesuai level customer`);
  };

  const addToCart = async (product) => {
    // Get price based on customer's price level
    let price = product.selling_price || product.wholesale_price || product.cost_price || 0;
    let priceLevel = 1;
    
    if (customer?.id) {
      const priceInfo = await getPriceForCustomer(product.id, customer.id);
      if (priceInfo && priceInfo.price > 0) {
        price = priceInfo.price;
        priceLevel = priceInfo.price_level || 1;
      }
    }
    
    if (price <= 0) {
      toast.error(`Harga produk "${product.name}" tidak valid (Rp 0). Silakan set harga jual di Master Item.`);
      return;
    }
    
    setCart(prev => {
      const existing = prev.find(item => item.id === product.id);
      if (existing) {
        return prev.map(item => item.id === product.id ? { ...item, qty: item.qty + 1 } : item);
      }
      return [...prev, {
        id: product.id, code: product.code, name: product.name,
        price: price, cost: product.cost_price || 0,
        stock: product.stock || product.available || 999, qty: 1, discount: 0,
        price_level: priceLevel
      }];
    });
    setSearchQuery('');
    setSearchResults([]);
  };

  const updateQty = (id, delta) => {
    setCart(prev => prev.map(item => {
      if (item.id === id) {
        const newQty = Math.max(1, item.qty + delta);
        if (newQty > item.stock) { toast.error('Stok tidak mencukupi'); return item; }
        return { ...item, qty: newQty };
      }
      return item;
    }));
  };

  const removeFromCart = (id) => setCart(prev => prev.filter(item => item.id !== id));
  const clearCart = () => { setCart([]); setCustomer(null); setDiscountPercent(0); setPayments([]); };

  const searchCustomers = async (q) => {
    if (q.length < 2) { setCustomerResults([]); return; }
    try {
      const res = await api(`/api/customers/search?q=${encodeURIComponent(q)}`);
      if (res.ok) setCustomerResults(await res.json());
    } catch (err) { console.error(err); }
  };

  const holdTransaction = async () => {
    if (cart.length === 0) return;
    try {
      const res = await api('/api/pos/hold', {
        method: 'POST',
        body: JSON.stringify({
          items: cart.map(item => ({ product_id: item.id, quantity: item.qty, discount_percent: item.discount })),
          customer_id: customer?.id, customer_name: customer?.name || '',
          hold_name: `Tahan-${new Date().toLocaleTimeString('id-ID')}`
        })
      });
      if (res.ok) { toast.success('Transaksi ditahan'); clearCart(); loadHeldTransactions(); }
    } catch (err) { toast.error('Gagal menahan transaksi'); }
  };

  const loadHeldTransactions = async () => {
    try {
      const res = await api('/api/pos/held');
      if (res.ok) setHeldTransactions(await res.json());
    } catch (err) { console.error(err); }
  };

  const recallTransaction = async (held) => {
    try {
      const res = await api(`/api/pos/held/${held.id}`);
      if (res.ok) {
        const data = await res.json();
        const items = [];
        for (const item of data.items) {
          const prodRes = await api(`/api/products/${item.product_id}`);
          if (prodRes.ok) {
            const product = await prodRes.json();
            items.push({
              id: product.id, code: product.code, name: product.name,
              price: product.selling_price, cost: product.cost_price,
              stock: product.total_stock || 999, qty: item.quantity, discount: item.discount_percent || 0
            });
          }
        }
        setCart(items);
        if (data.customer_id) setCustomer({ id: data.customer_id, name: data.customer_name });
        await api(`/api/pos/held/${held.id}`, { method: 'DELETE' });
        setShowHeldModal(false);
        loadHeldTransactions();
        toast.success('Transaksi dipanggil kembali');
      }
    } catch (err) { toast.error('Gagal memanggil transaksi'); }
  };

  const processPayment = async () => {
    if (cart.length === 0) return;
    const totalPaid = payments.reduce((sum, p) => sum + p.amount, 0);
    if (totalPaid < total) { toast.error('Pembayaran kurang'); return; }
    
    setProcessing(true);
    try {
      const res = await api('/api/pos/transaction', {
        method: 'POST',
        body: JSON.stringify({
          items: cart.map(item => ({ product_id: item.id, quantity: item.qty, discount_percent: item.discount })),
          customer_id: customer?.id, customer_name: customer?.name || '', customer_phone: customer?.phone || '',
          discount_percent: discountPercent,
          payments: payments.map(p => ({ method: p.method, amount: p.amount, reference: p.reference || '' })),
          notes: ''
        })
      });
      
      if (res.ok) {
        const data = await res.json();
        setLastInvoice({ ...data, total, paid: totalPaid, change: totalPaid - total, items: cart });
        setShowPaymentModal(false);
        setShowSuccessModal(true);
        clearCart();
      } else {
        const error = await res.json();
        toast.error(error.detail || 'Transaksi gagal');
      }
    } catch (err) { toast.error('Transaksi gagal'); }
    finally { setProcessing(false); }
  };

  const addPayment = (method) => {
    const remaining = total - payments.reduce((sum, p) => sum + p.amount, 0);
    if (remaining <= 0) return;
    setPayments(prev => [...prev, { method, amount: remaining, reference: '' }]);
  };

  useEffect(() => { loadHeldTransactions(); }, []);

  const handlePrintReceipt = (invoice) => {
    // Build receipt content
    const receiptContent = `
========================================
           OCB GROUP - STRUK
========================================
No. Invoice: ${invoice.invoice_number}
Tanggal: ${new Date().toLocaleString('id-ID')}
Kasir: ${user?.name || '-'}
Cabang: ${user?.branch?.name || '-'}
----------------------------------------
${invoice.items.map(item => 
  `${item.name}
   ${item.qty} x ${formatRupiah(item.price)} = ${formatRupiah(item.price * item.qty)}`
).join('\n')}
----------------------------------------
Subtotal: ${formatRupiah(invoice.total)}
Diskon: -${formatRupiah(invoice.total - (invoice.total / (1 - (discountPercent/100))) * (discountPercent/100))}
TOTAL: ${formatRupiah(invoice.total)}
Dibayar: ${formatRupiah(invoice.paid)}
Kembalian: ${formatRupiah(invoice.change)}
========================================
    Terima Kasih Telah Berbelanja!
========================================
`;
    
    // Open print window
    const printWindow = window.open('', '_blank', 'width=400,height=600');
    if (printWindow) {
      printWindow.document.write(`
        <html>
          <head>
            <title>Struk ${invoice.invoice_number}</title>
            <style>
              body { font-family: monospace; font-size: 12px; padding: 20px; }
              pre { white-space: pre-wrap; word-wrap: break-word; }
            </style>
          </head>
          <body>
            <pre>${receiptContent}</pre>
            <script>
              window.onload = function() {
                window.print();
                setTimeout(function() { window.close(); }, 500);
              }
            </script>
          </body>
        </html>
      `);
      printWindow.document.close();
      toast.success('Struk sedang dicetak...');
    } else {
      toast.error('Tidak dapat membuka jendela print. Periksa pop-up blocker.');
    }
  };

  const handleShareWhatsApp = (invoice) => {
    const message = `*STRUK PEMBELIAN OCB GROUP*
━━━━━━━━━━━━━━━━━━━━
No. Invoice: ${invoice.invoice_number}
Tanggal: ${new Date().toLocaleString('id-ID')}
━━━━━━━━━━━━━━━━━━━━
${invoice.items.map(item => 
  `• ${item.name}
  ${item.qty} x ${formatRupiah(item.price)} = *${formatRupiah(item.price * item.qty)}*`
).join('\n')}
━━━━━━━━━━━━━━━━━━━━
*TOTAL: ${formatRupiah(invoice.total)}*
Dibayar: ${formatRupiah(invoice.paid)}
Kembalian: ${formatRupiah(invoice.change)}
━━━━━━━━━━━━━━━━━━━━
_Terima kasih atas kunjungan Anda!_`;

    const encodedMessage = encodeURIComponent(message);
    const customerPhone = invoice.customer_phone || customer?.phone || '';
    
    if (customerPhone) {
      // Format phone for WhatsApp (remove leading 0, add 62)
      let formattedPhone = customerPhone.replace(/\D/g, '');
      if (formattedPhone.startsWith('0')) {
        formattedPhone = '62' + formattedPhone.substring(1);
      }
      window.open(`https://wa.me/${formattedPhone}?text=${encodedMessage}`, '_blank');
    } else {
      // Open WhatsApp without specific number
      window.open(`https://wa.me/?text=${encodedMessage}`, '_blank');
    }
    toast.success('Membuka WhatsApp...');
  };

  const paymentLabels = {
    cash: 'Tunai', bank_transfer: 'Transfer Bank', qris: 'QRIS', ewallet: 'E-Wallet', store_credit: 'Kredit Toko'
  };

  return (
    <div className="h-screen flex bg-[#0a0608] text-gray-100">
      {/* Panel Kiri - Produk */}
      <div className="flex-1 flex flex-col p-4">
        <div className="relative mb-4">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            ref={searchRef}
            type="text"
            placeholder="Cari produk atau scan barcode..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-3 bg-[#1a1214] border border-red-900/30 rounded-lg focus:outline-none focus:border-red-500 text-lg"
            data-testid="pos-search-input"
          />
          
          {searchResults.length > 0 && (
            <div className="absolute top-full left-0 right-0 mt-1 bg-[#1a1214] border border-red-900/30 rounded-lg shadow-xl z-50 max-h-80 overflow-y-auto">
              {searchResults.map(product => (
                <button
                  key={product.id}
                  onClick={() => addToCart(product)}
                  className="w-full px-4 py-3 flex items-center justify-between hover:bg-red-900/20 border-b border-red-900/10 last:border-0"
                >
                  <div>
                    <div className="font-medium">{product.name}</div>
                    <div className="text-sm text-gray-400">{product.code} • Stok: {product.stock || product.available || 0}</div>
                  </div>
                  <div className="text-amber-400 font-bold">{formatRupiah(product.selling_price)}</div>
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="flex gap-2 mb-4">
          <button onClick={() => setShowHeldModal(true)} className="px-4 py-2 bg-amber-600/20 text-amber-400 rounded-lg hover:bg-amber-600/30 flex items-center gap-2">
            <Clock className="h-4 w-4" /> Ditahan ({heldTransactions.length})
          </button>
          <button onClick={() => setShowCustomerModal(true)} className="px-4 py-2 bg-blue-600/20 text-blue-400 rounded-lg hover:bg-blue-600/30 flex items-center gap-2">
            <User className="h-4 w-4" /> {customer ? customer.name : 'Pilih Pelanggan'}
          </button>
        </div>

        <div className="flex-1 bg-[#1a1214] border border-red-900/30 rounded-lg overflow-hidden">
          <div className="p-3 bg-red-900/20 border-b border-red-900/30 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ShoppingCart className="h-5 w-5 text-red-400" />
              <span className="font-semibold">Keranjang ({cart.length} item)</span>
            </div>
            {cart.length > 0 && (
              <button onClick={clearCart} className="text-red-400 hover:text-red-300 text-sm">Kosongkan</button>
            )}
          </div>
          
          <div className="overflow-y-auto" style={{ height: 'calc(100vh - 400px)' }}>
            {cart.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-gray-500">
                <ShoppingCart className="h-16 w-16 mb-4 opacity-30" />
                <p>Keranjang kosong</p>
                <p className="text-sm">Cari atau scan produk</p>
              </div>
            ) : (
              cart.map(item => (
                <div key={item.id} className="p-3 border-b border-red-900/10 hover:bg-red-900/10">
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <div className="font-medium">{item.name}</div>
                      <div className="text-sm text-gray-400">{item.code}</div>
                    </div>
                    <button onClick={() => removeFromCart(item.id)} className="text-red-400 hover:text-red-300 p-1">
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                  <div className="flex justify-between items-center">
                    <div className="flex items-center gap-2">
                      <button onClick={() => updateQty(item.id, -1)} className="w-8 h-8 flex items-center justify-center bg-red-900/30 rounded hover:bg-red-900/50">
                        <Minus className="h-4 w-4" />
                      </button>
                      <span className="w-12 text-center font-bold">{item.qty}</span>
                      <button onClick={() => updateQty(item.id, 1)} className="w-8 h-8 flex items-center justify-center bg-red-900/30 rounded hover:bg-red-900/50">
                        <Plus className="h-4 w-4" />
                      </button>
                    </div>
                    <div className="text-right">
                      <div className="text-sm text-gray-400">@ {formatRupiah(item.price)}</div>
                      <div className="font-bold text-amber-400">{formatRupiah(item.price * item.qty)}</div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Panel Kanan - Ringkasan */}
      <div className="w-80 bg-[#12090b] border-l border-red-900/30 flex flex-col">
        <div className="p-4 border-b border-red-900/30">
          <div className="text-sm text-gray-400">Kasir</div>
          <div className="font-semibold">{user?.name}</div>
          <div className="text-xs text-gray-500">{user?.branch?.name}</div>
        </div>

        <div className="flex-1 p-4 flex flex-col">
          <div className="space-y-3 mb-6">
            <div className="flex justify-between text-gray-400">
              <span>Subtotal</span>
              <span>{formatRupiah(subtotal)}</span>
            </div>
            
            {/* Auto-applied discounts from engine */}
            {appliedDiscounts.length > 0 && (
              <div className="flex justify-between items-center text-amber-400">
                <span className="flex items-center gap-1">
                  <Tag className="h-3 w-3" />
                  Diskon Otomatis ({appliedDiscounts.length})
                </span>
                <span>-{formatRupiah(engineDiscount)}</span>
              </div>
            )}
            
            {/* Promotions */}
            {appliedPromos.length > 0 && (
              <div className="bg-green-900/20 border border-green-700/30 rounded p-2">
                <span className="text-xs text-green-400 flex items-center gap-1 mb-1">
                  <Gift className="h-3 w-3" /> Promo Aktif:
                </span>
                {appliedPromos.map((promo, idx) => (
                  <div key={idx} className="text-xs text-green-300">
                    {promo.promo_name}: {promo.benefit?.description}
                  </div>
                ))}
              </div>
            )}
            
            {/* Free items from promo */}
            {freeItems.length > 0 && (
              <div className="bg-green-900/20 border border-green-700/30 rounded p-2">
                <span className="text-xs text-green-400 flex items-center gap-1 mb-1">
                  <Sparkles className="h-3 w-3" /> Item Gratis:
                </span>
                {freeItems.map((item, idx) => (
                  <div key={idx} className="text-xs text-green-300">
                    {item.quantity}x {item.product_name}
                  </div>
                ))}
              </div>
            )}
            
            {/* Manual discount */}
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Diskon Manual</span>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  value={discountPercent}
                  onChange={(e) => setDiscountPercent(Math.max(0, Math.min(100, Number(e.target.value))))}
                  className="w-16 px-2 py-1 bg-[#1a1214] border border-red-900/30 rounded text-right"
                />
                <span>%</span>
              </div>
            </div>
            {discountAmount > 0 && (
              <div className="flex justify-between text-red-400">
                <span>Total Potongan</span>
                <span>-{formatRupiah(discountAmount)}</span>
              </div>
            )}
            
            {/* Customer price level indicator */}
            {customer && customerPriceLevel > 1 && (
              <div className="text-xs text-amber-400 flex items-center gap-1">
                <Tag className="h-3 w-3" />
                Harga Level {customerPriceLevel} ({customer.name})
              </div>
            )}
            
            {/* Calculating indicator */}
            {calculatingPricing && (
              <div className="text-xs text-gray-400 flex items-center gap-1">
                <Loader2 className="h-3 w-3 animate-spin" />
                Menghitung diskon & promo...
              </div>
            )}
          </div>

          <div className="mt-auto">
            <div className="flex justify-between text-2xl font-bold mb-6">
              <span>TOTAL</span>
              <span className="text-amber-400">{formatRupiah(total)}</span>
            </div>

            <div className="grid grid-cols-2 gap-2 mb-4">
              <button onClick={holdTransaction} disabled={cart.length === 0} className="py-3 bg-amber-600/20 text-amber-400 rounded-lg hover:bg-amber-600/30 disabled:opacity-50 flex items-center justify-center gap-2">
                <Clock className="h-5 w-5" /> Tahan
              </button>
              <button onClick={clearCart} disabled={cart.length === 0} className="py-3 bg-red-600/20 text-red-400 rounded-lg hover:bg-red-600/30 disabled:opacity-50 flex items-center justify-center gap-2">
                <X className="h-5 w-5" /> Batal
              </button>
            </div>

            <button
              onClick={() => { if (cart.length === 0) return; setPayments([]); setShowPaymentModal(true); }}
              disabled={cart.length === 0}
              className="w-full py-4 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg font-bold text-lg hover:from-red-500 hover:to-amber-500 disabled:opacity-50 flex items-center justify-center gap-2"
            >
              <CreditCard className="h-6 w-6" /> BAYAR SEKARANG
            </button>
          </div>
        </div>
      </div>

      {/* Modal Pembayaran */}
      {showPaymentModal && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-lg p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-bold">Pembayaran</h2>
              <button onClick={() => setShowPaymentModal(false)} className="text-gray-400 hover:text-white"><X className="h-6 w-6" /></button>
            </div>

            <div className="text-center mb-6">
              <div className="text-gray-400">Total Tagihan</div>
              <div className="text-3xl font-bold text-amber-400">{formatRupiah(total)}</div>
            </div>

            <div className="grid grid-cols-4 gap-2 mb-6">
              <button onClick={() => addPayment('cash')} className="p-3 bg-green-600/20 text-green-400 rounded-lg hover:bg-green-600/30 flex flex-col items-center gap-1">
                <Banknote className="h-6 w-6" /><span className="text-xs">Tunai</span>
              </button>
              <button onClick={() => addPayment('qris')} className="p-3 bg-purple-600/20 text-purple-400 rounded-lg hover:bg-purple-600/30 flex flex-col items-center gap-1">
                <QrCode className="h-6 w-6" /><span className="text-xs">QRIS</span>
              </button>
              <button onClick={() => addPayment('bank_transfer')} className="p-3 bg-blue-600/20 text-blue-400 rounded-lg hover:bg-blue-600/30 flex flex-col items-center gap-1">
                <CreditCard className="h-6 w-6" /><span className="text-xs">Transfer</span>
              </button>
              <button onClick={() => addPayment('ewallet')} className="p-3 bg-amber-600/20 text-amber-400 rounded-lg hover:bg-amber-600/30 flex flex-col items-center gap-1">
                <Wallet className="h-6 w-6" /><span className="text-xs">E-Wallet</span>
              </button>
            </div>

            {payments.length > 0 && (
              <div className="space-y-2 mb-6">
                {payments.map((p, idx) => (
                  <div key={idx} className="flex items-center gap-2 bg-[#0a0608] p-3 rounded-lg">
                    <span className="flex-1">{paymentLabels[p.method]}</span>
                    <input
                      type="number"
                      value={p.amount}
                      onChange={(e) => { const newPayments = [...payments]; newPayments[idx].amount = Number(e.target.value); setPayments(newPayments); }}
                      className="w-32 px-2 py-1 bg-[#1a1214] border border-red-900/30 rounded text-right"
                    />
                    <button onClick={() => setPayments(payments.filter((_, i) => i !== idx))} className="text-red-400 hover:text-red-300"><X className="h-5 w-5" /></button>
                  </div>
                ))}
              </div>
            )}

            <div className="border-t border-red-900/30 pt-4 mb-6">
              <div className="flex justify-between mb-2">
                <span className="text-gray-400">Dibayar</span>
                <span className="text-green-400">{formatRupiah(payments.reduce((s, p) => s + p.amount, 0))}</span>
              </div>
              <div className="flex justify-between text-lg font-bold">
                <span>Kembalian</span>
                <span className="text-amber-400">{formatRupiah(Math.max(0, payments.reduce((s, p) => s + p.amount, 0) - total))}</span>
              </div>
            </div>

            <button
              onClick={processPayment}
              disabled={processing || payments.reduce((s, p) => s + p.amount, 0) < total}
              className="w-full py-4 bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-lg font-bold text-lg disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {processing ? <Loader2 className="h-6 w-6 animate-spin" /> : <Check className="h-6 w-6" />}
              {processing ? 'Memproses...' : 'Selesaikan Transaksi'}
            </button>
          </div>
        </div>
      )}

      {/* Modal Sukses */}
      {showSuccessModal && lastInvoice && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-md p-6 text-center">
            <div className="w-16 h-16 bg-green-600/20 rounded-full flex items-center justify-center mx-auto mb-4">
              <Check className="h-8 w-8 text-green-400" />
            </div>
            <h2 className="text-xl font-bold mb-2">Transaksi Berhasil!</h2>
            <p className="text-gray-400 mb-4">No. Invoice: {lastInvoice.invoice_number}</p>
            
            <div className="bg-[#0a0608] rounded-lg p-4 mb-6 text-left">
              <div className="flex justify-between mb-2">
                <span className="text-gray-400">Total</span>
                <span className="font-bold">{formatRupiah(lastInvoice.total)}</span>
              </div>
              <div className="flex justify-between mb-2">
                <span className="text-gray-400">Dibayar</span>
                <span>{formatRupiah(lastInvoice.paid)}</span>
              </div>
              <div className="flex justify-between text-lg font-bold">
                <span>Kembalian</span>
                <span className="text-amber-400">{formatRupiah(lastInvoice.change)}</span>
              </div>
            </div>

            <div className="flex gap-3">
              <button 
                onClick={() => handlePrintReceipt(lastInvoice)}
                data-testid="print-receipt-btn"
                className="flex-1 py-3 bg-blue-600/20 text-blue-400 rounded-lg hover:bg-blue-600/30 flex items-center justify-center gap-2"
              >
                <Printer className="h-5 w-5" /> Cetak Struk
              </button>
              <button 
                onClick={() => handleShareWhatsApp(lastInvoice)}
                data-testid="share-whatsapp-btn"
                className="flex-1 py-3 bg-green-600/20 text-green-400 rounded-lg hover:bg-green-600/30 flex items-center justify-center gap-2"
              >
                <MessageCircle className="h-5 w-5" /> WhatsApp
              </button>
            </div>
            <button onClick={() => setShowSuccessModal(false)} className="w-full mt-3 py-3 border border-red-900/30 rounded-lg hover:bg-red-900/20">
              Tutup
            </button>
          </div>
        </div>
      )}

      {/* Modal Pelanggan */}
      {showCustomerModal && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-md p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">Pilih Pelanggan</h2>
              <button onClick={() => setShowCustomerModal(false)} className="text-gray-400 hover:text-white"><X className="h-6 w-6" /></button>
            </div>
            <input
              type="text"
              placeholder="Cari nama atau nomor HP..."
              value={customerSearch}
              onChange={(e) => { setCustomerSearch(e.target.value); searchCustomers(e.target.value); }}
              className="w-full px-4 py-3 bg-[#0a0608] border border-red-900/30 rounded-lg mb-4"
            />
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {customerResults.map(c => (
                <button
                  key={c.id}
                  onClick={() => handleCustomerSelect(c)}
                  className="w-full p-3 bg-[#0a0608] rounded-lg hover:bg-red-900/20 text-left"
                >
                  <div className="font-medium">{c.name}</div>
                  <div className="text-sm text-gray-400">{c.phone} • {c.segment}</div>
                </button>
              ))}
            </div>
            {customer && (
              <button onClick={() => { setCustomer(null); setCustomerPriceLevel(1); setShowCustomerModal(false); }} className="w-full mt-4 py-2 border border-red-900/30 rounded-lg text-red-400 hover:bg-red-900/20">
                Hapus Pelanggan
              </button>
            )}
          </div>
        </div>
      )}

      {/* Modal Transaksi Ditahan */}
      {showHeldModal && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-md p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">Transaksi Ditahan</h2>
              <button onClick={() => setShowHeldModal(false)} className="text-gray-400 hover:text-white"><X className="h-6 w-6" /></button>
            </div>
            {heldTransactions.length === 0 ? (
              <div className="text-center text-gray-400 py-8">Tidak ada transaksi ditahan</div>
            ) : (
              <div className="space-y-2 max-h-80 overflow-y-auto">
                {heldTransactions.map(held => (
                  <button key={held.id} onClick={() => recallTransaction(held)} className="w-full p-3 bg-[#0a0608] rounded-lg hover:bg-amber-900/20 text-left">
                    <div className="font-medium">{held.hold_name}</div>
                    <div className="text-sm text-gray-400">{held.items?.length || 0} item • {new Date(held.created_at).toLocaleTimeString('id-ID')}</div>
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
