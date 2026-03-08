import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Plus, Search, Edit, UserCog, Building2, Mail, Shield, Loader2, X, Save, Key } from 'lucide-react';
import { toast } from 'sonner';

const Users = () => {
  const { api } = useAuth();
  const [users, setUsers] = useState([]);
  const [branches, setBranches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    email: '', password: '', name: '', phone: '', role: 'cashier', branch_id: ''
  });

  useEffect(() => { loadUsers(); loadBranches(); }, [search, roleFilter]);

  const loadUsers = async () => {
    setLoading(true);
    try {
      let url = `/api/users?limit=100`;
      if (search) url += `&search=${encodeURIComponent(search)}`;
      if (roleFilter) url += `&role=${roleFilter}`;
      const res = await api(url);
      if (res.ok) { const data = await res.json(); setUsers(data.items || data || []); }
    } catch (err) { toast.error('Gagal memuat data pengguna'); }
    finally { setLoading(false); }
  };

  const loadBranches = async () => {
    try {
      const res = await api('/api/branches');
      if (res.ok) setBranches(await res.json());
    } catch (err) { console.error(err); }
  };

  const openModal = (user = null) => {
    if (user) {
      setEditingUser(user);
      setForm({ email: user.email, password: '', name: user.name, phone: user.phone || '', role: user.role, branch_id: user.branch_id || '' });
    } else {
      setEditingUser(null);
      setForm({ email: '', password: '', name: '', phone: '', role: 'cashier', branch_id: '' });
    }
    setShowModal(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.email || !form.name || !form.role) { toast.error('Email, nama, dan role wajib diisi'); return; }
    if (!editingUser && !form.password) { toast.error('Password wajib diisi untuk pengguna baru'); return; }
    
    setSaving(true);
    try {
      const url = editingUser ? `/api/users/${editingUser.id}` : '/api/users';
      const method = editingUser ? 'PUT' : 'POST';
      const body = editingUser 
        ? { name: form.name, phone: form.phone, role: form.role, branch_id: form.branch_id, ...(form.password && { password: form.password }) }
        : form;
      
      const res = await api(url, { method, body: JSON.stringify(body) });
      if (res.ok) {
        toast.success(editingUser ? 'Pengguna diperbarui' : 'Pengguna ditambahkan');
        setShowModal(false);
        loadUsers();
      } else { const error = await res.json(); toast.error(error.detail || 'Gagal menyimpan'); }
    } catch (err) { toast.error('Gagal menyimpan'); }
    finally { setSaving(false); }
  };

  const toggleStatus = async (userId, isActive) => {
    try {
      const res = await api(`/api/users/${userId}`, {
        method: 'PUT',
        body: JSON.stringify({ is_active: !isActive })
      });
      if (res.ok) { toast.success(isActive ? 'Pengguna dinonaktifkan' : 'Pengguna diaktifkan'); loadUsers(); }
    } catch (err) { toast.error('Gagal mengubah status'); }
  };

  const roles = [
    { value: 'owner', label: 'Pemilik', color: 'bg-amber-900/30 text-amber-400' },
    { value: 'admin', label: 'Administrator', color: 'bg-purple-900/30 text-purple-400' },
    { value: 'supervisor', label: 'Supervisor', color: 'bg-blue-900/30 text-blue-400' },
    { value: 'cashier', label: 'Kasir', color: 'bg-green-900/30 text-green-400' },
    { value: 'finance', label: 'Keuangan', color: 'bg-teal-900/30 text-teal-400' },
    { value: 'inventory', label: 'Gudang', color: 'bg-orange-900/30 text-orange-400' }
  ];

  const getRoleInfo = (role) => roles.find(r => r.value === role) || { label: role, color: 'bg-gray-900/30 text-gray-400' };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Pengguna</h1>
          <p className="text-gray-400">Kelola akun pengguna dan hak akses</p>
        </div>
        <button onClick={() => openModal()} className="px-4 py-2 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg flex items-center gap-2" data-testid="add-user-btn">
          <Plus className="h-5 w-5" /> Tambah Pengguna
        </button>
      </div>

      <div className="flex gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input type="text" placeholder="Cari nama atau email..." value={search} onChange={(e) => setSearch(e.target.value)} className="w-full pl-10 pr-4 py-2 bg-[#1a1214] border border-red-900/30 rounded-lg" />
        </div>
        <select value={roleFilter} onChange={(e) => setRoleFilter(e.target.value)} className="px-4 py-2 bg-[#1a1214] border border-red-900/30 rounded-lg">
          <option value="">Semua Role</option>
          {roles.map(r => <option key={r.value} value={r.value}>{r.label}</option>)}
        </select>
      </div>

      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
        <table className="w-full">
          <thead className="bg-red-900/20">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-semibold">Pengguna</th>
              <th className="px-4 py-3 text-left text-sm font-semibold">Role</th>
              <th className="px-4 py-3 text-left text-sm font-semibold">Cabang</th>
              <th className="px-4 py-3 text-center text-sm font-semibold">Status</th>
              <th className="px-4 py-3 text-center text-sm font-semibold">Aksi</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={5} className="px-4 py-8 text-center"><Loader2 className="h-8 w-8 animate-spin mx-auto text-red-400" /></td></tr>
            ) : users.length === 0 ? (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-400"><UserCog className="h-12 w-12 mx-auto mb-2 opacity-30" />Tidak ada pengguna</td></tr>
            ) : (
              users.map(user => {
                const roleInfo = getRoleInfo(user.role);
                const branch = branches.find(b => b.id === user.branch_id);
                return (
                  <tr key={user.id} className="border-t border-red-900/10 hover:bg-red-900/10">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-red-600 to-amber-500 flex items-center justify-center text-white font-semibold">
                          {user.name?.[0]?.toUpperCase() || 'U'}
                        </div>
                        <div>
                          <div className="font-medium">{user.name}</div>
                          <div className="text-sm text-gray-400">{user.email}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded text-xs font-semibold ${roleInfo.color}`}>
                        {roleInfo.label}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-400">{branch?.name || '-'}</td>
                    <td className="px-4 py-3 text-center">
                      <span className={`px-2 py-1 rounded text-xs font-semibold ${user.is_active !== false ? 'bg-green-900/30 text-green-400' : 'bg-red-900/30 text-red-400'}`}>
                        {user.is_active !== false ? 'Aktif' : 'Nonaktif'}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex justify-center gap-2">
                        <button onClick={() => openModal(user)} className="p-2 text-blue-400 hover:bg-blue-900/20 rounded" title="Edit">
                          <Edit className="h-4 w-4" />
                        </button>
                        <button onClick={() => toggleStatus(user.id, user.is_active !== false)} className={`p-2 rounded ${user.is_active !== false ? 'text-red-400 hover:bg-red-900/20' : 'text-green-400 hover:bg-green-900/20'}`} title={user.is_active !== false ? 'Nonaktifkan' : 'Aktifkan'}>
                          <Shield className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-md">
            <div className="p-6 border-b border-red-900/30 flex justify-between items-center">
              <h2 className="text-xl font-bold">{editingUser ? 'Edit Pengguna' : 'Tambah Pengguna'}</h2>
              <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-white"><X className="h-6 w-6" /></button>
            </div>
            
            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Nama *</label>
                <input type="text" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" required />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Email *</label>
                <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" required disabled={!!editingUser} />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">{editingUser ? 'Password Baru (kosongkan jika tidak diubah)' : 'Password *'}</label>
                <input type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" required={!editingUser} />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Telepon</label>
                <input type="tel" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Role *</label>
                <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" required>
                  {roles.map(r => <option key={r.value} value={r.value}>{r.label}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Cabang</label>
                <select value={form.branch_id} onChange={(e) => setForm({ ...form, branch_id: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg">
                  <option value="">Pilih Cabang</option>
                  {branches.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}
                </select>
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

export default Users;
