import React, { useState, useEffect, useCallback } from 'react';
import { 
  CreditCard, AlertTriangle, Shield, Users, DollarSign, Clock, 
  TrendingUp, Ban, CheckCircle2, XCircle, Search, Filter,
  RefreshCw, Eye, Lock, Unlock, AlertCircle, ChevronRight,
  Edit, Save, X
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

import { getApiUrl } from '../utils/apiConfig';
const API_URL = getApiUrl();

// Status Badge Component
const CreditStatusBadge = ({ status }) => {
  const styles = {
    active: 'bg-green-500/20 text-green-300 border-green-500/30',
    warning: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
    hold: 'bg-orange-500/20 text-orange-300 border-orange-500/30',
    blocked: 'bg-red-500/20 text-red-300 border-red-500/30',
    blacklist: 'bg-gray-800 text-gray-300 border-gray-600'
  };
  
  const labels = {
    active: 'Aktif',
    warning: 'Peringatan',
    hold: 'Ditahan',
    blocked: 'Diblokir',
    blacklist: 'Blacklist'
  };
  
  return (
    <span className={`px-2 py-1 text-xs font-medium rounded border ${styles[status] || styles.active}`}>
      {labels[status] || status}
    </span>
  );
};

// Customer Credit Detail Modal
const CustomerCreditModal = ({ customer, onClose, onUpdate, token }) => {
  const [loading, setLoading] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [creditLimit, setCreditLimit] = useState(customer?.credit_limit || 0);
  const [notes, setNotes] = useState('');
  const [holdReason, setHoldReason] = useState('');
  
  if (!customer) return null;
  
  const handleUpdateLimit = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_URL}/api/credit-control/customer/${customer.customer_id}/limit`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          customer_id: customer.customer_id,
          credit_limit: parseFloat(creditLimit),
          notes
        })
      });
      
      if (!res.ok) throw new Error('Gagal update limit');
      
      setEditMode(false);
      onUpdate();
    } catch (err) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };
  
  const handleHoldAction = async (action) => {
    try {
      setLoading(true);
      const res = await fetch(`${API_URL}/api/credit-control/customer/${customer.customer_id}/hold`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          customer_id: customer.customer_id,
          action,
          reason: holdReason
        })
      });
      
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Gagal mengubah status');
      }
      
      onUpdate();
      onClose();
    } catch (err) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };
  
  const utilizationPercent = customer.credit_limit > 0 
    ? (customer.outstanding_balance / customer.credit_limit * 100) 
    : 0;
  
  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="p-6 border-b border-red-900/30">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-amber-100">
                {customer.customer_name}
              </h3>
              <p className="text-sm text-gray-400">{customer.customer_code} - {customer.segment}</p>
            </div>
            <CreditStatusBadge status={customer.effective_status} />
          </div>
        </div>
        
        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Credit Summary Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-black/30 rounded-lg p-3">
              <p className="text-xs text-gray-500">Credit Limit</p>
              <p className="text-lg font-bold text-amber-100">
                Rp {customer.credit_limit?.toLocaleString('id-ID') || 0}
              </p>
            </div>
            <div className="bg-black/30 rounded-lg p-3">
              <p className="text-xs text-gray-500">Outstanding</p>
              <p className="text-lg font-bold text-red-400">
                Rp {customer.outstanding_balance?.toLocaleString('id-ID') || 0}
              </p>
            </div>
            <div className="bg-black/30 rounded-lg p-3">
              <p className="text-xs text-gray-500">Available</p>
              <p className="text-lg font-bold text-green-400">
                Rp {customer.available_credit?.toLocaleString('id-ID') || 0}
              </p>
            </div>
            <div className="bg-black/30 rounded-lg p-3">
              <p className="text-xs text-gray-500">Overdue</p>
              <p className="text-lg font-bold text-orange-400">
                Rp {customer.overdue_amount?.toLocaleString('id-ID') || 0}
              </p>
            </div>
          </div>
          
          {/* Utilization Bar */}
          {customer.credit_limit > 0 && (
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-gray-400">Utilisasi Credit</span>
                <span className={`font-medium ${utilizationPercent >= 100 ? 'text-red-400' : utilizationPercent >= 80 ? 'text-yellow-400' : 'text-green-400'}`}>
                  {utilizationPercent.toFixed(1)}%
                </span>
              </div>
              <div className="h-3 bg-black/50 rounded-full overflow-hidden">
                <div 
                  className={`h-full transition-all ${
                    utilizationPercent >= 100 ? 'bg-red-500' : 
                    utilizationPercent >= 80 ? 'bg-yellow-500' : 'bg-green-500'
                  }`}
                  style={{ width: `${Math.min(utilizationPercent, 100)}%` }}
                />
              </div>
            </div>
          )}
          
          {/* Details */}
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-500">Invoice Outstanding</span>
              <p className="text-gray-300">{customer.ar_count || 0} invoice</p>
            </div>
            <div>
              <span className="text-gray-500">Invoice Overdue</span>
              <p className="text-orange-400">{customer.overdue_count || 0} invoice ({customer.overdue_days || 0} hari)</p>
            </div>
          </div>
          
          {customer.status_reason && (
            <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-3">
              <p className="text-sm text-red-300">
                <AlertTriangle className="h-4 w-4 inline mr-2" />
                {customer.status_reason}
              </p>
            </div>
          )}
          
          {/* Edit Credit Limit */}
          <div className="border-t border-red-900/30 pt-4">
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-medium text-amber-100">Credit Limit</h4>
              {!editMode && (
                <button
                  onClick={() => setEditMode(true)}
                  className="text-sm text-amber-400 hover:text-amber-300 flex items-center gap-1"
                  data-testid="edit-limit-btn"
                >
                  <Edit className="h-4 w-4" /> Edit
                </button>
              )}
            </div>
            
            {editMode ? (
              <div className="space-y-3">
                <input
                  type="number"
                  value={creditLimit}
                  onChange={(e) => setCreditLimit(e.target.value)}
                  className="w-full bg-black/30 border border-red-900/30 rounded-lg p-3 text-amber-100"
                  placeholder="Credit Limit (Rp)"
                  data-testid="credit-limit-input"
                />
                <input
                  type="text"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  className="w-full bg-black/30 border border-red-900/30 rounded-lg p-3 text-amber-100"
                  placeholder="Catatan perubahan..."
                  data-testid="credit-notes-input"
                />
                <div className="flex gap-2">
                  <button
                    onClick={handleUpdateLimit}
                    disabled={loading}
                    className="px-4 py-2 bg-green-600 hover:bg-green-500 text-white rounded-lg disabled:opacity-50"
                    data-testid="save-limit-btn"
                  >
                    <Save className="h-4 w-4 inline mr-1" /> Simpan
                  </button>
                  <button
                    onClick={() => setEditMode(false)}
                    className="px-4 py-2 text-gray-400 hover:text-white"
                  >
                    Batal
                  </button>
                </div>
              </div>
            ) : (
              <p className="text-2xl font-bold text-amber-100">
                Rp {customer.credit_limit?.toLocaleString('id-ID') || 0}
              </p>
            )}
          </div>
          
          {/* Hold/Block Actions */}
          <div className="border-t border-red-900/30 pt-4">
            <h4 className="font-medium text-amber-100 mb-3">Credit Status Actions</h4>
            
            <div className="space-y-3">
              <input
                type="text"
                value={holdReason}
                onChange={(e) => setHoldReason(e.target.value)}
                className="w-full bg-black/30 border border-red-900/30 rounded-lg p-3 text-amber-100"
                placeholder="Alasan hold/block (wajib diisi)..."
                data-testid="hold-reason-input"
              />
              
              <div className="flex flex-wrap gap-2">
                {customer.effective_status === 'active' && (
                  <>
                    <button
                      onClick={() => handleHoldAction('hold')}
                      disabled={loading || !holdReason}
                      className="px-3 py-2 bg-orange-600 hover:bg-orange-500 text-white rounded-lg disabled:opacity-50 text-sm"
                      data-testid="hold-btn"
                    >
                      <Lock className="h-4 w-4 inline mr-1" /> Hold
                    </button>
                    <button
                      onClick={() => handleHoldAction('block')}
                      disabled={loading || !holdReason}
                      className="px-3 py-2 bg-red-600 hover:bg-red-500 text-white rounded-lg disabled:opacity-50 text-sm"
                      data-testid="block-btn"
                    >
                      <Ban className="h-4 w-4 inline mr-1" /> Block
                    </button>
                  </>
                )}
                
                {customer.effective_status === 'hold' && (
                  <button
                    onClick={() => handleHoldAction('release')}
                    disabled={loading}
                    className="px-3 py-2 bg-green-600 hover:bg-green-500 text-white rounded-lg disabled:opacity-50 text-sm"
                    data-testid="release-btn"
                  >
                    <Unlock className="h-4 w-4 inline mr-1" /> Release Hold
                  </button>
                )}
                
                {customer.effective_status === 'blocked' && (
                  <button
                    onClick={() => handleHoldAction('unblock')}
                    disabled={loading}
                    className="px-3 py-2 bg-green-600 hover:bg-green-500 text-white rounded-lg disabled:opacity-50 text-sm"
                    data-testid="unblock-btn"
                  >
                    <Unlock className="h-4 w-4 inline mr-1" /> Unblock
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
        
        {/* Footer */}
        <div className="p-6 border-t border-red-900/30 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-400 hover:text-amber-100"
            data-testid="close-modal-btn"
          >
            Tutup
          </button>
        </div>
      </div>
    </div>
  );
};

const CreditControl = () => {
  const { token } = useAuth();
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('dashboard');
  
  // Data states
  const [dashboard, setDashboard] = useState(null);
  const [atRiskCustomers, setAtRiskCustomers] = useState([]);
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);

  const fetchDashboard = useCallback(async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_URL}/api/credit-control/dashboard`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      setDashboard(data);
    } catch (err) {
      console.error('Error fetching dashboard:', err);
    } finally {
      setLoading(false);
    }
  }, [token]);

  const fetchAtRisk = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/credit-control/at-risk?min_overdue_days=7`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      setAtRiskCustomers(data.items || []);
    } catch (err) {
      console.error('Error fetching at-risk:', err);
    }
  }, [token]);

  const searchCustomer = async () => {
    if (!searchQuery.trim()) return;
    
    try {
      // First search customers
      const res = await fetch(`${API_URL}/api/customers/search?q=${encodeURIComponent(searchQuery)}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const customers = await res.json();
      
      // Then get credit info for each
      const results = await Promise.all(
        customers.slice(0, 10).map(async (c) => {
          try {
            const creditRes = await fetch(`${API_URL}/api/credit-control/customer/${c.id}`, {
              headers: { 'Authorization': `Bearer ${token}` }
            });
            return await creditRes.json();
          } catch {
            return { ...c, customer_id: c.id, error: true };
          }
        })
      );
      
      setSearchResults(results.filter(r => !r.error));
    } catch (err) {
      console.error('Error searching:', err);
    }
  };

  const viewCustomerDetail = async (customerId) => {
    try {
      const res = await fetch(`${API_URL}/api/credit-control/customer/${customerId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      setSelectedCustomer(data);
    } catch (err) {
      alert('Gagal memuat detail customer');
    }
  };

  useEffect(() => {
    if (token) {
      fetchDashboard();
      fetchAtRisk();
    }
  }, [token, fetchDashboard, fetchAtRisk]);

  const handleRefresh = () => {
    fetchDashboard();
    fetchAtRisk();
  };

  return (
    <div className="space-y-6" data-testid="credit-control-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Credit Control</h1>
          <p className="text-gray-400 text-sm mt-1">Monitor dan kelola credit limit pelanggan</p>
        </div>
        <button
          onClick={handleRefresh}
          className="flex items-center gap-2 px-4 py-2 bg-red-900/30 hover:bg-red-900/50 text-amber-100 rounded-lg"
          data-testid="refresh-btn"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Dashboard Summary */}
      {dashboard && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-gradient-to-br from-blue-900/30 to-blue-800/10 border border-blue-700/30 rounded-xl p-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-blue-500/20 flex items-center justify-center">
                <Users className="h-5 w-5 text-blue-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-blue-300">{dashboard.total_customers || 0}</p>
                <p className="text-xs text-blue-400/70">Total Pelanggan</p>
              </div>
            </div>
          </div>
          
          <div className="bg-gradient-to-br from-amber-900/30 to-amber-800/10 border border-amber-700/30 rounded-xl p-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-amber-500/20 flex items-center justify-center">
                <DollarSign className="h-5 w-5 text-amber-400" />
              </div>
              <div>
                <p className="text-lg font-bold text-amber-300">
                  Rp {(dashboard.total_outstanding / 1000000).toFixed(1)}jt
                </p>
                <p className="text-xs text-amber-400/70">Total Outstanding</p>
              </div>
            </div>
          </div>
          
          <div className="bg-gradient-to-br from-red-900/30 to-red-800/10 border border-red-700/30 rounded-xl p-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-red-500/20 flex items-center justify-center">
                <AlertTriangle className="h-5 w-5 text-red-400" />
              </div>
              <div>
                <p className="text-lg font-bold text-red-300">
                  Rp {(dashboard.total_overdue / 1000000).toFixed(1)}jt
                </p>
                <p className="text-xs text-red-400/70">Total Overdue ({dashboard.overdue_percentage}%)</p>
              </div>
            </div>
          </div>
          
          <div className="bg-gradient-to-br from-orange-900/30 to-orange-800/10 border border-orange-700/30 rounded-xl p-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-orange-500/20 flex items-center justify-center">
                <Shield className="h-5 w-5 text-orange-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-orange-300">{dashboard.pending_override_approvals || 0}</p>
                <p className="text-xs text-orange-400/70">Pending Override</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Customer Status Summary */}
      {dashboard?.customers_by_status && (
        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
          <h3 className="font-medium text-amber-100 mb-3">Status Pelanggan</h3>
          <div className="flex flex-wrap gap-3">
            {Object.entries(dashboard.customers_by_status).map(([status, count]) => (
              <div key={status} className="flex items-center gap-2">
                <CreditStatusBadge status={status} />
                <span className="text-gray-300 font-medium">{count}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 border-b border-red-900/30 pb-2">
        <button
          onClick={() => setActiveTab('dashboard')}
          className={`px-4 py-2 rounded-t-lg transition-colors ${
            activeTab === 'dashboard' 
              ? 'bg-red-900/30 text-amber-100 border-b-2 border-amber-500' 
              : 'text-gray-400 hover:text-amber-100'
          }`}
          data-testid="tab-dashboard"
        >
          <TrendingUp className="h-4 w-4 inline mr-2" />
          Dashboard
        </button>
        <button
          onClick={() => setActiveTab('at-risk')}
          className={`px-4 py-2 rounded-t-lg transition-colors ${
            activeTab === 'at-risk' 
              ? 'bg-red-900/30 text-amber-100 border-b-2 border-amber-500' 
              : 'text-gray-400 hover:text-amber-100'
          }`}
          data-testid="tab-at-risk"
        >
          <AlertTriangle className="h-4 w-4 inline mr-2" />
          At Risk ({atRiskCustomers.length})
        </button>
        <button
          onClick={() => setActiveTab('search')}
          className={`px-4 py-2 rounded-t-lg transition-colors ${
            activeTab === 'search' 
              ? 'bg-red-900/30 text-amber-100 border-b-2 border-amber-500' 
              : 'text-gray-400 hover:text-amber-100'
          }`}
          data-testid="tab-search"
        >
          <Search className="h-4 w-4 inline mr-2" />
          Cari Customer
        </button>
      </div>

      {/* Tab Content */}
      {activeTab === 'dashboard' && dashboard?.top_outstanding_customers && (
        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
          <h3 className="font-medium text-amber-100 mb-4">Top 10 Outstanding Customers</h3>
          <div className="space-y-2">
            {dashboard.top_outstanding_customers.map((customer, idx) => (
              <div 
                key={customer._id}
                className="flex items-center justify-between p-3 bg-black/30 rounded-lg hover:bg-red-900/20 cursor-pointer"
                onClick={() => viewCustomerDetail(customer._id)}
                data-testid={`top-customer-${idx}`}
              >
                <div className="flex items-center gap-3">
                  <span className="h-8 w-8 rounded-full bg-red-900/30 flex items-center justify-center text-amber-100 font-bold">
                    {idx + 1}
                  </span>
                  <div>
                    <p className="text-amber-100 font-medium">{customer.customer_name}</p>
                    <p className="text-xs text-gray-500">{customer.invoice_count} invoice</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-red-400 font-bold">
                    Rp {customer.total_outstanding?.toLocaleString('id-ID')}
                  </p>
                  <ChevronRight className="h-4 w-4 text-gray-500 inline" />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'at-risk' && (
        <div className="space-y-3">
          {atRiskCustomers.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <CheckCircle2 className="h-12 w-12 mx-auto mb-3 opacity-30" />
              <p>Tidak ada customer berisiko</p>
            </div>
          ) : (
            atRiskCustomers.map((customer) => (
              <div 
                key={customer.customer_id}
                className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4 hover:border-amber-500/30 cursor-pointer"
                onClick={() => setSelectedCustomer(customer)}
                data-testid={`at-risk-${customer.customer_id}`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-3 mb-2">
                      <span className="text-amber-100 font-semibold">{customer.customer_name}</span>
                      <span className="text-gray-500 text-sm">{customer.customer_code}</span>
                      <CreditStatusBadge status={customer.effective_status} />
                    </div>
                    
                    <div className="grid grid-cols-4 gap-4 text-sm">
                      <div>
                        <span className="text-gray-500">Limit</span>
                        <p className="text-gray-300">Rp {customer.credit_limit?.toLocaleString('id-ID')}</p>
                      </div>
                      <div>
                        <span className="text-gray-500">Outstanding</span>
                        <p className="text-red-400">Rp {customer.outstanding_balance?.toLocaleString('id-ID')}</p>
                      </div>
                      <div>
                        <span className="text-gray-500">Utilisasi</span>
                        <p className={`font-medium ${customer.utilization_percent >= 100 ? 'text-red-400' : customer.utilization_percent >= 80 ? 'text-yellow-400' : 'text-green-400'}`}>
                          {customer.utilization_percent?.toFixed(1)}%
                        </p>
                      </div>
                      <div>
                        <span className="text-gray-500">Overdue</span>
                        <p className="text-orange-400">{customer.overdue_days} hari</p>
                      </div>
                    </div>
                    
                    {customer.risk_factors?.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {customer.risk_factors.map((factor, i) => (
                          <span key={i} className="px-2 py-0.5 text-xs bg-red-900/30 text-red-300 rounded">
                            {factor}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                  
                  <ChevronRight className="h-5 w-5 text-gray-500" />
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {activeTab === 'search' && (
        <div className="space-y-4">
          <div className="flex gap-2">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && searchCustomer()}
                className="w-full pl-10 pr-4 py-2 bg-black/30 border border-red-900/30 rounded-lg text-amber-100 placeholder-gray-500"
                placeholder="Cari nama atau kode customer..."
                data-testid="search-input"
              />
            </div>
            <button
              onClick={searchCustomer}
              className="px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white rounded-lg"
              data-testid="search-btn"
            >
              Cari
            </button>
          </div>
          
          {searchResults.length > 0 && (
            <div className="space-y-2">
              {searchResults.map((customer) => (
                <div 
                  key={customer.customer_id}
                  className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4 hover:border-amber-500/30 cursor-pointer"
                  onClick={() => setSelectedCustomer(customer)}
                  data-testid={`search-result-${customer.customer_id}`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <span className="text-amber-100 font-semibold">{customer.customer_name}</span>
                      <span className="text-gray-500">{customer.customer_code}</span>
                      <CreditStatusBadge status={customer.effective_status} />
                    </div>
                    <div className="text-right">
                      <p className="text-gray-300">
                        Limit: Rp {customer.credit_limit?.toLocaleString('id-ID')}
                      </p>
                      <p className="text-sm text-gray-500">
                        Outstanding: Rp {customer.outstanding_balance?.toLocaleString('id-ID')}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Customer Detail Modal */}
      {selectedCustomer && (
        <CustomerCreditModal
          customer={selectedCustomer}
          onClose={() => setSelectedCustomer(null)}
          onUpdate={() => {
            handleRefresh();
            setSelectedCustomer(null);
          }}
          token={token}
        />
      )}
    </div>
  );
};

export default CreditControl;
