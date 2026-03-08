import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Plus, Search, Edit2, Trash2, Loader2, X, Building } from 'lucide-react';
import { toast } from 'sonner';

const MasterWarehouses = () => {
  const { api } = useAuth();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [branches, setBranches] = useState([]);
  const [formData, setFormData] = useState({ code: '', name: '', branch_id: '', address: '', is_active: true });

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [res, branchRes] = await Promise.all([
        api(`/api/master/warehouses?search=${searchTerm}`),
        api('/api/branches')
      ]);
      if (res.ok) setItems(await res.json());
      if (branchRes.ok) setBranches(await branchRes.json());
    } catch (err) { toast.error('Gagal memuat data'); }
    finally { setLoading(false); }
  }, [api, searchTerm]);

  useEffect(() => { loadData(); }, [loadData]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const url = editingItem ? `/api/master/warehouses/${editingItem.id}` : '/api/master/warehouses';
      const res = await api(url, { method: editingItem ? 'PUT' : 'POST', body: JSON.stringify(formData) });
      if (res.ok) { toast.success('Berhasil disimpan'); setShowModal(false); loadData(); }
    } catch (err) { toast.error('Gagal menyimpan'); }
  };

  const handleEdit = (item) => { 
    setEditingItem(item); 
    setFormData({ code: item.code, name: item.name, branch_id: item.branch_id || '', address: item.address || '', is_active: item.is_active }); 
    setShowModal(true); 
  };
  
  const handleDelete = async (item) => { 
    if (!confirm(`Hapus "${item.name}"?`)) return; 
    try { await api(`/api/master/warehouses/${item.id}`, { method: 'DELETE' }); toast.success('Berhasil dihapus'); loadData(); } 
    catch { toast.error('Gagal menghapus'); } 
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Dept / Gudang</h1>
          <p className="text-gray-400 text-sm">Kelola departemen dan gudang</p>
        </div>
        <button onClick={() => { setEditingItem(null); setFormData({ code: '', name: '', branch_id: '', address: '', is_active: true }); setShowModal(true); }} 
          className="px-4 py-2 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg flex items-center gap-2">
          <Plus className="h-4 w-4" /> Tambah
        </button>
      </div>

      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input type="text" placeholder="Cari gudang..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} 
            className="w-full pl-10 pr-4 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200" />
        </div>
      </div>

      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
        <table className="w-full">
          <thead className="bg-red-900/20">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">KODE</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">NAMA</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">CABANG</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">ALAMAT</th>
              <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">STATUS</th>
              <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">AKSI</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-red-900/20">
            {loading ? (
              <tr><td colSpan={6} className="px-4 py-8 text-center"><Loader2 className="h-8 w-8 animate-spin mx-auto text-amber-400" /></td></tr>
            ) : items.length === 0 ? (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-400">Belum ada data</td></tr>
            ) : items.map(item => (
              <tr key={item.id} className="hover:bg-red-900/10">
                <td className="px-4 py-3 text-sm font-mono text-amber-300">{item.code}</td>
                <td className="px-4 py-3 font-medium text-gray-200">
                  <div className="flex items-center gap-2">
                    <Building className="h-4 w-4 text-gray-500" />
                    {item.name}
                  </div>
                </td>
                <td className="px-4 py-3 text-sm text-gray-400">{item.branch_name || '-'}</td>
                <td className="px-4 py-3 text-sm text-gray-400">{item.address || '-'}</td>
                <td className="px-4 py-3 text-center">
                  <span className={`px-2 py-1 rounded-full text-xs ${item.is_active ? 'bg-green-600/20 text-green-400' : 'bg-red-600/20 text-red-400'}`}>
                    {item.is_active ? 'Aktif' : 'Nonaktif'}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center justify-center gap-1">
                    <button onClick={() => handleEdit(item)} className="p-1.5 hover:bg-blue-600/20 rounded text-blue-400"><Edit2 className="h-4 w-4" /></button>
                    <button onClick={() => handleDelete(item)} className="p-1.5 hover:bg-red-600/20 rounded text-red-400"><Trash2 className="h-4 w-4" /></button>
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
              <h2 className="text-lg font-semibold text-amber-100">{editingItem ? 'Edit' : 'Tambah'} Gudang</h2>
              <button onClick={() => setShowModal(false)} className="p-1 hover:bg-red-900/20 rounded"><X className="h-5 w-5" /></button>
            </div>
            <form onSubmit={handleSubmit} className="p-4 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Kode</label>
                  <input type="text" value={formData.code} onChange={(e) => setFormData({ ...formData, code: e.target.value })} 
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" required />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Cabang</label>
                  <select value={formData.branch_id} onChange={(e) => setFormData({ ...formData, branch_id: e.target.value })} 
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg">
                    <option value="">Pilih Cabang</option>
                    {branches.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Nama</label>
                <input type="text" value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} 
                  className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" required />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Alamat</label>
                <textarea value={formData.address} onChange={(e) => setFormData({ ...formData, address: e.target.value })} 
                  className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" rows={2} />
              </div>
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" checked={formData.is_active} onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })} className="w-4 h-4" />
                <span className="text-sm text-gray-300">Aktif</span>
              </label>
              <div className="flex justify-end gap-3 pt-4">
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

export default MasterWarehouses;
