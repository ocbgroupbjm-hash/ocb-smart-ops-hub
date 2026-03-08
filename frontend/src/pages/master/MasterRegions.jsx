import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Plus, Search, Edit2, Trash2, Loader2, X, MapPin } from 'lucide-react';
import { toast } from 'sonner';

const MasterRegions = () => {
  const { api } = useAuth();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [formData, setFormData] = useState({ 
    code: '', name: '', parent_id: '', type: 'province' 
  });

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api(`/api/master/regions?search=${searchTerm}`);
      if (res.ok) setItems(await res.json());
    } catch (err) { toast.error('Gagal memuat data'); }
    finally { setLoading(false); }
  }, [api, searchTerm]);

  useEffect(() => { loadData(); }, [loadData]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const url = editingItem ? `/api/master/regions/${editingItem.id}` : '/api/master/regions';
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
      parent_id: item.parent_id || '',
      type: item.type || 'province'
    }); 
    setShowModal(true); 
  };

  const handleDelete = async (item) => { 
    if (!confirm(`Hapus wilayah "${item.name}"?`)) return; 
    try { 
      await api(`/api/master/regions/${item.id}`, { method: 'DELETE' }); 
      toast.success('Berhasil dihapus'); 
      loadData(); 
    } catch { toast.error('Gagal menghapus'); } 
  };

  const resetForm = () => {
    setEditingItem(null);
    setFormData({ code: '', name: '', parent_id: '', type: 'province' });
  };

  const typeLabels = {
    province: 'Provinsi',
    city: 'Kota/Kabupaten',
    district: 'Kecamatan',
    village: 'Kelurahan/Desa'
  };

  return (
    <div className="space-y-4" data-testid="regions-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Wilayah</h1>
          <p className="text-gray-400 text-sm">Kelola data wilayah pengiriman</p>
        </div>
        <button onClick={() => { resetForm(); setShowModal(true); }} 
          className="px-4 py-2 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg flex items-center gap-2">
          <Plus className="h-4 w-4" /> Tambah Wilayah
        </button>
      </div>

      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input type="text" placeholder="Cari wilayah..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} 
            className="w-full pl-10 pr-4 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200" />
        </div>
      </div>

      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
        <table className="w-full">
          <thead className="bg-red-900/20">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">KODE</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">NAMA WILAYAH</th>
              <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">JENIS</th>
              <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">AKSI</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-red-900/20">
            {loading ? (
              <tr><td colSpan={4} className="px-4 py-8 text-center"><Loader2 className="h-8 w-8 animate-spin mx-auto text-amber-400" /></td></tr>
            ) : items.length === 0 ? (
              <tr><td colSpan={4} className="px-4 py-8 text-center text-gray-400">Belum ada data wilayah</td></tr>
            ) : items.map(item => (
              <tr key={item.id} className="hover:bg-red-900/10">
                <td className="px-4 py-3 text-sm font-mono text-amber-300">{item.code}</td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <MapPin className="h-4 w-4 text-gray-500" />
                    <span className="font-medium text-gray-200">{item.name}</span>
                  </div>
                </td>
                <td className="px-4 py-3 text-center">
                  <span className="px-2 py-1 bg-blue-600/20 text-blue-400 rounded text-xs">
                    {typeLabels[item.type] || item.type}
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

      {showModal && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-md">
            <div className="p-4 border-b border-red-900/30 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-amber-100">{editingItem ? 'Edit' : 'Tambah'} Wilayah</h2>
              <button onClick={() => setShowModal(false)} className="p-1 hover:bg-red-900/20 rounded"><X className="h-5 w-5" /></button>
            </div>
            <form onSubmit={handleSubmit} className="p-4 space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Kode *</label>
                <input type="text" value={formData.code} onChange={(e) => setFormData({ ...formData, code: e.target.value })} 
                  className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" required />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Nama Wilayah *</label>
                <input type="text" value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} 
                  className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" required />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Jenis Wilayah</label>
                <select value={formData.type} onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                  className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg">
                  <option value="province">Provinsi</option>
                  <option value="city">Kota/Kabupaten</option>
                  <option value="district">Kecamatan</option>
                  <option value="village">Kelurahan/Desa</option>
                </select>
              </div>
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

export default MasterRegions;
