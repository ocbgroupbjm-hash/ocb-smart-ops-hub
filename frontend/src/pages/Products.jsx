import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Plus, Search, Edit, Trash2, Package, X, Save, Loader2, BarChart3, Upload, Image, Camera, Sparkles, Star, StarOff, Eye, Building2, Filter } from 'lucide-react';
import { toast } from 'sonner';

import { getApiUrl } from '../utils/apiConfig';
const API_URL = getApiUrl();

const Products = () => {
  const { api } = useAuth();
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [branches, setBranches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [branchFilter, setBranchFilter] = useState('');
  const [brandFilter, setBrandFilter] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [showCategoryModal, setShowCategoryModal] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    code: '', barcode: '', name: '', description: '', category_id: '', brand: '', unit: 'pcs',
    cost_price: 0, selling_price: 0, wholesale_price: 0, member_price: 0, reseller_price: 0, min_stock: 5
  });
  const [categoryForm, setCategoryForm] = useState({ code: '', name: '', description: '' });
  
  // Photo upload states
  const fileInputRef = useRef(null);
  const [productPhotos, setProductPhotos] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [enhancing, setEnhancing] = useState(null);
  const [showPhotoModal, setShowPhotoModal] = useState(false);
  const [selectedProductForPhoto, setSelectedProductForPhoto] = useState(null);

  const formatRupiah = (num) => `Rp ${(num || 0).toLocaleString('id-ID')}`;

  useEffect(() => { loadProducts(); loadCategories(); loadBranches(); }, [search, categoryFilter, branchFilter, brandFilter]);

  const loadProducts = async () => {
    setLoading(true);
    try {
      let url = `/api/products?limit=200`;
      if (search) url += `&search=${encodeURIComponent(search)}`;
      if (categoryFilter) url += `&category_id=${categoryFilter}`;
      if (branchFilter) url += `&branch_id=${branchFilter}`;
      if (brandFilter) url += `&brand=${encodeURIComponent(brandFilter)}`;
      const res = await api(url);
      if (res.ok) { const data = await res.json(); setProducts(data.items || []); }
    } catch (err) { toast.error('Gagal memuat produk'); }
    finally { setLoading(false); }
  };

  const loadCategories = async () => {
    try {
      const res = await api('/api/products/categories');
      if (res.ok) setCategories(await res.json());
    } catch (err) { console.error(err); }
  };

  const loadBranches = async () => {
    try {
      const res = await api('/api/master/warehouses');
      if (res.ok) setBranches(await res.json());
    } catch (err) { console.error(err); }
  };

  const openModal = (product = null) => {
    if (product) { setEditingProduct(product); setForm({ ...product }); }
    else {
      setEditingProduct(null);
      setForm({ code: '', barcode: '', name: '', description: '', category_id: '', brand: '', unit: 'pcs', cost_price: 0, selling_price: 0, wholesale_price: 0, member_price: 0, reseller_price: 0, min_stock: 5 });
      setPendingPhotos([]);  // Reset pending photos when opening new product modal
    }
    setShowModal(true);
  };

  // New product with photos - state for pending uploads when creating new product
  const [pendingPhotos, setPendingPhotos] = useState([]);
  const [newProductPhotoRef, setNewProductPhotoRef] = useState(null);
  const newProductFileInputRef = useRef(null);

  const handleNewProductPhotoSelect = (e) => {
    const files = Array.from(e.target.files || []);
    if (files.length === 0) return;
    
    // Create preview objects
    const newPhotos = files.map((file, idx) => ({
      id: `pending-${Date.now()}-${idx}`,
      file: file,
      preview: URL.createObjectURL(file),
      is_primary: pendingPhotos.length === 0 && idx === 0
    }));
    
    setPendingPhotos(prev => [...prev, ...newPhotos]);
    if (newProductFileInputRef.current) {
      newProductFileInputRef.current.value = '';
    }
  };

  const removePendingPhoto = (photoId) => {
    setPendingPhotos(prev => {
      const filtered = prev.filter(p => p.id !== photoId);
      // If removed photo was primary and others exist, make first one primary
      if (filtered.length > 0 && !filtered.some(p => p.is_primary)) {
        filtered[0].is_primary = true;
      }
      return filtered;
    });
  };

  const setPendingPrimary = (photoId) => {
    setPendingPhotos(prev => prev.map(p => ({
      ...p,
      is_primary: p.id === photoId
    })));
  };

  const uploadPendingPhotos = async (productId) => {
    if (pendingPhotos.length === 0) return;
    
    for (const photo of pendingPhotos) {
      const formData = new FormData();
      formData.append('file', photo.file);
      formData.append('product_id', productId);
      formData.append('is_primary', photo.is_primary ? 'true' : 'false');
      
      try {
        await fetch(`${API_URL}/api/files/products/photo`, {
          method: 'POST',
          body: formData
        });
      } catch (err) {
        console.error('Upload error:', err);
      }
    }
    
    setPendingPhotos([]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.name || !form.selling_price) { toast.error('Nama dan harga jual wajib diisi'); return; }
    setSaving(true);
    try {
      const url = editingProduct ? `/api/products/${editingProduct.id}` : '/api/products';
      const method = editingProduct ? 'PUT' : 'POST';
      const res = await api(url, { method, body: JSON.stringify(form) });
      if (res.ok) {
        const result = await res.json();
        
        // If creating new product and has pending photos, upload them
        if (!editingProduct && pendingPhotos.length > 0 && result.id) {
          toast.info('Mengupload foto...');
          await uploadPendingPhotos(result.id);
        }
        
        toast.success(editingProduct ? 'Produk diperbarui' : 'Produk ditambahkan'); 
        setShowModal(false); 
        setPendingPhotos([]);
        loadProducts(); 
      }
      else { const error = await res.json(); toast.error(error.detail || 'Gagal menyimpan'); }
    } catch (err) { toast.error('Gagal menyimpan'); }
    finally { setSaving(false); }
  };

  const handleCategorySubmit = async (e) => {
    e.preventDefault();
    if (!categoryForm.code || !categoryForm.name) { toast.error('Kode dan nama kategori wajib diisi'); return; }
    try {
      const res = await api('/api/products/categories', { method: 'POST', body: JSON.stringify(categoryForm) });
      if (res.ok) { toast.success('Kategori ditambahkan'); setShowCategoryModal(false); loadCategories(); setCategoryForm({ code: '', name: '', description: '' }); }
      else { const error = await res.json(); toast.error(error.detail || 'Gagal menyimpan kategori'); }
    } catch (err) { toast.error('Gagal menyimpan kategori'); }
  };

  const deleteProduct = async (id) => {
    if (!window.confirm('Hapus produk ini?')) return;
    try {
      const res = await api(`/api/products/${id}`, { method: 'DELETE' });
      if (res.ok) { toast.success('Produk dihapus'); loadProducts(); }
    } catch (err) { toast.error('Gagal menghapus'); }
  };

  // Photo functions
  const loadProductPhotos = async (productId) => {
    try {
      const res = await fetch(`${API_URL}/api/files/products/photos/${productId}`);
      if (res.ok) {
        const data = await res.json();
        setProductPhotos(data.photos || []);
      }
    } catch (err) {
      console.error('Error loading photos:', err);
      setProductPhotos([]);
    }
  };

  const openPhotoModal = async (product) => {
    setSelectedProductForPhoto(product);
    await loadProductPhotos(product.id);
    setShowPhotoModal(true);
  };

  const handlePhotoUpload = async (e) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    
    setUploading(true);
    let successCount = 0;
    
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      const formData = new FormData();
      formData.append('file', file);
      formData.append('product_id', selectedProductForPhoto.id);
      formData.append('is_primary', productPhotos.length === 0 && i === 0 ? 'true' : 'false');
      
      try {
        const res = await fetch(`${API_URL}/api/files/products/photo`, {
          method: 'POST',
          body: formData
        });
        
        if (res.ok) {
          successCount++;
        }
      } catch (err) {
        console.error('Upload error:', err);
      }
    }
    
    if (successCount > 0) {
      toast.success(`${successCount} foto berhasil diupload`);
      await loadProductPhotos(selectedProductForPhoto.id);
      loadProducts(); // Refresh product list to show photos
    }
    
    setUploading(false);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const setPrimaryPhoto = async (photoId) => {
    try {
      const res = await fetch(`${API_URL}/api/files/products/photo/${photoId}/primary`, {
        method: 'PUT'
      });
      
      if (res.ok) {
        toast.success('Foto utama berhasil diubah');
        await loadProductPhotos(selectedProductForPhoto.id);
        loadProducts();
      }
    } catch (err) {
      toast.error('Gagal mengubah foto utama');
    }
  };

  const deletePhoto = async (photoId) => {
    if (!window.confirm('Hapus foto ini?')) return;
    
    try {
      const res = await fetch(`${API_URL}/api/files/products/photo/${photoId}`, {
        method: 'DELETE'
      });
      
      if (res.ok) {
        toast.success('Foto dihapus');
        await loadProductPhotos(selectedProductForPhoto.id);
        loadProducts();
      }
    } catch (err) {
      toast.error('Gagal menghapus foto');
    }
  };

  const enhancePhoto = async (photoId) => {
    setEnhancing(photoId);
    try {
      const res = await fetch(`${API_URL}/api/files/products/photo/${photoId}/enhance?enhancement_type=auto`, {
        method: 'POST'
      });
      
      const data = await res.json();
      if (res.ok) {
        toast.success('Enhancement diproses');
        toast.info(data.note || 'AI enhancement membutuhkan konfigurasi API key');
        await loadProductPhotos(selectedProductForPhoto.id);
      }
    } catch (err) {
      toast.error('Gagal enhance foto');
    } finally {
      setEnhancing(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Produk</h1>
          <p className="text-gray-400">Kelola katalog produk toko</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => setShowCategoryModal(true)} className="px-4 py-2 border border-red-900/30 text-gray-300 rounded-lg hover:bg-red-900/20 flex items-center gap-2">
            <BarChart3 className="h-5 w-5" /> Kategori
          </button>
          <button onClick={() => openModal()} className="px-4 py-2 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg hover:from-red-500 hover:to-amber-500 flex items-center gap-2">
            <Plus className="h-5 w-5" /> Tambah Produk
          </button>
        </div>
      </div>

      {/* Filters Section */}
      <div className="space-y-3">
        <div className="flex gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input type="text" placeholder="Cari kode, barcode, nama produk..." value={search} onChange={(e) => setSearch(e.target.value)} className="w-full pl-10 pr-4 py-2 bg-[#1a1214] border border-red-900/30 rounded-lg" data-testid="product-search" />
          </div>
          <select value={categoryFilter} onChange={(e) => setCategoryFilter(e.target.value)} className="px-4 py-2 bg-[#1a1214] border border-red-900/30 rounded-lg" data-testid="category-filter">
            <option value="">Semua Kategori</option>
            {categories.map(cat => <option key={cat.id} value={cat.id}>{cat.name}</option>)}
          </select>
          <button 
            onClick={() => setShowFilters(!showFilters)} 
            className={`px-4 py-2 border rounded-lg flex items-center gap-2 ${showFilters ? 'border-amber-500 text-amber-400 bg-amber-900/20' : 'border-red-900/30 text-gray-300 hover:bg-red-900/20'}`}
            data-testid="toggle-filters"
          >
            <Filter className="h-5 w-5" /> Filter
          </button>
        </div>

        {/* Extended Filters */}
        {showFilters && (
          <div className="grid grid-cols-4 gap-3 p-4 bg-[#1a1214] border border-red-900/30 rounded-lg">
            <div>
              <label className="block text-xs text-gray-400 mb-1">Cabang/Gudang</label>
              <select 
                value={branchFilter} 
                onChange={(e) => setBranchFilter(e.target.value)} 
                className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-sm"
                data-testid="branch-filter"
              >
                <option value="">Semua Cabang (Agregasi)</option>
                {branches.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Merek</label>
              <input 
                type="text" 
                value={brandFilter} 
                onChange={(e) => setBrandFilter(e.target.value)} 
                placeholder="Filter merek..."
                className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-sm"
                data-testid="brand-filter"
              />
            </div>
            <div className="col-span-2 flex items-end gap-2">
              <button 
                onClick={() => { setBranchFilter(''); setBrandFilter(''); setCategoryFilter(''); setSearch(''); }}
                className="px-4 py-2 border border-red-900/30 rounded-lg text-gray-400 hover:bg-red-900/20 text-sm"
              >
                Reset Filter
              </button>
              {branchFilter && (
                <span className="text-xs text-amber-400 flex items-center gap-1">
                  <Building2 className="h-3 w-3" />
                  Menampilkan stok untuk: {branches.find(b => b.id === branchFilter)?.name || branchFilter}
                </span>
              )}
            </div>
          </div>
        )}
      </div>

      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
        <table className="w-full">
          <thead className="bg-red-900/20">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-semibold">Produk</th>
              <th className="px-4 py-3 text-left text-sm font-semibold">Kode</th>
              <th className="px-4 py-3 text-right text-sm font-semibold">Modal</th>
              <th className="px-4 py-3 text-right text-sm font-semibold">Harga Jual</th>
              <th className="px-4 py-3 text-right text-sm font-semibold">
                Stok {branchFilter && <span className="text-xs text-amber-400">(Cabang)</span>}
              </th>
              <th className="px-4 py-3 text-center text-sm font-semibold">Status</th>
              <th className="px-4 py-3 text-center text-sm font-semibold">Aksi</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={7} className="px-4 py-8 text-center"><Loader2 className="h-8 w-8 animate-spin mx-auto text-red-400" /></td></tr>
            ) : products.length === 0 ? (
              <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-400"><Package className="h-12 w-12 mx-auto mb-2 opacity-30" /><p>Tidak ada produk</p></td></tr>
            ) : (
              products.map(product => {
                const stock = product.stock || 0;
                const minStock = product.min_stock || 5;
                const stockStatus = stock <= 0 ? 'empty' : stock <= minStock ? 'low' : 'ok';
                
                return (
                  <tr key={product.id} className="border-t border-red-900/10 hover:bg-red-900/10" data-testid={`product-row-${product.id}`}>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        {product.primary_photo_url ? (
                          <img 
                            src={`${API_URL}${product.primary_photo_url}`} 
                            alt={product.name}
                            className="w-12 h-12 rounded-lg object-cover border border-red-900/30"
                          />
                        ) : (
                          <div className="w-12 h-12 rounded-lg bg-red-900/20 flex items-center justify-center border border-red-900/30">
                            <Package className="h-6 w-6 text-gray-500" />
                          </div>
                        )}
                        <div>
                          <div className="font-medium">{product.name}</div>
                          <div className="text-sm text-gray-400">{product.brand || 'Tanpa merk'}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="font-mono">{product.code}</div>
                      <div className="text-sm text-gray-400">{product.barcode || '-'}</div>
                    </td>
                    <td className="px-4 py-3 text-right text-gray-400">{formatRupiah(product.cost_price)}</td>
                    <td className="px-4 py-3 text-right text-amber-400 font-semibold">{formatRupiah(product.selling_price)}</td>
                    <td className="px-4 py-3 text-right">
                      <div className={`font-bold text-lg ${
                        stockStatus === 'empty' ? 'text-red-400' : 
                        stockStatus === 'low' ? 'text-yellow-400' : 'text-green-400'
                      }`}>
                        {stock}
                      </div>
                      {product.branches_count !== undefined && !branchFilter && (
                        <div className="text-xs text-gray-500">{product.branches_count} cabang</div>
                      )}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`px-2 py-1 rounded text-xs ${
                        stockStatus === 'empty' ? 'bg-red-900/30 text-red-400' : 
                        stockStatus === 'low' ? 'bg-yellow-900/30 text-yellow-400' : 'bg-green-900/30 text-green-400'
                      }`}>
                        {stockStatus === 'empty' ? 'Habis' : stockStatus === 'low' ? 'Menipis' : 'Aman'}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex justify-center gap-2">
                        <button onClick={() => openPhotoModal(product)} className="p-2 text-green-400 hover:bg-green-900/20 rounded" title="Foto Produk">
                          <Camera className="h-4 w-4" />
                        </button>
                        <button onClick={() => openModal(product)} className="p-2 text-blue-400 hover:bg-blue-900/20 rounded"><Edit className="h-4 w-4" /></button>
                        <button onClick={() => deleteProduct(product.id)} className="p-2 text-red-400 hover:bg-red-900/20 rounded"><Trash2 className="h-4 w-4" /></button>
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Modal Produk */}
      {showModal && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-red-900/30 flex justify-between items-center sticky top-0 bg-[#1a1214]">
              <h2 className="text-xl font-bold">{editingProduct ? 'Edit Produk' : 'Tambah Produk'}</h2>
              <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-white"><X className="h-6 w-6" /></button>
            </div>
            
            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Nama Produk *</label>
                  <input type="text" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" required />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Kode Produk</label>
                  <input type="text" value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" placeholder="Otomatis jika kosong" />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Barcode</label>
                  <input type="text" value={form.barcode} onChange={(e) => setForm({ ...form, barcode: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Merk</label>
                  <input type="text" value={form.brand} onChange={(e) => setForm({ ...form, brand: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Kategori</label>
                  <select value={form.category_id} onChange={(e) => setForm({ ...form, category_id: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg">
                    <option value="">Pilih Kategori</option>
                    {categories.map(cat => <option key={cat.id} value={cat.id}>{cat.name}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Satuan</label>
                  <select value={form.unit} onChange={(e) => setForm({ ...form, unit: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg">
                    <option value="pcs">Pcs</option>
                    <option value="box">Box</option>
                    <option value="pack">Pack</option>
                    <option value="unit">Unit</option>
                  </select>
                </div>
              </div>

              <div className="border-t border-red-900/30 pt-4">
                <h3 className="text-lg font-semibold mb-3 text-amber-100">Harga</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">Harga Modal</label>
                    <input type="number" value={form.cost_price} onChange={(e) => setForm({ ...form, cost_price: Number(e.target.value) })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">Harga Jual *</label>
                    <input type="number" value={form.selling_price} onChange={(e) => setForm({ ...form, selling_price: Number(e.target.value) })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" required />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">Harga Grosir</label>
                    <input type="number" value={form.wholesale_price} onChange={(e) => setForm({ ...form, wholesale_price: Number(e.target.value) })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">Harga Member</label>
                    <input type="number" value={form.member_price} onChange={(e) => setForm({ ...form, member_price: Number(e.target.value) })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">Harga Reseller</label>
                    <input type="number" value={form.reseller_price} onChange={(e) => setForm({ ...form, reseller_price: Number(e.target.value) })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">Stok Minimum</label>
                    <input type="number" value={form.min_stock} onChange={(e) => setForm({ ...form, min_stock: Number(e.target.value) })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" />
                  </div>
                </div>
              </div>

              {/* Photo Upload Section - Available when adding new product */}
              {!editingProduct && (
                <div className="border-t border-red-900/30 pt-4">
                  <h3 className="text-lg font-semibold mb-3 text-amber-100 flex items-center gap-2">
                    <Camera className="h-5 w-5" /> Foto Produk
                  </h3>
                  
                  <input
                    type="file"
                    ref={newProductFileInputRef}
                    onChange={handleNewProductPhotoSelect}
                    accept="image/jpeg,image/png,image/webp"
                    multiple
                    className="hidden"
                  />
                  
                  <div className="border-2 border-dashed border-red-900/50 rounded-xl p-4 text-center mb-4">
                    <Upload className="h-8 w-8 mx-auto text-gray-500 mb-2" />
                    <p className="text-sm text-gray-400 mb-2">Upload foto produk</p>
                    <button
                      type="button"
                      onClick={() => newProductFileInputRef.current?.click()}
                      className="px-4 py-2 bg-gradient-to-r from-red-600 to-amber-600 text-white text-sm rounded-lg"
                    >
                      <Camera className="h-4 w-4 inline mr-2" /> Pilih Foto
                    </button>
                    <p className="text-xs text-gray-500 mt-2">Format: JPEG, PNG, WEBP. Bisa multiple.</p>
                  </div>

                  {/* Pending Photos Preview */}
                  {pendingPhotos.length > 0 && (
                    <div className="grid grid-cols-3 gap-3">
                      {pendingPhotos.map(photo => (
                        <div key={photo.id} className={`relative rounded-lg overflow-hidden border-2 ${photo.is_primary ? 'border-amber-500' : 'border-red-900/30'}`}>
                          <img src={photo.preview} alt="Preview" className="w-full h-24 object-cover" />
                          {photo.is_primary && (
                            <div className="absolute top-1 left-1 px-1.5 py-0.5 bg-amber-600 text-black text-[10px] font-bold rounded">
                              Utama
                            </div>
                          )}
                          <div className="absolute inset-0 bg-black/50 opacity-0 hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                            {!photo.is_primary && (
                              <button
                                type="button"
                                onClick={() => setPendingPrimary(photo.id)}
                                className="p-1.5 bg-amber-600 rounded text-black"
                                title="Jadikan utama"
                              >
                                <Star className="h-3 w-3" />
                              </button>
                            )}
                            <button
                              type="button"
                              onClick={() => removePendingPhoto(photo.id)}
                              className="p-1.5 bg-red-600 rounded text-white"
                              title="Hapus"
                            >
                              <Trash2 className="h-3 w-3" />
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Note for edit mode */}
              {editingProduct && (
                <div className="border-t border-red-900/30 pt-4">
                  <p className="text-sm text-gray-400 flex items-center gap-2">
                    <Camera className="h-4 w-4" />
                    Untuk kelola foto, klik ikon kamera di tabel setelah menyimpan.
                  </p>
                </div>
              )}

              <div className="flex gap-3 pt-4">
                <button type="button" onClick={() => setShowModal(false)} className="flex-1 py-2 border border-red-900/30 rounded-lg hover:bg-red-900/20">Batal</button>
                <button type="submit" disabled={saving} className="flex-1 py-2 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg disabled:opacity-50 flex items-center justify-center gap-2">
                  {saving ? <Loader2 className="h-5 w-5 animate-spin" /> : <Save className="h-5 w-5" />}
                  {saving ? 'Menyimpan...' : 'Simpan'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal Kategori */}
      {showCategoryModal && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-md">
            <div className="p-6 border-b border-red-900/30 flex justify-between items-center">
              <h2 className="text-xl font-bold">Kategori Produk</h2>
              <button onClick={() => setShowCategoryModal(false)} className="text-gray-400 hover:text-white"><X className="h-6 w-6" /></button>
            </div>
            
            <div className="p-6">
              <div className="space-y-2 max-h-60 overflow-y-auto mb-6">
                {categories.map(cat => (
                  <div key={cat.id} className="p-3 bg-[#0a0608] rounded-lg flex justify-between items-center">
                    <div>
                      <div className="font-medium">{cat.name}</div>
                      <div className="text-sm text-gray-400">{cat.code}</div>
                    </div>
                  </div>
                ))}
                {categories.length === 0 && <p className="text-center text-gray-400 py-4">Belum ada kategori</p>}
              </div>
              
              <form onSubmit={handleCategorySubmit} className="space-y-4 border-t border-red-900/30 pt-4">
                <h3 className="font-semibold">Tambah Kategori Baru</h3>
                <div className="grid grid-cols-2 gap-4">
                  <input type="text" placeholder="Kode" value={categoryForm.code} onChange={(e) => setCategoryForm({ ...categoryForm, code: e.target.value.toUpperCase() })} className="px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" required />
                  <input type="text" placeholder="Nama Kategori" value={categoryForm.name} onChange={(e) => setCategoryForm({ ...categoryForm, name: e.target.value })} className="px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" required />
                </div>
                <button type="submit" className="w-full py-2 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg">Tambah Kategori</button>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Modal Foto Produk */}
      {showPhotoModal && selectedProductForPhoto && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-red-900/30 flex justify-between items-center sticky top-0 bg-[#1a1214]">
              <div>
                <h2 className="text-xl font-bold text-amber-100">Foto Produk</h2>
                <p className="text-sm text-gray-400">{selectedProductForPhoto.name}</p>
              </div>
              <button onClick={() => setShowPhotoModal(false)} className="text-gray-400 hover:text-white"><X className="h-6 w-6" /></button>
            </div>
            
            <div className="p-6">
              {/* Upload Section */}
              <div className="mb-6 p-4 border-2 border-dashed border-red-900/50 rounded-xl text-center">
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handlePhotoUpload}
                  accept="image/jpeg,image/png,image/webp"
                  multiple
                  className="hidden"
                />
                <Upload className="h-12 w-12 mx-auto text-gray-500 mb-3" />
                <p className="text-gray-400 mb-2">Drag & drop atau klik untuk upload foto</p>
                <button
                  onClick={() => fileInputRef.current?.click()}
                  disabled={uploading}
                  className="px-6 py-2 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg disabled:opacity-50"
                >
                  {uploading ? (
                    <span className="flex items-center gap-2">
                      <Loader2 className="h-4 w-4 animate-spin" /> Uploading...
                    </span>
                  ) : (
                    <span className="flex items-center gap-2">
                      <Camera className="h-4 w-4" /> Pilih Foto
                    </span>
                  )}
                </button>
                <p className="text-xs text-gray-500 mt-2">Format: JPEG, PNG, WEBP. Bisa pilih multiple foto.</p>
              </div>

              {/* Photo Grid */}
              {productPhotos.length === 0 ? (
                <div className="text-center py-8 text-gray-400">
                  <Image className="h-16 w-16 mx-auto mb-4 opacity-30" />
                  <p>Belum ada foto untuk produk ini</p>
                </div>
              ) : (
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  {productPhotos.map(photo => (
                    <div key={photo.id} className="relative group">
                      <div className={`border-2 rounded-xl overflow-hidden ${photo.is_primary ? 'border-amber-500' : 'border-red-900/30'}`}>
                        <img
                          src={`${API_URL}${photo.file_url}`}
                          alt="Product photo"
                          className="w-full h-40 object-cover"
                        />
                        
                        {/* Primary badge */}
                        {photo.is_primary && (
                          <div className="absolute top-2 left-2 px-2 py-1 bg-amber-600 text-black text-xs font-bold rounded flex items-center gap-1">
                            <Star className="h-3 w-3" /> Utama
                          </div>
                        )}
                        
                        {/* Enhanced badge */}
                        {photo.is_enhanced && (
                          <div className="absolute top-2 right-2 px-2 py-1 bg-purple-600 text-white text-xs font-bold rounded flex items-center gap-1">
                            <Sparkles className="h-3 w-3" /> AI
                          </div>
                        )}
                        
                        {/* Actions overlay */}
                        <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-all flex items-center justify-center gap-2">
                          {!photo.is_primary && (
                            <button
                              onClick={() => setPrimaryPhoto(photo.id)}
                              className="p-2 bg-amber-600 rounded-lg hover:bg-amber-500"
                              title="Jadikan foto utama"
                            >
                              <Star className="h-5 w-5 text-black" />
                            </button>
                          )}
                          
                          <button
                            onClick={() => enhancePhoto(photo.id)}
                            disabled={enhancing === photo.id}
                            className="p-2 bg-purple-600 rounded-lg hover:bg-purple-500 disabled:opacity-50"
                            title="AI Enhancement"
                          >
                            {enhancing === photo.id ? (
                              <Loader2 className="h-5 w-5 animate-spin" />
                            ) : (
                              <Sparkles className="h-5 w-5" />
                            )}
                          </button>
                          
                          <button
                            onClick={() => window.open(`${API_URL}${photo.file_url}`, '_blank')}
                            className="p-2 bg-blue-600 rounded-lg hover:bg-blue-500"
                            title="Lihat full size"
                          >
                            <Eye className="h-5 w-5" />
                          </button>
                          
                          <button
                            onClick={() => deletePhoto(photo.id)}
                            className="p-2 bg-red-600 rounded-lg hover:bg-red-500"
                            title="Hapus foto"
                          >
                            <Trash2 className="h-5 w-5" />
                          </button>
                        </div>
                      </div>
                      
                      <div className="mt-1 text-xs text-gray-500">
                        {photo.original_filename?.slice(0, 20)}...
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* AI Enhancement Info */}
              <div className="mt-6 p-4 bg-purple-900/20 border border-purple-700/30 rounded-lg">
                <h4 className="font-medium text-purple-400 mb-2 flex items-center gap-2">
                  <Sparkles className="h-4 w-4" /> AI Photo Enhancement
                </h4>
                <p className="text-sm text-gray-400">
                  Klik tombol <Sparkles className="h-4 w-4 inline" /> pada foto untuk memperbaiki:
                </p>
                <ul className="text-sm text-gray-400 mt-2 ml-4 list-disc">
                  <li>Memperjelas foto (sharpen)</li>
                  <li>Memperbaiki pencahayaan</li>
                  <li>Merapikan background</li>
                  <li>Membuat foto lebih menarik untuk katalog</li>
                </ul>
                <p className="text-xs text-yellow-400 mt-2">
                  * Membutuhkan konfigurasi AI API key untuk fitur ini aktif sepenuhnya
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Products;
