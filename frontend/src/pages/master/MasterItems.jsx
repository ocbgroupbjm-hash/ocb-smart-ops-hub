import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { usePermission, PermissionGate } from '../../contexts/PermissionContext';
import { 
  Package, Plus, Search, RefreshCw, Download, Upload, Edit2, Trash2, 
  Eye, Barcode, Loader2, X, ChevronLeft, ChevronRight, Printer, Settings,
  Filter, FileSpreadsheet, FileText, Camera, ImagePlus, Wand2, Sparkles,
  DollarSign
} from 'lucide-react';
import { toast } from 'sonner';
import { PricingConfigModal } from '../../components/pricing';
import { ItemFormModal } from '../../components/master';
import { OwnerEditButton, OwnerEditModal } from '../../components/OwnerEditButton';
import ERPActionToolbar from '../../components/ERPActionToolbar';
import StockCardModal from '../../components/StockCardModal';

const MasterItems = () => {
  const { api, token, user } = useAuth();
  const { hasPermission } = usePermission();
  
  // Data states
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [categories, setCategories] = useState([]);
  const [units, setUnits] = useState([]);
  const [brands, setBrands] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [branches, setBranches] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  
  // Filter states - COMPREHENSIVE like ERP desktop
  const [filters, setFilters] = useState({
    keyword: '',
    itemType: 'semua', // barang, jasa, rakitan, non-inventory, biaya, semua
    branch: '', // CABANG sebagai lokasi utama (bukan gudang)
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
  
  // AI Photo Studio states
  const [showPhotoStudio, setShowPhotoStudio] = useState(false);
  const [selectedItemForPhoto, setSelectedItemForPhoto] = useState(null);
  const [itemImages, setItemImages] = useState([]);
  const [photoUploading, setPhotoUploading] = useState(false);
  const [aiProcessing, setAiProcessing] = useState(false);
  const [selectedImage, setSelectedImage] = useState(null);
  const [enhancedImage, setEnhancedImage] = useState(null);
  
  // Owner edit states
  const [showOwnerEdit, setShowOwnerEdit] = useState(false);
  const [ownerEditItem, setOwnerEditItem] = useState(null);
  
  // Pricing Modal states
  const [showPricingModal, setShowPricingModal] = useState(false);
  const [selectedItemForPricing, setSelectedItemForPricing] = useState(null);
  
  // Selected row for toolbar actions
  const [selectedItem, setSelectedItem] = useState(null);
  
  // Stock Card Modal
  const [showStockCard, setShowStockCard] = useState(false);
  const [stockCardItem, setStockCardItem] = useState(null);
  
  // Form data
  const [formData, setFormData] = useState({
    code: '',
    barcode: '',
    name: '',
    category_id: '',
    unit_id: '',
    brand_id: '',
    branch_id: '', // CABANG sebagai lokasi utama
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
      if (filters.branch) params.append('branch_id', filters.branch);
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
      const [catRes, unitRes, brandRes, whRes, branchRes, suppRes] = await Promise.all([
        api('/api/master/categories'),
        api('/api/master/units'),
        api('/api/master/brands'),
        api('/api/master/warehouses'),
        api('/api/global-map/branches'),
        api('/api/suppliers')
      ]);
      if (catRes.ok) setCategories(await catRes.json());
      if (unitRes.ok) setUnits(await unitRes.json());
      if (brandRes.ok) setBrands(await brandRes.json());
      if (whRes.ok) setWarehouses(await whRes.json());
      if (branchRes.ok) {
        const data = await branchRes.json();
        setBranches(data.branches || []);
      }
      if (suppRes.ok) {
        const data = await suppRes.json();
        // Handle both response formats: {items: []} or {suppliers: []}
        setSuppliers(data.items || data.suppliers || []);
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
      branch: '',
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
  const handleDelete = async (item) => {
    if (!confirm(`Hapus item "${item.name}"?`)) return;
    try {
      const res = await api(`/api/master/items/${item.id}`, { method: 'DELETE' });
      if (res.ok) {
        toast.success('Item berhasil dihapus');
        setSelectedItem(null);
        loadItems();
      }
    } catch (err) {
      toast.error('Gagal menghapus item');
    }
  };

  const handleEdit = (item) => {
    setEditingItem(item);
    setShowModal(true);
  };

  // Duplikasi item - generate kode baru otomatis
  const handleDuplicate = async (item) => {
    try {
      // Get next item code from number settings
      const codeRes = await api('/api/number-settings/generate/item');
      let newCode = item.code + '-DUP';
      if (codeRes.ok) {
        const codeData = await codeRes.json();
        newCode = codeData.number || codeData.generated_number || newCode;
      }
      
      // Create duplicate with new code
      const duplicateData = {
        code: newCode,
        barcode: '', // Clear barcode, user must set new one
        name: item.name + ' (Duplikat)',
        category_id: item.category_id,
        unit_id: item.unit_id,
        brand_id: item.brand_id,
        branch_id: item.branch_id,
        rack: item.rack,
        item_type: item.item_type,
        cost_price: item.cost_price,
        selling_price: item.selling_price,
        description: item.description,
        is_active: true,
        track_stock: item.track_stock,
        discontinued: false,
        min_stock: item.min_stock,
        max_stock: item.max_stock,
        pricing_mode: item.pricing_mode
      };
      
      // Open form with duplicate data for user to review/edit before saving
      setEditingItem(null);
      setFormData(duplicateData);
      setShowModal(true);
      toast.info('Data item diduplikasi. Silakan review dan simpan.');
    } catch (err) {
      toast.error('Gagal menduplikasi item');
    }
  };

  // Kartu Stok handler
  const handleStockCard = (item) => {
    setStockCardItem(item);
    setShowStockCard(true);
  };

  // Import handler
  const handleImport = () => {
    // Navigate to import page or open import modal
    window.location.href = '/import?type=items';
  };

  // Row selection handler
  const handleRowSelect = (item) => {
    if (selectedItem?.id === item.id) {
      setSelectedItem(null); // Deselect if same row clicked
    } else {
      setSelectedItem(item);
    }
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

  // AI Photo Studio Functions
  const openPhotoStudio = async (item) => {
    setSelectedItemForPhoto(item);
    setSelectedImage(null);
    setEnhancedImage(null);
    try {
      const res = await api(`/api/ai-photo-studio/images/${item.id}`);
      if (res.ok) {
        const data = await res.json();
        setItemImages(data.images || []);
      } else {
        setItemImages([]);
      }
    } catch (err) {
      setItemImages([]);
    }
    setShowPhotoStudio(true);
  };

  const handlePhotoUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    setPhotoUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('is_main', 'true');
      
      // Untuk FormData, gunakan fetch langsung dengan Authorization header only
      // Jangan set Content-Type karena browser harus set multipart/form-data dengan boundary
      const API_URL = process.env.REACT_APP_BACKEND_URL;
      const token = localStorage.getItem('token');
      
      const res = await fetch(`${API_URL}/api/ai-photo-studio/upload/${selectedItemForPhoto.id}`, {
        method: 'POST',
        body: formData,
        headers: {
          'Authorization': `Bearer ${token}`
          // Content-Type TIDAK boleh di-set manual untuk FormData
        }
      });
      
      if (res.ok) {
        toast.success('Foto berhasil diupload');
        // Reload images
        const imgRes = await api(`/api/ai-photo-studio/images/${selectedItemForPhoto.id}`);
        if (imgRes.ok) {
          const data = await imgRes.json();
          setItemImages(data.images || []);
        }
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Gagal upload foto');
      }
    } catch (err) {
      console.error('Upload error:', err);
      toast.error('Terjadi kesalahan saat upload');
    } finally {
      setPhotoUploading(false);
    }
  };

  const enhanceWithAI = async (enhancementType) => {
    if (!selectedImage) {
      toast.error('Pilih foto terlebih dahulu');
      return;
    }
    
    setAiProcessing(true);
    try {
      const res = await api('/api/ai-photo-studio/enhance', {
        method: 'POST',
        body: JSON.stringify({
          image_base64: selectedImage.image_data,
          enhancement_type: enhancementType,
          mode: 'marketplace'
        })
      });
      
      if (res.ok) {
        const data = await res.json();
        setEnhancedImage(data.enhanced_image);
        toast.success(`Foto berhasil di-${enhancementType}`);
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Gagal memproses foto');
      }
    } catch (err) {
      toast.error('Terjadi kesalahan saat memproses AI');
    } finally {
      setAiProcessing(false);
    }
  };

  const saveEnhancedPhoto = async () => {
    if (!enhancedImage) {
      toast.error('Tidak ada foto yang diproses');
      return;
    }
    
    try {
      const formData = new FormData();
      formData.append('image_base64', enhancedImage);
      formData.append('enhancement_type', 'enhanced');
      formData.append('mode', 'marketplace');
      formData.append('is_main', 'false');
      
      // Gunakan fetch langsung seperti upload
      const API_URL = process.env.REACT_APP_BACKEND_URL;
      const token = localStorage.getItem('token');
      
      const res = await fetch(`${API_URL}/api/ai-photo-studio/save-enhanced/${selectedItemForPhoto.id}`, {
        method: 'POST',
        body: formData,
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (res.ok) {
        toast.success('Foto AI berhasil disimpan');
        // Reload images
        const imgRes = await api(`/api/ai-photo-studio/images/${selectedItemForPhoto.id}`);
        if (imgRes.ok) {
          const data = await imgRes.json();
          setItemImages(data.images || []);
        }
        setEnhancedImage(null);
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Gagal menyimpan foto');
      }
    } catch (err) {
      console.error('Save error:', err);
      toast.error('Terjadi kesalahan');
    }
  };

  const deleteImage = async (imageId) => {
    if (!confirm('Hapus foto ini?')) return;
    try {
      const res = await api(`/api/ai-photo-studio/images/${imageId}`, { method: 'DELETE' });
      if (res.ok) {
        toast.success('Foto berhasil dihapus');
        setItemImages(prev => prev.filter(img => img.id !== imageId));
        if (selectedImage?.id === imageId) {
          setSelectedImage(null);
          setEnhancedImage(null);
        }
      }
    } catch (err) {
      toast.error('Gagal menghapus foto');
    }
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
          {hasPermission('master_item', 'create') && (
            <button
              onClick={() => { setEditingItem(null); setShowModal(true); }}
              className="px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700 flex items-center gap-1"
              data-testid="btn-add"
            >
              <Plus className="h-3 w-3" /> Tambah Item
            </button>
          )}
        </div>

        {/* BARIS 2: Tipe Item + Cabang + Jenis + Pilihan Item */}
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
            <span className="text-xs text-gray-400">Cabang</span>
            <select
              value={filters.branch}
              onChange={(e) => handleFilterChange('branch', e.target.value)}
              className="px-2 py-1 text-xs bg-[#0a0608] border border-red-900/30 rounded text-gray-200 w-32"
              data-testid="filter-branch"
            >
              <option value="">Semua</option>
              {branches.map(b => (
                <option key={b.id} value={b.id}>{b.name}</option>
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

      {/* TOOLBAR STANDAR ERP - Di Atas Tabel */}
      <ERPActionToolbar
        module="master_item"
        selectedItem={selectedItem}
        onAdd={() => { setEditingItem(null); setFormData({
          code: '', barcode: '', name: '', category_id: '', unit_id: '', brand_id: '',
          branch_id: '', rack: '', item_type: 'barang', cost_price: 0, selling_price: 0,
          description: '', is_active: true, track_stock: true, discontinued: false
        }); setShowModal(true); }}
        onEdit={(item) => handleEdit(item)}
        onDelete={(item) => handleDelete(item)}
        onDuplicate={(item) => handleDuplicate(item)}
        onStockCard={(item) => handleStockCard(item)}
        onImport={handleImport}
        onExport={() => handleExport('xlsx')}
        addLabel="Item Baru"
        editLabel="Edit Item"
        deleteLabel="Hapus Item"
      />

      {/* DATA TABLE - Compact ERP Style */}
      <div className="bg-[#1a1214] border border-red-900/30 rounded-lg overflow-hidden">
        <div className="overflow-x-auto" style={{ maxHeight: 'calc(100vh - 340px)' }}>
          <table className="w-full text-xs">
            <thead className="bg-red-900/30 sticky top-0">
              <tr>
                <th className="px-2 py-2 text-center text-amber-200 font-semibold w-8">
                  <input type="checkbox" className="w-3 h-3" disabled title="Pilih baris dengan klik" />
                </th>
                <th className="px-2 py-2 text-left text-amber-200 font-semibold">KODE</th>
                <th className="px-2 py-2 text-left text-amber-200 font-semibold">BARCODE</th>
                <th className="px-2 py-2 text-left text-amber-200 font-semibold">NAMA ITEM</th>
                <th className="px-2 py-2 text-left text-amber-200 font-semibold">TIPE</th>
                <th className="px-2 py-2 text-left text-amber-200 font-semibold">CABANG</th>
                <th className="px-2 py-2 text-left text-amber-200 font-semibold">RAK</th>
                <th className="px-2 py-2 text-left text-amber-200 font-semibold">MEREK</th>
                <th className="px-2 py-2 text-right text-amber-200 font-semibold">H.BELI</th>
                <th className="px-2 py-2 text-right text-amber-200 font-semibold">H.JUAL</th>
                <th className="px-2 py-2 text-center text-amber-200 font-semibold">MODE HARGA</th>
                <th className="px-2 py-2 text-right text-amber-200 font-semibold" title="Stok Saat Ini (dari Semua Periode)">STOK SAAT INI</th>
                <th className="px-2 py-2 text-center text-amber-200 font-semibold">STATUS</th>
                <th className="px-2 py-2 text-center text-amber-200 font-semibold">AKSI</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-red-900/20">
              {loading ? (
                <tr>
                  <td colSpan={14} className="px-4 py-8 text-center text-gray-400">
                    <Loader2 className="h-6 w-6 animate-spin mx-auto mb-2" />
                    Memuat data...
                  </td>
                </tr>
              ) : items.length === 0 ? (
                <tr>
                  <td colSpan={14} className="px-4 py-8 text-center text-gray-400">
                    Tidak ada data item ditemukan
                  </td>
                </tr>
              ) : (
                items.map((item, idx) => (
                  <tr 
                    key={item.id} 
                    onClick={() => handleRowSelect(item)}
                    className={`cursor-pointer transition-colors ${
                      selectedItem?.id === item.id 
                        ? 'bg-amber-900/30 border-l-2 border-amber-500' 
                        : idx % 2 === 0 ? 'bg-[#0a0608]/30 hover:bg-red-900/10' : 'hover:bg-red-900/10'
                    }`}
                    data-testid={`item-row-${idx}`}
                  >
                    <td className="px-2 py-1.5 text-center">
                      <input 
                        type="radio" 
                        checked={selectedItem?.id === item.id}
                        onChange={() => handleRowSelect(item)}
                        className="w-3 h-3 accent-amber-500"
                      />
                    </td>
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
                    <td className="px-2 py-1.5 text-gray-400">{item.branch_name || '-'}</td>
                    <td className="px-2 py-1.5 text-gray-400">{item.rack || '-'}</td>
                    <td className="px-2 py-1.5 text-gray-400">{item.brand_name || '-'}</td>
                    <td className="px-2 py-1.5 text-right text-gray-300">{formatCurrency(item.cost_price)}</td>
                    <td className="px-2 py-1.5 text-right text-green-400 font-medium">{formatCurrency(item.selling_price)}</td>
                    <td className="px-2 py-1.5 text-center">
                      <span className={`px-1.5 py-0.5 rounded text-[10px] ${
                        item.pricing_mode === 'quantity' ? 'bg-blue-900/50 text-blue-300' :
                        item.pricing_mode === 'level' ? 'bg-purple-900/50 text-purple-300' :
                        item.pricing_mode === 'unit' ? 'bg-amber-900/50 text-amber-300' :
                        'bg-green-900/50 text-green-300'
                      }`}>
                        {item.pricing_mode === 'quantity' ? 'QTY' :
                         item.pricing_mode === 'level' ? 'LEVEL' :
                         item.pricing_mode === 'unit' ? 'UNIT' : 'SINGLE'}
                      </span>
                    </td>
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
                        {hasPermission('master_item', 'edit') && (
                          <button
                            onClick={() => handleEdit(item)}
                            className="p-1 hover:bg-blue-900/30 rounded text-blue-400"
                            title="Edit"
                          >
                            <Edit2 className="h-3 w-3" />
                          </button>
                        )}
                        {hasPermission('ai_photo_studio', 'view') && (
                          <button
                            onClick={() => openPhotoStudio(item)}
                            className="p-1 hover:bg-amber-900/30 rounded text-amber-400"
                            title="AI Photo Studio"
                          >
                            <Camera className="h-3 w-3" />
                          </button>
                        )}
                        {hasPermission('master_item', 'edit') && (
                          <button
                            onClick={() => {
                              setSelectedItemForPricing(item);
                              setShowPricingModal(true);
                            }}
                            className="p-1 hover:bg-green-900/30 rounded text-green-400"
                            title="Konfigurasi Harga"
                          >
                            <DollarSign className="h-3 w-3" />
                          </button>
                        )}
                        {/* Owner Edit Button */}
                        <OwnerEditButton
                          item={item}
                          module="item"
                          onEdit={(i) => { setOwnerEditItem(i); setShowOwnerEdit(true); }}
                          size="sm"
                          showLabel={false}
                        />
                        <button
                          onClick={() => openBranchStockManager(item)}
                          className="p-1 hover:bg-purple-900/30 rounded text-purple-400"
                          title="Stok Per Cabang"
                        >
                          <Package className="h-3 w-3" />
                        </button>
                        {hasPermission('master_item', 'delete') && (
                          <button
                            onClick={() => handleDelete(item)}
                            className="p-1 hover:bg-red-900/30 rounded text-red-400"
                            title="Hapus"
                          >
                            <Trash2 className="h-3 w-3" />
                          </button>
                        )}
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

      {/* ADD/EDIT MODAL - Using new ItemFormModal component */}
      <ItemFormModal
        isOpen={showModal}
        onClose={() => {
          setShowModal(false);
          setEditingItem(null);
        }}
        editingItem={editingItem}
        token={token}
        categories={categories}
        units={units}
        brands={brands}
        suppliers={suppliers}
        onSave={() => {
          loadItems();
          setShowModal(false);
          setEditingItem(null);
        }}
      />

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
              <div className="mb-4 p-3 bg-blue-900/20 border border-blue-900/30 rounded-lg">
                <p className="text-sm text-blue-300">
                  <strong>Info:</strong> Stok Saat Ini hanya berubah melalui transaksi (Pembelian, Penjualan, Stok Masuk/Keluar, Transfer, Opname). Anda hanya dapat mengatur Stok Minimum dan Maksimum.
                </p>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-red-900/30">
                    <tr>
                      <th className="px-3 py-2 text-left text-amber-200">Cabang</th>
                      <th className="px-3 py-2 text-center text-amber-200">Stok Saat Ini</th>
                      <th className="px-3 py-2 text-right text-amber-200">Stok Minimum</th>
                      <th className="px-3 py-2 text-right text-amber-200">Stok Maksimum</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-red-900/20">
                    {branchStockData.map(bs => (
                      <tr key={bs.branch_id} className="hover:bg-red-900/10">
                        <td className="px-3 py-2 text-gray-200">{bs.branch_name}</td>
                        <td className="px-3 py-2 text-center">
                          {/* STOK SAAT INI - READ ONLY (hanya berubah dari transaksi inventory) */}
                          <span className={`inline-block min-w-[3rem] px-2 py-1 rounded text-sm font-medium text-right ${
                            bs.stock_current <= bs.stock_minimum ? 'bg-red-900/50 text-red-300' :
                            bs.stock_current <= bs.stock_minimum * 2 ? 'bg-yellow-900/50 text-yellow-300' :
                            'bg-green-900/50 text-green-300'
                          }`}>
                            {bs.stock_current || 0}
                          </span>
                        </td>
                        <td className="px-3 py-2">
                          <input
                            type="number"
                            value={bs.stock_minimum}
                            onChange={(e) => updateBranchStockValue(bs.branch_id, 'stock_minimum', e.target.value)}
                            className="w-20 px-2 py-1 bg-[#0a0608] border border-red-900/30 rounded text-gray-200 text-right text-sm"
                            min="0"
                          />
                        </td>
                        <td className="px-3 py-2">
                          <input
                            type="number"
                            value={bs.stock_maximum}
                            onChange={(e) => updateBranchStockValue(bs.branch_id, 'stock_maximum', e.target.value)}
                            className="w-20 px-2 py-1 bg-[#0a0608] border border-red-900/30 rounded text-gray-200 text-right text-sm"
                            min="0"
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

      {/* AI PHOTO STUDIO MODAL */}
      {showPhotoStudio && selectedItemForPhoto && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-lg w-full max-w-5xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between px-4 py-3 border-b border-red-900/30">
              <h3 className="text-lg font-bold text-amber-100 flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-amber-400" />
                AI Photo Studio: {selectedItemForPhoto.name}
              </h3>
              <button onClick={() => setShowPhotoStudio(false)} className="text-gray-400 hover:text-white">
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="p-4">
              {/* Upload Section */}
              <div className="mb-4 p-4 bg-[#0a0608] border border-dashed border-red-900/50 rounded-lg">
                <div className="flex items-center justify-center gap-4">
                  <label className="flex items-center gap-2 px-4 py-2 bg-amber-600 text-white rounded cursor-pointer hover:bg-amber-700">
                    <Upload className="h-4 w-4" />
                    <span>{photoUploading ? 'Uploading...' : 'Upload Foto Produk'}</span>
                    <input 
                      type="file" 
                      accept="image/*" 
                      onChange={handlePhotoUpload}
                      className="hidden"
                      disabled={photoUploading}
                    />
                  </label>
                  <span className="text-sm text-gray-400">Format: JPG, PNG, WEBP (Maks 5MB)</span>
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {/* Left: Image Gallery */}
                <div>
                  <h4 className="text-sm font-semibold text-amber-200 mb-2">Galeri Foto ({itemImages.length})</h4>
                  <div className="grid grid-cols-3 gap-2 max-h-[300px] overflow-y-auto">
                    {itemImages.map(img => (
                      <div 
                        key={img.id} 
                        className={`relative group cursor-pointer border-2 rounded ${selectedImage?.id === img.id ? 'border-amber-500' : 'border-transparent'}`}
                        onClick={() => setSelectedImage(img)}
                      >
                        <img 
                          src={`data:image/png;base64,${img.image_data}`} 
                          alt="Product"
                          className="w-full h-20 object-cover rounded"
                        />
                        {img.ai_generated && (
                          <span className="absolute top-1 left-1 px-1 py-0.5 bg-purple-600 text-white text-[8px] rounded">AI</span>
                        )}
                        {img.is_main && (
                          <span className="absolute top-1 right-1 px-1 py-0.5 bg-green-600 text-white text-[8px] rounded">MAIN</span>
                        )}
                        <button 
                          onClick={(e) => { e.stopPropagation(); deleteImage(img.id); }}
                          className="absolute bottom-1 right-1 p-1 bg-red-600 text-white rounded opacity-0 group-hover:opacity-100"
                        >
                          <Trash2 className="h-3 w-3" />
                        </button>
                      </div>
                    ))}
                    {itemImages.length === 0 && (
                      <div className="col-span-3 text-center py-8 text-gray-500">
                        Belum ada foto. Upload foto produk untuk memulai.
                      </div>
                    )}
                  </div>

                  {/* AI Tools */}
                  {selectedImage ? (
                    <div className="mt-4">
                      <h4 className="text-sm font-semibold text-amber-200 mb-2">
                        AI Enhancement Tools
                        {selectedImage.ai_generated && <span className="ml-2 text-xs text-purple-400">(Re-enhance)</span>}
                      </h4>
                      <div className="grid grid-cols-2 gap-2">
                        <button 
                          onClick={() => enhanceWithAI('enhance')}
                          disabled={aiProcessing}
                          className="flex items-center justify-center gap-2 px-3 py-2 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 disabled:opacity-50"
                        >
                          <Wand2 className="h-4 w-4" />
                          Enhance
                        </button>
                        <button 
                          onClick={() => enhanceWithAI('remove_bg')}
                          disabled={aiProcessing}
                          className="flex items-center justify-center gap-2 px-3 py-2 bg-purple-600 text-white text-sm rounded hover:bg-purple-700 disabled:opacity-50"
                        >
                          <ImagePlus className="h-4 w-4" />
                          Remove BG
                        </button>
                        <button 
                          onClick={() => enhanceWithAI('white_bg')}
                          disabled={aiProcessing}
                          className="flex items-center justify-center gap-2 px-3 py-2 bg-green-600 text-white text-sm rounded hover:bg-green-700 disabled:opacity-50"
                        >
                          <Sparkles className="h-4 w-4" />
                          White BG
                        </button>
                        <button 
                          onClick={() => enhanceWithAI('catalog')}
                          disabled={aiProcessing}
                          className="flex items-center justify-center gap-2 px-3 py-2 bg-amber-600 text-white text-sm rounded hover:bg-amber-700 disabled:opacity-50"
                        >
                          <Camera className="h-4 w-4" />
                          Catalog
                        </button>
                      </div>
                      {aiProcessing && (
                        <div className="mt-2 flex items-center justify-center gap-2 text-amber-400">
                          <Loader2 className="h-4 w-4 animate-spin" />
                          Memproses dengan AI...
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="mt-4 p-4 bg-blue-900/20 border border-blue-900/30 rounded-lg text-center">
                      <p className="text-sm text-blue-300">
                        Pilih foto dari galeri untuk mengaktifkan AI Enhancement Tools
                      </p>
                    </div>
                  )}
                </div>

                {/* Right: Preview / Comparison */}
                <div>
                  <h4 className="text-sm font-semibold text-amber-200 mb-2">Preview & Perbandingan</h4>
                  <div className="grid grid-cols-2 gap-2">
                    <div className="bg-[#0a0608] border border-red-900/30 rounded p-2">
                      <p className="text-xs text-gray-400 mb-1 text-center">Original</p>
                      {selectedImage ? (
                        <img 
                          src={`data:image/png;base64,${selectedImage.image_data}`}
                          alt="Original"
                          className="w-full h-48 object-contain"
                        />
                      ) : (
                        <div className="w-full h-48 flex items-center justify-center text-gray-600">
                          Pilih foto
                        </div>
                      )}
                    </div>
                    <div className="bg-[#0a0608] border border-red-900/30 rounded p-2">
                      <p className="text-xs text-gray-400 mb-1 text-center">AI Enhanced</p>
                      {enhancedImage ? (
                        <img 
                          src={`data:image/png;base64,${enhancedImage}`}
                          alt="Enhanced"
                          className="w-full h-48 object-contain"
                        />
                      ) : (
                        <div className="w-full h-48 flex items-center justify-center text-gray-600">
                          Hasil AI
                        </div>
                      )}
                    </div>
                  </div>
                  
                  {enhancedImage && (
                    <button 
                      onClick={saveEnhancedPhoto}
                      className="w-full mt-2 px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
                    >
                      Simpan Foto AI ke Galeri
                    </button>
                  )}
                </div>
              </div>

              <div className="flex gap-2 mt-4 pt-4 border-t border-red-900/30">
                <button
                  type="button"
                  onClick={() => setShowPhotoStudio(false)}
                  className="flex-1 px-4 py-2 bg-gray-700 text-white rounded hover:bg-gray-600"
                >
                  Tutup
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Pricing Configuration Modal */}
      <PricingConfigModal
        isOpen={showPricingModal}
        onClose={() => {
          setShowPricingModal(false);
          setSelectedItemForPricing(null);
        }}
        product={selectedItemForPricing}
        token={token}
        units={units}
        onSave={() => {
          loadItems();
        }}
      />
      
      {/* Owner Edit Modal */}
      <OwnerEditModal
        isOpen={showOwnerEdit}
        onClose={() => { setShowOwnerEdit(false); setOwnerEditItem(null); }}
        module="item"
        item={ownerEditItem}
        fields={[
          { name: 'name', label: 'Nama Produk', type: 'text' },
          { name: 'cost_price', label: 'Harga Beli (Rp)', type: 'number' },
          { name: 'selling_price', label: 'Harga Jual (Rp)', type: 'number' },
          { name: 'min_stock', label: 'Stok Minimum', type: 'number' }
        ]}
        onSave={() => { setShowOwnerEdit(false); setOwnerEditItem(null); loadItems(); }}
      />
      
      {/* Stock Card Modal - Kartu Stok dari stock_movements SSOT */}
      <StockCardModal
        isOpen={showStockCard}
        onClose={() => { setShowStockCard(false); setStockCardItem(null); }}
        item={stockCardItem}
      />
    </div>
  );
};

export default MasterItems;
