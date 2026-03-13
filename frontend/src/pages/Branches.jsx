import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Plus, Search, Edit, Edit2, Trash2, Building2, Phone, MapPin, Users, Loader2, X, Save, Wallet } from 'lucide-react';
import { toast } from 'sonner';
import ERPActionToolbar from '../components/ERPActionToolbar';

const Branches = () => {
  const { api } = useAuth();
  const [branches, setBranches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingBranch, setEditingBranch] = useState(null);
  const [selectedItem, setSelectedItem] = useState(null);
  const [saving, setSaving] = useState(false);
  const [viewMode, setViewMode] = useState('card'); // 'card' or 'table'
  const [form, setForm] = useState({
    code: '', name: '', address: '', city: '', phone: '', email: '', is_warehouse: false
  });

  useEffect(() => { loadBranches(); }, []);

  const loadBranches = async () => {
    setLoading(true);
    try {
      const res = await api('/api/branches');
      if (res.ok) setBranches(await res.json());
    } catch (err) { toast.error('Gagal memuat data cabang'); }
    finally { setLoading(false); }
  };

  const openModal = (branch = null) => {
    if (branch) {
      setEditingBranch(branch);
      setForm({ ...branch });
    } else {
      setEditingBranch(null);
      setForm({ code: '', name: '', address: '', city: '', phone: '', email: '', is_warehouse: false });
    }
    setShowModal(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.code || !form.name) { toast.error('Kode dan nama cabang wajib diisi'); return; }
    setSaving(true);
    try {
      const url = editingBranch ? `/api/branches/${editingBranch.id}` : '/api/branches';
      const method = editingBranch ? 'PUT' : 'POST';
      const res = await api(url, { method, body: JSON.stringify(form) });
      if (res.ok) {
        toast.success(editingBranch ? 'Cabang diperbarui' : 'Cabang ditambahkan');
        setShowModal(false);
        loadBranches();
      } else { const error = await res.json(); toast.error(error.detail || 'Gagal menyimpan'); }
    } catch (err) { toast.error('Gagal menyimpan'); }
    finally { setSaving(false); }
  };

  const handleDelete = async (branch) => {
    if (!confirm(`Hapus cabang "${branch.name}"? Pastikan tidak ada transaksi yang terikat.`)) return;
    try {
      const res = await api(`/api/branches/${branch.id}`, { method: 'DELETE' });
      if (res.ok) {
        toast.success('Cabang berhasil dihapus');
        setSelectedItem(null);
        loadBranches();
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Gagal menghapus cabang');
      }
    } catch (err) { toast.error('Gagal menghapus cabang'); }
  };

  const handleRowSelect = (branch) => {
    if (selectedItem?.id === branch.id) {
      setSelectedItem(null);
    } else {
      setSelectedItem(branch);
    }
  };

  const formatRupiah = (num) => `Rp ${(num || 0).toLocaleString('id-ID')}`;

  return (
    <div className="space-y-4" data-testid="branches-page">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Cabang & Gudang</h1>
          <p className="text-gray-400 text-sm">Kelola cabang dan gudang</p>
        </div>
        <div className="flex items-center gap-2">
          <button 
            onClick={() => setViewMode('card')} 
            className={`px-3 py-1.5 rounded text-sm ${viewMode === 'card' ? 'bg-amber-600 text-white' : 'bg-gray-700 text-gray-300'}`}
          >
            Card
          </button>
          <button 
            onClick={() => setViewMode('table')} 
            className={`px-3 py-1.5 rounded text-sm ${viewMode === 'table' ? 'bg-amber-600 text-white' : 'bg-gray-700 text-gray-300'}`}
          >
            Tabel
          </button>
        </div>
      </div>

      {/* TOOLBAR STANDAR ERP */}
      <ERPActionToolbar
        module="branch"
        selectedItem={selectedItem}
        onAdd={() => openModal()}
        onEdit={(item) => openModal(item)}
        onDelete={(item) => handleDelete(item)}
        addLabel="Tambah"
        editLabel="Edit"
        deleteLabel="Hapus"
      />

      {/* TABLE VIEW */}
      {viewMode === 'table' && (
        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
          <table className="w-full">
            <thead className="bg-red-900/20">
              <tr>
                <th className="px-3 py-3 text-center text-xs font-semibold text-amber-200 w-10">
                  <input type="checkbox" className="w-3 h-3" disabled />
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">KODE</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">NAMA</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">TIPE</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">KOTA</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">TELEPON</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-amber-200">SALDO KAS</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">KARYAWAN</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">AKSI</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-red-900/20">
              {loading ? (
                <tr><td colSpan={9} className="px-4 py-8 text-center"><Loader2 className="h-8 w-8 animate-spin mx-auto text-amber-400" /></td></tr>
              ) : branches.length === 0 ? (
                <tr><td colSpan={9} className="px-4 py-8 text-center text-gray-400">Belum ada data cabang</td></tr>
              ) : branches.map((branch, idx) => (
                <tr 
                  key={branch.id} 
                  onClick={() => handleRowSelect(branch)}
                  className={`cursor-pointer transition-colors ${
                    selectedItem?.id === branch.id 
                      ? 'bg-amber-900/30 border-l-2 border-amber-500' 
                      : 'hover:bg-red-900/10'
                  }`}
                  data-testid={`branch-row-${idx}`}
                >
                  <td className="px-3 py-3 text-center">
                    <input 
                      type="radio" 
                      checked={selectedItem?.id === branch.id}
                      onChange={() => handleRowSelect(branch)}
                      className="w-3 h-3 accent-amber-500"
                    />
                  </td>
                  <td className="px-4 py-3 text-sm font-mono text-amber-300">{branch.code}</td>
                  <td className="px-4 py-3 font-medium text-gray-200">{branch.name}</td>
                  <td className="px-4 py-3 text-center">
                    <span className={`px-2 py-1 rounded text-xs ${branch.is_warehouse ? 'bg-amber-900/30 text-amber-400' : 'bg-blue-900/30 text-blue-400'}`}>
                      {branch.is_warehouse ? 'Gudang' : 'Cabang'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-400">{branch.city || '-'}</td>
                  <td className="px-4 py-3 text-sm text-gray-400">{branch.phone || '-'}</td>
                  <td className="px-4 py-3 text-sm text-right text-amber-400">{formatRupiah(branch.cash_balance)}</td>
                  <td className="px-4 py-3 text-sm text-center text-gray-300">{branch.employee_count || 0}</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-center gap-1">
                      <button onClick={(e) => { e.stopPropagation(); openModal(branch); }} className="p-1.5 hover:bg-purple-600/20 rounded text-purple-400" title="Edit">
                        <Edit2 className="h-4 w-4" />
                      </button>
                      <button onClick={(e) => { e.stopPropagation(); handleDelete(branch); }} className="p-1.5 hover:bg-red-600/20 rounded text-red-400" title="Hapus">
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* CARD VIEW */}
      {viewMode === 'card' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {loading ? (
            <div className="col-span-full flex justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-red-400" />
            </div>
          ) : branches.length === 0 ? (
            <div className="col-span-full text-center py-12 text-gray-400">
              <Building2 className="h-16 w-16 mx-auto mb-4 opacity-30" />
              <p>Tidak ada cabang</p>
            </div>
          ) : (
            branches.map(branch => (
              <div 
                key={branch.id} 
                onClick={() => handleRowSelect(branch)}
                className={`bg-[#1a1214] border rounded-xl p-5 cursor-pointer transition-colors ${
                  selectedItem?.id === branch.id 
                    ? 'border-amber-500 bg-amber-900/20' 
                    : 'border-red-900/30 hover:border-red-700/50'
                }`}
                data-testid={`branch-card-${branch.id}`}
              >
                <div className="flex justify-between items-start mb-3">
                  <div className="flex items-center gap-3">
                    <div className={`p-3 rounded-lg ${branch.is_warehouse ? 'bg-amber-900/30' : 'bg-blue-900/30'}`}>
                      <Building2 className={`h-6 w-6 ${branch.is_warehouse ? 'text-amber-400' : 'text-blue-400'}`} />
                    </div>
                    <div>
                      <h3 className="font-semibold text-lg">{branch.name}</h3>
                      <span className="text-xs text-gray-400">{branch.code}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-1">
                    <button onClick={(e) => { e.stopPropagation(); openModal(branch); }} className="p-2 text-purple-400 hover:bg-purple-900/20 rounded" title="Edit">
                      <Edit className="h-4 w-4" />
                    </button>
                    <button onClick={(e) => { e.stopPropagation(); handleDelete(branch); }} className="p-2 text-red-400 hover:bg-red-900/20 rounded" title="Hapus">
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>

                {branch.is_warehouse && (
                  <span className="inline-block px-2 py-0.5 bg-amber-900/30 text-amber-400 text-xs rounded mb-3">Gudang</span>
                )}
                
                <div className="space-y-2 text-sm text-gray-400 mb-4">
                  {branch.phone && <div className="flex items-center gap-2"><Phone className="h-4 w-4" />{branch.phone}</div>}
                  {branch.city && <div className="flex items-center gap-2"><MapPin className="h-4 w-4" />{branch.city}</div>}
                  {branch.address && <div className="text-xs">{branch.address}</div>}
                </div>

                <div className="pt-3 border-t border-red-900/30 grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <div className="text-gray-400 flex items-center gap-1"><Users className="h-3 w-3" />Karyawan</div>
                    <div className="font-semibold">{branch.employee_count || 0}</div>
                  </div>
                  <div>
                    <div className="text-gray-400 flex items-center gap-1"><Wallet className="h-3 w-3" />Saldo Kas</div>
                    <div className="font-semibold text-amber-400">{formatRupiah(branch.cash_balance)}</div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {showModal && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-lg">
            <div className="p-6 border-b border-red-900/30 flex justify-between items-center">
              <h2 className="text-xl font-bold">{editingBranch ? 'Edit Cabang' : 'Tambah Cabang'}</h2>
              <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-white"><X className="h-6 w-6" /></button>
            </div>
            
            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Kode Cabang *</label>
                  <input type="text" value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value.toUpperCase() })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" required disabled={!!editingBranch} />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Nama Cabang *</label>
                  <input type="text" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" required />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Telepon</label>
                  <input type="tel" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Email</label>
                  <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" />
                </div>
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-1">Kota</label>
                <input type="text" value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" />
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-1">Alamat</label>
                <textarea value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" rows={2} />
              </div>

              <div className="flex items-center gap-3">
                <input type="checkbox" id="is_warehouse" checked={form.is_warehouse} onChange={(e) => setForm({ ...form, is_warehouse: e.target.checked })} className="w-4 h-4" />
                <label htmlFor="is_warehouse" className="text-sm">Jadikan sebagai Gudang</label>
              </div>
              
              <div className="flex gap-3 pt-4">
                <button type="button" onClick={() => setShowModal(false)} className="flex-1 py-2 border border-red-900/30 rounded-lg hover:bg-red-900/20">Batal</button>
                <button type="submit" disabled={saving} className="flex-1 py-2 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg disabled:opacity-50 flex items-center justify-center gap-2">
                  {saving ? <Loader2 className="h-5 w-5 animate-spin" /> : <Save className="h-5 w-5" />}
                  {saving ? 'Menyimpan...' : 'Simpan'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Branches;
