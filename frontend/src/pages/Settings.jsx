import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Settings as SettingsIcon, Store, Bell, Shield, Database, Palette, Save, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

const Settings = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('store');
  const [saving, setSaving] = useState(false);
  
  const [storeSettings, setStoreSettings] = useState({
    store_name: 'OCB GROUP',
    address: '',
    phone: '',
    email: '',
    tax_rate: 0,
    currency: 'IDR',
    receipt_footer: 'Terima kasih atas kunjungan Anda!'
  });

  const [posSettings, setPosSettings] = useState({
    auto_print: false,
    show_stock: true,
    allow_negative_stock: false,
    default_customer: '',
    low_stock_threshold: 5
  });

  const handleSave = async () => {
    setSaving(true);
    setTimeout(() => {
      toast.success('Pengaturan disimpan');
      setSaving(false);
    }, 1000);
  };

  const tabs = [
    { id: 'store', label: 'Info Toko', icon: Store },
    { id: 'pos', label: 'POS', icon: SettingsIcon },
    { id: 'notifications', label: 'Notifikasi', icon: Bell },
    { id: 'security', label: 'Keamanan', icon: Shield },
    { id: 'backup', label: 'Backup', icon: Database }
  ];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Pengaturan</h1>
          <p className="text-gray-400">Konfigurasi sistem</p>
        </div>
      </div>

      <div className="flex gap-6">
        {/* Sidebar Tab */}
        <div className="w-48 space-y-1">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`w-full px-4 py-3 rounded-lg flex items-center gap-3 transition-colors ${
                activeTab === tab.id 
                  ? 'bg-red-900/30 text-amber-400' 
                  : 'text-gray-400 hover:text-white hover:bg-red-900/20'
              }`}
            >
              <tab.icon className="h-5 w-5" />
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 bg-[#1a1214] border border-red-900/30 rounded-xl p-6">
          {/* Tab Info Toko */}
          {activeTab === 'store' && (
            <div className="space-y-6">
              <h2 className="text-xl font-bold text-amber-100">Informasi Toko</h2>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Nama Toko</label>
                  <input
                    type="text"
                    value={storeSettings.store_name}
                    onChange={(e) => setStoreSettings({ ...storeSettings, store_name: e.target.value })}
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Telepon</label>
                  <input
                    type="tel"
                    value={storeSettings.phone}
                    onChange={(e) => setStoreSettings({ ...storeSettings, phone: e.target.value })}
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Email</label>
                  <input
                    type="email"
                    value={storeSettings.email}
                    onChange={(e) => setStoreSettings({ ...storeSettings, email: e.target.value })}
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Tarif Pajak (%)</label>
                  <input
                    type="number"
                    value={storeSettings.tax_rate}
                    onChange={(e) => setStoreSettings({ ...storeSettings, tax_rate: Number(e.target.value) })}
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg"
                  />
                </div>
                <div className="col-span-2">
                  <label className="block text-sm text-gray-400 mb-1">Alamat</label>
                  <textarea
                    value={storeSettings.address}
                    onChange={(e) => setStoreSettings({ ...storeSettings, address: e.target.value })}
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg"
                    rows={2}
                  />
                </div>
                <div className="col-span-2">
                  <label className="block text-sm text-gray-400 mb-1">Footer Struk</label>
                  <textarea
                    value={storeSettings.receipt_footer}
                    onChange={(e) => setStoreSettings({ ...storeSettings, receipt_footer: e.target.value })}
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg"
                    rows={2}
                  />
                </div>
              </div>
            </div>
          )}

          {/* Tab POS */}
          {activeTab === 'pos' && (
            <div className="space-y-6">
              <h2 className="text-xl font-bold text-amber-100">Pengaturan POS</h2>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 bg-[#0a0608] rounded-lg">
                  <div>
                    <div className="font-medium">Cetak Otomatis</div>
                    <div className="text-sm text-gray-400">Cetak struk otomatis setelah transaksi</div>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" checked={posSettings.auto_print} onChange={(e) => setPosSettings({ ...posSettings, auto_print: e.target.checked })} className="sr-only peer" />
                    <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-red-600"></div>
                  </label>
                </div>
                <div className="flex items-center justify-between p-4 bg-[#0a0608] rounded-lg">
                  <div>
                    <div className="font-medium">Tampilkan Stok</div>
                    <div className="text-sm text-gray-400">Tampilkan jumlah stok di pencarian produk</div>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" checked={posSettings.show_stock} onChange={(e) => setPosSettings({ ...posSettings, show_stock: e.target.checked })} className="sr-only peer" />
                    <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-red-600"></div>
                  </label>
                </div>
                <div className="flex items-center justify-between p-4 bg-[#0a0608] rounded-lg">
                  <div>
                    <div className="font-medium">Izinkan Stok Negatif</div>
                    <div className="text-sm text-gray-400">Perbolehkan transaksi meski stok habis</div>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" checked={posSettings.allow_negative_stock} onChange={(e) => setPosSettings({ ...posSettings, allow_negative_stock: e.target.checked })} className="sr-only peer" />
                    <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-red-600"></div>
                  </label>
                </div>
                <div className="p-4 bg-[#0a0608] rounded-lg">
                  <label className="block font-medium mb-2">Batas Stok Menipis</label>
                  <input
                    type="number"
                    value={posSettings.low_stock_threshold}
                    onChange={(e) => setPosSettings({ ...posSettings, low_stock_threshold: Number(e.target.value) })}
                    className="w-32 px-3 py-2 bg-[#1a1214] border border-red-900/30 rounded-lg"
                  />
                  <div className="text-sm text-gray-400 mt-1">Tampilkan peringatan jika stok di bawah nilai ini</div>
                </div>
              </div>
            </div>
          )}

          {/* Tab Notifikasi */}
          {activeTab === 'notifications' && (
            <div className="space-y-6">
              <h2 className="text-xl font-bold text-amber-100">Pengaturan Notifikasi</h2>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 bg-[#0a0608] rounded-lg">
                  <div>
                    <div className="font-medium">Notifikasi Stok Menipis</div>
                    <div className="text-sm text-gray-400">Kirim notifikasi saat stok mencapai batas minimum</div>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" defaultChecked className="sr-only peer" />
                    <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-red-600"></div>
                  </label>
                </div>
                <div className="flex items-center justify-between p-4 bg-[#0a0608] rounded-lg">
                  <div>
                    <div className="font-medium">Laporan Harian</div>
                    <div className="text-sm text-gray-400">Kirim ringkasan penjualan harian via email</div>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" className="sr-only peer" />
                    <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-red-600"></div>
                  </label>
                </div>
              </div>
            </div>
          )}

          {/* Tab Keamanan */}
          {activeTab === 'security' && (
            <div className="space-y-6">
              <h2 className="text-xl font-bold text-amber-100">Pengaturan Keamanan</h2>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 bg-[#0a0608] rounded-lg">
                  <div>
                    <div className="font-medium">Two-Factor Authentication (2FA)</div>
                    <div className="text-sm text-gray-400">Aktifkan keamanan tambahan untuk login</div>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" className="sr-only peer" />
                    <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-red-600"></div>
                  </label>
                </div>
                <div className="flex items-center justify-between p-4 bg-[#0a0608] rounded-lg">
                  <div>
                    <div className="font-medium">Audit Log</div>
                    <div className="text-sm text-gray-400">Catat semua aktivitas pengguna</div>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" defaultChecked className="sr-only peer" />
                    <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-red-600"></div>
                  </label>
                </div>
                <div className="p-4 bg-[#0a0608] rounded-lg">
                  <label className="block font-medium mb-2">Timeout Sesi (menit)</label>
                  <input
                    type="number"
                    defaultValue={60}
                    className="w-32 px-3 py-2 bg-[#1a1214] border border-red-900/30 rounded-lg"
                  />
                  <div className="text-sm text-gray-400 mt-1">Logout otomatis setelah tidak aktif</div>
                </div>
              </div>
            </div>
          )}

          {/* Tab Backup */}
          {activeTab === 'backup' && (
            <div className="space-y-6">
              <h2 className="text-xl font-bold text-amber-100">Backup & Restore</h2>
              <div className="space-y-4">
                <div className="p-4 bg-[#0a0608] rounded-lg">
                  <div className="font-medium mb-2">Backup Otomatis</div>
                  <div className="text-sm text-gray-400 mb-4">Database di-backup secara otomatis setiap hari</div>
                  <div className="flex gap-2">
                    <button className="px-4 py-2 bg-green-600/20 text-green-400 rounded-lg hover:bg-green-600/30">
                      Backup Sekarang
                    </button>
                  </div>
                </div>
                <div className="p-4 bg-[#0a0608] rounded-lg">
                  <div className="font-medium mb-2">Backup Terakhir</div>
                  <div className="text-sm text-gray-400">Tidak ada backup tersimpan</div>
                </div>
                <div className="p-4 bg-amber-900/10 border border-amber-700/30 rounded-lg">
                  <p className="text-amber-400 text-sm">Fitur backup dalam pengembangan. Database MongoDB sudah memiliki sistem backup otomatis di cloud.</p>
                </div>
              </div>
            </div>
          )}

          {/* Save Button */}
          <div className="mt-6 pt-6 border-t border-red-900/30 flex justify-end">
            <button
              onClick={handleSave}
              disabled={saving}
              className="px-6 py-2 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg disabled:opacity-50 flex items-center gap-2"
            >
              {saving ? <Loader2 className="h-5 w-5 animate-spin" /> : <Save className="h-5 w-5" />}
              {saving ? 'Menyimpan...' : 'Simpan Pengaturan'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;
