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
  Plus, Search, Edit, Trash2, Save, X, Percent, Tag, 
  Calendar, Clock, DollarSign, RefreshCw, ChevronLeft,
  Package, Users, Building2, ShoppingCart
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const DISCOUNT_TYPES = [
  { value: 'percentage', label: 'Persentase (%)' },
  { value: 'nominal', label: 'Nominal (Rp)' },
  { value: 'per_pcs', label: 'Per Pcs (Rp/pcs)' },
  { value: 'per_item', label: 'Per Item' },
  { value: 'per_transaction', label: 'Per Transaksi' },
  { value: 'tiered', label: 'Bertingkat' },
];

const DISCOUNT_BASIS = [
  { value: 'transaction', label: 'Transaksi' },
  { value: 'item', label: 'Item' },
  { value: 'pcs', label: 'Per Qty' },
];

const MasterDiscountsAdvanced = () => {
  const [discounts, setDiscounts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('');
  const [filterActive, setFilterActive] = useState('');
  
  // Master data for selection
  const [branches, setBranches] = useState([]);
  const [customerGroups, setCustomerGroups] = useState([]);
  const [categories, setCategories] = useState([]);
  const [brands, setBrands] = useState([]);
  const [items, setItems] = useState([]);
  
  // Form state
  const [showForm, setShowForm] = useState(false);
  const [editingDiscount, setEditingDiscount] = useState(null);
  
  const [formData, setFormData] = useState({
    code: '',
    name: '',
    discount_type: 'percentage',
    basis: 'transaction',
    value: 0,
    min_purchase: 0,
    min_qty: 0,
    max_discount: 0,
    start_date: '',
    end_date: '',
    start_time: '00:00',
    end_time: '23:59',
    is_active: true,
    priority: 0,
    stackable: false,
    branches: [],
    customer_groups: [],
    categories: [],
    brands: [],
    items: [],
    notes: ''
  });

  const fetchDiscounts = useCallback(async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const params = new URLSearchParams();
      if (searchTerm) params.append('search', searchTerm);
      if (filterType && filterType !== 'all') params.append('discount_type', filterType);
      if (filterActive && filterActive !== 'all') params.append('is_active', filterActive);
      
      const res = await fetch(`${API_URL}/api/master-advanced/discounts?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      setDiscounts(data.items || []);
    } catch (err) {
      console.error('Error fetching discounts:', err);
    } finally {
      setLoading(false);
    }
  }, [searchTerm, filterType, filterActive]);

  const fetchMasterData = async () => {
    const token = localStorage.getItem('token');
    try {
      // Fetch branches
      const branchRes = await fetch(`${API_URL}/api/branches`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const branchData = await branchRes.json();
      setBranches(Array.isArray(branchData) ? branchData : branchData.items || []);

      // Fetch customer groups
      const groupRes = await fetch(`${API_URL}/api/master-advanced/customer-groups`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const groupData = await groupRes.json();
      setCustomerGroups(groupData.items || []);

      // Fetch categories
      const catRes = await fetch(`${API_URL}/api/master-erp/categories`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const catData = await catRes.json();
      setCategories(catData.items || []);

      // Fetch brands
      const brandRes = await fetch(`${API_URL}/api/master-erp/brands`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const brandData = await brandRes.json();
      setBrands(brandData.items || []);

      // Fetch items (limited)
      const itemRes = await fetch(`${API_URL}/api/master-erp/items?limit=100`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const itemData = await itemRes.json();
      setItems(itemData.items || []);
    } catch (err) {
      console.error('Error fetching master data:', err);
    }
  };

  useEffect(() => {
    fetchDiscounts();
    fetchMasterData();
  }, [fetchDiscounts]);

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

  const resetForm = () => {
    setFormData({
      code: '',
      name: '',
      discount_type: 'percentage',
      basis: 'transaction',
      value: 0,
      min_purchase: 0,
      min_qty: 0,
      max_discount: 0,
      start_date: '',
      end_date: '',
      start_time: '00:00',
      end_time: '23:59',
      is_active: true,
      priority: 0,
      stackable: false,
      branches: [],
      customer_groups: [],
      categories: [],
      brands: [],
      items: [],
      notes: ''
    });
    setEditingDiscount(null);
  };

  const openNewForm = () => {
    resetForm();
    setShowForm(true);
  };

  const openEditForm = async (discount) => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API_URL}/api/master-advanced/discounts/${discount.id}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      
      setFormData({
        code: data.code || '',
        name: data.name || '',
        discount_type: data.discount_type || 'percentage',
        basis: data.basis || 'transaction',
        value: data.value || 0,
        min_purchase: data.min_purchase || 0,
        min_qty: data.min_qty || 0,
        max_discount: data.max_discount || 0,
        start_date: data.start_date || '',
        end_date: data.end_date || '',
        start_time: data.start_time || '00:00',
        end_time: data.end_time || '23:59',
        is_active: data.is_active !== false,
        priority: data.priority || 0,
        stackable: data.stackable || false,
        branches: data.branches || [],
        customer_groups: data.customer_groups || [],
        categories: data.categories || [],
        brands: data.brands || [],
        items: data.items || [],
        notes: data.notes || ''
      });
      setEditingDiscount(data);
      setShowForm(true);
    } catch (err) {
      toast.error('Gagal memuat data diskon');
    }
  };

  const handleSubmit = async () => {
    if (!formData.name.trim()) {
      toast.error('Nama diskon wajib diisi');
      return;
    }
    if (formData.value <= 0) {
      toast.error('Nilai diskon harus lebih dari 0');
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const url = editingDiscount 
        ? `${API_URL}/api/master-advanced/discounts/${editingDiscount.id}`
        : `${API_URL}/api/master-advanced/discounts`;
      
      const res = await fetch(url, {
        method: editingDiscount ? 'PUT' : 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(formData)
      });

      const data = await res.json();
      
      if (res.ok && data.success) {
        toast.success(editingDiscount ? 'Diskon berhasil diupdate' : 'Diskon berhasil dibuat');
        setShowForm(false);
        resetForm();
        fetchDiscounts();
      } else {
        toast.error(data.detail || 'Gagal menyimpan diskon');
      }
    } catch (err) {
      toast.error('Terjadi kesalahan');
    }
  };

  const handleDelete = async (discount) => {
    if (!window.confirm(`Hapus diskon "${discount.name}"?`)) return;
    
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API_URL}/api/master-advanced/discounts/${discount.id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (res.ok) {
        toast.success('Diskon berhasil dihapus');
        fetchDiscounts();
      }
    } catch (err) {
      toast.error('Gagal menghapus diskon');
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(value || 0);
  };

  const getDiscountDisplay = (discount) => {
    const type = discount.discount_type;
    const value = discount.value;
    
    if (type === 'percentage') return `${value}%`;
    if (type === 'per_pcs') return `${formatCurrency(value)}/pcs`;
    return formatCurrency(value);
  };

  // Render Form
  if (showForm) {
    return (
      <div className="p-4 space-y-4" data-testid="discount-advanced-form">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={() => { setShowForm(false); resetForm(); }}>
            <ChevronLeft className="h-4 w-4 mr-1" />
            Kembali
          </Button>
          <h1 className="text-xl font-bold">
            {editingDiscount ? 'Edit Diskon' : 'Tambah Diskon Baru'}
          </h1>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Left Column - Basic Info */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Percent className="h-5 w-5" />
                Informasi Dasar
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Kode Diskon</Label>
                  <Input
                    value={formData.code}
                    onChange={(e) => handleInputChange('code', e.target.value)}
                    placeholder="Auto jika kosong"
                    data-testid="discount-code-input"
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
                <Label>Nama Diskon *</Label>
                <Input
                  value={formData.name}
                  onChange={(e) => handleInputChange('name', e.target.value)}
                  placeholder="Nama diskon"
                  data-testid="discount-name-input"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Jenis Diskon</Label>
                  <Select value={formData.discount_type} onValueChange={(v) => handleInputChange('discount_type', v)}>
                    <SelectTrigger data-testid="discount-type-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {DISCOUNT_TYPES.map(t => (
                        <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Basis Diskon</Label>
                  <Select value={formData.basis} onValueChange={(v) => handleInputChange('basis', v)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {DISCOUNT_BASIS.map(b => (
                        <SelectItem key={b.value} value={b.value}>{b.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Nilai Diskon *</Label>
                  <Input
                    type="number"
                    value={formData.value}
                    onChange={(e) => handleInputChange('value', parseFloat(e.target.value) || 0)}
                    placeholder="0"
                    data-testid="discount-value-input"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    {formData.discount_type === 'percentage' ? 'Dalam persen (%)' : 'Dalam Rupiah'}
                  </p>
                </div>
                <div>
                  <Label>Max Diskon (Rp)</Label>
                  <Input
                    type="number"
                    value={formData.max_discount}
                    onChange={(e) => handleInputChange('max_discount', parseFloat(e.target.value) || 0)}
                    placeholder="0 = tanpa batas"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Min. Belanja (Rp)</Label>
                  <Input
                    type="number"
                    value={formData.min_purchase}
                    onChange={(e) => handleInputChange('min_purchase', parseFloat(e.target.value) || 0)}
                    placeholder="0"
                  />
                </div>
                <div>
                  <Label>Min. Qty</Label>
                  <Input
                    type="number"
                    value={formData.min_qty}
                    onChange={(e) => handleInputChange('min_qty', parseInt(e.target.value) || 0)}
                    placeholder="0"
                  />
                </div>
              </div>

              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <Switch
                    checked={formData.is_active}
                    onCheckedChange={(v) => handleInputChange('is_active', v)}
                    data-testid="discount-active-switch"
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

          {/* Right Column - Period & Target */}
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
                      data-testid="discount-start-date"
                    />
                  </div>
                  <div>
                    <Label>Tanggal Selesai</Label>
                    <Input
                      type="date"
                      value={formData.end_date}
                      onChange={(e) => handleInputChange('end_date', e.target.value)}
                      data-testid="discount-end-date"
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
                <CardTitle className="text-lg flex items-center gap-2">
                  <Building2 className="h-5 w-5" />
                  Target Cabang
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-500 mb-2">Kosong = semua cabang</p>
                <div className="max-h-32 overflow-y-auto space-y-1">
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
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Users className="h-5 w-5" />
                  Target Grup Customer
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-500 mb-2">Kosong = semua grup</p>
                <div className="max-h-32 overflow-y-auto space-y-1">
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
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Target Items Section */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Target Kategori</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-gray-500 mb-2">Kosong = semua kategori</p>
              <div className="max-h-40 overflow-y-auto space-y-1">
                {categories.map(cat => (
                  <label key={cat.id} className="flex items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      checked={formData.categories.includes(cat.id)}
                      onChange={(e) => handleMultiSelect('categories', cat.id, e.target.checked)}
                      className="rounded"
                    />
                    {cat.name}
                  </label>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Target Brand</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-gray-500 mb-2">Kosong = semua brand</p>
              <div className="max-h-40 overflow-y-auto space-y-1">
                {brands.map(brand => (
                  <label key={brand.id} className="flex items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      checked={formData.brands.includes(brand.id)}
                      onChange={(e) => handleMultiSelect('brands', brand.id, e.target.checked)}
                      className="rounded"
                    />
                    {brand.name}
                  </label>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Target Item Spesifik</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-gray-500 mb-2">Kosong = semua item</p>
              <div className="max-h-40 overflow-y-auto space-y-1">
                {items.slice(0, 50).map(item => (
                  <label key={item.id} className="flex items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      checked={formData.items.includes(item.id)}
                      onChange={(e) => handleMultiSelect('items', item.id, e.target.checked)}
                      className="rounded"
                    />
                    <span className="truncate">{item.code} - {item.name}</span>
                  </label>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

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
          <Button onClick={handleSubmit} data-testid="save-discount-btn">
            <Save className="h-4 w-4 mr-1" />
            {editingDiscount ? 'Update' : 'Simpan'}
          </Button>
        </div>
      </div>
    );
  }

  // Render List
  return (
    <div className="p-4 space-y-4" data-testid="discount-advanced-list">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Percent className="h-6 w-6" />
            Master Diskon Advanced
          </h1>
          <p className="text-gray-500">Kelola diskon dengan berbagai jenis dan target</p>
        </div>
        <Button onClick={openNewForm} data-testid="add-discount-btn">
          <Plus className="h-4 w-4 mr-1" />
          Tambah Diskon
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
                  placeholder="Cari nama atau kode diskon..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                  data-testid="search-discount-input"
                />
              </div>
            </div>
            <Select value={filterType} onValueChange={setFilterType}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Semua Jenis" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Semua Jenis</SelectItem>
                {DISCOUNT_TYPES.map(t => (
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
            <Button variant="outline" onClick={fetchDiscounts}>
              <RefreshCw className="h-4 w-4" />
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Discount List */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-8 text-center text-gray-500">Loading...</div>
          ) : discounts.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              Belum ada data diskon
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Kode</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Nama</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Jenis</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Nilai</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Min Belanja</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Periode</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Aksi</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {discounts.map((discount) => (
                    <tr key={discount.id} className="hover:bg-gray-50" data-testid={`discount-row-${discount.id}`}>
                      <td className="px-4 py-3 text-sm font-medium">{discount.code}</td>
                      <td className="px-4 py-3">
                        <div>
                          <div className="font-medium">{discount.name}</div>
                          {discount.stackable && (
                            <Badge variant="outline" className="text-xs">Stackable</Badge>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant="outline">
                          {DISCOUNT_TYPES.find(t => t.value === discount.discount_type)?.label || discount.discount_type}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-sm font-semibold text-green-600">
                        {getDiscountDisplay(discount)}
                      </td>
                      <td className="px-4 py-3 text-sm">
                        {discount.min_purchase > 0 ? formatCurrency(discount.min_purchase) : '-'}
                      </td>
                      <td className="px-4 py-3 text-sm">
                        {discount.start_date || discount.end_date ? (
                          <div className="text-xs">
                            {discount.start_date && <div>Dari: {discount.start_date}</div>}
                            {discount.end_date && <div>Sampai: {discount.end_date}</div>}
                          </div>
                        ) : (
                          <span className="text-gray-400">Tanpa batas</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        {discount.is_active !== false ? (
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
                            onClick={() => openEditForm(discount)}
                            data-testid={`edit-discount-${discount.id}`}
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button 
                            size="sm" 
                            variant="ghost"
                            className="text-red-500 hover:text-red-700"
                            onClick={() => handleDelete(discount)}
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

export default MasterDiscountsAdvanced;
