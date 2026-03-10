import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { toast } from 'sonner';
import { 
  Shield, Users, Key, History, ChevronRight, Check, X, Save,
  Plus, Trash2, Edit, Search, Filter, RefreshCw, Building2,
  Eye, FileEdit, Printer, Download, Lock, Percent, CheckSquare
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Action icons mapping
const ACTION_ICONS = {
  view: Eye,
  create: Plus,
  edit: FileEdit,
  delete: Trash2,
  approve: CheckSquare,
  export: Download,
  print: Printer,
  lock_number: Lock,
  lock_date: Lock,
  override_price: Percent,
  override_discount: Percent
};

// Action labels in Indonesian
const ACTION_LABELS = {
  view: 'Lihat',
  create: 'Tambah',
  edit: 'Edit',
  delete: 'Hapus',
  approve: 'Approve',
  export: 'Export',
  print: 'Cetak',
  lock_number: 'Kunci No',
  lock_date: 'Kunci Tgl',
  override_price: 'Ubah Harga',
  override_discount: 'Ubah Diskon'
};

// Category labels
const CATEGORY_LABELS = {
  master_data: 'Master Data',
  pembelian: 'Pembelian',
  penjualan: 'Penjualan',
  persediaan: 'Persediaan',
  akuntansi: 'Akuntansi',
  laporan: 'Laporan',
  pengaturan: 'Pengaturan',
  menu: 'Visibilitas Menu',
  ai: 'AI Modules',
  hr: 'HR & Payroll'
};

export default function RBACManagement() {
  const { token } = useAuth();
  const [activeTab, setActiveTab] = useState('roles');
  const [roles, setRoles] = useState([]);
  const [selectedRole, setSelectedRole] = useState(null);
  const [permissionMatrix, setPermissionMatrix] = useState([]);
  const [actions, setActions] = useState([]);
  const [categories, setCategories] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [searchModule, setSearchModule] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [pendingChanges, setPendingChanges] = useState({});
  
  // Users for role assignment
  const [users, setUsers] = useState([]);
  const [branches, setBranches] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [userRoleForm, setUserRoleForm] = useState({ role_id: '', branch_access: [], all_branches: false });
  
  // Audit logs
  const [auditLogs, setAuditLogs] = useState([]);
  const [logFilters, setLogFilters] = useState({ user_id: '', module: '', action: '' });

  // Fetch roles
  const fetchRoles = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/rbac/roles`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      setRoles(data.roles || []);
      if (data.roles?.length > 0 && !selectedRole) {
        setSelectedRole(data.roles[0]);
      }
    } catch (err) {
      toast.error('Gagal memuat roles');
    }
  }, [token, selectedRole]);

  // Fetch modules/permissions structure
  const fetchModules = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/rbac/permissions/modules`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      setActions(data.actions || []);
      setCategories(data.categories || {});
    } catch (err) {
      toast.error('Gagal memuat modules');
    }
  }, [token]);

  // Fetch permission matrix for selected role
  const fetchPermissionMatrix = useCallback(async (roleId) => {
    if (!roleId) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/rbac/permissions/matrix/${roleId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      setPermissionMatrix(data.matrix || []);
      setPendingChanges({});
    } catch (err) {
      toast.error('Gagal memuat permission matrix');
    } finally {
      setLoading(false);
    }
  }, [token]);

  // Fetch users
  const fetchUsers = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/users`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      // API returns {items: [], total: n} format
      const usersList = data.items || data.users || data || [];
      setUsers(Array.isArray(usersList) ? usersList : []);
    } catch (err) {
      console.error('Failed to fetch users');
      setUsers([]);
    }
  }, [token]);

  // Fetch branches
  const fetchBranches = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/global-map/branches`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      setBranches(data.branches || []);
    } catch (err) {
      console.error('Failed to fetch branches');
    }
  }, [token]);

  // Fetch audit logs
  const fetchAuditLogs = useCallback(async () => {
    try {
      const params = new URLSearchParams();
      if (logFilters.user_id) params.append('user_id', logFilters.user_id);
      if (logFilters.module) params.append('module', logFilters.module);
      if (logFilters.action) params.append('action', logFilters.action);
      params.append('limit', '100');
      
      const res = await fetch(`${API_URL}/api/rbac/audit-logs?${params}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      setAuditLogs(data.logs || []);
    } catch (err) {
      console.error('Failed to fetch audit logs');
    }
  }, [token, logFilters]);

  useEffect(() => {
    fetchRoles();
    fetchModules();
    fetchUsers();
    fetchBranches();
  }, [fetchRoles, fetchModules, fetchUsers, fetchBranches]);

  useEffect(() => {
    if (selectedRole) {
      fetchPermissionMatrix(selectedRole.id);
    }
  }, [selectedRole, fetchPermissionMatrix]);

  useEffect(() => {
    if (activeTab === 'audit') {
      fetchAuditLogs();
    }
  }, [activeTab, fetchAuditLogs]);

  // Handle permission toggle
  const handlePermissionToggle = (module, action, currentValue) => {
    const key = `${module}_${action}`;
    const newValue = !currentValue;
    
    setPendingChanges(prev => ({
      ...prev,
      [key]: { module, action, allowed: newValue }
    }));
    
    // Update local matrix for immediate UI feedback
    setPermissionMatrix(prev => prev.map(m => {
      if (m.module === module) {
        return {
          ...m,
          permissions: { ...m.permissions, [action]: newValue }
        };
      }
      return m;
    }));
  };

  // Save permissions
  const savePermissions = async () => {
    if (Object.keys(pendingChanges).length === 0) {
      toast.info('Tidak ada perubahan untuk disimpan');
      return;
    }
    
    setSaving(true);
    try {
      const permissions = Object.values(pendingChanges);
      const res = await fetch(`${API_URL}/api/rbac/permissions/${selectedRole.id}`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ permissions })
      });
      
      if (res.ok) {
        toast.success(`${permissions.length} permission berhasil disimpan`);
        setPendingChanges({});
      } else {
        throw new Error('Failed to save');
      }
    } catch (err) {
      toast.error('Gagal menyimpan permissions');
    } finally {
      setSaving(false);
    }
  };

  // Bulk operations
  const bulkUpdatePermissions = async (action, category = '') => {
    setSaving(true);
    try {
      const params = new URLSearchParams({ action });
      if (category) params.append('category', category);
      
      const res = await fetch(`${API_URL}/api/rbac/permissions/${selectedRole.id}/bulk?${params}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (res.ok) {
        toast.success(action === 'set_all' ? 'Semua permission diaktifkan' : 'Semua permission dinonaktifkan');
        fetchPermissionMatrix(selectedRole.id);
      }
    } catch (err) {
      toast.error('Gagal update bulk permissions');
    } finally {
      setSaving(false);
    }
  };

  // Assign role to user
  const assignRoleToUser = async () => {
    if (!selectedUser || !userRoleForm.role_id) {
      toast.error('Pilih user dan role');
      return;
    }
    
    try {
      const res = await fetch(`${API_URL}/api/rbac/user/${selectedUser.id}/role`, {
        method: 'PUT',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(userRoleForm)
      });
      
      if (res.ok) {
        toast.success('Role berhasil di-assign');
        fetchUsers();
        setSelectedUser(null);
        setUserRoleForm({ role_id: '', branch_access: [], all_branches: false });
      }
    } catch (err) {
      toast.error('Gagal assign role');
    }
  };

  // Filter matrix by category and search
  const filteredMatrix = permissionMatrix.filter(m => {
    const matchSearch = !searchModule || 
      m.name.toLowerCase().includes(searchModule.toLowerCase()) ||
      m.module.toLowerCase().includes(searchModule.toLowerCase());
    const matchCategory = !selectedCategory || m.category === selectedCategory;
    return matchSearch && matchCategory;
  });

  // Group by category
  const groupedMatrix = {};
  filteredMatrix.forEach(m => {
    const cat = m.category;
    if (!groupedMatrix[cat]) groupedMatrix[cat] = [];
    groupedMatrix[cat].push(m);
  });

  return (
    <div className="p-6 bg-[#0a0a0a] min-h-screen">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Shield className="w-7 h-7 text-red-500" />
            RBAC Management
          </h1>
          <p className="text-gray-400 mt-1">Role-Based Access Control System</p>
        </div>
        
        {/* Tab Navigation */}
        <div className="flex gap-2 bg-[#1a1a1a] p-1 rounded-lg">
          {[
            { id: 'roles', label: 'Permission Matrix', icon: Key },
            { id: 'users', label: 'Assign Role', icon: Users },
            { id: 'audit', label: 'Audit Log', icon: History }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${
                activeTab === tab.id 
                  ? 'bg-red-600 text-white' 
                  : 'text-gray-400 hover:bg-[#2a2a2a]'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === 'roles' && (
        <div className="flex gap-6">
          {/* Role List Panel */}
          <div className="w-64 bg-[#111] border border-[#222] rounded-xl p-4">
            <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
              <Shield className="w-4 h-4 text-red-500" />
              Daftar Role
            </h3>
            <div className="space-y-2">
              {roles.map(role => (
                <button
                  key={role.id}
                  onClick={() => setSelectedRole(role)}
                  className={`w-full text-left px-3 py-2 rounded-lg transition-all flex items-center justify-between ${
                    selectedRole?.id === role.id
                      ? 'bg-red-600/20 border border-red-600 text-white'
                      : 'bg-[#1a1a1a] text-gray-300 hover:bg-[#222] border border-transparent'
                  }`}
                >
                  <div>
                    <div className="font-medium">{role.name}</div>
                    <div className="text-xs text-gray-500">Level {role.level}</div>
                  </div>
                  {selectedRole?.id === role.id && <ChevronRight className="w-4 h-4" />}
                </button>
              ))}
            </div>
            
            {selectedRole && (
              <div className="mt-4 pt-4 border-t border-[#333]">
                <div className="text-xs text-gray-500 mb-2">Quick Actions</div>
                <div className="flex gap-2">
                  <button
                    onClick={() => bulkUpdatePermissions('set_all')}
                    disabled={saving}
                    className="flex-1 px-2 py-1.5 bg-green-600/20 text-green-400 text-xs rounded hover:bg-green-600/30"
                  >
                    Aktifkan Semua
                  </button>
                  <button
                    onClick={() => bulkUpdatePermissions('clear_all')}
                    disabled={saving}
                    className="flex-1 px-2 py-1.5 bg-red-600/20 text-red-400 text-xs rounded hover:bg-red-600/30"
                  >
                    Nonaktifkan Semua
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Permission Matrix */}
          <div className="flex-1 bg-[#111] border border-[#222] rounded-xl overflow-hidden">
            {/* Matrix Header */}
            <div className="p-4 border-b border-[#222] bg-[#0d0d0d]">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-white font-semibold">
                    Permission Matrix: {selectedRole?.name || 'Pilih Role'}
                  </h3>
                  {selectedRole?.description && (
                    <p className="text-sm text-gray-500">{selectedRole.description}</p>
                  )}
                </div>
                <div className="flex items-center gap-3">
                  {/* Search */}
                  <div className="relative">
                    <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
                    <input
                      type="text"
                      placeholder="Cari modul..."
                      value={searchModule}
                      onChange={e => setSearchModule(e.target.value)}
                      className="pl-9 pr-4 py-2 bg-[#1a1a1a] border border-[#333] rounded-lg text-white text-sm w-48"
                    />
                  </div>
                  
                  {/* Category Filter */}
                  <select
                    value={selectedCategory}
                    onChange={e => setSelectedCategory(e.target.value)}
                    className="px-3 py-2 bg-[#1a1a1a] border border-[#333] rounded-lg text-white text-sm"
                  >
                    <option value="">Semua Kategori</option>
                    {Object.entries(CATEGORY_LABELS).map(([key, label]) => (
                      <option key={key} value={key}>{label}</option>
                    ))}
                  </select>
                  
                  {/* Save Button */}
                  <button
                    onClick={savePermissions}
                    disabled={saving || Object.keys(pendingChanges).length === 0}
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ${
                      Object.keys(pendingChanges).length > 0
                        ? 'bg-red-600 text-white hover:bg-red-700'
                        : 'bg-[#333] text-gray-500 cursor-not-allowed'
                    }`}
                  >
                    <Save className="w-4 h-4" />
                    {saving ? 'Menyimpan...' : `Simpan (${Object.keys(pendingChanges).length})`}
                  </button>
                </div>
              </div>
            </div>

            {/* Matrix Table */}
            <div className="overflow-auto max-h-[calc(100vh-280px)]">
              {loading ? (
                <div className="flex items-center justify-center h-64">
                  <RefreshCw className="w-8 h-8 text-red-500 animate-spin" />
                </div>
              ) : (
                <table className="w-full">
                  <thead className="bg-[#0d0d0d] sticky top-0 z-10">
                    <tr>
                      <th className="text-left p-3 text-gray-400 font-medium border-b border-[#222] min-w-[200px]">
                        Menu / Modul
                      </th>
                      {actions.slice(0, 7).map(action => {
                        const Icon = ACTION_ICONS[action] || Eye;
                        return (
                          <th key={action} className="p-3 text-center border-b border-[#222] min-w-[80px]">
                            <div className="flex flex-col items-center gap-1">
                              <Icon className="w-4 h-4 text-gray-500" />
                              <span className="text-xs text-gray-400">{ACTION_LABELS[action]}</span>
                            </div>
                          </th>
                        );
                      })}
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(groupedMatrix).map(([category, modules]) => (
                      <React.Fragment key={category}>
                        {/* Category Header */}
                        <tr className="bg-[#1a1a1a]">
                          <td colSpan={8} className="px-3 py-2 text-red-400 font-semibold text-sm border-b border-[#222]">
                            {CATEGORY_LABELS[category] || category}
                          </td>
                        </tr>
                        {/* Modules */}
                        {modules.map(module => (
                          <tr key={module.module} className="hover:bg-[#151515] transition-colors">
                            <td className="p-3 text-white border-b border-[#1a1a1a]">
                              {module.name}
                            </td>
                            {actions.slice(0, 7).map(action => {
                              const isAllowed = module.permissions[action];
                              const isPending = pendingChanges[`${module.module}_${action}`] !== undefined;
                              return (
                                <td key={action} className="p-3 text-center border-b border-[#1a1a1a]">
                                  <button
                                    onClick={() => handlePermissionToggle(module.module, action, isAllowed)}
                                    className={`w-8 h-8 rounded-lg flex items-center justify-center transition-all ${
                                      isAllowed
                                        ? 'bg-green-600/20 text-green-400 hover:bg-green-600/30'
                                        : 'bg-[#222] text-gray-600 hover:bg-[#333]'
                                    } ${isPending ? 'ring-2 ring-yellow-500' : ''}`}
                                  >
                                    {isAllowed ? <Check className="w-4 h-4" /> : <X className="w-4 h-4" />}
                                  </button>
                                </td>
                              );
                            })}
                          </tr>
                        ))}
                      </React.Fragment>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'users' && (
        <div className="grid grid-cols-2 gap-6">
          {/* User List */}
          <div className="bg-[#111] border border-[#222] rounded-xl p-4">
            <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
              <Users className="w-4 h-4 text-red-500" />
              Daftar User
            </h3>
            <div className="space-y-2 max-h-[500px] overflow-auto">
              {users.map(user => (
                <button
                  key={user.id}
                  onClick={() => {
                    setSelectedUser(user);
                    setUserRoleForm({
                      role_id: user.role_id || '',
                      branch_access: user.branch_access || [],
                      all_branches: false
                    });
                  }}
                  className={`w-full text-left p-3 rounded-lg transition-all ${
                    selectedUser?.id === user.id
                      ? 'bg-red-600/20 border border-red-600'
                      : 'bg-[#1a1a1a] border border-transparent hover:bg-[#222]'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-white font-medium">{user.name}</div>
                      <div className="text-sm text-gray-500">{user.email}</div>
                    </div>
                    <div className="text-right">
                      <div className={`text-xs px-2 py-1 rounded ${
                        user.role_name ? 'bg-green-600/20 text-green-400' : 'bg-yellow-600/20 text-yellow-400'
                      }`}>
                        {user.role_name || 'No Role'}
                      </div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Role Assignment Form */}
          <div className="bg-[#111] border border-[#222] rounded-xl p-4">
            <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
              <Key className="w-4 h-4 text-red-500" />
              Assign Role
            </h3>
            
            {selectedUser ? (
              <div className="space-y-4">
                <div className="p-3 bg-[#1a1a1a] rounded-lg">
                  <div className="text-white font-medium">{selectedUser.name}</div>
                  <div className="text-sm text-gray-500">{selectedUser.email}</div>
                </div>

                {/* Role Selection */}
                <div>
                  <label className="block text-gray-400 text-sm mb-2">Pilih Role</label>
                  <select
                    value={userRoleForm.role_id}
                    onChange={e => setUserRoleForm(prev => ({ ...prev, role_id: e.target.value }))}
                    className="w-full px-3 py-2 bg-[#1a1a1a] border border-[#333] rounded-lg text-white"
                  >
                    <option value="">-- Pilih Role --</option>
                    {roles.map(role => (
                      <option key={role.id} value={role.id}>{role.name}</option>
                    ))}
                  </select>
                </div>

                {/* Branch Access */}
                <div>
                  <label className="block text-gray-400 text-sm mb-2">Akses Cabang</label>
                  <label className="flex items-center gap-2 mb-3">
                    <input
                      type="checkbox"
                      checked={userRoleForm.all_branches}
                      onChange={e => setUserRoleForm(prev => ({
                        ...prev,
                        all_branches: e.target.checked,
                        branch_access: e.target.checked ? [] : prev.branch_access
                      }))}
                      className="w-4 h-4 rounded bg-[#1a1a1a] border-[#333]"
                    />
                    <span className="text-white">Akses Semua Cabang</span>
                  </label>
                  
                  {!userRoleForm.all_branches && (
                    <div className="max-h-48 overflow-auto space-y-1 bg-[#1a1a1a] p-3 rounded-lg">
                      {branches.map(branch => (
                        <label key={branch.id} className="flex items-center gap-2">
                          <input
                            type="checkbox"
                            checked={userRoleForm.branch_access.includes(branch.id)}
                            onChange={e => {
                              if (e.target.checked) {
                                setUserRoleForm(prev => ({
                                  ...prev,
                                  branch_access: [...prev.branch_access, branch.id]
                                }));
                              } else {
                                setUserRoleForm(prev => ({
                                  ...prev,
                                  branch_access: prev.branch_access.filter(id => id !== branch.id)
                                }));
                              }
                            }}
                            className="w-4 h-4 rounded bg-[#0a0a0a] border-[#333]"
                          />
                          <span className="text-gray-300 text-sm">{branch.name}</span>
                        </label>
                      ))}
                    </div>
                  )}
                </div>

                <button
                  onClick={assignRoleToUser}
                  disabled={!userRoleForm.role_id}
                  className="w-full py-3 bg-red-600 text-white font-medium rounded-lg hover:bg-red-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  <Save className="w-4 h-4" />
                  Simpan Role
                </button>
              </div>
            ) : (
              <div className="text-center py-12 text-gray-500">
                <Users className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>Pilih user dari daftar untuk assign role</p>
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === 'audit' && (
        <div className="bg-[#111] border border-[#222] rounded-xl overflow-hidden">
          {/* Audit Header */}
          <div className="p-4 border-b border-[#222] bg-[#0d0d0d]">
            <div className="flex items-center justify-between">
              <h3 className="text-white font-semibold flex items-center gap-2">
                <History className="w-4 h-4 text-red-500" />
                Audit Log
              </h3>
              <div className="flex items-center gap-3">
                <select
                  value={logFilters.action}
                  onChange={e => setLogFilters(prev => ({ ...prev, action: e.target.value }))}
                  className="px-3 py-2 bg-[#1a1a1a] border border-[#333] rounded-lg text-white text-sm"
                >
                  <option value="">Semua Aksi</option>
                  <option value="create">Create</option>
                  <option value="edit">Edit</option>
                  <option value="delete">Delete</option>
                  <option value="login">Login</option>
                </select>
                <button
                  onClick={fetchAuditLogs}
                  className="px-4 py-2 bg-[#1a1a1a] border border-[#333] rounded-lg text-white hover:bg-[#222]"
                >
                  <RefreshCw className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>

          {/* Audit Table */}
          <div className="overflow-auto max-h-[500px]">
            <table className="w-full">
              <thead className="bg-[#0d0d0d] sticky top-0">
                <tr>
                  <th className="text-left p-3 text-gray-400 font-medium border-b border-[#222]">Waktu</th>
                  <th className="text-left p-3 text-gray-400 font-medium border-b border-[#222]">User</th>
                  <th className="text-left p-3 text-gray-400 font-medium border-b border-[#222]">Aksi</th>
                  <th className="text-left p-3 text-gray-400 font-medium border-b border-[#222]">Modul</th>
                  <th className="text-left p-3 text-gray-400 font-medium border-b border-[#222]">Deskripsi</th>
                  <th className="text-left p-3 text-gray-400 font-medium border-b border-[#222]">IP</th>
                </tr>
              </thead>
              <tbody>
                {auditLogs.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="text-center py-12 text-gray-500">
                      Belum ada log aktivitas
                    </td>
                  </tr>
                ) : (
                  auditLogs.map(log => (
                    <tr key={log.id} className="hover:bg-[#151515]">
                      <td className="p-3 text-gray-400 text-sm border-b border-[#1a1a1a]">
                        {new Date(log.created_at).toLocaleString('id-ID')}
                      </td>
                      <td className="p-3 text-white border-b border-[#1a1a1a]">{log.user_name}</td>
                      <td className="p-3 border-b border-[#1a1a1a]">
                        <span className={`px-2 py-1 rounded text-xs ${
                          log.action === 'create' ? 'bg-green-600/20 text-green-400' :
                          log.action === 'edit' ? 'bg-blue-600/20 text-blue-400' :
                          log.action === 'delete' ? 'bg-red-600/20 text-red-400' :
                          'bg-gray-600/20 text-gray-400'
                        }`}>
                          {log.action}
                        </span>
                      </td>
                      <td className="p-3 text-gray-300 border-b border-[#1a1a1a]">{log.module}</td>
                      <td className="p-3 text-gray-400 text-sm border-b border-[#1a1a1a]">{log.description}</td>
                      <td className="p-3 text-gray-500 text-sm border-b border-[#1a1a1a]">{log.ip_address || '-'}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
