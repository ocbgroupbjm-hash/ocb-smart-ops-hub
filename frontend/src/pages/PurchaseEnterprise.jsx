import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { 
  Plus, Search, Eye, Printer, Edit, Trash2, Save, X, Loader2, FileText, 
  Package, Truck, CreditCard, RotateCcw, History, Calendar, Check, 
  ChevronDown, RefreshCw, Filter, Building2, AlertTriangle, Hash, 
  Barcode, Tag, User, Clock, FileCheck, Percent, DollarSign, Warehouse,
  StickyNote, Copy, ArrowUpDown, Download, Upload, ChevronLeft, ChevronRight,
  Banknote
} from 'lucide-react';
import { toast } from 'sonner';
import { formatDateDisplay, formatDateInput, getDefaultFilterDates, getTodayISO } from '../utils/dateUtils';
import { SearchableSelect } from '../components/ui/searchable-select';

// ==================== UTILITY FUNCTIONS ====================
const formatRupiah = (num) => `Rp ${(num || 0).toLocaleString('id-ID')}`;
const formatNumber = (num) => (num || 0).toLocaleString('id-ID');
const formatDate = (date) => formatDateDisplay(date, '-');
const formatDateTime = (date) => date ? new Date(date).toLocaleString('id-ID') : '-';
const formatTime = (date) => date ? new Date(date).toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' }) : '-';

// ==================== STATUS BADGE COMPONENT ====================
const StatusBadge = ({ status }) => {
  const styles = {
    draft: 'bg-gray-600/20 text-gray-300 border-gray-500/30',
    approved: 'bg-blue-600/20 text-blue-300 border-blue-500/30',
    pending: 'bg-yellow-600/20 text-yellow-300 border-yellow-500/30',
    posted: 'bg-green-600/20 text-green-300 border-green-500/30',
    ordered: 'bg-blue-600/20 text-blue-300 border-blue-500/30',
    partial: 'bg-amber-600/20 text-amber-300 border-amber-500/30',
    received: 'bg-green-600/20 text-green-300 border-green-500/30',
    cancelled: 'bg-red-600/20 text-red-300 border-red-500/30',
    lunas: 'bg-green-600/20 text-green-300 border-green-500/30',
    belum_lunas: 'bg-red-600/20 text-red-300 border-red-500/30',
    partial_paid: 'bg-yellow-600/20 text-yellow-300 border-yellow-500/30',
    retur_sebagian: 'bg-purple-600/20 text-purple-300 border-purple-500/30',
    retur_penuh: 'bg-pink-600/20 text-pink-300 border-pink-500/30',
    batal: 'bg-red-600/20 text-red-300 border-red-500/30',
  };
  const statusLabels = {
    draft: 'Draft', approved: 'Approved', pending: 'Pending', posted: 'Posted',
    ordered: 'Ordered', partial: 'Partial', received: 'Received', cancelled: 'Batal',
    lunas: 'Lunas', belum_lunas: 'Belum Lunas', partial_paid: 'Sebagian',
    retur_sebagian: 'Retur Sebagian', retur_penuh: 'Retur Penuh', batal: 'Batal'
  };
  return (
    <span className={`px-2 py-0.5 rounded border text-xs font-medium ${styles[status] || 'bg-gray-600/20 text-gray-300 border-gray-500/30'}`}>
      {statusLabels[status] || status?.toUpperCase() || 'N/A'}
    </span>
  );
};

// ==================== TAB BUTTON COMPONENT ====================
const TabButton = ({ active, onClick, label, count }) => (
  <button
    onClick={onClick}
    data-testid={`tab-${label.toLowerCase().replace(/\s/g, '-')}`}
    className={`px-4 py-2 text-sm font-medium transition-all border-b-2 ${
      active 
        ? 'border-blue-500 text-blue-400 bg-blue-500/5' 
        : 'border-transparent text-gray-400 hover:text-gray-200 hover:bg-gray-800/50'
    }`}
  >
    {label}
    {count !== undefined && count > 0 && (
      <span className="ml-2 px-1.5 py-0.5 text-xs bg-gray-700 rounded">{count}</span>
    )}
  </button>
);

// ==================== INPUT FIELD COMPONENT ====================
const InputField = ({ label, value, onChange, type = 'text', placeholder, required, disabled, className = '', options, icon: Icon }) => (
  <div className={className}>
    <label className="block text-xs text-gray-400 mb-1">
      {label} {required && <span className="text-red-400">*</span>}
    </label>
    <div className="relative">
      {Icon && <Icon className="absolute left-2 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-gray-500" />}
      {type === 'select' ? (
        <select
          value={value}
          onChange={(e) => onChange(e.target.value)}
          disabled={disabled}
          className={`w-full px-3 py-1.5 bg-gray-800 border border-gray-700 rounded text-sm text-white disabled:opacity-50 ${Icon ? 'pl-8' : ''}`}
        >
          <option value="">{placeholder || `Pilih ${label}`}</option>
          {options?.map((opt, idx) => (
            <option key={opt.value || idx} value={opt.value}>{opt.label}</option>
          ))}
        </select>
      ) : type === 'textarea' ? (
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          disabled={disabled}
          rows={2}
          className={`w-full px-3 py-1.5 bg-gray-800 border border-gray-700 rounded text-sm text-white disabled:opacity-50 ${Icon ? 'pl-8' : ''}`}
        />
      ) : (
        <input
          type={type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          disabled={disabled}
          className={`w-full px-3 py-1.5 bg-gray-800 border border-gray-700 rounded text-sm text-white disabled:opacity-50 ${Icon ? 'pl-8' : ''}`}
        />
      )}
    </div>
  </div>
);

// ==================== MAIN COMPONENT ====================
const PurchaseEnterprise = () => {
  const { api, user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const itemInputRef = useRef(null);
  
  // View mode: 'list' or 'form'
  const [viewMode, setViewMode] = useState('list');
  const [editingId, setEditingId] = useState(null);
  
  // Master data
  const [suppliers, setSuppliers] = useState([]);
  const [products, setProducts] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [branches, setBranches] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [paymentAccounts, setPaymentAccounts] = useState([]);
  
  // Bottom tab state
  const [activeBottomTab, setActiveBottomTab] = useState('rincian');
  
  // Filter states
  const [filters, setFilters] = useState({
    keyword: '', dateFrom: '', dateTo: '', supplier_id: '', branch_id: '',
    warehouse_id: '', status: '', payment_status: '', user_id: '',
    sales_id: '', item_id: '', invoice_no: '', tax_invoice: ''
  });
  
  // Transaction form state (HEADER)
  const [form, setForm] = useState({
    // Header fields
    transaction_no: '',        // Auto generated
    date: new Date().toISOString().split('T')[0],
    time: new Date().toTimeString().slice(0, 5),
    supplier_id: '',
    warehouse_id: '',
    branch_id: '',
    sales_person_id: '',       // PIC
    payment_account_id: '',    // Akun Pembayaran (Kas/Bank)
    dept: '',
    po_reference: '',
    transaction_type: 'direct', // direct, from_po, from_request, transfer
    ppn_percent: 11,
    user_id: '',
    notes: '',
    
    // Items
    items: [],
    
    // Footer calculation
    subtotal: 0,
    discount_percent: 0,
    discount_amount: 0,
    tax_amount: 0,
    other_cost: 0,
    shipping_cost: 0,
    rounding: 0,
    dp_amount: 0,
    deposit_amount: 0,
    grand_total: 0,
    
    // Payment
    cash_amount: 0,
    credit_amount: 0,
    remaining_debt: 0,
    payment_type: 'credit',    // cash, credit, dp, deposit, combo
    credit_due_days: 30,
    
    // Status
    status: 'draft',
    payment_status: 'belum_lunas'
  });
  
  // Selected item for history tabs
  const [selectedItemForHistory, setSelectedItemForHistory] = useState(null);
  const [priceHistory, setPriceHistory] = useState([]);
  const [supplierHistory, setSupplierHistory] = useState([]);
  
  // ==================== DATA LOADING ====================
  const loadMasterData = useCallback(async () => {
    try {
      const [supRes, prodRes, whRes, branchRes, empRes, accRes] = await Promise.all([
        api('/api/suppliers'),
        api('/api/products?limit=2000'),
        api('/api/master/warehouses'),
        api('/api/branches'),
        api('/api/erp/employees?status=active'),
        api('/api/accounts/cash-bank')
      ]);
      
      if (supRes.ok) {
        const data = await supRes.json();
        setSuppliers(data.items || data || []);
      }
      if (prodRes.ok) {
        const data = await prodRes.json();
        setProducts(data.items || data || []);
      }
      if (whRes.ok) {
        const data = await whRes.json();
        setWarehouses(data || []);
        
        // TASK 6: Auto-select default warehouse for user's branch
        const userBranch = user?.branch_id;
        if (userBranch) {
          const defaultWarehouse = (data || []).find(w => w.branch_id === userBranch);
          if (defaultWarehouse) {
            setForm(prev => ({ ...prev, warehouse_id: defaultWarehouse.id, branch_id: userBranch }));
          }
        }
      }
      if (branchRes.ok) {
        const data = await branchRes.json();
        setBranches(data || []);
      }
      if (empRes.ok) {
        const data = await empRes.json();
        setEmployees(data.employees || data.items || data || []);
      }
      if (accRes.ok) {
        const data = await accRes.json();
        setPaymentAccounts(data.accounts || data.items || data || []);
      }
    } catch (err) {
      console.error('Error loading master data:', err);
      toast.error('Gagal memuat data master');
    }
  }, [api]);
  
  const loadTransactions = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filters.status) params.append('status', filters.status);
      if (filters.supplier_id) params.append('supplier_id', filters.supplier_id);
      params.append('limit', '500');
      
      const res = await api(`/api/purchase/orders?${params}`);
      if (res.ok) {
        const data = await res.json();
        setTransactions(data.items || data || []);
      }
    } catch (err) {
      console.error('Error loading transactions:', err);
      toast.error('Gagal memuat data transaksi');
    } finally {
      setLoading(false);
    }
  }, [api, filters]);
  
  const loadPriceHistory = useCallback(async (productId, supplierId) => {
    try {
      const params = new URLSearchParams();
      if (productId) params.append('product_id', productId);
      const res = await api(`/api/purchase/price-history?${params}`);
      if (res.ok) {
        const data = await res.json();
        setPriceHistory(data.items || data || []);
        
        // Filter for supplier history
        if (supplierId) {
          setSupplierHistory(
            (data.items || data || []).filter(h => h.supplier_id === supplierId)
          );
        }
      }
    } catch (err) {
      console.error('Error loading price history:', err);
    }
  }, [api]);
  
  useEffect(() => {
    loadMasterData();
    loadTransactions();
  }, [loadMasterData, loadTransactions]);
  
  // ==================== GENERATE TRANSACTION NUMBER ====================
  const generateTransactionNo = useCallback(() => {
    const branchCode = branches.find(b => b.id === form.branch_id)?.code || 'HQ';
    const dateStr = new Date().toISOString().slice(0, 10).replace(/-/g, '');
    const seq = String(Math.floor(Math.random() * 9999) + 1).padStart(4, '0');
    return `PO-${branchCode}-${dateStr}-${seq}`;
  }, [branches, form.branch_id]);
  
  // ==================== FORM HANDLERS ====================
  const resetForm = () => {
    setForm({
      transaction_no: '',
      date: new Date().toISOString().split('T')[0],
      time: new Date().toTimeString().slice(0, 5),
      supplier_id: '',
      warehouse_id: warehouses[0]?.id || '',
      branch_id: user?.branch_id || branches[0]?.id || '',
      sales_person_id: '',
      payment_account_id: '',
      dept: '',
      po_reference: '',
      transaction_type: 'direct',
      ppn_percent: 11,
      user_id: user?.user_id || '',
      notes: '',
      items: [],
      subtotal: 0,
      discount_percent: 0,
      discount_amount: 0,
      tax_amount: 0,
      other_cost: 0,
      shipping_cost: 0,
      rounding: 0,
      dp_amount: 0,
      deposit_amount: 0,
      grand_total: 0,
      cash_amount: 0,
      credit_amount: 0,
      remaining_debt: 0,
      payment_type: 'credit',
      credit_due_days: 30,
      status: 'draft',
      payment_status: 'belum_lunas'
    });
    setSelectedItemForHistory(null);
    setPriceHistory([]);
    setSupplierHistory([]);
  };
  
  const handleNewTransaction = () => {
    resetForm();
    setEditingId(null);
    setViewMode('form');
    setTimeout(() => {
      setForm(prev => ({ ...prev, transaction_no: generateTransactionNo() }));
    }, 100);
  };
  
  const handleEditTransaction = (tx) => {
    // ============================================================
    // EDIT POLICY (Blueprint v2.4.6):
    // BOLEH EDIT: draft, ordered (belum ada receiving/stock/AP/jurnal)
    // TIDAK BOLEH EDIT: partial, received, cancelled, deleted
    // ============================================================
    const editableStatuses = ['draft', 'ordered'];
    const blockedStatuses = ['partial', 'received', 'cancelled', 'deleted', 'posted', 'completed', 'lunas', 'approved'];
    
    const currentStatus = tx.status?.toLowerCase();
    
    if (blockedStatuses.includes(currentStatus)) {
      let reason = '';
      if (currentStatus === 'partial') {
        reason = 'PO sudah ada penerimaan sebagian. Gunakan fitur Koreksi jika perlu perubahan.';
      } else if (currentStatus === 'received') {
        reason = 'PO sudah selesai diterima. Data tidak bisa diubah untuk menjaga integritas audit trail.';
      } else if (currentStatus === 'cancelled' || currentStatus === 'deleted') {
        reason = 'PO sudah dibatalkan/dihapus. Tidak bisa diedit.';
      } else {
        reason = 'Transaksi sudah di-POST. Gunakan fitur Koreksi/Reversal.';
      }
      
      toast.error(reason, { duration: 4000 });
      return;
    }
    
    if (!editableStatuses.includes(currentStatus)) {
      toast.error(`Status "${currentStatus}" tidak dapat diedit.`, { duration: 3000 });
      return;
    }
    
    // Map PO data to form
    setForm({
      ...tx,
      transaction_no: tx.po_number || tx.transaction_no,
      date: tx.created_at?.split('T')[0] || tx.order_date?.split('T')[0] || new Date().toISOString().split('T')[0],
      time: tx.created_at ? new Date(tx.created_at).toTimeString().slice(0, 5) : new Date().toTimeString().slice(0, 5),
      supplier_id: tx.supplier_id || '',
      warehouse_id: tx.warehouse_id || '',
      branch_id: tx.branch_id || '',
      sales_person_id: tx.pic_id || tx.sales_person_id || '',
      payment_account_id: tx.payment_account_id || '',
      items: tx.items || [],
      subtotal: tx.subtotal || 0,
      grand_total: tx.total || 0,
      notes: tx.notes || ''
    });
    setEditingId(tx.id);
    setViewMode('form');
    toast.info(`Edit PO ${tx.po_number} - Status: ${currentStatus.toUpperCase()}`);
  };
  
  // ============================================================
  // CHECK IF PO CAN BE EDITED (for UI display)
  // ============================================================
  const canEditPO = (tx) => {
    const editableStatuses = ['draft', 'ordered'];
    return editableStatuses.includes(tx.status?.toLowerCase());
  };
  
  // ============================================================
  // PRINT PO - TASK 3: Template Print Bersih
  // ============================================================
  const [showPrintModal, setShowPrintModal] = useState(false);
  const [printData, setPrintData] = useState(null);
  
  const handlePrintPO = async (tx) => {
    try {
      // Fetch print data from backend
      const res = await api(`/api/purchase/orders/${tx.id}/print`);
      if (res.ok) {
        const data = await res.json();
        setPrintData(data);
        setShowPrintModal(true);
      } else {
        toast.error('Gagal mengambil data untuk print');
      }
    } catch (err) {
      console.error('Print error:', err);
      toast.error('Terjadi kesalahan saat memuat data print');
    }
  };
  
  const printPODocument = () => {
    window.print();
  };
  
  // ============================================================
  // DELETE PO - TASK 2: Delete Policy
  // ============================================================
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleteReason, setDeleteReason] = useState('');
  const [deletePreview, setDeletePreview] = useState(null);
  
  const handleDeletePO = async (tx) => {
    try {
      // Get delete preview first
      const res = await api(`/api/purchase/orders/${tx.id}/delete-preview`);
      if (res.ok) {
        const preview = await res.json();
        setDeleteTarget(tx);
        setDeletePreview(preview);
        setShowDeleteModal(true);
      } else {
        toast.error('Gagal memuat preview penghapusan');
      }
    } catch (err) {
      console.error('Delete preview error:', err);
      toast.error('Terjadi kesalahan');
    }
  };
  
  const confirmDeletePO = async () => {
    if (!deleteTarget) return;
    
    try {
      const res = await api(`/api/purchase/orders/${deleteTarget.id}?reason=${encodeURIComponent(deleteReason)}`, {
        method: 'DELETE'
      });
      
      if (res.ok) {
        const result = await res.json();
        toast.success(result.message);
        setShowDeleteModal(false);
        setDeleteTarget(null);
        setDeleteReason('');
        setDeletePreview(null);
        loadTransactions();
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Gagal menghapus PO');
      }
    } catch (err) {
      console.error('Delete error:', err);
      toast.error('Terjadi kesalahan saat menghapus');
    }
  };
  
  const handleReversalTransaction = (tx) => {
    // Handle reversal for posted transactions
    toast.info(`Memproses koreksi/reversal untuk ${tx.po_number || tx.transaction_no}...`);
    // TODO: Implement reversal flow via BRE
  };
  
  // ==================== ITEM MANAGEMENT ====================
  const addItem = (product) => {
    if (form.items.find(i => i.product_id === product.id)) {
      toast.error('Item sudah ada dalam daftar');
      return;
    }
    
    // Load price history for this item
    loadPriceHistory(product.id, form.supplier_id);
    setSelectedItemForHistory(product);
    
    // Find last purchase price from history
    const lastPrice = priceHistory.find(h => h.product_id === product.id)?.unit_cost || product.cost_price || 0;
    
    const newItem = {
      no: form.items.length + 1,
      product_id: product.id,
      product_code: product.code || '',
      barcode: product.barcode || product.code || '',
      product_name: product.name,
      brand: product.brand || '',
      category: product.category_name || product.category || '',
      item_type: product.item_type || 'barang',
      info: product.description || '',
      qty_order: 1,
      qty_received: 0,
      unit: product.unit || 'PCS',
      conversion: 1,
      unit_price: lastPrice,
      discount_percent: 0,
      discount_amount: 0,
      subtotal: lastPrice,
      tax_percent: 0,
      tax_amount: 0,
      total: lastPrice,
      warehouse_id: form.warehouse_id,
      batch_no: '',
      expired_date: '',
      serial_number: '',
      item_notes: ''
    };
    
    setForm(prev => ({
      ...prev,
      items: [...prev.items, newItem]
    }));
    
    toast.success(`${product.name} ditambahkan`);
  };
  
  const updateItem = (index, field, value) => {
    setForm(prev => {
      const newItems = [...prev.items];
      newItems[index] = { ...newItems[index], [field]: value };
      
      // Recalculate item totals
      const item = newItems[index];
      const qty = parseFloat(item.qty_order) || 0;
      const price = parseFloat(item.unit_price) || 0;
      const discPct = parseFloat(item.discount_percent) || 0;
      const taxPct = parseFloat(item.tax_percent) || 0;
      
      const itemSubtotal = qty * price;
      const discAmount = itemSubtotal * (discPct / 100);
      const afterDisc = itemSubtotal - discAmount;
      const taxAmount = afterDisc * (taxPct / 100);
      const itemTotal = afterDisc + taxAmount;
      
      newItems[index] = {
        ...item,
        subtotal: itemSubtotal,
        discount_amount: discAmount,
        tax_amount: taxAmount,
        total: itemTotal
      };
      
      return { ...prev, items: newItems };
    });
  };
  
  const removeItem = (index) => {
    setForm(prev => ({
      ...prev,
      items: prev.items.filter((_, i) => i !== index).map((item, i) => ({ ...item, no: i + 1 }))
    }));
  };
  
  const selectItemForHistory = (item) => {
    setSelectedItemForHistory(item);
    loadPriceHistory(item.product_id, form.supplier_id);
    setActiveBottomTab('riwayat_harga');
  };
  
  // ==================== CALCULATIONS ====================
  const calculateTotals = useMemo(() => {
    let subtotal = 0;
    let totalItemDiscount = 0;
    let totalItemTax = 0;
    
    form.items.forEach(item => {
      const qty = parseFloat(item.qty_order) || 0;
      const price = parseFloat(item.unit_price) || 0;
      const discPct = parseFloat(item.discount_percent) || 0;
      const taxPct = parseFloat(item.tax_percent) || 0;
      
      const itemSubtotal = qty * price;
      const discAmount = itemSubtotal * (discPct / 100);
      const afterDisc = itemSubtotal - discAmount;
      const taxAmount = afterDisc * (taxPct / 100);
      
      subtotal += itemSubtotal;
      totalItemDiscount += discAmount;
      totalItemTax += taxAmount;
    });
    
    const transDiscPct = parseFloat(form.discount_percent) || 0;
    const transDiscAmt = parseFloat(form.discount_amount) || subtotal * (transDiscPct / 100);
    const afterTransDisc = subtotal - totalItemDiscount - transDiscAmt;
    
    const ppnAmt = afterTransDisc * (parseFloat(form.ppn_percent) || 0) / 100;
    const otherCost = parseFloat(form.other_cost) || 0;
    const shippingCost = parseFloat(form.shipping_cost) || 0;
    const rounding = parseFloat(form.rounding) || 0;
    const dpAmount = parseFloat(form.dp_amount) || 0;
    const depositAmount = parseFloat(form.deposit_amount) || 0;
    
    const grandTotal = afterTransDisc + ppnAmt + totalItemTax + otherCost + shippingCost + rounding;
    const cashAmount = parseFloat(form.cash_amount) || 0;
    const creditAmount = grandTotal - cashAmount - dpAmount - depositAmount;
    
    return {
      subtotal,
      totalItemDiscount,
      totalItemTax,
      transDiscAmt,
      ppnAmt,
      grandTotal,
      creditAmount: Math.max(0, creditAmount),
      remainingDebt: Math.max(0, creditAmount)
    };
  }, [form]);
  
  // ==================== SAVE TRANSACTION ====================
  const handleSave = async (status = 'draft') => {
    // Validation
    if (!form.supplier_id) {
      toast.error('Pilih supplier terlebih dahulu');
      return;
    }
    if (form.items.length === 0) {
      toast.error('Tambahkan minimal 1 item');
      return;
    }
    
    // Validate items
    for (const item of form.items) {
      if (!item.qty_order || item.qty_order <= 0) {
        toast.error(`Qty untuk ${item.product_name} harus > 0`);
        return;
      }
      if (item.unit_price < 0) {
        toast.error(`Harga untuk ${item.product_name} tidak boleh negatif`);
        return;
      }
      if (!item.warehouse_id && !form.warehouse_id) {
        toast.error(`Pilih gudang untuk ${item.product_name}`);
        return;
      }
    }
    
    setSaving(true);
    try {
      const payload = {
        supplier_id: form.supplier_id,
        branch_id: form.branch_id || user?.branch_id,
        expected_date: form.date,
        notes: form.notes,
        is_credit: form.payment_type === 'credit' || form.payment_type === 'combo',
        credit_due_days: parseInt(form.credit_due_days) || 30,
        items: form.items.map(item => ({
          product_id: item.product_id,
          quantity: parseInt(item.qty_order) || 1,
          unit_cost: parseFloat(item.unit_price) || 0,
          discount_percent: parseFloat(item.discount_percent) || 0
        }))
      };
      
      let res;
      if (editingId) {
        // Update existing PO (draft/ordered only)
        const updatePayload = {
          supplier_id: form.supplier_id,
          branch_id: form.branch_id || user?.branch_id,
          expected_date: form.date,
          notes: form.notes,
          items: form.items.map(item => ({
            product_id: item.product_id,
            product_code: item.product_code || '',
            product_name: item.product_name || '',
            unit: item.unit || 'PCS',
            quantity: parseFloat(item.qty_order) || 1,
            unit_cost: parseFloat(item.unit_price) || 0,
            discount_percent: parseFloat(item.discount_percent) || 0
          }))
        };
        
        res = await api(`/api/purchase/orders/${editingId}`, {
          method: 'PUT',
          body: JSON.stringify(updatePayload)
        });
        
        if (res.ok) {
          const result = await res.json();
          toast.success(result.message || `PO ${form.transaction_no} berhasil diupdate`);
          
          // If status is 'posted', submit the PO
          if (status === 'posted') {
            const submitRes = await api(`/api/purchase/orders/${editingId}/submit`, { method: 'POST' });
            if (submitRes.ok) {
              toast.success('PO berhasil di-submit');
            }
          }
          
          setViewMode('list');
          loadTransactions();
        } else {
          const err = await res.json();
          toast.error(err.detail || 'Gagal update PO');
        }
      } else {
        res = await api('/api/purchase/orders', {
          method: 'POST',
          body: JSON.stringify(payload)
        });
        
        if (res.ok) {
          const result = await res.json();
          toast.success(`Transaksi ${result.po_number} berhasil disimpan`);
          
          // If status is 'posted', submit the PO
          if (status === 'posted') {
            await api(`/api/purchase/orders/${result.id}/submit`, { method: 'POST' });
            toast.success('Transaksi berhasil diposting');
          }
          
          setViewMode('list');
          loadTransactions();
        } else {
          const err = await res.json();
          toast.error(err.detail || 'Gagal menyimpan transaksi');
        }
      }
    } catch (err) {
      console.error('Save error:', err);
      toast.error('Terjadi kesalahan saat menyimpan');
    } finally {
      setSaving(false);
    }
  };
  
  // ==================== FILTERED TRANSACTIONS ====================
  const filteredTransactions = useMemo(() => {
    return transactions.filter(tx => {
      if (filters.keyword) {
        const kw = filters.keyword.toLowerCase();
        const match = 
          tx.po_number?.toLowerCase().includes(kw) ||
          tx.supplier_name?.toLowerCase().includes(kw) ||
          tx.notes?.toLowerCase().includes(kw);
        if (!match) return false;
      }
      if (filters.status && tx.status !== filters.status) return false;
      if (filters.supplier_id && tx.supplier_id !== filters.supplier_id) return false;
      return true;
    });
  }, [transactions, filters]);
  
  // ==================== SUMMARY CALCULATIONS ====================
  const summary = useMemo(() => {
    const totals = filteredTransactions.reduce((acc, tx) => ({
      count: acc.count + 1,
      total: acc.total + (tx.total || 0),
      tax: acc.tax + (tx.tax_amount || 0),
      discount: acc.discount + (tx.discount_amount || 0),
      paid: acc.paid + (tx.paid_amount || 0),
      unpaid: acc.unpaid + ((tx.total || 0) - (tx.paid_amount || 0))
    }), { count: 0, total: 0, tax: 0, discount: 0, paid: 0, unpaid: 0 });
    
    return {
      ...totals,
      lunas: filteredTransactions.filter(tx => tx.payment_status === 'lunas' || tx.status === 'received').length,
      belumLunas: filteredTransactions.filter(tx => tx.payment_status !== 'lunas' && tx.status !== 'received').length
    };
  }, [filteredTransactions]);
  
  // ==================== RENDER LIST VIEW ====================
  const renderListView = () => (
    <div className="space-y-3">
      {/* Filter Section */}
      <div className="bg-gray-800/50 rounded-lg border border-gray-700 p-3">
        <div className="grid grid-cols-6 gap-2">
          <InputField
            label="Kata Kunci"
            value={filters.keyword}
            onChange={(v) => setFilters(prev => ({ ...prev, keyword: v }))}
            placeholder="Cari transaksi..."
            icon={Search}
          />
          <InputField
            label="Dari Tanggal"
            type="date"
            value={filters.dateFrom}
            onChange={(v) => setFilters(prev => ({ ...prev, dateFrom: v }))}
          />
          <InputField
            label="Sampai Tanggal"
            type="date"
            value={filters.dateTo}
            onChange={(v) => setFilters(prev => ({ ...prev, dateTo: v }))}
          />
          <InputField
            label="Supplier"
            type="select"
            value={filters.supplier_id}
            onChange={(v) => setFilters(prev => ({ ...prev, supplier_id: v }))}
            options={suppliers.map(s => ({ value: s.id, label: s.name }))}
            placeholder="Semua Supplier"
          />
          <InputField
            label="Status"
            type="select"
            value={filters.status}
            onChange={(v) => setFilters(prev => ({ ...prev, status: v }))}
            options={[
              { value: 'draft', label: 'Draft' },
              { value: 'ordered', label: 'Ordered' },
              { value: 'partial', label: 'Partial' },
              { value: 'received', label: 'Received' },
              { value: 'cancelled', label: 'Batal' }
            ]}
            placeholder="Semua Status"
          />
          <InputField
            label="Status Bayar"
            type="select"
            value={filters.payment_status}
            onChange={(v) => setFilters(prev => ({ ...prev, payment_status: v }))}
            options={[
              { value: 'lunas', label: 'Lunas' },
              { value: 'belum_lunas', label: 'Belum Lunas' },
              { value: 'partial_paid', label: 'Sebagian' }
            ]}
            placeholder="Semua"
          />
        </div>
        <div className="flex justify-between items-center mt-3 pt-3 border-t border-gray-700">
          <div className="flex gap-2">
            <button
              onClick={() => setFilters({ keyword: '', dateFrom: '', dateTo: '', supplier_id: '', branch_id: '', warehouse_id: '', status: '', payment_status: '', user_id: '', sales_id: '', item_id: '', invoice_no: '', tax_invoice: '' })}
              className="px-3 py-1.5 text-sm bg-gray-700 hover:bg-gray-600 rounded flex items-center gap-1"
            >
              <X className="h-3.5 w-3.5" /> Reset Filter
            </button>
            <button
              onClick={loadTransactions}
              className="px-3 py-1.5 text-sm bg-gray-700 hover:bg-gray-600 rounded flex items-center gap-1"
            >
              <RefreshCw className="h-3.5 w-3.5" /> Refresh
            </button>
          </div>
          <button
            onClick={handleNewTransaction}
            data-testid="btn-new-transaction"
            className="px-4 py-1.5 text-sm bg-blue-600 hover:bg-blue-700 rounded flex items-center gap-2"
          >
            <Plus className="h-4 w-4" /> Tambah Transaksi
          </button>
        </div>
      </div>
      
      {/* Transaction Table */}
      <div className="bg-gray-800/50 rounded-lg border border-gray-700 overflow-hidden">
        <div className="overflow-x-auto max-h-[calc(100vh-380px)]">
          <table className="w-full text-sm">
            <thead className="bg-gray-800 sticky top-0">
              <tr className="text-left text-gray-400 text-xs">
                <th className="p-2 border-b border-gray-700">No Transaksi</th>
                <th className="p-2 border-b border-gray-700">Tanggal</th>
                <th className="p-2 border-b border-gray-700">Jam</th>
                <th className="p-2 border-b border-gray-700">Kode Supplier</th>
                <th className="p-2 border-b border-gray-700">Nama Supplier</th>
                <th className="p-2 border-b border-gray-700">Cabang</th>
                <th className="p-2 border-b border-gray-700">Gudang</th>
                <th className="p-2 border-b border-gray-700">Sales</th>
                <th className="p-2 border-b border-gray-700">Ref PO</th>
                <th className="p-2 border-b border-gray-700 text-right">Subtotal</th>
                <th className="p-2 border-b border-gray-700 text-right">Diskon</th>
                <th className="p-2 border-b border-gray-700 text-right">Pajak</th>
                <th className="p-2 border-b border-gray-700 text-right">Total</th>
                <th className="p-2 border-b border-gray-700 text-right">Dibayar</th>
                <th className="p-2 border-b border-gray-700 text-right">Sisa Hutang</th>
                <th className="p-2 border-b border-gray-700">Status</th>
                <th className="p-2 border-b border-gray-700">User</th>
                <th className="p-2 border-b border-gray-700">Aksi</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700/50">
              {loading ? (
                <tr>
                  <td colSpan="18" className="p-8 text-center text-gray-400">
                    <Loader2 className="h-6 w-6 animate-spin mx-auto" />
                  </td>
                </tr>
              ) : filteredTransactions.length === 0 ? (
                <tr>
                  <td colSpan="18" className="p-8 text-center text-gray-400">
                    Tidak ada data transaksi
                  </td>
                </tr>
              ) : filteredTransactions.map((tx, idx) => (
                <tr key={tx.id} className="hover:bg-gray-800/30">
                  <td className="p-2 text-blue-400 font-medium">{tx.po_number}</td>
                  <td className="p-2">{formatDate(tx.created_at)}</td>
                  <td className="p-2">{formatTime(tx.created_at)}</td>
                  <td className="p-2 font-mono text-xs">{suppliers.find(s => s.id === tx.supplier_id)?.code || '-'}</td>
                  <td className="p-2">{tx.supplier_name}</td>
                  <td className="p-2">{branches.find(b => b.id === tx.branch_id)?.name || '-'}</td>
                  <td className="p-2">{warehouses.find(w => w.id === tx.warehouse_id)?.name || '-'}</td>
                  <td className="p-2">-</td>
                  <td className="p-2 text-xs">{tx.po_reference || '-'}</td>
                  <td className="p-2 text-right">{formatRupiah(tx.subtotal)}</td>
                  <td className="p-2 text-right text-red-400">{formatRupiah(tx.discount_amount || 0)}</td>
                  <td className="p-2 text-right">{formatRupiah(tx.tax_amount || 0)}</td>
                  <td className="p-2 text-right font-medium">{formatRupiah(tx.total)}</td>
                  <td className="p-2 text-right text-green-400">{formatRupiah(tx.paid_amount || 0)}</td>
                  <td className="p-2 text-right text-red-400 font-medium">{formatRupiah((tx.total || 0) - (tx.paid_amount || 0))}</td>
                  <td className="p-2"><StatusBadge status={tx.status} /></td>
                  <td className="p-2 text-xs">{tx.user_name || '-'}</td>
                  <td className="p-2">
                    <div className="flex gap-1">
                      <button
                        onClick={() => handleEditTransaction(tx)}
                        className={`p-1 rounded ${canEditPO(tx) ? 'hover:bg-blue-700 text-blue-400' : 'hover:bg-gray-700 text-gray-500'}`}
                        title={canEditPO(tx) ? 'Edit PO' : 'Lihat Detail (tidak bisa edit)'}
                        data-testid={`btn-edit-${tx.po_number}`}
                      >
                        {canEditPO(tx) ? <Edit className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
                      </button>
                      <button 
                        onClick={() => handlePrintPO(tx)}
                        className="p-1 hover:bg-gray-700 rounded" 
                        title="Print PO"
                        data-testid={`btn-print-${tx.po_number}`}
                      >
                        <Printer className="h-3.5 w-3.5 text-gray-400" />
                      </button>
                      <button
                        onClick={() => handleDeletePO(tx)}
                        className="p-1 hover:bg-red-700 rounded"
                        title="Hapus PO"
                        data-testid={`btn-delete-${tx.po_number}`}
                      >
                        <Trash2 className="h-3.5 w-3.5 text-red-400" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      
      {/* Summary Footer */}
      <div className="bg-gray-800/50 rounded-lg border border-gray-700 p-3">
        <div className="grid grid-cols-7 gap-4 text-sm">
          <div className="text-center">
            <p className="text-gray-400 text-xs">Jumlah Transaksi</p>
            <p className="font-bold text-lg">{summary.count}</p>
          </div>
          <div className="text-center">
            <p className="text-gray-400 text-xs">Total Pembelian</p>
            <p className="font-bold text-lg text-blue-400">{formatRupiah(summary.total)}</p>
          </div>
          <div className="text-center">
            <p className="text-gray-400 text-xs">Total Pajak</p>
            <p className="font-bold text-lg">{formatRupiah(summary.tax)}</p>
          </div>
          <div className="text-center">
            <p className="text-gray-400 text-xs">Total Diskon</p>
            <p className="font-bold text-lg text-red-400">{formatRupiah(summary.discount)}</p>
          </div>
          <div className="text-center">
            <p className="text-gray-400 text-xs">Total Hutang</p>
            <p className="font-bold text-lg text-red-400">{formatRupiah(summary.unpaid)}</p>
          </div>
          <div className="text-center">
            <p className="text-gray-400 text-xs">Transaksi Lunas</p>
            <p className="font-bold text-lg text-green-400">{summary.lunas}</p>
          </div>
          <div className="text-center">
            <p className="text-gray-400 text-xs">Belum Lunas</p>
            <p className="font-bold text-lg text-amber-400">{summary.belumLunas}</p>
          </div>
        </div>
      </div>
    </div>
  );
  
  // ==================== RENDER FORM VIEW ====================
  const renderFormView = () => (
    <div className="space-y-3">
      {/* Header Form */}
      <div className="bg-gray-800/50 rounded-lg border border-gray-700 p-3">
        <div className="flex justify-between items-center mb-3">
          <h3 className="font-medium flex items-center gap-2">
            <FileText className="h-4 w-4 text-blue-400" />
            {editingId ? `Edit PO: ${form.transaction_no}` : 'Buat PO Pembelian Baru'}
          </h3>
          <button
            onClick={() => setViewMode('list')}
            className="p-1.5 hover:bg-gray-700 rounded text-gray-400"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        
        {/* ROW 1: Core Fields - No PO, Tanggal, Supplier, Gudang */}
        <div className="grid grid-cols-4 gap-3">
          <InputField
            label="No PO"
            value={form.transaction_no}
            onChange={(v) => setForm(prev => ({ ...prev, transaction_no: v }))}
            disabled
            icon={Hash}
          />
          <InputField
            label="Tanggal"
            type="date"
            value={form.date}
            onChange={(v) => setForm(prev => ({ ...prev, date: v }))}
            required
            icon={Calendar}
          />
          {/* Supplier - Searchable - HIGH VISIBILITY */}
          <div>
            <label className="block text-xs text-gray-400 mb-1 flex items-center gap-1">
              <Truck className="h-3 w-3" />
              Supplier <span className="text-red-400">*</span>
            </label>
            <SearchableSelect
              options={suppliers.map(s => ({ 
                value: s.id, 
                label: s.name || 'Supplier',
                sublabel: `${s.code || ''} ${s.phone ? `| ${s.phone}` : ''}`
              }))}
              value={form.supplier_id}
              onValueChange={(v) => setForm(prev => ({ ...prev, supplier_id: v }))}
              placeholder="Pilih supplier..."
              searchPlaceholder="Cari supplier..."
              emptyText="Supplier tidak ditemukan"
              data-testid="select-supplier"
              triggerClassName={`bg-gray-800 border-gray-600 hover:bg-gray-700 ${form.supplier_id ? 'text-orange-300 font-medium border-orange-600/50' : 'text-gray-400'}`}
            />
            {form.supplier_id && (
              <div className="mt-1 text-xs text-orange-300/70">
                ✓ {suppliers.find(s => s.id === form.supplier_id)?.name || 'Dipilih'}
              </div>
            )}
          </div>
          {/* Gudang Tujuan - Searchable - FILTERED BY USER BRANCH */}
          <div>
            <label className="block text-xs text-gray-400 mb-1 flex items-center gap-1">
              <Warehouse className="h-3 w-3" />
              Gudang Tujuan <span className="text-red-400">*</span>
            </label>
            <SearchableSelect
              options={warehouses
                .filter(w => !user?.branch_id || w.branch_id === user.branch_id || !w.branch_id)
                .map(w => ({ 
                  value: w.id, 
                  label: w.name,
                  sublabel: `${w.code || ''} ${w.branch_id ? `(${branches.find(b => b.id === w.branch_id)?.name || 'Cabang'})` : '(Global)'}`
                }))}
              value={form.warehouse_id}
              onValueChange={(v) => {
                // TASK 6: When warehouse selected, set branch_id from warehouse
                const selectedWarehouse = warehouses.find(w => w.id === v);
                setForm(prev => ({ 
                  ...prev, 
                  warehouse_id: v,
                  branch_id: selectedWarehouse?.branch_id || prev.branch_id
                }));
              }}
              placeholder="Pilih gudang tujuan..."
              searchPlaceholder="Cari gudang..."
              emptyText="Gudang tidak ditemukan"
              data-testid="select-warehouse"
              triggerClassName={`bg-gray-800 border-gray-600 hover:bg-gray-700 ${form.warehouse_id ? 'text-blue-300 font-medium border-blue-600/50' : 'text-gray-400'}`}
            />
            {form.warehouse_id && (
              <div className="mt-1 text-xs text-blue-300/70">
                ✓ {warehouses.find(w => w.id === form.warehouse_id)?.name || 'Dipilih'}
              </div>
            )}
          </div>
        </div>
        
        {/* ROW 2: PIC, Akun Pembayaran, Catatan */}
        <div className="grid grid-cols-4 gap-3 mt-3">
          {/* PIC - Searchable - HIGH VISIBILITY */}
          <div>
            <label className="block text-xs text-gray-400 mb-1 flex items-center gap-1">
              <User className="h-3 w-3" />
              PIC (Person in Charge)
            </label>
            <SearchableSelect
              options={employees.map(e => ({ 
                value: e.id, 
                label: e.full_name || e.name || e.employee_name || 'Karyawan',
                sublabel: `${e.employee_id || ''} ${e.jabatan_name ? `- ${e.jabatan_name}` : (e.position ? `- ${e.position}` : '')}`
              }))}
              value={form.sales_person_id}
              onValueChange={(v) => setForm(prev => ({ ...prev, sales_person_id: v }))}
              placeholder="Pilih PIC..."
              searchPlaceholder="Cari karyawan..."
              emptyText="Karyawan tidak ditemukan"
              data-testid="select-pic"
              triggerClassName={`bg-gray-800 border-gray-600 hover:bg-gray-700 ${form.sales_person_id ? 'text-amber-200 font-medium border-amber-600/50' : 'text-gray-400'}`}
            />
            {form.sales_person_id && (
              <div className="mt-1 text-xs text-amber-300/70">
                ✓ {employees.find(e => e.id === form.sales_person_id)?.full_name || 
                   employees.find(e => e.id === form.sales_person_id)?.name || 'Dipilih'}
              </div>
            )}
          </div>
          {/* Akun Pembayaran - Searchable - HIGH VISIBILITY */}
          <div>
            <label className="block text-xs text-gray-400 mb-1 flex items-center gap-1">
              <Banknote className="h-3 w-3" />
              Akun Pembayaran
            </label>
            <SearchableSelect
              options={paymentAccounts.map(a => ({ 
                value: a.id || a.code, 
                label: a.name || 'Akun',
                sublabel: `${a.code || ''} - ${a.account_type?.toUpperCase() || a.type?.toUpperCase() || 'KAS/BANK'}`
              }))}
              value={form.payment_account_id}
              onValueChange={(v) => setForm(prev => ({ ...prev, payment_account_id: v }))}
              placeholder="Pilih akun kas/bank..."
              searchPlaceholder="Cari akun..."
              emptyText="Akun tidak ditemukan"
              data-testid="select-payment-account"
              triggerClassName={`bg-gray-800 border-gray-600 hover:bg-gray-700 ${form.payment_account_id ? 'text-green-300 font-medium border-green-600/50' : 'text-gray-400'}`}
            />
            {form.payment_account_id && (
              <div className="mt-1 text-xs text-green-300/70">
                ✓ {paymentAccounts.find(a => (a.id || a.code) === form.payment_account_id)?.name || 'Dipilih'}
              </div>
            )}
          </div>
          <div className="col-span-2">
            <InputField
              label="Catatan"
              value={form.notes}
              onChange={(v) => setForm(prev => ({ ...prev, notes: v }))}
              placeholder="Catatan/keterangan PO..."
              icon={StickyNote}
            />
          </div>
        </div>
      </div>
      
      {/* Product Search & Add */}
      <div className="bg-gray-800/50 rounded-lg border border-gray-700 p-3">
        <div className="flex items-center gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              ref={itemInputRef}
              type="text"
              placeholder="Scan barcode atau ketik kode/nama item lalu tekan Enter..."
              className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded text-white"
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  const found = products.find(p => 
                    p.code?.toLowerCase() === e.target.value.toLowerCase() ||
                    p.barcode?.toLowerCase() === e.target.value.toLowerCase() ||
                    p.name?.toLowerCase().includes(e.target.value.toLowerCase())
                  );
                  if (found) {
                    addItem(found);
                    e.target.value = '';
                  } else {
                    toast.error('Item tidak ditemukan');
                  }
                }
              }}
            />
          </div>
          <span className="text-xs text-gray-400">F2: Cari Item | F3: Simpan | F4: Posting | ESC: Batal</span>
        </div>
        
        {/* Quick product buttons */}
        <div className="mt-2 flex flex-wrap gap-1 max-h-16 overflow-y-auto">
          {products.slice(0, 24).map(p => (
            <button
              key={p.id}
              onClick={() => addItem(p)}
              className="px-2 py-1 text-xs bg-gray-700 hover:bg-gray-600 rounded truncate max-w-32"
            >
              {p.code} - {p.name}
            </button>
          ))}
        </div>
      </div>
      
      {/* Items Grid - SIMPLIFIED */}
      <div className="bg-gray-800/50 rounded-lg border border-gray-700 overflow-hidden">
        <div className="overflow-x-auto max-h-64">
          <table className="w-full text-xs">
            <thead className="bg-gray-800 sticky top-0">
              <tr className="text-left text-gray-400">
                <th className="p-1.5 border-b border-gray-700 w-8">No</th>
                <th className="p-1.5 border-b border-gray-700 w-24">Kode</th>
                <th className="p-1.5 border-b border-gray-700 min-w-48">Nama Produk</th>
                <th className="p-1.5 border-b border-gray-700 text-center w-20">Qty Pesan</th>
                <th className="p-1.5 border-b border-gray-700 w-16">Satuan</th>
                <th className="p-1.5 border-b border-gray-700 text-right w-28">Harga Beli</th>
                <th className="p-1.5 border-b border-gray-700 text-center w-16">Disk %</th>
                <th className="p-1.5 border-b border-gray-700 text-right w-28">Subtotal</th>
                <th className="p-1.5 border-b border-gray-700 w-8"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700/50">
              {form.items.length === 0 ? (
                <tr>
                  <td colSpan="9" className="p-4 text-center text-gray-400">
                    Belum ada item. Cari dan pilih produk di atas.
                  </td>
                </tr>
              ) : form.items.map((item, idx) => (
                <tr 
                  key={idx} 
                  className={`hover:bg-gray-800/30 cursor-pointer ${selectedItemForHistory?.product_id === item.product_id ? 'bg-blue-900/20' : ''}`}
                  onClick={() => selectItemForHistory(item)}
                  data-testid={`item-row-${idx}`}
                >
                  <td className="p-1.5 text-center">{item.no}</td>
                  <td className="p-1.5 font-mono text-xs">{item.product_code}</td>
                  <td className="p-1.5 font-medium text-amber-200" data-testid={`item-name-${idx}`}>{item.product_name || 'Nama tidak tersedia'}</td>
                  <td className="p-1.5">
                    <input
                      type="number"
                      min="1"
                      value={item.qty_order}
                      onClick={(e) => e.stopPropagation()}
                      onChange={(e) => updateItem(idx, 'qty_order', parseInt(e.target.value) || 0)}
                      className="w-full px-1 py-0.5 bg-gray-800 border border-gray-600 rounded text-center"
                      data-testid={`item-qty-${idx}`}
                    />
                  </td>
                  <td className="p-1.5 text-center">{item.unit}</td>
                  <td className="p-1.5">
                    <input
                      type="number"
                      min="0"
                      value={item.unit_price}
                      onClick={(e) => e.stopPropagation()}
                      onChange={(e) => updateItem(idx, 'unit_price', parseFloat(e.target.value) || 0)}
                      className="w-full px-1 py-0.5 bg-gray-800 border border-gray-600 rounded text-right"
                      data-testid={`item-price-${idx}`}
                    />
                  </td>
                  <td className="p-1.5">
                    <input
                      type="number"
                      min="0"
                      max="100"
                      value={item.discount_percent}
                      onClick={(e) => e.stopPropagation()}
                      onChange={(e) => updateItem(idx, 'discount_percent', parseFloat(e.target.value) || 0)}
                      className="w-full px-1 py-0.5 bg-gray-800 border border-gray-600 rounded text-center"
                      data-testid={`item-disc-${idx}`}
                    />
                  </td>
                  <td className="p-1.5 text-right font-medium text-green-400">{formatRupiah(item.total || item.subtotal)}</td>
                  <td className="p-1.5">
                    <button
                      onClick={(e) => { e.stopPropagation(); removeItem(idx); }}
                      className="p-0.5 hover:bg-red-700 rounded"
                      data-testid={`item-remove-${idx}`}
                    >
                      <Trash2 className="h-3.5 w-3.5 text-red-400" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      
      {/* Bottom Tabs - Simplified */}
      <div className="bg-gray-800/50 rounded-lg border border-gray-700 overflow-hidden">
        <div className="flex border-b border-gray-700 bg-gray-800">
          <TabButton active={activeBottomTab === 'rincian'} onClick={() => setActiveBottomTab('rincian')} label="Rincian Item" />
          <TabButton active={activeBottomTab === 'riwayat_harga'} onClick={() => setActiveBottomTab('riwayat_harga')} label="Riwayat Harga Beli" count={priceHistory.length} />
          <TabButton active={activeBottomTab === 'riwayat_supplier'} onClick={() => setActiveBottomTab('riwayat_supplier')} label="Riwayat Supplier" count={supplierHistory.length} />
        </div>
        
        <div className="p-3 min-h-32 max-h-48 overflow-y-auto">
          {activeBottomTab === 'rincian' && (
            <div className="space-y-2">
              {selectedItemForHistory ? (
                <div className="grid grid-cols-4 gap-4 text-sm">
                  <div>
                    <p className="text-gray-400 text-xs">Item Dipilih</p>
                    <p className="font-medium text-amber-200">{selectedItemForHistory.product_name}</p>
                  </div>
                  <div>
                    <p className="text-gray-400 text-xs">Kode</p>
                    <p className="font-mono">{selectedItemForHistory.product_code}</p>
                  </div>
                  <div>
                    <p className="text-gray-400 text-xs">Satuan</p>
                    <p>{selectedItemForHistory.unit || '-'}</p>
                  </div>
                  <div>
                    <p className="text-gray-400 text-xs">Harga Terakhir</p>
                    <p className="font-medium text-green-400">{formatRupiah(selectedItemForHistory.unit_price)}</p>
                  </div>
                </div>
              ) : (
                <p className="text-gray-400 text-sm">Klik item di grid untuk melihat rincian</p>
              )}
            </div>
          )}
          
          {activeBottomTab === 'riwayat_harga' && (
            <div className="text-sm">
              {priceHistory.length > 0 ? (
                <table className="w-full">
                  <thead className="text-gray-400 text-xs">
                    <tr>
                      <th className="text-left p-1">Tanggal</th>
                      <th className="text-left p-1">Supplier</th>
                      <th className="text-left p-1">No Transaksi</th>
                      <th className="text-right p-1">Harga</th>
                      <th className="text-right p-1">Qty</th>
                    </tr>
                  </thead>
                  <tbody>
                    {priceHistory.slice(0, 10).map((h, idx) => (
                      <tr key={idx} className="border-t border-gray-700">
                        <td className="p-1">{formatDate(h.date)}</td>
                        <td className="p-1">{h.supplier_name}</td>
                        <td className="p-1 text-blue-400">{h.po_number}</td>
                        <td className="p-1 text-right font-medium">{formatRupiah(h.unit_cost)}</td>
                        <td className="p-1 text-right">{h.quantity}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <p className="text-gray-400">Pilih item untuk melihat riwayat harga</p>
              )}
            </div>
          )}
          
          {activeBottomTab === 'riwayat_supplier' && (
            <div className="text-sm">
              {supplierHistory.length > 0 ? (
                <table className="w-full">
                  <thead className="text-gray-400 text-xs">
                    <tr>
                      <th className="text-left p-1">Tanggal</th>
                      <th className="text-left p-1">No Transaksi</th>
                      <th className="text-right p-1">Harga</th>
                      <th className="text-right p-1">Qty</th>
                      <th className="text-right p-1">Diskon</th>
                    </tr>
                  </thead>
                  <tbody>
                    {supplierHistory.slice(0, 10).map((h, idx) => (
                      <tr key={idx} className="border-t border-gray-700">
                        <td className="p-1">{formatDate(h.date)}</td>
                        <td className="p-1 text-blue-400">{h.po_number}</td>
                        <td className="p-1 text-right font-medium">{formatRupiah(h.unit_cost)}</td>
                        <td className="p-1 text-right">{h.quantity}</td>
                        <td className="p-1 text-right">{h.discount_percent || 0}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <p className="text-gray-400">Pilih supplier dan item untuk melihat riwayat</p>
              )}
            </div>
          )}
        </div>
      </div>
      
      {/* Footer Calculations & Payment */}
      <div className="grid grid-cols-3 gap-3">
        {/* Left: Totals */}
        <div className="bg-gray-800/50 rounded-lg border border-gray-700 p-3 col-span-2">
          <div className="grid grid-cols-4 gap-4 text-sm">
            <div>
              <p className="text-gray-400 text-xs">Subtotal Item</p>
              <p className="text-lg font-medium">{formatRupiah(calculateTotals.subtotal)}</p>
            </div>
            <div>
              <p className="text-gray-400 text-xs">Total Diskon</p>
              <p className="text-lg font-medium text-red-400">-{formatRupiah(calculateTotals.totalItemDiscount + calculateTotals.transDiscAmt)}</p>
            </div>
            <div>
              <p className="text-gray-400 text-xs">Total Pajak</p>
              <p className="text-lg font-medium">{formatRupiah(calculateTotals.ppnAmt + calculateTotals.totalItemTax)}</p>
            </div>
            <div>
              <p className="text-gray-400 text-xs">Grand Total</p>
              <p className="text-2xl font-bold text-green-400">{formatRupiah(calculateTotals.grandTotal)}</p>
            </div>
          </div>
        </div>
        
        {/* Right: Payment */}
        <div className="bg-gray-800/50 rounded-lg border border-gray-700 p-3">
          <div className="space-y-2">
            <InputField
              label="Jenis Pembayaran"
              type="select"
              value={form.payment_type}
              onChange={(v) => setForm(prev => ({ ...prev, payment_type: v }))}
              options={[
                { value: 'cash', label: 'Tunai' },
                { value: 'credit', label: 'Kredit/Hutang' },
                { value: 'dp', label: 'DP' },
                { value: 'deposit', label: 'Deposit Supplier' },
                { value: 'combo', label: 'Kombinasi' }
              ]}
            />
            {(form.payment_type === 'cash' || form.payment_type === 'combo') && (
              <InputField
                label="Tunai"
                type="number"
                value={form.cash_amount}
                onChange={(v) => setForm(prev => ({ ...prev, cash_amount: parseFloat(v) || 0 }))}
              />
            )}
            {(form.payment_type === 'credit' || form.payment_type === 'combo') && (
              <>
                <InputField
                  label="Jatuh Tempo (hari)"
                  type="number"
                  value={form.credit_due_days}
                  onChange={(v) => setForm(prev => ({ ...prev, credit_due_days: parseInt(v) || 30 }))}
                />
                <div>
                  <p className="text-xs text-gray-400">Sisa Hutang</p>
                  <p className="text-lg font-bold text-red-400">{formatRupiah(calculateTotals.remainingDebt)}</p>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
      
      {/* Action Buttons */}
      <div className="flex justify-between items-center bg-gray-800/50 rounded-lg border border-gray-700 p-3">
        <div className="flex gap-2">
          <button
            onClick={() => setViewMode('list')}
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded flex items-center gap-2"
          >
            <X className="h-4 w-4" /> Batal
          </button>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => handleSave('draft')}
            disabled={saving}
            className="px-4 py-2 bg-gray-600 hover:bg-gray-500 rounded flex items-center gap-2 disabled:opacity-50"
          >
            {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
            Simpan Draft
          </button>
          <button
            onClick={() => handleSave('posted')}
            disabled={saving}
            className="px-6 py-2 bg-green-600 hover:bg-green-700 rounded flex items-center gap-2 font-medium disabled:opacity-50"
            data-testid="btn-save-post"
          >
            {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />}
            Simpan & Posting
          </button>
        </div>
      </div>
    </div>
  );
  
  // ==================== KEYBOARD SHORTCUTS ====================
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (viewMode === 'form') {
        if (e.key === 'F2') {
          e.preventDefault();
          itemInputRef.current?.focus();
        } else if (e.key === 'F3') {
          e.preventDefault();
          handleSave('draft');
        } else if (e.key === 'F4') {
          e.preventDefault();
          handleSave('posted');
        } else if (e.key === 'Escape') {
          e.preventDefault();
          setViewMode('list');
        }
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [viewMode]);
  
  // ==================== MAIN RENDER ====================
  return (
    <div className="min-h-screen bg-gray-900 text-white p-4" data-testid="purchase-enterprise">
      {/* Page Header */}
      <div className="flex justify-between items-center mb-4">
        <div>
          <h1 className="text-xl font-bold flex items-center gap-2">
            <Truck className="h-6 w-6 text-blue-400" />
            Buat PO Pembelian
          </h1>
          <p className="text-sm text-gray-400">Form Purchase Order ke Supplier</p>
        </div>
        {viewMode === 'list' && (
          <div className="flex items-center gap-2 text-xs text-gray-400">
            <span>Total: {transactions.length} transaksi</span>
          </div>
        )}
      </div>
      
      {/* Content */}
      {viewMode === 'list' ? renderListView() : renderFormView()}
      
      {/* ============================================================ */}
      {/* PRINT MODAL - TASK 3: Template Print Bersih */}
      {/* ============================================================ */}
      {showPrintModal && printData && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4 print:p-0 print:bg-white">
          <div className="bg-white rounded-lg shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto print:max-h-none print:overflow-visible print:rounded-none print:shadow-none">
            {/* Print Header - Hide on print */}
            <div className="sticky top-0 bg-gray-100 p-4 flex justify-between items-center border-b print:hidden">
              <h3 className="text-lg font-bold text-gray-800">Preview Print PO</h3>
              <div className="flex gap-2">
                <button
                  onClick={printPODocument}
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 flex items-center gap-2"
                >
                  <Printer className="h-4 w-4" /> Print
                </button>
                <button
                  onClick={() => setShowPrintModal(false)}
                  className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
                >
                  Tutup
                </button>
              </div>
            </div>
            
            {/* Print Content - A4 Style Document */}
            <div className="p-8 bg-white text-black print:p-4" id="print-content">
              {/* Document Header */}
              <div className="text-center mb-6 border-b-2 border-gray-800 pb-4">
                <h1 className="text-2xl font-bold text-gray-900">PURCHASE ORDER</h1>
                <p className="text-sm text-gray-600 mt-1">Pesanan Pembelian ke Supplier</p>
              </div>
              
              {/* PO Info Grid */}
              <div className="grid grid-cols-2 gap-6 mb-6">
                <div>
                  <table className="text-sm w-full">
                    <tbody>
                      <tr>
                        <td className="py-1 text-gray-600 w-32">No. PO</td>
                        <td className="py-1 font-bold text-lg text-blue-700">: {printData.po_number}</td>
                      </tr>
                      <tr>
                        <td className="py-1 text-gray-600">Tanggal</td>
                        <td className="py-1">: {formatDate(printData.created_at || printData.order_date)}</td>
                      </tr>
                      <tr>
                        <td className="py-1 text-gray-600">Status</td>
                        <td className="py-1">
                          : <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                            printData.status === 'draft' ? 'bg-gray-200 text-gray-700' :
                            printData.status === 'ordered' ? 'bg-blue-100 text-blue-700' :
                            printData.status === 'received' ? 'bg-green-100 text-green-700' :
                            'bg-gray-100 text-gray-600'
                          }`}>{printData.status?.toUpperCase()}</span>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <div>
                  <div className="bg-gray-50 p-3 rounded border">
                    <p className="text-xs text-gray-500 mb-1">SUPPLIER</p>
                    <p className="font-bold text-lg">{printData.supplier?.name || '-'}</p>
                    <p className="text-sm text-gray-600">{printData.supplier?.code || ''}</p>
                    <p className="text-sm text-gray-500">{printData.supplier?.address || ''}</p>
                    <p className="text-sm text-gray-500">{printData.supplier?.phone || ''}</p>
                  </div>
                </div>
              </div>
              
              {/* Branch & PIC Info */}
              <div className="grid grid-cols-3 gap-4 mb-6 text-sm">
                <div>
                  <span className="text-gray-500">Cabang:</span>
                  <span className="ml-2 font-medium">{printData.branch?.name || '-'}</span>
                </div>
                <div>
                  <span className="text-gray-500">PIC:</span>
                  <span className="ml-2 font-medium">{printData.pic_name || printData.created_by_name || '-'}</span>
                </div>
                <div>
                  <span className="text-gray-500">Dibuat:</span>
                  <span className="ml-2 font-medium">{printData.created_by_name || '-'}</span>
                </div>
              </div>
              
              {/* Items Table */}
              <table className="w-full border-collapse mb-6">
                <thead>
                  <tr className="bg-gray-800 text-white">
                    <th className="border border-gray-300 p-2 text-center w-10">No</th>
                    <th className="border border-gray-300 p-2 text-left w-24">Kode</th>
                    <th className="border border-gray-300 p-2 text-left">Nama Produk</th>
                    <th className="border border-gray-300 p-2 text-center w-16">Qty</th>
                    <th className="border border-gray-300 p-2 text-center w-16">Satuan</th>
                    <th className="border border-gray-300 p-2 text-right w-28">Harga</th>
                    <th className="border border-gray-300 p-2 text-center w-14">Disk%</th>
                    <th className="border border-gray-300 p-2 text-right w-32">Subtotal</th>
                  </tr>
                </thead>
                <tbody>
                  {printData.items?.map((item, idx) => (
                    <tr key={idx} className={idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                      <td className="border border-gray-300 p-2 text-center">{item.no}</td>
                      <td className="border border-gray-300 p-2 font-mono text-xs">{item.product_code}</td>
                      <td className="border border-gray-300 p-2">{item.product_name}</td>
                      <td className="border border-gray-300 p-2 text-center">{item.quantity}</td>
                      <td className="border border-gray-300 p-2 text-center">{item.unit}</td>
                      <td className="border border-gray-300 p-2 text-right">{formatRupiah(item.unit_cost)}</td>
                      <td className="border border-gray-300 p-2 text-center">{item.discount_percent || 0}%</td>
                      <td className="border border-gray-300 p-2 text-right font-medium">{formatRupiah(item.subtotal)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              
              {/* Totals */}
              <div className="flex justify-end mb-6">
                <div className="w-72">
                  <div className="flex justify-between py-1 text-sm">
                    <span className="text-gray-600">Subtotal</span>
                    <span>{formatRupiah(printData.subtotal)}</span>
                  </div>
                  {printData.discount_amount > 0 && (
                    <div className="flex justify-between py-1 text-sm text-red-600">
                      <span>Diskon</span>
                      <span>-{formatRupiah(printData.discount_amount)}</span>
                    </div>
                  )}
                  {printData.tax_amount > 0 && (
                    <div className="flex justify-between py-1 text-sm">
                      <span className="text-gray-600">Pajak ({printData.tax_percent || 0}%)</span>
                      <span>{formatRupiah(printData.tax_amount)}</span>
                    </div>
                  )}
                  <div className="flex justify-between py-2 border-t-2 border-gray-800 font-bold text-lg">
                    <span>TOTAL</span>
                    <span className="text-blue-700">{formatRupiah(printData.total)}</span>
                  </div>
                </div>
              </div>
              
              {/* Notes */}
              {printData.notes && (
                <div className="mb-6 p-3 bg-gray-50 rounded border">
                  <p className="text-xs text-gray-500 mb-1">CATATAN:</p>
                  <p className="text-sm">{printData.notes}</p>
                </div>
              )}
              
              {/* Signatures */}
              <div className="grid grid-cols-3 gap-8 mt-12 text-center text-sm">
                <div>
                  <p className="text-gray-500 mb-16">Dibuat oleh,</p>
                  <div className="border-t border-gray-400 pt-2">
                    <p className="font-medium">{printData.created_by_name || '________________'}</p>
                    <p className="text-xs text-gray-500">Purchasing</p>
                  </div>
                </div>
                <div>
                  <p className="text-gray-500 mb-16">Disetujui oleh,</p>
                  <div className="border-t border-gray-400 pt-2">
                    <p className="font-medium">________________</p>
                    <p className="text-xs text-gray-500">Manager</p>
                  </div>
                </div>
                <div>
                  <p className="text-gray-500 mb-16">Supplier,</p>
                  <div className="border-t border-gray-400 pt-2">
                    <p className="font-medium">________________</p>
                    <p className="text-xs text-gray-500">{printData.supplier?.name || 'Supplier'}</p>
                  </div>
                </div>
              </div>
              
              {/* Footer */}
              <div className="mt-8 pt-4 border-t text-center text-xs text-gray-400">
                <p>Dicetak pada: {new Date().toLocaleString('id-ID')} | OCB TITAN ERP System</p>
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* ============================================================ */}
      {/* DELETE MODAL - TASK 2: Delete Policy Confirmation */}
      {/* ============================================================ */}
      {showDeleteModal && deleteTarget && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
          <div className="bg-gray-900 rounded-lg border border-red-700/50 shadow-2xl max-w-lg w-full">
            <div className="p-4 border-b border-red-700/30">
              <h3 className="text-lg font-bold text-red-300 flex items-center gap-2">
                <AlertTriangle className="h-5 w-5" />
                Hapus Purchase Order
              </h3>
            </div>
            
            <div className="p-4">
              <div className="bg-gray-800 rounded p-3 mb-4">
                <p className="text-sm text-gray-400">PO yang akan dihapus:</p>
                <p className="text-lg font-bold text-white">{deleteTarget.po_number}</p>
                <p className="text-sm text-gray-400">
                  Supplier: {deleteTarget.supplier_name} | Total: {formatRupiah(deleteTarget.total)}
                </p>
              </div>
              
              {deletePreview && (
                <div className={`rounded p-3 mb-4 ${deletePreview.impact_analysis.has_any_impact ? 'bg-amber-900/30 border border-amber-600/50' : 'bg-green-900/30 border border-green-600/50'}`}>
                  <p className="text-xs font-medium mb-2 uppercase tracking-wide">
                    {deletePreview.impact_analysis.has_any_impact ? '⚠️ Ada Dampak Transaksi' : '✓ Tidak Ada Dampak'}
                  </p>
                  <div className="text-sm space-y-1">
                    <p>• Receiving: {deletePreview.impact_analysis.has_receiving ? 'Ya' : 'Tidak'}</p>
                    <p>• Stock Movement: {deletePreview.impact_analysis.stock_movements_count}</p>
                    <p>• AP Record: {deletePreview.impact_analysis.ap_records_count}</p>
                    <p>• Journal: {deletePreview.impact_analysis.journal_entries_count}</p>
                  </div>
                  <div className="mt-3 pt-3 border-t border-gray-700">
                    <p className="text-sm">
                      <span className="font-medium">Mode Hapus:</span>{' '}
                      <span className={deletePreview.delete_preview.delete_mode === 'SOFT_DELETE' ? 'text-green-400' : 'text-amber-400'}>
                        {deletePreview.delete_preview.delete_mode}
                      </span>
                    </p>
                    <p className="text-xs text-gray-400 mt-1">{deletePreview.delete_preview.message}</p>
                  </div>
                </div>
              )}
              
              <div className="mb-4">
                <label className="block text-sm text-gray-400 mb-1">Alasan Penghapusan (opsional)</label>
                <textarea
                  value={deleteReason}
                  onChange={(e) => setDeleteReason(e.target.value)}
                  placeholder="Masukkan alasan penghapusan..."
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded text-white text-sm"
                  rows={2}
                />
              </div>
            </div>
            
            <div className="p-4 border-t border-gray-700 flex gap-3 justify-end">
              <button
                onClick={() => { setShowDeleteModal(false); setDeleteTarget(null); setDeleteReason(''); setDeletePreview(null); }}
                className="px-4 py-2 bg-gray-700 text-white rounded hover:bg-gray-600"
              >
                Batal
              </button>
              <button
                onClick={confirmDeletePO}
                className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 flex items-center gap-2"
              >
                <Trash2 className="h-4 w-4" />
                Hapus PO
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PurchaseEnterprise;
