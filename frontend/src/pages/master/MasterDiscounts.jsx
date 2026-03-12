import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { 
  Plus, Search, Edit2, Trash2, Loader2, X, Percent, Calendar, 
  Tag, Users, Package, ShoppingBag, CheckCircle, AlertCircle
} from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';

const MasterDiscounts = () => {
  const { api } = useAuth();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  
  // Reference data
  const [categories, setCategories] = useState([]);
  const [brands, setBrands] = useState([]);
  const [customerGroups, setCustomerGroups] = useState([]);
  const [products, setProducts] = useState([]);
  const [branches, setBranches] = useState([]);

  const [formData, setFormData] = useState({
    code: '',
    name: '',
    discount_type: 'percentage', // percentage, nominal, per_pcs, per_item, per_transaction, tiered
    discount_value: 0,
    
    // Target
    target_type: 'all', // all, item, category, brand, customer_group, branch
    target_ids: [],
    
    // Conditions
    min_purchase: 0,
    min_qty: 0,
    start_date: '',
    end_date: '',
    start_time: '',
    end_time: '',
    
    // Advanced
    priority: 1,
    stackable: false,
    max_usage: 0, // 0 = unlimited
    max_usage_per_customer: 0,
    
    // Tiered discount
    tiers: [],
    
    is_active: true,
    description: ''
  });

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [discRes, catRes, brandRes, groupRes, prodRes, branchRes] = await Promise.all([
        api(`/api/master/discounts?search=${searchTerm}`),
        api('/api/master/categories'),
        api('/api/master/brands'),
        api('/api/master/customer-groups'),
        api('/api/products?limit=500'),
        api('/api/branches')
      ]);
      
      if (discRes.ok) setItems(await discRes.json());
      if (catRes.ok) setCategories(await catRes.json());
      if (brandRes.ok) setBrands(await brandRes.json());
      if (groupRes.ok) setCustomerGroups(await groupRes.json());
      if (prodRes.ok) {
        const data = await prodRes.json();
        setProducts(data.items || data || []);
      }
      if (branchRes.ok) setBranches(await branchRes.json());
    } catch (err) { 
      toast.error('Gagal memuat data'); 
    }
    finally { setLoading(false); }
  }, [api, searchTerm]);

  useEffect(() => { loadData(); }, [loadData]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const url = editingItem ? `/api/master/discounts/${editingItem.id}` : '/api/master/discounts';
      const res = await api(url, { 
        method: editingItem ? 'PUT' : 'POST', 
        body: JSON.stringify(formData) 
      });
      if (res.ok) { 
        toast.success(editingItem ? 'Diskon diupdate' : 'Diskon ditambahkan'); 
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
      discount_type: item.discount_type || 'percentage',
      discount_value: item.discount_value || 0,
      target_type: item.target_type || 'all',
      target_ids: item.target_ids || [],
      min_purchase: item.min_purchase || 0,
      min_qty: item.min_qty || 0,
      start_date: item.start_date || '',
      end_date: item.end_date || '',
      start_time: item.start_time || '',
      end_time: item.end_time || '',
      priority: item.priority || 1,
      stackable: item.stackable || false,
      max_usage: item.max_usage || 0,
      max_usage_per_customer: item.max_usage_per_customer || 0,
      tiers: item.tiers || [],
      is_active: item.is_active !== false,
      description: item.description || ''
    }); 
    setShowModal(true); 
  };

  const handleDelete = async (item) => { 
    if (!confirm(`Hapus diskon "${item.name}"?`)) return; 
    try { 
      await api(`/api/master/discounts/${item.id}`, { method: 'DELETE' }); 
      toast.success('Diskon dihapus'); 
      loadData(); 
    } catch { toast.error('Gagal menghapus'); } 
  };

  const resetForm = () => {
    setEditingItem(null);
    setFormData({
      code: '', name: '', discount_type: 'percentage', discount_value: 0,
      target_type: 'all', target_ids: [], min_purchase: 0, min_qty: 0,
      start_date: '', end_date: '', start_time: '', end_time: '',
      priority: 1, stackable: false, max_usage: 0, max_usage_per_customer: 0,
      tiers: [], is_active: true, description: ''
    });
  };

  // Add tier for tiered discount
  const addTier = () => {
    setFormData({
      ...formData,
      tiers: [...formData.tiers, { min_qty: 0, min_amount: 0, discount_value: 0 }]
    });
  };

  const updateTier = (index, field, value) => {
    const newTiers = [...formData.tiers];
    newTiers[index][field] = Number(value);
    setFormData({ ...formData, tiers: newTiers });
  };

  const removeTier = (index) => {
    setFormData({
      ...formData,
      tiers: formData.tiers.filter((_, i) => i !== index)
    });
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('id-ID');
  };

  const formatCurrency = (num) => {
    return new Intl.NumberFormat('id-ID').format(num || 0);
  };

  const getDiscountDisplay = (item) => {
    if (item.discount_type === 'percentage') {
      return `${item.discount_value}%`;
    }
    return `Rp ${formatCurrency(item.discount_value)}`;
  };

  const getTargetTypeLabel = (type) => {
    const labels = {
      all: 'Semua',
      item: 'Item Tertentu',
      category: 'Kategori',
      brand: 'Merk',
      customer_group: 'Grup Pelanggan',
      branch: 'Cabang'
    };
    return labels[type] || type;
  };

  const discountTypeOptions = [
    { value: 'percentage', label: 'Persentase (%)' },
    { value: 'nominal', label: 'Nominal (Rp)' },
    { value: 'per_pcs', label: 'Per Pcs' },
    { value: 'per_item', label: 'Per Item' },
    { value: 'per_transaction', label: 'Per Transaksi' },
    { value: 'tiered', label: 'Bertingkat (Tiered)' }
  ];

  const targetTypeOptions = [
    { value: 'all', label: 'Semua Item', icon: ShoppingBag },
    { value: 'item', label: 'Item Tertentu', icon: Package },
    { value: 'category', label: 'Kategori', icon: Tag },
    { value: 'brand', label: 'Merk', icon: Tag },
    { value: 'customer_group', label: 'Grup Pelanggan', icon: Users },
    { value: 'branch', label: 'Cabang', icon: ShoppingBag }
  ];

  const getTargetOptions = () => {
    switch (formData.target_type) {
      case 'item': return products.map(p => ({ value: p.id, label: `${p.code} - ${p.name}` }));
      case 'category': return categories.map(c => ({ value: c.id, label: c.name }));
      case 'brand': return brands.map(b => ({ value: b.id, label: b.name }));
      case 'customer_group': return customerGroups.map(g => ({ value: g.id, label: g.name }));
      case 'branch': return branches.map(b => ({ value: b.id, label: b.name }));
      default: return [];
    }
  };

  return (
    <div className="space-y-4" data-testid="discounts-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-amber-100 flex items-center gap-2">
            <Percent className="h-6 w-6 text-green-400" />
            Master Diskon
          </h1>
          <p className="text-gray-400 text-sm">Kelola diskon dengan berbagai jenis dan target</p>
        </div>
        <Button 
          onClick={() => { resetForm(); setShowModal(true); }}
          className="bg-gradient-to-r from-red-600 to-amber-600"
        >
          <Plus className="h-4 w-4 mr-2" /> Tambah Diskon
        </Button>
      </div>

      {/* Search */}
      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input 
            placeholder="Cari diskon..." 
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
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">NAMA DISKON</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">JENIS</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">NILAI</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">TARGET</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">PERIODE</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">STATUS</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">AKSI</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-red-900/20">
              {loading ? (
                <tr><td colSpan={8} className="px-4 py-8 text-center"><Loader2 className="h-8 w-8 animate-spin mx-auto text-amber-400" /></td></tr>
              ) : items.length === 0 ? (
                <tr><td colSpan={8} className="px-4 py-8 text-center text-gray-400">Belum ada data diskon</td></tr>
              ) : items.map(item => (
                <tr key={item.id} className="hover:bg-red-900/10">
                  <td className="px-4 py-3 text-sm font-mono text-amber-300">{item.code}</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <Percent className="h-4 w-4 text-green-500" />
                      <div>
                        <span className="font-medium text-gray-200">{item.name}</span>
                        {item.description && (
                          <p className="text-xs text-gray-500 truncate max-w-[200px]">{item.description}</p>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className="px-2 py-1 bg-blue-600/20 text-blue-400 rounded text-xs">
                      {discountTypeOptions.find(o => o.value === item.discount_type)?.label || item.discount_type}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className="px-2 py-1 bg-green-600/20 text-green-400 rounded text-sm font-medium">
                      {getDiscountDisplay(item)}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className="px-2 py-1 bg-purple-600/20 text-purple-400 rounded text-xs">
                      {getTargetTypeLabel(item.target_type)}
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
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="p-4 border-b border-red-900/30 flex items-center justify-between sticky top-0 bg-[#1a1214]">
              <h2 className="text-lg font-semibold text-amber-100">
                {editingItem ? 'Edit' : 'Tambah'} Diskon
              </h2>
              <button onClick={() => setShowModal(false)} className="p-1 hover:bg-red-900/20 rounded">
                <X className="h-5 w-5" />
              </button>
            </div>
            <form onSubmit={handleSubmit} className="p-4 space-y-4">
              {/* Basic Info */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Kode Diskon *</label>
                  <Input
                    value={formData.code}
                    onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                    className="bg-[#0a0608] border-red-900/30"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Nama Diskon *</label>
                  <Input
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="bg-[#0a0608] border-red-900/30"
                    required
                  />
                </div>
              </div>

              {/* Discount Type & Value */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Jenis Diskon</label>
                  <Select 
                    value={formData.discount_type} 
                    onValueChange={(v) => setFormData({ ...formData, discount_type: v })}
                  >
                    <SelectTrigger className="bg-[#0a0608] border-red-900/30">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {discountTypeOptions.map(opt => (
                        <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                {formData.discount_type !== 'tiered' && (
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">
                      Nilai Diskon {formData.discount_type === 'percentage' ? '(%)' : '(Rp)'}
                    </label>
                    <Input
                      type="number"
                      min="0"
                      value={formData.discount_value}
                      onChange={(e) => setFormData({ ...formData, discount_value: Number(e.target.value) })}
                      className="bg-[#0a0608] border-red-900/30"
                    />
                  </div>
                )}
              </div>

              {/* Tiered Discount */}
              {formData.discount_type === 'tiered' && (
                <div className="bg-[#0a0608] border border-red-900/30 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <label className="text-sm text-amber-200 font-medium">Diskon Bertingkat</label>
                    <Button type="button" size="sm" variant="outline" onClick={addTier} className="border-red-900/30">
                      <Plus className="h-3 w-3 mr-1" /> Tambah Tier
                    </Button>
                  </div>
                  {formData.tiers.length === 0 ? (
                    <p className="text-gray-500 text-sm">Belum ada tier. Klik "Tambah Tier" untuk menambahkan.</p>
                  ) : (
                    <div className="space-y-2">
                      {formData.tiers.map((tier, index) => (
                        <div key={index} className="flex items-center gap-2 bg-[#1a1214] p-2 rounded">
                          <div className="flex-1">
                            <label className="text-xs text-gray-500">Min Qty</label>
                            <Input
                              type="number"
                              min="0"
                              value={tier.min_qty}
                              onChange={(e) => updateTier(index, 'min_qty', e.target.value)}
                              className="h-8 bg-[#0a0608] border-red-900/30"
                            />
                          </div>
                          <div className="flex-1">
                            <label className="text-xs text-gray-500">Min Amount</label>
                            <Input
                              type="number"
                              min="0"
                              value={tier.min_amount}
                              onChange={(e) => updateTier(index, 'min_amount', e.target.value)}
                              className="h-8 bg-[#0a0608] border-red-900/30"
                            />
                          </div>
                          <div className="flex-1">
                            <label className="text-xs text-gray-500">Diskon (%)</label>
                            <Input
                              type="number"
                              min="0"
                              value={tier.discount_value}
                              onChange={(e) => updateTier(index, 'discount_value', e.target.value)}
                              className="h-8 bg-[#0a0608] border-red-900/30"
                            />
                          </div>
                          <button type="button" onClick={() => removeTier(index)} className="p-1 hover:bg-red-600/20 rounded mt-4">
                            <Trash2 className="h-4 w-4 text-red-400" />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Target */}
              <div className="space-y-3">
                <label className="block text-sm text-amber-200 font-medium">Target Diskon</label>
                <div className="grid grid-cols-3 gap-2">
                  {targetTypeOptions.map(opt => (
                    <button
                      key={opt.value}
                      type="button"
                      onClick={() => setFormData({ ...formData, target_type: opt.value, target_ids: [] })}
                      className={`p-2 rounded-lg flex items-center gap-2 text-sm transition-all ${
                        formData.target_type === opt.value
                          ? 'bg-amber-600/20 border border-amber-600/50 text-amber-200'
                          : 'bg-[#0a0608] border border-red-900/30 text-gray-400 hover:border-red-900/50'
                      }`}
                    >
                      <opt.icon className="h-4 w-4" />
                      {opt.label}
                    </button>
                  ))}
                </div>
                
                {formData.target_type !== 'all' && (
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">Pilih {getTargetTypeLabel(formData.target_type)}</label>
                    <select
                      multiple
                      value={formData.target_ids}
                      onChange={(e) => {
                        const selected = Array.from(e.target.selectedOptions, opt => opt.value);
                        setFormData({ ...formData, target_ids: selected });
                      }}
                      className="w-full h-32 px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200"
                    >
                      {getTargetOptions().map(opt => (
                        <option key={opt.value} value={opt.value}>{opt.label}</option>
                      ))}
                    </select>
                    <p className="text-xs text-gray-500 mt-1">Ctrl + klik untuk pilih multiple</p>
                  </div>
                )}
              </div>

              {/* Conditions */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Min. Pembelian (Rp)</label>
                  <Input
                    type="number"
                    min="0"
                    value={formData.min_purchase}
                    onChange={(e) => setFormData({ ...formData, min_purchase: Number(e.target.value) })}
                    className="bg-[#0a0608] border-red-900/30"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Min. Qty</label>
                  <Input
                    type="number"
                    min="0"
                    value={formData.min_qty}
                    onChange={(e) => setFormData({ ...formData, min_qty: Number(e.target.value) })}
                    className="bg-[#0a0608] border-red-900/30"
                  />
                </div>
              </div>

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

              {/* Time Range */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Jam Mulai</label>
                  <Input
                    type="time"
                    value={formData.start_time}
                    onChange={(e) => setFormData({ ...formData, start_time: e.target.value })}
                    className="bg-[#0a0608] border-red-900/30"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Jam Selesai</label>
                  <Input
                    type="time"
                    value={formData.end_time}
                    onChange={(e) => setFormData({ ...formData, end_time: e.target.value })}
                    className="bg-[#0a0608] border-red-900/30"
                  />
                </div>
              </div>

              {/* Advanced Settings */}
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
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Max/Customer</label>
                  <Input
                    type="number"
                    min="0"
                    value={formData.max_usage_per_customer}
                    onChange={(e) => setFormData({ ...formData, max_usage_per_customer: Number(e.target.value) })}
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
                />
              </div>

              {/* Checkboxes */}
              <div className="flex gap-6">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={formData.is_active} 
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })} 
                    className="w-4 h-4" 
                  />
                  <span className="text-sm text-gray-300">Aktif</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={formData.stackable} 
                    onChange={(e) => setFormData({ ...formData, stackable: e.target.checked })} 
                    className="w-4 h-4" 
                  />
                  <span className="text-sm text-gray-300">Dapat Ditumpuk (Stackable)</span>
                </label>
              </div>

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

export default MasterDiscounts;
