import React, { useState, useEffect, useCallback } from 'react';
import { 
  Wallet, TrendingUp, Users, Building2, RefreshCw, Plus, Calculator,
  DollarSign, Award, CheckCircle2, XCircle, Clock, CreditCard,
  ChevronRight, Settings, ArrowRight, X, Percent
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Status Badge
const StatusBadge = ({ status }) => {
  const styles = {
    calculated: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
    approved: 'bg-green-500/20 text-green-300 border-green-500/30',
    paid: 'bg-purple-500/20 text-purple-300 border-purple-500/30',
    cancelled: 'bg-red-500/20 text-red-300 border-red-500/30'
  };
  
  const labels = {
    calculated: 'Calculated',
    approved: 'Approved',
    paid: 'Paid',
    cancelled: 'Cancelled'
  };
  
  return (
    <span className={`px-2 py-1 text-xs font-medium rounded border ${styles[status] || styles.calculated}`}>
      {labels[status] || status}
    </span>
  );
};

// Calculate Modal
const CalculateModal = ({ onClose, onSave, token }) => {
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    period_type: 'monthly',
    period_start: new Date().toISOString().slice(0, 8) + '01',
    period_end: '',
    calculate_for: 'all'
  });

  // Auto calculate period end
  useEffect(() => {
    if (form.period_start) {
      const start = new Date(form.period_start);
      let end;
      
      if (form.period_type === 'monthly') {
        end = new Date(start.getFullYear(), start.getMonth() + 1, 0);
      } else if (form.period_type === 'quarterly') {
        end = new Date(start.getFullYear(), start.getMonth() + 3, 0);
      } else {
        end = new Date(start.getFullYear(), 11, 31);
      }
      
      setForm({...form, period_end: end.toISOString().slice(0, 10)});
    }
  }, [form.period_start, form.period_type]);

  const handleSubmit = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_URL}/api/commission/calculate`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(form)
      });
      
      const data = await res.json();
      
      if (data.success) {
        alert(`Calculated ${data.calculated} commissions (${data.skipped} skipped)`);
        onSave();
      } else {
        throw new Error(data.detail || 'Gagal calculate');
      }
    } catch (err) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl max-w-md w-full">
        <div className="p-6 border-b border-red-900/30 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-amber-100">Calculate Commissions</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-white">
            <X className="h-5 w-5" />
          </button>
        </div>
        
        <div className="p-6 space-y-4">
          <div>
            <label className="text-sm text-gray-400 mb-1 block">Period Type</label>
            <select
              value={form.period_type}
              onChange={(e) => setForm({...form, period_type: e.target.value})}
              className="w-full bg-black/30 border border-red-900/30 rounded-lg p-3 text-amber-100"
              data-testid="period-type-select"
            >
              <option value="monthly">Bulanan</option>
              <option value="quarterly">Kuartalan</option>
              <option value="yearly">Tahunan</option>
            </select>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm text-gray-400 mb-1 block">Period Start</label>
              <input
                type="date"
                value={form.period_start}
                onChange={(e) => setForm({...form, period_start: e.target.value})}
                className="w-full bg-black/30 border border-red-900/30 rounded-lg p-3 text-amber-100"
                data-testid="period-start-input"
              />
            </div>
            <div>
              <label className="text-sm text-gray-400 mb-1 block">Period End</label>
              <input
                type="date"
                value={form.period_end}
                readOnly
                className="w-full bg-black/30 border border-red-900/30 rounded-lg p-3 text-gray-400"
              />
            </div>
          </div>
          
          <div>
            <label className="text-sm text-gray-400 mb-1 block">Calculate For</label>
            <select
              value={form.calculate_for}
              onChange={(e) => setForm({...form, calculate_for: e.target.value})}
              className="w-full bg-black/30 border border-red-900/30 rounded-lg p-3 text-amber-100"
              data-testid="calculate-for-select"
            >
              <option value="all">All Salesmen</option>
              <option value="salesman">Specific Salesman</option>
              <option value="branch">Specific Branch</option>
            </select>
          </div>
        </div>
        
        <div className="p-6 border-t border-red-900/30 flex gap-3 justify-end">
          <button onClick={onClose} className="px-4 py-2 text-gray-400 hover:text-amber-100">
            Batal
          </button>
          <button
            onClick={handleSubmit}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white rounded-lg disabled:opacity-50"
            data-testid="calculate-btn"
          >
            <Calculator className="h-4 w-4" />
            {loading ? 'Calculating...' : 'Calculate'}
          </button>
        </div>
      </div>
    </div>
  );
};

// Simulate Modal
const SimulateModal = ({ onClose, token, policy }) => {
  const [salesValue, setSalesValue] = useState(10000000);
  const [achievement, setAchievement] = useState(100);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSimulate = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_URL}/api/commission/simulate?sales_value=${salesValue}&achievement=${achievement}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      const data = await res.json();
      setResult(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl max-w-lg w-full">
        <div className="p-6 border-b border-red-900/30 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-amber-100">Commission Simulator</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-white">
            <X className="h-5 w-5" />
          </button>
        </div>
        
        <div className="p-6 space-y-4">
          <div>
            <label className="text-sm text-gray-400 mb-1 block">Sales Value (Rp)</label>
            <input
              type="number"
              value={salesValue}
              onChange={(e) => setSalesValue(parseFloat(e.target.value) || 0)}
              className="w-full bg-black/30 border border-red-900/30 rounded-lg p-3 text-amber-100"
              data-testid="sim-sales-input"
            />
          </div>
          
          <div>
            <label className="text-sm text-gray-400 mb-1 block">Achievement (%)</label>
            <input
              type="number"
              value={achievement}
              onChange={(e) => setAchievement(parseFloat(e.target.value) || 0)}
              className="w-full bg-black/30 border border-red-900/30 rounded-lg p-3 text-amber-100"
              data-testid="sim-achievement-input"
            />
          </div>
          
          <button
            onClick={handleSimulate}
            disabled={loading}
            className="w-full py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-lg disabled:opacity-50"
            data-testid="sim-calculate-btn"
          >
            {loading ? 'Calculating...' : 'Simulate'}
          </button>
          
          {result && (
            <div className="mt-4 p-4 bg-black/30 rounded-lg space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-400">Eligible:</span>
                <span className={result.eligible ? 'text-green-400' : 'text-red-400'}>
                  {result.eligible ? 'Yes' : `No (${result.reason})`}
                </span>
              </div>
              {result.eligible && (
                <>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Base Commission ({(policy?.base_rate || 0.02) * 100}%):</span>
                    <span className="text-amber-100">Rp {result.base_commission?.toLocaleString('id-ID')}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Achievement Bonus:</span>
                    <span className="text-blue-300">Rp {result.achievement_bonus?.toLocaleString('id-ID')}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Super Bonus ({'>'}110%):</span>
                    <span className="text-purple-300">Rp {result.super_bonus?.toLocaleString('id-ID')}</span>
                  </div>
                  <div className="border-t border-red-900/30 pt-2 flex justify-between">
                    <span className="text-amber-100 font-bold">Total Commission:</span>
                    <span className="text-green-400 font-bold text-lg">Rp {result.total_commission?.toLocaleString('id-ID')}</span>
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const CommissionEngine = () => {
  const { token } = useAuth();
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('list');
  
  // Data states
  const [commissions, setCommissions] = useState([]);
  const [summary, setSummary] = useState(null);
  const [dashboard, setDashboard] = useState(null);
  const [policy, setPolicy] = useState(null);
  const [selectedItems, setSelectedItems] = useState([]);
  
  // Filter states
  const [filterStatus, setFilterStatus] = useState('');
  const [filterPeriod, setFilterPeriod] = useState('monthly');
  
  // Modals
  const [showCalculate, setShowCalculate] = useState(false);
  const [showSimulate, setShowSimulate] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      
      const params = new URLSearchParams();
      if (filterStatus) params.append('status', filterStatus);
      if (filterPeriod) params.append('period_type', filterPeriod);
      
      const [listRes, dashRes, policyRes] = await Promise.all([
        fetch(`${API_URL}/api/commission/list?${params}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`${API_URL}/api/commission/dashboard/summary?period_type=${filterPeriod}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`${API_URL}/api/commission/policy`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
      ]);
      
      const [listData, dashData, policyData] = await Promise.all([
        listRes.json(),
        dashRes.json(),
        policyRes.json()
      ]);
      
      setCommissions(listData.items || []);
      setSummary(listData.summary || null);
      setDashboard(dashData);
      setPolicy(policyData);
      
    } catch (err) {
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  }, [token, filterStatus, filterPeriod]);

  useEffect(() => {
    if (token) fetchData();
  }, [token, fetchData]);

  const handleApprove = async () => {
    const calculatedItems = selectedItems.length > 0 
      ? selectedItems 
      : commissions.filter(c => c.status === 'calculated').map(c => c.id);
    
    if (calculatedItems.length === 0) {
      alert('Tidak ada commission calculated untuk di-approve');
      return;
    }
    
    try {
      const res = await fetch(`${API_URL}/api/commission/approve`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ commission_ids: calculatedItems })
      });
      
      const data = await res.json();
      
      if (data.success) {
        alert(`Approved ${data.approved} commissions`);
        setSelectedItems([]);
        fetchData();
      }
    } catch (err) {
      alert('Gagal approve');
    }
  };

  const handlePay = async () => {
    const approvedItems = selectedItems.length > 0 
      ? selectedItems 
      : commissions.filter(c => c.status === 'approved').map(c => c.id);
    
    if (approvedItems.length === 0) {
      alert('Tidak ada commission approved untuk dibayar');
      return;
    }
    
    const paymentMethod = prompt('Payment method (cash/bank_transfer):', 'bank_transfer');
    if (!paymentMethod) return;
    
    try {
      const res = await fetch(`${API_URL}/api/commission/pay`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
          commission_ids: approvedItems,
          payment_method: paymentMethod
        })
      });
      
      const data = await res.json();
      
      if (data.success) {
        alert(`Paid ${data.paid} commissions. Total: Rp ${data.total_amount?.toLocaleString('id-ID')}`);
        setSelectedItems([]);
        fetchData();
      }
    } catch (err) {
      alert('Gagal process payment');
    }
  };

  const toggleSelect = (id) => {
    if (selectedItems.includes(id)) {
      setSelectedItems(selectedItems.filter(i => i !== id));
    } else {
      setSelectedItems([...selectedItems, id]);
    }
  };

  return (
    <div className="space-y-6" data-testid="commission-engine-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Commission Engine</h1>
          <p className="text-gray-400 text-sm mt-1">Kelola komisi berdasarkan target dan penjualan</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowSimulate(true)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg"
            data-testid="simulate-btn"
          >
            <Calculator className="h-4 w-4" />
            Simulate
          </button>
          <button
            onClick={() => setShowCalculate(true)}
            className="flex items-center gap-2 px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white rounded-lg"
            data-testid="calculate-btn"
          >
            <Plus className="h-4 w-4" />
            Calculate
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

      {/* Dashboard Summary */}
      {dashboard && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-gradient-to-br from-amber-900/30 to-amber-800/10 border border-amber-700/30 rounded-xl p-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-amber-500/20 flex items-center justify-center">
                <DollarSign className="h-5 w-5 text-amber-400" />
              </div>
              <div>
                <p className="text-lg font-bold text-amber-100">Rp {((dashboard.total_amount || 0) / 1000000).toFixed(1)}jt</p>
                <p className="text-xs text-amber-400">Total Commission</p>
              </div>
            </div>
          </div>
          
          <div className="bg-gradient-to-br from-blue-900/30 to-blue-800/10 border border-blue-700/30 rounded-xl p-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-blue-500/20 flex items-center justify-center">
                <Clock className="h-5 w-5 text-blue-400" />
              </div>
              <div>
                <p className="text-lg font-bold text-blue-300">{dashboard.by_status?.calculated?.count || 0}</p>
                <p className="text-xs text-blue-400">Pending Approval</p>
              </div>
            </div>
          </div>
          
          <div className="bg-gradient-to-br from-green-900/30 to-green-800/10 border border-green-700/30 rounded-xl p-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-green-500/20 flex items-center justify-center">
                <CheckCircle2 className="h-5 w-5 text-green-400" />
              </div>
              <div>
                <p className="text-lg font-bold text-green-300">{dashboard.by_status?.approved?.count || 0}</p>
                <p className="text-xs text-green-400">Ready to Pay</p>
              </div>
            </div>
          </div>
          
          <div className="bg-gradient-to-br from-purple-900/30 to-purple-800/10 border border-purple-700/30 rounded-xl p-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-purple-500/20 flex items-center justify-center">
                <CreditCard className="h-5 w-5 text-purple-400" />
              </div>
              <div>
                <p className="text-lg font-bold text-purple-300">{dashboard.by_status?.paid?.count || 0}</p>
                <p className="text-xs text-purple-400">Paid</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Policy Card - Enhanced */}
      {policy && (
        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-3">
            <Settings className="h-5 w-5 text-gray-400" />
            <span className="text-amber-100 font-medium">Commission Policy</span>
            {policy.branch_pool_enabled && (
              <span className="px-2 py-0.5 bg-green-500/20 text-green-300 text-xs rounded">Branch Pool Active</span>
            )}
          </div>
          <div className="grid grid-cols-6 gap-4 text-sm">
            <div>
              <span className="text-gray-500">Type</span>
              <p className="text-amber-100 capitalize">{policy.commission_type || 'sales_value'}</p>
            </div>
            <div>
              <span className="text-gray-500">Base Rate</span>
              <p className="text-amber-100">{((policy.base_rate || 0.02) * 100)}%</p>
            </div>
            <div>
              <span className="text-gray-500">Min Achievement</span>
              <p className="text-amber-100">{policy.min_achievement_for_commission || 80}%</p>
            </div>
            <div>
              <span className="text-gray-500">Super Threshold</span>
              <p className="text-amber-100">{policy.super_bonus_threshold || 110}%</p>
            </div>
            <div>
              <span className="text-gray-500">Super Bonus</span>
              <p className="text-amber-100">{((policy.super_bonus_rate || 0.01) * 100)}%</p>
            </div>
            <div>
              <span className="text-gray-500">Branch Pool Rate</span>
              <p className="text-amber-100">{((policy.branch_pool_rate || 0.005) * 100)}%</p>
            </div>
          </div>
          
          {/* Achievement Tiers Info */}
          <div className="mt-3 pt-3 border-t border-red-900/30">
            <p className="text-xs text-gray-500 mb-2">Achievement Tiers:</p>
            <div className="flex gap-2 flex-wrap">
              <span className="px-2 py-1 bg-red-500/10 text-red-300 text-xs rounded">{'<'}80% = No Commission</span>
              <span className="px-2 py-1 bg-amber-500/10 text-amber-300 text-xs rounded">80-99% = Base</span>
              <span className="px-2 py-1 bg-blue-500/10 text-blue-300 text-xs rounded">100-109% = +Bonus</span>
              <span className="px-2 py-1 bg-purple-500/10 text-purple-300 text-xs rounded">{'≥'}110% = +Super</span>
            </div>
          </div>
        </div>
      )}
      {/* Filters & Actions */}
      <div className="flex flex-wrap gap-4 items-center">
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="px-4 py-2 bg-black/30 border border-red-900/30 rounded-lg text-amber-100"
          data-testid="filter-status"
        >
          <option value="">Semua Status</option>
          <option value="calculated">Calculated</option>
          <option value="approved">Approved</option>
          <option value="paid">Paid</option>
        </select>
        
        <select
          value={filterPeriod}
          onChange={(e) => setFilterPeriod(e.target.value)}
          className="px-4 py-2 bg-black/30 border border-red-900/30 rounded-lg text-amber-100"
          data-testid="filter-period"
        >
          <option value="monthly">Bulanan</option>
          <option value="quarterly">Kuartalan</option>
          <option value="yearly">Tahunan</option>
        </select>
        
        <div className="flex-1" />
        
        {commissions.some(c => c.status === 'calculated') && (
          <button
            onClick={handleApprove}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-500 text-white rounded-lg"
            data-testid="approve-btn"
          >
            <CheckCircle2 className="h-4 w-4" />
            Approve Selected
          </button>
        )}
        
        {commissions.some(c => c.status === 'approved') && (
          <button
            onClick={handlePay}
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-lg"
            data-testid="pay-btn"
          >
            <CreditCard className="h-4 w-4" />
            Pay Selected
          </button>
        )}
      </div>

      {/* Commission List */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <RefreshCw className="h-8 w-8 text-amber-500 animate-spin" />
        </div>
      ) : commissions.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <Wallet className="h-12 w-12 mx-auto mb-3 opacity-30" />
          <p>Belum ada data komisi</p>
          <button
            onClick={() => setShowCalculate(true)}
            className="mt-4 text-amber-400 hover:text-amber-300"
          >
            + Calculate Commission
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {commissions.map((commission) => (
            <div 
              key={commission.id}
              className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4 hover:border-amber-500/30"
              data-testid={`commission-${commission.id}`}
            >
              <div className="flex items-start gap-4">
                <input
                  type="checkbox"
                  checked={selectedItems.includes(commission.id)}
                  onChange={() => toggleSelect(commission.id)}
                  className="mt-1 rounded bg-black/30"
                  disabled={commission.status === 'paid' || commission.status === 'cancelled'}
                />
                
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    {commission.ref_type === 'salesman' ? (
                      <Users className="h-5 w-5 text-green-400" />
                    ) : (
                      <Building2 className="h-5 w-5 text-blue-400" />
                    )}
                    <span className="text-amber-100 font-semibold">{commission.ref_name}</span>
                    <span className="text-gray-500 text-sm">{commission.period_type}</span>
                    <StatusBadge status={commission.status} />
                    {commission.achievement_percent >= 110 && (
                      <span className="px-2 py-0.5 bg-purple-500/20 text-purple-300 text-xs rounded">SUPER</span>
                    )}
                  </div>
                  
                  <div className="grid grid-cols-6 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500">Period</span>
                      <p className="text-gray-300">{commission.period_start}</p>
                    </div>
                    <div>
                      <span className="text-gray-500">Sales</span>
                      <p className="text-gray-300">Rp {commission.sales_value?.toLocaleString('id-ID')}</p>
                    </div>
                    <div>
                      <span className="text-gray-500">Target</span>
                      <p className="text-gray-300">Rp {commission.target_value?.toLocaleString('id-ID')}</p>
                    </div>
                    <div>
                      <span className="text-gray-500">Achievement</span>
                      <p className={`font-bold ${commission.achievement_percent >= 100 ? 'text-green-400' : commission.achievement_percent >= 80 ? 'text-amber-100' : 'text-red-400'}`}>
                        {commission.achievement_percent}%
                      </p>
                    </div>
                    <div>
                      <span className="text-gray-500">Base / Bonus</span>
                      <p className="text-gray-300">
                        Rp {commission.base_commission?.toLocaleString('id-ID')} + {commission.achievement_bonus?.toLocaleString('id-ID')}
                      </p>
                    </div>
                    <div>
                      <span className="text-gray-500">Total</span>
                      <p className="text-green-400 font-bold">
                        Rp {commission.total_commission?.toLocaleString('id-ID')}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Top Earners */}
      {dashboard?.top_earners?.length > 0 && (
        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-4">
            <Award className="h-5 w-5 text-amber-400" />
            <span className="text-amber-100 font-medium">Top Earners</span>
          </div>
          <div className="space-y-2">
            {dashboard.top_earners.map((earner, idx) => (
              <div key={idx} className="flex items-center gap-4 p-2 bg-black/20 rounded-lg">
                <span className={`h-6 w-6 rounded-full flex items-center justify-center text-sm font-bold ${
                  idx === 0 ? 'bg-amber-500/30 text-amber-300' :
                  idx === 1 ? 'bg-gray-400/30 text-gray-300' :
                  'bg-orange-500/30 text-orange-300'
                }`}>
                  {idx + 1}
                </span>
                <span className="text-amber-100 flex-1">{earner.name}</span>
                <span className="text-gray-400">{earner.achievement}%</span>
                <span className="text-green-400 font-bold">Rp {earner.amount?.toLocaleString('id-ID')}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Modals */}
      {showCalculate && (
        <CalculateModal
          onClose={() => setShowCalculate(false)}
          onSave={() => {
            setShowCalculate(false);
            fetchData();
          }}
          token={token}
        />
      )}
      
      {showSimulate && (
        <SimulateModal
          onClose={() => setShowSimulate(false)}
          token={token}
          policy={policy}
        />
      )}
    </div>
  );
};

export default CommissionEngine;
