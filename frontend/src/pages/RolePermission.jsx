import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Shield, Plus, Edit, Trash2, X, Save, Loader2, Check, Eye, Pencil, Ban, Download, Printer, CheckCircle } from 'lucide-react';
import { toast } from 'sonner';

const RolePermission = () => {
  const { api, user } = useAuth();
  const [roles, setRoles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedRole, setSelectedRole] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [saving, setSaving] = useState(false);
  const [permissions, setPermissions] = useState({});
  const [newRole, setNewRole] = useState({ code: '', name: '', description: '' });

  const menuLabels = {
    dashboard: 'Dashboard',
    kasir: 'Kasir',
    produk: 'Produk',
    stok: 'Stok',
    pembelian: 'Pembelian',
    supplier: 'Supplier',
    pelanggan: 'Pelanggan',
    keuangan: 'Keuangan',
    akuntansi: 'Akuntansi',
    laporan: 'Laporan',
    cabang: 'Cabang',
    pengguna: 'Pengguna',
    pengaturan: 'Pengaturan',
    ai_bisnis: 'AI Bisnis'
  };

  const actionLabels = {
    lihat: 'Lihat',
    tambah: 'Tambah',
    edit: 'Edit',
    hapus: 'Hapus',
    approve: 'Approve',
    export: 'Export',
    cetak: 'Cetak',
    void: 'Void',
    retur: 'Retur',
    transfer: 'Transfer',
    opname: 'Opname',
    terima: 'Terima',
    reset_password: 'Reset Password'
  };

  const actionIcons = {
    lihat: Eye,
    tambah: Plus,
    edit: Pencil,
    hapus: Trash2,
    approve: CheckCircle,
    export: Download,
    cetak: Printer,
    void: Ban,
    retur: Ban,
    transfer: Shield,
    opname: Check,
    terima: Check,
    reset_password: Shield
  };

  useEffect(() => { loadRoles(); }, []);

  const loadRoles = async () => {
    setLoading(true);
    try {
      const res = await api('/api/roles');
      if (res.ok) {
        const data = await res.json();
        setRoles(data);
      }
    } catch (err) { toast.error('Gagal memuat data role'); }
    finally { setLoading(false); }
  };

  const openEditModal = async (role) => {
    setSelectedRole(role);
    setPermissions(role.permissions || {});
    setShowModal(true);
  };

  const togglePermission = (menu, action) => {
    setPermissions(prev => ({
      ...prev,
      [menu]: {
        ...prev[menu],
        [action]: !prev[menu]?.[action]
      }
    }));
  };

  const toggleAllMenu = (menu) => {
    const menuPerms = permissions[menu] || {};
    const allEnabled = Object.values(menuPerms).every(v => v);
    setPermissions(prev => ({
      ...prev,
      [menu]: Object.fromEntries(Object.keys(menuPerms).map(k => [k, !allEnabled]))
    }));
  };

  const handleSavePermissions = async () => {
    setSaving(true);
    try {
      const res = await api(`/api/roles/${selectedRole.code}`, {
        method: 'PUT',
        body: JSON.stringify({ permissions })
      });
      if (res.ok) {
        toast.success('Hak akses berhasil disimpan');
        setShowModal(false);
        loadRoles();
      } else {
        const error = await res.json();
        toast.error(error.detail || 'Gagal menyimpan');
      }
    } catch (err) { toast.error('Gagal menyimpan'); }
    finally { setSaving(false); }
  };

  const handleAddRole = async () => {
    if (!newRole.code || !newRole.name) {
      toast.error('Kode dan nama role wajib diisi');
      return;
    }
    setSaving(true);
    try {
      const res = await api('/api/roles', {
        method: 'POST',
        body: JSON.stringify(newRole)
      });
      if (res.ok) {
        toast.success('Role baru berhasil ditambahkan');
        setShowAddModal(false);
        setNewRole({ code: '', name: '', description: '' });
        loadRoles();
      } else {
        const error = await res.json();
        toast.error(error.detail || 'Gagal menambahkan role');
      }
    } catch (err) { toast.error('Gagal menambahkan role'); }
    finally { setSaving(false); }
  };

  const handleDeleteRole = async (roleCode) => {
    if (!window.confirm('Yakin ingin menghapus role ini?')) return;
    try {
      const res = await api(`/api/roles/${roleCode}`, { method: 'DELETE' });
      if (res.ok) {
        toast.success('Role berhasil dihapus');
        loadRoles();
      } else {
        const error = await res.json();
        toast.error(error.detail || 'Gagal menghapus role');
      }
    } catch (err) { toast.error('Gagal menghapus role'); }
  };

  const roleColors = {
    owner: 'from-amber-600 to-yellow-500',
    admin: 'from-purple-600 to-pink-500',
    supervisor: 'from-blue-600 to-cyan-500',
    cashier: 'from-green-600 to-emerald-500',
    finance: 'from-teal-600 to-cyan-500',
    inventory: 'from-orange-600 to-amber-500'
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Role & Hak Akses</h1>
          <p className="text-gray-400">Kelola role dan permission pengguna</p>
        </div>
        {user?.role === 'owner' && (
          <button onClick={() => setShowAddModal(true)} className="px-4 py-2 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg flex items-center gap-2" data-testid="add-role-btn">
            <Plus className="h-5 w-5" /> Tambah Role
          </button>
        )}
      </div>

      {/* Role Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {loading ? (
          <div className="col-span-full flex justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-red-400" />
          </div>
        ) : roles.length === 0 ? (
          <div className="col-span-full text-center py-12 text-gray-400">
            <Shield className="h-16 w-16 mx-auto mb-4 opacity-30" />
            <p>Tidak ada role</p>
          </div>
        ) : (
          roles.map(role => (
            <div key={role.code} className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden hover:border-red-700/50 transition-colors">
              <div className={`h-2 bg-gradient-to-r ${roleColors[role.code] || 'from-gray-600 to-gray-500'}`} />
              <div className="p-5">
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <h3 className="text-lg font-semibold">{role.name}</h3>
                    <span className="text-xs text-gray-400">{role.code}</span>
                  </div>
                  <div className="flex gap-1">
                    <button onClick={() => openEditModal(role)} className="p-2 text-blue-400 hover:bg-blue-900/20 rounded" title="Edit Hak Akses">
                      <Edit className="h-4 w-4" />
                    </button>
                    {!role.is_system && user?.role === 'owner' && (
                      <button onClick={() => handleDeleteRole(role.code)} className="p-2 text-red-400 hover:bg-red-900/20 rounded" title="Hapus Role">
                        <Trash2 className="h-4 w-4" />
                      </button>
                    )}
                  </div>
                </div>
                <p className="text-sm text-gray-400 mb-4">{role.description}</p>
                
                {/* Permission Summary */}
                <div className="flex flex-wrap gap-1">
                  {Object.entries(role.permissions || {}).slice(0, 5).map(([menu, perms]) => {
                    const hasAccess = perms?.lihat;
                    return hasAccess ? (
                      <span key={menu} className="px-2 py-0.5 bg-green-900/20 text-green-400 rounded text-xs">
                        {menuLabels[menu] || menu}
                      </span>
                    ) : null;
                  })}
                  {Object.keys(role.permissions || {}).length > 5 && (
                    <span className="px-2 py-0.5 bg-gray-900/30 text-gray-400 rounded text-xs">
                      +{Object.keys(role.permissions).length - 5} lainnya
                    </span>
                  )}
                </div>
                
                {role.is_system && (
                  <div className="mt-3 text-xs text-amber-400/70">Role sistem - tidak dapat dihapus</div>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Edit Permission Modal */}
      {showModal && selectedRole && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-5xl max-h-[90vh] overflow-hidden">
            <div className="p-6 border-b border-red-900/30 flex justify-between items-center sticky top-0 bg-[#1a1214] z-10">
              <div>
                <h2 className="text-xl font-bold">Atur Hak Akses</h2>
                <p className="text-gray-400">{selectedRole.name} ({selectedRole.code})</p>
              </div>
              <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-white"><X className="h-6 w-6" /></button>
            </div>
            
            <div className="p-6 overflow-y-auto max-h-[calc(90vh-180px)]">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-red-900/20 sticky top-0">
                    <tr>
                      <th className="px-4 py-3 text-left font-semibold">Menu</th>
                      {Object.keys(actionLabels).slice(0, 7).map(action => (
                        <th key={action} className="px-3 py-3 text-center font-semibold w-20">
                          {actionLabels[action]}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(menuLabels).map(([menu, label]) => {
                      const menuPerms = permissions[menu] || {};
                      const availableActions = Object.keys(menuPerms);
                      
                      return (
                        <tr key={menu} className="border-t border-red-900/10 hover:bg-red-900/10">
                          <td className="px-4 py-3">
                            <button onClick={() => toggleAllMenu(menu)} className="flex items-center gap-2 hover:text-amber-400">
                              <Shield className="h-4 w-4 text-gray-400" />
                              <span className="font-medium">{label}</span>
                            </button>
                          </td>
                          {Object.keys(actionLabels).slice(0, 7).map(action => {
                            const hasAction = action in menuPerms;
                            const isEnabled = menuPerms[action];
                            const ActionIcon = actionIcons[action] || Check;
                            
                            return (
                              <td key={action} className="px-3 py-3 text-center">
                                {hasAction ? (
                                  <button
                                    onClick={() => togglePermission(menu, action)}
                                    className={`p-2 rounded-lg transition-colors ${
                                      isEnabled 
                                        ? 'bg-green-600/20 text-green-400 hover:bg-green-600/30' 
                                        : 'bg-gray-800/50 text-gray-500 hover:bg-gray-700/50'
                                    }`}
                                  >
                                    {isEnabled ? <Check className="h-4 w-4" /> : <X className="h-4 w-4" />}
                                  </button>
                                ) : (
                                  <span className="text-gray-600">-</span>
                                )}
                              </td>
                            );
                          })}
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
            
            <div className="p-6 border-t border-red-900/30 flex gap-3 bg-[#1a1214]">
              <button onClick={() => setShowModal(false)} className="flex-1 py-2 border border-red-900/30 rounded-lg hover:bg-red-900/20">
                Batal
              </button>
              <button onClick={handleSavePermissions} disabled={saving} className="flex-1 py-2 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg disabled:opacity-50 flex items-center justify-center gap-2">
                {saving ? <Loader2 className="h-5 w-5 animate-spin" /> : <Save className="h-5 w-5" />}
                {saving ? 'Menyimpan...' : 'Simpan Perubahan'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Add Role Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-md">
            <div className="p-6 border-b border-red-900/30 flex justify-between items-center">
              <h2 className="text-xl font-bold">Tambah Role Baru</h2>
              <button onClick={() => setShowAddModal(false)} className="text-gray-400 hover:text-white"><X className="h-6 w-6" /></button>
            </div>
            
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Kode Role *</label>
                <input type="text" value={newRole.code} onChange={(e) => setNewRole({ ...newRole, code: e.target.value.toLowerCase().replace(/[^a-z0-9_]/g, '') })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" placeholder="contoh: marketing" />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Nama Role *</label>
                <input type="text" value={newRole.name} onChange={(e) => setNewRole({ ...newRole, name: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" placeholder="contoh: Marketing" />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Deskripsi</label>
                <textarea value={newRole.description} onChange={(e) => setNewRole({ ...newRole, description: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" rows={2} placeholder="Deskripsi role" />
              </div>
            </div>
            
            <div className="p-6 border-t border-red-900/30 flex gap-3">
              <button onClick={() => setShowAddModal(false)} className="flex-1 py-2 border border-red-900/30 rounded-lg hover:bg-red-900/20">Batal</button>
              <button onClick={handleAddRole} disabled={saving} className="flex-1 py-2 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg disabled:opacity-50 flex items-center justify-center gap-2">
                {saving ? <Loader2 className="h-5 w-5 animate-spin" /> : <Plus className="h-5 w-5" />}
                {saving ? 'Menyimpan...' : 'Tambah Role'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RolePermission;
