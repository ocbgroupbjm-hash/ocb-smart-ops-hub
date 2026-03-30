import React, { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { 
  DollarSign, Package, Users, Layers, Plus, Trash2, Save, X,
  Tag, Percent, ShoppingCart, Check, AlertCircle
} from 'lucide-react';

import { getApiUrl } from '../../utils/apiConfig';
const API_URL = getApiUrl();

// Pricing modes configuration
const PRICING_MODES = [
  { 
    code: 'single', 
    name: 'Satu Harga', 
    icon: DollarSign,
    description: 'Produk hanya memiliki satu harga jual tetap',
    color: 'text-green-400'
  },
  { 
    code: 'quantity', 
    name: 'Berdasarkan Jumlah', 
    icon: Package,
    description: 'Harga berubah berdasarkan jumlah pembelian',
    color: 'text-blue-400'
  },
  { 
    code: 'level', 
    name: 'Level Harga', 
    icon: Users,
    description: 'Harga berbeda berdasarkan tipe customer',
    color: 'text-purple-400'
  },
  { 
    code: 'unit', 
    name: 'Berdasarkan Satuan', 
    icon: Layers,
    description: 'Harga berbeda berdasarkan satuan (PCS, PACK, DUS)',
    color: 'text-amber-400'
  }
];

export default function PricingConfigModal({ 
  isOpen, 
  onClose, 
  product, 
  token, 
  units = [],
  onSave 
}) {
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [pricingMode, setPricingMode] = useState('single');
  const [sellingPrice, setSellingPrice] = useState(0);
  const [quantityPrices, setQuantityPrices] = useState([]);
  const [priceLevels, setPriceLevels] = useState({
    retail: 0,
    member: 0,
    reseller: 0,
    distributor: 0,
    grosir: 0
  });
  const [unitPrices, setUnitPrices] = useState([]);
  const [allowPriceSelection, setAllowPriceSelection] = useState(false);
  const [defaultLevel, setDefaultLevel] = useState('retail');
  const [customerLevels, setCustomerLevels] = useState([]);

  // Load pricing config when modal opens
  useEffect(() => {
    if (isOpen && product?.id) {
      loadPricingConfig();
      loadCustomerLevels();
    }
  }, [isOpen, product?.id]);

  const loadPricingConfig = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/pricing/product/${product.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        const pricing = data.pricing;
        
        setPricingMode(pricing.pricing_mode || 'single');
        setSellingPrice(pricing.selling_price || product.selling_price || 0);
        setQuantityPrices(pricing.quantity_prices || []);
        setPriceLevels(pricing.price_levels || {
          retail: 0, member: 0, reseller: 0, distributor: 0, grosir: 0
        });
        setUnitPrices(pricing.unit_prices || []);
        setAllowPriceSelection(pricing.allow_price_selection || false);
        setDefaultLevel(pricing.default_level || 'retail');
      }
    } catch (err) {
      console.error('Failed to load pricing config', err);
    } finally {
      setLoading(false);
    }
  };

  const loadCustomerLevels = async () => {
    try {
      const res = await fetch(`${API_URL}/api/pricing/customer-levels`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setCustomerLevels(data.levels || []);
      }
    } catch (err) {
      console.error('Failed to load customer levels', err);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const payload = {
        pricing_mode: pricingMode,
        selling_price: sellingPrice,
        quantity_prices: quantityPrices,
        price_levels: priceLevels,
        unit_prices: unitPrices,
        allow_price_selection: allowPriceSelection,
        default_level: defaultLevel
      };

      const res = await fetch(`${API_URL}/api/pricing/product/${product.id}`, {
        method: 'PUT',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        toast.success('Konfigurasi harga berhasil disimpan');
        onSave && onSave();
        onClose();
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Gagal menyimpan konfigurasi');
      }
    } catch (err) {
      toast.error('Gagal menyimpan konfigurasi harga');
    } finally {
      setSaving(false);
    }
  };

  // Quantity price handlers
  const addQuantityRule = () => {
    setQuantityPrices([
      ...quantityPrices,
      { min_qty: 1, max_qty: null, price: sellingPrice }
    ]);
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
    setUnitPrices([
      ...unitPrices,
      { unit_id: '', unit_name: '', conversion: 1, price: sellingPrice }
    ]);
  };

  const updateUnitPrice = (index, field, value) => {
    const updated = [...unitPrices];
    if (field === 'unit_id') {
      const selectedUnit = units.find(u => u.id === value);
      updated[index].unit_id = value;
      updated[index].unit_name = selectedUnit?.name || '';
    } else if (field === 'price' || field === 'conversion') {
      updated[index][field] = parseFloat(value) || 0;
    } else {
      updated[index][field] = value;
    }
    setUnitPrices(updated);
  };

  const removeUnitPrice = (index) => {
    setUnitPrices(unitPrices.filter((_, i) => i !== index));
  };

  if (!isOpen) return null;

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('id-ID').format(value);
  };

  return (
    <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
      <div className="bg-[#111] border border-[#333] rounded-xl w-full max-w-4xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="p-4 border-b border-[#333] bg-[#0d0d0d] flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <DollarSign className="w-5 h-5 text-green-400" />
              Konfigurasi Harga Jual
            </h2>
            <p className="text-sm text-gray-400">{product?.code} - {product?.name}</p>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-[#222] rounded-lg">
            <X className="w-5 h-5 text-gray-400" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 overflow-y-auto max-h-[calc(90vh-140px)]">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-500"></div>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Pricing Mode Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-3">
                  Pilih Mode Harga
                </label>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {PRICING_MODES.map(mode => {
                    const Icon = mode.icon;
                    const isSelected = pricingMode === mode.code;
                    return (
                      <button
                        key={mode.code}
                        onClick={() => setPricingMode(mode.code)}
                        className={`p-4 rounded-xl border-2 transition-all text-left ${
                          isSelected
                            ? 'border-green-500 bg-green-500/10'
                            : 'border-[#333] bg-[#1a1a1a] hover:border-[#444]'
                        }`}
                      >
                        <div className="flex items-center gap-2 mb-2">
                          <Icon className={`w-5 h-5 ${isSelected ? 'text-green-400' : mode.color}`} />
                          {isSelected && <Check className="w-4 h-4 text-green-400 ml-auto" />}
                        </div>
                        <div className="text-sm font-medium text-white">{mode.name}</div>
                        <div className="text-xs text-gray-500 mt-1">{mode.description}</div>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Base Price */}
              <div className="bg-[#1a1a1a] p-4 rounded-xl border border-[#333]">
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Harga Jual Dasar
                </label>
                <div className="flex items-center gap-2">
                  <span className="text-gray-400">Rp</span>
                  <input
                    type="number"
                    value={sellingPrice}
                    onChange={e => setSellingPrice(parseFloat(e.target.value) || 0)}
                    className="flex-1 px-3 py-2 bg-[#0d0d0d] border border-[#333] rounded-lg text-white text-lg font-mono"
                  />
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  Harga ini digunakan sebagai harga default jika tidak ada rule yang cocok
                </p>
              </div>

              {/* MODE: QUANTITY PRICING */}
              {pricingMode === 'quantity' && (
                <div className="bg-[#1a1a1a] p-4 rounded-xl border border-[#333]">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h3 className="text-white font-medium flex items-center gap-2">
                        <Package className="w-4 h-4 text-blue-400" />
                        Harga Berdasarkan Jumlah
                      </h3>
                      <p className="text-xs text-gray-500">Tentukan harga berbeda untuk jumlah pembelian tertentu</p>
                    </div>
                    <button
                      onClick={addQuantityRule}
                      className="px-3 py-1.5 bg-blue-600/20 text-blue-400 rounded-lg text-sm flex items-center gap-1 hover:bg-blue-600/30"
                    >
                      <Plus className="w-4 h-4" /> Tambah Rule
                    </button>
                  </div>

                  {quantityPrices.length === 0 ? (
                    <div className="text-center py-6 text-gray-500">
                      <Package className="w-8 h-8 mx-auto mb-2 opacity-50" />
                      <p>Belum ada rule quantity pricing</p>
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
                            onChange={e => updateQuantityRule(index, 'min_qty', e.target.value)}
                            className="px-3 py-2 bg-[#0d0d0d] border border-[#333] rounded-lg text-white text-sm"
                            placeholder="Min"
                          />
                          <input
                            type="number"
                            value={rule.max_qty || ''}
                            onChange={e => updateQuantityRule(index, 'max_qty', e.target.value)}
                            className="px-3 py-2 bg-[#0d0d0d] border border-[#333] rounded-lg text-white text-sm"
                            placeholder="Unlimited"
                          />
                          <div className="flex items-center gap-1">
                            <span className="text-gray-400 text-xs">Rp</span>
                            <input
                              type="number"
                              value={rule.price}
                              onChange={e => updateQuantityRule(index, 'price', e.target.value)}
                              className="flex-1 px-3 py-2 bg-[#0d0d0d] border border-[#333] rounded-lg text-white text-sm font-mono"
                            />
                          </div>
                          <button
                            onClick={() => removeQuantityRule(index)}
                            className="p-2 hover:bg-red-600/20 rounded-lg text-red-400"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Example */}
                  <div className="mt-4 p-3 bg-blue-900/20 border border-blue-800/30 rounded-lg">
                    <div className="text-xs text-blue-300 font-medium mb-1">Contoh:</div>
                    <div className="text-xs text-blue-200/70">
                      Qty 1-4 = Rp 10.000 | Qty 5-9 = Rp 9.000 | Qty 10+ = Rp 8.000
                    </div>
                  </div>
                </div>
              )}

              {/* MODE: LEVEL PRICING */}
              {pricingMode === 'level' && (
                <div className="bg-[#1a1a1a] p-4 rounded-xl border border-[#333]">
                  <h3 className="text-white font-medium flex items-center gap-2 mb-4">
                    <Users className="w-4 h-4 text-purple-400" />
                    Harga Berdasarkan Level Customer
                  </h3>
                  
                  <div className="space-y-3">
                    {['retail', 'member', 'reseller', 'distributor', 'grosir'].map(level => (
                      <div key={level} className="flex items-center gap-3">
                        <div className="w-28 text-sm text-gray-300 capitalize">{level}</div>
                        <div className="flex items-center gap-1 flex-1">
                          <span className="text-gray-400 text-xs">Rp</span>
                          <input
                            type="number"
                            value={priceLevels[level] || ''}
                            onChange={e => setPriceLevels({
                              ...priceLevels,
                              [level]: parseFloat(e.target.value) || 0
                            })}
                            className="flex-1 px-3 py-2 bg-[#0d0d0d] border border-[#333] rounded-lg text-white font-mono"
                            placeholder={`Harga ${level}`}
                          />
                        </div>
                        {priceLevels[level] > 0 && priceLevels[level] < sellingPrice && (
                          <span className="text-xs text-green-400">
                            -{Math.round(((sellingPrice - priceLevels[level]) / sellingPrice) * 100)}%
                          </span>
                        )}
                      </div>
                    ))}
                  </div>

                  <div className="mt-4 p-3 bg-purple-900/20 border border-purple-800/30 rounded-lg">
                    <div className="text-xs text-purple-300 font-medium mb-1">Info:</div>
                    <div className="text-xs text-purple-200/70">
                      Harga akan otomatis dipilih berdasarkan level customer saat transaksi
                    </div>
                  </div>
                </div>
              )}

              {/* MODE: UNIT PRICING */}
              {pricingMode === 'unit' && (
                <div className="bg-[#1a1a1a] p-4 rounded-xl border border-[#333]">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h3 className="text-white font-medium flex items-center gap-2">
                        <Layers className="w-4 h-4 text-amber-400" />
                        Harga Berdasarkan Satuan
                      </h3>
                      <p className="text-xs text-gray-500">Tentukan harga berbeda untuk setiap satuan</p>
                    </div>
                    <button
                      onClick={addUnitPrice}
                      className="px-3 py-1.5 bg-amber-600/20 text-amber-400 rounded-lg text-sm flex items-center gap-1 hover:bg-amber-600/30"
                    >
                      <Plus className="w-4 h-4" /> Tambah Satuan
                    </button>
                  </div>

                  {unitPrices.length === 0 ? (
                    <div className="text-center py-6 text-gray-500">
                      <Layers className="w-8 h-8 mx-auto mb-2 opacity-50" />
                      <p>Belum ada unit pricing</p>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <div className="grid grid-cols-4 gap-2 text-xs text-gray-400 px-2">
                        <div>Satuan</div>
                        <div>Konversi</div>
                        <div>Harga</div>
                        <div></div>
                      </div>
                      {unitPrices.map((up, index) => (
                        <div key={index} className="grid grid-cols-4 gap-2 items-center">
                          <select
                            value={up.unit_id}
                            onChange={e => updateUnitPrice(index, 'unit_id', e.target.value)}
                            className="px-3 py-2 bg-[#0d0d0d] border border-[#333] rounded-lg text-white text-sm"
                          >
                            <option value="">Pilih Satuan</option>
                            {units.map(u => (
                              <option key={u.id} value={u.id}>{u.name}</option>
                            ))}
                          </select>
                          <input
                            type="number"
                            value={up.conversion}
                            onChange={e => updateUnitPrice(index, 'conversion', e.target.value)}
                            className="px-3 py-2 bg-[#0d0d0d] border border-[#333] rounded-lg text-white text-sm"
                            placeholder="1"
                          />
                          <div className="flex items-center gap-1">
                            <span className="text-gray-400 text-xs">Rp</span>
                            <input
                              type="number"
                              value={up.price}
                              onChange={e => updateUnitPrice(index, 'price', e.target.value)}
                              className="flex-1 px-3 py-2 bg-[#0d0d0d] border border-[#333] rounded-lg text-white text-sm font-mono"
                            />
                          </div>
                          <button
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

              {/* Flexible Price Option */}
              <div className="bg-[#1a1a1a] p-4 rounded-xl border border-[#333]">
                <div className="flex items-start gap-3">
                  <input
                    type="checkbox"
                    id="allowPriceSelection"
                    checked={allowPriceSelection}
                    onChange={e => setAllowPriceSelection(e.target.checked)}
                    className="w-4 h-4 mt-1 rounded bg-[#0d0d0d] border-[#333]"
                  />
                  <div>
                    <label htmlFor="allowPriceSelection" className="text-sm font-medium text-white cursor-pointer">
                      Harga jual dipilih saat transaksi
                    </label>
                    <p className="text-xs text-gray-500 mt-1">
                      Jika diaktifkan, kasir bisa memilih level harga (dengan izin override_price)
                    </p>
                  </div>
                </div>

                {allowPriceSelection && (
                  <div className="mt-4 pl-7">
                    <label className="block text-xs text-gray-400 mb-2">Default Level Harga</label>
                    <select
                      value={defaultLevel}
                      onChange={e => setDefaultLevel(e.target.value)}
                      className="w-full px-3 py-2 bg-[#0d0d0d] border border-[#333] rounded-lg text-white text-sm"
                    >
                      <option value="retail">Retail</option>
                      <option value="member">Member</option>
                      <option value="reseller">Reseller</option>
                      <option value="distributor">Distributor</option>
                      <option value="grosir">Grosir</option>
                    </select>
                  </div>
                )}

                <div className="mt-4 p-3 bg-red-900/20 border border-red-800/30 rounded-lg">
                  <div className="flex items-start gap-2">
                    <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
                    <div className="text-xs text-red-200/70">
                      <strong className="text-red-300">Keamanan:</strong> Hanya user dengan permission{' '}
                      <code className="bg-red-800/30 px-1 rounded">override_price</code>{' '}
                      yang dapat mengubah harga saat transaksi
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-[#333] bg-[#0d0d0d] flex items-center justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
          >
            Batal
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center gap-2 disabled:opacity-50"
          >
            <Save className="w-4 h-4" />
            {saving ? 'Menyimpan...' : 'Simpan Konfigurasi'}
          </button>
        </div>
      </div>
    </div>
  );
}
