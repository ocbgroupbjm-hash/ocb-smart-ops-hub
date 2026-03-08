import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Package, AlertTriangle, ArrowRight, Search, Plus, Minus, RefreshCw, Loader2, Send, FileCheck, X } from 'lucide-react';
import { toast } from 'sonner';

const Inventory = () => {
  const { api, user } = useAuth();
  const [activeTab, setActiveTab] = useState('stock');
  const [stock, setStock] = useState([]);
  const [lowStock, setLowStock] = useState([]);
  const [movements, setMovements] = useState([]);
  const [transfers, setTransfers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showAdjustModal, setShowAdjustModal] = useState(false);
  const [showTransferModal, setShowTransferModal] = useState(false);
  const [showOpnameModal, setShowOpnameModal] = useState(false);
  const [showStockInModal, setShowStockInModal] = useState(false);
  const [showStockOutModal, setShowStockOutModal] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [adjustQty, setAdjustQty] = useState(0);
  const [adjustReason, setAdjustReason] = useState('');
  const [branches, setBranches] = useState([]);
  const [products, setProducts] = useState([]);
  const [transferForm, setTransferForm] = useState({ to_branch_id: '', items: [] });
  const [opnameItems, setOpnameItems] = useState([]);
  const [stockInForm, setStockInForm] = useState({ product_id: '', quantity: 0, notes: '' });
  const [stockOutForm, setStockOutForm] = useState({ product_id: '', quantity: 0, notes: '' });
  const [saving, setSaving] = useState(false);

  const formatRupiah = (num) => `Rp ${(num || 0).toLocaleString('id-ID')}`;

  useEffect(() => {
    loadBranches();
    loadProducts();
    if (activeTab === 'stock') loadStock();
    else if (activeTab === 'low-stock') loadLowStock();
    else if (activeTab === 'movements') loadMovements();
    else if (activeTab === 'transfers') loadTransfers();
  }, [activeTab, search]);

  const loadBranches = async () => {
    try {
      const res = await api('/api/branches');
      if (res.ok) setBranches(await res.json());
    } catch (err) { console.error(err); }
  };

  const loadProducts = async () => {
    try {
      const res = await api('/api/products?limit=500');
      if (res.ok) { const data = await res.json(); setProducts(data.items || []); }
    } catch (err) { console.error(err); }
  };

  const loadStock = async () => {
    setLoading(true);
    try {
      let url = `/api/inventory/stock?limit=200`;
      if (search) url += `&search=${encodeURIComponent(search)}`;
      const res = await api(url);
      if (res.ok) { const data = await res.json(); setStock(data.items || []); }
    } catch (err) { toast.error('Gagal memuat stok'); }
    finally { setLoading(false); }
  };

  const loadLowStock = async () => {
    setLoading(true);
    try {
      const res = await api('/api/inventory/stock/low');
      if (res.ok) setLowStock(await res.json());
    } catch (err) { toast.error('Gagal memuat stok menipis'); }
    finally { setLoading(false); }
  };

  const loadMovements = async () => {
    setLoading(true);
    try {
      const res = await api('/api/inventory/movements?limit=100');
      if (res.ok) { const data = await res.json(); setMovements(data.items || []); }
    } catch (err) { toast.error('Gagal memuat mutasi'); }
    finally { setLoading(false); }
  };

  const loadTransfers = async () => {
    setLoading(true);
    try {
      const res = await api('/api/inventory/transfers?limit=50');
      if (res.ok) { const data = await res.json(); setTransfers(data.items || []); }
    } catch (err) { toast.error('Gagal memuat transfer'); }
    finally { setLoading(false); }
  };

  const handleAdjust = async () => {
    if (!selectedProduct || adjustQty === 0) return;
    try {
      const res = await api('/api/inventory/adjust', {
        method: 'POST',
        body: JSON.stringify({ product_id: selectedProduct.product_id, quantity: adjustQty, reason: adjustReason })
      });
      if (res.ok) { toast.success('Stok disesuaikan'); setShowAdjustModal(false); loadStock(); }
      else { const error = await res.json(); toast.error(error.detail || 'Gagal'); }
    } catch (err) { toast.error('Gagal menyesuaikan stok'); }
  };

  const openAdjustModal = (item) => { setSelectedProduct(item); setAdjustQty(0); setAdjustReason(''); setShowAdjustModal(true); };

  const handleTransfer = async () => {
    if (!transferForm.to_branch_id || transferForm.items.length === 0) {
      toast.error('Pilih cabang tujuan dan tambahkan item');
      return;
    }
    try {
      const res = await api('/api/inventory/transfer', {
        method: 'POST',
        body: JSON.stringify({
          from_branch_id: user.branch_id,
          to_branch_id: transferForm.to_branch_id,
          items: transferForm.items
        })
      });
      if (res.ok) { toast.success('Transfer dibuat'); setShowTransferModal(false); setTransferForm({ to_branch_id: '', items: [] }); loadTransfers(); }
      else { const error = await res.json(); toast.error(error.detail || 'Gagal'); }
    } catch (err) { toast.error('Gagal membuat transfer'); }
  };

  const handleSendTransfer = async (id) => {
    try {
      const res = await api(`/api/inventory/transfer/${id}/send`, { method: 'POST' });
      if (res.ok) { toast.success('Transfer dikirim'); loadTransfers(); }
    } catch (err) { toast.error('Gagal mengirim'); }
  };

  const handleReceiveTransfer = async (id) => {
    try {
      const res = await api(`/api/inventory/transfer/${id}/receive`, { method: 'POST' });
      if (res.ok) { toast.success('Transfer diterima'); loadTransfers(); }
    } catch (err) { toast.error('Gagal menerima'); }
  };

  const handleOpname = async () => {
    if (opnameItems.length === 0) { toast.error('Tambahkan item untuk opname'); return; }
    try {
      const res = await api('/api/inventory/opname', {
        method: 'POST',
        body: JSON.stringify({ items: opnameItems, notes: 'Stok opname' })
      });
      if (res.ok) {
        const data = await res.json();
        // Auto approve
        await api(`/api/inventory/opname/${data.id}/approve`, { method: 'POST' });
        toast.success('Stok opname berhasil'); setShowOpnameModal(false); setOpnameItems([]); loadStock();
      }
    } catch (err) { toast.error('Gagal melakukan opname'); }
  };

  const handleStockIn = async () => {
    if (!stockInForm.product_id || stockInForm.quantity <= 0) {
      toast.error('Pilih produk dan masukkan jumlah');
      return;
    }
    setSaving(true);
    try {
      const res = await api('/api/inventory/stock-in', {
        method: 'POST',
        body: JSON.stringify(stockInForm)
      });
      if (res.ok) {
        toast.success('Stok berhasil ditambahkan');
        setShowStockInModal(false);
        setStockInForm({ product_id: '', quantity: 0, notes: '' });
        loadStock();
        loadMovements();
      } else {
        const error = await res.json();
        toast.error(error.detail || 'Gagal menambah stok');
      }
    } catch (err) { toast.error('Gagal menambah stok'); }
    finally { setSaving(false); }
  };

  const handleStockOut = async () => {
    if (!stockOutForm.product_id || stockOutForm.quantity <= 0) {
      toast.error('Pilih produk dan masukkan jumlah');
      return;
    }
    setSaving(true);
    try {
      const res = await api('/api/inventory/stock-out', {
        method: 'POST',
        body: JSON.stringify(stockOutForm)
      });
      if (res.ok) {
        toast.success('Stok berhasil dikurangi');
        setShowStockOutModal(false);
        setStockOutForm({ product_id: '', quantity: 0, notes: '' });
        loadStock();
        loadMovements();
      } else {
        const error = await res.json();
        toast.error(error.detail || 'Gagal mengurangi stok');
      }
    } catch (err) { toast.error('Gagal mengurangi stok'); }
    finally { setSaving(false); }
  };

  const tabs = [
    { id: 'stock', label: 'Stok Cabang', icon: Package },
    { id: 'low-stock', label: 'Stok Menipis', icon: AlertTriangle },
    { id: 'movements', label: 'Mutasi Stok', icon: ArrowRight },
    { id: 'transfers', label: 'Transfer Cabang', icon: Send }
  ];

  const movementLabels = {
    sale: 'Penjualan', stock_in: 'Stok Masuk', stock_out: 'Stok Keluar',
    adjustment: 'Penyesuaian', transfer: 'Transfer', return: 'Retur', opname: 'Opname'
  };

  const transferStatusLabels = {
    pending: 'Menunggu', in_transit: 'Dalam Perjalanan', received: 'Diterima', cancelled: 'Dibatalkan'
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Stok & Inventori</h1>
          <p className="text-gray-400">Kelola stok produk antar cabang</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => setShowStockInModal(true)} className="px-4 py-2 bg-green-600/20 text-green-400 rounded-lg hover:bg-green-600/30 flex items-center gap-2" data-testid="stock-in-btn">
            <Plus className="h-5 w-5" /> Stok Masuk
          </button>
          <button onClick={() => setShowStockOutModal(true)} className="px-4 py-2 bg-red-600/20 text-red-400 rounded-lg hover:bg-red-600/30 flex items-center gap-2" data-testid="stock-out-btn">
            <Minus className="h-5 w-5" /> Stok Keluar
          </button>
          <button onClick={() => { setOpnameItems(stock.map(s => ({ product_id: s.product_id, actual_qty: s.quantity }))); setShowOpnameModal(true); }} className="px-4 py-2 border border-red-900/30 text-gray-300 rounded-lg hover:bg-red-900/20 flex items-center gap-2">
            <FileCheck className="h-5 w-5" /> Stok Opname
          </button>
          <button onClick={() => setShowTransferModal(true)} className="px-4 py-2 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg flex items-center gap-2">
            <Send className="h-5 w-5" /> Transfer Stok
          </button>
        </div>
      </div>

      <div className="flex gap-2 border-b border-red-900/30 pb-2">
        {tabs.map(tab => (
          <button key={tab.id} onClick={() => setActiveTab(tab.id)} className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-colors ${activeTab === tab.id ? 'bg-red-900/30 text-amber-400' : 'text-gray-400 hover:text-white hover:bg-red-900/20'}`}>
            <tab.icon className="h-4 w-4" /> {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Stok */}
      {activeTab === 'stock' && (
        <>
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input type="text" placeholder="Cari produk..." value={search} onChange={(e) => setSearch(e.target.value)} className="w-full pl-10 pr-4 py-2 bg-[#1a1214] border border-red-900/30 rounded-lg" />
          </div>
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
            <table className="w-full">
              <thead className="bg-red-900/20">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-semibold">Produk</th>
                  <th className="px-4 py-3 text-right text-sm font-semibold">Jumlah</th>
                  <th className="px-4 py-3 text-right text-sm font-semibold">Min Stok</th>
                  <th className="px-4 py-3 text-right text-sm font-semibold">Nilai Stok</th>
                  <th className="px-4 py-3 text-center text-sm font-semibold">Status</th>
                  <th className="px-4 py-3 text-center text-sm font-semibold">Aksi</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr><td colSpan={6} className="px-4 py-8 text-center"><Loader2 className="h-8 w-8 animate-spin mx-auto text-red-400" /></td></tr>
                ) : stock.length === 0 ? (
                  <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-400">Tidak ada data stok</td></tr>
                ) : (
                  stock.map((item, idx) => (
                    <tr key={idx} className="border-t border-red-900/10 hover:bg-red-900/10">
                      <td className="px-4 py-3">
                        <div className="font-medium">{item.product_name}</div>
                        <div className="text-sm text-gray-400">{item.product_code}</div>
                      </td>
                      <td className="px-4 py-3 text-right font-semibold">{item.quantity}</td>
                      <td className="px-4 py-3 text-right text-gray-400">{item.min_stock}</td>
                      <td className="px-4 py-3 text-right text-amber-400">{formatRupiah((item.cost_price || 0) * item.quantity)}</td>
                      <td className="px-4 py-3 text-center">
                        <span className={`px-2 py-1 rounded-full text-xs font-semibold ${item.is_low_stock ? 'bg-red-900/30 text-red-400' : 'bg-green-900/30 text-green-400'}`}>
                          {item.is_low_stock ? 'Menipis' : 'Aman'}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex justify-center">
                          <button onClick={() => openAdjustModal(item)} className="p-2 text-blue-400 hover:bg-blue-900/20 rounded" title="Sesuaikan Stok">
                            <RefreshCw className="h-4 w-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </>
      )}

      {/* Tab Stok Menipis */}
      {activeTab === 'low-stock' && (
        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
          <table className="w-full">
            <thead className="bg-red-900/20">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-semibold">Produk</th>
                <th className="px-4 py-3 text-left text-sm font-semibold">Cabang</th>
                <th className="px-4 py-3 text-right text-sm font-semibold">Sisa</th>
                <th className="px-4 py-3 text-right text-sm font-semibold">Minimum</th>
                <th className="px-4 py-3 text-right text-sm font-semibold">Kekurangan</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={5} className="px-4 py-8 text-center"><Loader2 className="h-8 w-8 animate-spin mx-auto text-red-400" /></td></tr>
              ) : lowStock.length === 0 ? (
                <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-400"><AlertTriangle className="h-12 w-12 mx-auto mb-2 opacity-30" />Semua stok dalam kondisi baik</td></tr>
              ) : (
                lowStock.map((item, idx) => (
                  <tr key={idx} className="border-t border-red-900/10 hover:bg-red-900/10">
                    <td className="px-4 py-3">
                      <div className="font-medium">{item.product_name}</div>
                      <div className="text-sm text-gray-400">{item.product_code}</div>
                    </td>
                    <td className="px-4 py-3 text-gray-400">{item.branch_name}</td>
                    <td className="px-4 py-3 text-right text-red-400 font-bold">{item.quantity}</td>
                    <td className="px-4 py-3 text-right text-gray-400">{item.min_stock}</td>
                    <td className="px-4 py-3 text-right text-amber-400 font-semibold">{item.shortage}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Tab Mutasi */}
      {activeTab === 'movements' && (
        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
          <table className="w-full">
            <thead className="bg-red-900/20">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-semibold">Tanggal</th>
                <th className="px-4 py-3 text-left text-sm font-semibold">Produk</th>
                <th className="px-4 py-3 text-left text-sm font-semibold">Jenis</th>
                <th className="px-4 py-3 text-right text-sm font-semibold">Jumlah</th>
                <th className="px-4 py-3 text-left text-sm font-semibold">Keterangan</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={5} className="px-4 py-8 text-center"><Loader2 className="h-8 w-8 animate-spin mx-auto text-red-400" /></td></tr>
              ) : movements.length === 0 ? (
                <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-400">Belum ada mutasi</td></tr>
              ) : (
                movements.map((item, idx) => (
                  <tr key={idx} className="border-t border-red-900/10 hover:bg-red-900/10">
                    <td className="px-4 py-3 text-gray-400">{new Date(item.created_at).toLocaleDateString('id-ID')}</td>
                    <td className="px-4 py-3">
                      <div className="font-medium">{item.product_name}</div>
                      <div className="text-sm text-gray-400">{item.product_code}</div>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded text-xs font-semibold ${
                        item.movement_type === 'sale' ? 'bg-blue-900/30 text-blue-400' :
                        item.movement_type === 'stock_in' ? 'bg-green-900/30 text-green-400' :
                        item.movement_type === 'adjustment' ? 'bg-amber-900/30 text-amber-400' :
                        'bg-purple-900/30 text-purple-400'
                      }`}>
                        {movementLabels[item.movement_type] || item.movement_type}
                      </span>
                    </td>
                    <td className={`px-4 py-3 text-right font-bold ${item.quantity > 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {item.quantity > 0 ? '+' : ''}{item.quantity}
                    </td>
                    <td className="px-4 py-3 text-gray-400 text-sm">{item.notes || '-'}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Tab Transfer */}
      {activeTab === 'transfers' && (
        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
          <table className="w-full">
            <thead className="bg-red-900/20">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-semibold">No Transfer</th>
                <th className="px-4 py-3 text-left text-sm font-semibold">Dari</th>
                <th className="px-4 py-3 text-left text-sm font-semibold">Ke</th>
                <th className="px-4 py-3 text-center text-sm font-semibold">Item</th>
                <th className="px-4 py-3 text-center text-sm font-semibold">Status</th>
                <th className="px-4 py-3 text-center text-sm font-semibold">Aksi</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={6} className="px-4 py-8 text-center"><Loader2 className="h-8 w-8 animate-spin mx-auto text-red-400" /></td></tr>
              ) : transfers.length === 0 ? (
                <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-400">Belum ada transfer</td></tr>
              ) : (
                transfers.map((item, idx) => (
                  <tr key={idx} className="border-t border-red-900/10 hover:bg-red-900/10">
                    <td className="px-4 py-3 font-medium">{item.transfer_number}</td>
                    <td className="px-4 py-3 text-gray-400">{item.from_branch_name}</td>
                    <td className="px-4 py-3 text-gray-400">{item.to_branch_name}</td>
                    <td className="px-4 py-3 text-center">{item.items?.length || 0}</td>
                    <td className="px-4 py-3 text-center">
                      <span className={`px-2 py-1 rounded text-xs font-semibold ${
                        item.status === 'received' ? 'bg-green-900/30 text-green-400' :
                        item.status === 'in_transit' ? 'bg-blue-900/30 text-blue-400' :
                        'bg-amber-900/30 text-amber-400'
                      }`}>
                        {transferStatusLabels[item.status] || item.status}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex justify-center gap-2">
                        {item.status === 'pending' && item.from_branch_id === user?.branch_id && (
                          <button onClick={() => handleSendTransfer(item.id)} className="px-2 py-1 text-xs bg-blue-600/20 text-blue-400 rounded hover:bg-blue-600/30">Kirim</button>
                        )}
                        {item.status === 'in_transit' && item.to_branch_id === user?.branch_id && (
                          <button onClick={() => handleReceiveTransfer(item.id)} className="px-2 py-1 text-xs bg-green-600/20 text-green-400 rounded hover:bg-green-600/30">Terima</button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Modal Penyesuaian */}
      {showAdjustModal && selectedProduct && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-md p-6">
            <h2 className="text-xl font-bold mb-4">Penyesuaian Stok</h2>
            <p className="text-gray-400 mb-4">{selectedProduct.product_name}</p>
            
            <div className="mb-4">
              <label className="block text-sm text-gray-400 mb-1">Stok Saat Ini</label>
              <div className="text-2xl font-bold">{selectedProduct.quantity}</div>
            </div>

            <div className="mb-4">
              <label className="block text-sm text-gray-400 mb-1">Penyesuaian (+/-)</label>
              <div className="flex items-center gap-2">
                <button onClick={() => setAdjustQty(adjustQty - 1)} className="p-2 bg-red-900/30 rounded hover:bg-red-900/50"><Minus className="h-5 w-5" /></button>
                <input type="number" value={adjustQty} onChange={(e) => setAdjustQty(Number(e.target.value))} className="flex-1 px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-center text-xl font-bold" />
                <button onClick={() => setAdjustQty(adjustQty + 1)} className="p-2 bg-green-900/30 rounded hover:bg-green-900/50"><Plus className="h-5 w-5" /></button>
              </div>
              <div className="text-center mt-2 text-gray-400">Stok Baru: <span className="font-bold text-amber-400">{selectedProduct.quantity + adjustQty}</span></div>
            </div>

            <div className="mb-6">
              <label className="block text-sm text-gray-400 mb-1">Alasan</label>
              <input type="text" value={adjustReason} onChange={(e) => setAdjustReason(e.target.value)} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" placeholder="Contoh: Barang rusak, Hitung ulang" />
            </div>

            <div className="flex gap-3">
              <button onClick={() => setShowAdjustModal(false)} className="flex-1 py-2 border border-red-900/30 rounded-lg hover:bg-red-900/20">Batal</button>
              <button onClick={handleAdjust} disabled={adjustQty === 0} className="flex-1 py-2 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg disabled:opacity-50">Konfirmasi</button>
            </div>
          </div>
        </div>
      )}

      {/* Modal Transfer */}
      {showTransferModal && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-lg p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">Transfer Stok</h2>
              <button onClick={() => setShowTransferModal(false)} className="text-gray-400 hover:text-white"><X className="h-6 w-6" /></button>
            </div>
            
            <div className="mb-4">
              <label className="block text-sm text-gray-400 mb-1">Cabang Tujuan</label>
              <select value={transferForm.to_branch_id} onChange={(e) => setTransferForm({ ...transferForm, to_branch_id: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg">
                <option value="">Pilih Cabang</option>
                {branches.filter(b => b.id !== user?.branch_id).map(b => <option key={b.id} value={b.id}>{b.name}</option>)}
              </select>
            </div>

            <div className="mb-4">
              <label className="block text-sm text-gray-400 mb-2">Pilih Produk</label>
              <div className="max-h-48 overflow-y-auto space-y-2">
                {stock.filter(s => s.quantity > 0).map(s => {
                  const existing = transferForm.items.find(i => i.product_id === s.product_id);
                  return (
                    <div key={s.product_id} className="flex items-center justify-between p-2 bg-[#0a0608] rounded">
                      <div>
                        <div className="text-sm font-medium">{s.product_name}</div>
                        <div className="text-xs text-gray-400">Stok: {s.quantity}</div>
                      </div>
                      {existing ? (
                        <div className="flex items-center gap-2">
                          <input type="number" min="1" max={s.quantity} value={existing.quantity} onChange={(e) => {
                            const qty = Math.min(s.quantity, Math.max(1, Number(e.target.value)));
                            setTransferForm({ ...transferForm, items: transferForm.items.map(i => i.product_id === s.product_id ? { ...i, quantity: qty } : i) });
                          }} className="w-16 px-2 py-1 bg-[#1a1214] border border-red-900/30 rounded text-center" />
                          <button onClick={() => setTransferForm({ ...transferForm, items: transferForm.items.filter(i => i.product_id !== s.product_id) })} className="text-red-400"><X className="h-4 w-4" /></button>
                        </div>
                      ) : (
                        <button onClick={() => setTransferForm({ ...transferForm, items: [...transferForm.items, { product_id: s.product_id, quantity: 1 }] })} className="px-2 py-1 text-xs bg-green-600/20 text-green-400 rounded">Tambah</button>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="flex gap-3">
              <button onClick={() => setShowTransferModal(false)} className="flex-1 py-2 border border-red-900/30 rounded-lg hover:bg-red-900/20">Batal</button>
              <button onClick={handleTransfer} disabled={!transferForm.to_branch_id || transferForm.items.length === 0} className="flex-1 py-2 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg disabled:opacity-50">Buat Transfer</button>
            </div>
          </div>
        </div>
      )}

      {/* Modal Opname */}
      {showOpnameModal && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">Stok Opname</h2>
              <button onClick={() => setShowOpnameModal(false)} className="text-gray-400 hover:text-white"><X className="h-6 w-6" /></button>
            </div>
            <p className="text-gray-400 mb-4">Masukkan jumlah fisik aktual untuk setiap produk</p>
            
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {opnameItems.map((item, idx) => {
                const stockItem = stock.find(s => s.product_id === item.product_id);
                const diff = item.actual_qty - (stockItem?.quantity || 0);
                return (
                  <div key={idx} className="flex items-center gap-4 p-3 bg-[#0a0608] rounded-lg">
                    <div className="flex-1">
                      <div className="font-medium">{stockItem?.product_name}</div>
                      <div className="text-sm text-gray-400">Sistem: {stockItem?.quantity || 0}</div>
                    </div>
                    <div className="flex items-center gap-2">
                      <input type="number" min="0" value={item.actual_qty} onChange={(e) => {
                        const newItems = [...opnameItems];
                        newItems[idx].actual_qty = Number(e.target.value);
                        setOpnameItems(newItems);
                      }} className="w-20 px-2 py-1 bg-[#1a1214] border border-red-900/30 rounded text-center" />
                      <span className={`text-sm font-semibold ${diff > 0 ? 'text-green-400' : diff < 0 ? 'text-red-400' : 'text-gray-400'}`}>
                        {diff > 0 ? '+' : ''}{diff}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="flex gap-3 mt-6">
              <button onClick={() => setShowOpnameModal(false)} className="flex-1 py-2 border border-red-900/30 rounded-lg hover:bg-red-900/20">Batal</button>
              <button onClick={handleOpname} className="flex-1 py-2 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg">Simpan Opname</button>
            </div>
          </div>
        </div>
      )}

      {/* Modal Stok Masuk */}
      {showStockInModal && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-md">
            <div className="p-6 border-b border-red-900/30 flex justify-between items-center">
              <h2 className="text-xl font-bold flex items-center gap-2"><Plus className="h-5 w-5 text-green-400" /> Stok Masuk</h2>
              <button onClick={() => setShowStockInModal(false)} className="text-gray-400 hover:text-white"><X className="h-6 w-6" /></button>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Produk *</label>
                <select value={stockInForm.product_id} onChange={(e) => setStockInForm({ ...stockInForm, product_id: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg">
                  <option value="">Pilih Produk</option>
                  {products.map(p => <option key={p.id} value={p.id}>{p.code} - {p.name}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Jumlah *</label>
                <input type="number" min="1" value={stockInForm.quantity} onChange={(e) => setStockInForm({ ...stockInForm, quantity: Number(e.target.value) })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-xl" />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Keterangan</label>
                <input type="text" value={stockInForm.notes} onChange={(e) => setStockInForm({ ...stockInForm, notes: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" placeholder="Stok masuk dari supplier..." />
              </div>
              <div className="flex gap-3 pt-4">
                <button onClick={() => setShowStockInModal(false)} className="flex-1 py-2 border border-red-900/30 rounded-lg hover:bg-red-900/20">Batal</button>
                <button onClick={handleStockIn} disabled={saving} className="flex-1 py-2 bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-lg disabled:opacity-50 flex items-center justify-center gap-2">
                  {saving ? <Loader2 className="h-5 w-5 animate-spin" /> : <Plus className="h-5 w-5" />}
                  {saving ? 'Menyimpan...' : 'Tambah Stok'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal Stok Keluar */}
      {showStockOutModal && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-md">
            <div className="p-6 border-b border-red-900/30 flex justify-between items-center">
              <h2 className="text-xl font-bold flex items-center gap-2"><Minus className="h-5 w-5 text-red-400" /> Stok Keluar</h2>
              <button onClick={() => setShowStockOutModal(false)} className="text-gray-400 hover:text-white"><X className="h-6 w-6" /></button>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Produk *</label>
                <select value={stockOutForm.product_id} onChange={(e) => setStockOutForm({ ...stockOutForm, product_id: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg">
                  <option value="">Pilih Produk</option>
                  {stock.filter(s => s.quantity > 0).map(s => <option key={s.product_id} value={s.product_id}>{s.product_code} - {s.product_name} (Stok: {s.quantity})</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Jumlah *</label>
                <input type="number" min="1" value={stockOutForm.quantity} onChange={(e) => setStockOutForm({ ...stockOutForm, quantity: Number(e.target.value) })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-xl" />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Keterangan</label>
                <input type="text" value={stockOutForm.notes} onChange={(e) => setStockOutForm({ ...stockOutForm, notes: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" placeholder="Rusak, hilang, sample..." />
              </div>
              <div className="flex gap-3 pt-4">
                <button onClick={() => setShowStockOutModal(false)} className="flex-1 py-2 border border-red-900/30 rounded-lg hover:bg-red-900/20">Batal</button>
                <button onClick={handleStockOut} disabled={saving} className="flex-1 py-2 bg-gradient-to-r from-red-600 to-rose-600 text-white rounded-lg disabled:opacity-50 flex items-center justify-center gap-2">
                  {saving ? <Loader2 className="h-5 w-5 animate-spin" /> : <Minus className="h-5 w-5" />}
                  {saving ? 'Menyimpan...' : 'Kurangi Stok'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Inventory;
