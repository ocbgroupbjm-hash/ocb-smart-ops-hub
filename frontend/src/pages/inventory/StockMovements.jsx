import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Plus, Search, Loader2, ArrowUpRight, ArrowDownLeft, X, Package } from 'lucide-react';
import { toast } from 'sonner';

const StockMovements = () => {
  const { api } = useAuth();
  const [movements, setMovements] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [products, setProducts] = useState([]);
  const [branches, setBranches] = useState([]);
  const [formData, setFormData] = useState({
    product_id: '', branch_id: '', movement_type: 'stock_in', quantity: 0, notes: ''
  });

  const loadMovements = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        ...(searchTerm && { search: searchTerm }),
        ...(typeFilter && { movement_type: typeFilter })
      });
      const res = await api(`/api/inventory/movements?${params}`);
      if (res.ok) {
        const data = await res.json();
        setMovements(data.items || data || []);
      }
    } catch (err) {
      toast.error('Gagal memuat data');
    } finally {
      setLoading(false);
    }
  }, [api, searchTerm, typeFilter]);

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
    loadMovements();
    loadMasterData();
  }, [loadMovements, loadMasterData]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const res = await api('/api/inventory/adjust', {
        method: 'POST',
        body: JSON.stringify(formData)
      });
      if (res.ok) {
        toast.success('Stok berhasil diupdate');
        setShowModal(false);
        resetForm();
        loadMovements();
      }
    } catch (err) {
      toast.error('Gagal menyimpan');
    }
  };

  const resetForm = () => {
    setFormData({ product_id: '', branch_id: '', movement_type: 'stock_in', quantity: 0, notes: '' });
  };

  return (
    <div className="space-y-4" data-testid="stock-movements-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Stok Masuk/Keluar</h1>
          <p className="text-gray-400 text-sm">Catat pergerakan stok manual</p>
        </div>
        <button onClick={() => { resetForm(); setShowModal(true); }}
          className="px-4 py-2 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg flex items-center gap-2">
          <Plus className="h-4 w-4" /> Tambah Movement
        </button>
      </div>

      {/* Filters */}
      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Cari produk..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200"
            />
          </div>
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="px-4 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200"
          >
            <option value="">Semua Tipe</option>
            <option value="stock_in">Stok Masuk</option>
            <option value="stock_out">Stok Keluar</option>
            <option value="adjustment">Penyesuaian</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-red-900/20">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">TANGGAL</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">PRODUK</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">CABANG</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">TIPE</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">QTY</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">CATATAN</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-red-900/20">
              {loading ? (
                <tr><td colSpan={6} className="px-4 py-8 text-center"><Loader2 className="h-8 w-8 animate-spin mx-auto text-amber-400" /></td></tr>
              ) : movements.length === 0 ? (
                <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-400">Belum ada data movement</td></tr>
              ) : movements.map((m, idx) => (
                <tr key={idx} className="hover:bg-red-900/10">
                  <td className="px-4 py-3 text-sm text-gray-400">
                    {new Date(m.created_at).toLocaleDateString('id-ID')}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <Package className="h-4 w-4 text-gray-500" />
                      <span className="font-medium text-gray-200">{m.product_name}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-400">{m.branch_name || '-'}</td>
                  <td className="px-4 py-3 text-center">
                    <span className={`flex items-center justify-center gap-1 text-sm ${
                      m.movement_type === 'stock_in' ? 'text-green-400' : 'text-red-400'
                    }`}>
                      {m.movement_type === 'stock_in' ? <ArrowDownLeft className="h-4 w-4" /> : <ArrowUpRight className="h-4 w-4" />}
                      {m.movement_type === 'stock_in' ? 'Masuk' : m.movement_type === 'stock_out' ? 'Keluar' : 'Adjust'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center font-medium text-gray-200">{m.quantity}</td>
                  <td className="px-4 py-3 text-sm text-gray-400">{m.notes || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Create Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-md">
            <div className="p-4 border-b border-red-900/30 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-amber-100">Stok Masuk/Keluar</h2>
              <button onClick={() => setShowModal(false)} className="p-1 hover:bg-red-900/20 rounded"><X className="h-5 w-5" /></button>
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
              <div>
                <label className="block text-sm text-gray-400 mb-1">Cabang</label>
                <select value={formData.branch_id} onChange={(e) => setFormData({ ...formData, branch_id: e.target.value })}
                  className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg">
                  <option value="">Pilih cabang</option>
                  {branches.map(b => (
                    <option key={b.id} value={b.id}>{b.name}</option>
                  ))}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Tipe *</label>
                  <select value={formData.movement_type} onChange={(e) => setFormData({ ...formData, movement_type: e.target.value })}
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg">
                    <option value="stock_in">Stok Masuk</option>
                    <option value="stock_out">Stok Keluar</option>
                    <option value="adjustment">Penyesuaian</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Jumlah *</label>
                  <input type="number" min="1" value={formData.quantity}
                    onChange={(e) => setFormData({ ...formData, quantity: Number(e.target.value) })}
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" required />
                </div>
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Catatan</label>
                <textarea value={formData.notes} onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" rows={2}
                  placeholder="Alasan adjustment, referensi, dll" />
              </div>
              <div className="flex justify-end gap-3 pt-4 border-t border-red-900/30">
                <button type="button" onClick={() => setShowModal(false)} className="px-4 py-2 border border-red-900/30 rounded-lg">Batal</button>
                <button type="submit" className="px-4 py-2 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg">Simpan</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default StockMovements;
