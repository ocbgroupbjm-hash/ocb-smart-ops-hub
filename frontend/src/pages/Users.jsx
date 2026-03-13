import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Plus, Search, Edit, UserCog, Building2, Mail, Phone, Shield, Loader2, X, Save, Key, Eye, EyeOff, Trash2, RefreshCw } from 'lucide-react';
import { toast } from 'sonner';

const Users = () => {
  const { api, user: currentUser } = useAuth();
  const [users, setUsers] = useState([]);
  const [branches, setBranches] = useState([]);
  const [roles, setRoles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [branchFilter, setBranchFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [showResetModal, setShowResetModal] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [saving, setSaving] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [form, setForm] = useState({
    email: '', password: '', name: '', phone: '', role: 'cashier', branch_id: '', is_active: true
  });
  const [newPassword, setNewPassword] = useState('');

  useEffect(() => { loadUsers(); loadBranches(); loadRoles(); }, [search, roleFilter, branchFilter, statusFilter]);

  const loadUsers = async () => {
    setLoading(true);
    try {
      let url = `/api/users?limit=200`;
      if (search) url += `&search=${encodeURIComponent(search)}`;
      if (roleFilter) url += `&role=${roleFilter}`;
      if (branchFilter) url += `&branch_id=${branchFilter}`;
      const res = await api(url);
      if (res.ok) {
        let data = await res.json();
        let items = data.items || data || [];
        if (statusFilter === 'active') items = items.filter(u => u.is_active !== false);
        else if (statusFilter === 'inactive') items = items.filter(u => u.is_active === false);
        setUsers(items);
      }
    } catch (err) { toast.error('Gagal memuat data pengguna'); }
    finally { setLoading(false); }
  };

  const loadBranches = async () => {
    try {
      const res = await api('/api/branches');
      if (res.ok) setBranches(await res.json());
    } catch (err) { console.error(err); }
  };

  const loadRoles = async () => {
    try {
      const res = await api('/api/roles');
      if (res.ok) setRoles(await res.json());
    } catch (err) { console.error(err); }
  };

  const openModal = (user = null) => {
    if (user) {
      setEditingUser(user);
      setForm({ 
        email: user.email, 
        password: '', 
        name: user.name, 
        phone: user.phone || '', 
        role: user.role, 
        branch_id: user.branch_id || '',
        is_active: user.is_active !== false
      });
    } else {
      setEditingUser(null);
      setForm({ email: '', password: '', name: '', phone: '', role: 'cashier', branch_id: '', is_active: true });
    }
    setShowModal(true);
    setShowPassword(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.email || !form.name || !form.role) { 
      toast.error('Email, nama, dan role wajib diisi'); 
      return; 
    }
    if (!editingUser && !form.password) { 
      toast.error('Password wajib diisi untuk pengguna baru'); 
      return; 
    }
    
    setSaving(true);
    try {
      const url = editingUser ? `/api/users/${editingUser.id}` : '/api/users';
      const method = editingUser ? 'PUT' : 'POST';
      
      const body = editingUser 
        ? { 
            name: form.name, 
            phone: form.phone, 
            role: form.role, 
            branch_id: form.branch_id || null,
            is_active: form.is_active,
            ...(form.password && { password: form.password }) 
          }
        : form;
      
      const res = await api(url, { method, body: JSON.stringify(body) });
      if (res.ok) {
        toast.success(editingUser ? 'Pengguna berhasil diperbarui' : 'Pengguna berhasil ditambahkan');
        setShowModal(false);
        loadUsers();
      } else { 
        const error = await res.json(); 
        toast.error(error.detail || 'Gagal menyimpan'); 
      }
    } catch (err) { toast.error('Gagal menyimpan'); }
    finally { setSaving(false); }
  };

  const openResetModal = (user) => {
    setEditingUser(user);
    setNewPassword('');
    setShowResetModal(true);
  };

  const handleResetPassword = async () => {
    if (!newPassword || newPassword.length < 6) {
      toast.error('Password minimal 6 karakter');
      return;
    }
    setSaving(true);
    try {
      const res = await api(`/api/users/${editingUser.id}`, {
        method: 'PUT',
        body: JSON.stringify({ password: newPassword })
      });
      if (res.ok) {
        toast.success('Password berhasil direset');
        setShowResetModal(false);
      } else {
        const error = await res.json();
        toast.error(error.detail || 'Gagal reset password');
      }
    } catch (err) { toast.error('Gagal reset password'); }
    finally { setSaving(false); }
  };

  const toggleStatus = async (userId, isActive) => {
    try {
      const res = await api(`/api/users/${userId}`, {
        method: 'PUT',
        body: JSON.stringify({ is_active: !isActive })
      });
      if (res.ok) { 
        toast.success(isActive ? 'Pengguna dinonaktifkan' : 'Pengguna diaktifkan'); 
        loadUsers(); 
      }
    } catch (err) { toast.error('Gagal mengubah status'); }
  };

  const deleteUser = async (userId) => {
    if (!window.confirm('Yakin ingin menghapus pengguna ini?')) return;
    try {
      const res = await api(`/api/users/${userId}`, { method: 'DELETE' });
      if (res.ok) {
        toast.success('Pengguna berhasil dihapus');
        loadUsers();
      } else {
        const error = await res.json();
        toast.error(error.detail || 'Gagal menghapus');
      }
    } catch (err) { toast.error('Gagal menghapus pengguna'); }
  };

  const getRoleInfo = (roleCode) => {
    const role = roles.find(r => r.code === roleCode);
    return role ? role.name : roleCode;
  };

  const roleColors = {
    owner: 'bg-amber-900/30 text-amber-400',
    admin: 'bg-purple-900/30 text-purple-400',
    supervisor: 'bg-blue-900/30 text-blue-400',
    cashier: 'bg-green-900/30 text-green-400',
    finance: 'bg-teal-900/30 text-teal-400',
    inventory: 'bg-orange-900/30 text-orange-400'
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Pengguna</h1>
          <p className="text-gray-400">Kelola karyawan dan hak akses</p>
        </div>
        <button onClick={() => openModal()} className="px-4 py-2 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg flex items-center gap-2" data-testid="add-user-btn">
          <Plus className="h-5 w-5" /> Tambah Pengguna
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input type="text" placeholder="Cari nama atau email..." value={search} onChange={(e) => setSearch(e.target.value)} className="w-full pl-10 pr-4 py-2 bg-[#1a1214] border border-red-900/30 rounded-lg" />
        </div>
        <select value={roleFilter} onChange={(e) => setRoleFilter(e.target.value)} className="px-4 py-2 bg-[#1a1214] border border-red-900/30 rounded-lg">
          <option value="">Semua Role</option>
          {roles.map(r => <option key={r.code} value={r.code}>{r.name}</option>)}
        </select>
        <select value={branchFilter} onChange={(e) => setBranchFilter(e.target.value)} className="px-4 py-2 bg-[#1a1214] border border-red-900/30 rounded-lg">
          <option value="">Semua Cabang</option>
          {branches.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}
        </select>
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="px-4 py-2 bg-[#1a1214] border border-red-900/30 rounded-lg">
          <option value="">Semua Status</option>
          <option value="active">Aktif</option>
          <option value="inactive">Nonaktif</option>
        </select>
      </div>

      {/* Users Table - With Horizontal Scroll */}
      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[900px]">
            <thead className="bg-red-900/20">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-semibold whitespace-nowrap">Pengguna</th>
                <th className="px-4 py-3 text-left text-sm font-semibold whitespace-nowrap">Telepon</th>
                <th className="px-4 py-3 text-left text-sm font-semibold whitespace-nowrap">Role</th>
                <th className="px-4 py-3 text-left text-sm font-semibold whitespace-nowrap">Cabang</th>
                <th className="px-4 py-3 text-left text-sm font-semibold whitespace-nowrap">Login Terakhir</th>
                <th className="px-4 py-3 text-center text-sm font-semibold whitespace-nowrap">Status</th>
                <th className="px-4 py-3 text-center text-sm font-semibold whitespace-nowrap">Aksi</th>
              </tr>
            </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={7} className="px-4 py-8 text-center"><Loader2 className="h-8 w-8 animate-spin mx-auto text-red-400" /></td></tr>
            ) : users.length === 0 ? (
              <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-400"><UserCog className="h-12 w-12 mx-auto mb-2 opacity-30" />Tidak ada pengguna</td></tr>
            ) : (
              users.map(user => {
                const branch = branches.find(b => b.id === user.branch_id);
                const lastLogin = user.last_login ? new Date(user.last_login).toLocaleString('id-ID', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : '-';
                return (
                  <tr key={user.id} className="border-t border-red-900/10 hover:bg-red-900/10">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-red-600 to-amber-500 flex items-center justify-center text-white font-semibold flex-shrink-0">
                          {user.name?.[0]?.toUpperCase() || 'U'}
                        </div>
                        <div className="min-w-0">
                          <div className="font-medium truncate">{user.name}</div>
                          <div className="text-sm text-gray-400 truncate">{user.email}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-gray-400 whitespace-nowrap">{user.phone || '-'}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded text-xs font-semibold whitespace-nowrap ${roleColors[user.role] || 'bg-gray-900/30 text-gray-400'}`}>
                        {getRoleInfo(user.role)}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-400 whitespace-nowrap">{branch?.name || '-'}</td>
                    <td className="px-4 py-3 text-gray-400 text-sm whitespace-nowrap">{lastLogin}</td>
                    <td className="px-4 py-3 text-center">
                      <span className={`px-2 py-1 rounded text-xs font-semibold whitespace-nowrap ${user.is_active !== false ? 'bg-green-900/30 text-green-400' : 'bg-red-900/30 text-red-400'}`}>
                        {user.is_active !== false ? 'Aktif' : 'Nonaktif'}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex justify-center gap-1">
                        <button onClick={() => openModal(user)} className="p-2 text-blue-400 hover:bg-blue-900/20 rounded" title="Edit">
                          <Edit className="h-4 w-4" />
                        </button>
                        <button onClick={() => openResetModal(user)} className="p-2 text-amber-400 hover:bg-amber-900/20 rounded" title="Reset Password">
                          <Key className="h-4 w-4" />
                        </button>
                        <button onClick={() => toggleStatus(user.id, user.is_active !== false)} className={`p-2 rounded ${user.is_active !== false ? 'text-red-400 hover:bg-red-900/20' : 'text-green-400 hover:bg-green-900/20'}`} title={user.is_active !== false ? 'Nonaktifkan' : 'Aktifkan'}>
                          <Shield className="h-4 w-4" />
                        </button>
                        {currentUser?.role === 'owner' && user.id !== currentUser?.id && (
                          <button onClick={() => deleteUser(user.id)} className="p-2 text-red-400 hover:bg-red-900/20 rounded" title="Hapus">
                            <Trash2 className="h-4 w-4" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
        </div>
      </div>

      {/* Add/Edit User Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-lg">
            <div className="p-6 border-b border-red-900/30 flex justify-between items-center">
              <h2 className="text-xl font-bold">{editingUser ? 'Edit Pengguna' : 'Tambah Pengguna'}</h2>
              <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-white"><X className="h-6 w-6" /></button>
            </div>
            
            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Nama Lengkap *</label>
                <input type="text" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" required placeholder="Masukkan nama lengkap" />
              </div>
              
              <div>
                <label className="block text-sm text-gray-400 mb-1">Email *</label>
                <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" required disabled={!!editingUser} placeholder="email@example.com" />
              </div>
              
              <div>
                <label className="block text-sm text-gray-400 mb-1">{editingUser ? 'Password Baru (kosongkan jika tidak diubah)' : 'Password *'}</label>
                <div className="relative">
                  <input type={showPassword ? 'text' : 'password'} value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} className="w-full px-3 py-2 pr-10 bg-[#0a0608] border border-red-900/30 rounded-lg" required={!editingUser} placeholder={editingUser ? '••••••••' : 'Minimal 6 karakter'} />
                  <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white">
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>
              
              <div>
                <label className="block text-sm text-gray-400 mb-1">Nomor HP</label>
                <input type="tel" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" placeholder="08xxxxxxxxxx" />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Role *</label>
                  <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" required>
                    {roles.map(r => <option key={r.code} value={r.code}>{r.name}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Cabang</label>
                  <select value={form.branch_id} onChange={(e) => setForm({ ...form, branch_id: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg">
                    <option value="">Semua Cabang</option>
                    {branches.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}
                  </select>
                </div>
              </div>
              
              <div className="flex items-center gap-3">
                <input type="checkbox" id="is_active" checked={form.is_active} onChange={(e) => setForm({ ...form, is_active: e.target.checked })} className="w-4 h-4" />
                <label htmlFor="is_active" className="text-sm">Aktifkan pengguna ini</label>
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

      {/* Reset Password Modal */}
      {showResetModal && editingUser && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-md">
            <div className="p-6 border-b border-red-900/30 flex justify-between items-center">
              <div>
                <h2 className="text-xl font-bold">Reset Password</h2>
                <p className="text-gray-400 text-sm">{editingUser.name} ({editingUser.email})</p>
              </div>
              <button onClick={() => setShowResetModal(false)} className="text-gray-400 hover:text-white"><X className="h-6 w-6" /></button>
            </div>
            
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Password Baru *</label>
                <div className="relative">
                  <input type={showPassword ? 'text' : 'password'} value={newPassword} onChange={(e) => setNewPassword(e.target.value)} className="w-full px-3 py-2 pr-10 bg-[#0a0608] border border-red-900/30 rounded-lg" placeholder="Minimal 6 karakter" />
                  <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white">
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>
              
              <div className="flex gap-3">
                <button onClick={() => setShowResetModal(false)} className="flex-1 py-2 border border-red-900/30 rounded-lg hover:bg-red-900/20">Batal</button>
                <button onClick={handleResetPassword} disabled={saving} className="flex-1 py-2 bg-gradient-to-r from-amber-600 to-red-600 text-white rounded-lg disabled:opacity-50 flex items-center justify-center gap-2">
                  {saving ? <Loader2 className="h-5 w-5 animate-spin" /> : <RefreshCw className="h-5 w-5" />}
                  {saving ? 'Mereset...' : 'Reset Password'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Users;
