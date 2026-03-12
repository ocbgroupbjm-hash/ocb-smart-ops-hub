import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { 
  Plus, Search, Edit2, Trash2, Loader2, X, Gift, Calendar, 
  Tag, Package, ShoppingBag, CheckCircle, AlertCircle, Percent
} from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';

const MasterPromotions = () => {
  const { api } = useAuth();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  
  // Reference data
  const [categories, setCategories] = useState([]);
  const [brands, setBrands] = useState([]);
  const [products, setProducts] = useState([]);

  const [formData, setFormData] = useState({
    code: '',
    name: '',
    promo_type: 'product', // product, category, brand, bundle, buy_x_get_y, special_price, quota
    description: '',
    
    // Trigger conditions
    trigger_type: 'item', // item, qty, subtotal
    trigger_item_ids: [],
    trigger_category_ids: [],
    trigger_brand_ids: [],
    trigger_min_qty: 0,
    trigger_min_subtotal: 0,
    
    // Benefit
    benefit_type: 'discount', // discount, free_item, bundle_price, special_price
    benefit_discount_type: 'percentage', // percentage, nominal
    benefit_discount_value: 0,
    benefit_free_item_ids: [],
    benefit_free_qty: 0,
    benefit_bundle_price: 0,
    benefit_special_price: 0,
    
    // Quota (for quota promo type)
    quota_limit: 0,
    quota_used: 0,
    
    // Period
    start_date: '',
    end_date: '',
    start_time: '',
    end_time: '',
    
    // Advanced
    priority: 1,
    stackable: false,
    max_usage: 0,
    
    is_active: true
  });

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [promoRes, catRes, brandRes, prodRes] = await Promise.all([
        api(`/api/master/promotions?search=${searchTerm}`),
        api('/api/master/categories'),
        api('/api/master/brands'),
        api('/api/products?limit=500')
      ]);
      
      if (promoRes.ok) setItems(await promoRes.json());
      if (catRes.ok) setCategories(await catRes.json());
      if (brandRes.ok) setBrands(await brandRes.json());
      if (prodRes.ok) {
        const data = await prodRes.json();
        setProducts(data.items || data || []);
      }
    } catch (err) { 
      toast.error('Gagal memuat data'); 
    }
    finally { setLoading(false); }
  }, [api, searchTerm]);

  useEffect(() => { loadData(); }, [loadData]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const url = editingItem ? `/api/master/promotions/${editingItem.id}` : '/api/master/promotions';
      const res = await api(url, { 
        method: editingItem ? 'PUT' : 'POST', 
        body: JSON.stringify(formData) 
      });
      if (res.ok) { 
        toast.success(editingItem ? 'Promosi diupdate' : 'Promosi ditambahkan'); 
        setShowModal(false); 
        resetForm();
        loadData(); 
      }
    } catch (err) { toast.error('Gagal menyimpan'); }
  };

  const handleEdit = (item) => { 
    setEditingItem(item); 
    setFormData({
      code: item.code || '',
      name: item.name || '',
      promo_type: item.promo_type || 'product',
      description: item.description || '',
      trigger_type: item.trigger_type || 'item',
      trigger_item_ids: item.trigger_item_ids || [],
      trigger_category_ids: item.trigger_category_ids || [],
      trigger_brand_ids: item.trigger_brand_ids || [],
      trigger_min_qty: item.trigger_min_qty || 0,
      trigger_min_subtotal: item.trigger_min_subtotal || 0,
      benefit_type: item.benefit_type || 'discount',
      benefit_discount_type: item.benefit_discount_type || 'percentage',
      benefit_discount_value: item.benefit_discount_value || 0,
      benefit_free_item_ids: item.benefit_free_item_ids || [],
      benefit_free_qty: item.benefit_free_qty || 0,
      benefit_bundle_price: item.benefit_bundle_price || 0,
      benefit_special_price: item.benefit_special_price || 0,
      quota_limit: item.quota_limit || 0,
      quota_used: item.quota_used || 0,
      start_date: item.start_date || '',
      end_date: item.end_date || '',
      start_time: item.start_time || '',
      end_time: item.end_time || '',
      priority: item.priority || 1,
      stackable: item.stackable || false,
      max_usage: item.max_usage || 0,
      is_active: item.is_active !== false
    }); 
    setShowModal(true); 
  };

  const handleDelete = async (item) => { 
    if (!confirm(`Hapus promosi "${item.name}"?`)) return; 
    try { 
      await api(`/api/master/promotions/${item.id}`, { method: 'DELETE' }); 
      toast.success('Promosi dihapus'); 
      loadData(); 
    } catch { toast.error('Gagal menghapus'); } 
  };

  const resetForm = () => {
    setEditingItem(null);
    setFormData({
      code: '', name: '', promo_type: 'product', description: '',
      trigger_type: 'item', trigger_item_ids: [], trigger_category_ids: [],
      trigger_brand_ids: [], trigger_min_qty: 0, trigger_min_subtotal: 0,
      benefit_type: 'discount', benefit_discount_type: 'percentage',
      benefit_discount_value: 0, benefit_free_item_ids: [], benefit_free_qty: 0,
      benefit_bundle_price: 0, benefit_special_price: 0,
      quota_limit: 0, quota_used: 0,
      start_date: '', end_date: '', start_time: '', end_time: '',
      priority: 1, stackable: false, max_usage: 0, is_active: true
    });
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('id-ID');
  };

  const formatCurrency = (num) => {
    return new Intl.NumberFormat('id-ID').format(num || 0);
  };

  const promoTypeOptions = [
    { value: 'product', label: 'Diskon Produk', icon: Package },
    { value: 'category', label: 'Diskon Kategori', icon: Tag },
    { value: 'brand', label: 'Diskon Merk', icon: Tag },
    { value: 'bundle', label: 'Paket Bundle', icon: ShoppingBag },
    { value: 'buy_x_get_y', label: 'Beli X Gratis Y', icon: Gift },
    { value: 'special_price', label: 'Harga Spesial', icon: Percent },
    { value: 'quota', label: 'Promo Kuota', icon: Calendar }
  ];

  const benefitTypeOptions = [
    { value: 'discount', label: 'Diskon' },
    { value: 'free_item', label: 'Gratis Item' },
    { value: 'bundle_price', label: 'Harga Bundle' },
    { value: 'special_price', label: 'Harga Spesial' }
  ];

  const getBenefitDisplay = (item) => {
    if (item.benefit_type === 'discount') {
      if (item.benefit_discount_type === 'percentage') {
        return `Diskon ${item.benefit_discount_value}%`;
      }
      return `Diskon Rp ${formatCurrency(item.benefit_discount_value)}`;
    }
    if (item.benefit_type === 'free_item') {
      return `Gratis ${item.benefit_free_qty} item`;
    }
    if (item.benefit_type === 'bundle_price') {
      return `Bundle Rp ${formatCurrency(item.benefit_bundle_price)}`;
    }
    if (item.benefit_type === 'special_price') {
      return `Rp ${formatCurrency(item.benefit_special_price)}`;
    }
    return '-';
  };

  return (
    <div className="space-y-4" data-testid="promotions-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-amber-100 flex items-center gap-2">
            <Gift className="h-6 w-6 text-purple-400" />
            Master Promosi
          </h1>
          <p className="text-gray-400 text-sm">Kelola program promosi dengan rule engine</p>
        </div>
        <Button 
          onClick={() => { resetForm(); setShowModal(true); }}
          className="bg-gradient-to-r from-red-600 to-amber-600"
        >
          <Plus className="h-4 w-4 mr-2" /> Tambah Promosi
        </Button>
      </div>

      {/* Search */}
      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input 
            placeholder="Cari promosi..." 
            value={searchTerm} 
            onChange={(e) => setSearchTerm(e.target.value)} 
            className="pl-10 bg-[#0a0608] border-red-900/30"
          />
        </div>
      </div>

      {/* Table */}
      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-red-900/20">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">KODE</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">NAMA PROMOSI</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">JENIS</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">BENEFIT</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">PERIODE</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">STATUS</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">AKSI</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-red-900/20">
              {loading ? (
                <tr><td colSpan={7} className="px-4 py-8 text-center"><Loader2 className="h-8 w-8 animate-spin mx-auto text-amber-400" /></td></tr>
              ) : items.length === 0 ? (
                <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-400">Belum ada data promosi</td></tr>
              ) : items.map(item => (
                <tr key={item.id} className="hover:bg-red-900/10">
                  <td className="px-4 py-3 text-sm font-mono text-amber-300">{item.code}</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <Gift className="h-4 w-4 text-purple-400" />
                      <div>
                        <span className="font-medium text-gray-200">{item.name}</span>
                        {item.description && (
                          <p className="text-xs text-gray-500 truncate max-w-[200px]">{item.description}</p>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className="px-2 py-1 bg-purple-600/20 text-purple-400 rounded text-xs">
                      {promoTypeOptions.find(o => o.value === item.promo_type)?.label || item.promo_type}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className="px-2 py-1 bg-green-600/20 text-green-400 rounded text-xs">
                      {getBenefitDisplay(item)}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center text-xs text-gray-400">
                    {item.start_date || item.end_date 
                      ? `${formatDate(item.start_date)} - ${formatDate(item.end_date)}`
                      : 'Tidak terbatas'
                    }
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className={`px-2 py-1 rounded-full text-xs flex items-center justify-center gap-1 ${
                      item.is_active !== false ? 'bg-green-600/20 text-green-400' : 'bg-red-600/20 text-red-400'
                    }`}>
                      {item.is_active !== false ? <CheckCircle className="h-3 w-3" /> : <AlertCircle className="h-3 w-3" />}
                      {item.is_active !== false ? 'Aktif' : 'Nonaktif'}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-center gap-1">
                      <button onClick={() => handleEdit(item)} className="p-1.5 hover:bg-blue-600/20 rounded text-blue-400">
                        <Edit2 className="h-4 w-4" />
                      </button>
                      <button onClick={() => handleDelete(item)} className="p-1.5 hover:bg-red-600/20 rounded text-red-400">
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
            <div className="p-4 border-b border-red-900/30 flex items-center justify-between sticky top-0 bg-[#1a1214]">
              <h2 className="text-lg font-semibold text-amber-100">
                {editingItem ? 'Edit' : 'Tambah'} Promosi
              </h2>
              <button onClick={() => setShowModal(false)} className="p-1 hover:bg-red-900/20 rounded">
                <X className="h-5 w-5" />
              </button>
            </div>
            <form onSubmit={handleSubmit} className="p-4 space-y-4">
              {/* Basic Info */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Kode Promosi *</label>
                  <Input
                    value={formData.code}
                    onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                    className="bg-[#0a0608] border-red-900/30"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Nama Promosi *</label>
                  <Input
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="bg-[#0a0608] border-red-900/30"
                    required
                  />
                </div>
              </div>

              {/* Promo Type */}
              <div>
                <label className="block text-sm text-amber-200 font-medium mb-2">Jenis Promosi</label>
                <div className="grid grid-cols-4 gap-2">
                  {promoTypeOptions.map(opt => (
                    <button
                      key={opt.value}
                      type="button"
                      onClick={() => setFormData({ ...formData, promo_type: opt.value })}
                      className={`p-2 rounded-lg flex flex-col items-center gap-1 text-xs transition-all ${
                        formData.promo_type === opt.value
                          ? 'bg-purple-600/20 border border-purple-600/50 text-purple-200'
                          : 'bg-[#0a0608] border border-red-900/30 text-gray-400 hover:border-red-900/50'
                      }`}
                    >
                      <opt.icon className="h-4 w-4" />
                      {opt.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Trigger Section */}
              <div className="bg-[#0a0608] border border-red-900/30 rounded-lg p-4">
                <h3 className="text-amber-200 font-medium mb-3">Trigger / Kondisi</h3>
                
                <div className="grid grid-cols-3 gap-4 mb-3">
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">Tipe Trigger</label>
                    <Select 
                      value={formData.trigger_type} 
                      onValueChange={(v) => setFormData({ ...formData, trigger_type: v })}
                    >
                      <SelectTrigger className="bg-[#1a1214] border-red-900/30">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="item">Item Tertentu</SelectItem>
                        <SelectItem value="qty">Min. Quantity</SelectItem>
                        <SelectItem value="subtotal">Min. Subtotal</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">Min. Qty</label>
                    <Input
                      type="number"
                      min="0"
                      value={formData.trigger_min_qty}
                      onChange={(e) => setFormData({ ...formData, trigger_min_qty: Number(e.target.value) })}
                      className="bg-[#1a1214] border-red-900/30"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">Min. Subtotal</label>
                    <Input
                      type="number"
                      min="0"
                      value={formData.trigger_min_subtotal}
                      onChange={(e) => setFormData({ ...formData, trigger_min_subtotal: Number(e.target.value) })}
                      className="bg-[#1a1214] border-red-900/30"
                    />
                  </div>
                </div>

                {/* Trigger Items */}
                {formData.trigger_type === 'item' && (
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">Pilih Item Trigger</label>
                    <select
                      multiple
                      value={formData.trigger_item_ids}
                      onChange={(e) => {
                        const selected = Array.from(e.target.selectedOptions, opt => opt.value);
                        setFormData({ ...formData, trigger_item_ids: selected });
                      }}
                      className="w-full h-24 px-3 py-2 bg-[#1a1214] border border-red-900/30 rounded-lg text-gray-200 text-sm"
                    >
                      {products.map(p => (
                        <option key={p.id} value={p.id}>{p.code} - {p.name}</option>
                      ))}
                    </select>
                  </div>
                )}
              </div>

              {/* Benefit Section */}
              <div className="bg-[#0a0608] border border-red-900/30 rounded-lg p-4">
                <h3 className="text-amber-200 font-medium mb-3">Benefit / Keuntungan</h3>
                
                <div className="grid grid-cols-2 gap-4 mb-3">
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">Tipe Benefit</label>
                    <Select 
                      value={formData.benefit_type} 
                      onValueChange={(v) => setFormData({ ...formData, benefit_type: v })}
                    >
                      <SelectTrigger className="bg-[#1a1214] border-red-900/30">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {benefitTypeOptions.map(opt => (
                          <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  
                  {formData.benefit_type === 'discount' && (
                    <>
                      <div>
                        <label className="block text-sm text-gray-400 mb-1">Jenis Diskon</label>
                        <Select 
                          value={formData.benefit_discount_type} 
                          onValueChange={(v) => setFormData({ ...formData, benefit_discount_type: v })}
                        >
                          <SelectTrigger className="bg-[#1a1214] border-red-900/30">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="percentage">Persentase (%)</SelectItem>
                            <SelectItem value="nominal">Nominal (Rp)</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="col-span-2">
                        <label className="block text-sm text-gray-400 mb-1">
                          Nilai Diskon {formData.benefit_discount_type === 'percentage' ? '(%)' : '(Rp)'}
                        </label>
                        <Input
                          type="number"
                          min="0"
                          value={formData.benefit_discount_value}
                          onChange={(e) => setFormData({ ...formData, benefit_discount_value: Number(e.target.value) })}
                          className="bg-[#1a1214] border-red-900/30"
                        />
                      </div>
                    </>
                  )}
                  
                  {formData.benefit_type === 'free_item' && (
                    <>
                      <div>
                        <label className="block text-sm text-gray-400 mb-1">Qty Gratis</label>
                        <Input
                          type="number"
                          min="1"
                          value={formData.benefit_free_qty}
                          onChange={(e) => setFormData({ ...formData, benefit_free_qty: Number(e.target.value) })}
                          className="bg-[#1a1214] border-red-900/30"
                        />
                      </div>
                      <div className="col-span-2">
                        <label className="block text-sm text-gray-400 mb-1">Item Gratis</label>
                        <select
                          multiple
                          value={formData.benefit_free_item_ids}
                          onChange={(e) => {
                            const selected = Array.from(e.target.selectedOptions, opt => opt.value);
                            setFormData({ ...formData, benefit_free_item_ids: selected });
                          }}
                          className="w-full h-24 px-3 py-2 bg-[#1a1214] border border-red-900/30 rounded-lg text-gray-200 text-sm"
                        >
                          {products.map(p => (
                            <option key={p.id} value={p.id}>{p.code} - {p.name}</option>
                          ))}
                        </select>
                      </div>
                    </>
                  )}
                  
                  {formData.benefit_type === 'bundle_price' && (
                    <div>
                      <label className="block text-sm text-gray-400 mb-1">Harga Bundle (Rp)</label>
                      <Input
                        type="number"
                        min="0"
                        value={formData.benefit_bundle_price}
                        onChange={(e) => setFormData({ ...formData, benefit_bundle_price: Number(e.target.value) })}
                        className="bg-[#1a1214] border-red-900/30"
                      />
                    </div>
                  )}
                  
                  {formData.benefit_type === 'special_price' && (
                    <div>
                      <label className="block text-sm text-gray-400 mb-1">Harga Spesial (Rp)</label>
                      <Input
                        type="number"
                        min="0"
                        value={formData.benefit_special_price}
                        onChange={(e) => setFormData({ ...formData, benefit_special_price: Number(e.target.value) })}
                        className="bg-[#1a1214] border-red-900/30"
                      />
                    </div>
                  )}
                </div>
              </div>

              {/* Quota (for quota promo type) */}
              {formData.promo_type === 'quota' && (
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">Kuota Tersedia</label>
                    <Input
                      type="number"
                      min="0"
                      value={formData.quota_limit}
                      onChange={(e) => setFormData({ ...formData, quota_limit: Number(e.target.value) })}
                      className="bg-[#0a0608] border-red-900/30"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">Kuota Terpakai</label>
                    <Input
                      type="number"
                      value={formData.quota_used}
                      disabled
                      className="bg-[#0a0608] border-red-900/30"
                    />
                  </div>
                </div>
              )}

              {/* Period */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Tanggal Mulai</label>
                  <Input
                    type="date"
                    value={formData.start_date}
                    onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                    className="bg-[#0a0608] border-red-900/30"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Tanggal Selesai</label>
                  <Input
                    type="date"
                    value={formData.end_date}
                    onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                    className="bg-[#0a0608] border-red-900/30"
                  />
                </div>
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm text-gray-400 mb-1">Deskripsi</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200"
                  rows={2}
                  placeholder="Contoh: Beli 2 Gratis 1 untuk semua produk XYZ"
                />
              </div>

              {/* Advanced */}
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Prioritas</label>
                  <Input
                    type="number"
                    min="1"
                    value={formData.priority}
                    onChange={(e) => setFormData({ ...formData, priority: Number(e.target.value) })}
                    className="bg-[#0a0608] border-red-900/30"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Max Penggunaan (0=∞)</label>
                  <Input
                    type="number"
                    min="0"
                    value={formData.max_usage}
                    onChange={(e) => setFormData({ ...formData, max_usage: Number(e.target.value) })}
                    className="bg-[#0a0608] border-red-900/30"
                  />
                </div>
                <div className="flex items-end">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input 
                      type="checkbox" 
                      checked={formData.stackable} 
                      onChange={(e) => setFormData({ ...formData, stackable: e.target.checked })} 
                      className="w-4 h-4" 
                    />
                    <span className="text-sm text-gray-300">Stackable</span>
                  </label>
                </div>
              </div>

              {/* Active */}
              <label className="flex items-center gap-2 cursor-pointer">
                <input 
                  type="checkbox" 
                  checked={formData.is_active} 
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })} 
                  className="w-4 h-4" 
                />
                <span className="text-sm text-gray-300">Aktif</span>
              </label>

              {/* Submit */}
              <div className="flex justify-end gap-3 pt-4 border-t border-red-900/30">
                <Button type="button" variant="outline" onClick={() => setShowModal(false)} className="border-red-900/30">
                  Batal
                </Button>
                <Button type="submit" className="bg-gradient-to-r from-red-600 to-amber-600">
                  {editingItem ? 'Update' : 'Simpan'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default MasterPromotions;
