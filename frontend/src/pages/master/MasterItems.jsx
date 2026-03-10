import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { 
  Package, Plus, Search, RefreshCw, Download, Upload, Edit2, Trash2, 
  Eye, Barcode, Loader2, X, ChevronLeft, ChevronRight, Printer, Settings,
  Filter, FileSpreadsheet, FileText
} from 'lucide-react';
import { toast } from 'sonner';

const MasterItems = () => {
  const { api } = useAuth();
  
  // Data states
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [categories, setCategories] = useState([]);
  const [units, setUnits] = useState([]);
  const [brands, setBrands] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [branches, setBranches] = useState([]);
  
  // Filter states - COMPREHENSIVE like ERP desktop
  const [filters, setFilters] = useState({
    keyword: '',
    itemType: 'semua', // barang, jasa, rakitan, non-inventory, biaya, semua
    warehouse: '',
    category: '',
    itemStatus: 'semua', // semua, aktif, tidak_aktif, stok_ada, stok_habis
    rack: '',
    brand: '',
    discontinued: false,
    sortBy: 'code', // code, name, sell_price, buy_price, stock, brand
    sortOrder: 'asc'
  });
  
  // Pagination
  const [pagination, setPagination] = useState({ page: 1, limit: 50, total: 0 });
  
  // Modal states
  const [showModal, setShowModal] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [showBranchStock, setShowBranchStock] = useState(false);
  const [selectedItemForStock, setSelectedItemForStock] = useState(null);
  const [branchStockData, setBranchStockData] = useState([]);
  
  // Form data
  const [formData, setFormData] = useState({
    code: '',
    barcode: '',
    name: '',
    category_id: '',
    unit_id: '',
    brand_id: '',
    warehouse_id: '',
    rack: '',
    item_type: 'barang',
    cost_price: 0,
    selling_price: 0,
    description: '',
    is_active: true,
    track_stock: true,
    discontinued: false
  });

  // Load items with all filters
  const loadItems = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: pagination.page,
        limit: pagination.limit
      });
      
      // Add filters
      if (filters.keyword) params.append('search', filters.keyword);
      if (filters.itemType !== 'semua') params.append('item_type', filters.itemType);
      if (filters.warehouse) params.append('warehouse_id', filters.warehouse);
      if (filters.category) params.append('category_id', filters.category);
      if (filters.brand) params.append('brand_id', filters.brand);
      if (filters.rack) params.append('rack', filters.rack);
      if (filters.discontinued) params.append('discontinued', 'true');
      if (filters.itemStatus === 'aktif') params.append('is_active', 'true');
      if (filters.itemStatus === 'tidak_aktif') params.append('is_active', 'false');
      if (filters.itemStatus === 'stok_ada') params.append('has_stock', 'true');
      if (filters.itemStatus === 'stok_habis') params.append('has_stock', 'false');
      params.append('sort_by', filters.sortBy);
      params.append('sort_order', filters.sortOrder);
      
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
  }, [api, pagination.page, pagination.limit, filters]);

  // Load master data
  const loadMasterData = useCallback(async () => {
    try {
      const [catRes, unitRes, brandRes, whRes, branchRes] = await Promise.all([
        api('/api/master/categories'),
        api('/api/master/units'),
        api('/api/master/brands'),
        api('/api/master/warehouses'),
        api('/api/global-map/branches')
      ]);
      if (catRes.ok) setCategories(await catRes.json());
      if (unitRes.ok) setUnits(await unitRes.json());
      if (brandRes.ok) setBrands(await brandRes.json());
      if (whRes.ok) setWarehouses(await whRes.json());
      if (branchRes.ok) {
        const data = await branchRes.json();
        setBranches(data.branches || []);
      }
    } catch (err) {
      console.error('Error loading master data:', err);
    }
  }, [api]);

  useEffect(() => {
    loadItems();
    loadMasterData();
  }, [loadItems, loadMasterData]);

  // Filter change handlers
  const handleFilterChange = (field, value) => {
    setFilters(prev => ({ ...prev, [field]: value }));
    setPagination(prev => ({ ...prev, page: 1 }));
  };

  const resetFilters = () => {
    setFilters({
      keyword: '',
      itemType: 'semua',
      warehouse: '',
      category: '',
      itemStatus: 'semua',
      rack: '',
      brand: '',
      discontinued: false,
      sortBy: 'code',
      sortOrder: 'asc'
    });
    setPagination(prev => ({ ...prev, page: 1 }));
  };

  const handleSearch = () => {
    loadItems();
  };

  // CRUD handlers
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
      warehouse_id: item.warehouse_id || '',
      rack: item.rack || '',
      item_type: item.item_type || 'barang',
      cost_price: item.cost_price || 0,
      selling_price: item.selling_price || 0,
      description: item.description || '',
      is_active: item.is_active !== false,
      track_stock: item.track_stock !== false,
      discontinued: item.discontinued || false
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
      warehouse_id: '',
      rack: '',
      item_type: 'barang',
      cost_price: 0,
      selling_price: 0,
      description: '',
      is_active: true,
      track_stock: true,
      discontinued: false
    });
  };

  // Branch stock management
  const openBranchStockManager = async (item) => {
    setSelectedItemForStock(item);
    try {
      const res = await api(`/api/inventory/branch-stock/${item.id}`);
      if (res.ok) {
        const data = await res.json();
        setBranchStockData(data.branch_stocks || []);
      } else {
        // Initialize with all branches if no data
        setBranchStockData(branches.map(b => ({
          branch_id: b.id,
          branch_name: b.name,
          stock_current: 0,
          stock_minimum: 0,
          stock_maximum: 0
        })));
      }
    } catch (err) {
      setBranchStockData(branches.map(b => ({
        branch_id: b.id,
        branch_name: b.name,
        stock_current: 0,
        stock_minimum: 0,
        stock_maximum: 0
      })));
    }
    setShowBranchStock(true);
  };

  const saveBranchStock = async () => {
    try {
      const res = await api(`/api/inventory/branch-stock/${selectedItemForStock.id}`, {
        method: 'POST',
        body: JSON.stringify({ branch_stocks: branchStockData })
      });
      if (res.ok) {
        toast.success('Stok per cabang berhasil disimpan');
        setShowBranchStock(false);
      } else {
        toast.error('Gagal menyimpan stok cabang');
      }
    } catch (err) {
      toast.error('Terjadi kesalahan');
    }
  };

  const updateBranchStockValue = (branchId, field, value) => {
    setBranchStockData(prev => prev.map(bs => 
      bs.branch_id === branchId ? { ...bs, [field]: parseInt(value) || 0 } : bs
    ));
  };

  const handleExport = async (format) => {
    try {
      const res = await api(`/api/export-v2/master/products?format=${format}`);
      if (res.ok) {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `items.${format === 'xlsx' ? 'xlsx' : format}`;
        a.click();
        toast.success('Export berhasil');
      }
    } catch (err) {
      toast.error('Gagal export data');
    }
  };

  const formatCurrency = (num) => {
    return new Intl.NumberFormat('id-ID').format(num || 0);
  };

  const totalPages = Math.ceil(pagination.total / pagination.limit);

  return (
    <div className="min-h-screen bg-[#0a0608] p-2" data-testid="master-items-page">
      {/* COMPACT FILTER BAR - ERP Desktop Style */}
      <div className="bg-[#1a1214] border border-red-900/30 rounded-lg p-3 mb-2">
        {/* BARIS 1: Keyword + Buttons */}
        <div className="flex items-center gap-2 mb-2">
          <div className="flex items-center gap-1">
            <span className="text-xs text-gray-400 w-16">Kata Kunci</span>
            <input
              type="text"
              value={filters.keyword}
              onChange={(e) => handleFilterChange('keyword', e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="Kode / Nama / Barcode"
              className="w-48 px-2 py-1 text-sm bg-[#0a0608] border border-red-900/30 rounded text-gray-200"
              data-testid="filter-keyword"
            />
          </div>
          <button
            onClick={handleSearch}
            className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 flex items-center gap-1"
            data-testid="btn-search"
          >
            <Search className="h-3 w-3" /> Cari
          </button>
          <button
            onClick={resetFilters}
            className="px-3 py-1 bg-gray-600 text-white text-sm rounded hover:bg-gray-700 flex items-center gap-1"
            data-testid="btn-reset"
          >
            <RefreshCw className="h-3 w-3" /> Reset
          </button>
          <div className="flex-1" />
          <button
            onClick={() => handleExport('xlsx')}
            className="px-2 py-1 bg-green-700 text-white text-xs rounded hover:bg-green-800 flex items-center gap-1"
          >
            <FileSpreadsheet className="h-3 w-3" /> Excel
          </button>
          <button
            onClick={() => handleExport('csv')}
            className="px-2 py-1 bg-orange-600 text-white text-xs rounded hover:bg-orange-700 flex items-center gap-1"
          >
            <FileText className="h-3 w-3" /> CSV
          </button>
          <button
            onClick={() => { resetForm(); setShowModal(true); }}
            className="px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700 flex items-center gap-1"
            data-testid="btn-add"
          >
            <Plus className="h-3 w-3" /> Tambah Item
          </button>
        </div>

        {/* BARIS 2: Tipe Item + Dept/Gudang + Jenis + Pilihan Item */}
        <div className="flex items-center gap-4 mb-2 flex-wrap">
          <div className="flex items-center gap-1">
            <span className="text-xs text-gray-400">Tipe Item</span>
            <div className="flex gap-1 ml-1">
              {[
                { value: 'semua', label: 'Semua' },
                { value: 'barang', label: 'Barang' },
                { value: 'jasa', label: 'Jasa' },
                { value: 'rakitan', label: 'Rakitan' },
                { value: 'non-inventory', label: 'Non-Inv' },
                { value: 'biaya', label: 'Biaya' }
              ].map(opt => (
                <label key={opt.value} className="flex items-center text-xs text-gray-300 cursor-pointer">
                  <input
                    type="radio"
                    name="itemType"
                    value={opt.value}
                    checked={filters.itemType === opt.value}
                    onChange={(e) => handleFilterChange('itemType', e.target.value)}
                    className="mr-1 w-3 h-3"
                  />
                  {opt.label}
                </label>
              ))}
            </div>
          </div>
          <div className="flex items-center gap-1">
            <span className="text-xs text-gray-400">Dept./Gudang</span>
            <select
              value={filters.warehouse}
              onChange={(e) => handleFilterChange('warehouse', e.target.value)}
              className="px-2 py-1 text-xs bg-[#0a0608] border border-red-900/30 rounded text-gray-200 w-32"
              data-testid="filter-warehouse"
            >
              <option value="">Semua</option>
              {warehouses.map(w => (
                <option key={w.id} value={w.id}>{w.name}</option>
              ))}
            </select>
          </div>
          <div className="flex items-center gap-1">
            <span className="text-xs text-gray-400">Jenis</span>
            <select
              value={filters.category}
              onChange={(e) => handleFilterChange('category', e.target.value)}
              className="px-2 py-1 text-xs bg-[#0a0608] border border-red-900/30 rounded text-gray-200 w-32"
              data-testid="filter-category"
            >
              <option value="">Semua</option>
              {categories.map(c => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>
          <div className="flex items-center gap-1">
            <span className="text-xs text-gray-400">Pilihan Item</span>
            <select
              value={filters.itemStatus}
              onChange={(e) => handleFilterChange('itemStatus', e.target.value)}
              className="px-2 py-1 text-xs bg-[#0a0608] border border-red-900/30 rounded text-gray-200 w-28"
              data-testid="filter-status"
            >
              <option value="semua">Semua Data</option>
              <option value="aktif">Aktif</option>
              <option value="tidak_aktif">Tidak Aktif</option>
              <option value="stok_ada">Stok Ada</option>
              <option value="stok_habis">Stok Habis</option>
            </select>
          </div>
        </div>

        {/* BARIS 3: Rak + Merek + Discontinued */}
        <div className="flex items-center gap-4 mb-2 flex-wrap">
          <div className="flex items-center gap-1">
            <span className="text-xs text-gray-400">Rak</span>
            <input
              type="text"
              value={filters.rack}
              onChange={(e) => handleFilterChange('rack', e.target.value)}
              placeholder="Rak"
              className="w-20 px-2 py-1 text-xs bg-[#0a0608] border border-red-900/30 rounded text-gray-200"
              data-testid="filter-rack"
            />
          </div>
          <div className="flex items-center gap-1">
            <span className="text-xs text-gray-400">Merek</span>
            <select
              value={filters.brand}
              onChange={(e) => handleFilterChange('brand', e.target.value)}
              className="px-2 py-1 text-xs bg-[#0a0608] border border-red-900/30 rounded text-gray-200 w-32"
              data-testid="filter-brand"
            >
              <option value="">Semua</option>
              {brands.map(b => (
                <option key={b.id} value={b.id}>{b.name}</option>
              ))}
            </select>
          </div>
          <label className="flex items-center text-xs text-gray-300 cursor-pointer gap-1">
            <input
              type="checkbox"
              checked={filters.discontinued}
              onChange={(e) => handleFilterChange('discontinued', e.target.checked)}
              className="w-3 h-3"
              data-testid="filter-discontinued"
            />
            Tidak Dijual / Discontinued
          </label>
        </div>

        {/* BARIS 4: Sort + Total Data */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1">
            <span className="text-xs text-gray-400">Urut berdasarkan</span>
            <select
              value={filters.sortBy}
              onChange={(e) => handleFilterChange('sortBy', e.target.value)}
              className="px-2 py-1 text-xs bg-[#0a0608] border border-red-900/30 rounded text-gray-200 w-28"
              data-testid="filter-sort"
            >
              <option value="code">Kode Item</option>
              <option value="name">Nama Item</option>
              <option value="selling_price">Harga Jual</option>
              <option value="cost_price">Harga Beli</option>
              <option value="stock">Stok</option>
              <option value="brand">Merek</option>
            </select>
            <select
              value={filters.sortOrder}
              onChange={(e) => handleFilterChange('sortOrder', e.target.value)}
              className="px-2 py-1 text-xs bg-[#0a0608] border border-red-900/30 rounded text-gray-200 w-20"
            >
              <option value="asc">A-Z / 0-9</option>
              <option value="desc">Z-A / 9-0</option>
            </select>
          </div>
          <div className="text-sm font-medium text-amber-400" data-testid="total-data">
            Total data yang ditemukan: <span className="text-white">{pagination.total}</span>
          </div>
        </div>
      </div>

      {/* DATA TABLE - Compact ERP Style */}
      <div className="bg-[#1a1214] border border-red-900/30 rounded-lg overflow-hidden">
        <div className="overflow-x-auto" style={{ maxHeight: 'calc(100vh - 280px)' }}>
          <table className="w-full text-xs">
            <thead className="bg-red-900/30 sticky top-0">
              <tr>
                <th className="px-2 py-2 text-left text-amber-200 font-semibold">KODE</th>
                <th className="px-2 py-2 text-left text-amber-200 font-semibold">BARCODE</th>
                <th className="px-2 py-2 text-left text-amber-200 font-semibold">NAMA ITEM</th>
                <th className="px-2 py-2 text-left text-amber-200 font-semibold">TIPE</th>
                <th className="px-2 py-2 text-left text-amber-200 font-semibold">GUDANG</th>
                <th className="px-2 py-2 text-left text-amber-200 font-semibold">RAK</th>
                <th className="px-2 py-2 text-left text-amber-200 font-semibold">MEREK</th>
                <th className="px-2 py-2 text-right text-amber-200 font-semibold">H.BELI</th>
                <th className="px-2 py-2 text-right text-amber-200 font-semibold">H.JUAL</th>
                <th className="px-2 py-2 text-right text-amber-200 font-semibold">STOK</th>
                <th className="px-2 py-2 text-center text-amber-200 font-semibold">STATUS</th>
                <th className="px-2 py-2 text-center text-amber-200 font-semibold">AKSI</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-red-900/20">
              {loading ? (
                <tr>
                  <td colSpan={12} className="px-4 py-8 text-center text-gray-400">
                    <Loader2 className="h-6 w-6 animate-spin mx-auto mb-2" />
                    Memuat data...
                  </td>
                </tr>
              ) : items.length === 0 ? (
                <tr>
                  <td colSpan={12} className="px-4 py-8 text-center text-gray-400">
                    Tidak ada data item ditemukan
                  </td>
                </tr>
              ) : (
                items.map((item, idx) => (
                  <tr 
                    key={item.id} 
                    className={`hover:bg-red-900/10 ${idx % 2 === 0 ? 'bg-[#0a0608]/30' : ''}`}
                    data-testid={`item-row-${idx}`}
                  >
                    <td className="px-2 py-1.5 text-gray-200 font-mono">{item.code}</td>
                    <td className="px-2 py-1.5 text-gray-400 font-mono">{item.barcode || '-'}</td>
                    <td className="px-2 py-1.5 text-gray-200">{item.name}</td>
                    <td className="px-2 py-1.5">
                      <span className={`px-1.5 py-0.5 rounded text-[10px] ${
                        item.item_type === 'barang' ? 'bg-blue-900/50 text-blue-300' :
                        item.item_type === 'jasa' ? 'bg-purple-900/50 text-purple-300' :
                        item.item_type === 'rakitan' ? 'bg-green-900/50 text-green-300' :
                        'bg-gray-900/50 text-gray-300'
                      }`}>
                        {(item.item_type || 'barang').toUpperCase()}
                      </span>
                    </td>
                    <td className="px-2 py-1.5 text-gray-400">{item.warehouse_name || '-'}</td>
                    <td className="px-2 py-1.5 text-gray-400">{item.rack || '-'}</td>
                    <td className="px-2 py-1.5 text-gray-400">{item.brand_name || '-'}</td>
                    <td className="px-2 py-1.5 text-right text-gray-300">{formatCurrency(item.cost_price)}</td>
                    <td className="px-2 py-1.5 text-right text-green-400 font-medium">{formatCurrency(item.selling_price)}</td>
                    <td className="px-2 py-1.5 text-right">
                      <span className={`font-medium ${
                        (item.stock || 0) <= (item.min_stock || 0) ? 'text-red-400' : 
                        (item.stock || 0) <= (item.min_stock || 0) * 2 ? 'text-yellow-400' : 
                        'text-green-400'
                      }`}>
                        {item.stock || 0}
                      </span>
                    </td>
                    <td className="px-2 py-1.5 text-center">
                      {item.discontinued ? (
                        <span className="px-1.5 py-0.5 bg-red-900/50 text-red-300 rounded text-[10px]">DISC</span>
                      ) : item.is_active ? (
                        <span className="px-1.5 py-0.5 bg-green-900/50 text-green-300 rounded text-[10px]">AKTIF</span>
                      ) : (
                        <span className="px-1.5 py-0.5 bg-gray-900/50 text-gray-400 rounded text-[10px]">NON</span>
                      )}
                    </td>
                    <td className="px-2 py-1.5 text-center">
                      <div className="flex items-center justify-center gap-1">
                        <button
                          onClick={() => handleEdit(item)}
                          className="p-1 hover:bg-blue-900/30 rounded text-blue-400"
                          title="Edit"
                        >
                          <Edit2 className="h-3 w-3" />
                        </button>
                        <button
                          onClick={() => openBranchStockManager(item)}
                          className="p-1 hover:bg-purple-900/30 rounded text-purple-400"
                          title="Stok Per Cabang"
                        >
                          <Package className="h-3 w-3" />
                        </button>
                        <button
                          onClick={() => handleDelete(item)}
                          className="p-1 hover:bg-red-900/30 rounded text-red-400"
                          title="Hapus"
                        >
                          <Trash2 className="h-3 w-3" />
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
        <div className="flex items-center justify-between px-3 py-2 border-t border-red-900/30 bg-[#0a0608]/50">
          <div className="text-xs text-gray-400">
            Menampilkan {((pagination.page - 1) * pagination.limit) + 1} - {Math.min(pagination.page * pagination.limit, pagination.total)} dari {pagination.total} item
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setPagination(p => ({ ...p, page: Math.max(1, p.page - 1) }))}
              disabled={pagination.page === 1}
              className="px-2 py-1 bg-gray-700 text-white text-xs rounded disabled:opacity-50"
            >
              <ChevronLeft className="h-3 w-3" />
            </button>
            <span className="px-2 text-xs text-gray-300">
              Hal {pagination.page} / {totalPages || 1}
            </span>
            <button
              onClick={() => setPagination(p => ({ ...p, page: Math.min(totalPages, p.page + 1) }))}
              disabled={pagination.page >= totalPages}
              className="px-2 py-1 bg-gray-700 text-white text-xs rounded disabled:opacity-50"
            >
              <ChevronRight className="h-3 w-3" />
            </button>
          </div>
        </div>
      </div>

      {/* ADD/EDIT MODAL */}
      {showModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-lg w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between px-4 py-3 border-b border-red-900/30">
              <h3 className="text-lg font-bold text-amber-100">
                {editingItem ? 'Edit Item' : 'Tambah Item Baru'}
              </h3>
              <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-white">
                <X className="h-5 w-5" />
              </button>
            </div>
            <form onSubmit={handleSubmit} className="p-4 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs text-gray-400 mb-1">Kode Item *</label>
                  <input
                    type="text"
                    value={formData.code}
                    onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded text-gray-200 text-sm"
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-400 mb-1">Barcode</label>
                  <input
                    type="text"
                    value={formData.barcode}
                    onChange={(e) => setFormData({ ...formData, barcode: e.target.value })}
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded text-gray-200 text-sm"
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1">Nama Item *</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded text-gray-200 text-sm"
                  required
                />
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs text-gray-400 mb-1">Tipe Item</label>
                  <select
                    value={formData.item_type}
                    onChange={(e) => setFormData({ ...formData, item_type: e.target.value })}
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded text-gray-200 text-sm"
                  >
                    <option value="barang">Barang</option>
                    <option value="jasa">Jasa</option>
                    <option value="rakitan">Rakitan</option>
                    <option value="non-inventory">Non-Inventory</option>
                    <option value="biaya">Biaya</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-gray-400 mb-1">Kategori</label>
                  <select
                    value={formData.category_id}
                    onChange={(e) => setFormData({ ...formData, category_id: e.target.value })}
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded text-gray-200 text-sm"
                  >
                    <option value="">Pilih Kategori</option>
                    {categories.map(c => (
                      <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-gray-400 mb-1">Satuan</label>
                  <select
                    value={formData.unit_id}
                    onChange={(e) => setFormData({ ...formData, unit_id: e.target.value })}
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded text-gray-200 text-sm"
                  >
                    <option value="">Pilih Satuan</option>
                    {units.map(u => (
                      <option key={u.id} value={u.id}>{u.name}</option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs text-gray-400 mb-1">Merek</label>
                  <select
                    value={formData.brand_id}
                    onChange={(e) => setFormData({ ...formData, brand_id: e.target.value })}
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded text-gray-200 text-sm"
                  >
                    <option value="">Pilih Merek</option>
                    {brands.map(b => (
                      <option key={b.id} value={b.id}>{b.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-gray-400 mb-1">Gudang</label>
                  <select
                    value={formData.warehouse_id}
                    onChange={(e) => setFormData({ ...formData, warehouse_id: e.target.value })}
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded text-gray-200 text-sm"
                  >
                    <option value="">Pilih Gudang</option>
                    {warehouses.map(w => (
                      <option key={w.id} value={w.id}>{w.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-gray-400 mb-1">Rak</label>
                  <input
                    type="text"
                    value={formData.rack}
                    onChange={(e) => setFormData({ ...formData, rack: e.target.value })}
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded text-gray-200 text-sm"
                    placeholder="Contoh: A-01"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs text-gray-400 mb-1">Harga Beli</label>
                  <input
                    type="number"
                    value={formData.cost_price}
                    onChange={(e) => setFormData({ ...formData, cost_price: parseInt(e.target.value) || 0 })}
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded text-gray-200 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-400 mb-1">Harga Jual</label>
                  <input
                    type="number"
                    value={formData.selling_price}
                    onChange={(e) => setFormData({ ...formData, selling_price: parseInt(e.target.value) || 0 })}
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded text-gray-200 text-sm"
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1">Deskripsi</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded text-gray-200 text-sm"
                  rows={2}
                />
              </div>
              <div className="flex items-center gap-4">
                <label className="flex items-center gap-2 text-sm text-gray-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                    className="w-4 h-4"
                  />
                  Aktif
                </label>
                <label className="flex items-center gap-2 text-sm text-gray-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.track_stock}
                    onChange={(e) => setFormData({ ...formData, track_stock: e.target.checked })}
                    className="w-4 h-4"
                  />
                  Track Stok
                </label>
                <label className="flex items-center gap-2 text-sm text-gray-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.discontinued}
                    onChange={(e) => setFormData({ ...formData, discontinued: e.target.checked })}
                    className="w-4 h-4"
                  />
                  Discontinued
                </label>
              </div>
              <div className="flex gap-2 pt-4 border-t border-red-900/30">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="flex-1 px-4 py-2 bg-gray-700 text-white rounded hover:bg-gray-600"
                >
                  Batal
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
                >
                  {editingItem ? 'Update' : 'Simpan'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* BRANCH STOCK MODAL */}
      {showBranchStock && selectedItemForStock && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-lg w-full max-w-3xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between px-4 py-3 border-b border-red-900/30">
              <h3 className="text-lg font-bold text-amber-100">
                Stok Per Cabang: {selectedItemForStock.name}
              </h3>
              <button onClick={() => setShowBranchStock(false)} className="text-gray-400 hover:text-white">
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="p-4">
              <p className="text-sm text-gray-400 mb-4">
                Atur stok minimum dan maksimum untuk setiap cabang
              </p>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-red-900/30">
                    <tr>
                      <th className="px-3 py-2 text-left text-amber-200">Cabang</th>
                      <th className="px-3 py-2 text-right text-amber-200">Stok Saat Ini</th>
                      <th className="px-3 py-2 text-right text-amber-200">Stok Minimum</th>
                      <th className="px-3 py-2 text-right text-amber-200">Stok Maksimum</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-red-900/20">
                    {branchStockData.map(bs => (
                      <tr key={bs.branch_id} className="hover:bg-red-900/10">
                        <td className="px-3 py-2 text-gray-200">{bs.branch_name}</td>
                        <td className="px-3 py-2">
                          <input
                            type="number"
                            value={bs.stock_current}
                            onChange={(e) => updateBranchStockValue(bs.branch_id, 'stock_current', e.target.value)}
                            className="w-20 px-2 py-1 bg-[#0a0608] border border-red-900/30 rounded text-gray-200 text-right text-sm"
                          />
                        </td>
                        <td className="px-3 py-2">
                          <input
                            type="number"
                            value={bs.stock_minimum}
                            onChange={(e) => updateBranchStockValue(bs.branch_id, 'stock_minimum', e.target.value)}
                            className="w-20 px-2 py-1 bg-[#0a0608] border border-red-900/30 rounded text-gray-200 text-right text-sm"
                          />
                        </td>
                        <td className="px-3 py-2">
                          <input
                            type="number"
                            value={bs.stock_maximum}
                            onChange={(e) => updateBranchStockValue(bs.branch_id, 'stock_maximum', e.target.value)}
                            className="w-20 px-2 py-1 bg-[#0a0608] border border-red-900/30 rounded text-gray-200 text-right text-sm"
                          />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="flex gap-2 mt-4 pt-4 border-t border-red-900/30">
                <button
                  type="button"
                  onClick={() => setShowBranchStock(false)}
                  className="flex-1 px-4 py-2 bg-gray-700 text-white rounded hover:bg-gray-600"
                >
                  Batal
                </button>
                <button
                  type="button"
                  onClick={saveBranchStock}
                  className="flex-1 px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700"
                >
                  Simpan Stok Cabang
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MasterItems;
