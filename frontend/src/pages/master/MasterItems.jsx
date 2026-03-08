import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { 
  Package, Plus, Search, Filter, Download, Upload, Edit2, Trash2, 
  MoreVertical, Barcode, Eye, Copy, FileSpreadsheet, Loader2, X,
  ChevronLeft, ChevronRight
} from 'lucide-react';
import { toast } from 'sonner';

const MasterItems = () => {
  const { api } = useAuth();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [categories, setCategories] = useState([]);
  const [units, setUnits] = useState([]);
  const [brands, setBrands] = useState([]);
  const [pagination, setPagination] = useState({ page: 1, limit: 20, total: 0 });
  const [filterCategory, setFilterCategory] = useState('');

  const [formData, setFormData] = useState({
    code: '',
    barcode: '',
    name: '',
    category_id: '',
    unit_id: '',
    brand_id: '',
    cost_price: 0,
    selling_price: 0,
    min_stock: 0,
    max_stock: 0,
    description: '',
    is_active: true,
    track_stock: true
  });

  const loadItems = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: pagination.page,
        limit: pagination.limit,
        ...(searchTerm && { search: searchTerm }),
        ...(filterCategory && { category_id: filterCategory })
      });
      const res = await api(`/api/master/items?${params}`);
      if (res.ok) {
        const data = await res.json();
        setItems(data.items || []);
        setPagination(prev => ({ ...prev, total: data.total || 0 }));
      }
    } catch (err) {
      toast.error('Gagal memuat data item');
    } finally {
      setLoading(false);
    }
  }, [api, pagination.page, pagination.limit, searchTerm, filterCategory]);

  const loadMasterData = useCallback(async () => {
    try {
      const [catRes, unitRes, brandRes] = await Promise.all([
        api('/api/master/categories'),
        api('/api/master/units'),
        api('/api/master/brands')
      ]);
      if (catRes.ok) setCategories(await catRes.json());
      if (unitRes.ok) setUnits(await unitRes.json());
      if (brandRes.ok) setBrands(await brandRes.json());
    } catch (err) {
      console.error('Error loading master data:', err);
    }
  }, [api]);

  useEffect(() => {
    loadItems();
    loadMasterData();
  }, [loadItems, loadMasterData]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const url = editingItem 
        ? `/api/master/items/${editingItem.id}`
        : '/api/master/items';
      const method = editingItem ? 'PUT' : 'POST';
      
      const res = await api(url, {
        method,
        body: JSON.stringify(formData)
      });
      
      if (res.ok) {
        toast.success(editingItem ? 'Item berhasil diupdate' : 'Item berhasil ditambahkan');
        setShowModal(false);
        resetForm();
        loadItems();
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Gagal menyimpan item');
      }
    } catch (err) {
      toast.error('Terjadi kesalahan');
    }
  };

  const handleDelete = async (item) => {
    if (!confirm(`Hapus item "${item.name}"?`)) return;
    try {
      const res = await api(`/api/master/items/${item.id}`, { method: 'DELETE' });
      if (res.ok) {
        toast.success('Item berhasil dihapus');
        loadItems();
      }
    } catch (err) {
      toast.error('Gagal menghapus item');
    }
  };

  const handleEdit = (item) => {
    setEditingItem(item);
    setFormData({
      code: item.code || '',
      barcode: item.barcode || '',
      name: item.name || '',
      category_id: item.category_id || '',
      unit_id: item.unit_id || '',
      brand_id: item.brand_id || '',
      cost_price: item.cost_price || 0,
      selling_price: item.selling_price || 0,
      min_stock: item.min_stock || 0,
      max_stock: item.max_stock || 0,
      description: item.description || '',
      is_active: item.is_active !== false,
      track_stock: item.track_stock !== false
    });
    setShowModal(true);
  };

  const resetForm = () => {
    setEditingItem(null);
    setFormData({
      code: '',
      barcode: '',
      name: '',
      category_id: '',
      unit_id: '',
      brand_id: '',
      cost_price: 0,
      selling_price: 0,
      min_stock: 0,
      max_stock: 0,
      description: '',
      is_active: true,
      track_stock: true
    });
  };

  const handleExport = async () => {
    try {
      const res = await api('/api/master/items/export');
      if (res.ok) {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'items.xlsx';
        a.click();
        toast.success('Export berhasil');
      }
    } catch (err) {
      toast.error('Gagal export data');
    }
  };

  const totalPages = Math.ceil(pagination.total / pagination.limit);

  return (
    <div className="space-y-4" data-testid="master-items-page">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Daftar Item</h1>
          <p className="text-gray-400 text-sm">Kelola produk dan barang</p>
        </div>
        <div className="flex gap-2">
          <button 
            onClick={handleExport}
            className="px-3 py-2 bg-green-600/20 text-green-400 rounded-lg hover:bg-green-600/30 flex items-center gap-2"
          >
            <Download className="h-4 w-4" /> Export
          </button>
          <button 
            onClick={() => { resetForm(); setShowModal(true); }}
            className="px-4 py-2 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg hover:opacity-90 flex items-center gap-2"
            data-testid="add-item-btn"
          >
            <Plus className="h-4 w-4" /> Tambah Item
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Cari item..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200"
              data-testid="search-input"
            />
          </div>
          <select
            value={filterCategory}
            onChange={(e) => setFilterCategory(e.target.value)}
            className="px-4 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200"
          >
            <option value="">Semua Kategori</option>
            {categories.map(cat => (
              <option key={cat.id} value={cat.id}>{cat.name}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-red-900/20">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">KODE</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">BARCODE</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">NAMA ITEM</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">KATEGORI</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-amber-200">HARGA BELI</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-amber-200">HARGA JUAL</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">STATUS</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">AKSI</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-red-900/20">
              {loading ? (
                <tr>
                  <td colSpan={8} className="px-4 py-8 text-center">
                    <Loader2 className="h-8 w-8 animate-spin mx-auto text-amber-400" />
                  </td>
                </tr>
              ) : items.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-4 py-8 text-center text-gray-400">
                    Belum ada data item
                  </td>
                </tr>
              ) : (
                items.map(item => (
                  <tr key={item.id} className="hover:bg-red-900/10">
                    <td className="px-4 py-3 text-sm font-mono text-amber-300">{item.code}</td>
                    <td className="px-4 py-3 text-sm font-mono text-gray-400">{item.barcode || '-'}</td>
                    <td className="px-4 py-3">
                      <div className="font-medium text-gray-200">{item.name}</div>
                      <div className="text-xs text-gray-500">{item.unit_name || 'PCS'}</div>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-400">{item.category_name || '-'}</td>
                    <td className="px-4 py-3 text-sm text-right text-gray-300">
                      Rp {(item.cost_price || 0).toLocaleString('id-ID')}
                    </td>
                    <td className="px-4 py-3 text-sm text-right text-green-400 font-medium">
                      Rp {(item.selling_price || 0).toLocaleString('id-ID')}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`px-2 py-1 rounded-full text-xs ${
                        item.is_active 
                          ? 'bg-green-600/20 text-green-400' 
                          : 'bg-red-600/20 text-red-400'
                      }`}>
                        {item.is_active ? 'Aktif' : 'Nonaktif'}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-center gap-1">
                        <button 
                          onClick={() => handleEdit(item)}
                          className="p-1.5 hover:bg-blue-600/20 rounded text-blue-400"
                          title="Edit"
                        >
                          <Edit2 className="h-4 w-4" />
                        </button>
                        <button 
                          onClick={() => handleDelete(item)}
                          className="p-1.5 hover:bg-red-600/20 rounded text-red-400"
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

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="px-4 py-3 border-t border-red-900/20 flex items-center justify-between">
            <p className="text-sm text-gray-400">
              Menampilkan {items.length} dari {pagination.total} item
            </p>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPagination(p => ({ ...p, page: p.page - 1 }))}
                disabled={pagination.page === 1}
                className="p-2 hover:bg-red-900/20 rounded disabled:opacity-50"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
              <span className="text-sm text-gray-400">
                Halaman {pagination.page} dari {totalPages}
              </span>
              <button
                onClick={() => setPagination(p => ({ ...p, page: p.page + 1 }))}
                disabled={pagination.page >= totalPages}
                className="p-2 hover:bg-red-900/20 rounded disabled:opacity-50"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="p-4 border-b border-red-900/30 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-amber-100">
                {editingItem ? 'Edit Item' : 'Tambah Item Baru'}
              </h2>
              <button onClick={() => setShowModal(false)} className="p-1 hover:bg-red-900/20 rounded">
                <X className="h-5 w-5" />
              </button>
            </div>
            <form onSubmit={handleSubmit} className="p-4 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Kode Item *</label>
                  <input
                    type="text"
                    value={formData.code}
                    onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Barcode</label>
                  <input
                    type="text"
                    value={formData.barcode}
                    onChange={(e) => setFormData({ ...formData, barcode: e.target.value })}
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg"
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm text-gray-400 mb-1">Nama Item *</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg"
                  required
                />
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Kategori</label>
                  <select
                    value={formData.category_id}
                    onChange={(e) => setFormData({ ...formData, category_id: e.target.value })}
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg"
                  >
                    <option value="">Pilih Kategori</option>
                    {categories.map(cat => (
                      <option key={cat.id} value={cat.id}>{cat.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Satuan</label>
                  <select
                    value={formData.unit_id}
                    onChange={(e) => setFormData({ ...formData, unit_id: e.target.value })}
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg"
                  >
                    <option value="">Pilih Satuan</option>
                    {units.map(unit => (
                      <option key={unit.id} value={unit.id}>{unit.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Merk</label>
                  <select
                    value={formData.brand_id}
                    onChange={(e) => setFormData({ ...formData, brand_id: e.target.value })}
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg"
                  >
                    <option value="">Pilih Merk</option>
                    {brands.map(brand => (
                      <option key={brand.id} value={brand.id}>{brand.name}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Harga Beli</label>
                  <input
                    type="number"
                    value={formData.cost_price}
                    onChange={(e) => setFormData({ ...formData, cost_price: Number(e.target.value) })}
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Harga Jual</label>
                  <input
                    type="number"
                    value={formData.selling_price}
                    onChange={(e) => setFormData({ ...formData, selling_price: Number(e.target.value) })}
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Stok Minimum</label>
                  <input
                    type="number"
                    value={formData.min_stock}
                    onChange={(e) => setFormData({ ...formData, min_stock: Number(e.target.value) })}
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Stok Maksimum</label>
                  <input
                    type="number"
                    value={formData.max_stock}
                    onChange={(e) => setFormData({ ...formData, max_stock: Number(e.target.value) })}
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-1">Deskripsi</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={3}
                  className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg"
                />
              </div>

              <div className="flex items-center gap-6">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                    className="w-4 h-4 rounded border-red-900/30"
                  />
                  <span className="text-sm text-gray-300">Aktif</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.track_stock}
                    onChange={(e) => setFormData({ ...formData, track_stock: e.target.checked })}
                    className="w-4 h-4 rounded border-red-900/30"
                  />
                  <span className="text-sm text-gray-300">Lacak Stok</span>
                </label>
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-red-900/30">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 border border-red-900/30 rounded-lg hover:bg-red-900/20"
                >
                  Batal
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg"
                >
                  {editingItem ? 'Update' : 'Simpan'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default MasterItems;
