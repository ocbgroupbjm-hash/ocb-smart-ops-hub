import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Badge } from '../../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { Switch } from '../../components/ui/switch';
import { Textarea } from '../../components/ui/textarea';
import { toast } from 'sonner';
import { 
  Plus, Search, Edit, Trash2, Save, X, Gift, Tag, 
  Calendar, Clock, DollarSign, RefreshCw, ChevronLeft,
  Package, Users, Building2, ShoppingCart, Sparkles
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const PROMO_TYPES = [
  { value: 'product', label: 'Promo Produk' },
  { value: 'category', label: 'Promo Kategori' },
  { value: 'brand', label: 'Promo Brand' },
  { value: 'bundle', label: 'Bundle' },
  { value: 'buy_x_get_y', label: 'Beli X Gratis Y' },
  { value: 'special_price', label: 'Harga Khusus' },
  { value: 'period', label: 'Promo Periode' },
  { value: 'branch', label: 'Promo Cabang' },
  { value: 'customer_group', label: 'Promo Grup Customer' },
  { value: 'quota', label: 'Promo dengan Kuota' },
];

const BENEFIT_TYPES = [
  { value: 'discount', label: 'Diskon' },
  { value: 'free_item', label: 'Item Gratis' },
  { value: 'bundle_price', label: 'Harga Bundle' },
  { value: 'special_price', label: 'Harga Spesial' },
];

const MasterPromotionsAdvanced = () => {
  const [promotions, setPromotions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('');
  const [filterActive, setFilterActive] = useState('');
  
  // Master data
  const [branches, setBranches] = useState([]);
  const [customerGroups, setCustomerGroups] = useState([]);
  const [categories, setCategories] = useState([]);
  const [brands, setBrands] = useState([]);
  const [items, setItems] = useState([]);
  
  // Form state
  const [showForm, setShowForm] = useState(false);
  const [editingPromo, setEditingPromo] = useState(null);
  
  const [formData, setFormData] = useState({
    code: '',
    name: '',
    promo_type: 'product',
    description: '',
    start_date: '',
    end_date: '',
    start_time: '00:00',
    end_time: '23:59',
    is_active: true,
    priority: 0,
    stackable: false,
    branches: [],
    customer_groups: [],
    quota: 0,
    rules: [],
    targets: [],
    notes: ''
  });
  
  // Rule form
  const [currentRule, setCurrentRule] = useState({
    target_type: 'all',
    condition_qty: 0,
    condition_subtotal: 0,
    trigger_items: [],
    benefit_type: 'discount',
    benefit_discount_type: 'percentage',
    benefit_discount_value: 0,
    benefit_free_item_id: '',
    benefit_free_item_qty: 0,
    benefit_special_price: 0
  });
  
  // Target form
  const [currentTarget, setCurrentTarget] = useState({
    item_id: '',
    item_code: '',
    item_name: '',
    category_id: '',
    brand_id: '',
    trigger_qty: 0,
    reward_qty: 0,
    discount_value: 0,
    special_price: 0,
    is_free: false
  });

  const fetchPromotions = useCallback(async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const params = new URLSearchParams();
      if (searchTerm) params.append('search', searchTerm);
      if (filterType && filterType !== 'all') params.append('promo_type', filterType);
      if (filterActive && filterActive !== 'all') params.append('is_active', filterActive);
      
      const res = await fetch(`${API_URL}/api/master-advanced/promotions?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      setPromotions(data.items || []);
    } catch (err) {
      console.error('Error fetching promotions:', err);
    } finally {
      setLoading(false);
    }
  }, [searchTerm, filterType, filterActive]);

  const fetchMasterData = async () => {
    const token = localStorage.getItem('token');
    try {
      const [branchRes, groupRes, catRes, brandRes, itemRes] = await Promise.all([
        fetch(`${API_URL}/api/branches`, { headers: { 'Authorization': `Bearer ${token}` } }),
        fetch(`${API_URL}/api/master-advanced/customer-groups`, { headers: { 'Authorization': `Bearer ${token}` } }),
        fetch(`${API_URL}/api/master-erp/categories`, { headers: { 'Authorization': `Bearer ${token}` } }),
        fetch(`${API_URL}/api/master-erp/brands`, { headers: { 'Authorization': `Bearer ${token}` } }),
        fetch(`${API_URL}/api/master-erp/items?limit=100`, { headers: { 'Authorization': `Bearer ${token}` } })
      ]);
      
      const branchData = await branchRes.json();
      const groupData = await groupRes.json();
      const catData = await catRes.json();
      const brandData = await brandRes.json();
      const itemData = await itemRes.json();
      
      setBranches(Array.isArray(branchData) ? branchData : branchData.items || []);
      setCustomerGroups(groupData.items || []);
      setCategories(catData.items || []);
      setBrands(brandData.items || []);
      setItems(itemData.items || []);
    } catch (err) {
      console.error('Error fetching master data:', err);
    }
  };

  useEffect(() => {
    fetchPromotions();
    fetchMasterData();
  }, [fetchPromotions]);

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleMultiSelect = (field, value, checked) => {
    setFormData(prev => ({
      ...prev,
      [field]: checked 
        ? [...prev[field], value]
        : prev[field].filter(v => v !== value)
    }));
  };

  const addRule = () => {
    setFormData(prev => ({
      ...prev,
      rules: [...prev.rules, { ...currentRule }]
    }));
    setCurrentRule({
      target_type: 'all',
      condition_qty: 0,
      condition_subtotal: 0,
      trigger_items: [],
      benefit_type: 'discount',
      benefit_discount_type: 'percentage',
      benefit_discount_value: 0,
      benefit_free_item_id: '',
      benefit_free_item_qty: 0,
      benefit_special_price: 0
    });
  };

  const removeRule = (index) => {
    setFormData(prev => ({
      ...prev,
      rules: prev.rules.filter((_, i) => i !== index)
    }));
  };

  const addTarget = () => {
    if (!currentTarget.item_id && !currentTarget.category_id && !currentTarget.brand_id) {
      toast.error('Pilih item, kategori, atau brand');
      return;
    }
    
    // Get item details if item_id selected
    const item = items.find(i => i.id === currentTarget.item_id);
    
    setFormData(prev => ({
      ...prev,
      targets: [...prev.targets, {
        ...currentTarget,
        item_code: item?.code || '',
        item_name: item?.name || ''
      }]
    }));
    
    setCurrentTarget({
      item_id: '',
      item_code: '',
      item_name: '',
      category_id: '',
      brand_id: '',
      trigger_qty: 0,
      reward_qty: 0,
      discount_value: 0,
      special_price: 0,
      is_free: false
    });
  };

  const removeTarget = (index) => {
    setFormData(prev => ({
      ...prev,
      targets: prev.targets.filter((_, i) => i !== index)
    }));
  };

  const resetForm = () => {
    setFormData({
      code: '',
      name: '',
      promo_type: 'product',
      description: '',
      start_date: '',
      end_date: '',
      start_time: '00:00',
      end_time: '23:59',
      is_active: true,
      priority: 0,
      stackable: false,
      branches: [],
      customer_groups: [],
      quota: 0,
      rules: [],
      targets: [],
      notes: ''
    });
    setEditingPromo(null);
  };

  const openNewForm = () => {
    resetForm();
    setShowForm(true);
  };

  const openEditForm = async (promo) => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API_URL}/api/master-advanced/promotions/${promo.id}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      
      setFormData({
        code: data.code || '',
        name: data.name || '',
        promo_type: data.promo_type || 'product',
        description: data.description || '',
        start_date: data.start_date || '',
        end_date: data.end_date || '',
        start_time: data.start_time || '00:00',
        end_time: data.end_time || '23:59',
        is_active: data.is_active !== false,
        priority: data.priority || 0,
        stackable: data.stackable || false,
        branches: data.branches || [],
        customer_groups: data.customer_groups || [],
        quota: data.quota || 0,
        rules: data.rules || [],
        targets: data.targets || [],
        notes: data.notes || ''
      });
      setEditingPromo(data);
      setShowForm(true);
    } catch (err) {
      toast.error('Gagal memuat data promosi');
    }
  };

  const handleSubmit = async () => {
    if (!formData.name.trim()) {
      toast.error('Nama promosi wajib diisi');
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const url = editingPromo 
        ? `${API_URL}/api/master-advanced/promotions/${editingPromo.id}`
        : `${API_URL}/api/master-advanced/promotions`;
      
      const res = await fetch(url, {
        method: editingPromo ? 'PUT' : 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(formData)
      });

      const data = await res.json();
      
      if (res.ok && data.success) {
        toast.success(editingPromo ? 'Promosi berhasil diupdate' : 'Promosi berhasil dibuat');
        setShowForm(false);
        resetForm();
        fetchPromotions();
      } else {
        toast.error(data.detail || 'Gagal menyimpan promosi');
      }
    } catch (err) {
      toast.error('Terjadi kesalahan');
    }
  };

  const handleDelete = async (promo) => {
    if (!window.confirm(`Hapus promosi "${promo.name}"?`)) return;
    
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API_URL}/api/master-advanced/promotions/${promo.id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (res.ok) {
        toast.success('Promosi berhasil dihapus');
        fetchPromotions();
      }
    } catch (err) {
      toast.error('Gagal menghapus promosi');
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(value || 0);
  };

  // Render Form
  if (showForm) {
    return (
      <div className="p-4 space-y-4" data-testid="promo-advanced-form">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={() => { setShowForm(false); resetForm(); }}>
            <ChevronLeft className="h-4 w-4 mr-1" />
            Kembali
          </Button>
          <h1 className="text-xl font-bold">
            {editingPromo ? 'Edit Promosi' : 'Tambah Promosi Baru'}
          </h1>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Left Column - Basic Info */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Gift className="h-5 w-5" />
                Informasi Dasar
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Kode Promo</Label>
                  <Input
                    value={formData.code}
                    onChange={(e) => handleInputChange('code', e.target.value)}
                    placeholder="Auto jika kosong"
                    data-testid="promo-code-input"
                  />
                </div>
                <div>
                  <Label>Prioritas</Label>
                  <Input
                    type="number"
                    value={formData.priority}
                    onChange={(e) => handleInputChange('priority', parseInt(e.target.value) || 0)}
                    placeholder="0"
                  />
                </div>
              </div>

              <div>
                <Label>Nama Promosi *</Label>
                <Input
                  value={formData.name}
                  onChange={(e) => handleInputChange('name', e.target.value)}
                  placeholder="Nama promosi"
                  data-testid="promo-name-input"
                />
              </div>

              <div>
                <Label>Jenis Promosi</Label>
                <Select value={formData.promo_type} onValueChange={(v) => handleInputChange('promo_type', v)}>
                  <SelectTrigger data-testid="promo-type-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {PROMO_TYPES.map(t => (
                      <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label>Deskripsi</Label>
                <Textarea
                  value={formData.description}
                  onChange={(e) => handleInputChange('description', e.target.value)}
                  placeholder="Deskripsi promosi"
                  rows={2}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Kuota</Label>
                  <Input
                    type="number"
                    value={formData.quota}
                    onChange={(e) => handleInputChange('quota', parseInt(e.target.value) || 0)}
                    placeholder="0 = unlimited"
                  />
                  <p className="text-xs text-gray-500 mt-1">0 = tanpa batas</p>
                </div>
              </div>

              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <Switch
                    checked={formData.is_active}
                    onCheckedChange={(v) => handleInputChange('is_active', v)}
                    data-testid="promo-active-switch"
                  />
                  <Label>Aktif</Label>
                </div>
                <div className="flex items-center gap-2">
                  <Switch
                    checked={formData.stackable}
                    onCheckedChange={(v) => handleInputChange('stackable', v)}
                  />
                  <Label>Stackable</Label>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Right Column - Period & Scope */}
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Calendar className="h-5 w-5" />
                  Periode Berlaku
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Tanggal Mulai</Label>
                    <Input
                      type="date"
                      value={formData.start_date}
                      onChange={(e) => handleInputChange('start_date', e.target.value)}
                      data-testid="promo-start-date"
                    />
                  </div>
                  <div>
                    <Label>Tanggal Selesai</Label>
                    <Input
                      type="date"
                      value={formData.end_date}
                      onChange={(e) => handleInputChange('end_date', e.target.value)}
                      data-testid="promo-end-date"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Jam Mulai</Label>
                    <Input
                      type="time"
                      value={formData.start_time}
                      onChange={(e) => handleInputChange('start_time', e.target.value)}
                    />
                  </div>
                  <div>
                    <Label>Jam Selesai</Label>
                    <Input
                      type="time"
                      value={formData.end_time}
                      onChange={(e) => handleInputChange('end_time', e.target.value)}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Target Cabang & Customer</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label className="text-xs">Cabang (kosong = semua)</Label>
                  <div className="max-h-24 overflow-y-auto space-y-1 mt-1">
                    {branches.map(branch => (
                      <label key={branch.id} className="flex items-center gap-2 text-sm">
                        <input
                          type="checkbox"
                          checked={formData.branches.includes(branch.id)}
                          onChange={(e) => handleMultiSelect('branches', branch.id, e.target.checked)}
                          className="rounded"
                        />
                        {branch.name}
                      </label>
                    ))}
                  </div>
                </div>
                <div>
                  <Label className="text-xs">Grup Customer (kosong = semua)</Label>
                  <div className="max-h-24 overflow-y-auto space-y-1 mt-1">
                    {customerGroups.map(group => (
                      <label key={group.id} className="flex items-center gap-2 text-sm">
                        <input
                          type="checkbox"
                          checked={formData.customer_groups.includes(group.id || group.code)}
                          onChange={(e) => handleMultiSelect('customer_groups', group.id || group.code, e.target.checked)}
                          className="rounded"
                        />
                        {group.name}
                      </label>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Rules Section */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Sparkles className="h-5 w-5" />
              Aturan Promosi (Rules)
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 p-4 bg-gray-50 rounded-lg">
              <div>
                <Label className="text-xs">Target Type</Label>
                <Select value={currentRule.target_type} onValueChange={(v) => setCurrentRule(prev => ({ ...prev, target_type: v }))}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Semua</SelectItem>
                    <SelectItem value="category">Kategori</SelectItem>
                    <SelectItem value="brand">Brand</SelectItem>
                    <SelectItem value="item">Item Spesifik</SelectItem>
                    <SelectItem value="bundle">Bundle</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label className="text-xs">Syarat Qty</Label>
                <Input
                  type="number"
                  value={currentRule.condition_qty}
                  onChange={(e) => setCurrentRule(prev => ({ ...prev, condition_qty: parseInt(e.target.value) || 0 }))}
                  placeholder="0"
                />
              </div>
              <div>
                <Label className="text-xs">Benefit Type</Label>
                <Select value={currentRule.benefit_type} onValueChange={(v) => setCurrentRule(prev => ({ ...prev, benefit_type: v }))}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {BENEFIT_TYPES.map(b => (
                      <SelectItem key={b.value} value={b.value}>{b.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label className="text-xs">Nilai Benefit</Label>
                <div className="flex gap-2">
                  <Input
                    type="number"
                    value={currentRule.benefit_discount_value}
                    onChange={(e) => setCurrentRule(prev => ({ ...prev, benefit_discount_value: parseFloat(e.target.value) || 0 }))}
                    placeholder="0"
                  />
                  <Button size="sm" onClick={addRule}>
                    <Plus className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </div>
            
            {formData.rules.length > 0 && (
              <div className="space-y-2">
                <Label className="text-sm font-semibold">Daftar Rules:</Label>
                {formData.rules.map((rule, index) => (
                  <div key={index} className="flex items-center justify-between p-2 bg-white border rounded">
                    <div className="text-sm">
                      <span className="font-medium">{rule.target_type}</span>
                      {rule.condition_qty > 0 && <span className="ml-2">Qty: {rule.condition_qty}</span>}
                      <span className="ml-2">→ {rule.benefit_type}: {rule.benefit_discount_value}</span>
                    </div>
                    <Button size="sm" variant="ghost" onClick={() => removeRule(index)}>
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Targets Section */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Package className="h-5 w-5" />
              Target Produk
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4 p-4 bg-gray-50 rounded-lg">
              <div>
                <Label className="text-xs">Item</Label>
                <Select value={currentTarget.item_id} onValueChange={(v) => setCurrentTarget(prev => ({ ...prev, item_id: v }))}>
                  <SelectTrigger>
                    <SelectValue placeholder="Pilih item" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">-- Pilih --</SelectItem>
                    {items.slice(0, 50).map(item => (
                      <SelectItem key={item.id} value={item.id}>{item.code} - {item.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label className="text-xs">Trigger Qty</Label>
                <Input
                  type="number"
                  value={currentTarget.trigger_qty}
                  onChange={(e) => setCurrentTarget(prev => ({ ...prev, trigger_qty: parseInt(e.target.value) || 0 }))}
                  placeholder="0"
                />
              </div>
              <div>
                <Label className="text-xs">Harga Spesial</Label>
                <Input
                  type="number"
                  value={currentTarget.special_price}
                  onChange={(e) => setCurrentTarget(prev => ({ ...prev, special_price: parseFloat(e.target.value) || 0 }))}
                  placeholder="0"
                />
              </div>
              <div className="flex items-end gap-2">
                <div className="flex items-center gap-2">
                  <Switch
                    checked={currentTarget.is_free}
                    onCheckedChange={(v) => setCurrentTarget(prev => ({ ...prev, is_free: v }))}
                  />
                  <Label className="text-xs">Gratis</Label>
                </div>
              </div>
              <div className="flex items-end">
                <Button size="sm" onClick={addTarget}>
                  <Plus className="h-4 w-4 mr-1" />
                  Tambah
                </Button>
              </div>
            </div>
            
            {formData.targets.length > 0 && (
              <div className="space-y-2">
                <Label className="text-sm font-semibold">Daftar Target:</Label>
                {formData.targets.map((target, index) => (
                  <div key={index} className="flex items-center justify-between p-2 bg-white border rounded">
                    <div className="text-sm">
                      <span className="font-medium">{target.item_code || 'Item'} - {target.item_name}</span>
                      {target.trigger_qty > 0 && <span className="ml-2">Qty: {target.trigger_qty}</span>}
                      {target.special_price > 0 && <span className="ml-2 text-green-600">Harga: {formatCurrency(target.special_price)}</span>}
                      {target.is_free && <Badge className="ml-2 bg-yellow-100 text-yellow-800">GRATIS</Badge>}
                    </div>
                    <Button size="sm" variant="ghost" onClick={() => removeTarget(index)}>
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <Label>Catatan</Label>
            <Textarea
              value={formData.notes}
              onChange={(e) => handleInputChange('notes', e.target.value)}
              placeholder="Catatan tambahan"
              rows={2}
            />
          </CardContent>
        </Card>

        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={() => { setShowForm(false); resetForm(); }}>
            <X className="h-4 w-4 mr-1" />
            Batal
          </Button>
          <Button onClick={handleSubmit} data-testid="save-promo-btn">
            <Save className="h-4 w-4 mr-1" />
            {editingPromo ? 'Update' : 'Simpan'}
          </Button>
        </div>
      </div>
    );
  }

  // Render List
  return (
    <div className="p-4 space-y-4" data-testid="promo-advanced-list">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Gift className="h-6 w-6" />
            Master Promosi Advanced
          </h1>
          <p className="text-gray-500">Kelola promosi dengan berbagai jenis dan aturan</p>
        </div>
        <Button onClick={openNewForm} data-testid="add-promo-btn">
          <Plus className="h-4 w-4 mr-1" />
          Tambah Promosi
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap gap-4">
            <div className="flex-1 min-w-[200px]">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Cari nama atau kode promo..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                  data-testid="search-promo-input"
                />
              </div>
            </div>
            <Select value={filterType} onValueChange={setFilterType}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Semua Jenis" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Semua Jenis</SelectItem>
                {PROMO_TYPES.map(t => (
                  <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={filterActive} onValueChange={setFilterActive}>
              <SelectTrigger className="w-[140px]">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Semua</SelectItem>
                <SelectItem value="true">Aktif</SelectItem>
                <SelectItem value="false">Nonaktif</SelectItem>
              </SelectContent>
            </Select>
            <Button variant="outline" onClick={fetchPromotions}>
              <RefreshCw className="h-4 w-4" />
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Promotion List */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-8 text-center text-gray-500">Loading...</div>
          ) : promotions.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              Belum ada data promosi
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Kode</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Nama</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Jenis</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Periode</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Kuota</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Aksi</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {promotions.map((promo) => (
                    <tr key={promo.id} className="hover:bg-gray-50" data-testid={`promo-row-${promo.id}`}>
                      <td className="px-4 py-3 text-sm font-medium">{promo.code}</td>
                      <td className="px-4 py-3">
                        <div>
                          <div className="font-medium">{promo.name}</div>
                          {promo.description && (
                            <div className="text-xs text-gray-500 truncate max-w-xs">{promo.description}</div>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant="outline">
                          {PROMO_TYPES.find(t => t.value === promo.promo_type)?.label || promo.promo_type}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-sm">
                        {promo.start_date || promo.end_date ? (
                          <div className="text-xs">
                            {promo.start_date && <div>Dari: {promo.start_date}</div>}
                            {promo.end_date && <div>Sampai: {promo.end_date}</div>}
                          </div>
                        ) : (
                          <span className="text-gray-400">Tanpa batas</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-sm">
                        {promo.quota > 0 ? (
                          <span>{promo.used_count || 0} / {promo.quota}</span>
                        ) : (
                          <span className="text-gray-400">Unlimited</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        {promo.is_active !== false ? (
                          <Badge className="bg-green-100 text-green-800">Aktif</Badge>
                        ) : (
                          <Badge variant="destructive">Nonaktif</Badge>
                        )}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <div className="flex items-center justify-center gap-1">
                          <Button 
                            size="sm" 
                            variant="ghost" 
                            onClick={() => openEditForm(promo)}
                            data-testid={`edit-promo-${promo.id}`}
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button 
                            size="sm" 
                            variant="ghost"
                            className="text-red-500 hover:text-red-700"
                            onClick={() => handleDelete(promo)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default MasterPromotionsAdvanced;
