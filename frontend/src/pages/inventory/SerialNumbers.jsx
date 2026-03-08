import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Hash, Search, Plus, Loader2, CheckCircle, XCircle, AlertTriangle, Package, Trash2, Eye, Filter } from 'lucide-react';
import { toast } from 'sonner';

const SerialNumbers = () => {
  const { api } = useAuth();
  const [serials, setSerials] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [showBulkModal, setShowBulkModal] = useState(false);
  const [selectedSerial, setSelectedSerial] = useState(null);
  const [products, setProducts] = useState([]);
  const [newSerial, setNewSerial] = useState({
    serial: '',
    product_id: '',
    cost_price: 0,
    selling_price: 0,
    warranty_until: '',
    notes: ''
  });
  const [bulkData, setBulkData] = useState({
    product_id: '',
    prefix: '',
    start_number: 1,
    count: 10
  });

  useEffect(() => {
    loadSerials();
    loadProducts();
  }, [search, statusFilter]);

  const loadSerials = async () => {
    setLoading(true);
    try {
      let url = `/api/serial/list?limit=100`;
      if (search) url += `&search=${encodeURIComponent(search)}`;
      if (statusFilter) url += `&status=${statusFilter}`;
      
      const res = await api(url);
      if (res.ok) {
        const data = await res.json();
        setSerials(data.items || []);
      }
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  const loadProducts = async () => {
    try {
      const res = await api('/api/products?limit=500');
      if (res.ok) {
        const data = await res.json();
        setProducts(data.items || []);
      }
    } catch (err) { console.error(err); }
  };

  const addSerial = async () => {
    if (!newSerial.serial || !newSerial.product_id) {
      toast.error('Serial dan produk wajib diisi');
      return;
    }
    try {
      const res = await api('/api/serial/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newSerial)
      });
      if (res.ok) {
        toast.success('Serial number ditambahkan');
        setShowAddModal(false);
        setNewSerial({ serial: '', product_id: '', cost_price: 0, selling_price: 0, warranty_until: '', notes: '' });
        loadSerials();
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Gagal menambahkan');
      }
    } catch (err) { toast.error('Gagal menambahkan'); }
  };

  const bulkAddSerials = async () => {
    if (!bulkData.product_id || !bulkData.prefix || bulkData.count < 1) {
      toast.error('Data tidak lengkap');
      return;
    }
    try {
      const res = await api(`/api/serial/bulk-add?product_id=${bulkData.product_id}&prefix=${bulkData.prefix}&start_number=${bulkData.start_number}&count=${bulkData.count}`, {
        method: 'POST'
      });
      if (res.ok) {
        const data = await res.json();
        toast.success(data.message);
        setShowBulkModal(false);
        setBulkData({ product_id: '', prefix: '', start_number: 1, count: 10 });
        loadSerials();
      }
    } catch (err) { toast.error('Gagal menambahkan'); }
  };

  const deleteSerial = async (id) => {
    if (!window.confirm('Hapus serial number ini?')) return;
    try {
      const res = await api(`/api/serial/${id}`, { method: 'DELETE' });
      if (res.ok) {
        toast.success('Serial dihapus');
        loadSerials();
      }
    } catch (err) { toast.error('Gagal menghapus'); }
  };

  const updateStatus = async (id, status) => {
    try {
      const res = await api(`/api/serial/${id}/status?status=${status}`, { method: 'PUT' });
      if (res.ok) {
        toast.success('Status diupdate');
        loadSerials();
      }
    } catch (err) { toast.error('Gagal update status'); }
  };

  const getStatusBadge = (status) => {
    const styles = {
      available: 'bg-green-600/20 text-green-400',
      sold: 'bg-blue-600/20 text-blue-400',
      returned: 'bg-yellow-600/20 text-yellow-400',
      damaged: 'bg-red-600/20 text-red-400',
      reserved: 'bg-purple-600/20 text-purple-400'
    };
    const labels = {
      available: 'Tersedia',
      sold: 'Terjual',
      returned: 'Retur',
      damaged: 'Rusak',
      reserved: 'Dipesan'
    };
    return <span className={`px-2 py-1 rounded text-xs font-semibold ${styles[status] || 'bg-gray-600/20'}`}>{labels[status] || status}</span>;
  };

  return (
    <div className="space-y-6" data-testid="serial-numbers-page">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Serial Number</h1>
          <p className="text-gray-400">Lacak nomor seri produk</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowBulkModal(true)}
            className="px-4 py-2 bg-amber-600/20 text-amber-400 rounded-lg hover:bg-amber-600/30 flex items-center gap-2"
          >
            <Plus className="h-4 w-4" /> Tambah Massal
          </button>
          <button
            onClick={() => setShowAddModal(true)}
            className="px-4 py-2 bg-green-600/20 text-green-400 rounded-lg hover:bg-green-600/30 flex items-center gap-2"
          >
            <Plus className="h-4 w-4" /> Tambah Serial
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Cari serial number..."
            className="w-full pl-10 pr-4 py-2 bg-[#1a1214] border border-red-900/30 rounded-lg"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-4 py-2 bg-[#1a1214] border border-red-900/30 rounded-lg"
        >
          <option value="">Semua Status</option>
          <option value="available">Tersedia</option>
          <option value="sold">Terjual</option>
          <option value="returned">Retur</option>
          <option value="damaged">Rusak</option>
          <option value="reserved">Dipesan</option>
        </select>
      </div>

      {/* Table */}
      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
        <table className="w-full">
          <thead className="bg-red-900/20">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-semibold">Serial Number</th>
              <th className="px-4 py-3 text-left text-sm font-semibold">Produk</th>
              <th className="px-4 py-3 text-center text-sm font-semibold">Status</th>
              <th className="px-4 py-3 text-right text-sm font-semibold">Harga Jual</th>
              <th className="px-4 py-3 text-left text-sm font-semibold">Garansi</th>
              <th className="px-4 py-3 text-center text-sm font-semibold">Aksi</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={6} className="px-4 py-8 text-center"><Loader2 className="h-8 w-8 animate-spin mx-auto text-amber-400" /></td></tr>
            ) : serials.length === 0 ? (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-400">Tidak ada data</td></tr>
            ) : (
              serials.map((serial) => (
                <tr key={serial.id} className="border-t border-red-900/10 hover:bg-red-900/10">
                  <td className="px-4 py-3">
                    <div className="font-mono text-amber-300 font-semibold">{serial.serial}</div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="font-medium">{serial.product_name}</div>
                    <div className="text-sm text-gray-400">{serial.product_code}</div>
                  </td>
                  <td className="px-4 py-3 text-center">{getStatusBadge(serial.status)}</td>
                  <td className="px-4 py-3 text-right">Rp {(serial.selling_price || 0).toLocaleString('id-ID')}</td>
                  <td className="px-4 py-3 text-gray-400">{serial.warranty_until || '-'}</td>
                  <td className="px-4 py-3">
                    <div className="flex justify-center gap-1">
                      {serial.status === 'available' && (
                        <button
                          onClick={() => updateStatus(serial.id, 'reserved')}
                          className="p-1 text-purple-400 hover:bg-purple-600/20 rounded"
                          title="Reservasi"
                        >
                          <AlertTriangle className="h-4 w-4" />
                        </button>
                      )}
                      <button
                        onClick={() => deleteSerial(serial.id)}
                        className="p-1 text-red-400 hover:bg-red-600/20 rounded"
                        title="Hapus"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Add Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-6 w-[500px]">
            <h2 className="text-xl font-bold text-amber-100 mb-4">Tambah Serial Number</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Serial Number *</label>
                <input
                  type="text"
                  value={newSerial.serial}
                  onChange={(e) => setNewSerial({ ...newSerial, serial: e.target.value })}
                  className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg"
                  placeholder="SN001234567"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Produk *</label>
                <select
                  value={newSerial.product_id}
                  onChange={(e) => setNewSerial({ ...newSerial, product_id: e.target.value })}
                  className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg"
                >
                  <option value="">Pilih Produk</option>
                  {products.map(p => (
                    <option key={p.id} value={p.id}>{p.code} - {p.name}</option>
                  ))}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Harga Beli</label>
                  <input
                    type="number"
                    value={newSerial.cost_price}
                    onChange={(e) => setNewSerial({ ...newSerial, cost_price: Number(e.target.value) })}
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Harga Jual</label>
                  <input
                    type="number"
                    value={newSerial.selling_price}
                    onChange={(e) => setNewSerial({ ...newSerial, selling_price: Number(e.target.value) })}
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Garansi Sampai</label>
                <input
                  type="date"
                  value={newSerial.warranty_until}
                  onChange={(e) => setNewSerial({ ...newSerial, warranty_until: e.target.value })}
                  className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Catatan</label>
                <textarea
                  value={newSerial.notes}
                  onChange={(e) => setNewSerial({ ...newSerial, notes: e.target.value })}
                  className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg"
                  rows={2}
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <button onClick={() => setShowAddModal(false)} className="px-4 py-2 bg-gray-600 text-white rounded-lg">Batal</button>
              <button onClick={addSerial} className="px-4 py-2 bg-green-600 text-white rounded-lg">Simpan</button>
            </div>
          </div>
        </div>
      )}

      {/* Bulk Add Modal */}
      {showBulkModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-6 w-[500px]">
            <h2 className="text-xl font-bold text-amber-100 mb-4">Tambah Serial Massal</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Produk *</label>
                <select
                  value={bulkData.product_id}
                  onChange={(e) => setBulkData({ ...bulkData, product_id: e.target.value })}
                  className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg"
                >
                  <option value="">Pilih Produk</option>
                  {products.map(p => (
                    <option key={p.id} value={p.id}>{p.code} - {p.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Prefix Serial *</label>
                <input
                  type="text"
                  value={bulkData.prefix}
                  onChange={(e) => setBulkData({ ...bulkData, prefix: e.target.value })}
                  className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg"
                  placeholder="SN-"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Nomor Mulai</label>
                  <input
                    type="number"
                    value={bulkData.start_number}
                    onChange={(e) => setBulkData({ ...bulkData, start_number: Number(e.target.value) })}
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Jumlah</label>
                  <input
                    type="number"
                    value={bulkData.count}
                    onChange={(e) => setBulkData({ ...bulkData, count: Number(e.target.value) })}
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg"
                  />
                </div>
              </div>
              <div className="p-3 bg-amber-900/20 rounded-lg text-sm">
                <p className="text-amber-400">Preview: {bulkData.prefix}{String(bulkData.start_number).padStart(6, '0')} - {bulkData.prefix}{String(bulkData.start_number + bulkData.count - 1).padStart(6, '0')}</p>
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <button onClick={() => setShowBulkModal(false)} className="px-4 py-2 bg-gray-600 text-white rounded-lg">Batal</button>
              <button onClick={bulkAddSerials} className="px-4 py-2 bg-green-600 text-white rounded-lg">Generate</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SerialNumbers;
