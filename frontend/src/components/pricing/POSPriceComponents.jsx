import React, { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { 
  DollarSign, Tag, Users, Package, Layers, ShoppingCart,
  ChevronDown, Check, AlertTriangle, Lock
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Format currency
const formatCurrency = (value) => {
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    minimumFractionDigits: 0
  }).format(value);
};

// Price mode icons
const MODE_ICONS = {
  single: DollarSign,
  quantity: Package,
  level: Users,
  unit: Layers
};

/**
 * POS Product Price Display
 * Shows product with its calculated price based on pricing mode
 */
export function POSProductPrice({ 
  product, 
  quantity = 1, 
  customerLevel = 'retail',
  selectedUnit = null,
  token,
  onPriceCalculated 
}) {
  const [priceData, setPriceData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (product?.id) {
      calculatePrice();
    }
  }, [product?.id, quantity, customerLevel, selectedUnit]);

  const calculatePrice = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/pricing/calculate`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          product_id: product.id,
          quantity,
          customer_level: customerLevel,
          unit_id: selectedUnit || ''
        })
      });

      if (res.ok) {
        const data = await res.json();
        setPriceData(data);
        onPriceCalculated && onPriceCalculated(data);
      }
    } catch (err) {
      console.error('Price calculation error:', err);
    } finally {
      setLoading(false);
    }
  };

  if (!priceData) return null;

  const ModeIcon = MODE_ICONS[priceData.mode] || DollarSign;
  const hasDiscount = priceData.discount > 0;

  return (
    <div className="bg-[#1a1a1a] rounded-lg p-3 border border-[#333]">
      <div className="flex items-start justify-between">
        <div>
          <div className="text-sm text-gray-400 flex items-center gap-1">
            <ModeIcon className="w-3 h-3" />
            {priceData.rule_applied}
          </div>
          <div className="text-xl font-bold text-white mt-1">
            {formatCurrency(priceData.price)}
          </div>
          {hasDiscount && (
            <div className="flex items-center gap-2 mt-1">
              <span className="text-xs text-gray-500 line-through">
                {formatCurrency(priceData.original_price)}
              </span>
              <span className="text-xs px-1.5 py-0.5 bg-green-600/20 text-green-400 rounded">
                -{priceData.discount_percent}%
              </span>
            </div>
          )}
        </div>
        
        {/* Quantity tiers preview */}
        {priceData.quantity_tiers && priceData.quantity_tiers.length > 0 && (
          <div className="text-right">
            <div className="text-xs text-gray-500">Harga Qty:</div>
            {priceData.quantity_tiers.slice(0, 3).map((tier, i) => (
              <div key={i} className="text-xs text-gray-400">
                {tier.max_qty ? `${tier.min_qty}-${tier.max_qty}` : `${tier.min_qty}+`}: {formatCurrency(tier.price)}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}


/**
 * POS Price Level Selector
 * Allows cashier to select price level (with permission check)
 */
export function POSPriceLevelSelector({
  product,
  currentLevel = 'retail',
  onLevelChange,
  token,
  hasOverridePermission = false
}) {
  const [priceData, setPriceData] = useState(null);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (product?.id) {
      loadPricing();
    }
  }, [product?.id]);

  const loadPricing = async () => {
    try {
      const res = await fetch(`${API_URL}/api/pricing/product/${product.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setPriceData(data.pricing);
      }
    } catch (err) {
      console.error('Failed to load pricing:', err);
    }
  };

  const handleSelectLevel = async (level) => {
    if (level !== currentLevel && !hasOverridePermission) {
      toast.error('ANDA TIDAK MEMILIKI IZIN MENGUBAH HARGA');
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/pricing/pos/select-price`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          product_id: product.id,
          selected_level: level
        })
      });

      if (res.ok) {
        const data = await res.json();
        onLevelChange && onLevelChange(level, data.price);
        setIsOpen(false);
        toast.success(`Harga ${level} dipilih: ${formatCurrency(data.price)}`);
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Gagal memilih harga');
      }
    } catch (err) {
      toast.error('Gagal memilih harga');
    } finally {
      setLoading(false);
    }
  };

  if (!priceData || !priceData.allow_price_selection) {
    return null;
  }

  const priceLevels = priceData.price_levels || {};
  const availableLevels = Object.entries(priceLevels)
    .filter(([_, price]) => price > 0)
    .map(([level, price]) => ({ level, price }));

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`flex items-center gap-2 px-3 py-2 rounded-lg border text-sm ${
          hasOverridePermission 
            ? 'border-purple-500/50 bg-purple-900/20 text-purple-300 hover:bg-purple-900/30'
            : 'border-[#333] bg-[#1a1a1a] text-gray-400'
        }`}
      >
        <Tag className="w-4 h-4" />
        <span className="capitalize">{currentLevel}</span>
        <ChevronDown className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
        {!hasOverridePermission && <Lock className="w-3 h-3 text-gray-500" />}
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 mt-1 w-56 bg-[#1a1a1a] border border-[#333] rounded-lg shadow-xl z-50 overflow-hidden">
          <div className="p-2 border-b border-[#333] bg-[#111]">
            <div className="text-xs text-gray-400">Pilih Level Harga</div>
            {!hasOverridePermission && (
              <div className="text-xs text-amber-400 flex items-center gap-1 mt-1">
                <AlertTriangle className="w-3 h-3" />
                Butuh izin override_price
              </div>
            )}
          </div>
          <div className="max-h-48 overflow-y-auto">
            {availableLevels.map(({ level, price }) => (
              <button
                key={level}
                onClick={() => handleSelectLevel(level)}
                disabled={loading || (!hasOverridePermission && level !== currentLevel)}
                className={`w-full px-3 py-2 flex items-center justify-between hover:bg-[#222] transition-colors ${
                  level === currentLevel ? 'bg-green-900/20' : ''
                } ${!hasOverridePermission && level !== currentLevel ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                <span className="capitalize text-white">{level}</span>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-green-400 font-mono">
                    {formatCurrency(price)}
                  </span>
                  {level === currentLevel && (
                    <Check className="w-4 h-4 text-green-400" />
                  )}
                </div>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}


/**
 * POS Unit Selector
 * Allows selection of different units with different prices
 */
export function POSUnitSelector({
  product,
  currentUnit = null,
  onUnitChange,
  token
}) {
  const [priceData, setPriceData] = useState(null);
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    if (product?.id) {
      loadPricing();
    }
  }, [product?.id]);

  const loadPricing = async () => {
    try {
      const res = await fetch(`${API_URL}/api/pricing/product/${product.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setPriceData(data.pricing);
      }
    } catch (err) {
      console.error('Failed to load pricing:', err);
    }
  };

  if (!priceData || priceData.pricing_mode !== 'unit') {
    return null;
  }

  const unitPrices = priceData.unit_prices || [];
  const currentUnitData = currentUnit 
    ? unitPrices.find(u => u.unit_id === currentUnit)
    : unitPrices[0];

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-2 rounded-lg border border-amber-500/50 bg-amber-900/20 text-amber-300 hover:bg-amber-900/30 text-sm"
      >
        <Layers className="w-4 h-4" />
        <span>{currentUnitData?.unit_name || 'Pilih Satuan'}</span>
        <ChevronDown className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 mt-1 w-64 bg-[#1a1a1a] border border-[#333] rounded-lg shadow-xl z-50 overflow-hidden">
          <div className="p-2 border-b border-[#333] bg-[#111]">
            <div className="text-xs text-gray-400">Pilih Satuan</div>
          </div>
          <div className="max-h-48 overflow-y-auto">
            {unitPrices.map((unit) => (
              <button
                key={unit.unit_id}
                onClick={() => {
                  onUnitChange && onUnitChange(unit.unit_id, unit);
                  setIsOpen(false);
                }}
                className={`w-full px-3 py-2 flex items-center justify-between hover:bg-[#222] transition-colors ${
                  unit.unit_id === currentUnit ? 'bg-amber-900/20' : ''
                }`}
              >
                <div>
                  <span className="text-white">{unit.unit_name}</span>
                  {unit.conversion > 1 && (
                    <span className="text-xs text-gray-500 ml-2">
                      ({unit.conversion} pcs)
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-amber-400 font-mono">
                    {formatCurrency(unit.price)}
                  </span>
                  {unit.unit_id === currentUnit && (
                    <Check className="w-4 h-4 text-amber-400" />
                  )}
                </div>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}


/**
 * Complete POS Price Card
 * Shows all pricing information for a product in POS
 */
export function POSPriceCard({
  product,
  quantity = 1,
  customerLevel = 'retail',
  selectedUnit = null,
  token,
  hasOverridePermission = false,
  onPriceChange,
  onUnitChange,
  onLevelChange
}) {
  const [priceData, setPriceData] = useState(null);

  return (
    <div className="bg-[#111] border border-[#333] rounded-xl p-4 space-y-3">
      {/* Product Info */}
      <div className="flex items-center justify-between">
        <div>
          <div className="text-white font-medium">{product?.name}</div>
          <div className="text-xs text-gray-500">{product?.code}</div>
        </div>
        <div className="text-xs px-2 py-1 bg-[#1a1a1a] rounded text-gray-400">
          {product?.pricing_mode || 'single'}
        </div>
      </div>

      {/* Price Display */}
      <POSProductPrice
        product={product}
        quantity={quantity}
        customerLevel={customerLevel}
        selectedUnit={selectedUnit}
        token={token}
        onPriceCalculated={(data) => {
          setPriceData(data);
          onPriceChange && onPriceChange(data.price);
        }}
      />

      {/* Selectors */}
      <div className="flex items-center gap-2 flex-wrap">
        <POSPriceLevelSelector
          product={product}
          currentLevel={customerLevel}
          onLevelChange={onLevelChange}
          token={token}
          hasOverridePermission={hasOverridePermission}
        />
        <POSUnitSelector
          product={product}
          currentUnit={selectedUnit}
          onUnitChange={onUnitChange}
          token={token}
        />
      </div>

      {/* Promo indicator (if any) */}
      {product?.promo && (
        <div className="flex items-center gap-2 p-2 bg-red-900/20 border border-red-800/30 rounded-lg">
          <ShoppingCart className="w-4 h-4 text-red-400" />
          <span className="text-xs text-red-300">{product.promo}</span>
        </div>
      )}
    </div>
  );
}

export default POSPriceCard;
