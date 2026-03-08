import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Plus, Search, Edit2, Trash2, Loader2, X } from 'lucide-react';
import { toast } from 'sonner';

const MasterUnits = () => {
  const { api } = useAuth();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [formData, setFormData] = useState({ code: '', name: '', description: '' });

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api(`/api/master/units?search=${searchTerm}`);
      if (res.ok) setItems(await res.json());
    } catch (err) { toast.error('Gagal memuat data'); }
    finally { setLoading(false); }
  }, [api, searchTerm]);

  useEffect(() => { loadData(); }, [loadData]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const url = editingItem ? `/api/master/units/${editingItem.id}` : '/api/master/units';
      const res = await api(url, { method: editingItem ? 'PUT' : 'POST', body: JSON.stringify(formData) });
      if (res.ok) { toast.success('Berhasil disimpan'); setShowModal(false); loadData(); }
    } catch (err) { toast.error('Gagal menyimpan'); }
  };

  const handleEdit = (item) => { setEditingItem(item); setFormData({ code: item.code, name: item.name, description: item.description || '' }); setShowModal(true); };
  const handleDelete = async (item) => { if (!confirm(`Hapus "${item.name}"?`)) return; try { await api(`/api/master/units/${item.id}`, { method: 'DELETE' }); toast.success('Berhasil dihapus'); loadData(); } catch { toast.error('Gagal menghapus'); } };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div><h1 className="text-2xl font-bold text-amber-100">Satuan</h1><p className="text-gray-400 text-sm">Kelola satuan produk</p></div>
        <button onClick={() => { setEditingItem(null); setFormData({ code: '', name: '', description: '' }); setShowModal(true); }} className="px-4 py-2 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg flex items-center gap-2"><Plus className="h-4 w-4" /> Tambah</button>
      </div>
      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4"><div className="relative max-w-md"><Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" /><input type="text" placeholder="Cari satuan..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} className="w-full pl-10 pr-4 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200" /></div></div>
      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
        <table className="w-full"><thead className="bg-red-900/20"><tr><th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">KODE</th><th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">NAMA</th><th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">DESKRIPSI</th><th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">AKSI</th></tr></thead>
          <tbody className="divide-y divide-red-900/20">{loading ? (<tr><td colSpan={4} className="px-4 py-8 text-center"><Loader2 className="h-8 w-8 animate-spin mx-auto text-amber-400" /></td></tr>) : items.length === 0 ? (<tr><td colSpan={4} className="px-4 py-8 text-center text-gray-400">Belum ada data</td></tr>) : items.map(item => (<tr key={item.id} className="hover:bg-red-900/10"><td className="px-4 py-3 text-sm font-mono text-amber-300">{item.code}</td><td className="px-4 py-3 font-medium text-gray-200">{item.name}</td><td className="px-4 py-3 text-sm text-gray-400">{item.description || '-'}</td><td className="px-4 py-3"><div className="flex items-center justify-center gap-1"><button onClick={() => handleEdit(item)} className="p-1.5 hover:bg-blue-600/20 rounded text-blue-400"><Edit2 className="h-4 w-4" /></button><button onClick={() => handleDelete(item)} className="p-1.5 hover:bg-red-600/20 rounded text-red-400"><Trash2 className="h-4 w-4" /></button></div></td></tr>))}</tbody></table>
      </div>
      {showModal && (<div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4"><div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-md"><div className="p-4 border-b border-red-900/30 flex items-center justify-between"><h2 className="text-lg font-semibold text-amber-100">{editingItem ? 'Edit' : 'Tambah'} Satuan</h2><button onClick={() => setShowModal(false)} className="p-1 hover:bg-red-900/20 rounded"><X className="h-5 w-5" /></button></div><form onSubmit={handleSubmit} className="p-4 space-y-4"><div><label className="block text-sm text-gray-400 mb-1">Kode</label><input type="text" value={formData.code} onChange={(e) => setFormData({ ...formData, code: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" required /></div><div><label className="block text-sm text-gray-400 mb-1">Nama</label><input type="text" value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" required /></div><div><label className="block text-sm text-gray-400 mb-1">Deskripsi</label><textarea value={formData.description} onChange={(e) => setFormData({ ...formData, description: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" rows={2} /></div><div className="flex justify-end gap-3 pt-4"><button type="button" onClick={() => setShowModal(false)} className="px-4 py-2 border border-red-900/30 rounded-lg">Batal</button><button type="submit" className="px-4 py-2 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg">Simpan</button></div></form></div></div>)}
    </div>
  );
};
export default MasterUnits;
