import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Package, AlertTriangle, ArrowRight, Search, Plus, Minus, RefreshCw, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

const Inventory = () => {
  const { api, user } = useAuth();
  const [activeTab, setActiveTab] = useState('stock');
  const [stock, setStock] = useState([]);
  const [lowStock, setLowStock] = useState([]);
  const [movements, setMovements] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showAdjustModal, setShowAdjustModal] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [adjustQty, setAdjustQty] = useState(0);
  const [adjustReason, setAdjustReason] = useState('');

  useEffect(() => {
    if (activeTab === 'stock') loadStock();
    else if (activeTab === 'low-stock') loadLowStock();
    else if (activeTab === 'movements') loadMovements();
  }, [activeTab, search]);

  const loadStock = async () => {
    setLoading(true);
    try {
      let url = `/api/inventory/stock?limit=200`;
      if (search) url += `&search=${encodeURIComponent(search)}`;
      const res = await api(url);
      if (res.ok) {
        const data = await res.json();
        setStock(data.items || []);
      }
    } catch (err) {
      toast.error('Failed to load stock');
    } finally {
      setLoading(false);
    }
  };

  const loadLowStock = async () => {
    setLoading(true);
    try {
      const res = await api('/api/inventory/stock/low');
      if (res.ok) setLowStock(await res.json());
    } catch (err) {
      toast.error('Failed to load low stock');
    } finally {
      setLoading(false);
    }
  };

  const loadMovements = async () => {
    setLoading(true);
    try {
      const res = await api('/api/inventory/movements?limit=100');
      if (res.ok) {
        const data = await res.json();
        setMovements(data.items || []);
      }
    } catch (err) {
      toast.error('Failed to load movements');
    } finally {
      setLoading(false);
    }
  };

  const handleAdjust = async () => {
    if (!selectedProduct || adjustQty === 0) return;
    
    try {
      const res = await api('/api/inventory/adjust', {
        method: 'POST',
        body: JSON.stringify({
          product_id: selectedProduct.product_id,
          quantity: adjustQty,
          reason: adjustReason
        })
      });
      
      if (res.ok) {
        toast.success('Stock adjusted');
        setShowAdjustModal(false);
        setSelectedProduct(null);
        setAdjustQty(0);
        setAdjustReason('');
        loadStock();
      } else {
        const error = await res.json();
        toast.error(error.detail || 'Adjustment failed');
      }
    } catch (err) {
      toast.error('Adjustment failed');
    }
  };

  const openAdjustModal = (item) => {
    setSelectedProduct(item);
    setAdjustQty(0);
    setAdjustReason('');
    setShowAdjustModal(true);
  };

  const tabs = [
    { id: 'stock', label: 'Stock Overview', icon: Package },
    { id: 'low-stock', label: 'Low Stock Alerts', icon: AlertTriangle },
    { id: 'movements', label: 'Stock Movements', icon: ArrowRight }
  ];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Inventory</h1>
          <p className="text-gray-400">Manage stock across branches</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-red-900/30 pb-2">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-colors ${
              activeTab === tab.id
                ? 'bg-red-900/30 text-amber-400'
                : 'text-gray-400 hover:text-white hover:bg-red-900/20'
            }`}
          >
            <tab.icon className="h-4 w-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Stock Overview */}
      {activeTab === 'stock' && (
        <>
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search products..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-[#1a1214] border border-red-900/30 rounded-lg"
            />
          </div>

          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
            <table className="w-full">
              <thead className="bg-red-900/20">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-semibold">Product</th>
                  <th className="px-4 py-3 text-right text-sm font-semibold">Quantity</th>
                  <th className="px-4 py-3 text-right text-sm font-semibold">Min Stock</th>
                  <th className="px-4 py-3 text-right text-sm font-semibold">Stock Value</th>
                  <th className="px-4 py-3 text-center text-sm font-semibold">Status</th>
                  <th className="px-4 py-3 text-center text-sm font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center">
                      <Loader2 className="h-8 w-8 animate-spin mx-auto text-red-400" />
                    </td>
                  </tr>
                ) : stock.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center text-gray-400">No stock data</td>
                  </tr>
                ) : (
                  stock.map((item, idx) => (
                    <tr key={idx} className="border-t border-red-900/10 hover:bg-red-900/10">
                      <td className="px-4 py-3">
                        <div className="font-medium">{item.product_name}</div>
                        <div className="text-sm text-gray-400">{item.product_code}</div>
                      </td>
                      <td className="px-4 py-3 text-right font-semibold">{item.quantity}</td>
                      <td className="px-4 py-3 text-right text-gray-400">{item.min_stock}</td>
                      <td className="px-4 py-3 text-right text-amber-400">
                        Rp {((item.cost_price || 0) * item.quantity).toLocaleString()}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                          item.is_low_stock
                            ? 'bg-red-900/30 text-red-400'
                            : 'bg-green-900/30 text-green-400'
                        }`}>
                          {item.is_low_stock ? 'Low Stock' : 'OK'}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex justify-center gap-1">
                          <button
                            onClick={() => openAdjustModal(item)}
                            className="p-2 text-blue-400 hover:bg-blue-900/20 rounded"
                            title="Adjust Stock"
                          >
                            <RefreshCw className="h-4 w-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </>
      )}

      {/* Low Stock Alerts */}
      {activeTab === 'low-stock' && (
        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
          <table className="w-full">
            <thead className="bg-red-900/20">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-semibold">Product</th>
                <th className="px-4 py-3 text-left text-sm font-semibold">Branch</th>
                <th className="px-4 py-3 text-right text-sm font-semibold">Current</th>
                <th className="px-4 py-3 text-right text-sm font-semibold">Minimum</th>
                <th className="px-4 py-3 text-right text-sm font-semibold">Shortage</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center">
                    <Loader2 className="h-8 w-8 animate-spin mx-auto text-red-400" />
                  </td>
                </tr>
              ) : lowStock.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-gray-400">
                    <AlertTriangle className="h-12 w-12 mx-auto mb-2 opacity-30" />
                    All stock levels are OK
                  </td>
                </tr>
              ) : (
                lowStock.map((item, idx) => (
                  <tr key={idx} className="border-t border-red-900/10 hover:bg-red-900/10">
                    <td className="px-4 py-3">
                      <div className="font-medium">{item.product_name}</div>
                      <div className="text-sm text-gray-400">{item.product_code}</div>
                    </td>
                    <td className="px-4 py-3 text-gray-400">{item.branch_name}</td>
                    <td className="px-4 py-3 text-right text-red-400 font-bold">{item.quantity}</td>
                    <td className="px-4 py-3 text-right text-gray-400">{item.min_stock}</td>
                    <td className="px-4 py-3 text-right text-amber-400 font-semibold">{item.shortage}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Stock Movements */}
      {activeTab === 'movements' && (
        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
          <table className="w-full">
            <thead className="bg-red-900/20">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-semibold">Date</th>
                <th className="px-4 py-3 text-left text-sm font-semibold">Product</th>
                <th className="px-4 py-3 text-left text-sm font-semibold">Type</th>
                <th className="px-4 py-3 text-right text-sm font-semibold">Quantity</th>
                <th className="px-4 py-3 text-left text-sm font-semibold">Notes</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center">
                    <Loader2 className="h-8 w-8 animate-spin mx-auto text-red-400" />
                  </td>
                </tr>
              ) : movements.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-gray-400">No movements yet</td>
                </tr>
              ) : (
                movements.map((item, idx) => (
                  <tr key={idx} className="border-t border-red-900/10 hover:bg-red-900/10">
                    <td className="px-4 py-3 text-gray-400">
                      {new Date(item.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3">
                      <div className="font-medium">{item.product_name}</div>
                      <div className="text-sm text-gray-400">{item.product_code}</div>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded text-xs font-semibold capitalize ${
                        item.movement_type === 'sale' ? 'bg-blue-900/30 text-blue-400' :
                        item.movement_type === 'stock_in' ? 'bg-green-900/30 text-green-400' :
                        item.movement_type === 'adjustment' ? 'bg-amber-900/30 text-amber-400' :
                        'bg-purple-900/30 text-purple-400'
                      }`}>
                        {item.movement_type?.replace('_', ' ')}
                      </span>
                    </td>
                    <td className={`px-4 py-3 text-right font-bold ${
                      item.quantity > 0 ? 'text-green-400' : 'text-red-400'
                    }`}>
                      {item.quantity > 0 ? '+' : ''}{item.quantity}
                    </td>
                    <td className="px-4 py-3 text-gray-400 text-sm">{item.notes || '-'}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Adjust Modal */}
      {showAdjustModal && selectedProduct && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-md p-6">
            <h2 className="text-xl font-bold mb-4">Adjust Stock</h2>
            <p className="text-gray-400 mb-4">{selectedProduct.product_name}</p>
            
            <div className="mb-4">
              <label className="block text-sm text-gray-400 mb-1">Current Stock</label>
              <div className="text-2xl font-bold">{selectedProduct.quantity}</div>
            </div>

            <div className="mb-4">
              <label className="block text-sm text-gray-400 mb-1">Adjustment (+/-)</label>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setAdjustQty(adjustQty - 1)}
                  className="p-2 bg-red-900/30 rounded hover:bg-red-900/50"
                >
                  <Minus className="h-5 w-5" />
                </button>
                <input
                  type="number"
                  value={adjustQty}
                  onChange={(e) => setAdjustQty(Number(e.target.value))}
                  className="flex-1 px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-center text-xl font-bold"
                />
                <button
                  onClick={() => setAdjustQty(adjustQty + 1)}
                  className="p-2 bg-green-900/30 rounded hover:bg-green-900/50"
                >
                  <Plus className="h-5 w-5" />
                </button>
              </div>
              <div className="text-center mt-2 text-gray-400">
                New Stock: <span className="font-bold text-amber-400">{selectedProduct.quantity + adjustQty}</span>
              </div>
            </div>

            <div className="mb-6">
              <label className="block text-sm text-gray-400 mb-1">Reason</label>
              <input
                type="text"
                value={adjustReason}
                onChange={(e) => setAdjustReason(e.target.value)}
                className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg"
                placeholder="e.g., Damaged goods, Recount"
              />
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => setShowAdjustModal(false)}
                className="flex-1 py-2 border border-red-900/30 rounded-lg hover:bg-red-900/20"
              >
                Cancel
              </button>
              <button
                onClick={handleAdjust}
                disabled={adjustQty === 0}
                className="flex-1 py-2 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg disabled:opacity-50"
              >
                Confirm Adjustment
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Inventory;
