import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Plus, Search, Edit2, Trash2, Loader2, X, Users, Percent, Tag } from 'lucide-react';
import { toast } from 'sonner';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';

const MasterCustomerGroups = () => {
  const { api } = useAuth();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [formData, setFormData] = useState({ 
    code: '', name: '', discount_percent: 0, price_level: 1, description: '' 
  });

  const priceLevelOptions = [
    { value: 1, label: 'Level 1 - Harga Umum', color: 'gray' },
    { value: 2, label: 'Level 2 - Harga Member', color: 'blue' },
    { value: 3, label: 'Level 3 - Harga Grosir', color: 'green' },
    { value: 4, label: 'Level 4 - Harga Reseller', color: 'purple' },
    { value: 5, label: 'Level 5 - Harga VIP', color: 'amber' },
  ];

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api(`/api/master/customer-groups?search=${searchTerm}`);
      if (res.ok) setItems(await res.json());
    } catch (err) { toast.error('Gagal memuat data'); }
    finally { setLoading(false); }
  }, [api, searchTerm]);

  useEffect(() => { loadData(); }, [loadData]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const url = editingItem ? `/api/master/customer-groups/${editingItem.id}` : '/api/master/customer-groups';
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
      discount_percent: item.discount_percent || 0,
      price_level: item.price_level || 1,
      description: item.description || '' 
    }); 
    setShowModal(true); 
  };

  const handleDelete = async (item) => { 
    if (!confirm(`Hapus grup "${item.name}"?`)) return; 
    try { 
      await api(`/api/master/customer-groups/${item.id}`, { method: 'DELETE' }); 
      toast.success('Berhasil dihapus'); 
      loadData(); 
    } catch { toast.error('Gagal menghapus'); } 
  };

  const resetForm = () => {
    setEditingItem(null);
    setFormData({ code: '', name: '', discount_percent: 0, price_level: 1, description: '' });
  };

  const getPriceLevelBadge = (level) => {
    const opt = priceLevelOptions.find(o => o.value === level) || priceLevelOptions[0];
    const colors = {
      gray: 'bg-gray-600/20 text-gray-400',
      blue: 'bg-blue-600/20 text-blue-400',
      green: 'bg-green-600/20 text-green-400',
      purple: 'bg-purple-600/20 text-purple-400',
      amber: 'bg-amber-600/20 text-amber-400',
    };
    return (
      <span className={`px-2 py-1 rounded text-xs ${colors[opt.color]}`}>
        Level {level}
      </span>
    );
  };

  return (
    <div className="space-y-4" data-testid="customer-groups-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Grup Pelanggan</h1>
          <p className="text-gray-400 text-sm">Kelola grup pelanggan dengan price level</p>
        </div>
        <button onClick={() => { resetForm(); setShowModal(true); }} 
          className="px-4 py-2 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg flex items-center gap-2">
          <Plus className="h-4 w-4" /> Tambah Grup
        </button>
      </div>

      {/* Info Price Level */}
      <div className="bg-[#1a1214] border border-amber-600/30 rounded-xl p-4">
        <div className="flex items-center gap-2 mb-2">
          <Tag className="h-4 w-4 text-amber-400" />
          <span className="text-amber-200 font-medium text-sm">Price Level System</span>
        </div>
        <div className="flex flex-wrap gap-2">
          {priceLevelOptions.map(opt => (
            <div key={opt.value} className={`px-3 py-1.5 rounded-lg text-xs ${
              opt.value === 1 ? 'bg-gray-600/20 text-gray-400' :
              opt.value === 2 ? 'bg-blue-600/20 text-blue-400' :
              opt.value === 3 ? 'bg-green-600/20 text-green-400' :
              opt.value === 4 ? 'bg-purple-600/20 text-purple-400' :
              'bg-amber-600/20 text-amber-400'
            }`}>
              {opt.label}
            </div>
          ))}
        </div>
        <p className="text-gray-500 text-xs mt-2">
          Setiap grup pelanggan di-mapping ke price level. Saat transaksi, sistem otomatis menggunakan harga sesuai level.
        </p>
      </div>

      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input type="text" placeholder="Cari grup..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} 
            className="w-full pl-10 pr-4 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200" />
        </div>
      </div>

      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
        <table className="w-full">
          <thead className="bg-red-900/20">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">KODE</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">NAMA GRUP</th>
              <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">PRICE LEVEL</th>
              <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">DISKON %</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">DESKRIPSI</th>
              <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">AKSI</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-red-900/20">
            {loading ? (
              <tr><td colSpan={6} className="px-4 py-8 text-center"><Loader2 className="h-8 w-8 animate-spin mx-auto text-amber-400" /></td></tr>
            ) : items.length === 0 ? (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-400">Belum ada data grup pelanggan</td></tr>
            ) : items.map(item => (
              <tr key={item.id} className="hover:bg-red-900/10">
                <td className="px-4 py-3 text-sm font-mono text-amber-300">{item.code}</td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <Users className="h-4 w-4 text-gray-500" />
                    <span className="font-medium text-gray-200">{item.name}</span>
                  </div>
                </td>
                <td className="px-4 py-3 text-center">
                  {getPriceLevelBadge(item.price_level || 1)}
                </td>
                <td className="px-4 py-3 text-center">
                  <span className="px-2 py-1 bg-green-600/20 text-green-400 rounded text-sm">
                    {item.discount_percent || 0}%
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-gray-400">{item.description || '-'}</td>
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
              <h2 className="text-lg font-semibold text-amber-100">{editingItem ? 'Edit' : 'Tambah'} Grup Pelanggan</h2>
              <button onClick={() => setShowModal(false)} className="p-1 hover:bg-red-900/20 rounded"><X className="h-5 w-5" /></button>
            </div>
            <form onSubmit={handleSubmit} className="p-4 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Kode Grup *</label>
                  <input type="text" value={formData.code} onChange={(e) => setFormData({ ...formData, code: e.target.value })} 
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" required />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Nama Grup *</label>
                  <input type="text" value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} 
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" required />
                </div>
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Price Level (Mapping Harga)</label>
                <Select 
                  value={String(formData.price_level)} 
                  onValueChange={(v) => setFormData({ ...formData, price_level: Number(v) })}
                >
                  <SelectTrigger className="w-full bg-[#0a0608] border-red-900/30">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {priceLevelOptions.map(opt => (
                      <SelectItem key={opt.value} value={String(opt.value)}>{opt.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-xs text-gray-500 mt-1">Pelanggan dalam grup ini akan menggunakan harga sesuai level</p>
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Diskon Default (%)</label>
                <input type="number" min="0" max="100" value={formData.discount_percent} 
                  onChange={(e) => setFormData({ ...formData, discount_percent: Number(e.target.value) })} 
                  className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Deskripsi</label>
                <textarea value={formData.description} onChange={(e) => setFormData({ ...formData, description: e.target.value })} 
                  className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" rows={2} />
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

export default MasterCustomerGroups;
