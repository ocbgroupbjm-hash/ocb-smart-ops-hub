import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Building2, Plus, Loader2, Edit, Trash2, CheckCircle, Database, RefreshCw, Store, Shirt, Smartphone, Coffee, ShoppingBag, Briefcase } from 'lucide-react';
import { toast } from 'sonner';

const BusinessManager = () => {
  const { api, logout } = useAuth();
  const [businesses, setBusinesses] = useState([]);
  const [currentDb, setCurrentDb] = useState('');
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [switching, setSwitching] = useState(null);
  
  const [formData, setFormData] = useState({
    id: '',
    name: '',
    db_name: '',
    description: '',
    icon: 'store',
    color: '#991B1B'
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
    </div>
  );
};

export default BusinessManager;
