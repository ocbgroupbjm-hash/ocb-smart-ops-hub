import React, { useState, useEffect, useCallback } from 'react';
import { 
  Warehouse, Package, ArrowRightLeft, Plus, RefreshCw, Search,
  ChevronRight, Building2, CheckCircle2, XCircle, Clock, Truck,
  AlertTriangle, Eye, Edit, MapPin
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

import { getApiUrl } from '../utils/apiConfig';
const API_URL = getApiUrl();

// Status Badge
const TransferStatusBadge = ({ status }) => {
  const styles = {
    pending: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
    approved: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
    in_transit: 'bg-purple-500/20 text-purple-300 border-purple-500/30',
    completed: 'bg-green-500/20 text-green-300 border-green-500/30',
    rejected: 'bg-red-500/20 text-red-300 border-red-500/30',
    cancelled: 'bg-gray-500/20 text-gray-400 border-gray-500/30'
  };
  
  const labels = {
    pending: 'Pending',
    approved: 'Disetujui',
    in_transit: 'Dalam Perjalanan',
    completed: 'Selesai',
    rejected: 'Ditolak',
    cancelled: 'Dibatalkan'
  };
  
  return (
    <span className={`px-2 py-1 text-xs font-medium rounded border ${styles[status] || styles.pending}`}>
      {labels[status] || status}
    </span>
  );
};

// Create Warehouse Modal
const CreateWarehouseModal = ({ onClose, onSave, token }) => {
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    name: '',
    code: '',
    branch_id: 'main',
    address: '',
    type: 'storage',
    is_default: false
  });

  const handleSubmit = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_URL}/api/warehouse`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(form)
      });
      
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Gagal membuat gudang');
      }
      
      onSave();
    } catch (err) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl max-w-md w-full">
        <div className="p-6 border-b border-red-900/30">
          <h3 className="text-lg font-semibold text-amber-100">Tambah Gudang Baru</h3>
        </div>
        
        <div className="p-6 space-y-4">
          <div>
            <label className="text-sm text-gray-400 mb-1 block">Nama Gudang *</label>
            <input
              type="text"
              value={form.name}
              onChange={(e) => setForm({...form, name: e.target.value})}
              className="w-full bg-black/30 border border-red-900/30 rounded-lg p-3 text-amber-100"
              placeholder="Gudang Utama"
              data-testid="warehouse-name-input"
            />
          </div>
          
          <div>
            <label className="text-sm text-gray-400 mb-1 block">Kode *</label>
            <input
              type="text"
              value={form.code}
              onChange={(e) => setForm({...form, code: e.target.value.toUpperCase()})}
              className="w-full bg-black/30 border border-red-900/30 rounded-lg p-3 text-amber-100"
              placeholder="WH-001"
              data-testid="warehouse-code-input"
            />
          </div>
          
          <div>
            <label className="text-sm text-gray-400 mb-1 block">Alamat</label>
            <textarea
              value={form.address}
              onChange={(e) => setForm({...form, address: e.target.value})}
              className="w-full bg-black/30 border border-red-900/30 rounded-lg p-3 text-amber-100"
              rows={2}
              placeholder="Alamat gudang..."
            />
          </div>
          
          <div>
            <label className="text-sm text-gray-400 mb-1 block">Tipe</label>
            <select
              value={form.type}
              onChange={(e) => setForm({...form, type: e.target.value})}
              className="w-full bg-black/30 border border-red-900/30 rounded-lg p-3 text-amber-100"
            >
              <option value="storage">Storage</option>
              <option value="retail">Retail</option>
              <option value="distribution">Distribution</option>
            </select>
          </div>
          
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={form.is_default}
              onChange={(e) => setForm({...form, is_default: e.target.checked})}
              className="rounded bg-black/30 border-red-900/30"
            />
            <span className="text-gray-300">Jadikan gudang default</span>
          </label>
        </div>
        
        <div className="p-6 border-t border-red-900/30 flex gap-3 justify-end">
          <button onClick={onClose} className="px-4 py-2 text-gray-400 hover:text-amber-100">
            Batal
          </button>
          <button
            onClick={handleSubmit}
            disabled={loading || !form.name || !form.code}
            className="px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white rounded-lg disabled:opacity-50"
            data-testid="save-warehouse-btn"
          >
            {loading ? 'Menyimpan...' : 'Simpan'}
          </button>
        </div>
      </div>
    </div>
  );
};

// Transfer Modal
const CreateTransferModal = ({ warehouses, onClose, onSave, token }) => {
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    source_warehouse_id: '',
    destination_warehouse_id: '',
    transfer_reason: '',
    items: [{ product_id: '', quantity: 1, notes: '' }]
  });
  const [products, setProducts] = useState([]);
  const [sourceStock, setSourceStock] = useState({});

  useEffect(() => {
    const fetchProducts = async () => {
      const res = await fetch(`${API_URL}/api/products?limit=100`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      setProducts(data.items || []);
    };
    fetchProducts();
  }, [token]);

  useEffect(() => {
    if (form.source_warehouse_id) {
      const fetchStock = async () => {
        const res = await fetch(`${API_URL}/api/warehouse/${form.source_warehouse_id}/stock`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await res.json();
        const stockMap = {};
        (data.items || []).forEach(item => {
          stockMap[item.product_id] = item.current_stock;
        });
        setSourceStock(stockMap);
      };
      fetchStock();
    }
  }, [form.source_warehouse_id, token]);

  const addItem = () => {
    setForm({...form, items: [...form.items, { product_id: '', quantity: 1, notes: '' }]});
  };

  const updateItem = (idx, field, value) => {
    const items = [...form.items];
    items[idx][field] = value;
    setForm({...form, items});
  };

  const removeItem = (idx) => {
    const items = form.items.filter((_, i) => i !== idx);
    setForm({...form, items});
  };

  const handleSubmit = async () => {
    try {
      setLoading(true);
      const validItems = form.items.filter(i => i.product_id && i.quantity > 0);
      
      const res = await fetch(`${API_URL}/api/warehouse/transfer`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({...form, items: validItems})
      });
      
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Gagal membuat transfer');
      }
      
      onSave();
    } catch (err) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-red-900/30">
          <h3 className="text-lg font-semibold text-amber-100">Transfer Stok</h3>
        </div>
        
        <div className="p-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm text-gray-400 mb-1 block">Dari Gudang *</label>
              <select
                value={form.source_warehouse_id}
                onChange={(e) => setForm({...form, source_warehouse_id: e.target.value})}
                className="w-full bg-black/30 border border-red-900/30 rounded-lg p-3 text-amber-100"
                data-testid="source-warehouse-select"
              >
                <option value="">Pilih gudang asal</option>
                {warehouses.map(wh => (
                  <option key={wh.id} value={wh.id}>{wh.name}</option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="text-sm text-gray-400 mb-1 block">Ke Gudang *</label>
              <select
                value={form.destination_warehouse_id}
                onChange={(e) => setForm({...form, destination_warehouse_id: e.target.value})}
                className="w-full bg-black/30 border border-red-900/30 rounded-lg p-3 text-amber-100"
                data-testid="dest-warehouse-select"
              >
                <option value="">Pilih gudang tujuan</option>
                {warehouses.filter(wh => wh.id !== form.source_warehouse_id).map(wh => (
                  <option key={wh.id} value={wh.id}>{wh.name}</option>
                ))}
              </select>
            </div>
          </div>
          
          <div>
            <label className="text-sm text-gray-400 mb-1 block">Alasan Transfer *</label>
            <input
              type="text"
              value={form.transfer_reason}
              onChange={(e) => setForm({...form, transfer_reason: e.target.value})}
              className="w-full bg-black/30 border border-red-900/30 rounded-lg p-3 text-amber-100"
              placeholder="Alasan transfer stok..."
              data-testid="transfer-reason-input"
            />
          </div>
          
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm text-gray-400">Item Transfer</label>
              <button
                onClick={addItem}
                className="text-sm text-amber-400 hover:text-amber-300"
              >
                + Tambah Item
              </button>
            </div>
            
            <div className="space-y-2">
              {form.items.map((item, idx) => (
                <div key={idx} className="flex gap-2 items-center">
                  <select
                    value={item.product_id}
                    onChange={(e) => updateItem(idx, 'product_id', e.target.value)}
                    className="flex-1 bg-black/30 border border-red-900/30 rounded-lg p-2 text-amber-100 text-sm"
                  >
                    <option value="">Pilih produk</option>
                    {products.map(p => (
                      <option key={p.id} value={p.id}>
                        {p.name} (Stok: {sourceStock[p.id] || 0})
                      </option>
                    ))}
                  </select>
                  <input
                    type="number"
                    value={item.quantity}
                    onChange={(e) => updateItem(idx, 'quantity', parseInt(e.target.value) || 0)}
                    className="w-24 bg-black/30 border border-red-900/30 rounded-lg p-2 text-amber-100 text-sm"
                    min="1"
                  />
                  {form.items.length > 1 && (
                    <button
                      onClick={() => removeItem(idx)}
                      className="text-red-400 hover:text-red-300 p-2"
                    >
                      <XCircle className="h-4 w-4" />
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
        
        <div className="p-6 border-t border-red-900/30 flex gap-3 justify-end">
          <button onClick={onClose} className="px-4 py-2 text-gray-400 hover:text-amber-100">
            Batal
          </button>
          <button
            onClick={handleSubmit}
            disabled={loading || !form.source_warehouse_id || !form.destination_warehouse_id || !form.transfer_reason}
            className="px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white rounded-lg disabled:opacity-50"
            data-testid="submit-transfer-btn"
          >
            {loading ? 'Memproses...' : 'Buat Transfer'}
          </button>
        </div>
      </div>
    </div>
  );
};

const WarehouseControl = () => {
  const { token } = useAuth();
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('warehouses');
  
  // Data states
  const [dashboard, setDashboard] = useState(null);
  const [warehouses, setWarehouses] = useState([]);
  const [transfers, setTransfers] = useState([]);
  
  // Modal states
  const [showCreateWarehouse, setShowCreateWarehouse] = useState(false);
  const [showCreateTransfer, setShowCreateTransfer] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      
      const [dashRes, whRes, trfRes] = await Promise.all([
        fetch(`${API_URL}/api/warehouse/dashboard/summary`, { headers: { 'Authorization': `Bearer ${token}` }}),
        fetch(`${API_URL}/api/warehouse`, { headers: { 'Authorization': `Bearer ${token}` }}),
        fetch(`${API_URL}/api/warehouse/transfers?limit=20`, { headers: { 'Authorization': `Bearer ${token}` }})
      ]);
      
      const [dashData, whData, trfData] = await Promise.all([
        dashRes.json(),
        whRes.json(),
        trfRes.json()
      ]);
      
      setDashboard(dashData);
      setWarehouses(whData.items || []);
      setTransfers(trfData.items || []);
      
    } catch (err) {
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    if (token) fetchData();
  }, [token, fetchData]);

  const handleTransferAction = async (transferId, action) => {
    try {
      const res = await fetch(`${API_URL}/api/warehouse/transfer/${transferId}/action`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ action, notes: '' })
      });
      
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Gagal');
      }
      
      fetchData();
    } catch (err) {
      alert(err.message);
    }
  };

  return (
    <div className="space-y-6" data-testid="warehouse-control-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Warehouse Control</h1>
          <p className="text-gray-400 text-sm mt-1">Kelola gudang dan transfer stok</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowCreateTransfer(true)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg"
            data-testid="new-transfer-btn"
          >
            <ArrowRightLeft className="h-4 w-4" />
            Transfer Stok
          </button>
          <button
            onClick={() => setShowCreateWarehouse(true)}
            className="flex items-center gap-2 px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white rounded-lg"
            data-testid="new-warehouse-btn"
          >
            <Plus className="h-4 w-4" />
            Tambah Gudang
          </button>
          <button
            onClick={fetchData}
            className="flex items-center gap-2 px-4 py-2 bg-red-900/30 hover:bg-red-900/50 text-amber-100 rounded-lg"
            data-testid="refresh-btn"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      {dashboard && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-gradient-to-br from-blue-900/30 to-blue-800/10 border border-blue-700/30 rounded-xl p-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-blue-500/20 flex items-center justify-center">
                <Warehouse className="h-5 w-5 text-blue-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-blue-300">{dashboard.total_warehouses || 0}</p>
                <p className="text-xs text-blue-400/70">Total Gudang</p>
              </div>
            </div>
          </div>
          
          <div className="bg-gradient-to-br from-yellow-900/30 to-yellow-800/10 border border-yellow-700/30 rounded-xl p-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-yellow-500/20 flex items-center justify-center">
                <Clock className="h-5 w-5 text-yellow-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-yellow-300">{dashboard.pending_transfers || 0}</p>
                <p className="text-xs text-yellow-400/70">Pending Transfer</p>
              </div>
            </div>
          </div>
          
          <div className="bg-gradient-to-br from-purple-900/30 to-purple-800/10 border border-purple-700/30 rounded-xl p-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-purple-500/20 flex items-center justify-center">
                <Truck className="h-5 w-5 text-purple-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-purple-300">{dashboard.in_transit_transfers || 0}</p>
                <p className="text-xs text-purple-400/70">Dalam Perjalanan</p>
              </div>
            </div>
          </div>
          
          <div className="bg-gradient-to-br from-green-900/30 to-green-800/10 border border-green-700/30 rounded-xl p-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-green-500/20 flex items-center justify-center">
                <Package className="h-5 w-5 text-green-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-green-300">
                  {dashboard.warehouses?.reduce((sum, w) => sum + (w.total_stock || 0), 0) || 0}
                </p>
                <p className="text-xs text-green-400/70">Total Stok Items</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 border-b border-red-900/30 pb-2">
        <button
          onClick={() => setActiveTab('warehouses')}
          className={`flex items-center gap-2 px-4 py-2 rounded-t-lg transition-colors ${
            activeTab === 'warehouses' 
              ? 'bg-red-900/30 text-amber-100 border-b-2 border-amber-500' 
              : 'text-gray-400 hover:text-amber-100'
          }`}
          data-testid="tab-warehouses"
        >
          <Warehouse className="h-4 w-4" />
          Gudang ({warehouses.length})
        </button>
        <button
          onClick={() => setActiveTab('transfers')}
          className={`flex items-center gap-2 px-4 py-2 rounded-t-lg transition-colors ${
            activeTab === 'transfers' 
              ? 'bg-red-900/30 text-amber-100 border-b-2 border-amber-500' 
              : 'text-gray-400 hover:text-amber-100'
          }`}
          data-testid="tab-transfers"
        >
          <ArrowRightLeft className="h-4 w-4" />
          Transfer ({transfers.length})
        </button>
      </div>

      {/* Content */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <RefreshCw className="h-8 w-8 text-amber-500 animate-spin" />
        </div>
      ) : (
        <>
          {activeTab === 'warehouses' && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {warehouses.length === 0 ? (
                <div className="col-span-full text-center py-12 text-gray-500">
                  <Warehouse className="h-12 w-12 mx-auto mb-3 opacity-30" />
                  <p>Belum ada gudang</p>
                  <button
                    onClick={() => setShowCreateWarehouse(true)}
                    className="mt-4 text-amber-400 hover:text-amber-300"
                  >
                    + Tambah Gudang Pertama
                  </button>
                </div>
              ) : (
                warehouses.map(wh => (
                  <div 
                    key={wh.id}
                    className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4 hover:border-amber-500/30 transition-colors"
                    data-testid={`warehouse-${wh.id}`}
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h3 className="text-amber-100 font-semibold">{wh.name}</h3>
                        <p className="text-sm text-gray-500">{wh.code}</p>
                      </div>
                      {wh.is_default && (
                        <span className="px-2 py-0.5 text-xs bg-amber-500/20 text-amber-300 rounded">
                          Default
                        </span>
                      )}
                    </div>
                    
                    <div className="space-y-2 text-sm">
                      <div className="flex items-center gap-2 text-gray-400">
                        <MapPin className="h-4 w-4" />
                        <span>{wh.address || 'Alamat belum diisi'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">Total Produk</span>
                        <span className="text-amber-100">{wh.total_products || 0}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">Total Stok</span>
                        <span className="text-amber-100">{wh.total_stock_items || wh.total_stock || 0}</span>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {activeTab === 'transfers' && (
            <div className="space-y-3">
              {transfers.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  <ArrowRightLeft className="h-12 w-12 mx-auto mb-3 opacity-30" />
                  <p>Belum ada transfer</p>
                </div>
              ) : (
                transfers.map(trf => (
                  <div 
                    key={trf.id}
                    className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4 hover:border-amber-500/30 transition-colors"
                    data-testid={`transfer-${trf.id}`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <span className="text-amber-100 font-semibold">{trf.transfer_no}</span>
                          <TransferStatusBadge status={trf.status} />
                        </div>
                        
                        <div className="flex items-center gap-2 text-sm text-gray-400 mb-2">
                          <span>{trf.source_warehouse_name}</span>
                          <ArrowRightLeft className="h-4 w-4" />
                          <span>{trf.destination_warehouse_name}</span>
                        </div>
                        
                        <div className="grid grid-cols-3 gap-4 text-sm">
                          <div>
                            <span className="text-gray-500">Total Items</span>
                            <p className="text-gray-300">{trf.total_items}</p>
                          </div>
                          <div>
                            <span className="text-gray-500">Total Qty</span>
                            <p className="text-gray-300">{trf.total_quantity}</p>
                          </div>
                          <div>
                            <span className="text-gray-500">Alasan</span>
                            <p className="text-gray-300 truncate">{trf.transfer_reason}</p>
                          </div>
                        </div>
                      </div>
                      
                      {trf.status === 'pending' && (
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleTransferAction(trf.id, 'reject')}
                            className="p-2 hover:bg-red-600/30 rounded-lg text-red-400"
                            title="Tolak"
                          >
                            <XCircle className="h-5 w-5" />
                          </button>
                          <button
                            onClick={() => handleTransferAction(trf.id, 'approve')}
                            className="p-2 hover:bg-green-600/30 rounded-lg text-green-400"
                            title="Setujui"
                          >
                            <CheckCircle2 className="h-5 w-5" />
                          </button>
                        </div>
                      )}
                      
                      {trf.status === 'approved' && (
                        <button
                          onClick={() => handleTransferAction(trf.id, 'complete')}
                          className="px-3 py-1 bg-green-600 hover:bg-green-500 text-white rounded-lg text-sm"
                        >
                          Selesaikan
                        </button>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </>
      )}

      {/* Modals */}
      {showCreateWarehouse && (
        <CreateWarehouseModal
          onClose={() => setShowCreateWarehouse(false)}
          onSave={() => {
            setShowCreateWarehouse(false);
            fetchData();
          }}
          token={token}
        />
      )}

      {showCreateTransfer && (
        <CreateTransferModal
          warehouses={warehouses}
          onClose={() => setShowCreateTransfer(false)}
          onSave={() => {
            setShowCreateTransfer(false);
            fetchData();
          }}
          token={token}
        />
      )}
    </div>
  );
};

export default WarehouseControl;
