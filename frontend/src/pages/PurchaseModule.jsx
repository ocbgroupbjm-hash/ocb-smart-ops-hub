import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { 
  Plus, Search, Eye, Printer, Edit, Trash2, Save, X, Loader2,
  FileText, Package, Truck, CreditCard, RotateCcw, History,
  Calendar, Check, ChevronDown, ChevronRight, RefreshCw,
  Download, Upload, Filter, Building2
} from 'lucide-react';
import { toast } from 'sonner';

// ==================== UTILITY FUNCTIONS ====================
const formatRupiah = (num) => `Rp ${(num || 0).toLocaleString('id-ID')}`;
const formatDate = (date) => date ? new Date(date).toLocaleDateString('id-ID') : '-';
const formatDateTime = (date) => date ? new Date(date).toLocaleString('id-ID') : '-';

// ==================== SUB-COMPONENTS ====================
// Tab Navigation
const TabButton = ({ active, onClick, icon: Icon, label, count }) => (
  <button
    onClick={onClick}
    data-testid={`tab-${label.toLowerCase().replace(/\s/g, '-')}`}
    className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-colors ${
      active 
        ? 'border-blue-500 text-blue-400 bg-blue-500/10' 
        : 'border-transparent text-gray-400 hover:text-gray-200 hover:bg-gray-800/50'
    }`}
  >
    <Icon className="h-4 w-4" />
    <span className="text-sm font-medium">{label}</span>
    {count !== undefined && (
      <span className={`px-2 py-0.5 rounded-full text-xs ${active ? 'bg-blue-500 text-white' : 'bg-gray-700 text-gray-300'}`}>
        {count}
      </span>
    )}
  </button>
);

// Status Badge
const StatusBadge = ({ status }) => {
  const styles = {
    draft: 'bg-gray-600 text-gray-100',
    ordered: 'bg-blue-600 text-blue-100',
    partial: 'bg-yellow-600 text-yellow-100',
    received: 'bg-green-600 text-green-100',
    cancelled: 'bg-red-600 text-red-100',
    unpaid: 'bg-red-600 text-red-100',
    partial_paid: 'bg-yellow-600 text-yellow-100',
    paid: 'bg-green-600 text-green-100',
    open: 'bg-blue-600 text-blue-100',
  };
  return (
    <span className={`px-2 py-1 rounded text-xs font-medium ${styles[status] || 'bg-gray-600'}`}>
      {status?.toUpperCase() || 'N/A'}
    </span>
  );
};

// ==================== MAIN COMPONENT ====================
const PurchaseModule = () => {
  const { api, user } = useAuth();
  const [activeTab, setActiveTab] = useState('orders');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  
  // Data States
  const [orders, setOrders] = useState([]);
  const [purchases, setPurchases] = useState([]);
  const [payments, setPayments] = useState([]);
  const [returns, setReturns] = useState([]);
  const [priceHistory, setPriceHistory] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [products, setProducts] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [payables, setPayables] = useState([]);
  
  // Filter States
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [supplierFilter, setSupplierFilter] = useState('');
  
  // Modal States
  const [showCreatePO, setShowCreatePO] = useState(false);
  const [showReceiveModal, setShowReceiveModal] = useState(false);
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [showReturnModal, setShowReturnModal] = useState(false);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);
  
  // Form States
  const [poForm, setPoForm] = useState({
    supplier_id: '',
    warehouse_id: '',
    expected_date: '',
    notes: '',
    ppn_percent: 11,
    is_credit: true,
    credit_due_days: 30,
    items: []
  });
  
  const [receiveForm, setReceiveForm] = useState({ items: [], notes: '' });
  const [paymentForm, setPaymentForm] = useState({
    supplier_id: '',
    payment_method: 'transfer',
    bank_id: '',
    reference: '',
    notes: '',
    selected_invoices: []
  });
  const [returnForm, setReturnForm] = useState({
    supplier_id: '',
    purchase_id: '',
    notes: '',
    items: []
  });

  // ==================== DATA LOADING ====================
  const loadMasterData = useCallback(async () => {
    try {
      const [supRes, prodRes, whRes] = await Promise.all([
        api('/api/suppliers'),
        api('/api/products?limit=1000'),
        api('/api/master/warehouses')
      ]);
      if (supRes.ok) setSuppliers((await supRes.json()).items || await supRes.json() || []);
      if (prodRes.ok) setProducts((await prodRes.json()).items || []);
      if (whRes.ok) setWarehouses((await whRes.json()) || []);
    } catch (err) {
      console.error('Error loading master data:', err);
    }
  }, [api]);

  const loadOrders = useCallback(async () => {
    try {
      const params = new URLSearchParams();
      if (statusFilter) params.append('status', statusFilter);
      if (supplierFilter) params.append('supplier_id', supplierFilter);
      params.append('limit', '200');
      
      const res = await api(`/api/purchase/orders?${params}`);
      if (res.ok) {
        const data = await res.json();
        setOrders(data.items || data || []);
      }
    } catch (err) {
      toast.error('Gagal memuat data pesanan');
    }
  }, [api, statusFilter, supplierFilter]);

  const loadPurchases = useCallback(async () => {
    try {
      const params = new URLSearchParams();
      params.append('limit', '200');
      if (supplierFilter) params.append('supplier_id', supplierFilter);
      
      const res = await api(`/api/purchase/orders?status=received&${params}`);
      if (res.ok) {
        const data = await res.json();
        setPurchases(data.items || data || []);
      }
    } catch (err) {
      console.error(err);
    }
  }, [api, supplierFilter]);

  const loadPayments = useCallback(async () => {
    try {
      const res = await api('/api/purchase/payments?limit=200');
      if (res.ok) {
        const data = await res.json();
        setPayments(data.items || data || []);
      }
    } catch (err) {
      console.error(err);
    }
  }, [api]);

  const loadReturns = useCallback(async () => {
    try {
      const res = await api('/api/purchase/returns?limit=200');
      if (res.ok) {
        const data = await res.json();
        setReturns(data.items || data || []);
      }
    } catch (err) {
      console.error(err);
    }
  }, [api]);

  const loadPriceHistory = useCallback(async () => {
    try {
      const res = await api('/api/purchase/price-history?limit=500');
      if (res.ok) {
        const data = await res.json();
        setPriceHistory(data.items || data || []);
      }
    } catch (err) {
      console.error(err);
    }
  }, [api]);

  const loadPayables = useCallback(async () => {
    try {
      const res = await api('/api/ap/list?status=unpaid&limit=200');
      if (res.ok) {
        const data = await res.json();
        setPayables(data.items || data || []);
      }
    } catch (err) {
      console.error(err);
    }
  }, [api]);

  // Initial load
  useEffect(() => {
    setLoading(true);
    loadMasterData();
    loadOrders();
    loadPayments();
    loadReturns();
    loadPriceHistory();
    loadPayables();
    setLoading(false);
  }, []);

  // Reload on filter change
  useEffect(() => {
    if (activeTab === 'orders') loadOrders();
    if (activeTab === 'purchases') loadPurchases();
  }, [statusFilter, supplierFilter, activeTab]);

  // ==================== FORM HANDLERS ====================
  const resetPoForm = () => {
    setPoForm({
      supplier_id: '',
      warehouse_id: '',
      expected_date: '',
      notes: '',
      ppn_percent: 11,
      is_credit: true,
      credit_due_days: 30,
      items: []
    });
  };

  const addItemToPO = (product) => {
    if (poForm.items.find(i => i.product_id === product.id)) {
      toast.error('Item sudah ada dalam daftar');
      return;
    }
    setPoForm(prev => ({
      ...prev,
      items: [...prev.items, {
        product_id: product.id,
        product_code: product.code,
        product_name: product.name,
        item_type: product.item_type || 'barang',
        quantity: 1,
        unit: product.unit || 'PCS',
        unit_cost: product.cost_price || 0,
        discount_percent: 0,
        tax_percent: 0
      }]
    }));
  };

  const updatePoItem = (index, field, value) => {
    setPoForm(prev => ({
      ...prev,
      items: prev.items.map((item, i) => 
        i === index ? { ...item, [field]: value } : item
      )
    }));
  };

  const removePoItem = (index) => {
    setPoForm(prev => ({
      ...prev,
      items: prev.items.filter((_, i) => i !== index)
    }));
  };

  const calculatePoTotals = () => {
    let subtotal = 0;
    let totalDiscount = 0;
    let totalTax = 0;
    
    poForm.items.forEach(item => {
      const itemSubtotal = item.quantity * item.unit_cost;
      const itemDiscount = itemSubtotal * (item.discount_percent / 100);
      const itemTax = (itemSubtotal - itemDiscount) * (item.tax_percent / 100);
      
      subtotal += itemSubtotal;
      totalDiscount += itemDiscount;
      totalTax += itemTax;
    });
    
    const ppn = (subtotal - totalDiscount) * (poForm.ppn_percent / 100);
    const total = subtotal - totalDiscount + ppn + totalTax;
    
    return { subtotal, totalDiscount, ppn, totalTax, total };
  };

  // ==================== API HANDLERS ====================
  const handleCreatePO = async (e) => {
    e.preventDefault();
    if (!poForm.supplier_id) {
      toast.error('Pilih supplier terlebih dahulu');
      return;
    }
    if (poForm.items.length === 0) {
      toast.error('Tambahkan minimal 1 item');
      return;
    }

    setSaving(true);
    try {
      const res = await api('/api/purchase/orders', {
        method: 'POST',
        body: JSON.stringify({
          supplier_id: poForm.supplier_id,
          branch_id: poForm.warehouse_id,
          expected_date: poForm.expected_date,
          notes: poForm.notes,
          is_credit: poForm.is_credit,
          credit_due_days: poForm.credit_due_days,
          items: poForm.items.map(item => ({
            product_id: item.product_id,
            quantity: parseInt(item.quantity),
            unit_cost: parseFloat(item.unit_cost),
            discount_percent: parseFloat(item.discount_percent || 0)
          }))
        })
      });

      if (res.ok) {
        const result = await res.json();
        toast.success(`PO ${result.po_number} berhasil dibuat`);
        setShowCreatePO(false);
        resetPoForm();
        loadOrders();
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Gagal membuat PO');
      }
    } catch (err) {
      toast.error('Terjadi kesalahan');
    } finally {
      setSaving(false);
    }
  };

  const handleSubmitPO = async (order) => {
    if (!window.confirm(`Kirim PO ${order.po_number} ke supplier?`)) return;
    
    try {
      const res = await api(`/api/purchase/orders/${order.id}/submit`, { method: 'POST' });
      if (res.ok) {
        toast.success('PO berhasil dikirim ke supplier');
        loadOrders();
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Gagal submit PO');
      }
    } catch (err) {
      toast.error('Terjadi kesalahan');
    }
  };

  const handleCancelPO = async (order) => {
    if (!window.confirm(`Batalkan PO ${order.po_number}?`)) return;
    
    try {
      const res = await api(`/api/purchase/orders/${order.id}/cancel`, { method: 'POST' });
      if (res.ok) {
        toast.success('PO dibatalkan');
        loadOrders();
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Gagal membatalkan PO');
      }
    } catch (err) {
      toast.error('Terjadi kesalahan');
    }
  };

  const openReceiveModal = (order) => {
    setSelectedItem(order);
    setReceiveForm({
      items: order.items.map(item => ({
        product_id: item.product_id,
        product_name: item.product_name,
        ordered_qty: item.quantity,
        received_qty: item.received_qty || 0,
        receive_now: Math.max(0, item.quantity - (item.received_qty || 0))
      })),
      notes: ''
    });
    setShowReceiveModal(true);
  };

  const handleReceivePO = async () => {
    const itemsToReceive = receiveForm.items
      .filter(item => item.receive_now > 0)
      .map(item => ({
        product_id: item.product_id,
        quantity: parseInt(item.receive_now)
      }));

    if (itemsToReceive.length === 0) {
      toast.error('Tidak ada item yang diterima');
      return;
    }

    setSaving(true);
    try {
      const res = await api(`/api/purchase/orders/${selectedItem.id}/receive`, {
        method: 'POST',
        body: JSON.stringify({ items: itemsToReceive, notes: receiveForm.notes })
      });

      if (res.ok) {
        const result = await res.json();
        toast.success('Barang berhasil diterima');
        if (result.ap_created) {
          toast.info('Hutang dagang otomatis terbentuk');
        }
        setShowReceiveModal(false);
        loadOrders();
        loadPurchases();
        loadPayables();
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Gagal menerima barang');
      }
    } catch (err) {
      toast.error('Terjadi kesalahan');
    } finally {
      setSaving(false);
    }
  };

  const openPaymentModal = () => {
    setPaymentForm({
      supplier_id: '',
      payment_method: 'transfer',
      bank_id: '',
      reference: '',
      notes: '',
      selected_invoices: []
    });
    loadPayables();
    setShowPaymentModal(true);
  };

  const handleCreatePayment = async () => {
    if (!paymentForm.supplier_id) {
      toast.error('Pilih supplier');
      return;
    }
    if (paymentForm.selected_invoices.length === 0) {
      toast.error('Pilih minimal 1 hutang untuk dibayar');
      return;
    }

    const totalPayment = paymentForm.selected_invoices.reduce((sum, inv) => sum + (inv.pay_amount || 0), 0);
    if (totalPayment <= 0) {
      toast.error('Total pembayaran harus lebih dari 0');
      return;
    }

    setSaving(true);
    try {
      // Create payment for each selected invoice
      for (const invoice of paymentForm.selected_invoices) {
        if (invoice.pay_amount > 0) {
          await api('/api/purchase/payments', {
            method: 'POST',
            body: JSON.stringify({
              po_id: invoice.source_id,
              amount: invoice.pay_amount,
              payment_method: paymentForm.payment_method,
              bank_id: paymentForm.bank_id,
              reference: paymentForm.reference,
              notes: paymentForm.notes
            })
          });
        }
      }
      
      toast.success('Pembayaran berhasil dicatat');
      setShowPaymentModal(false);
      loadPayments();
      loadPayables();
    } catch (err) {
      toast.error('Gagal mencatat pembayaran');
    } finally {
      setSaving(false);
    }
  };

  const openReturnModal = () => {
    setReturnForm({
      supplier_id: '',
      purchase_id: '',
      notes: '',
      items: []
    });
    setShowReturnModal(true);
  };

  const handleCreateReturn = async () => {
    if (!returnForm.supplier_id || returnForm.items.length === 0) {
      toast.error('Lengkapi data retur');
      return;
    }

    setSaving(true);
    try {
      const res = await api('/api/purchase/returns', {
        method: 'POST',
        body: JSON.stringify(returnForm)
      });

      if (res.ok) {
        toast.success('Retur pembelian berhasil dicatat');
        setShowReturnModal(false);
        loadReturns();
        loadPayables();
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Gagal membuat retur');
      }
    } catch (err) {
      toast.error('Terjadi kesalahan');
    } finally {
      setSaving(false);
    }
  };

  // Filter data based on search
  const filteredOrders = orders.filter(order => {
    const matchSearch = !searchTerm || 
      order.po_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      order.supplier_name?.toLowerCase().includes(searchTerm.toLowerCase());
    return matchSearch;
  });

  const filteredPayables = payables.filter(p => 
    !paymentForm.supplier_id || p.supplier_id === paymentForm.supplier_id
  );

  // ==================== RENDER FUNCTIONS ====================
  const renderOrdersTab = () => (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex flex-wrap gap-3 items-center justify-between">
        <div className="flex gap-2 flex-1 max-w-xl">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Cari no transaksi, supplier..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white"
            />
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white"
          >
            <option value="">Semua Status</option>
            <option value="draft">Draft</option>
            <option value="ordered">Ordered</option>
            <option value="partial">Partial</option>
            <option value="received">Received</option>
            <option value="cancelled">Cancelled</option>
          </select>
          <select
            value={supplierFilter}
            onChange={(e) => setSupplierFilter(e.target.value)}
            className="px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white"
          >
            <option value="">Semua Supplier</option>
            {suppliers.map(s => (
              <option key={s.id} value={s.id}>{s.name}</option>
            ))}
          </select>
        </div>
        <button
          onClick={() => setShowCreatePO(true)}
          data-testid="btn-create-po"
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-white"
        >
          <Plus className="h-4 w-4" /> Tambah PO
        </button>
      </div>

      {/* Table */}
      <div className="bg-gray-800/50 rounded-lg border border-gray-700 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-800">
              <tr className="text-left text-gray-400 text-sm">
                <th className="p-3">No Transaksi</th>
                <th className="p-3">Tanggal</th>
                <th className="p-3">Tgl Kirim</th>
                <th className="p-3">Supplier</th>
                <th className="p-3 text-right">Jml Pesan</th>
                <th className="p-3 text-right">Jml Terima</th>
                <th className="p-3 text-right">Total</th>
                <th className="p-3">Status</th>
                <th className="p-3">User</th>
                <th className="p-3 text-center">Aksi</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700">
              {loading ? (
                <tr><td colSpan="10" className="p-8 text-center text-gray-400">
                  <Loader2 className="h-6 w-6 animate-spin mx-auto" />
                </td></tr>
              ) : filteredOrders.length === 0 ? (
                <tr><td colSpan="10" className="p-8 text-center text-gray-400">
                  Tidak ada data pesanan pembelian
                </td></tr>
              ) : filteredOrders.map(order => {
                const totalOrdered = order.items?.reduce((sum, i) => sum + i.quantity, 0) || 0;
                const totalReceived = order.items?.reduce((sum, i) => sum + (i.received_qty || 0), 0) || 0;
                return (
                  <tr key={order.id} className="hover:bg-gray-800/50">
                    <td className="p-3 font-medium text-blue-400">{order.po_number}</td>
                    <td className="p-3 text-sm">{formatDate(order.created_at)}</td>
                    <td className="p-3 text-sm">{formatDate(order.expected_date)}</td>
                    <td className="p-3">{order.supplier_name}</td>
                    <td className="p-3 text-right">{totalOrdered}</td>
                    <td className="p-3 text-right">{totalReceived}</td>
                    <td className="p-3 text-right font-medium">{formatRupiah(order.total)}</td>
                    <td className="p-3"><StatusBadge status={order.status} /></td>
                    <td className="p-3 text-sm text-gray-400">{order.user_name || '-'}</td>
                    <td className="p-3">
                      <div className="flex justify-center gap-1">
                        <button
                          onClick={() => { setSelectedItem(order); setShowDetailModal(true); }}
                          className="p-1.5 hover:bg-gray-700 rounded"
                          title="Detail"
                        >
                          <Eye className="h-4 w-4 text-gray-400" />
                        </button>
                        {order.status === 'draft' && (
                          <>
                            <button
                              onClick={() => handleSubmitPO(order)}
                              className="p-1.5 hover:bg-blue-700 rounded"
                              title="Kirim ke Supplier"
                            >
                              <Truck className="h-4 w-4 text-blue-400" />
                            </button>
                            <button
                              onClick={() => handleCancelPO(order)}
                              className="p-1.5 hover:bg-red-700 rounded"
                              title="Batalkan"
                            >
                              <X className="h-4 w-4 text-red-400" />
                            </button>
                          </>
                        )}
                        {['ordered', 'partial'].includes(order.status) && (
                          <button
                            onClick={() => openReceiveModal(order)}
                            className="p-1.5 hover:bg-green-700 rounded"
                            title="Terima Barang"
                          >
                            <Package className="h-4 w-4 text-green-400" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );

  const renderPurchasesTab = () => (
    <div className="space-y-4">
      <div className="flex gap-3 items-center justify-between">
        <div className="flex gap-2">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Cari transaksi..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white"
            />
          </div>
          <select
            value={supplierFilter}
            onChange={(e) => setSupplierFilter(e.target.value)}
            className="px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white"
          >
            <option value="">Semua Supplier</option>
            {suppliers.map(s => (
              <option key={s.id} value={s.id}>{s.name}</option>
            ))}
          </select>
        </div>
        <button
          onClick={() => loadPurchases()}
          className="flex items-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-white"
        >
          <RefreshCw className="h-4 w-4" /> Refresh
        </button>
      </div>

      <div className="bg-gray-800/50 rounded-lg border border-gray-700 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-800">
              <tr className="text-left text-gray-400 text-sm">
                <th className="p-3">No Transaksi</th>
                <th className="p-3">Tanggal</th>
                <th className="p-3">Supplier</th>
                <th className="p-3">Gudang</th>
                <th className="p-3">Keterangan</th>
                <th className="p-3 text-right">Total</th>
                <th className="p-3">PPN</th>
                <th className="p-3">User</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700">
              {purchases.length === 0 ? (
                <tr><td colSpan="8" className="p-8 text-center text-gray-400">
                  Tidak ada data pembelian yang sudah diterima
                </td></tr>
              ) : purchases.map(p => (
                <tr key={p.id} className="hover:bg-gray-800/50">
                  <td className="p-3 font-medium text-blue-400">{p.po_number}</td>
                  <td className="p-3 text-sm">{formatDate(p.received_date || p.updated_at)}</td>
                  <td className="p-3">{p.supplier_name}</td>
                  <td className="p-3">{p.branch_name || '-'}</td>
                  <td className="p-3 text-sm text-gray-400">{p.notes || '-'}</td>
                  <td className="p-3 text-right font-medium">{formatRupiah(p.total)}</td>
                  <td className="p-3">{p.ppn_percent || 0}%</td>
                  <td className="p-3 text-sm text-gray-400">{p.user_name || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );

  const renderPaymentsTab = () => (
    <div className="space-y-4">
      <div className="flex gap-3 items-center justify-between">
        <div className="flex gap-2">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Cari pembayaran..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white"
            />
          </div>
        </div>
        <button
          onClick={openPaymentModal}
          data-testid="btn-create-payment"
          className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg text-white"
        >
          <Plus className="h-4 w-4" /> Tambah Pembayaran
        </button>
      </div>

      <div className="bg-gray-800/50 rounded-lg border border-gray-700 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-800">
              <tr className="text-left text-gray-400 text-sm">
                <th className="p-3">No Transaksi</th>
                <th className="p-3">Tanggal</th>
                <th className="p-3">Cara Bayar</th>
                <th className="p-3">Supplier</th>
                <th className="p-3">Referensi</th>
                <th className="p-3">Keterangan</th>
                <th className="p-3 text-right">Total</th>
                <th className="p-3">User</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700">
              {payments.length === 0 ? (
                <tr><td colSpan="8" className="p-8 text-center text-gray-400">
                  Tidak ada data pembayaran hutang
                </td></tr>
              ) : payments.map(p => (
                <tr key={p.id} className="hover:bg-gray-800/50">
                  <td className="p-3 font-medium text-green-400">{p.payment_number || p.id?.slice(0,8)}</td>
                  <td className="p-3 text-sm">{formatDate(p.created_at)}</td>
                  <td className="p-3">{p.payment_method?.toUpperCase()}</td>
                  <td className="p-3">{p.supplier_name || '-'}</td>
                  <td className="p-3 text-sm">{p.reference || '-'}</td>
                  <td className="p-3 text-sm text-gray-400">{p.notes || '-'}</td>
                  <td className="p-3 text-right font-medium text-green-400">{formatRupiah(p.amount)}</td>
                  <td className="p-3 text-sm text-gray-400">{p.user_name || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );

  const renderReturnsTab = () => (
    <div className="space-y-4">
      <div className="flex gap-3 items-center justify-between">
        <div className="flex gap-2">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Cari retur..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white"
            />
          </div>
        </div>
        <button
          onClick={openReturnModal}
          data-testid="btn-create-return"
          className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg text-white"
        >
          <Plus className="h-4 w-4" /> Tambah Retur
        </button>
      </div>

      <div className="bg-gray-800/50 rounded-lg border border-gray-700 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-800">
              <tr className="text-left text-gray-400 text-sm">
                <th className="p-3">No Transaksi</th>
                <th className="p-3">Tanggal</th>
                <th className="p-3">Supplier</th>
                <th className="p-3">Keterangan</th>
                <th className="p-3 text-right">Total</th>
                <th className="p-3">User</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700">
              {returns.length === 0 ? (
                <tr><td colSpan="6" className="p-8 text-center text-gray-400">
                  Tidak ada data retur pembelian
                </td></tr>
              ) : returns.map(r => (
                <tr key={r.id} className="hover:bg-gray-800/50">
                  <td className="p-3 font-medium text-red-400">{r.return_number || r.id?.slice(0,8)}</td>
                  <td className="p-3 text-sm">{formatDate(r.created_at)}</td>
                  <td className="p-3">{r.supplier_name || '-'}</td>
                  <td className="p-3 text-sm text-gray-400">{r.notes || '-'}</td>
                  <td className="p-3 text-right font-medium text-red-400">{formatRupiah(r.total)}</td>
                  <td className="p-3 text-sm text-gray-400">{r.user_name || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );

  const renderPriceHistoryTab = () => (
    <div className="space-y-4">
      <div className="flex gap-3 items-center">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Cari item atau supplier..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white"
          />
        </div>
      </div>

      <div className="bg-gray-800/50 rounded-lg border border-gray-700 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-800">
              <tr className="text-left text-gray-400 text-sm">
                <th className="p-3">Supplier</th>
                <th className="p-3">No Transaksi</th>
                <th className="p-3">Tanggal</th>
                <th className="p-3">Kode Item</th>
                <th className="p-3">Nama Item</th>
                <th className="p-3">Satuan</th>
                <th className="p-3 text-right">Harga</th>
                <th className="p-3 text-right">Jumlah</th>
                <th className="p-3 text-right">Potongan</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700">
              {priceHistory.length === 0 ? (
                <tr><td colSpan="9" className="p-8 text-center text-gray-400">
                  Tidak ada history harga beli
                </td></tr>
              ) : priceHistory.filter(h => 
                !searchTerm || 
                h.product_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                h.supplier_name?.toLowerCase().includes(searchTerm.toLowerCase())
              ).map((h, idx) => (
                <tr key={idx} className="hover:bg-gray-800/50">
                  <td className="p-3">{h.supplier_name || '-'}</td>
                  <td className="p-3 text-blue-400">{h.po_number || '-'}</td>
                  <td className="p-3 text-sm">{formatDate(h.date)}</td>
                  <td className="p-3 font-mono text-sm">{h.product_code}</td>
                  <td className="p-3">{h.product_name}</td>
                  <td className="p-3">{h.unit || 'PCS'}</td>
                  <td className="p-3 text-right font-medium">{formatRupiah(h.unit_cost)}</td>
                  <td className="p-3 text-right">{h.quantity}</td>
                  <td className="p-3 text-right">{h.discount_percent || 0}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );

  const renderPayablesTab = () => (
    <div className="space-y-4">
      <div className="flex gap-3 items-center justify-between">
        <div className="flex gap-2">
          <select
            value={supplierFilter}
            onChange={(e) => setSupplierFilter(e.target.value)}
            className="px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white"
          >
            <option value="">Semua Supplier</option>
            {suppliers.map(s => (
              <option key={s.id} value={s.id}>{s.name}</option>
            ))}
          </select>
        </div>
        <button
          onClick={openPaymentModal}
          className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg text-white"
        >
          <CreditCard className="h-4 w-4" /> Bayar Hutang
        </button>
      </div>

      <div className="bg-gray-800/50 rounded-lg border border-gray-700 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-800">
              <tr className="text-left text-gray-400 text-sm">
                <th className="p-3">No AP</th>
                <th className="p-3">Supplier</th>
                <th className="p-3">No Referensi</th>
                <th className="p-3">Tanggal</th>
                <th className="p-3">Jatuh Tempo</th>
                <th className="p-3 text-right">Jumlah</th>
                <th className="p-3 text-right">Dibayar</th>
                <th className="p-3 text-right">Sisa</th>
                <th className="p-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700">
              {payables.filter(p => !supplierFilter || p.supplier_id === supplierFilter).length === 0 ? (
                <tr><td colSpan="9" className="p-8 text-center text-gray-400">
                  Tidak ada hutang dagang
                </td></tr>
              ) : payables.filter(p => !supplierFilter || p.supplier_id === supplierFilter).map(p => (
                <tr key={p.id} className="hover:bg-gray-800/50">
                  <td className="p-3 font-medium text-orange-400">{p.ap_number}</td>
                  <td className="p-3">{p.supplier_name}</td>
                  <td className="p-3 text-blue-400">{p.source_number}</td>
                  <td className="p-3 text-sm">{formatDate(p.created_at)}</td>
                  <td className="p-3 text-sm">{formatDate(p.due_date)}</td>
                  <td className="p-3 text-right font-medium">{formatRupiah(p.amount)}</td>
                  <td className="p-3 text-right text-green-400">{formatRupiah(p.paid_amount)}</td>
                  <td className="p-3 text-right font-medium text-red-400">{formatRupiah(p.amount - p.paid_amount)}</td>
                  <td className="p-3"><StatusBadge status={p.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );

  // ==================== MODALS ====================
  const renderCreatePOModal = () => {
    const totals = calculatePoTotals();
    const selectedSupplier = suppliers.find(s => s.id === poForm.supplier_id);
    
    return (
      <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
        <div className="bg-gray-900 rounded-xl w-full max-w-6xl max-h-[90vh] overflow-hidden flex flex-col">
          <div className="p-4 border-b border-gray-700 flex justify-between items-center">
            <h2 className="text-lg font-semibold">Tambah Pesanan Pembelian</h2>
            <button onClick={() => setShowCreatePO(false)} className="p-1 hover:bg-gray-700 rounded">
              <X className="h-5 w-5" />
            </button>
          </div>
          
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {/* Header Form */}
            <div className="grid grid-cols-4 gap-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Supplier *</label>
                <select
                  value={poForm.supplier_id}
                  onChange={(e) => setPoForm({ ...poForm, supplier_id: e.target.value })}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white"
                  data-testid="select-supplier"
                >
                  <option value="">Pilih Supplier</option>
                  {suppliers.map(s => (
                    <option key={s.id} value={s.id}>{s.code} - {s.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Gudang Tujuan</label>
                <select
                  value={poForm.warehouse_id}
                  onChange={(e) => setPoForm({ ...poForm, warehouse_id: e.target.value })}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white"
                >
                  <option value="">Pilih Gudang</option>
                  {warehouses.map(w => (
                    <option key={w.id} value={w.id}>{w.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Tanggal Kirim</label>
                <input
                  type="date"
                  value={poForm.expected_date}
                  onChange={(e) => setPoForm({ ...poForm, expected_date: e.target.value })}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">PPN %</label>
                <input
                  type="number"
                  value={poForm.ppn_percent}
                  onChange={(e) => setPoForm({ ...poForm, ppn_percent: parseFloat(e.target.value) || 0 })}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white"
                />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="is_credit"
                  checked={poForm.is_credit}
                  onChange={(e) => setPoForm({ ...poForm, is_credit: e.target.checked })}
                  className="w-4 h-4 rounded"
                />
                <label htmlFor="is_credit" className="text-sm">Kredit/Hutang</label>
              </div>
              {poForm.is_credit && (
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Jatuh Tempo (hari)</label>
                  <input
                    type="number"
                    value={poForm.credit_due_days}
                    onChange={(e) => setPoForm({ ...poForm, credit_due_days: parseInt(e.target.value) || 30 })}
                    className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white"
                  />
                </div>
              )}
              <div>
                <label className="block text-sm text-gray-400 mb-1">Keterangan</label>
                <input
                  type="text"
                  value={poForm.notes}
                  onChange={(e) => setPoForm({ ...poForm, notes: e.target.value })}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white"
                  placeholder="Catatan..."
                />
              </div>
            </div>

            {/* Product Search */}
            <div className="border border-gray-700 rounded-lg p-3">
              <label className="block text-sm text-gray-400 mb-2">Cari & Tambah Item</label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Ketik kode atau nama item..."
                  className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      const found = products.find(p => 
                        p.code?.toLowerCase() === e.target.value.toLowerCase() ||
                        p.name?.toLowerCase().includes(e.target.value.toLowerCase())
                      );
                      if (found) {
                        addItemToPO(found);
                        e.target.value = '';
                      }
                    }
                  }}
                />
              </div>
              <div className="mt-2 max-h-32 overflow-y-auto">
                <div className="grid grid-cols-4 gap-1">
                  {products.slice(0, 20).map(p => (
                    <button
                      key={p.id}
                      onClick={() => addItemToPO(p)}
                      className="text-left px-2 py-1 text-xs bg-gray-800 hover:bg-gray-700 rounded truncate"
                    >
                      {p.code} - {p.name}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Items Table */}
            <div className="border border-gray-700 rounded-lg overflow-hidden">
              <table className="w-full">
                <thead className="bg-gray-800">
                  <tr className="text-left text-gray-400 text-sm">
                    <th className="p-2">Kode</th>
                    <th className="p-2">Nama Item</th>
                    <th className="p-2">Jenis</th>
                    <th className="p-2 text-right">Qty</th>
                    <th className="p-2">Satuan</th>
                    <th className="p-2 text-right">Harga</th>
                    <th className="p-2 text-right">Pot %</th>
                    <th className="p-2 text-right">Tax %</th>
                    <th className="p-2 text-right">Total</th>
                    <th className="p-2"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-700">
                  {poForm.items.length === 0 ? (
                    <tr><td colSpan="10" className="p-4 text-center text-gray-400">
                      Belum ada item. Cari dan tambahkan item di atas.
                    </td></tr>
                  ) : poForm.items.map((item, idx) => {
                    const itemSubtotal = item.quantity * item.unit_cost;
                    const discount = itemSubtotal * (item.discount_percent / 100);
                    const total = itemSubtotal - discount;
                    return (
                      <tr key={idx}>
                        <td className="p-2 font-mono text-sm">{item.product_code}</td>
                        <td className="p-2">{item.product_name}</td>
                        <td className="p-2 text-sm">{item.item_type}</td>
                        <td className="p-2">
                          <input
                            type="number"
                            min="1"
                            value={item.quantity}
                            onChange={(e) => updatePoItem(idx, 'quantity', parseInt(e.target.value) || 1)}
                            className="w-16 px-2 py-1 bg-gray-800 border border-gray-600 rounded text-right"
                          />
                        </td>
                        <td className="p-2 text-sm">{item.unit}</td>
                        <td className="p-2">
                          <input
                            type="number"
                            min="0"
                            value={item.unit_cost}
                            onChange={(e) => updatePoItem(idx, 'unit_cost', parseFloat(e.target.value) || 0)}
                            className="w-28 px-2 py-1 bg-gray-800 border border-gray-600 rounded text-right"
                          />
                        </td>
                        <td className="p-2">
                          <input
                            type="number"
                            min="0"
                            max="100"
                            value={item.discount_percent}
                            onChange={(e) => updatePoItem(idx, 'discount_percent', parseFloat(e.target.value) || 0)}
                            className="w-16 px-2 py-1 bg-gray-800 border border-gray-600 rounded text-right"
                          />
                        </td>
                        <td className="p-2">
                          <input
                            type="number"
                            min="0"
                            max="100"
                            value={item.tax_percent}
                            onChange={(e) => updatePoItem(idx, 'tax_percent', parseFloat(e.target.value) || 0)}
                            className="w-16 px-2 py-1 bg-gray-800 border border-gray-600 rounded text-right"
                          />
                        </td>
                        <td className="p-2 text-right font-medium">{formatRupiah(total)}</td>
                        <td className="p-2">
                          <button
                            onClick={() => removePoItem(idx)}
                            className="p-1 hover:bg-red-700 rounded"
                          >
                            <Trash2 className="h-4 w-4 text-red-400" />
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Totals */}
            <div className="flex justify-end">
              <div className="w-80 space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-400">Sub Total Item:</span>
                  <span>{formatRupiah(totals.subtotal)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Potongan:</span>
                  <span className="text-red-400">-{formatRupiah(totals.totalDiscount)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">PPN ({poForm.ppn_percent}%):</span>
                  <span>{formatRupiah(totals.ppn)}</span>
                </div>
                <div className="flex justify-between border-t border-gray-700 pt-2 text-lg font-bold">
                  <span>Total Akhir:</span>
                  <span className="text-green-400">{formatRupiah(totals.total)}</span>
                </div>
              </div>
            </div>
          </div>

          <div className="p-4 border-t border-gray-700 flex justify-end gap-3">
            <button
              onClick={() => setShowCreatePO(false)}
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg"
            >
              Batal
            </button>
            <button
              onClick={handleCreatePO}
              disabled={saving}
              className="flex items-center gap-2 px-6 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg disabled:opacity-50"
            >
              {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
              Simpan PO
            </button>
          </div>
        </div>
      </div>
    );
  };

  const renderReceiveModal = () => {
    if (!selectedItem) return null;
    
    return (
      <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
        <div className="bg-gray-900 rounded-xl w-full max-w-4xl max-h-[80vh] overflow-hidden flex flex-col">
          <div className="p-4 border-b border-gray-700 flex justify-between items-center">
            <div>
              <h2 className="text-lg font-semibold">Terima Barang</h2>
              <p className="text-sm text-gray-400">PO: {selectedItem.po_number} - {selectedItem.supplier_name}</p>
            </div>
            <button onClick={() => setShowReceiveModal(false)} className="p-1 hover:bg-gray-700 rounded">
              <X className="h-5 w-5" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-4">
            <table className="w-full">
              <thead className="bg-gray-800">
                <tr className="text-left text-gray-400 text-sm">
                  <th className="p-3">Produk</th>
                  <th className="p-3 text-right">Qty Pesan</th>
                  <th className="p-3 text-right">Sudah Diterima</th>
                  <th className="p-3 text-right">Terima Sekarang</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {receiveForm.items.map((item, idx) => (
                  <tr key={idx}>
                    <td className="p-3">{item.product_name}</td>
                    <td className="p-3 text-right">{item.ordered_qty}</td>
                    <td className="p-3 text-right text-green-400">{item.received_qty}</td>
                    <td className="p-3 text-right">
                      <input
                        type="number"
                        min="0"
                        max={item.ordered_qty - item.received_qty}
                        value={item.receive_now}
                        onChange={(e) => {
                          const newItems = [...receiveForm.items];
                          newItems[idx].receive_now = parseInt(e.target.value) || 0;
                          setReceiveForm({ ...receiveForm, items: newItems });
                        }}
                        className="w-20 px-2 py-1 bg-gray-800 border border-gray-600 rounded text-right"
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            <div className="mt-4">
              <label className="block text-sm text-gray-400 mb-1">Catatan</label>
              <textarea
                value={receiveForm.notes}
                onChange={(e) => setReceiveForm({ ...receiveForm, notes: e.target.value })}
                className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white"
                rows="2"
              />
            </div>
          </div>

          <div className="p-4 border-t border-gray-700 flex justify-end gap-3">
            <button
              onClick={() => setShowReceiveModal(false)}
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg"
            >
              Batal
            </button>
            <button
              onClick={handleReceivePO}
              disabled={saving}
              className="flex items-center gap-2 px-6 py-2 bg-green-600 hover:bg-green-700 rounded-lg disabled:opacity-50"
            >
              {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />}
              Konfirmasi Terima
            </button>
          </div>
        </div>
      </div>
    );
  };

  const renderPaymentModal = () => (
    <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
      <div className="bg-gray-900 rounded-xl w-full max-w-5xl max-h-[85vh] overflow-hidden flex flex-col">
        <div className="p-4 border-b border-gray-700 flex justify-between items-center">
          <h2 className="text-lg font-semibold">Tambah Pembayaran Hutang</h2>
          <button onClick={() => setShowPaymentModal(false)} className="p-1 hover:bg-gray-700 rounded">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          <div className="grid grid-cols-4 gap-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Supplier *</label>
              <select
                value={paymentForm.supplier_id}
                onChange={(e) => setPaymentForm({ ...paymentForm, supplier_id: e.target.value, selected_invoices: [] })}
                className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white"
              >
                <option value="">Pilih Supplier</option>
                {suppliers.map(s => (
                  <option key={s.id} value={s.id}>{s.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Cara Bayar</label>
              <select
                value={paymentForm.payment_method}
                onChange={(e) => setPaymentForm({ ...paymentForm, payment_method: e.target.value })}
                className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white"
              >
                <option value="transfer">Transfer Bank</option>
                <option value="cash">Tunai</option>
                <option value="giro">Giro</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">No Referensi</label>
              <input
                type="text"
                value={paymentForm.reference}
                onChange={(e) => setPaymentForm({ ...paymentForm, reference: e.target.value })}
                className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Keterangan</label>
              <input
                type="text"
                value={paymentForm.notes}
                onChange={(e) => setPaymentForm({ ...paymentForm, notes: e.target.value })}
                className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white"
              />
            </div>
          </div>

          <div className="border border-gray-700 rounded-lg overflow-hidden">
            <div className="bg-gray-800 p-2 text-sm font-medium">Daftar Hutang</div>
            <table className="w-full">
              <thead className="bg-gray-800/50">
                <tr className="text-left text-gray-400 text-xs">
                  <th className="p-2">Pilih</th>
                  <th className="p-2">No Transaksi</th>
                  <th className="p-2">Tanggal</th>
                  <th className="p-2">Jatuh Tempo</th>
                  <th className="p-2 text-right">Sisa Hutang</th>
                  <th className="p-2 text-right">Potongan</th>
                  <th className="p-2 text-right">Jumlah Bayar</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {filteredPayables.length === 0 ? (
                  <tr><td colSpan="7" className="p-4 text-center text-gray-400">
                    {paymentForm.supplier_id ? 'Tidak ada hutang untuk supplier ini' : 'Pilih supplier terlebih dahulu'}
                  </td></tr>
                ) : filteredPayables.map(inv => {
                  const selected = paymentForm.selected_invoices.find(s => s.id === inv.id);
                  const remaining = inv.amount - (inv.paid_amount || 0);
                  return (
                    <tr key={inv.id}>
                      <td className="p-2">
                        <input
                          type="checkbox"
                          checked={!!selected}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setPaymentForm(prev => ({
                                ...prev,
                                selected_invoices: [...prev.selected_invoices, { ...inv, pay_amount: remaining, discount: 0 }]
                              }));
                            } else {
                              setPaymentForm(prev => ({
                                ...prev,
                                selected_invoices: prev.selected_invoices.filter(s => s.id !== inv.id)
                              }));
                            }
                          }}
                          className="w-4 h-4 rounded"
                        />
                      </td>
                      <td className="p-2 text-blue-400 text-sm">{inv.source_number}</td>
                      <td className="p-2 text-xs">{formatDate(inv.created_at)}</td>
                      <td className="p-2 text-xs">{formatDate(inv.due_date)}</td>
                      <td className="p-2 text-right text-red-400">{formatRupiah(remaining)}</td>
                      <td className="p-2">
                        {selected && (
                          <input
                            type="number"
                            min="0"
                            value={selected.discount || 0}
                            onChange={(e) => {
                              setPaymentForm(prev => ({
                                ...prev,
                                selected_invoices: prev.selected_invoices.map(s => 
                                  s.id === inv.id ? { ...s, discount: parseFloat(e.target.value) || 0 } : s
                                )
                              }));
                            }}
                            className="w-24 px-2 py-1 bg-gray-800 border border-gray-600 rounded text-right text-sm"
                          />
                        )}
                      </td>
                      <td className="p-2">
                        {selected && (
                          <input
                            type="number"
                            min="0"
                            max={remaining}
                            value={selected.pay_amount || 0}
                            onChange={(e) => {
                              setPaymentForm(prev => ({
                                ...prev,
                                selected_invoices: prev.selected_invoices.map(s => 
                                  s.id === inv.id ? { ...s, pay_amount: parseFloat(e.target.value) || 0 } : s
                                )
                              }));
                            }}
                            className="w-32 px-2 py-1 bg-gray-800 border border-gray-600 rounded text-right text-sm"
                          />
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <div className="flex justify-end">
            <div className="w-64 space-y-1 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-400">Total Potongan:</span>
                <span className="text-green-400">
                  {formatRupiah(paymentForm.selected_invoices.reduce((sum, inv) => sum + (inv.discount || 0), 0))}
                </span>
              </div>
              <div className="flex justify-between font-bold text-lg">
                <span>Total Bayar:</span>
                <span className="text-blue-400">
                  {formatRupiah(paymentForm.selected_invoices.reduce((sum, inv) => sum + (inv.pay_amount || 0), 0))}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="p-4 border-t border-gray-700 flex justify-end gap-3">
          <button
            onClick={() => setShowPaymentModal(false)}
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg"
          >
            Batal
          </button>
          <button
            onClick={handleCreatePayment}
            disabled={saving}
            className="flex items-center gap-2 px-6 py-2 bg-green-600 hover:bg-green-700 rounded-lg disabled:opacity-50"
          >
            {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
            Simpan Pembayaran
          </button>
        </div>
      </div>
    </div>
  );

  const renderDetailModal = () => {
    if (!selectedItem) return null;
    
    return (
      <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
        <div className="bg-gray-900 rounded-xl w-full max-w-4xl max-h-[80vh] overflow-hidden flex flex-col">
          <div className="p-4 border-b border-gray-700 flex justify-between items-center">
            <div>
              <h2 className="text-lg font-semibold">Detail PO: {selectedItem.po_number}</h2>
              <p className="text-sm text-gray-400">{selectedItem.supplier_name}</p>
            </div>
            <div className="flex items-center gap-3">
              <StatusBadge status={selectedItem.status} />
              <button onClick={() => setShowDetailModal(false)} className="p-1 hover:bg-gray-700 rounded">
                <X className="h-5 w-5" />
              </button>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            <div className="grid grid-cols-4 gap-4 text-sm">
              <div>
                <span className="text-gray-400">Tanggal:</span>
                <p>{formatDateTime(selectedItem.created_at)}</p>
              </div>
              <div>
                <span className="text-gray-400">Tanggal Kirim:</span>
                <p>{formatDate(selectedItem.expected_date)}</p>
              </div>
              <div>
                <span className="text-gray-400">Kredit:</span>
                <p>{selectedItem.is_credit ? `Ya (${selectedItem.credit_due_days} hari)` : 'Tunai'}</p>
              </div>
              <div>
                <span className="text-gray-400">Total:</span>
                <p className="font-bold text-green-400">{formatRupiah(selectedItem.total)}</p>
              </div>
            </div>

            <table className="w-full">
              <thead className="bg-gray-800">
                <tr className="text-left text-gray-400 text-sm">
                  <th className="p-3">Kode</th>
                  <th className="p-3">Nama Item</th>
                  <th className="p-3 text-right">Qty Pesan</th>
                  <th className="p-3 text-right">Qty Terima</th>
                  <th className="p-3 text-right">Harga</th>
                  <th className="p-3 text-right">Subtotal</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {selectedItem.items?.map((item, idx) => (
                  <tr key={idx}>
                    <td className="p-3 font-mono text-sm">{item.product_code}</td>
                    <td className="p-3">{item.product_name}</td>
                    <td className="p-3 text-right">{item.quantity}</td>
                    <td className="p-3 text-right text-green-400">{item.received_qty || 0}</td>
                    <td className="p-3 text-right">{formatRupiah(item.unit_cost)}</td>
                    <td className="p-3 text-right font-medium">{formatRupiah(item.subtotal)}</td>
                  </tr>
                ))}
              </tbody>
            </table>

            {selectedItem.notes && (
              <div className="p-3 bg-gray-800 rounded-lg">
                <span className="text-gray-400 text-sm">Catatan:</span>
                <p>{selectedItem.notes}</p>
              </div>
            )}
          </div>

          <div className="p-4 border-t border-gray-700 flex justify-end">
            <button
              onClick={() => setShowDetailModal(false)}
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg"
            >
              Tutup
            </button>
          </div>
        </div>
      </div>
    );
  };

  // ==================== MAIN RENDER ====================
  return (
    <div className="min-h-screen bg-gray-900 text-white p-6" data-testid="purchase-module">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold flex items-center gap-3">
            <Truck className="h-7 w-7 text-blue-400" />
            Modul Pembelian
          </h1>
          <p className="text-gray-400 text-sm mt-1">Kelola pesanan pembelian, penerimaan barang, hutang dan pembayaran</p>
        </div>

        {/* Tab Navigation */}
        <div className="flex overflow-x-auto border-b border-gray-700 mb-6">
          <TabButton
            active={activeTab === 'orders'}
            onClick={() => setActiveTab('orders')}
            icon={FileText}
            label="Pesanan Pembelian"
            count={orders.length}
          />
          <TabButton
            active={activeTab === 'purchases'}
            onClick={() => { setActiveTab('purchases'); loadPurchases(); }}
            icon={Package}
            label="Daftar Pembelian"
            count={purchases.length}
          />
          <TabButton
            active={activeTab === 'price-history'}
            onClick={() => setActiveTab('price-history')}
            icon={History}
            label="History Harga"
          />
          <TabButton
            active={activeTab === 'payables'}
            onClick={() => { setActiveTab('payables'); loadPayables(); }}
            icon={CreditCard}
            label="Daftar Hutang"
            count={payables.length}
          />
          <TabButton
            active={activeTab === 'payments'}
            onClick={() => { setActiveTab('payments'); loadPayments(); }}
            icon={CreditCard}
            label="Pembayaran Hutang"
            count={payments.length}
          />
          <TabButton
            active={activeTab === 'returns'}
            onClick={() => { setActiveTab('returns'); loadReturns(); }}
            icon={RotateCcw}
            label="Retur Pembelian"
            count={returns.length}
          />
        </div>

        {/* Tab Content */}
        {activeTab === 'orders' && renderOrdersTab()}
        {activeTab === 'purchases' && renderPurchasesTab()}
        {activeTab === 'price-history' && renderPriceHistoryTab()}
        {activeTab === 'payables' && renderPayablesTab()}
        {activeTab === 'payments' && renderPaymentsTab()}
        {activeTab === 'returns' && renderReturnsTab()}

        {/* Modals */}
        {showCreatePO && renderCreatePOModal()}
        {showReceiveModal && renderReceiveModal()}
        {showPaymentModal && renderPaymentModal()}
        {showDetailModal && renderDetailModal()}
      </div>
    </div>
  );
};

export default PurchaseModule;
