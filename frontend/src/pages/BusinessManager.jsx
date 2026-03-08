import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Building2, Plus, Loader2, Edit, Trash2, CheckCircle, Database, RefreshCw, Store, Shirt, Smartphone, Coffee, ShoppingBag, Briefcase, Copy, Package, Users, FileText, Settings } from 'lucide-react';
import { toast } from 'sonner';

const BusinessManager = () => {
  const { api, logout } = useAuth();
  const [businesses, setBusinesses] = useState([]);
  const [currentDb, setCurrentDb] = useState('');
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showCloneModal, setShowCloneModal] = useState(false);
  const [cloneSource, setCloneSource] = useState(null);
  const [cloning, setCloning] = useState(false);
  const [switching, setSwitching] = useState(null);
  
  const [formData, setFormData] = useState({
    id: '',
    name: '',
    db_name: '',
    description: '',
    icon: 'store',
    color: '#991B1B'
  });

  const [cloneData, setCloneData] = useState({
    target_name: '',
    target_db_name: '',
    target_description: '',
    target_icon: 'store',
    target_color: '#991B1B',
    clone_products: true,
    clone_categories: true,
    clone_suppliers: true,
    clone_customers: true,
    clone_coa: true,
    clone_settings: true,
    create_admin_user: true,
    admin_email: '',
    admin_password: ''
  });

  const icons = [
    { id: 'store', icon: Store, label: 'Toko' },
    { id: 'building', icon: Building2, label: 'Gedung' },
    { id: 'shirt', icon: Shirt, label: 'Fashion' },
    { id: 'smartphone', icon: Smartphone, label: 'Counter' },
    { id: 'coffee', icon: Coffee, label: 'F&B' },
    { id: 'shopping', icon: ShoppingBag, label: 'Retail' },
    { id: 'briefcase', icon: Briefcase, label: 'Kantor' },
  ];

  const colors = [
    '#991B1B', // Red
    '#1E40AF', // Blue
    '#065F46', // Green
    '#7C2D12', // Orange
    '#5B21B6', // Purple
    '#0F766E', // Teal
    '#78350F', // Amber
    '#374151', // Gray
  ];

  useEffect(() => {
    loadBusinesses();
  }, []);

  const loadBusinesses = async () => {
    setLoading(true);
    try {
      const res = await api('/api/business/list');
      if (res.ok) {
        const data = await res.json();
        setBusinesses(data.businesses || []);
        setCurrentDb(data.current_db || '');
      }
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  const createBusiness = async () => {
    if (!formData.name || !formData.db_name) {
      toast.error('Nama dan Database wajib diisi');
      return;
    }
    
    // Generate ID from name
    const id = formData.db_name.toLowerCase().replace(/[^a-z0-9]/g, '_');
    
    try {
      const res = await api('/api/business/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...formData, id })
      });
      
      if (res.ok) {
        toast.success('Bisnis baru berhasil dibuat');
        setShowAddModal(false);
        setFormData({ id: '', name: '', db_name: '', description: '', icon: 'store', color: '#991B1B' });
        loadBusinesses();
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Gagal membuat bisnis');
      }
    } catch (err) { toast.error('Gagal membuat bisnis'); }
  };

  const switchBusiness = async (dbName, businessName) => {
    if (dbName === currentDb) {
      toast.info('Anda sudah di bisnis ini');
      return;
    }
    
    if (!window.confirm(`Switch ke bisnis "${businessName}"?\n\nAnda akan logout dan perlu login ulang.`)) {
      return;
    }
    
    setSwitching(dbName);
    try {
      const res = await api(`/api/business/switch/${dbName}`, { method: 'POST' });
      
      if (res.ok) {
        toast.success(`Berhasil switch ke ${businessName}. Silakan login ulang...`);
        // Wait a moment then logout
        setTimeout(() => {
          logout();
          window.location.reload();
        }, 1500);
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Gagal switch bisnis');
        setSwitching(null);
      }
    } catch (err) { 
      toast.error('Gagal switch bisnis'); 
      setSwitching(null);
    }
  };

  const deleteBusiness = async (id, name) => {
    if (!window.confirm(`Hapus bisnis "${name}" dari daftar?\n\nNote: Database tidak akan dihapus, hanya entri dari daftar.`)) {
      return;
    }
    
    try {
      const res = await api(`/api/business/${id}`, { method: 'DELETE' });
      if (res.ok) {
        toast.success('Bisnis dihapus dari daftar');
        loadBusinesses();
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Gagal menghapus');
      }
    } catch (err) { toast.error('Gagal menghapus'); }
  };

  const openCloneModal = (business) => {
    setCloneSource(business);
    setCloneData({
      target_name: '',
      target_db_name: '',
      target_description: '',
      target_icon: business.icon || 'store',
      target_color: business.color || '#991B1B',
      clone_products: true,
      clone_categories: true,
      clone_suppliers: true,
      clone_customers: true,
      clone_coa: true,
      clone_settings: true,
      create_admin_user: true,
      admin_email: '',
      admin_password: ''
    });
    setShowCloneModal(true);
  };

  const cloneBusiness = async () => {
    if (!cloneData.target_name || !cloneData.target_db_name) {
      toast.error('Nama dan Database target wajib diisi');
      return;
    }
    
    if (cloneData.create_admin_user && (!cloneData.admin_email || !cloneData.admin_password)) {
      toast.error('Email dan password admin wajib diisi');
      return;
    }
    
    setCloning(true);
    try {
      const res = await api('/api/business/clone', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source_db: cloneSource.db_name,
          ...cloneData
        })
      });
      
      if (res.ok) {
        const data = await res.json();
        toast.success(`Bisnis berhasil di-clone! Data: ${Object.entries(data.cloned_data || {}).map(([k,v]) => `${k}: ${v}`).join(', ')}`);
        setShowCloneModal(false);
        setCloneSource(null);
        loadBusinesses();
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Gagal clone bisnis');
      }
    } catch (err) { 
      toast.error('Gagal clone bisnis'); 
    } finally {
      setCloning(false);
    }
  };

  const getIconComponent = (iconId) => {
    const found = icons.find(i => i.id === iconId);
    return found ? found.icon : Store;
  };

  return (
    <div className="space-y-6" data-testid="business-manager-page">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Kelola Bisnis</h1>
          <p className="text-gray-400">Pisahkan database untuk setiap bisnis Anda</p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="px-4 py-2 bg-green-600/20 text-green-400 rounded-lg hover:bg-green-600/30 flex items-center gap-2"
        >
          <Plus className="h-4 w-4" /> Tambah Bisnis Baru
        </button>
      </div>

      {/* Info Box */}
      <div className="p-4 bg-blue-900/20 border border-blue-700/30 rounded-xl">
        <div className="flex items-start gap-3">
          <Database className="h-5 w-5 text-blue-400 mt-0.5" />
          <div>
            <p className="text-blue-400 font-medium">Tentang Multi-Bisnis</p>
            <p className="text-sm text-gray-400 mt-1">
              Setiap bisnis memiliki database terpisah. Data tidak akan tercampur antara bisnis satu dengan lainnya.
              Contoh: Toko Baju dan Counter HP bisa dikelola dalam satu aplikasi tapi data terpisah.
            </p>
          </div>
        </div>
      </div>

      {/* Business List */}
      {loading ? (
        <div className="text-center py-12">
          <Loader2 className="h-8 w-8 animate-spin mx-auto text-amber-400" />
          <p className="text-gray-400 mt-2">Memuat daftar bisnis...</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {businesses.map((business) => {
            const IconComp = getIconComponent(business.icon);
            const isActive = business.db_name === currentDb;
            const isSwitching = switching === business.db_name;
            
            return (
              <div 
                key={business.id} 
                className={`relative bg-[#1a1214] border rounded-xl p-5 transition-all ${
                  isActive ? 'border-green-500/50 ring-2 ring-green-500/20' : 'border-red-900/30 hover:border-red-900/50'
                }`}
              >
                {isActive && (
                  <div className="absolute -top-2 -right-2 bg-green-600 text-white text-xs px-2 py-1 rounded-full flex items-center gap-1">
                    <CheckCircle className="h-3 w-3" /> Aktif
                  </div>
                )}
                
                <div className="flex items-start gap-4">
                  <div 
                    className="p-3 rounded-xl"
                    style={{ backgroundColor: `${business.color}20` }}
                  >
                    <IconComp className="h-8 w-8" style={{ color: business.color }} />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-lg text-amber-100">{business.name}</h3>
                    <p className="text-sm text-gray-400 mt-1">{business.description || 'Tidak ada deskripsi'}</p>
                    <div className="mt-2 flex items-center gap-2 text-xs text-gray-500">
                      <Database className="h-3 w-3" />
                      <code className="bg-[#0a0608] px-2 py-0.5 rounded">{business.db_name}</code>
                    </div>
                  </div>
                </div>

                <div className="mt-4 pt-4 border-t border-red-900/20 flex gap-2">
                  {!isActive ? (
                    <button
                      onClick={() => switchBusiness(business.db_name, business.name)}
                      disabled={isSwitching}
                      className="flex-1 px-3 py-2 bg-amber-600/20 text-amber-400 rounded-lg hover:bg-amber-600/30 flex items-center justify-center gap-2 disabled:opacity-50"
                    >
                      {isSwitching ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <RefreshCw className="h-4 w-4" />
                      )}
                      {isSwitching ? 'Switching...' : 'Gunakan Bisnis Ini'}
                    </button>
                  ) : (
                    <div className="flex-1 px-3 py-2 bg-green-600/10 text-green-400 rounded-lg text-center text-sm">
                      Sedang Digunakan
                    </div>
                  )}
                  
                  <button
                    onClick={() => openCloneModal(business)}
                    className="p-2 text-blue-400 hover:bg-blue-600/20 rounded-lg"
                    title="Clone bisnis ini"
                  >
                    <Copy className="h-4 w-4" />
                  </button>
                  
                  {business.id !== 'default' && (
                    <button
                      onClick={() => deleteBusiness(business.id, business.name)}
                      className="p-2 text-red-400 hover:bg-red-600/20 rounded-lg"
                      title="Hapus dari daftar"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Add Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-6 w-[500px]">
            <h2 className="text-xl font-bold text-amber-100 mb-4">Tambah Bisnis Baru</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Nama Bisnis *</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg"
                  placeholder="Toko Baju Kita"
                />
              </div>
              
              <div>
                <label className="block text-sm text-gray-400 mb-1">Nama Database *</label>
                <input
                  type="text"
                  value={formData.db_name}
                  onChange={(e) => setFormData({ ...formData, db_name: e.target.value.toLowerCase().replace(/[^a-z0-9_]/g, '_') })}
                  className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg font-mono"
                  placeholder="toko_baju"
                />
                <p className="text-xs text-gray-500 mt-1">Hanya huruf kecil, angka, dan underscore</p>
              </div>
              
              <div>
                <label className="block text-sm text-gray-400 mb-1">Deskripsi</label>
                <input
                  type="text"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg"
                  placeholder="Bisnis fashion retail"
                />
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-2">Ikon</label>
                <div className="flex gap-2 flex-wrap">
                  {icons.map((icon) => (
                    <button
                      key={icon.id}
                      onClick={() => setFormData({ ...formData, icon: icon.id })}
                      className={`p-3 rounded-lg border transition-all ${
                        formData.icon === icon.id 
                          ? 'border-amber-500 bg-amber-500/20' 
                          : 'border-red-900/30 hover:border-red-900/50'
                      }`}
                      title={icon.label}
                    >
                      <icon.icon className="h-5 w-5" />
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-2">Warna</label>
                <div className="flex gap-2">
                  {colors.map((color) => (
                    <button
                      key={color}
                      onClick={() => setFormData({ ...formData, color })}
                      className={`w-8 h-8 rounded-full border-2 transition-all ${
                        formData.color === color ? 'border-white scale-110' : 'border-transparent'
                      }`}
                      style={{ backgroundColor: color }}
                    />
                  ))}
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-2 mt-6">
              <button 
                onClick={() => setShowAddModal(false)} 
                className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
              >
                Batal
              </button>
              <button 
                onClick={createBusiness} 
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
              >
                Buat Bisnis
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Clone Modal */}
      {showCloneModal && cloneSource && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-6 w-[600px] max-h-[90vh] overflow-y-auto">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-blue-600/20 rounded-lg">
                <Copy className="h-5 w-5 text-blue-400" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-amber-100">Clone Bisnis</h2>
                <p className="text-sm text-gray-400">Dari: <span className="text-amber-400">{cloneSource.name}</span></p>
              </div>
            </div>
            
            <div className="space-y-4">
              {/* Target Business Info */}
              <div className="p-4 bg-[#0a0608] rounded-lg space-y-3">
                <h3 className="font-medium text-amber-100 flex items-center gap-2">
                  <Building2 className="h-4 w-4" /> Info Bisnis Baru
                </h3>
                
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs text-gray-400 mb-1">Nama Bisnis *</label>
                    <input
                      type="text"
                      value={cloneData.target_name}
                      onChange={(e) => setCloneData({ ...cloneData, target_name: e.target.value })}
                      className="w-full px-3 py-2 bg-[#1a1214] border border-red-900/30 rounded-lg text-sm"
                      placeholder="Toko Baru"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-400 mb-1">Nama Database *</label>
                    <input
                      type="text"
                      value={cloneData.target_db_name}
                      onChange={(e) => setCloneData({ ...cloneData, target_db_name: e.target.value.toLowerCase().replace(/[^a-z0-9_]/g, '_') })}
                      className="w-full px-3 py-2 bg-[#1a1214] border border-red-900/30 rounded-lg text-sm font-mono"
                      placeholder="toko_baru"
                    />
                  </div>
                </div>
                
                <div>
                  <label className="block text-xs text-gray-400 mb-1">Deskripsi</label>
                  <input
                    type="text"
                    value={cloneData.target_description}
                    onChange={(e) => setCloneData({ ...cloneData, target_description: e.target.value })}
                    className="w-full px-3 py-2 bg-[#1a1214] border border-red-900/30 rounded-lg text-sm"
                    placeholder="Cabang baru dari..."
                  />
                </div>

                <div className="flex gap-4">
                  <div className="flex-1">
                    <label className="block text-xs text-gray-400 mb-2">Ikon</label>
                    <div className="flex gap-1 flex-wrap">
                      {icons.map((icon) => (
                        <button
                          key={icon.id}
                          onClick={() => setCloneData({ ...cloneData, target_icon: icon.id })}
                          className={`p-2 rounded border transition-all ${
                            cloneData.target_icon === icon.id 
                              ? 'border-amber-500 bg-amber-500/20' 
                              : 'border-red-900/30'
                          }`}
                        >
                          <icon.icon className="h-4 w-4" />
                        </button>
                      ))}
                    </div>
                  </div>
                  <div className="flex-1">
                    <label className="block text-xs text-gray-400 mb-2">Warna</label>
                    <div className="flex gap-1">
                      {colors.map((color) => (
                        <button
                          key={color}
                          onClick={() => setCloneData({ ...cloneData, target_color: color })}
                          className={`w-6 h-6 rounded-full border-2 ${
                            cloneData.target_color === color ? 'border-white' : 'border-transparent'
                          }`}
                          style={{ backgroundColor: color }}
                        />
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* Data to Clone */}
              <div className="p-4 bg-[#0a0608] rounded-lg space-y-3">
                <h3 className="font-medium text-amber-100 flex items-center gap-2">
                  <Database className="h-4 w-4" /> Data yang Di-clone
                </h3>
                
                <div className="grid grid-cols-2 gap-2">
                  <label className="flex items-center gap-2 p-2 rounded hover:bg-[#1a1214] cursor-pointer">
                    <input 
                      type="checkbox" 
                      checked={cloneData.clone_categories}
                      onChange={(e) => setCloneData({ ...cloneData, clone_categories: e.target.checked })}
                      className="rounded border-gray-600"
                    />
                    <Package className="h-4 w-4 text-blue-400" />
                    <span className="text-sm">Kategori</span>
                  </label>
                  
                  <label className="flex items-center gap-2 p-2 rounded hover:bg-[#1a1214] cursor-pointer">
                    <input 
                      type="checkbox" 
                      checked={cloneData.clone_products}
                      onChange={(e) => setCloneData({ ...cloneData, clone_products: e.target.checked })}
                      className="rounded border-gray-600"
                    />
                    <ShoppingBag className="h-4 w-4 text-green-400" />
                    <span className="text-sm">Produk (stok = 0)</span>
                  </label>
                  
                  <label className="flex items-center gap-2 p-2 rounded hover:bg-[#1a1214] cursor-pointer">
                    <input 
                      type="checkbox" 
                      checked={cloneData.clone_suppliers}
                      onChange={(e) => setCloneData({ ...cloneData, clone_suppliers: e.target.checked })}
                      className="rounded border-gray-600"
                    />
                    <Briefcase className="h-4 w-4 text-purple-400" />
                    <span className="text-sm">Supplier</span>
                  </label>
                  
                  <label className="flex items-center gap-2 p-2 rounded hover:bg-[#1a1214] cursor-pointer">
                    <input 
                      type="checkbox" 
                      checked={cloneData.clone_customers}
                      onChange={(e) => setCloneData({ ...cloneData, clone_customers: e.target.checked })}
                      className="rounded border-gray-600"
                    />
                    <Users className="h-4 w-4 text-cyan-400" />
                    <span className="text-sm">Pelanggan (saldo = 0)</span>
                  </label>
                  
                  <label className="flex items-center gap-2 p-2 rounded hover:bg-[#1a1214] cursor-pointer">
                    <input 
                      type="checkbox" 
                      checked={cloneData.clone_coa}
                      onChange={(e) => setCloneData({ ...cloneData, clone_coa: e.target.checked })}
                      className="rounded border-gray-600"
                    />
                    <FileText className="h-4 w-4 text-amber-400" />
                    <span className="text-sm">Chart of Accounts</span>
                  </label>
                  
                  <label className="flex items-center gap-2 p-2 rounded hover:bg-[#1a1214] cursor-pointer">
                    <input 
                      type="checkbox" 
                      checked={cloneData.clone_settings}
                      onChange={(e) => setCloneData({ ...cloneData, clone_settings: e.target.checked })}
                      className="rounded border-gray-600"
                    />
                    <Settings className="h-4 w-4 text-gray-400" />
                    <span className="text-sm">Pengaturan</span>
                  </label>
                </div>
              </div>

              {/* Admin User */}
              <div className="p-4 bg-[#0a0608] rounded-lg space-y-3">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={cloneData.create_admin_user}
                    onChange={(e) => setCloneData({ ...cloneData, create_admin_user: e.target.checked })}
                    className="rounded border-gray-600"
                  />
                  <h3 className="font-medium text-amber-100">Buat User Admin</h3>
                </label>
                
                {cloneData.create_admin_user && (
                  <div className="grid grid-cols-2 gap-3 mt-2">
                    <div>
                      <label className="block text-xs text-gray-400 mb-1">Email Admin *</label>
                      <input
                        type="email"
                        value={cloneData.admin_email}
                        onChange={(e) => setCloneData({ ...cloneData, admin_email: e.target.value })}
                        className="w-full px-3 py-2 bg-[#1a1214] border border-red-900/30 rounded-lg text-sm"
                        placeholder="admin@toko.com"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-400 mb-1">Password *</label>
                      <input
                        type="password"
                        value={cloneData.admin_password}
                        onChange={(e) => setCloneData({ ...cloneData, admin_password: e.target.value })}
                        className="w-full px-3 py-2 bg-[#1a1214] border border-red-900/30 rounded-lg text-sm"
                        placeholder="********"
                      />
                    </div>
                  </div>
                )}
              </div>
            </div>

            <div className="flex justify-end gap-2 mt-6">
              <button 
                onClick={() => { setShowCloneModal(false); setCloneSource(null); }} 
                className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
                disabled={cloning}
              >
                Batal
              </button>
              <button 
                onClick={cloneBusiness} 
                disabled={cloning}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2 disabled:opacity-50"
              >
                {cloning ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Cloning...
                  </>
                ) : (
                  <>
                    <Copy className="h-4 w-4" />
                    Clone Bisnis
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default BusinessManager;
