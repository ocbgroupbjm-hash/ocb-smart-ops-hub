import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { Switch } from '../../components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../../components/ui/dialog';
import { Badge } from '../../components/ui/badge';
import { Plus, Search, Edit2, Trash2, Loader2, Percent, Calendar, Package, Users, Tag, RefreshCw, X } from 'lucide-react';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

const MasterDiscountsAdvanced = () => {
  const { api } = useAuth();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [saving, setSaving] = useState(false);
  
  // Reference data
  const [categories, setCategories] = useState([]);
  const [brands, setBrands] = useState([]);
  const [products, setProducts] = useState([]);
  const [customerGroups, setCustomerGroups] = useState([]);
  const [branches, setBranches] = useState([]);
  
  // Selected targets
  const [selectedProducts, setSelectedProducts] = useState([]);
  const [selectedCategories, setSelectedCategories] = useState([]);
  const [selectedBrands, setSelectedBrands] = useState([]);
  
  const [formData, setFormData] = useState({
    // Basic Info
    code: 'AUTO',
    code_mode: 'auto',
    name: '',
    description: '',
    
    // Discount Type
    discount_type: 'percent', // percent, nominal, per_pcs
    discount_value: 0,
    
    // Basis
    basis: 'per_transaction', // per_transaction, per_item, per_pcs
    
    // Conditions
    min_purchase: 0,
    min_qty: 0,
    max_discount: 0,
    
    // Target
    target_type: 'all', // all, category, brand, product, customer_group, branch
    target_categories: [],
    target_brands: [],
    target_products: [],
    target_customer_groups: [],
    target_branches: [],
    
    // Period
    start_date: '',
    end_date: '',
    start_time: '',
    end_time: '',
    
    // Rules
    priority: 1,
    stackable: false,
    is_active: true
  });

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [res, catRes, brandRes, prodRes, groupRes, branchRes] = await Promise.all([
        api(`/api/master/discounts?search=${searchTerm}`),
        api('/api/master/categories'),
        api('/api/master/brands'),
        api('/api/products?limit=100'),
        api('/api/master/customer-groups'),
        api('/api/master/branches')
      ]);
      
      if (res.ok) setItems(await res.json());
      if (catRes.ok) setCategories(await catRes.json());
      if (brandRes.ok) setBrands(await brandRes.json());
      if (prodRes.ok) {
        const prodData = await prodRes.json();
        setProducts(prodData.items || prodData || []);
      }
      if (groupRes.ok) setCustomerGroups(await groupRes.json());
      if (branchRes.ok) setBranches(await branchRes.json());
    } catch (err) { 
      console.error(err);
      toast.error('Gagal memuat data'); 
    }
    finally { setLoading(false); }
  }, [api, searchTerm]);

  useEffect(() => { loadData(); }, [loadData]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      toast.error('Nama diskon wajib diisi');
      return;
    }
    if (formData.discount_value <= 0) {
      toast.error('Nilai diskon harus lebih dari 0');
      return;
    }
    
    setSaving(true);
    try {
      // Generate auto code if needed
      let finalCode = formData.code;
      if (formData.code === 'AUTO') {
        const genRes = await fetch(`${API}/api/number-settings/generate/transaction`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ module_code: 'DSK' })
        });
        if (genRes.ok) {
          const genData = await genRes.json();
          finalCode = genData.number;
        } else {
          finalCode = `DSK-${Date.now()}`;
        }
      }
      
      const payload = { 
        ...formData, 
        code: finalCode,
        target_products: selectedProducts.map(p => p.id),
        target_categories: selectedCategories.map(c => c.id),
        target_brands: selectedBrands.map(b => b.id)
      };
      
      const url = editingItem ? `/api/master/discounts/${editingItem.id}` : '/api/master/discounts';
      const res = await api(url, { method: editingItem ? 'PUT' : 'POST', body: JSON.stringify(payload) });
      
      if (res.ok) { 
        toast.success(`Diskon ${finalCode} berhasil disimpan`); 
        setShowModal(false); 
        loadData(); 
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Gagal menyimpan');
      }
    } catch (err) { 
      toast.error('Gagal menyimpan: ' + err.message); 
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (item) => { 
    setEditingItem(item); 
    setFormData({
      code: item.code || '',
      code_mode: 'manual',
      name: item.name || '',
      description: item.description || '',
      discount_type: item.discount_type || 'percent',
      discount_value: item.discount_value || 0,
      basis: item.basis || 'per_transaction',
      min_purchase: item.min_purchase || 0,
      min_qty: item.min_qty || 0,
      max_discount: item.max_discount || 0,
      target_type: item.target_type || 'all',
      target_categories: item.target_categories || [],
      target_brands: item.target_brands || [],
      target_products: item.target_products || [],
      target_customer_groups: item.target_customer_groups || [],
      target_branches: item.target_branches || [],
      start_date: item.start_date ? item.start_date.split('T')[0] : '',
      end_date: item.end_date ? item.end_date.split('T')[0] : '',
      start_time: item.start_time || '',
      end_time: item.end_time || '',
      priority: item.priority || 1,
      stackable: item.stackable || false,
      is_active: item.is_active !== false
    });
    
    // Load selected items
    if (item.target_products) {
      setSelectedProducts(products.filter(p => item.target_products.includes(p.id)));
    }
    if (item.target_categories) {
      setSelectedCategories(categories.filter(c => item.target_categories.includes(c.id)));
    }
    if (item.target_brands) {
      setSelectedBrands(brands.filter(b => item.target_brands.includes(b.id)));
    }
    
    setShowModal(true); 
  };

  const handleDelete = async (item) => { 
    if (!window.confirm(`Hapus diskon "${item.name}"?`)) return; 
    try { 
      await api(`/api/master/discounts/${item.id}`, { method: 'DELETE' }); 
      toast.success('Berhasil dihapus'); 
      loadData(); 
    } catch { 
      toast.error('Gagal menghapus'); 
    } 
  };

  const resetForm = () => {
    setEditingItem(null);
    setSelectedProducts([]);
    setSelectedCategories([]);
    setSelectedBrands([]);
    setFormData({
      code: 'AUTO', code_mode: 'auto', name: '', description: '',
      discount_type: 'percent', discount_value: 0, basis: 'per_transaction',
      min_purchase: 0, min_qty: 0, max_discount: 0,
      target_type: 'all', target_categories: [], target_brands: [], target_products: [],
      target_customer_groups: [], target_branches: [],
      start_date: '', end_date: '', start_time: '', end_time: '',
      priority: 1, stackable: false, is_active: true
    });
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(value || 0);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('id-ID');
  };

  const getDiscountTypeLabel = (type) => {
    switch(type) {
      case 'percent': return 'Persentase';
      case 'nominal': return 'Nominal';
      case 'per_pcs': return 'Per Pcs';
      default: return type;
    }
  };

  const getBasisLabel = (basis) => {
    switch(basis) {
      case 'per_transaction': return 'Per Transaksi';
      case 'per_item': return 'Per Item';
      case 'per_pcs': return 'Per Pcs';
      default: return basis;
    }
  };

  const addProduct = (productId) => {
    const product = products.find(p => p.id === productId);
    if (product && !selectedProducts.find(p => p.id === productId)) {
      setSelectedProducts([...selectedProducts, product]);
    }
  };

  const removeProduct = (productId) => {
    setSelectedProducts(selectedProducts.filter(p => p.id !== productId));
  };

  const addCategory = (categoryId) => {
    const category = categories.find(c => c.id === categoryId);
    if (category && !selectedCategories.find(c => c.id === categoryId)) {
      setSelectedCategories([...selectedCategories, category]);
    }
  };

  const removeCategory = (categoryId) => {
    setSelectedCategories(selectedCategories.filter(c => c.id !== categoryId));
  };

  const addBrand = (brandId) => {
    const brand = brands.find(b => b.id === brandId);
    if (brand && !selectedBrands.find(b => b.id === brandId)) {
      setSelectedBrands([...selectedBrands, brand]);
    }
  };

  const removeBrand = (brandId) => {
    setSelectedBrands(selectedBrands.filter(b => b.id !== brandId));
  };

  return (
    <div className="space-y-4" data-testid="discounts-advanced-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Manajemen Diskon</h1>
          <p className="text-gray-400 text-sm">Kelola diskon dengan target produk, kategori, periode, dan aturan lengkap</p>
        </div>
        <Button onClick={() => { resetForm(); setShowModal(true); }} 
          className="bg-gradient-to-r from-red-600 to-amber-600" data-testid="add-discount-btn">
          <Plus className="h-4 w-4 mr-2" /> Tambah Diskon
        </Button>
      </div>

      <Card className="bg-[#1a1214] border-red-900/30">
        <CardContent className="pt-4">
          <div className="flex gap-4">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input type="text" placeholder="Cari diskon..." value={searchTerm} 
                onChange={(e) => setSearchTerm(e.target.value)} 
                className="pl-10 bg-[#0a0608] border-red-900/30" />
            </div>
            <Button variant="outline" onClick={loadData}><RefreshCw className="h-4 w-4" /></Button>
          </div>
        </CardContent>
      </Card>

      <Card className="bg-[#1a1214] border-red-900/30">
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-red-900/20">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">KODE</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">NAMA DISKON</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">JENIS</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-amber-200">NILAI</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">BASIS</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">TARGET</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">PERIODE</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">STATUS</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">AKSI</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-red-900/20">
                {loading ? (
                  <tr><td colSpan={9} className="px-4 py-8 text-center"><Loader2 className="h-8 w-8 animate-spin mx-auto text-amber-400" /></td></tr>
                ) : items.length === 0 ? (
                  <tr><td colSpan={9} className="px-4 py-8 text-center text-gray-400">Belum ada diskon</td></tr>
                ) : items.map(item => (
                  <tr key={item.id} className="hover:bg-red-900/10">
                    <td className="px-4 py-3 text-sm font-mono text-amber-300">{item.code}</td>
                    <td className="px-4 py-3">
                      <div className="font-medium text-gray-200">{item.name}</div>
                      {item.description && <div className="text-xs text-gray-500">{item.description}</div>}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <Badge variant="outline">{getDiscountTypeLabel(item.discount_type)}</Badge>
                    </td>
                    <td className="px-4 py-3 text-right text-amber-300 font-semibold">
                      {item.discount_type === 'percent' ? `${item.discount_value}%` : formatCurrency(item.discount_value)}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <Badge variant="secondary">{getBasisLabel(item.basis)}</Badge>
                    </td>
                    <td className="px-4 py-3 text-center text-sm text-gray-400">
                      {item.target_type === 'all' ? 'Semua' : item.target_type}
                    </td>
                    <td className="px-4 py-3 text-center text-sm text-gray-400">
                      {item.start_date && item.end_date ? (
                        <div className="text-xs">
                          {formatDate(item.start_date)} - {formatDate(item.end_date)}
                        </div>
                      ) : '-'}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <Badge variant={item.is_active ? "default" : "destructive"} className={item.is_active ? "bg-green-600" : ""}>
                        {item.is_active ? 'Aktif' : 'Nonaktif'}
                      </Badge>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-center gap-1">
                        <Button size="sm" variant="ghost" onClick={() => handleEdit(item)} className="text-blue-400">
                          <Edit2 className="h-4 w-4" />
                        </Button>
                        <Button size="sm" variant="ghost" onClick={() => handleDelete(item)} className="text-red-400">
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Discount Form Modal */}
      <Dialog open={showModal} onOpenChange={(open) => !open && setShowModal(false)}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto bg-[#1a1214] border-red-900/30">
          <DialogHeader>
            <DialogTitle className="text-amber-100 flex items-center gap-2">
              <Percent className="h-5 w-5" />
              {editingItem ? 'Edit' : 'Tambah'} Diskon
            </DialogTitle>
          </DialogHeader>
          
          <form onSubmit={handleSubmit}>
            <Tabs defaultValue="basic" className="w-full">
              <TabsList className="grid w-full grid-cols-4 bg-[#0a0608]">
                <TabsTrigger value="basic" className="data-[state=active]:bg-red-900/50">Info Dasar</TabsTrigger>
                <TabsTrigger value="target" className="data-[state=active]:bg-red-900/50">Target</TabsTrigger>
                <TabsTrigger value="condition" className="data-[state=active]:bg-red-900/50">Syarat</TabsTrigger>
                <TabsTrigger value="period" className="data-[state=active]:bg-red-900/50">Periode</TabsTrigger>
              </TabsList>

              {/* Tab: Info Dasar */}
              <TabsContent value="basic" className="space-y-4 mt-4">
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <Label className="text-gray-300">Mode Kode</Label>
                    <Select value={formData.code === 'AUTO' ? 'auto' : 'manual'}
                      onValueChange={(v) => setFormData({...formData, code: v === 'auto' ? 'AUTO' : '', code_mode: v})}>
                      <SelectTrigger className="bg-[#0a0608] border-red-900/30"><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="auto">AUTO</SelectItem>
                        <SelectItem value="manual">MANUAL</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label className="text-gray-300">Kode Diskon</Label>
                    <Input value={formData.code} 
                      onChange={(e) => setFormData({...formData, code: e.target.value.toUpperCase(), code_mode: 'manual'})}
                      disabled={formData.code === 'AUTO'}
                      className={`bg-[#0a0608] border-red-900/30 ${formData.code === 'AUTO' ? 'text-amber-400' : ''}`} />
                  </div>
                  <div>
                    <Label className="text-gray-300">Prioritas</Label>
                    <Input type="number" value={formData.priority} 
                      onChange={(e) => setFormData({...formData, priority: parseInt(e.target.value) || 1})}
                      className="bg-[#0a0608] border-red-900/30" min="1" />
                  </div>
                </div>
                
                <div>
                  <Label className="text-gray-300">Nama Diskon <span className="text-red-400">*</span></Label>
                  <Input value={formData.name} onChange={(e) => setFormData({...formData, name: e.target.value})}
                    className="bg-[#0a0608] border-red-900/30" placeholder="Contoh: Diskon Akhir Tahun 10%" required />
                </div>
                
                <div>
                  <Label className="text-gray-300">Deskripsi</Label>
                  <Input value={formData.description} onChange={(e) => setFormData({...formData, description: e.target.value})}
                    className="bg-[#0a0608] border-red-900/30" placeholder="Keterangan diskon" />
                </div>
                
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <Label className="text-gray-300">Jenis Diskon <span className="text-red-400">*</span></Label>
                    <Select value={formData.discount_type} onValueChange={(v) => setFormData({...formData, discount_type: v})}>
                      <SelectTrigger className="bg-[#0a0608] border-red-900/30"><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="percent">Persentase (%)</SelectItem>
                        <SelectItem value="nominal">Nominal (Rp)</SelectItem>
                        <SelectItem value="per_pcs">Per Pcs (Rp/pcs)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label className="text-gray-300">Nilai Diskon <span className="text-red-400">*</span></Label>
                    <Input type="number" value={formData.discount_value} 
                      onChange={(e) => setFormData({...formData, discount_value: parseFloat(e.target.value) || 0})}
                      className="bg-[#0a0608] border-red-900/30" min="0" required />
                    <p className="text-xs text-gray-500 mt-1">
                      {formData.discount_type === 'percent' ? 'Dalam persen (%)' : 
                       formData.discount_type === 'per_pcs' ? 'Rupiah per pcs' : 'Dalam Rupiah'}
                    </p>
                  </div>
                  <div>
                    <Label className="text-gray-300">Basis Penghitungan</Label>
                    <Select value={formData.basis} onValueChange={(v) => setFormData({...formData, basis: v})}>
                      <SelectTrigger className="bg-[#0a0608] border-red-900/30"><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="per_transaction">Per Transaksi</SelectItem>
                        <SelectItem value="per_item">Per Item</SelectItem>
                        <SelectItem value="per_pcs">Per Pcs</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                
                <div className="flex items-center gap-4 pt-2">
                  <div className="flex items-center gap-2">
                    <Switch checked={formData.stackable} onCheckedChange={(c) => setFormData({...formData, stackable: c})} />
                    <Label className="text-gray-300">Bisa Digabung</Label>
                  </div>
                  <div className="flex items-center gap-2">
                    <Switch checked={formData.is_active} onCheckedChange={(c) => setFormData({...formData, is_active: c})} />
                    <Label className="text-gray-300">Aktif</Label>
                  </div>
                </div>
                
                {/* Example calculation */}
                <div className="p-4 bg-blue-900/20 border border-blue-700/30 rounded-lg">
                  <p className="text-blue-300 text-sm font-semibold mb-2">Contoh Perhitungan:</p>
                  <p className="text-blue-200 text-sm">
                    {formData.discount_type === 'per_pcs' ? (
                      <>Qty 10 pcs × Rp {formData.discount_value.toLocaleString('id-ID')} = <strong>Rp {(10 * formData.discount_value).toLocaleString('id-ID')}</strong> total diskon</>
                    ) : formData.discount_type === 'percent' ? (
                      <>Subtotal Rp 1.000.000 × {formData.discount_value}% = <strong>Rp {((1000000 * formData.discount_value) / 100).toLocaleString('id-ID')}</strong> diskon</>
                    ) : (
                      <>Diskon flat <strong>Rp {formData.discount_value.toLocaleString('id-ID')}</strong></>
                    )}
                  </p>
                </div>
              </TabsContent>

              {/* Tab: Target */}
              <TabsContent value="target" className="space-y-4 mt-4">
                <div>
                  <Label className="text-gray-300">Target Diskon</Label>
                  <Select value={formData.target_type} onValueChange={(v) => setFormData({...formData, target_type: v})}>
                    <SelectTrigger className="bg-[#0a0608] border-red-900/30 max-w-xs"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">Semua Produk</SelectItem>
                      <SelectItem value="product">Produk Tertentu</SelectItem>
                      <SelectItem value="category">Kategori Tertentu</SelectItem>
                      <SelectItem value="brand">Brand Tertentu</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                {formData.target_type === 'product' && (
                  <div className="space-y-2">
                    <Label className="text-gray-300">Pilih Produk</Label>
                    <Select onValueChange={(v) => v !== 'none' && addProduct(v)}>
                      <SelectTrigger className="bg-[#0a0608] border-red-900/30"><SelectValue placeholder="Tambah produk..." /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">-- Pilih Produk --</SelectItem>
                        {products.filter(p => !selectedProducts.find(sp => sp.id === p.id)).map(p => (
                          <SelectItem key={p.id} value={p.id}>{p.code} - {p.name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    {selectedProducts.length > 0 && (
                      <div className="flex flex-wrap gap-2 mt-2">
                        {selectedProducts.map(p => (
                          <Badge key={p.id} variant="secondary" className="flex items-center gap-1">
                            {p.code} - {p.name}
                            <button type="button" onClick={() => removeProduct(p.id)} className="ml-1 hover:text-red-400">
                              <X className="h-3 w-3" />
                            </button>
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>
                )}
                
                {formData.target_type === 'category' && (
                  <div className="space-y-2">
                    <Label className="text-gray-300">Pilih Kategori</Label>
                    <Select onValueChange={(v) => v !== 'none' && addCategory(v)}>
                      <SelectTrigger className="bg-[#0a0608] border-red-900/30"><SelectValue placeholder="Tambah kategori..." /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">-- Pilih Kategori --</SelectItem>
                        {categories.filter(c => !selectedCategories.find(sc => sc.id === c.id)).map(c => (
                          <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    {selectedCategories.length > 0 && (
                      <div className="flex flex-wrap gap-2 mt-2">
                        {selectedCategories.map(c => (
                          <Badge key={c.id} variant="secondary" className="flex items-center gap-1">
                            {c.name}
                            <button type="button" onClick={() => removeCategory(c.id)} className="ml-1 hover:text-red-400">
                              <X className="h-3 w-3" />
                            </button>
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>
                )}
                
                {formData.target_type === 'brand' && (
                  <div className="space-y-2">
                    <Label className="text-gray-300">Pilih Brand</Label>
                    <Select onValueChange={(v) => v !== 'none' && addBrand(v)}>
                      <SelectTrigger className="bg-[#0a0608] border-red-900/30"><SelectValue placeholder="Tambah brand..." /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">-- Pilih Brand --</SelectItem>
                        {brands.filter(b => !selectedBrands.find(sb => sb.id === b.id)).map(b => (
                          <SelectItem key={b.id} value={b.id}>{b.name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    {selectedBrands.length > 0 && (
                      <div className="flex flex-wrap gap-2 mt-2">
                        {selectedBrands.map(b => (
                          <Badge key={b.id} variant="secondary" className="flex items-center gap-1">
                            {b.name}
                            <button type="button" onClick={() => removeBrand(b.id)} className="ml-1 hover:text-red-400">
                              <X className="h-3 w-3" />
                            </button>
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </TabsContent>

              {/* Tab: Syarat */}
              <TabsContent value="condition" className="space-y-4 mt-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-gray-300">Minimum Belanja (Rp)</Label>
                    <Input type="number" value={formData.min_purchase} 
                      onChange={(e) => setFormData({...formData, min_purchase: parseFloat(e.target.value) || 0})}
                      className="bg-[#0a0608] border-red-900/30" min="0" />
                    <p className="text-xs text-gray-500 mt-1">0 = tanpa minimum</p>
                  </div>
                  <div>
                    <Label className="text-gray-300">Minimum Qty</Label>
                    <Input type="number" value={formData.min_qty} 
                      onChange={(e) => setFormData({...formData, min_qty: parseInt(e.target.value) || 0})}
                      className="bg-[#0a0608] border-red-900/30" min="0" />
                    <p className="text-xs text-gray-500 mt-1">0 = tanpa minimum</p>
                  </div>
                </div>
                
                <div>
                  <Label className="text-gray-300">Maksimum Diskon (Rp)</Label>
                  <Input type="number" value={formData.max_discount} 
                    onChange={(e) => setFormData({...formData, max_discount: parseFloat(e.target.value) || 0})}
                    className="bg-[#0a0608] border-red-900/30 max-w-xs" min="0" />
                  <p className="text-xs text-gray-500 mt-1">0 = tanpa maksimum</p>
                </div>
              </TabsContent>

              {/* Tab: Periode */}
              <TabsContent value="period" className="space-y-4 mt-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-gray-300">Tanggal Mulai</Label>
                    <Input type="date" value={formData.start_date} 
                      onChange={(e) => setFormData({...formData, start_date: e.target.value})}
                      className="bg-[#0a0608] border-red-900/30" />
                  </div>
                  <div>
                    <Label className="text-gray-300">Tanggal Selesai</Label>
                    <Input type="date" value={formData.end_date} 
                      onChange={(e) => setFormData({...formData, end_date: e.target.value})}
                      className="bg-[#0a0608] border-red-900/30" />
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-gray-300">Jam Mulai</Label>
                    <Input type="time" value={formData.start_time} 
                      onChange={(e) => setFormData({...formData, start_time: e.target.value})}
                      className="bg-[#0a0608] border-red-900/30" />
                  </div>
                  <div>
                    <Label className="text-gray-300">Jam Selesai</Label>
                    <Input type="time" value={formData.end_time} 
                      onChange={(e) => setFormData({...formData, end_time: e.target.value})}
                      className="bg-[#0a0608] border-red-900/30" />
                  </div>
                </div>
                
                <p className="text-sm text-gray-500">Kosongkan jika diskon berlaku tanpa batas waktu</p>
              </TabsContent>
            </Tabs>

            <DialogFooter className="mt-6">
              <Button type="button" variant="outline" onClick={() => setShowModal(false)} disabled={saving}>Batal</Button>
              <Button type="submit" className="bg-gradient-to-r from-red-600 to-amber-600" disabled={saving} data-testid="save-discount-btn">
                {saving ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                Simpan
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default MasterDiscountsAdvanced;
