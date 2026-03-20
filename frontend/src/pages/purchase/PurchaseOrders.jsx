import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { 
  Plus, Search, Eye, Printer, Truck, Check, X, RotateCcw, 
  Loader2, FileText, Calendar, Package, ChevronDown, Edit, Edit2, Trash2
} from 'lucide-react';
import { toast } from 'sonner';
import { OwnerEditButton, OwnerEditModal, isOwner } from '../../components/OwnerEditButton';
import ERPActionToolbar from '../../components/ERPActionToolbar';

const PurchaseOrders = () => {
  const { api, user } = useAuth();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [deleteFilter, setDeleteFilter] = useState('active'); // 'active', 'deleted', 'all'
  const [showModal, setShowModal] = useState(false);
  const [showReceiveModal, setShowReceiveModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleteReason, setDeleteReason] = useState('');
  const [deletePreview, setDeletePreview] = useState(null);
  const [reversalPreview, setReversalPreview] = useState(null);
  const [actionMode, setActionMode] = useState('delete'); // 'delete' or 'reverse'
  const [reversing, setReversing] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [selectedItem, setSelectedItem] = useState(null); // For toolbar selection
  const [suppliers, setSuppliers] = useState([]);
  const [products, setProducts] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [cashBankAccounts, setCashBankAccounts] = useState([]);
  const [itemSearchTerm, setItemSearchTerm] = useState('');
  const [showItemSearch, setShowItemSearch] = useState(false);
  const [searchResults, setSearchResults] = useState([]);
  const [activeItemIndex, setActiveItemIndex] = useState(null);
  
  // Owner Edit States
  const [showOwnerEditModal, setShowOwnerEditModal] = useState(false);
  const [ownerEditItem, setOwnerEditItem] = useState(null);
  
  const [formData, setFormData] = useState({
    supplier_id: '',
    warehouse_id: '',
    pic_id: '',
    payment_account_id: '',
    notes: '',
    items: [{ product_id: '', product_name: '', quantity: 1, unit_cost: 0, discount_percent: 0, purchase_unit: '', conversion_ratio: 1, sn_start: '', sn_end: '' }]
  });

  const loadOrders = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        ...(searchTerm && { search: searchTerm }),
        ...(statusFilter && { status: statusFilter }),
        // Delete filter
        ...(deleteFilter === 'deleted' && { only_deleted: 'true' }),
        ...(deleteFilter === 'all' && { include_deleted: 'true' })
        // 'active' is default - no extra param needed
      });
      const res = await api(`/api/purchase/orders?${params}`);
      if (res.ok) {
        const data = await res.json();
        setOrders(data.items || data || []);
      }
    } catch (err) {
      toast.error('Gagal memuat data');
    } finally {
      setLoading(false);
    }
  }, [api, searchTerm, statusFilter, deleteFilter]);

  const loadMasterData = useCallback(async () => {
    try {
      const [supRes, prodRes, whRes, empRes, coaRes] = await Promise.all([
        api('/api/suppliers'),
        api('/api/products'),
        api('/api/master/warehouses'),
        api('/api/hr/employees?status=active'),
        api('/api/account-settings/chart-of-accounts?types=CASH,BANK')
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
        setWarehouses(data.items || data.warehouses || data || []);
      }
      if (empRes.ok) {
        const data = await empRes.json();
        setEmployees(data.employees || data.items || data || []);
      }
      if (coaRes.ok) {
        const data = await coaRes.json();
        setCashBankAccounts(data.accounts || data.items || data || []);
      }
    } catch (err) {
      console.error('Error loading master data');
    }
  }, [api]);

  useEffect(() => {
    loadOrders();
    loadMasterData();
  }, [loadOrders, loadMasterData]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validasi mandatory fields
    if (!formData.supplier_id) {
      toast.error('Pilih supplier terlebih dahulu');
      return;
    }
    if (!formData.warehouse_id) {
      toast.error('Pilih gudang tujuan');
      return;
    }
    if (formData.items.length === 0 || formData.items.every(i => !i.product_id)) {
      toast.error('Minimal harus ada 1 item');
      return;
    }
    if (formData.items.some(i => i.product_id && i.quantity <= 0)) {
      toast.error('Jumlah item harus lebih dari 0');
      return;
    }

    // Calculate total
    const total = calculateTotal();
    
    const payload = {
      ...formData,
      total_amount: total,
      items: formData.items.filter(i => i.product_id) // Only include items with product
    };

    try {
      const res = await api('/api/purchase/orders', {
        method: 'POST',
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        toast.success('Purchase Order berhasil dibuat');
        setShowModal(false);
        resetForm();
        loadOrders();
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Gagal membuat PO');
      }
    } catch (err) {
      toast.error('Terjadi kesalahan');
    }
  };

  const handleSubmitPO = async (order) => {
    if (!confirm(`Submit PO ${order.po_number} ke supplier?`)) return;
    try {
      const res = await api(`/api/purchase/orders/${order.id}/submit`, { method: 'POST' });
      if (res.ok) {
        toast.success('PO berhasil disubmit');
        loadOrders();
      }
    } catch (err) {
      toast.error('Gagal submit PO');
    }
  };

  const handleReceive = async () => {
    if (!selectedOrder) return;
    try {
      const receiveItems = selectedOrder.items.map(item => ({
        product_id: item.product_id,
        quantity: item.quantity - (item.received_quantity || 0)
      }));

      const res = await api(`/api/purchase/orders/${selectedOrder.id}/receive`, {
        method: 'POST',
        body: JSON.stringify({ items: receiveItems, notes: 'Penerimaan barang' })
      });
      if (res.ok) {
        toast.success('Barang berhasil diterima, stok diupdate');
        setShowReceiveModal(false);
        setSelectedOrder(null);
        loadOrders();
      }
    } catch (err) {
      toast.error('Gagal menerima barang');
    }
  };

  const handleCancel = async (order) => {
    if (!confirm(`Batalkan PO ${order.po_number}?`)) return;
    try {
      const res = await api(`/api/purchase/orders/${order.id}/cancel`, { method: 'POST' });
      if (res.ok) {
        toast.success('PO dibatalkan');
        setSelectedItem(null);
        loadOrders();
      }
    } catch (err) {
      toast.error('Gagal membatalkan PO');
    }
  };

  // Delete PO handler - Safe Delete with preview
  const handleDeleteClick = async (order) => {
    try {
      // Determine action based on status
      if (order.status === 'draft') {
        // For draft, use delete preview
        const res = await api(`/api/purchase/orders/${order.id}/delete-preview`);
        if (res.ok) {
          const preview = await res.json();
          setDeleteTarget(order);
          setDeletePreview(preview);
          setReversalPreview(null);
          setActionMode('delete');
          setDeleteReason('');
          setShowDeleteModal(true);
        } else {
          toast.error('Gagal memuat preview hapus');
        }
      } else {
        // For non-draft, use reversal preview
        const res = await api(`/api/purchase/orders/${order.id}/reversal-preview`);
        if (res.ok) {
          const preview = await res.json();
          setDeleteTarget(order);
          setReversalPreview(preview);
          setDeletePreview(null);
          setActionMode(preview.can_delete ? 'delete' : 'reverse');
          setDeleteReason('');
          setShowDeleteModal(true);
        } else {
          const err = await res.json();
          toast.error(err.detail || 'Gagal memuat preview');
        }
      }
    } catch (err) {
      toast.error('Gagal memuat preview');
    }
  };

  const handleDeleteConfirm = async () => {
    if (!deleteTarget) return;
    try {
      const res = await api(`/api/purchase/orders/${deleteTarget.id}?reason=${encodeURIComponent(deleteReason)}`, { 
        method: 'DELETE' 
      });
      if (res.ok) {
        const data = await res.json();
        toast.success(data.message || 'PO berhasil dihapus dari daftar aktif');
        setShowDeleteModal(false);
        setDeleteTarget(null);
        setDeletePreview(null);
        setReversalPreview(null);
        setDeleteReason('');
        setSelectedItem(null);
        loadOrders();
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Gagal menghapus PO');
      }
    } catch (err) {
      toast.error('Gagal menghapus PO');
    }
  };

  const handleReverseConfirm = async () => {
    if (!deleteTarget || !deleteReason.trim()) {
      toast.error('Alasan reversal wajib diisi');
      return;
    }
    
    setReversing(true);
    try {
      const res = await api(`/api/purchase/orders/${deleteTarget.id}/reverse`, {
        method: 'POST',
        body: JSON.stringify({ reason: deleteReason, notes: '' })
      });
      
      if (res.ok) {
        const data = await res.json();
        toast.success(
          <div>
            <div className="font-bold">PO Berhasil di-Reverse!</div>
            <div className="text-sm">
              {data.reversal_summary?.stock_movements_reversed || 0} stok dikembalikan, 
              {data.reversal_summary?.journals_reversed || 0} jurnal di-reverse
            </div>
          </div>,
          { duration: 5000 }
        );
        setShowDeleteModal(false);
        setDeleteTarget(null);
        setReversalPreview(null);
        setDeleteReason('');
        setSelectedItem(null);
        loadOrders();
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Gagal reverse PO');
      }
    } catch (err) {
      toast.error('Gagal reverse PO');
    } finally {
      setReversing(false);
    }
  };

  // Legacy delete handler for backward compatibility
  const handleDelete = async (order) => {
    handleDeleteClick(order);
  };

  // Edit PO handler - open form with existing data
  const handleEdit = (order) => {
    if (order.status !== 'draft') {
      toast.warning('Hanya PO dengan status Draft yang bisa diedit langsung');
      // For non-draft, use owner edit
      setOwnerEditItem(order);
      setShowOwnerEditModal(true);
      return;
    }
    setFormData({
      supplier_id: order.supplier_id || '',
      notes: order.notes || '',
      items: order.items?.map(i => ({
        product_id: i.product_id,
        quantity: i.quantity,
        unit_cost: i.unit_cost,
        discount_percent: i.discount_percent || 0
      })) || [{ product_id: '', quantity: 1, unit_cost: 0, discount_percent: 0 }]
    });
    setSelectedOrder(order);
    setShowModal(true);
  };

  // Print handler
  const handlePrint = (order) => {
    toast.info(`Mencetak PO ${order.po_number}...`);
    // TODO: Implement print functionality
    window.print();
  };

  // Row selection handler
  const handleRowSelect = (order) => {
    if (selectedItem?.id === order.id) {
      setSelectedItem(null);
    } else {
      setSelectedItem(order);
    }
  };

  const resetForm = () => {
    setFormData({
      supplier_id: '',
      warehouse_id: '',
      pic_id: '',
      payment_account_id: '',
      notes: '',
      items: [{ product_id: '', product_name: '', quantity: 1, unit_cost: 0, discount_percent: 0, purchase_unit: '', conversion_ratio: 1, sn_start: '', sn_end: '' }]
    });
    setSelectedOrder(null);
    setItemSearchTerm('');
    setSearchResults([]);
    setShowItemSearch(false);
  };

  const addItem = () => {
    setFormData(prev => ({
      ...prev,
      items: [...prev.items, { product_id: '', product_name: '', quantity: 1, unit_cost: 0, discount_percent: 0, purchase_unit: '', conversion_ratio: 1, sn_start: '', sn_end: '' }]
    }));
  };

  const removeItem = (index) => {
    if (formData.items.length === 1) return;
    setFormData(prev => ({
      ...prev,
      items: prev.items.filter((_, i) => i !== index)
    }));
  };

  const updateItem = (index, field, value) => {
    const newItems = [...formData.items];
    newItems[index][field] = value;
    
    // Auto-fill price and unit when product selected
    if (field === 'product_id') {
      const product = products.find(p => p.id === value);
      if (product) {
        newItems[index].unit_cost = product.cost_price || 0;
        newItems[index].product_name = product.name || '';
        newItems[index].purchase_unit = product.unit || 'pcs';
        newItems[index].conversion_ratio = 1;
      }
    }
    
    setFormData(prev => ({ ...prev, items: newItems }));
  };

  // Item search handler - search then select flow
  const handleItemSearch = (term) => {
    setItemSearchTerm(term);
    if (term.length >= 2) {
      const results = products.filter(p => 
        p.name?.toLowerCase().includes(term.toLowerCase()) ||
        p.code?.toLowerCase().includes(term.toLowerCase()) ||
        p.barcode?.includes(term)
      ).slice(0, 10);
      setSearchResults(results);
      setShowItemSearch(true);
    } else {
      setSearchResults([]);
      setShowItemSearch(false);
    }
  };

  // Select item from search results
  const selectSearchItem = (product, itemIndex) => {
    const newItems = [...formData.items];
    newItems[itemIndex] = {
      ...newItems[itemIndex],
      product_id: product.id,
      product_name: product.name,
      unit_cost: product.cost_price || 0,
      purchase_unit: product.unit || 'pcs',
      conversion_ratio: 1
    };
    setFormData(prev => ({ ...prev, items: newItems }));
    setShowItemSearch(false);
    setItemSearchTerm('');
    setSearchResults([]);
    setActiveItemIndex(null);
  };

  const getStatusBadge = (status, isDeleted = false) => {
    const badges = {
      draft: 'bg-gray-600/20 text-gray-400',
      submitted: 'bg-blue-600/20 text-blue-400',
      ordered: 'bg-blue-600/20 text-blue-400',
      partial: 'bg-yellow-600/20 text-yellow-400',
      received: 'bg-green-600/20 text-green-400',
      cancelled: 'bg-red-600/20 text-red-400',
      deleted: 'bg-red-800/30 text-red-300 line-through'
    };
    const labels = {
      draft: 'Draft',
      submitted: 'Disubmit',
      ordered: 'Dipesan',
      partial: 'Sebagian',
      received: 'Diterima',
      cancelled: 'Dibatalkan',
      deleted: 'Dihapus'
    };
    
    // If deleted, show deleted badge
    if (isDeleted || status === 'deleted') {
      return (
        <span className={`px-2 py-1 rounded-full text-xs ${badges.deleted}`}>
          🗑️ {labels.deleted}
        </span>
      );
    }
    
    return (
      <span className={`px-2 py-1 rounded-full text-xs ${badges[status] || badges.draft}`}>
        {labels[status] || status}
      </span>
    );
  };

  const calculateTotal = () => {
    return formData.items.reduce((sum, item) => {
      const subtotal = item.quantity * item.unit_cost;
      const discount = subtotal * (item.discount_percent / 100);
      return sum + subtotal - discount;
    }, 0);
  };

  return (
    <div className="space-y-4" data-testid="purchase-orders-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Pesanan Pembelian</h1>
          <p className="text-gray-400 text-sm">Kelola purchase order ke supplier</p>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Cari no. PO, supplier..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200"
            />
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-4 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200"
          >
            <option value="">Semua Status</option>
            <option value="draft">Draft</option>
            <option value="submitted">Disubmit</option>
            <option value="ordered">Dipesan</option>
            <option value="partial">Sebagian Diterima</option>
            <option value="received">Diterima</option>
            <option value="cancelled">Dibatalkan</option>
            <option value="deleted">Dihapus</option>
          </select>
          <select
            value={deleteFilter}
            onChange={(e) => setDeleteFilter(e.target.value)}
            className="px-4 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200"
            data-testid="delete-filter"
          >
            <option value="active">Aktif Saja</option>
            <option value="deleted">Dihapus Saja</option>
            <option value="all">Semua (Termasuk Dihapus)</option>
          </select>
        </div>
      </div>

      {/* TOOLBAR STANDAR ERP */}
      <ERPActionToolbar
        module="purchase_order"
        selectedItem={selectedItem}
        onAdd={() => { resetForm(); setShowModal(true); }}
        onEdit={(item) => handleEdit(item)}
        onDelete={(item) => handleDelete(item)}
        onPrint={(item) => handlePrint(item)}
        onApprove={(item) => handleSubmitPO(item)}
        onReceive={(item) => { setSelectedOrder(item); setShowReceiveModal(true); }}
        addLabel="Tambah PO"
        editLabel="Edit PO"
        deleteLabel="Hapus PO"
      />

      {/* Table */}
      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-red-900/20">
              <tr>
                <th className="px-3 py-3 text-center text-xs font-semibold text-amber-200 w-10">
                  <input type="checkbox" className="w-3 h-3" disabled />
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">NO. PO</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">TANGGAL</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">SUPPLIER</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-amber-200">ITEMS</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-amber-200">TOTAL</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">STATUS</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">AKSI</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-red-900/20">
              {loading ? (
                <tr><td colSpan={8} className="px-4 py-8 text-center"><Loader2 className="h-8 w-8 animate-spin mx-auto text-amber-400" /></td></tr>
              ) : orders.length === 0 ? (
                <tr><td colSpan={8} className="px-4 py-8 text-center text-gray-400">Belum ada purchase order</td></tr>
              ) : orders.map((order, idx) => (
                <tr 
                  key={order.id} 
                  onClick={() => handleRowSelect(order)}
                  className={`cursor-pointer transition-colors ${
                    selectedItem?.id === order.id 
                      ? 'bg-amber-900/30 border-l-2 border-amber-500' 
                      : 'hover:bg-red-900/10'
                  }`}
                  data-testid={`po-row-${idx}`}
                >
                  <td className="px-3 py-3 text-center">
                    <input 
                      type="radio" 
                      checked={selectedItem?.id === order.id}
                      onChange={() => handleRowSelect(order)}
                      className="w-3 h-3 accent-amber-500"
                    />
                  </td>
                  <td className="px-4 py-3">
                    <div className="font-medium text-amber-300 font-mono">{order.po_number}</div>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-400">
                    {new Date(order.created_at).toLocaleDateString('id-ID')}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-200">{order.supplier_name}</td>
                  <td className="px-4 py-3 text-sm text-right text-gray-300">{order.items?.length || 0} item</td>
                  <td className="px-4 py-3 text-sm text-right text-green-400 font-medium">
                    Rp {(order.total || 0).toLocaleString('id-ID')}
                  </td>
                  <td className="px-4 py-3 text-center">{getStatusBadge(order.status, order.is_deleted)}</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-center gap-1">
                      {/* Show actions only if not deleted */}
                      {!order.is_deleted && (
                        <>
                          {order.status === 'draft' && (
                            <button 
                              onClick={() => handleSubmitPO(order)}
                              className="p-1.5 hover:bg-blue-600/20 rounded text-blue-400"
                              title="Submit ke Supplier"
                            >
                              <Truck className="h-4 w-4" />
                            </button>
                          )}
                          {(order.status === 'submitted' || order.status === 'partial' || order.status === 'ordered') && (
                            <button 
                              onClick={() => { setSelectedOrder(order); setShowReceiveModal(true); }}
                              className="p-1.5 hover:bg-green-600/20 rounded text-green-400"
                              title="Terima Barang"
                            >
                              <Check className="h-4 w-4" />
                            </button>
                          )}
                          <button 
                            onClick={() => handleDeleteClick(order)}
                            className="p-1.5 hover:bg-red-600/20 rounded text-red-400"
                            title="Hapus PO"
                            data-testid={`delete-btn-${order.po_number}`}
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </>
                      )}
                      {order.is_deleted && (
                        <span className="text-xs text-gray-500 italic">Dihapus</span>
                      )}
                      <button className="p-1.5 hover:bg-gray-600/20 rounded text-gray-400" title="Print">
                        <Printer className="h-4 w-4" />
                      </button>
                      
                      {/* OWNER EDIT BUTTON */}
                      <OwnerEditButton
                        item={order}
                        module="purchase-order"
                        onEdit={(item) => { setOwnerEditItem(item); setShowOwnerEditModal(true); }}
                        size="sm"
                        showLabel={false}
                      />
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Create PO Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <div className="p-4 border-b border-red-900/30 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-amber-100">Buat Purchase Order Baru</h2>
              <button onClick={() => setShowModal(false)} className="p-1 hover:bg-red-900/20 rounded">
                <X className="h-5 w-5" />
              </button>
            </div>
            <form onSubmit={handleSubmit} className="p-4 space-y-4">
              {/* Row 1: Supplier & Warehouse */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Supplier *</label>
                  <select
                    value={formData.supplier_id}
                    onChange={(e) => setFormData({ ...formData, supplier_id: e.target.value })}
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg"
                    required
                    data-testid="po-supplier-select"
                  >
                    <option value="">Pilih Supplier</option>
                    {suppliers.map(s => (
                      <option key={s.id} value={s.id}>{s.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Gudang Tujuan *</label>
                  <select
                    value={formData.warehouse_id}
                    onChange={(e) => setFormData({ ...formData, warehouse_id: e.target.value })}
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg"
                    required
                    data-testid="po-warehouse-select"
                  >
                    <option value="">Pilih Gudang</option>
                    {warehouses.map(w => (
                      <option key={w.id} value={w.id}>{w.name}</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Row 2: PIC & Payment Account */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">PIC (Person in Charge)</label>
                  <select
                    value={formData.pic_id}
                    onChange={(e) => setFormData({ ...formData, pic_id: e.target.value })}
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg"
                    data-testid="po-pic-select"
                  >
                    <option value="">Pilih PIC</option>
                    {employees.map(emp => (
                      <option key={emp.id} value={emp.id}>{emp.name} - {emp.position || 'Staff'}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Akun Pembayaran</label>
                  <select
                    value={formData.payment_account_id}
                    onChange={(e) => setFormData({ ...formData, payment_account_id: e.target.value })}
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg"
                    data-testid="po-payment-account-select"
                  >
                    <option value="">Pilih Akun Kas/Bank</option>
                    {cashBankAccounts.map(acc => (
                      <option key={acc.id} value={acc.id}>{acc.code} - {acc.name}</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Row 3: Notes */}
              <div>
                <label className="block text-sm text-gray-400 mb-1">Catatan</label>
                <input
                  type="text"
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg"
                  placeholder="Catatan tambahan..."
                  data-testid="po-notes-input"
                />
              </div>

              {/* Items */}
              <div className="border border-red-900/30 rounded-lg overflow-hidden">
                <div className="bg-red-900/20 px-4 py-2 flex items-center justify-between">
                  <span className="font-medium text-amber-200">Item Pembelian</span>
                  <button type="button" onClick={addItem} className="text-sm text-amber-400 hover:text-amber-300" data-testid="po-add-item-btn">
                    + Tambah Item
                  </button>
                </div>
                <table className="w-full">
                  <thead className="bg-red-900/10">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs text-gray-400">PRODUK</th>
                      <th className="px-4 py-2 text-center text-xs text-gray-400 w-20">QTY</th>
                      <th className="px-4 py-2 text-center text-xs text-gray-400 w-20">SATUAN</th>
                      <th className="px-4 py-2 text-right text-xs text-gray-400 w-28">HARGA</th>
                      <th className="px-4 py-2 text-center text-xs text-gray-400 w-16">DISK %</th>
                      <th className="px-4 py-2 text-center text-xs text-gray-400 w-24">SN AWAL</th>
                      <th className="px-4 py-2 text-center text-xs text-gray-400 w-24">SN AKHIR</th>
                      <th className="px-4 py-2 text-right text-xs text-gray-400 w-28">SUBTOTAL</th>
                      <th className="px-4 py-2 w-10"></th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-red-900/20">
                    {formData.items.map((item, idx) => {
                      const subtotal = item.quantity * item.unit_cost * (1 - item.discount_percent/100);
                      const snCount = (item.sn_start && item.sn_end) ? 
                        Math.max(0, parseInt(item.sn_end) - parseInt(item.sn_start) + 1) : 0;
                      return (
                        <tr key={idx}>
                          {/* Product Search with Click-to-Select Flow */}
                          <td className="px-4 py-2 relative">
                            {item.product_id ? (
                              <div className="flex items-center gap-2">
                                <span className="text-sm text-gray-200 flex-1">{item.product_name || products.find(p => p.id === item.product_id)?.name || 'Product'}</span>
                                <button 
                                  type="button" 
                                  onClick={() => updateItem(idx, 'product_id', '')} 
                                  className="text-red-400 hover:text-red-300 text-xs"
                                >
                                  <X className="h-3 w-3" />
                                </button>
                              </div>
                            ) : (
                              <div className="relative">
                                <input
                                  type="text"
                                  placeholder="Cari produk..."
                                  value={activeItemIndex === idx ? itemSearchTerm : ''}
                                  onChange={(e) => { setActiveItemIndex(idx); handleItemSearch(e.target.value); }}
                                  onFocus={() => setActiveItemIndex(idx)}
                                  className="w-full px-2 py-1 bg-[#0a0608] border border-red-900/30 rounded text-sm"
                                  data-testid={`po-item-search-${idx}`}
                                />
                                {/* Search Results Dropdown */}
                                {showItemSearch && activeItemIndex === idx && searchResults.length > 0 && (
                                  <div className="absolute z-10 w-full mt-1 bg-[#1a1214] border border-red-900/30 rounded-lg shadow-lg max-h-48 overflow-y-auto">
                                    {searchResults.map(p => (
                                      <button
                                        key={p.id}
                                        type="button"
                                        onClick={() => selectSearchItem(p, idx)}
                                        className="w-full px-3 py-2 text-left text-sm hover:bg-red-900/20 flex justify-between"
                                        data-testid={`po-item-option-${p.id}`}
                                      >
                                        <span>{p.name}</span>
                                        <span className="text-gray-500">{p.code}</span>
                                      </button>
                                    ))}
                                  </div>
                                )}
                              </div>
                            )}
                          </td>
                          <td className="px-4 py-2">
                            <input
                              type="number"
                              min="1"
                              value={item.quantity}
                              onChange={(e) => updateItem(idx, 'quantity', Number(e.target.value))}
                              className="w-full px-2 py-1 bg-[#0a0608] border border-red-900/30 rounded text-sm text-center"
                              data-testid={`po-item-qty-${idx}`}
                            />
                          </td>
                          {/* Purchase Unit - Can be changed */}
                          <td className="px-4 py-2">
                            <select
                              value={item.purchase_unit || 'pcs'}
                              onChange={(e) => updateItem(idx, 'purchase_unit', e.target.value)}
                              className="w-full px-1 py-1 bg-[#0a0608] border border-red-900/30 rounded text-sm text-center"
                              data-testid={`po-item-unit-${idx}`}
                            >
                              <option value="pcs">pcs</option>
                              <option value="box">box</option>
                              <option value="karton">karton</option>
                              <option value="lusin">lusin</option>
                              <option value="pak">pak</option>
                              <option value="rim">rim</option>
                              <option value="kg">kg</option>
                              <option value="liter">liter</option>
                            </select>
                          </td>
                          <td className="px-4 py-2">
                            <input
                              type="number"
                              min="0"
                              value={item.unit_cost}
                              onChange={(e) => updateItem(idx, 'unit_cost', Number(e.target.value))}
                              className="w-full px-2 py-1 bg-[#0a0608] border border-red-900/30 rounded text-sm text-right"
                              data-testid={`po-item-price-${idx}`}
                            />
                          </td>
                          <td className="px-4 py-2">
                            <input
                              type="number"
                              min="0"
                              max="100"
                              value={item.discount_percent}
                              onChange={(e) => updateItem(idx, 'discount_percent', Number(e.target.value))}
                              className="w-full px-1 py-1 bg-[#0a0608] border border-red-900/30 rounded text-sm text-center"
                              data-testid={`po-item-discount-${idx}`}
                            />
                          </td>
                          {/* PRIORITAS 5: SN Awal */}
                          <td className="px-4 py-2">
                            <input
                              type="text"
                              value={item.sn_start || ''}
                              onChange={(e) => updateItem(idx, 'sn_start', e.target.value)}
                              className="w-full px-2 py-1 bg-[#0a0608] border border-red-900/30 rounded text-sm text-center"
                              placeholder="10001"
                              data-testid={`sn-start-${idx}`}
                            />
                          </td>
                          {/* PRIORITAS 5: SN Akhir */}
                          <td className="px-4 py-2">
                            <div>
                              <input
                                type="text"
                                value={item.sn_end || ''}
                                onChange={(e) => updateItem(idx, 'sn_end', e.target.value)}
                                className="w-full px-2 py-1 bg-[#0a0608] border border-red-900/30 rounded text-sm text-center"
                                placeholder="10010"
                                data-testid={`sn-end-${idx}`}
                              />
                              {snCount > 0 && (
                                <p className="text-xs text-gray-500 text-center mt-0.5">{snCount} unit</p>
                              )}
                            </div>
                          </td>
                          <td className="px-4 py-2 text-right text-sm text-green-400">
                            Rp {subtotal.toLocaleString('id-ID')}
                          </td>
                          <td className="px-4 py-2">
                            {formData.items.length > 1 && (
                              <button 
                                type="button" 
                                onClick={() => removeItem(idx)}
                                className="p-1 hover:bg-red-600/20 rounded text-red-400"
                              >
                                <X className="h-4 w-4" />
                              </button>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                  <tfoot className="bg-red-900/10">
                    <tr>
                      <td colSpan={4} className="px-4 py-3 text-right font-semibold text-amber-200">TOTAL:</td>
                      <td className="px-4 py-3 text-right font-bold text-green-400">
                        Rp {calculateTotal().toLocaleString('id-ID')}
                      </td>
                      <td></td>
                    </tr>
                  </tfoot>
                </table>
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-red-900/30">
                <button type="button" onClick={() => setShowModal(false)} className="px-4 py-2 border border-red-900/30 rounded-lg">
                  Batal
                </button>
                <button type="submit" className="px-4 py-2 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg">
                  Simpan PO
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Receive Modal */}
      {showReceiveModal && selectedOrder && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-2xl">
            <div className="p-4 border-b border-red-900/30 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-amber-100">
                Terima Barang - {selectedOrder.po_number}
              </h2>
              <button onClick={() => setShowReceiveModal(false)} className="p-1 hover:bg-red-900/20 rounded">
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="p-4">
              <p className="text-gray-400 mb-4">Barang yang akan diterima:</p>
              <table className="w-full mb-4">
                <thead className="bg-red-900/20">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs text-amber-200">PRODUK</th>
                    <th className="px-4 py-2 text-center text-xs text-amber-200">DIPESAN</th>
                    <th className="px-4 py-2 text-center text-xs text-amber-200">DITERIMA</th>
                    <th className="px-4 py-2 text-center text-xs text-amber-200">SISA</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-red-900/20">
                  {selectedOrder.items?.map((item, idx) => (
                    <tr key={idx}>
                      <td className="px-4 py-2 text-gray-200">{item.product_name}</td>
                      <td className="px-4 py-2 text-center text-gray-400">{item.quantity}</td>
                      <td className="px-4 py-2 text-center text-green-400">{item.received_quantity || 0}</td>
                      <td className="px-4 py-2 text-center text-amber-400">
                        {item.quantity - (item.received_quantity || 0)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div className="flex justify-end gap-3">
                <button 
                  onClick={() => setShowReceiveModal(false)} 
                  className="px-4 py-2 border border-red-900/30 rounded-lg"
                >
                  Batal
                </button>
                <button 
                  onClick={handleReceive}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg flex items-center gap-2"
                >
                  <Check className="h-4 w-4" /> Terima Semua Sisa
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* Delete/Reverse Confirmation Modal */}
      {showDeleteModal && deleteTarget && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-xl" data-testid="delete-modal">
            <div className="p-4 border-b border-red-900/30 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-amber-100">
                {reversalPreview?.action_recommended === 'REVERSE' || reversalPreview?.action_recommended === 'REVERSE_PAYMENTS_FIRST'
                  ? `Reverse PO - ${deleteTarget.po_number}`
                  : `Hapus PO - ${deleteTarget.po_number}`
                }
              </h2>
              <button onClick={() => setShowDeleteModal(false)} className="p-1 hover:bg-red-900/20 rounded">
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="p-4 space-y-4 max-h-[70vh] overflow-y-auto">
              
              {/* DRAFT DELETE - Simple Mode */}
              {deleteTarget.status === 'draft' && deletePreview && (
                <div className="space-y-3">
                  <div className="p-3 rounded-lg bg-green-900/20 border border-green-600/30">
                    <p className="text-sm text-green-200 font-medium mb-1">✅ PO Status: DRAFT</p>
                    <p className="text-green-100 text-sm">
                      PO ini dapat dihapus langsung karena belum ada transaksi terkait.
                    </p>
                  </div>
                </div>
              )}
              
              {/* REVERSAL MODE - Complex Mode */}
              {reversalPreview && (
                <div className="space-y-4">
                  {/* Status Info */}
                  <div className="p-3 rounded-lg bg-amber-900/20 border border-amber-600/30">
                    <p className="text-sm text-amber-200 font-medium mb-1">
                      ⚠️ PO Status: {deleteTarget.status?.toUpperCase()}
                    </p>
                    <p className="text-amber-100 text-sm">
                      {reversalPreview.message}
                    </p>
                  </div>
                  
                  {/* Active Payments Warning */}
                  {reversalPreview.has_active_payments && (
                    <div className="p-3 rounded-lg bg-red-900/30 border border-red-600/50">
                      <p className="text-sm text-red-200 font-bold mb-2">
                        🚫 TIDAK DAPAT DI-REVERSE
                      </p>
                      <p className="text-red-100 text-sm mb-2">
                        Ada {reversalPreview.summary?.blocking_payments || 0} pembayaran aktif yang harus di-reverse terlebih dahulu:
                      </p>
                      <ul className="text-sm text-gray-300 space-y-1 ml-4">
                        {reversalPreview.impacts?.payments?.slice(0, 5).map((p, idx) => (
                          <li key={idx}>• {p.payment_no} - Rp {(p.amount || 0).toLocaleString('id-ID')}</li>
                        ))}
                      </ul>
                      <p className="text-xs text-gray-400 mt-2">
                        Buka menu Hutang → Pembayaran Hutang untuk reverse pembayaran.
                      </p>
                    </div>
                  )}
                  
                  {/* Reversal Impact Preview */}
                  {!reversalPreview.has_active_payments && reversalPreview.impacts && (
                    <div className="space-y-3">
                      <p className="text-sm text-gray-300 font-medium">
                        Berikut yang akan terjadi jika PO di-reverse:
                      </p>
                      
                      {/* Stock Impact */}
                      {reversalPreview.impacts.stock_movements?.length > 0 && (
                        <div className="p-3 rounded-lg bg-blue-900/20 border border-blue-600/30">
                          <p className="text-sm text-blue-200 font-medium mb-2">
                            📦 Stok akan dikembalikan ({reversalPreview.summary?.total_stock_movements} item)
                          </p>
                          <ul className="text-xs text-gray-300 space-y-1 max-h-24 overflow-y-auto">
                            {reversalPreview.impacts.stock_movements.slice(0, 5).map((s, idx) => (
                              <li key={idx}>• {s.product_name}: -{s.quantity} pcs</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      
                      {/* AP Impact */}
                      {reversalPreview.impacts.ap_records?.length > 0 && (
                        <div className="p-3 rounded-lg bg-purple-900/20 border border-purple-600/30">
                          <p className="text-sm text-purple-200 font-medium mb-2">
                            💳 Hutang akan di-cancel ({reversalPreview.summary?.total_ap_records} record)
                          </p>
                          <ul className="text-xs text-gray-300 space-y-1">
                            {reversalPreview.impacts.ap_records.slice(0, 3).map((ap, idx) => (
                              <li key={idx}>• {ap.ap_number}: Rp {(ap.amount || 0).toLocaleString('id-ID')}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      
                      {/* Journal Impact */}
                      {reversalPreview.impacts.journals?.length > 0 && (
                        <div className="p-3 rounded-lg bg-orange-900/20 border border-orange-600/30">
                          <p className="text-sm text-orange-200 font-medium mb-2">
                            📒 Jurnal akan di-reverse ({reversalPreview.summary?.total_journals} jurnal)
                          </p>
                          <ul className="text-xs text-gray-300 space-y-1">
                            {reversalPreview.impacts.journals.slice(0, 3).map((j, idx) => (
                              <li key={idx}>• {j.journal_no}: Rp {(j.total_debit || 0).toLocaleString('id-ID')}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
              
              {/* Legacy Delete Preview (for cancel_hide mode) */}
              {deletePreview && deleteTarget.status !== 'draft' && !reversalPreview && (
                <div className="space-y-3">
                  <div className="p-3 rounded-lg bg-amber-900/20 border border-amber-600/30">
                    <p className="text-sm text-amber-200 font-medium mb-2">Mode Penghapusan:</p>
                    <p className="text-amber-100">
                      {deletePreview.delete_preview?.delete_mode === 'SOFT_DELETE' 
                        ? '📝 Soft Delete - PO akan dihapus tanpa dampak transaksi' 
                        : '🔒 Cancel & Hide - PO akan disembunyikan, jejak transaksi tetap aman'}
                    </p>
                  </div>
                  
                  {deletePreview.impact_analysis?.has_any_impact && (
                    <div className="p-3 rounded-lg bg-red-900/20 border border-red-600/30">
                      <p className="text-sm text-red-200 font-medium mb-2">⚠️ Dampak Transaksi Terdeteksi:</p>
                      <ul className="text-sm text-gray-300 space-y-1">
                        {deletePreview.impact_analysis.has_receiving && (
                          <li>• Sudah ada penerimaan barang</li>
                        )}
                        {deletePreview.impact_analysis.stock_movements_count > 0 && (
                          <li>• {deletePreview.impact_analysis.stock_movements_count} pergerakan stok</li>
                        )}
                        {deletePreview.impact_analysis.ap_records_count > 0 && (
                          <li>• {deletePreview.impact_analysis.ap_records_count} catatan hutang (AP)</li>
                        )}
                        {deletePreview.impact_analysis.journal_entries_count > 0 && (
                          <li>• {deletePreview.impact_analysis.journal_entries_count} jurnal akuntansi</li>
                        )}
                      </ul>
                      <p className="text-xs text-gray-400 mt-2">
                        Data transaksi akan tetap tersimpan untuk audit trail.
                      </p>
                    </div>
                  )}
                </div>
              )}
              
              {/* Reason Input */}
              <div>
                <label className="block text-sm text-gray-400 mb-1">
                  Alasan {reversalPreview?.can_reverse ? 'Reversal' : 'Penghapusan'} 
                  {reversalPreview?.can_reverse && <span className="text-red-400">*</span>}
                </label>
                <textarea
                  value={deleteReason}
                  onChange={(e) => setDeleteReason(e.target.value)}
                  placeholder={reversalPreview?.can_reverse ? "Wajib isi alasan reversal..." : "Masukkan alasan penghapusan..."}
                  className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200 resize-none"
                  rows={2}
                  data-testid="delete-reason-input"
                />
              </div>
              
              {/* Action Buttons */}
              <div className="flex justify-end gap-3 pt-2">
                <button 
                  onClick={() => setShowDeleteModal(false)} 
                  className="px-4 py-2 border border-red-900/30 rounded-lg text-gray-300 hover:bg-red-900/20"
                >
                  Batal
                </button>
                
                {/* Show REVERSE button for non-draft POs that can be reversed */}
                {reversalPreview?.can_reverse && (
                  <button 
                    onClick={handleReverseConfirm}
                    disabled={reversing || !deleteReason.trim()}
                    className="px-4 py-2 bg-amber-600 text-white rounded-lg flex items-center gap-2 hover:bg-amber-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    data-testid="confirm-reverse-btn"
                  >
                    {reversing ? <Loader2 className="h-4 w-4 animate-spin" /> : <RotateCcw className="h-4 w-4" />}
                    Reverse PO
                  </button>
                )}
                
                {/* Show DELETE button for draft or if reversal not available */}
                {(deleteTarget.status === 'draft' || (deletePreview && !reversalPreview)) && (
                  <button 
                    onClick={handleDeleteConfirm}
                    className="px-4 py-2 bg-red-600 text-white rounded-lg flex items-center gap-2 hover:bg-red-700"
                    data-testid="confirm-delete-btn"
                  >
                    <Trash2 className="h-4 w-4" /> Hapus PO
                  </button>
                )}
                
                {/* Show disabled state for blocked reversals */}
                {reversalPreview?.has_active_payments && (
                  <button 
                    disabled
                    className="px-4 py-2 bg-gray-600 text-gray-400 rounded-lg flex items-center gap-2 cursor-not-allowed"
                  >
                    <X className="h-4 w-4" /> Tidak Dapat Diproses
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* Owner Edit Modal */}
      <OwnerEditModal
        isOpen={showOwnerEditModal}
        onClose={() => { setShowOwnerEditModal(false); setOwnerEditItem(null); }}
        module="purchase-order"
        item={ownerEditItem}
        fields={[
          { name: 'notes', label: 'Catatan', type: 'textarea', placeholder: 'Catatan PO...' },
          { name: 'expected_date', label: 'Tanggal Diharapkan', type: 'date' }
        ]}
        onSave={() => { setShowOwnerEditModal(false); setOwnerEditItem(null); loadOrders(); }}
      />
    </div>
  );
};

export default PurchaseOrders;
