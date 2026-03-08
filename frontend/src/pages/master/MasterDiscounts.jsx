import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Plus, Search, Edit2, Trash2, Loader2, X, Percent, Calendar } from 'lucide-react';
import { toast } from 'sonner';

const MasterDiscounts = () => {
  const { api } = useAuth();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [formData, setFormData] = useState({ 
    code: '', name: '', discount_type: 'percent', discount_value: 0, min_purchase: 0,
    start_date: '', end_date: '', is_active: true
  });

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api(`/api/master/discounts?search=${searchTerm}`);
      if (res.ok) setItems(await res.json());
    } catch (err) { toast.error('Gagal memuat data'); }
    finally { setLoading(false); }
  }, [api, searchTerm]);

  useEffect(() => { loadData(); }, [loadData]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const url = editingItem ? `/api/master/discounts/${editingItem.id}` : '/api/master/discounts';
      const res = await api(url, { method: editingItem ? 'PUT' : 'POST', body: JSON.stringify(formData) });
      if (res.ok) { 
        toast.success(editingItem ? 'Berhasil diupdate' : 'Berhasil ditambahkan'); 
        setShowModal(false); 
        resetForm();
        loadData(); 
      }
    } catch (err) { toast.error('Gagal menyimpan'); }
  };

  const handleEdit = (item) => { 
    setEditingItem(item); 
    setFormData({ 
      code: item.code || '', 
      name: item.name || '', 
      discount_type: item.discount_type || 'percent',
      discount_value: item.discount_value || 0,
      min_purchase: item.min_purchase || 0,
      start_date: item.start_date || '',
      end_date: item.end_date || '',
      is_active: item.is_active !== false
    }); 
    setShowModal(true); 
  };

  const handleDelete = async (item) => { 
    if (!confirm(`Hapus diskon "${item.name}"?`)) return; 
    try { 
      await api(`/api/master/discounts/${item.id}`, { method: 'DELETE' }); 
      toast.success('Berhasil dihapus'); 
      loadData(); 
    } catch { toast.error('Gagal menghapus'); } 
  };

  const resetForm = () => {
    setEditingItem(null);
    setFormData({ code: '', name: '', discount_type: 'percent', discount_value: 0, min_purchase: 0,
      start_date: '', end_date: '', is_active: true });
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('id-ID');
  };

  return (
    <div className="space-y-4" data-testid="discounts-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Diskon Periode</h1>
          <p className="text-gray-400 text-sm">Kelola diskon berdasarkan periode waktu</p>
        </div>
        <button onClick={() => { resetForm(); setShowModal(true); }} 
          className="px-4 py-2 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg flex items-center gap-2">
          <Plus className="h-4 w-4" /> Tambah Diskon
        </button>
      </div>

      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input type="text" placeholder="Cari diskon..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} 
            className="w-full pl-10 pr-4 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200" />
        </div>
      </div>

      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-red-900/20">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">KODE</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">NAMA DISKON</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">NILAI</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-amber-200">MIN. BELANJA</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">PERIODE</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">STATUS</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">AKSI</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-red-900/20">
              {loading ? (
                <tr><td colSpan={7} className="px-4 py-8 text-center"><Loader2 className="h-8 w-8 animate-spin mx-auto text-amber-400" /></td></tr>
              ) : items.length === 0 ? (
                <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-400">Belum ada data diskon</td></tr>
              ) : items.map(item => (
                <tr key={item.id} className="hover:bg-red-900/10">
                  <td className="px-4 py-3 text-sm font-mono text-amber-300">{item.code}</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <Percent className="h-4 w-4 text-green-500" />
                      <span className="font-medium text-gray-200">{item.name}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className="px-2 py-1 bg-green-600/20 text-green-400 rounded text-sm font-medium">
                      {item.discount_type === 'percent' 
                        ? `${item.discount_value}%` 
                        : `Rp ${(item.discount_value || 0).toLocaleString('id-ID')}`}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-right text-gray-300">
                    {item.min_purchase ? `Rp ${item.min_purchase.toLocaleString('id-ID')}` : '-'}
                  </td>
                  <td className="px-4 py-3 text-center text-xs text-gray-400">
                    {formatDate(item.start_date)} - {formatDate(item.end_date)}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className={`px-2 py-1 rounded-full text-xs ${
                      item.is_active !== false ? 'bg-green-600/20 text-green-400' : 'bg-red-600/20 text-red-400'
                    }`}>
                      {item.is_active !== false ? 'Aktif' : 'Nonaktif'}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-center gap-1">
                      <button onClick={() => handleEdit(item)} className="p-1.5 hover:bg-blue-600/20 rounded text-blue-400">
                        <Edit2 className="h-4 w-4" />
                      </button>
                      <button onClick={() => handleDelete(item)} className="p-1.5 hover:bg-red-600/20 rounded text-red-400">
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

      {showModal && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-lg">
            <div className="p-4 border-b border-red-900/30 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-amber-100">{editingItem ? 'Edit' : 'Tambah'} Diskon</h2>
              <button onClick={() => setShowModal(false)} className="p-1 hover:bg-red-900/20 rounded"><X className="h-5 w-5" /></button>
            </div>
            <form onSubmit={handleSubmit} className="p-4 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Kode *</label>
                  <input type="text" value={formData.code} onChange={(e) => setFormData({ ...formData, code: e.target.value })} 
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" required />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Nama Diskon *</label>
                  <input type="text" value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} 
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" required />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Jenis Diskon</label>
                  <select value={formData.discount_type} onChange={(e) => setFormData({ ...formData, discount_type: e.target.value })}
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg">
                    <option value="percent">Persentase (%)</option>
                    <option value="amount">Nominal (Rp)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Nilai Diskon</label>
                  <input type="number" min="0" value={formData.discount_value} 
                    onChange={(e) => setFormData({ ...formData, discount_value: Number(e.target.value) })} 
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" />
                </div>
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Minimum Belanja (Rp)</label>
                <input type="number" min="0" value={formData.min_purchase} 
                  onChange={(e) => setFormData({ ...formData, min_purchase: Number(e.target.value) })} 
                  className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Tanggal Mulai</label>
                  <input type="date" value={formData.start_date} 
                    onChange={(e) => setFormData({ ...formData, start_date: e.target.value })} 
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Tanggal Selesai</label>
                  <input type="date" value={formData.end_date} 
                    onChange={(e) => setFormData({ ...formData, end_date: e.target.value })} 
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" />
                </div>
              </div>
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" checked={formData.is_active} onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })} className="w-4 h-4" />
                <span className="text-sm text-gray-300">Aktif</span>
              </label>
              <div className="flex justify-end gap-3 pt-4 border-t border-red-900/30">
                <button type="button" onClick={() => setShowModal(false)} className="px-4 py-2 border border-red-900/30 rounded-lg">Batal</button>
                <button type="submit" className="px-4 py-2 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg">
                  {editingItem ? 'Update' : 'Simpan'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default MasterDiscounts;
