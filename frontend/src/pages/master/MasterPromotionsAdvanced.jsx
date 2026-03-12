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
import { Plus, Search, Edit2, Trash2, Loader2, Gift, Calendar, Package, Tag, RefreshCw, X, Percent, ShoppingCart } from 'lucide-react';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

const MasterPromotionsAdvanced = () => {
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
  
  // Promo detail items
  const [promoItems, setPromoItems] = useState([]);
  
  const [formData, setFormData] = useState({
    // Header
    code: 'AUTO',
    code_mode: 'auto',
    name: '',
    description: '',
    
    // Type
    promo_type: 'discount', // discount, buy_x_get_y, bundle, special_price, free_item
    
    // Target Type
    target_type: 'all', // all, category, brand, product, bundle
    
    // Conditions
    min_qty: 0,
    min_subtotal: 0,
    quota: 0, // 0 = unlimited
    
    // Benefit
    benefit_type: 'percent', // percent, nominal, free_item, special_price
    benefit_value: 0,
    free_product_id: '',
    free_qty: 0,
    bundle_price: 0,
    
    // Period
    start_date: '',
    end_date: '',
    start_time: '',
    end_time: '',
    
    // Rules
    priority: 1,
    stackable: false,
    is_active: true,
    
    // Target branches/customer groups
    target_branches: [],
    target_customer_groups: []
  });

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [res, catRes, brandRes, prodRes, groupRes, branchRes] = await Promise.all([
        api(`/api/master/promotions?search=${searchTerm}`),
        api('/api/master/categories'),
        api('/api/master/brands'),
        api('/api/products?limit=200'),
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
      toast.error('Nama promosi wajib diisi');
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
          body: JSON.stringify({ module_code: 'PRM' })
        });
        if (genRes.ok) {
          const genData = await genRes.json();
          finalCode = genData.number;
        } else {
          finalCode = `PRM-${Date.now()}`;
        }
      }
      
      const payload = { 
        ...formData, 
        code: finalCode,
        items: promoItems
      };
      
      const url = editingItem ? `/api/master/promotions/${editingItem.id}` : '/api/master/promotions';
      const res = await api(url, { method: editingItem ? 'PUT' : 'POST', body: JSON.stringify(payload) });
      
      if (res.ok) { 
        toast.success(`Promosi ${finalCode} berhasil disimpan`); 
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
      promo_type: item.promo_type || 'discount',
      target_type: item.target_type || 'all',
      min_qty: item.min_qty || 0,
      min_subtotal: item.min_subtotal || 0,
      quota: item.quota || 0,
      benefit_type: item.benefit_type || 'percent',
      benefit_value: item.benefit_value || 0,
      free_product_id: item.free_product_id || '',
      free_qty: item.free_qty || 0,
      bundle_price: item.bundle_price || 0,
      start_date: item.start_date ? item.start_date.split('T')[0] : '',
      end_date: item.end_date ? item.end_date.split('T')[0] : '',
      start_time: item.start_time || '',
      end_time: item.end_time || '',
      priority: item.priority || 1,
      stackable: item.stackable || false,
      is_active: item.is_active !== false,
      target_branches: item.target_branches || [],
      target_customer_groups: item.target_customer_groups || []
    });
    setPromoItems(item.items || []);
    setShowModal(true); 
  };

  const handleDelete = async (item) => { 
    if (!window.confirm(`Hapus promosi "${item.name}"?`)) return; 
    try { 
      await api(`/api/master/promotions/${item.id}`, { method: 'DELETE' }); 
      toast.success('Berhasil dihapus'); 
      loadData(); 
    } catch { 
      toast.error('Gagal menghapus'); 
    } 
  };

  const resetForm = () => {
    setEditingItem(null);
    setPromoItems([]);
    setFormData({
      code: 'AUTO', code_mode: 'auto', name: '', description: '',
      promo_type: 'discount', target_type: 'all',
      min_qty: 0, min_subtotal: 0, quota: 0,
      benefit_type: 'percent', benefit_value: 0,
      free_product_id: '', free_qty: 0, bundle_price: 0,
      start_date: '', end_date: '', start_time: '', end_time: '',
      priority: 1, stackable: false, is_active: true,
      target_branches: [], target_customer_groups: []
    });
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(value || 0);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('id-ID');
  };

  const getPromoTypeLabel = (type) => {
    switch(type) {
      case 'discount': return 'Diskon';
      case 'buy_x_get_y': return 'Beli X Gratis Y';
      case 'bundle': return 'Bundle';
      case 'special_price': return 'Harga Khusus';
      case 'free_item': return 'Gratis Item';
      default: return type;
    }
  };

  const getPromoTypeIcon = (type) => {
    switch(type) {
      case 'discount': return <Percent className="h-4 w-4" />;
      case 'buy_x_get_y': return <Gift className="h-4 w-4" />;
      case 'bundle': return <Package className="h-4 w-4" />;
      case 'special_price': return <Tag className="h-4 w-4" />;
      case 'free_item': return <ShoppingCart className="h-4 w-4" />;
      default: return <Tag className="h-4 w-4" />;
    }
  };

  // Add product to promo items
  const addPromoItem = (productId) => {
    const product = products.find(p => p.id === productId);
    if (product && !promoItems.find(pi => pi.product_id === productId)) {
      setPromoItems([...promoItems, {
        product_id: productId,
        product_code: product.code,
        product_name: product.name,
        qty_trigger: 1,
        qty_reward: 0,
        discount_value: 0,
        special_price: 0,
        is_free_item: false
      }]);
    }
  };

  const updatePromoItem = (index, field, value) => {
    const updated = [...promoItems];
    updated[index][field] = value;
    setPromoItems(updated);
  };

  const removePromoItem = (index) => {
    setPromoItems(promoItems.filter((_, i) => i !== index));
  };

  return (
    <div className="space-y-4" data-testid="promotions-advanced-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Manajemen Promosi</h1>
          <p className="text-gray-400 text-sm">Kelola promosi produk, bundle, buy X get Y, dan harga khusus</p>
        </div>
        <Button onClick={() => { resetForm(); setShowModal(true); }} 
          className="bg-gradient-to-r from-red-600 to-amber-600" data-testid="add-promo-btn">
          <Plus className="h-4 w-4 mr-2" /> Tambah Promosi
        </Button>
      </div>

      <Card className="bg-[#1a1214] border-red-900/30">
        <CardContent className="pt-4">
          <div className="flex gap-4">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input type="text" placeholder="Cari promosi..." value={searchTerm} 
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
                  <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">NAMA PROMOSI</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">JENIS</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">BENEFIT</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">KUOTA</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">PERIODE</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">STATUS</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">AKSI</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-red-900/20">
                {loading ? (
                  <tr><td colSpan={8} className="px-4 py-8 text-center"><Loader2 className="h-8 w-8 animate-spin mx-auto text-amber-400" /></td></tr>
                ) : items.length === 0 ? (
                  <tr><td colSpan={8} className="px-4 py-8 text-center text-gray-400">Belum ada promosi</td></tr>
                ) : items.map(item => (
                  <tr key={item.id} className="hover:bg-red-900/10">
                    <td className="px-4 py-3 text-sm font-mono text-amber-300">{item.code}</td>
                    <td className="px-4 py-3">
                      <div className="font-medium text-gray-200">{item.name}</div>
                      {item.description && <div className="text-xs text-gray-500">{item.description}</div>}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <Badge variant="outline" className="flex items-center gap-1 justify-center">
                        {getPromoTypeIcon(item.promo_type)}
                        {getPromoTypeLabel(item.promo_type)}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-center text-amber-300 font-semibold">
                      {item.benefit_type === 'percent' ? `${item.benefit_value}%` : 
                       item.benefit_type === 'free_item' ? `${item.free_qty} gratis` :
                       formatCurrency(item.benefit_value || item.bundle_price)}
                    </td>
                    <td className="px-4 py-3 text-center text-sm text-gray-400">
                      {item.quota > 0 ? item.quota : 'Unlimited'}
                    </td>
                    <td className="px-4 py-3 text-center text-sm text-gray-400">
                      {item.start_date && item.end_date ? (
                        <div className="text-xs">
                          {formatDate(item.start_date)} - {formatDate(item.end_date)}
                        </div>
                      ) : 'Tidak terbatas'}
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

      {/* Promotion Form Modal */}
      <Dialog open={showModal} onOpenChange={(open) => !open && setShowModal(false)}>
        <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto bg-[#1a1214] border-red-900/30">
          <DialogHeader>
            <DialogTitle className="text-amber-100 flex items-center gap-2">
              <Gift className="h-5 w-5" />
              {editingItem ? 'Edit' : 'Tambah'} Promosi
            </DialogTitle>
          </DialogHeader>
          
          <form onSubmit={handleSubmit}>
            <Tabs defaultValue="general" className="w-full">
              <TabsList className="grid w-full grid-cols-4 bg-[#0a0608]">
                <TabsTrigger value="general" className="data-[state=active]:bg-red-900/50">Umum</TabsTrigger>
                <TabsTrigger value="rule" className="data-[state=active]:bg-red-900/50">Rule & Benefit</TabsTrigger>
                <TabsTrigger value="products" className="data-[state=active]:bg-red-900/50">Produk</TabsTrigger>
                <TabsTrigger value="period" className="data-[state=active]:bg-red-900/50">Periode</TabsTrigger>
              </TabsList>

              {/* Tab: Umum */}
              <TabsContent value="general" className="space-y-4 mt-4">
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
                    <Label className="text-gray-300">Kode Promosi</Label>
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
                  <Label className="text-gray-300">Nama Promosi <span className="text-red-400">*</span></Label>
                  <Input value={formData.name} onChange={(e) => setFormData({...formData, name: e.target.value})}
                    className="bg-[#0a0608] border-red-900/30" placeholder="Contoh: Promo Akhir Tahun - Beli 2 Gratis 1" required />
                </div>
                
                <div>
                  <Label className="text-gray-300">Deskripsi</Label>
                  <Input value={formData.description} onChange={(e) => setFormData({...formData, description: e.target.value})}
                    className="bg-[#0a0608] border-red-900/30" placeholder="Keterangan promosi" />
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-gray-300">Jenis Promosi <span className="text-red-400">*</span></Label>
                    <Select value={formData.promo_type} onValueChange={(v) => setFormData({...formData, promo_type: v})}>
                      <SelectTrigger className="bg-[#0a0608] border-red-900/30"><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="discount">Diskon</SelectItem>
                        <SelectItem value="buy_x_get_y">Beli X Gratis Y</SelectItem>
                        <SelectItem value="bundle">Bundle / Paket</SelectItem>
                        <SelectItem value="special_price">Harga Khusus</SelectItem>
                        <SelectItem value="free_item">Gratis Item</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label className="text-gray-300">Target</Label>
                    <Select value={formData.target_type} onValueChange={(v) => setFormData({...formData, target_type: v})}>
                      <SelectTrigger className="bg-[#0a0608] border-red-900/30"><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">Semua Produk</SelectItem>
                        <SelectItem value="category">Kategori Tertentu</SelectItem>
                        <SelectItem value="brand">Brand Tertentu</SelectItem>
                        <SelectItem value="product">Produk Tertentu</SelectItem>
                        <SelectItem value="bundle">Bundle Produk</SelectItem>
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
              </TabsContent>

              {/* Tab: Rule & Benefit */}
              <TabsContent value="rule" className="space-y-4 mt-4">
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <Label className="text-gray-300">Minimum Qty</Label>
                    <Input type="number" value={formData.min_qty} 
                      onChange={(e) => setFormData({...formData, min_qty: parseInt(e.target.value) || 0})}
                      className="bg-[#0a0608] border-red-900/30" min="0" />
                  </div>
                  <div>
                    <Label className="text-gray-300">Minimum Subtotal (Rp)</Label>
                    <Input type="number" value={formData.min_subtotal} 
                      onChange={(e) => setFormData({...formData, min_subtotal: parseFloat(e.target.value) || 0})}
                      className="bg-[#0a0608] border-red-900/30" min="0" />
                  </div>
                  <div>
                    <Label className="text-gray-300">Kuota Promo</Label>
                    <Input type="number" value={formData.quota} 
                      onChange={(e) => setFormData({...formData, quota: parseInt(e.target.value) || 0})}
                      className="bg-[#0a0608] border-red-900/30" min="0" />
                    <p className="text-xs text-gray-500 mt-1">0 = unlimited</p>
                  </div>
                </div>
                
                <div className="p-4 bg-green-900/20 border border-green-700/30 rounded-lg space-y-4">
                  <h3 className="text-green-300 font-semibold">Benefit Promosi</h3>
                  
                  <div>
                    <Label className="text-gray-300">Jenis Benefit</Label>
                    <Select value={formData.benefit_type} onValueChange={(v) => setFormData({...formData, benefit_type: v})}>
                      <SelectTrigger className="bg-[#0a0608] border-red-900/30 max-w-xs"><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="percent">Diskon Persentase</SelectItem>
                        <SelectItem value="nominal">Diskon Nominal</SelectItem>
                        <SelectItem value="free_item">Gratis Item</SelectItem>
                        <SelectItem value="special_price">Harga Khusus</SelectItem>
                        <SelectItem value="bundle_price">Harga Bundle</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  
                  {(formData.benefit_type === 'percent' || formData.benefit_type === 'nominal') && (
                    <div>
                      <Label className="text-gray-300">Nilai Diskon</Label>
                      <Input type="number" value={formData.benefit_value} 
                        onChange={(e) => setFormData({...formData, benefit_value: parseFloat(e.target.value) || 0})}
                        className="bg-[#0a0608] border-red-900/30 max-w-xs" min="0" />
                      <p className="text-xs text-gray-500 mt-1">
                        {formData.benefit_type === 'percent' ? 'Dalam persen (%)' : 'Dalam Rupiah'}
                      </p>
                    </div>
                  )}
                  
                  {formData.benefit_type === 'free_item' && (
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label className="text-gray-300">Produk Gratis</Label>
                        <Select value={formData.free_product_id || 'none'} 
                          onValueChange={(v) => setFormData({...formData, free_product_id: v === 'none' ? '' : v})}>
                          <SelectTrigger className="bg-[#0a0608] border-red-900/30"><SelectValue placeholder="Pilih produk gratis" /></SelectTrigger>
                          <SelectContent>
                            <SelectItem value="none">-- Pilih --</SelectItem>
                            {products.map(p => <SelectItem key={p.id} value={p.id}>{p.code} - {p.name}</SelectItem>)}
                          </SelectContent>
                        </Select>
                      </div>
                      <div>
                        <Label className="text-gray-300">Qty Gratis</Label>
                        <Input type="number" value={formData.free_qty} 
                          onChange={(e) => setFormData({...formData, free_qty: parseInt(e.target.value) || 0})}
                          className="bg-[#0a0608] border-red-900/30" min="0" />
                      </div>
                    </div>
                  )}
                  
                  {formData.benefit_type === 'bundle_price' && (
                    <div>
                      <Label className="text-gray-300">Harga Bundle</Label>
                      <Input type="number" value={formData.bundle_price} 
                        onChange={(e) => setFormData({...formData, bundle_price: parseFloat(e.target.value) || 0})}
                        className="bg-[#0a0608] border-red-900/30 max-w-xs" min="0" />
                    </div>
                  )}
                  
                  {formData.benefit_type === 'special_price' && (
                    <div>
                      <Label className="text-gray-300">Harga Khusus</Label>
                      <Input type="number" value={formData.benefit_value} 
                        onChange={(e) => setFormData({...formData, benefit_value: parseFloat(e.target.value) || 0})}
                        className="bg-[#0a0608] border-red-900/30 max-w-xs" min="0" />
                    </div>
                  )}
                </div>
              </TabsContent>

              {/* Tab: Produk */}
              <TabsContent value="products" className="space-y-4 mt-4">
                <div className="p-4 bg-blue-900/20 border border-blue-700/30 rounded-lg">
                  <p className="text-blue-300 text-sm">Tambah produk yang termasuk dalam promosi ini</p>
                </div>
                
                <div>
                  <Label className="text-gray-300">Tambah Produk</Label>
                  <Select onValueChange={(v) => v !== 'none' && addPromoItem(v)}>
                    <SelectTrigger className="bg-[#0a0608] border-red-900/30"><SelectValue placeholder="Pilih produk..." /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">-- Pilih Produk --</SelectItem>
                      {products.filter(p => !promoItems.find(pi => pi.product_id === p.id)).map(p => (
                        <SelectItem key={p.id} value={p.id}>{p.code} - {p.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                
                {promoItems.length > 0 && (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-red-900/20">
                        <tr>
                          <th className="px-3 py-2 text-left text-amber-200">Produk</th>
                          <th className="px-3 py-2 text-center text-amber-200">Qty Trigger</th>
                          <th className="px-3 py-2 text-center text-amber-200">Qty Reward</th>
                          <th className="px-3 py-2 text-center text-amber-200">Diskon</th>
                          <th className="px-3 py-2 text-center text-amber-200">Harga Khusus</th>
                          <th className="px-3 py-2 text-center text-amber-200">Gratis?</th>
                          <th className="px-3 py-2 text-center text-amber-200">Aksi</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-red-900/20">
                        {promoItems.map((item, index) => (
                          <tr key={index}>
                            <td className="px-3 py-2 text-gray-200">{item.product_code} - {item.product_name}</td>
                            <td className="px-3 py-2">
                              <Input type="number" value={item.qty_trigger} 
                                onChange={(e) => updatePromoItem(index, 'qty_trigger', parseInt(e.target.value) || 0)}
                                className="bg-[#0a0608] border-red-900/30 w-20 h-8 text-center" min="0" />
                            </td>
                            <td className="px-3 py-2">
                              <Input type="number" value={item.qty_reward} 
                                onChange={(e) => updatePromoItem(index, 'qty_reward', parseInt(e.target.value) || 0)}
                                className="bg-[#0a0608] border-red-900/30 w-20 h-8 text-center" min="0" />
                            </td>
                            <td className="px-3 py-2">
                              <Input type="number" value={item.discount_value} 
                                onChange={(e) => updatePromoItem(index, 'discount_value', parseFloat(e.target.value) || 0)}
                                className="bg-[#0a0608] border-red-900/30 w-24 h-8 text-center" min="0" />
                            </td>
                            <td className="px-3 py-2">
                              <Input type="number" value={item.special_price} 
                                onChange={(e) => updatePromoItem(index, 'special_price', parseFloat(e.target.value) || 0)}
                                className="bg-[#0a0608] border-red-900/30 w-28 h-8 text-center" min="0" />
                            </td>
                            <td className="px-3 py-2 text-center">
                              <Switch checked={item.is_free_item} 
                                onCheckedChange={(c) => updatePromoItem(index, 'is_free_item', c)} />
                            </td>
                            <td className="px-3 py-2 text-center">
                              <Button type="button" size="sm" variant="ghost" onClick={() => removePromoItem(index)} className="text-red-400">
                                <X className="h-4 w-4" />
                              </Button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
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
                
                <p className="text-sm text-gray-500">Kosongkan jika promosi berlaku tanpa batas waktu</p>
              </TabsContent>
            </Tabs>

            <DialogFooter className="mt-6">
              <Button type="button" variant="outline" onClick={() => setShowModal(false)} disabled={saving}>Batal</Button>
              <Button type="submit" className="bg-gradient-to-r from-red-600 to-amber-600" disabled={saving} data-testid="save-promo-btn">
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

export default MasterPromotionsAdvanced;
