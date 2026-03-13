import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Plus, Search, Loader2, ArrowRight, ArrowLeft, X, Package, Building2, Edit2, Trash2, Printer } from 'lucide-react';
import { toast } from 'sonner';
import ERPActionToolbar from '../../components/ERPActionToolbar';

const StockTransfers = () => {
  const { api } = useAuth();
  const [transfers, setTransfers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingTransfer, setEditingTransfer] = useState(null);
  const [selectedItem, setSelectedItem] = useState(null);
  const [products, setProducts] = useState([]);
  const [branches, setBranches] = useState([]);
  const [formData, setFormData] = useState({
    product_id: '', from_branch_id: '', to_branch_id: '', quantity: 0, notes: ''
  });

  const loadTransfers = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api(`/api/inventory/transfers?search=${searchTerm}`);
      if (res.ok) {
        const data = await res.json();
        setTransfers(data.items || data || []);
      }
    } catch (err) {
      toast.error('Gagal memuat data');
    } finally {
      setLoading(false);
    }
  }, [api, searchTerm]);

  const loadMasterData = useCallback(async () => {
    try {
      const [prodRes, branchRes] = await Promise.all([
        api('/api/products'),
        api('/api/branches')
      ]);
      if (prodRes.ok) {
        const data = await prodRes.json();
        setProducts(data.items || data || []);
      }
      if (branchRes.ok) {
        const data = await branchRes.json();
        setBranches(data.items || data || []);
      }
    } catch (err) { console.error('Error loading master data'); }
  }, [api]);

  useEffect(() => {
    loadTransfers();
    loadMasterData();
  }, [loadTransfers, loadMasterData]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (formData.from_branch_id === formData.to_branch_id) {
      toast.error('Cabang asal dan tujuan tidak boleh sama');
      return;
    }
    try {
      const url = editingTransfer 
        ? `/api/inventory/transfers/${editingTransfer.id}` 
        : '/api/inventory/transfers';
      const res = await api(url, {
        method: editingTransfer ? 'PUT' : 'POST',
        body: JSON.stringify(formData)
      });
      if (res.ok) {
        toast.success(editingTransfer ? 'Transfer berhasil diupdate' : 'Transfer stok berhasil');
        setShowModal(false);
        resetForm();
        loadTransfers();
      }
    } catch (err) {
      toast.error('Gagal menyimpan');
    }
  };

  const handleEdit = (transfer) => {
    if (transfer.status !== 'pending') {
      toast.warning('Hanya transfer dengan status Pending yang bisa diedit');
      return;
    }
    setEditingTransfer(transfer);
    setFormData({
      product_id: transfer.product_id || '',
      from_branch_id: transfer.from_branch_id || '',
      to_branch_id: transfer.to_branch_id || '',
      quantity: transfer.quantity || 0,
      notes: transfer.notes || ''
    });
    setShowModal(true);
  };

  const handleDelete = async (transfer) => {
    if (transfer.status !== 'pending') {
      toast.error('Hanya transfer dengan status Pending yang bisa dihapus');
      return;
    }
    if (!confirm(`Hapus transfer ${transfer.transfer_number}?`)) return;
    try {
      const res = await api(`/api/inventory/transfers/${transfer.id}`, { method: 'DELETE' });
      if (res.ok) {
        toast.success('Transfer berhasil dihapus');
        setSelectedItem(null);
        loadTransfers();
      }
    } catch (err) {
      toast.error('Gagal menghapus transfer');
    }
  };

  const handlePrint = (transfer) => {
    toast.info(`Mencetak transfer ${transfer.transfer_number}...`);
    window.print();
  };

  const resetForm = () => {
    setEditingTransfer(null);
    setFormData({ product_id: '', from_branch_id: '', to_branch_id: '', quantity: 0, notes: '' });
  };

  const handleRowSelect = (transfer) => {
    if (selectedItem?.id === transfer.id) {
      setSelectedItem(null);
    } else {
      setSelectedItem(transfer);
    }
  };

  const getStatusBadge = (status) => {
    const badges = {
      pending: 'bg-yellow-600/20 text-yellow-400',
      completed: 'bg-green-600/20 text-green-400',
      cancelled: 'bg-red-600/20 text-red-400'
    };
    const labels = { pending: 'Pending', completed: 'Selesai', cancelled: 'Dibatalkan' };
    return <span className={`px-2 py-1 rounded-full text-xs ${badges[status] || badges.pending}`}>{labels[status] || status}</span>;
  };

  return (
    <div className="space-y-4" data-testid="stock-transfers-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Transfer Stok</h1>
          <p className="text-gray-400 text-sm">Pindahkan stok antar cabang/gudang</p>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Cari transfer..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200"
          />
        </div>
      </div>

      {/* TOOLBAR STANDAR ERP */}
      <ERPActionToolbar
        module="stock_transfer"
        selectedItem={selectedItem}
        onAdd={() => { resetForm(); setShowModal(true); }}
        onEdit={(item) => handleEdit(item)}
        onDelete={(item) => handleDelete(item)}
        onPrint={(item) => handlePrint(item)}
        addLabel="Tambah"
        editLabel="Edit"
        deleteLabel="Hapus"
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
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">NO. TRANSFER</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">TANGGAL</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">PRODUK</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">DARI</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">KE</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">QTY</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">STATUS</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">AKSI</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-red-900/20">
              {loading ? (
                <tr><td colSpan={9} className="px-4 py-8 text-center"><Loader2 className="h-8 w-8 animate-spin mx-auto text-amber-400" /></td></tr>
              ) : transfers.length === 0 ? (
                <tr><td colSpan={9} className="px-4 py-8 text-center text-gray-400">Belum ada data transfer</td></tr>
              ) : transfers.map((t, idx) => (
                <tr 
                  key={t.id} 
                  onClick={() => handleRowSelect(t)}
                  className={`cursor-pointer transition-colors ${
                    selectedItem?.id === t.id 
                      ? 'bg-amber-900/30 border-l-2 border-amber-500' 
                      : 'hover:bg-red-900/10'
                  }`}
                  data-testid={`transfer-row-${idx}`}
                >
                  <td className="px-3 py-3 text-center">
                    <input 
                      type="radio" 
                      checked={selectedItem?.id === t.id}
                      onChange={() => handleRowSelect(t)}
                      className="w-3 h-3 accent-amber-500"
                    />
                  </td>
                  <td className="px-4 py-3 text-sm font-mono text-amber-300">{t.transfer_number || '-'}</td>
                  <td className="px-4 py-3 text-sm text-gray-400">
                    {new Date(t.created_at).toLocaleDateString('id-ID')}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <Package className="h-4 w-4 text-gray-500" />
                      <span className="font-medium text-gray-200">{t.product_name}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-400">
                    <div className="flex items-center gap-1">
                      <Building2 className="h-3 w-3" />
                      {t.from_branch_name}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-400">
                    <div className="flex items-center gap-1">
                      <Building2 className="h-3 w-3" />
                      {t.to_branch_name}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-center font-medium text-gray-200">{t.quantity}</td>
                  <td className="px-4 py-3 text-center">{getStatusBadge(t.status)}</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-center gap-1">
                      <button onClick={(e) => { e.stopPropagation(); handleEdit(t); }} className="p-1.5 hover:bg-purple-600/20 rounded text-purple-400" title="Edit">
                        <Edit2 className="h-4 w-4" />
                      </button>
                      <button onClick={(e) => { e.stopPropagation(); handlePrint(t); }} className="p-1.5 hover:bg-blue-600/20 rounded text-blue-400" title="Print">
                        <Printer className="h-4 w-4" />
                      </button>
                      <button onClick={(e) => { e.stopPropagation(); handleDelete(t); }} className="p-1.5 hover:bg-red-600/20 rounded text-red-400" title="Hapus">
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Create/Edit Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-md">
            <div className="p-4 border-b border-red-900/30 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-amber-100">
                {editingTransfer ? 'Edit' : 'Buat'} Transfer Stok
              </h2>
              <button onClick={() => { setShowModal(false); resetForm(); }} className="p-1 hover:bg-red-900/20 rounded">
                <X className="h-5 w-5" />
              </button>
            </div>
            <form onSubmit={handleSubmit} className="p-4 space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Produk *</label>
                <select value={formData.product_id} onChange={(e) => setFormData({ ...formData, product_id: e.target.value })}
                  className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" required>
                  <option value="">Pilih produk</option>
                  {products.map(p => (
                    <option key={p.id} value={p.id}>{p.name}</option>
                  ))}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Dari Cabang *</label>
                  <select value={formData.from_branch_id} onChange={(e) => setFormData({ ...formData, from_branch_id: e.target.value })}
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" required>
                    <option value="">Pilih</option>
                    {branches.map(b => (
                      <option key={b.id} value={b.id}>{b.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Ke Cabang *</label>
                  <select value={formData.to_branch_id} onChange={(e) => setFormData({ ...formData, to_branch_id: e.target.value })}
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" required>
                    <option value="">Pilih</option>
                    {branches.map(b => (
                      <option key={b.id} value={b.id}>{b.name}</option>
                    ))}
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Jumlah *</label>
                <input type="number" min="1" value={formData.quantity}
                  onChange={(e) => setFormData({ ...formData, quantity: Number(e.target.value) })}
                  className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" required />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Catatan</label>
                <textarea value={formData.notes} onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" rows={2} />
              </div>
              <div className="flex justify-end gap-3 pt-4 border-t border-red-900/30">
                <button type="button" onClick={() => { setShowModal(false); resetForm(); }} className="px-4 py-2 border border-red-900/30 rounded-lg">Batal</button>
                <button type="submit" className="px-4 py-2 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg">
                  {editingTransfer ? 'Update' : 'Simpan'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default StockTransfers;
