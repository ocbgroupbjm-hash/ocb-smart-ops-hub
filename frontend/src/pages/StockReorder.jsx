import React, { useState, useEffect, useCallback } from 'react';
import { 
  Package, AlertTriangle, TrendingUp, ShoppingCart, BarChart3,
  RefreshCw, Filter, Search, ChevronRight, Settings, FileText,
  ArrowDown, ArrowUp, Clock, Truck, AlertCircle, CheckCircle2
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { SearchableEnumSelect, URGENCY_OPTIONS } from '../components/ui/searchable-enum-select';
import { useToast } from '../hooks/use-toast';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Urgency options for reorder
const reorderUrgencyOptions = [
  { value: 'critical', label: 'Kritis', color: 'red' },
  { value: 'high', label: 'Tinggi', color: 'orange' },
  { value: 'medium', label: 'Sedang', color: 'yellow' },
  { value: 'low', label: 'Rendah', color: 'blue' },
];

// Urgency Badge
const UrgencyBadge = ({ urgency }) => {
  const styles = {
    critical: 'bg-red-500/20 text-red-300 border-red-500/30',
    high: 'bg-orange-500/20 text-orange-300 border-orange-500/30',
    medium: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
    low: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
    none: 'bg-green-500/20 text-green-300 border-green-500/30'
  };
  
  const labels = {
    critical: 'Kritis',
    high: 'Tinggi',
    medium: 'Sedang',
    low: 'Rendah',
    none: 'Aman'
  };
  
  return (
    <span className={`px-2 py-1 text-xs font-medium rounded border ${styles[urgency] || styles.none}`}>
      {labels[urgency] || urgency}
    </span>
  );
};

// Stock Setting Modal
const StockSettingModal = ({ product, onClose, onSave, token }) => {
  const [loading, setLoading] = useState(false);
  const [settings, setSettings] = useState({
    minimum_stock: product?.minimum_stock || 0,
    maximum_stock: product?.maximum_stock || 0,
    lead_time_days: product?.lead_time_days || 3
  });

  const handleSave = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_URL}/api/stock-reorder/settings`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          product_id: product.product_id,
          ...settings
        })
      });
      
      if (!res.ok) throw new Error('Gagal menyimpan');
      onSave();
    } catch (err) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (!product) return null;

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl max-w-md w-full">
        <div className="p-6 border-b border-red-900/30">
          <h3 className="text-lg font-semibold text-amber-100">Setting Stok</h3>
          <p className="text-sm text-gray-400 mt-1">{product.product_name}</p>
        </div>
        
        <div className="p-6 space-y-4">
          <div className="bg-black/30 rounded-lg p-3">
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Stok Saat Ini</span>
              <span className="text-amber-100 font-bold">{product.current_stock} {product.unit}</span>
            </div>
            <div className="flex justify-between text-sm mt-1">
              <span className="text-gray-500">Velocity (per hari)</span>
              <span className="text-gray-300">{product.sales_velocity} {product.unit}</span>
            </div>
          </div>
          
          <div>
            <label className="text-sm text-gray-400 mb-1 block">Stok Minimum</label>
            <input
              type="number"
              value={settings.minimum_stock}
              onChange={(e) => setSettings({...settings, minimum_stock: parseFloat(e.target.value) || 0})}
              className="w-full bg-black/30 border border-red-900/30 rounded-lg p-3 text-amber-100"
              data-testid="min-stock-input"
            />
          </div>
          
          <div>
            <label className="text-sm text-gray-400 mb-1 block">Stok Maximum</label>
            <input
              type="number"
              value={settings.maximum_stock}
              onChange={(e) => setSettings({...settings, maximum_stock: parseFloat(e.target.value) || 0})}
              className="w-full bg-black/30 border border-red-900/30 rounded-lg p-3 text-amber-100"
              data-testid="max-stock-input"
            />
          </div>
          
          <div>
            <label className="text-sm text-gray-400 mb-1 block">Lead Time (hari)</label>
            <input
              type="number"
              value={settings.lead_time_days}
              onChange={(e) => setSettings({...settings, lead_time_days: parseInt(e.target.value) || 3})}
              className="w-full bg-black/30 border border-red-900/30 rounded-lg p-3 text-amber-100"
              data-testid="lead-time-input"
            />
          </div>
        </div>
        
        <div className="p-6 border-t border-red-900/30 flex gap-3 justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-400 hover:text-amber-100"
          >
            Batal
          </button>
          <button
            onClick={handleSave}
            disabled={loading}
            className="px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white rounded-lg disabled:opacity-50"
            data-testid="save-settings-btn"
          >
            {loading ? 'Menyimpan...' : 'Simpan'}
          </button>
        </div>
      </div>
    </div>
  );
};

const StockReorder = () => {
  const { token } = useAuth();
  const { toast } = useToast();
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('suggestions');
  
  // Data states
  const [dashboard, setDashboard] = useState(null);
  const [suggestions, setSuggestions] = useState([]);
  const [summary, setSummary] = useState(null);
  const [selectedProduct, setSelectedProduct] = useState(null);
  
  // Filter states
  const [urgencyFilter, setUrgencyFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  const fetchDashboard = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/stock-reorder/dashboard`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      setDashboard(data);
    } catch (err) {
      console.error('Error:', err);
    }
  }, [token]);

  const fetchSuggestions = useCallback(async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (urgencyFilter) params.append('urgency', urgencyFilter);
      
      const res = await fetch(`${API_URL}/api/stock-reorder/suggestions?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      setSuggestions(data.items || []);
      setSummary(data.summary || null);
    } catch (err) {
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  }, [token, urgencyFilter]);

  useEffect(() => {
    if (token) {
      fetchDashboard();
      fetchSuggestions();
    }
  }, [token, fetchDashboard, fetchSuggestions]);

  const handleRefresh = () => {
    fetchDashboard();
    fetchSuggestions();
  };

  const generatePODraft = async (saveToDb = false) => {
    try {
      // Build query params
      const params = new URLSearchParams();
      if (urgencyFilter) params.append('urgency_filter', urgencyFilter);
      params.append('save_to_db', saveToDb.toString());
      
      const res = await fetch(`${API_URL}/api/stock-reorder/generate-po-draft?${params}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      const data = await res.json();
      
      if (!res.ok) {
        throw new Error(data.detail || data.message || 'Gagal generate PO draft');
      }
      
      if (data.success) {
        if (saveToDb) {
          toast({ 
            title: 'Sukses', 
            description: `Berhasil membuat ${data.saved_count} PO Draft dengan ${data.total_items} item`
          });
          handleRefresh();
        } else {
          toast({ 
            title: 'Preview PO', 
            description: `${data.total_drafts} draft PO dengan ${data.total_items} item. Klik "Save PO Draft" untuk menyimpan.`
          });
        }
      } else {
        toast({ 
          title: 'Info', 
          description: data.message || 'Tidak ada item untuk di-reorder',
          variant: 'destructive'
        });
      }
    } catch (err) {
      console.error('Generate PO error:', err);
      toast({ 
        title: 'Error', 
        description: err.message || 'Gagal generate PO draft',
        variant: 'destructive'
      });
    }
  };

  // Filter suggestions
  const filteredSuggestions = suggestions.filter(s => 
    !searchQuery || 
    s.product_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    s.product_code?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6" data-testid="stock-reorder-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Stock Reorder</h1>
          <p className="text-gray-400 text-sm mt-1">Rekomendasi pembelian stok otomatis</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => generatePODraft(false)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg"
            data-testid="preview-po-btn"
          >
            <FileText className="h-4 w-4" />
            Preview PO
          </button>
          <button
            onClick={() => generatePODraft(true)}
            className="flex items-center gap-2 px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white rounded-lg"
            data-testid="generate-po-btn"
          >
            <ShoppingCart className="h-4 w-4" />
            Save PO Draft
          </button>
          <button
            onClick={handleRefresh}
            className="flex items-center gap-2 px-4 py-2 bg-red-900/30 hover:bg-red-900/50 text-amber-100 rounded-lg"
            data-testid="refresh-btn"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Dashboard Summary */}
      {dashboard && (
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div className="bg-gradient-to-br from-blue-900/30 to-blue-800/10 border border-blue-700/30 rounded-xl p-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-blue-500/20 flex items-center justify-center">
                <Package className="h-5 w-5 text-blue-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-blue-300">{dashboard.summary?.total_products || 0}</p>
                <p className="text-xs text-blue-400/70">Total Produk</p>
              </div>
            </div>
          </div>
          
          <div className="bg-gradient-to-br from-red-900/30 to-red-800/10 border border-red-700/30 rounded-xl p-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-red-500/20 flex items-center justify-center">
                <AlertTriangle className="h-5 w-5 text-red-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-red-300">{dashboard.summary?.critical_count || 0}</p>
                <p className="text-xs text-red-400/70">Kritis</p>
              </div>
            </div>
          </div>
          
          <div className="bg-gradient-to-br from-orange-900/30 to-orange-800/10 border border-orange-700/30 rounded-xl p-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-orange-500/20 flex items-center justify-center">
                <ArrowDown className="h-5 w-5 text-orange-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-orange-300">{dashboard.summary?.high_count || 0}</p>
                <p className="text-xs text-orange-400/70">Prioritas Tinggi</p>
              </div>
            </div>
          </div>
          
          <div className="bg-gradient-to-br from-yellow-900/30 to-yellow-800/10 border border-yellow-700/30 rounded-xl p-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-yellow-500/20 flex items-center justify-center">
                <ShoppingCart className="h-5 w-5 text-yellow-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-yellow-300">{dashboard.summary?.needs_reorder || 0}</p>
                <p className="text-xs text-yellow-400/70">Perlu Reorder</p>
              </div>
            </div>
          </div>
          
          <div className="bg-gradient-to-br from-gray-800/50 to-gray-700/20 border border-gray-600/30 rounded-xl p-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-gray-500/20 flex items-center justify-center">
                <AlertCircle className="h-5 w-5 text-gray-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-300">{dashboard.summary?.out_of_stock || 0}</p>
                <p className="text-xs text-gray-400/70">Stok Habis</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-wrap gap-4">
        <div className="flex-1 min-w-[200px]">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
            <input
              type="text"
              placeholder="Cari produk..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-black/30 border border-red-900/30 rounded-lg text-amber-100 placeholder-gray-500"
              data-testid="search-input"
            />
          </div>
        </div>
        
        <div className="w-44">
          <SearchableEnumSelect
            options={reorderUrgencyOptions}
            value={urgencyFilter}
            onValueChange={setUrgencyFilter}
            placeholder="Semua Urgency"
            showAllOption={true}
            allOptionLabel="Semua Urgency"
            data-testid="urgency-filter"
          />
        </div>
      </div>

      {/* Suggestions List */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <RefreshCw className="h-8 w-8 text-amber-500 animate-spin" />
        </div>
      ) : filteredSuggestions.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <CheckCircle2 className="h-12 w-12 mx-auto mb-3 opacity-30" />
          <p>Tidak ada produk yang perlu reorder</p>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredSuggestions.map((item) => (
            <div 
              key={item.product_id}
              className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4 hover:border-amber-500/30 transition-colors"
              data-testid={`suggestion-${item.product_id}`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-amber-100 font-semibold">{item.product_name}</span>
                    <span className="text-gray-500 text-sm">{item.product_code}</span>
                    <UrgencyBadge urgency={item.urgency} />
                  </div>
                  
                  <div className="grid grid-cols-2 md:grid-cols-6 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500">Stok Saat Ini</span>
                      <p className={`font-medium ${item.current_stock <= 0 ? 'text-red-400' : item.current_stock <= item.minimum_stock ? 'text-orange-400' : 'text-gray-300'}`}>
                        {item.current_stock} {item.unit}
                      </p>
                    </div>
                    <div>
                      <span className="text-gray-500">Min / Max</span>
                      <p className="text-gray-300">{item.minimum_stock} / {item.maximum_stock}</p>
                    </div>
                    <div>
                      <span className="text-gray-500">Reorder Point</span>
                      <p className="text-gray-300">{item.reorder_point}</p>
                    </div>
                    <div>
                      <span className="text-gray-500">Velocity/Hari</span>
                      <p className="text-gray-300">{item.sales_velocity} {item.unit}</p>
                    </div>
                    <div>
                      <span className="text-gray-500">Sisa Hari</span>
                      <p className={`font-medium ${item.days_remaining <= 3 ? 'text-red-400' : item.days_remaining <= 7 ? 'text-yellow-400' : 'text-green-400'}`}>
                        {item.days_remaining >= 999 ? '∞' : `${item.days_remaining} hari`}
                      </p>
                    </div>
                    <div>
                      <span className="text-gray-500">Saran Order</span>
                      <p className="text-amber-100 font-bold">{item.suggested_qty} {item.unit}</p>
                    </div>
                  </div>
                </div>
                
                <button
                  onClick={() => setSelectedProduct(item)}
                  className="p-2 hover:bg-red-900/30 rounded-lg text-gray-400 hover:text-amber-100"
                  title="Setting Stok"
                  data-testid={`settings-${item.product_id}`}
                >
                  <Settings className="h-5 w-5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Critical Items Alert */}
      {dashboard?.critical_items?.length > 0 && (
        <div className="bg-red-900/20 border border-red-500/30 rounded-xl p-4">
          <h3 className="font-medium text-red-300 mb-3 flex items-center gap-2">
            <AlertTriangle className="h-5 w-5" />
            Item Kritis - Perlu Segera Direorder
          </h3>
          <div className="space-y-2">
            {dashboard.critical_items.map((item, idx) => (
              <div key={idx} className="flex items-center justify-between p-2 bg-black/30 rounded">
                <div>
                  <span className="text-amber-100">{item.product_name}</span>
                  <span className="text-gray-500 text-sm ml-2">({item.product_code})</span>
                </div>
                <div className="text-right">
                  <span className="text-red-400">Stok: {item.current_stock}</span>
                  <span className="text-gray-500 ml-2">Saran: {item.suggested_qty} {item.unit}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Stock Setting Modal */}
      {selectedProduct && (
        <StockSettingModal
          product={selectedProduct}
          onClose={() => setSelectedProduct(null)}
          onSave={() => {
            setSelectedProduct(null);
            handleRefresh();
          }}
          token={token}
        />
      )}
    </div>
  );
};

export default StockReorder;
