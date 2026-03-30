import React, { useState, useEffect, useCallback } from 'react';
import { 
  ClipboardList, Package, RefreshCw, Search, Filter, Plus,
  CheckCircle2, XCircle, Clock, AlertTriangle, Truck, Calendar,
  FileText, ChevronRight, TrendingUp, Building2, ArrowRight
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { SearchableEnumSelect, STATUS_OPTIONS, URGENCY_OPTIONS } from '../components/ui/searchable-enum-select';

import { getApiUrl } from '../utils/apiConfig';
const API_URL = getApiUrl();

// Status options for planning
const planningStatusOptions = [
  { value: 'draft', label: 'Draft', color: 'gray' },
  { value: 'reviewed', label: 'Reviewed', color: 'blue' },
  { value: 'approved', label: 'Approved', color: 'green' },
  { value: 'po_created', label: 'PO Created', color: 'purple' },
  { value: 'cancelled', label: 'Cancelled', color: 'red' },
];

const planningUrgencyOptions = [
  { value: 'critical', label: 'Critical', color: 'red' },
  { value: 'high', label: 'High', color: 'orange' },
  { value: 'medium', label: 'Medium', color: 'yellow' },
  { value: 'low', label: 'Low', color: 'blue' },
  { value: 'none', label: 'None', color: 'green' },
];

// Status Badge
const StatusBadge = ({ status }) => {
  const styles = {
    draft: 'bg-gray-500/20 text-gray-300 border-gray-500/30',
    reviewed: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
    approved: 'bg-green-500/20 text-green-300 border-green-500/30',
    po_created: 'bg-purple-500/20 text-purple-300 border-purple-500/30',
    cancelled: 'bg-red-500/20 text-red-300 border-red-500/30'
  };
  
  const labels = {
    draft: 'Draft',
    reviewed: 'Reviewed',
    approved: 'Approved',
    po_created: 'PO Created',
    cancelled: 'Cancelled'
  };
  
  return (
    <span className={`px-2 py-1 text-xs font-medium rounded border ${styles[status] || styles.draft}`}>
      {labels[status] || status}
    </span>
  );
};

// Urgency Badge
const UrgencyBadge = ({ urgency }) => {
  const styles = {
    critical: 'bg-red-500/20 text-red-300',
    high: 'bg-orange-500/20 text-orange-300',
    medium: 'bg-yellow-500/20 text-yellow-300',
    low: 'bg-blue-500/20 text-blue-300',
    none: 'bg-green-500/20 text-green-300'
  };
  
  return (
    <span className={`px-2 py-0.5 text-xs font-medium rounded ${styles[urgency] || styles.none}`}>
      {urgency}
    </span>
  );
};

const PurchasePlanning = () => {
  const { token } = useAuth();
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [creatingPO, setCreatingPO] = useState(false);
  
  // Data states
  const [plannings, setPlannings] = useState([]);
  const [summary, setSummary] = useState(null);
  const [dashboard, setDashboard] = useState(null);
  const [selectedItems, setSelectedItems] = useState([]);
  
  // Filter states
  const [filterStatus, setFilterStatus] = useState('');
  const [filterSupplier, setFilterSupplier] = useState('');
  const [filterUrgency, setFilterUrgency] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      
      const params = new URLSearchParams();
      if (filterStatus) params.append('status', filterStatus);
      if (filterSupplier) params.append('supplier_id', filterSupplier);
      if (filterUrgency) params.append('urgency', filterUrgency);
      
      const [listRes, dashRes] = await Promise.all([
        fetch(`${API_URL}/api/purchase-planning/list?${params}&limit=200`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`${API_URL}/api/purchase-planning/dashboard/summary`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
      ]);
      
      const [listData, dashData] = await Promise.all([
        listRes.json(),
        dashRes.json()
      ]);
      
      setPlannings(listData.items || []);
      setSummary(listData.summary || null);
      setDashboard(dashData);
      
    } catch (err) {
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  }, [token, filterStatus, filterSupplier, filterUrgency]);

  useEffect(() => {
    if (token) fetchData();
  }, [token, fetchData]);

  const handleGenerate = async () => {
    try {
      setGenerating(true);
      const res = await fetch(`${API_URL}/api/purchase-planning/generate`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ include_all_low_stock: true })
      });
      
      const data = await res.json();
      
      if (data.success) {
        alert(`Generated ${data.generated} planning recommendations (${data.skipped} skipped)`);
        fetchData();
      }
    } catch (err) {
      alert('Gagal generate planning');
    } finally {
      setGenerating(false);
    }
  };

  const handleStatusChange = async (planningId, newStatus) => {
    try {
      const res = await fetch(`${API_URL}/api/purchase-planning/${planningId}/status`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ status: newStatus, notes: '' })
      });
      
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Gagal update status');
      }
      
      fetchData();
    } catch (err) {
      alert(err.message);
    }
  };

  const handleCreatePO = async () => {
    const approvedItems = selectedItems.length > 0 
      ? selectedItems 
      : plannings.filter(p => p.status === 'approved').map(p => p.id);
    
    if (approvedItems.length === 0) {
      alert('Tidak ada item approved untuk dibuat PO. Approve item terlebih dahulu dengan mengklik tombol "Approve Selected" atau mengubah status per item.');
      return;
    }
    
    try {
      setCreatingPO(true);
      const res = await fetch(`${API_URL}/api/purchase-planning/create-po`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ planning_ids: approvedItems })
      });
      
      const data = await res.json();
      
      if (data.success) {
        alert(`Created ${data.created_pos} PO drafts`);
        setSelectedItems([]);
        fetchData();
      }
    } catch (err) {
      alert('Gagal membuat PO');
    } finally {
      setCreatingPO(false);
    }
  };

  const handleBulkApprove = async () => {
    // Get items to approve (selected or all draft/reviewed items)
    const itemsToApprove = selectedItems.length > 0 
      ? selectedItems.filter(id => {
          const item = plannings.find(p => p.id === id);
          return item && ['draft', 'reviewed'].includes(item.status);
        })
      : plannings.filter(p => ['draft', 'reviewed'].includes(p.status)).map(p => p.id);
    
    if (itemsToApprove.length === 0) {
      alert('Tidak ada item draft/reviewed untuk di-approve');
      return;
    }
    
    if (!window.confirm(`Approve ${itemsToApprove.length} item?`)) {
      return;
    }
    
    try {
      // Approve each item
      for (const id of itemsToApprove) {
        await fetch(`${API_URL}/api/purchase-planning/${id}/status`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ status: 'approved', notes: 'Bulk approval' })
        });
      }
      
      alert(`${itemsToApprove.length} item berhasil di-approve`);
      setSelectedItems([]);
      fetchData();
    } catch (err) {
      alert('Gagal approve item');
    }
  };

  const toggleSelect = (id) => {
    if (selectedItems.includes(id)) {
      setSelectedItems(selectedItems.filter(i => i !== id));
    } else {
      setSelectedItems([...selectedItems, id]);
    }
  };

  const selectAllApproved = () => {
    const approved = plannings.filter(p => p.status === 'approved').map(p => p.id);
    setSelectedItems(approved);
  };

  // Filter by search
  const filteredPlannings = plannings.filter(p => 
    !searchQuery || 
    p.product_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    p.product_code?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    p.supplier_name?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6" data-testid="purchase-planning-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Purchase Planning</h1>
          <p className="text-gray-400 text-sm mt-1">Perencanaan pembelian berdasarkan stok dan velocity</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleGenerate}
            disabled={generating}
            className="flex items-center gap-2 px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white rounded-lg disabled:opacity-50"
            data-testid="generate-btn"
          >
            <Plus className={`h-4 w-4 ${generating ? 'animate-spin' : ''}`} />
            {generating ? 'Generating...' : 'Generate Planning'}
          </button>
          <button
            onClick={handleBulkApprove}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg"
            data-testid="approve-btn"
          >
            <CheckCircle2 className="h-4 w-4" />
            Approve Selected
          </button>
          <button
            onClick={handleCreatePO}
            disabled={creatingPO}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-500 text-white rounded-lg disabled:opacity-50"
            data-testid="create-po-btn"
          >
            <FileText className="h-4 w-4" />
            {creatingPO ? 'Creating...' : 'Create Draft PO'}
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
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div className="bg-gradient-to-br from-gray-800/50 to-gray-700/20 border border-gray-600/30 rounded-xl p-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-gray-500/20 flex items-center justify-center">
                <ClipboardList className="h-5 w-5 text-gray-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-300">{dashboard.by_status?.draft || 0}</p>
                <p className="text-xs text-gray-400">Draft</p>
              </div>
            </div>
          </div>
          
          <div className="bg-gradient-to-br from-blue-900/30 to-blue-800/10 border border-blue-700/30 rounded-xl p-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-blue-500/20 flex items-center justify-center">
                <Clock className="h-5 w-5 text-blue-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-blue-300">{dashboard.by_status?.reviewed || 0}</p>
                <p className="text-xs text-blue-400">Reviewed</p>
              </div>
            </div>
          </div>
          
          <div className="bg-gradient-to-br from-green-900/30 to-green-800/10 border border-green-700/30 rounded-xl p-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-green-500/20 flex items-center justify-center">
                <CheckCircle2 className="h-5 w-5 text-green-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-green-300">{dashboard.by_status?.approved || 0}</p>
                <p className="text-xs text-green-400">Approved</p>
              </div>
            </div>
          </div>
          
          <div className="bg-gradient-to-br from-red-900/30 to-red-800/10 border border-red-700/30 rounded-xl p-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-red-500/20 flex items-center justify-center">
                <AlertTriangle className="h-5 w-5 text-red-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-red-300">{dashboard.by_urgency?.critical || 0}</p>
                <p className="text-xs text-red-400">Critical</p>
              </div>
            </div>
          </div>
          
          <div className="bg-gradient-to-br from-purple-900/30 to-purple-800/10 border border-purple-700/30 rounded-xl p-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-purple-500/20 flex items-center justify-center">
                <FileText className="h-5 w-5 text-purple-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-purple-300">{dashboard.by_status?.po_created || 0}</p>
                <p className="text-xs text-purple-400">PO Created</p>
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
              placeholder="Cari item, supplier..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-black/30 border border-red-900/30 rounded-lg text-amber-100 placeholder-gray-500"
              data-testid="search-input"
            />
          </div>
        </div>
        
        <div className="w-40">
          <SearchableEnumSelect
            options={planningStatusOptions}
            value={filterStatus}
            onValueChange={setFilterStatus}
            placeholder="Semua Status"
            showAllOption={true}
            allOptionLabel="Semua Status"
            data-testid="filter-status"
          />
        </div>
        
        <div className="w-40">
          <SearchableEnumSelect
            options={planningUrgencyOptions}
            value={filterUrgency}
            onValueChange={setFilterUrgency}
            placeholder="Semua Urgency"
            showAllOption={true}
            allOptionLabel="Semua Urgency"
            data-testid="filter-urgency"
          />
        </div>
        
        {selectedItems.length === 0 && plannings.some(p => p.status === 'approved') && (
          <button
            onClick={selectAllApproved}
            className="px-4 py-2 text-amber-400 hover:text-amber-300"
          >
            Select All Approved
          </button>
        )}
      </div>

      {/* Planning Table */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <RefreshCw className="h-8 w-8 text-amber-500 animate-spin" />
        </div>
      ) : filteredPlannings.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <ClipboardList className="h-12 w-12 mx-auto mb-3 opacity-30" />
          <p>Tidak ada planning</p>
          <button
            onClick={handleGenerate}
            className="mt-4 text-amber-400 hover:text-amber-300"
          >
            + Generate Planning
          </button>
        </div>
      ) : (
        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-black/30">
                <tr className="text-left text-sm text-gray-400">
                  <th className="p-3 w-10">
                    <input
                      type="checkbox"
                      checked={selectedItems.length > 0 && selectedItems.length === filteredPlannings.filter(p => p.status === 'approved').length}
                      onChange={(e) => e.target.checked ? selectAllApproved() : setSelectedItems([])}
                      className="rounded bg-black/30"
                    />
                  </th>
                  <th className="p-3">Item</th>
                  <th className="p-3">Warehouse</th>
                  <th className="p-3 text-right">Current Stock</th>
                  <th className="p-3 text-right">Reorder Point</th>
                  <th className="p-3 text-right">Velocity/Day</th>
                  <th className="p-3 text-right">Lead Time</th>
                  <th className="p-3 text-right">Recommend Qty</th>
                  <th className="p-3">Supplier</th>
                  <th className="p-3">Order Date</th>
                  <th className="p-3">Status</th>
                  <th className="p-3">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredPlannings.map((item) => (
                  <tr 
                    key={item.id}
                    className="border-t border-red-900/20 hover:bg-red-900/10"
                    data-testid={`planning-row-${item.id}`}
                  >
                    <td className="p-3">
                      {item.status === 'approved' && (
                        <input
                          type="checkbox"
                          checked={selectedItems.includes(item.id)}
                          onChange={() => toggleSelect(item.id)}
                          className="rounded bg-black/30"
                        />
                      )}
                    </td>
                    <td className="p-3">
                      <div>
                        <span className="text-amber-100 font-medium">{item.product_name}</span>
                        <span className="text-gray-500 text-xs ml-2">{item.product_code}</span>
                      </div>
                      <UrgencyBadge urgency={item.urgency} />
                    </td>
                    <td className="p-3 text-gray-300 text-sm">{item.warehouse_id || '-'}</td>
                    <td className="p-3 text-right">
                      <span className={`${item.current_stock <= item.minimum_stock ? 'text-red-400' : 'text-gray-300'}`}>
                        {item.current_stock} {item.unit}
                      </span>
                    </td>
                    <td className="p-3 text-right text-gray-300">{item.reorder_point}</td>
                    <td className="p-3 text-right text-gray-300">{item.sales_velocity}</td>
                    <td className="p-3 text-right text-gray-300">{item.lead_time_days} days</td>
                    <td className="p-3 text-right">
                      <span className="text-amber-100 font-bold">{item.recommended_qty} {item.unit}</span>
                    </td>
                    <td className="p-3 text-gray-300 text-sm">{item.supplier_name || '-'}</td>
                    <td className="p-3 text-gray-300 text-sm">{item.suggested_order_date}</td>
                    <td className="p-3">
                      <StatusBadge status={item.status} />
                    </td>
                    <td className="p-3">
                      <div className="flex gap-1">
                        {item.status === 'draft' && (
                          <button
                            onClick={() => handleStatusChange(item.id, 'reviewed')}
                            className="p-1 text-blue-400 hover:text-blue-300"
                            title="Review"
                          >
                            <Clock className="h-4 w-4" />
                          </button>
                        )}
                        {item.status === 'reviewed' && (
                          <button
                            onClick={() => handleStatusChange(item.id, 'approved')}
                            className="p-1 text-green-400 hover:text-green-300"
                            title="Approve"
                          >
                            <CheckCircle2 className="h-4 w-4" />
                          </button>
                        )}
                        {item.status !== 'po_created' && item.status !== 'cancelled' && (
                          <button
                            onClick={() => handleStatusChange(item.id, 'cancelled')}
                            className="p-1 text-red-400 hover:text-red-300"
                            title="Cancel"
                          >
                            <XCircle className="h-4 w-4" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Selection Summary */}
      {selectedItems.length > 0 && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 bg-amber-900/90 border border-amber-500/50 rounded-lg px-6 py-3 flex items-center gap-4 shadow-xl">
          <span className="text-amber-100">{selectedItems.length} items selected</span>
          <button
            onClick={handleCreatePO}
            disabled={creatingPO}
            className="px-4 py-2 bg-green-600 hover:bg-green-500 text-white rounded-lg"
          >
            Create PO
          </button>
          <button
            onClick={() => setSelectedItems([])}
            className="text-gray-400 hover:text-white"
          >
            Cancel
          </button>
        </div>
      )}
    </div>
  );
};

export default PurchasePlanning;
