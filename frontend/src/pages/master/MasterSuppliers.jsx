import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Plus, Search, Edit2, Trash2, Loader2, X, Phone, Mail, MapPin } from 'lucide-react';
import { toast } from 'sonner';

const MasterSuppliers = () => {
  const { api } = useAuth();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [formData, setFormData] = useState({
    code: '', name: '', contact_name: '', phone: '', email: '', 
    address: '', city: '', payment_terms: 0, is_active: true
  });

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api(`/api/suppliers?search=${searchTerm}`);
      if (res.ok) {
        const data = await res.json();
        setItems(data.items || data || []);
      }
    } catch (err) { toast.error('Gagal memuat data'); }
    finally { setLoading(false); }
  }, [api, searchTerm]);

  useEffect(() => { loadData(); }, [loadData]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const url = editingItem ? `/api/suppliers/${editingItem.id}` : '/api/suppliers';
      const res = await api(url, { method: editingItem ? 'PUT' : 'POST', body: JSON.stringify(formData) });
      if (res.ok) { toast.success('Berhasil disimpan'); setShowModal(false); loadData(); }
    } catch (err) { toast.error('Gagal menyimpan'); }
  };

  const handleEdit = (item) => { 
    setEditingItem(item); 
    setFormData({
      code: item.code || '', name: item.name || '', contact_name: item.contact_name || '',
      phone: item.phone || '', email: item.email || '', address: item.address || '',
      city: item.city || '', payment_terms: item.payment_terms || 0, is_active: item.is_active !== false
    }); 
    setShowModal(true); 
  };
  
  const handleDelete = async (item) => { 
    if (!confirm(`Hapus supplier "${item.name}"?`)) return; 
    try { await api(`/api/suppliers/${item.id}`, { method: 'DELETE' }); toast.success('Berhasil dihapus'); loadData(); } 
    catch { toast.error('Gagal menghapus'); } 
  };

  const resetForm = () => {
    setEditingItem(null);
    setFormData({ code: '', name: '', contact_name: '', phone: '', email: '', address: '', city: '', payment_terms: 0, is_active: true });
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Daftar Supplier</h1>
          <p className="text-gray-400 text-sm">Kelola data supplier/pemasok</p>
        </div>
        <button onClick={() => { resetForm(); setShowModal(true); }} 
          className="px-4 py-2 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg flex items-center gap-2">
          <Plus className="h-4 w-4" /> Tambah Supplier
        </button>
      </div>

      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input type="text" placeholder="Cari supplier..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} 
            className="w-full pl-10 pr-4 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200" />
        </div>
      </div>

      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-red-900/20">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">KODE</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">NAMA SUPPLIER</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">KONTAK</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">TELEPON</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">KOTA</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">TEMPO</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">STATUS</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">AKSI</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-red-900/20">
              {loading ? (
                <tr><td colSpan={8} className="px-4 py-8 text-center"><Loader2 className="h-8 w-8 animate-spin mx-auto text-amber-400" /></td></tr>
              ) : items.length === 0 ? (
                <tr><td colSpan={8} className="px-4 py-8 text-center text-gray-400">Belum ada data supplier</td></tr>
              ) : items.map(item => (
                <tr key={item.id} className="hover:bg-red-900/10">
                  <td className="px-4 py-3 text-sm font-mono text-amber-300">{item.code}</td>
                  <td className="px-4 py-3 font-medium text-gray-200">{item.name}</td>
                  <td className="px-4 py-3 text-sm text-gray-400">{item.contact_name || '-'}</td>
                  <td className="px-4 py-3 text-sm text-gray-400">
                    {item.phone && <div className="flex items-center gap-1"><Phone className="h-3 w-3" /> {item.phone}</div>}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-400">{item.city || '-'}</td>
                  <td className="px-4 py-3 text-sm text-center text-gray-400">{item.payment_terms || 0} hari</td>
                  <td className="px-4 py-3 text-center">
                    <span className={`px-2 py-1 rounded-full text-xs ${item.is_active !== false ? 'bg-green-600/20 text-green-400' : 'bg-red-600/20 text-red-400'}`}>
                      {item.is_active !== false ? 'Aktif' : 'Nonaktif'}
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
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="p-4 border-b border-red-900/30 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-amber-100">{editingItem ? 'Edit' : 'Tambah'} Supplier</h2>
              <button onClick={() => setShowModal(false)} className="p-1 hover:bg-red-900/20 rounded"><X className="h-5 w-5" /></button>
            </div>
            <form onSubmit={handleSubmit} className="p-4 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Kode Supplier *</label>
                  <input type="text" value={formData.code} onChange={(e) => setFormData({ ...formData, code: e.target.value })} 
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" required />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Tempo Pembayaran (hari)</label>
                  <input type="number" value={formData.payment_terms} onChange={(e) => setFormData({ ...formData, payment_terms: Number(e.target.value) })} 
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" />
                </div>
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Nama Supplier *</label>
                <input type="text" value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} 
                  className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" required />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Nama Kontak</label>
                  <input type="text" value={formData.contact_name} onChange={(e) => setFormData({ ...formData, contact_name: e.target.value })} 
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Telepon</label>
                  <input type="text" value={formData.phone} onChange={(e) => setFormData({ ...formData, phone: e.target.value })} 
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Email</label>
                  <input type="email" value={formData.email} onChange={(e) => setFormData({ ...formData, email: e.target.value })} 
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Kota</label>
                  <input type="text" value={formData.city} onChange={(e) => setFormData({ ...formData, city: e.target.value })} 
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" />
                </div>
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

export default MasterSuppliers;
