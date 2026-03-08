import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Settings as SettingsIcon, Store, Bell, Shield, Database, Printer, Save, Loader2, Download, Upload, Trash2, RefreshCw, Plus, Check } from 'lucide-react';
import { toast } from 'sonner';

const Settings = () => {
  const { api, user } = useAuth();
  const [activeTab, setActiveTab] = useState('store');
  const [saving, setSaving] = useState(false);
  const [backups, setBackups] = useState([]);
  const [printers, setPrinters] = useState([]);
  const [loadingBackups, setLoadingBackups] = useState(false);
  const [creatingBackup, setCreatingBackup] = useState(false);
  const [restoringBackup, setRestoringBackup] = useState(null);
  const [showAddPrinter, setShowAddPrinter] = useState(false);
  
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

  const [newPrinter, setNewPrinter] = useState({
    name: '',
    type: 'usb',
    connection_string: '',
    paper_width: 80,
    is_default: false
  });

  const [receiptTemplate, setReceiptTemplate] = useState({
    show_logo: true,
    logo_url: '',
    header_text: '',
    show_branch_name: true,
    show_branch_address: true,
    show_branch_phone: true,
    show_cashier_name: true,
    show_customer_name: true,
    show_date_time: true,
    show_tax_detail: true,
    show_payment_method: true,
    footer_text: 'Terima kasih atas kunjungan Anda!',
    additional_notes: ''
  });

  useEffect(() => {
    if (activeTab === 'backup') loadBackups();
    if (activeTab === 'print') {
      loadPrinters();
      loadReceiptTemplate();
    }
  }, [activeTab]);

  const loadBackups = async () => {
    setLoadingBackups(true);
    try {
      const res = await api('/api/backup/list');
      if (res.ok) {
        const data = await res.json();
        setBackups(data.backups || []);
      }
    } catch (err) { console.error(err); }
    finally { setLoadingBackups(false); }
  };

  const createBackup = async () => {
    setCreatingBackup(true);
    try {
      const res = await api('/api/backup/create', { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        toast.success(`Backup berhasil: ${data.name} (${data.total_records} records)`);
        loadBackups();
      } else {
        toast.error('Gagal membuat backup');
      }
    } catch (err) { toast.error('Gagal membuat backup'); }
    finally { setCreatingBackup(false); }
  };

  const downloadBackup = async (backupId, backupName) => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/backup/download/${backupId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${backupName}.json`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
        toast.success('Download berhasil');
      }
    } catch (err) { toast.error('Gagal download'); }
  };

  const restoreBackup = async (backupId) => {
    if (!window.confirm('PERINGATAN: Restore akan menghapus semua data saat ini dan menggantinya dengan data backup. Lanjutkan?')) return;
    
    setRestoringBackup(backupId);
    try {
      const res = await api(`/api/backup/restore/${backupId}`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        toast.success(`Restore berhasil: ${data.total_records_restored} records`);
      } else {
        toast.error('Gagal restore');
      }
    } catch (err) { toast.error('Gagal restore'); }
    finally { setRestoringBackup(null); }
  };

  const deleteBackup = async (backupId) => {
    if (!window.confirm('Hapus backup ini?')) return;
    try {
      const res = await api(`/api/backup/${backupId}`, { method: 'DELETE' });
      if (res.ok) {
        toast.success('Backup dihapus');
        loadBackups();
      }
    } catch (err) { toast.error('Gagal hapus'); }
  };

  const loadPrinters = async () => {
    try {
      const res = await api('/api/print/printers');
      if (res.ok) {
        const data = await res.json();
        setPrinters(data.printers || []);
      }
    } catch (err) { console.error(err); }
  };

  const loadReceiptTemplate = async () => {
    try {
      const res = await api('/api/print/template');
      if (res.ok) {
        const data = await res.json();
        setReceiptTemplate(prev => ({ ...prev, ...data }));
      }
    } catch (err) { console.error(err); }
  };

  const addPrinter = async () => {
    try {
      const res = await api('/api/print/printers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newPrinter)
      });
      if (res.ok) {
        toast.success('Printer ditambahkan');
        setShowAddPrinter(false);
        setNewPrinter({ name: '', type: 'usb', connection_string: '', paper_width: 80, is_default: false });
        loadPrinters();
      }
    } catch (err) { toast.error('Gagal tambah printer'); }
  };

  const deletePrinter = async (printerId) => {
    if (!window.confirm('Hapus printer ini?')) return;
    try {
      const res = await api(`/api/print/printers/${printerId}`, { method: 'DELETE' });
      if (res.ok) {
        toast.success('Printer dihapus');
        loadPrinters();
      }
    } catch (err) { toast.error('Gagal hapus'); }
  };

  const saveReceiptTemplate = async () => {
    setSaving(true);
    try {
      const res = await api('/api/print/template', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(receiptTemplate)
      });
      if (res.ok) toast.success('Template struk disimpan');
      else toast.error('Gagal menyimpan');
    } catch (err) { toast.error('Gagal menyimpan'); }
    finally { setSaving(false); }
  };

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
    { id: 'print', label: 'Print Struk', icon: Printer },
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
              <div className="flex justify-between items-center">
                <h2 className="text-xl font-bold text-amber-100">Backup & Restore Database</h2>
                <button
                  onClick={createBackup}
                  disabled={creatingBackup}
                  className="px-4 py-2 bg-green-600/20 text-green-400 rounded-lg hover:bg-green-600/30 flex items-center gap-2 disabled:opacity-50"
                >
                  {creatingBackup ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
                  {creatingBackup ? 'Membuat Backup...' : 'Buat Backup Baru'}
                </button>
              </div>
              
              <div className="p-4 bg-amber-900/10 border border-amber-700/30 rounded-lg">
                <p className="text-amber-400 text-sm">
                  <strong>Tips:</strong> Lakukan backup secara berkala untuk mengamankan data Anda. 
                  File backup dapat diunduh dan disimpan di lokasi aman.
                </p>
              </div>

              {loadingBackups ? (
                <div className="text-center py-8">
                  <Loader2 className="h-8 w-8 animate-spin mx-auto text-amber-400" />
                  <p className="text-gray-400 mt-2">Memuat daftar backup...</p>
                </div>
              ) : backups.length === 0 ? (
                <div className="text-center py-8 text-gray-400">
                  <Database className="h-12 w-12 mx-auto mb-3 opacity-50" />
                  <p>Belum ada backup tersimpan</p>
                  <p className="text-sm">Klik "Buat Backup Baru" untuk membuat backup pertama</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {backups.map((backup) => (
                    <div key={backup.id} className="p-4 bg-[#0a0608] rounded-lg flex justify-between items-center">
                      <div>
                        <div className="font-medium text-amber-100">{backup.name}</div>
                        <div className="text-sm text-gray-400">
                          {new Date(backup.created_at).toLocaleString('id-ID')} • {backup.size} • {backup.total_records} records
                        </div>
                        <div className="text-xs text-gray-500 mt-1">
                          Oleh: {backup.created_by} • Koleksi: {backup.collections?.length || 0}
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={() => downloadBackup(backup.id, backup.name)}
                          className="p-2 bg-blue-600/20 text-blue-400 rounded-lg hover:bg-blue-600/30"
                          title="Download"
                        >
                          <Download className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => restoreBackup(backup.id)}
                          disabled={restoringBackup === backup.id}
                          className="p-2 bg-amber-600/20 text-amber-400 rounded-lg hover:bg-amber-600/30 disabled:opacity-50"
                          title="Restore"
                        >
                          {restoringBackup === backup.id ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
                        </button>
                        <button
                          onClick={() => deleteBackup(backup.id)}
                          className="p-2 bg-red-600/20 text-red-400 rounded-lg hover:bg-red-600/30"
                          title="Hapus"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Tab Print Struk */}
          {activeTab === 'print' && (
            <div className="space-y-6">
              <h2 className="text-xl font-bold text-amber-100">Pengaturan Print Struk</h2>
              
              {/* Printer List */}
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <h3 className="font-semibold">Daftar Printer</h3>
                  <button
                    onClick={() => setShowAddPrinter(!showAddPrinter)}
                    className="px-3 py-1 bg-green-600/20 text-green-400 rounded-lg text-sm hover:bg-green-600/30 flex items-center gap-1"
                  >
                    <Plus className="h-4 w-4" /> Tambah Printer
                  </button>
                </div>

                {showAddPrinter && (
                  <div className="p-4 bg-[#0a0608] rounded-lg space-y-3 border border-green-900/30">
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="block text-sm text-gray-400 mb-1">Nama Printer</label>
                        <input
                          type="text"
                          value={newPrinter.name}
                          onChange={(e) => setNewPrinter({ ...newPrinter, name: e.target.value })}
                          className="w-full px-3 py-2 bg-[#1a1214] border border-red-900/30 rounded-lg"
                          placeholder="Printer Kasir 1"
                        />
                      </div>
                      <div>
                        <label className="block text-sm text-gray-400 mb-1">Tipe Koneksi</label>
                        <select
                          value={newPrinter.type}
                          onChange={(e) => setNewPrinter({ ...newPrinter, type: e.target.value })}
                          className="w-full px-3 py-2 bg-[#1a1214] border border-red-900/30 rounded-lg"
                        >
                          <option value="usb">USB</option>
                          <option value="bluetooth">Bluetooth</option>
                          <option value="wifi">WiFi</option>
                          <option value="network">Network (IP)</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-sm text-gray-400 mb-1">Alamat/Port</label>
                        <input
                          type="text"
                          value={newPrinter.connection_string}
                          onChange={(e) => setNewPrinter({ ...newPrinter, connection_string: e.target.value })}
                          className="w-full px-3 py-2 bg-[#1a1214] border border-red-900/30 rounded-lg"
                          placeholder="COM1 / 192.168.1.100"
                        />
                      </div>
                      <div>
                        <label className="block text-sm text-gray-400 mb-1">Lebar Kertas (mm)</label>
                        <select
                          value={newPrinter.paper_width}
                          onChange={(e) => setNewPrinter({ ...newPrinter, paper_width: Number(e.target.value) })}
                          className="w-full px-3 py-2 bg-[#1a1214] border border-red-900/30 rounded-lg"
                        >
                          <option value={58}>58mm</option>
                          <option value={80}>80mm</option>
                        </select>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={newPrinter.is_default}
                        onChange={(e) => setNewPrinter({ ...newPrinter, is_default: e.target.checked })}
                        className="rounded"
                      />
                      <span className="text-sm">Jadikan printer default</span>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={addPrinter}
                        className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                      >
                        Simpan
                      </button>
                      <button
                        onClick={() => setShowAddPrinter(false)}
                        className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
                      >
                        Batal
                      </button>
                    </div>
                  </div>
                )}

                {printers.length === 0 ? (
                  <div className="p-4 bg-[#0a0608] rounded-lg text-center text-gray-400">
                    <Printer className="h-8 w-8 mx-auto mb-2 opacity-50" />
                    <p>Belum ada printer dikonfigurasi</p>
                  </div>
                ) : (
                  printers.map((printer) => (
                    <div key={printer.id} className="p-4 bg-[#0a0608] rounded-lg flex justify-between items-center">
                      <div className="flex items-center gap-3">
                        <Printer className="h-8 w-8 text-amber-400" />
                        <div>
                          <div className="font-medium flex items-center gap-2">
                            {printer.name}
                            {printer.is_default && (
                              <span className="px-2 py-0.5 bg-green-600/20 text-green-400 rounded text-xs">Default</span>
                            )}
                          </div>
                          <div className="text-sm text-gray-400">
                            {printer.printer_type?.toUpperCase()} • {printer.connection_string} • {printer.paper_width}mm
                          </div>
                        </div>
                      </div>
                      <button
                        onClick={() => deletePrinter(printer.id)}
                        className="p-2 text-red-400 hover:bg-red-600/20 rounded-lg"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  ))
                )}
              </div>

              {/* Receipt Template */}
              <div className="border-t border-red-900/30 pt-6">
                <h3 className="font-semibold mb-4">Template Struk</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-3">
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={receiptTemplate.show_logo}
                        onChange={(e) => setReceiptTemplate({ ...receiptTemplate, show_logo: e.target.checked })}
                        className="rounded"
                      />
                      <span>Tampilkan Logo</span>
                    </label>
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={receiptTemplate.show_branch_name}
                        onChange={(e) => setReceiptTemplate({ ...receiptTemplate, show_branch_name: e.target.checked })}
                        className="rounded"
                      />
                      <span>Tampilkan Nama Cabang</span>
                    </label>
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={receiptTemplate.show_branch_address}
                        onChange={(e) => setReceiptTemplate({ ...receiptTemplate, show_branch_address: e.target.checked })}
                        className="rounded"
                      />
                      <span>Tampilkan Alamat Cabang</span>
                    </label>
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={receiptTemplate.show_cashier_name}
                        onChange={(e) => setReceiptTemplate({ ...receiptTemplate, show_cashier_name: e.target.checked })}
                        className="rounded"
                      />
                      <span>Tampilkan Nama Kasir</span>
                    </label>
                  </div>
                  <div className="space-y-3">
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={receiptTemplate.show_customer_name}
                        onChange={(e) => setReceiptTemplate({ ...receiptTemplate, show_customer_name: e.target.checked })}
                        className="rounded"
                      />
                      <span>Tampilkan Nama Pelanggan</span>
                    </label>
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={receiptTemplate.show_tax_detail}
                        onChange={(e) => setReceiptTemplate({ ...receiptTemplate, show_tax_detail: e.target.checked })}
                        className="rounded"
                      />
                      <span>Tampilkan Detail Pajak</span>
                    </label>
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={receiptTemplate.show_payment_method}
                        onChange={(e) => setReceiptTemplate({ ...receiptTemplate, show_payment_method: e.target.checked })}
                        className="rounded"
                      />
                      <span>Tampilkan Metode Pembayaran</span>
                    </label>
                  </div>
                </div>
                <div className="mt-4 space-y-3">
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">Header Struk</label>
                    <input
                      type="text"
                      value={receiptTemplate.header_text}
                      onChange={(e) => setReceiptTemplate({ ...receiptTemplate, header_text: e.target.value })}
                      className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg"
                      placeholder="Selamat Datang di OCB GROUP"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">Footer Struk</label>
                    <textarea
                      value={receiptTemplate.footer_text}
                      onChange={(e) => setReceiptTemplate({ ...receiptTemplate, footer_text: e.target.value })}
                      className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg"
                      rows={2}
                    />
                  </div>
                </div>
                <button
                  onClick={saveReceiptTemplate}
                  disabled={saving}
                  className="mt-4 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2"
                >
                  {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />}
                  Simpan Template
                </button>
              </div>
            </div>
          )}

          {/* Save Button */}
          {activeTab !== 'backup' && activeTab !== 'print' && (
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
          )}
        </div>
      </div>
    </div>
  );
};

export default Settings;
