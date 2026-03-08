import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Plus, Search, Edit, Trash2, Package, X, Save, Loader2, BarChart3 } from 'lucide-react';
import { toast } from 'sonner';

const Products = () => {
  const { api } = useAuth();
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [showCategoryModal, setShowCategoryModal] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    code: '', barcode: '', name: '', description: '', category_id: '', brand: '', unit: 'pcs',
    cost_price: 0, selling_price: 0, wholesale_price: 0, member_price: 0, reseller_price: 0, min_stock: 5
  });
  const [categoryForm, setCategoryForm] = useState({ code: '', name: '', description: '' });

  const formatRupiah = (num) => `Rp ${(num || 0).toLocaleString('id-ID')}`;

  useEffect(() => { loadProducts(); loadCategories(); }, [search, categoryFilter]);

  const loadProducts = async () => {
    setLoading(true);
    try {
      let url = `/api/products?limit=200`;
      if (search) url += `&search=${encodeURIComponent(search)}`;
      if (categoryFilter) url += `&category_id=${categoryFilter}`;
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

  const openModal = (product = null) => {
    if (product) { setEditingProduct(product); setForm({ ...product }); }
    else {
      setEditingProduct(null);
      setForm({ code: '', barcode: '', name: '', description: '', category_id: '', brand: '', unit: 'pcs', cost_price: 0, selling_price: 0, wholesale_price: 0, member_price: 0, reseller_price: 0, min_stock: 5 });
    }
    setShowModal(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.name || !form.selling_price) { toast.error('Nama dan harga jual wajib diisi'); return; }
    setSaving(true);
    try {
      const url = editingProduct ? `/api/products/${editingProduct.id}` : '/api/products';
      const method = editingProduct ? 'PUT' : 'POST';
      const res = await api(url, { method, body: JSON.stringify(form) });
      if (res.ok) { toast.success(editingProduct ? 'Produk diperbarui' : 'Produk ditambahkan'); setShowModal(false); loadProducts(); }
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

      <div className="flex gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input type="text" placeholder="Cari produk..." value={search} onChange={(e) => setSearch(e.target.value)} className="w-full pl-10 pr-4 py-2 bg-[#1a1214] border border-red-900/30 rounded-lg" />
        </div>
        <select value={categoryFilter} onChange={(e) => setCategoryFilter(e.target.value)} className="px-4 py-2 bg-[#1a1214] border border-red-900/30 rounded-lg">
          <option value="">Semua Kategori</option>
          {categories.map(cat => <option key={cat.id} value={cat.id}>{cat.name}</option>)}
        </select>
      </div>

      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
        <table className="w-full">
          <thead className="bg-red-900/20">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-semibold">Produk</th>
              <th className="px-4 py-3 text-left text-sm font-semibold">Kode</th>
              <th className="px-4 py-3 text-right text-sm font-semibold">Modal</th>
              <th className="px-4 py-3 text-right text-sm font-semibold">Harga Jual</th>
              <th className="px-4 py-3 text-right text-sm font-semibold">Min Stok</th>
              <th className="px-4 py-3 text-center text-sm font-semibold">Aksi</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={6} className="px-4 py-8 text-center"><Loader2 className="h-8 w-8 animate-spin mx-auto text-red-400" /></td></tr>
            ) : products.length === 0 ? (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-400"><Package className="h-12 w-12 mx-auto mb-2 opacity-30" /><p>Tidak ada produk</p></td></tr>
            ) : (
              products.map(product => (
                <tr key={product.id} className="border-t border-red-900/10 hover:bg-red-900/10">
                  <td className="px-4 py-3">
                    <div className="font-medium">{product.name}</div>
                    <div className="text-sm text-gray-400">{product.brand || 'Tanpa merk'}</div>
                  </td>
                  <td className="px-4 py-3">
                    <div>{product.code}</div>
                    <div className="text-sm text-gray-400">{product.barcode || '-'}</div>
                  </td>
                  <td className="px-4 py-3 text-right text-gray-400">{formatRupiah(product.cost_price)}</td>
                  <td className="px-4 py-3 text-right text-amber-400 font-semibold">{formatRupiah(product.selling_price)}</td>
                  <td className="px-4 py-3 text-right">{product.min_stock}</td>
                  <td className="px-4 py-3">
                    <div className="flex justify-center gap-2">
                      <button onClick={() => openModal(product)} className="p-2 text-blue-400 hover:bg-blue-900/20 rounded"><Edit className="h-4 w-4" /></button>
                      <button onClick={() => deleteProduct(product.id)} className="p-2 text-red-400 hover:bg-red-900/20 rounded"><Trash2 className="h-4 w-4" /></button>
                    </div>
                  </td>
                </tr>
              ))
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
    </div>
  );
};

export default Products;
