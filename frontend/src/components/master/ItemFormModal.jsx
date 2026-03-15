import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { toast } from 'sonner';
import { 
  X, Save, Package, DollarSign, Warehouse, Calculator, 
  Plus, Trash2, Check, Tag, Users, Layers, Info, AlertCircle
} from 'lucide-react';
import { SearchableSelect } from '../ui/searchable-select';
import { SearchableEnumSelect } from '../ui/searchable-enum-select';
import { SearchableSelectWithCreate } from './QuickCreateModal';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Pricing modes
const PRICING_MODES = [
  { code: 'single', name: 'Satu Harga', icon: DollarSign, description: 'Produk hanya memiliki satu harga jual tetap' },
  { code: 'quantity', name: 'Berdasarkan Jumlah', icon: Package, description: 'Harga berubah berdasarkan jumlah pembelian' },
  { code: 'level', name: 'Level Harga', icon: Users, description: 'Harga berbeda berdasarkan tipe customer' },
  { code: 'unit', name: 'Berdasarkan Satuan', icon: Layers, description: 'Harga berbeda berdasarkan satuan' }
];

// Customer levels
const CUSTOMER_LEVELS = ['retail', 'member', 'reseller', 'distributor', 'grosir'];

export default function ItemFormModal({
  isOpen,
  onClose,
  editingItem,
  token,
  categories = [],
  units = [],
  brands = [],
  suppliers = [],
  onSave,
  onRefreshMasterData  // Callback untuk refresh master data setelah quick create
}) {
  const [activeTab, setActiveTab] = useState('data');
  const [saving, setSaving] = useState(false);
  
  // Local state for dynamically added items
  const [localCategories, setLocalCategories] = useState([]);
  const [localUnits, setLocalUnits] = useState([]);
  const [localBrands, setLocalBrands] = useState([]);
  
  // Merge passed props with locally added items
  const allCategories = useMemo(() => [...categories, ...localCategories], [categories, localCategories]);
  const allUnits = useMemo(() => [...units, ...localUnits], [units, localUnits]);
  const allBrands = useMemo(() => [...brands, ...localBrands], [brands, localBrands]);
  
  // Convert master data to options format for SearchableSelect
  const categoryOptions = useMemo(() => 
    allCategories.map(c => ({ value: c.id, label: c.name, sublabel: c.code })), 
    [allCategories]
  );
  
  const unitOptions = useMemo(() => 
    allUnits.map(u => ({ value: u.id, label: u.name, sublabel: u.code })), 
    [allUnits]
  );
  
  const brandOptions = useMemo(() => 
    allBrands.map(b => ({ value: b.id, label: b.name, sublabel: b.code })), 
    [allBrands]
  );
  
  const supplierOptions = useMemo(() => 
    suppliers.map(s => ({ value: s.id, label: s.name, sublabel: s.code })), 
    [suppliers]
  );
  
  // Handler for quick create success - add to local state and optionally refresh parent
  const handleQuickCreateSuccess = useCallback((type, newItem) => {
    switch (type) {
      case 'category':
        setLocalCategories(prev => [...prev, newItem]);
        break;
      case 'unit':
        setLocalUnits(prev => [...prev, newItem]);
        break;
      case 'brand':
        setLocalBrands(prev => [...prev, newItem]);
        break;
    }
    
    // Optionally refresh parent's master data
    if (onRefreshMasterData) {
      onRefreshMasterData(type);
    }
  }, [onRefreshMasterData]);
  
  // Item type options for searchable enum
  const itemTypeOptions = [
    { value: 'barang', label: 'Barang' },
    { value: 'jasa', label: 'Jasa' },
    { value: 'rakitan', label: 'Rakitan' },
    { value: 'non-inventory', label: 'Non-Inventory' },
    { value: 'biaya', label: 'Biaya' },
  ];
  
  // Form data - TAB 1: Data Umum
  const [formData, setFormData] = useState({
    code: '',
    barcode: '',
    name: '',
    category_id: '',
    unit_id: '',
    brand_id: '',
    rack: '',
    item_type: 'barang',
    cost_price: 0,
    selling_price: 0,
    description: '',
    is_active: true,
    track_stock: true,
    discontinued: false,
    // New fields
    sku_internal: '',
    supplier_id: '',
    weight: 0,
    weight_unit: 'gr',
    has_serial: false,
    has_expired: false
  });
  
  // TAB 2: Pricing Config
  const [pricingMode, setPricingMode] = useState('single');
  const [quantityPrices, setQuantityPrices] = useState([]);
  const [priceLevels, setPriceLevels] = useState({
    retail: 0, member: 0, reseller: 0, distributor: 0, grosir: 0
  });
  const [unitPrices, setUnitPrices] = useState([]);
  const [allowPriceSelection, setAllowPriceSelection] = useState(false);
  
  // TAB 3: Stock Config
  const [stockConfig, setStockConfig] = useState({
    min_stock: 0,
    max_stock: 0,
    default_rack: ''
  });
  
  // TAB 4: Accounting
  const [accountConfig, setAccountConfig] = useState({
    inventory_account: '',
    sales_account: '',
    cogs_account: '',
    return_account: '',
    discount_account: ''
  });

  // Load item data when editing
  useEffect(() => {
    if (editingItem) {
      setFormData({
        code: editingItem.code || '',
        barcode: editingItem.barcode || '',
        name: editingItem.name || '',
        category_id: editingItem.category_id || '',
        unit_id: editingItem.unit_id || '',
        brand_id: editingItem.brand_id || '',
        rack: editingItem.rack || '',
        item_type: editingItem.item_type || 'barang',
        cost_price: editingItem.cost_price || 0,
        selling_price: editingItem.selling_price || 0,
        description: editingItem.description || '',
        is_active: editingItem.is_active !== false,
        track_stock: editingItem.track_stock !== false,
        discontinued: editingItem.discontinued || false,
        sku_internal: editingItem.sku_internal || '',
        supplier_id: editingItem.supplier_id || '',
        weight: editingItem.weight || 0,
        weight_unit: editingItem.weight_unit || 'gr',
        has_serial: editingItem.has_serial || false,
        has_expired: editingItem.has_expired || false
      });
      
      // Load pricing config
      loadPricingConfig(editingItem.id);
    } else {
      resetForm();
    }
  }, [editingItem]);

  const resetForm = () => {
    setFormData({
      code: '', barcode: '', name: '', category_id: '', unit_id: '', brand_id: '',
      rack: '', item_type: 'barang', cost_price: 0, selling_price: 0, description: '',
      is_active: true, track_stock: true, discontinued: false,
      sku_internal: '', supplier_id: '', weight: 0, weight_unit: 'gr',
      has_serial: false, has_expired: false
    });
    setPricingMode('single');
    setQuantityPrices([]);
    setPriceLevels({ retail: 0, member: 0, reseller: 0, distributor: 0, grosir: 0 });
    setUnitPrices([]);
    setAllowPriceSelection(false);
    setStockConfig({ min_stock: 0, max_stock: 0, default_rack: '' });
    setActiveTab('data');
  };

  const loadPricingConfig = async (productId) => {
    try {
      const res = await fetch(`${API_URL}/api/pricing/product/${productId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        const pricing = data.pricing;
        setPricingMode(pricing.pricing_mode || 'single');
        setQuantityPrices(pricing.quantity_prices || []);
        setPriceLevels(pricing.price_levels || { retail: 0, member: 0, reseller: 0, distributor: 0, grosir: 0 });
        setUnitPrices(pricing.unit_prices || []);
        setAllowPriceSelection(pricing.allow_price_selection || false);
      }
    } catch (err) {
      console.error('Failed to load pricing config', err);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validation - skip code check if AUTO
    if (!formData.code.trim() || (formData.code !== 'AUTO' && !formData.code.trim())) {
      toast.error('Kode Item wajib diisi atau pilih AUTO');
      return;
    }
    if (!formData.name.trim()) {
      toast.error('Nama Item wajib diisi');
      return;
    }
    if (!formData.unit_id) {
      toast.error('Satuan wajib dipilih');
      return;
    }
    if (formData.cost_price < 0) {
      toast.error('Harga Beli tidak boleh negatif');
      return;
    }
    if (formData.selling_price < 0) {
      toast.error('Harga Jual tidak boleh negatif');
      return;
    }
    
    // Validate pricing mode specific requirements
    if (pricingMode === 'quantity' && quantityPrices.length === 0) {
      toast.error('Mode Berdasarkan Jumlah memerlukan minimal 1 tier harga');
      setActiveTab('pricing');
      return;
    }
    if (pricingMode === 'level') {
      const hasLevel = Object.values(priceLevels).some(p => p > 0);
      if (!hasLevel) {
        toast.error('Mode Level Harga memerlukan minimal 1 level dengan harga');
        setActiveTab('pricing');
        return;
      }
    }
    if (pricingMode === 'unit' && unitPrices.length === 0) {
      toast.error('Mode Berdasarkan Satuan memerlukan minimal 1 satuan harga');
      setActiveTab('pricing');
      return;
    }

    setSaving(true);
    try {
      // If AUTO code, generate from number settings engine
      let finalCode = formData.code;
      if (formData.code === 'AUTO') {
        try {
          const genRes = await fetch(`${API_URL}/api/number-settings/generate/master?entity_type=item`, {
            method: 'POST',
            headers: { Authorization: `Bearer ${token}` }
          });
          if (genRes.ok) {
            const genData = await genRes.json();
            finalCode = genData.code;
            toast.info(`Kode otomatis: ${finalCode}`);
          } else {
            throw new Error('Gagal generate kode otomatis');
          }
        } catch (err) {
          toast.error('Gagal generate kode otomatis: ' + err.message);
          setSaving(false);
          return;
        }
      }
      
      // Step 1: Save item data (without branch_id!)
      const url = editingItem 
        ? `${API_URL}/api/master/items/${editingItem.id}`
        : `${API_URL}/api/master/items`;
      const method = editingItem ? 'PUT' : 'POST';
      
      // Prepare item payload - NO branch_id
      const itemPayload = {
        code: finalCode,
        barcode: formData.barcode,
        name: formData.name,
        category_id: formData.category_id,
        unit_id: formData.unit_id,
        brand_id: formData.brand_id,
        rack: formData.rack,
        item_type: formData.item_type,
        cost_price: formData.cost_price,
        selling_price: formData.selling_price,
        description: formData.description,
        is_active: formData.is_active,
        track_stock: formData.track_stock,
        discontinued: formData.discontinued,
        sku_internal: formData.sku_internal,
        supplier_id: formData.supplier_id,
        weight: formData.weight,
        weight_unit: formData.weight_unit,
        has_serial: formData.has_serial,
        has_expired: formData.has_expired,
        pricing_mode: pricingMode
      };

      const itemRes = await fetch(url, {
        method,
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(itemPayload)
      });

      if (!itemRes.ok) {
        const err = await itemRes.json();
        throw new Error(err.detail || 'Gagal menyimpan item');
      }

      const itemData = await itemRes.json();
      const productId = editingItem?.id || itemData.id;

      // Step 2: Save pricing config if not single mode or has custom config
      if (pricingMode !== 'single' || quantityPrices.length > 0 || Object.values(priceLevels).some(p => p > 0)) {
        const pricingPayload = {
          pricing_mode: pricingMode,
          selling_price: formData.selling_price,
          quantity_prices: quantityPrices,
          price_levels: priceLevels,
          unit_prices: unitPrices,
          allow_price_selection: allowPriceSelection,
          default_level: 'retail'
        };

        await fetch(`${API_URL}/api/pricing/product/${productId}`, {
          method: 'PUT',
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(pricingPayload)
        });
      }

      toast.success(editingItem ? 'Item berhasil diupdate' : 'Item berhasil ditambahkan');
      onSave && onSave();
      onClose();
    } catch (err) {
      toast.error(err.message || 'Gagal menyimpan item');
    } finally {
      setSaving(false);
    }
  };

  // Quantity price handlers
  const addQuantityRule = () => {
    setQuantityPrices([...quantityPrices, { min_qty: 1, max_qty: null, price: formData.selling_price }]);
  };

  const updateQuantityRule = (index, field, value) => {
    const updated = [...quantityPrices];
    updated[index][field] = field === 'price' ? parseFloat(value) || 0 : parseInt(value) || null;
    setQuantityPrices(updated);
  };

  const removeQuantityRule = (index) => {
    setQuantityPrices(quantityPrices.filter((_, i) => i !== index));
  };

  // Unit price handlers
  const addUnitPrice = () => {
    setUnitPrices([...unitPrices, { unit_id: '', unit_name: '', conversion: 1, price: formData.selling_price }]);
  };

  const updateUnitPrice = (index, field, value) => {
    const updated = [...unitPrices];
    if (field === 'unit_id') {
      const selectedUnit = units.find(u => u.id === value);
      updated[index].unit_id = value;
      updated[index].unit_name = selectedUnit?.name || '';
    } else if (field === 'price' || field === 'conversion') {
      updated[index][field] = parseFloat(value) || 0;
    }
    setUnitPrices(updated);
  };

  const removeUnitPrice = (index) => {
    setUnitPrices(unitPrices.filter((_, i) => i !== index));
  };

  if (!isOpen) return null;

  const tabs = [
    { id: 'data', name: 'Data Umum', icon: Package },
    { id: 'pricing', name: 'Harga Jual', icon: DollarSign },
    { id: 'stock', name: 'Stok & Gudang', icon: Warehouse },
    { id: 'accounting', name: 'Akunting', icon: Calculator }
  ];

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-[#111] border border-[#333] rounded-xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-4 py-3 border-b border-[#333] bg-[#0d0d0d] flex items-center justify-between">
          <h3 className="text-lg font-bold text-white flex items-center gap-2">
            <Package className="w-5 h-5 text-red-400" />
            {editingItem ? 'Edit Item' : 'Tambah Item Baru'}
          </h3>
          <button onClick={onClose} className="p-1 hover:bg-[#222] rounded">
            <X className="w-5 h-5 text-gray-400" />
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="flex border-b border-[#333] bg-[#0d0d0d] px-2">
          {tabs.map(tab => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? 'border-red-500 text-red-400'
                    : 'border-transparent text-gray-400 hover:text-white'
                }`}
              >
                <Icon className="w-4 h-4" />
                {tab.name}
              </button>
            );
          })}
        </div>

        {/* Tab Content */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto">
          <div className="p-4">
            {/* TAB 1: Data Umum */}
            {activeTab === 'data' && (
              <div className="space-y-4">
                {/* Info Banner */}
                <div className="p-3 bg-blue-900/20 border border-blue-800/30 rounded-lg flex items-start gap-2">
                  <Info className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
                  <p className="text-xs text-blue-300">
                    Master Item bersifat <strong>global</strong>. Penempatan item per cabang diatur melalui modul Stok Cabang.
                  </p>
                </div>

                {/* Row 1: Code Mode, Code, Barcode */}
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="block text-xs text-gray-400 mb-1">Mode Kode</label>
                    <select
                      value={formData.code === 'AUTO' || formData.code_mode === 'auto' ? 'auto' : 'manual'}
                      onChange={async (e) => {
                        if (e.target.value === 'auto') {
                          setFormData({ ...formData, code: 'AUTO', code_mode: 'auto' });
                        } else {
                          setFormData({ ...formData, code: '', code_mode: 'manual' });
                        }
                      }}
                      className="w-full px-3 py-2 bg-[#0a0a0a] border border-[#333] rounded-lg text-white text-sm"
                      data-testid="code-mode-select"
                    >
                      <option value="auto">AUTO</option>
                      <option value="manual">MANUAL</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs text-gray-400 mb-1">Kode Item <span className="text-red-400">*</span></label>
                    <input
                      type="text"
                      value={formData.code}
                      onChange={(e) => setFormData({ ...formData, code: e.target.value.toUpperCase(), code_mode: 'manual' })}
                      className={`w-full px-3 py-2 bg-[#0a0a0a] border border-[#333] rounded-lg text-sm ${
                        formData.code === 'AUTO' ? 'text-amber-400 font-semibold' : 'text-white'
                      }`}
                      placeholder={formData.code === 'AUTO' ? 'Akan di-generate otomatis' : 'Input kode manual'}
                      disabled={formData.code === 'AUTO'}
                      required
                      data-testid="item-code-input"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-400 mb-1">Barcode</label>
                    <input
                      type="text"
                      value={formData.barcode}
                      onChange={(e) => setFormData({ ...formData, barcode: e.target.value })}
                      className="w-full px-3 py-2 bg-[#0a0a0a] border border-[#333] rounded-lg text-white text-sm"
                      placeholder="Scan atau input manual"
                      data-testid="item-barcode-input"
                    />
                  </div>
                </div>

                {/* Row 2: Name */}
                <div>
                  <label className="block text-xs text-gray-400 mb-1">Nama Item <span className="text-red-400">*</span></label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-3 py-2 bg-[#0a0a0a] border border-[#333] rounded-lg text-white text-sm"
                    placeholder="Nama produk"
                    required
                  />
                </div>

                {/* Row 3: Type, Category, Unit */}
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="block text-xs text-gray-400 mb-1">Tipe Item</label>
                    <SearchableEnumSelect
                      options={itemTypeOptions}
                      value={formData.item_type}
                      onValueChange={(val) => setFormData({ ...formData, item_type: val })}
                      placeholder="Pilih Tipe"
                      data-testid="item-type-select"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-400 mb-1">
                      Kategori
                      <span className="text-green-400 text-[10px] ml-1">(+ Baru)</span>
                    </label>
                    <SearchableSelectWithCreate
                      options={categoryOptions}
                      value={formData.category_id}
                      onValueChange={(val) => setFormData({ ...formData, category_id: val })}
                      placeholder="Pilih Kategori"
                      searchPlaceholder="Ketik kategori..."
                      type="category"
                      token={token}
                      onItemCreated={handleQuickCreateSuccess}
                      data-testid="category-select"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-400 mb-1">
                      Satuan <span className="text-red-400">*</span>
                      <span className="text-green-400 text-[10px] ml-1">(+ Baru)</span>
                    </label>
                    <SearchableSelectWithCreate
                      options={unitOptions}
                      value={formData.unit_id}
                      onValueChange={(val) => setFormData({ ...formData, unit_id: val })}
                      placeholder="Pilih Satuan"
                      searchPlaceholder="Ketik satuan..."
                      type="unit"
                      token={token}
                      onItemCreated={handleQuickCreateSuccess}
                      data-testid="unit-select"
                    />
                  </div>
                </div>

                {/* Row 4: Brand, Rack, SKU */}
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="block text-xs text-gray-400 mb-1">
                      Merek
                      <span className="text-green-400 text-[10px] ml-1">(+ Baru)</span>
                    </label>
                    <SearchableSelectWithCreate
                      options={brandOptions}
                      value={formData.brand_id}
                      onValueChange={(val) => setFormData({ ...formData, brand_id: val })}
                      placeholder="Pilih Merek"
                      searchPlaceholder="Ketik merek..."
                      type="brand"
                      token={token}
                      onItemCreated={handleQuickCreateSuccess}
                      data-testid="brand-select"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-400 mb-1">Rak Default</label>
                    <input
                      type="text"
                      value={formData.rack}
                      onChange={(e) => setFormData({ ...formData, rack: e.target.value })}
                      className="w-full px-3 py-2 bg-[#0a0a0a] border border-[#333] rounded-lg text-white text-sm"
                      placeholder="Contoh: A-01"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-400 mb-1">SKU Internal</label>
                    <input
                      type="text"
                      value={formData.sku_internal}
                      onChange={(e) => setFormData({ ...formData, sku_internal: e.target.value })}
                      className="w-full px-3 py-2 bg-[#0a0a0a] border border-[#333] rounded-lg text-white text-sm"
                      placeholder="SKU internal"
                    />
                  </div>
                </div>

                {/* Row 5: Cost Price, Default Selling Price */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs text-gray-400 mb-1">Harga Beli</label>
                    <div className="flex items-center gap-2">
                      <span className="text-gray-400 text-sm">Rp</span>
                      <input
                        type="number"
                        value={formData.cost_price}
                        onChange={(e) => setFormData({ ...formData, cost_price: parseInt(e.target.value) || 0 })}
                        className="flex-1 px-3 py-2 bg-[#0a0a0a] border border-[#333] rounded-lg text-white text-sm font-mono"
                        min="0"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-xs text-gray-400 mb-1">Harga Jual Default</label>
                    <div className="flex items-center gap-2">
                      <span className="text-gray-400 text-sm">Rp</span>
                      <input
                        type="number"
                        value={formData.selling_price}
                        onChange={(e) => setFormData({ ...formData, selling_price: parseInt(e.target.value) || 0 })}
                        className="flex-1 px-3 py-2 bg-[#0a0a0a] border border-[#333] rounded-lg text-white text-sm font-mono"
                        min="0"
                      />
                    </div>
                    <p className="text-[10px] text-gray-500 mt-1">
                      Digunakan sebagai fallback jika tidak ada rule harga yang cocok
                    </p>
                  </div>
                </div>

                {/* Row 6: Weight, Supplier */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs text-gray-400 mb-1">Berat</label>
                    <div className="flex gap-2">
                      <input
                        type="number"
                        value={formData.weight}
                        onChange={(e) => setFormData({ ...formData, weight: parseFloat(e.target.value) || 0 })}
                        className="flex-1 px-3 py-2 bg-[#0a0a0a] border border-[#333] rounded-lg text-white text-sm"
                        min="0"
                      />
                      <select
                        value={formData.weight_unit}
                        onChange={(e) => setFormData({ ...formData, weight_unit: e.target.value })}
                        className="w-20 px-2 py-2 bg-[#0a0a0a] border border-[#333] rounded-lg text-white text-sm"
                      >
                        <option value="gr">gr</option>
                        <option value="kg">kg</option>
                        <option value="ml">ml</option>
                        <option value="l">l</option>
                      </select>
                    </div>
                  </div>
                  <div>
                    <label className="block text-xs text-gray-400 mb-1">Supplier Default</label>
                    <SearchableSelect
                      options={supplierOptions}
                      value={formData.supplier_id}
                      onValueChange={(val) => setFormData({ ...formData, supplier_id: val })}
                      placeholder="Pilih Supplier"
                      searchPlaceholder="Ketik nama supplier..."
                      data-testid="supplier-select"
                    />
                  </div>
                </div>

                {/* Row 7: Description */}
                <div>
                  <label className="block text-xs text-gray-400 mb-1">Deskripsi</label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    className="w-full px-3 py-2 bg-[#0a0a0a] border border-[#333] rounded-lg text-white text-sm"
                    rows={2}
                    placeholder="Deskripsi produk (opsional)"
                  />
                </div>

                {/* Row 8: Checkboxes */}
                <div className="flex flex-wrap items-center gap-x-6 gap-y-2">
                  <label className="flex items-center gap-2 text-sm text-gray-300 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.is_active}
                      onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                      className="w-4 h-4 rounded bg-[#0a0a0a] border-[#333]"
                    />
                    Aktif
                  </label>
                  <label className="flex items-center gap-2 text-sm text-gray-300 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.track_stock}
                      onChange={(e) => setFormData({ ...formData, track_stock: e.target.checked })}
                      className="w-4 h-4 rounded bg-[#0a0a0a] border-[#333]"
                    />
                    Track Stok
                  </label>
                  <label className="flex items-center gap-2 text-sm text-gray-300 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.has_serial}
                      onChange={(e) => setFormData({ ...formData, has_serial: e.target.checked })}
                      className="w-4 h-4 rounded bg-[#0a0a0a] border-[#333]"
                    />
                    Serial Number
                  </label>
                  <label className="flex items-center gap-2 text-sm text-gray-300 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.has_expired}
                      onChange={(e) => setFormData({ ...formData, has_expired: e.target.checked })}
                      className="w-4 h-4 rounded bg-[#0a0a0a] border-[#333]"
                    />
                    Expired Date
                  </label>
                  <label className="flex items-center gap-2 text-sm text-gray-300 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.discontinued}
                      onChange={(e) => setFormData({ ...formData, discontinued: e.target.checked })}
                      className="w-4 h-4 rounded bg-[#0a0a0a] border-[#333]"
                    />
                    Discontinued
                  </label>
                </div>
              </div>
            )}

            {/* TAB 2: Harga Jual */}
            {activeTab === 'pricing' && (
              <div className="space-y-4">
                {/* Mode Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-3">Pilih Mode Harga</label>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {PRICING_MODES.map(mode => {
                      const Icon = mode.icon;
                      const isSelected = pricingMode === mode.code;
                      return (
                        <button
                          key={mode.code}
                          type="button"
                          onClick={() => setPricingMode(mode.code)}
                          className={`p-3 rounded-xl border-2 transition-all text-left ${
                            isSelected
                              ? 'border-green-500 bg-green-500/10'
                              : 'border-[#333] bg-[#1a1a1a] hover:border-[#444]'
                          }`}
                        >
                          <div className="flex items-center gap-2 mb-1">
                            <Icon className={`w-4 h-4 ${isSelected ? 'text-green-400' : 'text-gray-400'}`} />
                            {isSelected && <Check className="w-3 h-3 text-green-400 ml-auto" />}
                          </div>
                          <div className="text-xs font-medium text-white">{mode.name}</div>
                          <div className="text-[10px] text-gray-500 mt-0.5">{mode.description}</div>
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* MODE: SINGLE - Just show default price info */}
                {pricingMode === 'single' && (
                  <div className="p-4 bg-[#1a1a1a] rounded-xl border border-[#333]">
                    <div className="flex items-center gap-2 text-green-400 mb-2">
                      <DollarSign className="w-4 h-4" />
                      <span className="font-medium">Satu Harga</span>
                    </div>
                    <p className="text-sm text-gray-400">
                      Produk menggunakan <strong className="text-white">Harga Jual Default</strong> yang diatur di tab Data Umum.
                    </p>
                    <div className="mt-3 p-3 bg-[#0a0a0a] rounded-lg">
                      <span className="text-xs text-gray-500">Harga Jual:</span>
                      <span className="text-xl text-green-400 font-bold ml-2">
                        Rp {formData.selling_price.toLocaleString('id-ID')}
                      </span>
                    </div>
                  </div>
                )}

                {/* MODE: QUANTITY */}
                {pricingMode === 'quantity' && (
                  <div className="p-4 bg-[#1a1a1a] rounded-xl border border-[#333]">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-2 text-blue-400">
                        <Package className="w-4 h-4" />
                        <span className="font-medium">Harga Berdasarkan Jumlah</span>
                      </div>
                      <button
                        type="button"
                        onClick={addQuantityRule}
                        className="px-3 py-1.5 bg-blue-600/20 text-blue-400 rounded-lg text-xs flex items-center gap-1 hover:bg-blue-600/30"
                      >
                        <Plus className="w-3 h-3" /> Tambah Tier
                      </button>
                    </div>

                    {quantityPrices.length === 0 ? (
                      <div className="text-center py-6 text-gray-500">
                        <Package className="w-8 h-8 mx-auto mb-2 opacity-50" />
                        <p className="text-sm">Klik "Tambah Tier" untuk menambahkan aturan harga</p>
                      </div>
                    ) : (
                      <div className="space-y-2">
                        <div className="grid grid-cols-4 gap-2 text-xs text-gray-400 px-2">
                          <div>Min Qty</div>
                          <div>Max Qty</div>
                          <div>Harga</div>
                          <div></div>
                        </div>
                        {quantityPrices.map((rule, index) => (
                          <div key={index} className="grid grid-cols-4 gap-2 items-center">
                            <input
                              type="number"
                              value={rule.min_qty}
                              onChange={(e) => updateQuantityRule(index, 'min_qty', e.target.value)}
                              className="px-3 py-2 bg-[#0a0a0a] border border-[#333] rounded-lg text-white text-sm"
                              placeholder="Min"
                              min="1"
                            />
                            <input
                              type="number"
                              value={rule.max_qty || ''}
                              onChange={(e) => updateQuantityRule(index, 'max_qty', e.target.value)}
                              className="px-3 py-2 bg-[#0a0a0a] border border-[#333] rounded-lg text-white text-sm"
                              placeholder="∞"
                            />
                            <div className="flex items-center gap-1">
                              <span className="text-gray-400 text-xs">Rp</span>
                              <input
                                type="number"
                                value={rule.price}
                                onChange={(e) => updateQuantityRule(index, 'price', e.target.value)}
                                className="flex-1 px-2 py-2 bg-[#0a0a0a] border border-[#333] rounded-lg text-white text-sm font-mono"
                              />
                            </div>
                            <button
                              type="button"
                              onClick={() => removeQuantityRule(index)}
                              className="p-2 hover:bg-red-600/20 rounded-lg text-red-400"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        ))}
                      </div>
                    )}

                    <div className="mt-4 p-3 bg-blue-900/20 border border-blue-800/30 rounded-lg">
                      <div className="text-xs text-blue-300 font-medium mb-1">Contoh:</div>
                      <div className="text-xs text-blue-200/70">
                        Qty 1-4 = Rp 20.000 | Qty 5-9 = Rp 18.000 | Qty 10+ = Rp 15.000
                      </div>
                    </div>
                  </div>
                )}

                {/* MODE: LEVEL */}
                {pricingMode === 'level' && (
                  <div className="p-4 bg-[#1a1a1a] rounded-xl border border-[#333]">
                    <div className="flex items-center gap-2 text-purple-400 mb-4">
                      <Users className="w-4 h-4" />
                      <span className="font-medium">Harga Berdasarkan Level Customer</span>
                    </div>
                    
                    <div className="space-y-3">
                      {CUSTOMER_LEVELS.map(level => (
                        <div key={level} className="flex items-center gap-3">
                          <div className="w-28 text-sm text-gray-300 capitalize">{level}</div>
                          <div className="flex items-center gap-1 flex-1">
                            <span className="text-gray-400 text-xs">Rp</span>
                            <input
                              type="number"
                              value={priceLevels[level] || ''}
                              onChange={(e) => setPriceLevels({
                                ...priceLevels,
                                [level]: parseFloat(e.target.value) || 0
                              })}
                              className="flex-1 px-3 py-2 bg-[#0a0a0a] border border-[#333] rounded-lg text-white font-mono text-sm"
                              placeholder={`Harga ${level}`}
                            />
                          </div>
                          {priceLevels[level] > 0 && priceLevels[level] < formData.selling_price && (
                            <span className="text-xs text-green-400 w-16 text-right">
                              -{Math.round(((formData.selling_price - priceLevels[level]) / formData.selling_price) * 100)}%
                            </span>
                          )}
                        </div>
                      ))}
                    </div>

                    <div className="mt-4 p-3 bg-purple-900/20 border border-purple-800/30 rounded-lg">
                      <div className="text-xs text-purple-300 font-medium mb-1">Info:</div>
                      <div className="text-xs text-purple-200/70">
                        Harga otomatis dipilih berdasarkan level customer saat transaksi
                      </div>
                    </div>
                  </div>
                )}

                {/* MODE: UNIT */}
                {pricingMode === 'unit' && (
                  <div className="p-4 bg-[#1a1a1a] rounded-xl border border-[#333]">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-2 text-amber-400">
                        <Layers className="w-4 h-4" />
                        <span className="font-medium">Harga Berdasarkan Satuan</span>
                      </div>
                      <button
                        type="button"
                        onClick={addUnitPrice}
                        className="px-3 py-1.5 bg-amber-600/20 text-amber-400 rounded-lg text-xs flex items-center gap-1 hover:bg-amber-600/30"
                      >
                        <Plus className="w-3 h-3" /> Tambah Satuan
                      </button>
                    </div>

                    {unitPrices.length === 0 ? (
                      <div className="text-center py-6 text-gray-500">
                        <Layers className="w-8 h-8 mx-auto mb-2 opacity-50" />
                        <p className="text-sm">Klik "Tambah Satuan" untuk menambahkan harga per satuan</p>
                      </div>
                    ) : (
                      <div className="space-y-2">
                        <div className="grid grid-cols-4 gap-2 text-xs text-gray-400 px-2">
                          <div>Satuan</div>
                          <div>Konversi (ke dasar)</div>
                          <div>Harga Jual</div>
                          <div></div>
                        </div>
                        {unitPrices.map((up, index) => (
                          <div key={index} className="grid grid-cols-4 gap-2 items-center">
                            <SearchableSelect
                              options={unitOptions}
                              value={up.unit_id}
                              onValueChange={(val) => updateUnitPrice(index, 'unit_id', val)}
                              placeholder="Pilih"
                              searchPlaceholder="Ketik satuan..."
                              data-testid={`unit-price-${index}`}
                              className="text-sm"
                            />
                            <input
                              type="number"
                              value={up.conversion}
                              onChange={(e) => updateUnitPrice(index, 'conversion', e.target.value)}
                              className="px-3 py-2 bg-[#0a0a0a] border border-[#333] rounded-lg text-white text-sm"
                              placeholder="1"
                              min="1"
                            />
                            <div className="flex items-center gap-1">
                              <span className="text-gray-400 text-xs">Rp</span>
                              <input
                                type="number"
                                value={up.price}
                                onChange={(e) => updateUnitPrice(index, 'price', e.target.value)}
                                className="flex-1 px-2 py-2 bg-[#0a0a0a] border border-[#333] rounded-lg text-white text-sm font-mono"
                              />
                            </div>
                            <button
                              type="button"
                              onClick={() => removeUnitPrice(index)}
                              className="p-2 hover:bg-red-600/20 rounded-lg text-red-400"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        ))}
                      </div>
                    )}

                    <div className="mt-4 p-3 bg-amber-900/20 border border-amber-800/30 rounded-lg">
                      <div className="text-xs text-amber-300 font-medium mb-1">Contoh:</div>
                      <div className="text-xs text-amber-200/70">
                        1 PCS = Rp 1.500 | 1 PACK (10 PCS) = Rp 14.000 | 1 DUS (50 PCS) = Rp 55.000
                      </div>
                    </div>
                  </div>
                )}

                {/* Allow Price Selection */}
                <div className="p-4 bg-[#1a1a1a] rounded-xl border border-[#333]">
                  <div className="flex items-start gap-3">
                    <input
                      type="checkbox"
                      id="allowPriceSelection"
                      checked={allowPriceSelection}
                      onChange={(e) => setAllowPriceSelection(e.target.checked)}
                      className="w-4 h-4 mt-1 rounded bg-[#0a0a0a] border-[#333]"
                    />
                    <div>
                      <label htmlFor="allowPriceSelection" className="text-sm font-medium text-white cursor-pointer">
                        Harga jual dipilih saat transaksi
                      </label>
                      <p className="text-xs text-gray-500 mt-1">
                        Jika diaktifkan, kasir bisa memilih level harga (dengan izin <code className="bg-[#333] px-1 rounded">override_price</code>)
                      </p>
                    </div>
                  </div>

                  <div className="mt-3 p-3 bg-red-900/20 border border-red-800/30 rounded-lg">
                    <div className="flex items-start gap-2">
                      <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
                      <div className="text-xs text-red-200/70">
                        <strong className="text-red-300">Keamanan:</strong> Kasir tanpa izin akan mendapat pesan error "ANDA TIDAK MEMILIKI IZIN MENGUBAH HARGA"
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* TAB 3: Stok & Gudang */}
            {activeTab === 'stock' && (
              <div className="space-y-4">
                <div className="p-3 bg-blue-900/20 border border-blue-800/30 rounded-lg flex items-start gap-2">
                  <Info className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
                  <p className="text-xs text-blue-300">
                    Pengaturan stok per cabang dilakukan melalui modul <strong>Stok Per Cabang</strong>. Di sini hanya pengaturan global.
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs text-gray-400 mb-1">Minimal Stok</label>
                    <input
                      type="number"
                      value={stockConfig.min_stock}
                      onChange={(e) => setStockConfig({ ...stockConfig, min_stock: parseInt(e.target.value) || 0 })}
                      className="w-full px-3 py-2 bg-[#0a0a0a] border border-[#333] rounded-lg text-white text-sm"
                      min="0"
                      placeholder="0"
                    />
                    <p className="text-[10px] text-gray-500 mt-1">Alert jika stok di bawah nilai ini</p>
                  </div>
                  <div>
                    <label className="block text-xs text-gray-400 mb-1">Maksimal Stok</label>
                    <input
                      type="number"
                      value={stockConfig.max_stock}
                      onChange={(e) => setStockConfig({ ...stockConfig, max_stock: parseInt(e.target.value) || 0 })}
                      className="w-full px-3 py-2 bg-[#0a0a0a] border border-[#333] rounded-lg text-white text-sm"
                      min="0"
                      placeholder="0"
                    />
                    <p className="text-[10px] text-gray-500 mt-1">Batas atas stok ideal</p>
                  </div>
                </div>

                <div>
                  <label className="block text-xs text-gray-400 mb-1">Rak Default</label>
                  <input
                    type="text"
                    value={stockConfig.default_rack}
                    onChange={(e) => setStockConfig({ ...stockConfig, default_rack: e.target.value })}
                    className="w-full px-3 py-2 bg-[#0a0a0a] border border-[#333] rounded-lg text-white text-sm"
                    placeholder="Contoh: A-01"
                  />
                </div>
              </div>
            )}

            {/* TAB 4: Akunting */}
            {activeTab === 'accounting' && (
              <div className="space-y-4">
                <div className="p-3 bg-yellow-900/20 border border-yellow-800/30 rounded-lg flex items-start gap-2">
                  <AlertCircle className="w-4 h-4 text-yellow-400 mt-0.5 flex-shrink-0" />
                  <p className="text-xs text-yellow-300">
                    Pengaturan akun ini opsional. Jika tidak diisi, sistem akan menggunakan akun default dari pengaturan perusahaan.
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs text-gray-400 mb-1">Akun Persediaan</label>
                    <input
                      type="text"
                      value={accountConfig.inventory_account}
                      onChange={(e) => setAccountConfig({ ...accountConfig, inventory_account: e.target.value })}
                      className="w-full px-3 py-2 bg-[#0a0a0a] border border-[#333] rounded-lg text-white text-sm"
                      placeholder="Pilih akun persediaan"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-400 mb-1">Akun Penjualan</label>
                    <input
                      type="text"
                      value={accountConfig.sales_account}
                      onChange={(e) => setAccountConfig({ ...accountConfig, sales_account: e.target.value })}
                      className="w-full px-3 py-2 bg-[#0a0a0a] border border-[#333] rounded-lg text-white text-sm"
                      placeholder="Pilih akun penjualan"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-400 mb-1">Akun HPP</label>
                    <input
                      type="text"
                      value={accountConfig.cogs_account}
                      onChange={(e) => setAccountConfig({ ...accountConfig, cogs_account: e.target.value })}
                      className="w-full px-3 py-2 bg-[#0a0a0a] border border-[#333] rounded-lg text-white text-sm"
                      placeholder="Pilih akun HPP"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-400 mb-1">Akun Retur</label>
                    <input
                      type="text"
                      value={accountConfig.return_account}
                      onChange={(e) => setAccountConfig({ ...accountConfig, return_account: e.target.value })}
                      className="w-full px-3 py-2 bg-[#0a0a0a] border border-[#333] rounded-lg text-white text-sm"
                      placeholder="Pilih akun retur"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-400 mb-1">Akun Diskon</label>
                    <input
                      type="text"
                      value={accountConfig.discount_account}
                      onChange={(e) => setAccountConfig({ ...accountConfig, discount_account: e.target.value })}
                      className="w-full px-3 py-2 bg-[#0a0a0a] border border-[#333] rounded-lg text-white text-sm"
                      placeholder="Pilih akun diskon"
                    />
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="p-4 border-t border-[#333] bg-[#0d0d0d] flex items-center justify-between">
            <div className="text-xs text-gray-500">
              <span className="text-red-400">*</span> Wajib diisi
            </div>
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
              >
                Batal
              </button>
              <button
                type="submit"
                disabled={saving}
                className="px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors flex items-center gap-2 disabled:opacity-50"
              >
                <Save className="w-4 h-4" />
                {saving ? 'Menyimpan...' : (editingItem ? 'Update Item' : 'Simpan Item')}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
